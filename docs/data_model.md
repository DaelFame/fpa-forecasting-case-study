# Data model — analytics layer

The Power BI report consumes a **galaxy schema**: six fact tables with distinct
grains, sharing conformed dimensions.

This document is the contract between the Python ETL and the dashboard. Every
table described here is written to `data/processed/` as CSV and loaded by Power BI
through the `pDataFolder` parameter.

## Why a galaxy and not a single star

The business has processes with genuinely different grains:

- sales happen per **quarter × product**;
- financial statements close per **year × line item**;
- the forecast lives per **year × line item × scenario × regime × fold**.

Forcing them into one fact would require inventing a grain that does not exist.
When there are several processes, there are several facts. That is a galaxy.

## Keys

Natural keys are used, stored as readable text (`2026-Q3`, `gross_profit`). At fewer
than 2,000 rows, integer surrogates add no value and make the CSVs unreadable when
reviewed in a pull request.

## Dimensions

### `dim_period.csv`

One row per period. Annual and quarterly periods coexist; the `grain` column keeps
them from being confused.

| Column | Type | Example | Notes |
|---|---|---|---|
| `period_key` | text | `2026-Q3` | Primary key |
| `grain` | text | `quarter` | `year` or `quarter` |
| `year` | int | 2026 | |
| `quarter` | int, nullable | 3 | Null for annual rows |
| `period_end` | date | 2026-09-30 | Used for sorting and time intelligence |
| `label` | text | `Q3 2026` | Display label |
| `is_closed` | bool | true | Actual reported data |
| `is_forecast` | bool | false | Projected data |

### `dim_product.csv`

| Column | Type | Example |
|---|---|---|
| `product_key` | text | `corbatas` |
| `label` | text | Neckties |
| `sort_order` | int | 1 |

### `dim_line_item.csv`

The P&L, cash-flow and debt hierarchy.

| Column | Type | Example | Notes |
|---|---|---|---|
| `line_item_key` | text | `gross_profit` | Primary key |
| `label` | text | Gross profit | |
| `statement` | text | `income_statement` | `income_statement`, `cash_flow`, `debt` |
| `section` | text | `margin` | Grouping for the bridge |
| `sign` | int | 1 | `-1` for costs, so a simple SUM nets correctly |
| `is_subtotal` | bool | true | Excluded from driver-level analysis |
| `display_order` | int | 30 | Presentation order |

### `dim_account.csv`

Balance-sheet accounts, separate from P&L line items because the grain and the
additivity rules differ.

| Column | Type | Example |
|---|---|---|
| `account_key` | text | `total_assets` |
| `label` | text | Total assets |
| `section` | text | `non_current_assets` |
| `is_total` | bool | true |

### `dim_scenario.csv`

| Column | Type | Example | Notes |
|---|---|---|---|
| `scenario_key` | text | `budget` | `actual`, `budget`, `forecast`, `upside`, `downside`, `stress` |
| `label` | text | Budget | |
| `is_committed` | bool | true | A committed plan vs a modelled scenario |
| `sort_order` | int | 2 | |

### `dim_status.csv`

Data provenance as a first-class dimension. This is what lets a viewer filter the
report to "only confirmed figures", which is a legitimate analytical requirement in
this dataset.

| Column | Type | Example |
|---|---|---|
| `status_key` | text | `unreconciled` |
| `label` | text | Unreconciled |
| `severity` | int | 3 |
| `description` | text | Fails a reconciliation and is carried forward as a visible gap |

### `dim_regime.csv`

| Column | Type | Example |
|---|---|---|
| `regime_key` | text | `A` |
| `label` | text | Decision-conditional |

### `dim_fold.csv`

| Column | Type | Example |
|---|---|---|
| `fold_key` | text | `F1` |
| `label` | text | Train ≤2027, predict 2028 |
| `train_through` | int | 2027 |
| `target_year` | int | 2028 |

### `dim_driver.csv`

Sensitivity drivers.

| Column | Type | Example |
|---|---|---|
| `driver_key` | text | `unit_cost` |
| `label` | text | Unit cost |
| `unit` | text | `percent` |

## Facts

### `fact_financials.csv` — grain: period × line item × scenario

| Column | Type | Notes |
|---|---|---|
| `period_key` | text | FK → `dim_period` |
| `line_item_key` | text | FK → `dim_line_item` |
| `scenario_key` | text | FK → `dim_scenario` |
| `amount` | decimal | Signed EUR |
| `status_key` | text | FK → `dim_status` |

Annual grain. ~435 rows for 2024–2028 (29 line items × 5 years × 3 scenarios).

### `fact_balance.csv` — grain: period × account

| Column | Type | Notes |
|---|---|---|
| `period_key` | text | FK → `dim_period` |
| `account_key` | text | FK → `dim_account` |
| `amount` | decimal | EUR |
| `status_key` | text | FK → `dim_status` |

Annual grain, period-end snapshot. ~120 rows.

### `fact_sales.csv` — grain: quarter × product

| Column | Type | Notes |
|---|---|---|
| `period_key` | text | FK → `dim_period` (quarter grain) |
| `product_key` | text | FK → `dim_product` |
| `units_sold` | int | |
| `revenue` | decimal | Net of channel discount |

Quarterly grain. 20 quarters × 3 products = 60 rows. Cost is not available at
quarterly depth, so it lives in `fact_product_annual`.

### `fact_product_annual.csv` — grain: year × product

