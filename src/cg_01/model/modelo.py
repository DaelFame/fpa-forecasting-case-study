"""Motor de simulacion Spain10 - reconstruido desde los resultados 2024-2028."""

PRODUCTOS = ["Corbatas", "Bufandas", "Calcetines"]

# ---------- Base calibrada en 2028 (unico anio con desglose completo) ----------
BASE = {
    "mp":        [1.13, 2.75, 0.22],
    "elab":      [0.88, 1.99, 0.15],
    "energia":   [0.32, 0.43, 0.08],
    "personal":  [2.38, 4.12, 0.43],
    "indirecto": [1.49, 1.53, 1.88],   # = coste fab unit - directo
}
PROD_2028 = [235000, 38000, 90000]
CAP_2028 = [235000, 38000, 150000]
SOLD_2028 = [234538, 37815, 88670]
INV_2028_U = [5438, 880, 2084]
REV_2028 = [3799516, 1021005, 287291]
FIXED_FAB = [b * p for b, p in zip(BASE["indirecto"], PROD_2028)]  # coste fijo fabrica por linea

# ---------- Decisiones Ronda 4 (2029) ----------
D = dict(
    precio=[20.70, 34.50, 4.14],
    descuento=0.15,
    promo=[150000, 100000, 50000],
    incentivo=[0.04, 0.04, 0.04],
    gama=[15, 8, 5],
    diseno=[60000, 60000, 30000],
    proveedor=["Estandar", "Estandar", "Economica"],
    produccion=[255000, 46000, 115000],
    capacidad=[255000, 46000, 150000],
    mantenimiento=0.03,
    capex_ampliacion=[140000, 120000, 0],
    capex_solar=145000,
    capex_modernizacion=[250000, 0, 25000],
    venta_terreno_caja=415000,
    venta_terreno_libros=220000,
    compra_lp_anterior=[200000],
    deuda_publica_lp=300000,
    deuda_publica_cp_trim=[0, 500000, 500000, 500000],
    prestamo_lp_nuevo=0,
    prestamo_cp_nuevo=0,
    cancelacion_lp=296649,
    dividendos=0.0,
    acuerdo_calcetines_uds=60000,
    acuerdo_calcetines_precio=3.00,
)

IPC = 0.03
TIPO_IMPUESTO = 0.25
RATIO_CLIENTES = 0.08935
RATIO_PROVEEDORES = 0.0985
MEMO_DESCUADRE = 246390
TIPO_LP = 0.066
TIPO_CP = 0.059
RENT_DEUDA_LP = 0.05625      # manual: devengo anual 5,625% sobre 500.000 (200.000 + 300.000)
RENT_DEUDA_CP = 0.0405       # manual: devengo trimestral 4,05% sobre cada colocacion de 500.000

# ---------- 2028 de partida ----------
P2028 = dict(
    ingresos=5107811, coste_ventas=2200596, margen=2907215,
    marketing=220000, personal=704498, id=238440, dep=138000,
    insolvencias=24281, generales=235925, total_gastos=1561144,
    rdo_bruto=1346071, ing_fin=13001, gto_fin=28919, rdo_fin=-15918,
    extraordinario=323000, rdo_neto=1653153, impuestos=413288, rdo_desp=1239865,
    im_bruto=5923000, intangible=770000, dep_acum=3856950, terrenos=1305000,
    af_neto=4141050, participaciones=305000, af_lp=200000, af_cp=0,
    inventario=65965, clientes=456410, efectivo=1661477, total_cte=2183852,
    activo=6829902, capital=2802686, reservas=1777962, pn=5820513,
    lp=296649, cp=329108, extra=0, imp_pend=413288, proveedores=216734,
    total_pc=959130, total_pasivo=1255779,
)


