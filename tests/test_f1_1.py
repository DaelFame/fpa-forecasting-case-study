from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from openpyxl import Workbook

from cg_01.canonical import (
    canonicalize_sources,
    detect_period_blocks,
    extract_excel_observations,
)
from cg_01.config import load_config
from cg_01.loader import discover_sources, load_excel_source, load_json_source, load_sources
from cg_01.models import RawCell, SourceInfo
from cg_01.pipeline import run_pipeline
from cg_01.validation import validate_observations


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


def make_workbook(path: Path, sheets: dict[str, dict[str, object]]) -> None:
    workbook = Workbook()
    default = workbook.active
    workbook.remove(default)
    for sheet_name, values in sheets.items():
        sheet = workbook.create_sheet(sheet_name)
        for coordinate, value in values.items():
            sheet[coordinate] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    workbook.close()


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


def test_period_detection_annual_quarter_and_traceability(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    path = tmp_path / "data" / "matrix.xlsx"
    make_workbook(
        path,
        {
            "Produccion": {
                "A1": "Análisis de producción con título largo",
                "B4": 2026,
                "C4": 2025,
                "A5": "Total Unid. Producidas",
                "B5": 210000,
                "C5": 195000,
                "A7": "Unidades producidas por trimestre",
                "B7": 2026,
                "F7": 2025,
                "B8": "1er Trim",
                "C8": "2do Trim",
                "D8": "3er Trim",
                "E8": "4to Trim",
                "F8": "1er Trim",
                "G8": "2do Trim",
                "H8": "3er Trim",
                "I8": "4to Trim",
                "A9": "Corbatas",
                "B9": 52500,
                "C9": 52500,
                "D9": 52500,
                "E9": 52500,
                "F9": 48750,
                "G9": 48750,
                "H9": 48750,
                "I9": 48750,
            }
        },
    )
    source = make_source(path)
    cells = load_excel_source(source, config)
    blocks = detect_period_blocks(cells, config)
    assert [block.header_row for block in blocks] == [4, 7]

    observations, _ = extract_excel_observations(source, cells, config, 1)
    annual = next(obs for obs in observations if obs.cell == "B5")
    quarter = next(obs for obs in observations if obs.cell == "B9")
    assert annual.period == "2026"
    assert annual.label_raw == "Total Unid. Producidas"
    assert annual.source_row == 5
    assert annual.source_column == 2
    assert annual.provenance.startswith("source=matrix.xlsx")
    assert quarter.period == "2026-Q1"
    assert quarter.segment == "1er Trim"
    assert quarter.value == 52500


def test_balance_identity_is_flagged_as_critical(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    path = tmp_path / "data" / "balance.xlsx"
    make_workbook(
        path,
        {
            "Balance": {
                "B4": 2026,
                "C4": 2025,
                "A5": "Total Activo",
                "B5": 100,
                "A6": "Total No Corriente",
                "B6": 60,
                "A7": "Total Corriente",
                "B7": 40,
                "A8": "Total Pasivo",
                "B8": 40,
                "A9": "Total Pasivo Corriente",
                "B9": 40,
                "A10": "Préstamo Largo Plazo",
                "B10": 0,
                "A11": "Crédito Extraordinario",
                "B11": 0,
                "A12": "Patrimonio Neto",
                "B12": 50,
                "A13": "Capital",
                "B13": 40,
                "A14": "Reservas",
                "B14": 5,
                "A15": "Resultado Desp. Impuestos",
                "B15": 5,
                "A16": "Total Pasivo + Patrimonio Neto",
                "B16": 90,
            }
        },
    )
    source = make_source(path)
    cells = load_excel_source(source, config)
    observations, _ = extract_excel_observations(source, cells, config, 1)
    anomalies = validate_observations(observations, [], [source], {source.source_id: cells}, config)

    balance = [anomaly for anomaly in anomalies if anomaly.rule_id == "BAL-ASSETS-LIAB-EQUITY"]
    assert len(balance) == 1
    assert balance[0].severity == "critical"
    total_asset = next(obs for obs in observations if obs.cell == "B5")
    total_liab_equity = next(obs for obs in observations if obs.cell == "B16")
    assert total_asset.financial_status == "invalid"
    assert total_liab_equity.financial_status == "invalid"


def test_scale_mismatch_and_duplicate_preservation(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    path = tmp_path / "data" / "ingresos.xlsx"
    make_workbook(
        path,
        {
            "Ingresos": {
                "B4": 2026,
                "C4": 2025,
                "A5": "Total",
                "B5": 1000000,
                "C5": 900000,
                "A6": "Total productos",
                "B6": 10000,
                "C6": 9000,
                "A9": "Total productos",
                "B9": 1000000,
                "C9": 900000,
            }
        },
    )
    source = make_source(path)
    cells = load_excel_source(source, config)
    observations, _ = extract_excel_observations(source, cells, config, 1)
    anomalies = validate_observations(observations, [], [source], {source.source_id: cells}, config)

    assert any(anomaly.rule_id == "SCALE-100" for anomaly in anomalies)
    smaller = next(obs for obs in observations if obs.cell == "B6")
    assert smaller.value == 10000
    assert smaller.normalized_value == 1000000
    assert smaller.normalization_status == "pending_scale_confirmation"
    duplicated = [obs for obs in observations if obs.period == "2026" and obs.cell in {"B5", "B9"}]
    assert len(duplicated) == 2
    assert len({obs.cell for obs in duplicated}) == 2



def test_occupancy_penalty_mode_selects_line_or_plant(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    path = tmp_path / "data" / "ocupacion.xlsx"
    make_workbook(
        path,
        {
            "Produccion": {
                "B4": 2026,
                "C4": 2025,
                "B5": "Corbatas",
                "C5": "Bufandas",
                "A6": "Porcentaje de ocupación fábrica",
                "B6": 0.50,
                "C6": 0.90,
            },
            "Indicadores Clave": {
                "B4": 2026,
                "C4": 2025,
                "A5": "Tasa ocupa. fábricas Pct.",
                "B5": 0.50,
                "C5": 0.90,
            },
        },
    )
    source = make_source(path)
    cells = load_excel_source(source, config)
    observations, _ = extract_excel_observations(source, cells, config, 1)

    assert config.occupancy_penalty_mode == "plant"
    assert config.occupancy_cost_mode == "line"

    plant_anomalies = validate_observations(
        observations, [], [source], {source.source_id: cells}, config
    )
    plant_occupancy = [
        anomaly for anomaly in plant_anomalies if anomaly.rule_id == "OCCUPANCY-MIN"
    ]
    assert len(plant_occupancy) == 1
    assert plant_occupancy[0].sheet == "Indicadores Clave"
    assert plant_occupancy[0].cell == "B5"

    line_anomalies = validate_observations(
        observations,
        [],
        [source],
        {source.source_id: cells},
        replace(config, occupancy_penalty_mode="line"),
    )
    line_occupancy = [
        anomaly for anomaly in line_anomalies if anomaly.rule_id == "OCCUPANCY-MIN"
    ]
    assert len(line_occupancy) == 1
    assert line_occupancy[0].sheet == "Produccion"
    assert line_occupancy[0].cell == "B6"


def test_current_liabilities_identity_flags_missing_components(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    path = tmp_path / "data" / "pasivo.xlsx"
    make_workbook(
        path,
        {
            "Balance": {
                "B4": 2026,
                "C4": 2025,
                "A5": "Total Activo",
                "B5": 1000,
                "A6": "Total No Corriente",
                "B6": 600,
                "A7": "Total Corriente",
                "B7": 400,
                "A8": "Total Pasivo",
                "B8": 400,
                "A9": "Total Pasivo Corriente",
                "B9": 400,
                "A10": "Préstamo Corto Plazo",
                "B10": 100,
                "A11": "Crédito Extraordinario",
                "B11": 0,
                "A12": "Proveedores",
                "B12": 200,
                "A13": "Patrimonio Neto",
                "B13": 600,
                "A14": "Capital",
                "B14": 600,
                "A15": "Reservas",
                "B15": 0,
                "A16": "Resultado Desp. Impuestos",
                "B16": 0,
                "A17": "Total Pasivo + Patrimonio Neto",
                "B17": 1000,
            }
        },
    )
    source = make_source(path)
    cells = load_excel_source(source, config)
    observations, _ = extract_excel_observations(source, cells, config, 1)
    anomalies = validate_observations(
        observations, [], [source], {source.source_id: cells}, config
    )
    current = [
        anomaly for anomaly in anomalies if anomaly.rule_id == "BAL-CURRENT-LIABILITIES"
    ]
    assert len(current) == 1
    assert current[0].cell == "B9"
    assert current[0].difference == "100"

def test_alias_variants_ignore_case_but_flag_accents() -> None:
    config = load_config(REPO_ROOT / "config" / "f1.toml", project_root=REPO_ROOT)
    cells = [
        RawCell("S", "m.xlsx", "Produccion", 1, 1, "A1", "Economica", "string"),
        RawCell("S", "m.xlsx", "Produccion", 2, 1, "A2", "Económica", "string"),
        RawCell("S", "m.xlsx", "Produccion", 3, 1, "A3", "Total", "string"),
        RawCell("S", "m.xlsx", "Produccion", 4, 1, "A4", "TOTAL", "string"),
    ]
    anomalies = validate_observations([], [], [], {"S": cells}, config)
    alias = [anomaly for anomaly in anomalies if anomaly.rule_id == "ALIAS-TEXT"]
    assert len(alias) == 1
    assert "economica" in alias[0].observed.casefold()


def test_price_corridor_on_json_decisions(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    decisions = tmp_path / "data" / "decisiones"
    decisions.mkdir(parents=True)
    for year, price in ((2026, 10.0), (2027, 12.0)):
        (decisions / f"Bitacora_decisiones_para_{year}.json").write_text(
            json.dumps(
                {
                    "periodo": year,
                    "decisiones": {
                        "ventas": {"precio_unitario": {"corbatas": price}},
                        "produccion": {"unidades_producir": {"corbatas": 0}},
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    sources = discover_sources(config.data_dir, config.project_root)
    cells_by_source, summaries = load_sources(sources, config)
    observations = canonicalize_sources(sources, cells_by_source, summaries, config)
    anomalies = validate_observations(observations, summaries, sources, cells_by_source, config)
    assert any(anomaly.rule_id == "PRICE-CORRIDOR" for anomaly in anomalies)
    assert any(anomaly.rule_id == "PROD-ZERO-KEEP" for anomaly in anomalies)
    price_2027 = next(obs for obs in observations if obs.year == 2027 and "precio_unitario" in obs.metric)
    assert price_2027.unit == "EUR_per_unit"
    assert price_2027.financial_status == "warning"


@pytest.mark.skipif(not (REPO_ROOT / "data" / "Matriz_General_1.xlsx").exists(), reason="datos reales no disponibles")
def test_real_pipeline_generates_four_outputs(tmp_path: Path) -> None:
    config = load_config(
        REPO_ROOT / "config" / "f1.toml",
        data_dir=REPO_ROOT / "data",
        output_dir=tmp_path / "outputs",
        markdown_dir=tmp_path / "outputs" / "markdown",
        project_root=REPO_ROOT,
    )
    result = run_pipeline(config)

    for name in ("inventory.json", "canonical_points.csv", "anomalies.csv", "report.md"):
        assert (tmp_path / "outputs" / name).exists()
    assert (tmp_path / "outputs" / "markdown" / "manifest.json").exists()
    assert result.markdown["summary"]["workbooks_exported"] == 4

    assert len(result.sources) == 7
    assert result.inventory["summary"]["all_hashes_unchanged"] is True
    assert result.inventory["summary"]["latest_real_year"] == 2028
    assert result.inventory["summary"]["latest_decision_year"] == 2028
    assert result.observations
    assert result.anomalies
    assert any(obs.data_type == "decision" and obs.year == 2027 for obs in result.observations)
    assert any(obs.data_type == "real" and obs.year == 2027 for obs in result.observations)
    assert any(obs.data_type == "budget" and obs.year == 2026 for obs in result.observations)
    assert any(obs.data_type == "budget" and obs.year == 2027 for obs in result.observations)
    assert any(
        obs.data_type == "budget"
        and obs.year == 2026
        and obs.label_normalized == "resultado neto"
        and obs.value == 398088
        for obs in result.observations
    )
    assert any(
        anomaly.rule_id == "BAL-ASSETS-EQUATION"
        and anomaly.sheet == "Indicadores Clave"
        and anomaly.period == "2026"
        and anomaly.severity == "critical"
        for anomaly in result.anomalies
    )
    assert all(obs.financial_status != "" for obs in result.observations)
