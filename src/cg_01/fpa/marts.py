"""Analytics marts: the galaxy schema consumed by the Power BI report.

Facts and dimensions are written to ``data/processed`` as CSV. The shape follows
``docs/data_model.md``.

Run ``uv run python -m cg_01.fpa.marts`` to rebuild ``outputs/f2`` and
``data/processed`` from the raw sources in one deterministic step.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ..config import load_config
from ..f2_engine import F2Result, load_f2_config, run_f2, sheet_role
from ..models import Observation
from ..text import period_string
from .market import build_market
from .variance import BUDGET_LABELS, annual_units, budget_values, build_variance, driver_dimension
from .backtest import build_backtest, summarise

PRODUCTS: dict[str, tuple[str, int]] = {
    "corbatas": ("Neckties", 1),
    "bufandas": ("Scarves", 2),
    "calcetines": ("Socks", 3),
}

SCENARIOS: list[tuple[str, str, bool, int]] = [
    ("actual", "Actual", True, 1),
    ("budget", "Budget", True, 2),
    ("forecast", "Forecast", False, 3),
    ("upside", "Upside", False, 4),
    ("downside", "Downside", False, 5),
    ("stress", "Stress", False, 6),
]

STATUS_META: dict[str, tuple[int, str]] = {
    "confirmed": (0, "Ties to a source cell and passes all applicable identities"),
    "inferred_accepted": (1, "Derived from confirmed inputs; derivation documented"),
    "pending": (2, "Source exists but is incomplete or contested"),
    "accepted_exception": (3, "Known deviation, documented and deliberately not corrected"),
    "unreconciled": (4, "Fails a reconciliation and is carried forward as a visible gap"),
}

REGIMES: list[tuple[str, str]] = [
    ("A", "Decision-conditional"),
    ("B", "Decision-free"),
]

FOLDS: list[tuple[str, str, int, int]] = [
    ("F1", "Train up to 2027, predict 2028", 2027, 2028),
    ("F2", "Train up to 2028, predict 2029", 2028, 2029),
]

INCOME_ORDER: list[str] = [
    "revenue_corbatas",
    "revenue_bufandas",
    "revenue_calcetines",
    "revenue_total",
    "cost_corbatas",
    "cost_bufandas",
    "cost_calcetines",
    "cost_of_sales_total",
    "gross_profit",
    "margin_corbatas",
    "margin_bufandas",
    "margin_calcetines",
    "marketing_expenses",
    "personnel_expenses",
    "rd_expenses",
    "depreciation_expenses",
    "insolvency_expenses",
    "general_expenses",
    "operating_expenses_total",
    "gross_result",
    "financial_income",
    "financial_expense",
    "financial_result",
    "extraordinary_result",
    "net_result_before_taxes",
    "taxes",
    "net_result_after_taxes",
]

COST_KEYS = {
    "cost_corbatas",
    "cost_bufandas",
    "cost_calcetines",
    "cost_of_sales_total",
    "marketing_expenses",
    "personnel_expenses",
    "rd_expenses",
    "depreciation_expenses",
    "insolvency_expenses",
    "general_expenses",
    "operating_expenses_total",
    "financial_expense",
    "taxes",
}

SUBTOTAL_KEYS = {
    "revenue_total",
    "cost_of_sales_total",
    "gross_profit",
    "operating_expenses_total",
    "gross_result",
    "financial_result",
    "net_result_before_taxes",
    "net_result_after_taxes",
}

# Budget lines are labelled differently from the statement metrics; the mapping
# lives in `variance.BUDGET_LABELS` and is shared by the fact and the bridge.
QUARTER_END = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}


def _cell(value: Any) -> Any:
    """Drop the trailing .0 so integral amounts read as integers."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _write(path: Path, columns: list[str], rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(row.get(key, "")) for key in columns})
            count += 1
    return count


def _period_end(period: str) -> date:
    if "-Q" in period:
        year, quarter = period.split("-Q")
        month, day = QUARTER_END[int(quarter)]
        return date(int(year), month, day)
    return date(int(period), 12, 31)


