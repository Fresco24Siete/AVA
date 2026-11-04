"""Contenido propio de la SEMANA 7: «Matrices».

Qué es esto
-----------
Aquí vive solo lo de esta semana: el quiz del calentamiento y cuatro dibujos.
Los cuatro salen de la MISMA función (`_s7_html_matriz`), porque los cuatro son
la misma cosa —una tabla de celdas— vista con distinta ropa:

- `ver_tabla_datos()`  el gancho: la tabla con nombres de columna, para que se
                       vea que una matriz es un conjunto de datos y no un
                       ejercicio de sintaxis.
- `ver_matriz()`       el dibujo que sostiene el cuadernillo: la matriz con el
                       índice de columna arriba y el de fila a la izquierda, y
                       una celda resaltada. El error de la semana es confundir
                       el orden de los dos índices, y verlo dibujado lo cura
                       más rápido que leerlo tres veces (es la misma apuesta
                       que `ver_lista` en la semana 06, y funcionó).
- `ver_confusion()`    la matriz cuadrada de aciertos con la diagonal marcada.
                       Es el gancho de carrera: esa tabla se llama matriz de
                       confusión y vuelve en la semana 15.
- `ver_transpuesta()`  el ANTES y el DESPUÉS de transponer, lado a lado. A
                       propósito **no** se muestra el código que transpone:
                       eso es el Ejercicio 3. Aquí se da la especificación, que
                       es lo que el alumno necesita para poder escribirlo.

Dos límites que condicionan el diseño y que el cuadernillo dice en voz alta:

- **El intérprete de pseudocódigo del curso no conoce arreglos.** `Dimension
  m[3,3]` contesta «no conozco el símbolo '['» (comprobado). Así que esta
  semana no hay pseudocódigo ejecutable: todo lo calificable es Python. Mismo
  criterio que la semana 06 con las listas.
- **El taller de roles y la bitácora no se pueden autocalificar.** Están
  nombrados en el cierre como lo que son —lo que se lleva a la clase
  presencial— y no se finge medirlos.

Prefijos `_s7_` en todo lo privado: los módulos de cada semana se cargan en el
MISMO espacio de nombres que el motor, así que un nombre repetido pisaría el de
otra semana sin avisar.

Dependencias: biblioteca estándar. Sin matplotlib.
"""
from IPython.display import HTML as _HTML7, display as _display7

_S7_VIOLETA = "#4a3aa7"
_S7_AZUL = "#2a78d6"
_S7_AMBAR = "#eda100"
_S7_GRIS = "#52514e"
_S7_GRIS_SUAVE = "#f4f5f7"
_S7_BORDE = "#dfe3e8"
_S7_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
_S7_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _s7_pintar(html):
    _display7(_HTML7(html))


def _s7_motor():
    return globals().get("ava")


