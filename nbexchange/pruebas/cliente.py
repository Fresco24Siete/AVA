#!/usr/bin/env python3
"""Recorre el exchange desde dentro de la imagen del AVA, como lo haría cada rol.

Lo lanza prueba_integracion.sh dentro de un contenedor de la imagen del alumno,
con las mismas variables de entorno que pondría el Hub (CURSO_ID, ALUMNO_ROL,
JUPYTERHUB_API_TOKEN, NBEXCHANGE_URL). Cada paso es un subcomando:

  publicar       (docente) Generate simulado + publicar-cuadernillo
  republicar     (docente) corrige el contenido y vuelve a publicar --sin-activar
  traer          (alumno)  entregar-cuadernillo: lo publicado llega a work/
  entregar       (alumno)  entrega desde el panel (misma función que el botón)
  recoger        (docente) Collect, como lo hace formgrader
  retirar        (docente) borrar-cuadernillo -> unrelease
  prohibido      (alumno)  lo que un alumno NO debe poder hacer

Imprime una línea `OK <paso>` o `FALLO <paso>: motivo` y sale con 0/1.
"""
import json
import os
import shutil
import sys

PASO = sys.argv[1] if len(sys.argv) > 1 else ""
CURSO = os.environ["CURSO_ID"]
RAIZ = f"/srv/nbgrader/{CURSO}"          # el curso del docente (volumen)
WORK = os.environ.get("PRUEBA_WORK", "/home/jovyan/work")
TAREA = "semana_01"


def ok(msg=""):
    print(f"OK {PASO} {msg}".rstrip())
    sys.exit(0)


def fallo(msg):
    print(f"FALLO {PASO}: {msg}")
    sys.exit(1)


def notebook(texto):
    return {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": [texto]},
            {"cell_type": "code", "metadata": {"nbgrader": {"grade": False, "solution": True,
                                                            "grade_id": "ejercicio_1"}},
             "execution_count": None, "outputs": [],
             "source": ["# ESCRIBE TU CODIGO AQUI\nraise NotImplementedError()"]},
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                    "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5,
    }


def escribir_release(texto):
    """Lo que deja Generate: release/<tarea>/cuadernillo.ipynb (y source/)."""
    for carpeta in ("source", "release"):
        d = os.path.join(RAIZ, carpeta, TAREA)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "cuadernillo.ipynb"), "w") as f:
            json.dump(notebook(texto), f)


def correr(cmd):
    import subprocess
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip())
    if r.stderr.strip():
        print(r.stderr.strip(), file=sys.stderr)
    return r.returncode


# --- docente -------------------------------------------------------------------

if PASO == "publicar":
    escribir_release("# Semana 1 — versión A")
    rc = correr(["publicar-cuadernillo", TAREA])
    if rc != 0:
        fallo(f"publicar-cuadernillo devolvió {rc}")
    from nbexchange_cliente import ava
    liberadas, _ = ava.liberados()
    if TAREA not in liberadas:
        fallo(f"el servicio no lista {TAREA}: {liberadas}")
    ok(f"liberada {TAREA} en {liberadas[TAREA]['timestamp']}")

elif PASO == "republicar":
    escribir_release("# Semana 1 — versión B (errata corregida)")
    rc = correr(["publicar-cuadernillo", TAREA, "--sin-activar"])
    if rc != 0:
        fallo(f"publicar-cuadernillo devolvió {rc}")
    ok()

elif PASO == "recoger":
    # Exactamente lo que hace el botón Collect de formgrader.
    from nbgrader.apps.api import NbGraderAPI
    from nbgrader.coursedir import CourseDirectory
    from nbexchange_cliente import ava
    cfg = ava.cargar_config()
    cd = CourseDirectory(config=cfg)
    api = NbGraderAPI(cd, config=cfg)
    if api.exchange_missing:
        fallo("NbGraderAPI dice exchange_missing=True (List falló)")
    r = api.collect(TAREA)
    print(r.get("log", "")[-600:])
    if not r.get("success"):
        fallo(f"collect: {r.get('error')}")
    entregas = sorted(os.listdir(os.path.join(RAIZ, "submitted")))
    esperado = os.environ.get("PRUEBA_ESPERA_ALUMNOS", "").split(",")
    esperado = [e for e in esperado if e]
    for alumno in esperado:
        ruta = os.path.join(RAIZ, "submitted", alumno, TAREA)
        if not os.path.isfile(os.path.join(ruta, "cuadernillo.ipynb")):
            fallo(f"no llegó submitted/{alumno}/{TAREA}/cuadernillo.ipynb (hay: {entregas})")
        if not os.path.isfile(os.path.join(ruta, "timestamp.txt")):
            fallo(f"falta timestamp.txt en submitted/{alumno}/{TAREA}")
        with open(os.path.join(ruta, "cuadernillo.ipynb")) as f:
            nb = json.load(f)
        marca = nb.get("metadata", {}).get("prueba_alumno")
        if marca != alumno:
            fallo(f"submitted/{alumno} contiene el trabajo de {marca!r}, no de {alumno}")
    # Las entregas de otros cursos no deben aparecer
    intrusos = [a for a in entregas if a not in esperado]
    if intrusos:
        fallo(f"submitted/ trae alumnos que no son de este curso: {intrusos}")
    # Y el libro de notas tiene a los alumnos con su nombre completo
    from nbgrader.api import Gradebook
    with Gradebook(cd.db_url, CURSO) as gb:
        nombres = {s.id: (s.first_name, s.last_name, s.email) for s in gb.students}
    print("gradebook:", nombres)
    for alumno in esperado:
        if alumno not in nombres:
            fallo(f"{alumno} no quedó en el gradebook")
    ok(f"recogidas {esperado}")

