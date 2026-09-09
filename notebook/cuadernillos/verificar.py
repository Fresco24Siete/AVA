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

    # Todas las celdas de código del cuerpo, no solo los ejercicios. Este bloque
    # existe porque faltaba: un `c.code("iniciar()")` copiado de otra semana
    # construía perfecto, pasaba los contratos, y reventaba con NameError en la
    # PRIMERA celda que ejecuta el estudiante. Lo vio la clase entera antes que
    # nadie aquí. Las celdas de ejercicio se saltan: se comprueban aparte, y su
    # plantilla falla a propósito.
    fallos = 0
    ids_ejercicio = set(celdas)
    # Se ejecutan sobre el MISMO espacio, acumulando, como hace un notebook de
    # verdad: una celda usa lo que dejaron las anteriores. Ejecutarlas aisladas
    # daba una avalancha de NameError falsos.
    cuerpo = dict(base)
    for pos, celda in enumerate(codigos[1:], start=1):
        gid = celda.get("metadata", {}).get("nbgrader", {}).get("grade_id")
        if gid in ids_ejercicio:
            continue        # los ejercicios se comprueban aparte, mas abajo
        fuente = "".join(celda["source"])
        if not fuente.strip():
            continue
        # Las magias de IPython (!pwd, %timeit) no son Python y aqui no hay
        # kernel que las entienda. En Jupyter funcionan; se saltan.
        if any(l.lstrip().startswith(("!", "%")) for l in fuente.splitlines()):
            continue
        # Hay celdas que fallan A PROPOSITO: la semana 1 ensena los tres tipos
        # de error rompiendo codigo adrede. Se reconocen por el comentario, y
        # para esas el fallo es el exito: lo que se comprueba es que sigan
        # fallando, porque una celda que enseña un error y deja de darlo
        # convierte la explicacion en una mentira.
        etiquetas = celda.get("metadata", {}).get("tags", [])
        # "error-sembrado" es la convención que ya usaba el repositorio para las
        # celdas que enseñan un error rompiendo código adrede.
        adrede = ("error-sembrado" in etiquetas
                  or "a propósito" in fuente or "a proposito" in fuente)
        try:
            with contextlib.redirect_stdout(mudo), contextlib.redirect_stderr(mudo):
                exec(compile(fuente, f"celda_{pos}", "exec"), cuerpo)
        except Exception as err:
            if adrede:
                continue
            fallos += 1
            primera = fuente.strip().splitlines()[0][:46]
            print(f"  celda {pos} ({primera}): {type(err).__name__}: "
                  f"{str(err).splitlines()[0][:70]}")
        else:
            if adrede:
                fallos += 1
                print(f"  celda {pos}: dice que falla a proposito y NO falla; "
                      f"la explicacion de al lado ya no es cierta")

    numeros = sorted(int(k.split("_")[1]) for k in celdas
                     if k.startswith("ejercicio_"))
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
