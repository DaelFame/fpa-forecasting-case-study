from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from cg_01.f2_engine import bind_sources, load_f2_config
from cg_01.loader import discover_sources

ROOT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "f2.toml"


def _workbook(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    book = Workbook()
    book.active["A1"] = "periodo"
    book.save(path)


def test_source_ids_follow_a_case_insensitive_order(tmp_path: Path) -> None:
    """A new workbook must never renumber the ones already published.

    `sorted()` compares case-sensitively, so `Matriz_General_4.xlsx` sorted
    before `Matriz_general_2.xlsx` and shifted every enumerated `source_id`.
    """
    data_dir = tmp_path / "data"
    for name in (
        "Matriz_General_0.xlsx",
        "Matriz_General_1.xlsx",
        "Matriz_general_2.xlsx",
        "Matriz_general_3.xlsx",
        "Matriz_General_4.xlsx",
    ):
        _workbook(data_dir / name)

    sources = discover_sources(data_dir, tmp_path)
    assert {source.source_key: source.source_id for source in sources} == {
        "matriz_general_0": "SRC-XLSX-001",
        "matriz_general_1": "SRC-XLSX-002",
        "matriz_general_2": "SRC-XLSX-003",
        "matriz_general_3": "SRC-XLSX-004",
        "matriz_general_4": "SRC-XLSX-005",
    }


def test_source_key_survives_renumbering(tmp_path: Path) -> None:
    """Enumerated ids may shift; config bindings follow the stable key."""
    data_dir = tmp_path / "data"
    _workbook(data_dir / "Matriz_general_3.xlsx")
    first = discover_sources(data_dir, tmp_path)
    _workbook(data_dir / "Matriz_General_0.xlsx")
    second = discover_sources(data_dir, tmp_path)

    assert {source.source_key: source.source_id for source in first} == {
        "matriz_general_3": "SRC-XLSX-001"
    }
    by_key = {source.source_key: source.source_id for source in second}
    assert by_key["matriz_general_0"] == "SRC-XLSX-001"
    assert by_key["matriz_general_3"] == "SRC-XLSX-002"

    config_path = tmp_path / "f2.toml"
    config_path.write_text(
        '[periods]\nstart = 2024\nend = 2024\n[precedence]\n"2024" = ["matriz_general_3"]\n',
        encoding="utf-8",
    )
    precedence, _, _ = bind_sources(load_f2_config(config_path, project_root=tmp_path), second)
    assert precedence[2024] == {by_key["matriz_general_3"]: 0}


def test_config_bindings_resolve_by_source_key(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    for name in ("Matriz_general_2.xlsx", "Matriz_General_4.xlsx"):
        _workbook(data_dir / name)
    sources = discover_sources(data_dir, tmp_path)

    config_path = tmp_path / "f2.toml"
    config_path.write_text(
        "\n".join(
            [
                "[periods]",
                "start = 2024",
                "end = 2024",
                "[precedence]",
                '"2024" = ["matriz_general_4", "matriz_general_2"]',
                "[sheet_aliases.matriz_general_2]",
                '"Hoja 1" = "balance"',
            ]
        ),
        encoding="utf-8",
    )
    config = load_f2_config(config_path, project_root=tmp_path)
    precedence, aliases, unresolved = bind_sources(config, sources)

    by_key = {source.source_key: source.source_id for source in sources}
    assert precedence[2024] == {
        by_key["matriz_general_4"]: 0,
        by_key["matriz_general_2"]: 1,
    }
    assert set(aliases) == {by_key["matriz_general_2"]}
    assert unresolved == []


def test_unknown_bindings_are_reported_instead_of_ignored(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _workbook(data_dir / "Matriz_general_2.xlsx")
    sources = discover_sources(data_dir, tmp_path)

    config_path = tmp_path / "f2.toml"
    config_path.write_text(
        '[periods]\nstart = 2024\nend = 2024\n[precedence]\n"2024" = ["matriz_general_9"]\n',
        encoding="utf-8",
    )
    config = load_f2_config(config_path, project_root=tmp_path)
    precedence, aliases, unresolved = bind_sources(config, sources)

    assert precedence[2024] == {}
    assert aliases == {}
    assert unresolved == ["matriz_general_9"]


def test_shipped_config_survives_an_earlier_workbook(tmp_path: Path) -> None:
    """The real config must keep pointing at the real workbooks.

    A workbook that sorts first shifts every enumerated id; the shipped bindings
    have to keep resolving to `matriz_general_3` / `matriz_general_4`.
    """
    data_dir = tmp_path / "data"
    for name in (
        "AAA_earlier.xlsx",
        "Matriz_General_0.xlsx",
        "Matriz_General_1.xlsx",
        "Matriz_general_2.xlsx",
        "Matriz_general_3.xlsx",
        "Matriz_General_4.xlsx",
    ):
        _workbook(data_dir / name)

    sources = discover_sources(data_dir, tmp_path)
    keys = {source.source_id: source.source_key for source in sources}
    config = load_f2_config(ROOT_CONFIG, project_root=tmp_path)
    precedence, aliases, unresolved = bind_sources(config, sources)

    assert unresolved == []
    assert [keys[source_id] for source_id in precedence[2028]] == ["matriz_general_3"]
    assert [keys[source_id] for source_id in precedence[2029]] == ["matriz_general_4"]
    assert [keys[source_id] for source_id in aliases] == ["matriz_general_3"]
