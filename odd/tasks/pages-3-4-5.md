# Feature: report pages 03 | Variance, 04 | Forecast, 05 | Market

Objective: turn the three empty report pages into data-bound, verified pages that
match the `01 | Summary` / `02 | Profitability` layout, then close the project.
Branch: `main` (uncommitted work; no commit without explicit approval).
Delivery strategy: `single-pr` not applicable — changes stay uncommitted.
Test runner: `uv run pytest -q`; PBIR checks via `powerbi-report-author validate`.

## Specs

- **S1** — `fact_forecast` holds 8 rows per line item (scenario `base`/`upside`/
  `downside`/`stress` × regime `A`/`B`, and `base A` = `base B` byte for byte), so
  summing it inflates 2030 eight times: revenue reads `48,145,031` instead of
  `6,206,656`. `[Forecast Amount]` must be scoped to one regime so a 2030 figure is
  a single forecast, not an eight-fold duplication. Verified targets for 2030 base:
  revenue `6,206,656`, gross profit `3,879,909`, net result before taxes `2,385,094`.
- **S2** — `03 | Variance` must answer one question and reuse the established
  skeleton: header textbox `(32,32) 920x72`, horizontal page navigator at
  `x=968..1748, y=48, 140x40` (active page `#1F3864`, others `#2E75B6`, arrow to the
  next page), four KPI cards at `y=120`, chart row at `y=312 h=404`, bottom row at
  `y=732 h=316`, takeaway textbox `(1124,732) 764x316`.
- **S3** — Verified variance figures for page 03, pre-tax: net income vs budget
  total `+867,945` (`+21.9%`), by year 2026 `-243,137`, 2027 `+351,995`,
  2028 `+499,886`, 2029 `+259,201`; `3 of 4` budget years ahead of plan.
  Bridge drivers: Extraordinary result `+572,000`, Unit cost `+551,368`,
  Volume `+255,229`, Financial result `+51,353`, Mix `-1`, Rounding `-1`,
  Price `-235,793`, Operating expenses `-326,210`.
  Operating-expense lines: General `-199,051`, R&D `-155,100` (model label reads
  `Rd expenses`), Insolvency `-25,832`, Depreciation `+19,000`, Personnel `+34,773`.
- **S4** — `04 | Forecast` uses the same skeleton and states the honest accuracy
  story on the committed regime: F1 (2028 fold) MAPE `13.1%`, bias `-8.8%`,
  accuracy `86.9%`; F2 (2029 fold) MAPE `23.8%`, bias `-21.4%`, accuracy `76.2%`;
  F3 has no actuals. The 2030 base case repeats 2029 almost exactly
  (revenue `6,206,656` vs `6,206,657`) and the scenario band is revenue
  `5.31M`-`6.65M`, net result `1.61M`-`2.71M`.
- **S5** — `05 | Market` uses the same skeleton and stops where the data stops:
  market units, company units and share cover `2024–2029`; demand and unserved
  units exist only for `2026–2028` (limitation L-15), so no 2029 gap is invented.
  Verified: 2028 unserved `594,748` across three lines (Neckties `405,181`,
  Scarves `112,242`, Socks `77,325`); 2028 demand `2,430,000`;
  2028 market served `1,835,252`; 2029 company units `410,046`;
  share 2028 Neckties `16.7%`, Scarves `20.1%`, Socks `36.5%`.
- **S6** — Every user-facing string is English (`dashboard/AGENTS.md` rule 2). The
  page name `05 | Market ` keeps its trailing space out of the report.
- **S7** — Every number, title, subtitle and takeaway is executed against the live
  model at the grain the visual shows before it is written (`dashboard/AGENTS.md`
  rule 1); unverified claims are not published.
- **S8** — Validation completes only with `powerbi-report-author validate` **and** a
  fresh screenshot of each built page, reviewed for overlap, clipping and wrong
  totals, with fixes applied and the loop repeated.
- **S9** — `dashboard/README.md` status reflects the three finished pages.
- **S10** — The five report screenshots in `assets/` are the only source for the
  README galleries and the portfolio case page. Each is a 1920x1080 crop of the
  page canvas (no Desktop chrome, no hover tooltip), captured after the last
  verified edit, and carries the current page copy and numbers.

## Tasks

| ID | Specs | Work | Route | Status |
|---|---|---|---|---|
| T1 | S1, S7 | Scope `[Forecast Amount]` to one regime; add forecast/backtest measures; verify 2030 totals | inline | done |
| T2 | S3, S7 | Add page-03 measures (opex variance, years ahead, card texts) | inline | done |
| T3 | S2, S3, S6 | Build `03 | Variance` visuals (nav, header, 4 cards, bridge bar, year matrix, opex bar, takeaway) | inline | done |
| T4 | S8 | Validate + screenshot + review page 03 | inline | done |
| T5 | S4, S7 | Add page-04 measures (scenario axis, latest-fold accuracy) and verify | inline | done |
| T6 | S2, S4, S6 | Build `04 | Forecast` visuals | inline | done |
| T7 | S8 | Validate + screenshot + review page 04 | inline | done |
| T8 | S5, S7 | Add page-05 measures (demand, unserved share, latest-year cards) | inline | done |
| T9 | S2, S5, S6 | Build `05 | Market` visuals + fix trailing space in page name | inline | done |
| T10 | S8 | Validate + screenshot + review page 05 | inline | done |
| T11 | S9 | Update `dashboard/README.md` status | inline | pending |
| T12 | S6, S9 | Replace automatic display units on pages 01/02 with literal `M` suffix | inline | done |
| T13 | S10 | Regenerate the five English screenshots in `assets/` and rebuild the README galleries | inline | done |

