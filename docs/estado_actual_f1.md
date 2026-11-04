# Estado actual de Fase 1 (cerrada) — cg_01

Fecha: 2026-10-23  
Estado: F1.1, F1.2 literal y F1.3 aceptadas; F1.4 aprobada; F2.1 aprobada.  
Alcance: Fase 1 cerrada. F2.1 aprobada; F2.2 pendiente de aprobación de alcance; Monte Carlo y optimización no iniciados.

---

## 1. Fuentes actuales

| Fuente | Ruta | SHA-256 |
|---|---|---|
| Matriz 0 | `data/Matriz_General_0.xlsx` | `30a0b3bd4815d4848a9de9fb3d43cb7a235667a429b1cbe0528c21d551fe6f1c` |
| Matriz 1 | `data/Matriz_General_1.xlsx` | `4411320d15b5f8589cb0a4f31c72cd0f5636ae68e9624c5c9a4244cad208b4eb` |
| Matriz 2 | `data/Matriz_general_2.xlsx` | `044f63f05501529f8c58d06e1d21e6b190764d018f7e17597d1fb02f0a52b5d0` |
| Bitácora 2026 | `data/decisiones/Bitacora_decisiones_para_2026.json` | `316add54deb45b61d5e00e583ddb393a50b2c22c04f56f1fd7614c43d5e4ff1e` |
| Bitácora 2027 | `data/decisiones/Bitacora_decisiones_para_2027.json` | `e0d5dbc62a515628c5c0c3423f8d704d96c67b1eb93ee6f003f76162d34705ed` |

`data/` es de solo lectura. Los hashes se recalculan al final del pipeline y permanecen estables.

---

## 2. Pipeline

```text
data/ (Excel, JSON)
    ↓
loader.py: descubrimiento, hash, carga
    ↓
excel_to_md.py: lectura literal de celdas
    ↓
outputs/markdown/: un .md por hoja + manifest.json + cell_index.csv
    ↓
canonical.py: capa normalizada y periodos
    ↓
validation.py: identidades, reglas y anomalías
    ↓
reporting.py: outputs/f1/
    ↓
analysis.py → notebooks/01_revision_matrices.ipynb
    ↓
.specify/memory/interpretations.json + open_questions.json
```

El Markdown literal y la capa canónica comparten los mismos archivos de origen, pero son responsabilidades separadas:

- `excel_to_md.py` no interpreta tablas ni periodos.
- `canonical.py` clasifica periodos, etiquetas y tipos de dato del juego.
- `cell_index.csv` conecta cada celda Markdown con su coordenada Excel.

---

## 3. F1.2 literal — estado verificado

Salida en `outputs/markdown/`:

- 3 Excel exportados.
- 33 hojas.
- 33 archivos `.md`, uno por hoja, más `index.md`.
- `cell_index.csv` con 11.859 celdas no vacías de Excel.
- 0 celdas perdidas.
- 0 duplicadas.
- 0 diferencias de texto.
- 0 filas Markdown ausentes.
- Hojas ocultas: 0 en las matrices actuales; el extractor las recorre si existen.
- `data/` intacto.

Columnas de `cell_index.csv`:

```text
source, source_path, sheet, cell, row, col, raw_text, data_type,
is_merged, merged_range
```

`raw_text` es el texto literal. No existe columna `value`. No se evalúan fórmulas ni valores calculados.

### Diferencia 12.037 vs 11.859

- 12.037 es el número de celdas brutas no vacías del inventario completo.
- 11.859 son celdas de hojas Excel.
- 178 son celdas de las bitácoras JSON: 109 de 2026 y 69 de 2027.
- `cell_index.csv` indexa solo Excel; por eso el test de “perdidas 0” se refiere al universo Excel.
- No hay 178 celdas perdidas: hay 178 celdas JSON fuera del alcance de F1.2 literal.

---

## 4. Qué está verificado

