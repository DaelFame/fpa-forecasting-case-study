import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

import modelo as M

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(REPO_ROOT, "outputs", "modelo_r4", "Modelo_Spain10_Ronda4.xlsx")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

AZUL = "1F3864"
GRIS = "F2F2F2"
AMAR = "FFF2CC"
VERDE = "E2EFDA"
ROJO = "FCE4EC"
BLANCO = "FFFFFF"

H = Font(color="FFFFFF", bold=True, size=11)
HB = PatternFill("solid", fgColor=AZUL)
BOLD = Font(bold=True)
TITLE = Font(bold=True, size=14, color=AZUL)
SUB = Font(italic=True, size=9, color="595959")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")

wb = openpyxl.Workbook()


def head(ws, row, cols, widths=None):
    for i, c in enumerate(cols, start=1):
        cell = ws.cell(row=row, column=i, value=c)
        cell.font = H
        cell.fill = HB
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    if widths:
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w


def section(ws, row, text, ncols=6):
    c = ws.cell(row=row, column=1, value=text)
    c.font = BOLD
    c.fill = PatternFill("solid", fgColor=GRIS)
    for i in range(1, ncols + 1):
        ws.cell(row=row, column=i).fill = PatternFill("solid", fgColor=GRIS)


def num(ws, r, c, v, fmt="#,##0", bold=False, fill=None):
    cell = ws.cell(row=r, column=c, value=v)
    cell.number_format = fmt
    cell.border = BOX
    if bold:
        cell.font = BOLD
    if fill:
        cell.fill = PatternFill("solid", fgColor=fill)
    return cell


# ============================== ESCENARIOS ==============================
VENTAS = [255000, 46000, 103000]   # produccion 115.000, venta esperada 103.000
comp, pyg_base, fin, bal = M.run(M.D["produccion"], VENTAS)
sold_mod = [int(x * 0.9) for x in M.D["produccion"]]
_, pyg_menos, _, bal_menos = M.run(M.D["produccion"], sold_mod)
_, pyg_todo, _, bal_todo = M.run(M.D["produccion"], M.D["produccion"])
_, pyg_cal90, _, bal_cal90 = M.run([255000, 46000, 90000], [255000, 46000, 90000])
_, pyg_cal40, _, bal_cal40 = M.run(M.D["produccion"], [255000, 46000, 40000])
_, pyg_cal130, _, bal_cal130 = M.run([255000, 46000, 130000], [255000, 46000, 130000])
L0 = pyg_base["local"]

# ============================== MERCADO / DEMANDA ==============================
MKT = {  # unidades vendidas total companias
    "Corbatas":   {2024: 1361528, 2025: 1367310, 2026: 1359745, 2027: 1321636, 2028: 1404819},
    "Bufandas":   {2024: 177317,  2025: 175322,  2026: 172553,  2027: 169362,  2028: 187758},
    "Calcetines": {2024: 193956,  2025: 195881,  2026: 197223,  2027: 191661,  2028: 242675},
}
DEM_MKT = {  # intencion de compra total mercado
    "Corbatas":   {2026: 1820000, 2027: 1830000, 2028: 1810000},
    "Bufandas":   {2026: 250000,  2027: 245000,  2028: 300000},
    "Calcetines": {2026: 260000,  2027: 270000,  2028: 320000},
}
VEN_EMP = {  # unidades vendidas Spain10
    "Corbatas":   {2024: 194504, 2025: 195330, 2026: 209805, 2027: 214885, 2028: 234538},
    "Bufandas":   {2024: 25331,  2025: 25046,  2026: 28902,  2027: 29976,  2028: 37815},
    "Calcetines": {2024: 27708,  2025: 27983,  2026: 32885,  2027: 40010,  2028: 88670},
}
DEM_EMP = {  # intencion de compra Spain10
    "Corbatas":   {2026: 311000, 2027: 274000, 2028: 325000},
    "Bufandas":   {2026: 40000,  2027: 37000,  2028: 100000},
    "Calcetines": {2026: 58000,  2027: 40000,  2028: 103000},
}
CAP_2029 = {"Corbatas": 255000, "Bufandas": 46000, "Calcetines": 150000}

# ============================== 00 LEE ME ==============================
ws = wb.active
ws.title = "00_Lee_me"
ws.column_dimensions["A"].width = 3
ws.column_dimensions["B"].width = 34
ws.column_dimensions["C"].width = 96

ws["B2"] = "Spain10 — Modelo de resultados Ronda 4 (2029)"
ws["B2"].font = TITLE
ws["B3"] = "Reconstruido desde los resultados reales 2024-2028 (Matriz 0 a Matriz 3). No es el presupuesto del simulador: es la logica contable aplicada a tus decisiones."
ws["B3"].font = SUB

rows = [
    ("QUE HACE", "Toma tus 6 modulos de decision de la Ronda 4 y calcula Cuenta de Resultados, Balance, Caja y el efecto en Patrimonio."),
    ("QUE NO HACE", "No proyecta la demanda: mide la demanda observada 2026-2028 (hoja 09) y usa la produccion como techo de venta. Donde hay mas demanda que fabrica, venderas lo que produzcas; donde no, el exceso queda en inventario."),
    ("POR QUE", "El simulador no publica formulas. La logica se ha reconstruido una a una contra los 5 ejercicios disponibles y cada supuesto lleva su fuente en la hoja 07."),
    ("BASE DE CALIBRACION", "Ejercicio 2028 (ultimo cerrado). Todo coste unitario, ratio y saldo arranca del dato real de 2028 y se mueve solo por la palanca que tu decision cambia."),
    ("PRECISION", "El modelo reproduce 2028 exactamente por construccion. Hacia delante el error esperado esta en el coste unitario: entre 2026 y 2028 ese coste cayo de forma no documentada (MP -13%, elaboracion -21% en corbatas). Se compensa con la sensibilidad de la hoja 06."),
    ("SALVEDAD 1", "El balance de 2028 del simulador no cuadra por 246.390 EUR (Total Activo 6.829.902 vs Patrimonio+Pasivo 7.076.292). Se arrastra como linea memorizada para que el balance cierre."),
    ("SALVEDAD 2", "El resultado neto del simulador es ANTES de impuestos. Aqui se calcula igual y se resta el 25% despues."),
    ("COMO USARLO", "Cambia solo las celdas amarillas de la hoja 01 y las unidades vendidas de la hoja 06. El resto son calculos. La hoja 10 tiene las 44 lineas del presupuesto con su formula exacta y su base real 2028. La hoja 11 mide el aporte aislado de cada decision."),
    ("DEMANDA", "La hoja 09 mide la demanda real de los ultimos tres ejercicios (intencion de compra) y la compara con lo que Spain10 pudo vender. No es una prediccion: es el techo observado. En 2029 corbatas y bufandas siguen limitadas por fabrica; calcetines es la unica linea con capacidad ociosa."),
]
r = 5
for k, v in rows:
    ws.cell(row=r, column=2, value=k).font = BOLD
    ws.cell(row=r, column=2).alignment = WRAP
    c = ws.cell(row=r, column=3, value=v)
    c.alignment = WRAP
    r += 1

r += 1
ws.cell(row=r, column=2, value="RESULTADO CENTRAL (ventas = produccion)").font = TITLE
r += 1
head(ws, r, ["", "Concepto", "Valor 2029"], [3, 34, 20])
resumen = [
    ("Ingresos", pyg_base["ingresos"]),
    ("Margen", pyg_base["margen"]),
    ("Resultado antes de impuestos", bal["rdo_neto"]),
    ("Resultado despues de impuestos", bal["rdo_desp"]),
    ("Patrimonio Neto", bal["pn"]),
    ("Total Activo", bal["activo"]),
    ("Caja final", bal["efectivo"]),
]
for k, v in resumen:
    r += 1
    ws.cell(row=r, column=2, value=k).border = BOX
    num(ws, r, 3, v, bold=True)

