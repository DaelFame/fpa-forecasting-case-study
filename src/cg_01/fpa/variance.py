"""Budget-vs-actual variance as an additive bridge.

Every row is an **impact on profit**, signed so the rows of a period add up to the
change in net income after taxes:

    sum(fact_variance.amount | period) == actual_net_income - budget_net_income

The gross-margin block is decomposed into four drivers with the standard
price-volume-mix-cost identity:

    volume    = (Q_actual - Q_budget) * budget_unit_margin
    price     = sum(q_i * (p_i - P_budget))
    unit_cost = -sum(q_i * (u_i - U_budget))
    mix       = gross_margin_variance - volume - price - unit_cost

`mix` is the exact closing item, so the bridge always ties, including when the
source restates quantities.

The budget does not publish quantities: the committed volume is the planned
production in the decision log (`unidades_producir`), which is what the simulation
budgets against.
"""

from __future__ import annotations

from typing import Any, Iterable

from ..f2_engine import F2Result, sheet_role
from ..models import Observation
from ..text import normalize_label

BUDGET_LABELS: dict[str, str] = {
    "ingresos totales": "revenue_total",
    "margen de contribucion": "gross_profit",
    "gastos de marketing": "marketing_expenses",
    "gastos de personal": "personnel_expenses",
    "gastos i d": "rd_expenses",
    "gastos de depreciacion": "depreciation_expenses",
    "dotaciones por insolvencias": "insolvency_expenses",
    "gastos generales": "general_expenses",
    "total gastos": "operating_expenses_total",
    "resultado bruto": "gross_result",
    "ingresos financieros": "financial_income",
    "gastos financieros": "financial_expense",
    "resultado financiero": "financial_result",
    "resultado extraordinario": "extraordinary_result",
    "resultado neto": "net_result_before_taxes",
}

OPEX_LINES: tuple[str, ...] = (
    "marketing_expenses",
    "personnel_expenses",
    "rd_expenses",
    "depreciation_expenses",
    "insolvency_expenses",
    "general_expenses",
)

DRIVER_LABELS: dict[str, str] = {
    "price": "Price",
    "volume": "Volume",
    "mix": "Mix",
    "unit_cost": "Unit cost",
    "gross_margin": "Gross margin",
    "opex": "Operating expenses",
    "financial_result": "Financial result",
    "extraordinary_result": "Extraordinary result",
    "taxes": "Taxes",
    "rounding": "Rounding",
}


def annual_units(
    observations: Iterable[Observation],
    aliases: dict[str, dict[str, str]],
    products: Iterable[str],
) -> dict[tuple[int, str], float]:
    """Sold units per year and product.

    Annual rows win over quarterly ones, and duplicates take the largest value:
    some sales sheets repeat the same figure in more than one block, and a later
    block (expired units, ratios) must never overwrite the real volume.
    """
    keys = {normalize_label(product) for product in products}
    annual: dict[tuple[int, str], float] = {}
    quarterly: dict[tuple[int, str], float] = {}
    for observation in observations:
        if observation.data_type != "real" or observation.year is None:
            continue
        if observation.label_normalized not in keys:
            continue
        if sheet_role(observation.sheet, observation.source_id, aliases) != "ventas":
            continue
        value = observation.numeric_value
        if value is None:
            continue
        key = (observation.year, observation.label_normalized)
        if observation.quarter is None:
            annual[key] = max(annual.get(key, value), value)
        else:
            quarterly[key] = quarterly.get(key, 0.0) + value
    result = dict(quarterly)
    result.update(annual)
    return result


def planned_units(
    observations: Iterable[Observation], products: Iterable[str]
) -> dict[tuple[int, str], float]:
    """Planned production per year and product, from the decision log.

    A zero means "keep the previous plan" in the simulator, so it is carried
    forward instead of read as no plan. The decision-log schema changed between
    rounds: 2026-2027 use `produccion.unidades_producir`, 2028-2029 use
    `modulos.produccion.unidades_a_producir`.
    """
    keys = {normalize_label(product) for product in products}
    raw: dict[tuple[int, str], float] = {}
    for observation in observations:
        if observation.data_type != "decision" or observation.year is None:
            continue
        scope = normalize_label(observation.scope)
        if "produccion" not in scope:
            continue
        if "unidades producir" not in scope and "unidades a producir" not in scope:
            continue
        if observation.label_normalized not in keys:
            continue
        value = observation.numeric_value
        if value is None:
            continue
        raw[(observation.year, observation.label_normalized)] = value

    result: dict[tuple[int, str], float] = {}
    carried: dict[str, float] = {}
    for year in sorted({year for year, _ in raw}):
        for product in keys:
            value = raw.get((year, product))
            if value is None:
                continue
            if value > 0:
                carried[product] = value
            elif product in carried:
                value = carried[product]
            else:
                continue
            result[(year, product)] = value
    return result


