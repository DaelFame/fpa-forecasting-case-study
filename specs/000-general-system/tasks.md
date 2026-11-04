# Tareas — Fase 0, Fase 1 y F2.1

Versión: 0.2.0
Estado: Fase 0 cerrada; Fase 1 cerrada y aprobada; F2.1 aprobada; F2.2 pendiente de aprobación de alcance
Alcance: Fase 0, Fase 1 y F2.1

---

## 1. Reglas de esta lista

- Contiene tareas de Fase 0, Fase 1 y F2.1.
- No contiene Monte Carlo ni optimización.
- Fase 0 no implementa código; Fase 1 sí lo hace.
- No se modifica `data/`.
- Cada tarea debe poder verificarse con evidencia.
- La fase no se cierra hasta que el responsable la apruebe.

Las fases 2–4 se planifican en `plan.md` y se detallarán cuando se inicien.

---

## 2. Tareas

### T0.1. Inventariar fuentes y diagnóstico

- [x] Revisar estructura del repositorio, matrices, bitácoras y documentación.
- [x] Identificar periodos disponibles y naturaleza de cada fuente.
- [x] Detectar carencias y contradicciones relevantes.
- [x] Separar hechos, interpretaciones, propuestas y pendientes.

**Evidencia:** diagnóstico de Fase 0 y secciones 6–10 de `spec.md`.

**Dependencias:** ninguna.

---

### T0.2. Redactar la Constitución

- [x] Crear `.specify/memory/constitution.md`.
- [x] Definir principios permanentes.
- [x] Establecer jerarquía documental.
- [x] Definir la taxonomía de reglas, parámetros, hipótesis y pendientes.
- [x] Establecer gobierno de cambios y criterios de conflicto.

**Evidencia:** `.specify/memory/constitution.md`.

**Dependencias:** T0.1.

**Aceptación:** los principios no dependen de un año ni de una edición concreta del juego.

---

### T0.3. Redactar la Especificación

- [x] Crear `specs/000-general-system/spec.md`.
- [x] Definir problema empresarial, actores, alcance y decisiones.
- [x] Definir información necesaria, riesgos y criterios de evaluación.
- [x] Separar reglas del juego, parámetros, hipótesis y pendientes.
- [x] Definir la regla interanual sin depender de numeración fija.
- [x] Definir requisitos funcionales y no funcionales generales.

**Evidencia:** `specs/000-general-system/spec.md`.

**Dependencias:** T0.1 y T0.2.

**Aceptación:** no se presenta ninguna hipótesis como regla oficial.

---

### T0.4. Redactar el Plan

- [x] Crear `specs/000-general-system/plan.md`.
- [x] Definir arquitectura conceptual simple.
- [x] Definir fases, dependencias, entregables y puertas.
- [x] Mantener las fases futuras a nivel general.
- [x] Definir el gobierno de funcionalidades futuras.

**Evidencia:** `specs/000-general-system/plan.md`.

**Dependencias:** T0.2 y T0.3.

**Aceptación:** no se anticipan fórmulas, algoritmos ni contratos técnicos de fases posteriores.

---

### T0.5. Redactar las tareas de Fase 0

- [x] Crear `specs/000-general-system/tasks.md`.
- [x] Limitar el contenido a la Fase 0.
- [x] Añadir dependencias y criterios de aceptación.
- [x] No incluir tareas de fases posteriores.

**Evidencia:** este archivo.

**Dependencias:** T0.2, T0.3 y T0.4.

**Aceptación:** no hay tareas de implementación ni de Fase 1.

---

### T0.6. Verificar coherencia documental

- [x] Revisar que los cuatro documentos usan la misma jerarquía y taxonomía.
- [x] Revisar que las reglas, parámetros, hipótesis y pendientes no se contradicen.
- [x] Revisar que la regla interanual es la misma en `spec.md` y `plan.md`.
- [x] Revisar que `tasks.md` no introduce requisitos nuevos.
- [x] Revisar que las fases futuras no están detalladas en exceso.

