#!/usr/bin/env python3
"""Entrega al alumno el cuadernillo ACTIVO decidido por el instructor vía nbgrader.

Lo decide un manifest publicado por el instructor (NO el backend): el instructor
libera la tarea en nbgrader y la publica con una ventana de tiempo. Este script
corre en el arranque del contenedor del ALUMNO y:

  1. Lee /srv/publicados/<CURSO_ID>/manifest.json (volumen read-only).
  2. Valida la ventana de tiempo (abre/cierra).
  3. Copia el notebook liberado (sin soluciones) a /home/jovyan/work/cuadernillo.ipynb
     — nombre FIJO, para que el Hub siempre pueda apuntar default_url ahí.
  4. Si está fuera de ventana o no hay activo, entrega un notebook "cerrado".
  5. Imprime en stdout el codigo del cuadernillo, que el entrypoint exporta como
     CUADERNILLO_CODIGO para que la telemetría lo etiquete.

No sobrescribe el trabajo del alumno: si ya existe cuadernillo.ipynb (re-spawn),
no lo toca, para no borrar su progreso.
"""
import json
import os
import shutil
from datetime import datetime, timezone

CURSO = os.environ.get("CURSO_ID", "curso_default")
# Rutas configurables por env (defaults de producción); facilita las pruebas.
PUB_BASE = os.environ.get("PUBLICADOS_BASE", "/srv/publicados")
DESTINO = os.environ.get("CUADERNILLO_DESTINO", "/home/jovyan/work/cuadernillo.ipynb")
PUB_DIR = f"{PUB_BASE}/{CURSO}"
MANIFEST = f"{PUB_DIR}/manifest.json"


def _nb_markdown(titulo, cuerpo):
    """Devuelve un .ipynb mínimo válido con un solo cell markdown."""
    return {
        "cells": [{
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"# {titulo}\n", "\n", cuerpo],
        }],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _escribir(nb):
    with open(DESTINO, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False)


def _parse(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def main():
    # No pisar el trabajo del alumno si ya tiene el cuadernillo (re-spawn).
    ya_existe = os.path.exists(DESTINO)

    try:
        with open(MANIFEST, encoding="utf-8") as f:
            m = json.load(f)
    except FileNotFoundError:
        if not ya_existe:
            _escribir(_nb_markdown(
                "Aún no hay cuadernillo",
                "El profesor todavía no ha publicado un cuadernillo para este curso."))
        return ""
    except Exception as exc:  # manifest corrupto
        if not ya_existe:
            _escribir(_nb_markdown("No se pudo cargar el cuadernillo", str(exc)))
        return ""

    codigo = str(m.get("cuadernillo_id", ""))
    notebook = m.get("notebook", "")
    ahora = datetime.now(timezone.utc)
    abre = _parse(m.get("abre"))
    cierra = _parse(m.get("cierra"))

    if ya_existe:
        # El alumno ya tiene su copia; no la tocamos. Solo devolvemos el código
        # para etiquetar la telemetría.
        return codigo

    if abre and ahora < abre:
        _escribir(_nb_markdown(
            "Cuadernillo aún no disponible",
            f"Este cuadernillo abre el **{abre.isoformat()}**. Vuelve más tarde."))
        return codigo
    if cierra and ahora > cierra:
        _escribir(_nb_markdown(
            "Cuadernillo cerrado",
            f"El plazo cerró el **{cierra.isoformat()}**. Ya no está disponible."))
        return codigo

    origen = f"{PUB_DIR}/{codigo}/{notebook}"
    try:
        shutil.copyfile(origen, DESTINO)
    except Exception as exc:
        _escribir(_nb_markdown(
            "No se pudo entregar el cuadernillo",
            f"No se encontró el archivo publicado (`{origen}`): {exc}"))
    return codigo


if __name__ == "__main__":
    try:
        print(main())
    except Exception:
        # Nunca fallar el arranque del contenedor por esto.
        print("")
