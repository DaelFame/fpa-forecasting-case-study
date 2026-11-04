from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from .models import SourceInfo
from .text import strip_accents, value_type


LITERAL_SCHEMA_VERSION = "f1.2-literal"


@dataclass
class LiteralCell:
    coordinate: str
    row: int
    column: int
    raw_text: str
    data_type: str
    is_merged: bool
    merged_range: str


@dataclass
class LiteralSheet:
    name: str
    hidden: bool
    dimensions: str
    max_row: int
    max_column: int
    merged_ranges: list[str] = field(default_factory=list)
    cells: list[LiteralCell] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class LiteralWorkbook:
    path: Path
    sheets: list[LiteralSheet]
    warnings: list[str] = field(default_factory=list)

    @property
    def cell_count(self) -> int:
        return sum(len(sheet.cells) for sheet in self.sheets)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _merged_map(sheet: Any) -> dict[str, str]:
    merged: dict[str, str] = {}
    for merged_range in sheet.merged_cells.ranges:
        reference = str(merged_range)
        for row in range(merged_range.min_row, merged_range.max_row + 1):
            for column in range(merged_range.min_col, merged_range.max_col + 1):
                merged[sheet.cell(row, column).coordinate] = reference
    return merged


def read_literal_workbook(path: Path) -> LiteralWorkbook:
    workbook = load_workbook(path, data_only=False, read_only=False)
    sheets: list[LiteralSheet] = []
    workbook_warnings: list[str] = []
    try:
        for sheet in workbook.worksheets:
            merged = _merged_map(sheet)
            hidden = sheet.sheet_state != "visible"
            record = LiteralSheet(
                name=sheet.title,
                hidden=hidden,
                dimensions=str(sheet.dimensions),
                max_row=sheet.max_row,
                max_column=sheet.max_column,
                merged_ranges=sorted(str(item) for item in sheet.merged_cells.ranges),
            )
            for row in sheet.iter_rows(
                min_row=1,
                max_row=sheet.max_row,
                min_col=1,
                max_col=sheet.max_column,
            ):
                for cell in row:
                    value = cell.value
                    if value is None:
                        continue
                    raw_text = str(value)
                    if raw_text.strip() == "":
                        continue
                    if isinstance(value, str) and value.startswith("="):
                        record.warnings.append(
                            f"Celda {cell.coordinate}: fórmula conservada como texto literal, no evaluada."
                        )
                    record.cells.append(
                        LiteralCell(
                            coordinate=cell.coordinate,
                            row=cell.row,
                            column=cell.column,
                            raw_text=raw_text,
                            data_type=value_type(value),
                            is_merged=cell.coordinate in merged,
                            merged_range=merged.get(cell.coordinate, ""),
                        )
                    )
            if not record.cells:
                record.warnings.append("Hoja sin celdas no vacías.")
            sheets.append(record)
    finally:
        workbook.close()
    return LiteralWorkbook(path=path, sheets=sheets, warnings=workbook_warnings)


def _safe_name(value: str) -> str:
    text = strip_accents(value)
    text = re.sub(r"[^0-9A-Za-z._-]+", "_", text).strip("_")
    return text or "hoja"


def sheet_filename(source: SourceInfo, index: int, sheet_name: str) -> str:
    return f"{source.source_id}__H{index:02d}__{_safe_name(sheet_name)}.md"


def _escape_md(text: str) -> str:
    return (
        text.replace("|", "\\|")
        .replace("\r\n", "<br>")
        .replace("\n", "<br>")
        .replace("\r", "<br>")
    )


def _md_row(cell: LiteralCell) -> str:
    merged = "sí" if cell.is_merged else "no"
    return (
        f"| {cell.coordinate} | {cell.row} | {cell.column} | {cell.data_type} | "
        f"{merged} | {cell.merged_range} | {_escape_md(cell.raw_text)} |"
    )