def costes_unitarios(prod, prod_base):
    """Coste unitario de fabricacion 2029 aplicando las palancas decididas."""
    elab_f = [0.80 if D["capex_modernizacion"][i] > 0 else 1.00 for i in range(3)]
    ener_f = [0.67 if D["capex_solar"] > 0 else 1.00 for i in range(3)]
    mp_f = [1.00, 1.00, 1.00]            # mismo proveedor que 2028
    per = [BASE["personal"][i] * prod_base[i] / prod[i] for i in range(3)]

    # nueva depreciacion por linea (10% del capex) + solar repartida por unidades
    dep_linea = [c * 0.10 for c in D["capex_ampliacion"]]
    dep_linea = [dep_linea[i] + D["capex_modernizacion"][i] * 0.10 for i in range(3)]
    total_prod = sum(prod)
    dep_solar = [D["capex_solar"] * 0.10 * prod[i] / total_prod for i in range(3)]
    fijo = [FIXED_FAB[i] + dep_linea[i] + dep_solar[i] for i in range(3)]
    ind = [fijo[i] / prod[i] for i in range(3)]

    comp = {
        "mp": [BASE["mp"][i] * mp_f[i] for i in range(3)],
        "elab": [BASE["elab"][i] * elab_f[i] for i in range(3)],
        "energia": [BASE["energia"][i] * ener_f[i] for i in range(3)],
        "personal": per,
        "indirecto": ind,
    }
    comp["directo"] = [comp["mp"][i] + comp["elab"][i] + comp["energia"][i] + comp["personal"][i] for i in range(3)]
    comp["total"] = [comp["directo"][i] + comp["indirecto"][i] for i in range(3)]
    comp["fijo"] = fijo
    return comp


def pyg(prod, vendidas, precios, descuento, comp, promo, incentivo, diseno,
        dep_total, insol_pct=0.005, gen_base=None, id_otros=118440):
    neto = [precios[i] * (1 - descuento) for i in range(3)]
    acuerdo_u = min(D["acuerdo_calcetines_uds"], vendidas[2])
    ingreso_prod = [
        vendidas[0] * neto[0],
        vendidas[1] * neto[1],
        vendidas[2] * neto[2],
    ]
    ingresos = sum(ingreso_prod)

    fab = [comp["total"][i] * vendidas[i] for i in range(3)]
    logistica = [vendidas[i] * [0.22, 0.18, 0.13][i] for i in range(3)]
    # Almacenaje: se paga por lo que queda en stock (documentado en Hoja 4).
    # 2028: 9.385 EUR sobre 8.402 unidades en inventario = 1,117 EUR/ud.
    inv_u = [INV_2028_U[i] + prod[i] - vendidas[i] for i in range(3)]
    almacenaje = [max(0.0, u) * 1.117 for u in inv_u]
    no_calidad = [fab[i] * [0.008, 0.011, 0.006][i] for i in range(3)]
    coste_ventas = sum(fab) + sum(logistica) + sum(almacenaje) + sum(no_calidad)

    marketing = sum(promo)
    personal = P2028["personal"] * (1 + IPC)
    id_total = id_otros * (1 + IPC) + sum(diseno)
    dep = P2028["dep"] + dep_total
    insol = ingresos * insol_pct
    comisiones_28 = 0.035 * REV_2028[0] + 0.04 * REV_2028[1] + 0.035 * REV_2028[2]
    comisiones_29 = sum(incentivo[i] * ingreso_prod[i] for i in range(3))
    gen_base = P2028["generales"] * (1 + IPC) if gen_base is None else gen_base
    generales = gen_base + (comisiones_29 - comisiones_28)

    total_gastos = marketing + personal + id_total + dep + insol + generales
    margen = ingresos - coste_ventas
    rdo_bruto = margen - total_gastos
    return dict(local=dict(ingreso_prod=ingreso_prod, neto=neto, fab=fab, logistica=logistica,
                           almacenaje=almacenaje, no_calidad=no_calidad, marketing=marketing,
                           personal=personal, id=id_total, dep=dep, insol=insol,
                           generales=generales, comisiones=comisiones_29),
                ingresos=ingresos, coste_ventas=coste_ventas, margen=margen,
                total_gastos=total_gastos, rdo_bruto=rdo_bruto)


