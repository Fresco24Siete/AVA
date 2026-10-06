"""Contenido propio de la SEMANA 5: «Consolidar».

Qué es esto
-----------
La sesión 1 de esta unidad es la primera evaluación, así que el cuadernillo no
trae examen: trae la **guía de repaso** con la que llegar a él, y el contenido
nuevo de la sesión 2.

Aquí vive solo lo de esta semana: el mapa de lo aprendido, el autodiagnóstico
y el visor de tipos. (La tabla de las tres estructuras y dos de los tres quices
se fueron en el recorte del 2026-09-22: el cuadernillo bajó de 56 a 35 min.)

Una decisión de enfoque que conviene conocer antes de editar: el temario oficial
de la sesión 2 dice «lenguaje compilado e interpretado». El profesor pidió que
no haya comparaciones entre lenguajes ni temas de bajo nivel, así que aquí se
cuenta **solo qué hace Python con tu archivo** —lee, comprueba, ejecuta línea a
línea— sin ponerlo al lado de ningún otro lenguaje. Se cubre el fondo del tema
sin el contenido que quedó fuera.

Dependencias: biblioteca estándar. Sin matplotlib.
"""
import types

from IPython.display import HTML as _HTML5, display as _display5

_S5_API_PSEUDO = (
    "ejecutar_pseudo", "traducir_a_python", "diagrama", "tabla_dos_columnas",
    "laboratorio", "trazador", "comparador",
    "guion_flowgorithm", "exportar_flowgorithm",
    "usar_entradas", "restaurar_input", "entradas",
    "Resultado", "Paso", "Error",
)


def _s5_fachada(espacio):
    return types.SimpleNamespace(
        **{n: espacio[n] for n in _S5_API_PSEUDO if n in espacio})


ps = _s5_fachada(globals())

_S5_VIOLETA = "#4a3aa7"
_S5_AZUL = "#2a78d6"
_S5_VERDE = "#0ca30c"
_S5_ROJO = "#d03b3b"
_S5_AMBAR = "#eda100"
_S5_GRIS = "#52514e"
_S5_BORDE = "#dfe3e8"
_S5_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
_S5_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _s5_pintar(html):
    _display5(_HTML5(html))


def _s5_motor():
    return globals().get("ava")


