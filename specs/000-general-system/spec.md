# Especificación General — cg_01 / CompanyGame Spain10

Versión: 0.2.0
Estado: Fase 0 cerrada; Fase 1 cerrada y aprobada; F2.1 implementada y verificada
Depende de: `.specify/memory/constitution.md`
Documento de planificación: `plan.md`
Tareas de la fase: `tasks.md`

---

## 1. Problema empresarial

En cada cierre, la dirección debe decidir precios, producto, producción, financiación, inversiones y proyectos para el ejercicio siguiente. Esas decisiones afectan al Valor de la Compañía, pero también a la caja, la deuda, la solvencia, la ocupación industrial y la precisión presupuestaria.

El problema no es maximizar una única variable. Es elegir una combinación de decisiones que:

- mejore el Valor de la Compañía;
- preserve la liquidez y la continuidad operativa;
- mantenga una estructura de deuda sostenible;
- respete las reglas del juego;
- sea explicable y trazable;
- pueda compararse con una alternativa de referencia.

El sistema debe apoyar esa comparación y explicar las consecuencias de cada alternativa. No debe limitarse a emitir una puntuación sin justificación financiera.

---

## 2. Actores

| Actor | Responsabilidad |
|---|---|
| Dirección / usuario decisor | Define objetivos, revisa alternativas y aprueba decisiones |
| Analista | Prepara datos, ejecuta escenarios y valida resultados |
| Sistema | Carga, valida, calcula, simula, compara y explica |
| Responsable de datos | Aporta matrices, decisiones y cierres actualizados |

El sistema no sustituye la aprobación humana.

---

## 3. Alcance funcional

El sistema deberá cubrir, de forma progresiva:

| Bloque | Contenido |
|---|---|
| Fuentes y datos | Inventario, carga, clasificación, identificación de periodos, trazabilidad y validación |
| Modelo financiero | Reconstrucción histórica y proyección de resultados, balance y tesorería |
| Incertidumbre | Escenarios, sensibilidad y evaluación del riesgo |
| Evaluación | Comparación de decisiones, restricciones y línea base |
| Reporting | Conciliaciones, explicaciones, métricas y seguimiento |

### 3.1. Decisiones que debe apoyar

- Precio, descuento de canal, promoción e incentivos de ventas.
- Diseño, amplitud de gama y proveedor.
- Unidades a producir, ampliación de capacidad y mantenimiento.
- Préstamos LP/CP, plazos de cobro y pago, cancelación de deuda y dividendos.
- Inversiones financieras a corto y largo plazo.
- Proyectos especiales, CAPEX y otras inversiones estratégicas.

### 3.2. Información necesaria

- Último cierre real validado.
- Caja inicial y calendario de cobros y pagos.
- Deuda, vencimientos, intereses y condiciones.
- Activos financieros y su disponibilidad efectiva.
- Inversiones ya comprometidas.
- Necesidades de capital operativo.
- Capacidad, ocupación, inventarios y demanda.
- Decisiones históricas y resultados reales.
- Reglas del juego, parámetros e hipótesis vigentes.

### 3.3. Fuera de alcance

- Ejecutar decisiones automáticamente.
- Aprobar operaciones irreversibles o dilutivas sin autorización.
- Modificar los archivos originales de `data/`.
- Crear una base de datos, una API, una interfaz web o un servicio externo.
- Desarrollar en Fase 0 el modelo financiero, el simulador o el optimizador.
- Presentar como oficiales reglas, tasas o pesos no verificados.
- Convertir un Markdown generado en fuente original o en una segunda copia editable.

### 3.4. Arquitectura de datos y análisis

El flujo permanente es:

```text
fuentes originales y capturadas
        ↓
inventario, hash y clasificación
        ↓
Markdown generado para lectura
        ↓
capa normalizada única y trazable
        ↓
validación y anomalías
        ↓
notebook de auditoría
        ↓
interpretaciones confirmadas y preguntas abiertas
```

Reglas de arquitectura:

