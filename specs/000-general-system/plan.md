# Plan General — cg_01 / CompanyGame Spain10

Versión: 0.2.0
Estado: Fase 0 cerrada; Fase 1 cerrada y aprobada; F2.1 aprobada; F2.2 pendiente de aprobación de alcance
Depende de: `.specify/memory/constitution.md` y `spec.md`

---

## 1. Estrategia

El proyecto se desarrolla por fases. Cada fase tiene un objetivo acotado, un entregable verificable y una puerta de cierre. Las funcionalidades futuras se especifican al iniciar la fase correspondiente; este plan no las desarrolla por anticipado.

Principio de secuencia:

```text
Fundamentos → Datos → Modelo financiero → Incertidumbre → Optimización
```

No se avanza si la puerta anterior no está satisfecha.

---

## 2. Arquitectura conceptual

La arquitectura se organiza en cinco bloques funcionales y dos elementos transversales. Es una propuesta inicial, no un diseño de clases ni de interfaces.

### 2.1. Fuentes y datos

Responsabilidades:

- inventario de matrices, JSON y documentación;
- carga en solo lectura;
- clasificación por naturaleza y periodo;
- normalización y trazabilidad;
- validación, conciliación y registro de anomalías.

Entradas: `data/`, documentación de módulos y futuras matrices.
Salidas: datos canónicos, informe de fuentes y registro de contradicciones.

### 2.1.1. Extractor textual literal y capturas manuales

Responsabilidades de F1.2:

- generar un `.md` por hoja para cada Excel, incluidas las hojas ocultas;
- conservar el texto literal de cada celda no vacía, sin fórmulas ni valores calculados;
- escapar pipes y saltos de línea para que el Markdown sea legible;
- generar `cell_index.csv` con `raw_text`, fuente, hoja, celda, fila, columna, `data_type`, `is_merged` y `merged_range`;
- generar `manifest.json` con hash, hojas, dimensiones, rangos combinados y advertencias;
- distinguir Markdown generado de Markdown capturado manualmente;
- incorporar capturas con frontmatter, hash y procedencia;
- normalizar una captura solo cuando periodo y tipo de dato estén suficientemente respaldados.

F1.2 **no interpreta** tablas, encabezados, periodos ni tipos de dato del juego. Esa clasificación pertenece a la capa canónica.

Salida generada: `outputs/markdown/` con un `.md` por hoja, `manifest.json` y `cell_index.csv`.
Las capturas manuales son fuentes y no se reescriben.

### 2.1.2. Notebook y memoria operativa

Responsabilidades:

- ofrecer una interfaz de auditoría en VS Code;
- consultar fuentes, hojas, fidelidad literal, anomalías y comparaciones de periodos;
- mostrar interpretaciones confirmadas y preguntas abiertas;
- evitar duplicar en celdas la lógica que ya vive en los módulos.

La memoria operativa vive en `.specify/memory/interpretations.json` y `.specify/memory/open_questions.json`.

### 2.2. Modelo financiero

Responsabilidades:

- reconstrucción del último cierre validado;
- proyección de resultados, balance, deuda y tesorería;
- cálculo de caja mínima operativa;
- identificación del excedente potencialmente invertible;
- validación frente a históricos y reglas del juego.

No incluye todavía el simulador ni el optimizador.

### 2.3. Incertidumbre

Responsabilidades:

- definición de escenarios y variables inciertas;
- simulación de resultados y riesgos;
- análisis de sensibilidad;
- validación de supuestos.

Depende de un modelo financiero determinista suficientemente validado.

### 2.4. Evaluación y optimización

Responsabilidades:

- comparación de decisiones candidatas;
- respeto de restricciones duras;
- evaluación de riesgo;
- comparación con una línea base;
- explicación de alternativas.

No se diseña la fórmula definitiva en Fase 0. Los pesos son configuración e hipótesis.

### 2.5. Validación y reporting

Responsabilidades:

- conciliaciones;
- métricas de precisión;
- explicación de desviaciones;
- informes de escenarios;
- seguimiento de recomendaciones;
- registro de versión, semilla y supuestos.

### 2.6. Elementos transversales

| Elemento | Responsabilidad |
|---|---|
| Reglas y configuración | Mantener separadas reglas, parámetros e hipótesis; versionar la configuración |
| Orquestación / CLI | Ejecutar el flujo, validar entradas y generar salidas reproducibles |
| Markdown y auditoría | Generar representación legible, verificar fidelidad y facilitar la revisión humana |

### 2.7. Dependencias

