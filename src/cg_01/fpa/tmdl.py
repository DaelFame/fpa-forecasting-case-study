"""Generate the TMDL tables and relationships for the Power BI project.

The semantic model is derived from ``data/processed``: column names and types come
from the CSV headers and values, so the model cannot drift from the marts. Run it
whenever a mart gains or loses a column.

    uv run python -m cg_01.fpa.tmdl
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any

MODEL_KEY = "pDataFolder"

# Fact column -> dimension table. Foreign keys are hidden on the fact side.
FOREIGN_KEYS: dict[str, dict[str, str]] = {
    "fact_financials": {
        "period_key": "dim_period",
        "line_item_key": "dim_line_item",
        "scenario_key": "dim_scenario",
        "status_key": "dim_status",
    },
    "fact_balance": {
        "period_key": "dim_period",
        "account_key": "dim_account",
        "status_key": "dim_status",
    },
    "fact_sales": {"period_key": "dim_period", "product_key": "dim_product"},
    "fact_product_annual": {"period_key": "dim_period", "product_key": "dim_product"},
    "fact_market": {"period_key": "dim_period", "product_key": "dim_product"},
    "fact_variance": {
        "period_key": "dim_period",
        "driver_key": "dim_driver",
        "line_item_key": "dim_line_item",
        "status_key": "dim_status",
    },
    "fact_backtest": {
        "fold_key": "dim_fold",
        "regime_key": "dim_regime",
        "period_key": "dim_period",
        "line_item_key": "dim_line_item",
        "status_key": "dim_status",
    },
    "fact_forecast": {
        "period_key": "dim_period",
        "line_item_key": "dim_line_item",
        "scenario_key": "dim_scenario",
        "regime_key": "dim_regime",
        "fold_key": "dim_fold",
        "status_key": "dim_status",
    },
}

# Dimension label column -> the column it must be sorted by.
SORT_KEYS: dict[str, tuple[str, str]] = {
    "dim_product": ("label", "sort_order"),
    "dim_scenario": ("label", "sort_order"),
    "dim_line_item": ("label", "display_order"),
}

INT_PATTERN = re.compile(r"^-?\d+$")
FLOAT_PATTERN = re.compile(r"^-?\d+\.\d+$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Primary key of each dimension. Hidden, and its type is authoritative for the
# matching foreign key, otherwise the relationship is rejected for type mismatch.
DIM_KEYS: dict[str, str] = {
    "dim_period": "period_key",
    "dim_product": "product_key",
    "dim_line_item": "line_item_key",
    "dim_account": "account_key",
    "dim_scenario": "scenario_key",
    "dim_status": "status_key",
    "dim_regime": "regime_key",
    "dim_fold": "fold_key",
    "dim_driver": "driver_key",
}


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _classify(values: list[str]) -> tuple[str, str]:
    """Return the (TMDL dataType, M type) for a column."""
    present = [value for value in values if value != ""]
    if not present:
        return "string", "type text"
    if all(value in {"true", "false"} for value in present):
        return "boolean", "type logical"
    if all(INT_PATTERN.match(value) for value in present):
        return "int64", "Int64.Type"
    if all(FLOAT_PATTERN.match(value) or INT_PATTERN.match(value) for value in present):
        return "double", "type number"
    if all(DATE_PATTERN.match(value) for value in present):
        return "dateTime", "type date"
    return "string", "type text"


def _column_block(name: str, data_type: str, *, hidden: bool, sort_by: str | None) -> str:
    lines = [f"\tcolumn {name}", f"\t\tdataType: {data_type}"]
    if sort_by:
        lines.append(f"\t\tsortByColumn: {sort_by}")
    if hidden:
        lines.append("\t\tisHidden")
    lines.append("\t\tsummarizeBy: none")
    lines.append(f"\t\tsourceColumn: {name}")
    return "\n".join(lines)


def _partition(table: str, steps: list[str], last: str) -> str:
    body = "\n".join(f"\t\t\t\t{step}" for step in steps)
    return (
        f"\tpartition {table} = m\n"
        "\t\tmode: import\n"
        "\t\tsource =\n"
        "\t\t\tlet\n"
        f"{body}\n"
        "\t\t\tin\n"
        f"\t\t\t\t{last}"
    )


def _table_tmdl(
    table: str,
    columns: list[str],
    rows: list[dict[str, str]],
    declared: dict[str, dict[str, tuple[str, str]]],
) -> str:
    chart = dict(FOREIGN_KEYS.get(table, {}))
    sort_pair = SORT_KEYS.get(table)
    label_column = sort_pair[0] if sort_pair else None
    sort_column = sort_pair[1] if sort_pair else None
    own_key = DIM_KEYS.get(table)

    blocks: list[str] = []
    types: list[str] = []
    empty_columns: list[str] = []
    for column in columns:
        values = [row[column] for row in rows]
        data_type, m_type = _classify(values)
        dimension = chart.get(column)
        if dimension and column in declared.get(dimension, {}):
            data_type, m_type = declared[dimension][column]
        types.append(f'{{"{column}", {m_type}}}')
        if any(value == "" for value in values) and data_type != "string":
            empty_columns.append(column)
        hidden = column in chart or column == sort_column or column == own_key
        sort_by = sort_column if column == label_column else None
        blocks.append(
            _column_block(column, data_type, hidden=hidden, sort_by=sort_by)
        )

    steps = [
        f'Origen = Csv.Document(File.Contents({MODEL_KEY} & "\\{table}.csv"), '
        '[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),",
    ]
    last = "Tipos"
    if empty_columns:
        column_list = ", ".join(f'"{column}"' for column in empty_columns)
        steps.append(
            'Reemplazados = Table.ReplaceValue(Encabezados, "", null, '
            f"Replacer.ReplaceValue, {{{column_list}}}),"
        )
        steps.append(
            f"Tipos = Table.TransformColumnTypes(Reemplazados, {{{', '.join(types)}}})"
        )
    else:
        steps.append(
            f"Tipos = Table.TransformColumnTypes(Encabezados, {{{', '.join(types)}}})"
        )

    header = f"table {table}\n\n"
    return header + "\n\n".join(blocks) + "\n\n" + _partition(table, steps, last) + "\n"


def _relationships(columns_by_table: dict[str, list[str]]) -> str:
    lines: list[str] = []
    for table, keys in FOREIGN_KEYS.items():
        available = set(columns_by_table.get(table, []))
        for column, dimension in keys.items():
            if column not in available:
                continue
            lines.append(
                f"relationship {table}_{column}\n"
                f"\tfromColumn: {table}.{column}\n"
                f"\ttoColumn: {dimension}.{column}\n"
            )
    return "\n".join(lines)


def _model_tmdl(tables: list[str], existing: str) -> str:
    header = existing.split("ref ")[0].rstrip()
    refs = "\n".join(f"ref table {table}" for table in tables)
    culture = "ref cultureInfo es-PE"
    return f"{header}\n\n{culture}\n\n{refs}\n"


def build(data_dir: Path, model_dir: Path) -> dict[str, int]:
    csv_paths = sorted(path for path in data_dir.glob("*.csv") if not path.name.startswith("_"))
    tables_dir = model_dir / "definition" / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    columns_by_table: dict[str, list[str]] = {}
    loaded: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    for path in csv_paths:
        columns, rows = _read(path)
        loaded[path.stem] = (columns, rows)

    declared = {
        table: {column: _classify([row[column] for row in rows]) for column in columns}
        for table, (columns, rows) in loaded.items()
    }

    for table, (columns, rows) in loaded.items():
        columns_by_table[table] = columns
        (tables_dir / f"{table}.tmdl").write_text(
            _table_tmdl(table, columns, rows, declared), encoding="utf-8"
        )

    relationships = _relationships(columns_by_table)
    (model_dir / "definition" / "relationships.tmdl").write_text(
        relationships, encoding="utf-8"
    )

    model_path = model_dir / "definition" / "model.tmdl"
    model_path.write_text(
        _model_tmdl(sorted(columns_by_table), model_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )

    return {"tables": len(columns_by_table), "relationships": relationships.count("relationship ")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cg_01.fpa.tmdl",
        description="Regenerate the TMDL tables and relationships from data/processed.",
    )
    parser.add_argument("--data", type=Path, default=Path("data/processed"))
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("dashboard/FPA_Case_Study.SemanticModel"),
    )
    args = parser.parse_args(argv)

    counts = build(args.data, args.model)
    print(f"TMDL generado: {counts['tables']} tablas, {counts['relationships']} relaciones.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