| Column | Type | Notes |
|---|---|---|
| `period_key` | text | FK → `dim_period` (year grain) |
| `product_key` | text | FK → `dim_product` |
| `revenue` | decimal | |
| `cost_of_sales` | decimal | Direct cost only |
| `gross_margin` | decimal | `revenue - cost_of_sales` |

Annual grain. 5 years × 3 products = 15 rows.

### `fact_market.csv` — grain: year × product

| Column | Type | Notes |
|---|---|---|
| `period_key` | text | FK → `dim_period` (year grain) |
| `product_key` | text | FK → `dim_product` |
| `market_units` | int | Total market demand |
| `company_units` | int | Units sold by the company |
| `demand_intent_units` | int | Stated purchase intent, where available |

Annual grain. ~45 rows.

### `fact_forecast.csv` — grain: period × line item × scenario × regime × fold

| Column | Type | Notes |
|---|---|---|
| `period_key` | text | FK → `dim_period` |
| `line_item_key` | text | FK → `dim_line_item` |
| `scenario_key` | text | FK → `dim_scenario` |
| `regime_key` | text | FK → `dim_regime` |
| `fold_key` | text | FK → `dim_fold` |
| `forecast_amount` | decimal | Model output |
| `actual_amount` | decimal | Real outcome for the same period |

Stores both sides so error is computed in DAX, not pre-computed in Python. ~580 rows.

### `fact_sensitivity.csv` — grain: driver × delta × line item

| Column | Type | Notes |
|---|---|---|
| `driver_key` | text | FK → `dim_driver` |
| `delta_pct` | decimal | -0.15, -0.10, 0, +0.10, +0.15 |
| `line_item_key` | text | FK → `dim_line_item` |
| `result_delta` | decimal | Change in the target metric vs the base case |

No period: this is a static scenario analysis. ~75 rows.

## Relationships

All relationships are **many-to-one, single direction**, from fact to dimension.

```
dim_period     1 ── *  fact_financials
dim_line_item  1 ── *  fact_financials
dim_scenario   1 ── *  fact_financials
dim_status     1 ── *  fact_financials

dim_period     1 ── *  fact_balance
dim_account    1 ── *  fact_balance
dim_status     1 ── *  fact_balance

dim_period     1 ── *  fact_sales
dim_product    1 ── *  fact_sales

dim_period     1 ── *  fact_product_annual
dim_product    1 ── *  fact_product_annual

dim_period     1 ── *  fact_market
dim_product    1 ── *  fact_market

dim_period     1 ── *  fact_forecast
dim_line_item  1 ── *  fact_forecast
dim_scenario   1 ── *  fact_forecast
dim_regime     1 ── *  fact_forecast
dim_fold       1 ── *  fact_forecast

dim_driver     1 ── *  fact_sensitivity
dim_line_item  1 ── *  fact_sensitivity
```

No relationship exists directly between two fact tables. Facts are never joined to
each other.

## Additivity rules

This is where most financial dashboards produce wrong numbers.

| Measure | Behaviour | Rule |
|---|---|---|
| Revenue, costs, units | Additive | SUM over period and product |
| Balance-sheet amounts | **Semi-additive** | Last value in period, never SUM over time |
| Cash balance | **Semi-additive** | Last value in period |
| Variance | Additive | Sum of differences |
| MAPE | **Non-additive** | Computed as ratio of sums, never average of ratios |

DAX guidance:

```dax
Closing Balance :=
CALCULATE ( SUM ( fact_balance[amount] ), LASTNONBLANK ( dim_period[period_key], 1 ) )

MAPE :=
DIVIDE (
    SUMX ( fact_forecast, ABS ( fact_forecast[forecast_amount] - fact_forecast[actual_amount] ) ),
    SUM ( fact_forecast[actual_amount] )
)
```

Averaging a column of percentages is the single most common error in forecast
accuracy reporting.

## Traps to avoid

**Chasm trap.** `fact_financials` (period × line item) and `fact_sales`
(period × product) share only `dim_period`. A visual mixing both, filtered by
product, will not propagate that filter. Keep one fact per visual.

**Fan trap.** `dim_line_item` fans out to `fact_financials`, `fact_forecast` and
`fact_sensitivity`. Filtering one fact by a dimension reached through another
produces double counting.

**Rule:** one fact per visual; dimensions cross, facts never do.

## Annual vs quarterly

The annual figure is authoritative and is **not** the sum of its quarters in this
dataset. Both grains are stored in `dim_period` with an explicit `grain` column so
that a filter can never silently mix them. Any measure that aggregates across
grains must filter on `dim_period[grain]` first.

## Implementation status

| Table | Status |
|---|---|
| 9 dimensions | Produced |
| `fact_financials` | Produced — 177 rows (5 years actual + 3 years budget) |
| `fact_balance` | Produced — 115 rows |
| `fact_sales` | Produced — 60 rows |
| `fact_product_annual` | Produced — 15 rows |
| `fact_market` | Pending — the market sheet stacks three blocks and needs block disambiguation |
| `fact_forecast` | Pending — needs the forecast engine |
| `fact_sensitivity` | Pending — needs the sensitivity engine |

## Adding a new year

1. Drop the workbook and the decision log into `data/`.
2. Add the year to `config/f2.toml` under `[periods]`, `[precedence]` and, if the
   workbook renames sheets, `[sheet_aliases]`.
3. Run the pipeline.

The export is driven by the configuration, so the new year flows into
`dim_period` and every fact without a code change. Dashboard visuals must
therefore never hardcode a year: use "latest closed period" measures instead.
