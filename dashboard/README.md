# Power BI dashboard

This folder holds the Power BI project for the FP&A case study.

## Format: `.pbip`, never `.pbix`

The dashboard is versioned as a **Power BI Project (`.pbip`)**. The semantic model
is stored as TMDL and the report as text, so both are diffable and reviewable in a
pull request.

`.pbix` files are binary blobs: no diff, no review, no meaningful history. They are
excluded from version control.

```
FPA_Case_Study.pbip
FPA_Case_Study.SemanticModel/   # tables, relationships, DAX measures (TMDL)
FPA_Case_Study.Report/          # pages and visuals
screenshots/                    # exported PNGs, referenced from the root README
```

To save in this format: `File → Save as → Power BI Project (*.pbip)`. If the option
is not visible, enable it under `File → Options and settings → Options → Preview features`.

## Data source: a parameter, not a hardcoded path

Power BI stores absolute file paths when connecting to CSVs, which breaks for
anyone who clones the repository. All connections therefore go through a single
Power Query parameter:

| Parameter | Default value | Purpose |
|---|---|---|
| `pDataFolder` | `..\data\processed` | Folder containing the exported analysis tables |

Every table loads from `pDataFolder`. If the default does not resolve on your
machine, change that one value in `Transform data → Manage parameters`.

Data is never loaded directly from the raw Excel workbooks. The pipeline exports
small, purpose-built tables to `data/processed/` first, so the dashboard always
reflects a reproducible build rather than a manual refresh.

## Expected tables

| File | Grain | Used by |
|---|---|---|
| `pl_annual.csv` | Year × line item | Executive summary, P&L |
| `budget_vs_actual.csv` | Year × line item × scenario | Variance page |
| `panel_quarterly.csv` | Quarter × product | Seasonality |
| `forecast.csv` | Year × line item × scenario | Forecast page |
| `backtest.csv` | Fold × line item × metric | Forecast page |
| `market_share.csv` | Year × product | Market page |
| `sensitivity.csv` | Driver × delta | Sensitivity page |

Exact schemas are defined in `docs/data_dictionary.md`.

## Pages

| Page | Question it answers |
|---|---|
| 1. Executive summary | How did the business perform, and what drove it? |
| 2. P&L and variance | Where did the budget miss, line by line? |
| 3. Forecast | How accurate is the model, and what is the 2030 outlook? |
| 4. Sensitivity and decisions | What moves the result, and what is each decision worth? |

## Screenshots are mandatory

Reviewers do not install Power BI Desktop to look at a portfolio project. Every
page must be exported to `screenshots/` as a PNG and embedded in the root README,
plus a full PDF export of the report.

A dashboard nobody can see is a dashboard that does not exist.

## DAX conventions

- Measures over calculated columns wherever the value is aggregated at query time.
- One measure per business concept, named in business language (`Gross Margin %`,
  not `GM_PCT_Calc`).
- No hardcoded filter values; slicers and parameters drive the context.
- Time intelligence uses an explicit date table, not `AUTOEXISTING` on fact dates.

## Status

Not started. Depends on the analysis layer producing `data/processed/`.