ws.cell(row=r + 2, column=2, value="Generado desde data/Matriz_General_0..3.xlsx + Bitacora_decisiones_2026..2028.json + decisiones Ronda 4 indicadas por el usuario.").font = SUB

# ============================== 01 DECISIONES ==============================
ws = wb.create_sheet("01_Decisiones")
head(ws, 1, ["Modulo", "Variable", "Valor", "Regla / rango", "Fuente"],
     [16, 34, 16, 34, 40])
d = [
    ("Ventas", "Precio corbatas (EUR)", 20.70, "+15% sobre 18,00", "Decision R4"),
    ("Ventas", "Precio bufandas (EUR)", 34.50, "+15% sobre 30,00", "Decision R4"),
    ("Ventas", "Precio calcetines (EUR)", 4.14, "+15% sobre 3,60", "Decision R4"),
    ("Ventas", "Descuento al canal (%)", 0.15, "7%-25%", "Decision R4"),
    ("Ventas", "Promocion corbatas (EUR)", 150000, "0-400.000", "Decision R4"),
    ("Ventas", "Promocion bufandas (EUR)", 100000, "0-400.000", "Decision R4"),
    ("Ventas", "Promocion calcetines (EUR)", 50000, "0-400.000", "Decision R4"),
    ("Ventas", "Incentivo equipo corbatas (%)", 0.04, "0%-12%", "Decision R4"),
    ("Ventas", "Incentivo equipo bufandas (%)", 0.04, "0%-12%", "Decision R4"),
    ("Ventas", "Incentivo equipo calcetines (%)", 0.04, "0%-12%", "Decision R4"),
    ("Producto", "Amplitud gama corbatas", 15, "1-25", "Decision R4"),
    ("Producto", "Amplitud gama bufandas", 8, "1-15", "Decision R4"),
    ("Producto", "Amplitud gama calcetines", 5, "1-10", "Decision R4"),
    ("Producto", "Materia prima corbatas", "Estandar", "Economica/Standar/Premium", "Decision R4"),
    ("Producto", "Materia prima bufandas", "Estandar", "Economica/Standar/Premium", "Decision R4"),
    ("Producto", "Materia prima calcetines", "Economica", "Economica/Standar/Premium", "Decision R4"),
    ("Producto", "Diseno corbatas (EUR)", 60000, "0-350.000", "Decision R4"),
    ("Producto", "Diseno bufandas (EUR)", 60000, "0-350.000", "Decision R4"),
    ("Producto", "Diseno calcetines (EUR)", 30000, "0-350.000", "Decision R4"),
    ("Produccion", "Produccion corbatas (uds)", 255000, "0-600.000", "Decision R4"),
    ("Produccion", "Produccion bufandas (uds)", 46000, "0-600.000", "Decision R4"),
    ("Produccion", "Produccion calcetines (uds)", 90000, "0-600.000", "Decision R4"),
    ("Produccion", "Capacidad corbatas (uds)", 255000, "235.000 + 20.000 nivel 1", "Matriz 3 + ampliacion R4"),
    ("Produccion", "Capacidad bufandas (uds)", 46000, "38.000 + 8.000 nivel 1", "Matriz 3 + ampliacion R4"),
    ("Produccion", "Capacidad calcetines (uds)", 150000, "nivel 2 vigente de 2028", "Matriz 3"),
    ("Produccion", "Mantenimiento (%)", 0.03, "1%-7%", "Decision R4"),
    ("Capex", "Ampliacion corbatas (EUR)", 140000, "nivel 1", "Decision R4"),
    ("Capex", "Ampliacion bufandas (EUR)", 120000, "nivel 1", "Decision R4"),
    ("Capex", "Ampliacion calcetines (EUR)", 0, "nivel 0", "Decision R4"),
    ("Capex", "Planta fotovoltaica (EUR)", 145000, "-33% energia", "Decision R4"),
    ("Capex", "Modernizacion corbatas (EUR)", 250000, "-20% elaboracion", "Decision R4"),
    ("Capex", "Modernizacion calcetines (EUR)", 25000, "-20% elaboracion", "Decision R4"),
    ("Otros proyectos", "Venta solar anexo - caja (EUR)", 415000, "entrada", "Decision R4"),
    ("Otros proyectos", "Venta solar anexo - valor libros (EUR)", 220000, "baja de terrenos", "Decision R4"),
    ("Financiacion", "Cancelacion prestamo LP (EUR)", 296649, "saldo vivo 2028", "Matriz 3 H11 B22"),
    ("Financiacion", "Prestamo LP nuevo (EUR)", 0, "sin deuda nueva", "Decision R4"),
    ("Financiacion", "Prestamo CP nuevo (EUR)", 0, "sin deuda nueva", "Decision R4"),
    ("Financiacion", "Dividendos (%)", 0.0, "0%-100%", "Decision R4"),
    ("Inversiones", "Deuda publica LP (EUR)", 300000, "max 1.200.000 a 2 anios", "Decision R4"),
    ("Inversiones", "Deuda publica CP T1 (EUR)", 0, "max 500.000/trimestre", "Decision R4"),
    ("Inversiones", "Deuda publica CP T2 (EUR)", 500000, "max 500.000/trimestre", "Decision R4"),
    ("Inversiones", "Deuda publica CP T3 (EUR)", 500000, "max 500.000/trimestre", "Decision R4"),
    ("Inversiones", "Deuda publica CP T4 (EUR)", 500000, "max 500.000/trimestre", "Decision R4"),
    ("Acuerdo", "Calcetines acuerdo - unidades", 60000, "acuerdo 2028", "Decision R4"),
    ("Acuerdo", "Calcetines acuerdo - precio (EUR)", 3.00, "precio pactado", "Decision R4"),
]
r = 2
for mod, var, val, rng, src in d:
    ws.cell(row=r, column=1, value=mod).border = BOX
    ws.cell(row=r, column=2, value=var).border = BOX
    c = ws.cell(row=r, column=3, value=val)
    c.fill = PatternFill("solid", fgColor=AMAR)
    c.border = BOX
    if isinstance(val, float) and val < 1:
        c.number_format = "0.0%"
    elif isinstance(val, (int, float)):
        c.number_format = "#,##0"
    ws.cell(row=r, column=4, value=rng).border = BOX
    ws.cell(row=r, column=5, value=src).border = BOX
    r += 1

# ============================== 02 COSTES ==============================
ws = wb.create_sheet("02_Costes_Unitarios")
head(ws, 1, ["Componente", "Corbatas", "Bufandas", "Calcetines", "Como se calcula", "Palanca aplicada"],
     [30, 14, 14, 14, 62, 34])
filas = [
    ("Base 2028 - Materia prima", M.BASE["mp"], "Dato real 2028 (Hoja 4, fila 54)", "Sin cambio de proveedor"),
    ("Base 2028 - Elaboracion", M.BASE["elab"], "Dato real 2028 (fila 55)", "-20% corbatas y calcetines"),
    ("Base 2028 - Energia", M.BASE["energia"], "Dato real 2028 (fila 56)", "-33% planta fotovoltaica"),
    ("Base 2028 - Personal", M.BASE["personal"], "Dato real 2028 (fila 57)", "Coste fijo / nuevas unidades"),
    ("Base 2028 - Indirecto", M.BASE["indirecto"], "Coste fab. total - directo (fila 21 - 58)", "Fijo fabrica / unidades"),
]
r = 2
for nom, vals, como, pal in filas:
    ws.cell(row=r, column=1, value=nom).border = BOX
    for i, v in enumerate(vals):
        num(ws, r, 2 + i, v, "0.000")
    ws.cell(row=r, column=5, value=como).border = BOX
    ws.cell(row=r, column=6, value=pal).border = BOX
    r += 1
