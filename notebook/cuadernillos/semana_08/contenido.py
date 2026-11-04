"""Contenido propio de la SEMANA 8: «Funciones y colecciones».

Qué es esto
-----------
Lo de esta semana y nada más: el quiz del calentamiento, la anatomía de una
función dibujada sobre código de verdad, la tabla de «tupla, diccionario o
conjunto» y el visor de la bolsa de palabras — que es la pieza que convierte
«elige la estructura» en algo que se ve.

El gancho de la semana, y por qué el cuadernillo está armado así
---------------------------------------------------------------
El alumno **escribe funciones con `def` y `return` desde la semana 1** y nunca
se las explicaron: revisados los seis cuadernillos anteriores, no hay una sola
sección dedicada a funciones. Así que esta semana no estrena un tema, le pone
nombre a lo que ya hace. De ahí que `_s8_anatomia()` etiquete una función que
el alumno reconoce en vez de presentar una nueva: el salto cognitivo es
«aprender el vocabulario de algo que ya domino», que es mucho más corto que
«aprender una herramienta nueva».

Dos límites que condicionan el diseño, dichos en voz alta dentro del cuadernillo
--------------------------------------------------------------------------------
1. **El intérprete de pseudocódigo del curso no tiene funciones.** Comprobado
   ejecutándolo: `Funcion`, `SubProceso`, `Retornar` y `Dimension` están en la
   tabla `_NO_TENGO` de `motor/pseudo_uis.py` y devuelven el error PS06 («este
   motor no tiene funciones propias»). La planeación pide «*args y **kwargs en
   pseudocódigo y Python»; en pseudocódigo del curso eso es literalmente
   imposible, así que esta semana el pseudocódigo no se ejecuta y todo lo
   calificable es Python. Igual que hizo la semana 6 con las listas.
2. **El alumno no ha visto tuplas, conjuntos ni métodos de diccionario.** Todo
   lo que necesita una solución —`set()`, `len()`, `in`, `.get()`, `.items()`,
   `return a, b`— se enseña antes, en este mismo cuadernillo. Nada de lo que se
   califica depende de algo que no esté arriba.

Una decisión sobre `bolsa_y_vocabulario()`: cuenta las palabras **dentro** de su
propio cuerpo, sin una función auxiliar de módulo. No es estilo: si existiera un
`_s8_contar(palabras)` en el espacio global, el ejercicio de `bolsa_de_palabras`
se resolvería llamándolo y dejaría de medir nada. Y pinta HTML y devuelve `None`, así que
`return bolsa_y_vocabulario(...)` tampoco sirve de atajo.

Dependencias: biblioteca estándar. Sin matplotlib.
"""
from IPython.display import HTML as _HTML8, display as _display8

_S8_VIOLETA = "#4a3aa7"
_S8_AZUL = "#2a78d6"
_S8_VERDE = "#0ca30c"
_S8_ROJO = "#d03b3b"
_S8_AMBAR = "#eda100"
_S8_GRIS = "#52514e"
_S8_BORDE = "#dfe3e8"
_S8_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
_S8_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _s8_pintar(html):
    _display8(_HTML8(html))


def _s8_motor():
    return globals().get("ava")


