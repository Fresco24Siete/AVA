"""Contenido propio de la SEMANA 3: «Decidir».

Qué es esto
-----------
`motor/ava_motor.py` trae lo común a todas las semanas (barra de XP, quices,
ordenar, pistas, tarjetas) y `motor/pseudo_uis.py` el mini-intérprete de
pseudocódigo. **Este módulo no repite nada de eso.** Aquí vive solo lo de esta
semana: los quices del calentamiento, la tabla de verdad interactiva, la
chuleta de operadores y el evaluador de expresiones.

Cómo se incrusta
----------------
El constructor ejecuta este archivo en la celda de arranque, en el mismo
espacio de nombres y **después** del motor y de `pseudo_uis`. De ahí dos reglas:

- el objeto `ava` todavía no existe cuando este archivo se ejecuta: se busca en
  tiempo de llamada con `_s3_motor()`, nunca en tiempo de definición;
- los nombres propios llevan prefijo `_s3_` / `_S3_` para no pisar los del motor
  ni los de `pseudo_uis`, que comparten espacio con este módulo.

Dependencias: biblioteca estándar. **Sin matplotlib**: son unos 80 MB de RAM por
kernel y el servidor del curso se reparte entre toda la clase a la vez, así que
todo lo visual va como SVG o HTML escrito a mano.
"""
import types

from IPython.display import HTML as _HTML3, display as _display3


# =============================================================================
# Fachada `ps`
# =============================================================================
# `pseudo_uis.py` no se importa: se ejecuta dentro del notebook, así que sus
# funciones quedan sueltas en el espacio global. El estudiante, en cambio, las
# llama siempre como `ps.algo(...)` — es lo que leen los mensajes del propio
# motor. Esta fachada reconstruye ese `ps` con lo que haya en el espacio.
_S3_API_PSEUDO = (
    "ejecutar_pseudo", "traducir_a_python", "diagrama", "tabla_dos_columnas",
    "laboratorio", "trazador", "comparador",
    "guion_flowgorithm", "exportar_flowgorithm",
    "usar_entradas", "restaurar_input", "entradas",
    "Resultado", "Paso", "Error",
)


def _s3_fachada(espacio):
    return types.SimpleNamespace(
        **{n: espacio[n] for n in _S3_API_PSEUDO if n in espacio}
    )


ps = _s3_fachada(globals())


# =============================================================================
# Identidad visual
# =============================================================================
_S3_VIOLETA = "#4a3aa7"
_S3_AZUL = "#2a78d6"
_S3_VERDE = "#0ca30c"
_S3_ROJO = "#d03b3b"
_S3_AMBAR = "#eda100"
_S3_GRIS = "#52514e"
_S3_BORDE = "#dfe3e8"
_S3_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
_S3_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _s3_pintar(html):
    _display3(_HTML3(html))


def _s3_motor():
    """El objeto `ava` en tiempo de llamada, no de definición.

    Cuando este archivo se ejecuta, el motor ya corrió pero `ava` puede no estar
    todavía en el espacio global. Buscarlo aquí evita un NameError que dejaría
    el cuadernillo sin quices y sin XP.
    """
    return globals().get("ava")


def _s3_escapar(texto):
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# =============================================================================
# Calentamiento — tres preguntas de la semana 2
# =============================================================================
def quiz_eps():
    ava = _s3_motor()
    if ava is None:
        return
    return ava.quiz(
        "s3_eps", 5,
        "En la estructura Entrada-Proceso-Salida de un algoritmo que calcula el "
        "total de una compra, ¿qué es el precio unitario?",
        ["Una entrada", "Un proceso", "Una salida", "Una restricción"],
        0,
        "Es un dato que el algoritmo necesita recibir para poder empezar. El "
        "proceso es la multiplicación; la salida es el total.",
    )


def quiz_traza():
    ava = _s3_motor()
    if ava is None:
        return
    return ava.quiz(
        "s3_traza", 5,
        "En una prueba de escritorio, ¿qué anotas en cada fila de la tabla?",
        ["El valor de cada variable después de ejecutar una línea",
         "El resultado final del algoritmo",
         "Los errores que encontraste",
         "El tiempo que tarda cada instrucción"],
        0,
        "Una fila por línea ejecutada y una columna por variable. Es la única "
        "forma de ver dónde se tuerce un algoritmo sin ejecutarlo.",
    )


