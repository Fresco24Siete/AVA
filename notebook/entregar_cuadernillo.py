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


# El alumno abre `inicio.ipynb`: un indice con los cuadernillos publicados hasta
# hoy, marcando el de esta semana. Cada cuadernillo vive en `<id>.ipynb`.
INICIO = os.environ.get("CUADERNILLO_INICIO",
                        os.path.join(os.path.dirname(DESTINO), "inicio.ipynb"))


# Qué versión de cada cuadernillo tiene ya el alumno. Vive en su carpeta de
# trabajo -- es decir, en su volumen -- para sobrevivir a que se recree el
# contenedor.
REGISTRO = os.path.join(os.path.dirname(DESTINO), ".ava_versiones.json")


def _leer_registro():
    try:
        with open(REGISTRO, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _guardar_registro(datos):
    try:
        with open(REGISTRO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)
    except OSError:
        pass          # no vale la pena tumbar el arranque por esto


def _titulo_bonito(codigo):
    """'semana_01' -> 'Semana 1'. Si no encaja, se devuelve el codigo tal cual."""
    partes = codigo.split("_")
    if len(partes) == 2 and partes[1].isdigit():
        return f"{partes[0].capitalize()} {int(partes[1])}"
    return codigo


def _escribir_indice(entregados, activo):
    """Escribe el indice. Se regenera siempre: no contiene trabajo del alumno."""
    lineas = [
        "# Tus cuadernillos",
        "",
        "Aqui estan todos los cuadernillos publicados del curso. El de **esta "
        "semana** es el que tiene la marca; los anteriores siguen disponibles "
        "para repasar, y lo que ya respondiste en ellos se conserva.",
        "",
    ]
    if not entregados:
        lineas.append("_Todavia no hay ningun cuadernillo publicado._")
    else:
        lineas += ["| | Cuadernillo | Abrir |", "|---|---|---|"]
        for c in entregados:
            marca = "**Esta semana**" if c["id"] == activo else ""
            enlace = f"[abrir]({c['archivo']})"
            if c.get("anterior"):
                # Hubo una correccion. Se enlaza la version nueva y, aparte, la
                # que el alumno ya tenia: su trabajo esta ahi y no se toca.
                enlace += (f"<br/>corregido &middot; "
                           f"[tu version anterior]({c['anterior']})")
            lineas.append(f"| {marca} | {_titulo_bonito(c['id'])} | {enlace} |")
        lineas += [
            "",
            "---",
            "",
            "Para abrir uno, haz clic en su enlace. Si un cuadernillo se te "
            "cierra por fecha deja de aparecer aqui, pero lo que ya hiciste no "
            "se borra.",
        ]
    _escribir_en(INICIO, _nb_markdown_crudo("\n".join(lineas)))


def _nb_markdown_crudo(texto):
    return {
        "cells": [{"cell_type": "markdown", "metadata": {}, "source": [texto]}],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                    "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5,
    }


def _escribir_en(ruta, nb):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False)


def _disponible(entrada, ahora):
    """True si el cuadernillo esta dentro de su ventana de tiempo."""
    abre = _parse(entrada.get("abre"))
    cierra = _parse(entrada.get("cierra"))
    if abre and ahora < abre:
        return False
    if cierra and ahora > cierra:
        return False
    return True


def main():
    try:
        with open(MANIFEST, encoding="utf-8") as f:
            m = json.load(f)
    except FileNotFoundError:
        _escribir_indice([], "")
        _escribir(_nb_markdown(
            "Aun no hay cuadernillo",
            "El profesor todavia no ha publicado un cuadernillo para este curso."))
        return ""
    except Exception as exc:  # manifest corrupto
        _escribir_indice([], "")
        _escribir(_nb_markdown("No se pudo cargar el cuadernillo", str(exc)))
        return ""

    activo = str(m.get("cuadernillo_id", ""))
    ahora = datetime.now(timezone.utc)

    # Formato nuevo (lista) con respaldo al viejo (uno solo).
    publicados = m.get("cuadernillos") or []
    if not publicados and activo:
        publicados = [{"id": activo, "notebook": m.get("notebook", ""),
                       "abre": m.get("abre"), "cierra": m.get("cierra")}]

    carpeta = os.path.dirname(DESTINO)

    # Migracion del modelo viejo: el trabajo del alumno estaba en
    # 'cuadernillo.ipynb' a secas. Se renombra al nombre nuevo para que no lo
    # pierda al pasar al indice.
    destino_activo = os.path.join(carpeta, f"{activo}.ipynb") if activo else None
    if (destino_activo and os.path.exists(DESTINO)
            and not os.path.exists(destino_activo)):
        try:
            shutil.move(DESTINO, destino_activo)
        except Exception:
            pass

    registro = _leer_registro()
    entregados = []
    for entrada in publicados:
        codigo = str(entrada.get("id", ""))
        if not codigo or not _disponible(entrada, ahora):
            continue

        version = str(entrada.get("version", ""))
        origen = f"{PUB_DIR}/{codigo}/{entrada.get('notebook', '')}"
        archivo = f"{codigo}.ipynb"
        destino = os.path.join(carpeta, archivo)
        anterior = None

        if not os.path.exists(destino):
            # Primera vez: se entrega con su nombre normal.
            try:
                shutil.copyfile(origen, destino)
            except Exception:
                continue
            registro[archivo] = version

        elif version and registro.get(archivo, version) != version:
            # El docente corrigio el cuadernillo despues de que este alumno ya lo
            # tenia. NO se sobrescribe: su trabajo esta dentro. La version nueva
            # se entrega al lado y el indice enlaza las dos.
            anterior = archivo
            n = 2
            while os.path.exists(os.path.join(carpeta, f"{codigo}_v{n}.ipynb")):
                if registro.get(f"{codigo}_v{n}.ipynb") == version:
                    break          # esa correccion ya se le habia entregado
                n += 1
            archivo = f"{codigo}_v{n}.ipynb"
            destino = os.path.join(carpeta, archivo)
            if not os.path.exists(destino):
                try:
                    shutil.copyfile(origen, destino)
                except Exception:
                    continue
                registro[archivo] = version

        entregados.append({"id": codigo, "archivo": archivo, "anterior": anterior})

    _guardar_registro(registro)

    _escribir_indice(entregados, activo)

    # El codigo que se devuelve etiqueta la telemetria y el cupo del tutor: es
    # el del cuadernillo de esta semana.
    return activo


if __name__ == "__main__":
    try:
        print(main())
    except Exception:
        # Nunca fallar el arranque del contenedor por esto.
        print("")