def budget_values(observations: Iterable[Observation]) -> dict[tuple[int, str], float]:
    """Budget P&L lines per year, from the committed budget block."""
    result: dict[tuple[int, str], float] = {}
    for observation in observations:
        if observation.data_type != "budget" or observation.year is None:
            continue
        metric = BUDGET_LABELS.get(observation.label_normalized)
        if metric is None or observation.numeric_value is None:
            continue
        result.setdefault((observation.year, metric), observation.numeric_value)
    return result


def _actuals(f2: F2Result, period: int) -> dict[str, float]:
    return {
        row.metric: float(row.value)
        for row in f2.rows
        if row.section == "income_statement" and row.period == period and row.value is not None
    }


def _product_actuals(f2: F2Result, period: int, products: Iterable[str]) -> dict[str, tuple[float, float]]:
    values = _actuals(f2, period)
    return {
        product: (values[f"revenue_{product}"], values[f"cost_{product}"])
        for product in products
        if f"revenue_{product}" in values and f"cost_{product}" in values
    }


def build_variance(
    f2: F2Result,
    products: Iterable[str],
    *,
    tolerance: float = 1.0,
) -> list[dict[str, Any]]:
    observations = f2.pipeline.observations
    aliases = f2.f2_config.sheet_aliases
    units = annual_units(observations, aliases, products)
    plan = planned_units(observations, products)
    budget = budget_values(observations)

    rows: list[dict[str, Any]] = []
    periods = sorted({period for period, _ in budget} & {row.period for row in f2.rows})

    for period in periods:
        actual = _actuals(f2, period)
        revenue_a = actual.get("revenue_total")
        gross_a = actual.get("gross_profit")
        cost_a = actual.get("cost_of_sales_total")
        revenue_b = budget.get((period, "revenue_total"))
        gross_b = budget.get((period, "gross_profit"))
        if None in (revenue_a, gross_a, cost_a, revenue_b, gross_b):
            continue

        period_units = {
            product: units[(period, product)]
            for product in products
            if (period, product) in units
        }
        period_plan = {
            product: plan[(period, product)]
            for product in products
            if (period, product) in plan
        }
        product_actuals = _product_actuals(f2, period, products)

        effects: list[tuple[str, str, float]] = []
        quantity_a = sum(period_units.values())
        quantity_b = sum(period_plan.values())
        cost_b = revenue_b - gross_b
        margin_a = gross_a
        margin_b = gross_b

        if quantity_a and quantity_b and product_actuals:
            price_b = revenue_b / quantity_b
            unit_cost_b = cost_b / quantity_b
            unit_margin_b = price_b - unit_cost_b
            volume = (quantity_a - quantity_b) * unit_margin_b
            price = 0.0
            unit_cost = 0.0
            for product, (revenue_i, cost_i) in product_actuals.items():
                quantity_i = period_units.get(product, 0.0)
                if not quantity_i:
                    continue
                price += quantity_i * (revenue_i / quantity_i - price_b)
                unit_cost -= quantity_i * (cost_i / quantity_i - unit_cost_b)
            mix = margin_a - margin_b - volume - price - unit_cost
            effects.extend(
                [
                    ("volume", "gross_profit", volume),
                    ("price", "revenue_total", price),
                    ("unit_cost", "cost_of_sales_total", unit_cost),
                    ("mix", "gross_profit", mix),
                ]
            )
        else:
            effects.append(("gross_margin", "gross_profit", margin_a - margin_b))

        for line in OPEX_LINES:
            amount = actual.get(line, 0.0) - budget.get((period, line), 0.0)
            if abs(amount) > 1e-9:
                effects.append(("opex", line, -amount))

        for driver, line in (
            ("financial_result", "financial_result"),
            ("extraordinary_result", "extraordinary_result"),
        ):
            amount = actual.get(line, 0.0) - budget.get((period, line), 0.0)
            if abs(amount) > 1e-9:
                effects.append((driver, line, amount))

        # La varianza se mide antes de impuestos: el presupuesto no modela
        # impuestos, así que comparar el resultado después de impuestos contra un
        # presupuesto pre-tax mezclaría dos bases distintas y el puente no cerraría
        # sobre el número que se reporta.
        net_actual = actual.get("net_result_before_taxes")
        net_budget = budget.get((period, "net_result_before_taxes"), 0.0)
        expected = None if net_actual is None else net_actual - net_budget
        total = sum(amount for _, _, amount in effects)
        if expected is None or abs(total - expected) > tolerance:
            raise ValueError(
                f"La cascada de {period} no cuadra: efectos={total:.2f}, "
                f"resultado={expected}."
            )
        residual = expected - total
        if abs(residual) > 0.005:
            effects.append(("rounding", "net_result_before_taxes", residual))

        for driver, line, amount in effects:
            rows.append(
                {
                    "period_key": str(period),
                    "driver_key": driver,
                    "line_item_key": line,
                    "amount": amount,
                    "status_key": "inferred_accepted",
                }
            )

    return rows


def driver_dimension(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only the drivers that actually appear in the fact, in a stable order."""
    present = {row["driver_key"] for row in rows}
    return [
        {"driver_key": key, "label": label, "unit": "percent"}
        for key, label in DRIVER_LABELS.items()
        if key in present
    ]