def quiz_asignacion():
    ava = _s3_motor()
    if ava is None:
        return
    return ava.quiz(
        "s3_asignacion", 5,
        "Si `x` vale 4 y ejecutas `x <- x + 1`, ¿qué pasa?",
        ["Es un error: x no puede estar a los dos lados",
         "x pasa a valer 5",
         "x sigue valiendo 4",
         "Se crea una variable nueva"],
        1,
        "La flecha no es un «igual» de matemáticas: primero se calcula lo de la "
        "derecha con el valor actual (4 + 1 = 5) y ese resultado se guarda en x.",
    )


# =============================================================================
# La tabla de verdad, dibujada
# =============================================================================
# Se dibuja en vez de escribirse en markdown porque el color hace el trabajo:
# de un vistazo se ve que `y` casi siempre es falso y `o` casi siempre verdadero,
# que es exactamente la intuición que hay que llevarse.
_S3_FILAS_Y = [(True, True, True), (True, False, False),
               (False, True, False), (False, False, False)]
_S3_FILAS_O = [(True, True, True), (True, False, True),
               (False, True, True), (False, False, False)]


def _s3_celda(valor):
    color = _S3_VERDE if valor else _S3_ROJO
    texto = "Verdadero" if valor else "Falso"
    return (f'<td style="padding:7px 12px;text-align:center;color:#fff;'
            f'background:{color};font-family:{_S3_MONO};font-size:13px">'
            f'{texto}</td>')


def _s3_tabla(titulo, operador, filas):
    cabecera = (f'<tr><th style="padding:7px 12px;background:#f4f6f8;'
                f'border-bottom:2px solid {_S3_BORDE}">A</th>'
                f'<th style="padding:7px 12px;background:#f4f6f8;'
                f'border-bottom:2px solid {_S3_BORDE}">B</th>'
                f'<th style="padding:7px 12px;background:#f4f6f8;'
                f'border-bottom:2px solid {_S3_BORDE}">A {operador} B</th></tr>')
    cuerpo = "".join(
        "<tr>" + "".join(_s3_celda(v) for v in fila) + "</tr>" for fila in filas)
    return (f'<div style="display:inline-block;margin:0 18px 12px 0;'
            f'vertical-align:top">'
            f'<div style="font:600 14px {_S3_FUENTE};color:{_S3_VIOLETA};'
            f'margin-bottom:6px">{titulo}</div>'
            f'<table style="border-collapse:collapse;border:1px solid {_S3_BORDE}">'
            f'{cabecera}{cuerpo}</table></div>')


def tablas_de_verdad():
    """Las dos tablas que hay que saberse, con el color haciendo de resumen."""
    _s3_pintar(
        '<div style="margin:10px 0">'
        + _s3_tabla("y — exige las dos", "y", _S3_FILAS_Y)
        + _s3_tabla("o — le basta una", "o", _S3_FILAS_O)
        + '<div style="clear:both"></div>'
        f'<p style="font:14px {_S3_FUENTE};color:{_S3_GRIS};max-width:640px;'
        f'margin-top:6px">Mira el color, no las palabras: con <b>y</b> casi todo '
        f'sale falso —hace falta que las dos se cumplan— y con <b>o</b> casi todo '
        f'sale verdadero. Esa es la intuición que te tienes que llevar.</p></div>')


# =============================================================================
# Evaluador de expresiones
# =============================================================================
def evaluar(*expresiones):
    """Evalúa expresiones booleanas y las muestra con su resultado.

    Existe para que el estudiante **pruebe** en vez de adivinar: escribe la
    expresión, ve el valor, y de paso ve cómo la escribiría en pseudocódigo.
    """
    filas = []
    for expresion in expresiones:
        try:
            valor = eval(expresion, {"__builtins__": {}}, {})
            color = _S3_VERDE if valor else _S3_ROJO
            resultado = "Verdadero" if valor else "Falso"
        except Exception as err:
            color, resultado = _S3_AMBAR, f"no se pudo evaluar: {type(err).__name__}"
        filas.append(
            f'<tr><td style="padding:6px 14px;font-family:{_S3_MONO};'
            f'font-size:13.5px;border-bottom:1px solid {_S3_BORDE}">'
            f'{_s3_escapar(expresion)}</td>'
            f'<td style="padding:6px 14px;color:{color};font-weight:600;'
            f'font-family:{_S3_FUENTE};font-size:13.5px;'
            f'border-bottom:1px solid {_S3_BORDE}">{resultado}</td></tr>')
    _s3_pintar(f'<table style="border-collapse:collapse;margin:8px 0;'
               f'border:1px solid {_S3_BORDE}">{"".join(filas)}</table>')


