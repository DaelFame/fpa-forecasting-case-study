"""The TMDL model must stay consistent with the marts it reads.

Power BI rejects a relationship whose two sides have different data types, and the
failure only surfaces when the project is opened. These checks catch it offline.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

from cg_01.fpa.tmdl import build

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_ROOT / "dashboard" / "FPA_Case_Study.SemanticModel"
TABLES_DIR = MODEL_DIR / "definition" / "tables"

COLUMN_RE = re.compile(r"^\tcolumn (\S+)$")
TYPE_RE = re.compile(r"^\t\tdataType: (\S+)$")
RELATIONSHIP_RE = re.compile(r"^relationship (\S+)$")
FROM_RE = re.compile(r"^\tfromColumn: ([^.]+)\.(\S+)$")
TO_RE = re.compile(r"^\ttoColumn: ([^.]+)\.(\S+)$")


def _model() -> tuple[dict[str, dict[str, str]], list[tuple[str, str, str, str]]]:
    columns: dict[str, dict[str, str]] = {}
    relationships: list[tuple[str, str, str, str]] = []
    for path in sorted(TABLES_DIR.glob("*.tmdl")):
        table = path.stem
        current: str | None = None
        for line in path.read_text(encoding="utf-8").splitlines():
            if match := COLUMN_RE.match(line):
                current = match.group(1)
                columns.setdefault(table, {})[current] = ""
            elif current and (match := TYPE_RE.match(line)):
                columns[table][current] = match.group(1)

    source = ""
    for line in (MODEL_DIR / "definition" / "relationships.tmdl").read_text(encoding="utf-8").splitlines():
        if RELATIONSHIP_RE.match(line):
            source = line.split(" ", 1)[1]
        elif match := FROM_RE.match(line):
            from_table, from_column = match.groups()
        elif match := TO_RE.match(line):
            to_table, to_column = match.groups()
            relationships.append((from_table, from_column, to_table, to_column))
    return columns, relationships


@pytest.fixture(scope="module")
def model() -> tuple[dict[str, dict[str, str]], list[tuple[str, str, str, str]]]:
    if not TABLES_DIR.exists() or not any(TABLES_DIR.glob("*.tmdl")):
        build(REPO_ROOT / "data" / "processed", MODEL_DIR)
    return _model()


def test_every_mart_has_a_table(model) -> None:
    columns, _ = model
    marts = {path.stem for path in (REPO_ROOT / "data" / "processed").glob("*.csv") if not path.name.startswith("_")}
    assert marts == set(columns)


def test_every_relationship_targets_existing_columns(model) -> None:
    columns, relationships = model
    assert relationships
    for from_table, from_column, to_table, to_column in relationships:
        assert from_column in columns.get(from_table, {}), f"{from_table}.{from_column}"
        assert to_column in columns.get(to_table, {}), f"{to_table}.{to_column}"


def test_relationship_types_match(model) -> None:
    columns, relationships = model
    for from_table, from_column, to_table, to_column in relationships:
        assert columns[from_table][from_column] == columns[to_table][to_column], (
            f"{from_table}.{from_column} ({columns[from_table][from_column]}) -> "
            f"{to_table}.{to_column} ({columns[to_table][to_column]})"
        )


def test_every_table_declares_a_partition(model) -> None:
    for path in sorted(TABLES_DIR.glob("*.tmdl")):
        text = path.read_text(encoding="utf-8")
        assert "\tpartition " in text, path.stem
        assert "mode: import" in text, path.stem


def test_every_csv_column_reaches_the_model(model) -> None:
    columns, _ = model
    for path in sorted((REPO_ROOT / "data" / "processed").glob("*.csv")):
        if path.name.startswith("_"):
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert set(header) <= set(columns[path.stem]), path.stem
