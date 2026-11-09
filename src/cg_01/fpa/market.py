"""Market fact: what the market sold, what we sold, and the demand left unserved.

Two different gaps live here and they must not be confused:

- `unserved_units`: market demand minus market sales, i.e. demand the whole market
  could not serve. It is the capacity story, market-wide.
- `company_unserved_units`: our own demand intent minus what we sold. It is the
  share of that gap attributable to us.

The source publishes the demand table only for some close files, so the demand
columns are empty where it does not exist. Market units, our units and our share
are complete for every year.
"""

from __future__ import annotations

from typing import Any, Iterable

from ..f2_engine import F2Result, sheet_role
from ..models import Observation
from ..text import normalize_label
from .variance import annual_units


def _market_units(
    observations: Iterable[Observation],
    aliases: dict[str, dict[str, str]],
    products: Iterable[str],
) -> dict[tuple[int, str], float]:
    keys = {normalize_label(product) for product in products}
    result: dict[tuple[int, str], float] = {}
    for observation in observations:
        if observation.data_type != "real" or observation.year is None:
            continue
        if observation.quarter is not None or observation.label_normalized not in keys:
            continue
        if sheet_role(observation.sheet, observation.source_id, aliases) != "mercado":
            continue
        if "unidades vendidas" not in normalize_label(observation.scope):
            continue
        value = observation.numeric_value
        if value is None:
            continue
        result[(observation.year, observation.label_normalized)] = value
    return result


def _scope_kind(scope: str) -> str:
    normalized = normalize_label(scope)
    if "total mercado" in normalized:
        return "market"
    if "analisis compan" in normalized:
        return "company"
    return ""


def _demand_units(observations: Iterable[Observation]) -> dict[tuple[int, str, str], float]:
    """Demand intent, preferring the units column over the thousands one."""
    units: dict[tuple[int, str, str], float] = {}
    thousands: dict[tuple[int, str, str], float] = {}
    for observation in observations:
        if observation.data_type != "real" or observation.year is None:
            continue
        segment = normalize_label(observation.segment)
        if not segment.startswith("intencion de compra"):
            continue
        kind = _scope_kind(observation.scope)
        if not kind:
            continue
        value = observation.numeric_value
        if value is None:
            continue
        key = (observation.year, observation.label_normalized, kind)
        if "miles" in segment:
            thousands[key] = value * 1_000
        else:
            units[key] = value
    result = dict(thousands)
    result.update(units)
    return result


def build_market(f2: F2Result, products: Iterable[str]) -> list[dict[str, Any]]:
    observations = f2.pipeline.observations
    aliases = f2.f2_config.sheet_aliases
    product_keys = [normalize_label(product) for product in products]

    sold = annual_units(observations, aliases, product_keys)
    market = _market_units(observations, aliases, product_keys)
    demand = _demand_units(observations)

    years = sorted({year for year, _ in market} | {year for year, _ in sold})
    rows: list[dict[str, Any]] = []
    for year in years:
        for product in product_keys:
            market_units = market.get((year, product))
            units_sold = sold.get((year, product))
            if market_units is None and units_sold is None:
                continue
            market_demand = demand.get((year, product, "market"))
            company_demand = demand.get((year, product, "company"))
            share = units_sold / market_units if market_units and units_sold is not None else None
            unserved = (
                market_demand - market_units
                if market_demand is not None and market_units is not None
                else None
            )
            company_unserved = (
                max(0.0, company_demand - units_sold)
                if company_demand is not None and units_sold is not None
                else None
            )
            rows.append(
                {
                    "period_key": str(year),
                    "product_key": product,
                    "market_units": market_units,
                    "units_sold": units_sold,
                    "market_share": share,
                    "demand_units": market_demand,
                    "unserved_units": unserved,
                    "company_unserved_units": company_unserved,
                }
            )
    return rows