section(ws, r, "COSTE UNITARIO 2029 RESULTANTE", 6)
r += 1
for nom, key, como in [
    ("Materia prima", "mp", "Base x 1,00 (mismo proveedor)"),
    ("Elaboracion", "elab", "Base x 0,80 / 1,00 / 0,80"),
    ("Energia", "energia", "Base x 0,67"),
    ("Personal", "personal", "Base x (produccion 2028 / produccion 2029)"),
    ("Indirecto", "indirecto", "(fijo 2028 + nueva amortizacion) / produccion"),
    ("Subtotal directo", "directo", "Suma de los cuatro primeros"),
    ("COSTE FABRICACION", "total", "Directo + indirecto"),
]:
    ws.cell(row=r, column=1, value=nom).font = BOLD if nom in ("Subtotal directo", "COSTE FABRICACION") else Font()
    ws.cell(row=r, column=1).border = BOX
    for i, v in enumerate(comp[key]):
        num(ws, r, 2 + i, v, "0.000", bold=nom in ("Subtotal directo", "COSTE FABRICACION"),
            fill=VERDE if nom in ("Subtotal directo", "COSTE FABRICACION") else None)
    ws.cell(row=r, column=5, value=como).border = BOX
    r += 1
r += 1
ws.cell(row=r, column=1, value="Comparativa: 2028 real = 6,20 / 10,73 / 2,76").font = SUB
r += 1
ws.cell(row=r, column=1, value="Amortizacion nueva: 10% de 680.000 de capex = 68.000 EUR/anio. Entra en el coste unitario (indirectos de fabrica), NO en la linea de gastos de depreciacion, que es la de la central (138.000).").font = SUB

# ============================== 03 PyG ==============================
ws = wb.create_sheet("03_PyG_2029")
head(ws, 1, ["Linea", "2028 real", "2029 modelo", "Variacion", "Variacion %", "Como se calcula"],
     [34, 15, 15, 15, 11, 52])
p28 = [
    ("Ingresos totales", 5107811), ("Coste de las ventas", 2200596), ("Margen", 2907215),
    ("Gastos de marketing", 220000), ("Gastos de personal", 704498), ("Gastos I+D", 238440),
    ("Gastos de depreciacion", 138000), ("Dotaciones insolvencias", 24281),
    ("Gastos generales", 235925), ("Total gastos de operacion", 1561144),
    ("Resultado bruto", 1346071), ("Ingresos financieros", 13001),
    ("Gastos financieros", 28919), ("Resultado financiero", -15918),
    ("Resultados extraordinarios", 323000), ("Resultado antes de impuestos", 1653153),
    ("Impuestos", 413288), ("Resultado despues de impuestos", 1239865),
]
p29 = [
    ("Ingresos totales", pyg_base["ingresos"]),
    ("Coste de las ventas", pyg_base["coste_ventas"]),
    ("Margen", pyg_base["margen"]),
    ("Gastos de marketing", pyg_base["local"]["marketing"]),
    ("Gastos de personal", pyg_base["local"]["personal"]),
    ("Gastos I+D", pyg_base["local"]["id"]),
    ("Gastos de depreciacion", pyg_base["local"]["dep"]),
    ("Dotaciones insolvencias", pyg_base["local"]["insol"]),
    ("Gastos generales", pyg_base["local"]["generales"]),
    ("Total gastos de operacion", pyg_base["total_gastos"]),
    ("Resultado bruto", pyg_base["rdo_bruto"]),
    ("Ingresos financieros", fin["ing_fin"]),
    ("Gastos financieros", fin["gto_fin"]),
    ("Resultado financiero", fin["rdo_fin"]),
    ("Resultados extraordinarios", 195000),
    ("Resultado antes de impuestos", bal["rdo_neto"]),
    ("Impuestos", bal["impuestos"]),
    ("Resultado despues de impuestos", bal["rdo_desp"]),
]
como = [
    "Unidades vendidas x precio neto (precio x 0,85)",
    "Fab. unitario x vendidas + logistica + almacen + no calidad",
    "Ingresos - coste de las ventas",
    "Suma de la promocion decidida (300.000)",
    "Personal 2028 x 1,03 (IPC 2029)",
    "Otras I+D 2028 x 1,03 + presupuesto de diseno (150.000)",
    "138.000 de depreciacion de la central, sin cambios: la de fabrica ya va dentro del coste unitario",
    "0,5% de los ingresos",
    "Generales 2028 x 1,03 + delta de comisiones (3,5/4/3,5 -> 4/4/4)",
    "Suma de los seis gastos anteriores",
    "Margen - total gastos",
    "500.000 de deuda publica LP al 6,5% + CP por trimestres",
    "LP 296.649 al 6,6% solo el T1 (se cancela) + CP 329.108 al 5,9% medio anio",
    "Ingresos - gastos financieros",
    "Plusvalia solar anexo: 415.000 - 220.000",
    "Resultado bruto + financiero + extraordinario",
    "25% del resultado antes de impuestos",
    "Resultado antes de impuestos - impuestos",
]
r = 2
for (n1, v1), (n2, v2), cm in zip(p28, p29, como):
    ws.cell(row=r, column=1, value=n1).border = BOX
    num(ws, r, 2, v1)
    num(ws, r, 3, v2, bold=n1.startswith("Resultado despues"), fill=VERDE if n1.startswith("Resultado despues") else None)
    num(ws, r, 4, v2 - v1)
    c = ws.cell(row=r, column=5, value=(v2 - v1) / abs(v1) if v1 else None)
    c.number_format = "0.0%"
    c.border = BOX
    ws.cell(row=r, column=6, value=cm).border = BOX
    r += 1

# ============================== 04 BALANCE ==============================
ws = wb.create_sheet("04_Balance_2029")
head(ws, 1, ["Linea", "2028 real", "2029 modelo", "Variacion", "Como se calcula"],
     [34, 15, 15, 15, 56])
b28 = [
    ("Inmovilizado material bruto", 5923000), ("Inmovilizado intangible", 770000),
    ("Terrenos", 1305000), ("Depreciacion acumulada", 3856950), ("Activo fijo neto", 4141050),
    ("Participaciones", 305000), ("Activos financieros LP", 200000), ("Total no corriente", 4646050),
    ("Activos financieros CP", 0), ("Inventario", 65965), ("Clientes", 456410),
    ("Efectivo", 1661477), ("Descuadre de origen 2028 (memorando)", 0),
    ("Total corriente", 2183852), ("TOTAL ACTIVO", 6829902),
    ("Capital", 2802686), ("Reservas", 1777962), ("Resultado del ejercicio", 1239865),
    ("Patrimonio Neto", 5820513), ("Prestamo LP", 296649), ("Prestamo CP", 329108),
    ("Impuestos pendientes", 413288), ("Proveedores", 216734), ("Total pasivo", 1255779),
    ("TOTAL PASIVO + PN", 6829902),
]
b29 = [
    ("Inmovilizado material bruto", bal["im_bruto"]), ("Inmovilizado intangible", 770000),
    ("Terrenos", bal["terrenos"]), ("Depreciacion acumulada", bal["dep_acum"]),
    ("Activo fijo neto", bal["af_neto"]), ("Participaciones", 305000),
    ("Activos financieros LP", bal["af_lp"]), ("Total no corriente", bal["no_cte"]),
    ("Activos financieros CP", bal["af_cp"]), ("Inventario", bal["inventario"]),
    ("Clientes", bal["clientes"]), ("Efectivo", bal["efectivo"]),
    ("Descuadre de origen 2028 (memorando)", bal["memo"]),
    ("Total corriente", bal["activo_cte"] + bal["memo"]), ("TOTAL ACTIVO", bal["activo"]),
    ("Capital", 2802686), ("Reservas", bal["reservas"]),
    ("Resultado del ejercicio", bal["rdo_desp"]), ("Patrimonio Neto", bal["pn"]),
    ("Prestamo LP", 0), ("Prestamo CP", 0),
    ("Impuestos pendientes", bal["impuestos"]), ("Proveedores", bal["proveedores"]),
    ("Total pasivo", bal["pasivo"]), ("TOTAL PASIVO + PN", bal["pn"] + bal["pasivo"]),
]
bcomo = [
    "2028 + 680.000 de capex", "Sin cambios", "2028 - 220.000 (venta solar anexo)",
    "2028 + 138.000 de amortizacion (central)", "Material + intangible - amortizacion + terrenos",
    "Sin cambios", "200.000 anteriores + 300.000 nuevos", "Suma",
    "T1 0 + T2 500.000 + T3 500.000 + T4 500.000", "Sin cambios (se vende la produccion)",
    "8,94% de los ingresos (dias de cobro 2028)", "Cuadre del balance",
    "El balance 2028 publicado suma 6.829.902 de activo pero 7.076.292 de PN+pasivo: los 246.390 se arrastran aqui desde 2029",
    "AF CP + inventario + clientes + caja + memorando", "No corriente + corriente",
    "Sin cambios", "2028 + resultado 2028", "Resultado despues de impuestos 2029",
    "Capital + reservas + resultado", "Cancelado integramente", "Amortizado al vencimiento",
    "25% del resultado 2029", "9,85% del coste de las ventas", "Suma", "Debe igualar el activo",
]
r = 2
for (n1, v1), (n2, v2), cm in zip(b28, b29, bcomo):
    ws.cell(row=r, column=1, value=n1).border = BOX
    num(ws, r, 2, v1)
    num(ws, r, 3, v2, bold=n1.startswith("TOTAL"), fill=VERDE if n1.startswith("TOTAL") else None)
    num(ws, r, 4, v2 - v1)
    ws.cell(row=r, column=5, value=cm).border = BOX
    r += 1
