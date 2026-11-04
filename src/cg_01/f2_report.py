from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .f2_engine import F2Result, F2Row


CSV_FIELDS = [
    "section",
    "metric",
    "period",
    "value",
    "unit",
    "status",
    "source_anomaly_status",
    "reconciliation_status",
    "tolerance_eur",
    "source_primary",
    "source_cells",
    "pd_dependencies",
    "derived_from",
    "notes",
]


def _write_csv(path: Path, rows: list[F2Row]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_dict())


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _fmt(value: float | None) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _write_report(path: Path, result: F2Result) -> None:
    counts = Counter(row.status for row in result.rows)
    recon_counts = Counter(row.reconciliation_status for row in result.rows)
    lines: list[str] = [
        "# F2.1 — Motor financiero determinista",
        "",
        f"Generado: `{result.manifest['generated_at']}`",
        "",
        "## Resumen",
        "",
        f"- Filas: **{len(result.rows)}**.",
        f"- Anomalías de balance: **{len(result.balance_anomalies)}**; críticas: **{result.manifest['summary']['critical_balance_anomalies']}**.",
        f"- Tolerancia exacta: **{result.f2_config.exact_tolerance_eur:g} €**.",
        f"- Tolerancia de residual documentado: **{result.f2_config.documented_residual_eur:g} €**.",
        "",
        "### Estados de cifra",
        "",
        "| Estado | Filas |",
        "|---|---:|",
    ]
    for status in ("confirmed", "inferred_accepted", "accepted_exception", "pending", "unreconciled"):
        lines.append(f"| `{status}` | {counts.get(status, 0)} |")
    lines.extend(
        [
            "",
            "### Estados de conciliación",
            "",
            "| Estado | Filas |",
            "|---|---:|",
        ]
    )
    for status in ("exact", "documented_residual", "unreconciled", "not_applicable"):
        lines.append(f"| `{status}` | {recon_counts.get(status, 0)} |")
    lines.extend(
        [
            "",
            "## Tabla resumen de cifras y estados",
            "",
            "| Sección | Métrica | Periodo | Valor | Unidad | Estado | Anomalía fuente | Conciliación | Tolerancia € | Fuente | PD | Nota |",
            "|---|---|---:|---:|---|---|---|---|---:|---|---|---|",
        ]
    )
    for row in result.rows:
        lines.append(
            f"| `{row.section}` | `{row.metric}` | {row.period} | {_fmt(row.value)} | `{row.unit}` | "
            f"`{row.status}` | `{row.source_anomaly_status}` | `{row.reconciliation_status}` | "
            f"{row.tolerance_eur:g} | {_md(row.source_cells or row.source_primary)} | "
            f"{_md(row.pd_dependencies)} | {_md(row.notes)} |"
        )
    lines.extend(
        [
            "",
            "## Anomalías de balance",
            "",
            f"El modelo conserva **{len(result.balance_anomalies)}** anomalías de categoría balance; "
            f"**{result.manifest['summary']['critical_balance_anomalies']}** son críticas. Todas se marcan "
            "`source_anomaly_status=unreconciled` y no se corrigen.",
            "",
            "La lista completa, con ID, regla, hoja, celda, periodo y estado, está en `manifest.json`.",
            "",
            "## Conciliaciones",
            "",
            "| Métrica | Periodo | Diferencia | Estado |",
            "|---|---:|---:|---|",
        ]
    )
    for row in result.rows:
        if row.section != "reconciliation":
            continue
        lines.append(
            f"| `{row.metric}` | {row.period} | {_fmt(row.value)} | `{row.reconciliation_status}` |"
        )
    lines.extend(
        [
            "",
            "## Diagnóstico del puente de caja",
            "",
            "El residual anterior coincidía exactamente con la Depreciación Fábrica de Balance: "
            "278.100 € en 2026 y 327.300 € en 2027. No era una diferencia de fuente. La línea "
            "`Gastos de Depreciación` de Resultados (148.000 € y 136.750 €) no incluye la depreciación "
            "de fábrica, que está embebida en el coste de ventas. El puente anterior, por tanto, no "
            "incorporaba ese ajuste no-cash.",
            "",
            "Ahora se añade `factory_depreciation_cash` desde `Balance` (fila `Gasto Deprec Fabrica`): "
            "278.100 € en 2026 y 327.300 € en 2027. La depreciación total del puente queda en "
            "426.100 € y 464.050 €, coincidiendo con el incremento de Depreciación Acumulada del balance.",
            "",
            "Residual resultante: **1 € en 2026** (`documented_residual`) y **0 € en 2027** (`exact`). "
            "El residual de 1 € se conserva sin redondear ni corregir.",
            "",
            "## Filas unreconciled",
            "",
            "| Métrica | Periodo | Valor | Motivo |",
            "|---|---:|---:|---|",
        ]
    )
    for row in result.rows:
        if row.status != "unreconciled":
            continue
        lines.append(
            f"| `{row.metric}` | {row.period} | {_fmt(row.value)} | {_md(row.notes or row.source_anomaly_status)} |"
        )
    lines.extend(
        [
            "",
            "## Filas pending",
            "",
            "| Métrica | Periodo | Valor | PD |",
            "|---|---:|---:|---|",
        ]
    )
    for row in result.rows:
        if row.status != "pending":
            continue
        lines.append(
            f"| `{row.metric}` | {row.period} | {_fmt(row.value)} | {_md(row.pd_dependencies)} |"
        )
    lines.extend(
        [
            "",
            "## Lectura de estados",
            "",
            "- `confirmed`: dato directo de fuente; puede seguir dependiendo de una PD si se indica.",
            "- `inferred_accepted`: inferencia aceptada, como INT-003.",
            "- `accepted_exception`: excepción aceptada, como Q-009.",
            "- `pending`: depende de una PD o de una construcción no oficial.",
            "- `unreconciled`: anomalía de balance o derivado que depende de ella.",
            "",
            "## Limitaciones",
            "",
            "- Las 81 anomalías de balance siguen abiertas; no se corrigen ni se inventan valores.",
            "- PD-05: ingresos usan el valor normalizado aceptado; se conserva el bruto.",
            "- PD-06: gastos generales 2026 usan 344.808 con hipótesis de 150.000.",
            "- PD-07: CAPEX 1.133.000 sin causa documentada.",
            "- PD-09: pasivo corriente trimestral no se usa para la deuda anual.",
            "- PD-10: alias normalizados; `raw_text` se conserva en F1.2.",
            "- PD-11: fuera de este corte.",
            "- PD-15: sin capturas manuales en este corte.",
            "- PD-16/Q-009: producción de bufandas 2027 aceptada como excepción; no se generaliza.",
            "",
            "## Integridad",
            "",
            f"- Hashes sin cambios: **{all(source.hash_unchanged is True for source in result.pipeline.sources)}**.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_f2_outputs(result: F2Result, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sections = {
        "income_statement.csv": "income_statement",
        "balance.csv": "balance",
        "debt.csv": "debt",
        "cash_flow.csv": "cash_flow",
        "reconciliation.csv": "reconciliation",
    }
    for filename, section in sections.items():
        _write_csv(
            output_dir / filename,
            [row for row in result.rows if row.section == section],
        )
    (output_dir / "manifest.json").write_text(
        json.dumps(result.manifest, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    _write_report(output_dir / "report.md", result)
    return result.manifest
