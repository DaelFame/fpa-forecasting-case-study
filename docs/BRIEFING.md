# Interview Briefing — FP&A Case Study

Study document for defending this repository in an FP&A interview.
Every figure is cited as `file:line`.

**Citation convention.** Files under `outputs/` are generated and excluded from
version control. They are reproducible with `uv run python -m cg_01`. A citation
into `outputs/` is therefore verifiable only after one pipeline run; this is stated
where it matters. Files under `data/`, `src/`, `docs/` and `config/` are committed
and citeable directly.

---

## 1. The dataset

### What is in `data/`

| File | Role | Coverage |
|---|---|---|
| `Matriz_General_0.xlsx` | Round workbook: history + results | Close 2024–2025 |
| `Matriz_General_1.xlsx` | Round workbook | Close 2026, budget 2026 |
| `Matriz_general_2.xlsx` | Round workbook | Close 2027, budget 2027 |
| `Matriz_general_3.xlsx` | Round workbook | Close 2028, budget 2028 |
| `Bitacora_decisiones_para_2026.json` | Decision log | Inputs for 2026 |
| `Bitacora_decisiones_para_2027.json` | Decision log | Inputs for 2027 |
| `Bitacora_decisiones_para_2028.json` | Decision log | Inputs for 2028 |

Verified coverage: `real` 2024–2028 (annual and quarterly), `budget` 2026–2028,
`decision` 2026–2028, `scenario` 2029–2031. Summary available in
`outputs/f1/inventory.json` after a pipeline run.

### "Matriz" and "bitácora"

These are the simulation's words, not finance words.

- **Matriz** = the results workbook returned after a round is resolved. Eleven
  sheets, one per business area: `Marketing`, `Produccion`, `Logistica`,
  `Mercado`, `Ventas`, `Ingresos`, `Margen`, `Resultados`, `Balance`,
  `Indicadores Clave`, `Valor de la compañía`.
- **Bitácora** = the decision log. The inputs chosen *before* the outcome existed:
  prices, production units, capex projects, channel discount, financing.

The distinction is the whole foundation of the project: **the bitácora is the
budget, the matriz is the actual.**

**Interview translation.** Never say "matriz" or "bitácora" to a finance
interviewer. Say *results workbook* and *decision log*, or *plan inputs* and
*reported actuals*.

---

## 2. Anatomy of the two artefacts — a real 2026 example

### The decision log (inputs)

`data/decisiones/Bitacora_decisiones_para_2026.json`:

| Field | Line | Value |
|---|---|---|
| Tie price | 7 | €17.20 |
| Scarf price | 8 | €28.90 |
| Sock price | 9 | €3.00 |
| Channel discount | 21 | 15% |

### The results workbook (outputs)

`outputs/f2/income_statement.csv` (generated):

| Metric | Line | 2026 |
|---|---|---|
| Revenue — ties | 28 | €3,067,349 |
| Revenue — scarves | 26 | €709,833 |
| Revenue — socks | 27 | €83,857 |
| Revenue — total | 29 | €3,861,039 |
| Cost of sales | 5 | €2,048,743 |
| Gross profit | 13 | €1,812,296 |
| Operating expenses | 23 | €1,646,127 |
| Net result | 21 | €154,951 |

### The chain that proves the model is real

Units sold 2026, ties: `209,805` — `outputs/f1/canonical_points.csv:2294`.

```
209,805 units × €17.20 × (1 − 0.15) = €3,067,349.10
```

That matches revenue for ties exactly (`income_statement.csv:28`). And:

```
3,067,349 + 709,833 + 83,857 = 3,861,039
```

This is the single best thing to show in an interview: **price × volume ×
(1 − discount) reconciles to the reported revenue, to the euro.**

---

## 3. Five concepts you must be able to defend

### (a) Budget vs actual: why 2026 closed 61% below plan with revenue on plan

Revenue landed within **0.94%** of budget:

| Item | Budget | Line | Actual | Line |
|---|---|---|---|---|
| Revenue | €3,825,241 | `canonical_points.csv:1574` | €3,861,039 | `income_statement.csv:29` |
| Net result | €398,088 | `canonical_points.csv:1608` | €154,951 | `income_statement.csv:21` |

Net variance: **−€243,137 (−61.1%)**.

The bridge, which closes to the euro:

| Driver | Budget | Actual | Variance |
|---|---|---|---|
| Gross profit | €1,737,839 (`:1582`) | €1,812,296 (`:13`) | **+€74,457** |
| General expenses | €141,793 (`:1594`) | €344,808 (`:11`) | **−€203,015** |
| R&D | €156,000 (`:1588`) | €249,240 (`:25`) | **−€93,240** |
| Personnel | €642,946 (`:1586`) | €678,298 (`:24`) | −€35,352 |
| Insolvency | €0 | €5,781 (`:15`) | −€5,781 |
| Depreciation | €125,500 | €148,000 (`:6`) | −€22,500 |
| **Total operating expenses** | **€1,286,239** (`:1596`) | **€1,646,127** (`:23`) | **−€359,888** |
| Financial result | −€53,512 | −€29,218 (`:10`) | +€24,294 |
| Extraordinary result | €0 | €18,000 (`:7`) | +€18,000 |
| **Net variance** | | | **−€243,137** |

Arithmetic check: `74,457 − 359,888 + 24,294 + 18,000 = −243,137`.

**The sentence that wins the interview:** *"Revenue was on plan; the entire miss
was operating expense discipline, and €150,000 of it has no documentary support."*
That last part is limitation L-02, `docs/limitations.md:35`.

### (b) Driver-based model: from price and volume to the P&L

A driver-based model does not extrapolate the P&L. It rebuilds it from the
operating levers:

```
price, volume, mix
  → revenue
  → cost of sales (unit cost × volume)
  → gross margin
  → opex (marketing, personnel, R&D, general)
  → EBITDA → depreciation → financial result → tax → net income
  → working capital → cash
```

The unit cost is decomposed in five components per product —
`src/cg_01/model/modelo.py:6` (`BASE`: raw material, labour, energy, direct
personnel, factory overhead).

Why it matters: when the P&L is rebuilt from drivers, a variance can be
**attributed**. "Revenue beat by €35,798" is reporting. "Revenue beat by €35,798
and opex overran by €359,888" is FP&A.

### (c) Out-of-sample backtest: why 2028 is the test year

A backtest is only meaningful if the target year was **not** used to fit the model.

2028 is the right test year because it is the last year where both sides exist:

- Budget: €1,153,267 — `canonical_points.csv:6052`
- Actual, pre-tax: €1,653,153 — `canonical_points.csv:6051`

Training window 2024–2027, prediction target 2028. The model never sees 2028.

**Correction to an earlier figure.** An earlier version of this analysis reported
the 2028 variance as **+7.5%**. That was wrong: it compared the **after-tax**
actual (€1,239,865, `canonical_points.csv:7637`) against a **pre-tax** budget.
The budget carries no tax line, so the only consistent comparison is pre-tax:
`1,653,153 / 1,153,267 − 1 = +43.3%`.

Correct budget-accuracy series, all on the same pre-tax basis:

| Year | Budget | Actual pre-tax | Variance |
|---|---|---|---|
| 2026 | €398,088 | €154,951 | **−61.1%** |
| 2027 | €277,098 (`:3569`) | €629,093 (`income_statement.csv:51`) | **+127.0%** |
| 2028 | €1,153,267 (`:6052`) | €1,653,153 (`:6051`) | **+43.3%** |

### (d) The circularity trap

`src/cg_01/model/modelo.py:5` says it in the source:

```
# ---------- Base calibrada en 2028 (unico anio con desglose completo) ----------
```

`BASE` (`:6`), `PROD_2028` (`:13`), `SOLD_2028` (`:15`), `REV_2028` (`:17`) and
`P2028` (`:59`) are all **calibrated from the 2028 close**.

If that model is used to forecast 2028, the forecast is the input restated. The
error would be near zero and completely meaningless.

**Vintage rule:** inside each backtest fold, the cost structure must be
recalibrated using only the last year available *at that fold* — 2027 for fold 1.

This is the most common methodological error in forecasting portfolios, and it is
the first thing a technically strong interviewer looks for.

### (e) Regime A vs regime B

| | Regime A — decision-conditional | Regime B — decision-free |
|---|---|---|
| Information | The actual decision log for the year | History and macro only |
| What it measures | Fidelity of the model to the business mechanics | Predictive power of the historical record |
| Comparable to | A budget / plan | A rolling forecast with no committed plan |
| Expected error | Low (single-digit %) | High (double-digit %) |

The **delta** between the two is the headline finding: how much forecast accuracy
comes from knowing the levers versus extrapolating the past.

**Honest status: this has not been computed yet.** Do not quote a number for the
delta in an interview. Say that the design is defined and the measurement is the
next step.