1. Los Excel y JSON originales permanecen inmutables en `data/`.
2. Las capturas manuales viven separadas, preferentemente en `data/manual/`, con frontmatter y procedencia.
3. El Markdown generado vive en `outputs/markdown/` y se identifica como derivado. No se edita como fuente.
4. F1.2 es un **extractor textual literal**: un `.md` por hoja con el contenido textual de cada celda no vacía, sin fórmulas, sin valores calculados y sin interpretación.
5. `cell_index.csv` conserva `raw_text` (no `value`), además de fuente, hoja, celda, fila, columna, tipo de celda, estado de combinación y rango combinado.
6. `manifest.json` conserva hash, hojas, dimensiones, rangos combinados y advertencias. Las hojas ocultas también se recorren.
7. Los cálculos usan la capa normalizada, no el Markdown.
8. El notebook llama a las funciones existentes y no duplica reglas de negocio.
9. Las interpretaciones confirmadas y las preguntas abiertas se registran en `.specify/memory/`.
10. El Markdown literal no decide encabezados, tablas, periodos ni tipos de dato del juego. Esa clasificación vive en la capa canónica.

### 3.5. Flujo de comprensión y preguntas

El trabajo sigue este orden:

```text
incorporar fuentes → verificar fidelidad → leer y comprender → contrastar periodos
→ registrar discrepancias → formular dudas concretas → registrar interpretaciones
→ implementar reglas verificadas → comprobar resultados
```

Antes de preguntar se revisan la documentación, la Constitución, la Spec y las decisiones ya confirmadas. Una pregunta debe incluir concepto, referencias, valores contradictorios, verificación realizada, alternativas con consecuencias y el dato o decisión necesaria. Se priorizan los asuntos que afectan a resultado, presupuesto, balance, caja, deuda y decisiones operativas.

---

## 4. Riesgos que el sistema debe ayudar a prevenir

- Iliquidez y crédito extraordinario.
- Endeudamiento excesivo o mal estructurado.
- Inversiones que comprometan obligaciones futuras.
- Penalizaciones por ocupación inferior al umbral.
- Precios fuera del corredor permitido.
- Errores por mala interpretación de la semántica de producción.
- Desviaciones presupuestarias graves.
- Decisiones basadas en datos inconsistentes.
- Exceso de confianza en un modelo no validado.
- Pérdida de trazabilidad entre decisión y resultado.

---

## 5. Evaluación de una decisión

Una decisión se evaluará como mínimo en estas dimensiones:

1. Valor de la Compañía.
2. Resultado económico y rentabilidad.
3. Precisión presupuestaria.
4. Liquidez y caja mínima.
5. Solvencia y estructura de deuda.
6. Producto, marca, distribución y posición de mercado.
7. Robustez frente a escenarios.
8. Explicabilidad y trazabilidad.
9. Comparación con una línea base.

**No se fija todavía una fórmula definitiva de puntuación.** Los pesos y la normalización son parámetros e hipótesis hasta disponer de una fuente oficial o de una decisión explícita.

Criterios de calidad de una decisión:

- es factible según las reglas;
- es financieramente sostenible;
- es robusta en escenarios razonables;
- es explicable;
- mejora o iguala la línea base sin deteriorar el riesgo de forma inaceptable.

---

## 6. Reglas del juego documentadas

Las siguientes reglas están documentadas en `docs/modules/` y se clasifican como **RG**. Su aplicación concreta puede depender de parámetros configurados. Que una regla esté documentada no implica que todas sus cifras estén libres de contradicción: las discrepancias se registran como **PD**.

