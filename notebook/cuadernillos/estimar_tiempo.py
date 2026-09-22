#!/usr/bin/env python3
"""Estima cuánto dura un cuadernillo, a partir de lo que de verdad tiene dentro.

    python3 notebook/cuadernillos/estimar_tiempo.py            # todos
    python3 notebook/cuadernillos/estimar_tiempo.py semana_03   # uno

Por qué existe: los minutos que anuncia cada sección estaban escritos a mano y
se quedaron viejos. Tras recortar las semanas 3 a 6 en la fase 5 seguían
diciendo lo de antes —la semana 3 anunciaba 153 minutos para un cuadernillo de
seis ejercicios—, y el profesor lo leyó en pantalla en la reunión del
2026-09-22: «aquí dice 55 minutos, esto es lo que podemos bajarle».

Un número escrito a mano envejece en cuanto alguien toca el contenido. Este sale
del contenido, así que no puede quedarse viejo sin que nadie lo note.

EL MÉTODO, dicho en voz alta para que se pueda discutir:

  - Leer .......... 200 palabras por minuto. Es ritmo de lectura técnica con
                    comprensión, no de novela.
  - Ejecutar ...... 0,5 min por celda de código no calificable: leerla,
                    ejecutarla y mirar la salida.
  - Resolver ...... por dificultad, medida sobre los cuadernillos que ya se
                    hicieron: 1★=4 min, 2★=7, 3★=11, 4★=15.

No pretende ser exacto: pretende ser HONESTO y moverse cuando el contenido se
mueve. Si un cuadernillo anuncia 40 minutos y en clase cuesta 70, lo que hay que
ajustar son estas constantes, aquí, una vez.
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(AQUI, "..", "notebook_semana")

PALABRAS_POR_MINUTO = 200
MIN_POR_CELDA_CODIGO = 0.5
MIN_POR_ESTRELLAS = {1: 4, 2: 7, 3: 11, 4: 15}


def _estrellas(texto):
    """El constructor escribe la dificultad como ★☆☆☆ en el enunciado."""
    llenas = texto.count("★")
    return llenas if 1 <= llenas <= 4 else 2


def estimar(ruta_ipynb):
    with open(ruta_ipynb, encoding="utf-8") as f:
        return estimar_nb(json.load(f))


def estimar_nb(nb):
    """Lo mismo, sobre un cuadernillo ya cargado. Lo usa build.py para avisar
    en el momento de construir, que es cuando todavía se puede arreglar."""
    palabras = 0
    celdas_codigo = 0
    ejercicios = []

    for celda in nb["cells"]:
        fuente = "".join(celda.get("source", []))
        ng = celda.get("metadata", {}).get("nbgrader", {})
        etiquetas = celda.get("metadata", {}).get("tags", []) or []

        if celda["cell_type"] == "markdown":
            if re.search(r"^### Ejercicio \d+", fuente, re.M):
                ejercicios.append(_estrellas(fuente))
            # El markdown se lee entero, enunciados incluidos.
            palabras += len(fuente.split())
        elif celda["cell_type"] == "code":
            # La celda del motor no se lee ni se piensa: se ejecuta y ya.
            if "ava-motor" in etiquetas:
                continue
            # Las de solución y prueba se cuentan en el tiempo del ejercicio.
            if ng.get("grade_id"):
                continue
            celdas_codigo += 1

    leer = palabras / PALABRAS_POR_MINUTO
    ejecutar = celdas_codigo * MIN_POR_CELDA_CODIGO
    resolver = sum(MIN_POR_ESTRELLAS.get(e, 7) for e in ejercicios)

    return {
        "palabras": palabras,
        "celdas_codigo": celdas_codigo,
        "ejercicios": ejercicios,
        "leer": leer,
        "ejecutar": ejecutar,
        "resolver": resolver,
        "total": leer + ejecutar + resolver,
    }


def main(argv):
    semanas = argv or sorted(
        d for d in os.listdir(DESTINO)
        if os.path.isdir(os.path.join(DESTINO, d)))

    print(f"{'cuadernillo':14} {'leer':>7} {'ejecutar':>9} {'resolver':>9} "
          f"{'TOTAL':>7}   ejercicios")
    for sem in semanas:
        ruta = os.path.join(DESTINO, sem, "cuadernillo.ipynb")
        if not os.path.isfile(ruta):
            continue
        e = estimar(ruta)
        estrellas = "".join(str(x) for x in e["ejercicios"])
        print(f"{sem:14} {e['leer']:6.0f}m {e['ejecutar']:8.0f}m "
              f"{e['resolver']:8.0f}m {e['total']:6.0f}m   "
              f"{len(e['ejercicios'])} ({estrellas})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
