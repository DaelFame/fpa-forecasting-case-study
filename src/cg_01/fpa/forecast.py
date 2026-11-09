"""Live forecast for the year after the last close.

2030 is built with the same driver engine as the backtest, from the 2029 close.
There is no 2030 decision log, and the 2029 one does not reconcile with its own
close (L-17), so the forecast deliberately uses the **executed** 2029 levers:
realised net price, sold volume, unit cost and operating expenses. It never reads
the 2029 log.

Two regimes:

- **A, decision-conditional**: price and volume are separate levers, so a scenario
  can move them independently.
- **B, decision-free**: only volume moves; price and cost stay at the 2029 level.

Scenarios are explicit assumptions, not source facts (L-19). They are applied to the
drivers, never to the final profit, so the statements stay internally consistent.
"""

from __future__ import annotations

from typing import Any, Iterable

from ..f2_engine import F2Result
from ..text import normalize_label
from .backtest import LINES, OPEX_LINES, actuals_by_year, tax_rate
from .variance import annual_units

TARGET_YEAR = 2030
FOLD_KEY = "F3"

SCENARIOS: dict[str, dict[str, float]] = {
    "base": {"price": 1.00, "volume": 1.00, "unit_cost": 1.00},
    "upside": {"price": 1.02, "volume": 1.05, "unit_cost": 1.00},
    "downside": {"price": 0.98, "volume": 0.95, "unit_cost": 1.00},
    "stress": {"price": 0.95, "volume": 0.90, "unit_cost": 1.05},
}


def _forecast(
    base: dict[str, float],
    products: Iterable[str],
    scenario: dict[str, float],
    regime: str,
) -> dict[str, float]:
    forecast = {"revenue_total": 0.0, "cost_of_sales_total": 0.0}
    volume_multiplier = scenario["volume"]
    price_multiplier = scenario["price"] if regime == "A" else 1.0
    cost_multiplier = scenario["unit_cost"] if regime == "A" else 1.0

    for product in products:
        quantity = base.get(f"units_{product}")
        revenue = base.get(f"revenue_{product}", 0.0)
        cost = base.get(f"cost_{product}", 0.0)
        if not quantity:
            continue
        price = revenue / quantity
        unit_cost = cost / quantity
        forecast[f"revenue_{product}"] = (
            price * price_multiplier * quantity * volume_multiplier
        )
        forecast[f"cost_{product}"] = (
            unit_cost * cost_multiplier * quantity * volume_multiplier
        )
        forecast["revenue_total"] += forecast[f"revenue_{product}"]
        forecast["cost_of_sales_total"] += forecast[f"cost_{product}"]

    forecast["gross_profit"] = forecast["revenue_total"] - forecast["cost_of_sales_total"]
    for line in OPEX_LINES:
        forecast[line] = base.get(line, 0.0)
    forecast["operating_expenses_total"] = sum(forecast[line] for line in OPEX_LINES)
    forecast["financial_result"] = base.get("financial_result", 0.0)
    forecast["extraordinary_result"] = base.get("extraordinary_result", 0.0)
    forecast["net_result_before_taxes"] = (
        forecast["gross_profit"]
        + forecast["financial_result"]
        + forecast["extraordinary_result"]
        - forecast["operating_expenses_total"]
    )
    forecast["taxes"] = max(0.0, forecast["net_result_before_taxes"]) * tax_rate(base)
    forecast["net_result_after_taxes"] = (
        forecast["net_result_before_taxes"] - forecast["taxes"]
    )
    return forecast


def build_forecast(f2: F2Result, products: Iterable[str]) -> list[dict[str, Any]]:
    product_keys = [normalize_label(product) for product in products]
    actuals = actuals_by_year(f2)
    units = annual_units(f2.pipeline.observations, f2.f2_config.sheet_aliases, product_keys)
    base_year = max(year for year in actuals if year < TARGET_YEAR)
    base = dict(actuals[base_year])
    for product in product_keys:
        if (base_year, product) in units:
            base[f"units_{product}"] = units[(base_year, product)]

    rows: list[dict[str, Any]] = []
    for scenario_key, scenario in SCENARIOS.items():
        for regime in ("A", "B"):
            forecast = _forecast(base, product_keys, scenario, regime)
            for line in LINES:
                value = forecast.get(line)
                if value is None:
                    continue
                rows.append(
                    {
                        "period_key": str(TARGET_YEAR),
                        "line_item_key": line,
                        "scenario_key": scenario_key,
                        "regime_key": regime,
                        "fold_key": FOLD_KEY,
                        "forecast_amount": value,
                        "status_key": "inferred_accepted",
                    }
                )
    return rows
