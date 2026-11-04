"""Contenido propio de la SEMANA 10: «Análisis y comunicación de datos».

Qué es esto
-----------
Lo de esta semana y nada más: el quiz del calentamiento, dos figuras y la
portada.

- `quiz_columna()`          el calentamiento. Repasa lo de la semana 7 que hace
                            falta HOY: una característica vive en una columna.
- `ver_tabla_con_nombres()` el puente: la misma tabla dos veces, a la izquierda
                            como lista de listas con índices y a la derecha con
                            nombres de columna. Es el gancho conceptual de la
                            semana —«un DataFrame es la matriz de la semana 7,
                            pero las columnas tienen nombre»— y se ve en dos
                            segundos, que es menos de lo que cuesta leerlo.
- `ver_rotulos()`           la figura que sostiene el cuadernillo: un diagrama
                            de barras con sus cuatro rótulos numerados y, al
                            lado, la tabla que dice con qué se vuelve a leer
                            cada uno (`ax.get_title()`, `ax.get_xlabel()`…).

Por qué `ver_rotulos()` es la pieza clave, y no un adorno
---------------------------------------------------------
Una gráfica no se puede autocalificar por si es bonita. Lo que SÍ se puede, y
es justo lo que pide la clase 1 de la planeación («títulos, ejes, leyendas y
comunicación de resultados»), es su **estructura**: que tenga título, que los
dos ejes estén etiquetados, que las barras dibujen los números correctos. Y eso
se comprueba volviendo a preguntárselo a los ejes.

Al alumno hay que decírselo con todas las letras —la celda de prueba lee
`ax.get_title()`— porque si no, «etiqueta la gráfica» suena a consejo de buenos
modales y se salta. Esta figura es donde se le dice. Los cuatro `get_*` que
aparecen aquí están comprobados en la imagen del AVA (Python 3.11.18,
matplotlib 3.9.2): devuelven lo que se les puso, y lo siguen devolviendo
**después** de que el backend inline cierre la figura, que es lo que pasa en
cuanto el alumno llama a `plt.show()` dentro de su función.

Lo que esta figura NO hace: dibujar con matplotlib. Es SVG escrito a mano. El
motivo es que las figuras de contenido.py se incrustan en el notebook y se
ejecutan antes de que el alumno haya importado nada; además, una figura de
matplotlib que explica cómo se rotula una figura de matplotlib se mezcla con
las de verdad del laboratorio y deja de leerse como lo que es, un esquema.

Prefijos `_s10_` en todo lo privado: los módulos de cada semana se cargan en el
MISMO espacio de nombres que el motor, así que un nombre repetido pisaría el de
otra semana sin avisar.

Dependencias: biblioteca estándar. **Sin pandas y sin matplotlib**, aunque sean
el tema de la semana. Si este módulo hiciera `import pandas as pd`, el nombre
`pd` quedaría en el espacio global desde la primera celda y el alumno podría
usar pandas sin haber escrito un import en su vida — y, peor, los imports del
laboratorio dejarían de hacer falta sin que nada lo dijera. Aquí los imports se
escriben donde se usan, que es como se escribe un análisis de verdad.
"""
import sys as _sys10

from IPython.display import HTML as _HTML10, display as _display10

# -----------------------------------------------------------------------------
# Parche de compatibilidad con verificar.py. CUATRO líneas, y conviene saber por
# qué están.
#
# `verificar.py` no tiene IPython cuando corre fuera de un kernel, así que
# instala un sustituto (`_stub_ipython`) con lo justo para que el motor pinte
# HTML: `display`, `HTML`, `get_ipython`… pero **sin `version_info`**. Y
# matplotlib pide ese atributo al crear su PRIMERA figura, en
# `backend_bases.FigureCanvasBase._fix_ipython_backend2gui`:
#
#     mod_ipython = sys.modules.get("IPython")
#     if mod_ipython is None or mod_ipython.version_info[:2] >= (8, 24):
#         return
#
# Con el sustituto puesto, eso es `AttributeError: module 'IPython' has no
# attribute 'version_info'` y revienta cualquier `plt.subplots()`. Esta es la
# primera semana que dibuja, así que es la primera que se lo encuentra: sin el
# parche, el ejercicio de la gráfica —el de 3★, 10 de los 25 puntos— no se puede
# verificar en local, y un ejercicio que no se verifica se publica a ciegas.
#
# No se toca verificar.py porque el sustituto es correcto para lo que hace (el
# motor) y ampliarlo es decisión de quien lo mantiene. Y esto NO cambia nada en
# el AVA: allí IPython es el de verdad (9.17.1, comprobado en la imagen) y ya
# trae `version_info`, así que el `hasattr` es falso y no se ejecuta ni una
# línea. El valor que se pone es el que hace que matplotlib tome la rama
# «IPython moderno, no hace falta parchear nada» y se vaya sin mirar más.
_IP10 = _sys10.modules.get("IPython")
if _IP10 is not None and not hasattr(_IP10, "version_info"):
    _IP10.version_info = (8, 24, 0, "")

