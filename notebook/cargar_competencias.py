#!/usr/bin/env python3
"""Carga al backend qué competencia evalúa cada ejercicio (lo corre el INSTRUCTOR).

    cargar-competencias                 usa el mapeo de la imagen
    cargar-competencias mapeo.json      usa otro archivo

El mapeo lo emite `build.py` al construir los cuadernillos, en
`notebook/cuadernillos/competencias.json`. De ahí viaja a la imagen y este
comando lo sube.

Por qué existe: la competencia NO viaja con cada intento de los estudiantes. Vive
en el backend y se resuelve por JOIN al consultar, de modo que si un ejercicio
queda mal etiquetado y se corrige más adelante, todo el histórico ya recogido se
corrige solo. Si viajara en el evento, esos datos serían incorregibles.

Reemplaza el mapeo de los cuadernillos que vengan en el archivo y no toca los
demás.
"""
import json
import os
import sys
import urllib.error
import urllib.request

MAPEO = os.environ.get("COMPETENCIAS_MAPEO", "/opt/plantillas/competencias.json")
BASE = os.environ.get("METRICS_API_BASE",
                      os.environ.get("STUDENT_METRICS_API_BASE", "http://api_go:8080"))
TOKEN = os.environ.get("METRICS_API_TOKEN", "")


def main(argv):
    ruta = argv[1] if len(argv) > 1 else MAPEO

    if not TOKEN:
        print("[ERROR] Falta METRICS_API_TOKEN: es el que autoriza a cargar el mapeo.")
        return 2

    try:
        with open(ruta, encoding="utf-8") as f:
            mapeo = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] No encontré el mapeo en {ruta}.")
        print("        Lo genera 'build.py' al construir los cuadernillos.")
        return 2
    except ValueError as err:
        print(f"[ERROR] El mapeo no es JSON válido: {err}")
        return 2

    if not mapeo:
        print("[ERROR] El mapeo está vacío; no se envía nada.")
        return 2

    total = sum(len(c) for ejs in mapeo.values() for c in ejs.values())
    print(f"Enviando {len(mapeo)} cuadernillo(s), {total} relación(es):")
    for cuadernillo, ejercicios in sorted(mapeo.items()):
        print(f"  {cuadernillo}: {len(ejercicios)} ejercicios")

    peticion = urllib.request.Request(
        BASE.rstrip("/") + "/internal/competencias",
        data=json.dumps(mapeo).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {TOKEN}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=10) as resp:
            cuerpo = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        print(f"[ERROR] El backend respondió {err.code}: "
              f"{err.read()[:200].decode('utf-8', 'replace')}")
        return 3
    except Exception as err:
        print(f"[ERROR] No se pudo contactar al backend en {BASE}: {err}")
        return 3

    print(f"\n[OK] {cuerpo.get('message')}: "
          f"{cuerpo.get('relaciones')} relaciones en {cuerpo.get('cuadernillos')} cuadernillo(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