# =============================================================================
# Chuleta de operadores
# =============================================================================
_S3_OPERADORES = [
    ("Relacionales", "comparan dos valores y dan Verdadero o Falso", [
        ("=", "==", "¿son iguales?", "nota == 3"),
        ("<>", "!=", "¿son distintos?", "nota != 3"),
        (">", ">", "¿mayor que?", "nota > 3"),
        ("<", "<", "¿menor que?", "nota < 3"),
        (">=", ">=", "¿mayor o igual?", "nota >= 3"),
        ("<=", "<=", "¿menor o igual?", "nota <= 3"),
    ]),
    ("Lógicos", "combinan respuestas de Verdadero/Falso", [
        ("y", "and", "las dos se cumplen", "nota >= 3 and asistio"),
        ("o", "or", "al menos una se cumple", "beca or descuento"),
        ("no", "not", "le da la vuelta", "not aprobo"),
    ]),
    ("Aritméticos", "calculan un número", [
        ("+", "+", "suma", "3 + 2"),
        ("-", "-", "resta", "3 - 2"),
        ("*", "*", "multiplica", "3 * 2"),
        ("/", "/", "divide (da decimales)", "7 / 2  →  3.5"),
        ("div", "//", "divide y descarta decimales", "7 // 2  →  3"),
        ("mod", "%", "el residuo de la división", "7 % 2  →  1"),
    ]),
]


def chuleta_operadores():
    """La tabla de referencia. Pseudocódigo y Python lado a lado, a propósito:
    el estudiante escribe en los dos idiomas la misma semana y la confusión más
    cara del semestre es usar `=` donde va `==`."""
    bloques = []
    for familia, para_que, filas in _S3_OPERADORES:
        cuerpo = "".join(
            f'<tr>'
            f'<td style="padding:5px 12px;font-family:{_S3_MONO};font-size:13px;'
            f'border-bottom:1px solid {_S3_BORDE}">{_s3_escapar(pseudo)}</td>'
            f'<td style="padding:5px 12px;font-family:{_S3_MONO};font-size:13px;'
            f'color:{_S3_AZUL};border-bottom:1px solid {_S3_BORDE}">'
            f'{_s3_escapar(python)}</td>'
            f'<td style="padding:5px 12px;font:13px {_S3_FUENTE};'
            f'border-bottom:1px solid {_S3_BORDE}">{_s3_escapar(que)}</td>'
            f'<td style="padding:5px 12px;font-family:{_S3_MONO};font-size:12.5px;'
            f'color:{_S3_GRIS};border-bottom:1px solid {_S3_BORDE}">'
            f'{_s3_escapar(ejemplo)}</td></tr>'
            for pseudo, python, que, ejemplo in filas)
        bloques.append(
            f'<div style="margin-bottom:16px">'
            f'<div style="font:600 14.5px {_S3_FUENTE};color:{_S3_VIOLETA}">'
            f'{familia}</div>'
            f'<div style="font:13px {_S3_FUENTE};color:{_S3_GRIS};'
            f'margin-bottom:5px">{para_que}</div>'
            f'<table style="border-collapse:collapse;border:1px solid {_S3_BORDE};'
            f'width:100%;max-width:660px">'
            f'<tr><th style="padding:5px 12px;background:#f4f6f8;text-align:left;'
            f'font:600 12px {_S3_FUENTE}">Pseudocódigo</th>'
            f'<th style="padding:5px 12px;background:#f4f6f8;text-align:left;'
            f'font:600 12px {_S3_FUENTE}">Python</th>'
            f'<th style="padding:5px 12px;background:#f4f6f8;text-align:left;'
            f'font:600 12px {_S3_FUENTE}">Qué hace</th>'
            f'<th style="padding:5px 12px;background:#f4f6f8;text-align:left;'
            f'font:600 12px {_S3_FUENTE}">Ejemplo</th></tr>'
            f'{cuerpo}</table></div>')
    _s3_pintar("".join(bloques))
