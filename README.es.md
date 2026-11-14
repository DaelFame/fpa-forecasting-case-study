# FP&A Forecasting & Variance Analysis - Caso de estudio: accesorios de moda

![CI](https://github.com/DaelFame/fpa-forecasting-case-study/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![uv](https://img.shields.io/badge/managed%20with-uv-black)
![Tests](https://img.shields.io/badge/tests-74%20passing-brightgreen)

Un fabricante de corbatas, bufandas y calcetines creció un 0,9% en ingresos en 2026 y vio
caer su resultado neto un 61%. Un modelo financiero en Python reconstruyó sus estados
contables desde los libros de cierre originales, atribuyó toda la desviación a gastos
operativos y pronosticó los ingresos del año siguiente con un **0,3% de error** - un año
antes, usando solo la información disponible en ese momento.

---

## 📊 Estado del Dashboard Ejecutivo (Informe Power BI PBIR)

**Páginas completadas y verificadas:**
- `01 | Summary` — Tarjetas DAX-verificadas, páginas de tooltip, encabezado y toma de decisiones ejecutiva
- `02 | Profitability` — Análisis de margen de producto, distribución en grilla de 12 columnas, títulos guiados por preguntas
- `03 | Variance` — **Construido / En revisión**: Puente de varianza, columnas año-a-año, desglose de gastos operativos, tooltips interactivos (capturas al pasar el cursor disponibles)

**Canvas:** 1920×1080 · `#F5F7FA` · distribución en 12 columnas (139 px de ancho, 16 px de hueco, 32 px de márgenes)
**Paleta:** Primario `#1F3864`, Secundario `#2E75B6`, Neutro `#8C8C8C`, Tarjeta `#FFFFFF`
**Tipografía:** 16 px de título, 11 px de subtítulo, 10 px de etiqueta de tarjeta, 32 px de valor llamada
**Todo el texto 100% inglés** — regla permanente en `dashboard/AGENTS.md`

**Números verificados por DAX en vivo (FY 2026–2029, pre-tax):**
- Plan Net Income: **€3,954,345** | Real: **€4,822,290** | Variación: **+€867,945** (`+21,9%`)
- 2026: **−€243,137** (`−61,1%`) | 2027: **+€351,995** (`+127,0%`)
- 2028: **+€499,886** (`+43,3%`) | 2029: **+€259,201** (`+12,2%`)
- Drivers: Extraordinario **+€572,000** (65,9% del superávit), Costo Unitario **+€551,368**, Volumen **+€255,229**, Sobrecoste Operativo **−€326,210**

**Report Page Tooltips:** Páginas de tooltip ocultas vinculadas a cada tarjeta KPI y visual, verificadas contra el patrón PBIR trabajado de `tipRevenue`.

---

## El problema de negocio

**1. Los ingresos crecieron. El beneficio se hundió.** En 2026 los ingresos quedaron dentro del 0,9% del presupuesto mientras el resultado neto falló un 61,1%. La cascada es indiscutible:

| Cascada contra presupuesto, 2026 | EUR |
|---|---:|
| Margen bruto por encima | +74.457 |
| Gastos operativos | (359.888) |
| Resultado financiero | +24.294 |
| Resultado extraordinario | +18.000 |
| **Desviación neta** | **(243.137)** |

El mercado respondió. La disciplina de costes no. De la desviación, **150.000 ? de gastos generales no tienen respaldo documental**: se registran como hueco visible, no se suavizan. El margen bruto se descompone en precio +41.536, volumen -2.607, mix +1 y coste unitario +35.527.

**2. La empresa estaba limitada por capacidad, no por demanda.** En 2028 el mercado
no pudo servir **594.748 unidades** de demanda: 405.181 corbatas, 112.242 bufandas y
77.325 calcetines. La cuota era del 16,7%, 20,1% y 36,5%: el techo era la producción,
lo que convierte una pregunta comercial en una decisión de asignación de capital.

**3. El presupuesto estaba sesgado, no solo desviado.** Medido sobre resultado antes
de impuestos, el real contra presupuesto fue -61,1% (2026), **+127,0% (2027)**, +43,3% (2028) y
+12,2% (2029). Desde 2027 la empresa superó sistemáticamente su propio plan. Eso no es ruido:
un hábito de presupuestar a la baja oculta necesidades de capacidad y subestima la caja.

---

## El motor de limpieza y procesamiento de datos (`cg_01`)

El motor `cg_01` es la tubería automatizada y auditable que transforma los libros de
trabajo operativos y financieros en bruto en un esquema estrella (18 tablas, 28
relaciones, 46 medidas DAX) consumido por el dashboard de Power BI.

**Ingesta** (`src/cg_01/loader.py`):
- Libros Excel (`data/*.xlsx`), logs de decisiones JSON y bitácoras Markdown
- Verificación SHA-256 en cada ejecución (`sha256_file`)
- Ordenamiento determinista de fuentes (`_sorted_paths`) para que `source_id` nunca se desplace
- Tres tipos de fuente: `excel`, `json`, `markdown` con frontmatter

**Limpieza y Normalización** (`src/cg_01/canonical.py`):
- Detección de cuadrícula, identificación de celdas de período/cuarter
- Parteo de años relativos (`Ano +1`), limpieza de etiquetas, quita de acentos
- Normalización de clave de producto (quitar sufijos `_catalogo_euro`, `_euro`, `_eur`)
- Parsea de decisiones: precios, unidades de producción, selección de CAPEX, porcentajes de descuento
- Detección de anomalías: tolerancia de balance, umbrales de ocupación, corredores de precio

**Salida** (`src/cg_01/pipeline.py` → `write_all_outputs`):
- Exportación de marts a `data/processed/` como CSV para Power BI
- Generación de Markdown (`outputs/markdown/`) con exportación literal celda por celda
- Resumen de anomalías: conteos critical/high/medium/low/info
- Reconciliación de hashes: bandera `all_hashes_unchanged` en cada ejecución

**Garantías de transparencia:**
- Cada cifra lleva un archivo fuente, hoja y coordenada de celda
- Los hashes de las fuentes se verifican en cada ejecución; las discrepancias se marcan como advertencias
- Los logs de decisiones se marcan `pending` cuando contradicen el cierre (ej. el log de 2029)
- 74 tests pytest en identidades contables, integridad referencial, cuadre exacto de la varianza,
  cobertura del backtest y regresiones de identidad de fuentes

**Stack tecnológico:** Python 3.12 · pandas, NumPy, openpyxl · Data marts en esquema galaxia (8
tablas de hechos que comparten 9 dimensiones conformes) · Git y CI (GitHub Actions) · Power BI
(.pbip versionado como TMDL)

**Ejecutando el motor:**
```bash
uv sync --group dev
uv run python -m cg_01              # capa canónica + exportación literal de celdas
uv run python -m cg_01.fpa.marts   # estados, marts y pronóstico 2030
uv run pytest -q                     # 74 tests
```

---

## 📸 Recursos visuales

![1_Summary.png](assets/1_Summary.png)
*Página 01 | Summary — tarjetas KPI, encabezado título/subtítulo, fila de navegación y tooltips al pasar el cursor*

![2_Profitability.png](assets/2_Profitability.png)
*Página 02 | Profitability — análisis de margen de producto, grilla de 12 columnas, botones de navegación*

---

## Ejecutando el pipeline completo

```bash
uv sync --group dev
uv run python -m cg_01              # capa canónica + exportación literal de celdas
uv run python -m cg_01.fpa.marts   # estados, marts y el pronóstico 2030
uv run pytest -q                     # 74 tests
```

Visite `outputs/markdown/` para el exportación literal celda por celda y
`dashboard/FPA_Case_Study.Report/` para el informe Power BI PBIR.

---

## Transparencia

Este es un **caso de estudio anonimizado construido sobre un simulador de negocio competitivo**, no datos de cliente ni las cuentas de una empresa real. La marca del simulador y la identidad de los otros equipos se han eliminado; el origen se declara porque afirmarlo lo contrario sería trivialmente refutable.

Lo que demuestra es el método: convertir los libros de cierre en bruto en un modelo financiero auditable, encontrar dónde se fue el dinero y probar que un pronóstico merece confianza antes de usarlo.

---

## Reproducirlo

```bash
uv sync --group dev
uv run python -m cg_01            # capa canónica + exportación literal de celdas
uv run python -m cg_01.fpa.marts  # estados, marts y el pronóstico 2030
uv run pytest -q                  # 74 tests
```

Dentro del repositorio: `outputs/markdown/` guarda una exportación literal celda a celda de
cada hoja, `notebooks/01_revision_matrices.ipynb` contiene la revisión exploratoria
de las matrices de origen, y `data/processed/` los marts que consume el dashboard.

Empezar por [`docs/README.md`](docs/README.md) para el método, el modelo de datos y
todas las limitaciones conocidas, o leer la versión inglesa en [`README.md`](README.md).

---

## Licencia

MIT - ver [LICENSE](LICENSE).