r += 1
ws.cell(row=r, column=1, value="Memorandum: el balance 2028 publicado no cuadra por 246.390 EUR (activo 6.829.902 vs PN+pasivo 7.076.292). Se arrastra como diferencia no explicada; no afecta a los flujos del periodo.").font = SUB

# ============================== 05 CAJA ==============================
ws = wb.create_sheet("05_Caja_2029")
head(ws, 1, ["Concepto", "Importe", "Detalle"], [40, 16, 66])
caja = [
    ("Caja inicial 2028", 1661477, "Matriz 3 Hoja 11 B15"),
    ("+ Resultado despues de impuestos", bal["rdo_desp"], "03_PyG"),
    ("- Plusvalia solar anexo (no es caja)", -195000, "Se cobra en la linea de inversion"),
    ("+ Amortizacion", bal["dep_acum"] - 3856950, "No es salida de caja"),
    ("- Aumento de clientes", -(bal["clientes"] - 456410), "45 dias de cobro"),
    ("+ Aumento de impuestos pendientes", bal["impuestos"] - 413288, "Se devenga y se paga al anio siguiente"),
    ("+ Aumento de proveedores", bal["proveedores"] - 216734, "45 dias de pago"),
    ("- Aumento de inventario", -(bal["inventario"] - 65965), "Solo si produces mas de lo que vendes"),
    ("Flujo de explotacion", bal["flujo_op"], ""),
    ("- Capex ampliaciones y proyectos", -680000, "140k + 120k + 145k + 250k + 25k"),
    ("+ Venta solar anexo", 415000, "Entrada de caja"),
    ("- Deuda publica LP", -300000, "Inversion financiera"),
    ("- Deuda publica CP (3 trimestres)", -1500000, "500.000 x 3"),
    ("Flujo de inversion", bal["flujo_inv"], ""),
    ("- Cancelacion prestamo LP", -296649, "Deuda bancaria a cero"),
    ("- Amortizacion prestamo CP", -329108, "Vencimiento 1 anio"),
    ("- Dividendos", 0, "0% decidido"),
    ("Flujo de financiacion", bal["flujo_fin"], ""),
    ("CAJA FINAL 2029", bal["efectivo"], "Caja inicial + los tres flujos. Coincide con el balance."),
]
r = 2
for nom, val, det in caja:
    bold = nom.startswith("Flujo") or nom.startswith("CAJA")
    ws.cell(row=r, column=1, value=nom).font = BOLD if bold else Font()
    ws.cell(row=r, column=1).border = BOX
    num(ws, r, 2, val, bold=bold, fill=VERDE if nom.startswith("CAJA") else None)
    ws.cell(row=r, column=3, value=det).border = BOX
    r += 1
r += 1
ws.cell(row=r, column=1, value="La caja se obtiene tambien como cuadre del balance y las dos vias coinciden al euro. El descuadre de origen de 2028 (246.390 EUR) se arrastra como linea memorizada en la hoja 04.").font = SUB
r += 1
ws.cell(row=r, column=1, value=f"Aviso: 1.800.000 EUR inmovilizados en deuda publica dejan la caja en {bal['efectivo']:,.0f} EUR, frente a 1.661.477 de 2028.").font = SUB

# ============================== 06 SENSIBILIDAD ==============================
ws = wb.create_sheet("06_Sensibilidad")
head(ws, 1, ["Escenario", "Unidades vendidas (C/B/Ca)", "Ingresos", "Margen", "Rdo. antes imp.", "Rdo. despues imp.", "Caja final", "Inventario cierre", "Patrimonio"],
     [42, 22, 14, 14, 15, 15, 14, 15, 14])
esc = [
    ("A. Plan: 115.000 fabricadas, 103.000 vendidas", "255.000 / 46.000 / 103.000", pyg_base, bal),
    ("B. El mercado absorbe las 115.000", "255.000 / 46.000 / 115.000", pyg_todo, bal_todo),
    ("C. El acuerdo no sigue: solo 40.000 salen", "255.000 / 46.000 / 40.000", pyg_cal40, bal_cal40),
    ("D. Calcetines a 90.000 (decision anterior)", "255.000 / 46.000 / 90.000", pyg_cal90, bal_cal90),
    ("E. Calcetines: demanda crece con el mercado (130k)", "255.000 / 46.000 / 130.000", pyg_cal130, bal_cal130),
    ("F. Demanda -10% en todas las lineas", "229.500 / 41.400 / 81.000", pyg_menos, bal_menos),
]
r = 2
for nom, u, p, b in esc:
    ws.cell(row=r, column=1, value=nom).border = BOX
    ws.cell(row=r, column=2, value=u).border = BOX
    num(ws, r, 3, p["ingresos"])
    num(ws, r, 4, p["margen"])
    num(ws, r, 5, b["rdo_neto"])
    num(ws, r, 6, b["rdo_desp"])
    num(ws, r, 7, b["efectivo"])
    num(ws, r, 8, b["inventario"])
    num(ws, r, 9, b["pn"])
    r += 1
r += 1
ws.cell(row=r, column=1, value="Los escenarios A-C mantienen la produccion decidida; solo cambia lo que se vende. En C y D el exceso queda en inventario y caduca en el ejercicio siguiente.").font = SUB
r += 2
ws.cell(row=r, column=1, value="Sensibilidad al coste unitario (escenario base)").font = BOLD
r += 1
head(ws, r, ["Coste unitario", "Coste de ventas", "Resultado antes imp.", "Resultado despues imp.", "Caja final"])
for delta in (-0.10, -0.05, 0.0, 0.05, 0.10):
    r += 1
    cv = pyg_base["coste_ventas"] * (1 + delta)
    margen = pyg_base["ingresos"] - cv
    rb = margen - pyg_base["total_gastos"]
    rn = rb + fin["rdo_fin"] + 195000
    imp = max(0, rn) * 0.25
    caja = bal["efectivo"] + (rn - imp) - bal["rdo_desp"]
    ws.cell(row=r, column=1, value=f"{delta:+.0%}").border = BOX
    num(ws, r, 2, cv)
    num(ws, r, 3, rn)
    num(ws, r, 4, rn - imp)
    num(ws, r, 5, caja)

# ============================== 09 MERCADO Y DEMANDA ==============================
ws = wb.create_sheet("09_Mercado_Demanda")
ws.column_dimensions["A"].width = 30
for col in "BCDEFGHI":
    ws.column_dimensions[col].width = 14

