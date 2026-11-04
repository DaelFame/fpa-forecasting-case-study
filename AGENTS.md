# Guía permanente para agentes — cg_01

Este archivo es la guía central de trabajo. No sustituye a la Constitución ni a la Spec; indica cómo abordar cualquier tarea en este repositorio.

## Lectura obligatoria al iniciar

1. `.specify/memory/constitution.md`
2. `specs/000-general-system/spec.md`
3. `specs/000-general-system/plan.md`
4. `specs/000-general-system/tasks.md`
5. `.specify/memory/interpretations.json` y `.specify/memory/open_questions.json`
6. `docs/estado_actual_f1.md`
7. Documentación de módulos en `docs/modules/Decisiones_matriz_1/` y `docs/modules/Decisiones_matriz_2/`

Antes de crear módulos nuevos, revisa la estructura de `src/cg_01/`, las pruebas y las convenciones existentes.

## Reglas de trabajo

1. **Lee la Constitución, la Spec y el Plan vigentes** antes de modificar alcance, datos o arquitectura.
2. **Revisa los módulos y convenciones existentes** antes de crear archivos, clases o dependencias.
3. **Mantén sincronizados** especificación, roadmap, tareas, pruebas y documentación cuando cambie el alcance.
4. **Usa las fuentes y reglas existentes**; no inventes datos, fórmulas, tasas ni interpretaciones.
5. **Formula preguntas concretas** cuando una decisión material no pueda resolverse con evidencia. Incluye concepto, referencias, contradicción, alternativas y consecuencias.
6. **Registra las respuestas confirmadas** en `.specify/memory/interpretations.json` para no repetir preguntas.
7. **Verifica la implementación** con pruebas y ejecución real antes de declarar una tarea completada.
8. **Evita sobreingeniería, duplicación de lógica y documentación inútil**. Prefiere la solución más sencilla que satisfaga el requisito.
9. **Respeta los originales de `data/`** y el alcance autorizado. No sobrescribas trabajo del usuario ni crees copias editables de fuentes.
10. **No inicies funcionalidades de fases futuras** hasta cumplir sus condiciones de entrada. Monte Carlo y optimización no están autorizados en Fase 1.

## Fuentes y datos

- `data/` es de solo lectura. Los hashes deben permanecer estables.
- Las capturas manuales viven en `data/manual/` con frontmatter y procedencia.
- El Markdown de `outputs/markdown/` es generado y no editable.
- La capa canónica es la única fuente para cálculos y validaciones.
- No conviertas una inferencia pendiente en regla oficial.

## Flujo recomendado

```text
leer documentación y estado
→ revisar módulos y pruebas
→ identificar la evidencia disponible
→ implementar la solución mínima
→ actualizar pruebas y documentación
→ ejecutar pytest, pipeline y notebook
→ registrar interpretaciones o preguntas
→ verificar hashes y estado de Git
```

## Comandos

```bash
uv sync --group dev
uv run pytest -q
uv run python -m cg_01
```

Si una tarea cambia el alcance, actualiza también `specs/000-general-system/spec.md`, `plan.md` y `tasks.md`. Si una tarea queda bloqueada por una decisión humana, regístrala en `.specify/memory/open_questions.json`; no la ocultes como si estuviera resuelta.
