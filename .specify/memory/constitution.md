# Constitución del Sistema — cg_01 / CompanyGame Spain10

Versión: 0.2.0
Estado: Fase 1 en curso; principios de datos, Markdown y auditoría incorporados
Ámbito: sistema de planificación financiera y apoyo a decisiones para CORBATUL / Spain10
Autoridad: este documento prevalece sobre `spec.md`, `plan.md`, `tasks.md` y cualquier implementación futura.

---

## 1. Propósito

Esta Constitución fija los principios permanentes del proyecto. No describe fórmulas financieras, funcionalidades concretas ni tareas de implementación. Su finalidad es evitar que decisiones técnicas o de negocio posteriores contradigan los fundamentos acordados.

El sistema debe ayudar a comparar decisiones empresariales y explicar sus consecuencias financieras, no limitarse a producir una cifra de optimización sin justificación.

---

## 2. Jerarquía documental

1. **Constitución:** principios permanentes y reglas de gobierno.
2. **Especificación (`spec.md`):** problema de negocio, alcance, requisitos generales, reglas del juego, parámetros, hipótesis y pendientes.
3. **Plan (`plan.md`):** fases, dependencias, entregables y arquitectura conceptual.
4. **Tareas (`tasks.md`):** trabajo concreto para cerrar una fase.
5. **Código y configuración:** implementación subordinada a los documentos anteriores.
6. **Memoria operativa:** `.specify/memory/interpretations.json` y `.specify/memory/open_questions.json` registran interpretaciones confirmadas y preguntas abiertas. No crean reglas nuevas ni sustituyen a la Constitución o a la Spec.

Si existe conflicto, prevalece el documento de mayor jerarquía. Ningún artefacto inferior puede introducir una regla nueva presentándola como oficial.

---

## 3. Taxonomía obligatoria de afirmaciones

Toda afirmación relevante del proyecto debe clasificarse con una de estas etiquetas:

| Código | Tipo | Significado |
|---|---|---|
| **PR** | Principio permanente | Regla de gobierno del proyecto; no depende de una edición concreta del juego |
| **RG** | Regla del juego | Regla documentada de CompanyGame, con fuente identificable |
| **CF** | Parámetro configurable | Valor operativo que puede cambiar entre periodos o escenarios |
| **HY** | Hipótesis | Supuesto de trabajo no verificado oficialmente |
| **PD** | Pendiente | Contradicción, dato ausente o cuestión que requiere confirmación |

Reglas de uso:

- Una **RG** debe citar su fuente documental.
- Un **CF** no se hardcodea; se carga desde configuración versionada.
- Una **HY** debe explicar qué la sustenta y cómo se validará.
- Un **PD** debe registrar la contradicción, su impacto y el momento previsto de resolución.
- Una **HY** no puede ascender a **RG** sin evidencia y aprobación explícita.
- Un **PD** no se cierra por conveniencia; se cierra con evidencia o con una decisión documentada.

### 3.1. Naturaleza de las fuentes

Toda fuente se clasifica, además de por su contenido, por su naturaleza:

| Tipo | Significado | Tratamiento |
|---|---|---|
| **Original** | Excel, JSON o documento aportado como fuente de verdad | Inmutable en `data/`; se hashea y se conserva |
| **Capturada** | Markdown recopilado manualmente desde una web o documento externo | Fuente de lectura; conserva procedencia y fecha de captura cuando exista |
| **Generada** | Markdown o salida producida por el sistema a partir de una fuente | Artefacto derivado; nunca se convierte en fuente original |

Un Markdown generado y un Markdown capturado no son intercambiables. La procedencia y el hash deben permitir distinguirlos.

---

## 4. Principios permanentes

### PR-01. Integridad de los datos originales

`data/` es de solo lectura. No se sobrescriben, corrigen ni completan los Excel, JSON o documentos originales. Cualquier normalización se realiza en una capa canónica separada y trazable.

### PR-02. No invención de reglas ni cifras

No se inventan datos, fórmulas, tasas ni reglas oficiales. Los vacíos se documentan. Las estimaciones se identifican como hipótesis, nunca como hechos.

### PR-03. Trazabilidad completa

Todo dato canónico debe poder rastrearse hasta su archivo, hoja, celda o registro de origen. Toda decisión debe poder rastrearse hasta las fuentes, supuestos y cálculos que la sustentaron.

### PR-04. Diseño interanual y reutilizable

El sistema no depende de un año concreto ni de una numeración fija de archivos. Debe identificar el periodo por su contenido, clasificar su naturaleza y determinar el último ejercicio real validado. La regla general es:

> Último ejercicio real validado → siguiente ejercicio como objetivo de planificación.

La falta de un cierre reciente no impide definir ni desarrollar el sistema. Solo limita las operaciones que necesiten ese cierre para producir resultados financieros validados.

### PR-05. Separación entre reglas, parámetros e hipótesis

Las reglas del juego, los parámetros configurables, las hipótesis y las contradicciones pendientes se mantienen en categorías distintas. Un valor observado en un histórico no se convierte automáticamente en regla.

### PR-06. Prudencia financiera

La continuidad operativa y la liquidez prevalecen sobre la maximización de cualquier métrica aislada. Ninguna recomendación puede comprometer la capacidad de la empresa para atender sus obligaciones.

