"""Rolling-origin backtest of a driver-based forecast, with two information sets.

Folds use an expanding window: each fold only sees years that were closed before
the target year.

    F1  train <= 2027  ->  predict 2028
    F2  train <= 2028  ->  predict 2029

Two regimes share the same structure and differ only in what they know:

- **A, decision-conditional**: the prices, planned production and marketing
  decisions recorded for the target year, plus unit costs carried from the last
  closed year.
- **B, decision-free**: the last closed year, held flat. No target-year information.

Unit costs are carried from the last closed year in both regimes: the decision log
does not publish them, so they cancel out of the A/B delta by construction.

Each row is one P&L line for one fold and regime. `error_eur` is signed
(forecast - actual); `abs_pct_error` and `bias_pct` are relative to the absolute
actual and are empty when the actual line is too small to make a ratio meaningful.
"""

from __future__ import annotations

from typing import Any, Iterable

from ..f2_engine import F2Result
from ..models import Observation
from ..text import normalize_label
from .variance import annual_units, planned_units

FOLDS: tuple[tuple[str, str, int, int], ...] = (
    ("F1", "Train up to 2027, predict 2028", 2027, 2028),
    ("F2", "Train up to 2028, predict 2029", 2028, 2029),
    ("F3", "Train up to 2029, predict 2030", 2029, 2030),
)

LINES: tuple[str, ...] = (
    "revenue_total",
    "cost_of_sales_total",
    "gross_profit",
    "marketing_expenses",
    "personnel_expenses",
    "rd_expenses",
    "depreciation_expenses",
    "insolvency_expenses",
    "general_expenses",
    "operating_expenses_total",
    "financial_result",
    "extraordinary_result",
    "net_result_before_taxes",
    "taxes",
    "net_result_after_taxes",
)

OPEX_LINES: tuple[str, ...] = (
    "marketing_expenses",
    "personnel_expenses",
    "rd_expenses",
    "depreciation_expenses",
    "insolvency_expenses",
    "general_expenses",
)

MIN_ACTUAL_FOR_RATIO = 1_000.0
"""Below one thousand euro a percentage error is noise, not information."""
RECONCILIATION_TOLERANCE = 0.02
"""A decision log that implies revenue more than 2% away from the budget is flagged."""


def actuals_by_year(f2: F2Result) -> dict[int, dict[str, float]]:
    result: dict[int, dict[str, float]] = {}
    for row in f2.rows:
        if row.section != "income_statement" or row.value is None:
            continue
        result.setdefault(row.period, {})[row.metric] = float(row.value)
    return result


def _product_of(label: str, product_keys: Iterable[str]) -> str | None:
    for key in product_keys:
        if label == key or label.startswith(f"{key} "):
            return key
    return None


def _decision_values(
    observations: Iterable[Observation],
    *,
    scope_tokens: Iterable[str],
    product_keys: Iterable[str],
) -> dict[tuple[int, str], float]:
    """Decision values keyed by (year, product).

    Decision labels are not uniform across rounds: 2026 says `corbatas`, 2028 says
    `corbatas_euro`. The product is the prefix, and anything else (a `total` line)
    is ignored instead of being summed into a product.
    """
    tokens = tuple(scope_tokens)
    keys = list(product_keys)
    result: dict[tuple[int, str], float] = {}
    for observation in observations:
        if observation.data_type != "decision" or observation.year is None:
            continue
        scope = normalize_label(observation.scope)
        if not all(token in scope for token in tokens):
            continue
        product = _product_of(observation.label_normalized, keys)
        if product is None:
            continue
        value = observation.numeric_value
        if value is None:
            continue
        result[(observation.year, product)] = value
    return result