```text
Fuentes y datos
      ├──────────────► Markdown generado + índice de celdas
      ↓
Modelo financiero
      ↓
Incertidumbre
      ↓
Evaluación y optimización
      ↓
Reporting
      ↑
Notebook de auditoría + memoria operativa (transversales)

Reglas/configuración y orquestación: transversales
```

La validación y el reporting acompañan a todas las fases, pero no sustituyen las puertas de cada una.

### 2.8. Decisión de simplicidad

- Sin base de datos.
- Sin API.
- Sin interfaz web.
- Sin servicios externos.
- Sin dependencias adicionales sin justificación.
- Sin estructuras de datos detalladas hasta que la fase correspondiente las requiera.
- `ipykernel` y `nbclient` son dependencias de desarrollo para ejecutar y verificar el notebook; no forman parte del runtime del modelo.

---

## 3. Fases

### Fase 0 — Planificación general y fundamentos

**Objetivo:** definir el problema, los principios, el alcance, la regla interanual, la arquitectura conceptual y la hoja de ruta.

**Entregable:** los cuatro artefactos SDD aprobados.

**Dependencias:** ninguna.

**Inicio:** inmediato.

**Cierre:** revisión y aprobación explícita. No se escribe código.

---

### Fase 1 — Datos, trazabilidad y comprensión

**Objetivo:** saber qué datos existen, qué representan, qué periodos cubren y qué contradicciones contienen; disponer de una representación legible y de una interfaz de auditoría.

**Entregables principales:**

- F1.1: inventario estructurado, capa canónica, validación y registro de anomalías;
- F1.2: extractor textual literal por hoja, captura manual, notebook de auditoría y memoria operativa.

**Dependencias:** Fase 0 cerrada.

**Inicio:** aprobación de Fase 0.

**Cierre:**

- fuentes inventariadas, hasheadas y clasificadas;
- periodos identificados por contenido;
- último cierre real y siguiente objetivo determinados cuando sea posible;
- datos canónicos trazables;
- anomalías documentadas;
- un `.md` literal por hoja para las matrices Excel disponibles;
- `cell_index.csv` con `raw_text` y cero celdas perdidas o duplicadas en el universo Excel;
- capturas manuales separadas y trazables;
- notebook ejecutable con las fuentes disponibles;
- interpretaciones confirmadas y preguntas abiertas registradas;
- `data/` intacto;
- pruebas de carga, validación, Markdown y notebook verdes;
- defectos de extracción corregidos y probados; incidencias abiertas documentadas, no silenciadas.

**Subfases:**

| Subfase | Estado | Contenido |
|---|---|---|
| F1.1 | Implementada | Inventario, carga, periodos, capa canónica y validación |
| F1.2 | Implementada y verificada | Extractor textual literal por hoja, capturas, notebook y memoria operativa |

**Nota:** `Matriz_general_2` es el cierre real y ejecutado de 2027, confirmado por el usuario (Q-008). Los tres defectos de extracción (año+2, deuda trimestral y pasivo corriente trimestral) fueron corregidos y cubiertos por pruebas. La producción de bufandas 2027 se acepta como excepción documentada (Q-009); no se modifica RG-02.

---

### Fase 2 — Modelo financiero determinista

**Objetivo:** reconstruir la situación financiera del último cierre validado y proyectar resultados, balance, deuda y tesorería.

**Entregable principal:** modelo financiero validado, caja mínima operativa y excedente potencialmente invertible.

**Dependencias:** Fase 1 cerrada.

**Inicio:** datos canónicos y anomalías documentadas.

**F2.1 — Primera entrega acotada (aprobada):**

- estado de resultados e ingresos/costes por producto 2026–2027;
- balance histórico y estructura de deuda, incluida la porción corriente del LP;
- flujo de caja y liquidez;
- conciliación histórica contra 2026 real y 2027 real (Matriz 2 como fuente principal 2027);
- informe de conciliaciones y discrepancias;
- tolerancias 0,005 € / 1 €;
- estados `confirmed`, `inferred_accepted`, `pending`, `accepted_exception`, `unreconciled`;
- las 16 críticas de balance y las 81 anomalías de balance se marcan `unreconciled`, sin corrección;
- cualquier derivado que use una cifra no conciliada hereda la marca.

**Fuera de F2.1:** producción/inventarios como módulo propio, Monte Carlo y optimización.

F2.1 no cierra toda la Fase 2: entrega el corte vertical histórico. No se inicia F2.2 ni Monte Carlo sin nueva aprobación.

**Cierre:**

