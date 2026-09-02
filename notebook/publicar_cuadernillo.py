#!/usr/bin/env python3
"""Publica un cuadernillo para los alumnos (lo corre el INSTRUCTOR).

nbgrader es la fuente del contenido: el instructor autora en source/, hace
"Generate" (que quita las soluciones -> release/) y luego publica con este
comando. Publicar es liberar la tarea en el servicio de intercambio (nbexchange):
a partir de ese momento cualquier contenedor de alumno, ya esté abierto o se
abra mañana, la trae de ahí al arrancar o al abrir su panel. No hay que
reconstruir ninguna imagen ni montar ninguna carpeta.

Uso:
    publicar-cuadernillo <tarea> [abre_iso] [cierra_iso] [--sin-activar]

Ejemplos:
    publicar-cuadernillo semana_01
    publicar-cuadernillo semana_01 2026-08-25T00:00:00-05:00 2026-09-01T23:59:00-05:00
    publicar-cuadernillo semana_01 --sin-activar     # corrige una errata sin
                                                     # quitarle el turno a la
                                                     # semana en curso

Qué decide "activo" (la marca «Esta semana» del panel del alumno, la etiqueta
de su telemetría y el cupo del tutor): el cuadernillo liberado más reciente que
esté dentro de su ventana, salvo los publicados con --sin-activar. Republicar
una semana vieja para corregir una errata la volvería a poner activa; para eso
existe la opción.

La ventana y la marca viajan dentro de la propia liberación, en
release/<tarea>/ava_publicacion.json, así que llegan al alumno por el mismo
camino que el cuadernillo. El botón «Release» de formgrader libera igual, pero
sin ventana y activando.
"""
import glob
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

from nbexchange_cliente import ava

CURSO = os.environ.get("CURSO_ID", "curso_default")
RELEASE = os.environ.get("NBGRADER_RELEASE", f"/srv/nbgrader/{CURSO}/release")


def _fecha(texto, nombre):
    """Valida una fecha ISO y la devuelve normalizada, con zona horaria.

    Una fecha sin zona se toma como UTC y se avisa: el docente escribe '2026-08-25'
    pensando en Colombia y la ventana se abriría cinco horas antes. Una fecha
    que no se entiende es un error, no un 'sin límite' silencioso.
    """
    if not texto:
        return None
    try:
        f = datetime.fromisoformat(str(texto).replace("Z", "+00:00"))
    except ValueError:
        raise SystemExit(f"[ERROR] No entiendo la fecha de '{nombre}': {texto!r}. "
                         f"Usa ISO 8601, p.ej. 2026-08-25T00:00:00-05:00")
    if f.tzinfo is None:
        print(f"[AVISO] '{nombre}' no trae zona horaria; se toma como UTC "
              f"(Colombia es -05:00).")
        f = f.replace(tzinfo=timezone.utc)
    return f.isoformat()


def main(argv):
    sin_activar = "--sin-activar" in argv
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1

    assignment = args[0]
    abre = _fecha(args[1] if len(args) > 1 else None, "abre")
    cierra = _fecha(args[2] if len(args) > 2 else None, "cierra")
    if abre and cierra and cierra < abre:
        print("[ERROR] 'cierra' es anterior a 'abre'.")
        return 2

    origen = os.path.join(RELEASE, assignment)
    notebooks = sorted(os.path.basename(p) for p in glob.glob(f"{origen}/*.ipynb"))
    if not notebooks:
        print(f"[ERROR] No encontré la versión liberada de '{assignment}'.")
        print("        Primero haz 'Generate' en formgrader (crea release/), y")
        print(f"        que exista {origen}/ con un .ipynb.")
        return 2

    # El notebook que abre el alumno: el primero (normalmente hay uno).
    principal = notebooks[0]

    # Huella del contenido. El entregador del alumno la compara con la que ya
    # tiene: si cambió, le deja la versión nueva AL LADO de la suya (su trabajo
    # está dentro); si solo cambió la ventana, no le toca nada.
    with open(os.path.join(origen, principal), "rb") as f:
        version = hashlib.sha256(f.read()).hexdigest()[:12]

    publicacion = {
        "id": assignment,
        "notebook": principal,
        "abre": abre,
        "cierra": cierra,
        "activar": not sin_activar,
        "version": version,
        "publicado_en": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(origen, ava.FICHERO_PUBLICACION), "w", encoding="utf-8") as f:
        json.dump(publicacion, f, ensure_ascii=False, indent=2)

    try:
        ava.liberar(assignment)
    except ava.ExchangeError as err:
        print(f"[ERROR] No se pudo liberar '{assignment}' en el servicio de intercambio:")
        print(f"        {err}")
        print("        ¿Está arrancado el contenedor 'nbexchange'? (docker compose ps)")
        return 3

    try:
        liberadas, _ = ava.liberados()
    except ava.ExchangeError:
        liberadas = {assignment: {}}

    print(f"[OK] Publicado '{assignment}' (curso {CURSO}).")
    print(f"     Notebook: {principal}")
    print(f"     Ventana: abre={abre or 'siempre'}  cierra={cierra or 'sin límite'}")
    print(f"     Version del contenido: {version}")
    print(f"     Publicados en total: {', '.join(sorted(liberadas))}")
    if sin_activar:
        print("     Publicado SIN activar: el de esta semana sigue siendo el que era.")
    else:
        print(f"     El alumno verá el índice con todos y '{assignment}' marcado como "
              f"el de esta semana.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
