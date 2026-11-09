# Page 01 — Executive Summary: build sheet

Follow top to bottom. Each step is one action. Do not skip ahead.

Canvas: **1920 × 1080**. Page background `#F5F7FA` (from the theme).

---

## Step 0 — Rename the pages

Double-click each tab at the bottom and set:

```
01 Summary
02 Profitability
03 Variance
04 Forecast
05 Market
```

Long names do not fit the sidebar.

---

## Block A — Sidebar and navigation

### A1. Background rectangle

`Insertar → Formas → Rectángulo`

| Property | Value |
|---|---|
| X | 0 |
| Y | 0 |
| Width | 180 |
| Height | 1080 |
| Fill | `#1F3864` |
| Border | off |
| Rounding | 0 |

### A2. Page navigator

`Insertar → Botones → Navegador → Navegador de páginas`

| Property | Value |
|---|---|
| X | 12 |
| Y | 24 |
| Width | 156 |
| Height | 600 |

In Format:

- Font: Segoe UI Semibold, 11
- Text colour: `#FFFFFF`
- Fill: transparent
- Active item fill: `#2E75B6`
- Active item text: `#FFFFFF`
- Alignment: left, padding 12

---

## Block B — Header

### B1. Title

`Insertar → Cuadro de texto`

| Property | Value |
|---|---|
| X | 196 |
| Y | 24 |
| Width | 900 |
| Height | 32 |

Text: `FP&A Case Study · Fashion Accessories`
Font 16, Semibold, `#1F3864`

### B2. Subtitle

| Property | Value |
|---|---|
| X | 196 |
| Y | 56 |
| Width | 900 |
| Height | 20 |

Text: `Five years of statements · four planning cycles`
Font 11, Regular, `#8C8C8C`

### B3. Latest closed year card

`Insertar → Tarjeta` (Card)

| Property | Value |
|---|---|
| X | 1140 |
| Y | 24 |
| Width | 180 |
| Height | 64 |
| Field | `_Measures[Latest Closed Year]` |
| Label | `Last closed year` |

Format: background `#FFFFFF`, border `#E6E9EF`, radius 8, callout 24, label 9.

---

## Block C — KPI strip

Y = **112**, height = **160**, width = **328** for all five.

| # | X | Measure | Label |
|---:|---:|---|---|
| C1 | 196 | `Revenue Latest` | Revenue |
| C2 | 540 | `Gross Margin % Latest` | Gross margin |
| C3 | 884 | `Net Income Latest` | Net income |
| C4 | 1228 | `Net Income vs Budget % Latest` | vs budget |
| C5 | 1572 | `Closing Cash Latest` | Closing cash |

For every card:

- Background `#FFFFFF`, border `#E6E9EF`, radius 8
- Callout 32, Semibold, `#1F3864`
- Label 10, `#595959`, positioned above the value
- Category label: **off**
- Title: **off**

Only C4 gets conditional colour:
`Format → Callout value → fx → Rules` → if value < 0 then `#C00000`, else `#4E7A4E`.

**Checkpoint:** C1 must show the latest year revenue (a few million), not ~20 M.
If it shows ~20 M it is summing every year and the measure is wrong.

---

## Block D — Revenue and net income

`Insertar → Gráfico de líneas y columnas agrupadas`

| Property | Value |
|---|---|
| X | 196 |
| Y | 288 |
| Width | 1180 |
| Height | 560 |

Fields:

| Well | Field |
|---|---|
| X axis | `dim_period[year]` |
| Column Y | `Revenue` |
| Line Y | `Net income` |

Visual filter: `dim_period[grain] = "year"`.

Format:

- Both series share one Y axis (both are EUR). **Do not enable a secondary axis.**
- Title: `Revenue and net income` (16, Semibold, `#1F3864`)
- Gridlines off, axis titles off
- Legend: on, bottom, 10
- Column colour `#1F3864`, line colour `#E8A33D`, line width 3
- Data labels: columns on (9), line off

---

## Block E — Gross margin

`Insertar → Gráfico de líneas`

| Property | Value |
|---|---|
| X | 1392 |
| Y | 288 |
| Width | 508 |
| Height | 560 |

Fields:

| Well | Field |
|---|---|
| X axis | `dim_period[year]` |
| Y | `Gross Margin %` |

Visual filter: `dim_period[grain] = "year"`.

Format: title `Gross margin %`, line `#2E75B6` width 3, markers only on the last
point, gridlines off, data labels on (9, `0.0%`).

---

## Block F — Takeaway

`Insertar → Cuadro de texto`

| Property | Value |
|---|---|
| X | 196 |
| Y | 864 |
| Width | 1704 |
| Height | 184 |

Text, 14 pt, `#1F3864`, left aligned, vertically centred:

> The company moved from a €196K loss in 2024 to a €2.39M pre-tax profit in 2029.
> Gross margin drove it, not volume: 35% to 57%.

Background `#FFFFFF`, border `#E6E9EF`, radius 8.

---

## Final checklist

- [ ] Five page tabs renamed
- [ ] Sidebar and navigator present, active page highlighted
- [ ] Five cards, correct measures, no red, values from the latest year
- [ ] Revenue and net income share one axis
- [ ] Gross margin line has markers only at the end
- [ ] Takeaway reads as a finding, not a label
- [ ] Nothing touches the 32 px margin
- [ ] No gridlines anywhere
- [ ] Page fits without scrollbars (View → Fit to page)