ws["A1"] = "Que pide el mercado: intencion de compra frente a ventas reales"
ws["A1"].font = TITLE
ws["A2"] = "Fuente: pestana Mercado de Matriz General 0, 1, 2 y 3. La intencion de compra es la demanda disponible; la diferencia con las ventas es demanda que nadie sirvio, normalmente por falta de producto."
ws["A2"].font = SUB

r = 4
section(ws, r, "1. UNIDADES VENDIDAS DEL MERCADO COMPLETO", 6)
r += 1
head(ws, r, ["Producto", "2024", "2025", "2026", "2027", "2028", "Var. 27-28"])
for prod in ["Corbatas", "Bufandas", "Calcetines"]:
    r += 1
    ws.cell(row=r, column=1, value=prod).border = BOX
    for i, y in enumerate([2024, 2025, 2026, 2027, 2028], start=2):
        num(ws, r, i, MKT[prod][y])
    c = ws.cell(row=r, column=7, value=MKT[prod][2028] / MKT[prod][2027] - 1)
    c.number_format = "0.0%"
    c.border = BOX

r += 2
section(ws, r, "2. DEMANDA NO SERVIDA DEL MERCADO (intencion de compra vs ventas)", 7)
r += 1
head(ws, r, ["Producto / anio", "Intencion", "Ventas", "Sin servir", "Cumplimiento"])
for y in [2026, 2027, 2028]:
    for prod in ["Corbatas", "Bufandas", "Calcetines"]:
        r += 1
        ws.cell(row=r, column=1, value=f"{prod} {y}").border = BOX
        num(ws, r, 2, DEM_MKT[prod][y])
        num(ws, r, 3, MKT[prod][y])
        num(ws, r, 4, DEM_MKT[prod][y] - MKT[prod][y])
        c = ws.cell(row=r, column=5, value=MKT[prod][y] / DEM_MKT[prod][y])
        c.number_format = "0.0%"
        c.border = BOX

r += 2
section(ws, r, "3. SPAIN10: QUE DEMANDA TENIA Y QUE PUDO VENDER", 8)
r += 1
head(ws, r, ["Producto / anio", "Demanda", "Ventas", "Sin servir", "Captacion", "Cuota mercado"])
for y in [2026, 2027, 2028]:
    for prod in ["Corbatas", "Bufandas", "Calcetines"]:
        r += 1
        ws.cell(row=r, column=1, value=f"{prod} {y}").border = BOX
        num(ws, r, 2, DEM_EMP[prod][y])
        num(ws, r, 3, VEN_EMP[prod][y])
        num(ws, r, 4, DEM_EMP[prod][y] - VEN_EMP[prod][y])
        c = ws.cell(row=r, column=5, value=VEN_EMP[prod][y] / DEM_EMP[prod][y])
        c.number_format = "0.0%"
        c.border = BOX
        c = ws.cell(row=r, column=6, value=VEN_EMP[prod][y] / MKT[prod][y])
        c.number_format = "0.0%"
        c.border = BOX

r += 2
section(ws, r, "4. 2029: CAPACIDAD DECIDIDA FRENTE A LA DEMANDA DE 2028", 6)
r += 1
head(ws, r, ["Producto", "Demanda 2028", "Capacidad 2029", "Produccion 2029", "Hueco vs demanda", "Lectura"])
for prod in ["Corbatas", "Bufandas", "Calcetines"]:
    r += 1
    dem = DEM_EMP[prod][2028]
    cap = CAP_2029[prod]
    pr = M.D["produccion"][["Corbatas", "Bufandas", "Calcetines"].index(prod)]
    ws.cell(row=r, column=1, value=prod).border = BOX
    num(ws, r, 2, dem)
    num(ws, r, 3, cap)
    num(ws, r, 4, pr)
    num(ws, r, 5, pr - dem, bold=True)
    if cap < dem:
        lectura = "Limitado por fabrica: la demanda supera la capacidad"
    elif pr < dem:
        lectura = "Capacidad ociosa y demanda sin atender"
    else:
        lectura = "Produccion alineada con la demanda"
    ws.cell(row=r, column=6, value=lectura).border = BOX

r += 2
section(ws, r, "5. LECTURA DE CALCETINES (lo que preguntaste)", 6)
r += 1
txt = [
    ("El mercado crece", "Calcetines es la unica linea que crece de forma sostenida: 193.956 unidades en 2024, 197.223 en 2026 y 242.675 en 2028 (+26,6% en el ultimo anio). Corbatas y bufandas llevan cuatro anios planas o a la baja."),
    ("Pero el salto es tuyo", "De esas 242.675 unidades, 88.670 son de Spain10. El mercado sin Spain10 pasa de 151.651 a 154.005: +2.354 unidades (+1,6%). El resto del crecimiento del mercado lo aporta tu propio acuerdo comercial."),
    ("La demanda no servida es real", "En 2028 el mercado pidio 320.000 calcetines y vendio 242.675: quedaron 77.325 sin servir. Spain10 pidio 103.000 y vendio 88.670: 13.000 que no pudo atender, no que rechazo."),
    ("Quedan 35.000 unidades de capacidad sin usar", "Con 115.000 fabricadas y una capacidad de 150.000, hay 35.000 unidades de margen sin invertir un euro. Pero cada 1.000 pares que no se venden se quedan en almacen: 1.117 EUR de coste y 0,73 EUR de caja inmovilizada por unidad."),
    ("El riesgo no es el precio, es el volumen", "Si el acuerdo no se renueva y la demanda vuelve a 40.000, produces 50.000 de mas: quedan en inventario por 138.423 EUR y caducan. Ese es el escenario C de la hoja 06."),
    ("Corbatas y bufandas son el problema contrario", "En 2028 la demanda fue 325.000 corbatas y 100.000 bufandas, y solo pudiste fabricar 235.000 y 38.000. Pierdes 90.000 y 62.000 unidades de venta por falta de fabrica, no por falta de mercado. La ampliacion de un nivel no cierra ese hueco."),
]
for k, v in txt:
    ws.cell(row=r, column=1, value=k).font = BOLD
    ws.cell(row=r, column=1).alignment = WRAP
    c = ws.cell(row=r, column=2, value=v)
    c.alignment = WRAP
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 44
    r += 1

r += 1
ws.cell(row=r, column=1, value="Aviso: la intencion de compra no es una prediccion. Es la demanda que el simulador registro en cada ejercicio con los precios, descuento, promocion y cobertura de distribucion de ese anio. En 2029 la cobertura de distribucion puede cambiar y con ella la demanda.").font = SUB
ws.cell(row=r, column=1).alignment = WRAP

# ============================== 07 TRAZABILIDAD ==============================
ws = wb.create_sheet("07_Trazabilidad")
head(ws, 1, ["Concepto", "2026", "2027", "2028", "Regla aplicada en 2029", "Fuente"],
     [36, 14, 14, 14, 52, 34])
