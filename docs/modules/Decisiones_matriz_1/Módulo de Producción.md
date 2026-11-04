# Módulo de Producción

## 1. Identificación del Área
* **Módulo:** Producción / Operaciones e Infraestructura.
* **Objetivo General:** Planificar los volúmenes de fabricación, gestionar la capacidad instalada de la fábrica, determinar el presupuesto de mantenimiento industrial e invertir en proyectos de eficiencia operativa y reducción de costos directos (energía, transporte y almacenamiento).

---

## 2. Palancas de Decisión Principales (Variables Modificables y Restricciones)

### A. Nivel de Ampliación de Capacidad de Fabricación
* **Líneas:** Corbatas, Bufandas, Calcetines.
* **Opciones de Decisión:** Nivel **0**, **1**, **2** o **3**.
* **Estructura de Capacidad e Inversión:**
  * **Corbatas:**
    * Nivel 1: +20.000 unidades | Inversión: 140.000
    * Nivel 2: +40.000 unidades | Inversión: 320.000
    * Nivel 3: +60.000 unidades | Inversión: 750.000
  * **Bufandas:**
    * Nivel 1: +8.000 unidades | Inversión: 120.000
    * Nivel 2: +17.000 unidades | Inversión: 220.000
    * Nivel 3: +45.000 unidades | Inversión: 450.000
  * **Calcetines:**
    * Nivel 1: +35.000 unidades | Inversión: 130.000
    * Nivel 2: +50.000 unidades | Inversión: 170.000
    * Nivel 3: +125.000 unidades | Inversión: 450.000
* **Impacto:** Incrementa la capacidad máxima disponible para períodos futuros a cambio de un desembolso de inversión en activo fijo.

### B. Unidades a Producir por Producto
* **Líneas:** Corbatas, Bufandas, Calcetines.
* **Límites:** Rango continuo entre **0** y **600.000** unidades por línea.
* **Valores de Referencia (Capacidades Base Anteriores):**
  * Corbatas: 215.000 unidades
  * Bufandas: 30.000 unidades
  * Calcetines: 40.000 unidades
* **Reglas y Restricciones Especiales del Sistema:**
  * **Límite de Ocupación Mínima (60%):** Si se fabrica por debajo del 60% del uso total de la capacidad de planta, se generan **gastos excepcionales** por despido de personal e ineficiencia industrial.
  * **Comportamiento del Valor Cero (0):** Ingresar `0` en la casilla **NO detiene** la producción; el sistema interpretará que se desea mantener la cantidad producida en el período anterior.
  * **Detención Deliberada de Producción (1):** Para detener por completo la fabricación de una línea de producto, se debe ingresar exactamente el valor `1`.

### C. Porcentaje de Gastos de Mantenimiento
* **Límites:** Rango continuo entre **1%** y **7%** (Anterior: 3%).
* **Base de Cálculo:** Se aplica directamente sobre el **Activo Fijo Bruto de Fábrica**.
* **Impacto:** Preserva la eficiencia de la maquinaria, previene mermas y evita la depreciación acelerada del activo fijo industrial.

---

## 3. Tablas de Estructura de Costos Industriales

### A. Costo Base de Materia Prima por Tipo de Proveedor
| Proveedor | Corbatas | Bufandas | Calcetines |
| :--- | :---: | :---: | :---: |
| **Económica** | 1,34 | 3,63 | 0,36 |
| **Estándar** | 2,40 | 6,70 | 0,60 |
| **Premium** | 3,50 | 7,50 | 0,80 |

### B. Multiplicador de Costo por Amplitud de Gama
*El costo de elaboración se multiplica por este factor según la amplitud de gama seleccionada:*
* **Gama 1:** 1,00x
* **Gama 3:** 1,01x (Corbatas) | 1,05x (Bufandas/Calcetines)
* **Gama 5:** 1,02x (Corbatas) | 1,07x (Bufandas) | 1,08x (Calcetines)
* **Gama 15 (Máx. Bufandas):** ~1,22x
* **Gama 25 (Máx. Corbatas):** 1,23x

---

## 4. Proyectos Especiales de Inversión Operativa (Sub-palancas)

### Proyecto A: Generación de Energía Renovable (Planta Fotovoltaica)
* **Beneficio Operativo:** Reducción directa del costo de energía en **33 €/$**.
* **Opciones de Decisión:**
  * **Sin Inversión (NS/NC):** No se adhiere al proyecto.
  * **Opción 1 (Inversión Directa):**
    * **Presupuesto:** **145.000 €/$**
    * **Impacto Contable:** Registra Activo No Corriente e incrementa los **gastos de depreciación** en la cuenta de resultados.
  * **Opción 2 (Adquisición de Participación de Capital):**
    * **Presupuesto:** **205.000 €/$**
    * **Impacto Contable:** Registra Participación en el Activo No Corriente. No suma gastos de depreciación operativa al PyG.

### Proyecto B: Mejora del Sistema de Almacén y Distribución (Centro Logístico Común)
* **Beneficio Operativo:** Reducción directa del costo de transporte y almacenaje en **24 €/$**.
* **Opciones de Decisión:**
  * **Sin Inversión (NS/NC):** No se adhiere al proyecto.
  * **Opción 1 (Inversión Directa):**
    * **Presupuesto:** **435.000 €/$**
    * **Impacto Contable:** Registra Activo No Corriente e incrementa los **gastos de depreciación** en la cuenta de resultados.
  * **Opción 2 (Adquisición de Participación de Capital):**
    * **Presupuesto:** **635.000 €/$**
    * **Impacto Contable:** Registra Participación en el Activo No Corriente. No suma gastos de depreciación operativa al PyG.
