## Alcance de esta respuesta

Modo planificación: no he creado ni modificado archivos, no he ejecutado el modelo y no he tocado `data/`. Los cuatro artefactos SDD **no existen todavía en disco**; lo que sigue es el diagnóstico y la propuesta para tu revisión.

Etiquetas usadas:
- **[HECHO]**: comprobado en el repositorio.
- **[INTERPRETACIÓN]**: deducción razonable, no verificada oficialmente.
- **[PROPUESTA]**: decisión de diseño pendiente de aprobación.
- **[PENDIENTE]**: requiere información o confirmación.

---

# A. Diagnóstico del estado actual

## A.1. Qué existe

| Elemento | Estado |
|---|---|
| Repositorio Git | Inicializado, sin ningún commit; todo aparece como no rastreado |
| `data/Matriz_General_0.xlsx` | Históricos 2025 y 2024 |
| `data/Matriz_General_1.xlsx` | Históricos 2026, 2025 y 2024 |
| `data/decisiones/Bitacora_decisiones_para_2026.json` | Decisiones de 2026 |
| `data/decisiones/Bitacora_decisiones_para_2027.json` | Decisiones de 2027, sin resultados reales asociados |
| `docs/modules/*` | Documentación de Ventas, Producto, Producción, Financiación, Inversiones Financieras y Otros Proyectos |
| `src/`, `outputs/` | Vacíos |
| `main.py` | Stub sin funcionalidad |
| `pyproject.toml` | `numpy`, `openpyxl`, `pandas`; sin `pytest` |
| `.specify/`, `specs/` | No existen |
| `README.md` | Vacío |
| Scripts o prototipos previos | No existen |

## A.2. Qué falta

- **`Matriz_General_2` y `Matriz_General_3` no están en el repositorio.**
- **No hay cierre real de 2027.** Solo existen las decisiones tomadas para 2027.
- No hay manual oficial de CompanyGame ni fuente verificable de la fórmula de Valor de Compañía.
- No hay artefactos SDD, tests, ni historial de versiones.
- No hay documentación de demanda, fiscalidad, cobros/pagos ni caja mínima operativa.

## A.3. Contradicción principal para 2028

**[HECHO]** La última base real validada es **2026**. `Matriz_General_1` contiene 2026, 2025 y 2024; no contiene resultados de 2027.

**[HECHO]** El JSON de 2027 contiene decisiones, pero no resultados. Por tanto, **2027 es un año planificado, no un cierre real validado**.

**[INTERPRETACIÓN]** Si `Matriz_General_2` sigue la secuencia de las matrices anteriores, debería contener 2027/2026 y sería la base para preparar 2028. Pero **no está disponible y no se puede verificar su contenido ni su periodo**.

**Conclusión:** la planificación de 2028 puede especificarse ahora, pero **no puede ejecutarse con datos validados** hasta recibir el cierre de 2027. Esto no bloquea la Fase 0; sí bloquea el inicio real de la planificación 2028.

## A.4. Inconsistencias verificadas

| # | Hecho comprobado | Impacto |
|---|---|---|
| 1 | Balance 2026: activo 5.335.431; pasivo 1.447.132; patrimonio reportado 4.134.690. La suma pasivo + patrimonio da 5.581.822, con diferencia de **246.391**. | El balance no cuadra con el patrimonio reportado. |
| 2 | Las reservas detalladas son 930.663; las resumidas son 1.177.053. La diferencia es 246.390. | Una de las dos bases de reservas es incorrecta o hay una partida no explicada. |
| 3 | “Total Corriente” resumido: 903.281. Detalle: 1.028.281. Diferencia: 125.000, que son activos financieros CP. | El total corriente resumido excluye activos financieros CP. |
| 4 | “Activo No Corriente” en la tabla comparativa aparece como 903.281, importe que corresponde a activos corrientes. | Etiqueta incorrecta. |
| 5 | Activo corriente trimestral: 524.904, que excluye caja (503.378). | Total trimestral incompleto. |
| 6 | Pasivo corriente trimestral: 297.748, que omite proveedores (221.978) y coincide con la porción corriente del LP. | Total trimestral incompleto y posible confusión con deuda CP. |
| 7 | Ingresos 2026: 38.610,39 en una tabla y 3.861.039 en otra. | Error de escala ×100. |
| 8 | Gastos generales 2026: 344.808 total, pero 194.808 en el detalle administrativo. | 150.000 sin explicar. |
| 9 | Tipo del crédito extraordinario: 7,6 % en una tabla y 13,2 % en otra y en la documentación. | Contradicción interna; afecta a la penalización por iliquidez. |
| 10 | Aumento de activo fijo bruto 2026: 1.533.000. Proyectos seleccionados en el JSON 2026: 400.000. | 1.133.000 de CAPEX no explicado por la bitácora. |
| 11 | 2027: `unidades_producir` = 0/0/0. Según la regla confirmada, `0` significa mantener la producción anterior, no detenerla. | Riesgo alto de mala interpretación: 2027 equivaldría a 210.000/29.000/33.000 unidades, no a cero. |
| 12 | Proveedores: “Economica” en 2026, “Estandar” en 2027; la documentación usa “Económica” y “Estándar”. | Necesita normalización de alias. |
| 13 | Presupuesto 2026: resultado neto previsto 398.088; real 154.951. Gastos generales previstos 141.793; reales 344.808. | La precisión presupuestaria es un problema real, no solo teórico. |
| 14 | No hay fórmula oficial de Valor de Compañía ni pesos verificables. | No se puede tratar la puntuación como regla oficial. |