tr = [
    ("Coste MP corbatas", 1.01, 1.30, 1.13, "Sin cambio: mismo proveedor", "Hoja 4 fila 54"),
    ("Coste MP bufandas", 2.72, 3.20, 2.75, "Sin cambio", "Hoja 4 fila 54"),
    ("Coste MP calcetines", 0.27, 0.26, 0.22, "Sin cambio", "Hoja 4 fila 54"),
    ("Elaboracion corbatas", 1.11, 1.02, 0.88, "-20% por modernizacion", "Hoja 4 fila 55"),
    ("Elaboracion bufandas", 2.41, 2.31, 1.99, "Sin cambio", "Hoja 4 fila 55"),
    ("Elaboracion calcetines", 0.17, 0.15, 0.15, "-20% por modernizacion", "Hoja 4 fila 55"),
    ("Coste fabricacion corbatas", 7.44, 7.42, 6.20, "Recalculo por componentes", "Hoja 4 fila 21"),
    ("Coste fabricacion bufandas", 12.79, 12.57, 10.73, "Recalculo por componentes", "Hoja 4 fila 21"),
    ("Coste fabricacion calcetines", 3.59, 3.16, 2.76, "Recalculo por componentes", "Hoja 4 fila 21"),
    ("Gastos personal", 678298, 712458, 704498, "2028 x 1,03 (IPC)", "Hoja 10"),
    ("Gastos I+D", 249240, 218190, 238440, "Otras I+D x 1,03 + diseno", "Hoja 10"),
    ("Gastos generales", 344808, 266090, 235925, "2028 x 1,03 + delta comisiones", "Hoja 10"),
    ("Depreciacion", 148000, 136750, 138000, "+10% del capex nuevo", "Hoja 10"),
    ("Clientes / ingresos", 0.0892, 0.0891, 0.0894, "8,94% de los ingresos", "Hoja 11 fila 14"),
    ("Proveedores / coste ventas", 0.1083, 0.1025, 0.0985, "9,85% del coste de ventas", "Hoja 11 fila 26"),
    ("Tipo impositivo efectivo", 0.0, 0.113, 0.25, "25%", "Hoja 10 filas 47-48"),
]
r = 2
for nom, v26, v27, v28, regla, src in tr:
    ws.cell(row=r, column=1, value=nom).border = BOX
    for i, v in enumerate([v26, v27, v28], start=2):
        c = ws.cell(row=r, column=i, value=v)
        c.number_format = "0.000" if isinstance(v, float) and abs(v) < 100 else "#,##0"
        c.border = BOX
    ws.cell(row=r, column=5, value=regla).border = BOX
    ws.cell(row=r, column=6, value=src).border = BOX
    r += 1
r += 1
ws.cell(row=r, column=1, value="Aviso de precision: el coste unitario cae de forma no documentada entre 2026 y 2028 (-21% en elaboracion de corbatas). El modelo NO extrapola esa caida: si se repite, el resultado mejora; si se revierte, empeora. Ver sensibilidad en hoja 06.").font = SUB

# ============================== 08 ALERTAS ==============================
ws = wb.create_sheet("08_Alertas")
head(ws, 1, ["#", "Alerta", "Por que importa", "Que revisar"], [5, 60, 60, 46])
al = [
    (1, "Calcetines: el acuerdo NO aplico precio de 3,00 EUR en 2028. Se corrige el modelo.",
     "El precio neto realizado en 2028 fue 3,24 = 3,60 x 0,90 exacto (287.291 / 88.670). Si 60.000 uds hubieran ido a 3,00, el ingreso habria sido 272.891. El acuerdo actua como volumen, no como descuento.",
     "Verificar en Otros Proyectos de Ronda 4 si el acuerdo sigue vigente."),
    (2, "Tu calculo de ingresos usa 235.000 / 38.000 vendidas, pero la fabrica hara 255.000 / 46.000.",
     "No es sobreproduccion: en 2028 la demanda de corbatas fue 325.000 y la de bufandas 100.000, y la fabrica solo pudo hacer 235.000 y 38.000. Con la ampliacion, 255.000 y 46.000 se venden y sobran 70.000 y 54.000 de demanda sin atender. Tu calculo subestima los ingresos en 586.500 EUR.",
     "Sustituir 235.000 / 38.000 por la produccion real en el calculo de ventas."),
    (3, "Deuda publica CP por 1.500.000 EUR.",
     f"Es el 24% de los ingresos y deja la caja en {bal['efectivo']:,.0f} EUR frente a 1.661.477 de 2028. Si la demanda cae un 10% y produces igual, la caja baja a {bal_menos['efectivo']:,.0f} EUR.",
     "Ver escenario E de la hoja 06."),
    (4, "Cancelacion anticipada del prestamo LP: no se declara comision.",
     "El simulador puede aplicar una penalizacion por cancelacion anticipada. No hay dato en el proyecto para cuantificarla.",
     "Comprobar en la pantalla de Financiacion si aparece comision."),
    (5, "Mantenimiento al 3%: no tiene efecto numerico modelado.",
     "El proyecto solo describe el efecto cualitativamente. Se ha dejado fuera del calculo; el coste aparece via amortizacion, no via mantenimiento.",
     "Sin accion: el 3% no altera la PyG en el modelo."),
    (6, "El balance 2028 publicado no cuadra por 246.390 EUR.",
     "Total activo 6.829.902 frente a Patrimonio+Pasivo 7.076.292. Todas las proyecciones de patrimonio arrastran esa diferencia.",
     "Es un defecto del fichero, no de las decisiones."),
    (7, "Depreciacion de fabrica: 68.000 EUR nuevos sobre 680.000 de capex (10%).",
     "La Matriz 3 separa la depreciacion de la fabrica (294.050 en 2028, dentro del coste unitario) de la de la central (138.000, linea de la PyG). El capex nuevo es todo de fabrica: sube el coste unitario, no la linea de gastos. Si el simulador la imputara tambien a gastos, el resultado seria 51.000 EUR menor.",
     "Contrastar en el primer cierre real."),
    (8, "Tipo impositivo 25% sobre todo el beneficio.",
     "2027 pago el 11,3% y 2026 el 0% (compensacion de perdidas). Si quedan bases negativas, el impuesto sera menor.",
     "Revisar si la pantalla de impuestos muestra bases pendientes."),
    (9, "Ingresos financieros calculados a 6,5% (LP) y 4,5% (CP).",
     "El tipo de la deuda publica no aparece en el proyecto; se deduce de 2028 (13.001 sobre 200.000 = 6,5%).",
     "Confirmar el tipo en la pantalla de Inversiones Financieras."),
]
r = 2
for n, a, b, c in al:
    ws.cell(row=r, column=1, value=n).border = BOX
    ws.cell(row=r, column=2, value=a).alignment = WRAP
    ws.cell(row=r, column=3, value=b).alignment = WRAP
    ws.cell(row=r, column=4, value=c).alignment = WRAP
    ws.row_dimensions[r].height = 46
    r += 1

# ============================== 10 DESGLOSE EXACTO ==============================
ws = wb.create_sheet("10_Desglose_Exacto")
head(ws, 1, ["Bloque", "Linea", "Importe 2029", "Como se calcula (formula exacta)", "Base real 2028"],
     [16, 34, 16, 74, 22])

