# Contexto de Decisiones para Agentes de IA: Módulo de Producción (Matriz 2)

## 1. Identificación del Área
* **Módulo:** Producción / Operaciones e Infraestructura (Periodo 2/4 - Decisiones para 2028).
* **Objetivo General:** Planificar los volúmenes de fabricación, gestionar la capacidad instalada de la fábrica, determinar el presupuesto de mantenimiento industrial e implementar proyectos de eficiencia logística y reducción de costos variables de operación.

---

## 2. Palancas de Decisión Principales (Variables Modificables y Restricciones)

### A. Nivel de Ampliación de Capacidad de Fabricación
* **Líneas:** Corbatas, Bufandas, Calcetines.
* **Opciones de Decisión:** Nivel discreto **0**, **1**, **2** o **3** (Anterior en todas las líneas: 0).
* **Impacto:** Incrementa la capacidad máxima disponible para períodos futuros mediante inversión en Activo Fijo Industrial.

### B. Unidades a Producir por Producto
* **Líneas:** Corbatas, Bufandas, Calcetines.
* **Límites:** Rango continuo entre **0** y **600.000** unidades por línea.
* **Reglas y Restricciones Especiales del Sistema:**
  * **Regla de Ocupación Mínima (60%):** Si el volumen total producido se sitúa por debajo del **60% de la capacidad de planta**, se generan **gastos excepcionales** significativos por despido de personal e ineficiencia industrial.
  * **Comportamiento del Valor Cero (`0`):** Ingresar `0` **no detiene** la producción; el sistema interpretará la decisión como mantener exactamente el volumen producido en el período anterior (Anterior: Corbatas 215.000, Bufandas 32.000, Calcetines 40.000).
  * **Detención Deliberada de Producción (`1`):** Para detener por completo la fabricación de una línea de producto, se debe ingresar obligatoriamente el valor `1` en la casilla correspondiente.

### C. Porcentaje de Gastos de Mantenimiento
* **Límites:** Rango continuo entre **1%** y **7%** (Anterior: 3%).
* **Base de Cálculo:** Se aplica directamente sobre el **Activo Fijo Bruto de Fábrica**.
* **Impacto:** Preserva la operatividad de la maquinaria, previene mermas y evita la depreciación acelerada del activo industrial.

---

## 3. Tablas de Estructura de Capacidad, Costos e Inversión Industrial

### Tabla 1: Estructura de Ampliación de Capacidad de Fabricación por Nivel
| Línea de Producto | Nivel 1 (Capacidad / Inversión) | Nivel 2 (Capacidad / Inversión) | Nivel 3 (Capacidad / Inversión) |
| :--- | :---: | :---: | :---: |
| **Corbatas** | +20.000 uds / 140.000 €/$ | +40.000 uds / 320.000 €/$ | +60.000 uds / 750.000 €/$ |
| **Bufandas** | +8.000 uds / 120.000 €/$ | +17.000 uds / 220.000 €/$ | +45.000 uds / 450.000 €/$ |
| **Calcetines** | +35.000 uds / 130.000 €/$ | +50.000 uds / 170.000 €/$ | +125.000 uds / 450.000 €/$ |

### Tabla 2: Capacidad Instalada e Histórico de Unidades a Producir
| Línea de Producto | Capacidad Instalada (2024-2027) | Decisión Anterior (2027) | Rango Permitido de Producción |
| :--- | :---: | :---: | :---: |
| **Corbatas** | 215.000 unidades | 215.000 unidades | 0 a 600.000 unidades |
| **Bufandas** | 30.000 unidades | 32.000 unidades | 0 a 600.000 unidades |
| **Calcetines** | 40.000 unidades | 40.000 unidades | 0 a 600.000 unidades |

### Tabla 3: Nivel de Costes Base de Materia Prima por Tipología de Proveedor
| Proveedor | Corbatas (2027) | Bufandas (2027) | Calcetines (2027) | Corbatas (2026) | Bufandas (2026) | Calcetines (2026) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Económica** | 0,00 | 0,00 | 0,36 | 1,34 | 3,63 | 0,36 |
| **Estándar** | 1,90 | 5,29 | 0,00 | 0,00 | 0,00 | 0,00 |
| **Premium** | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |

### Tabla 4: Índice Multiplicador de Coste de Elaboración por Amplitud de Gama
*Nota: Este índice multiplica sobre el resto de componentes para calcular el coste industrial total.*

| Amplitud de Gama | Factor Corbatas | Factor Bufandas | Factor Calcetines |
| :---: | :---: | :---: | :---: |
| **Gama 1** | 1,00x | 1,00x | 1,00x |
| **Gama 3** | 1,01x | 1,05x | 1,05x |
| **Gama 5** | 1,02x | 1,07x | 1,08x |
| **Gama 7** | 1,04x | 1,10x | 1,12x |
| **Gama 9** | 1,06x | 1,13x | 1,15x |
| **Gama 11** | 1,09x | 1,15x | 1,16x |
| **Gama 13** | 1,12x | 1,19x | 1,16x |
| **Gama 16** | 1,15x | 1,22x (Máx.) | 1,16x (Máx.) |
| **Gama 19** | 1,18x | 1,22x | 1,16x |
| **Gama 21** | 1,19x | 1,22x | 1,16x |
| **Gama 23** | 1,21x | 1,22x | 1,16x |
| **Gama 25** | 1,23x (Máx.) | 1,22x | 1,16x |

---

## 4. Proyecto Especial Activo de Inversión Operativa (Sub-pestaña)

### Proyecto: Mejora del Sistema de Almacén y Distribución de Productos (Centro Logístico Común)
* **Objetivo:** Adhesión al nuevo centro logístico común promovido por la Asociación de Empresas Industriales de la región.
* **Beneficio Operativo Directo:** Reducción del coste de transporte y almacenaje en **24 €/$** por unidad.
* **Opciones de Decisión:**
  * **Sin Inversión (NS/NC):** No se adhiere al proyecto. No exige desembolso ni genera ahorro de costos.
  * **Opción 1 (Inversión Directa):**
    * **Presupuesto / Inversión:** **435.000 €/$**
    * **Impacto Contable/Financiero:** Se registra en el **Activo No Corriente** (Inmovilizado Material) e incrementa los **gastos de depreciación** anuales en la cuenta de pérdidas y ganancias.
  * **Opción 2 (Adquisición de Participación de Capital):**
    * **Presupuesto / Inversión:** **635.000 €/$**
    * **Impacto Contable/Financiero:** Se registra como **Participación en el Activo No Corriente** del Balance. **No genera impacto de depreciación** en el resultado operativo (PyG).

### Tabla 5: Matriz de Opciones del Proyecto Especial de Logística
| Opción de Decisión | Modalidad de Vinculación | Presupuesto (€/$) | Imputación Contable | Impacto en PyG |
| :--- | :--- | :---: | :--- | :--- |
| **Sin Inversión (NS/NC)** | No adhesión al proyecto | 0 | Ninguno | Sin desembolso ni ahorro de costos |
| **Opción 1** | Inversión Directa | 435.000 | Activo No Corriente | Incrementa los gastos de depreciación |
| **Opción 2** | Participación de Capital | 635.000 | Participación Activo No Corriente | Sin gastos de depreciación en PyG |