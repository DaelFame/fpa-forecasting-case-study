from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .config import PROJECT_ROOT, F1Config, load_config
from .models import Anomaly, DecisionSummary, Observation, RawCell, SourceInfo
from .pipeline import PipelineResult, run_pipeline
from .text import normalize_label, period_sort_key


STATE_DIR = PROJECT_ROOT / ".specify" / "memory"
INTERPRETATIONS_PATH = STATE_DIR / "interpretations.json"
OPEN_QUESTIONS_PATH = STATE_DIR / "open_questions.json"


@dataclass
class ReviewBundle:
    config: F1Config
    sources: list[SourceInfo]
    observations: list[Observation]
    anomalies: list[Anomaly]
    summaries: list[DecisionSummary]
    inventory: dict[str, Any]
    markdown: dict[str, Any]
    cells_by_source: dict[str, list[RawCell]]


def run_review(config: F1Config | None = None, *, export_markdown: bool = True) -> ReviewBundle:
    resolved = config or load_config()
    result: PipelineResult = run_pipeline(resolved, export_markdown=export_markdown)
    return ReviewBundle(
        config=result.config,
        sources=result.sources,
        observations=result.observations,
        anomalies=result.anomalies,
        summaries=result.summaries,
        inventory=result.inventory,
        markdown=result.markdown,
        cells_by_source=result.cells_by_source,
    )


def _empty_state(schema: str, root_key: str) -> dict[str, Any]:
    return {"schema_version": schema, root_key: [], "notes": []}


def load_interpretations(path: Path | None = None) -> dict[str, Any]:
    target = path or INTERPRETATIONS_PATH
    if not target.exists():
        return _empty_state("1.0", "items")
    return json.loads(target.read_text(encoding="utf-8"))


def load_open_questions(path: Path | None = None) -> dict[str, Any]:
    target = path or OPEN_QUESTIONS_PATH
    if not target.exists():
        return _empty_state("1.0", "questions")
    return json.loads(target.read_text(encoding="utf-8"))


def sources_frame(sources: list[SourceInfo]) -> pd.DataFrame:
    rows = [
        {
            "source_id": source.source_id,
            "relative_path": source.relative_path,
            "source_type": source.source_type,
            "kind": source.kind,
            "sheets": len(source.sheets),
            "periods": ", ".join(source.periods),
            "data_types": ", ".join(source.data_types),
            "hash_unchanged": source.hash_unchanged,
            "captured_at": source.captured_at,
            "origin_url": source.origin_url,
            "title": source.title,
            "warnings": len(source.warnings),
        }
        for source in sources
    ]
    return pd.DataFrame(rows)


