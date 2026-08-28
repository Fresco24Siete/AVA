"""Contenido propio de la SEMANA 4: «Repetir».

Qué es esto
-----------
El motor común (`motor/ava_motor.py`) y el intérprete de pseudocódigo
(`motor/pseudo_uis.py`) traen lo que sirve todas las semanas. Aquí vive solo lo
de esta: los quices del calentamiento, el contador de vueltas dibujado y la
tabla de traza de un ciclo.

Una nota que condiciona el cuadernillo entero: **el motor de pseudocódigo
entiende `Mientras` pero no `Para`** (ver `pseudo_uis._INSTRUCCIONES`). No es
una carencia que haya que disimular, es una oportunidad: en pseudocódigo se
enseña el ciclo con `Mientras`, que es el que de verdad explica el mecanismo, y
el `Para` aparece en Python presentado como lo que es, un atajo para cuando ya
sabes cuántas vueltas vas a dar.

Cómo se incrusta
----------------
El constructor ejecuta este archivo en la celda de arranque, después del motor y
de `pseudo_uis`, en el mismo espacio de nombres. De ahí las dos reglas de
siempre: `ava` se busca en tiempo de llamada, y los nombres propios llevan
prefijo `_s4_` para no pisar nada.

Dependencias: biblioteca estándar. Sin matplotlib, por la memoria del servidor.
"""
import types

from IPython.display import HTML as _HTML4, display as _display4

_S4_API_PSEUDO = (
    "ejecutar_pseudo", "traducir_a_python", "diagrama", "tabla_dos_columnas",
    "laboratorio", "trazador", "comparador",
    "guion_flowgorithm", "exportar_flowgorithm",
    "usar_entradas", "restaurar_input", "entradas",
    "Resultado", "Paso", "Error",
)


def _s4_fachada(espacio):
    return types.SimpleNamespace(
        **{n: espacio[n] for n in _S4_API_PSEUDO if n in espacio})


ps = _s4_fachada(globals())

_S4_VIOLETA = "#4a3aa7"
_S4_AZUL = "#2a78d6"
_S4_VERDE = "#0ca30c"
_S4_ROJO = "#d03b3b"
_S4_GRIS = "#52514e"
_S4_BORDE = "#dfe3e8"
_S4_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
_S4_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _s4_pintar(html):
    _display4(_HTML4(html))


def _s4_motor():
    return globals().get("ava")


