# Documentation index

Three kinds of documents live here, and they answer different questions.

## 1. The case study (read these)

| Document | Question it answers |
|---|---|
| [`engine.html`](engine.html) | Interactive map of the engine, from raw cells to the 2030 forecast |
| [`engine.es.html`](engine.es.html) | Mapa interactivo del motor en español |
| [`BRIEFING.md`](BRIEFING.md) | What is this company, what data exists and what does it cover? |
| [`methodology.md`](methodology.md) | How is every number produced, and why this way? |
| [`data_model.md`](data_model.md) | What tables does the analytics layer expose and at what grain? |
| [`data_dictionary.md`](data_dictionary.md) | What does each column, type and status mean? |
| [`limitations.md`](limitations.md) | What is broken, missing or assumed, and what is its impact? |

## 2. Delivery record (how it was built)

| Document | Content |
|---|---|
| [`estado_actual_f1.md`](estado_actual_f1.md) | Closed phases, verified figures and the 2029 close update |
| [`f2_2_scope.md`](f2_2_scope.md) | Scope proposal for the FP&A layer |
| `archive/` | Superseded planning notes, kept for traceability |

## 3. Source material (provenance, not analysis)

| Path | Content |
|---|---|
| `modules/Decisiones_matriz_1/` | Rules of each decision module, round 1 |
| `modules/Decisiones_matriz_2/` | Rules of each decision module, round 2 |
| [`Bitacora_Decisiones_Spain10_CORBATUL.md`](Bitacora_Decisiones_Spain10_CORBATUL.md) | Decision log and consequences, consolidated |

Nothing in this folder is a source of numbers. The only sources of numbers are the
files in `data/`, and every figure in the outputs carries a `source_id`, a sheet and a
cell.

## Reading order for a reviewer

1. Root `README.md` — the business problem and the headline findings.
2. `BRIEFING.md` — the dataset, in five minutes.
3. `methodology.md` — how the pipeline earns trust.
4. `limitations.md` — what it does not claim.
5. `data_model.md` — the contract with the dashboard.
