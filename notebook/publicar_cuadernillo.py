#!/usr/bin/env python3
"""Publica un cuadernillo para los alumnos (lo corre el INSTRUCTOR).

nbgrader es la fuente del contenido: el instructor autora en source/, hace
"Generate" (que quita las soluciones -> release/) y luego publica con este
comando, definiendo la ventana de tiempo. El backend NO decide nada de esto.

Uso:
    publicar-cuadernillo <assignment> [abre_iso] [cierra_iso]

Ejemplos:
    publicar-cuadernillo semana_1
    publicar-cuadernillo semana_1 2026-08-01T00:00:00Z 2026-08-08T23:59:00Z

Copia el/los .ipynb liberados de release/<assignment>/ (o del exchange) al
volumen compartido de publicados y escribe el manifest que leerá el alumno.
"""
import glob
import hashlib
import json
import os
import shutil
import sys

CURSO = os.environ.get("CURSO_ID", "curso_default")
PUB_DIR = f"/srv/publicados/{CURSO}"


def _origen_release(assignment):
    """Ubica el directorio con la versión liberada (sin soluciones)."""
    candidatos = [
        f"/srv/nbgrader/{CURSO}/release/{assignment}",              # salida de "Generate"
        f"/srv/nbgrader/exchange/{CURSO}/outbound/{assignment}",    # tras "Release"
    ]
    for d in candidatos:
        if os.path.isdir(d) and glob.glob(f"{d}/*.ipynb"):
            return d
    return None


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1

    assignment = argv[1]
    abre = argv[2] if len(argv) > 2 else None
    cierra = argv[3] if len(argv) > 3 else None

    origen = _origen_release(assignment)
    if not origen:
        print(f"[ERROR] No encontré la versión liberada de '{assignment}'.")
        print("        Primero haz 'Generate' en formgrader (crea release/), y")
        print(f"        que exista {CURSO}/release/{assignment}/ con un .ipynb.")
        return 2

    destino = f"{PUB_DIR}/{assignment}"
    os.makedirs(destino, exist_ok=True)

    notebooks = [os.path.basename(p) for p in glob.glob(f"{origen}/*.ipynb")]
    for nb in notebooks:
        shutil.copyfile(f"{origen}/{nb}", f"{destino}/{nb}")

    # El notebook que abre el alumno: el primero (normalmente hay uno).
    principal = sorted(notebooks)[0]

    # El manifest acumula TODOS los cuadernillos publicados, no solo el último:
    # el alumno entra a un índice y puede volver a los de semanas anteriores.
    # Se conservan 'cuadernillo_id' y 'notebook' en la raíz porque marcan cuál es
    # el activo —el de esta semana— y porque el entregador antiguo los leía así.
    os.makedirs(PUB_DIR, exist_ok=True)
    ruta_manifest = f"{PUB_DIR}/manifest.json"
    try:
        with open(ruta_manifest, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        manifest = {}

    publicados = manifest.get("cuadernillos") or []
    # Si el manifest venía del formato viejo (un solo cuadernillo), se rescata
    # para no perder de la lista lo que ya estaba publicado.
    if not publicados and manifest.get("cuadernillo_id"):
        publicados = [{
            "id": manifest["cuadernillo_id"],
            "notebook": manifest.get("notebook", "cuadernillo.ipynb"),
            "abre": manifest.get("abre"),
            "cierra": manifest.get("cierra"),
        }]

    # Huella del contenido publicado. Sirve para que el entregador sepa si lo
    # que tiene el alumno corresponde a ESTA version o a una anterior, sin que
    # nadie tenga que llevar un numero de version a mano.
    with open(f"{destino}/{principal}", "rb") as f:
        version = hashlib.sha256(f.read()).hexdigest()[:12]

    entrada = {"id": assignment, "notebook": principal, "abre": abre,
               "cierra": cierra, "version": version}
    publicados = [c for c in publicados if c.get("id") != assignment] + [entrada]
    publicados.sort(key=lambda c: str(c.get("id")))

    manifest = {
        "cuadernillo_id": assignment,   # el activo: el que se marca en el índice
        "notebook": principal,
        "abre": abre,
        "cierra": cierra,
        "cuadernillos": publicados,
    }
    with open(ruta_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[OK] Publicado '{assignment}' (curso {CURSO}).")
    print(f"     Notebook activo: {principal}")
    print(f"     Ventana: abre={abre or 'siempre'}  cierra={cierra or 'sin límite'}")
    print(f"     Version del contenido: {version}")
    print(f"     Publicados en total: {', '.join(c['id'] for c in publicados)}")
    print(f"     El alumno verá el índice con todos y '{assignment}' marcado como el de esta semana.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