- **Q-001:** bloque detallado adoptado; reservas detalladas 930.663; resumen 1.177.053; D-02 es explicación del usuario sin documento independiente. Residuales de 1 € registrados sin redondear.
- **Q-008:** `Matriz_general_2` es el cierre real y ejecutado de 2027; clasificación por tabla y periodo.
- **Q-009:** aceptada como excepción documentada; se conserva 30.000 real en bufandas 2027 y no se cambia RG-02.
- **INT-003:** aceptada como inferencia; valor bruto 38.610,39 y normalizado 3.861.039 separados.
- **Defectos corregidos:** `Año+2`, deuda trimestral y pasivo corriente trimestral.
- **Pruebas:** 42 passed, 0 xfailed.
- **Notebook:** 24 celdas, 0 errores.
- **Integridad:** hashes de `data/` sin cambios.

---

## 5. Separación RG / CF / HY / PD

La fuente normativa es `specs/000-general-system/spec.md`.

### Reglas del juego (RG)

- RG-01: precio ±15 % respecto al periodo anterior.
- RG-02: producción `0` mantiene, `1` detiene, `2..600.000` unidades reales.
- RG-03: ocupación mínima del 60 % de la planta para penalización; costes industriales por línea.
- RG-04: mantenimiento 1 %–7 % del activo fijo bruto de fábrica.
- RG-05: LP 6,6 % / CP 5,9 %; extraordinario 7,6 % nominal del periodo y 13,2 % de penalización.
- RG-06: crédito extraordinario automático si la caja queda negativa.
- RG-07: dividendos solo con resultado positivo del periodo anterior.
- RG-08: descuento de canal 7 %–25 %; promoción 0–400.000; incentivo 0 %–12 %.
- RG-09: diseño 0–350.000; amplitud de gama por línea.
- RG-10: ampliación de capacidad 0–3 con inversión y capacidad publicadas.
- RG-11: deuda pública CP hasta 500.000/trimestre; LP hasta 1.200.000 a 2 años.
- RG-12: cobros/pagos 1–365 días; cancelación LP hasta 500.000.

### Parámetros configurables (CF)

En `config/f1.toml`:

- `price_corridor_pct = 15.0`
- `occupancy_threshold_pct = 60.0`
- `occupancy_penalty_mode = "plant"`
- `occupancy_cost_mode = "line"`
- `balance_tolerance_eur = 1.0`

### Hipótesis (HY)

Las HY vigentes están en `spec.md`. Destacan:

- 2027 es cierre real confirmado; la producción de bufandas es una excepción aceptada.
- La demanda y conversión no tienen función oficial verificada.
- La caja mínima operativa se derivará de obligaciones y riesgo.
- La puntuación de Valor de Compañía es configuración, no fórmula oficial.

### Pendientes y excepciones (PD)

- PD-05: escala de ingresos; inferencia aceptada, no corrección automática.
- PD-06: 150.000 de gastos generales; hipótesis del usuario sin evidencia documental.
- PD-07: CAPEX 1.133.000 sin causa documentada.
- PD-09: pasivo corriente trimestral no concilia con todos sus componentes.
- PD-10: alias de proveedores.
- PD-11: pesos del Valor de Compañía no oficiales.
- PD-15: capturas manuales solo se normalizan si el periodo es explícito.
- PD-16: producción de bufandas 2027; aceptada como excepción.

---

## 6. Qué no está resuelto y por qué no bloquea

- **D-02 sin documento independiente.** La decisión de usar el detalle está tomada; la trazabilidad documental queda como limitación.
- **Residuales de 1 €.** Se conservan sin redondear; el modelo debe usar tolerancias explícitas, no corregir la fuente.
- **Producción de bufandas 2027.** Excepción aceptada; no se generaliza a otros ejercicios.
- **Pasivo corriente trimestral.** Se detecta la diferencia; no impide usar el cierre anual.
- **Gastos generales y CAPEX.** Hay hipótesis y desglose, pero no documento de origen para el resto.
- **Escala de ingresos.** Inferencia aceptada con valor bruto y normalizado separados.

Ninguna de estas limitaciones impide iniciar F2; todas deben quedar visibles en el modelo y en los informes.

---

## 7. Checklist para cargar una matriz nueva