def sheet_index(markdown: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for source in markdown.get("sources", []):
        for sheet in source.get("sheets", []):
            rows.append(
                {
                    "source": source.get("source", ""),
                    "source_path": source.get("source_path", ""),
                    "sheet": sheet.get("name", ""),
                    "hidden": sheet.get("hidden", False),
                    "dimensions": sheet.get("dimensions", ""),
                    "max_row": sheet.get("max_row", 0),
                    "max_column": sheet.get("max_column", 0),
                    "merged_ranges": len(sheet.get("merged_ranges", [])),
                    "nonempty_cells": sheet.get("nonempty_cells", 0),
                    "md_file": sheet.get("md_file", ""),
                    "warnings": len(sheet.get("warnings", [])),
                }
            )
    return pd.DataFrame(rows)


def table_index(markdown: dict[str, Any]) -> pd.DataFrame:
    """Alias de compatibilidad; F1.2 literal indexa hojas, no tablas."""
    return sheet_index(markdown)


def raw_sheet_frame(
    cells_by_source: dict[str, list[RawCell]],
    source_id: str,
    sheet: str,
) -> pd.DataFrame:
    cells = [
        cell
        for cell in cells_by_source.get(source_id, [])
        if cell.sheet == sheet
    ]
    rows = [
        {
            "coordinate": cell.coordinate,
            "row": cell.row,
            "column": cell.column,
            "value": cell.value,
            "raw_text": cell.raw_text,
            "value_type": cell.value_type,
            "number_format": cell.number_format,
            "merged_range": cell.merged_range,
        }
        for cell in sorted(cells, key=lambda item: (item.row, item.column))
    ]
    return pd.DataFrame(rows)


def _matches_metric(observation: Observation, target: str) -> bool:
    label = observation.label_normalized
    metric = normalize_label(observation.metric)
    return bool(target) and (
        target == label
        or target in label
        or target == metric
        or target in metric
    )


def compare_metric(
    observations: Iterable[Observation],
    metric: str,
    *,
    source_id: str | None = None,
    sheet: str | None = None,
    unit: str | None = None,
) -> pd.DataFrame:
    target = normalize_label(metric)
    rows: list[dict[str, Any]] = []
    for observation in observations:
        if observation.numeric_value is None or not observation.period:
            continue
        if not _matches_metric(observation, target):
            continue
        if source_id and observation.source_id != source_id:
            continue
        if sheet and observation.sheet != sheet:
            continue
        if unit and observation.unit != unit:
            continue
        rows.append(
            {
                "period": observation.period,
                "year": observation.year,
                "quarter": observation.quarter,
                "data_type": observation.data_type,
                "source_id": observation.source_id,
                "sheet": observation.sheet,
                "cell": observation.cell,
                "label": observation.label_raw,
                "segment": observation.segment,
                "scope": observation.scope,
                "value": observation.numeric_value,
                "unit": observation.unit,
                "financial_status": observation.financial_status,
                "provenance": observation.provenance,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["_period_key"] = frame["period"].map(period_sort_key)
    frame = frame.sort_values(["_period_key", "source_id", "sheet", "cell"])
    return frame.drop(columns="_period_key").reset_index(drop=True)


def _sheet_key(sheet: str) -> str:
    value = normalize_label(sheet)
    value = value.replace("analisis de ", "").replace("analisis ", "")
    value = value.replace("valor de ", "valor ")
    return value


def source_overlap(
    observations: Iterable[Observation],
    source_a: str,
    source_b: str,
    *,
    data_type: str = "real",
    only_discrepancies: bool = True,
    tolerance_abs: float = 1.0,
    tolerance_pct: float = 0.01,
) -> pd.DataFrame:
    grouped: dict[tuple[str, str, str], dict[str, list[Observation]]] = {}
    for observation in observations:
        if (
            observation.numeric_value is None
            or not observation.period
            or not observation.label_normalized
            or observation.data_type != data_type
        ):
            continue
        if observation.source_id not in {source_a, source_b}:
            continue
        key = (
            _sheet_key(observation.sheet),
            observation.label_normalized,
            observation.period,
            observation.unit,
        )
        grouped.setdefault(key, {}).setdefault(observation.source_id, []).append(observation)

    rows: list[dict[str, Any]] = []
    for (sheet_key, label, period, unit), by_source in grouped.items():
        left = sorted(by_source.get(source_a, []), key=lambda item: (item.source_row, item.source_column))
        right = sorted(by_source.get(source_b, []), key=lambda item: (item.source_row, item.source_column))
        if not left or not right:
            continue
        first, second = left[0], right[0]
        value_a = first.numeric_value
        value_b = second.numeric_value
        if value_a is None or value_b is None:
            continue
        difference = value_b - value_a
        relative = difference / abs(value_a) if value_a else None
        threshold = max(tolerance_abs, abs(value_a) * tolerance_pct)
        comparable = abs(difference) <= threshold
        if only_discrepancies and comparable:
            continue
        rows.append(
            {
                "sheet": sheet_key,
                "label": label,
                "period": period,
                "unit": unit,
                "data_type": data_type,
                "value_a": value_a,
                "value_b": value_b,
                "difference": difference,
                "relative_pct": relative * 100.0 if relative is not None else None,
                "comparable": comparable,
                "source_a": source_a,
                "source_b": source_b,
                "cell_a": first.cell,
                "cell_b": second.cell,
                "sheet_a": first.sheet,
                "sheet_b": second.sheet,
                "observations_a": len(left),
                "observations_b": len(right),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["_period_key"] = frame["period"].map(period_sort_key)
    frame = frame.sort_values(["label", "_period_key", "unit"])
    return frame.drop(columns="_period_key").reset_index(drop=True)


def period_pivot(
    frame: pd.DataFrame,
    *,
    index: str = "label",
    columns: str = "period",
    values: str = "value",
) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame.pivot_table(index=index, columns=columns, values=values, aggfunc="first")


def anomalies_frame(anomalies: list[Anomaly]) -> pd.DataFrame:
    return pd.DataFrame([anomaly.to_dict() for anomaly in anomalies])


def markdown_fidelity_frame(markdown: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for source in markdown.get("sources", []):
        rows.append(
            {
                "source": source.get("source", ""),
                "source_path": source.get("source_path", ""),
                "sheets": len(source.get("sheets", [])),
                "nonempty_cells": source.get("nonempty_cells", 0),
                "indexed_cells": source.get("indexed_cells", 0),
                "missing_cells": source.get("missing_cells", 0),
                "duplicate_cells": source.get("duplicate_cells", 0),
                "hash_unchanged": source.get("hash_unchanged"),
                "warnings": len(source.get("warnings", [])),
            }
        )
    return pd.DataFrame(rows)


def interpretations_frame(state: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(state.get("items", []))


def open_questions_frame(state: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(state.get("questions", []))