## A.5. Qué conservar y qué corregir

**Conservar:**
- Los Excel y JSON originales, sin modificaciones.
- La documentación de módulos como fuente principal disponible.
- El stack Python ya preparado.
- La estructura simple del repositorio.

**Corregir en la capa canónica, nunca en los originales:**
- Etiquetas de activo corriente/no corriente.
- Totales trimestrales incompletos.
- Escala de ingresos.
- Tratamiento de la porción corriente del LP.
- Tipo extraordinario.
- CAPEX no explicado.
- Semántica de `0` en producción.
- Alias de proveedores.
- Periodos y naturaleza de cada matriz.

---

# B. Definición del negocio

## B.1. Problema empresarial

**[PROPUESTA]** El sistema debe ayudar a responder, cada año:

> Dado el último cierre real validado y la situación de caja, deuda, activos y compromisos, ¿qué combinación de decisiones permite mejorar el Valor de la Compañía sin comprometer la liquidez, la solvencia ni la continuidad operativa, y con una precisión presupuestaria defendible?

No es un problema de “maximizar una cifra”. Es un problema de decisión con restricciones, incertidumbre y trazabilidad.

## B.2. Decisiones que debe apoyar

- Precios, descuentos, promoción e incentivos comerciales.
- Diseño, amplitud de gama y proveedores.
- Producción, ampliación de capacidad y mantenimiento.
- Financiación LP/CP, cobros, pagos, cancelación de deuda y dividendos.
- Inversiones financieras CP/LP.
- Proyectos especiales y CAPEX.
- Comparación de alternativas y explicación de consecuencias.

## B.3. Información necesaria

- Último cierre real validado.
- Caja inicial y calendario de cobros/pagos.
- Deuda, vencimientos, intereses y condiciones.
- Activos financieros y su disponibilidad real.
- Inversiones comprometidas.
- Necesidades de capital operativo.
- Capacidad, ocupación, inventarios y demanda.
- Restricciones y reglas del juego.
- Decisiones históricas y resultados reales para comparar.

## B.4. Riesgos que debe prevenir

- Iliquidez y crédito extraordinario.
- Endeudamiento excesivo o mal estructurado.
- Inversiones que comprometan obligaciones futuras.
- Penalizaciones por ocupación insuficiente.
- Precios fuera del corredor.
- Errores de producción por mala interpretación de `0`/`1`.
- Desviaciones presupuestarias graves.
- Decisiones basadas en datos inconsistentes.
- Exceso de confianza en un modelo no validado.

## B.5. Cómo se evaluará una decisión

Dimensiones, sin fijar todavía la fórmula definitiva:

1. **Rentabilidad y Valor de Compañía.**
2. **Precisión presupuestaria.**
3. **Liquidez y caja mínima.**
4. **Solvencia y estructura de deuda.**
5. **Marca, producto, distribución y mercado.**
6. **Robustez frente a escenarios.**
7. **Explicabilidad y trazabilidad.**
8. **Comparación con una línea base.**

**[PROPUESTA]** Una decisión se considera buena si es factible, financieramente sostenible, robusta, explicable y mejor que la alternativa de referencia. No solo si obtiene una puntuación alta.

## B.6. Límites impuestos por CompanyGame

