"""Contenido propio de la SEMANA 9: «Archivos y arreglos».

Qué es esto
-----------
Lo de esta semana y nada más: el quiz del calentamiento y tres dibujos.

- `quiz_columna()`      el calentamiento. Pregunta por el recorrido de una
                        COLUMNA a mano, que es lo que la semana 7 le costó dos
                        índices y lo que NumPy va a resolver hoy en `a[:, 0]`.
                        Está elegido para que el alumno tenga el recuerdo
                        fresco cuando aparezca el atajo: si no se acuerda de lo
                        que costaba, el atajo no le parece nada.
- `ver_archivo_sucio()` el gancho: el contenido de un archivo de medidas, con
                        las líneas que NO se pueden convertir marcadas en rojo.
                        Va antes de cualquier sintaxis, porque el problema de
                        la semana es ese y no `try`.
- `ver_flujo_try()`     la tabla de `try` / `except` / `else` / `finally`: qué
                        bloque corre cuando la conversión funciona y qué bloque
                        corre cuando falla, en dos columnas. Son cuatro
                        palabras nuevas y la duda real no es qué significan
                        sino CUÁNDO corre cada una; una tabla de dos columnas
                        lo contesta de un golpe y un párrafo no.
- `ver_antes_despues()` el pago de la semana: el código de la semana 7 —dos
                        ciclos anidados, escritos por el alumno— al lado de la
                        línea de NumPy que hace lo mismo. Lado a lado, con el
                        mismo resultado debajo de los dos.

Por qué NO hay matplotlib aquí
------------------------------
La imagen del alumno trae matplotlib y funciona (el backend del kernel ya es
`matplotlib_inline`, así que `plt.show()` dibuja). Pero la planeación de esta
semana no pide ninguna gráfica: pide archivos, excepciones y arreglos. Meter una
gráfica costaría minutos del presupuesto de ~30 y no mediría nada de lo de hoy.
Los dibujos de aquí son HTML, como en las semanas 7 y 8.

Por qué `ver_antes_despues()` NO ejecuta el código que muestra
--------------------------------------------------------------
Los dos resultados están escritos a mano en la constante. Podría calcularlos, y
sería más bonito; pero entonces esta función tendría dentro, en el espacio
global del cuadernillo, un máximo-por-columna con ciclos anidados y la línea de
NumPy que lo sustituye — es decir, media solución del tercer ejercicio a una
llamada de distancia. Mismo motivo por el que `bolsa_y_vocabulario` de la
semana 8 cuenta dentro de su propio cuerpo.

Prefijos `_s9_` en todo lo privado: los módulos de cada semana se cargan en el
MISMO espacio de nombres que el motor, así que un nombre repetido pisaría el de
otra semana sin avisar.

Dependencias: biblioteca estándar. Sin NumPy y sin matplotlib — este archivo se
ejecuta también al construir, fuera de la imagen, donde no hay ninguno de los
dos.
"""
from IPython.display import HTML as _HTML9, display as _display9

_S9_VIOLETA = "#4a3aa7"
_S9_AZUL = "#2a78d6"
_S9_VERDE = "#0ca30c"
_S9_ROJO = "#d03b3b"
_S9_GRIS = "#52514e"
_S9_GRIS_SUAVE = "#f4f5f7"
_S9_BORDE = "#dfe3e8"
_S9_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
_S9_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _s9_pintar(html):
    _display9(_HTML9(html))


def _s9_motor():
    return globals().get("ava")


