#!/usr/bin/env python3
"""Ejecuta los ejercicios de un cuadernillo ya construido.

`build.py` valida los contratos —pares de celdas, grade_id, puntos, metadatos—
pero no ejecuta una sola línea. Un ejercicio puede construir perfecto y estar
roto: una solución que no corre, una prueba que se contradice, o algo peor —una
plantilla tan completa que el alumno aprueba sin escribir nada.

De cada ejercicio se comprueban las dos mitades:

  1. La SOLUCIÓN del instructor debe pasar las pruebas visibles Y las ocultas.
     Si no, el ejercicio no tiene respuesta correcta y nadie puede sacarlo.
  2. La PLANTILLA que ve el alumno debe FALLAR. Si pasa, el ejercicio está
     regalado y no mide nada. Este es el fallo que nunca se ve mirando el
     notebook, porque a simple vista todo parece bien.

    python3 notebook/cuadernillos/verificar.py            # todos
    python3 notebook/cuadernillos/verificar.py semana_01  # uno

Devuelve 1 si algo falla, para poder encadenarlo con build.py.
"""
import contextlib
import io
import json
import os
import sys
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(os.path.dirname(AQUI), "notebook_semana")

INI_SOL, FIN_SOL = "### INICIO SOLUCION", "### FIN SOLUCION"
INI_OCULTO, FIN_OCULTO = "### INICIO PRUEBAS OCULTAS", "### FIN PRUEBAS OCULTAS"


def _stub_ipython():
    """IPython no está fuera del contenedor y el motor lo usa para pintar HTML.

    Aquí no interesa lo que pinte: lo que se verifica es la lógica. Con el
    sustituto, el arranque del cuadernillo corre en cualquier Python.
    """
    if "IPython" in sys.modules:
        return
    def nada(*a, **k):
        return None
    class Objeto:
        def __init__(self, *a, **k):
            pass
        def _repr_html_(self):
            return ""
    for nombre in ("IPython", "IPython.display", "IPython.core",
                   "IPython.core.display"):
        sys.modules[nombre] = types.ModuleType(nombre)
    display = sys.modules["IPython.display"]
    for attr, valor in (("display", nada), ("HTML", Objeto), ("Markdown", Objeto),
                        ("SVG", Objeto), ("Javascript", Objeto),
                        ("clear_output", nada), ("Image", Objeto)):
        setattr(display, attr, valor)
        setattr(sys.modules["IPython"], attr, valor)
    sys.modules["IPython"].display = display
    sys.modules["IPython"].get_ipython = nada


def _celdas_por_grade_id(nb):
    fuera = {}
    for celda in nb["cells"]:
        gid = celda.get("metadata", {}).get("nbgrader", {}).get("grade_id")
        if gid:
            fuera[gid] = "".join(celda["source"])
    return fuera


def verificar(codigo):
    ruta = os.path.join(SALIDA, codigo, "cuadernillo.ipynb")
    if not os.path.isfile(ruta):
        print(f"  no existe {ruta} — construye primero con build.py")
        return 1

    _stub_ipython()
    with io.open(ruta, encoding="utf-8") as f:
        nb = json.load(f)
    celdas = _celdas_por_grade_id(nb)
    codigos = [c for c in nb["cells"] if c["cell_type"] == "code"]

    # La primera celda de código es el arranque: trae el motor y el contenido
    # de la semana. Todo lo demás se ejecuta sobre una copia de su espacio.
    base = {"__name__": "__main__"}
    mudo = io.StringIO()
    try:
        with contextlib.redirect_stdout(mudo), contextlib.redirect_stderr(mudo):
            exec(compile("".join(codigos[0]["source"]), "arranque", "exec"), base)
    except Exception as err:
        print(f"  el arranque no corre: {type(err).__name__}: {err}")
        return 1

    numeros = sorted(int(k.split("_")[1]) for k in celdas
                     if k.startswith("ejercicio_"))
    fallos = 0
    for n in numeros:
        solucion = celdas[f"ejercicio_{n}"]
        prueba = (celdas[f"test_ejercicio_{n}"]
                  .replace(INI_OCULTO, "").replace(FIN_OCULTO, ""))
        entera = solucion.replace(INI_SOL, "").replace(FIN_SOL, "")
        plantilla = solucion.split(INI_SOL)[0]

        estado = []
        entorno = dict(base)
        try:
            with contextlib.redirect_stdout(mudo), contextlib.redirect_stderr(mudo):
                exec(compile(entera, f"solucion_{n}", "exec"), entorno)
                exec(compile(prueba, f"prueba_{n}", "exec"), entorno)
        except Exception as err:
            fallos += 1
            estado.append(f"la solución NO pasa ({type(err).__name__}: "
                          f"{str(err).splitlines()[0][:90]})")

        entorno = dict(base)
        try:
            with contextlib.redirect_stdout(mudo), contextlib.redirect_stderr(mudo):
                exec(compile(plantilla, f"plantilla_{n}", "exec"), entorno)
                exec(compile(prueba, f"prueba_{n}", "exec"), entorno)
            fallos += 1
            estado.append("la PLANTILLA VACÍA ya aprueba: el ejercicio está regalado")
        except Exception:
            pass

        print(f"  ejercicio {n}: " + ("OK" if not estado else " · ".join(estado)))
    return fallos


def main(argv):
    codigos = argv[1:] or sorted(
        d for d in os.listdir(SALIDA)
        if os.path.isdir(os.path.join(SALIDA, d)))
    total = 0
    for codigo in codigos:
        print(f"\n== {codigo} ==")
        total += verificar(codigo)
    print()
    if total:
        print(f"{total} problema(s). Ningún cuadernillo debería publicarse así.")
        return 1
    print("Todos los ejercicios corren y ninguno está regalado.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
