# Data provenance and limitations

## Origin of the data

The dataset is an **anonymised case study from a competitive business simulation**.
It models a mid-size European fashion-accessories manufacturer operating three
product lines (neckties, scarves, socks) over the 2024–2029 horizon.

What is anonymised: the company name, the simulation brand, and the identity of the
other participating teams.

What is **not** anonymised, and must never be presented as such: the origin. This is
not client data, not a real company's books, and not extracted from any ERP. Any
claim to the contrary is trivially falsifiable and would undermine the credibility
of the entire portfolio.

This is a feature, not a defect. The dataset is complete, internally consistent,
auditable end to end and free of the confidentiality constraints that make real
financial data unpublishable. What it demonstrates is the *method*.

## Known limitations

Each limitation is registered, quantified and carried forward as a visible gap. None
of them is silently corrected.

### L-01 — Revenue scale ambiguity (formerly PD-05)

The 2026 revenue total appears as `38,610.39` in one row and `3,861,039` in the rest
of the sheet: a factor-of-100 discrepancy. The normalised value `3,861,039` is used
for statements, and both the raw and normalised values are preserved separately.
Any downstream figure that depends on 2026 revenue inherits this caveat.

**Impact:** low for ratios, high for any absolute 2026 comparison.

### L-02 — Unsupported general expenses (formerly PD-06)

2026 general expenses report `344,808` against `194,808` in the administrative
breakdown. The `150,000` difference has no documentary support and is retained as a
user hypothesis.

**Impact:** it is the single largest driver of the 2026 budget miss, so it is
disclosed wherever that variance is presented.

### L-03 — Unexplained capex (formerly PD-07)

Fixed-asset movement in 2026 shows `1,533,000` against `400,000` of accepted
projects. `1,133,000` has no documented cause.

**Impact:** depreciation and cash flow projections for 2026–2027 are less reliable
than for later years.

### L-04 — Current liabilities do not fully reconcile (formerly PD-09)

2026 current liabilities report `297,748` against components totalling `221,457`
(a `76,291` gap). 2027 shows a similar mismatch. Tax accruals are not broken out.

**Impact:** the current ratio is indicative, not exact.

### L-05 — Company-value weights are a hypothesis (formerly PD-11)

No official formula or weighting for the composite company-value score exists in the
source. Any score presented is a documented assumption, not a reported figure.

**Impact:** the metric is excluded from the financial analysis and shown only as a
narrative indicator.

### L-06 — Production exception, 2027 scarves (formerly PD-16)

2027 reports `30,000` scarf units despite a production decision of `0` (which should
keep the prior plan). It is retained as an accepted exception and not generalised to
other years or lines.

**Impact:** the 2027 volume-mix attribution for scarves is flagged as uncertain.

### L-07 — Balance sheet anomalies

`142` balance-sheet anomalies are detected, `25` of them critical. All are marked
`unreconciled` and carried forward. The balance sheet is therefore usable for
structural analysis and trend, but is not an audited statement.

The critical ones are a property of the simulator, not of the parser: the source
reports `total assets ≠ non-current + current` in every workbook from 2024 to 2029.
It is reproduced identically across five independent files, which rules out a
transcription error on our side.

**Impact:** measures that depend on equity or total assets inherit the flag.

### L-08 — Conflicting macro series for 2029

Two sheets provide 2029 macro indicators that do not agree (GDP `3.2` vs `2.6`,
interest rate `5.2` vs `4.5`). Neither is authoritative in the source.

**Impact:** any forecast using macro drivers must resolve this first. Until then,
scenario drivers are documented explicitly rather than imported silently.

### L-09 — No competitor-level data

The market sheets provide aggregate market demand and the company's own results.
Individual competitor financials are not available, so benchmarking is limited to
market share and demand coverage, not peer financial ratios.

### L-10 — Quarterly statement depth

Quarterly data is reliable for volume and revenue from 2024, but the full income
statement only reaches quarterly depth from 2026. Quarterly analysis is therefore
restricted to seasonality and revenue, never to full P&L.

### L-11 — 2024 cash flow is partial

2024 is the first year with a reported close, so its opening cash position (the 2023
closing balance) is not in the dataset. Eight of the fifteen cash-flow rows for 2024
are therefore empty, and the operating, investing and financing bridges cannot be
closed for that year. The 2024 income statement, balance sheet and debt schedule are
complete.

**Impact:** cash-flow trend analysis starts in 2025. 2024 is used for revenue,
margin and balance structure only.

### L-12 — 2029 sales are reported annually, not quarterly

The 2029 closing workbook reports units sold per product **per year only**; the
quarterly sales sheet stops at 2028. The `2029-Q1..Q4` revenue per product does
exist, in the `Ingresos` sheet of the 2029 workbook.

`fact_sales` is the quarter × product fact and must carry both units and revenue, so
it keeps its grain for 2024–2028 only. Emitting 2029 revenue rows with empty units
would inject nulls into the fact; emitting units by assumption would invent data.
The 12 real 2029 quarterly revenue rows are therefore **deliberately excluded** from
that fact and the 2029 product volume, revenue and margin live in
`fact_product_annual` at year × product grain.

