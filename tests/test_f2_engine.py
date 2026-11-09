from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from cg_01.config import load_config
from cg_01.f2_engine import load_f2_config, run_f2
from cg_01.f2_report import write_f2_outputs
from cg_01.loader import sha256_file


REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_STATUSES = {
    "confirmed",
    "inferred_accepted",
    "pending",
    "accepted_exception",
    "unreconciled",
}


@pytest.fixture(scope="module")
def f2_result(tmp_path_factory):
    output_root = tmp_path_factory.mktemp("f2")
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
    return run_f2(f1_config, f2_config)


def row(result, section: str, metric: str, period: int):
    return next(
        item
        for item in result.rows
        if item.section == section and item.metric == metric and item.period == period
    )


def test_income_statement_reconciles_2026_and_2027(f2_result) -> None:
    assert row(f2_result, "income_statement", "revenue_total", 2026).value == 3_861_039
    assert row(f2_result, "income_statement", "cost_of_sales_total", 2026).value == 2_048_743
    assert row(f2_result, "income_statement", "gross_profit", 2026).value == 1_812_296
    assert row(f2_result, "income_statement", "net_result_after_taxes", 2026).value == 154_951
    assert row(f2_result, "income_statement", "revenue_total", 2027).value == 4_304_333
    assert row(f2_result, "income_statement", "cost_of_sales_total", 2027).value == 2_098_663
    assert row(f2_result, "income_statement", "gross_profit", 2027).value == 2_205_670
    assert row(f2_result, "income_statement", "net_result_after_taxes", 2027).value == 557_448

    assert row(f2_result, "reconciliation", "revenue_products_vs_total", 2026).value == 0
    assert row(f2_result, "reconciliation", "cost_products_vs_total", 2026).value == 1
    assert row(f2_result, "reconciliation", "revenue_products_vs_total", 2027).value == 0
    assert row(f2_result, "reconciliation", "cost_products_vs_total", 2027).value == -1
    assert row(f2_result, "reconciliation", "cost_products_vs_total", 2026).reconciliation_status == "documented_residual"
    assert row(f2_result, "reconciliation", "cost_products_vs_total", 2027).reconciliation_status == "documented_residual"


def test_balance_detailed_identity_and_unreconciled_status(f2_result) -> None:
    assert row(f2_result, "balance", "total_assets", 2026).value == 5_335_431
    assert row(f2_result, "balance", "total_liabilities", 2026).value == 1_447_132
    assert row(f2_result, "balance", "reserves", 2026).value == 930_663
    assert row(f2_result, "balance", "detailed_equity", 2026).value == 3_888_300
    assert row(f2_result, "balance", "balance_detail_residual", 2026).value == -1
    assert row(f2_result, "balance", "balance_reported_residual", 2026).value == -246_391

    assert row(f2_result, "balance", "total_assets", 2027).value == 5_665_584
    assert row(f2_result, "balance", "total_liabilities", 2027).value == 1_219_836
    assert row(f2_result, "balance", "reserves", 2027).value == 1_085_613
    assert row(f2_result, "balance", "detailed_equity", 2027).value == 4_445_747
    assert row(f2_result, "balance", "balance_detail_residual", 2027).value == 1
    assert row(f2_result, "balance", "balance_reported_residual", 2027).value == -246_390

    for period in (2026, 2027):
        assert row(f2_result, "balance", "total_assets", period).status == "unreconciled"
        assert row(f2_result, "balance", "detailed_equity", period).status == "unreconciled"
        assert row(f2_result, "balance", "current_ratio", period).status == "unreconciled"
        assert row(f2_result, "balance", "working_capital", period).status == "unreconciled"
        detail = row(f2_result, "reconciliation", "balance_detail_identity", period)
        assert detail.status == "unreconciled"
        assert detail.reconciliation_status == "documented_residual"
        assert abs(detail.value) <= 1.0


def test_debt_structure_includes_current_portion_of_long_term_debt(f2_result) -> None:
    assert row(f2_result, "debt", "long_term_debt", 2026).value == 927_406
    assert row(f2_result, "debt", "short_term_debt_direct", 2026).value == 0
    assert row(f2_result, "debt", "current_portion_long_term_debt", 2026).value == 297_748
    assert row(f2_result, "debt", "total_debt", 2026).value == 1_225_154
    assert row(f2_result, "debt", "long_term_debt", 2027).value == 619_995
    assert row(f2_result, "debt", "short_term_debt_direct", 2027).value == 0
    assert row(f2_result, "debt", "current_portion_long_term_debt", 2027).value == 313_036
    assert row(f2_result, "debt", "total_debt", 2027).value == 933_031
    assert row(f2_result, "reconciliation", "debt_total_check", 2026).value == 0
    assert row(f2_result, "reconciliation", "debt_total_check", 2027).value == 0
    assert row(f2_result, "debt", "debt_to_equity", 2026).status == "unreconciled"
    assert row(f2_result, "debt", "debt_to_equity", 2027).status == "unreconciled"


