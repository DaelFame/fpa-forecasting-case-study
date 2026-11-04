# Alcance F2.2 — Producción, inventarios y coste de ventas

Fecha: 2026-10-23  
Estado: página de alcance para aprobación. **F2.2 no implementada.**

## 0. Entrada

- F2.1 aprobada.
- Se heredan las reglas de F2.1: tolerancias 0,005 € / 1 €, estados por cifra, separación `source_anomaly_status` / `model_reconciliation_status`, y las 81 anomalías de balance como `unreconciled`.
- No se corrigen fuentes, no se inventan valores y no se sobrescribe `data/`.

## 1. Qué entra

- Producción histórica 2026–2027 por línea.
- Inventarios históricos de producto terminado por línea.
- Coste de ventas reconstruido y conciliado por producto y total.
- Costes unitarios y su conciliación con el coste de ventas de fuente.
- Ocupación de planta y ocupación por línea, con reglas separadas.
- Cruce con `factory_depreciation_cash` sin duplicar depreciación.
- Consolidación de causas `unreconciled` por cuenta canónica + periodo.
- Informe y tests de F2.2.

## 2. Qué no entra

- Decisiones de producción 2028 o simulación forward.
- Monte Carlo.
- Optimización.
- Valoración de la Compañía.
- Corrección o reclasificación del balance.
- Reconstrucción de inventarios valorados con un método de coste no documentado.
- Producción como variable de decisión para F3/F4.

## 3. Fuentes y precedencia

- **2027:** `Matriz_general_2` como cierre real principal, clasificando por tabla y periodo.
- **2026:** Matriz 1 y comparativos de Matriz 2; Matriz 2 prevalece cuando la métrica y el periodo son comparables.
- **2024–2025:** histórico para apertura de inventarios y comparaciones.
- Se conservan todas las versiones y las discrepancias.

## 4. Modelo de producción e inventarios

Para cada línea `p` y periodo `t`:

```text
inventory_units[p,t] = inventory_units[p,t-1] + production_units[p,t] - sales_units[p,t]
```

Criterio de aceptación:

- La identidad debe ser exacta para 2026 y 2027 en Corbatas, Bufandas y Calcetines.
- `production_units` se toma de fuente; no se deriva de ventas.
- `inventory_units` se toma de fuente y se cruza con la identidad.
- El valor de inventario se toma de fuente. **No se reconstruye** desde costes unitarios porque el método de valoración no está documentado.
- La ocupación por línea se toma de `Produccion`; la ocupación de planta, de `Indicadores Clave`.
- `occupancy_penalty_mode = "plant"` y `occupancy_cost_mode = "line"` se reportan por separado. No se mezclan.

## 5. Coste de ventas: dos capas explícitas

### 5.1. Capa contable de componentes

Para cada producto:

```text
coste_ventas_componentes =
    coste_fabricacion_ventas
  + coste_logistica_externa
  + coste_almacenaje
  + coste_no_calidad
```

Se compara con `Total coste de las ventas` de la misma tabla.

Criterio:

- 2026: suma de productos 2.048.744 frente a fuente 2.048.743 → residual **1 €** documentado.
- 2027: suma de productos 2.098.662 frente a fuente 2.098.663 → residual **1 €** documentado.
- No se corrige el total de fuente.

### 5.2. Capa de coste unitario

Para cada producto:

```text
coste_unitario_ventas =
    coste_unitario_fabricacion * sales_units
  + coste_logistica_externa
  + coste_almacenaje
  + coste_no_calidad
```

Los costes unitarios de fuente están redondeados a 2 decimales. Por eso esta capa no se fuerza a cero:

- tolerancia de redondeo por línea: `0,005 € * sales_units`;
- tolerancia adicional por redondeo de componentes: `1 €`;
- si el residual supera esa cota, se marca `unreconciled`;
- si queda dentro, se marca `documented_residual` con la cota aplicada.

Esta capa explica el coste unitario; la capa contable de componentes es la que se usa como ancla del estado de resultados. No se sustituye el total de fuente por el reconstruido.

## 6. Depreciación de fábrica

