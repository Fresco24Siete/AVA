#!/usr/bin/env python3
"""Que `sin_usar()` cace la construcción prohibida y no cace de más.

Existe porque una restricción mal comprobada hace daño en las dos direcciones:
si no caza, el enunciado miente; si caza de más, el alumno pierde puntos por
una solución correcta y no entiende por qué.

    python3 backend/tests/telemetria/prueba_restricciones.py
"""
import importlib.util
import os
import sys
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
MOTOR = os.path.join(REPO, "notebook", "cuadernillos", "motor", "ava_motor.py")


def _cargar_motor():
    """Mismo truco que prueba_huella: dobles vacíos de IPython (aquí no hay)."""
    for nombre in ("IPython", "IPython.display", "ipywidgets"):
        if nombre not in sys.modules:
            modulo = types.ModuleType(nombre)
            modulo.HTML = modulo.display = lambda *a, **k: None
            sys.modules[nombre] = modulo
    spec = importlib.util.spec_from_file_location("ava_motor_restr", MOTOR)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# --- Soluciones de mentira, una por caso ------------------------------------
def con_for(xs, y):
    for i in range(len(xs)):
        if xs[i] == y:
            return i
    return -1


def con_while(xs, y):
    i = 0
    while i < len(xs):
        if xs[i] == y:
            return i
        i = i + 1
    return -1


def con_comprension(xs, y):
    return [i for i, v in enumerate(xs) if v == y]


def con_for_en_cadena(xs, y):
    # Este 'for' va dentro de un comentario y de un texto, no es un ciclo.
    mensaje = "recorre con for si quieres"
    i = 0
    while i < len(xs):
        if xs[i] == y:
            return mensaje and i
        i = i + 1
    return -1


def _auxiliar_con_for(xs, y):
    for i in range(len(xs)):
        if xs[i] == y:
            return i
    return -1


def delega_en_auxiliar(xs, y):
    # Sin un solo 'for' a la vista: el ciclo esta una llamada mas abajo.
    return _auxiliar_con_for(xs, y)


def delega_en_limpia(xs, y):
    return con_while(xs, y)


def con_sum(xs):
    return sum(xs)


def con_sort(xs):
    xs.sort()
    return xs


def recursiva(n):
    return 1 if n <= 1 else n * recursiva(n - 1)


def main():
    motor = _cargar_motor()
    sin_usar = motor.sin_usar

    pasan = fallan = 0

    def caso(nombre, fn, prohibido, debe_saltar):
        nonlocal pasan, fallan
        try:
            sin_usar(fn, *prohibido)
            salto, mensaje = False, ""
        except AssertionError as e:
            salto, mensaje = True, str(e)
        if salto == debe_saltar:
            pasan += 1
            print(f"OK    {nombre}" + (f"  → {mensaje}" if mensaje else ""))
        else:
            fallan += 1
            esperado = "que saltara" if debe_saltar else "que NO saltara"
            print(f"FALLO {nombre}: se esperaba {esperado}; mensaje={mensaje!r}")

    # Caza lo que debe cazar
    caso("1. 'for' con un for",            con_for,          ("for",),   True)
    caso("2. 'for' con por-comprensión",   con_comprension,  ("for",),   True)
    caso("3. 'while' con un while",        con_while,        ("while",), True)
    caso("4. 'sum' con sum()",             con_sum,          ("sum",),   True)
    caso("5. 'sort' como método",          con_sort,         ("sort",),  True)
    caso("6. recursión que se llama",      recursiva,  ("recursion",),   True)

    # Y NO caza lo que no debe
    caso("7. 'for' con un while",          con_while,        ("for",),   False)
    caso("8. 'for' en comentario y texto", con_for_en_cadena,("for",),   False)
    caso("9. 'while' con un for",          con_for,          ("while",), False)
    caso("10. sin recursión",              con_while, ("recursion",),    False)
    caso("11. varias a la vez, ninguna",   con_while, ("for", "sum", "sorted"), False)

    # El truco de esconder el ciclo en una auxiliar no vale
    caso("13. 'for' escondido en una auxiliar", delega_en_auxiliar, ("for",), True)
    caso("14. delegar en una auxiliar limpia",  delega_en_limpia,   ("for",), False)

    # Sin fuente no puede callar: debe avisar, no dar por bueno.
    try:
        sin_usar(len, "for")
        print("FALLO 12. una función sin fuente pasó como buena"); fallan += 1
    except AssertionError as e:
        print(f"OK    12. sin fuente avisa  → {e}"); pasan += 1

    print(f"\n{pasan}/{pasan + fallan} casos OK")
    sys.exit(1 if fallan else 0)


if __name__ == "__main__":
    main()
