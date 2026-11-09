# The model, explained simply

This is the plain-language companion to [data_model.md](data_model.md). That one is
the contract; this one is the intuition.

## What the model is

Think of a filing cabinet.

- **The drawers have labels**: year, product, line item, scenario, account. Those are
  the **dimensions**. They hold no numbers, only the ways you can slice.
- **Inside the drawers are the numbers**: revenue, units, balances, forecast error.
  Those are the **facts**.

Every fact row carries the labels it belongs to. That is the whole idea. A fact
without a label is a number nobody can filter; a label without a fact is a column
nobody needs.

## The picture

```
        dim_period   dim_product   dim_line_item   dim_account
             \           |             |               |
              \          |             |               |
   fact_financials ──────┼─────────────┼───────────────┼── dim_scenario
   fact_balance ─────────┼─────────────┼───────────────┼── dim_status
   fact_sales ───────────┼─────────────┘               │
   fact_product_annual ──┼─────────────────────────────┘
   fact_market ──────────┼─────────────┐
   fact_variance ────────┼─────────────┼── dim_driver
   fact_backtest ────────┼─────────────┼── dim_fold, dim_regime
   fact_forecast ────────┴─────────────┴── dim_scenario, dim_fold, dim_regime
```

Read it as: **one arrow per question you can ask.**

- "Revenue by product" needs `fact_financials` + `dim_line_item`, filtered to the
  revenue lines.
- "Margin by product per year" needs `fact_product_annual`.
- "How wrong was the forecast" needs `fact_backtest`.

## Three rules that keep it honest

**1. One grain per fact.** A row of `fact_sales` is *one quarter of one product*.
A row of `fact_financials` is *one year of one line item*. If you cannot say that
sentence, it is not a fact table.

**2. Dimensions are shared, never duplicated.** `dim_product` is one table used by
four facts. If each fact had its own product list, "Corbatas" in one place and
"Corbatas " with a trailing space in another would silently break every total.

**3. Not every number adds up the same way.**

| Kind | Example | Rule |
|---|---|---|
| Additive | Revenue, units, costs | Sum across time freely |
| **Semi-additive** | Balance sheet, cash | Take the **last value** in a period, never sum |
| **Non-additive** | MAPE, margins % | Ratio of sums, never average of ratios |

Summing the cash balance of six years gives a number that means nothing. Averaging
six percentages gives a number that means less than nothing, because small items
dominate it.

## Why there is no calendar table (and no "auto date/time")

This is deliberate, not an oversight.

Power BI can generate a hidden daily date table automatically. Here it would be
wrong for two reasons:

1. **The facts are not daily.** The finest grain is a quarter. A daily calendar would
   be 2,190 rows to describe 20 quarters.
2. **`period_end` cannot be a date-table key.** The annual row `2026` and the
   quarterly row `2026-Q4` both end on 2026-12-31. Power BI requires unique dates in
   a date table, so `dim_period` can never be marked as one.

Instead, `dim_period` is a **period dimension**: `period_key` is the key
(`2026`, `2026-Q3`), `grain` keeps annual and quarterly rows from mixing, and `year`
and `quarter` are plain numbers you can sort and compare.

Time comparisons (year over year, quarter over quarter) are written as explicit
measures using those number columns — not with `SAMEPERIODLASTYEAR`, which needs a
real date table.

## Why eight facts instead of one

Because the business measures different things at different grains:

| Fact | One row is | Rows |
|---|---|---|
| `fact_financials` | one year, one P&L line, one scenario | 222 |
| `fact_balance` | one year, one account | 138 |
| `fact_sales` | one quarter, one product | 60 |
| `fact_product_annual` | one year, one product | 18 |
| `fact_market` | one year, one product | 18 |
| `fact_variance` | one year, one driver, one line | 48 |
| `fact_backtest` | one fold, one regime, one line | 60 |
| `fact_forecast` | one scenario, one regime, one line | 120 |

Trying to merge them would force a fake grain and produce a table where most cells
are empty and every total is ambiguous.

## The four traps this model avoids

**Type mismatch on the key.** `period_key` is text (`2026`, `2026-Q3`) because it
holds quarters. If a fact declared it as a number, Power BI would reject the
relationship. Every foreign key inherits its dimension's type, and a test pins it.

**Chasm trap.** Two facts that share only *some* dimensions cannot be joined
directly. `fact_financials` (year × line) and `fact_sales` (quarter × product) share
`dim_period` but not `dim_product`. A visual mixing both would not cross-filter
correctly. The rule: **one fact per visual; dimensions cross, facts never do.**

**Semi-additive balances.** Covered above. Use `LASTNONBLANK`, not `SUM`.

**The reported-equity gap.** `reported_equity` carries a constant €246,390 with no
counterpart in the detail. `detailed_equity` balances the sheet within €1. The model
uses that account, and the gap is documented as limitation L-13.

## Adding a new year

1. Drop the workbook and the decision log into `data/`.
2. Add the year to `config/f2.toml` (`periods`, `precedence`, and `sheet_aliases` if
   the workbook renames sheets).
3. Run the pipeline, then regenerate the model:

```bash
uv run python -m cg_01.fpa.marts
uv run python -m cg_01.fpa.tmdl
```

No Power BI clicking. The new year flows into `dim_period` and every fact.

## Six words worth knowing

| Word | Meaning here |
|---|---|
| **Grain** | What one row of a fact represents |
| **Conformed dimension** | One dimension shared by several facts |
| **Additive** | Sums correctly across time and categories |
| **Semi-additive** | Sums across categories, not across time |
| **Surrogate key** | A meaningless integer standing in for a natural key |
| **Star / galaxy** | One fact with dimensions / several facts sharing them |
