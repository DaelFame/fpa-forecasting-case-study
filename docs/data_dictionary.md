# Data dictionary

Conventions for every figure produced by this repository.

## Periods

| Format | Example | Granularity |
|---|---|---|
| `YYYY` | `2026` | Annual |
| `YYYY-Qn` | `2026-Q3` | Quarterly |

Quarterly values reconcile to the annual figure within €1 in every closed year
(verified for 2024–2028). The annual figure remains authoritative for statements
because it is the reported total; quarterly figures are used for seasonality and
volume analysis.

## Data types

| Type | Meaning | Years |
|---|---|---|
| `real` | Reported outcome after the period closed | 2024–2029 |
| `budget` | Plan committed before the period was resolved | 2026–2029 |
| `decision` | Inputs chosen by management for the period | 2026–2029 |
| `scenario` | Macro assumptions for future years | 2029–2032 |

A budget and its corresponding real value are a matched pair. Comparing them is
the core of the variance analysis; comparing figures of different types is a
category error and is rejected by the validators.

## Status fields

| Field | Values |
|---|---|
| `status` | `confirmed`, `inferred_accepted`, `pending`, `accepted_exception`, `unreconciled` |
| `reconciliation_status` | `exact`, `within_tolerance`, `not_reconciled`, `not_applicable` |
| `financial_status` | `validated`, `not_validated`, `warning`, `invalid`, `not_applicable` |
| `integrity_status` | `ok`, `error` |

## Products

| Key | Description |
|---|---|
| `corbatas` | Neckties — highest revenue line |
| `bufandas` | Scarves — highest unit price |
| `calcetines` | Socks — highest unit volume, lowest unit price |

Keys are normalised to lowercase and stripped of currency suffixes such as `_euro`.
Aggregate rows (`total_*`) are excluded from product maps.

## Key income statement metrics

| Metric | Definition |
|---|---|
| `revenue_total` | Net revenue after channel discount |
| `cost_of_sales_total` | Manufacturing, logistics, storage and non-quality cost |
| `gross_profit` | `revenue_total - cost_of_sales_total` |
| `gross_margin_pct` | `gross_profit / revenue_total` |
| `general_expenses` | Administrative overhead, excluding personnel and R&D |
| `financial_result` | Financial income minus financial expense |
| `extraordinary_result` | Non-recurring items; excluded from recurring earnings analysis |
| `net_income` | Result after tax |

## Key balance and cash metrics

| Metric | Definition |
|---|---|
| `gross_fixed_assets` | Fixed assets before accumulated depreciation |
| `net_fixed_assets` | `gross_fixed_assets - accumulated_depreciation` |
| `inventory` | Finished goods at direct cost |
| `receivables` | Trade receivables, driven by collection days |
| `payables` | Trade payables, driven by payment days |
| `current_portion_lp` | Current portion of long-term debt |
| `cash` | Cash and equivalents, verified against the cash flow bridge |

## Decision inputs

| Field | Unit | Notes |
|---|---|---|
| `prices` | EUR per unit | Constrained to ±15% versus the prior period |
| `production_units` | units | `0` keeps the previous year's plan, `1` stops the line |
| `maintenance_pct` | % of gross factory assets | Range 1–7% |
| `discount_pct` | % | Channel discount, 7–25% |
| `capex_selected` | EUR | Sum of accepted project investments |
| `ampliacion_capacidad` | level | 0–3 per line, each level adds published capacity |

Two decision schemas exist in the source history and are normalised into a single
record: the legacy form (`decisiones.ventas.precio_unitario`) and the round-based
form (`modulos.ventas.precios_venta_unitario`).

## Forecast metrics

| Metric | Unit | Definition |
|---|---|---|
| `mape` | % | Mean absolute percentage error across periods |
| `bias` | % | Mean signed error; positive means under-forecast |
| `abs_error` | EUR | Absolute error in currency units |
| `fold` | — | `F1` = train ≤2027, `F2` = train ≤2028 |
| `regime` | — | `A` = decision-conditional, `B` = decision-free |