def _render_sheet_markdown(
    source: SourceInfo,
    sheet: LiteralSheet,
    md_file: str,
) -> str:
    lines: list[str] = [
        "---",
        f"source: {json.dumps(source.source_id)}",
        f"source_path: {json.dumps(source.relative_path)}",
        f"sheet: {json.dumps(sheet.name)}",
        f"hidden: {json.dumps(sheet.hidden)}",
        f"dimensions: {json.dumps(sheet.dimensions)}",
        f"generated_at: {json.dumps(datetime.now(timezone.utc).isoformat())}",
        'kind: "literal"',
        "---",
        "",
        f"# {Path(source.relative_path).name} — {sheet.name}",
        "",
        "> **GENERADO — no editar.** Extracción textual literal de celdas. "
        "No interpreta tablas, encabezados, fórmulas ni periodos.",
        "",
        f"- Fuente: `{source.relative_path}`",
        f"- Hoja: `{sheet.name}`",
        f"- Oculta: {'sí' if sheet.hidden else 'no'}",
        f"- Dimensiones: `{sheet.dimensions}`",
        f"- Celdas no vacías: {len(sheet.cells)}",
        f"- Rangos combinados: {', '.join(sheet.merged_ranges) if sheet.merged_ranges else 'ninguno'}",
        "",
        "| Celda | Fila | Col | Tipo | Combinada | Rango combinado | Texto literal |",
        "|---|---:|---:|---|---|---|---|",
    ]
    lines.extend(_md_row(cell) for cell in sheet.cells)
    if sheet.warnings:
        lines.extend(["", "## Advertencias", ""])
        lines.extend(f"- {warning}" for warning in sheet.warnings)
    lines.append("")
    return "\n".join(lines)