def _decisions(
    observations: Iterable[Observation], products: Iterable[str]
) -> dict[int, dict[str, Any]]:
    product_keys = [normalize_label(product) for product in products]
    prices = _decision_values(
        observations, scope_tokens=("precio", "unitario"), product_keys=product_keys
    )
    discount = {
        observation.year: observation.numeric_value
        for observation in observations
        if observation.data_type == "decision"
        and observation.year is not None
        and "descuento canal" in normalize_label(observation.label_normalized)
        and observation.numeric_value is not None
    }
    marketing = _decision_values(
        observations, scope_tokens=("promocion", "marca"), product_keys=product_keys
    )
    volumes = planned_units(observations, products)

    result: dict[int, dict[str, Any]] = {}
    years = sorted({year for year, _ in prices} | {year for year, _ in volumes})
    for year in years:
        price_net: dict[str, float] = {}
        rate = 1.0 - float(discount.get(year, 0.0)) / 100.0
        for product in product_keys:
            price = prices.get((year, product))
            if price is not None:
                price_net[product] = price * rate
        result[year] = {
            "price_net": price_net,
            "volume": {
                product: volumes[(year, product)]
                for product in product_keys
                if (year, product) in volumes
            },
            "marketing": sum(
                value
                for (value_year, _product), value in marketing.items()
                if value_year == year
            ),
            "discount_pct": float(discount.get(year, 0.0)),
        }
    return result


def tax_rate(actual: dict[str, float]) -> float:
    before = actual.get("net_result_before_taxes") or 0.0
    taxes = actual.get("taxes") or 0.0
    if before <= 0:
        return 0.0
    return max(0.0, min(1.0, taxes / before))


def _forecast_b(
    actual: dict[str, float], products: Iterable[str]
) -> dict[str, float]:
    """Last closed year, held flat."""
    forecast = {"revenue_total": 0.0, "cost_of_sales_total": 0.0}
    for product in products:
        revenue = actual.get(f"revenue_{product}", 0.0)
        cost = actual.get(f"cost_{product}", 0.0)
        forecast[f"revenue_{product}"] = revenue
        forecast[f"cost_{product}"] = cost
        forecast["revenue_total"] += revenue
        forecast["cost_of_sales_total"] += cost
    forecast["gross_profit"] = forecast["revenue_total"] - forecast["cost_of_sales_total"]
    for line in OPEX_LINES:
        forecast[line] = actual.get(line, 0.0)
    forecast["operating_expenses_total"] = sum(forecast[line] for line in OPEX_LINES)
    forecast["financial_result"] = actual.get("financial_result", 0.0)
    forecast["extraordinary_result"] = actual.get("extraordinary_result", 0.0)
    forecast["net_result_before_taxes"] = (
        forecast["gross_profit"]
        + forecast["financial_result"]
        + forecast["extraordinary_result"]
        - forecast["operating_expenses_total"]
    )
    forecast["taxes"] = max(0.0, forecast["net_result_before_taxes"]) * tax_rate(actual)
    forecast["net_result_after_taxes"] = (
        forecast["net_result_before_taxes"] - forecast["taxes"]
    )
    return forecast


def _forecast_a(
    actual: dict[str, float],
    decisions: dict[str, Any],
    products: Iterable[str],
) -> dict[str, float]:
    """Decision-conditional: prices, volumes, marketing and R&D from the log."""
    forecast = {"revenue_total": 0.0, "cost_of_sales_total": 0.0}
    for product in products:
        volume = decisions["volume"].get(product)
        price = decisions["price_net"].get(product)
        quantity = actual.get(f"units_{product}")
        if volume is None or price is None or not quantity:
            continue
        unit_cost = actual.get(f"cost_{product}", 0.0) / quantity
        forecast[f"revenue_{product}"] = price * volume
        forecast[f"cost_{product}"] = unit_cost * volume
        forecast["revenue_total"] += forecast[f"revenue_{product}"]
        forecast["cost_of_sales_total"] += forecast[f"cost_{product}"]
    forecast["gross_profit"] = forecast["revenue_total"] - forecast["cost_of_sales_total"]
    for line in OPEX_LINES:
        forecast[line] = actual.get(line, 0.0)
    if decisions["marketing"]:
        forecast["marketing_expenses"] = decisions["marketing"]
    forecast["operating_expenses_total"] = sum(forecast[line] for line in OPEX_LINES)
    forecast["financial_result"] = actual.get("financial_result", 0.0)
    forecast["extraordinary_result"] = actual.get("extraordinary_result", 0.0)
    forecast["net_result_before_taxes"] = (
        forecast["gross_profit"]
        + forecast["financial_result"]
        + forecast["extraordinary_result"]
        - forecast["operating_expenses_total"]
    )
    forecast["taxes"] = max(0.0, forecast["net_result_before_taxes"]) * tax_rate(actual)
    forecast["net_result_after_taxes"] = (
        forecast["net_result_before_taxes"] - forecast["taxes"]
    )
    return forecast


