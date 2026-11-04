from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .config import F1Config
from .models import DecisionSummary, Observation, RawCell, SourceInfo
from .text import (
    clean_display_label,
    strip_accents,
    format_number,
    is_year_value,
    normalize_label,
    period_string,
    quarter_from_label,
    value_as_float,
    year_from_value,
)


@dataclass(frozen=True)
class PeriodValue:
    year: int
    quarter: int | None = None

    @property
    def key(self) -> str:
        return period_string(self.year, self.quarter)


@dataclass
class PeriodBlock:
    header_row: int
    quarter_row: int | None
    col_periods: dict[int, PeriodValue]
    col_data_types: dict[int, str] = field(default_factory=dict)


_CORE_REAL_SHEETS = {
    "ventas",
    "produccion",
    "ingresos",
    "resultados",
    "analisis de balance",
    "balance",
    "margen",
    "logistica",
    "mercado",
}


def _grid(cells: Iterable[RawCell]) -> dict[tuple[int, int], RawCell]:
    return {(cell.row, cell.column): cell for cell in cells}


def _year_cells(grid: dict[tuple[int, int], RawCell], row: int) -> list[tuple[int, int]]:
    found: list[tuple[int, int]] = []
    for (cell_row, column), cell in grid.items():
        if cell_row != row:
            continue
        year = year_from_value(cell.value)
        if year is not None:
            found.append((column, year))
    return sorted(found)


def _relative_year_cells(
    grid: dict[tuple[int, int], RawCell], row: int, base_year: int
) -> list[tuple[int, int]]:
    found: list[tuple[int, int]] = []
    for (cell_row, column), cell in grid.items():
        if cell_row != row or cell.value_type != "string":
            continue
        text = strip_accents(clean_display_label(cell.value)).casefold()
        match = re.search(r"ano\s*\+\s*(\d+)", text)
        if match:
            found.append((column, base_year + int(match.group(1))))
    return sorted(found)


def _quarter_cells(grid: dict[tuple[int, int], RawCell], row: int) -> list[tuple[int, int]]:
    found: list[tuple[int, int]] = []
    for (cell_row, column), cell in grid.items():
        if cell_row != row or not isinstance(cell.value, str):
            continue
        quarter = quarter_from_label(cell.value)
        if quarter is not None:
            found.append((column, quarter))
    return sorted(found)


def _numeric_columns(grid: dict[tuple[int, int], RawCell], row: int) -> list[int]:
    return sorted(
        column
        for (cell_row, column), cell in grid.items()
        if cell_row == row and cell.value_type == "number"
    )


def _string_count(grid: dict[tuple[int, int], RawCell], row: int, columns: list[int]) -> int:
    count = 0
    for column in columns:
        cell = grid.get((row, column))
        if cell is None or cell.value_type != "string":
            continue
        if year_from_value(cell.value) is not None:
            continue
        if clean_display_label(cell.value):
            count += 1
    return count


