#!/usr/bin/env python3
"""Lleva un cuadernillo de las plantillas de la imagen a source/ de nbgrader.

    sembrar-cuadernillo                    lista qué hay y en qué estado
    sembrar-cuadernillo semana_02          siembra si aún no está
    sembrar-cuadernillo semana_02 --forzar reemplaza la versión que haya

Por qué existe: el arranque del contenedor siembra con `cp -n`, que NO pisa lo
que ya está en source/. Se hizo así para no borrar las ediciones que el docente
haga desde formgrader, y es lo correcto — pero tiene una trampa: al actualizar el
contenido de un cuadernillo, la versión nueva no entra sola. El docente hace
"Generate", publica, y sigue publicándose la vieja sin que nada avise.

Este comando hace ese refresco EXPLÍCITO. Y antes de reemplazar nada guarda una
copia con fecha, porque lo que hay en source/ puede llevar horas de trabajo del
docente encima.

No toca los envíos de los estudiantes ni lo publicado: solo source/.
"""
import os
import shutil
import sys
from datetime import datetime

CURSO = os.environ.get("CURSO_ID", "curso_default")
PLANTILLAS = os.environ.get("PLANTILLAS_DIR", "/opt/plantillas")
SOURCE = f"/srv/nbgrader/{CURSO}/source"
RESPALDOS = f"/srv/nbgrader/{CURSO}/respaldos_source"


def _plantillas():
    """Cada subcarpeta de /opt/plantillas es un cuadernillo."""
    if not os.path.isdir(PLANTILLAS):
        return []
    return sorted(
        d for d in os.listdir(PLANTILLAS)
        if os.path.isdir(os.path.join(PLANTILLAS, d))
    )


def _listar():
    disponibles = _plantillas()
    if not disponibles:
        print(f"No hay plantillas en {PLANTILLAS}.")
        return 0
    print(f"Cuadernillos disponibles en la imagen (curso {CURSO}):\n")
    for tarea in disponibles:
        destino = os.path.join(SOURCE, tarea)
        if not os.path.isdir(destino):
            estado = "sin sembrar"
        else:
            estado = "ya en source/ (usa --forzar para reemplazarlo)"
        print(f"  {tarea:16s} {estado}")
    print("\n  sembrar-cuadernillo <nombre> [--forzar]")
    return 0


def _respaldar(destino, tarea):
    """Guarda lo que hay en source/ antes de pisarlo."""
    if not os.path.isdir(destino) or not os.listdir(destino):
        return None
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    copia = os.path.join(RESPALDOS, f"{tarea}_{marca}")
    os.makedirs(os.path.dirname(copia), exist_ok=True)
    shutil.copytree(destino, copia)
    return copia


def main(argv):
    forzar = "--forzar" in argv
    tareas = [a for a in argv if not a.startswith("-")]

    if not tareas:
        return _listar()

    disponibles = _plantillas()
    for tarea in tareas:
        if tarea not in disponibles:
            print(f"[ERROR] No hay plantilla para '{tarea}'.")
            print(f"        Disponibles: {', '.join(disponibles) or '(ninguna)'}")
            return 2

        origen = os.path.join(PLANTILLAS, tarea)
        destino = os.path.join(SOURCE, tarea)
        existe = os.path.isdir(destino) and os.listdir(destino)

        if existe and not forzar:
            print(f"[ATENCION] '{tarea}' ya está en source/ y NO se tocó.")
            print( "           Si querías actualizarlo con la versión nueva de la")
            print( "           imagen, repite con --forzar. Se guardará una copia")
            print( "           de lo que hay antes de reemplazarlo.")
            continue

        copia = _respaldar(destino, tarea) if existe else None
        os.makedirs(destino, exist_ok=True)
        copiados = 0
        for archivo in sorted(os.listdir(origen)):
            if not archivo.endswith(".ipynb"):
                continue
            shutil.copyfile(os.path.join(origen, archivo),
                            os.path.join(destino, archivo))
            copiados += 1

        print(f"[OK] '{tarea}': {copiados} notebook(s) en source/.")
        if copia:
            print(f"     Copia de lo anterior: {copia}")
        print( "     Ahora haz 'Generate' en formgrader y luego")
        print(f"     publicar-cuadernillo {tarea}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