def _row(
    fold: str,
    regime: str,
    period: int,
    line: str,
    forecast: float | None,
    actual_value: float | None,
    status: str,
) -> dict[str, Any] | None:
    if forecast is None or actual_value is None:
        return None
    error = forecast - actual_value
    ratio_ok = abs(actual_value) >= MIN_ACTUAL_FOR_RATIO
    return {
        "fold_key": fold,
        "regime_key": regime,
        "period_key": str(period),
        "line_item_key": line,
        "forecast_amount": forecast,
        "actual_amount": actual_value,
        "error_eur": error,
        "abs_pct_error": abs(error) / abs(actual_value) if ratio_ok else None,
        "bias_pct": error / abs(actual_value) if ratio_ok else None,
        "status_key": status,
    }


def build_backtest(
    f2: F2Result,
    products: Iterable[str],
    *,
    budget: dict[tuple[int, str], float] | None = None,
) -> list[dict[str, Any]]:
    product_keys = [normalize_label(product) for product in products]
    actuals = actuals_by_year(f2)
    units = annual_units(f2.pipeline.observations, f2.f2_config.sheet_aliases, product_keys)
    for (year, product), quantity in units.items():
        actuals.setdefault(year, {})[f"units_{product}"] = quantity
    decisions = _decisions(f2.pipeline.observations, product_keys)
    budget = budget or {}

    rows: list[dict[str, Any]] = []
    for fold, _label, train, target in FOLDS:
        if train not in actuals or target not in actuals:
            continue
        training = actuals[train]
        actual = actuals[target]

        regime_a = _forecast_a(training, decisions.get(target, {
            "price_net": {},
            "volume": {},
            "marketing": 0.0,
        }), product_keys)
        regime_b = _forecast_b(training, product_keys)

        status_a = "inferred_accepted"
        budget_revenue = budget.get((target, "revenue_total"))
        if budget_revenue:
            implied = regime_a["revenue_total"]
            if abs(implied - budget_revenue) / abs(budget_revenue) > RECONCILIATION_TOLERANCE:
                status_a = "pending"

        for regime, forecast, status in (
            ("A", regime_a, status_a),
            ("B", regime_b, "inferred_accepted"),
        ):
            for line in LINES:
                row = _row(fold, regime, target, line, forecast.get(line), actual.get(line), status)
                if row is not None:
                    rows.append(row)
    return rows


def summarise(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Weighted percentage error and weighted bias per fold and regime.

    Error is aggregated as a ratio of sums, never as an average of ratios: a small
    line item with a large relative error must not dominate the headline number.
    """
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        if row["abs_pct_error"] is None or row["error_eur"] is None or row["actual_amount"] is None:
            continue
        grouped.setdefault((row["fold_key"], row["regime_key"]), []).append(row)
    summary: dict[str, dict[str, float]] = {}
    for (fold, regime), items in sorted(grouped.items()):
        base = sum(abs(item["actual_amount"]) for item in items)
        summary[f"{fold}-{regime}"] = {
            "mape": sum(abs(item["error_eur"]) for item in items) / base if base else 0.0,
            "bias": sum(item["error_eur"] for item in items) / base if base else 0.0,
            "lines": len(items),
            "method": "weighted",
        }
    return summary