| Código | Regla | Fuente |
|---|---|---|
| RG-01 | La variación de precio por producto no puede superar ±15 % respecto al periodo anterior | `docs/modules/Decisiones_matriz_1/Módulo de Ventas.md` |
| RG-02 | Producción: `0` mantiene la cantidad anterior; `1` detiene la línea; `2..600.000` son unidades reales | `docs/modules/Decisiones_matriz_1/Módulo de Producción.md`; `docs/modules/Decisiones_matriz_2/Modulo_Produccion_matriz_2.md` |
| RG-03 | Producir por debajo del 60 % del uso de la planta genera gastos excepcionales | `docs/modules/Decisiones_matriz_1/Módulo de Producción.md`; `docs/modules/Decisiones_matriz_2/Modulo_Produccion_matriz_2.md` |
| RG-04 | Mantenimiento entre 1 % y 7 % del activo fijo bruto de fábrica | `docs/modules/Decisiones_matriz_1/Módulo de Producción.md` |
| RG-05 | LP: 6,6 % a 8 años. CP: 5,9 % a 1 año. Extraordinario: 7,6 % calculado para el periodo (`Analisis de Balance!E98`) y 13,2 % como tasa de penalización (`B168`); contextos distintos (INT-011) | `docs/modules/Decisiones_matriz_1/Módulo de Financiación.md` |
| RG-06 | Si la caja queda negativa, se concede un crédito extraordinario automático | `docs/modules/Decisiones_matriz_1/Módulo de Financiación.md` |
| RG-07 | Los dividendos solo están disponibles si el resultado del periodo anterior fue positivo | `docs/modules/Decisiones_matriz_1/Módulo de Financiación.md` |
| RG-08 | Descuento de canal entre 7 % y 25 %; promoción entre 0 y 400.000 por línea; incentivo entre 0 % y 12 % | `docs/modules/Decisiones_matriz_1/Módulo de Ventas.md` |
| RG-09 | Diseño entre 0 y 350.000 por línea; amplitud de gama: corbatas 1–25, bufandas 1–15, calcetines 1–10 | `docs/modules/Decisiones_matriz_1/Módulo de Producto.md` |
| RG-10 | Ampliación de capacidad por niveles 0–3, con inversión y capacidad publicadas | `docs/modules/Decisiones_matriz_1/Módulo de Producción.md`; `docs/modules/Decisiones_matriz_2/Modulo_Produccion_matriz_2.md` |
| RG-11 | Deuda pública CP: hasta 500.000 por trimestre. Deuda pública LP: hasta 1.200.000 a 2 años | `docs/modules/Decisiones_matriz_1/Módulo de Inver Financieras.md` |
| RG-12 | Plazos de cobro y pago entre 1 y 365 días; cancelación anticipada de LP hasta 500.000 | `docs/modules/Decisiones_matriz_1/Módulo de Financiación.md` |

**RG-03 se interpreta en dos niveles:** la penalización por baja ocupación se evalúa sobre la planta global (`occupancy_penalty_mode=plant`), mientras que el cálculo de costes industriales usa la ocupación específica de cada línea (`occupancy_cost_mode=line`). La documentación respalda el umbral sobre el uso total de la planta; la distinción queda registrada en INT-006.

Las reglas de proyectos especiales y sus presupuestos se incorporarán al catálogo canónico en Fase 1. No se reproducen aquí para evitar duplicación y porque algunos importes figuran como “según parametrización”.

---

## 7. Parámetros configurables

Los siguientes valores son **CF**. No se hardcodean en la lógica: se cargan desde configuración versionada y deben quedar registrados con la versión del modelo.

| Código | Parámetro | Valor de referencia | Nota |
|---|---|---|---|
| CF-01 | Corredor de precios | 15 % | Regla RG-01 |
| CF-02 | Ocupación mínima | 60 % | Penalización sobre planta; costes industriales por línea (INT-006) |
| CF-03 | Rango de mantenimiento | 1 %–7 % | Regla RG-04 |
| CF-04 | Capacidades base | 215.000 / 30.000 / 40.000 | Corbatas / bufandas / calcetines |
| CF-05 | Límite de producción por línea | 600.000 | Regla RG-02 |
| CF-06 | Tipos de interés | LP 6,6 %; CP 5,9 %; extraordinario 7,6 % nominal / 13,2 % penalización | Ver INT-011 |
| CF-07 | Plazos de deuda | LP 8 años; CP 1 año | Regla RG-05 |
| CF-08 | Semilla de simulación | Sin valor por defecto | Se fija en Fase 3 |
| CF-09 | Número de escenarios | Sin valor por defecto | Se fija en Fase 3 |
| CF-10 | Umbrales de precisión presupuestaria | Pendientes de aprobación | Política interna, no regla oficial |
| CF-11 | Pesos de evaluación | Pendientes de validación | No son regla oficial |
| CF-12 | Caja mínima operativa | Pendiente de cálculo | Se define en Fase 2 |

La configuración debe permitir cambiar estos valores sin reescribir el modelo.

---

