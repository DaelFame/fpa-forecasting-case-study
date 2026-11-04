# FP&A Analytics — Fashion Accessories Manufacturer

A financial analytics case study built on five years of statements (2024–2028) for a
mid-size European manufacturer of neckties, scarves and socks: canonical data layer,
budget-vs-actual reconciliation, driver-based forecasting and scenario analysis.

> **Data provenance.** An anonymised dataset from a competitive business simulation.
> The company is anonymised; the origin is not. See [docs/limitations.md](docs/limitations.md).

![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![uv](https://img.shields.io/badge/managed%20with-uv-black)

---

## The business problem

The company entered 2024 loss-making and margin-poor, and exited 2028 profitable and
structurally stronger. Between those two points sit four annual planning cycles,
each one a committed budget that was later measured against the real outcome.

The question this repository answers is not *"what happened"* — that is reporting.
It is:

1. **Which decisions** produced the margin expansion, and what did each one cost?
2. **How accurate** was the budgeting, and was the error random or systematic?
3. **What is the 2030 outlook** if the current strategy holds, and what breaks it?

## Key findings (verified against source)

### Margin expansion of 21.5 points, driven by price and product mix

| EUR | 2024 | 2025 | 2026 | 2027 | 2028 |
|---|---:|---:|---:|---:|---:|
| Revenue | 3,274,513 | 3,346,747 | 3,861,039 | 4,304,333 | 5,107,811 |
| Gross margin | 1,157,881 | 1,088,267 | 1,812,296 | 2,205,670 | 2,907,215 |
| Gross margin % | 35.4% | 32.5% | 46.9% | 51.2% | 56.9% |
| Net income | (196,177) | (105,110) | 154,951 | 629,093 | 1,239,865 |

### The 2026 miss was operational, not commercial

Revenue landed within **0.9%** of budget, yet net income missed by **61.1%**.

| Bridge to budget | EUR |
|---|---:|
| Gross margin beat | +74,457 |
| General expenses | (203,015) |
| R&D | (93,240) |
| Personnel | (35,352) |
| Depreciation | (22,500) |
| Provisions | (5,781) |
| Financial result | +24,294 |
| Extraordinary result | +18,000 |
| **Net variance** | **(243,137)** |

The entire miss sits in operating expense discipline, and `150,000` of the general
expense overrun has no documentary support (L-02). Budget accuracy then improved
from **−61.1% (2026)** to **+127.0% (2027)** to **+7.5% (2028)**.

### Demand exceeds capacity, not price

2028 market coverage, from the market sheet:

| Product | Market units | Sold | Share | Unserved |
|---|---:|---:|---:|---:|
| Neckties | 1,404,819 | 234,538 | 16.7% | 405,181 |
| Scarves | 187,758 | 37,815 | 20.1% | 112,242 |
| Socks | 242,675 | 88,670 | 36.5% | 77,325 |

**594,748 units of demand were not served** — a capacity constraint, which is what
makes the capacity-expansion decision a financial decision rather than an operational one.

## How it works

```
data/ (immutable source workbooks and decision logs)
   |
   +-- literal cell extraction ......... outputs/markdown/
   +-- canonical normalisation ......... period, data type, metric, value
   +-- validation rules ................ 20+ accounting and business identities
   +-- statement engine ................ income statement, balance, debt, cash flow
   |
   +-- FP&A layer ...................... panel -> forecast -> backtest -> variance
```

Every figure carries an explicit status — `confirmed`, `inferred_accepted`,
`pending`, `accepted_exception` or `unreconciled` — and derived values inherit the
weakest status of their inputs. No number is silently trusted, corrected or rounded
into place.

## Repository layout

```
config/              Analysis parameters and tolerances
data/                Immutable sources: workbooks, decision logs
docs/                Methodology, data dictionary, limitations
notebooks/           Exploratory review of the source matrices (01_revision_matrices.ipynb)
src/cg_01/
  loader.py          Source discovery, hashing, decision-log normalisation
  canonical.py       Period and metric classification
  validation.py      Accounting identities and business rules
  f2_engine.py       Financial statement construction and reconciliation
  model/             Reconstructed deterministic driver model
tests/               Test suite, including literal-fidelity checks
```

`outputs/` is generated and excluded from version control.

## Quickstart

```bash
uv sync --group dev
uv run python -m cg_01
uv run pytest -q
```

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

## Status

| Component | Status |
|---|---|
| Literal extraction, canonical layer, validation | Done |
| Income statement, balance, debt, cash flow reconciliation | Done — 2026–2027 |
| Dual decision-schema normalisation | Done |
| Deterministic driver model | Done — reconstructed from 2024–2028 |
| Annual and quarterly panel, 2024–2029 | In progress |
| Rolling-origin backtest (folds F1, F2) | In progress |
| Variance decomposition engine | In progress |
| Power BI dashboard | Planned |

## Method notes

- **Driver-based, not statistical.** With 20 quarterly observations a pure
  time-series model cannot be defended; drivers are explicit and editable, and the
  statistical model is only a cross-check.
- **Two forecast regimes.** Decision-conditional (plan known) versus decision-free
  (history only). The gap between them is the headline: how much accuracy comes from
  knowing the levers.
- **Bias over MAPE.** A correctable systematic bias is a more useful finding than a
  low average error.

Full detail in [docs/methodology.md](docs/methodology.md).

## Stack

Python 3.12 · pandas · numpy · openpyxl · pytest · Power BI · uv

## License

MIT — see [LICENSE](LICENSE).