**Evidencia:** lista de comprobación de esta tarea y revisión final.

**Dependencias:** T0.1–T0.5.

---

### T0.7. Verificar integridad del repositorio

- [x] Confirmar que no se ha modificado ningún archivo de `data/`.
- [x] Confirmar que no se ha creado código de implementación.
- [x] Confirmar que solo se han creado los cuatro artefactos SDD y sus directorios.
- [x] Revisar el estado de Git.

**Evidencia:** `git status --short`, inventario de archivos y comprobación de rutas.

**Dependencias:** T0.6.

---

### T0.8. Puerta de Fase 0

- [x] El responsable revisa los cuatro artefactos.
- [x] El responsable aprueba la Fase 0.
- [x] Se autoriza el inicio de la Fase 1.

**Dependencias:** T0.6 y T0.7.

**Aceptación:** aprobación explícita. Sin ella, no se inicia la Fase 1.

---

## 3. Fase 1 — Datos, Markdown y auditoría

### F1.1. Capa canónica y validación

#### F1.1.1. Inventario, carga y hashes

- [x] Descubrir Excel y JSON de `data/` sin modificarlos.
- [x] Calcular SHA-256 antes y después de la ejecución.
- [x] Cargar Excel y JSON en modo lectura.
- [x] Identificar periodos por contenido y clasificar tipos de dato.

**Evidencia:** `src/cg_01/loader.py`, `outputs/f1/inventory.json`, pruebas de la capa canónica.

#### F1.1.2. Capa normalizada

- [x] Extraer observaciones con fuente, hoja, celda, fila, columna y etiqueta.
- [x] Mantener una única implementación de detección de periodos.
- [x] Conservar observaciones coincidentes sin deduplicación destructiva.

**Evidencia:** `src/cg_01/canonical.py`, `outputs/f1/canonical_points.csv`.

#### F1.1.3. Validación y anomalías

- [x] Validar precios, producción, ocupación, balance, escala y cruces con bitácoras.
- [x] Registrar anomalías con severidad, procedencia y estado abierto.
- [x] Alinear los códigos `PD-*` de `reporting.py` con la Spec.

**Evidencia:** `src/cg_01/validation.py`, `outputs/f1/anomalies.csv`, `outputs/f1/report.md`.

#### F1.1.4. Pruebas de la capa canónica

- [x] Cubrir detección de periodos, identidades de balance, escala, alias y precios.
- [x] Verificar reproducibilidad y conservación de fuentes reales.

**Evidencia:** `tests/test_f1_1.py`, `tests/test_f1_1_audit.py`.

### F1.2. Extractor textual literal, capturas, notebook y memoria

> F1.2 queda redefinida: no se acepta como “Markdown interpretado”. El criterio es extracción textual literal.

#### F1.2.1. Extractor textual literal

- [x] Recorrer todas las hojas de los tres Excel, incluidas las ocultas.
- [x] Leer cada celda no vacía como texto literal, sin fórmulas ni valores calculados.
- [x] Generar un `.md` por hoja, escapando pipes y saltos de línea.
- [x] Marcar el Markdown como generado y no editable.

**Evidencia:** `src/cg_01/excel_to_md.py`, `outputs/markdown/`, `tests/test_markdown_export.py`.

#### F1.2.2. Índice de celdas y manifiesto

- [x] Generar `cell_index.csv` con `raw_text` (no `value`), fuente, hoja, celda, fila, columna, `data_type`, `is_merged` y `merged_range`.
- [x] Generar `manifest.json` con hash, hojas, dimensiones, rangos combinados y advertencias.
- [x] Verificar cero celdas perdidas y cero duplicadas en el universo Excel.
- [x] Comparar el texto contra una lectura independiente de cada Excel.

**Evidencia:** `outputs/markdown/manifest.json`, `outputs/markdown/cell_index.csv`, `tests/test_markdown_export.py`.

#### F1.2.3. Capturas manuales