def test_cash_liquidity_and_bridge_residual(f2_result) -> None:
    assert row(f2_result, "cash_flow", "opening_cash", 2026).value == 1_916_796
    assert row(f2_result, "cash_flow", "closing_cash", 2026).value == 503_378
    assert row(f2_result, "cash_flow", "net_cash_change", 2026).value == -1_413_418
    assert row(f2_result, "cash_flow", "opening_cash", 2027).value == 503_378
    assert row(f2_result, "cash_flow", "closing_cash", 2027).value == 1_151_288
    assert row(f2_result, "cash_flow", "net_cash_change", 2027).value == 647_910
    assert row(f2_result, "reconciliation", "cash_change_check", 2026).value == 0
    assert row(f2_result, "reconciliation", "cash_change_check", 2027).value == 0
    assert row(f2_result, "cash_flow", "factory_depreciation_cash", 2026).value == 278_100
    assert row(f2_result, "cash_flow", "factory_depreciation_cash", 2027).value == 327_300
    assert row(f2_result, "cash_flow", "factory_depreciation_cash", 2026).status == "confirmed"
    assert row(f2_result, "cash_flow", "cash_bridge_residual", 2026).value == 1
    assert row(f2_result, "cash_flow", "cash_bridge_residual", 2027).value == 0
    assert row(f2_result, "cash_flow", "cash_bridge_residual", 2026).reconciliation_status == "documented_residual"
    assert row(f2_result, "cash_flow", "cash_bridge_residual", 2027).reconciliation_status == "exact"
    assert row(f2_result, "cash_flow", "cash_bridge_residual", 2026).status == "confirmed"
    assert row(f2_result, "cash_flow", "cash_bridge_residual", 2027).status == "confirmed"
    assert row(f2_result, "cash_flow", "cash_bridge_total", 2026).value == -1_413_419
    assert row(f2_result, "cash_flow", "cash_bridge_total", 2027).value == 647_910


def test_all_balance_anomalies_are_unreconciled(f2_result) -> None:
    balance_anomalies = [
        anomaly for anomaly in f2_result.pipeline.anomalies if anomaly.category == "balance"
    ]
    assert len(f2_result.balance_anomalies) == len(balance_anomalies)
    assert f2_result.manifest["summary"]["critical_balance_anomalies"] == sum(
        1 for anomaly in balance_anomalies if anomaly.severity == "critical"
    )
    assert all(item["status"] == "unreconciled" for item in f2_result.balance_anomalies)
    assert all(
        row.source_anomaly_status == "unreconciled"
        for row in f2_result.rows
        if row.section == "balance" and row.metric in {
            "total_assets",
            "total_liabilities",
            "total_current_assets",
            "total_current_liabilities",
            "reported_equity",
            "reserves",
        }
    )


def test_provenance_status_and_derived_dependencies(f2_result) -> None:
    for item in f2_result.rows:
        assert item.status in ALLOWED_STATUSES
        assert item.tolerance_eur >= 0
        assert item.source_cells or item.derived_from
    assert row(f2_result, "balance", "current_ratio", 2026).status == "unreconciled"
    assert row(f2_result, "balance", "working_capital", 2026).status == "unreconciled"
    assert row(f2_result, "debt", "debt_to_equity", 2026).status == "unreconciled"
    assert "PD-05" in row(f2_result, "income_statement", "revenue_total", 2026).pd_dependencies
    assert "PD-06" in row(f2_result, "income_statement", "general_expenses", 2026).pd_dependencies


def test_outputs_are_complete_and_report_has_status_table(f2_result, tmp_path: Path) -> None:
    write_f2_outputs(f2_result, tmp_path)
    expected = {
        "income_statement.csv",
        "balance.csv",
        "debt.csv",
        "cash_flow.csv",
        "reconciliation.csv",
        "manifest.json",
        "report.md",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "Tabla resumen de cifras y estados" in report
    assert "balance_detail_residual" in report
    assert "`unreconciled`" in report
    assert "Diagnóstico del puente de caja" in report
    assert "278.100" in report and "327.300" in report
    assert "16" in report and "81" in report
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["summary"]["rows"] == len(f2_result.rows)
    assert len(manifest["balance_anomalies"]) == len(f2_result.balance_anomalies)
    with (tmp_path / "income_statement.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert "status" in rows[0]
    assert "reconciliation_status" in rows[0]


def test_sources_remain_unchanged(f2_result) -> None:
    for source in f2_result.pipeline.sources:
        assert source.hash_unchanged is True
        assert sha256_file(Path(source.path)) == source.sha256_before


def test_engine_covers_every_closed_year(f2_result) -> None:
    years = {row.period for row in f2_result.rows if row.section == "income_statement"}
    assert years == set(f2_result.f2_config.periods)


def test_every_closed_year_has_a_positive_revenue(f2_result) -> None:
    for year in f2_result.f2_config.periods:
        revenue = next(
            row
            for row in f2_result.rows
            if row.section == "income_statement"
            and row.metric == "revenue_total"
            and row.period == year
        )
        assert revenue.value is not None, f"sin ingresos en {year}"
        assert revenue.value > 0, f"ingresos no positivos en {year}"