def financiero(af_lp_ini, af_lp_nuevo, cp_trim, lp_ini, cp_ini):
    ing_lp = (af_lp_ini + af_lp_nuevo) * RENT_DEUDA_LP
    # Manual: las colocaciones CP vencen a los 3 meses y el principal vuelve a caja.
    # Cada colocacion devenga un trimestre completo: importe x 4,05% x 3/12.
    ing_cp = sum(cp_trim) * RENT_DEUDA_CP * 0.25
    cancelado = D["cancelacion_lp"]
    # Manual: el prestamo CP (329.108) se amortiza al inicio del Q1 y el LP se cancela
    # anticipadamente en el Q1. La deuda bancaria queda a cero y no devenga interes en 2029.
    gto_lp = 0.0
    gto_cp = 0.0
    return dict(ing_lp=ing_lp, ing_cp=ing_cp, ing_fin=ing_lp + ing_cp,
                gto_lp=gto_lp, gto_cp=gto_cp, gto_fin=gto_lp + gto_cp,
                rdo_fin=ing_lp + ing_cp - gto_lp - gto_cp)


def balance(p, fin, comp, inv_delta=None):
    # resultado
    rdo_neto = p["rdo_bruto"] + fin["rdo_fin"] + (D["venta_terreno_caja"] - D["venta_terreno_libros"])
    impuestos = max(0.0, rdo_neto) * TIPO_IMPUESTO
    rdo_desp = rdo_neto - impuestos

    capex = sum(D["capex_ampliacion"]) + D["capex_solar"] + sum(D["capex_modernizacion"])
    im_bruto = P2028["im_bruto"] + capex
    terrenos = P2028["terrenos"] - D["venta_terreno_libros"]
    dep_acum = P2028["dep_acum"] + p["local"]["dep"]
    af_neto = im_bruto + P2028["intangible"] - dep_acum + terrenos

    af_lp = P2028["af_lp"] + D["deuda_publica_lp"]
    no_cte = af_neto + P2028["participaciones"] + af_lp

    # Manual: Q2, Q3 y Q4 vencen dentro del ejercicio, el principal vuelve a caja.
    # Al 31/12/2029 no queda ninguna colocacion CP abierta.
    af_cp = 0.0
    inventario = P2028["inventario"]
    if inv_delta is not None:
        # inventario valorado a coste directo (verificado en 2028: 25.831/5.438 = 4,75 ~ directo 4,71)
        inventario += sum(inv_delta[i] * comp["directo"][i] for i in range(3))
    clientes = p["ingresos"] * RATIO_CLIENTES
    capex = sum(D["capex_ampliacion"]) + D["capex_solar"] + sum(D["capex_modernizacion"])

    reservas = P2028["reservas"] + P2028["rdo_desp"] * (1 - D["dividendos"])
    pn = P2028["capital"] + reservas + rdo_desp
    proveedores = p["coste_ventas"] * RATIO_PROVEEDORES
    pasivo_cte = impuestos + proveedores
    pasivo = pasivo_cte + (P2028["lp"] - D["cancelacion_lp"])

    activo_sin_caja = no_cte + inventario + clientes + af_cp + MEMO_DESCUADRE
    efectivo = pn + pasivo - activo_sin_caja
    activo = activo_sin_caja + efectivo
    activo_cte = inventario + clientes + af_cp + efectivo
    memo = MEMO_DESCUADRE

    # estado de flujos (comprobacion independiente)
    flujo_op = (rdo_desp - (D["venta_terreno_caja"] - D["venta_terreno_libros"])
                + p["local"]["dep"] - (clientes - P2028["clientes"])
                + (impuestos - P2028["imp_pend"]) + (proveedores - P2028["proveedores"])
                - (inventario - P2028["inventario"]))
    flujo_inv = -capex + D["venta_terreno_caja"] - D["deuda_publica_lp"] - af_cp
    flujo_fin = -D["cancelacion_lp"] - P2028["cp"]
    flujo_neto = flujo_op + flujo_inv + flujo_fin
    caja_check = P2028["efectivo"] + flujo_neto
    return dict(inv_delta=inv_delta, memo=memo, af_cp=af_cp, rdo_neto=rdo_neto, impuestos=impuestos, rdo_desp=rdo_desp, capex=capex,
                im_bruto=im_bruto, terrenos=terrenos, dep_acum=dep_acum, af_neto=af_neto,
                af_lp=af_lp, no_cte=no_cte, inventario=inventario, clientes=clientes,
                efectivo=efectivo, activo_cte=activo_cte, activo=activo, reservas=reservas,
                pn=pn, proveedores=proveedores, pasivo_cte=pasivo_cte, pasivo=pasivo,
                flujo_op=flujo_op, flujo_inv=flujo_inv, flujo_fin=flujo_fin,
                flujo_neto=flujo_neto, caja_check=caja_check,
                descuadre=activo - (pn + pasivo), dif_caja=efectivo - caja_check)