Confirmados en la documentación disponible:
- Precios con variación máxima de ±15 %.
- Producción: `0` mantiene, `1` detiene, `2..600.000` unidades reales.
- Capacidades base y niveles de ampliación.
- Ocupación mínima del 60 %, con gastos excepcionales por debajo.
- Mantenimiento entre 1 % y 7 % del activo fijo bruto de fábrica.
- LP al 6,6 % a 8 años; CP al 5,9 % a 1 año; extraordinario al 13,2 %.
- Dividendos solo si el periodo anterior fue positivo.
- Límites de inversiones financieras y proyectos.

**[PENDIENTE]** La documentación dice “uso total de la planta”; una decisión previa del stakeholder hablaba de ocupación por línea. No se resolverá por conveniencia: se registrará como ambigüedad y se validará antes de F2.

## B.7. Fuera de alcance

- Ejecutar decisiones automáticamente.
- Aprobar ampliaciones de capital dilutivas sin autorización.
- Modificar `data/`.
- Presentar hipótesis como reglas oficiales.
- Construir una interfaz web, base de datos o servicio externo.
- Desarrollar el modelo completo en Fase 0.

---

# C. Regla interanual

## C.1. Principio

**[PROPUESTA]**

> Último ejercicio real validado → ejercicio inmediatamente siguiente como objetivo de planificación.

El sistema no se diseña solo para 2028. Debe poder repetir el ciclo para 2029, 2030 y siguientes.

## C.2. Clasificación de fuentes

Toda fuente debe clasificarse como:

- **Real:** cierre validado.
- **Decisión:** bitácora de decisiones tomadas.
- **Presupuesto:** previsión aprobada.
- **Proyección:** resultado del modelo.
- **Escenario:** simulación.

Una decisión o un presupuesto **no son un real**.

## C.3. Comportamiento esperado

1. Identificar el periodo por contenido, no por nombre de archivo.
2. Verificar la secuencia temporal y la transición declarada.
3. Distinguir real, decisión, presupuesto y proyección.
4. Validar que el cierre es suficiente y coherente.
5. Determinar el último real validado.
6. Establecer el siguiente ejercicio objetivo.
7. Conservar el historial fuente → decisión → resultado.
8. Incorporar nuevas matrices sin depender de numeración fija.
9. Registrar contradicciones y detenerse si no hay evidencia suficiente.

## C.4. Aplicación al estado actual

**[HECHO]**
- Último real validado: **2026**.
- 2027: solo decisiones.
- 2028: objetivo solicitado, pero sin base real 2027.
- `Matriz_General_2`: no disponible.

**[INTERPRETACIÓN]** La secuencia `0 → 1 → 2` sugiere que `Matriz_General_2` contendrá 2027/2026. No se afirmará hasta verificar su contenido.

**Consecuencia:** F0 puede definir la regla; F1 puede preparar la carga; la planificación 2028 debe esperar al cierre 2027.

## C.5. Historial

**[PROPUESTA]** Mantener un registro conceptual, no una base de datos:

- Fuente y periodo.
- Naturaleza del dato.
- Decisiones asociadas.
- Resultado real, si existe.
- Desviación entre previsión y real.
- Supuestos y versión del modelo.

---

# D. Fundamentos financieros

## D.1. Distinciones obligatorias

| Concepto | Significado | No confundir con |
|---|---|---|
| Caja contable | Saldo de efectivo al cierre | Liquidez inmediata total |
| Liquidez disponible | Caja + activos realizables según condiciones | Caja contable |
| Caja mínima operativa | Colchón para obligaciones y riesgo | Porcentaje arbitrario |
| Flujo de caja | Movimientos del periodo | Resultado contable |
| Excedente invertible | Caja disponible menos caja mínima y compromisos | Beneficio del ejercicio |
| Activos financieros CP/LP | Inversiones financieras | Efectivo inmediato |

## D.2. Principios

1. **Separar resultado contable y caja.** Un beneficio no equivale a efectivo disponible.
2. **Usar calendario de cobros y pagos.** No basta con el devengo.
3. **No contar dos veces las obligaciones.** Si un pago ya está en las salidas, no se resta otra vez del excedente.
4. **No tratar activos financieros como caja libre.** El CP puede tener disponibilidad trimestral; el LP no es líquido inmediato.
5. **Incluir deuda, vencimientos e intereses.** Sin duplicar la porción corriente del LP.
6. **Incluir impuestos.** No asumir tipos nulos por pérdidas anteriores sin regla verificada.
7. **Justificar la caja mínima.** Debe derivarse de personal, proveedores, deuda, impuestos, inversiones comprometidas, estacionalidad y contingencia.
8. **Distinguir restricciones duras de objetivos deseables.** La caja no negativa es dura; mejorar la marca es deseable.
9. **No recomendar inversiones que comprometan obligaciones futuras.**
10. **No ejecutar decisiones sin aprobación humana.**

