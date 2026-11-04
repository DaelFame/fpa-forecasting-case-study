from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from cg_01.config import load_config
from cg_01.loader import discover_sources, load_sources
from cg_01.pipeline import run_pipeline


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_DATA = REPO_ROOT / "data" / "Matriz_General_1.xlsx"


def real_config(output_dir: Path):
    return load_config(
        REPO_ROOT / "config" / "f1.toml",
        data_dir=REPO_ROOT / "data",
        output_dir=output_dir,
        markdown_dir=output_dir.parent / "markdown",
        project_root=REPO_ROOT,
    )


@pytest.fixture(scope="module")
def real_result(tmp_path_factory):
    if not REAL_DATA.exists():
        pytest.skip("datos reales no disponibles")
    output_dir = tmp_path_factory.mktemp("f1-audit") / "outputs"
    return run_pipeline(real_config(output_dir))


def test_real_outputs_are_traceable_to_raw_sources(real_result) -> None:
    observations = real_result.observations
    assert len(observations) == 8708
    assert len({observation.observation_id for observation in observations}) == 8708
    assert len(
        {
            (observation.source_id, observation.sheet, observation.cell, observation.period)
            for observation in observations
        }
    ) == 8708
    assert Counter(observation.source_id for observation in observations) == {
        "SRC-XLSX-001": 1448,
        "SRC-XLSX-002": 1812,
        "SRC-XLSX-003": 2397,
        "SRC-XLSX-004": 2813,
        "SRC-JSON-001": 109,
        "SRC-JSON-002": 69,
        "SRC-JSON-003": 60,
    }

    sources = discover_sources(real_result.config.data_dir, real_result.config.project_root)
    cells_by_source, _ = load_sources(sources, real_result.config)
    raw = {
        (cell.source_id, cell.sheet, cell.coordinate): cell.value
        for cells in cells_by_source.values()
        for cell in cells
    }
    for observation in observations:
        assert observation.provenance
        assert raw[(observation.source_id, observation.sheet, observation.cell)] == observation.value


def test_inventory_periods_match_observations(real_result) -> None:
    for source in real_result.inventory["sources"]:
        observed = {
            observation.period
            for observation in real_result.observations
            if observation.source_id == source["source_id"]
        }
        assert sorted(observed) == sorted(source["periods"])


def test_budget_year_is_inferred_from_previous_block(real_result) -> None:
    budget = [
        observation
        for observation in real_result.observations
        if observation.data_type == "budget"
    ]
    assert len(budget) == 111
    assert {observation.year for observation in budget} == {2026, 2027, 2028}
    assert any(
        observation.source_id == "SRC-XLSX-002"
        and observation.sheet == "Indicadores Clave"
        and observation.cell == "C72"
        and observation.numeric_value == 398088
        for observation in budget
    )


def test_2027_decisions_coexist_with_the_2027_close_and_budget(real_result) -> None:
    observations_2027 = [
        observation
        for observation in real_result.observations
        if observation.year == 2027
    ]
    decisions = [
        observation
        for observation in observations_2027
        if observation.data_type == "decision"
    ]
    assert len(decisions) == 69
    assert {observation.source_type for observation in decisions} == {"json"}
    assert any(
        observation.data_type == "real" and observation.source_id == "SRC-XLSX-003"
        for observation in observations_2027
    )
    assert any(
        observation.data_type == "budget" and observation.source_id == "SRC-XLSX-003"
        for observation in observations_2027
    )
    assert real_result.inventory["summary"]["latest_real_year"] == 2028
    assert real_result.inventory["summary"]["latest_decision_year"] == 2028


def test_pipeline_is_byte_reproducible_without_duplicate_observations(tmp_path: Path) -> None:
    first = run_pipeline(real_config(tmp_path / "first"))
    second = run_pipeline(real_config(tmp_path / "second"))

    for name in ("canonical_points.csv", "anomalies.csv"):
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()

    first_ids = [observation.observation_id for observation in first.observations]
    second_ids = [observation.observation_id for observation in second.observations]
    assert first_ids == second_ids
    assert len(first_ids) == len(set(first_ids))
    canonical = (tmp_path / "first" / "canonical_points.csv").read_text(encoding="utf-8")
    assert len(canonical.splitlines()) == len(first_ids) + 1
    assert first.inventory["summary"]["all_hashes_unchanged"] is True
    assert second.inventory["summary"]["all_hashes_unchanged"] is True


def test_macro_anio_mas_dos_is_canonicalized(real_result) -> None:
    present = {
        (observation.source_id, observation.sheet, observation.cell)
        for observation in real_result.observations
    }
    expected = {
        ("SRC-XLSX-001", "Indicadores_Clave", f"E{row}") for row in range(50, 54)
    } | {
        ("SRC-XLSX-002", "Indicadores Clave", f"E{row}") for row in range(106, 110)
    }
    assert expected <= present
    first = next(
        observation
        for observation in real_result.observations
        if observation.source_id == "SRC-XLSX-001" and observation.cell == "E50"
    )
    assert first.period == "2028"
    assert first.data_type == "scenario"
    second = next(
        observation
        for observation in real_result.observations
        if observation.source_id == "SRC-XLSX-002" and observation.cell == "E106"
    )
    assert second.period == "2029"
    assert second.data_type == "scenario"


def test_quarterly_total_debt_is_extracted(real_result) -> None:
    present = {
        (observation.source_id, observation.sheet, observation.cell)
        for observation in real_result.observations
    }
    expected = {
        ("SRC-XLSX-001", "Balance", f"{column}137") for column in "BCDE"
    } | {
        ("SRC-XLSX-002", "Analisis de Balance", f"{column}182") for column in "BCDE"
    }
    assert expected <= present
    debt = next(
        observation
        for observation in real_result.observations
        if observation.source_id == "SRC-XLSX-001" and observation.cell == "B137"
    )
    assert debt.period == "2025-Q1"
    assert debt.numeric_value == 1712577.0


def test_quarterly_current_liabilities_are_flagged(real_result) -> None:
    assert any(
        anomaly.sheet == "Analisis de Balance"
        and anomaly.cell in {f"{column}88" for column in "BCDE"}
        for anomaly in real_result.anomalies
    )
    assert any(
        anomaly.source_id == "SRC-XLSX-003"
        and anomaly.sheet == "Balance"
        and anomaly.cell in {f"{column}87" for column in "BCDE"}
        for anomaly in real_result.anomalies
    )


def test_source_overlap_reports_known_2025_discrepancies(real_result) -> None:
    from cg_01.analysis import source_overlap

    overlap = source_overlap(
        real_result.observations,
        "SRC-XLSX-002",
        "SRC-XLSX-003",
    )
    assert not overlap.empty
    assert {"reservas", "total corriente"} <= set(overlap["label"])
    assert set(overlap["period"]) == {"2025"}