- `factory_depreciation_cash` ya está en el puente de caja de F2.1.
- La depreciación de fábrica está embebida en el coste de fabricación de ventas; **no se añade otra vez** al coste de ventas.
- Cruce obligatorio:

```text
depreciación_resultados + depreciación_fábrica = incremento de Depreciación Acumulada
```

Valores verificados:

- 2026: 148.000 + 278.100 = **426.100 €**.
- 2027: 136.750 + 327.300 = **464.050 €**.

Si el cruce falla, la línea se marca `unreconciled`.

## 7. Q-009 / PD-16: excepción aislada

- 2026 Bufandas: producción 29.000.
- 2027 Bufandas: producción real 30.000; capacidad 30.000.
- Bitácora 2027: decisión `0`.
- Documentación de Matriz 2 declara anterior 32.000, que no coincide con 29.000 ni con 30.000.

Regla:

- **RG-02 se mantiene**: `0` significa mantener la producción anterior.
- Q-009/PD-16 se marca `accepted_exception` **solo** en la fila de producción de Bufandas 2027.
- No se generaliza a Corbatas, Calcetines ni a otros periodos.
- Los tests deben comprobar que la excepción no contamina otras líneas.

## 8. Herencia de balance y consolidación de `unreconciled`

- Las cifras de balance `unreconciled` se heredan; no se corrigen.
- Cualquier derivado que use una cifra `unreconciled` o `pending` hereda el estado y la causa.
- Para el informe, las 30 filas `unreconciled` se agrupan por **cuenta canónica + periodo**:
  - `total_assets`
  - `total_current_assets`
  - `total_liabilities`
  - `total_current_liabilities`
  - `reported_equity` / `patrimonio_neto`
  - `reserves`
- Cada grupo muestra una sola causa y la lista de métricas afectadas; no se repiten diez filas con la misma causa.
- La tabla resumen de `report.md` sigue mostrando cada cifra y su estado; la tabla consolidada evita duplicar la explicación.

## 9. Salidas previstas

Se mantienen los siete archivos de F2.1 y se añaden:

- `outputs/f2/production.csv`
- `outputs/f2/inventory.csv`
- `outputs/f2/cost_of_sales.csv`
- `outputs/f2/occupancy.csv`
- `outputs/f2/unreconciled_consolidated.csv`

`report.md` incluirá:

- tabla resumen por cifra y estado;
- conciliaciones de producción, inventario y coste de ventas;
- cruce de depreciación;
- ocupación planta/línea;
- excepción Q-009;
- tabla consolidada de causas `unreconciled`.

## 10. Tests de aceptación

- `test_production_inventory_identity_2026_2027`: producción − ventas = cambio de inventario, por línea y periodo.
- `test_inventory_units_reconcile_with_source`: inventario inicial + producción − ventas = inventario final.
- `test_cost_of_sales_component_reconciliation`: suma de componentes vs total de fuente; residual 1 € documentado.
- `test_cost_of_sales_unit_cost_reconciliation`: coste unitario × ventas + componentes vs coste de ventas; residual dentro de la cota de redondeo o `unreconciled`.
- `test_factory_depreciation_not_duplicated`: depreciación resultados + fábrica = incremento de depreciación acumulada.
- `test_occupancy_plant_and_line_are_separate`: valores de planta y línea, sin mezcla.
- `test_q009_is_isolated`: 30.000 en Bufandas 2027 `accepted_exception`; Corbatas/Calcetines no contaminados.
- `test_unreconciled_consolidation`: 30 filas agrupadas por cuenta + periodo; derivados heredan estado.
- `test_f2_2_report_summary`: tabla por cifra/estado y tabla consolidada.
- `test_sources_unchanged`: hashes de `data/` intactos.

## 11. Criterio de entrega

F2.2 se considerará entregada cuando:

- producción e inventarios concilien 2026–2027;
- coste de ventas esté reconstruido y conciliado con residual documentado;
- la depreciación de fábrica no se duplique;
- ocupación planta/línea esté separada;
- Q-009 quede aislada;
- las causas `unreconciled` estén consolidadas;
- los tests estén verdes;
- `data/` permanezca intacto;
- `report.md` muestre la tabla resumen y las conciliaciones.

No se inicia Monte Carlo ni optimización.