com28 = 0.035 * M.REV_2028[0] + 0.04 * M.REV_2028[1] + 0.035 * M.REV_2028[2]
com29 = sum(M.D["incentivo"][i] * L0["ingreso_prod"][i] for i in range(3))
filas = [
    ("Ingresos", "Corbatas", L0["ingreso_prod"][0], f"255.000 uds x 20,70 x 0,85 (descuento 15%) = 17,595 neto", 3799516),
    ("Ingresos", "Bufandas", L0["ingreso_prod"][1], f"46.000 uds x 34,50 x 0,85 = 29,325 neto", 1021005),
    ("Ingresos", "Calcetines", L0["ingreso_prod"][2], "103.000 uds x 4,14 x 0,85 = 3,519 neto (fabricadas 115.000)", 287291),
    ("Ingresos", "TOTAL INGRESOS", pyg_base["ingresos"], "Suma de las tres lineas", 5107811),

    ("Costes", "Coste fabricacion corbatas", L0["fab"][0], "255.000 uds x 5,805 EUR/ud (hoja 02)", 1454136),
    ("Costes", "Coste fabricacion bufandas", L0["fab"][1], "46.000 uds x 9,993 EUR/ud", 405755),
    ("Costes", "Coste fabricacion calcetines", L0["fab"][2], f"103.000 uds x {comp['total'][2]:.3f} EUR/ud", 244729),
    ("Costes", "Coste logistica externa", sum(L0["logistica"]), f"255.000x0,22 + 46.000x0,18 + 103.000x0,13", 69932),
    ("Costes", "Coste de almacenaje", sum(L0["almacenaje"]), "1,117 EUR por unidad que queda en stock: 20.402 uds al cierre (8.402 de 2028 + 12.000 sin vender)", 9385),
    ("Costes", "Coste de no calidad", sum(L0["no_calidad"]), "Fab x 0,8% / 1,1% / 0,6% por linea", 17564),
    ("Costes", "TOTAL COSTE DE VENTAS", pyg_base["coste_ventas"], "Fab + logistica + almacen + no calidad", 2200596),

    ("Gastos", "Marketing", L0["marketing"], "150.000 + 100.000 + 50.000 (decision R4)", 220000),
    ("Gastos", "Personal", L0["personal"], "704.498 x 1,03 (IPC 2029)", 704498),
    ("Gastos", "I+D", L0["id"], "Otras I+D 118.440 x 1,03 + diseno 150.000", 238440),
    ("Gastos", "Generales", L0["generales"], f"235.925 x 1,03 + (comisiones {com29:,.0f} - 183.878) = {L0['generales']:,.2f}", 235925),
    ("Gastos", "Depreciacion", L0["dep"], "138.000 de la central; la de fabrica (68.000 nuevos) va en el coste unitario", 138000),
    ("Gastos", "Dotaciones insolvencias", L0["insol"], "0,5% de los ingresos", 24281),
    ("Gastos", "TOTAL GASTOS", pyg_base["total_gastos"], "Suma de los seis gastos", 1561144),

    ("Resultados", "Margen", pyg_base["margen"], "Ingresos - coste de ventas", 2907215),
    ("Resultados", "Resultado bruto", pyg_base["rdo_bruto"], "Margen - total gastos", 1346071),
    ("Resultados", "Ingresos financieros", fin["ing_fin"], "500.000 x 6,5% (32.500) + 750.000 medio x 4,5% (33.750)", 13001),
    ("Resultados", "Gastos por intereses", fin["gto_fin"], "LP 296.649 x 6,6% x 0,25 + CP 329.108 x 5,9% x 0,5", 28919),
    ("Resultados", "Resultado financiero", fin["rdo_fin"], "Ingresos financieros - gastos por intereses", -15918),
    ("Resultados", "Resultados extraordinarios", 195000, "Venta solar anexo 415.000 - valor en libros 220.000", 323000),
    ("Resultados", "RESULTADO ANTES DE IMPUESTOS", bal["rdo_neto"], "Rdo bruto + rdo financiero + extraordinarios", 1653153),
    ("Resultados", "Impuestos", bal["impuestos"], "25% del resultado antes de impuestos", 413288),
    ("Resultados", "RESULTADO DESPUES DE IMPUESTOS", bal["rdo_desp"], "RAI - impuestos", 1239865),

    ("Activo no cte", "Activo fijo bruto", bal["im_bruto"], "5.923.000 + 680.000 de capex (140+120+145+250+25)", 5923000),
    ("Activo no cte", "Depreciacion acumulada", bal["dep_acum"], "3.856.950 + 138.000 del ejercicio", 3856950),
    ("Activo no cte", "Activos financieros LP", bal["af_lp"], "200.000 anteriores + 300.000 de deuda publica LP", 200000),
    ("Activo no cte", "Participaciones", 305000, "Sin movimiento", 305000),
    ("Activo no cte", "TOTAL ACTIVO NO CORRIENTE", bal["no_cte"], "AF neto + AF LP + participaciones", 4646050),

    ("Activo cte", "Clientes", bal["clientes"], "6.152.385 x 8,935% (ratio 2028: 456.410 / 5.107.811)", 456410),
    ("Activo cte", "Efectivo disponible", bal["efectivo"], "Cuadre del balance (ver hoja 05)", 1661477),
    ("Activo cte", "Activos financieros CP", bal["af_cp"], "0 + 500.000 x 3 trimestres", 0),
    ("Activo cte", "Inventario", bal["inventario"], "65.965 + (115.000 - 103.000) x 0,73 (coste directo)", 65965),
    ("Activo cte", "Descuadre de origen 2028 (memorando)", bal["memo"], "Gap del balance 2028 publicado: 6.829.902 de activo vs 7.076.292 de PN+pasivo", 0),
    ("Activo cte", "TOTAL ACTIVO CORRIENTE", bal["activo_cte"] + bal["memo"], "Clientes + efectivo + AF CP + inventario + memorando", 2183852),
    ("Activo cte", "TOTAL ACTIVO", bal["activo"], "No corriente + corriente (incluye 246.390 de memorando)", 6829902),

    ("PN y pasivo", "Proveedores", bal["proveedores"], "2.293.746 x 9,85% (ratio 2028: 216.734 / 2.200.596)", 216734),
    ("PN y pasivo", "Prestamos corto plazo", 0, "Amortizado integramente", 329108),
    ("PN y pasivo", "Prestamos largo plazo", 0, "Cancelacion anticipada de 296.649", 296649),
    ("PN y pasivo", "Capital", 2802686, "Sin ampliacion", 2802686),
    ("PN y pasivo", "Reservas", bal["reservas"], "1.777.962 + 1.239.865 (resultado 2028 retenido al 0% dividendos)", 1777962),
    ("PN y pasivo", "Resultado del ejercicio", bal["rdo_desp"], "Resultado despues de impuestos 2029", 1239865),
    ("PN y pasivo", "PATRIMONIO NETO", bal["pn"], "Capital + reservas + resultado", 5820513),
    ("PN y pasivo", "Impuestos pendientes", bal["impuestos"], "25% del RAI, se paga al anio siguiente", 413288),
    ("PN y pasivo", "TOTAL PATRIMONIO + PASIVO", bal["pn"] + bal["pasivo"], "PN + proveedores + impuestos + prestamos", 7076292),
]
r = 2
for bl, li, val, frm, base in filas:
    ws.cell(row=r, column=1, value=bl).border = BOX
    ws.cell(row=r, column=2, value=li).border = BOX
    bold = li.isupper() or li.startswith("TOTAL") or li.startswith("RESULTADO")
    num(ws, r, 3, val, bold=bold, fill=VERDE if bold else None)
    ws.cell(row=r, column=4, value=frm).border = BOX
    ws.cell(row=r, column=4).alignment = WRAP
    num(ws, r, 5, base)
    ws.row_dimensions[r].height = 26
    r += 1

r += 1
ws.cell(row=r, column=1, value="2029 frente a 2028: todas las lineas de gasto se actualizan con IPC 3% salvo marketing, diseno, depreciacion y comisiones, que nacen de decisiones explicitas.").font = SUB

# ============================== 11 DECISIONES IMPACTO ==============================
import copy as _copy


def _delta(**kw):
    base = _copy.deepcopy(M.D)
    M.D.update(kw)
    c, p, f, b = M.run(M.D["produccion"], VENTAS)
    M.D.clear(); M.D.update(base)
    return b["rdo_desp"] - bal["rdo_desp"], b["efectivo"] - bal["efectivo"]


def _delta_prod(prod, capex_amp=None):
    base = _copy.deepcopy(M.D)
    if capex_amp is not None:
        M.D["capex_ampliacion"] = capex_amp
    ventas = [min(prod[i], VENTAS[i]) for i in range(3)]
    c, p, f, b = M.run(prod, ventas)
    M.D.clear(); M.D.update(base)
    return b["rdo_desp"] - bal["rdo_desp"], b["efectivo"] - bal["efectivo"]

