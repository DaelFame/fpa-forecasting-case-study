from __future__ import annotations

import json
from pathlib import Path

from cg_01.loader import load_json_source
from cg_01.models import SourceInfo


def _source(path: Path) -> SourceInfo:
    return SourceInfo(
        source_id="SRC-JSON-TEST",
        path=str(path),
        relative_path=f"data/decisiones/{path.name}",
        source_type="json",
        kind="decisions",
        sha256_before="",
        size_bytes=path.stat().st_size,
    )


def _write(tmp_path: Path, payload: dict) -> Path:
    directory = tmp_path / "data" / "decisiones"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"Bitacora_decisiones_para_{payload['periodo']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_legacy_schema_is_still_parsed(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        {
            "periodo": 2027,
            "transicion": "1_a_2",
            "decisiones": {
                "ventas": {"precio_unitario": {"corbatas": 17.5}, "descuento_canal_pct": 10.0},
                "produccion": {"unidades_producir": {"corbatas": 0}, "mantenimiento_pct": 1.0},
                "otros_proyectos": {
                    "eficiencia": {"seleccionado": True, "inversion_eur": 250000},
                },
            },
        },
    )
    _, summary = load_json_source(_source(path), None)  # type: ignore[arg-type]

    assert summary.period == 2027
    assert summary.prices == {"corbatas": 17.5}
    assert summary.production_units == {"corbatas": 0.0}
    assert summary.maintenance_pct == 1.0
    assert summary.discount_pct == 10.0
    assert summary.capex_selected == 250000.0


def test_round_schema_is_parsed(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        {
            "empresa": "Spain10",
            "periodo": 2029,
            "ronda": 4,
            "modulos": {
                "ventas": {
                    "precios_venta_unitario": {
                        "corbatas_euro": 18.0,
                        "bufandas_euro": 30.0,
                        "calcetines_catalogo_euro": 3.6,
                    },
                    "descuento_canal_porcentaje": 10.0,
                    "promocion_marca_euro": {"corbatas": 120000, "total_euro": 220000},
                },
                "produccion": {
                    "unidades_a_producir": {
                        "corbatas": 235000,
                        "bufandas": 38000,
                        "calcetines": 90000,
                        "total_unidades": 363000,
                    },
                    "gasto_mantenimiento_porcentaje": 3.0,
                },
                "otros_proyectos": {
                    "automatizacion_almacen": {"decision": "Aceptar", "inversion_euro": 125000},
                    "modernizacion_fabrica": {
                        "decision": "Aceptar",
                        "inversion_corbatas_euro": 250000,
                        "inversion_calcetines_euro": 25000,
                    },
                    "venta_solar_urbanizable": {
                        "decision": "Aceptar",
                        "ingreso_caja_euro": 585000,
                        "plusvalia_contable_euro": 305000,
                    },
                    "venta_terreno_agricola": {"decision": "Rechazar"},
                },
            },
        },
    )
    _, summary = load_json_source(_source(path), None)  # type: ignore[arg-type]

    assert summary.period == 2029
    assert summary.prices == {"corbatas": 18.0, "bufandas": 30.0, "calcetines": 3.6}
    assert summary.production_units == {
        "corbatas": 235000.0,
        "bufandas": 38000.0,
        "calcetines": 90000.0,
    }
    assert summary.maintenance_pct == 3.0
    assert summary.discount_pct == 10.0
    assert summary.capex_selected == 400000.0
