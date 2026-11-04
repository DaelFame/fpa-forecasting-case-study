from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import F1Config
from .models import Anomaly, DecisionSummary, Observation, RawCell, SourceInfo
from .text import period_sort_key


INVENTORY_SCHEMA_VERSION = "f1.2"

_DOCUMENTED_LIMITATIONS = [
    ("PD-05", "Ingresos 2026: 38.610,39 en la fila de total frente a 3.861.039 en el resto de la hoja; inferencia de escala pendiente."),
    ("PD-06", "Gastos generales 2026: 344.808 de total frente a 194.808 de procesos administrativos; 150.000 atribuidos a central/taller sin evidencia documental."),
    ("PD-07", "CAPEX 2026: 1.533.000 de incremento (fábrica 1.308.000 + almacén 225.000) frente a 400.000 de proyectos; 1.133.000 sin causa documentada."),
    ("PD-09", "Pasivo corriente trimestral: 2026 total 297.748 vs componentes 221.457 (76.291); 2027 trimestral 313.036 vs componentes ~214.932-215.167, sin impuestos desglosados."),
    ("PD-10", "Alias de proveedores y textos: Economica/Económica y Estandar/Estándar."),
    ("PD-11", "No hay fórmula ni pesos oficiales del Valor de Compañía; los pesos son una hipótesis."),
    ("PD-15", "Las capturas Markdown manuales solo se normalizan cuando el periodo y el tipo de dato son explícitos."),
    ("PD-16", "Producción de bufandas 2027: 30.000 unidades con decisión 0, frente a 29.000 en 2026 y 32.000 en la documentación de Matriz 2; regla general sin explicar."),
]

_RULES = [
    ("PRICE-CORRIDOR", "Precios fuera del corredor configurado (±15% por defecto)."),
    ("PROD-ZERO-KEEP", "Semántica RG-02: 0 unidades a producir mantiene la producción anterior."),
    ("PROD-ONE-STOP", "Semántica RG-02: 1 unidad a producir detiene la producción."),
    ("PROD-RANGE", "Producción fuera del rango documentado 0..600.000."),
    ("OCCUPANCY-MIN", "Penalización por ocupación por debajo del mínimo según occupancy_penalty_mode (line/plant)."),
    ("BAL-*", "Identidades contables: activo, pasivo, patrimonio, corriente y pasivo corriente; impuestos opcionales si existen."),
    ("BAL-CROSS-BLOCK", "Misma cuenta con valores distintos en bloques del mismo periodo."),
    ("SCALE-100", "Dos totales del mismo periodo difieren en un factor ~100."),
    ("EXPENSE-GENERAL", "Total de gastos generales frente a su detalle administrativo."),
    ("CAPEX-CROSS", "Inmovilizado material frente a inversiones seleccionadas de la bitácora."),
    ("MAINTENANCE-CROSS", "Gasto de mantenimiento frente al porcentaje de la bitácora."),
    ("PRICE-CROSS", "Precios de la bitácora frente a Marketing."),
    ("PRODUCTION-CROSS", "Unidades a producir de la bitácora frente a Producción."),
    ("ALIAS-TEXT", "Variantes de escritura para el mismo valor normalizado."),
]