## D.3. Qué debe validarse en F2

- Reconstrucción del cierre 2026.
- Conciliación de caja.
- Cuadre de balance.
- Deuda e intereses.
- Capital operativo.
- Caja mínima operativa.
- Excedente potencialmente invertible.
- Comparación con 2025 y con presupuesto.

**[PROPUESTA]** En F0 no se fija una fórmula de caja mínima ni un porcentaje. Se define el principio y se deja la calibración para F2.

---

# E. Organización SDD

## E.1. Propósito de cada artefacto

| Artefacto | Debe contener | No debe contener |
|---|---|---|
| `constitution.md` | Principios permanentes: integridad, prudencia, trazabilidad, modularidad, control de cambios, autorización | Fórmulas financieras detalladas ni tareas |
| `spec.md` | Problema de negocio, actores, alcance, decisiones, información, riesgos, dimensiones de evaluación, reglas fundamentales, comportamiento interanual | Arquitectura técnica detallada ni algoritmos |
| `plan.md` | Fases, dependencias, entregables, condiciones de inicio/cierre, bloques funcionales, gestión de features | Especificación exhaustiva de cada feature |
| `tasks.md` | Solo tareas concretas para cerrar Fase 0, con dependencias y aceptación | Tareas de F1–F4 ni detalles de implementación |

## E.2. Cambios propuestos

- **Crear los cuatro artefactos desde cero.** No existen en disco.
- **`tasks.md` limitado a Fase 0.** Las tareas futuras se detallarán al iniciar cada fase.
- **Constitución estable y breve.** Sin duplicar la especificación.
- **Spec centrada en el negocio.** No empezar por clases ni módulos.
- **Plan sin sobreingeniería.** Cinco bloques funcionales y una arquitectura conceptual; sin contratos técnicos prematuros.
- **Regla de no duplicación.** Cada regla vive en un solo documento y se referencia desde los demás.
- **Trazabilidad de supuestos.** Toda regla no verificada se marca como supuesto.

## E.3. Coherencia

- La Constitución manda sobre la Spec.
- La Spec manda sobre el Plan.
- El Plan manda sobre las Tasks.
- Las Tasks no pueden introducir requisitos nuevos.
- Ningún documento puede convertir una hipótesis en regla oficial.

---

# F. Hoja de ruta general

| Fase | Objetivo | Entregable principal | Depende de | Empieza cuando | Termina cuando |
|---|---|---|---|---|---|
| **0. Planificación** | Definir problema, principios, regla interanual, arquitectura y F0 | 4 artefactos SDD aprobados | — | Ahora | Aprobación explícita |
| **1. Datos y trazabilidad** | Inventariar, cargar, clasificar, validar y conciliar fuentes | Dataset canónico + informe de anomalías | F0 | F0 cerrada | Datos trazables, `data/` intacto, anomalías documentadas |
| **2. Modelo financiero determinista** | Reconstruir el cierre y proyectar resultados, balance y caja | Modelo validado + caja mínima + excedente | F1 | F1 cerrada | Reconstrucción histórica validada y reglas del juego respetadas |
| **3. Incertidumbre** | Modelar escenarios y riesgo | Simulación reproducible + sensibilidad | F2 | Modelo validado | Supuestos documentados y resultados auditables |
| **4. Optimización** | Comparar y recomendar decisiones | Recomendación vs línea base + informe de riesgo | F3 | Simulación validada | Restricciones cumplidas y aprobación humana |

## F.1. Condiciones generales

- **F1** no empieza hasta que F0 esté aprobada.
- **F2** no empieza hasta que F1 tenga datos canónicos y anomalías documentadas.
- **F3** no empieza hasta que F2 esté validado. Sin modelo financiero fiable no hay Monte Carlo.
- **F4** no empieza hasta que F3 sea reproducible. Sin incertidumbre medida no hay optimización robusta.

## F.2. Primera funcionalidad después de F0

**[PROPUESTA]** La primera feature será **F1: fuentes, inventario, carga, identificación de periodos, validación y conciliación**.

No será el motor financiero ni el optimizador. Primero hay que saber qué datos existen, qué representan y qué contradicciones contienen.