- [x] Definir frontmatter opcional y no imponer un año o tipo único.
- [x] Descubrir y hashear capturas de `data/manual/`.
- [x] Normalizar solo observaciones con periodo explícito y clasificación respaldada.
- [x] Marcar como advertencia las tablas sin periodo explícito.

**Evidencia:** `src/cg_01/loader.py`, `src/cg_01/canonical.py`, prueba de captura Markdown.

#### F1.2.4. Notebook de auditoría

- [x] Crear `notebooks/01_revision_matrices.ipynb`.
- [x] Adaptar el notebook al `cell_index` literal y al nuevo `manifest.json`.
- [x] Mostrar interpretaciones confirmadas y preguntas abiertas.
- [x] Ejecutar el notebook con las fuentes disponibles.

**Evidencia:** notebook y `tests/test_notebook.py`.

#### F1.2.5. Memoria operativa

- [x] Crear `.specify/memory/interpretations.json`.
- [x] Crear `.specify/memory/open_questions.json`.
- [x] Registrar las preguntas materiales investigadas y las interpretaciones respaldadas.
- [x] Tratar la regla de producción `0 = mantener` como RG-02, no como pregunta.

**Evidencia:** archivos de memoria y sección de preguntas del notebook.

#### F1.2.6. Simplificación y limpieza

- [x] Fusionar `sources.py` en `loader.py` y actualizar imports y pruebas.
- [x] Eliminar código y configuración sin uso (`dump_json`, `ratio_tolerance_pct`).
- [x] Sustituir el stub `main.py` por el punto de entrada real.
- [x] Mantener una sola ruta canónica y una sola ruta Markdown literal.

**Evidencia:** estructura de `src/cg_01/`, `src/cg_01/excel_to_md.py` y pruebas verdes.

#### F1.2.7. Sincronización documental

- [x] Actualizar Constitución, Spec, Plan y Tareas.
- [x] Actualizar README y crear `AGENTS.md`.
- [x] Ajustar VS Code y `.gitignore` sin añadir archivos indiscriminadamente.

**Evidencia:** documentos actualizados y revisión final.

### F1.3. Pendientes técnicos y de negocio

#### F1.3.1. Extracción de año+2

- [x] Mapear encabezados `Año+2` a su periodo relativo.
- [x] Verificar 2028 en Matriz 0 y 2029 en Matriz 1.
- [x] Eliminar el `xfail` y cubrir el caso con prueba.

**Evidencia:** `tests/test_f1_1_audit.py::test_macro_anio_mas_dos_is_canonicalized`.

#### F1.3.2. Deuda trimestral

- [x] Corregir la detección de títulos que bloqueaba la tabla trimestral.
- [x] Extraer B137:E137 y B182:E182 con su periodo.
- [x] Eliminar el `xfail` y verificar valores.

**Evidencia:** `tests/test_f1_1_audit.py::test_quarterly_total_debt_is_extracted`.

#### F1.3.3. Pasivo corriente trimestral

- [x] Añadir la identidad `BAL-CURRENT-LIABILITIES`.
- [x] Detectar la diferencia de 76.291 en el pasivo corriente trimestral 2026.
- [x] Eliminar el `xfail` y cubrir la regla con prueba sintética.

**Evidencia:** `tests/test_f1_1_audit.py::test_quarterly_current_liabilities_are_flagged`, `tests/test_f1_1.py::test_current_liabilities_identity_flags_missing_components`.

#### F1.3.4. Preguntas materiales abiertas

