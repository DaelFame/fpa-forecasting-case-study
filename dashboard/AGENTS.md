# Rules for the Power BI report

Permanent rules for any change to `FPA_Case_Study.Report` or
`FPA_Case_Study.SemanticModel`. They override convenience and speed.

## Rule 1 - Every number, label and tooltip must be verified against live DAX

Before writing, keeping or validating any title, subtitle, tooltip, takeaway or
closing sentence, the number or claim behind it must be executed against the live
semantic model.

1. When Power BI Desktop has the project open, connect with `powerbi-modeling-mcp`:
   `connection_operations` -> `ListLocalInstances`, then `Connect` with the
   returned `connectionString`.
2. Run `dax_query_operations` -> `Execute` with an `EVALUATE` query that returns
   the exact figure the text claims, at the exact grain the visual shows.
3. Write the text only from that result. Do not infer, extrapolate or reuse a
   figure from another page, another year or another measure.
4. If no live model is available, do not guess: mark the claim as unverified and
   ask, or leave the text unchanged.

Recurring traps this rule exists to catch:

- `[Closing Cash]` is a point-in-time balance. It is never additive across years.
- `fact_sales` covers 2024-2028 only, while the P&L and product tables reach 2029.
  Any unit-based claim stops at 2028.
- `[Latest Closed Year]` is 2029; 2030 is the only forecast year.
- Budget data starts in 2026. There is no budget for 2024 or 2025.

## Rule 2 - The report is English only

Every user-facing string in the PBIR files is English: page names, visual titles
and subtitles, card labels, matrix headings, tooltips, button text and closing
paragraphs.

No Spanish, no mixed-language labels, and no untranslated leftovers from an
earlier draft. A Spanish Power BI Desktop UI (`Filtros`, `Insertar`) is
application chrome and is not part of the report.

When a string is added or edited, re-read the surrounding visual JSON and confirm
the whole visible text block is English before validating.
