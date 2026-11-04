from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from .canonical import canonicalize_sources
from .config import F1Config
from .loader import discover_sources, load_sources, refresh_hashes
from .excel_to_md import export_excel_to_markdown
from .models import Anomaly, DecisionSummary, Observation, RawCell, SourceInfo
from .reporting import write_all_outputs
from .validation import validate_observations


@dataclass
class PipelineResult:
    config: F1Config
    sources: list[SourceInfo]
    observations: list[Observation]
    anomalies: list[Anomaly]
    summaries: list[DecisionSummary]
    inventory: dict[str, Any]
    raw_cell_count: int
    elapsed_seconds: float
    cells_by_source: dict[str, list[RawCell]]
    markdown: dict[str, Any]


def run_pipeline(config: F1Config, *, export_markdown: bool = True) -> PipelineResult:
    started = time.perf_counter()
    sources = discover_sources(config.data_dir, config.project_root)
    cells_by_source, summaries = load_sources(sources, config)
    raw_cell_count = sum(len(cells) for cells in cells_by_source.values())
    if export_markdown:
        markdown = export_excel_to_markdown(
            sources,
            config.markdown_dir,
            project_root=config.project_root,
        )
    else:
        markdown = {
            "schema_version": "f1.2-literal",
            "sources": [],
            "captured_sources": [],
            "summary": {
                "workbooks_exported": 0,
                "captured_sources": 0,
                "sheets": 0,
                "indexed_cells": 0,
                "missing_cells": 0,
                "duplicate_cells": 0,
                "warnings": 0,
            },
        }
    observations = canonicalize_sources(sources, cells_by_source, summaries, config)
    anomalies = validate_observations(
        observations,
        summaries,
        sources,
        cells_by_source,
        config,
    )
    refresh_hashes(sources)
    elapsed = time.perf_counter() - started
    inventory = write_all_outputs(
        config=config,
        sources=sources,
        observations=observations,
        anomalies=anomalies,
        summaries=summaries,
        raw_cell_count=raw_cell_count,
        elapsed_seconds=elapsed,
        markdown=markdown,
    )
    return PipelineResult(
        config=config,
        sources=sources,
        observations=observations,
        anomalies=anomalies,
        summaries=summaries,
        inventory=inventory,
        raw_cell_count=raw_cell_count,
        elapsed_seconds=elapsed,
        cells_by_source=cells_by_source,
        markdown=markdown,
    )
