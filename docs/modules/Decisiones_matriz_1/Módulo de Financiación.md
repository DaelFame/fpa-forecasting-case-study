# Módulo de Financiación

## 1. Identificación del Área
* **Módulo:** Financiación / Gestión Financiera y Tesorería.
* **Objetivo General:** Garantizar la liquidez y solvencia de la compañía, estructurar la deuda bancaria (a corto y largo plazo), gestionar el capital de trabajo (días de cobro a clientes y pago a proveedores) y definir la política de retribución al accionista (dividendos) y capitalización de reservas.

---

## 2. Palancas de Decisión Principales (Variables Modificables y Restricciones)

### A. Solicitud de Préstamo a Largo Plazo (LP)
* **Límites:** Rango continuo entre **0** y **10.000.000** unidades monetarias (Anterior: 0).
* **Condiciones:** Tasa de interés de referencia del **6,6%** anual con un plazo de vencimiento a **8 años**.
* **Impacto:** Otorga liquidez estructural de largo plazo para financiar grandes inversiones en activo fijo (ampliaciones de fábrica o proyectos especiales) sin presionar la tesorería inmediata.

### B. Solicitud de Préstamo a Corto Plazo (CP)
* **Límites:** Rango continuo entre **0** y **500.000** unidades monetarias (Anterior: 0).
* **Condiciones:** Tasa de interés del **5,9%** anual con un plazo de vencimiento de **1 año**.
* **Impacto:** Otorga liquidez inmediata para cubrir desfases temporales de tesorería, necesidades puntuales de capital de trabajo o pequeñas inversiones operativas.

### C. Plazo de Cobro a Clientes (Días)
* **Límites:** Rango continuo entre **1** y **365** días (Anterior: 45 días).
* **Impacto:** 
  * **Reducir días:** Acelera el ingreso de efectivo y reduce las cuentas por cobrar, mejorando la liquidez, pero puede restar competitividad comercial frente a los clientes.
  * **Aumentar días:** Mejora el atractivo comercial y la fidelización del cliente, pero incrementa las necesidades financieras e inmoviliza caja en el activo corriente.

### D. Plazo de Pago a Proveedores (Días)
* **Límites:** Rango continuo entre **1** y **365** días (Anterior: 45 días).
* **Impacto:** 
  * **Aumentar días:** Permite a la compañía financiarse a través de los proveedores, demorando las salidas de caja y mejorando la liquidez inmediata.
  * **Reducir días:** Puede mejorar las condiciones comerciales o descuentos por pronto pago con proveedores, pero exige mayor disponibilidad de tesorería.

### E. Cancelación Anticipada de Préstamo a Largo Plazo
* **Límites:** Rango continuo entre **0** y **500.000** unidades monetarias (Anterior: 0).
* **Impacto:** Destina el exceso de liquidez/efectivo disponible a amortizar deudas financieras previas, reduciendo los gastos financieros por intereses en periodos futuros.

### F. Porcentaje de Distribución de Dividendos (%)
* **Límites:** Rango continuo entre **0%** y **100%** del resultado después de impuestos (Anterior: 0%).
* **Condición de Activación:** Esta decisión **solo está disponible si el resultado del último periodo fue positivo** (2026: +154.951).
* **Impacto:** 
  * Un mayor porcentaje retribuye a los accionistas e incrementa el atractivo de la compañía en el mercado.
  * Las utilidades no distribuidas (100% - % Dividendos) se acumulan automáticamente como **Reservas Legales** dentro del Patrimonio Neto, fortaleciendo la solvencia y autonomía financiera de la empresa.

---

## 3. Condiciones Financieras de Referencia del Banco

| Tipo de Financiación | Tasa de Interés | Plazo de Vencimiento |
| :--- | :---: | :---: |
| **Préstamo Largo Plazo (LP)** | 6,6% | 8 años |
| **Crédito Corto Plazo (CP)** | 5,9% | 1 año |
| **Crédito Extraordinario (Penalización)** | 13,2% | 1 año |

---

## 4. Alertas Financieras y Reglas Operativas Clave

1. **Crédito Extraordinario Automático (Riesgo de Iliquidez):**
   * Si las salidas de caja superan el disponible de tesorería y la compañía se queda en números rojos (Efectivo < 0), el sistema concederá automáticamente un **Crédito Extraordinario** a una tasa penalizada del **13,2%** anual (más del doble de una tasa normal).
2. **Cálculo de Necesidades Financieras:**
   * La IA debe prever las salidas de caja generadas por las decisiones de otros módulos (ampliaciones de fábrica, inversiones en proyectos especiales de energía/almacén, gastos de promoción, compras de materia prima) y compararlas con la tesorería inicial disponible (2026: 503.378) antes de fijar los préstamos o dividendos.