_S10_VIOLETA = "#4a3aa7"
_S10_AZUL = "#2a78d6"
_S10_AMBAR = "#eda100"
_S10_VERDE = "#0ca30c"
_S10_GRIS = "#52514e"
_S10_GRIS_SUAVE = "#f4f5f7"
_S10_BORDE = "#dfe3e8"
_S10_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
_S10_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _s10_pintar(html):
    _display10(_HTML10(html))


def _s10_motor():
    return globals().get("ava")


def _s10_escapar(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _s10_titulo(texto):
    return (f'<div style="font:600 13.5px {_S10_FUENTE};color:{_S10_VIOLETA};'
            f'margin-bottom:4px">{texto}</div>')


def _s10_pie(texto):
    return (f'<div style="font:12.5px {_S10_FUENTE};color:{_S10_GRIS};'
            f'margin-top:6px;max-width:660px">{texto}</div>')


# =============================================================================
# Calentamiento
# =============================================================================
def quiz_columna():
    """Una de la semana 7, elegida porque es la que hace falta hoy.

    No es un repaso de relleno: todo el cuadernillo descansa en que una
    CARACTERÍSTICA vive en una columna. Quien crea que vive en una fila va a
    pedirle el promedio a la fila equivocada en los tres ejercicios, y es mejor
    que lo descubra aquí, sin nota, que al final.
    """
    ava = _s10_motor()
    if ava is None:
        return
    return ava.quiz(
        "s10_columna", 5,
        "En una tabla de datos, cada fila es un ejemplo y cada columna una "
        "característica. Para sacar el promedio de UNA característica, ¿qué "
        "tienes que recorrer?",
        ["una fila", "una columna", "la diagonal", "la tabla entera"],
        1,
        "El promedio de una característica es el promedio de su columna: se lee "
        "de arriba abajo, moviendo la fila y dejando la columna quieta. En la "
        "semana 7 eso era un ciclo escrito a mano; esta semana la columna tiene "
        "nombre y sabe calcular su promedio ella sola.",
    )


# =============================================================================
# El puente: la matriz de la semana 7, ahora con nombres
# =============================================================================
# OJO: estas cuatro filas son las cuatro PRIMERAS del archivo que escribe el
# laboratorio. Están repetidas aquí porque esta figura se dibuja antes de que
# exista el archivo, y porque el alumno tiene que reconocer los mismos números a
# los dos lados del puente. Si cambias el CSV del generador, cambia esto.
_S10_MUESTRA = [
    ["gato", 0.91, 320],
    ["gato", 0.42, 256],
    ["gato", 0.88, 320],
    ["gato", 0.73, 512],
]
_S10_COLUMNAS = ["etiqueta", "nitidez", "ancho"]


def _s10_celda(texto, mono=True, fondo="#ffffff", color="#0b0b0b", grueso=False):
    fuente = _S10_MONO if mono else _S10_FUENTE
    peso = "600" if grueso else "400"
    return (f'<td style="border:1px solid {_S10_BORDE};padding:6px 12px;'
            f'text-align:center;font-family:{fuente};font-size:13px;'
            f'font-weight:{peso};background:{fondo};color:{color}">'
            f'{_s10_escapar(texto)}</td>')


def _s10_rotulo(texto):
    return (f'<td style="padding:5px 12px;text-align:center;'
            f'font:600 12px {_S10_MONO};color:{_S10_GRIS};'
            f'background:{_S10_GRIS_SUAVE};border:1px solid {_S10_BORDE}">'
            f'{_s10_escapar(texto)}</td>')


def _s10_tabla_html(filas, encabezados, rotulos_fila):
    cabecera = "<td></td>" + "".join(_s10_rotulo(h) for h in encabezados)
    cuerpo = []
    for i, fila in enumerate(filas):
        celdas = [_s10_rotulo(rotulos_fila[i])]
        celdas += [_s10_celda(v) for v in fila]
        cuerpo.append("<tr>" + "".join(celdas) + "</tr>")
    return ('<table style="border-collapse:collapse">'
            f'<tr>{cabecera}</tr>{"".join(cuerpo)}</table>')


def ver_tabla_con_nombres():
    """La misma tabla a los dos lados del puente: con índices y con nombres.

    Es el gancho conceptual entero: lo nuevo de pandas no es la tabla —esa ya la
    tiene desde la semana 7— sino que las columnas se piden por su NOMBRE y
    cada una sabe de qué tipo es. Verlo al lado cuesta dos segundos; explicarlo
    con palabras, un párrafo que nadie lee.
    """
    columna = ('<div style="display:inline-block;vertical-align:top;'
               'margin:0 10px 0 0">')
    etiqueta = (f'<div style="font:600 12px {_S10_MONO};color:{_S10_GRIS};'
                f'margin-bottom:4px">')
    flecha = (f'<div style="display:inline-block;vertical-align:middle;'
              f'margin:0 10px;font:700 22px {_S10_FUENTE};color:{_S10_AZUL}">'
              f'&rarr;</div>')
    izquierda = _s10_tabla_html(
        _S10_MUESTRA,
        [f"c={i}" for i in range(len(_S10_COLUMNAS))],
        [f"f={i}" for i in range(len(_S10_MUESTRA))])
    derecha = _s10_tabla_html(
        _S10_MUESTRA, _S10_COLUMNAS,
        [str(i) for i in range(len(_S10_MUESTRA))])
    _s10_pintar(
        '<div style="margin:10px 0">'
        + _s10_titulo("La misma tabla, dos veces")
        + columna + etiqueta + "lista de listas (semana 7)</div>"
        + izquierda + "</div>"
        + flecha
        + columna + etiqueta + "DataFrame (esta semana)</div>"
        + derecha + "</div>"
        + _s10_pie(
            "A la izquierda, para llegar a la nitidez de la cuarta foto hay que "
            "acordarse de que la nitidez es la columna <code>1</code>: "
            "<code>m[3][1]</code>. A la derecha se pide por su nombre: "
            "<code>tabla[\"nitidez\"][3]</code>. Los números son los mismos; lo "
            "que cambia es que la tabla ya sabe cómo se llama cada columna — y "
            "de qué tipo es, que es por lo que puede calcular un promedio ella "
            "sola. Una diferencia que importa luego: a la izquierda el "
            "<code>3</code> es la <b>posición</b> de la fila; a la derecha es la "
            "<b>etiqueta</b> que esa fila lleva puesta, y una tabla filtrada se "
            "queda con las etiquetas que traía.")
        + "</div>")


# =============================================================================
# La figura clave: los cuatro rótulos de una gráfica, y cómo se vuelven a leer
# =============================================================================
# Por qué está dibujada a mano en SVG y no con matplotlib: ver el docstring del
# módulo. En corto: se dibuja antes de que el alumno importe nada, y un esquema
# tiene que distinguirse de las gráficas de verdad del laboratorio.
_S10_NUMEROS = [
    ("1", "Título", "ax.set_title(...)", "ax.get_title()",
     "que no esté vacío"),
    ("2", "Eje X", "ax.set_xlabel(...)", "ax.get_xlabel()",
     "que no esté vacío"),
    ("3", "Eje Y", "ax.set_ylabel(...)", "ax.get_ylabel()",
     "que no esté vacío"),
    ("4", "Leyenda", "ax.legend()", "ax.get_legend()",
     "que exista, si hay dos series"),
]


def _s10_marca(x, y, n):
    """Un círculo numerado sobre el esquema."""
    return (f'<circle cx="{x}" cy="{y}" r="10" fill="{_S10_AMBAR}"/>'
            f'<text x="{x}" y="{y + 4}" text-anchor="middle" '
            f'font-family="{_S10_MONO}" font-size="12" font-weight="700" '
            f'fill="#ffffff">{n}</text>')


def _s10_svg_rotulos():
    barras = ""
    for i, (x, alto) in enumerate(((120, 96), (176, 56), (232, 128))):
        y = 230 - alto
        barras += (f'<rect x="{x}" y="{y}" width="38" height="{alto}" '
                   f'rx="2" fill="{_S10_AZUL}" opacity="0.85"/>')
    etiquetas_x = ""
    for x, texto in ((139, "gato"), (195, "perro"), (251, "ave")):
        etiquetas_x += (f'<text x="{x}" y="248" text-anchor="middle" '
                        f'font-family="{_S10_MONO}" font-size="11" '
                        f'fill="{_S10_GRIS}">{texto}</text>')
    return (
        '<svg viewBox="0 0 420 300" width="420" height="300" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="Esquema de un diagrama de barras con sus cuatro rotulos '
        'numerados: titulo, eje X, eje Y y leyenda.">'
        # marco del area de dibujo
        f'<line x1="100" y1="60" x2="100" y2="230" stroke="{_S10_GRIS}" '
        'stroke-width="1.5"/>'
        f'<line x1="100" y1="230" x2="300" y2="230" stroke="{_S10_GRIS}" '
        'stroke-width="1.5"/>'
        + barras + etiquetas_x +
        # 1. titulo
        f'<text x="200" y="40" text-anchor="middle" font-family="{_S10_FUENTE}" '
        f'font-size="14" font-weight="700" fill="#0b0b0b">Fotos por clase</text>'
        + _s10_marca(330, 36, "1") +
        # 2. eje X
        f'<text x="200" y="272" text-anchor="middle" font-family="{_S10_FUENTE}" '
        f'font-size="12.5" fill="{_S10_GRIS}">clase</text>'
        + _s10_marca(258, 268, "2") +
        # 3. eje Y
        f'<text x="52" y="145" text-anchor="middle" font-family="{_S10_FUENTE}" '
        f'font-size="12.5" fill="{_S10_GRIS}" '
        'transform="rotate(-90 52 145)">cuántas fotos</text>'
        + _s10_marca(52, 95, "3") +
        # 4. leyenda
        f'<rect x="300" y="70" width="104" height="30" rx="4" fill="#ffffff" '
        f'stroke="{_S10_BORDE}"/>'
        f'<rect x="309" y="81" width="14" height="9" fill="{_S10_AZUL}" '
        'opacity="0.85"/>'
        f'<text x="330" y="90" font-family="{_S10_MONO}" font-size="11" '
        f'fill="{_S10_GRIS}">conteo</text>'
        + _s10_marca(330, 118, "4") +
        '</svg>')


def ver_rotulos():
    """El esquema de los cuatro rótulos, y con qué se vuelve a leer cada uno.

    La tabla de la derecha es la que convierte «etiqueta tu gráfica» en algo
    comprobable. Dice, sin rodeos, qué mira la celda de prueba.
    """
    filas = "".join(
        f'<tr>'
        f'<td style="padding:5px 10px 5px 0;text-align:center">'
        f'<span style="display:inline-block;width:19px;height:19px;'
        f'line-height:19px;border-radius:50%;background:{_S10_AMBAR};'
        f'color:#fff;font:700 11.5px {_S10_MONO}">{n}</span></td>'
        f'<td style="padding:5px 12px 5px 0;font:600 13px {_S10_FUENTE}">'
        f'{nombre}</td>'
        f'<td style="padding:5px 12px 5px 0;font:12.5px {_S10_MONO};'
        f'color:{_S10_VIOLETA}">{_s10_escapar(pone)}</td>'
        f'<td style="padding:5px 12px 5px 0;font:12.5px {_S10_MONO};'
        f'color:{_S10_VERDE}">{_s10_escapar(lee)}</td>'
        f'<td style="padding:5px 0;font:12.5px {_S10_FUENTE};'
        f'color:{_S10_GRIS}">{comprueba}</td></tr>'
        for n, nombre, pone, lee, comprueba in _S10_NUMEROS)
    _s10_pintar(
        '<div style="margin:10px 0">'
        + _s10_titulo("Los cuatro rótulos, y cómo se vuelven a leer")
        + '<div style="display:inline-block;vertical-align:middle">'
        + _s10_svg_rotulos() + '</div>'
        + '<div style="display:inline-block;vertical-align:middle;'
          'margin-left:14px">'
        + '<table style="border-collapse:collapse">'
        + f'<tr><td></td><td style="padding:0 12px 6px 0;font:600 11px '
          f'{_S10_FUENTE};color:{_S10_GRIS};text-transform:uppercase;'
          f'letter-spacing:.05em">qué es</td>'
          f'<td style="padding:0 12px 6px 0;font:600 11px {_S10_FUENTE};'
          f'color:{_S10_VIOLETA};text-transform:uppercase;'
          f'letter-spacing:.05em">se pone con</td>'
          f'<td style="padding:0 12px 6px 0;font:600 11px {_S10_FUENTE};'
          f'color:{_S10_VERDE};text-transform:uppercase;'
          f'letter-spacing:.05em">se lee con</td>'
          f'<td style="padding:0 0 6px 0;font:600 11px {_S10_FUENTE};'
          f'color:{_S10_GRIS};text-transform:uppercase;'
          f'letter-spacing:.05em">se exige</td></tr>'
        + filas + '</table></div>'
        + _s10_pie(
            "La columna verde es la importante: un rótulo no se queda solo en "
            "la imagen, se le puede volver a preguntar a los ejes. Por eso una "
            "gráfica sí se puede calificar — no por si es bonita, que eso no lo "
            "sabe medir nadie, sino por si está <b>rotulada</b> y por si las "
            "barras dibujan los números correctos (<code>ax.patches</code>, uno "
            "por barra, con su <code>get_height()</code>).")
        + "</div>")


# =============================================================================
# Portada
# =============================================================================
def portada():
    """Tarjeta de bienvenida: la primera salida que produce el propio kernel.

    Cada semana tiene la suya, con su titulo y sus datos. No esta en el motor
    comun adrede: es lo unico que identifica de un vistazo en que cuadernillo
    esta el estudiante.

    OJO: los «25 puntos» de aqui son la SEGUNDA copia del total. La primera la
    suma el constructor a partir de los ejercicios, y build.py falla si no
    cuadran (se desincronizaron en las semanas 03-06 y nadie lo vio, porque
    este texto viaja comprimido dentro de la celda del motor).
    """
    _s10_pintar(
        f'<div style="font-family:{_S10_FUENTE};background:linear-gradient(135deg,'
        f'#2e2377,{_S10_AZUL});color:#fff;border-radius:10px;padding:18px 22px;'
        'margin:6px 0 10px">'
        '<div style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;'
        # «Unidad 10» y no «Unidad 3», que es como la llama la planeacion: las
        # portadas publicadas numeran la unidad por la semana desde la 4, y un
        # salto de «Unidad 9» a «Unidad 3» lo reportaria el alumno como error.
        # El NOMBRE del tema si es el de la planeacion, literal. Ver el
        # docstring del generador.
        'opacity:.82">Semana 10 · Unidad 10</div>'
        '<div style="font-size:26px;font-weight:700;margin:2px 0 6px">'
        'Analisis y comunicacion de datos</div>'
        '<div style="font-size:14.5px;line-height:1.5;opacity:.94">DataFrame, '
        'filtros, estadisticas descriptivas y graficas rotuladas.<br>'
        '<span style="opacity:.8">25 puntos · 5 XP · insignia «Quien comunica»'
        '</span></div></div>')


# Alias: los cuadernillos 1 y 2 estrenaron dos nombres distintos para lo mismo
# --iniciar() y portada()-- y conviene que los dos funcionen en todas las
# semanas. Que un alumno escriba el de otro cuadernillo y le salte un NameError
# en la PRIMERA celda es la peor bienvenida posible, y ya paso una vez.
iniciar = portada
