# Estado actual de Fase 1 (cerrada) — cg_01

Fecha: 2026-10-23 (actualizado 2026-11-09 con el cierre de 2029)  
Estado: F1.1, F1.2 literal y F1.3 aceptadas; F1.4 aprobada; F2.1 aprobada; cierre 2029 integrado.  
Alcance: Fase 1 cerrada. F2 cubre 2024–2029; backtest, varianza y forecast 2030 pendientes.

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

---

## 10. Actualización 2026-11-09 — cierre de 2029 integrado

### Fuentes

| Fuente | Periodo | Estado |
|---|---|---|
| `data/Matriz_General_0.xlsx` … `Matriz_General_1.xlsx` | 2024–2026 | sin cambios |
| `data/Matriz_general_2.xlsx` | 2024–2027 | sin cambios |
| `data/Matriz_general_3.xlsx` | 2024–2028 | sin cambios |
| `data/Matriz_General_4.xlsx` | 2024–2029 + escenarios 2030/2032 | nueva |
| `data/decisiones/Bitacora_decisiones_para_2029.json` | 2029 | nueva |

El pipeline procesa 9 fuentes, 22.586 celdas no vacías y 11.743 observaciones
canónicas; los hashes permanecen estables. La capa F1 detecta 2029 y sus cuatro
trimestres, y conserva los bloques de escenario 2030/2032 del simulador.

### Motor F2

- Cobertura: **2024–2029** (`config/f2.toml`, `end = 2029`).
- 492 filas: 284 `confirmed`, 59 `inferred_accepted`, 53 `pending`, 96 `unreconciled`.
- 142 anomalías de balance, 25 críticas, todas `unreconciled`.
- 2029: ingresos 6.206.657 €; margen bruto 62,5 %; resultado después de impuestos 1.788.820 €.

### Identidad de fuentes (corrección)

Los `source_id` se enumeran por orden de descubrimiento. Al entrar
`Matriz_General_4.xlsx`, el orden sensible a mayúsculas renumeró las matrices y dejó
la precedencia y los alias de `config/f2.toml` apuntando a otro libro.

Corregido en dos capas:

1. Descubrimiento en orden insensible a mayúsculas: `matriz_general_3` vuelve a
   `SRC-XLSX-004` y `matriz_general_4` recibe `SRC-XLSX-005`.
2. Cada fuente expone un `source_key` estable (ruta relativa a `data/`). La
   precedencia y los alias se declaran con esa clave y `bind_sources()` los resuelve
   contra el `source_id` vigente. Las claves desconocidas se informan en el manifiesto
   F2 (`unresolved_source_bindings`) en vez de ignorarse.

Prueba de regresión: `tests/test_source_identity.py` fija el `source_id` publicado de
cada matriz y demuestra que la clave sobrevive a una renumeración.

### Capa analítica

- `uv run python -m cg_01.fpa.marts` reconstruye `outputs/f2` y `data/processed` en un
  solo paso reproducible (antes solo lo hacían los tests).
- 13 tablas, 532 filas. `dim_period` cubre 2024–2029 anual y 2024-Q1…2028-Q4 trimestral.
- `fact_sales` mantiene granularidad trimestral 2024–2028; 2029 no tiene ventas
  trimestrales en la fuente (limitación L-12). El volumen anual de 2029 está en
  `fact_product_annual`.

### Verificación

`uv run pytest -q` → **56 passed**. El CI de GitHub vuelve a verde.

### Pendiente

1. Motor de varianza (bridge 2026 y accuracy 2026–2029) reproducible.
2. Backtest rolling-origin F1/F2 con Régimen A y B.
3. Forecast 2030.
4. Dashboard Power BI y capturas (fuera de alcance de esta sesión).

---

## 11. Hechos de mercado y varianza (2026-11-09)

### `fact_market`

Granularidad año × producto, 18 filas. Unidades de mercado, unidades vendidas,
cuota, demanda intencionada, demanda no servida del mercado y brecha propia de la
compañía. Las tres medidas de mercado están completas 2024–2029; las de demanda
existen 2026–2028 porque el libro de 2029 no publica esa tabla (L-15).

Para obtenerla se añadió al motor canónico la extracción del bloque "Intención de
Compra VS Ventas", que está transpuesto (filas = productos, columnas = medidas) y
por eso el detector de periodos no lo veía. Treinta y cuatro observaciones nuevas,
sin anomalías adicionales.

### `fact_variance`

Granularidad periodo × driver × línea, 39 filas, 2026–2029. Cada fila es un impacto
en el resultado, firmado, de modo que las filas de un año suman exactamente la
variación del resultado neto:

| Año | Efectos | Actual − budget |
|---|---:|---:|
| 2026 | −243.137 | −243.137 |
| 2027 | +280.350 | +280.350 |
| 2028 | +86.598 | +86.598 |
| 2029 | −337.072 | −337.072 |