1. Copiar el Excel original a `data/` sin editarlo.
2. Ejecutar `uv run python -m cg_01 --quiet`.
3. Revisar `outputs/f1/inventory.json`: fuente, hash, hojas, periodos y tipos.
4. Revisar `outputs/markdown/manifest.json`: dimensiones, rangos combinados y advertencias.
5. Revisar `outputs/markdown/cell_index.csv`: columnas y recuento por hoja.
6. Ejecutar `uv run pytest -q`; la fidelidad literal debe dar 0 pérdidas, 0 duplicados y 0 diferencias.
7. Clasificar cada tabla y periodo en la capa canónica; no etiquetar todo el archivo como `real`.
8. Registrar cualquier ambigüedad en `.specify/memory/open_questions.json` o como inferencia/hipótesis en `interpretations.json`.
9. No editar los `.md` generados ni los originales de `data/`.

---

## 8. Fase 1 cerrada y habilitación de F2.1

F1.4 está aprobada. La Fase 1 queda cerrada con las PD como limitaciones documentadas, no como cifras contables verificadas.

F2.1 autorizada:

- estado de resultados e ingresos/costes por producto 2026–2027;
- balance histórico y estructura de deuda, incluida la porción corriente del LP;
- flujo de caja y liquidez;
- conciliación histórica contra 2026 real y 2027 real;
- tolerancias 0,005 € / 1 €;
- estados `confirmed`, `inferred_accepted`, `pending`, `accepted_exception`, `unreconciled`;
- las 16 críticas de balance y las 81 anomalías de balance se marcan `unreconciled`;
- cualquier derivado que use una cifra no conciliada hereda la marca.

Condiciones de F2.1:

- motor determinista funcional;
- pruebas verdes;
- conciliaciones históricas documentadas;
- lista de discrepancias restantes;
- `data/` intacto.

Fuera de F2.1: producción/inventarios como módulo propio, Monte Carlo y optimización. F2.1 se detiene al completar el corte vertical.

---

## 9. Riesgos abiertos y mitigación

| Riesgo | Mitigación |
|---|---|
| D-02 sin documento | Mantener la decisión y la limitación visibles; no presentar D-02 como evidencia documental. |
| Residuales de 1 € | Usar tolerancia configurable; no redondear ni corregir la fuente. |
| Excepción de bufandas 2027 | Aislarla como caso; no cambiar RG-02. |
| Escala de ingresos | Conservar valor bruto y normalizado; no aplicar corrección silenciosa. |
| Pasivo corriente trimestral | Auditar por componentes; documentar impuestos no desglosados. |
| CAPEX/gastos generales sin origen | Marcarlos como hipótesis/desglose parcial en el modelo. |
| Matrices solapadas | Precedencia por ejercicio, métrica y periodo; conservar todas las versiones. |
| Markdown literal no semántico | Usar la capa canónica para interpretar; no leer el Markdown como regla. |
| Hojas ocultas | El extractor las recorre y el manifiesto marca `hidden`. |
| Capturas manuales ambiguas | Normalizar solo con periodo explícito; marcar el resto con advertencia. |


## 9. F2.1 aprobada

Salidas en `outputs/f2/`:

- `income_statement.csv`
- `balance.csv`
- `debt.csv`
- `cash_flow.csv`
- `reconciliation.csv`
- `manifest.json`
- `report.md`

Resultados de la entrega:

- 164 filas de cálculo y conciliación: 97 confirmed, 15 inferred_accepted, 22 pending y 30 unreconciled.
- 81 anomalías de balance, de ellas 16 críticas, todas `unreconciled`.
- Tolerancias 0,005 € / 1 €.
- Conciliación de resultados 2026–2027: ingresos exactos; coste de ventas por producto con residual de 1 €; márgenes y resultado neto exactos.
- Balance detallado: residual de 1 € en 2026 y 2027; patrimonio reportado no conciliado.
- Deuda anual: 1.225.154 € en 2026 y 933.031 € en 2027, con porción corriente del LP de 297.748 € y 313.036 €.
- Caja: 1.916.796 → 503.378 en 2026 y 503.378 → 1.151.288 en 2027; el puente incluye la Depreciación Fábrica no-cash (278.100 € / 327.300 €) y el residual queda en 1 € / 0 €.
- `report.md` contiene la tabla resumen de cada cifra con estado, anomalía fuente, conciliación, tolerancia, fuente y PD.
- Pruebas: **42 passed**, incluida la suite F2.
- F2.1 aprobada por el usuario. F2.2 tiene página de alcance en `docs/f2_2_scope.md`, pendiente de aprobación.

No se inicia Monte Carlo ni optimización.
