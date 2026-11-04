from __future__ import annotations

import json
from pathlib import Path

from openpyxl import load_workbook


REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX1 = REPO_ROOT / "data" / "Matriz_General_1.xlsx"
MATRIX2 = REPO_ROOT / "data" / "Matriz_general_2.xlsx"


def _sheet(path: Path, name: str):
    workbook = load_workbook(path, data_only=True)
    return workbook, workbook[name]


def test_balance_detail_rounding_and_reserve_difference() -> None:
    workbook, sheet = _sheet(MATRIX1, "Analisis de Balance")
    try:
        current_components = sum(
            sheet[f"B{row}"].value for row in (12, 13, 14, 15)
        )
        assert current_components == 1_028_282
        assert sheet["B47"].value == 1_028_281
        assert current_components - sheet["B47"].value == 1
        assert sheet["B19"].value - sheet["B50"].value == 246_390
        assert sheet["B49"].value + sheet["B50"].value + sheet["B51"].value == 3_888_300
        assert sheet["B52"].value == 4_134_690
        assert sheet["B28"].value + sheet["B21"].value == 5_581_822
        assert sheet["B29"].value == 5_335_431
        assert sheet["B60"].value == 5_335_431
    finally:
        workbook.close()


def test_interest_rate_tables_have_distinct_contexts_and_values() -> None:
    workbook, sheet = _sheet(MATRIX1, "Analisis de Balance")
    try:
        assert sheet["E98"].value == 0.076
        assert "Tipo de Interés aplicable por tipo de operación" in " ".join(
            str(sheet.cell(92, column).value or "") for column in range(1, 6)
        )
        assert sheet["B168"].value == 0.132
        assert "Tasas/Tipos aplicables por modadlidad de préstamo." in str(sheet["A162"].value)
        assert sheet["A166"].value == "Largo Plazo"
        assert sheet["A168"].value == "Crédito Extraordinario"
    finally:
        workbook.close()
    financing = (REPO_ROOT / "docs" / "modules" / "Decisiones_matriz_1" / "Módulo de Financiación.md").read_text(
        encoding="utf-8"
    )
    assert "13,2%" in financing
    assert "7,6%" not in financing


def test_capex_increment_is_split_between_factory_and_warehouse() -> None:
    workbook, sheet = _sheet(MATRIX1, "Analisis de Balance")
    try:
        assert sheet["B5"].value - sheet["C5"].value == 1_533_000
        factory_delta = sheet["B201"].value - sheet["C201"].value
        warehouse_delta = sheet["B205"].value - sheet["C205"].value
        assert factory_delta == 1_308_000
        assert warehouse_delta == 225_000
        assert factory_delta + warehouse_delta == 1_533_000
    finally:
        workbook.close()
    decisions = json.loads(
        (REPO_ROOT / "data" / "decisiones" / "Bitacora_decisiones_para_2026.json").read_text(
            encoding="utf-8"
        )
    )
    selected = sum(
        project.get("inversion_eur", 0)
        for project in decisions["decisiones"]["otros_proyectos"].values()
        if project.get("seleccionado") is True
    )
    assert selected == 400_000
    assert 1_533_000 - selected == 1_133_000


def test_competitor_2025_table_is_repeated_but_later_data_differs() -> None:
    workbook, sheet = _sheet(MATRIX1, "Ingresos")
    try:
        reference = sheet["J47"].value
        repeated = [sheet.cell(47, column).value for column in range(9, 15)]
        assert repeated == [reference] * len(repeated)
    finally:
        workbook.close()

    workbook, sheet = _sheet(MATRIX2, "Ingresos")
    try:
        later_values = [sheet.cell(48, column).value for column in range(9, 16)]
        assert len(set(later_values)) > 1
    finally:
        workbook.close()


def test_detailed_2027_identity_and_reserve_residual() -> None:
    workbook, sheet = _sheet(MATRIX2, "Balance")
    try:
        equity_components = sheet["B48"].value + sheet["B49"].value + sheet["B50"].value
        assert equity_components == 4_445_747
        assert sheet["B51"].value == 4_692_138
        assert sheet["B51"].value - equity_components == 246_391
        liabilities = sheet["B58"].value
        assets = sheet["B17"].value
        assert liabilities + equity_components == 5_665_583
        assert assets == 5_665_584
        assert assets - (liabilities + equity_components) == 1
        assert sheet["B49"].value == 1_085_613
        assert 930_663 + 154_951 == 1_085_614
        assert 1_085_614 - sheet["B49"].value == 1
    finally:
        workbook.close()


def test_2027_bufandas_production_case_remains_unexplained() -> None:
    workbook, sheet = _sheet(MATRIX1, "Produccion")
    try:
        assert [sheet[f"{column}6"].value for column in "BCD"] == [215_000, 30_000, 40_000]
        assert [sheet[f"{column}7"].value for column in "BCD"] == [210_000, 29_000, 33_000]
    finally:
        workbook.close()

    workbook, sheet = _sheet(MATRIX2, "Produccion")
    try:
        assert [sheet[f"{column}7"].value for column in "BCD"] == [215_000, 30_000, 40_000]
        assert [sheet[f"{column}8"].value for column in "BCD"] == [215_000, 30_000, 40_000]
    finally:
        workbook.close()

    decisions = json.loads(
        (REPO_ROOT / "data" / "decisiones" / "Bitacora_decisiones_para_2027.json").read_text(
            encoding="utf-8"
        )
    )
    assert decisions["decisiones"]["produccion"]["unidades_producir"] == {
        "corbatas": 0,
        "bufandas": 0,
        "calcetines": 0,
    }
    production_doc = (
        REPO_ROOT
        / "docs"
        / "modules"
        / "Decisiones_matriz_2"
        / "Modulo_Produccion_matriz_2.md"
    ).read_text(encoding="utf-8")
    assert "32.000" in production_doc