## 8. Hipótesis de trabajo

Las siguientes afirmaciones son **HY**. No son reglas oficiales y deben validarse o sustituirse cuando exista evidencia.

| Código | Hipótesis | Validación prevista |
|---|---|---|
| HY-01 | El último cierre real disponible en el repositorio es 2026 | Fase 1, al clasificar fuentes |
| HY-02 | Las decisiones de 2027 no son un cierre real | Fase 1, hasta recibir resultados 2027 |
| HY-03 | Los impuestos históricos son cero, pero no existe una regla general de impuestos nulos | Fase 2, con históricos y documentación |
| HY-04 | La demanda y la conversión no tienen función oficial verificada | Fase 3, con escenarios y calibración |
| HY-05 | La convención de cobros, pagos y devengo debe calibrarse con históricos | Fase 2 |
| HY-06 | La caja mínima operativa se derivará de obligaciones y riesgo, no de un porcentaje fijo | Fase 2 |
| HY-07 | La ocupación se modela en dos niveles: penalización sobre planta y costes por línea (INT-006) | Fase 1–2 |
| HY-08 | La puntuación de Valor de Compañía se tratará como configuración, no como fórmula oficial | Fase 4 |
| HY-09 | La producción `0` de 2027 significa mantener la producción de 2026 | Fase 1, aplicando RG-02 |
| HY-10 | Los activos financieros CP no son equivalentes a caja libre inmediata | Fase 2 |
| HY-11 | Las ventas y resultados de 2027 deberán obtenerse de una nueva matriz o cierre | Fase 1 |
| HY-12 | El balance requiere una base canónica reconciliada antes de proyectar | Fase 2 |

---

## 9. Contradicciones y cuestiones pendientes

| Código | Hecho comprobado | Impacto | Resolución prevista |
|---|---|---|---|
| PD-05 | Ingresos 2026: 38.610,39 en la fila de total y 3.861.039 en el resto de tablas | Posible escala ×100; no se aplica corrección automática | Inferencia INT-003 pendiente de confirmación |
| PD-06 | Gastos generales 2026: total 344.808 y detalle 194.808; 150.000 atribuidos por el usuario a central/taller | El resultado depende de un importe sin detalle documental | Hipótesis INT-009; evidencia pendiente |
| PD-07 | CAPEX 2026: incremento 1.533.000 (fábrica 1.308.000 + almacén 225.000) frente a 400.000 de proyectos seleccionados; restan 1.133.000 | El desglose está cuantificado, pero la causa de 1.133.000 no está documentada | Hecho INT-010; causa pendiente |
| PD-09 | Pasivo corriente trimestral: 2026 total 297.748 frente a componentes 221.457 (76.291); 2027 trimestral 313.036 frente a componentes ~214.932-215.167 (97.869-98.104), sin fila trimestral de impuestos | La identidad de pasivo corriente ya se audita y detecta las diferencias | Conciliación pendiente |
| PD-10 | Proveedores “Economica”/“Estandar” frente a “Económica”/“Estándar” | Normalización de alias | Fase 1 |
| PD-11 | No hay fórmula oficial ni pesos verificables del Valor de Compañía | La puntuación no puede presentarse como oficial | Antes de Fase 4 |
| PD-15 | Las capturas Markdown manuales solo se normalizan cuando periodo y tipo de dato son explícitos | Limita la incorporación automática de capturas ambiguas | Al incorporar la primera captura real |
| PD-16 | Producción de bufandas 2027: 30.000 unidades con decisión 0, frente a 29.000 en 2026 y 32.000 en la documentación de Matriz 2 | La regla general 0 = mantener no explica el paso 29.000 -> 30.000 | Aceptada como excepción documentada; no se modifica RG-02 |

Ninguna de estas cuestiones impide cerrar la Fase 0. Las que afectan a resultados financieros se resolverán antes de la puerta correspondiente; las resueltas por política o evidencia se registran en `.specify/memory/interpretations.json`. En particular, el ajuste D-02 se registra en INT-008/INT-012 como explicación del usuario sin documento independiente, y los residuales de 1 € se conservan sin redondear.

---

## 10. Comportamiento interanual

### 10.1. Principio

