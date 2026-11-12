---
name: Power BI Design System
description: Visual and layout rules for the FPA Power BI report — palette, grid, chart selection and formatting defaults. Use whenever building or reviewing a report page in dashboard/.
---

# Power BI design system

Every page in `dashboard/` follows this. Deviating is a bug, not a preference.

## Narrative hierarchy

Every page answers one question, in three levels:

| Level | Element | What it carries | Example |
|---|---|---|---|
| 1 | Page title | **The question** | `How did the business perform over the last five years?` |
| 2 | Chart titles | **The finding** | `Revenue almost doubled; profit arrived only in 2026` |
| 3 | Closing text box | **The answer** | `Revenue almost doubled and profit swung from −€196K to €2.39M` |

Rules:

- The page title is a question, never a noun phrase. `Profitability` is a tab name, not a page title.
- The question is identical to the one shown when hovering that item in the navigation. One sentence, two places.
- A chart title that could be guessed from the axis is a label, not a finding. Rewrite it.
- The subtitle carries scope and basis (`2024–2029 · pre-tax`), never a repeat of the field names.
- The closing text box states the answer with numbers that appear on the page.

## Canvas

| Property | Value |
|---|---|
| Size | 1920 × 1080 (16:9) |
| Page background | `#F5F7FA` |
| Outer margin | 32 px on all four sides |
| Gutter between visuals | 16 px |
| Columns | 12 |

Column width: `(1920 - 64 - 11×16) / 12 = 139.3 px`. Round to 139.

## Palette

| Role | Hex |
|---|---|
| Primary (titles, main series) | `#1F3864` |
| Secondary series | `#2E75B6` |
| Tertiary | `#5B9BD5` |
| Light / prior period | `#A9C7E8` |
| Negative / alert | `#C00000` |
| Warning / amber | `#E8A33D` |
| Positive | `#4E7A4E` |
| Neutral / text secondary | `#8C8C8C` |
| Card background | `#FFFFFF` |
| Card border | `#E6E9EF` |

Never introduce a colour outside this list. If a chart needs a ninth colour, the
chart has too many categories.

## Typography

| Element | Size | Weight | Colour |
|---|---|---|---|
| Page title | 16 | Semibold | `#1F3864` |
| Subtitle / context | 11 | Regular | `#8C8C8C` |
| Card label | 10 | Regular | `#595959` |
| Card value (callout) | 32 | Semibold | `#1F3864` |
| Axis labels | 9 | Regular | `#8C8C8C` |

One size per role across the whole report.

## Always remove

- Gridlines
- Axis titles (the chart title already says it)
- Legends when there is a single series
- The visual background when it sits on a card that already has one
- Borders on charts inside a card
- Default visual titles when a text box above the chart already names it

## Chart selection

| Question | Visual | Never |
|---|---|---|
| One number, one period | Card | Gauge |
| Trend over time | Line, smooth off, markers only on the last point | Area with 5 series |
| Rank across categories | Horizontal bar, sorted | Pie |
| Budget bridge | Waterfall | Stacked bar |
| Forecast vs actual | Scatter, with a 45° reference line | Dual axis |
| Composition over time | Stacked column, max 3 categories | 100% stacked with 6 |
| Detail table | Matrix, no gridlines, conditional formatting on variance | Table with 20 columns |

## Page pattern

```
┌──────────────────────────────────────────────────────────┐
│ Header: title + context + page navigator           96 px │
├──────────────────────────────────────────────────────────┤
│ KPI strip: 3 to 5 cards                           160 px │
├───────────────────────────────┬──────────────────────────┤
│ Primary visual                │ Secondary visual         │
│ (the thesis of the page)      │                          │ 428 px
├───────────────────────────────┼──────────────────────────┤
│ Supporting detail             │ Takeaway text card       │ 332 px
└───────────────────────────────┴──────────────────────────┘
```

Rules:

1. **One thesis per page.** If the page needs two theses, it is two pages.
2. **Five KPI cards maximum.** Eight numbers are not read.
3. **One protagonist visual per row.** Two competing charts halve the attention.
4. **Every page closes with a sentence**, not with a number.

## Cards

- Background `#FFFFFF`, border `#E6E9EF`, radius 8, shadow transparency 94.
- Label above the number, not below.
- Value right-aligned or left-aligned consistently across the strip, never mixed.
- Percentages use `0.0%`; currency uses `#,##0`; units use `#,##0`.

## Navigation

A single page navigator in the header, right-aligned. Native page navigator is
preferred: it highlights the active page and adapts when pages are added.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Slicer on every page | Filters belong in one place, or in no place |
| Dual-axis charts | The reader cannot compare scales |
| 3D anything | Distorts proportion |
| Rainbow palette | Colour stops meaning |
| Titles like "Chart 1" | A title is a finding, not a label |
| Hardcoded year in a title | Breaks when a new year lands; use `[Latest Closed Year]` |