def _s4_escapar(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# =============================================================================
# Calentamiento — tres de la semana 3
# =============================================================================
def quiz_igualdad():
    ava = _s4_motor()
    if ava is None:
        return
    return ava.quiz(
        "s4_igualdad", 5,
        "¿Cuál de estas dos líneas COMPARA, y cuál GUARDA?",
        ["`x = 5` compara y `x == 5` guarda",
         "`x = 5` guarda y `x == 5` compara",
         "Las dos comparan",
         "Las dos guardan"],
        1,
        "Un solo `=` guarda un valor en la variable. Dos `==` preguntan si son "
        "iguales y devuelven Verdadero o Falso.",
    )


def quiz_cadena():
    ava = _s4_motor()
    if ava is None:
        return
    return ava.quiz(
        "s4_cadena", 5,
        "En una cadena `if / elif / else`, ¿cuántas ramas se ejecutan?",
        ["Todas las que se cumplan", "Solo la primera que se cumple",
         "Solo la última", "Ninguna, si no hay else"],
        1,
        "Se prueba de arriba abajo y en cuanto una se cumple, se ejecuta esa y "
        "se salta el resto. Por eso el orden importa tanto.",
    )


def quiz_precedencia():
    ava = _s4_motor()
    if ava is None:
        return
    return ava.quiz(
        "s4_precedencia", 5,
        "¿Cuánto vale `10 % 3`?",
        ["3", "1", "3.33", "0"],
        1,
        "`%` da el RESIDUO: 10 entre 3 son 3 con 1 de sobra. El 3 lo daría "
        "`10 // 3`.",
    )


# =============================================================================
# El contador de vueltas
# =============================================================================
def vueltas(inicio, condicion, paso, tope=12):
    """Dibuja, vuelta a vuelta, cómo cambia una variable dentro de un ciclo.

    Es la prueba de escritorio de la semana 2 aplicada a un ciclo, y existe
    porque el error tipico del primer `while` no es de sintaxis: es no ver
    cuando se deja de cumplir la condicion. Aqui se ve.
    """
    filas, valor, n = [], inicio, 0
    while n < tope:
        try:
            sigue = eval(condicion, {"__builtins__": {}}, {"i": valor})
        except Exception as err:
            filas.append(("—", str(valor), f"no se pudo evaluar: {err}"))
            break
        filas.append((n + 1, str(valor), "sí, entra" if sigue else "no, sale"))
        if not sigue:
            break
        try:
            valor = eval(paso, {"__builtins__": {}}, {"i": valor})
        except Exception as err:
            filas.append(("—", str(valor), f"el paso falla: {err}"))
            break
        n += 1
    else:
        filas.append(("…", str(valor), f"se pasó de {tope} vueltas: revisa el paso"))

    cuerpo = "".join(
        f'<tr><td style="padding:5px 14px;text-align:center;font-family:{_S4_MONO};'
        f'border-bottom:1px solid {_S4_BORDE}">{v}</td>'
        f'<td style="padding:5px 14px;text-align:center;font-family:{_S4_MONO};'
        f'border-bottom:1px solid {_S4_BORDE}">{val}</td>'
        f'<td style="padding:5px 14px;font:13px {_S4_FUENTE};'
        f'color:{_S4_VERDE if "sí" in str(est) else _S4_ROJO};'
        f'border-bottom:1px solid {_S4_BORDE}">{_s4_escapar(est)}</td></tr>'
        for v, val, est in filas)
    _s4_pintar(
        f'<div style="font:600 14px {_S4_FUENTE};color:{_S4_VIOLETA};margin:8px 0 4px">'
        f'i empieza en {inicio} · sigue mientras <code>{_s4_escapar(condicion)}</code>'
        f' · cada vuelta <code>i = {_s4_escapar(paso)}</code></div>'
        f'<table style="border-collapse:collapse;border:1px solid {_S4_BORDE}">'
        f'<tr><th style="padding:5px 14px;background:#f4f6f8;font:600 12px {_S4_FUENTE}">Vuelta</th>'
        f'<th style="padding:5px 14px;background:#f4f6f8;font:600 12px {_S4_FUENTE}">i vale</th>'
        f'<th style="padding:5px 14px;background:#f4f6f8;font:600 12px {_S4_FUENTE}">¿Se cumple?</th></tr>'
        f'{cuerpo}</table>')


# =============================================================================
# Contador, acumulador, bandera
# =============================================================================
_S4_TRES = [
    ("Contador", "cuenta CUÁNTAS veces pasó algo",
     "empieza en 0 y sube de uno en uno", "aprobados = aprobados + 1", _S4_AZUL),
    ("Acumulador", "va SUMANDO valores que llegan",
     "empieza en 0 y le sumas lo que venga", "total = total + nota", _S4_VERDE),
    ("Bandera", "recuerda SI ocurrió algo, aunque fuera una sola vez",
     "empieza en False y solo puede pasar a True", "hubo_perdida = True", _S4_ROJO),
]


def las_tres_variables():
    """Las tres variables que aparecen en casi todo ciclo. Se dibujan juntas
    porque el error es confundirlas: sumar donde había que contar da un numero
    que parece razonable y es falso, y eso no lo avisa nadie."""
    tarjetas = "".join(
        f'<div style="flex:1;min-width:200px;border:1px solid {_S4_BORDE};'
        f'border-top:3px solid {color};border-radius:6px;padding:12px 14px">'
        f'<div style="font:600 15px {_S4_FUENTE};color:{color}">{nombre}</div>'
        f'<div style="font:13.5px {_S4_FUENTE};margin:4px 0 6px">{para}</div>'
        f'<div style="font:12.5px {_S4_FUENTE};color:{_S4_GRIS}">{como}</div>'
        f'<div style="font-family:{_S4_MONO};font-size:12.5px;background:#f6f7f9;'
        f'padding:5px 8px;border-radius:4px;margin-top:7px">{_s4_escapar(ej)}</div>'
        f'</div>'
        for nombre, para, como, ej, color in _S4_TRES)
    _s4_pintar(f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin:10px 0">'
               f'{tarjetas}</div>')
