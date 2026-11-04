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

`108` balance-sheet anomalies are detected, `20` of them critical. All are marked
`unreconciled` and carried forward. The balance sheet is therefore usable for
structural analysis and trend, but is not an audited statement.

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

## How these limitations are handled

1. Every affected figure carries an explicit status.
2. Derived values inherit the weakest status of their inputs.
3. Tolerances absorb rounding; they never mask a real gap.
4. Source files are immutable and their hashes are verified on every run.
5. Limitations are surfaced in the outputs, not only in this document.
