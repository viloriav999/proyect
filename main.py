"""Distribución mensual de tres plantas a seis ciudades mediante programación lineal."""

import csv
from pathlib import Path

import pulp

# Datos del proyecto. Las columnas corresponden a C1, C2, C3, C4, C5 y C6.
plantas = ["P1", "P2", "P3"]
ciudades = ["C1", "C2", "C3", "C4", "C5", "C6"]
capacidad = [500, 700, 800]
demanda_base = [250, 350, 400, 300, 200, 300]
costos = [
    [12, 15, 20, 18, 25, 30],
    [10, 14, 12, 16, 18, 22],
    [20, 18, 15, 10, 12, 14],
]

COSTO_REPORTADO = 28600


def resolver(titulo, factor):
    """Resuelve un escenario y devuelve su resumen y sus envíos óptimos."""
    print(f"\n{titulo}")
    print("-" * len(titulo))

    # El factor modifica la demanda mensual de cada ciudad y conserva las capacidades.
    demanda = [cantidad * factor for cantidad in demanda_base]
    modelo = pulp.LpProblem("Transporte", pulp.LpMinimize)
    origenes = range(len(plantas))
    destinos = range(len(ciudades))
    rutas = [(i, j) for i in origenes for j in destinos]
    # envio[i, j] representa la cantidad continua y no negativa de P_i a C_j.
    envio = modelo.add_variable_dicts("envio", rutas, lowBound=0)

    # Minimizar la suma de costo unitario por cantidad enviada en todas las rutas.
    modelo += pulp.lpSum(costos[i][j] * envio[i, j] for i, j in rutas)

    # Las salidas de cada planta tienen un máximo y las entregas a cada ciudad un mínimo.
    for i in origenes:
        modelo += pulp.lpSum(envio[i, j] for j in destinos) <= capacidad[i], f"capacidad_{plantas[i]}"

    for j in destinos:
        modelo += pulp.lpSum(envio[i, j] for i in origenes) >= demanda[j], f"demanda_{ciudades[j]}"

    resultado = modelo.solve(pulp.COIN_CMD(msg=False))
    estado = resultado.status_str
    print("Estado del modelo:", estado)
    print(f"Demanda mensual: {sum(demanda):.0f} unidades")
    print(f"Capacidad disponible: {sum(capacidad)} unidades")

    faltante = max(0, sum(demanda) - sum(capacidad))
    resumen = {
        "escenario": titulo, "estado": estado, "demanda_unidades": sum(demanda),
        "capacidad_unidades": sum(capacidad), "faltante_unidades": faltante,
        "costo_minimo_usd": None, "ahorro_usd": None,
    }
    detalle = []
    # Solo se publican valores de las variables si CBC confirmó una solución óptima.
    if estado != "Optimal":
        if faltante > 0:
            print(f"Faltan {faltante:.0f} unidades de capacidad.")
        print("No se genera un plan de envíos para este escenario.")
        return resumen, detalle

    total = pulp.value(modelo.objective)
    resumen["costo_minimo_usd"] = total
    print(f"Costo mínimo mensual: USD {total:,.0f}")
    if factor == 1:
        ahorro = COSTO_REPORTADO - total
        resumen["ahorro_usd"] = ahorro
        print(f"Costo mensual reportado: USD {COSTO_REPORTADO:,.0f}")
        print(f"Ahorro estimado: USD {ahorro:,.0f} ({100 * ahorro / COSTO_REPORTADO:.2f} %)")

    print("\nAsignación óptima en unidades")
    print(f"{'Planta':<8}" + "".join(f"{c:>6}" for c in ciudades) + f"{'Total':>8}")
    for i, planta in enumerate(plantas):
        fila = [envio[i, j].value() for j in destinos]
        detalle.extend((titulo, planta, ciudades[j], fila[j], costos[i][j]) for j in destinos)
        print(f"{planta:<8}" + "".join(f"{v:6g}" for v in fila)
              + f"{sum(fila):8g}")

    return resumen, detalle


def main():
    escenarios = [
        resolver("PRUEBA 1. DISTRIBUCIÓN MENSUAL ACTUAL OPTIMIZADA", 1.0),
        resolver("PRUEBA 2. AUMENTO DEL 15 % EN LA DEMANDA", 1.15),
    ]
    carpeta = Path(__file__).resolve().parent / "resultados"
    carpeta.mkdir(exist_ok=True)
    campos_resumen = escenarios[0][0].keys()
    with (carpeta / "resumen.csv").open("w", encoding="utf-8-sig", newline="") as archivo:
        tabla = csv.DictWriter(archivo, fieldnames=campos_resumen)
        tabla.writeheader()
        tabla.writerows(resumen for resumen, _ in escenarios)

    with (carpeta / "envios.csv").open("w", encoding="utf-8-sig", newline="") as archivo:
        tabla = csv.writer(archivo)
        tabla.writerow(["escenario", "planta", "ciudad", "unidades", "costo_unitario_usd"])
        for _, detalle in escenarios:
            tabla.writerows(detalle)
    print(f"\nArchivos CSV guardados en {carpeta}")


if __name__ == "__main__":
    main()
