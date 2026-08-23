#!/usr/bin/env python3
"""Elimina una actividad de nbgrader (lo corre el INSTRUCTOR).

    borrar-cuadernillo                       lista qué hay y qué se borraría
    borrar-cuadernillo semana_1              borra, si no tiene envíos
    borrar-cuadernillo semana_1 --forzar     borra aunque tenga envíos

Formgrader no tiene ningún botón para esto: lo más parecido es «unrelease», que
solo vacía el buzón y no elimina nada. Para quitar una actividad de la lista hay
que borrar sus carpetas, y hacerlo a mano en el servidor es justo el tipo de
operación en la que se borra lo que no era.

Qué borra:
  - source/<tarea>      lo que autoró el docente
  - release/<tarea>     la versión generada para el alumno
  - su liberación en el servicio de intercambio (deja de aparecerle al alumno)
  - su ficha en gradebook.db, para que el nombre quede libre de verdad

Qué NO borra nunca sin --forzar:
  - submitted/, autograded/, feedback/  ->  el trabajo entregado por los alumnos

Antes de borrar nada guarda una copia completa con fecha. La copia se conserva:
recuperarla es mover una carpeta, y no tenerla es perder el semestre.
"""
import os
import shutil
import sys
from datetime import datetime

CURSO = os.environ.get("CURSO_ID", "curso_default")
RAIZ = f"/srv/nbgrader/{CURSO}"
RESPALDOS = f"{RAIZ}/respaldos_borrados"

# Carpetas del docente: se borran. Carpetas con trabajo de alumnos: se protegen.
DEL_DOCENTE = ["source", "release"]
DEL_ALUMNOS = ["submitted", "autograded", "feedback"]


def _carpetas(tarea):
    rutas = [(d, os.path.join(RAIZ, d, tarea)) for d in DEL_DOCENTE + DEL_ALUMNOS]
    return [(etiqueta, ruta) for etiqueta, ruta in rutas if os.path.isdir(ruta)]


def _envios(tarea):
    """Cuántos estudiantes entregaron algo de esta tarea."""
    total = 0
    for d in DEL_ALUMNOS:
        base = os.path.join(RAIZ, d)
        if not os.path.isdir(base):
            continue
        for alumno in os.listdir(base):
            if os.path.isdir(os.path.join(base, alumno, tarea)):
                total += 1
    # nbgrader guarda submitted/<alumno>/<tarea>, pero algunos flujos dejan
    # submitted/<tarea>. Se cuentan los dos.
    for d in DEL_ALUMNOS:
        if os.path.isdir(os.path.join(RAIZ, d, tarea)):
            total += 1
    return total


def _listar():
    fuente = os.path.join(RAIZ, "source")
    if not os.path.isdir(fuente):
        print(f"No hay actividades en {fuente}.")
        return 0
    tareas = sorted(d for d in os.listdir(fuente)
                    if os.path.isdir(os.path.join(fuente, d)))
    if not tareas:
        print("No hay actividades.")
        return 0
    print(f"Actividades del curso {CURSO}:\n")
    for tarea in tareas:
        envios = _envios(tarea)
        aviso = f"  ATENCION: {envios} con envios de alumnos" if envios else ""
        print(f"  {tarea:16s}{aviso}")
    print("\n  borrar-cuadernillo <nombre> [--forzar]")
    print("  Siempre se guarda una copia antes de borrar.")
    return 0


def _retirar_del_exchange(tarea):
    """Deja de ofrecer la tarea en el servicio de intercambio.

    Es el «unrelease» de nbgrader: el alumno deja de verla en su índice. Lo que
    ya tenga en su carpeta, y las entregas que estén en el servicio, no se
    tocan. Devuelve (ok, mensaje).
    """
    try:
        from nbexchange_cliente import ava
        ava.retirar(tarea)
        return True, "retirada del intercambio: deja de aparecerle al alumno"
    except Exception as err:
        return False, (f"no se pudo retirar del intercambio ({err}); el alumno "
                       f"seguirá viéndola hasta que se retire a mano con "
                       f"'nbgrader list --remove {tarea}'")


def _quitar_del_gradebook(tarea, destino):
    """Borra la actividad de gradebook.db.

    Borrar solo las carpetas deja la fila viva en la base de nbgrader con sus
    notas y entregas colgando. No se nota —formgrader lista por carpeta— hasta
    que alguien crea otra actividad con el mismo nombre y hereda las notas de la
    anterior. Antes de tocar nada se guarda una copia de la base junto al resto
    del respaldo.
    """
    bd = os.path.join(RAIZ, "gradebook.db")
    if not os.path.isfile(bd):
        return None
    try:
        shutil.copy2(bd, os.path.join(destino, "gradebook.db"))
    except Exception as err:
        return f"no pude respaldar gradebook.db ({err}): no se tocó la base"
    try:
        from nbgrader.api import Gradebook, MissingEntry
        # El curso, explícito. Gradebook() lo tiene por defecto en
        # 'default_course' y lo CREA si no existe, así que abrirlo sin decirle
        # cuál es deja una fila de curso fantasma en el libro de notas. Ya metió
        # una.
        with Gradebook("sqlite:///" + bd, course_id=CURSO) as gb:
            try:
                gb.remove_assignment(tarea)
            except MissingEntry:
                return None
    except Exception as err:
        return f"no se pudo limpiar gradebook.db: {err}"
    return "borrado: la ficha en gradebook.db (con sus notas)"


def borrar(tarea, forzar=False):
    """Devuelve (ok, mensajes). Usado por el CLI y por el panel del docente."""
    msgs = []
    carpetas = _carpetas(tarea)
    if not carpetas:
        return False, [f"No encontré la actividad '{tarea}'."]

    envios = _envios(tarea)
    if envios and not forzar:
        return False, [
            f"'{tarea}' tiene trabajo entregado por {envios} estudiante(s).",
            "NO se borró. Si de verdad quieres eliminarla, repite con --forzar.",
            "Se guardará una copia igualmente, pero perderás esas entregas de la",
            "vista de calificación.",
        ]

    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(RESPALDOS, f"{tarea}_{marca}")
    os.makedirs(destino, exist_ok=True)

    for etiqueta, ruta in carpetas:
        try:
            shutil.copytree(ruta, os.path.join(destino, etiqueta))
        except Exception as err:
            return False, [f"No pude respaldar {etiqueta}: {err}. No se borró nada."]
    msgs.append(f"Copia guardada en {destino}")

    for etiqueta, ruta in carpetas:
        try:
            shutil.rmtree(ruta)
            msgs.append(f"borrado: {etiqueta}")
        except Exception as err:
            msgs.append(f"no se pudo borrar {etiqueta}: {err}")

    aviso_bd = _quitar_del_gradebook(tarea, destino)
    if aviso_bd:
        msgs.append(aviso_bd)

    _, aviso_exchange = _retirar_del_exchange(tarea)
    msgs.append(aviso_exchange)

    if envios:
        msgs.append(f"ATENCION: se borraron entregas de {envios} estudiante(s).")

    return True, msgs


def main(argv):
    forzar = "--forzar" in argv
    tareas = [a for a in argv if not a.startswith("-")]
    if not tareas:
        return _listar()

    for tarea in tareas:
        ok, msgs = borrar(tarea, forzar)
        print(f"[{'OK' if ok else 'NO SE BORRO'}] {tarea}")
        for m in msgs:
            print(f"     {m}")
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
