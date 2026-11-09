# FP&A Forecasting & Variance Analysis — Caso de estudio: accesorios de moda

![CI](https://github.com/DaelFame/fpa-forecasting-case-study/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![uv](https://img.shields.io/badge/managed%20with-uv-black)
![Tests](https://img.shields.io/badge/tests-74%20passing-brightgreen)

Un fabricante de corbatas, bufandas y calcetines creció un 0,9% en ingresos en 2026 y
vio caer su resultado neto un 61%. Un modelo financiero en Python reconstruyó sus
estados contables desde los libros de cierre originales, atribuyó toda la desviación
a gastos operativos y pronosticó los ingresos del año siguiente con un **0,3% de
error** — un año antes, usando solo información disponible en ese momento.

---

## El problema de negocio

**1. Los ingresos crecieron. El beneficio se hundió.** En 2026 los ingresos quedaron
a un 0,9% del presupuesto mientras el resultado neto falló un 61,1%. La cascada no
deja lugar a dudas:

| Cascada contra presupuesto, 2026 | EUR |
|---|---:|
| Margen bruto por encima | +74.457 |
| Gastos operativos | (359.888) |
| Resultado financiero | +24.294 |
| Resultado extraordinario | +18.000 |
| **Desviación neta** | **(243.137)** |

El mercado respondió. La disciplina de costes no. De la desviación, **150.000 € de
gastos generales no tienen respaldo documental**: se registran como hueco visible, no
se suavizan. El margen bruto se descompone en precio +41.536, volumen −2.607, mix +1
y coste unitario +35.527.

**2. La empresa estaba limitada por capacidad, no por demanda.** En 2028 el mercado
no pudo servir **594.748 unidades** de demanda: 405.181 corbatas, 112.242 bufandas y
77.325 calcetines. La cuota era del 16,7%, 20,1% y 36,5%: el techo era la producción,
lo que convierte una pregunta comercial en una decisión de asignación de capital.

**3. El presupuesto estaba sesgado, no solo desviado.** Medido sobre resultado antes
de impuestos, el real contra presupuesto fue −61,1% (2026), **+127,0% (2027)**,
+43,3% (2028) y +12,2% (2029). Desde 2027 la empresa superó sistemáticamente su
propio plan. Eso no es ruido: un hábito de presupuestar a la baja oculta necesidades
de capacidad y subestima la caja.

## La metodología

El motor también está disponible como [diagrama interactivo en español](docs/engine.es.html)
—zoom, búsqueda y temas claro/oscuro, sin instalar nada— y en
[versión inglesa](docs/engine.html).

**Backtest de ventana expansiva.** Dos folds, cada uno entrenado solo con años ya
cerrados:

| Fold | Entrena con | Predice | Se evalúa contra |
|---|---|---|---|
| F1 | 2024–2027 | 2028 | Cierre real 2028 |
| F2 | 2024–2028 | 2029 | Cierre real 2029 |

**Dos regímenes de información, un solo motor.** El régimen A conoce las decisiones
de la gerencia para el año objetivo: precios, producción planificada, marketing. El
régimen B solo conoce el último año cerrado, mantenido plano. La diferencia entre
ambos cuantifica el valor de saber las palancas.

| Fuera de muestra, 2028 | A — con decisiones | B — sin decisiones |
|---|---:|---:|
| Error de ingresos | **0,3%** | 15,7% |
| Error de margen bruto | 9,9% | 24,1% |
| Error de resultado neto | 25,5% | 55,0% |
| MAPE medio, 15 líneas de P&L | 26,6% | 32,3% |

Conocer las decisiones recorta el error de ingresos en **15,4 puntos: un 98% menos**.
Ambos regímenes comparten sesgo negativo (−22,8% y −30,4%): la extrapolación
subestima sistemáticamente un negocio que crece, y el sesgo es el hallazgo, no el
ruido.

**Todo es auditable.** Cada cifra lleva archivo, hoja y celda de origen; cada línea de
los estados lleva estado (`confirmed`, `inferred_accepted`, `pending`,
`unreconciled`); los hashes de las fuentes se verifican en cada ejecución. Cuando un
registro de decisiones contradice el cierre — como ocurre con el de 2029 — las filas
afectadas se exportan como `pending` en lugar de corregirse en silencio.

## La perspectiva 2030

Construida sobre el cierre ejecutado de 2029, con escenarios aplicados a los drivers:

| Escenario | Ingresos | Margen bruto | Resultado neto | Margen neto |
|---|---:|---:|---:|---:|
| Stress | 5.306.691 | 3.107.915 | 1.209.825 | 22,8% |
| Downside | 5.778.397 | 3.567.987 | 1.554.879 | 26,9% |
| **Base** | **6.206.656** | **3.879.909** | **1.788.821** | **28,8%** |
| Upside | 6.647.329 | 4.204.244 | 2.032.072 | 30,6% |

Base mantiene la estrategia actual: es idéntico con y sin conocimiento de las
decisiones, porque no hay decisiones nuevas. El valor del régimen A aparece solo
cuando una decisión cambia. En los escenarios Downside y Stress el régimen sin
decisiones conserva más beneficio, porque el régimen A aplica también el recorte de
precio además del de volumen.

## Stack técnico

- **Python 3.12** — pandas, NumPy, openpyxl. Modelo basado en drivers, sin caja negra
  estadística: con 20 observaciones trimestrales un modelo de series temporales no es
  defendible, así que los drivers son explícitos y editables.
- **Data marts en esquema galaxia** — 8 tablas de hechos que comparten 9 dimensiones
  conformes, exportadas a CSV (`data/processed`) para Power BI. Cero dimensiones
  huérfanas.
- **Git y CI** — 74 tests en GitHub Actions: identidades contables, integridad
  referencial, cuadre exacto de la cascada de varianza, cobertura del backtest y
  regresiones de identidad de fuentes.
- **Power BI** — el proyecto `.pbip` se versiona como texto (TMDL); la capa de
  informe está en progreso.

## Transparencia

Es un **caso de estudio anonimizado construido sobre un simulador de negocio
competitivo**, no datos de cliente ni las cuentas de una empresa real. Se eliminan la
marca del simulador y la identidad de los demás equipos; el origen se declara porque
afirmar lo contrario sería trivialmente refutable.

Lo que demuestra es el método: convertir libros de cierre en un modelo financiero
auditable, encontrar dónde se fue el dinero y probar que un pronóstico merece
confianza antes de usarlo.

## Reproducirlo

```bash
uv sync --group dev
uv run python -m cg_01            # capa canónica + exportación literal de celdas
uv run python -m cg_01.fpa.marts  # estados, marts y pronóstico 2030
uv run pytest -q                  # 74 tests
```

Dentro del repositorio: `outputs/markdown/` guarda una exportación literal celda a
celda de cada hoja, `notebooks/01_revision_matrices.ipynb` contiene la revisión
exploratoria de las matrices de origen, y `data/processed/` los marts que consume el
dashboard.

Empezar por [`docs/README.md`](docs/README.md) para el método, el modelo de datos y
todas las limitaciones conocidas, o leer la versión inglesa en
[`README.md`](README.md).

## Licencia

MIT — ver [LICENSE](LICENSE).
