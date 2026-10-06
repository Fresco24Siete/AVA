#!/usr/bin/env python3
"""Sube al backend las notas de un cuadernillo (lo corre el INSTRUCTOR).

    registrar-notas                 lista qué cuadernillos tienen notas
    registrar-notas semana_02       sube las notas de ese cuadernillo

Desde formgrader ya no hace falta: al pulsar «Autograde», admin_bridge llama a
registrar() y la nota llega sola al panel del alumno; y el bloque de ayuda tiene
un botón «Subir notas» para repetirlo. Este comando queda para el terminal y
para cuando el backend estuvo caído en ese momento. La nota real la calcula
nbgrader ejecutando también las pruebas ocultas; este comando solo la lee de su
libro de calificaciones y la lleva a la base, que es donde el panel y el análisis
por competencia pueden usarla.

Por eso la nota se marca con origen='nbgrader': para distinguirla de cualquier
cifra provisional deducida de la telemetría, que solo vio las pruebas visibles.
"""
import json
import os
import sys
import urllib.error
import urllib.request

CURSO = os.environ.get("CURSO_ID", "curso_default")
RAIZ = f"/home/jovyan/work/nbgrader/{CURSO}"
BASE = os.environ.get("METRICS_API_BASE",
                      os.environ.get("STUDENT_METRICS_API_BASE", "http://api_go:8080"))
# El token de docente, acotado a este curso, que el Hub acuña al arrancar el
# contenedor. METRICS_API_TOKEN queda como respaldo para un Hub anterior.
TOKEN = (os.environ.get("METRICS_DOCENTE_TOKEN")
         or os.environ.get("METRICS_API_TOKEN", ""))


def _libro():
    """Abre el libro de nbgrader. Se importa aquí para que listar no lo exija."""
    from nbgrader.api import Gradebook
    return Gradebook(f"sqlite:///{RAIZ}/gradebook.db", course_id=CURSO)


def _notas(cuadernillo):
    """Devuelve [(estudiante, obtenidos, maximos)] de las entregas calificadas."""
    salida = []
    with _libro() as gb:
        for envio in gb.assignment_submissions(cuadernillo):
            # score y max_score los calcula nbgrader sumando las celdas de
            # prueba. Una entrega recogida pero sin calificar da score 0, que no
            # es lo mismo que un cero merecido: se avisa aparte.
            salida.append((envio.student_id, float(envio.score), float(envio.max_score)))
    return salida


def _listar():
    try:
        with _libro() as gb:
            tareas = [a.name for a in gb.assignments]
    except Exception as err:
        print(f"[ERROR] No pude abrir el libro de calificaciones: {err}")
        print(f"        Se esperaba en {RAIZ}/gradebook.db")
        return 2

    if not tareas:
        print("No hay actividades en el libro de calificaciones.")
        return 0

    print(f"Actividades del curso {CURSO}:\n")
    for tarea in sorted(tareas):
        try:
            notas = _notas(tarea)
        except Exception:
            notas = []
        if notas:
            print(f"  {tarea:16s} {len(notas)} entrega(s) calificada(s)")
        else:
            print(f"  {tarea:16s} sin entregas recogidas")
    print("\n  registrar-notas <cuadernillo>")
    print("  Ejecútalo después de 'Autograde' en formgrader.")
    return 0


def registrar(cuadernillo):
    """Sube las notas de un cuadernillo. Devuelve un dict con el resultado, para
    que lo usen igual el comando de terminal y el botón de formgrader:

        {"ok": bool, "guardadas": int, "notas": [(estudiante, obtenidos, maximos)],
         "avisos": [str], "error": str | None}
    """
    salida = {"ok": False, "guardadas": 0, "notas": [], "avisos": [], "error": None}
    if not TOKEN:
        salida["error"] = "Falta METRICS_DOCENTE_TOKEN: es el que autoriza a subir notas."
        return salida

    try:
        notas = _notas(cuadernillo)
    except Exception as err:
        salida["error"] = f"No pude leer las notas de '{cuadernillo}': {err}"
        return salida
    salida["notas"] = notas

    if not notas:
        salida["error"] = (f"'{cuadernillo}' no tiene entregas calificadas. "
                           "Primero «Collect» y luego «Autograde» en formgrader.")
        return salida

    sin_puntos = [e for e, _, mx in notas if mx == 0]
    if sin_puntos:
        salida["avisos"].append(
            f"{len(sin_puntos)} entrega(s) con puntaje máximo 0. "
            "Suele indicar que se recogieron pero no se calificaron.")

    payload = {
        "course_id": CURSO,
        "cuadernillo_id": cuadernillo,
        "origen": "nbgrader",
        "notas": [{"student_id": e, "puntos_obtenidos": ob, "puntos_maximos": mx}
                  for e, ob, mx in notas],
    }
    peticion = urllib.request.Request(
        BASE.rstrip("/") + "/internal/notas",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {TOKEN}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=15) as resp:
            cuerpo = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        salida["error"] = (f"El backend respondió {err.code}: "
                           f"{err.read()[:200].decode('utf-8', 'replace')}")
        return salida
    except Exception as err:
        salida["error"] = f"No se pudo contactar al backend en {BASE}: {err}"
        return salida

    salida["ok"] = True
    salida["guardadas"] = int(cuerpo.get("guardadas") or 0)
    salida["mensaje"] = cuerpo.get("message", "")
    return salida


def main(argv):
    if not argv:
        return _listar()

    cuadernillo = argv[0]
    resultado = registrar(cuadernillo)

    for estudiante, obtenidos, maximos in sorted(resultado["notas"])[:5]:
        print(f"  {estudiante:28s} {obtenidos:g} / {maximos:g}")
    if len(resultado["notas"]) > 5:
        print(f"  … y {len(resultado['notas']) - 5} más")
    for aviso in resultado["avisos"]:
        print(f"[AVISO] {aviso}")

    if not resultado["ok"]:
        print(f"[ERROR] {resultado['error']}")
        return 1 if "no tiene entregas" in (resultado["error"] or "") else 3

    print(f"\n[OK] {resultado.get('mensaje')}: {resultado['guardadas']} nota(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