def cp_ini_repay():
    return P2028["cp"]


def run(prod, vendidas):
    comp = costes_unitarios(prod, PROD_2028)
    # La depreciacion de la nueva inversion de fabrica ya entra en el coste unitario
    # (Hoja 4: los indirectos de fabricacion incluyen la depreciacion de la fabrica).
    # La linea "Gastos de depreciacion" de la PyG es la de la central (138.000) y no cambia.
    dep_central = 0.0
    p = pyg(prod, vendidas, D["precio"], D["descuento"], comp, D["promo"],
            D["incentivo"], D["diseno"], dep_central)
    fin = financiero(P2028["af_lp"], D["deuda_publica_lp"], D["deuda_publica_cp_trim"],
                     P2028["lp"], P2028["cp"])
    inv_delta = [prod[i] - vendidas[i] for i in range(3)]
    b = balance(p, fin, comp, inv_delta)
    return comp, p, fin, b


if __name__ == "__main__":
    comp, p, fin, b = run(D["produccion"], D["produccion"])
    print("== COSTE UNITARIO 2029 ==")
    for k in ["mp", "elab", "energia", "personal", "indirecto", "directo", "total"]:
        print(f"{k:12s}", " | ".join(f"{v:8.3f}" for v in comp[k]))
    print("\n== PyG 2029 ==")
    for k, v in [("Ingresos", p["ingresos"]), ("Coste ventas", p["coste_ventas"]),
                 ("Margen", p["margen"]), ("Marketing", p["local"]["marketing"]),
                 ("Personal", p["local"]["personal"]), ("I+D", p["local"]["id"]),
                 ("Depreciacion", p["local"]["dep"]), ("Insolvencias", p["local"]["insol"]),
                 ("Generales", p["local"]["generales"]), ("Total gastos", p["total_gastos"]),
                 ("Rdo bruto", p["rdo_bruto"]), ("Rdo financiero", fin["rdo_fin"]),
                 ("Extraordinario", 195000), ("Rdo neto", b["rdo_neto"]),
                 ("Impuestos", b["impuestos"]), ("Rdo despues", b["rdo_desp"])]:
        print(f"{k:16s} {v:14,.0f}")
    print("\n== BALANCE 2029 ==")
    for k in ["im_bruto", "terrenos", "dep_acum", "af_neto", "no_cte", "inventario",
              "clientes", "efectivo", "activo", "pn", "pasivo", "descuadre",
              "flujo_op", "flujo_inv", "flujo_fin", "flujo_neto", "dif_caja"]:
        print(f"{k:16s} {b[k]:14,.0f}")