New measures are added to `_Measures.tmdl` (the only hand-edited model file per
`fpa-model-conventions`) and mirrored to the live model with
`powerbi-modeling-mcp` so previews render the same numbers.

## Log

### L1 — user request (verbatim)

> ahora deseo  y requiero el echo de pasar  las visalisacines  principalmente el
> echo crear  ya las paginas sigueinte tanto 3 4 y 5  paso a paso cada uno  pero
> el objetivo es ya temrianr este prpyecto

### L2 — discovery

- Pages 3/4/5 contain only five vertical `actionButton` navigation bars
  (`x=0, y=20..438, 180x104`); p1/p2 use the horizontal header navigator, so the
  vertical bars are replaced rather than kept.
- `fact_forecast` has 8 rows per 2030 line item; `base A` and `base B` are
  identical, so `[Forecast Amount]` must be regime-scoped (S1).
- `dim_line_item[label]` carries Spanish product labels (`Revenue corbatas`) and the
  `Rd expenses` typo; only expense labels reach the page-03 opex chart, and the
  takeaway names R&D without quoting the raw label.

### L3 — verification evidence (live model, `localhost:49870`)

- Variance by year and total as recorded in S3; `[Bridge Residual]` = 0 for every
  budget year.
- Backtest folds as recorded in S4.
- Market as recorded in S5.

### L4 — accuracy must describe one model, not two

`fact_backtest` holds 60 rows: 15 line items x 2 folds x 2 regimes, and the two
regimes are different forecasts (F2 revenue: A `5,085,180`, B `5,107,812` against
`6,206,657` actual). The original `[MAPE Weighted]` summed both, producing
`18.5%`/`22.0%` for a model that does not exist. Both ratio measures and every
backtest sum are now restricted to regime `A`, the regime `[Forecast Amount]`
already used, so the accuracy figure and the 2030 forecast come from the same
model. Corrected: F1 `13.1%` MAPE / `-8.8%` bias / `86.9%` accuracy; F2 `23.8%` /
`-21.4%` / `76.2%`.

### L5 — page 04 built; the display-unit suffix comes from the model culture

- `04 | Forecast` built and reviewed (15 visuals): scenario band, fold matrix,
  error-by-headline bar, 4 cards (`6,206,656` / `2,385,094` / `76.2%` /
  `-21.4%`), takeaway.
- The model culture is `es-PE`, so any automatic display unit renders its suffix
  in Spanish: the scenario and error charts printed `mill.` and then `milK`.
  English-only rule applies to rendered labels too, so the two charts now read
  `Scenario Revenue K`, `Scenario Net Result K` and `Backtest Error K` — the
  value is divided by 1000 in DAX and `K` is a literal in the format string, with
  `labelDisplayUnits: 1D` so nothing is divided twice. Pages 01 and 02 still use
  automatic units and are a follow-up (S9).
- The error chart title had claimed "every headline was called too low" while
  cost of sales was called `+101,109` high; rewritten to name that exception.
- Model edits must not put a `///` comment between a measure expression and its
  properties: TMDL then fails with `Unexpected line type: Property!` and the
  report will not render.

### L6 — page 05 reviewed; two defects found and fixed

- First render of `05 | Market` had a black error tile in the bottom-left chart:
  the visual referenced `Unserved Units K`, a measure that was never added to
  `_Measures.tmdl` (only `Unserved Units` existed). The measure now exists:
  `[Unserved Units] / 1000` with format `#,##0"K"`.
- Both page-05 charts showed only half their year labels (2024/2026/2028 on the
  share chart) because a numeric `dim_period[year]` category thins its axis
  labels in a horizontal bar chart. The category is now `dim_period[label]`, the
  text column that reads `2024`..`2029` at year grain and stays blank at quarter
  grain, so all six bars are labelled in order. Sorting stays on `year`.
- Re-rendered and reviewed: share `14.3%` (2024-2025, the published baseline),
  `15.7%`, `16.9%`, `19.7%`, `20.1%` (2029); unserved `600K`, `662K`, `595K`
  (2026-2028). Cards, matrix and takeaway unchanged and correct.

### L7 — pages 01 and 02 carried Spanish display units

- Page 01 printed `0.0 mill.` / `2.0 mill.` on its value axis and page 02 printed
  `10.33 mill.` / `2.69 mill.` as data labels, both from the `es-PE` culture.
  English-only rule 2 covers rendered labels, and the screenshots are now
  published, so both charts were converted the same way as pages 03-05:
  `Net Income M` and `Product Gross Margin M` divide by `1,000,000` and carry
  `M` as a literal suffix, `labelDisplayUnits: 1D`, value axis hidden.
- Verified against the live model before publishing: page 01 labels
  `-0.20M`, `-0.11M`, `0.15M`, `0.63M`, `1.65M`, `2.39M`; page 02 labels
  `10.33M`, `2.69M`, `0.03M`.

### L8 — screenshots regenerated as the single image source (S10)

- `assets/` now holds `01-summary.png` … `05-market.png`, all 1920x1080 crops of
  the page canvas. The old `1_Summary.png`, `2_Profitability.png`,
  `3 Variance.png`, `4 FOrecast.png` and `5 market.png` were stale (the page-05
  one showed the broken chart) and were deleted.
- The crop helper detects the page rectangle from the two full-width drop-shadow
  bands that bound the canvas and derives the height from the 16:9 page; the
  mouse is parked in a corner before each capture so no visual header or tooltip
  is caught in the frame.

