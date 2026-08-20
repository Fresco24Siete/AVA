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
  - exchange/.../<tarea> el buzón
  - lo publicado y su entrada en el manifest, si estaba publicada

Qué NO borra nunca sin --forzar:
  - submitted/, autograded/, feedback/  ->  el trabajo entregado por los alumnos

Antes de borrar nada guarda una copia completa con fecha. La copia se conserva:
recuperarla es mover una carpeta, y no tenerla es perder el semestre.
"""
import json
import os
import shutil
import sys
from datetime import datetime

CURSO = os.environ.get("CURSO_ID", "curso_default")
RAIZ = f"/srv/nbgrader/{CURSO}"
EXCHANGE = f"/srv/nbgrader/exchange/{CURSO}"
PUB = os.environ.get("PUBLICADOS_BASE", "/srv/publicados") + f"/{CURSO}"
RESPALDOS = f"{RAIZ}/respaldos_borrados"

# Carpetas del docente: se borran. Carpetas con trabajo de alumnos: se protegen.
DEL_DOCENTE = ["source", "release"]
DEL_ALUMNOS = ["submitted", "autograded", "feedback"]


def _carpetas(tarea):
    rutas = [(d, os.path.join(RAIZ, d, tarea)) for d in DEL_DOCENTE + DEL_ALUMNOS]
    rutas.append(("exchange", os.path.join(EXCHANGE, "outbound", tarea)))
    rutas.append(("publicado", os.path.join(PUB, tarea)))
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


def _quitar_del_manifest(tarea):
    """Saca la tarea del manifest para que deje de aparecerle al alumno."""
    ruta = os.path.join(PUB, "manifest.json")
    try:
        with open(ruta, encoding="utf-8") as f:
            m = json.load(f)
    except (OSError, ValueError):
        return False

    publicados = [c for c in (m.get("cuadernillos") or []) if c.get("id") != tarea]
    cambio = len(publicados) != len(m.get("cuadernillos") or [])

    # Si era el activo, se pasa el testigo al último que quede.
    if m.get("cuadernillo_id") == tarea:
        if publicados:
            m["cuadernillo_id"] = publicados[-1]["id"]
            m["notebook"] = publicados[-1].get("notebook", "cuadernillo.ipynb")
        else:
            m["cuadernillo_id"] = ""
        cambio = True

    if cambio:
        m["cuadernillos"] = publicados
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=2)
    return cambio


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

    if _quitar_del_manifest(tarea):
        msgs.append("quitada del manifest: deja de aparecerle al alumno")

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
