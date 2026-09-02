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
  - su ficha en gradebook.db, para que el nombre quede libre de verdad (y deje
    de salir en la lista de formgrader: una actividad creada con el nombre mal
    escrito existe ahí aunque no tenga ni carpeta ni notebook)
  - si estaba publicada, su liberación en el servicio de intercambio

Qué NO borra nunca sin --forzar (en formgrader, la casilla «forzar»):
  - una actividad PUBLICADA: los alumnos ya la tienen. Retírala primero
    (Release en formgrader, que entonces dice «unrelease») o insiste.
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
    """Cuántos estudiantes entregaron algo de esta tarea.

    Personas distintas: un alumno que está en submitted/, autograded/ y
    feedback/ es uno, no tres. Antes se sumaban pares (etapa, alumno) y un solo
    alumno calificado salía como «2 con entregas».
    """
    alumnos = set()
    for d in DEL_ALUMNOS:
        base = os.path.join(RAIZ, d)
        if not os.path.isdir(base):
            continue
        for alumno in os.listdir(base):
            if os.path.isdir(os.path.join(base, alumno, tarea)):
                alumnos.add(alumno)
        # nbgrader guarda submitted/<alumno>/<tarea>, pero algunos flujos dejan
        # submitted/<tarea>. Se cuenta también.
        if os.path.isdir(os.path.join(base, tarea)):
            alumnos.add(f"({d})")
    return len(alumnos)


def _nombre_valido(tarea):
    """Un nombre de actividad es una carpeta simple. Sin esto, 'semana_01/'
    (el autocompletado del shell) borraba carpetas, dejaba el respaldo en una
    ruta inservible y reportaba [OK]."""
    return bool(tarea) and tarea == tarea.strip() and "/" not in tarea \
        and "\\" not in tarea and not tarea.startswith(".")


def _en_gradebook(tarea):
    """True si el libro de notas tiene ficha de la actividad."""
    bd = os.path.join(RAIZ, "gradebook.db")
    if not os.path.isfile(bd):
        return False
    try:
        import sqlite3
        con = sqlite3.connect(f"file:{bd}?mode=ro", uri=True, timeout=2)
        try:
            return con.execute("select 1 from assignment where name = ?",
                               (tarea,)).fetchone() is not None
        finally:
            con.close()
    except Exception:
        return False


def _tareas_en_gradebook():
    bd = os.path.join(RAIZ, "gradebook.db")
    if not os.path.isfile(bd):
        return []
    try:
        import sqlite3
        con = sqlite3.connect(f"file:{bd}?mode=ro", uri=True, timeout=2)
        try:
            return [r[0] for r in con.execute("select name from assignment")]
        finally:
            con.close()
    except Exception:
        return []


def _publicada(tarea):
    """True/False según el servicio de intercambio; None si no respondió."""
    try:
        from nbexchange_cliente import ava
        liberadas, _ = ava.liberados()
        return tarea in liberadas
    except Exception:
        return None


def actividades():
    """Todas las actividades del curso con su estado, para el comando y el panel.

    Une lo que hay en source/ con lo que hay en el gradebook: una actividad
    recién creada desde formgrader con el nombre mal escrito está en los dos
    sitios pero vacía; una borrada a medias puede estar solo en uno.
    """
    fuente = os.path.join(RAIZ, "source")
    en_disco = set()
    if os.path.isdir(fuente):
        en_disco = {d for d in os.listdir(fuente) if os.path.isdir(os.path.join(fuente, d))}
    nombres = sorted(en_disco | set(_tareas_en_gradebook()))
    try:
        from nbexchange_cliente import ava
        liberadas, _ = ava.liberados()
        publicadas = set(liberadas)
    except Exception:
        publicadas = None
    salida = []
    for tarea in nombres:
        carpeta = os.path.join(fuente, tarea)
        vacia = not (os.path.isdir(carpeta)
                     and any(f.endswith(".ipynb") for f in os.listdir(carpeta)))
        salida.append({
            "id": tarea,
            "envios": _envios(tarea),
            "publicada": (tarea in publicadas) if publicadas is not None else None,
            "vacia": vacia,
            "en_gradebook": tarea in _tareas_en_gradebook(),
        })
    return salida


def _listar():
    lista = actividades()
    if not lista:
        print("No hay actividades.")
        return 0
    print(f"Actividades del curso {CURSO}:\n")
    for a in lista:
        notas = []
        if a["publicada"]:
            notas.append("PUBLICADA")
        elif a["publicada"] is None:
            notas.append("¿publicada? (el intercambio no respondió)")
        if a["envios"]:
            notas.append(f"{a['envios']} con envíos")
        if a["vacia"]:
            notas.append("sin notebook")
        print(f"  {a['id']:20s}{'  ' + ' · '.join(notas) if notas else ''}")
    print("\n  borrar-cuadernillo <nombre> [--forzar]")
    print("  Siempre se guarda una copia antes de borrar. --forzar hace falta si")
    print("  está publicada o tiene entregas.")
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
    tarea = str(tarea or "")
    if not _nombre_valido(tarea):
        return False, [f"Nombre de actividad no válido: {tarea!r}."]

    carpetas = _carpetas(tarea)
    en_gb = _en_gradebook(tarea)
    if not carpetas and not en_gb:
        return False, [f"No encontré la actividad '{tarea}'."]

    publicada = _publicada(tarea)
    if publicada and not forzar:
        return False, [
            f"'{tarea}' está PUBLICADA: los alumnos la tienen.",
            "NO se borró. Retírala primero (en formgrader, el botón Release de",
            "una actividad publicada dice «unrelease»), o insiste con «forzar».",
        ]

    envios = _envios(tarea)
    if envios and not forzar:
        return False, [
            f"'{tarea}' tiene trabajo entregado por {envios} estudiante(s).",
            "NO se borró. Si de verdad quieres eliminarla, insiste con «forzar».",
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
    elif en_gb:
        msgs.append("borrado: la ficha en gradebook.db")

    if publicada:
        _, aviso_exchange = _retirar_del_exchange(tarea)
        msgs.append(aviso_exchange)
    elif publicada is None:
        msgs.append("el servicio de intercambio no respondió: si estaba publicada, "
                    f"retírala a mano con 'nbgrader list --remove {tarea}'")

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
