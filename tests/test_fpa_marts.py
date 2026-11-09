from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cg_01.config import load_config
from cg_01.f2_engine import load_f2_config, run_f2
from cg_01.fpa.marts import build_marts


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data"
CLOSED_YEARS = {
    str(year)
    for year in load_f2_config(
        REPO_ROOT / "config" / "f2.toml", project_root=REPO_ROOT
    ).periods
}
BUDGET_YEARS = {
    path.stem[-4:] for path in (DATA_ROOT / "decisiones").glob("*.json")
}

DIMENSIONS = {
    "dim_period.csv": "period_key",
    "dim_product.csv": "product_key",
    "dim_line_item.csv": "line_item_key",
    "dim_account.csv": "account_key",
    "dim_scenario.csv": "scenario_key",
    "dim_status.csv": "status_key",
    "dim_regime.csv": "regime_key",
    "dim_fold.csv": "fold_key",
    "dim_driver.csv": "driver_key",
}

FOREIGN_KEYS = {
    "fact_financials.csv": [
        ("period_key", "dim_period.csv"),
        ("line_item_key", "dim_line_item.csv"),
        ("scenario_key", "dim_scenario.csv"),
        ("status_key", "dim_status.csv"),
    ],
    "fact_balance.csv": [
        ("period_key", "dim_period.csv"),
        ("account_key", "dim_account.csv"),
        ("status_key", "dim_status.csv"),
    ],
    "fact_sales.csv": [
        ("period_key", "dim_period.csv"),
        ("product_key", "dim_product.csv"),
    ],
    "fact_product_annual.csv": [
        ("period_key", "dim_period.csv"),
        ("product_key", "dim_product.csv"),
    ],
}


def _load(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def marts(tmp_path_factory) -> tuple[Path, dict[str, int]]:
    output_root = tmp_path_factory.mktemp("marts")
    f1_config = load_config(
        REPO_ROOT / "config" / "f1.toml",
        data_dir=REPO_ROOT / "data",
        output_dir=output_root / "f1",
        markdown_dir=output_root / "markdown",
        project_root=REPO_ROOT,
    )
    f2_config = load_f2_config(
        REPO_ROOT / "config" / "f2.toml",
        output_dir=output_root / "f2",
        project_root=REPO_ROOT,
    )
    result = run_f2(f1_config, f2_config)
    target = output_root / "processed"
    return target, build_marts(result, target)


def test_every_table_is_written(marts) -> None:
    target, counts = marts
    for name in list(DIMENSIONS) + list(FOREIGN_KEYS):
        assert (target / name).exists(), name
        assert counts[name] > 0, name


def test_no_foreign_key_is_orphan(marts) -> None:
    target, _ = marts
    dimension_keys = {
        name: {row[key] for row in _load(target / name)}
        for name, key in DIMENSIONS.items()
    }
    for fact, relations in FOREIGN_KEYS.items():
        rows = _load(target / fact)
        for column, dimension in relations:
            orphans = {row[column] for row in rows} - dimension_keys[dimension]
            assert not orphans, f"{fact}.{column} referencia {dimension}: {orphans}"


def test_no_key_or_measure_is_empty(marts) -> None:
    target, _ = marts
    for fact in FOREIGN_KEYS:
        for row in _load(target / fact):
            for column, value in row.items():
                assert value != "", f"{fact}.{column} vacío"


def test_financials_cover_every_year_in_both_scenarios(marts) -> None:
    target, _ = marts
    rows = _load(target / "fact_financials.csv")
    actual_years = {row["period_key"] for row in rows if row["scenario_key"] == "actual"}
    budget_years = {row["period_key"] for row in rows if row["scenario_key"] == "budget"}
    assert actual_years == CLOSED_YEARS
    assert budget_years == BUDGET_YEARS


def test_sales_fact_is_quarterly_by_product(marts) -> None:
    target, _ = marts
    rows = _load(target / "fact_sales.csv")
    periods = {row["period_key"] for row in rows}
    assert len(periods) % 4 == 0
    assert len(rows) == 3 * len(periods)
    assert all("-Q" in period for period in periods)
    assert {row["product_key"] for row in rows} == {"corbatas", "bufandas", "calcetines"}


def test_sales_fact_keeps_its_grain_when_units_are_annual_only(marts) -> None:
    target, _ = marts
    sales = _load(target / "fact_sales.csv")
    annual = _load(target / "fact_product_annual.csv")
    assert not any(row["period_key"].startswith("2029") for row in sales)
    assert any(row["period_key"] == "2029" for row in annual)
    assert all(row["units_sold"] and row["revenue"] for row in sales)


def test_period_dimension_keeps_gauges_separate(marts) -> None:
    target, _ = marts
    rows = _load(target / "dim_period.csv")
    annual = {row["period_key"] for row in rows if row["grain"] == "year"}
    quarterly = {row["period_key"] for row in rows if row["grain"] == "quarter"}
    sales_periods = {row["period_key"] for row in _load(target / "fact_sales.csv")}
    assert annual == CLOSED_YEARS
    assert quarterly == sales_periods
    assert not annual & quarterly