### PR-07. No duplicación de obligaciones

Una obligación ya incluida en una proyección no se resta por segunda vez al calcular el excedente. La porción corriente de un préstamo a largo plazo no se trata como un préstamo a corto plazo independiente.

### PR-08. Modelo antes que simulación y optimización

No se desarrolla simulación de incertidumbre ni optimización antes de disponer de un modelo financiero determinista suficientemente validado. La simulación no sustituye la validación histórica.

### PR-09. Explicabilidad y comparación

Toda recomendación debe explicar sus supuestos, sus consecuencias y su grado de incertidumbre. Toda optimización debe compararse con una línea base.

### PR-10. Control humano de las decisiones

El sistema no ejecuta decisiones empresariales. No aprueba ampliaciones de capital dilutivas, endeudamiento irreversible ni inversiones estratégicas sin autorización expresa.

### PR-11. Simplicidad y modularidad

Se prioriza código legible, cálculos verificables y pruebas útiles. Se evitan abstracciones innecesarias, dependencias no justificadas, bases de datos, servicios externos e interfaces web.

### PR-12. Control de cambios

Los cambios en reglas, parámetros, hipótesis, alcance o dependencias deben documentarse. No se reemplaza silenciosamente información histórica.

### PR-13. Fuentes originales inmutables y fuentes capturadas trazables

Los originales de `data/` no se modifican, corrigen ni completan. Las capturas manuales se incorporan como fuentes separadas, con procedencia, fecha de captura cuando esté disponible y referencia al origen. No se crean copias editables de los mismos datos.

### PR-14. Markdown como representación de lectura

El Markdown es la representación principal para leer y comprender las matrices. Se genera de forma automática y reproducible desde los Excel. No sustituye a la fuente original ni garantiza por sí solo la interpretación de la estructura. Cuando una tabla es ambigua, se conservan los valores, las referencias y la evidencia, y se emite una advertencia.

### PR-15. Capa normalizada única para cálculos

Los cálculos y validaciones usan una única capa normalizada y trazable. Se distingue entre valor original, valor normalizado, interpretación confirmada, inferencia pendiente y anomalía de origen. No se mantienen pipelines paralelos que dupliquen la misma lógica.

### PR-16. Notebook como interfaz de auditoría

`notebooks/01_revision_matrices.ipynb` es la interfaz de inspección y comprensión. Debe llamar a las funciones existentes, no reimplementar reglas ni cálculos. Una persona sin conocimiento interno debe poder ver qué examina, cómo se obtuvo el resultado y dónde comprobar la evidencia.

### PR-17. Interpretaciones confirmadas y preguntas persistentes

Antes de preguntar al usuario se revisan la documentación, la Constitución, la Spec y las decisiones ya confirmadas. Las respuestas se registran en la memoria operativa para no repetirlas. Las preguntas pendientes deben incluir concepto, evidencia, contradicción, alternativas, consecuencias y dato o decisión necesaria.

### PR-18. Simplicidad, no duplicación y sincronización documental

Se prefiere la solución más sencilla que satisfaga los requisitos. Se evita la sobreingeniería, la duplicación de lógica y la documentación que no contribuya al trabajo. Código, pruebas, especificaciones, roadmap y memoria deben mantenerse sincronizados. Un módulo solo se elimina o fusiona cuando la auditoría demuestra que reduce complejidad real sin perder funcionalidad útil.

---

## 5. Gobierno de las fases

Cada fase tiene un objetivo, un entregable y una condición de cierre. No se avanza si la puerta anterior no está satisfecha.

Las fases futuras se especifican cuando comienzan. La Fase 0 no debe anticipar fórmulas, algoritmos, clases, contratos técnicos ni pruebas detalladas de funcionalidades que todavía no se han definido.

La falta de datos para un periodo concreto no invalida el diseño general. Se documenta como limitación y se aplica a las operaciones afectadas.

---

## 6. Criterios de conflicto

Si dos fuentes o documentos se contradicen:

1. Se conserva la fuente original.
2. Se registra la contradicción como **PD**.
3. No se elige un valor arbitrariamente.
4. Se documenta el impacto de cada alternativa.
5. Se resuelve con evidencia, con una decisión explícita del responsable o se mantiene como pendiente.
6. Mientras no se resuelva, el valor afectado no se presenta como oficial.

---

## 7. Enmiendas

Toda enmienda a esta Constitución requiere:

- motivación;
- regla afectada;
- documentos y código impactados;
- aprobación explícita;
- registro de la nueva versión.

---

## 8. Comprobación de cumplimiento

Antes de cerrar cualquier fase se verificará:

- [ ] No se ha modificado `data/`.
- [ ] Los datos nuevos son trazables.
- [ ] Las reglas tienen fuente o están marcadas como hipótesis.
- [ ] Los parámetros son configurables.
- [ ] Las contradicciones están registradas.
- [ ] No se ha convertido una hipótesis en regla oficial.
- [ ] El alcance de la fase no se ha ampliado sin aprobación.
- [ ] Los resultados son reproducibles.
- [ ] Las recomendaciones se comparan con una línea base.
- [ ] No se ejecutan decisiones sin autorización.