**Impact:** quarterly seasonality cannot be measured for 2029, and 2029 quarterly
revenue is available in `outputs/f1/canonical_points.csv` but not in the mart. Any
2029 quarter figure in a report must come from the canonical layer, not `fact_sales`.

### L-13 — Reported equity carries a constant €246,390 gap

The gap between reported equity and the detailed equity block is exactly `−246,390`
in **every** closed year, 2024–2029, not only in the last two. A residual identical
across six years is a fixed item, not accumulated error, and it has no counterpart in
the account detail (`balance_detail_residual` is 0 ± €1).

`detailed_equity` is the line that balances the sheet within €1. The model uses that
account; `reported_equity` is kept only for traceability.

**Impact:** any visual that pairs `total_assets` with `reported_equity` shows a
€246,390 discrepancy. It is disclosed deliberately rather than smoothed away.

### L-14 — Source identity must not depend on discovery order

Source ids (`SRC-XLSX-001…`) are enumerated in discovery order and shift when a new
workbook lands. Adding `Matriz_General_4.xlsx` in November 2026 renumbered the
existing matrices because plain filename sorting is case-sensitive.

Two guards now prevent it: discovery sorts case-insensitively, and every config
binding (`precedence`, `sheet_aliases`) keys on a stable `source_key` derived from
the file path. Unknown keys are reported in the F2 manifest instead of being
silently ignored, and a regression test pins the published id of each matrix.

**Impact:** none on the figures; it protects traceability across future close files.

### L-15 — Demand intent is published unevenly

The "Intención de Compra VS Ventas" table exists in the 2026, 2027 and 2028 close
files, in thousands for 2027 and in units for 2026 and 2028, and it does not exist
in the 2029 file. `fact_market` therefore carries demand and unserved units for
2026–2028 only. Market units, company units and market share are complete.

**Impact:** the demand-gap visual stops at 2028. The 2029 gap cannot be shown
without an assumption, so it is left empty.

### L-16 — Sales sheets stack several quarterly tables

The sales sheet carries real units, competitor shares and expired units in
consecutive blocks that the parser attaches to the same period. Summing every
quarterly row with a product label over-counts: 2028 corbatas would read `10,456`
instead of `234,538`.

`fact_sales` now keeps, per year and product, the quarterly series whose four
quarters add up to the annual total published in the same workbook. That is a
data-driven reconciliation, not a hardcoded row, but it depends on the annual total
being present. When it is missing, the series with the most quarters wins.

**Impact:** no impact on 2024–2028 under the current sources; a future workbook
without an annual total would need review.

### L-17 — The 2029 decision log does not reconcile with the close

The 2029 log records list prices of `16.20 / 27.00 / 3.08` and a 10% channel
discount, which implies a net price near `14.58`. The 2029 close reports unit
prices of `20.70 / 34.50 / 4.14` and an effective 15% discount, and the committed
budget revenue (`6,198,132`) matches the close, not the log.

The backtest uses the log on purpose: regime A is "decisions known", and the log is
the decision record. The contradiction is therefore surfaced as `status_key =
pending` for every F2-A row instead of being smoothed away, and the 2029 regime-A
error includes a data defect, not a model defect (L-17).

**Impact:** the F2 comparison A versus B is not a fair model test. The F1 fold,
where the log matches execution, is the one to read.

### L-18 — Unit costs are not a modelled decision

The decision log publishes prices, volumes, marketing and design, but not unit
costs. Both regimes therefore carry the last closed year's unit cost. Cost-side
decisions (factory modernisation, solar energy) are not translated into a cost
forecast, so they cancel out of the A/B delta and leave regime A with a gross-margin
error of about 10% in F1 even when its revenue error is 0.3%.

**Impact:** the backtest measures the value of knowing price, volume and marketing
levers. It does not measure the value of cost decisions.

### L-19 — The 2030 scenarios are explicit assumptions

There is no 2030 decision log. The macro block for 2030 exists twice in the last
workbook with different values (GDP `2.6` vs `1.2`, CPI `3.0` vs `2.2`), which is the
conflict already registered as L-08, so it is not used as a forecast input.

The 2030 scenarios are therefore documented assumptions applied to the drivers, not
source facts:

| Scenario | Price | Volume | Unit cost |
|---|---:|---:|---:|
| Base | ×1.00 | ×1.00 | ×1.00 |
| Upside | ×1.02 | ×1.05 | ×1.00 |
| Downside | ×0.98 | ×0.95 | ×1.00 |
| Stress | ×0.95 | ×0.90 | ×1.05 |

Regime A moves price and volume separately; regime B moves only volume, because a
decision-free forecaster does not know the price lever. Base is identical in both
regimes by construction: with no new decisions, knowing the levers adds nothing.

**Impact:** the scenarios bound the range, they do not predict it. Any change to
these multipliers is a change of assumption, not a data refresh.

## How these limitations are handled

1. Every affected figure carries an explicit status.
2. Derived values inherit the weakest status of their inputs.
3. Tolerances absorb rounding; they never mask a real gap.
4. Source files are immutable and their hashes are verified on every run.
5. Limitations are surfaced in the outputs, not only in this document.