def _s7_escapar(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# =============================================================================
# Calentamiento
# =============================================================================
def quiz_recorrido():
    """Una de la semana pasada, elegida porque es la que hace falta hoy.

    No es un repaso cualquiera: esta semana el alumno necesita DOS índices a la
    vez, y el `for valor in datos` que le basta para recorrer una lista no le
    da ninguno. Mejor descubrirlo aquí, sin nota, que en el Ejercicio 2.
    """
    ava = _s7_motor()
    if ava is None:
        return
    return ava.quiz(
        "s7_recorrido", 5,
        "Para recorrer una lista y poder usar la POSICIÓN de cada elemento, "
        "¿cuál de estas escribes?",
        ["for valor in datos:", "for i in range(len(datos)):",
         "while datos:", "for i in datos[0]:"],
        1,
        "`for valor in datos` te da los valores, pero no las posiciones. Con "
        "`range(len(datos))` tienes el índice en la mano, y esta semana vas a "
        "necesitar dos a la vez: uno para la fila y otro para la columna.",
    )


# =============================================================================
# El dibujo de la matriz, que es lo único que hay que entender esta semana
# =============================================================================
def _s7_celda(texto, fondo, color, grueso=False):
    peso = "600" if grueso else "400"
    return (f'<td style="border:1px solid {_S7_BORDE};padding:8px 15px;'
            f'text-align:center;font-family:{_S7_MONO};font-size:14px;'
            f'font-weight:{peso};background:{fondo};color:{color}">'
            f'{_s7_escapar(texto)}</td>')


def _s7_rotulo(texto, ancho_auto=True):
    """Celda de encabezado: un índice de fila o de columna, o un nombre."""
    relleno = "5px 12px" if ancho_auto else "5px 8px"
    return (f'<td style="padding:{relleno};text-align:center;'
            f'font:600 12px {_S7_MONO};color:{_S7_GRIS};'
            f'background:{_S7_GRIS_SUAVE};border:1px solid {_S7_BORDE}">'
            f'{_s7_escapar(texto)}</td>')


def _s7_html_matriz(m, resaltar=None, diagonal=False,
                    etiquetas_col=None, etiquetas_fila=None):
    """El HTML de una matriz dibujada como tabla, con sus rótulos.

    Una sola función para los cuatro dibujos del cuadernillo. `resaltar` es una
    pareja (fila, columna); `diagonal=True` marca en verde las celdas donde los
    dos índices coinciden; las etiquetas sustituyen los índices por nombres
    («horas», «ejemplo 0») cuando lo que se quiere mostrar es el SIGNIFICADO de
    la tabla y no su indexado.
    """
    n_col = max((len(f) for f in m), default=0)
    cols = etiquetas_col or [f"c={i}" for i in range(n_col)]
    filas_rot = etiquetas_fila or [f"f={i}" for i in range(len(m))]

    cabecera = "<td></td>" + "".join(_s7_rotulo(c) for c in cols)
    cuerpo = []
    for f, fila in enumerate(m):
        celdas = [_s7_rotulo(filas_rot[f])]
        for c, valor in enumerate(fila):
            marcada = resaltar is not None and tuple(resaltar) == (f, c)
            en_diagonal = diagonal and f == c
            if marcada:
                fondo, color = _S7_AMBAR, "#ffffff"
            elif en_diagonal:
                fondo, color = "#e3f6e3", "#0a6d0a"
            else:
                fondo, color = "#ffffff", "#0b0b0b"
            celdas.append(_s7_celda(valor, fondo, color,
                                    grueso=marcada or en_diagonal))
        cuerpo.append("<tr>" + "".join(celdas) + "</tr>")
    return ('<table style="border-collapse:collapse">'
            f'<tr>{cabecera}</tr>{"".join(cuerpo)}</table>')


def _s7_titulo(texto):
    return (f'<div style="font:600 13.5px {_S7_FUENTE};color:{_S7_VIOLETA};'
            f'margin-bottom:4px">{texto}</div>')


def _s7_pie(texto):
    return (f'<div style="font:12.5px {_S7_FUENTE};color:{_S7_GRIS};'
            f'margin-top:4px;max-width:620px">{texto}</div>')


def ver_matriz(m, resaltar=None, titulo=""):
    """La matriz con sus dos índices a la vista, y una celda marcada.

    Es la única función del cuadernillo que se le pide al alumno que toque por
    su cuenta («cambia el `resaltar` y mira dónde cae cada celda»), así que
    comprueba sus dos argumentos y contesta con palabras en vez de dejar que
    reviente por dentro. Los TRES errores que va a cometer:

    - pasarle una lista suelta en vez de una lista de listas, que es la
      confusión de la semana;
    - pedir una celda que no existe;
    - y pasarle **un solo número** en `resaltar`. Este último no es
      hipotético: la semana pasada `ver_lista(notas, resaltar=0)` llevaba un
      entero, porque en una lista una posición es un número, y el alumno
      acaba de entregar ese cuadernillo. Antes, `resaltar=2` reventaba con
      `TypeError: 'int' object is not iterable` justo en la sección que le
      pide que no gaste preguntas del tutor.
    """
    if not isinstance(m, list) or not m or not all(isinstance(f, list) for f in m):
        _s7_pintar(_s7_pie(
            "<b>Eso no es una matriz.</b> <code>ver_matriz</code> espera una "
            "lista de listas, una por fila: <code>[[1, 2], [3, 4]]</code>. Si le pasas "
            "una lista suelta, como <code>[1, 2, 3]</code>, no hay filas que "
            "dibujar."))
        return
    pareja = None
    if resaltar is not None:
        try:
            pareja = tuple(resaltar)
        except TypeError:          # un entero, que es el error de costumbre
            pareja = None
        if pareja is None or len(pareja) != 2 or not all(
                isinstance(i, int) for i in pareja):
            _s7_pintar(_s7_pie(
                "<b><code>resaltar</code> son DOS números</b>, la fila y la "
                "columna, y en ese orden: <code>resaltar=(1, 2)</code>. En una "
                "lista bastaba una posición; en una tabla hacen falta las dos "
                f"para señalar una celda. Tú pasaste <code>{_s7_escapar(resaltar)}"
                "</code>."))
            return
        f, c = pareja
        if not (0 <= f < len(m) and 0 <= c < len(m[f])):
            _s7_pintar(_s7_pie(
                f"<b>La celda [{f}][{c}] no existe en esta matriz</b>, que "
                f"tiene {len(m)} fila(s) y {len(m[0])} columna(s). Recuerda que "
                f"se cuenta desde cero: los índices de fila van de 0 a "
                f"{len(m) - 1}, y los de columna, de 0 a {len(m[0]) - 1}."))
            return
    pie = ("Arriba, el índice de <b>columna</b>; a la izquierda, el de "
           "<b>fila</b>. Siempre en ese orden: <code>m[fila][columna]</code>.")
    if pareja is not None:
        f, c = pareja
        pie += (f" La celda marcada es <code>m[{f}][{c}]</code>, "
                f"y vale <code>{_s7_escapar(m[f][c])}</code>.")
    _s7_pintar('<div style="margin:10px 0">'
               + (_s7_titulo(_s7_escapar(titulo)) if titulo else "")
               + _s7_html_matriz(m, resaltar=pareja) + _s7_pie(pie) + "</div>")


# =============================================================================
# El gancho: una matriz ES un conjunto de datos
# =============================================================================
# Cuatro estudiantes y tres datos de cada uno. Son los mismos números que la
# matriz `datos` de la teoría, a propósito: el alumno los ve primero con nombre
# de columna y después indexados, así que indexar no es manipular símbolos sin
# sentido. Los ejercicios calificables, en cambio, usan matrices DISTINTAS y de
# otra forma: si compartieran los números, el primero se resolvería leyendo la
# teoría en vez de la tabla.
_S7_DATOS = [
    [12, 5, 1],
    [9, 7, 0],
    [15, 3, 1],
    [8, 6, 0],
]
_S7_CARACTERISTICAS = ["horas de estudio", "ejercicios resueltos", "¿aprobó?"]


def ver_tabla_datos():
    """La tabla con nombres de columna: el gancho de apertura del cuadernillo."""
    _s7_pintar(
        '<div style="margin:10px 0">'
        + _s7_titulo("Cuatro estudiantes, tres datos de cada uno")
        + _s7_html_matriz(
            _S7_DATOS,
            etiquetas_col=_S7_CARACTERISTICAS,
            etiquetas_fila=[f"ejemplo {i}" for i in range(len(_S7_DATOS))])
        + _s7_pie("Cada <b>fila</b> es un <b>ejemplo</b> (un estudiante). Cada "
                  "<b>columna</b>, una <b>característica</b>. Así se llaman en "
                  "Inteligencia Artificial, y así se van a llamar el resto de "
                  "la carrera.")
        + "</div>")


# =============================================================================
# La diagonal: matriz de confusión
# =============================================================================
# Por qué está aquí: la diagonal, explicada sola, es una curiosidad geométrica
# («las celdas donde los índices coinciden») y se olvida. Puesta sobre una
# matriz de aciertos, es la medida con la que se juzga un modelo. El temario la
# pide esta semana y el curso la usa de verdad en la semana 15, con árboles de
# decisión: decirlo ahora cuesta una línea y le da sentido al recorrido.
_S7_CONFUSION = [
    [8, 1, 1],
    [2, 7, 1],
    [0, 2, 8],
]
_S7_CLASES = ["gato", "perro", "ave"]


def ver_confusion():
    """La matriz cuadrada de aciertos, con la diagonal marcada y su exactitud."""
    aciertos = sum(_S7_CONFUSION[i][i] for i in range(len(_S7_CONFUSION)))
    total = sum(sum(fila) for fila in _S7_CONFUSION)
    _s7_pintar(
        '<div style="margin:10px 0">'
        + _s7_titulo("30 fotos clasificadas: lo que era (filas) contra lo que "
                     "el modelo dijo (columnas)")
        + _s7_html_matriz(
            _S7_CONFUSION, diagonal=True,
            etiquetas_col=[f"dijo {c}" for c in _S7_CLASES],
            etiquetas_fila=[f"era {c}" for c in _S7_CLASES])
        + _s7_pie(
            f"En verde, la <b>diagonal</b>: las celdas donde la fila y la "
            f"columna coinciden, o sea donde el modelo dijo lo que era. Suman "
            f"<b>{aciertos}</b> de <b>{total}</b>, que es un "
            f"<b>{100 * aciertos / total:.1f}%</b>. Todo lo que está fuera de "
            f"la diagonal es un error, y mirando DÓNDE cae se ve qué confunde "
            f"con qué: los perros se le van a gato dos veces.")
        + "</div>")


# =============================================================================
# Transponer: el antes y el después, sin el código
# =============================================================================
def ver_transpuesta():
    """Las dos matrices lado a lado. El código que lo hace es el Ejercicio 3."""
    original = [[1, 2, 3], [4, 5, 6]]
    transpuesta = [[1, 4], [2, 5], [3, 6]]
    columna = (f'<div style="display:inline-block;vertical-align:middle;'
               f'margin:0 6px">')
    flecha = (f'<div style="display:inline-block;vertical-align:middle;'
              f'margin:0 14px;font:700 22px {_S7_FUENTE};color:{_S7_AZUL}">'
              f'&rarr;</div>')
    etiqueta = (f'<div style="font:600 12px {_S7_MONO};color:{_S7_GRIS};'
                f'margin-bottom:3px">')
    _s7_pintar(
        '<div style="margin:10px 0">'
        + _s7_titulo("Transponer: las filas pasan a ser columnas")
        + columna + etiqueta + "2 filas &times; 3 columnas</div>"
        + _s7_html_matriz(original) + "</div>"
        + flecha
        + columna + etiqueta + "3 filas &times; 2 columnas</div>"
        + _s7_html_matriz(transpuesta) + "</div>"
        + _s7_pie("Ni un número cambia de valor: cambian de sitio. El 2 estaba "
                  "en la fila 0, columna 1; acaba en la fila 1, columna 0. "
                  "Los dos índices se intercambian, y con ellos la forma de "
                  "la tabla.")
        + "</div>")


# =============================================================================
# Portada
# =============================================================================
def portada():
    """Tarjeta de bienvenida: la primera salida que produce el propio kernel.

    Cada semana tiene la suya, con su titulo y sus datos. No esta en el motor
    comun a proposito: es lo unico que identifica de un vistazo en que
    cuadernillo esta el estudiante.

    CUIDADO: los «25 puntos» de aqui estan escritos a mano y el constructor los
    suma por su cuenta. Si cambias los puntos de un ejercicio, cambia tambien
    esta linea: build.py compara las dos cifras y falla si no cuadran. Las
    semanas 03 a 06 se quedaron anunciando 80 puntos cuando ya eran otros, y
    nadie lo vio porque este texto viaja comprimido dentro del notebook.
    """
    _s7_pintar(
        f'<div style="font-family:{_S7_FUENTE};background:linear-gradient(135deg,'
        f'#2e2377,{_S7_AZUL});color:#fff;border-radius:10px;padding:18px 22px;'
        'margin:6px 0 10px">'
        '<div style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;'
        'opacity:.82">Semana 7 · Unidad 7</div>'
        '<div style="font-size:26px;font-weight:700;margin:2px 0 6px">Matrices</div>'
        '<div style="font-size:14.5px;line-height:1.5;opacity:.94">Listas bidimensionales: filas, columnas y datos en tabla.<br>'
        '<span style="opacity:.8">25 puntos · 5 XP · insignia «Quien tabula»</span></div></div>')


# Alias: los cuadernillos 1 y 2 estrenaron dos nombres distintos para lo mismo
# --iniciar() y portada()-- y conviene que los dos funcionen en todas las
# semanas. Que un alumno escriba el de otro cuadernillo y le salte un NameError
# en la PRIMERA celda es la peor bienvenida posible, y ya paso una vez.
iniciar = portada
