from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from .config import F1Config
from .markdown import parse_frontmatter, parse_markdown_tables
from .models import DecisionSummary, RawCell, SourceInfo
from .text import json_safe, value_type


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return path.name


def _kind(path: Path, source_type: str) -> str:
    if source_type == "markdown":
        return "captured"
    if source_type == "json":
        return "decisions" if "decision" in path.name.casefold() else "json"
    if path.name.casefold().startswith("matriz_general"):
        return "matrix"
    return "workbook"


def discover_sources(data_dir: Path, project_root: Path) -> list[SourceInfo]:
    if not data_dir.exists():
        raise FileNotFoundError(f"No existe el directorio de datos: {data_dir}")

    excel_paths = sorted(
        path
        for path in data_dir.rglob("*.xlsx")
        if path.is_file() and not path.name.startswith("~$") and not path.name.startswith(".")
    )
    json_paths = sorted(
        path
        for path in data_dir.rglob("*.json")
        if path.is_file() and not path.name.startswith(".")
    )
    manual_dir = data_dir / "manual"
    markdown_paths = sorted(
        path
        for path in manual_dir.rglob("*.md")
        if path.is_file()
        and not path.name.startswith(".")
        and not path.name.startswith("_")
        and path.name.casefold() != "readme.md"
    ) if manual_dir.exists() else []

    sources: list[SourceInfo] = []
    for index, path in enumerate(excel_paths, start=1):
        source_type = "excel"
        sources.append(
            SourceInfo(
                source_id=f"SRC-XLSX-{index:03d}",
                path=str(path.resolve()),
                relative_path=_relative(path, project_root),
                source_type=source_type,
                kind=_kind(path, source_type),
                sha256_before=sha256_file(path),
                size_bytes=path.stat().st_size,
            )
        )
    for index, path in enumerate(json_paths, start=1):
        source_type = "json"
        sources.append(
            SourceInfo(
                source_id=f"SRC-JSON-{index:03d}",
                path=str(path.resolve()),
                relative_path=_relative(path, project_root),
                source_type=source_type,
                kind=_kind(path, source_type),
                sha256_before=sha256_file(path),
                size_bytes=path.stat().st_size,
            )
        )
    for index, path in enumerate(markdown_paths, start=1):
        source_type = "markdown"
        frontmatter, _, warnings = parse_frontmatter(path.read_text(encoding="utf-8"))
        sources.append(
            SourceInfo(
                source_id=f"SRC-MD-{index:03d}",
                path=str(path.resolve()),
                relative_path=_relative(path, project_root),
                source_type=source_type,
                kind=_kind(path, source_type),
                sha256_before=sha256_file(path),
                size_bytes=path.stat().st_size,
                warnings=warnings,
                captured_at=str(frontmatter.get("captured_at", "")),
                origin_url=str(frontmatter.get("source_url", frontmatter.get("origin_url", ""))),
                title=str(frontmatter.get("title", path.stem)),
                frontmatter=frontmatter,
            )
        )
    return sources


def refresh_hashes(sources: list[SourceInfo]) -> list[SourceInfo]:
    for source in sources:
        source.sha256_after = sha256_file(Path(source.path))
    return sources


def load_excel_source(source: SourceInfo, config: F1Config) -> list[RawCell]:
    path = Path(source.path)
    workbook = load_workbook(path, data_only=False, read_only=False)
    cells: list[RawCell] = []
    try:
        for sheet in workbook.worksheets:
            source.sheets.append(sheet.title)
            merged: dict[str, str] = {}
            for merged_range in sheet.merged_cells.ranges:
                text = str(merged_range)
                for row in range(merged_range.min_row, merged_range.max_row + 1):
                    for column in range(merged_range.min_col, merged_range.max_col + 1):
                        merged[sheet.cell(row, column).coordinate] = text
            for row in sheet.iter_rows():
                for cell in row:
                    value = cell.value
                    if _is_blank(value):
                        continue
                    safe_value = json_safe(value)
                    cells.append(
                        RawCell(
                            source_id=source.source_id,
                            source_path=source.relative_path,
                            sheet=sheet.title,
                            row=cell.row,
                            column=cell.column,
                            coordinate=cell.coordinate,
                            value=safe_value,
                            value_type=value_type(safe_value),
                            number_format=str(cell.number_format or ""),
                            merged_range=merged.get(cell.coordinate),
                            raw_text=str(value),
                        )
                    )
    finally:
        workbook.close()
    return cells


def _walk_json(value: Any, path: str, output: list[RawCell], source: SourceInfo) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _walk_json(child, f"{path}.{key}" if path else str(key), output, source)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_json(child, f"{path}[{index}]", output, source)
    else:
        if _is_blank(value):
            return
        safe_value = json_safe(value)
        output.append(
            RawCell(
                source_id=source.source_id,
                source_path=source.relative_path,
                sheet="JSON:decisiones",
                row=0,
                column=0,
                coordinate=path,
                value=safe_value,
                value_type=value_type(safe_value),
                number_format="",
                merged_range=None,
                raw_text=str(value),
            )
        )


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _period_from_json(data: dict[str, Any], path: Path) -> int | None:
    value = data.get("periodo")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    match = re.search(r"(20\d{2})", path.name)
    return int(match.group(1)) if match else None


