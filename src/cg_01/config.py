from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .text import normalize_label


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "f1.toml"


@dataclass(frozen=True)
class F1Config:
    project_root: Path
    data_dir: Path
    output_dir: Path
    markdown_dir: Path
    min_year: int = 2000
    max_year: int = 2100
    price_corridor_pct: float = 15.0
    occupancy_threshold_pct: float = 60.0
    occupancy_penalty_mode: str = "plant"
    occupancy_cost_mode: str = "line"
    balance_tolerance_eur: float = 1.0
    aliases: dict[str, str] = field(default_factory=dict)
    config_path: Path | None = None

    def account(self, label: Any) -> str:
        normalized = normalize_label(label)
        return self.aliases.get(normalized, normalized)


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name, {})
    return value if isinstance(value, dict) else {}


def load_config(
    path: str | Path | None = None,
    *,
    data_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    markdown_dir: str | Path | None = None,
    project_root: str | Path | None = None,
) -> F1Config:
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    root = Path(project_root) if project_root is not None else config_path.parent.parent
    raw: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open("rb") as handle:
            raw = tomllib.load(handle)

    paths = _section(raw, "paths")
    periods = _section(raw, "periods")
    validation = _section(raw, "validation")
    labels = _section(raw, "labels")

    resolved_data = Path(data_dir) if data_dir is not None else Path(str(paths.get("data_dir", "data")))
    resolved_output = Path(output_dir) if output_dir is not None else Path(str(paths.get("output_dir", "outputs/f1")))
    resolved_markdown = Path(markdown_dir) if markdown_dir is not None else Path(str(paths.get("markdown_dir", "outputs/markdown")))
    if not resolved_data.is_absolute():
        resolved_data = (root / resolved_data).resolve()
    if not resolved_output.is_absolute():
        resolved_output = (root / resolved_output).resolve()
    if not resolved_markdown.is_absolute():
        resolved_markdown = (root / resolved_markdown).resolve()

    occupancy_penalty_mode = str(validation.get("occupancy_penalty_mode", "plant")).strip().casefold()
    occupancy_cost_mode = str(validation.get("occupancy_cost_mode", "line")).strip().casefold()
    for name, value in (
        ("occupancy_penalty_mode", occupancy_penalty_mode),
        ("occupancy_cost_mode", occupancy_cost_mode),
    ):
        if value not in {"line", "plant"}:
            raise ValueError(f"{name} no válido: {value!r}; usa 'line' o 'plant'.")

    aliases = {
        normalize_label(key): str(value)
        for key, value in labels.items()
        if normalize_label(key)
    }

    return F1Config(
        project_root=root,
        data_dir=resolved_data,
        output_dir=resolved_output,
        markdown_dir=resolved_markdown,
        min_year=int(periods.get("min_year", 2000)),
        max_year=int(periods.get("max_year", 2100)),
        price_corridor_pct=float(validation.get("price_corridor_pct", 15.0)),
        occupancy_threshold_pct=float(validation.get("occupancy_threshold_pct", 60.0)),
        occupancy_penalty_mode=occupancy_penalty_mode,
        occupancy_cost_mode=occupancy_cost_mode,
        balance_tolerance_eur=float(validation.get("balance_tolerance_eur", 1.0)),
        aliases=aliases,
        config_path=config_path.resolve() if config_path.exists() else config_path,
    )
