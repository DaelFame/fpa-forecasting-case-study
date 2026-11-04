from __future__ import annotations

import re
from typing import Any

from .models import RawCell


_NUMERIC_RE = re.compile(r"^-?(?:\d+|\d{1,3}(?:\.\d{3})+|\d+[.,]\d+)(?:[.,]\d+)?$")
_SEPARATOR_CELL_RE = re.compile(r"^:?-{3,}:?$")


def _nearest_title(lines: list[str], index: int) -> str:
    for line in reversed(lines[max(0, index - 4) : index]):
        text = line.strip()
        if not text:
            continue
        if "|" in text:
            break
        return text.lstrip("#").strip()
    return ""


def _split_md_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for character in text:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    cells.append("".join(current).strip())
    return cells


def _is_table_line(line: str) -> bool:
    return "|" in line and bool(line.strip())


def _is_separator_line(line: str) -> bool:
    if "|" not in line:
        return False
    cells = _split_md_row(line)
    return bool(cells) and all(_SEPARATOR_CELL_RE.match(cell.replace(" ", "")) for cell in cells)


def _parse_captured_number(text: str) -> tuple[Any, str]:
    value = text.strip()
    if not value or not _NUMERIC_RE.match(value):
        return text, "string" if text else "empty"
    if re.fullmatch(r"-?\d+", value):
        return int(value), "number"
    if re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+(?:,\d+)?", value):
        normalized = value.replace(".", "").replace(",", ".")
        return float(normalized), "number"
    normalized = value.replace(",", ".")
    try:
        return float(normalized), "number"
    except ValueError:
        return text, "string"


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, []
    end: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return {}, text, ["Frontmatter Markdown sin delimitador de cierre; se conserva el texto completo."]
    metadata: dict[str, Any] = {}
    warnings: list[str] = []
    for line_number, line in enumerate(lines[1:end], start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            warnings.append(f"Frontmatter línea {line_number}: se ignora una entrada sin ':'.")
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not key:
            warnings.append(f"Frontmatter línea {line_number}: clave vacía.")
            continue
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if value.startswith("[") and value.endswith("]"):
            metadata[key] = [
                item.strip().strip('"').strip("'")
                for item in value[1:-1].split(",")
                if item.strip()
            ]
        elif value.casefold() in {"true", "false"}:
            metadata[key] = value.casefold() == "true"
        else:
            metadata[key] = value
    body = "\n".join(lines[end + 1 :])
    return metadata, body, warnings


def parse_markdown_tables(
    body: str,
    *,
    source_id: str,
    source_path: str,
) -> tuple[list[RawCell], list[dict[str, Any]], list[str]]:
    lines = body.splitlines()
    cells: list[RawCell] = []
    tables: list[dict[str, Any]] = []
    warnings: list[str] = []
    index = 0
    table_index = 0
    while index < len(lines) - 1:
        if not (_is_table_line(lines[index]) and _is_separator_line(lines[index + 1])):
            index += 1
            continue
        header = _split_md_row(lines[index])
        separator = _split_md_row(lines[index + 1])
        table_index += 1
        sheet = f"MD:T{table_index:02d}"
        title = _nearest_title(lines, index)
        table_warnings: list[str] = []
        if len(header) != len(separator):
            table_warnings.append(
                f"Tabla {table_index}: encabezado y separador tienen distinto número de columnas."
            )
        if not any(header):
            table_warnings.append(f"Tabla {table_index}: encabezado vacío; estructura ambigua.")
        data_rows: list[list[str]] = []
        cursor = index + 2
        while cursor < len(lines) and _is_table_line(lines[cursor]) and not _is_separator_line(lines[cursor]):
            data_rows.append(_split_md_row(lines[cursor]))
            cursor += 1
        if not data_rows:
            table_warnings.append(f"Tabla {table_index}: sin filas de datos.")
        for column, value in enumerate(header, start=1):
            text = value.strip()
            if not text:
                continue
            parsed, parsed_type = _parse_captured_number(text)
            cells.append(
                RawCell(
                    source_id=source_id,
                    source_path=source_path,
                    sheet=sheet,
                    row=1,
                    column=column,
                    coordinate=f"T{table_index:02d}R01C{column:02d}",
                    value=parsed,
                    value_type=parsed_type,
                    raw_text=text,
                    number_format="markdown",
                )
            )
        for row_number, row in enumerate(data_rows, start=2):
            for column, value in enumerate(row, start=1):
                text = value.strip()
                if not text:
                    continue
                parsed, parsed_type = _parse_captured_number(text)
                cells.append(
                    RawCell(
                        source_id=source_id,
                        source_path=source_path,
                        sheet=sheet,
                        row=row_number,
                        column=column,
                        coordinate=f"T{table_index:02d}R{row_number:02d}C{column:02d}",
                        value=parsed,
                        value_type=parsed_type,
                        raw_text=text,
                        number_format="markdown",
                    )
                )
        tables.append(
            {
                "index": table_index,
                "sheet": sheet,
                "title": title,
                "headers": header,
                "header_rows": [1],
                "data_start": 2,
                "row_count": len(data_rows),
                "warnings": table_warnings,
            }
        )
        warnings.extend(table_warnings)
        index = cursor
    if not tables:
        warnings.append("No se detectaron tablas Markdown con formato de tuberías.")
    return cells, tables, warnings
