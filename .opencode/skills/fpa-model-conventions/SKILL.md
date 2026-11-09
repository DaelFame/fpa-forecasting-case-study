---
name: FPA Model Conventions
description: Rules for the measures and semantic model of the FP&A Power BI report — additivity, naming, display folders and regeneration. Use when adding measures, changing the model, or validating the dashboard.
---

# FP&A model conventions

## Additivity

This is the rule that most dashboards get wrong.

| Kind | Columns | Rule | DAX |
|---|---|---|---|
| Additive | `fact_financials[amount]`, `fact_sales[units_sold]`, `fact_market[*]` | Sum freely | `SUM` |
| **Semi-additive** | `fact_balance[amount]` | Last value in period, never sum across time | `CALCULATE(SUM(...), LASTNONBLANK(dim_period[year], 1))` |
| **Non-additive** | MAPE, bias, margins % | Ratio of sums, never average of ratios | `DIVIDE(SUMX(f, ABS(f[error])), SUMX(f, ABS(f[actual])))` |

Summing a cash balance across six years produces a number with no meaning.
Averaging per-line percentage errors lets a €100 line outweigh a €1M line.

## Naming

| Rule | Example |
|---|---|
| No page prefix — the display folder already says it | `Revenue`, not `P1_Revenue` |
| Business language, not technical | `Net Income vs Budget`, not `NI_BDG_DIFF` |
| Percent measures end in `%` | `Gross Margin %` |
| One measure per business concept | Do not add `Revenue 2` |

Display folders, in this order:
`01 Executive`, `02 Profitability`, `03 Variance`, `04 Forecast`, `05 Market`,
`99 Format & SVG`.

Measures used only to draw an SVG go in `99 Format & SVG` and are hidden.

## Never hardcode a period

Titles and measures must derive the year:

```dax
Latest Closed Year =
CALCULATE(
    MAX ( dim_period[year] ),
    dim_period[grain] = "year",
    dim_period[is_closed] = TRUE ()
)
```

A measure containing `"2028"` will be wrong the moment a new close lands.

## Model rules

- **One fact per visual.** Dimensions cross; facts never do. Mixing
  `fact_financials` (year × line) and `fact_sales` (quarter × product) in one
  visual produces a chasm trap and silently wrong numbers.
- **Foreign keys are hidden on the fact side**, hidden and typed by the
  dimension. A type mismatch makes Power BI reject the relationship.
- **No calendar table.** `dim_period.period_end` repeats (annual and Q4 share
  31 December), so it cannot be a date-table key. Auto date/time stays off.
- **Equity uses `detailed_equity`,** not `reported_equity`: the latter carries a
  constant €246,390 with no counterpart in the detail (limitation L-13).
- **Variance is pre-tax.** The budget models no tax, so `fact_variance` closes
  to `net_result_before_taxes` exactly.

## Regeneration

The model is derived, never hand-edited, except `_Measures.tmdl`.

```bash
uv run python -m cg_01.fpa.marts    # rebuild the marts from the sources
uv run python -m cg_01.fpa.tmdl     # rebuild tables and relationships
uv run pytest -q                    # 81+ checks
```

`cg_01.fpa.tmdl` rewrites every table from the CSV headers, keeps hand-written
tables such as `_Measures`, and deletes Power BI auto date tables. Running it
after a mart change is not optional: the model would drift from the data.

## Validation before opening Power BI

```bash
uv run pytest tests/test_tmdl_model.py -q
```

It fails when a relationship points at a missing column, when the two sides have
different types, when a mart has no table, or when a CSV column never reaches
the model. All four only surface as a broken project otherwise.

## Known caveats to disclose, never hide

| Caveat | Where |
|---|---|
| Reported equity gap of €246,390 | L-13 |
| 2024 cash flow is partial (no 2023 close) | L-11 |
| 2029 has no quarterly sales | L-12 |
| 108 balance anomalies, all unreconciled | L-07 |
