#!/usr/bin/env python3
"""Que la huella del constructor y la del motor den lo mismo.

Hay dos copias de la misma función a propósito: `constructor.huella` calcula al
CONSTRUIR el cuadernillo, y `ava_motor.huella` corre DENTRO del cuadernillo,
donde no se puede importar el constructor. Si se separaran, el cuadernillo le
diría al alumno que todas sus respuestas están mal y el mensaje no daría
ninguna pista de por qué.

Esta prueba es lo que impide que eso pase en silencio.

    python3 backend/tests/telemetria/prueba_huella.py
"""
import importlib.util
import os
import sys
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
CUADERNILLOS = os.path.join(REPO, "notebook", "cuadernillos")
MOTOR = os.path.join(CUADERNILLOS, "motor", "ava_motor.py")


def _cargar_motor():
    """ava_motor importa IPython e ipywidgets, que aquí no hacen falta ni están.

    Se cargan dobles vacíos: lo único que se prueba es `huella`, que solo usa
    hashlib. Es preferible a copiar la función a la prueba, porque así se
    verifica la de verdad.
    """
    for nombre in ("IPython", "IPython.display", "ipywidgets"):
        if nombre not in sys.modules:
            modulo = types.ModuleType(nombre)
            modulo.HTML = modulo.display = lambda *a, **k: None
            sys.modules[nombre] = modulo

    spec = importlib.util.spec_from_file_location("ava_motor_prueba", MOTOR)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def main():
    sys.path.insert(0, CUADERNILLOS)
    from constructor import huella as huella_constructor

    motor = _cargar_motor()
    huella_motor = motor.huella

    casos = [
        ("ejercicio_1", "a", True),
        ("ejercicio_1", "b", False),
        ("ejercicio_1", "a", False),      # mismo sitio, otra respuesta
        ("ejercicio_2", "a", True),       # otra pregunta, misma respuesta
        ("ejercicio_4", "p", 4),
        ("ejercicio_4", "r", 5),
        ("ejercicio_6", "s", "texto"),
        ("ejercicio_3", "x", 3.5),
        ("ejercicio_3", "y", None),
    ]

    fallos = 0
    for ejercicio, llave, valor in casos:
        a = huella_constructor(ejercicio, llave, valor)
        b = huella_motor(ejercicio, llave, valor)
        if a != b:
            fallos += 1
            print(f"FALLO  {ejercicio}/{llave}={valor!r}: constructor={a} motor={b}")
    if not fallos:
        print(f"OK     las {len(casos)} huellas coinciden entre constructor y motor")

    # Dos respuestas distintas no pueden dar la misma huella, y la misma
    # respuesta en dos preguntas distintas tampoco: si colisionaran, el
    # cuadernillo daría por buena una respuesta equivocada.
    todas = {huella_constructor(*c) for c in casos}
    if len(todas) != len(casos):
        fallos += 1
        print(f"FALLO  hay huellas repetidas: {len(todas)} distintas de {len(casos)}")
    else:
        print("OK     ninguna huella se repite entre casos distintos")

    # Y la huella no puede llevar la respuesta dentro: es lo único que impide
    # que el alumno la lea en la celda.
    h = huella_constructor("ejercicio_1", "a", "MANZANA")
    if "MANZANA" in h or "manzana" in h.lower():
        fallos += 1
        print("FALLO  la huella contiene la respuesta en claro")
    else:
        print("OK     la huella no deja ver la respuesta")

    print(f"\n{'TODO OK' if not fallos else str(fallos) + ' FALLO(S)'}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
