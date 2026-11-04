from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceInfo:
    source_id: str
    path: str
    relative_path: str
    source_type: str
    kind: str
    sha256_before: str
    size_bytes: int
    sha256_after: str | None = None
    sheets: list[str] = field(default_factory=list)
    periods: list[str] = field(default_factory=list)
    data_types: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    captured_at: str = ""
    origin_url: str = ""
    title: str = ""
    frontmatter: dict[str, Any] = field(default_factory=dict)
    markdown_tables: list[dict[str, Any]] = field(default_factory=list)

    @property
    def hash_unchanged(self) -> bool | None:
        if self.sha256_after is None:
            return None
        return self.sha256_before == self.sha256_after

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "path": self.path,
            "relative_path": self.relative_path,
            "source_type": self.source_type,
            "kind": self.kind,
            "sha256_before": self.sha256_before,
            "sha256_after": self.sha256_after,
            "hash_unchanged": self.hash_unchanged,
            "size_bytes": self.size_bytes,
            "sheets": self.sheets,
            "periods": self.periods,
            "data_types": self.data_types,
            "warnings": self.warnings,
            "captured_at": self.captured_at,
            "origin_url": self.origin_url,
            "title": self.title,
            "frontmatter": self.frontmatter,
            "markdown_tables": self.markdown_tables,
        }


@dataclass
class RawCell:
    source_id: str
    source_path: str
    sheet: str
    row: int
    column: int
    coordinate: str
    value: Any
    value_type: str
    number_format: str = ""
    merged_range: str | None = None
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_path": self.source_path,
            "sheet": self.sheet,
            "row": self.row,
            "column": self.column,
            "coordinate": self.coordinate,
            "value": self.value,
            "value_type": self.value_type,
            "number_format": self.number_format,
            "merged_range": self.merged_range,
            "raw_text": self.raw_text,
        }


@dataclass
class Observation:
    observation_id: str
    source_id: str
    source_path: str
    source_type: str
    sheet: str
    cell: str
    source_row: int
    source_column: int
    block_id: int | None
    label_raw: str
    label_normalized: str
    period: str
    year: int | None
    quarter: int | None
    period_status: str
    data_type: str
    metric: str
    scope: str
    segment: str
    value: Any
    value_text: str
    value_type: str
    unit: str
    currency: str
    normalized_value: float | None = None
    normalization_status: str = "identity"
    normalization_note: str = ""
    load_status: str = "loaded"
    integrity_status: str = "ok"
    financial_status: str = "not_validated"
    provenance: str = ""
    issues: list[str] = field(default_factory=list)

    @property
    def numeric_value(self) -> float | None:
        from .text import value_as_float

        return value_as_float(self.value)

    def add_issue(self, issue: str) -> None:
        if issue and issue not in self.issues:
            self.issues.append(issue)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "source_id": self.source_id,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "sheet": self.sheet,
            "cell": self.cell,
            "source_row": self.source_row,
            "source_column": self.source_column,
            "block_id": self.block_id,
            "label_raw": self.label_raw,
            "label_normalized": self.label_normalized,
            "period": self.period,
            "year": self.year,
            "quarter": self.quarter,
            "period_status": self.period_status,
            "data_type": self.data_type,
            "metric": self.metric,
            "scope": self.scope,
            "segment": self.segment,
            "value": self.value,
            "value_text": self.value_text,
            "value_type": self.value_type,
            "unit": self.unit,
            "currency": self.currency,
            "normalized_value": self.normalized_value,
            "normalization_status": self.normalization_status,
            "normalization_note": self.normalization_note,
            "load_status": self.load_status,
            "integrity_status": self.integrity_status,
            "financial_status": self.financial_status,
            "provenance": self.provenance,
            "issues": "; ".join(self.issues),
        }


@dataclass
class Anomaly:
    anomaly_id: str
    rule_id: str
    severity: str
    category: str
    source_id: str
    source_path: str
    sheet: str
    cell: str
    period: str
    message: str
    expected: str = ""
    observed: str = ""
    difference: str = ""
    provenance: str = ""
    resolution_status: str = "open"

    def to_dict(self) -> dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "category": self.category,
            "source_id": self.source_id,
            "source_path": self.source_path,
            "sheet": self.sheet,
            "cell": self.cell,
            "period": self.period,
            "message": self.message,
            "expected": self.expected,
            "observed": self.observed,
            "difference": self.difference,
            "provenance": self.provenance,
            "resolution_status": self.resolution_status,
        }


@dataclass
class DecisionSummary:
    source_id: str
    period: int
    prices: dict[str, float] = field(default_factory=dict)
    production_units: dict[str, float] = field(default_factory=dict)
    capex_selected: float = 0.0
    maintenance_pct: float | None = None
    discount_pct: float | None = None
    raw_path: str = ""
