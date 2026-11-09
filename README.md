# FP&A Forecasting & Variance Analysis — Fashion Accessories Case Study

![CI](https://github.com/DaelFame/fpa-forecasting-case-study/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![uv](https://img.shields.io/badge/managed%20with-uv-black)
![Tests](https://img.shields.io/badge/tests-74%20passing-brightgreen)

A manufacturer of neckties, scarves and socks grew revenue 0.9% in 2026 and watched
net income fall 61%. A Python financial model rebuilt its statements from the raw
closing workbooks, traced the entire miss to operating expenses, and forecast the
next year's revenue within **0.3%** of the actual close — one year ahead, using only
information available at the time.

---

## The business problem

**1. Revenue grew. Profit collapsed.** In 2026 revenue landed within 0.9% of budget
while net income missed by 61.1%. The bridge is unambiguous:

| Bridge to budget, 2026 | EUR |
|---|---:|
| Gross margin beat | +74,457 |
| Operating expenses | (359,888) |
| Financial result | +24,294 |
| Extraordinary result | +18,000 |
| **Net variance** | **(243,137)** |

The market showed up. The cost discipline did not. Of the overrun, **€150,000 of
general expenses has no documentary support** — it is carried as a visible gap, not
smoothed away. Gross margin itself broke down into price +41,536, volume −2,607,
mix +1 and unit cost +35,527.

**2. The company was capacity-constrained, not demand-constrained.** In 2028 the
market could not serve **594,748 units** of demand: 405,181 neckties, 112,242
scarves, 77,325 socks. Market share was 16.7%, 20.1% and 36.5% — the ceiling was
production, which turns a commercial question into a capital-allocation decision.

**3. The budget was biased, not merely inaccurate.** Measured on profit before
taxes, actual versus budget ran −61.1% (2026), **+127.0% (2027)**, +43.3% (2028) and
+12.2% (2029). From 2027 onward the company systematically beat its own plan. That
is not noise: an under-budgeting habit hides capacity needs and understates cash.

## The methodology

**Rolling-origin backtest.** Two folds, each trained only on years that were already
closed:

| Fold | Trains on | Predicts | Evaluated against |
|---|---|---|---|
| F1 | 2024–2027 | 2028 | Actual 2028 |
| F2 | 2024–2028 | 2029 | Actual 2029 |

**Two information regimes, one engine.** Regime A knows the management decisions for
the target year — prices, planned production, marketing. Regime B knows only the last
closed year, held flat. The gap between them quantifies the value of knowing the
levers.

| Out-of-sample, 2028 | A — decisions known | B — decisions unknown |
|---|---:|---:|
| Revenue error | **0.3%** | 15.7% |
| Gross profit error | 9.9% | 24.1% |
| Net income error | 25.5% | 55.0% |
| Mean MAPE, 15 P&L lines | 26.6% | 32.3% |

Knowing the decisions cut the revenue error by **15.4 points — a 98% reduction**.
Both regimes share a negative bias (−22.8% and −30.4%): extrapolation systematically
under-forecasts a growing business, and bias is the finding, not the noise.

**Everything is auditable.** Every figure carries a source file, sheet and cell; every
statement line carries a status (`confirmed`, `inferred_accepted`, `pending`,
`unreconciled`); source hashes are verified on every run. When a decision log
contradicts the close — as the 2029 log does — the affected rows are exported as
`pending` instead of being quietly corrected.

## The 2030 outlook

Built from the executed 2029 close, with scenarios applied to the drivers:

| Scenario | Revenue | Gross margin | Net income | Net margin |
|---|---:|---:|---:|---:|
| Stress | 5,306,691 | 3,107,915 | 1,209,825 | 22.8% |
| Downside | 5,778,397 | 3,567,987 | 1,554,879 | 26.9% |
| **Base** | **6,206,656** | **3,879,909** | **1,788,821** | **28.8%** |
| Upside | 6,647,329 | 4,204,244 | 2,032,072 | 30.6% |

Base holds the current strategy: it is identical with and without knowledge of the
decisions, because no new decisions exist. The value of regime A appears only when a
decision changes. In the downside and stress cases the decision-free regime keeps
more profit, because regime A applies the price cut as well as the volume cut.

## Tech stack

- **Python 3.12** — pandas, NumPy, openpyxl. Driver-based model, no statistical black
  box: with 20 quarterly observations a time-series model cannot be defended, so the
  drivers are explicit and editable.
- **Galaxy-schema data marts** — 8 fact tables sharing 9 conformed dimensions,
  exported as CSV (`data/processed`) for Power BI. Zero orphan dimensions.
- **Git and CI** — 74 tests on GitHub Actions: accounting identities, referential
  integrity, exact variance tie-out, backtest coverage, source-identity regressions.
- **Power BI** — the `.pbip` project is versioned as text (TMDL); the report layer is
  in progress.

## Transparency

This is an **anonymised case study built on a competitive business simulation**, not
client data and not a real company's books. The simulation brand and the identity of
the other teams are removed; the origin is disclosed because claiming otherwise would
be trivially falsifiable.

What it demonstrates is the method: turning raw closing workbooks into an auditable
financial model, finding where the money went, and proving a forecast can be trusted
before it is used.

## Reproduce it

```bash
uv sync --group dev
uv run python -m cg_01            # canonical layer + literal cell export
uv run python -m cg_01.fpa.marts  # statements, marts and the 2030 forecast
uv run pytest -q                  # 74 tests
```

Start with [`docs/README.md`](docs/README.md) for the method, the data model and
every known limitation, or read the Spanish version at
[`README.es.md`](README.es.md).

## License

MIT — see [LICENSE](LICENSE).