Cascada de 2026: volumen −2.607; precio +41.536; mix +1; coste unitario +35.527;
OPEX −359.888; resultado financiero +24.294; extraordinario +18.000.

Los planes de producción de 2027 vienen a cero en la bitácora ("mantener plan
anterior"), así que se arrastran desde 2026. Las bitácoras de 2028 y 2029 usan otro
esquema (`modulos.produccion.unidades_a_producir`) y también se leen.

### Ventas trimestrales

La hoja de ventas apila varias tablas trimestrales (unidades reales, cuotas de
competidores, unidades caducadas). El hecho elegía la última y publicaba 10.456
unidades de corbatas en 2028 en vez de 234.538. Ahora se queda con la serie cuyos
cuatro trimestres suman el total anual del mismo libro (L-16).

### Verificación

`uv run pytest -q` → **64 passed**. `fact_variance` incluye una prueba que exige que
la cascada cuadre al céntimo en los cuatro años.

---

## 12. Backtest rolling-origin (2026-11-09)

`fact_backtest`: 60 filas (2 folds × 2 regímenes × 15 líneas de P&L). Cada fila
guarda pronóstico, real, error firmado, error porcentual absoluto y sesgo. MAPE y
sesgo se agregan en el dashboard, no se congelan en el hecho.

Modelo: mismo motor en ambos regímenes; solo cambia la información disponible.

- **A (con decisiones)**: precios, producción planificada y marketing del año
  objetivo desde la bitácora; coste unitario del último año cerrado.
- **B (sin decisiones)**: último año cerrado, plano.

El coste unitario no está en la bitácora, así que se arrastra en ambos regímenes y
se cancela en el delta (L-18).

### Resultados

| Fold | Objetivo | MAPE A | MAPE B | Delta |
|---|---|---:|---:|---:|
| F1 | 2028 | 26,6 % | 32,3 % | −5,7 pp |
| F2 | 2029 | 33,1 % | 32,1 % | +1,0 pp |

Por línea, en el fold limpio (F1):

| Línea | Error A | Error B |
|---|---:|---:|
| Ingresos | 0,3 % | 15,7 % |
| Margen bruto | 9,9 % | 24,1 % |
| Resultado neto | 25,5 % | 55,0 % |

### El log de 2029 no cuadra

La bitácora de 2029 registra precios de 16,20 / 27,00 / 3,08 con 10 % de descuento;
la matriz publica 20,70 / 34,50 / 4,14 y el descuento efectivo es del 15 %. El
presupuesto de ingresos (6.198.132) coincide con el cierre, no con la bitácora.

Regime A usa la bitácora por definición. Por eso todas las filas F2-A se exportan
con `status_key = pending`: el error de 2029 mide un defecto del dato, no del
modelo (L-17). El backtest detecta el input malo en lugar de esconderlo.

### Verificación

`uv run pytest -q` → **71 passed**. Incluye: cobertura de folds y regímenes,
consistencia de error/porcentaje/sesgo, que A bata a B en el fold limpio y que el
log inconsistente quede marcado.

---

## 13. Forecast vivo 2030 (2026-11-09)

`fact_forecast`: 120 filas = 4 escenarios × 2 regímenes × 15 líneas. Periodo 2030,
fold F3, `dim_period` marca 2030 como `is_forecast = true`.

Base de cálculo: el cierre ejecutado de 2029. **No se usa la bitácora de 2029**
porque no concilia con su propio cierre (L-17). Esto se decidió explícitamente para
no propagar un dato roto a tres años vista.

Escenarios (supuestos declarados, L-19):

| Escenario | Precio | Volumen | Coste unitario |
|---|---:|---:|---:|
| Base | ×1,00 | ×1,00 | ×1,00 |
| Upside | ×1,02 | ×1,05 | ×1,00 |
| Downside | ×0,98 | ×0,95 | ×1,00 |
| Stress | ×0,95 | ×0,90 | ×1,05 |

Resultados:

| Escenario | Ingresos | Resultado neto A | Resultado neto B |
|---|---:|---:|---:|
| Stress | 5.306.691 | 1.209.825 | 1.497.828 |
| Downside | 5.778.397 | 1.554.879 | 1.643.324 |
| Base | 6.206.656 | 1.788.821 | 1.788.821 |
| Upside | 6.647.329 | 2.032.072 | 1.934.317 |

Regime A mueve precio y volumen; B solo volumen. En Base ambos coinciden por
construcción: sin decisiones nuevas, saber las palancas no aporta nada. En Downside
y Stress, B conserva más resultado porque A aplica además el recorte de precio.

### Verificación

`uv run pytest -q` → **74 passed**. Incluye: cobertura de escenarios y regímenes,
que el Base reproduzca el cierre de 2029, el orden Stress < Downside < Base <
Upside, y que 2030 esté marcado como pronóstico en `dim_period`.