def _json_dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _csv_write(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def _coincident_groups(observations: list[Observation]) -> tuple[int, int]:
    groups: dict[tuple[str, str, float], list[Observation]] = defaultdict(list)
    for observation in observations:
        value = observation.numeric_value
        if value is None or not observation.period or not observation.label_normalized:
            continue
        groups[(observation.period, observation.label_normalized, round(value, 6))].append(observation)
    coincident = [
        items
        for items in groups.values()
        if len({(item.source_id, item.sheet, item.cell) for item in items}) > 1
    ]
    return len(coincident), sum(len(items) for items in coincident)


def _periods_by_type(observations: list[Observation]) -> dict[str, list[str]]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for observation in observations:
        if observation.period:
            grouped[observation.data_type].add(observation.period)
    return {
        key: sorted(values, key=period_sort_key)
        for key, values in sorted(grouped.items())
    }


def _severity_counts(anomalies: list[Anomaly]) -> dict[str, int]:
    counts = Counter(anomaly.severity for anomaly in anomalies)
    return {severity: counts.get(severity, 0) for severity in ("critical", "high", "medium", "low", "info")}


def build_inventory(
    *,
    config: F1Config,
    sources: list[SourceInfo],
    observations: list[Observation],
    anomalies: list[Anomaly],
    summaries: list[DecisionSummary],
    raw_cell_count: int,
    elapsed_seconds: float,
    markdown: dict[str, Any] | None = None,
) -> dict[str, Any]:
    coincident_groups, coincident_observations = _coincident_groups(observations)
    data_type_counts = Counter(observation.data_type for observation in observations)
    financial_counts = Counter(observation.financial_status for observation in observations)
    integrity_counts = Counter(observation.integrity_status for observation in observations)
    source_type_counts = Counter(observation.source_type for observation in observations)
    category_counts = Counter(anomaly.category for anomaly in anomalies)
    periods_by_type = _periods_by_type(observations)
    all_periods = sorted(
        {observation.period for observation in observations if observation.period},
        key=period_sort_key,
    )
    latest_real_year = max(
        (observation.year for observation in observations if observation.data_type == "real" and observation.year),
        default=None,
    )
    latest_decision_year = max(
        (summary.period for summary in summaries if summary.period), default=None
    )
    warnings = [
        f"{source.source_id}: {warning}"
        for source in sources
        for warning in source.warnings
    ]
    if latest_decision_year and latest_real_year and latest_decision_year > latest_real_year:
        warnings.append(
            f"El último cierre real es {latest_real_year}, pero existen decisiones hasta "
            f"{latest_decision_year}; no son resultados financieros validados."
        )
    return {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "config": {
            "data_dir": str(config.data_dir),
            "output_dir": str(config.output_dir),
            "markdown_dir": str(config.markdown_dir),
            "min_year": config.min_year,
            "max_year": config.max_year,
            "price_corridor_pct": config.price_corridor_pct,
            "occupancy_threshold_pct": config.occupancy_threshold_pct,
            "occupancy_penalty_mode": config.occupancy_penalty_mode,
            "occupancy_cost_mode": config.occupancy_cost_mode,
            "balance_tolerance_eur": config.balance_tolerance_eur,
            "alias_count": len(config.aliases),
        },
        "sources": [source.to_dict() for source in sources],
        "summary": {
            "source_count": len(sources),
            "raw_cell_count": raw_cell_count,
            "observation_count": len(observations),
            "anomaly_count": len(anomalies),
            "coincident_groups": coincident_groups,
            "coincident_observations": coincident_observations,
            "observations_by_data_type": dict(sorted(data_type_counts.items())),
            "observations_by_source_type": dict(sorted(source_type_counts.items())),
            "observations_by_financial_status": dict(sorted(financial_counts.items())),
            "observations_by_integrity_status": dict(sorted(integrity_counts.items())),
            "anomalies_by_severity": _severity_counts(anomalies),
            "anomalies_by_category": dict(sorted(category_counts.items())),
            "all_hashes_unchanged": all(source.hash_unchanged is True for source in sources),
            "latest_real_year": latest_real_year,
            "latest_decision_year": latest_decision_year,
        },
        "period_coverage": {
            "all_periods": all_periods,
            "by_data_type": periods_by_type,
        },
        "markdown": markdown or {"sources": [], "summary": {}},
        "decision_summaries": [
            {
                "source_id": summary.source_id,
                "period": summary.period,
                "prices": summary.prices,
                "production_units": summary.production_units,
                "capex_selected": summary.capex_selected,
                "maintenance_pct": summary.maintenance_pct,
                "discount_pct": summary.discount_pct,
                "raw_path": summary.raw_path,
            }
            for summary in summaries
        ],
        "validation_rules": [{"rule_id": rule_id, "description": description} for rule_id, description in _RULES],
        "documented_limitations": [
            {"id": identifier, "description": description}
            for identifier, description in _DOCUMENTED_LIMITATIONS
        ],
        "warnings": warnings,
    }


def write_inventory(path: Path, inventory: dict[str, Any]) -> None:
    _json_dump(path, inventory)


def write_canonical_csv(path: Path, observations: list[Observation]) -> None:
    rows = [observation.to_dict() for observation in observations]
    fieldnames = list(rows[0].keys()) if rows else list(Observation.__dataclass_fields__)
    _csv_write(path, rows, fieldnames)


def write_anomalies_csv(path: Path, anomalies: list[Anomaly]) -> None:
    rows = [anomaly.to_dict() for anomaly in anomalies]
    fieldnames = list(rows[0].keys()) if rows else list(Anomaly.__dataclass_fields__)
    _csv_write(path, rows, fieldnames)


def _md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_report_md(
    path: Path,
    *,
    config: F1Config,
    sources: list[SourceInfo],
    observations: list[Observation],
    anomalies: list[Anomaly],
    inventory: dict[str, Any],
) -> None:
    summary = inventory["summary"]
    severity = summary["anomalies_by_severity"]
    periods = inventory["period_coverage"]["by_data_type"]
    lines: list[str] = []
    lines.append("# F1 — Inventario, capa canónica y representación Markdown")
    lines.append("")
    lines.append(f"Generado: `{inventory['generated_at']}`")
    lines.append("")
    lines.append("## Resumen ejecutivo")
    lines.append("")
    lines.append(f"- Fuentes inventariadas: **{summary['source_count']}**.")
    lines.append(f"- Celdas brutas no vacías: **{summary['raw_cell_count']}**.")
    lines.append(f"- Observaciones canónicas: **{summary['observation_count']}**.")
    lines.append(f"- Anomalías: **{summary['anomaly_count']}** "
                 f"(críticas {severity['critical']}, altas {severity['high']}, "
                 f"medias {severity['medium']}, bajas {severity['low']}, info {severity['info']}).")
    lines.append(f"- Hashes de fuentes sin cambios: **{summary['all_hashes_unchanged']}**.")
    lines.append(f"- Último año real detectado: **{summary['latest_real_year']}**; "
                 f"último año con decisiones: **{summary['latest_decision_year']}**.")
    lines.append(
        f"- Observaciones coincidentes conservadas: **{summary['coincident_observations']}** "
        f"en **{summary['coincident_groups']}** grupos (no se eliminan automáticamente)."
    )
    lines.append("")
    lines.append("## Fuentes")
    lines.append("")
    lines.append("| ID | Ruta | Tipo | Hojas | Periodos | Tipos | SHA-256 antes | SHA-256 después | Igual |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for source in sources:
        lines.append(
            "| {id} | `{path}` | {type} | {sheets} | {periods} | {types} | `{before}` | `{after}` | {same} |".format(
                id=source.source_id,
                path=_md_escape(source.relative_path),
                type=source.source_type,
                sheets=", ".join(source.sheets) or "—",
                periods=", ".join(source.periods) or "—",
                types=", ".join(source.data_types) or "—",
                before=source.sha256_before[:16],
                after=(source.sha256_after or "")[:16],
                same="sí" if source.hash_unchanged else "no",
            )
        )
    lines.append("")
    lines.append("## Cobertura temporal")
    lines.append("")
    lines.append("| Tipo de dato | Periodos |")
    lines.append("|---|---|")
    for data_type, values in periods.items():
        lines.append(f"| `{data_type}` | {', '.join(values)} |")
    lines.append("")
    lines.append("## Estado de las observaciones")
    lines.append("")
    lines.append("| Estado financiero | Observaciones |")
    lines.append("|---|---:|")
    for status, count in summary["observations_by_financial_status"].items():
        lines.append(f"| `{status}` | {count} |")
    lines.append("")
    lines.append("| Tipo de dato | Observaciones |")
    lines.append("|---|---:|")
    for data_type, count in summary["observations_by_data_type"].items():
        lines.append(f"| `{data_type}` | {count} |")
    lines.append("")
    lines.append("## Anomalías")
    lines.append("")
    lines.append("| Severidad | Anomalías |")
    lines.append("|---|---:|")
    for key, count in severity.items():
        lines.append(f"| `{key}` | {count} |")
    lines.append("")
    lines.append("| Categoría | Anomalías |")
    lines.append("|---|---:|")
    for category, count in summary["anomalies_by_category"].items():
        lines.append(f"| `{category}` | {count} |")
    lines.append("")
    if anomalies:
        lines.append("### Anomalías prioritarias")
        lines.append("")
        lines.append("| ID | Severidad | Regla | Fuente | Hoja | Celda | Periodo | Mensaje |")
        lines.append("|---|---|---|---|---|---|---|---|")
        priority = [anomaly for anomaly in anomalies if anomaly.severity in {"critical", "high"}][:25]
        for anomaly in priority:
            lines.append(
                f"| {anomaly.anomaly_id} | `{anomaly.severity}` | `{anomaly.rule_id}` | "
                f"{anomaly.source_id} | {_md_escape(anomaly.sheet)} | `{anomaly.cell}` | "
                f"{anomaly.period or '—'} | {_md_escape(anomaly.message)} |"
            )
        lines.append("")
        lines.append("El detalle completo, con valores esperados/observados y procedencia, está en `anomalies.csv`.")
        lines.append("")
    markdown = inventory.get("markdown", {})
    markdown_summary = markdown.get("summary", {}) if isinstance(markdown, dict) else {}
    if markdown_summary:
        lines.append("## Representación Markdown")
        lines.append("")
        lines.append(f"- Excel exportados: **{markdown_summary.get('workbooks_exported', 0)}**.")
        lines.append(f"- Fuentes Markdown capturadas: **{markdown_summary.get('captured_sources', 0)}**.")
        lines.append(f"- Hojas exportadas: **{markdown_summary.get('sheets', 0)}**.")
        lines.append(f"- Celdas indexadas: **{markdown_summary.get('indexed_cells', 0)}**.")
        lines.append(f"- Celdas no indexadas: **{markdown_summary.get('missing_cells', 0)}**.")
        lines.append(f"- Celdas duplicadas en el índice: **{markdown_summary.get('duplicate_cells', 0)}**.")
        lines.append(f"- Advertencias: **{markdown_summary.get('warnings', 0)}**.")
        lines.append("")
        lines.append("El detalle y la comprobación de fidelidad están en `outputs/markdown/`.")
        lines.append("")
    lines.append("## Reglas de validación aplicadas")
    lines.append("")
    for rule_id, description in _RULES:
        lines.append(f"- `{rule_id}`: {description}")
    lines.append("")
    lines.append("## Limitaciones y pendientes documentados")
    lines.append("")
    lines.append("F1.1 no corrige las fuentes ni resuelve estas contradicciones; solo las conserva y las reporta.")
    lines.append("")
    for identifier, description in _DOCUMENTED_LIMITATIONS:
        lines.append(f"- `{identifier}`: {description}")
    lines.append("")
    lines.append("## Notas de trazabilidad")
    lines.append("")
    lines.append("- Cada observación conserva fuente, hoja, celda, fila, columna, etiqueta y procedencia.")
    lines.append("- Las celdas combinadas se registran en la celda superior izquierda.")
    lines.append("- Las observaciones coincidentes se conservan; no se deduplican destructivamente.")
    lines.append("- `financial_status` distingue validación financiera de carga técnica e integridad.")
    lines.append("- Los periodos se detectan por contenido, no por nombre de archivo ni numeración fija.")
    lines.append("- Los hashes SHA-256 se recalculan después de la ejecución para verificar que `data/` no cambió.")
    lines.append("")
    lines.append("## Archivos generados")
    lines.append("")
    lines.append("- `inventory.json`")
    lines.append("- `canonical_points.csv`")
    lines.append("- `anomalies.csv`")
    lines.append("- `report.md`")
    lines.append("- `markdown/` (Markdown generado, manifiesto e índice de celdas)")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_all_outputs(
    *,
    config: F1Config,
    sources: list[SourceInfo],
    observations: list[Observation],
    anomalies: list[Anomaly],
    summaries: list[DecisionSummary],
    raw_cell_count: int,
    elapsed_seconds: float,
    markdown: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory(
        config=config,
        sources=sources,
        observations=observations,
        anomalies=anomalies,
        summaries=summaries,
        raw_cell_count=raw_cell_count,
        elapsed_seconds=elapsed_seconds,
        markdown=markdown,
    )
    write_inventory(output_dir / "inventory.json", inventory)
    write_canonical_csv(output_dir / "canonical_points.csv", observations)
    write_anomalies_csv(output_dir / "anomalies.csv", anomalies)
    write_report_md(
        output_dir / "report.md",
        config=config,
        sources=sources,
        observations=observations,
        anomalies=anomalies,
        inventory=inventory,
    )
    return inventory