_neg = lambda t: (-t[0], -t[1])
AMP = _neg(_delta_prod([235000, 38000, 115000], [0, 0, 0]))
SOL = _neg(_delta(capex_solar=0))
MOD = _neg(_delta(capex_modernizacion=[0, 0, 0]))
VEN = _neg(_delta(venta_terreno_caja=0, venta_terreno_libros=0))
CAN = _neg(_delta(cancelacion_lp=0))
DLP = _neg(_delta(deuda_publica_lp=0))
DCP = _neg(_delta(deuda_publica_cp_trim=[0, 0, 0, 0]))
P90 = _neg(_delta(precio=[18.0, 30.0, 3.6]))
DSC = _neg(_delta(descuento=0.10))
PRO = _neg(_delta(promo=[120000, 80000, 20000]))
INC = _neg(_delta(incentivo=[0.035, 0.04, 0.035]))
DIS = _neg(_delta(diseno=[60000, 40000, 20000]))
def _delta_pv(prod, ventas):
    base = _copy.deepcopy(M.D)
    c, p, f, b = M.run(prod, ventas)
    M.D.clear(); M.D.update(base)
    return b["rdo_desp"] - bal["rdo_desp"], b["efectivo"] - bal["efectivo"]

CAL90 = _delta_pv([255000, 46000, 90000], [255000, 46000, 90000])
CAL115 = _neg(CAL90)
CAL115T = _delta_pv([255000, 46000, 115000], [255000, 46000, 115000])
CAL130 = _delta_pv([255000, 46000, 130000], [255000, 46000, 130000])
CAL150 = _delta_pv([255000, 46000, 150000], [255000, 46000, 150000])

ws = wb.create_sheet("11_Decisiones_Impacto")
head(ws, 1, ["Modulo", "Decision", "Aporte al resultado (RDI)", "Efecto en caja final", "Como funciona", "Veredicto"],
     [16, 40, 16, 15, 62, 34])
filas = [
    ("Ventas", "Precio +15%: 20,70 / 34,50 / 4,14", P90, "Precio neto x unidades. Con el 15% de descuento el neto sube 8,6%, no 15%.", "Mantener: es la que mas aporta, pero sin elasticidad medida"),
    ("Ventas", "Descuento al canal 15% (vs 10%)", DSC, "Cada punto de descuento son 45.000 EUR de ingresos netos.", "Revisar: cuesta 259.000 de resultado si no mueve volumen"),
    ("Ventas", "Promocion 300.000 (vs 220.000)", PRO, "Gasto fijo; no depende de las ventas.", "Caro: 80.000 de caja por 60.000 de resultado"),
    ("Ventas", "Incentivos 4/4/4 (vs 3,5/4/3,5)", INC, f"Comision sobre ingresos netos; el 4% son {com29:,.0f}.", "Mantener: 18.000 de coste"),
    ("Ventas", "Plazo de cobro 45 dias", (0, 0), "Sin cambio frente a 2028: el saldo real es 8,94% de la venta, no 12,5%.", "Mantener"),
    ("Producto", "Diseno 150.000 (vs 120.000)", DIS, "Gasto fijo en I+D; no se capitaliza.", "Mantener: 22.500 de coste"),
    ("Producto", "Gama 15/8/5 y materia prima", (0, 0), "Mismos multiplicadores que 2028; no mueve coste unitario.", "Mantener"),
    ("Produccion", "Ampliaciones de capacidad 260.000", AMP, "20.000 corbatas y 8.000 bufandas mas al anio; margen unitario 11,79 y 19,33.", "La mejor del plan: 334.000 de resultado"),
    ("Produccion", "Planta solar 145.000", SOL, "Energia -33% (35.831) menos 14.500 de amortizacion.", "Mantener: se paga en 4 anios"),
    ("Produccion", "Modernizacion 275.000", MOD, "Elaboracion -20% en corbatas y calcetines (47.580) menos 27.500 de amortizacion.", "Marginal: 15.000 de resultado por 275.000 de caja"),
    ("Produccion", "Mantenimiento 3%", (0, 0), "Misma tasa que 2028: no hay cambio ni efecto modelado.", "Sin impacto, pero es una palanca sin explorar"),
    ("Produccion", "Calcetines 115.000 (60.000 acuerdo + 55.000 catalogo)", CAL115, "Fabricar 115.000 y vender 103.000 deja 12.000 en almacen.", "Ojo: 12.000 pares a la espera y 35.000 de capacidad ociosa"),
    ("Otros", "Venta del solar anexo 415.000", VEN, "Plusvalia 195.000 y entrada de caja 415.000.", "Mantener: sin riesgo"),
    ("Financiacion", "Cancelar prestamo LP 296.649", CAN, "Ahorra 14.684 de intereses y consume 296.649 de caja.", "Solo si sobra caja: rinde 4,95% neto"),
    ("Financiacion", "Dividendos 0%", (0, 0), "Todo el beneficio a reservas.", "Mantener"),
    ("Inversiones", "Deuda publica LP 300.000 al 6,5%", DLP, "Renta fija a 2 anios; 19.500 al anio.", "Mantener: mejor que cancelar deuda"),
    ("Inversiones", "Deuda publica CP 1.500.000 al 4,5%", DCP, "500.000 en T2, T3 y T4; devenga medio anio.", "Es lo que deja la caja en 44 dias"),
]
r = 2
for mod, dec, (drdi, dcaja), mec, ver in filas:
    ws.cell(row=r, column=1, value=mod).border = BOX
    ws.cell(row=r, column=2, value=dec).border = BOX
    num(ws, r, 3, drdi, bold=abs(drdi) > 100000, fill=VERDE if drdi > 100000 else None)
    num(ws, r, 4, dcaja, bold=abs(dcaja) > 100000)
    c5 = ws.cell(row=r, column=5, value=mec); c5.border = BOX; c5.alignment = WRAP
    c6 = ws.cell(row=r, column=6, value=ver); c6.border = BOX; c6.alignment = WRAP
    ws.row_dimensions[r].height = 30
    r += 1

r += 1
ws.cell(row=r, column=1, value="VOLUMEN EXTRA DE CALCETINES (sin capex: la fabrica ya tiene 150.000 de capacidad)").font = BOLD
r += 1
for nom, (drdi, dcaja) in [("90.000 vendidas (decision anterior)", CAL90), ("115.000 fabricadas y vendidas", CAL115T), ("130.000 uds (demanda +26,6%)", CAL130), ("150.000 uds (tope de fabrica)", CAL150)]:
    ws.cell(row=r, column=2, value=nom).border = BOX
    num(ws, r, 3, drdi)
    num(ws, r, 4, dcaja)
    c5 = ws.cell(row=r, column=5, value="Cada 10.000 calcetines valen ~21.000 EUR despues de impuestos; el coste unitario baja al diluir la fabrica.")
    c5.alignment = WRAP; c5.border = BOX
    r += 1
r += 1
ws.cell(row=r, column=1, value="Efecto aislado de cada decision sobre el plan completo. En las decisiones de inversion la caja baja porque se convierte en activo (deuda publica, capex): no es una perdida.").font = SUB
r += 1
ws.cell(row=r, column=1, value="Las decisiones de precio y promocion se miden con el volumen dado: el modelo no estima elasticidad. Su valor real depende de que el mercado absorba el plan (hoja 09).").font = SUB

_i = wb.sheetnames.index("10_Desglose_Exacto")
wb.move_sheet("10_Desglose_Exacto", offset=len(wb.sheetnames) - 1 - _i)
_i = wb.sheetnames.index("09_Mercado_Demanda")
wb.move_sheet("09_Mercado_Demanda", offset=len(wb.sheetnames) - 2 - _i)
_i = wb.sheetnames.index("11_Decisiones_Impacto")
wb.move_sheet("11_Decisiones_Impacto", offset=len(wb.sheetnames) - 1 - _i)

for sh in wb.worksheets:
    sh.sheet_view.showGridLines = False
    sh.freeze_panes = "A2" if sh.title != "00_Lee_me" else None

wb.save(OUT)
print("OK", OUT)
print("Rdo 2029:", round(bal["rdo_desp"]), "Caja:", round(bal["efectivo"]), "PN:", round(bal["pn"]))
print("Esc -10%:", round(bal_menos["rdo_desp"]), round(bal_menos["efectivo"]))
print("Esc todo vendido:", round(bal_todo["rdo_desp"]), round(bal_todo["efectivo"]))