def _groups_from_quarters(quarter_columns: list[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    groups: list[list[tuple[int, int]]] = []
    current: list[tuple[int, int]] = []
    previous_col: int | None = None
    previous_q: int | None = None
    for column, quarter in quarter_columns:
        starts_new = (
            previous_col is None
            or column != previous_col + 1
            or previous_q is None
            or quarter != previous_q + 1
        )
        if starts_new and current:
            groups.append(current)
            current = []
        current.append((column, quarter))
        previous_col = column
        previous_q = quarter
    if current:
        groups.append(current)
    return groups


def detect_period_blocks(cells: list[RawCell], config: F1Config) -> list[PeriodBlock]:
    if not cells:
        return []
    grid = _grid(cells)
    max_row = max(cell.row for cell in cells)
    blocks: list[PeriodBlock] = []
    used_quarter_rows: set[int] = set()

    for row in range(1, max_row + 1):
        years = _year_cells(grid, row)
        if not years:
            continue

        quarter_row: int | None = None
        quarter_columns: list[tuple[int, int]] = []
        for candidate in (row + 1, row + 2):
            candidate_quarters = _quarter_cells(grid, candidate)
            if len(candidate_quarters) >= 2:
                quarter_row = candidate
                quarter_columns = candidate_quarters
                break

        if quarter_row is not None:
            groups = _groups_from_quarters(quarter_columns)
            unique_years = []
            seen_years: set[int] = set()
            for _, year in years:
                if year not in seen_years:
                    seen_years.add(year)
                    unique_years.append(year)
            col_periods: dict[int, PeriodValue] = {}
            for index, group in enumerate(groups):
                if len(groups) == len(unique_years):
                    period_year = unique_years[index]
                else:
                    group_start = group[0][0]
                    preceding = [col for col, _ in years if col <= group_start]
                    period_year = (
                        next((year for col, year in reversed(years) if col == preceding[-1]), unique_years[0])
                        if preceding
                        else unique_years[0]
                    )
                for column, quarter in group:
                    col_periods[column] = PeriodValue(period_year, quarter)
            if col_periods:
                blocks.append(PeriodBlock(header_row=row, quarter_row=quarter_row, col_periods=col_periods))
                used_quarter_rows.add(quarter_row)
            continue

        unique_years = []
        seen_years = set()
        for _, year in years:
            if year not in seen_years:
                seen_years.add(year)
                unique_years.append(year)
        if len(unique_years) < 2:
            continue

        relative_years = _relative_year_cells(grid, row, max(unique_years))
        year_columns = sorted(years + relative_years)
        min_year_col = min(column for column, _ in year_columns)
        data_columns = _numeric_columns(grid, row + 2)
        if not data_columns:
            data_columns = _numeric_columns(grid, row + 1)
        relevant_columns = [column for column in data_columns if column >= min_year_col]
        if relevant_columns:
            range_cols = list(range(min_year_col, max(relevant_columns) + 1))
        else:
            range_cols = [column for column, _ in year_columns]

        string_count = _string_count(grid, row + 1, range_cols)
        split_groups = (
            not relative_years
            and len(range_cols) > len(unique_years)
            and string_count >= len(unique_years)
            and len(range_cols) % len(unique_years) == 0
        )
        col_periods = {}
        if split_groups:
            width = len(range_cols) // len(unique_years)
            for index, year in enumerate(unique_years):
                for column in range_cols[index * width : (index + 1) * width]:
                    col_periods[column] = PeriodValue(year)
        else:
            for column, year in year_columns:
                col_periods[column] = PeriodValue(year)
        if col_periods:
            blocks.append(PeriodBlock(header_row=row, quarter_row=None, col_periods=col_periods))

    quarter_rows = [
        row for row in range(1, max_row + 1) if len(_quarter_cells(grid, row)) >= 2
    ]
    for quarter_row in quarter_rows:
        if quarter_row in used_quarter_rows:
            continue
        previous_years = [
            period.year
            for block in blocks
            if block.header_row < quarter_row
            for period in block.col_periods.values()
        ]
        if not previous_years:
            continue
        period_year = max(previous_years)
        col_periods = {
            column: PeriodValue(period_year, quarter)
            for column, quarter in _quarter_cells(grid, quarter_row)
        }
        if col_periods:
            blocks.append(PeriodBlock(header_row=quarter_row, quarter_row=quarter_row, col_periods=col_periods))

    for row in range(1, max_row + 1):
        row_cells = {
            column: cell
            for (cell_row, column), cell in grid.items()
            if cell_row == row
        }
        if not row_cells or any(cell.value_type == "number" for cell in row_cells.values()):
            continue
        labels = {
            column: normalize_label(cell.value)
            for column, cell in row_cells.items()
            if cell.value_type == "string"
        }
        budget_columns = [column for column, label in labels.items() if label == "presupuesto"]
        result_columns = [
            column
            for column, label in labels.items()
            if label in {"resultado", "real", "actual"}
        ]
        if not budget_columns or not result_columns:
            continue
        previous_years = [
            period.year
            for block in blocks
            if block.header_row < row
            for period in block.col_periods.values()
        ]
        if not previous_years:
            continue
        period_year = max(previous_years)
        col_periods: dict[int, PeriodValue] = {}
        col_data_types: dict[int, str] = {}
        for column in result_columns:
            col_periods[column] = PeriodValue(period_year)
            col_data_types[column] = "real"
        for column in budget_columns:
            col_periods[column] = PeriodValue(period_year)
            col_data_types[column] = "budget"
        blocks.append(
            PeriodBlock(
                header_row=row,
                quarter_row=None,
                col_periods=col_periods,
                col_data_types=col_data_types,
            )
        )

    blocks.sort(key=lambda block: block.header_row)
    return blocks


def _section_hints(
    cells: list[RawCell], max_row: int, reset_rows: set[int]
) -> dict[int, str | None]:
    by_row: dict[int, list[str]] = {}
    for cell in cells:
        if cell.value_type == "string":
            text = clean_display_label(cell.value)
            if text and len(text) <= 120 and "\n" not in str(cell.value):
                by_row.setdefault(cell.row, []).append(text)
    hints: dict[int, str | None] = {}
    current: str | None = None
    for row in range(1, max_row + 1):
        if row in reset_rows:
            current = None
        texts = " ".join(by_row.get(row, [])).casefold()
        if "presupuesto" in texts:
            current = "budget"
        elif "escenario" in texts:
            current = "scenario"
        elif "proyeccion" in texts or "previsión" in texts or "prevision" in texts:
            current = "projection"
        elif "historico" in texts or "histórico" in texts:
            current = "real"
        hints[row] = current
    return hints


def _section_titles(cells: list[RawCell], max_row: int) -> tuple[dict[int, str], set[int]]:
    by_row: dict[int, list[RawCell]] = {}
    for cell in cells:
        by_row.setdefault(cell.row, []).append(cell)
    titles: dict[int, str] = {}
    reset_rows: set[int] = set()
    current: str = ""
    for row in range(1, max_row + 1):
        row_cells = by_row.get(row, [])
        has_number = any(cell.value_type == "number" for cell in row_cells)
        title = ""
        if not has_number and len(row_cells) == 1:
            cell = row_cells[0]
            if cell.value_type == "string" and year_from_value(cell.value) is None:
                text = clean_display_label(cell.value)
                if len(text) >= 20:
                    title = text
        if title:
            current = title
            reset_rows.add(row)
        titles[row] = current
    return titles, reset_rows


def _sheet_data_type(sheet: str) -> str:
    normalized = normalize_label(sheet)
    if "presupuesto" in normalized:
        return "budget"
    if "escenario" in normalized:
        return "scenario"
    return "real"


def _data_type(sheet: str, section_hint: str | None) -> str:
    return section_hint or _sheet_data_type(sheet)


def _unit_for(sheet: str, label: str, title: str = "") -> str:
    normalized = normalize_label(label)
    title_normalized = normalize_label(title)
    sheet_norm = normalize_label(sheet)
    if sheet_norm == "marketing" and "precio" in title_normalized and normalized in {
        "corbatas",
        "bufandas",
        "calcetines",
    }:
        return "EUR_per_unit"
    if any(
        token in normalized
        for token in (
            "pct",
            "porcentaje",
            "tasa",
            "ratio",
            "margen",
            "variacion",
            "cobertura",
            "endeudamiento",
            "participacion",
            "rentabilidad",
            "rendimiento",
        )
    ):
        return "percent"
    if "precio" in normalized or "coste unitario" in normalized:
        return "EUR_per_unit"
    if any(token in normalized for token in ("unidades", "unid ", "capacidad", "inventario", "produccion")):
        return "units"
    if sheet_norm in {"ventas"} and not any(
        token in normalized for token in ("ingreso", "precio", "coste", "margen", "total")
    ):
        return "units"
    if any(
        token in normalized
        for token in (
            "ingreso",
            "venta",
            "coste",
            "gasto",
            "resultado",
            "activo",
            "pasivo",
            "patrimonio",
            "deuda",
            "efectivo",
            "reserva",
            "capital",
            "inversion",
            "inversión",
            "valor",
            "amortizacion",
            "depreciacion",
            "financiero",
            "capex",
            "caja",
            "proveedor",
            "impuesto",
        )
    ):
        return "EUR"
    return "number"


def _currency_for(unit: str) -> str:
    return "EUR" if unit.startswith("EUR") else ""


def _find_label(grid: dict[tuple[int, int], RawCell], row: int, column: int) -> str:
    for candidate in range(column - 1, 0, -1):
        cell = grid.get((row, candidate))
        if cell is None:
            continue
        if cell.value_type == "string":
            text = clean_display_label(cell.value)
            if text:
                return text
        if cell.value_type == "number":
            continue
    for offset in range(1, 6):
        cell = grid.get((row - offset, column))
        if cell is not None and cell.value_type == "string":
            text = clean_display_label(cell.value)
            if text:
                return text
    return ""


def _find_column_header(grid: dict[tuple[int, int], RawCell], row: int, column: int) -> str:
    for offset in range(1, 6):
        cell = grid.get((row - offset, column))
        if cell is None or cell.value_type != "string":
            continue
        if year_from_value(cell.value) is not None:
            continue
        text = clean_display_label(cell.value)
        if text:
            return text
    return ""


def _active_block(blocks: list[PeriodBlock], row: int) -> PeriodBlock | None:
    active: PeriodBlock | None = None
    for block in blocks:
        if block.header_row < row:
            active = block
        else:
            break
    return active


def _json_label(path: str) -> str:
    tail = path.rsplit(".", 1)[-1]
    if "[" in tail:
        tail = tail.split("[", 1)[0]
    return tail


def _json_scope(path: str) -> str:
    return path.rsplit(".", 1)[0] if "." in path else ""


def _json_unit(path: str, label: str, value_type: str) -> str:
    if value_type in {"string", "boolean"}:
        return value_type
    normalized = normalize_label(path)
    if "precio_unitario" in normalized or "precio unitario" in normalized or "precio" in normalize_label(label):
        return "EUR_per_unit"
    if "unidades" in normalized or "unidades_producir" in normalized:
        return "units"
    if any(token in normalized for token in ("pct", "porcentaje", "incentivo", "descuento")):
        return "percent"
    if any(token in normalized for token in ("inversion", "capex", "precio", "promocion", "presupuesto")):
        return "EUR"
    return "number"


def extract_excel_observations(
    source: SourceInfo,
    cells: list[RawCell],
    config: F1Config,
    start_index: int,
) -> tuple[list[Observation], int]:
    observations: list[Observation] = []
    counter = start_index
    by_sheet: dict[str, list[RawCell]] = {}
    for cell in cells:
        by_sheet.setdefault(cell.sheet, []).append(cell)

    for sheet in source.sheets:
        sheet_cells = by_sheet.get(sheet, [])
        if not sheet_cells:
            continue
        grid = _grid(sheet_cells)
        max_row = max(cell.row for cell in sheet_cells)
        blocks = detect_period_blocks(sheet_cells, config)
        titles, reset_rows = _section_titles(sheet_cells, max_row)
        hints = _section_hints(sheet_cells, max_row, reset_rows)
        header_rows = {
            value
            for block in blocks
            for value in (block.header_row, block.quarter_row)
            if value is not None
        }
        for row in range(1, max_row + 1):
            last_reset = max((value for value in reset_rows if value <= row), default=0)
            block = _active_block(blocks, row)
            if block is None or row in header_rows or block.header_row < last_reset:
                continue
            for cell in sorted(
                (cell for (cell_row, _), cell in grid.items() if cell_row == row),
                key=lambda value: value.column,
            ):
                if cell.value_type != "number" or cell.column not in block.col_periods:
                    continue
                label = _find_label(grid, row, cell.column)
                segment = _find_column_header(grid, row, cell.column)
                normalized = normalize_label(label)
                period_value = block.col_periods[cell.column]
                quarter = period_value.quarter
                if quarter is None:
                    row_quarter = quarter_from_label(label)
                    if row_quarter is not None:
                        quarter = row_quarter
                period = period_string(period_value.year, quarter)
                data_type = block.col_data_types.get(
                    cell.column, _data_type(sheet, hints.get(row))
                )
                title = titles.get(row, "")
                unit = _unit_for(sheet, label, title)
                section = hints.get(row)
                scope_parts = [sheet]
                if title:
                    scope_parts.append(title)
                if section:
                    scope_parts.append(section)
                scope = " / ".join(scope_parts)
                issues: list[str] = []
                integrity = "ok"
                if not label:
                    integrity = "warning"
                    issues.append("sin etiqueta de fila")
                observation = Observation(
                    observation_id=f"OBS-{counter:06d}",
                    source_id=source.source_id,
                    source_path=source.relative_path,
                    source_type="excel",
                    sheet=sheet,
                    cell=cell.coordinate,
                    source_row=row,
                    source_column=cell.column,
                    block_id=block.header_row,
                    label_raw=label,
                    label_normalized=normalized,
                    period=period,
                    year=period_value.year,
                    quarter=quarter,
                    period_status="unknown",
                    data_type=data_type,
                    metric=normalized or f"{sheet}:{row}:{cell.column}",
                    scope=scope,
                    segment=segment,
                    value=cell.value,
                    value_text=format_number(value_as_float(cell.value)),
                    value_type=cell.value_type,
                    unit=unit,
                    currency=_currency_for(unit),
                    normalized_value=value_as_float(cell.value),
                    normalization_status="identity" if cell.value_type == "number" else "not_applicable",
                    integrity_status=integrity,
                    provenance=(
                        f"source={source.relative_path};sheet={sheet};"
                        f"cell={cell.coordinate};row={row};col={cell.column};label={label}"
                    ),
                    issues=issues,
                )
                observations.append(observation)
                counter += 1
    return observations, counter


def extract_json_observations(
    source: SourceInfo,
    cells: list[RawCell],
    summary: DecisionSummary,
    config: F1Config,
    start_index: int,
) -> tuple[list[Observation], int]:
    observations: list[Observation] = []
    counter = start_index
    for cell in cells:
        label = _json_label(cell.coordinate)
        scope = _json_scope(cell.coordinate)
        unit = _json_unit(cell.coordinate, label, cell.value_type)
        observations.append(
            Observation(
                observation_id=f"OBS-{counter:06d}",
                source_id=source.source_id,
                source_path=source.relative_path,
                source_type="json",
                sheet=cell.sheet,
                cell=cell.coordinate,
                source_row=0,
                source_column=0,
                block_id=None,
                label_raw=label,
                label_normalized=normalize_label(label),
                period=str(summary.period) if summary.period else "",
                year=summary.period or None,
                quarter=None,
                period_status="unknown",
                data_type="decision",
                metric=cell.coordinate,
                scope=scope,
                segment=scope,
                value=cell.value,
                value_text=format_number(value_as_float(cell.value)),
                value_type=cell.value_type,
                unit=unit,
                currency=_currency_for(unit),
                normalized_value=value_as_float(cell.value),
                normalization_status="identity" if cell.value_type == "number" else "not_applicable",
                integrity_status="ok" if summary.period else "warning",
                financial_status="not_applicable",
                provenance=f"source={source.relative_path};path={cell.coordinate};label={label}",
                issues=[] if summary.period else ["periodo no determinable"],
            )
        )
        counter += 1
    return observations, counter


def _markdown_data_type(table: dict[str, Any]) -> str:
    text = normalize_label(
        " ".join([str(table.get("title", ""))] + [str(value) for value in table.get("headers", [])])
    )
    if "presupuesto" in text or "budget" in text:
        return "budget"
    if "escenario" in text or "scenario" in text:
        return "scenario"
    if "proyeccion" in text or "prevision" in text:
        return "projection"
    if "real" in text or "actual" in text or "historico" in text:
        return "real"
    return "captured"


def _period_from_header(value: Any) -> tuple[int | None, int | None]:
    text = clean_display_label(value)
    if not text:
        return None, None
    match = re.search(r"\b(20\d{2})\b", text)
    year = int(match.group(1)) if match else None
    return year, quarter_from_label(text)


def extract_markdown_observations(
    source: SourceInfo,
    cells: list[RawCell],
    config: F1Config,
    start_index: int,
) -> tuple[list[Observation], int]:
    observations: list[Observation] = []
    counter = start_index
    by_sheet: dict[str, list[RawCell]] = {}
    for cell in cells:
        by_sheet.setdefault(cell.sheet, []).append(cell)

    for table in source.markdown_tables:
        sheet = str(table.get("sheet", ""))
        sheet_cells = by_sheet.get(sheet, [])
        if not sheet_cells:
            continue
        data_type = _markdown_data_type(table)
        headers = [str(value) for value in table.get("headers", [])]
        data_start = int(table.get("data_start", 2))
        rows = sorted({cell.row for cell in sheet_cells if cell.row >= data_start})
        string_counts: dict[int, int] = {}
        for row in rows:
            for cell in sheet_cells:
                if cell.row == row and cell.value_type == "string":
                    string_counts[cell.column] = string_counts.get(cell.column, 0) + 1
        label_column = max(string_counts, key=string_counts.get) if string_counts else 1
        title = str(table.get("title", "")) or source.title

        for row in rows:
            row_cells = sorted(
                (cell for cell in sheet_cells if cell.row == row),
                key=lambda cell: cell.column,
            )
            label_cell = next((cell for cell in row_cells if cell.column == label_column), None)
            label = clean_display_label(label_cell.value) if label_cell is not None else ""
            if not label:
                label = next(
                    (
                        clean_display_label(cell.value)
                        for cell in row_cells
                        if cell.value_type == "string"
                    ),
                    "",
                )
            for cell in row_cells:
                if cell.value_type != "number" or cell.column == label_column:
                    continue
                header = headers[cell.column - 1] if cell.column - 1 < len(headers) else ""
                year, quarter = _period_from_header(header)
                period = period_string(year, quarter) if year is not None else ""
                issues: list[str] = []
                integrity = "ok"
                if year is None:
                    integrity = "warning"
                    issues.append("periodo no explícito en el encabezado de la columna")
                if not label:
                    integrity = "warning"
                    issues.append("sin etiqueta de fila")
                normalized = normalize_label(label)
                scope = " / ".join(item for item in (source.title or source.relative_path, title) if item)
                observations.append(
                    Observation(
                        observation_id=f"OBS-{counter:06d}",
                        source_id=source.source_id,
                        source_path=source.relative_path,
                        source_type="markdown",
                        sheet=sheet,
                        cell=cell.coordinate,
                        source_row=row,
                        source_column=cell.column,
                        block_id=int(table.get("index", 0)) or None,
                        label_raw=label,
                        label_normalized=normalized,
                        period=period,
                        year=year,
                        quarter=quarter,
                        period_status="unknown",
                        data_type=data_type,
                        metric=normalized or f"{sheet}:{row}:{cell.column}",
                        scope=scope,
                        segment=header,
                        value=cell.value,
                        value_text=cell.raw_text or format_number(value_as_float(cell.value)),
                        value_type=cell.value_type,
                        unit=_unit_for("markdown", label, title),
                        currency="",
                        normalized_value=value_as_float(cell.value),
                        normalization_status="identity" if cell.value_type == "number" else "not_applicable",
                        integrity_status=integrity,
                        financial_status="not_applicable" if data_type == "captured" else "not_validated",
                        provenance=(
                            f"source={source.relative_path};table=T{int(table.get('index', 0)):02d};"
                            f"sheet={sheet};cell={cell.coordinate};row={row};col={cell.column};"
                            f"label={label}"
                        ),
                        issues=issues,
                    )
                )
                counter += 1
    return observations, counter


def _finalize_observations(observations: list[Observation]) -> None:
    core_years = [
        observation.year
        for observation in observations
        if observation.data_type == "real"
        and observation.year is not None
        and normalize_label(observation.sheet) in _CORE_REAL_SHEETS
    ]
    all_real_years = [
        observation.year
        for observation in observations
        if observation.data_type == "real" and observation.year is not None
    ]
    latest_real = max(core_years or all_real_years or [0])

    for observation in observations:
        if observation.year is None:
            observation.period_status = "unknown"
            continue
        if observation.data_type == "real" and observation.year > latest_real:
            observation.data_type = "projection"
            observation.add_issue("periodo posterior al último cierre real; tratado como proyección")
            if observation.financial_status == "not_validated":
                observation.financial_status = "not_validated"
        if observation.year < latest_real:
            observation.period_status = "historical"
        elif observation.year == latest_real:
            observation.period_status = "current"
        else:
            observation.period_status = "future"


def canonicalize_sources(
    sources: list[SourceInfo],
    cells_by_source: dict[str, list[RawCell]],
    summaries: list[DecisionSummary],
    config: F1Config,
) -> list[Observation]:
    summary_by_source = {summary.source_id: summary for summary in summaries}
    observations: list[Observation] = []
    counter = 1
    for source in sources:
        cells = cells_by_source.get(source.source_id, [])
        if source.source_type == "excel":
            extracted, counter = extract_excel_observations(source, cells, config, counter)
        elif source.source_type == "markdown":
            extracted, counter = extract_markdown_observations(source, cells, config, counter)
        else:
            summary = summary_by_source.get(source.source_id)
            if summary is None:
                continue
            extracted, counter = extract_json_observations(source, cells, summary, config, counter)
        observations.extend(extracted)

    _finalize_observations(observations)
    for source in sources:
        source_observations = [obs for obs in observations if obs.source_id == source.source_id]
        source.periods = sorted(
            {obs.period for obs in source_observations if obs.period},
            key=lambda value: (int(value[:4]), value),
        )
        source.data_types = sorted({obs.data_type for obs in source_observations})
    return observations
