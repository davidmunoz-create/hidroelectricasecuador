#!/usr/bin/env python3
"""
Descarga la hidrología y la producción de las centrales de CELEC (Mazar, Molino,
Sopladora, Minas San Francisco, Agoyán, Manduriacu y Coca Codo Sinclair) y regenera:

    data/hidrologia-diario.csv    data/hidrologia-mensual.csv
    data/produccion-diario.csv    data/produccion-mensual.csv

con el mismo formato del botón "Descargar CSV" de
https://generacioncsr.celec.gob.ec/graficasproduccionCELEC/index.html

Uso:
    python scripts/actualizar.py              # día y mes actuales
    python scripts/actualizar.py 2026-10-13   # un día concreto (y su mes)

Solo usa la biblioteca estándar de Python 3.8 o superior.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = "https://generacioncsr.celec.gob.ec:8443/ords/csr/"
ECUADOR = timezone(timedelta(hours=-5))
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# Códigos de medición de CELEC, comprobados contra sus propios CSV.
# Mensual: los caudales son el promedio del día y las cotas, el valor de la hora 24.
HIDROLOGIA = [
    ("CaudalMaz", 30538, "caudal"),
    ("CotaMaz", 30031, "cota"),
    ("CaudalMol", 24811, "caudal"),
    ("CotaMol", 24019, "cota"),
    ("CaudalSop", 90537, "caudal"),
    ("CotaSop", 90919, "cota"),
    ("CaudalMsf", 650538, "caudal"),
    ("CotaMsf", 650919, "cota"),
    ("CaudalCuencaPaute", 24812, "cuenca"),
    ("CaudalAgo", 140537, "caudal"),
    ("CotaAgo", 140031, "cota"),
    ("CaudalMan", 110537, "caudal"),
    ("CotaMan", 110031, "cota"),
    ("CaudalCCS", 100037, "caudal"),
    ("CotaCCS", 100540, "cota"),
]

# Energía: servicio propio de cada central. Unidades en línea: código de medición.
ENERGIA = {
    "Maz": "sardommaz/mazEner", "Mol": "sardommol/molEner", "Sop": "sardomsop/sopEner",
    "Msf": "sardommsf/msfEner", "Csr": "sardomcsr/csrEner", "Ago": "sardomago/agoEner",
    "Man": "sardomman/manEner", "CCS": "sardomccs/ccsEner",
}
UNIDADES = {"Maz": 30503, "Mol": 44822, "Sop": 90503, "Msf": 650503, "Ago": 140503, "Man": 110503, "CCS": 100503}
PROD_DIARIO = ["EnergiaMaz", "UnidadesMaz", "EnergiaMol", "UnidadesMol", "EnergiaSop", "UnidadesSop",
               "EnergiaMsf", "UnidadesMsf", "EnergiaCsr", "EnergiaAgo", "UnidadesAgo",
               "EnergiaMan", "UnidadesMan", "EnergiaCCS", "UnidadesCCS"]
PROD_MENSUAL = ["EnergiaMaz", "EnergiaMol", "EnergiaSop", "EnergiaMsf", "EnergiaCsr",
                "EnergiaAgo", "EnergiaMan", "EnergiaCCS"]


def iso_utc(d):
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def consultar(ruta, params, intentos=3):
    """Devuelve {fecha local sin zona: valor} para un servicio de CELEC."""
    url = BASE + ruta + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (visualizador hidroelectricas)",
        "Accept": "application/json",
        "Origin": "https://generacioncsr.celec.gob.ec",
        "Referer": "https://generacioncsr.celec.gob.ec/graficasproduccionCELEC/index.html",
    })
    ultimo_error = None
    for i in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                items = json.loads(r.read().decode("utf-8")).get("items", [])
            salida = {}
            for it in items:
                t = datetime.strptime(it["loctimestamp"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                salida[t.astimezone(ECUADOR).replace(tzinfo=None)] = it.get("valueedit")
            return salida
        except Exception as e:  # noqa: BLE001
            ultimo_error = e
            time.sleep(5 * (i + 1))
    raise RuntimeError("No se pudo consultar %s: %s" % (ruta, ultimo_error))


def rango(inicio, fin, mrid=None):
    p = {"fechaInicio": iso_utc(inicio), "fechaFin": iso_utc(fin), "fecha": inicio.strftime("%d/%m/%Y %H:%M:%S")}
    if mrid is not None:
        p["mrid"] = mrid
    return p


def escribir(nombre, columnas, filas):
    """filas: lista de (fecha, {columna: valor}), de la más reciente a la más antigua."""
    lineas = ["Fecha," + ",".join(columnas)]
    for fecha, valores in filas:
        celdas = []
        for col in columnas:
            v = valores.get(col)
            celdas.append("" if v is None else repr(float(v)).rstrip("0").rstrip("."))
        lineas.append('"%s",%s' % (fecha.strftime("%d/%m/%Y %H:%M:%S"), ",".join(celdas)))
    ruta = os.path.join(CARPETA, nombre)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    print("Escrito", ruta)


def tiene_datos(filas):
    return any(v is not None for _, valores in filas for v in valores.values())


def horas_del_dia(dia):
    inicio = datetime(dia.year, dia.month, dia.day, 1, tzinfo=ECUADOR)
    return inicio, inicio + timedelta(days=1), [(inicio + timedelta(hours=h)).replace(tzinfo=None) for h in range(24)]


def dias_del_mes(dia):
    inicio = datetime(dia.year, dia.month, 1, 1, tzinfo=ECUADOR)
    fin = datetime(dia.year + (dia.month == 12), dia.month % 12 + 1, 1, 1, tzinfo=ECUADOR)
    dias, d = [], datetime(dia.year, dia.month, 1)
    while d.month == dia.month:
        dias.append(d)
        d += timedelta(days=1)
    return inicio, fin, dias


def armar(fechas, series, columnas):
    filas = [(f, {c: series[c].get(f) for c in columnas}) for f in fechas]
    return list(reversed(filas))


def hidrologia_diaria(dia):
    inicio, fin, horas = horas_del_dia(dia)
    series = {col: consultar("sardomcsr/pointValues", rango(inicio, fin, mrid)) for col, mrid, _ in HIDROLOGIA}
    return armar(horas, series, [c for c, _, _ in HIDROLOGIA])


def hidrologia_mensual(dia):
    inicio, fin, dias = dias_del_mes(dia)
    servicio = {"caudal": "pointValuesMesAvg", "cota": "pointValuesMesH24", "cuenca": "csrCaudCuenMesAvg"}
    series = {}
    for col, mrid, tipo in HIDROLOGIA:
        series[col] = consultar("sardomcsr/" + servicio[tipo], rango(inicio, fin, None if tipo == "cuenca" else mrid))
    return armar(dias, series, [c for c, _, _ in HIDROLOGIA])


def produccion_diaria(dia):
    inicio, fin, horas = horas_del_dia(dia)
    fecha = {"fecha": dia.strftime("%d/%m/%Y 00:00:00")}
    series = {}
    for c, ruta in ENERGIA.items():
        series["Energia" + c] = consultar(ruta + "Dia", fecha)
    for c, mrid in UNIDADES.items():
        series["Unidades" + c] = consultar("sardomcsr/pointValues", rango(inicio, fin, mrid))
    return armar(horas, series, PROD_DIARIO)


def produccion_mensual(dia):
    _, _, dias = dias_del_mes(dia)
    fecha = {"fecha": dia.strftime("%d/%m/%Y 00:00:00")}
    series = {"Energia" + c: consultar(ruta + "Mes", fecha) for c, ruta in ENERGIA.items()}
    return armar(dias, series, PROD_MENSUAL)


def main():
    if len(sys.argv) > 1:
        dia = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
        forzado = True
    else:
        dia = datetime.now(ECUADOR).date()
        forzado = False

    h_dia = hidrologia_diaria(dia)
    # Entre la medianoche y la 01:00 todavía no hay registros del día: se usa el anterior.
    if not tiene_datos(h_dia) and not forzado:
        dia = dia - timedelta(days=1)
        h_dia = hidrologia_diaria(dia)
    if not tiene_datos(h_dia):
        print("CELEC no devolvió datos para el %s; no se modifica nada." % dia)
        return 0

    escribir("hidrologia-diario.csv", [c for c, _, _ in HIDROLOGIA], h_dia)
    pasos = [
        ("hidrologia-mensual.csv", [c for c, _, _ in HIDROLOGIA], hidrologia_mensual),
        ("produccion-diario.csv", PROD_DIARIO, produccion_diaria),
        ("produccion-mensual.csv", PROD_MENSUAL, produccion_mensual),
    ]
    fallos = 0
    for nombre, columnas, funcion in pasos:
        try:
            filas = funcion(dia)
            if tiene_datos(filas):
                escribir(nombre, columnas, filas)
        except Exception as e:  # noqa: BLE001
            fallos += 1
            print("Aviso: no se actualizó %s (%s)" % (nombre, e))
    return 1 if fallos == len(pasos) else 0


if __name__ == "__main__":
    sys.exit(main())