elif PASO == "retirar":
    rc = correr(["borrar-cuadernillo", TAREA, "--forzar"])
    if rc != 0:
        fallo(f"borrar-cuadernillo devolvió {rc}")
    from nbexchange_cliente import ava
    liberadas, _ = ava.liberados()
    if TAREA in liberadas:
        fallo(f"{TAREA} sigue liberada tras borrar")
    ok()

# --- alumno --------------------------------------------------------------------

elif PASO == "traer":
    os.environ["CUADERNILLO_DESTINO"] = os.path.join(WORK, "cuadernillo.ipynb")
    import entregar_cuadernillo
    activo = entregar_cuadernillo.main()
    archivos = sorted(os.listdir(WORK))
    print("work/:", archivos, "activo:", activo)
    esperado = os.environ.get("PRUEBA_ESPERA_ARCHIVO", f"{TAREA}.ipynb")
    if esperado not in archivos:
        fallo(f"no llegó {esperado}")
    with open(os.path.join(WORK, esperado)) as f:
        nb = json.load(f)
    texto = "".join(nb["cells"][0]["source"])
    if os.environ.get("PRUEBA_ESPERA_TEXTO", "") not in texto:
        fallo(f"el contenido no es el esperado: {texto!r}")
    if os.environ.get("PRUEBA_ESPERA_ACTIVO", TAREA) != activo:
        fallo(f"activo={activo!r}, esperaba {os.environ.get('PRUEBA_ESPERA_ACTIVO', TAREA)!r}")
    if "ava_publicacion.json" in archivos:
        fallo("el fichero de publicación no debe quedar en work/")
    ok(f"{esperado}: {texto!r}")

elif PASO == "entregar":
    # El alumno escribe algo en su cuadernillo y pulsa «Entregar».
    ruta = os.path.join(WORK, f"{TAREA}.ipynb")
    with open(ruta) as f:
        nb = json.load(f)
    nb["metadata"]["prueba_alumno"] = os.environ["PRUEBA_ALUMNO"]
    with open(ruta, "w") as f:
        json.dump(nb, f)
    os.environ["PANEL_CARPETA"] = WORK
    os.environ["CUADERNILLO_DESTINO"] = os.path.join(WORK, "cuadernillo.ipynb")
    import panel_bridge
    hecho, error = panel_bridge._entregar(TAREA, f"{TAREA}.ipynb")
    if not hecho:
        fallo(error)
    from nbexchange_cliente import ava
    _, entregadas = ava.liberados()
    if TAREA not in entregadas:
        fallo("el servicio no registra la entrega")
    # Y el panel lo sabe tras refrescar
    import entregar_cuadernillo
    entregar_cuadernillo.main()
    if TAREA not in panel_bridge._entregas():
        fallo("el panel no muestra la entrega")
    ok(f"entregada en {entregadas[TAREA]}; panel dice {panel_bridge._entregas()[TAREA]!r}")

elif PASO == "prohibido":
    from nbexchange_cliente import ava
    from nbgrader.exchange import ExchangeError
    escribir_release("# intento del alumno")
    try:
        ava.liberar(TAREA)
        fallo("un alumno pudo liberar una tarea")
    except ExchangeError as err:
        print("liberar ->", str(err)[:80])
    try:
        ava.entregas_en_exchange(TAREA)
        fallo("un alumno pudo listar las entregas de todos")
    except ExchangeError as err:
        print("collections ->", str(err)[:80])
    try:
        from nbgrader.exchange import ExchangeFactory
        cfg = ava.cargar_config()
        c = ava._exchange(ava.ExchangeCollect, cfg, TAREA)
        c.start()
        if os.path.isdir(os.path.join(RAIZ, "submitted")) and os.listdir(os.path.join(RAIZ, "submitted")):
            fallo("un alumno pudo recoger entregas")
        print("collect -> nada recogido")
    except ExchangeError as err:
        print("collect ->", str(err)[:80])
    # Curso ajeno: ni listar ni traer
    os.environ["CURSO_ID"] = os.environ.get("PRUEBA_OTRO_CURSO", "99999")
    import importlib
    importlib.reload(ava)
    try:
        liberadas, _ = ava.liberados()
        if liberadas:
            fallo(f"un alumno listó las tareas de otro curso: {liberadas}")
        print("otro curso -> lista vacía")
    except ExchangeError as err:
        print("otro curso ->", str(err)[:80])
    ok()

else:
    fallo(f"paso desconocido {PASO!r}")