El sistema debe funcionar con las matrices, ejercicios y decisiones disponibles, sin depender de un año concreto ni de una numeración fija de archivos.

Regla general:

> Último ejercicio real validado → siguiente periodo como objetivo de planificación.

### 10.2. Clasificación de fuentes

Toda fuente debe clasificarse como:

- **Real:** cierre validado.
- **Decisión:** bitácora de decisiones.
- **Presupuesto:** previsión aprobada.
- **Proyección:** salida del modelo.
- **Escenario:** simulación.
- **Capturada:** Markdown manual pendiente de clasificación; no se presenta como cierre real.

Una decisión, un presupuesto, una proyección o una captura no son un cierre real.

### 10.3. Comportamiento esperado

1. Identificar el periodo por el contenido, no por el nombre del archivo.
2. Verificar la secuencia temporal y la transición declarada.
3. Validar que el cierre es suficiente y coherente.
4. Determinar el último ejercicio real validado.
5. Establecer el siguiente ejercicio objetivo.
6. Conservar el historial fuente → decisión → resultado.
7. Incorporar nuevas matrices sin depender de numeración fija.
8. Registrar contradicciones y solicitar confirmación cuando no haya evidencia suficiente.

### 10.4. Estado actual

- `Matriz_general_2` es el cierre real y ejecutado de 2027, confirmado por el usuario.
- El último cierre real validado es **2027**.
- 2027: decisiones y resultados coexisten; la clasificación se hace por tabla y periodo.
- Objetivo solicitado para la primera planificación: **2028**.
- Caso abierto: producción de bufandas 2027 (PD-16 / Q-009).

La regla interanual permite usar 2027 como base y establecer 2028 como objetivo. La contradicción específica de producción de bufandas no invalida el cierre completo, pero debe resolverse antes de modelar la semántica de producción de forma general.

### 10.5. Historial

El sistema debe conservar, de forma conceptual:

- fuente y periodo;
- naturaleza del dato;
- decisiones asociadas;
- resultado real, si existe;
- desviación entre previsión y real;
- supuestos y versión del modelo.

---

## 11. Requisitos funcionales generales

| Código | Requisito |
|---|---|
| FR-01 | Inventariar y clasificar las fuentes disponibles |
| FR-02 | Cargar Excel y JSON en modo solo lectura |
| FR-03 | Identificar periodos y naturaleza de los datos por contenido |
| FR-04 | Normalizar a una capa canónica trazable |
| FR-05 | Validar y reconciliar totales, componentes e identidades |
| FR-06 | Registrar anomalías, contradicciones y datos ausentes |
| FR-07 | Determinar el último ejercicio real validado y el siguiente objetivo |
| FR-08 | Conservar el historial de fuentes, decisiones y resultados |
| FR-09 | Reconstruir y proyectar resultados, balance, deuda y tesorería |
| FR-10 | Evaluar escenarios e incertidumbre |
| FR-11 | Comparar decisiones con restricciones y línea base |
| FR-12 | Explicar resultados, riesgos y desviaciones |
| FR-13 | Separar configuración, reglas, hipótesis y datos |
| FR-14 | Generar un Markdown literal por hoja con el texto de cada celda no vacía, sin fórmulas ni valores calculados |
| FR-15 | Incorporar Markdown capturado manualmente con procedencia, hash y metadatos opcionales |
| FR-16 | Ofrecer un notebook de auditoría que consulte fuentes, tablas, fidelidad, anomalías e interpretaciones |
| FR-17 | Registrar interpretaciones confirmadas y preguntas abiertas para no repetir trabajo |
| FR-18 | Verificar que los originales de `data/` no cambian y que el Markdown literal conserva todas las celdas y su texto |

No se especifican aquí algoritmos, estructuras de clases ni contratos técnicos.

---

## 12. Requisitos no funcionales

- Python 3.12+ con `uv`.
- `pandas`, `numpy` y `openpyxl` como bibliotecas principales.
- `pytest` para pruebas.
- Sin base de datos, servicios externos, API ni interfaz web.
- Ejecución reproducible y determinista cuando se fije una semilla.
- Módulos pequeños y legibles.
- `data/` inmutable.
- Resultados en `outputs/`.
- Errores y anomalías explícitos, no silenciosos.
- Toda salida relevante debe incluir versión de configuración y supuestos.