def _s9_escapar(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _s9_titulo(texto):
    return (f'<div style="font:600 13.5px {_S9_FUENTE};color:{_S9_VIOLETA};'
            f'margin-bottom:5px">{texto}</div>')


def _s9_pie(texto):
    return (f'<div style="font:12.5px {_S9_FUENTE};color:{_S9_GRIS};'
            f'margin-top:6px;max-width:660px">{texto}</div>')


# =============================================================================
# Calentamiento
# =============================================================================
def quiz_columna():
    """Una de la semana 7, elegida porque es justo la que hoy se jubila.

    El alumno escribió con sus manos el recorrido de una columna hace dos
    semanas: el índice de la fila se mueve y el de la columna se queda quieto.
    Hoy eso se escribe `a[:, 2]`. Para que el atajo signifique algo tiene que
    acordarse primero de lo que cuesta sin él, y una pregunta sin nota es la
    forma más corta de obligarle a recordarlo.
    """
    ava = _s9_motor()
    if ava is None:
        return
    return ava.quiz(
        "s9_columna", 5,
        "Tienes una matriz `m` (lista de listas) y quieres recorrer la columna "
        "2 de arriba abajo, a mano, como en la semana 7. ¿Cuál escribes?",
        ["for f in range(len(m)):  ... m[f][2]",
         "for c in range(len(m[0])):  ... m[2][c]",
         "for valor in m[2]:  ...",
         "for f in range(len(m)):  ... m[2][f]"],
        0,
        "Una columna se lee de arriba abajo: lo que se mueve es la FILA y el "
        "índice de la columna se queda quieto, `m[f][2]`. Las otras tres "
        "recorren la fila 2, que es otra cosa. Acuérdate de lo que cuesta "
        "escribir esto: dentro de un rato lo vas a ver en cuatro caracteres.",
    )


# =============================================================================
# El gancho: un archivo con filas que no sirven
# =============================================================================
# Por qué el gancho es un archivo sucio y no la palabra `try`:
#
# La excepción, presentada sola, es una ceremonia de sintaxis que se olvida
# («rodea esto con try»). Presentada sobre un archivo real es lo único que hay:
# cualquiera que haya cargado un conjunto de datos de verdad sabe que la fila
# 1.483 trae una coma decimal, un hueco o la palabra «NA», y que el programa se
# detiene ahí. Primero el problema, después la herramienta.
#
# Las cuatro líneas malas son las cuatro que aparecen de verdad y cada una por
# un motivo distinto: la coma decimal (que en Colombia es LA normal), el texto
# en una columna numérica, el hueco del dato que nadie midió y la línea vacía
# del final del archivo. Las mismas cuatro reaparecen en el laboratorio y en el
# ejercicio, con otros números.
_S9_ARCHIVO = [
    ("21.4", True),
    ("19.8", True),
    ("3,5", False),
    ("22.1", True),
    ("NA", False),
    ("", False),
    ("20.6", True),
]
_S9_MOTIVOS = {
    "3,5": "coma decimal: `float` solo entiende el punto",
    "NA": "el que midió escribió «no disponible» con letras",
    "": "una línea vacía, de las que sobran al final de todo archivo",
}


def ver_archivo_sucio():
    """Pinta el contenido del archivo de medidas, marcando lo que no convierte."""
    filas = []
    for i, (texto, sirve) in enumerate(_S9_ARCHIVO, start=1):
        if sirve:
            fondo, color, nota = "#ffffff", "#0b0b0b", ""
        else:
            fondo, color = "#fdeeee", _S9_ROJO
            nota = _S9_MOTIVOS.get(texto, "")
        visible = _s9_escapar(texto) if texto else "&nbsp;"
        filas.append(
            f'<tr>'
            f'<td style="padding:4px 10px;text-align:right;font:12px {_S9_MONO};'
            f'color:{_S9_GRIS};background:{_S9_GRIS_SUAVE};'
            f'border:1px solid {_S9_BORDE}">{i}</td>'
            f'<td style="padding:4px 14px;font:14px {_S9_MONO};background:{fondo};'
            f'color:{color};border:1px solid {_S9_BORDE};min-width:90px">'
            f'{visible}</td>'
            f'<td style="padding:4px 12px;font:12.5px {_S9_FUENTE};'
            f'color:{_S9_ROJO};border:none">{nota}</td></tr>')
    buenas = sum(1 for _, sirve in _S9_ARCHIVO if sirve)
    _s9_pintar(
        '<div style="margin:10px 0">'
        + _s9_titulo("medidas.txt — siete líneas que alguien midió y guardó")
        + '<table style="border-collapse:collapse">' + "".join(filas) + '</table>'
        + _s9_pie(
            f"Un número por línea, y <b>{buenas} de {len(_S9_ARCHIVO)}</b> se "
            f"pueden convertir. Las otras tres no son un archivo roto: son un "
            f"archivo <b>normal</b>. Ningún conjunto de datos del mundo real "
            f"llega limpio, y lo primero que hace cualquiera antes de entrenar "
            f"algo es cargarlo y descubrir esto.")
        + "</div>")


# =============================================================================
# try / except / else / finally: cuándo corre cada bloque
# =============================================================================
# Son cuatro palabras y la duda real no es qué significan: es cuál corre y
# cuándo. Dos columnas —«funcionó» y «falló»— lo contestan de un golpe. La
# alternativa era un párrafo de cuatro frases, y un párrafo de cuatro frases
# sobre flujo de control no se recuerda.
_S9_BLOQUES = [
    ("try:", _S9_VIOLETA, "lo que puede fallar",
     ("corre", "corre, y se corta justo en la línea que falla")),
    ("except ValueError:", _S9_ROJO, "el plan B si falla ESE error",
     ("no corre", "corre")),
    ("else:", _S9_VERDE, "lo que solo tiene sentido si NO falló",
     ("corre", "no corre")),
    ("finally:", _S9_AZUL, "la limpieza, pase lo que pase",
     ("corre", "corre")),
]


def ver_flujo_try():
    """La tabla de los cuatro bloques contra los dos casos posibles."""
    filas = []
    for palabra, color, para_que, (si_ok, si_mal) in _S9_BLOQUES:
        filas.append(
            f'<tr>'
            f'<td style="padding:7px 14px;font:700 13px {_S9_MONO};color:{color};'
            f'white-space:nowrap;border-bottom:1px solid {_S9_BORDE}">'
            f'{_s9_escapar(palabra)}</td>'
            f'<td style="padding:7px 14px;font:13px {_S9_FUENTE};'
            f'border-bottom:1px solid {_S9_BORDE}">{para_que}</td>'
            f'<td style="padding:7px 14px;font:600 13px {_S9_FUENTE};'
            f'color:{_S9_VERDE if si_ok.startswith("corre") else _S9_GRIS};'
            f'border-bottom:1px solid {_S9_BORDE}">{si_ok}</td>'
            f'<td style="padding:7px 14px;font:600 13px {_S9_FUENTE};'
            f'color:{_S9_VERDE if si_mal.startswith("corre") else _S9_GRIS};'
            f'border-bottom:1px solid {_S9_BORDE}">{si_mal}</td></tr>')
    cabecera = "".join(
        f'<th style="padding:7px 14px;text-align:left;font:600 11.5px '
        f'{_S9_FUENTE};color:{_S9_GRIS};text-transform:uppercase;'
        f'letter-spacing:.05em;border-bottom:2px solid {_S9_BORDE}">{t}</th>'
        for t in ("Bloque", "Para qué está",
                  'float("21.4") funciona', 'float("3,5") falla'))
    _s9_pintar(
        '<div style="margin:10px 0">'
        + _s9_titulo("Los cuatro bloques, y cuál corre en cada caso")
        + f'<table style="border-collapse:collapse;border:1px solid {_S9_BORDE}">'
        + f'<tr>{cabecera}</tr>' + "".join(filas) + '</table>'
        + _s9_pie(
            "Solo <code>try</code> y <code>except</code> son obligatorios; "
            "<code>else</code> y <code>finally</code> se ponen si hacen falta. "
            "Fíjate en la fila de <code>finally</code>: corre en las dos "
            "columnas, y por eso es donde se cierra lo que haya quedado "
            "abierto.")
        + "</div>")


# =============================================================================
# El pago: la semana 7, en una línea
# =============================================================================
# Esto es la semana entera en un dibujo. El alumno escribió el código de la
# izquierda con sus manos hace dos semanas —el máximo por columna y la
# transposición fueron sus ejercicios de 2★ y 3★—, así que no se le está
# vendiendo una librería nueva: se le está devolviendo su propio trabajo en una
# línea. Ese es el único argumento que convence de aprender una herramienta.
#
# Los resultados van escritos a mano, no calculados: calcularlos obligaría a
# dejar en el espacio global del cuadernillo un máximo-por-columna con ciclos y
# su equivalente vectorizado, que es media solución del tercer ejercicio.
_S9_COMPARACION = [
    ("El máximo de cada columna",
     "mayores = []\n"
     "for c in range(len(m[0])):\n"
     "    mayor = m[0][c]\n"
     "    for f in range(len(m)):\n"
     "        if m[f][c] > mayor:\n"
     "            mayor = m[f][c]\n"
     "    mayores.append(mayor)",
     "a.max(axis=0)",
     "[15  7  1]"),
    ("Transponer",
     "nueva = []\n"
     "for c in range(len(m[0])):\n"
     "    fila = []\n"
     "    for f in range(len(m)):\n"
     "        fila.append(m[f][c])\n"
     "    nueva.append(fila)",
     "a.T",
     "[[12  9 15  8]\n [ 5  7  3  6]\n [ 1  0  1  0]]"),
]


def _s9_panel(etiqueta, codigo, color, fondo):
    return (
        f'<div style="display:inline-block;vertical-align:top;margin:0 10px 0 0">'
        f'<div style="font:600 11.5px {_S9_FUENTE};color:{color};'
        f'text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px">'
        f'{etiqueta}</div>'
        f'<pre style="margin:0;font-family:{_S9_MONO};font-size:12.5px;'
        f'line-height:1.45;background:{fondo};border:1px solid {_S9_BORDE};'
        f'border-radius:7px;padding:10px 14px">{_s9_escapar(codigo)}</pre></div>')


def ver_antes_despues():
    """Lo que el alumno escribió en la semana 7, al lado de su línea de NumPy."""
    bloques = []
    for que, a_mano, con_numpy, resultado in _S9_COMPARACION:
        bloques.append(
            f'<div style="margin:14px 0 0">'
            + _s9_titulo(_s9_escapar(que))
            + _s9_panel("Tu semana 7 · a mano", a_mano, _S9_GRIS, "#f7f8fa")
            + _s9_panel("Hoy · NumPy", con_numpy, _S9_AZUL, "#eef5fd")
            + f'<div style="font:12.5px {_S9_FUENTE};color:{_S9_GRIS};'
              f'margin-top:4px">Las dos dan '
              f'<code style="font-size:12px">{_s9_escapar(resultado)}</code>'
              f'</div></div>')
    _s9_pintar(
        '<div style="margin:10px 0">'
        + _s9_titulo("La misma matriz de la semana 7: "
                     "m = [[12, 5, 1], [9, 7, 0], [15, 3, 1], [8, 6, 0]]")
        + "".join(bloques)
        + _s9_pie(
            "No es que NumPy sea más corto: es que el de la izquierda lo "
            "escribiste tú y te costó una tarde, y en el de la derecha no "
            "caben los errores que cometiste —el índice cambiado, el ciclo que "
            "se para una fila antes, el candidato que arranca en cero—. "
            "<b>Las líneas que no escribes no se pueden equivocar.</b>")
        + "</div>")


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
    _s9_pintar(
        f'<div style="font-family:{_S9_FUENTE};background:linear-gradient(135deg,'
        f'#2e2377,{_S9_AZUL});color:#fff;border-radius:10px;padding:18px 22px;'
        'margin:6px 0 10px">'
        '<div style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;'
        # «Unidad 9» y no «Unidad 3», que es como la llama la planeacion: los
        # cuadernillos publicados numeran la unidad por la semana desde la 4
        # («Unidad 7», «Unidad 8»). Ver el docstring del generador.
        'opacity:.82">Semana 9 · Unidad 9</div>'
        '<div style="font-size:26px;font-weight:700;margin:2px 0 6px">Archivos y arreglos</div>'
        '<div style="font-size:14.5px;line-height:1.5;opacity:.94">Datos que sobreviven al kernel, '
        'errores que no detienen el programa y cuentas sin ciclos.<br>'
        '<span style="opacity:.8">25 puntos · 5 XP · insignia «Quien persiste»</span></div></div>')


# Alias: los cuadernillos 1 y 2 estrenaron dos nombres distintos para lo mismo
# --iniciar() y portada()-- y conviene que los dos funcionen en todas las
# semanas. Que un alumno escriba el de otro cuadernillo y le salte un NameError
# en la PRIMERA celda es la peor bienvenida posible, y ya paso una vez.
iniciar = portada