def _s5_escapar(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# =============================================================================
# El mapa de lo aprendido
# =============================================================================
# Cuatro semanas en una sola imagen. No es decoración: en un repaso lo primero
# que hace falta es ver el conjunto, porque el estudiante llega con cuatro
# cuadernillos sueltos y ninguna idea de cómo encajan.
_S5_EJES = [
    ("Semana 1", "El entorno", _S5_AZUL,
     ["celdas y kernel", "variables y tipos", "los tres errores", "archivos"]),
    ("Semana 2", "Del problema al algoritmo", _S5_VIOLETA,
     ["Entrada-Proceso-Salida", "pseudocódigo", "diagramas de flujo",
      "prueba de escritorio"]),
    ("Semana 3", "Decidir", _S5_AMBAR,
     ["expresiones booleanas", "operadores", "if / elif / else", "precedencia"]),
    ("Semana 4", "Repetir", _S5_VERDE,
     ["while y for", "contador y acumulador", "bandera", "ciclos anidados"]),
]


def mapa_del_curso():
    """Las cuatro semanas, una al lado de otra, con lo que hay que llevarse."""
    columnas = "".join(
        f'<div style="flex:1;min-width:170px;border:1px solid {_S5_BORDE};'
        f'border-top:4px solid {color};border-radius:6px;padding:12px 14px">'
        f'<div style="font:600 12px {_S5_FUENTE};color:{_S5_GRIS};'
        f'text-transform:uppercase;letter-spacing:.4px">{semana}</div>'
        f'<div style="font:600 15px {_S5_FUENTE};color:{color};margin:2px 0 8px">'
        f'{titulo}</div>'
        + "".join(f'<div style="font:13px {_S5_FUENTE};padding:3px 0;'
                  f'border-top:1px solid #f0f2f4">{_s5_escapar(t)}</div>'
                  for t in temas)
        + '</div>'
        for semana, titulo, color, temas in _S5_EJES)
    _s5_pintar(f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin:10px 0">'
               f'{columnas}</div>')


# =============================================================================
# Autodiagnóstico
# =============================================================================
def quiz_errores():
    ava = _s5_motor()
    if ava is None:
        return
    return ava.quiz(
        "s5_errores", 5,
        "Un programa corre completo, sin ningún mensaje rojo, y da un resultado "
        "equivocado. ¿Qué tipo de error tiene?",
        ["De sintaxis", "De ejecución", "De lógica", "Ninguno: si corre, está bien"],
        2,
        "El de lógica es el único que no avisa. Por eso es el peligroso: hay que "
        "cazarlo probando, no esperando a que salga un mensaje.",
    )


# =============================================================================
# Visor de tipos
# =============================================================================
def ver_tipos(*valores):
    """Muestra qué tipo tiene cada valor y por qué importa.

    Python no te obliga a declarar el tipo, pero eso no significa que no exista:
    significa que lo decide él al ejecutar. Verlo es la forma rápida de entender
    por qué `"3" + "4"` da "34" y no 7.
    """
    filas = []
    for v in valores:
        try:
            valor = eval(v, {"__builtins__": {"True": True, "False": False}}, {})
            tipo = type(valor).__name__
            color = {"int": _S5_AZUL, "float": _S5_VIOLETA,
                     "str": _S5_VERDE, "bool": _S5_AMBAR}.get(tipo, _S5_GRIS)
            resultado = repr(valor)
        except Exception as err:
            tipo, color, resultado = type(err).__name__, _S5_ROJO, str(err)[:60]
        filas.append(
            f'<tr><td style="padding:6px 14px;font-family:{_S5_MONO};font-size:13px;'
            f'border-bottom:1px solid {_S5_BORDE}">{_s5_escapar(v)}</td>'
            f'<td style="padding:6px 14px;font-family:{_S5_MONO};font-size:13px;'
            f'border-bottom:1px solid {_S5_BORDE}">{_s5_escapar(resultado)}</td>'
            f'<td style="padding:6px 14px;font:600 13px {_S5_FUENTE};color:{color};'
            f'border-bottom:1px solid {_S5_BORDE}">{tipo}</td></tr>')
    _s5_pintar(
        f'<table style="border-collapse:collapse;border:1px solid {_S5_BORDE};margin:8px 0">'
        f'<tr>' + "".join(
            f'<th style="padding:6px 14px;background:#f4f6f8;text-align:left;'
            f'font:600 12px {_S5_FUENTE}">{h}</th>'
            for h in ("Escribes", "Da", "Y su tipo es"))
        + f'</tr>{"".join(filas)}</table>')

# =============================================================================
# Portada
# =============================================================================
def portada():
    """Tarjeta de bienvenida: la primera salida que produce el propio kernel.

    Cada semana tiene la suya, con su titulo y sus datos. No esta en el motor
    comun a proposito: es lo unico que identifica de un vistazo en que
    cuadernillo esta el estudiante.
    """
    _s5_pintar(
        f'<div style="font-family:{_S5_FUENTE};background:linear-gradient(135deg,'
        f'#2e2377,{_S5_AZUL});color:#fff;border-radius:10px;padding:18px 22px;'
        'margin:6px 0 10px">'
        '<div style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;'
        'opacity:.82">Semana 5 · Unidad 5</div>'
        '<div style="font-size:26px;font-weight:700;margin:2px 0 6px">Consolidar</div>'
        '<div style="font-size:14.5px;line-height:1.5;opacity:.94">Media vuelta: repaso de las cuatro semanas y Python por dentro.<br>'
        '<span style="opacity:.8">30 puntos · 5 XP · insignia «Media vuelta»</span></div></div>')


# Alias: los cuadernillos 1 y 2 estrenaron dos nombres distintos para lo mismo
# --iniciar() y portada()-- y conviene que los dos funcionen en todas las
# semanas. Que un alumno escriba el de otro cuadernillo y le salte un NameError
# en la PRIMERA celda es la peor bienvenida posible, y ya paso una vez.
iniciar = portada