- reconstrucción histórica validada;
- identidades contables y de caja comprobadas;
- deuda e intereses sin duplicidades;
- caja mínima justificada;
- excedente calculado sin restar dos veces las mismas obligaciones;
- reglas del juego respetadas;
- pruebas de regresión verdes.

Si la validación histórica no alcanza el nivel acordado, no se avanza a Fase 3.

---

### Fase 3 — Simulación y análisis de incertidumbre

**Objetivo:** medir cómo cambian los resultados y el riesgo ante distintas hipótesis de mercado y operación.

**Entregable principal:** simulación reproducible, escenarios, percentiles y análisis de sensibilidad.

**Dependencias:** Fase 2 cerrada.

**Inicio:** modelo financiero validado.

**Cierre:**

- variables inciertas y rangos documentados;
- simulación reproducible con semilla;
- restricciones evaluadas por escenario;
- resultados auditables;
- supuestos revisados y versionados.

---

### Fase 4 — Optimización y apoyo a decisiones

**Objetivo:** comparar alternativas y recomendar decisiones que mejoren el Valor de la Compañía sin comprometer liquidez ni solvencia.

**Entregable principal:** recomendación explicada, comparación con línea base y análisis de riesgo.

**Dependencias:** Fase 3 cerrada.

**Inicio:** simulación validada.

**Cierre:**

- restricciones duras cumplidas;
- comparación con línea base;
- riesgo de iliquidez controlado;
- resultados explicados;
- decisión presentada para aprobación humana.

---

## 4. Gestión de funcionalidades futuras

Cada funcionalidad que se aborde después de Fase 0 tendrá su propia especificación, alcance, dependencias, criterios de aceptación y plan de validación.

Reglas:

1. No se implementa una funcionalidad sin especificación previa.
2. No se especifica en detalle una funcionalidad que pertenece a una fase posterior.
3. Una funcionalidad no puede contradecir la Constitución ni la Spec.
4. Las tareas de una funcionalidad se crean al iniciar su fase.
5. Los resultados de una funcionalidad deben ser verificables y reproducibles.

Ejemplos de funcionalidades futuras:

- carga y clasificación de matrices;
- identificación de periodos;
- conciliación de balance;
- proyección de tesorería trimestral;
- modelo de deuda e intereses;
- simulación Monte Carlo;
- optimización con restricciones.

Ninguna se desarrolla en Fase 0.

---

## 5. Riesgos del plan

| Riesgo | Mitigación |
|---|---|
| Datos incompletos o contradictorios | Registro de anomalías y capa canónica |
| Falta de cierre reciente | Limitar resultados validados; no bloquear el diseño general |
| Fórmulas no verificadas | Marcarlas como hipótesis y calibrarlas |
| Sobreajuste al histórico | Validación y análisis de sensibilidad |
| Iliquidez | Restricción de caja y evaluación de riesgo |
| Deuda duplicada | Separar LP, porción corriente y CP |
| Optimización prematura | Puerta de Fase 2 |
| Sobreingeniería | Arquitectura simple y revisión por fase |

---

## 6. Entregables de la Fase 0

- `.specify/memory/constitution.md`
- `specs/000-general-system/spec.md`
- `specs/000-general-system/plan.md`
- `specs/000-general-system/tasks.md`

No se incluye código, datos procesados ni resultados financieros.

---

## 7. Criterio de cierre de la Fase 0

La Fase 0 termina cuando:

- los cuatro documentos son coherentes entre sí;
- las reglas, parámetros, hipótesis y pendientes están separados;
- la regla interanual no depende de años ni numeración fija;
- las fases futuras están descritas solo a nivel general;
- `tasks.md` se limita a la Fase 0;
- `data/` permanece intacto;
- el responsable aprueba el resultado.

Después del cierre, la primera funcionalidad a especificar será **F1: fuentes, inventario, carga, identificación de periodos, validación y conciliación**.


## 8. Entregables de la Fase 1

- Inventario y capa canónica en `outputs/f1/`.
- Markdown literal por hoja, `manifest.json` y `cell_index.csv` en `outputs/markdown/`.
- Notebook `notebooks/01_revision_matrices.ipynb`.
- Memoria operativa en `.specify/memory/interpretations.json` y `.specify/memory/open_questions.json`.
- Pruebas de carga, validación, fidelidad Markdown y ejecución del notebook.
- Documentación sincronizada: Constitución, Spec, Plan, Tareas, README y `AGENTS.md`.

No se incluye el modelo financiero, Monte Carlo ni optimización.