---

## 4. Glossary — 15 terms

| Term | Definition |
|---|---|
| **FP&A** | Financial Planning & Analysis: budgeting, forecasting and variance work, as opposed to accounting close. |
| **Budget** | The committed financial plan for a period, fixed before the period starts. |
| **Actual** | The reported outcome once the period closes. |
| **Variance** | The difference between actual and budget, expressed in currency and in percent. |
| **Bridge / waterfall** | A chart that decomposes the movement between two figures into its drivers, closing with no residual. |
| **Driver** | An operating lever (price, volume, unit cost) that mechanically explains a financial line. |
| **Gross margin** | Revenue minus cost of sales; expresses the profitability of what is sold before overhead. |
| **Contribution margin** | Price minus variable cost per unit; the amount each unit contributes to fixed costs. |
| **OPEX** | Operating expenses: the fixed and semi-fixed costs of running the business. |
| **EBITDA** | Earnings before interest, tax, depreciation and amortisation; a proxy for operating cash generation. |
| **Working capital** | Receivables plus inventory minus payables; the cash tied up in operating the business. |
| **CAPEX** | Capital expenditure: investment in long-lived assets, capitalised rather than expensed. |
| **Rolling forecast** | A forecast continuously updated for the next N periods, used when no plan is yet committed. |
| **MAPE** | Mean absolute percentage error: average size of the miss, ignoring direction. |
| **Forecast bias** | Mean signed error; reveals systematic over- or under-forecasting, which is correctable. |

---

## 5. Five likely interview questions

### Q1 — "Is this real company data?"

| | |
|---|---|
| **Bad** | "Yes, it's a real manufacturer." Falsifiable in one follow-up question, and it destroys credibility in the other two projects. |
| **Good** | "It's an anonymised case study built on a competitive business-simulation dataset. The company is anonymised; the origin isn't. What it demonstrates is the method: five years of statements, four planning cycles, and a forecast that can be backtested against real outcomes." |

### Q2 — "Why didn't you use ARIMA or machine learning?"

| | |
|---|---|
| **Bad** | "Because time series models are old." Shows no judgement. |
| **Good** | "Twenty quarterly observations cannot support a statistical model. A driver-based model is defensible because every assumption is explicit and attributable. I use time-series only as an independent cross-check on the driver output." |

### Q3 — "How do you know your model is right?"

| | |
|---|---|
| **Bad** | "It matches the historical data." That is fitting, not validation. |
| **Good** | "Out-of-sample backtest: fit on 2024–2027, predict 2028, compare against the actual close. And the cost structure is recalibrated inside the fold, so the model never sees the target year." |

### Q4 — "Your 2026 forecast missed by 61%. Why should I trust you?"

| | |
|---|---|
| **Bad** | "The simulation changed the rules." An excuse, not an analysis. |
| **Good** | "Because the miss is the finding. Revenue landed within 1% of plan; the entire gap was operating expense, €203k of it in general expenses and €93k in R&D, and €150k of that has no supporting documentation. That's exactly the kind of thing FP&A exists to catch before it compounds." |

### Q5 — "What would you do with more time or data?"

| | |
|---|---|
| **Bad** | "Add more charts." |
| **Good** | "A second backtest fold one year forward, a variance decomposition at product and channel level, and a driver-level confidence interval instead of point estimates. And I'd fix the taxonomic ambiguity in the market sheet before trusting elasticities from it." |

---

## 6. Known gaps — say these out loud before you are asked

| Gap | Where |
|---|---|
| 2028 was previously reported as +7.5% on a mixed tax basis; correct figure is +43.3% pre-tax | §3(c) |
| Regime A vs B delta not yet measured | §3(e) |
| 108 balance-sheet anomalies, 20 critical, all unreconciled | `docs/limitations.md:75` |
| 2026 revenue has a factor-of-100 ambiguity in the source | `docs/limitations.md:26` |
| €150,000 of 2026 general expenses has no documentary support | `docs/limitations.md:35` |
| Two conflicting 2029 macro series exist | `docs/limitations.md:83` |
| No competitor-level financials — benchmarking is market-share only | `docs/limitations.md:91` |
| Quarterly P&L depth only from 2026; volume and revenue only from 2024 | `docs/limitations.md:97` |

Declaring a limitation before the interviewer finds it converts a weakness into
evidence of rigour. Hiding one converts a strength into a credibility problem.