def _dim_period(periods: list[int], quarters: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for period in periods:
        rows.append(
            {
                "period_key": str(period),
                "grain": "year",
                "year": period,
                "quarter": "",
                "period_end": _period_end(str(period)).isoformat(),
                "label": str(period),
                "is_closed": "true",
                "is_forecast": "false",
            }
        )
    for period in quarters:
        year, quarter = period.split("-Q")
        rows.append(
            {
                "period_key": period,
                "grain": "quarter",
                "year": int(year),
                "quarter": int(quarter),
                "period_end": _period_end(period).isoformat(),
                "label": f"Q{quarter} {year}",
                "is_closed": "true",
                "is_forecast": "false",
            }
        )
    rows.sort(key=lambda row: (row["year"], row["grain"] == "quarter", row["quarter"] or 0))
    return rows


def _dim_product() -> list[dict[str, Any]]:
    return [
        {"product_key": key, "label": label, "sort_order": order}
        for key, (label, order) in PRODUCTS.items()
    ]


def _dim_line_item(f2: F2Result) -> list[dict[str, Any]]:
    metrics = {
        row.metric
        for row in f2.rows
        if row.section == "income_statement" and row.unit == "EUR"
    }
    order = {key: index for index, key in enumerate(INCOME_ORDER, start=1)}
    rows = []
    for metric in sorted(metrics, key=lambda key: (order.get(key, 900), key)):
        rows.append(
            {
                "line_item_key": metric,
                "label": metric.replace("_", " ").capitalize(),
                "statement": "income_statement",
                "section": _income_section(metric),
                "sign": -1 if metric in COST_KEYS else 1,
                "is_subtotal": "true" if metric in SUBTOTAL_KEYS else "false",
                "display_order": order.get(metric, 900),
            }
        )
    return rows


def _income_section(metric: str) -> str:
    if metric.startswith("revenue"):
        return "revenue"
    if metric.startswith("cost") or metric.startswith("margin_"):
        return "cost_of_sales"
    if metric in {"gross_profit", "gross_result"}:
        return "margin"
    if metric in {"financial_income", "financial_expense", "financial_result"}:
        return "financial"
    if metric == "extraordinary_result":
        return "extraordinary"
    if metric.startswith("net_result") or metric == "taxes":
        return "net"
    return "opex"


def _dim_account(f2: F2Result) -> list[dict[str, Any]]:
    metrics = sorted(
        {row.metric for row in f2.rows if row.section == "balance" and row.unit == "EUR"}
    )
    return [
        {
            "account_key": metric,
            "label": metric.replace("_", " ").capitalize(),
            "section": _balance_section(metric),
            "is_total": "true" if metric.startswith("total") else "false",
        }
        for metric in metrics
    ]


def _balance_section(metric: str) -> str:
    if metric.startswith("total_assets") or metric.startswith("total_non_current") or metric.startswith("total_current_assets"):
        return "assets"
    if metric.startswith("total_liabilit"):
        return "liabilities"
    if metric in {"reported_equity", "detailed_equity", "reserves", "capital", "result"}:
        return "equity"
    if metric in {"inventory", "accounts_receivable", "cash"}:
        return "current_assets"
    if metric in {"suppliers", "short_term_debt", "taxes_payable"}:
        return "current_liabilities"
    return "other"


def _dim_scenario() -> list[dict[str, Any]]:
    return [
        {
            "scenario_key": key,
            "label": label,
            "is_committed": "true" if committed else "false",
            "sort_order": order,
        }
        for key, label, committed, order in SCENARIOS
    ]


def _dim_status(f2: F2Result) -> list[dict[str, Any]]:
    present = {row.status for row in f2.rows}
    return [
        {
            "status_key": key,
            "label": key.replace("_", " ").capitalize(),
            "severity": severity,
            "description": description,
        }
        for key, (severity, description) in STATUS_META.items()
        if key in present
    ]


def _dim_regime() -> list[dict[str, Any]]:
    return [{"regime_key": key, "label": label} for key, label in REGIMES]


def _dim_fold() -> list[dict[str, Any]]:
    return [
        {
            "fold_key": key,
            "label": label,
            "train_through": train,
            "target_year": target,
        }
        for key, label, train, target in FOLDS
    ]


def _fact_financials(f2: F2Result, aliases: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in f2.rows:
        if row.section != "income_statement" or row.unit != "EUR":
            continue
        rows.append(
            {
                "period_key": str(row.period),
                "line_item_key": row.metric,
                "scenario_key": "actual",
                "amount": row.value,
                "status_key": row.status,
            }
        )

    seen: set[tuple[str, str]] = set()
    for observation in f2.pipeline.observations:
        if observation.data_type != "budget":
            continue
        metric = BUDGET_LABELS.get(observation.label_normalized)
        if metric is None or observation.numeric_value is None:
            continue
        period = str(observation.year)
        if (period, metric) in seen:
            continue
        seen.add((period, metric))
        rows.append(
            {
                "period_key": period,
                "line_item_key": metric,
                "scenario_key": "budget",
                "amount": observation.numeric_value,
                "status_key": "confirmed",
            }
        )
    return rows


def _fact_balance(f2: F2Result) -> list[dict[str, Any]]:
    return [
        {
            "period_key": str(row.period),
            "account_key": row.metric,
            "amount": row.value,
            "status_key": row.status,
        }
        for row in f2.rows
        if row.section == "balance" and row.unit == "EUR"
    ]


def _quarterly_series(
    observations: Iterable[Observation],
    aliases: dict[str, dict[str, str]],
    role: str,
    product_keys: dict[str, str],
    annual_totals: dict[tuple[int, str], float],
) -> dict[tuple[str, str], float]:
    """Pick one quarterly series per year and product.

    Some sheets stack several tables under the same role: real units, competitor
    shares, expired units. They are all quarterly numbers with a product label, so
    the only reliable selector is the annual total published in the same workbook.
    The series whose four quarters add up to that total is the real one.
    """
    groups: dict[tuple[int, str, int], dict[int, float]] = {}
    for observation in observations:
        if observation.data_type != "real" or observation.year is None:
            continue
        if not observation.quarter or observation.numeric_value is None:
            continue
        product = product_keys.get(observation.label_normalized)
        if product is None:
            continue
        if sheet_role(observation.sheet, observation.source_id, aliases) != role:
            continue
        groups.setdefault(
            (observation.year, product, observation.source_row), {}
        )[observation.quarter] = observation.numeric_value

    best: dict[tuple[int, str], tuple[float, dict[int, float]]] = {}
    for (year, product, _row), quarters in groups.items():
        total = sum(quarters.values())
        target = annual_totals.get((year, product))
        score = abs(total - target) if target is not None else 0.0
        current = best.get((year, product))
        if current is None or score < current[0] or (
            score == current[0] and len(quarters) > len(current[1])
        ):
            best[(year, product)] = (score, quarters)

    return {
        (period_string(year, quarter), product): value
        for (year, product), (_, quarters) in best.items()
        for quarter, value in quarters.items()
    }


def _fact_sales(f2: F2Result, aliases: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    product_keys = {key: key for key in PRODUCTS}
    observations = f2.pipeline.observations
    revenue_annual = {
        (row.period, row.metric[len("revenue_"):]): float(row.value)
        for row in f2.rows
        if row.section == "income_statement"
        and row.metric.startswith("revenue_")
        and row.metric[len("revenue_"):] in PRODUCTS
        and row.value is not None
    }
    units_annual = {
        (year, product): value
        for (year, product), value in annual_units(observations, aliases, PRODUCTS).items()
    }

    units = _quarterly_series(observations, aliases, "ventas", product_keys, units_annual)
    revenue = _quarterly_series(observations, aliases, "ingresos", product_keys, revenue_annual)

    keys = sorted(set(units) & set(revenue))
    return [
        {
            "period_key": period,
            "product_key": product,
            "units_sold": units[(period, product)],
            "revenue": revenue[(period, product)],
        }
        for period, product in keys
    ]


def _fact_product_annual(f2: F2Result) -> list[dict[str, Any]]:
    by_period: dict[int, dict[str, dict[str, float]]] = {}
    for row in f2.rows:
        if row.section != "income_statement" or row.unit != "EUR":
            continue
        for prefix, field in (("revenue_", "revenue"), ("cost_", "cost_of_sales"), ("margin_", "gross_margin")):
            if row.metric.startswith(prefix) and row.metric[len(prefix):] in PRODUCTS and row.value is not None:
                by_period.setdefault(row.period, {}).setdefault(row.metric[len(prefix):], {})[field] = row.value

    rows: list[dict[str, Any]] = []
    for period in sorted(by_period):
        for product, values in sorted(by_period[period].items()):
            rows.append(
                {
                    "period_key": str(period),
                    "product_key": product,
                    "revenue": values.get("revenue", ""),
                    "cost_of_sales": values.get("cost_of_sales", ""),
                    "gross_margin": values.get("gross_margin", ""),
                }
            )
    return rows


def build_marts(f2: F2Result, output_dir: Path | None = None) -> dict[str, int]:
    config = f2.f2_config
    target = output_dir if output_dir is not None else config.project_root / "data" / "processed"
    aliases = config.sheet_aliases

    sales = _fact_sales(f2, aliases)
    quarters = sorted({row["period_key"] for row in sales})
    periods = list(config.periods)
    variance = build_variance(f2, PRODUCTS)
    market = build_market(f2, PRODUCTS)
    backtest = build_backtest(
        f2, PRODUCTS, budget=budget_values(f2.pipeline.observations)
    )

    counts: dict[str, int] = {}
    counts["dim_period.csv"] = _write(
        target / "dim_period.csv",
        ["period_key", "grain", "year", "quarter", "period_end", "label", "is_closed", "is_forecast"],
        _dim_period(periods, quarters),
    )
    counts["dim_product.csv"] = _write(
        target / "dim_product.csv",
        ["product_key", "label", "sort_order"],
        _dim_product(),
    )
    counts["dim_line_item.csv"] = _write(
        target / "dim_line_item.csv",
        ["line_item_key", "label", "statement", "section", "sign", "is_subtotal", "display_order"],
        _dim_line_item(f2),
    )
    counts["dim_account.csv"] = _write(
        target / "dim_account.csv",
        ["account_key", "label", "section", "is_total"],
        _dim_account(f2),
    )
    counts["dim_scenario.csv"] = _write(
        target / "dim_scenario.csv",
        ["scenario_key", "label", "is_committed", "sort_order"],
        _dim_scenario(),
    )
    counts["dim_status.csv"] = _write(
        target / "dim_status.csv",
        ["status_key", "label", "severity", "description"],
        _dim_status(f2),
    )
    counts["dim_regime.csv"] = _write(
        target / "dim_regime.csv",
        ["regime_key", "label"],
        _dim_regime(),
    )
    counts["dim_fold.csv"] = _write(
        target / "dim_fold.csv",
        ["fold_key", "label", "train_through", "target_year"],
        _dim_fold(),
    )
    counts["dim_driver.csv"] = _write(
        target / "dim_driver.csv",
        ["driver_key", "label", "unit"],
        driver_dimension(variance),
    )
    counts["fact_financials.csv"] = _write(
        target / "fact_financials.csv",
        ["period_key", "line_item_key", "scenario_key", "amount", "status_key"],
        _fact_financials(f2, aliases),
    )
    counts["fact_balance.csv"] = _write(
        target / "fact_balance.csv",
        ["period_key", "account_key", "amount", "status_key"],
        _fact_balance(f2),
    )
    counts["fact_sales.csv"] = _write(
        target / "fact_sales.csv",
        ["period_key", "product_key", "units_sold", "revenue"],
        sales,
    )
    counts["fact_product_annual.csv"] = _write(
        target / "fact_product_annual.csv",
        ["period_key", "product_key", "revenue", "cost_of_sales", "gross_margin"],
        _fact_product_annual(f2),
    )
    counts["fact_market.csv"] = _write(
        target / "fact_market.csv",
        [
            "period_key",
            "product_key",
            "market_units",
            "units_sold",
            "market_share",
            "demand_units",
            "unserved_units",
            "company_unserved_units",
        ],
        market,
    )
    counts["fact_variance.csv"] = _write(
        target / "fact_variance.csv",
        ["period_key", "driver_key", "line_item_key", "amount", "status_key"],
        variance,
    )
    counts["fact_backtest.csv"] = _write(
        target / "fact_backtest.csv",
        [
            "fold_key",
            "regime_key",
            "period_key",
            "line_item_key",
            "forecast_amount",
            "actual_amount",
            "error_eur",
            "abs_pct_error",
            "bias_pct",
            "status_key",
        ],
        backtest,
    )
    _write_manifest(target, f2, counts, summarise(backtest))
    return counts


def _write_manifest(
    target: Path,
    f2: F2Result,
    counts: dict[str, int],
    backtest_summary: dict[str, dict[str, float]],
) -> None:
    """Build stamp for the dashboard: when, from which sources, how many rows.

    Deliberately not versioned: it changes on every run. Power BI reads it to show
    data freshness and to detect a stale export.
    """
    payload = {
        "schema_version": "marts.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "periods": list(f2.f2_config.periods),
        "row_counts": counts,
        "backtest_summary": backtest_summary,
        "sources": [
            {
                "source_id": source.source_id,
                "source_key": source.source_key,
                "relative_path": source.relative_path,
                "sha256": source.sha256_before,
            }
            for source in f2.pipeline.sources
        ],
    }
    (target / "_manifest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cg_01.fpa.marts",
        description="Rebuild outputs/f2 and the analytics marts in data/processed.",
    )
    parser.add_argument("--config", type=Path, default=None, help="Ruta a config/f1.toml.")
    parser.add_argument("--f2-config", type=Path, default=None, help="Ruta a config/f2.toml.")
    parser.add_argument("--output", type=Path, default=None, help="Directorio de los marts.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    f1_config = load_config(args.config)
    f2_config = load_f2_config(
        args.f2_config,
        output_dir=None,
        project_root=f1_config.project_root,
    )
    result = run_f2(f1_config, f2_config)

    from ..f2_report import write_f2_outputs

    write_f2_outputs(result, f2_config.output_dir)
    counts = build_marts(result, args.output)
    if not args.quiet:
        print(
            f"Marts completados: {len(result.rows)} filas F2, "
            f"{sum(counts.values())} filas en {len(counts)} tablas."
        )
        target = args.output or f2_config.project_root / "data" / "processed"
        manifest = json.loads((target / "_manifest.json").read_text(encoding="utf-8"))
        summary = manifest.get("backtest_summary", {})
        if summary:
            parts = [
                f"{key} MAPE {value['mape'] * 100:.1f}% (bias {value['bias'] * 100:+.1f}%)"
                for key, value in sorted(summary.items())
            ]
            print("Backtest: " + " | ".join(parts))
        print(f"Salida: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