---

## 13. Criterios de aceptación

### 13.1. Fase 0

A nivel de especificación, la Fase 0 es aceptable cuando:

- el problema, el alcance y los criterios de evaluación son comprensibles;
- las reglas, parámetros, hipótesis y pendientes están separados;
- la regla interanual es reutilizable y no depende de un año ni de una numeración;
- las fases futuras quedan definidas solo a nivel general.

### 13.2. Fase 1

La Fase 1 se acepta cuando se cumplen **F1.2 literal** y los criterios de F1.1:

- las fuentes están inventariadas, hasheadas y clasificadas;
- los periodos se identifican por contenido en la capa canónica;
- la capa normalizada es trazable y no duplica la lógica;
- existe un `.md` por hoja para cada Excel, incluidas las hojas ocultas;
- cada `.md` contiene el texto literal de cada celda no vacía, escapando pipes y saltos de línea;
- no se evalúan fórmulas ni se reconstruyen valores calculados;
- `cell_index.csv` contiene `raw_text`, fuente, hoja, celda, fila, columna, `data_type`, `is_merged` y `merged_range`;
- `manifest.json` contiene hash, hojas, dimensiones, rangos combinados y advertencias;
- la fidelidad se comprueba por hoja: misma cantidad de celdas no vacías, mismo texto, cero duplicados y cero celdas perdidas;
- las capturas manuales se distinguen de los originales y del Markdown generado;
- el notebook se ejecuta con las fuentes disponibles;
- las interpretaciones confirmadas y las preguntas abiertas están registradas;
- `data/` conserva sus hashes originales;
- las pruebas pertinentes pasan.

### 13.3. F1.2 — Extractor textual literal

F1.2 no interpreta tablas, encabezados ni periodos. Su única responsabilidad es conservar el contenido textual literal de las celdas.

Criterios exactos:

1. Un `.md` por hoja, con nombre estable que incluya fuente y hoja.
2. Se recorren todas las hojas, incluidas las ocultas.
3. Se lee cada celda no vacía como texto literal; no se usa `data_only=True` para obtener resultados calculados.
4. El Markdown escapa `|` y saltos de línea para seguir siendo legible.
5. `cell_index.csv` usa `raw_text`, no `value`.
6. `data_type` describe el tipo de celda de Excel (`string`, `number`, `boolean`, `date`), no el tipo de dato del juego.
7. `is_merged` y `merged_range` conservan la evidencia de celdas combinadas.
8. `manifest.json` registra hash, hojas, dimensiones, rangos combinados y advertencias.
9. La prueba de fidelidad compara contra una lectura independiente de cada Excel: celdas no vacías por hoja, texto, duplicados y pérdidas.
10. `data/` permanece intacto.

Aclaración de conteos: el inventario puede incluir celdas de fuentes JSON (por ejemplo, 178 celdas de decisión) que no forman parte de `cell_index.csv`, porque F1.2 indexa hojas Excel. La prueba de “cero celdas perdidas” se refiere al universo Excel, no a las celdas JSON.

La comprobación operativa y la puerta de aprobación se detallan en `tasks.md`.

---

## 14. Preguntas que la Fase 0 debe dejar respondidas

- ¿Qué problema empresarial se resuelve?
- ¿Qué principios no se pueden violar?
- ¿Cómo se planifica el ejercicio siguiente con la información disponible?
- ¿Cómo se conserva la trazabilidad entre fuentes, decisiones y resultados?
- ¿Qué fases deben completarse y en qué orden?
- ¿Qué documentos gobiernan el trabajo?
- ¿Qué falta confirmar y cuándo se resolverá?
- ¿Cuál es la primera funcionalidad que debe especificarse después de la Fase 0?
- ¿Cómo se distingue una fuente original, una captura manual y un Markdown generado?
- ¿Dónde se registra una interpretación confirmada y una pregunta pendiente?

La primera funcionalidad posterior fue **F1: fuentes, inventario, carga, identificación de periodos, validación y conciliación**. F1 se divide en F1.1 (capa canónica y validación) y F1.2 (Markdown, capturas, notebook y memoria operativa).
