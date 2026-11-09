# Methodology

This document describes how the numbers in this repository are produced, and why
each modelling choice was made. It is written for a reviewer who wants to
reproduce the result or challenge the assumptions.

## 1. Two layers, one source of truth

| Layer | Purpose | Status |
|---|---|---|
| **Data foundation** | Turn raw source workbooks into a traceable, validated financial history | Implemented |
| **FP&A layer** | Forecast, backtest and variance decomposition on top of that history | In progress |

The foundation never interprets business meaning; the FP&A layer never reads raw
workbooks directly. Every number has a `source_id`, a sheet and a cell.

Two identities travel with each source, and they answer different questions:

| Field | Stable? | Used for |
|---|---|---|
| `source_id` (`SRC-XLSX-004`) | No — enumerated in discovery order | Human-readable references in reports |
| `source_key` (`matriz_general_3`) | Yes — derived from the path inside `data/` | Precedence and sheet aliases in `config/f2.toml` |

Configuration never binds to the enumerated id. When a new closing workbook lands,
discovery is case-insensitive and every binding resolves through `source_key`, so an
existing workbook keeps its role. Unresolvable keys are reported in the F2 manifest
rather than silently dropped; `tests/test_source_identity.py` pins the contract.

## 2. Data foundation

### 2.1 Literal extraction

Each source workbook is exported cell by cell into Markdown, one file per sheet,
plus a `cell_index.csv` that maps every Markdown row back to its Excel coordinate.
The extractor does not evaluate formulas, merge tables or infer periods. If a cell
contains a formula, the formula text is preserved verbatim and flagged.

This guarantees that the readable artefact and the computational layer cannot
disagree: both derive from the same immutable cells.

### 2.2 Canonical layer

The canonical layer assigns, for every non-empty cell:

- **period** — annual (`2026`) or quarterly (`2026-Q3`);
- **data type** — `real`, `budget`, `scenario` or `decision`;
- **metric** and **segment** — normalised label and product/scope;
- **value** and **normalisation status**.

Precedence between overlapping workbooks follows the rule *by year, metric and
period*: a later closing workbook wins over an earlier one for the same year,
but every version is retained.

### 2.3 Status vocabulary

Every figure carries an explicit epistemic status. No number is silently trusted.

| Status | Meaning |
|---|---|
| `confirmed` | Ties to a source cell and passes all applicable identities |
| `inferred_accepted` | Derived from confirmed inputs; the derivation is documented |
| `pending` | Source exists but is incomplete or contested |
| `accepted_exception` | Known deviation, documented and deliberately not corrected |
| `unreconciled` | Fails a reconciliation and is carried forward as a visible gap |

Any derived value that depends on an `unreconciled` input inherits the flag.

### 2.4 Tolerances

| Tolerance | Value | Rationale |
|---|---|---|
| Rounding | €0.005 | Absorbs source rounding at the cent |
| Reconciliation | €1.00 | Absorbs accumulated rounding in aggregates |

Tolerances are configuration, not corrections. The source is never edited to make
an identity hold.

### 2.5 Financial statements

The statement engine builds income statement, balance sheet, debt schedule and
cash flow from the canonical layer, then reconciles each line against the reported
figure. The cash flow is verified independently by rebuilding it from the balance
movements and comparing the closing cash balance.

## 3. FP&A layer (in progress)

### 3.1 Panel construction

Annual panel (2024–2029) and quarterly panel (20 quarters, 2024–2028) at product
level. Quarterly granularity is used for volume and revenue only; the full P&L is
annual, because quarterly statement depth is not available for the earliest years,
and 2029 has no quarterly sales sheet at all (L-12).

### 3.2 Variance bridge

Budget versus actual is exported as an additive bridge, never as a single
percentage. Each row of `fact_variance` is an impact on profit, so the rows of a
year add up exactly to the change in net income:

```
volume    = (Q_actual - Q_budget) * budget_unit_margin
price     = sum(q_i * (p_i - P_budget))
unit_cost = -sum(q_i * (u_i - U_budget))
mix       = gross_margin_variance - volume - price - unit_cost
opex      = -(actual - budget) per operating-expense line
other     = financial result, extraordinary result and taxes
```

`mix` is the exact closing item, which keeps the identity true even when the source
restates quantities. The budget publishes no quantities, so the committed volume is
the planned production in the decision log; a zero there means "keep the previous
plan", as the simulator defines it.

### 3.3 Driver-based forecasting

The forecast is **driver-based, not statistical**. With 20 quarterly observations,
a purely time-series model cannot be defended. Instead:

```
price, volume, product mix, unit cost, opex, capex
    -> revenue -> gross margin -> EBITDA -> net income -> cash
```

Each driver is explicit and editable. A statistical model is used only as an
independent cross-check, never as the primary engine.

### 3.4 Two forecast regimes

Both regimes use the same model. Only the information set changes.

| Regime | Information available | What it measures |
|---|---|---|
| **A — decision-conditional** | Target-year prices, planned production and marketing from the decision log, plus last closed unit costs | Value of knowing the levers |
| **B — decision-free** | The last closed year, held flat | Power of extrapolating the past |

Unit costs are carried from the last closed year in both regimes, because the log
does not publish them (L-18). They therefore cancel out of the delta, which measures
the value of price, volume and marketing decisions.

When a decision log contradicts the committed budget by more than 2% on implied
revenue, regime A is exported with `status_key = pending` instead of silently
producing a number that looks trustworthy (L-17).

### 3.5 Rolling-origin backtest

Evaluation uses an expanding window, so each fold only sees information that was
actually available at that point.

| Fold | Trains on | Predicts | Evaluated against |
|---|---|---|---|
| F1 | 2024–2027 | 2028 | Actual 2028 |
| F2 | 2024–2028 | 2029 | Actual 2029 |

**Vintage rule.** The cost structure must be recalibrated inside each fold using
only the last year available *at that fold*. Calibrating on the target year makes
the backtest circular and invalid.

### 3.6 Forecast metrics

| Metric | Definition | Why it matters |
|---|---|---|
| MAPE | Mean absolute percentage error per P&L line | Magnitude of the miss |
| Bias | Mean signed error | Reveals systematic over- or under-forecasting |
| Absolute error (€) | Error in currency units | A 5% miss on €155k is not a 5% miss on €1.2M |

Bias is reported alongside MAPE because a correctable systematic bias is a more
useful finding than a low average error.

### 3.7 Variance decomposition

Budget-vs-actual gaps are decomposed into volume, price, mix, cost and one-off
effects, so that the bridge closes to the reported figure with no residual. Section
3.2 defines the identity; `fact_variance` carries the result row by row.

## 4. Reproducibility

Every output under `outputs/` is generated, and therefore excluded from version
control. A clean checkout plus two commands reproduce the entire dataset:

```bash
uv sync --group dev
uv run python -m cg_01            # canonical layer + literal markdown
uv run python -m cg_01.fpa.marts  # statements + data/processed
```

Source hashes are recomputed at the end of every run and must remain unchanged.