def _write_cell_index(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "source",
        "source_path",
        "sheet",
        "cell",
        "row",
        "col",
        "raw_text",
        "data_type",
        "is_merged",
        "merged_range",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def export_excel_to_markdown(
    sources: list[SourceInfo],
    output_dir: Path,
    *,
    project_root: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("*.md"):
        if stale.name != "index.md":
            stale.unlink()
    index_rows: list[dict[str, Any]] = []
    manifest_sources: list[dict[str, Any]] = []
    index_lines: list[str] = [
        "# Markdown literal de hojas Excel",
        "",
        "Un archivo por hoja. Contenido textual literal, sin interpretación.",
        "",
        "| Fuente | Hoja | Oculta | Celdas | Markdown |",
        "|---|---|---|---:|---|",
    ]

    for source in sources:
        if source.source_type != "excel":
            continue
        path = Path(source.path)
        before = source.sha256_before or _sha256_file(path)
        workbook = read_literal_workbook(path)
        after = _sha256_file(path)
        sheet_records: list[dict[str, Any]] = []
        source_index_rows: list[dict[str, Any]] = []
        for index, sheet in enumerate(workbook.sheets, start=1):
            md_name = sheet_filename(source, index, sheet.name)
            md_path = output_dir / md_name
            md_path.write_text(_render_sheet_markdown(source, sheet, md_name), encoding="utf-8")
            for cell in sheet.cells:
                source_index_rows.append(
                    {
                        "source": source.source_id,
                        "source_path": source.relative_path,
                        "sheet": sheet.name,
                        "cell": cell.coordinate,
                        "row": cell.row,
                        "col": cell.column,
                        "raw_text": cell.raw_text,
                        "data_type": cell.data_type,
                        "is_merged": "true" if cell.is_merged else "false",
                        "merged_range": cell.merged_range,
                    }
                )
            sheet_records.append(
                {
                    "name": sheet.name,
                    "hidden": sheet.hidden,
                    "dimensions": sheet.dimensions,
                    "max_row": sheet.max_row,
                    "max_column": sheet.max_column,
                    "merged_ranges": sheet.merged_ranges,
                    "md_file": md_name,
                    "nonempty_cells": len(sheet.cells),
                    "indexed_cells": len(sheet.cells),
                    "missing_cells": 0,
                    "duplicate_cells": 0,
                    "warnings": sheet.warnings,
                }
            )
            index_lines.append(
                f"| `{source.source_id}` | {sheet.name} | {'sí' if sheet.hidden else 'no'} | "
                f"{len(sheet.cells)} | [{md_name}]({md_name}) |"
            )
        index_rows.extend(source_index_rows)
        duplicates = [
            key for key, count in Counter(
                (row["source"], row["sheet"], row["cell"]) for row in source_index_rows
            ).items() if count > 1
        ]
        manifest_sources.append(
            {
                "source": source.source_id,
                "source_path": source.relative_path,
                "sha256_before": before,
                "sha256_after": after,
                "hash_unchanged": before == after,
                "hidden_sheets": [sheet["name"] for sheet in sheet_records if sheet["hidden"]],
                "sheets": sheet_records,
                "nonempty_cells": sum(sheet["nonempty_cells"] for sheet in sheet_records),
                "indexed_cells": len(source_index_rows),
                "missing_cells": 0,
                "duplicate_cells": len(duplicates),
                "warnings": [warning for sheet in sheet_records for warning in sheet["warnings"]],
            }
        )

    _write_cell_index(output_dir / "cell_index.csv", index_rows)
    (output_dir / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    markdown_sources = [source for source in sources if source.source_type == "markdown"]
    manifest = {
        "schema_version": LITERAL_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(output_dir),
        "sources": manifest_sources,
        "captured_sources": [
            {
                "source": source.source_id,
                "source_path": source.relative_path,
                "sha256_before": source.sha256_before,
                "sha256_after": source.sha256_after,
                "hash_unchanged": source.hash_unchanged,
                "tables": len(source.markdown_tables),
                "warnings": list(source.warnings),
            }
            for source in markdown_sources
        ],
        "summary": {
            "workbooks_exported": len(manifest_sources),
            "captured_sources": len(markdown_sources),
            "sheets": sum(len(source["sheets"]) for source in manifest_sources),
            "indexed_cells": len(index_rows),
            "missing_cells": sum(source["missing_cells"] for source in manifest_sources),
            "duplicate_cells": sum(source["duplicate_cells"] for source in manifest_sources),
            "warnings": sum(len(source["warnings"]) for source in manifest_sources)
            + sum(len(source.warnings) for source in markdown_sources),
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_literal_export(
    output_dir: Path,
    sources: list[SourceInfo],
) -> dict[str, Any]:
    manifest_path = output_dir / "manifest.json"
    index_path = output_dir / "cell_index.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No existe el manifiesto Markdown: {manifest_path}")
    if not index_path.exists():
        raise FileNotFoundError(f"No existe cell_index.csv: {index_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with index_path.open("r", encoding="utf-8", newline="") as handle:
        indexed_rows = list(csv.DictReader(handle))

    expected: dict[tuple[str, str, str], str] = {}
    markdown_lines: dict[tuple[str, str], set[str]] = {}
    for source in sources:
        if source.source_type != "excel":
            continue
        workbook = read_literal_workbook(Path(source.path))
        for sheet in workbook.sheets:
            md_name = next(
                (
                    record["md_file"]
                    for source_record in manifest.get("sources", [])
                    if source_record["source"] == source.source_id
                    for record in source_record.get("sheets", [])
                    if record["name"] == sheet.name
                ),
                "",
            )
            if md_name:
                lines = (output_dir / md_name).read_text(encoding="utf-8").splitlines()
                markdown_lines[(source.source_id, sheet.name)] = set(lines)
            for cell in sheet.cells:
                expected[(source.source_id, sheet.name, cell.coordinate)] = cell.raw_text

    actual: dict[tuple[str, str, str], str] = {}
    counts = Counter((row["source"], row["sheet"], row["cell"]) for row in indexed_rows)
    for row in indexed_rows:
        actual[(row["source"], row["sheet"], row["cell"])] = row["raw_text"]

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    mismatches = [
        {"cell": key, "expected": expected[key], "actual": actual[key]}
        for key in sorted(set(expected) & set(actual))
        if expected[key] != actual[key]
    ]

    markdown_missing: list[dict[str, Any]] = []
    for source in sources:
        if source.source_type != "excel":
            continue
        workbook = read_literal_workbook(Path(source.path))
        for sheet in workbook.sheets:
            lines = markdown_lines.get((source.source_id, sheet.name))
            if lines is None:
                markdown_missing.append({"source": source.source_id, "sheet": sheet.name, "cell": ""})
                continue
            for cell in sheet.cells:
                if _md_row(cell) not in lines:
                    markdown_missing.append(
                        {"source": source.source_id, "sheet": sheet.name, "cell": cell.coordinate}
                    )

    return {
        "manifest": manifest,
        "index_rows": len(indexed_rows),
        "expected_cells": len(expected),
        "missing_cells": missing,
        "extra_cells": extra,
        "duplicates": duplicates,
        "text_mismatches": mismatches,
        "markdown_missing": markdown_missing,
        "sources_with_missing_cells": [
            source["source"]
            for source in manifest.get("sources", [])
            if source.get("missing_cells", 0) > 0
        ],
    }
