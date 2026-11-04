from __future__ import annotations

import csv
import json
from pathlib import Path

from openpyxl import Workbook

from cg_01.canonical import canonicalize_sources
from cg_01.config import load_config
from cg_01.excel_to_md import export_excel_to_markdown, verify_literal_export
from cg_01.loader import discover_sources, load_sources, sha256_file
from cg_01.models import SourceInfo


REPO_ROOT = Path(__file__).resolve().parents[1]


def make_config(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return load_config(
        REPO_ROOT / "config" / "f1.toml",
        data_dir=data_dir,
        output_dir=tmp_path / "outputs",
        markdown_dir=tmp_path / "outputs" / "markdown",
        project_root=tmp_path,
    )


def make_source(path: Path, source_id: str = "SRC-XLSX-001") -> SourceInfo:
    return SourceInfo(
        source_id=source_id,
        path=str(path),
        relative_path=str(path.name),
        source_type="excel",
        kind="workbook",
        sha256_before="",
        size_bytes=path.stat().st_size,
    )


def test_literal_export_preserves_text_merges_hidden_sheets_and_formulas(tmp_path: Path) -> None:
    path = tmp_path / "data" / "hoja_arbitraria.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Hoja Rara"
    sheet["A1"] = "Texto | con pipe"
    sheet["B2"] = "Línea 1\nLínea 2"
    sheet["C3"] = 123.5
    sheet["D4"] = "   "
    sheet["A5"] = "Combinada"
    sheet.merge_cells("A5:B6")
    sheet["E7"] = "=SUM(A1:A2)"
    hidden = workbook.create_sheet("Oculta")
    hidden["A1"] = "Dato oculto"
    hidden.sheet_state = "hidden"
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    workbook.close()

    source = make_source(path)
    before = sha256_file(path)
    manifest = export_excel_to_markdown(
        [source],
        tmp_path / "outputs" / "markdown",
        project_root=tmp_path,
    )

    assert manifest["summary"]["workbooks_exported"] == 1
    assert manifest["summary"]["sheets"] == 2
    assert manifest["summary"]["indexed_cells"] == 6
    assert manifest["summary"]["missing_cells"] == 0
    assert manifest["summary"]["duplicate_cells"] == 0
    assert sha256_file(path) == before

    with (tmp_path / "outputs" / "markdown" / "cell_index.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    fieldnames = list(rows[0].keys())
    assert "raw_text" in fieldnames
    assert "value" not in fieldnames
    assert {"source", "sheet", "cell", "row", "col", "data_type", "is_merged", "merged_range"} <= set(
        fieldnames
    )
    assert len(rows) == 6
    by_cell = {(row["sheet"], row["cell"]): row for row in rows}
    assert by_cell[("Hoja Rara", "A1")]["raw_text"] == "Texto | con pipe"
    assert by_cell[("Hoja Rara", "B2")]["raw_text"] == "Línea 1\nLínea 2"
    assert by_cell[("Hoja Rara", "C3")]["data_type"] == "number"
    assert by_cell[("Hoja Rara", "A5")]["is_merged"] == "true"
    assert by_cell[("Hoja Rara", "A5")]["merged_range"] == "A5:B6"
    assert by_cell[("Hoja Rara", "E7")]["raw_text"] == "=SUM(A1:A2)"
    assert by_cell[("Oculta", "A1")]["raw_text"] == "Dato oculto"
    assert ("Hoja Rara", "D4") not in by_cell

    source_manifest = manifest["sources"][0]
    assert source_manifest["hidden_sheets"] == ["Oculta"]
    assert source_manifest["hash_unchanged"] is True
    assert source_manifest["sheets"][1]["hidden"] is True
    assert "A5:B6" in source_manifest["sheets"][0]["merged_ranges"]

    md_files = [
        (tmp_path / "outputs" / "markdown" / sheet_record["md_file"])
        for sheet_record in source_manifest["sheets"]
    ]
    visible_text = md_files[0].read_text(encoding="utf-8")
    assert "Texto \\| con pipe" in visible_text
    assert "Línea 1<br>Línea 2" in visible_text
    assert "=SUM(A1:A2)" in visible_text
    assert "fórmula conservada como texto literal" in visible_text
    assert "GENERADO" in visible_text
    assert "Oculta: sí" in md_files[1].read_text(encoding="utf-8")

    verification = verify_literal_export(
        tmp_path / "outputs" / "markdown",
        [source],
    )
    assert verification["expected_cells"] == 6
    assert verification["missing_cells"] == []
    assert verification["extra_cells"] == []
    assert verification["duplicates"] == []
    assert verification["text_mismatches"] == []
    assert verification["markdown_missing"] == []


def test_captured_markdown_is_discovered_and_normalized_only_with_explicit_period(
    tmp_path: Path,
) -> None:
    config = make_config(tmp_path)
    manual = tmp_path / "data" / "manual"
    manual.mkdir(parents=True)
    (manual / "captura_web.md").write_text(
        """---
title: "Captura web de prueba"
source_url: "https://example.invalid/informe"
captured_at: "2026-10-23"
---

# Tabla anual

| Producto | 2026 | 2025 |
|---|---:|---:|
| Corbatas | 100 | 90 |
| Bufandas | 50 | 40 |

# Tabla sin periodo explícito

| Producto | Valor |
|---|---:|
| Calcetines | 25 |
""",
        encoding="utf-8",
    )

    sources = discover_sources(config.data_dir, config.project_root)
    markdown_sources = [source for source in sources if source.source_type == "markdown"]
    assert len(markdown_sources) == 1
    source = markdown_sources[0]
    assert source.source_id == "SRC-MD-001"
    assert source.kind == "captured"
    assert source.title == "Captura web de prueba"
    assert source.captured_at == "2026-10-23"
    assert source.origin_url == "https://example.invalid/informe"

    before_hash = sha256_file(Path(source.path))
    cells_by_source, summaries = load_sources(sources, config)
    observations = canonicalize_sources(sources, cells_by_source, summaries, config)
    assert sha256_file(Path(source.path)) == before_hash
    markdown_observations = [
        observation for observation in observations if observation.source_id == source.source_id
    ]
    annual = [
        observation for observation in markdown_observations if observation.label_normalized == "corbatas"
    ]
    assert {observation.period for observation in annual} == {"2026", "2025"}
    assert all(observation.data_type == "captured" for observation in markdown_observations)
    assert all(observation.source_type == "markdown" for observation in markdown_observations)
    assert all("table=" in observation.provenance for observation in markdown_observations)

    ambiguous = [
        observation
        for observation in markdown_observations
        if observation.label_normalized == "calcetines"
    ]
    assert len(ambiguous) == 1
    assert ambiguous[0].period == ""
    assert ambiguous[0].integrity_status == "warning"
    assert any("periodo no explícito" in issue for issue in ambiguous[0].issues)

    from cg_01.pipeline import run_pipeline

    result = run_pipeline(config)
    captured = next(
        source for source in result.inventory["sources"] if source["source_type"] == "markdown"
    )
    assert captured["captured_at"] == "2026-10-23"
    assert captured["origin_url"] == "https://example.invalid/informe"
    assert captured["title"] == "Captura web de prueba"
    assert result.markdown["summary"]["captured_sources"] == 1
    assert result.markdown["summary"]["workbooks_exported"] == 0
    assert any(observation.source_type == "markdown" for observation in result.observations)


def test_real_matrices_literal_fidelity() -> None:
    config = load_config(
        REPO_ROOT / "config" / "f1.toml",
        data_dir=REPO_ROOT / "data",
        output_dir=REPO_ROOT / "outputs" / "f1",
        project_root=REPO_ROOT,
    )
    sources = [
        source
        for source in discover_sources(config.data_dir, config.project_root)
        if source.source_type == "excel"
    ]
    assert len(sources) == 4
    before_hashes = {source.source_id: sha256_file(Path(source.path)) for source in sources}
    manifest = export_excel_to_markdown(
        sources,
        REPO_ROOT / "outputs" / "markdown",
        project_root=REPO_ROOT,
    )
    assert manifest["summary"]["workbooks_exported"] == 4
    assert manifest["summary"]["sheets"] == 44
    assert manifest["summary"]["indexed_cells"] == 16_980
    assert manifest["summary"]["missing_cells"] == 0
    assert manifest["summary"]["duplicate_cells"] == 0
    assert {source.source_id: sha256_file(Path(source.path)) for source in sources} == before_hashes

    with (REPO_ROOT / "outputs" / "markdown" / "cell_index.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0].keys())[:10] == [
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
    assert len(rows) == 16_980
    counts = {}
    for row in rows:
        counts[(row["source"], row["sheet"])] = counts.get((row["source"], row["sheet"]), 0) + 1
    assert sum(counts.values()) == 16_980
    assert all(count > 0 for count in counts.values())

    verification = verify_literal_export(REPO_ROOT / "outputs" / "markdown", sources)
    assert verification["expected_cells"] == 16_980
    assert verification["missing_cells"] == []
    assert verification["extra_cells"] == []
    assert verification["duplicates"] == []
    assert verification["text_mismatches"] == []
    assert verification["markdown_missing"] == []


def test_pipeline_integrates_literal_markdown_and_explains_json_difference(tmp_path: Path) -> None:
    from cg_01.pipeline import run_pipeline

    config = load_config(
        REPO_ROOT / "config" / "f1.toml",
        data_dir=REPO_ROOT / "data",
        output_dir=tmp_path / "outputs",
        markdown_dir=tmp_path / "outputs" / "markdown",
        project_root=REPO_ROOT,
    )
    result = run_pipeline(config)
    manifest_path = tmp_path / "outputs" / "markdown" / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["summary"] == result.markdown["summary"]
    assert result.markdown["summary"]["workbooks_exported"] == 4
    assert result.markdown["summary"]["sheets"] == 44
    assert result.markdown["summary"]["indexed_cells"] == 16_980
    assert result.markdown["summary"]["missing_cells"] == 0
    assert result.inventory["summary"]["raw_cell_count"] == 17_218
    assert result.inventory["summary"]["observations_by_source_type"]["json"] == 238
    assert result.inventory["summary"]["raw_cell_count"] - result.markdown["summary"]["indexed_cells"] == 238

    skipped = run_pipeline(config, export_markdown=False)
    assert skipped.markdown["summary"]["workbooks_exported"] == 0
    assert skipped.markdown["summary"]["indexed_cells"] == 0