- [x] Q-001: adoptar el bloque detallado y registrar D-02 como ajuste interno de presentación sin documento independiente.
- [x] Q-002: registrar los 150.000 como hipótesis de central/taller, sin evidencia documental.
- [x] Q-003: documentar la composición del CAPEX (fábrica +1.308.000; almacén +225.000; proyectos 400.000; resto 1.133.000 sin causa documentada).
- [x] Q-004: adoptar precedencia provisional por ejercicio, métrica y periodo (INT-004).
- [x] Q-005: separar penalización sobre planta y costes industriales por línea (INT-006).
- [x] Q-006: registrar 7,6 % nominal del periodo y 13,2 % de penalización con sus contextos (INT-011).
- [x] Q-007: confirmar la igualdad solo en la tabla de 2025 y usar la matriz nueva para ejercicios posteriores (INT-007).
- [x] Q-008: confirmar Matriz_general_2 como cierre real y ejecutado de 2027; clasificar por tabla y periodo.
- [x] Q-009: aceptada como excepción documentada; se conserva 30.000 real y no se cambia RG-02.

**Evidencia:** `.specify/memory/open_questions.json`, `.specify/memory/interpretations.json`.

#### F1.3.5. Integridad de originales

- [x] Verificar que `data/` conserva sus hashes antes y después de la ejecución.
- [x] No añadir los originales a Git ni crear copias editables.

**Evidencia:** hashes de `data/` y manifiesto Markdown.

#### F1.3.6. Incorporación de `Matriz_general_2`

- [x] Descubrir, hashear y cargar la matriz nueva sin modificar `data/`.
- [x] Extraer 2027 y sus comparativos; el pipeline detecta 2027 como año real.
- [x] Generar el Markdown literal y verificar fidelidad de las tres matrices.
- [x] Confirmar 2027 como cierre real y ejecutado (Q-008).
- [x] Documentar la producción de bufandas 2027 como excepción aceptada (Q-009).

**Evidencia:** `data/Matriz_general_2.xlsx`, `outputs/markdown/`, `tests/test_source_evidence.py`, Q-008.

### F1.4. Puerta de Fase 1

- [x] Q-009 aceptada como excepción documentada.
- [x] INT-003 aceptada como inferencia con valor bruto y normalizado separados.
- [x] Q-001 y Q-008 están resueltas.
- [x] Los tres defectos de extracción están corregidos y probados.
- [x] El responsable aprueba la Fase 1.
- [x] Fase 1 cerrada formalmente.

### F2. Primera entrega acotada — motor determinista

- [x] Crear `config/f2.toml` con tolerancias 0,005 € / 1 €.
- [x] Implementar `f2_engine.py` con estados y procedencia.
- [x] Implementar `f2_report.py` con los 7 archivos de `outputs/f2/`.
- [x] Conciliar estado de resultados 2026–2027.
- [x] Conciliar balance detallado 2026–2027.
- [x] Conciliar deuda anual, incluida la porción corriente del LP.
- [x] Conciliar caja inicial/variación/final con residual explícito.
- [x] Marcar las 16 críticas y las 81 anomalías de balance como `unreconciled`.
- [x] Propagar dependencias a ratios, márgenes y resultados derivados.
- [x] Generar `report.md` con tabla resumen por cifra y estado.
- [x] Tests F2 verdes y `data/` intacto.
- [x] F2.1 aprobada por el usuario.

**Aceptación:** F2.1 implementada y probada. No se inicia F2.2, Monte Carlo ni optimización.

---

## 4. Criterio de cierre

La Fase 0 está cerrada cuando T0.1–T0.7 están verificadas y T0.8 está aprobada.

La Fase 1 está cerrada: F1.1, F1.2 literal y F1.3 verificadas; F1.4 aprobada.

Después del cierre de Fase 0:

1. No se inicia automáticamente la Fase 2.
2. Se ejecuta **F1: fuentes, inventario, carga, identificación de periodos, validación, Markdown y auditoría**.
3. Las tareas detalladas de F1 viven en este archivo.

Estado actual: Fase 1 cerrada; F2.1 aprobada; F2.2 pendiente de aprobación de alcance; Monte Carlo y optimización no iniciados.

---

## 5. Fuera de alcance

- Implementar el loader.
- Implementar el motor financiero.
- Implementar Monte Carlo.
- Implementar el optimizador.
- Resolver todas las contradicciones detectadas.
- Modificar Excel o JSON originales.
- Crear resultados financieros definitivos.
