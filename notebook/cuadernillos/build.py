#!/usr/bin/env python3
"""Construye los cuadernillos del curso y los deja listos para nbgrader.

    python3 notebook/cuadernillos/build.py            # todos
    python3 notebook/cuadernillos/build.py semana_01  # uno solo
    python3 notebook/cuadernillos/build.py --legible  # motor sin comprimir (depuración)

Qué hace y por qué en este orden:

1. Cada `semana_XX/generador.py` describe su cuadernillo en Python y devuelve un
   objeto `Cuadernillo`. El notebook es una salida generada, no una fuente que se
   edite a mano: así el contenido se revisa en un diff legible y no en el JSON de
   un .ipynb.
2. El resultado se escribe en `notebook/notebook_semana/<codigo>/cuadernillo.ipynb`.
   Esa carpeta va a `/opt/plantillas` en la imagen y `entrypoint.sh` la siembra en
   `source/<codigo>` de nbgrader. De ahí el instructor hace «Generate» (que borra
   las soluciones) y publica con `publicar-cuadernillo <codigo>`.
3. Se valida el resultado: pares de celdas de nbgrader bien formados y
   `grade_id` únicos. Un par mal formado no da error visible en Jupyter, pero
   deja el ejercicio fuera de la nota Y fuera de la telemetría.
"""
import importlib.util
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.abspath(os.path.join(AQUI, "..", "notebook_semana"))
# Mapeo ejercicio -> competencias. Va aparte del notebook a propósito: es diseño
# del curso, no dato del alumno, y el backend lo resuelve por JOIN. Así, corregir
# una etiqueta mal puesta corrige todo el histórico ya recogido.
MAPEO = os.path.join(AQUI, "competencias.json")


def _leer_mapeo():
    """El mapeo acumula todas las semanas, no solo las que se construyen ahora."""
    try:
        with open(MAPEO, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _escribir_mapeo(mapeo):
    with open(MAPEO, "w", encoding="utf-8") as f:
        json.dump(mapeo, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def _generadores():
    for nombre in sorted(os.listdir(AQUI)):
        ruta = os.path.join(AQUI, nombre, "generador.py")
        if os.path.isdir(os.path.join(AQUI, nombre)) and os.path.exists(ruta):
            yield nombre, ruta


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(f"generador_{nombre}", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    if not hasattr(modulo, "construir"):
        raise AttributeError(f"{ruta} debe definir una función construir(**opciones)")
    return modulo


def validar(nb):
    """Revisa los contratos que el AVA da por supuestos. Devuelve lista de fallos."""
    fallos = []
    ids = {}
    soluciones, pruebas = set(), set()

    for i, celda in enumerate(nb["cells"]):
        ng = celda.get("metadata", {}).get("nbgrader")
        if not ng:
            continue
        gid = ng.get("grade_id")
        if not gid:
            fallos.append(f"celda {i}: metadata de nbgrader sin grade_id")
            continue
        if gid in ids:
            fallos.append(f"grade_id duplicado '{gid}' (celdas {ids[gid]} y {i})")
        ids[gid] = i
        if ng.get("solution"):
            soluciones.add(gid)
        if ng.get("grade"):
            pruebas.add(gid)
            if not gid.startswith("test_"):
                fallos.append(
                    f"'{gid}' califica pero no empieza por 'test_': custom.js no "
                    f"emitirá telemetría de este ejercicio"
                )
            if not ng.get("points"):
                fallos.append(f"'{gid}' califica pero no tiene points")

    for gid in sorted(soluciones):
        if f"test_{gid}" not in pruebas:
            fallos.append(f"'{gid}' no tiene su celda de prueba 'test_{gid}'")
    for gid in sorted(pruebas):
        base = gid[len("test_"):]
        if base not in soluciones:
            fallos.append(f"'{gid}' no tiene su celda de solución '{base}'")

    if "tutor_ia" not in nb["metadata"]:
        fallos.append("falta metadata.tutor_ia (el panel del tutor no se dibujará)")
    return fallos


def main(argv):
    legible = "--legible" in argv
    pedidos = [a for a in argv if not a.startswith("-")]

    disponibles = dict(_generadores())
    if not disponibles:
        print(f"[ERROR] No hay generadores en {AQUI}")
        return 2
    if pedidos:
        faltan = [p for p in pedidos if p not in disponibles]
        if faltan:
            print(f"[ERROR] No existe: {', '.join(faltan)}")
            print(f"        Disponibles: {', '.join(disponibles)}")
            return 2
        objetivo = {k: disponibles[k] for k in pedidos}
    else:
        objetivo = disponibles

    problemas = 0
    mapeo = _leer_mapeo()
    for nombre, ruta in objetivo.items():
        print(f"\n== {nombre} ==")
        modulo = _cargar(nombre, ruta)
        cuadernillo = modulo.construir(motor_comprimido=not legible)
        salida = os.path.join(DESTINO, cuadernillo.codigo, "cuadernillo.ipynb")
        cuadernillo.escribir(salida)

        # Un ejercicio sin competencia no da ningún error: simplemente
        # desaparece de los análisis. Por eso se avisa aquí.
        mapeo[cuadernillo.codigo] = cuadernillo.competencias
        sin_etiquetar = [f"ejercicio_{n}" for n, _ in cuadernillo._ejercicios
                         if f"ejercicio_{n}" not in cuadernillo.competencias]
        if sin_etiquetar:
            print(f"     [AVISO] sin competencia asignada: {', '.join(sin_etiquetar)}")
            print( "             No fallan, pero no aparecerán en el análisis por competencia.")
        else:
            print(f"     Competencias: {len(cuadernillo.competencias)} ejercicios etiquetados")

        with open(salida, encoding="utf-8") as f:
            nb = json.load(f)
        fallos = validar(nb)
        if fallos:
            problemas += len(fallos)
            print("     [FALLA LA VALIDACION]")
            for f_ in fallos:
                print(f"       - {f_}")
        else:
            print("     Validación: contratos de nbgrader, telemetría y tutor correctos.")

    _escribir_mapeo(mapeo)
    print(f"\nMapeo de competencias en {os.path.relpath(MAPEO)}")
    print( "Para cargarlo al backend:  cargar-competencias")

    if problemas:
        print(f"\n{problemas} problema(s). Los cuadernillos se escribieron igual, "
              f"pero no los publiques así.")
        return 1
    print("\nListo. Para publicarlos, dentro del contenedor del instructor:")
    for nombre in objetivo:
        print(f"  formgrader -> Generate '{nombre}'  y luego  publicar-cuadernillo {nombre}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