_ACCEPTED_DECISIONS = frozenset({"aceptar", "si", "sí", "yes", "true", "seleccionado"})
_PRODUCT_SUFFIXES = ("_catalogo_euro", "_euro", "_eur")


def _decision_sections(data: dict[str, Any]) -> dict[str, Any]:
    """Devuelve el bloque de decisiones sea cual sea el esquema de la bitácora.

    Esquema histórico (2026-2027): ``decisiones.ventas.precio_unitario``.
    Esquema por rondas (2028+): ``modulos.ventas.precios_venta_unitario``.
    """
    for key in ("decisiones", "modulos"):
        section = data.get(key)
        if isinstance(section, dict) and section:
            return section
    return {}


def _product_key(raw_key: object) -> str:
    key = str(raw_key).strip().lower()
    for suffix in _PRODUCT_SUFFIXES:
        if key.endswith(suffix):
            key = key[: -len(suffix)]
    return key


def _product_values(raw: object) -> dict[str, float]:
    """Normaliza un mapa producto -> valor descartando totales y claves no numéricas."""
    if not isinstance(raw, dict):
        return {}
    values: dict[str, float] = {}
    for key, value in raw.items():
        product = _product_key(key)
        if not product or product.startswith("total"):
            continue
        number = _number(value)
        if number is not None:
            values[product] = number
    return values


def _first_number(mapping: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        number = _number(mapping.get(key))
        if number is not None:
            return number
    return None


def _project_selected(project: dict[str, Any]) -> bool:
    value = project.get("seleccionado", project.get("decision"))
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _ACCEPTED_DECISIONS
    return False


def _project_investment(project: dict[str, Any]) -> float:
    """Suma las claves de inversión del proyecto, ignorando ingresos y plusvalías."""
    total = 0.0
    for key, value in project.items():
        if not key.startswith("inversion"):
            continue
        number = _number(value)
        if number is not None:
            total += number
    return total


def _decision_summary(data: dict[str, Any], source: SourceInfo, path: Path) -> DecisionSummary:
    decisions = _decision_sections(data)
    period = _period_from_json(data, path)
    summary = DecisionSummary(
        source_id=source.source_id,
        period=period or 0,
        raw_path=source.relative_path,
    )
    ventas = decisions.get("ventas", {})
    if isinstance(ventas, dict):
        prices = ventas.get("precio_unitario")
        if not isinstance(prices, dict) or not prices:
            prices = ventas.get("precios_venta_unitario")
        summary.prices = _product_values(prices)
        summary.discount_pct = _first_number(
            ventas, "descuento_canal_pct", "descuento_canal_porcentaje"
        )
    produccion = decisions.get("produccion", {})
    if isinstance(produccion, dict):
        units = produccion.get("unidades_producir")
        if not isinstance(units, dict) or not units:
            units = produccion.get("unidades_a_producir")
        summary.production_units = _product_values(units)
        summary.maintenance_pct = _first_number(
            produccion, "mantenimiento_pct", "gasto_mantenimiento_porcentaje"
        )
    projects = decisions.get("otros_proyectos", {})
    if isinstance(projects, dict):
        capex = 0.0
        for project in projects.values():
            if not isinstance(project, dict):
                continue
            if _project_selected(project):
                capex += _project_investment(project)
        summary.capex_selected = capex
    if period is None:
        source.warnings.append(f"No se pudo determinar el periodo de {source.relative_path}")
    return summary


def load_json_source(source: SourceInfo, config: F1Config) -> tuple[list[RawCell], DecisionSummary]:
    path = Path(source.path)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"El JSON de decisiones debe ser un objeto: {path}")

    source.sheets.append("JSON:decisiones")
    cells: list[RawCell] = []
    decisions = data.get("decisiones", data)
    _walk_json(decisions, "decisiones", cells, source)
    return cells, _decision_summary(data, source, path)


def load_markdown_source(source: SourceInfo, config: F1Config) -> list[RawCell]:
    path = Path(source.path)
    text = path.read_text(encoding="utf-8")
    frontmatter, body, warnings = parse_frontmatter(text)
    source.frontmatter = frontmatter or source.frontmatter
    source.captured_at = str(frontmatter.get("captured_at", source.captured_at))
    source.origin_url = str(
        frontmatter.get("source_url", frontmatter.get("origin_url", source.origin_url))
    )
    source.title = str(frontmatter.get("title", source.title or path.stem))
    source.warnings.extend(warnings)
    cells, tables, table_warnings = parse_markdown_tables(
        body,
        source_id=source.source_id,
        source_path=source.relative_path,
    )
    source.markdown_tables.extend(tables)
    source.sheets.extend(table["sheet"] for table in tables)
    source.warnings.extend(table_warnings)
    return cells


def load_sources(
    sources: list[SourceInfo], config: F1Config
) -> tuple[dict[str, list[RawCell]], list[DecisionSummary]]:
    cells_by_source: dict[str, list[RawCell]] = {}
    summaries: list[DecisionSummary] = []
    for source in sources:
        if source.source_type == "excel":
            cells_by_source[source.source_id] = load_excel_source(source, config)
        elif source.source_type == "json":
            cells, summary = load_json_source(source, config)
            cells_by_source[source.source_id] = cells
            summaries.append(summary)
        elif source.source_type == "markdown":
            cells_by_source[source.source_id] = load_markdown_source(source, config)
        else:
            source.warnings.append(f"Tipo de fuente no soportado: {source.source_type}")
    return cells_by_source, summaries