---

# G. Tareas para cerrar Fase 0

| ID | Tarea | Depende de | Aceptación |
|---|---|---|---|
| **T0.1** | Documentar el inventario de fuentes y el diagnóstico | — | Fuentes, periodos, naturaleza y carencias identificadas |
| **T0.2** | Redactar `constitution.md` | T0.1 | Principios permanentes y control de cambios |
| **T0.3** | Redactar `spec.md` | T0.1 | Problema, alcance, actores, requisitos y regla interanual |
| **T0.4** | Redactar `plan.md` | T0.1 | Fases, dependencias, entregables y puertas |
| **T0.5** | Redactar `tasks.md` | T0.2–T0.4 | Solo tareas F0, con dependencias y aceptación |
| **T0.6** | Verificar coherencia y no duplicación | T0.2–T0.5 | Mismas reglas, mismos umbrales, sin contradicciones |
| **T0.7** | Verificar que no se ha tocado código ni `data/` | T0.6 | Solo documentación; datos intactos |
| **T0.8** | **Puerta F0:** aprobación explícita | T0.7 | Autorización para iniciar F1 |

No se incluyen tareas de implementación.

---

# H. Riesgos y cuestiones pendientes

## H.1. Bloqueantes reales

| Cuestión | Estado | Bloquea |
|---|---|---|
| Falta el cierre real de 2027 / `Matriz_General_2` | **[HECHO]** No está en el repo | Ejecutar la planificación 2028, no la Fase 0 |
| Aprobación explícita de los artefactos | **[PENDIENTE]** | Crear los documentos |

## H.2. A resolver antes de F2

- **Balance canónico:** decidir si se usa el balance detallado, el resumido o una reconciliación documentada. Hay una diferencia de 246.391 €.
- **Reservas:** determinar la base correcta.
- **Intereses:** confirmar la convención de devengo y la tasa aplicable; hay contradicción 7,6 % / 13,2 %.
- **Deuda:** confirmar que la porción corriente del LP no se trata como préstamo CP independiente.
- **CAPEX 2026:** explicar los 1.533.000 € frente a los 400.000 € del JSON.
- **Ocupación:** confirmar si el 60 % es por línea o total planta.
- **Fiscalidad:** no asumir impuestos nulos sin regla.
- **Caja mínima:** justificar su cálculo.

## H.3. A resolver antes de F4

- Fórmula oficial del Valor de Compañía.
- Pesos oficiales y tratamiento de cada componente.
- Penalización por “No Decisión”.
- Criterio de comparación con la línea base.

## H.4. No bloqueantes ahora

- Alias de proveedores.
- Detalle de demanda y elasticidades.
- Tratamiento trimestral de producción.
- Proyectos con presupuesto 0.
- Distribución de cobros y pagos.
- Partidas extraordinarias.
- Cambios de perímetro o nuevas matrices.

## H.5. Riesgo de proceso

**[HECHO]** El repositorio no tiene ningún commit. Todo está sin rastrear.

**[PROPUESTA]** Tras aprobar la F0, crear un commit inicial solo con la documentación. No se hará ahora.

---

# I. Recomendación de cierre

## I.1. Qué está suficientemente definido

- El problema empresarial.
- Los principios permanentes.
- La regla interanual.
- La separación entre real, decisión, presupuesto y proyección.
- El orden de fases y sus dependencias.
- La arquitectura conceptual en cinco bloques.
- Las tareas para cerrar F0.

## I.2. Qué debe revisarse antes de escribir

- Confirmar que la primera planificación es 2028 y que se acepta que **no se ejecutará hasta disponer del cierre 2027**.
- Confirmar que `tasks.md` contendrá **solo Fase 0**, no todas las fases.
- Confirmar que la puntuación de Valor de Compañía queda como **configuración no oficial** hasta validación.
- Confirmar que las contradicciones se documentan, no se corrigen en los Excel originales.

## I.3. Siguiente paso

**[PROPUESTA]** Aprobar la creación de:

- `.specify/memory/constitution.md`
- `specs/000-general-system/spec.md`
- `specs/000-general-system/plan.md`
- `specs/000-general-system/tasks.md`

Después de crearlos, detenerme y no iniciar F1 hasta nueva aprobación.

**¿Apruebas que redacte los cuatro artefactos con este enfoque, sabiendo que la planificación 2028 quedará especificada pero no podrá ejecutarse hasta recibir el cierre real de 2027?**