def _s8_escapar(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# =============================================================================
# Calentamiento
# =============================================================================
def quiz_retorno():
    """La pregunta con la que arranca la semana.

    No repasa la semana pasada: repasa `return`, que el alumno usa desde la
    semana 1 sin que nadie se lo explicara. Y pregunta por el error que todos
    han cometido —olvidar el `return` y creer que la función «ya calculó»—
    porque reconocerlo es lo que hace que el resto del cuadernillo importe.
    """
    ava = _s8_motor()
    if ava is None:
        return
    return ava.quiz(
        "s8_retorno", 5,
        "A esta función alguien le borró el `return`: `def promedio(a, b):` y "
        "dentro `(a + b) / 2`. La cuenta sigue estando bien escrita. "
        "¿Qué recibe quien la llame?",
        ["El promedio: la cuenta está hecha",
         "`None`: sin `return`, el resultado se calcula y se tira",
         "Un error de sintaxis, porque falta el `return`",
         "El último número que se escribió en pantalla"],
        1,
        "La cuenta se hace y el resultado se tira a la basura. Una función sin "
        "`return` devuelve `None`, y `None` no se puede sumar ni comparar: el "
        "error aparece más tarde y en otra línea, que es lo que lo hace difícil "
        "de encontrar.",
    )


# =============================================================================
# La anatomía de una función, etiquetada sobre código que el alumno reconoce
# =============================================================================
# Esta es la pieza del gancho. El ejemplo no es inventado: es la forma exacta
# de las funciones que el alumno viene escribiendo desde la semana 1 (recibe
# datos, calcula, devuelve). Lo único nuevo es el vocabulario.
#
# Ojo con el ejemplo: el valor por defecto va en `escala`, no en `total`. Un
# `total=0` por defecto haría que `exactitud(5)` reventara con
# ZeroDivisionError, y el primer ejemplo de la semana no puede ser una función
# que se rompe sola en cuanto alguien la llama como la tabla dice que se puede.
_S8_PIEZAS = [
    ("def", "la palabra que abre la definición",
     "Siempre igual. Avisa a Python de que viene una función."),
    ("exactitud", "el nombre",
     "Con él la llamas luego. Lo eliges tú, como el de una variable."),
    ("aciertos, total", "los parámetros",
     "Los datos que la función necesita para trabajar. Son nombres vacíos "
     "hasta que alguien la llama."),
    ("escala=100", "un valor por defecto",
     "Lo que vale ese parámetro si quien llama no lo dice. Así "
     "<code>exactitud(41, 50)</code> ya da un porcentaje. Esto es nuevo "
     "esta semana."),
    ("return", "lo que DEVUELVE",
     "El resultado que sale de la función. Sin él, la función devuelve "
     "<code>None</code>."),
]


def anatomia():
    """Dibuja una función con cada pieza etiquetada y explicada."""
    codigo = (
        f'<span style="color:{_S8_VIOLETA};font-weight:700">def</span> '
        f'<span style="color:{_S8_AZUL};font-weight:700">exactitud</span>'
        f'(<span style="color:{_S8_AMBAR};font-weight:700">aciertos, total</span>, '
        f'<span style="color:{_S8_ROJO};font-weight:700">escala=100</span>):<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;'
        f'<span style="color:{_S8_VERDE};font-weight:700">return</span> '
        f'aciertos / total * escala'
    )
    colores = [_S8_VIOLETA, _S8_AZUL, _S8_AMBAR, _S8_ROJO, _S8_VERDE]
    filas = "".join(
        f'<tr><td style="padding:6px 14px;font-family:{_S8_MONO};font-size:13.5px;'
        f'font-weight:700;color:{color};white-space:nowrap;'
        f'border-bottom:1px solid {_S8_BORDE}">{_s8_escapar(trozo)}</td>'
        f'<td style="padding:6px 14px;font:600 13.5px {_S8_FUENTE};color:{color};'
        f'white-space:nowrap;border-bottom:1px solid {_S8_BORDE}">{nombre}</td>'
        f'<td style="padding:6px 14px;font:13px {_S8_FUENTE};color:{_S8_GRIS};'
        f'border-bottom:1px solid {_S8_BORDE}">{que}</td></tr>'
        for (trozo, nombre, que), color in zip(_S8_PIEZAS, colores))
    _s8_pintar(
        f'<div style="margin:10px 0">'
        f'<div style="font:600 13.5px {_S8_FUENTE};color:{_S8_VIOLETA};'
        f'margin-bottom:6px">Esto ya lo escribes. Ahora cada parte tiene nombre'
        f'</div>'
        f'<div style="font-family:{_S8_MONO};font-size:15px;line-height:1.7;'
        f'background:#f7f8fa;border:1px solid {_S8_BORDE};border-radius:8px;'
        f'padding:12px 16px;margin-bottom:8px">{codigo}</div>'
        f'<table style="border-collapse:collapse;border:1px solid {_S8_BORDE}">'
        f'{filas}</table></div>')


# =============================================================================
# Tupla, diccionario o conjunto: la tabla de decisión
# =============================================================================
# El resultado esperado de la semana es SELECCIONAR la estructura, no recitar
# métodos. Así que la tabla se organiza por la PREGUNTA que cada estructura
# responde, no por su sintaxis: es la forma en que hay que pensarla cuando
# llega un problema nuevo.
_S8_COLECCIONES = [
    ("tupla", "( )", "#7a4fd0",
     "Un grupo de datos que <b>no va a cambiar</b>",
     '("positiva", "negativa", "neutra")',
     "las clases que puede predecir un clasificador: son las que son"),
    ("diccionario", "{clave: valor}", _S8_AZUL,
     "<b>Asociar</b> cada cosa con un dato suyo",
     '{"gato": 3, "perro": 1}',
     "cuántas veces aparece cada palabra en un texto: una bolsa de palabras"),
    ("conjunto", "{ }  /  set()", _S8_VERDE,
     "Los elementos <b>distintos</b>, y preguntar si algo <b>está</b>",
     '{"gato", "perro"}',
     "el vocabulario de un corpus: cada palabra una sola vez"),
]


def tabla_colecciones():
    """Las tres estructuras, puestas una al lado de otra por lo que resuelven."""
    filas = "".join(
        f'<tr>'
        f'<td style="padding:9px 14px;font:700 14px {_S8_FUENTE};color:{color};'
        f'border-bottom:1px solid {_S8_BORDE};white-space:nowrap">{nombre}<br>'
        f'<span style="font-family:{_S8_MONO};font-size:12px;font-weight:400;'
        f'color:{_S8_GRIS}">{_s8_escapar(sintaxis)}</span></td>'
        f'<td style="padding:9px 14px;font:14px {_S8_FUENTE};'
        f'border-bottom:1px solid {_S8_BORDE}">{para}</td>'
        f'<td style="padding:9px 14px;font-family:{_S8_MONO};font-size:12.5px;'
        f'color:{_S8_GRIS};border-bottom:1px solid {_S8_BORDE}">'
        f'{_s8_escapar(ejemplo)}</td>'
        f'<td style="padding:9px 14px;font:13px {_S8_FUENTE};color:{_S8_GRIS};'
        f'border-bottom:1px solid {_S8_BORDE}">{ia}</td></tr>'
        for nombre, sintaxis, color, para, ejemplo, ia in _S8_COLECCIONES)
    _s8_pintar(
        f'<div style="font:600 14px {_S8_FUENTE};color:{_S8_VIOLETA};'
        f'margin:8px 0 4px">La pregunta decide la estructura</div>'
        f'<table style="border-collapse:collapse;border:1px solid {_S8_BORDE}">'
        f'<tr>'
        f'<th style="padding:7px 14px;text-align:left;font:600 12px {_S8_FUENTE};'
        f'color:{_S8_GRIS};text-transform:uppercase;letter-spacing:.05em;'
        f'border-bottom:2px solid {_S8_BORDE}">Estructura</th>'
        f'<th style="padding:7px 14px;text-align:left;font:600 12px {_S8_FUENTE};'
        f'color:{_S8_GRIS};text-transform:uppercase;letter-spacing:.05em;'
        f'border-bottom:2px solid {_S8_BORDE}">Cuándo</th>'
        f'<th style="padding:7px 14px;text-align:left;font:600 12px {_S8_FUENTE};'
        f'color:{_S8_GRIS};text-transform:uppercase;letter-spacing:.05em;'
        f'border-bottom:2px solid {_S8_BORDE}">Se ve así</th>'
        f'<th style="padding:7px 14px;text-align:left;font:600 12px {_S8_FUENTE};'
        f'color:{_S8_GRIS};text-transform:uppercase;letter-spacing:.05em;'
        f'border-bottom:2px solid {_S8_BORDE}">En tu carrera</th></tr>'
        f'{filas}</table>'
        f'<p style="font:13.5px {_S8_FUENTE};color:{_S8_GRIS};max-width:700px;'
        f'margin-top:8px">Una lista también sirve para casi todo, y por eso es '
        f'la trampa: si lo que necesitas es saber si algo <i>está</i>, un '
        f'conjunto lo responde de un golpe mientras la lista los mira uno por '
        f'uno — lo que medimos en la semana 6.</p>')


# =============================================================================
# El visor de la bolsa de palabras
# =============================================================================
# La pieza que justifica el cuadernillo: las tres estructuras SOBRE LOS MISMOS
# DATOS, cada una respondiendo a una pregunta distinta. «Elige la estructura
# adecuada» no se entiende con una definición; se entiende viendo que el
# conjunto no sabe cuántas veces y el diccionario sí.
#
# Cuenta dentro de su propio cuerpo, a propósito: sin un `_s8_contar` suelto en
# el espacio global, `bolsa_de_palabras` no se puede resolver llamándolo. Y devuelve
# None, así que tampoco sirve como atajo.
def bolsa_y_vocabulario(frase):
    """Pinta la misma frase vista como lista, como conjunto y como diccionario."""
    palabras = frase.lower().split()
    vocabulario = sorted(set(palabras))
    bolsa = {}
    for palabra in palabras:
        bolsa[palabra] = bolsa.get(palabra, 0) + 1

    fichas = "".join(
        f'<span style="display:inline-block;font-family:{_S8_MONO};'
        f'font-size:12.5px;background:#f0f2f6;border:1px solid {_S8_BORDE};'
        f'border-radius:5px;padding:2px 8px;margin:2px 3px 2px 0">'
        f'{_s8_escapar(p)}</span>' for p in palabras)
    unicas = "".join(
        f'<span style="display:inline-block;font-family:{_S8_MONO};'
        f'font-size:12.5px;background:#e9f7e9;border:1px solid #bfe3bf;'
        f'color:#0a6b0a;border-radius:5px;padding:2px 8px;margin:2px 3px 2px 0">'
        f'{_s8_escapar(p)}</span>' for p in vocabulario)
    maximo = max(bolsa.values()) if bolsa else 1
    cuenta = "".join(
        f'<tr><td style="padding:3px 12px 3px 0;font-family:{_S8_MONO};'
        f'font-size:13px;text-align:right">{_s8_escapar(p)}</td>'
        f'<td style="padding:3px 0"><span style="display:inline-block;'
        f'height:12px;width:{int(90 * n / maximo)}px;background:{_S8_AZUL};'
        f'border-radius:2px;vertical-align:middle"></span>'
        f'<span style="font-family:{_S8_MONO};font-size:12.5px;'
        f'color:{_S8_GRIS};margin-left:7px">{n}</span></td></tr>'
        for p, n in sorted(bolsa.items(), key=lambda par: (-par[1], par[0])))

    _s8_pintar(
        f'<div style="font-family:{_S8_FUENTE};margin:10px 0;max-width:720px">'
        f'<div style="font:600 13.5px {_S8_FUENTE};color:{_S8_VIOLETA}">'
        f'«{_s8_escapar(frase)}»</div>'
        f'<div style="font:12px {_S8_FUENTE};color:{_S8_GRIS};'
        f'margin:10px 0 2px;text-transform:uppercase;letter-spacing:.05em">'
        f'Lista — las {len(palabras)} palabras, en orden y con repeticiones</div>'
        f'{fichas}'
        f'<div style="font:12px {_S8_FUENTE};color:{_S8_GRIS};'
        f'margin:12px 0 2px;text-transform:uppercase;letter-spacing:.05em">'
        f'Conjunto — el vocabulario: {len(vocabulario)} palabras distintas</div>'
        f'{unicas}'
        f'<div style="font:12px {_S8_FUENTE};color:{_S8_GRIS};'
        f'margin:12px 0 2px;text-transform:uppercase;letter-spacing:.05em">'
        f'Diccionario — cuántas veces aparece cada una</div>'
        f'<table style="border-collapse:collapse">{cuenta}</table>'
        f'<p style="font:13.5px {_S8_FUENTE};max-width:700px;margin-top:10px">'
        f'Los tres guardan la misma frase y ninguno sobra: el conjunto sabe '
        f'<b>cuáles</b> palabras hay pero no cuántas veces; el diccionario sabe '
        f'<b>cuántas veces</b> pero ya no sabe en qué orden venían. Un modelo de '
        f'texto trabaja con el del medio y el de abajo, y tira el orden: por eso '
        f'se llama <b>bolsa</b> de palabras.</p></div>')


# =============================================================================
# Portada
# =============================================================================
def portada():
    """Tarjeta de bienvenida: la primera salida que produce el propio kernel.

    Cada semana tiene la suya, con su titulo y sus datos. No esta en el motor
    comun a proposito: es lo unico que identifica de un vistazo en que
    cuadernillo esta el estudiante.

    OJO: los 25 puntos de aqui son la SEGUNDA copia del total. La primera la
    suma el constructor a partir de los ejercicios, y build.py falla si no
    cuadran (se desincronizaron en las semanas 03-06 y nadie lo vio, porque
    este texto viaja comprimido dentro de la celda del motor).
    """
    _s8_pintar(
        f'<div style="font-family:{_S8_FUENTE};background:linear-gradient(135deg,'
        f'#2e2377,{_S8_AZUL});color:#fff;border-radius:10px;padding:18px 22px;'
        'margin:6px 0 10px">'
        '<div style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;'
        # «Unidad 8» y no «Unidad 3», que es como la llama la planeacion: las
        # seis portadas anteriores numeran la unidad por la semana y la semana 3
        # ya ocupa ese numero con otro nombre. Ver el docstring del generador.
        'opacity:.82">Semana 8 · Unidad 8</div>'
        '<div style="font-size:26px;font-weight:700;margin:2px 0 6px">Funciones y colecciones</div>'
        '<div style="font-size:14.5px;line-height:1.5;opacity:.94">Parametros, retorno multiple, '
        'tuplas, diccionarios y conjuntos.<br>'
        '<span style="opacity:.8">25 puntos · 5 XP · insignia «Quien empaqueta»</span></div></div>')


# Alias: los cuadernillos 1 y 2 estrenaron dos nombres distintos para lo mismo
# --iniciar() y portada()-- y conviene que los dos funcionen en todas las
# semanas. Que un alumno escriba el de otro cuadernillo y le salte un NameError
# en la PRIMERA celda es la peor bienvenida posible, y ya paso una vez.
iniciar = portada
