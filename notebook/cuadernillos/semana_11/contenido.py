"""Contenido propio de la SEMANA 11: «Programación orientada a objetos».

Qué es esto
-----------
Lo de esta semana y nada más: el quiz del calentamiento, dos figuras y la
portada.

- `quiz_dato_y_calculo()`   el calentamiento. Repasa lo de la semana 8 que hace
                            falta HOY: un diccionario agrupa DATOS, y el
                            cálculo sobre esos datos se queda fuera, en una
                            función aparte. Esa separación es el problema que
                            una clase resuelve, así que conviene que el alumno
                            la haya visto como un problema antes de que
                            aparezca la palabra «clase».
- `ver_dict_vs_objeto()`    el puente: la misma corrida a la izquierda como
                            diccionario + función suelta, y a la derecha como
                            objeto con su método dentro. Es el gancho conceptual
                            de la semana —agrupar estado Y comportamiento— y se
                            ve en dos segundos, que es menos de lo que cuesta
                            leerlo en prosa.
- `ver_anatomia_clase()`    la figura que sostiene el cuadernillo: las cinco
                            piezas de una clase numeradas sobre el código
                            (`class`, `__init__`, `self.atributo`, el método, y
                            la instancia), con una tabla al lado que dice cómo
                            se llama cada una y qué hace.

UN SOLO EJEMPLO PARA TODA LA TEORÍA, y es una decisión, no pereza
-----------------------------------------------------------------
El quiz, las dos figuras y el laboratorio usan la MISMA clase, `Corrida` (una
corrida de entrenamiento: su modelo y sus épocas). Primero porque un ejemplo
que crece se sigue mejor que cuatro que se estrenan. Y segundo, que es lo que
de verdad obliga: `Corrida` **no es la respuesta de ningún ejercicio**.

Esa segunda razón costó una reescritura de este archivo. La primera versión
dibujaba en el puente `class Experimento` con `__init__(nombre, epocas, error)`
y un método `mejoro()`, que es exactamente lo que pide el Ejercicio 1. El
ejercicio quedaba resuelto con Ctrl-F sobre la figura de teoría — la primera
señal de la lista de `docs/cuadernillos_semanas_7_a_16.md` §2 para decir que un
ejercicio sobra. Si mañana alguien cambia el ejemplo de estas figuras, tiene
que seguir cumpliendo esto: la teoría enseña la FORMA, no la respuesta.

Por qué `ver_anatomia_clase()` es la pieza clave, y no un adorno
----------------------------------------------------------------
`self` es donde se atasca todo el mundo en su primera semana de POO, y se atasca
por una razón concreta: en la definición `self` es un parámetro más, pero en la
llamada **no se escribe**. Explicado en prosa son dos párrafos que se leen y no
se entienden; señalado con una marca sobre las dos líneas a la vez —la del
`def` y la de la llamada— se entiende de un vistazo. Esta figura es ese
señalamiento, y por eso va antes del laboratorio y no después.

Lo que esta figura NO hace: inventar vocabulario. Las cinco palabras que usa
—clase, constructor, atributo, método, instancia— son las que el alumno va a
leer en cualquier otro material del tema, y las mismas que usa el glosario del
cierre.

Prefijos `_s11_` en todo lo privado: los módulos de cada semana se cargan en el
MISMO espacio de nombres que el motor, así que un nombre repetido pisaría el de
otra semana sin avisar.

Y una regla que importa MÁS esta semana que ninguna otra: **aquí no se define
ninguna clase a nivel de módulo**. Este archivo se incrusta en la primera celda
y todo lo que define queda en el espacio global del cuadernillo desde antes de
que el alumno escriba una línea. Si definiera `Experimento`, `Lote` o
`ColaDeLectura` —los tres nombres que son la respuesta de los ejercicios—
pasarían dos cosas: la guarda «ejecuta primero TU celda» no podría saltar nunca
(el nombre existe siempre) y la celda de prueba calificaría la clase de ESTE
archivo en vez de la del alumno. El constructor avisa de esto al construir
(`_respuestas_que_pisan`); mejor no llegar a que avise. Las figuras dibujan
clases, pero las dibujan como TEXTO.

Dependencias: biblioteca estándar. Sin pandas, sin numpy y sin matplotlib: esta
semana no hacen falta, y un import aquí dejaría su nombre suelto en el espacio
global del alumno.
"""
from IPython.display import HTML as _HTML11, display as _display11

_S11_VIOLETA = "#4a3aa7"
_S11_AZUL = "#2a78d6"
_S11_AMBAR = "#eda100"
_S11_VERDE = "#0ca30c"
_S11_ROJO = "#c0392b"
_S11_GRIS = "#52514e"
_S11_GRIS_SUAVE = "#f4f5f7"
_S11_BORDE = "#dfe3e8"
_S11_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
_S11_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _s11_pintar(html):
    _display11(_HTML11(html))


def _s11_motor():
    return globals().get("ava")


def _s11_escapar(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _s11_titulo(texto):
    return (f'<div style="font:600 13.5px {_S11_FUENTE};color:{_S11_VIOLETA};'
            f'margin-bottom:4px">{texto}</div>')


def _s11_pie(texto):
    return (f'<div style="font:12.5px {_S11_FUENTE};color:{_S11_GRIS};'
            f'margin-top:6px;max-width:680px">{texto}</div>')


def _s11_panel(lineas, titulo, color):
    """Un bloque de código monoespaciado, con su rótulo encima.

    `lineas` llega ya escapada por quien la arma: algunas traen marcado
    (`<span>`, `<b>`) y escaparlas aquí lo destruiría.
    """
    cuerpo = "".join(
        f'<div style="white-space:pre;font:12.5px/1.65 {_S11_MONO};'
        f'min-height:1.65em">{l}</div>'
        for l in lineas)
    return (
        '<div style="display:inline-block;vertical-align:top;margin:0 12px 8px 0">'
        f'<div style="font:600 11.5px {_S11_FUENTE};color:{color};'
        'text-transform:uppercase;letter-spacing:.05em;margin-bottom:5px">'
        f'{titulo}</div>'
        f'<div style="border:1px solid {_S11_BORDE};border-left:3px solid {color};'
        f'border-radius:5px;background:{_S11_GRIS_SUAVE};padding:10px 14px">'
        f'{cuerpo}</div></div>')


# =============================================================================
# Calentamiento
# =============================================================================
def quiz_dato_y_calculo():
    """Una de la semana 8, elegida porque es el problema que abre esta semana.

    No es un repaso de relleno: el cuadernillo entero descansa en que el alumno
    sienta como un problema algo que hasta ahora le parecía normal —que los
    datos vayan en un diccionario y el cálculo sobre ellos en una función
    suelta, sin nada que los ate—. Quien no vea ahí un problema va a leer el
    resto del cuadernillo como «otra sintaxis para hacer lo mismo».
    """
    ava = _s11_motor()
    if ava is None:
        return
    return ava.quiz(
        "s11_dato_y_calculo", 5,
        "Guardas una corrida de entrenamiento en un diccionario: "
        "{'modelo': 'resnet', 'epocas': 20}. Y escribes aparte una funcion "
        "larga(corrida) que mira si paso de 10 epocas. ¿Que impide que alguien "
        "use ese diccionario sin enterarse de que larga() existe?",
        ["el diccionario no deja: hay que pasar por la funcion",
         "nada: el dato y el calculo viajan por separado",
         "la funcion queda guardada dentro del diccionario",
         "Python avisa con un error al imprimir el diccionario"],
        1,
        "Nada lo impide. El diccionario no sabe que larga() existe, y larga() "
        "no sabe si el diccionario que le llega trae las claves que espera: son "
        "dos cosas sueltas que alguien tiene que acordarse de juntar. Esta "
        "semana vas a atarlas: los datos y lo que se calcula con ellos, en un "
        "solo sitio.",
    )


# =============================================================================
# El puente: la misma corrida, suelta y agrupada
# =============================================================================
def ver_dict_vs_objeto():
    """La misma corrida a los dos lados del puente.

    Izquierda: diccionario + función suelta, que es lo que el alumno sabe hacer
    desde la semana 8. Derecha: lo mismo con el cálculo dentro. Los datos son
    los mismos a los dos lados a propósito: lo que cambia no es qué se guarda,
    es quién es el dueño del cálculo.
    """
    rojo = f'<span style="color:{_S11_ROJO}">'
    verde = f'<span style="color:{_S11_VERDE}">'
    izquierda = _s11_panel([
        "c = {&quot;modelo&quot;: &quot;resnet&quot;,",
        "     &quot;epocas&quot;: 20}",
        "",
        "def larga(corrida):",
        "    return corrida[&quot;epocas&quot;] &gt; 10",
        "",
        f'{rojo}# acuerdate de las dos cosas</span>',
        f'{rojo}larga(c)</span>',
    ], "lo que ya sabes hacer", _S11_GRIS)
    derecha = _s11_panel([
        "class Corrida:",
        "    def __init__(self, modelo, epocas):",
        "        self.modelo = modelo",
        "        self.epocas = epocas",
        "",
        "    def larga(self):",
        "        return self.epocas &gt; 10",
        "",
        f'{verde}c = Corrida(&quot;resnet&quot;, 20)</span>',
        f'{verde}c.larga()</span>',
    ], "lo de esta semana", _S11_VERDE)
    _s11_pintar(
        '<div style="margin:10px 0">'
        + _s11_titulo("La misma corrida, suelta y agrupada")
        + izquierda + derecha
        + _s11_pie(
            "Los datos son los mismos a los dos lados; lo que cambia es de "
            "quién es el cálculo. A la izquierda, <code>larga</code> es una "
            "función que vive aparte: hay que saber que existe, hay que pasarle "
            "el diccionario correcto, y nada avisa si le pasas otro que no "
            "tiene la clave <code>epocas</code>. A la derecha, "
            "<code>larga</code> es algo que una corrida <b>sabe hacer</b>: se "
            "le pide a ella, <code>c.larga()</code>, y ella ya tiene sus "
            "propios datos. Eso es lo único que significa «orientado a "
            "objetos»: el estado y el comportamiento que va con ese estado, "
            "guardados juntos.")
        + "</div>")


# =============================================================================
# La figura clave: las cinco piezas de una clase, y dónde está `self`
# =============================================================================
# Cada fila es (numero de marca, linea de codigo ya escapada). Con None, la
# linea va sin marca.
_S11_ANATOMIA = [
    ("1", "class Corrida:"),
    ("2", "    def __init__(self, modelo, epocas):"),
    ("3", "        self.modelo = modelo"),
    (None, "        self.epocas = epocas"),
    (None, ""),
    ("4", "    def larga(self):"),
    (None, "        return self.epocas &gt; 10"),
    (None, ""),
    ("5", "c = Corrida(&quot;resnet&quot;, 20)"),
    (None, "c.larga()"),
]

_S11_PIEZAS = [
    ("1", "Clase", "class Corrida:",
     "La plantilla. No es una corrida: es el molde del que salen."),
    ("2", "Constructor", "__init__",
     "Lo que corre al crear una. Recibe los datos y los guarda."),
    ("3", "Atributo", "self.modelo = modelo",
     "Un dato pegado a ESA corrida. A la derecha del <code>=</code>, el "
     "parámetro que llegó; a la izquierda, el atributo que se queda."),
    ("4", "Método", "def larga(self):",
     "Algo que una corrida sabe hacer con sus propios atributos."),
    ("5", "Instancia", 'Corrida("resnet", 20)',
     "Una corrida concreta, con sus valores. Caben todas las que quieras."),
]


def _s11_badge(n):
    if n is None:
        return '<span style="display:inline-block;width:19px"></span>'
    return (f'<span style="display:inline-block;width:19px;height:19px;'
            f'line-height:19px;text-align:center;border-radius:50%;'
            f'background:{_S11_AMBAR};color:#fff;font:700 11.5px {_S11_MONO}">'
            f'{n}</span>')


def ver_anatomia_clase():
    """Las cinco piezas de una clase, numeradas sobre el código.

    La tabla de la derecha es la que convierte cinco palabras nuevas en algo
    que se puede señalar con el dedo. Y el pie dice lo único que de verdad hay
    que entender de `self`, que es donde se atasca todo el mundo: en el `def`
    se escribe y en la llamada no.
    """
    filas_codigo = "".join(
        '<tr><td style="padding:1px 10px 1px 0;vertical-align:top">'
        + _s11_badge(n) + "</td>"
        f'<td style="padding:1px 0;white-space:pre;font:12.5px/1.7 {_S11_MONO}">'
        f'{linea}</td></tr>'
        for n, linea in _S11_ANATOMIA)
    filas_tabla = "".join(
        '<tr><td style="padding:4px 10px 4px 0;vertical-align:top">'
        + _s11_badge(n) + "</td>"
        f'<td style="padding:4px 12px 4px 0;font:600 13px {_S11_FUENTE};'
        f'white-space:nowrap;vertical-align:top">{nombre}</td>'
        f'<td style="padding:4px 12px 4px 0;font:12.5px {_S11_MONO};'
        f'color:{_S11_VIOLETA};white-space:nowrap;vertical-align:top">'
        f'{_s11_escapar(codigo)}</td>'
        f'<td style="padding:4px 0;font:12.5px {_S11_FUENTE};'
        f'color:{_S11_GRIS};max-width:320px">{que}</td></tr>'
        for n, nombre, codigo, que in _S11_PIEZAS)
    _s11_pintar(
        '<div style="margin:10px 0">'
        + _s11_titulo("Las cinco piezas, y dónde está cada una")
        + '<div style="display:inline-block;vertical-align:top;'
          f'border:1px solid {_S11_BORDE};border-radius:5px;'
          f'background:{_S11_GRIS_SUAVE};padding:10px 14px;margin:0 14px 8px 0">'
        + f'<table style="border-collapse:collapse">{filas_codigo}</table>'
        + "</div>"
        + '<div style="display:inline-block;vertical-align:top">'
        + f'<table style="border-collapse:collapse">{filas_tabla}</table>'
        + "</div>"
        + _s11_pie(
            "Y lo único que hay que entender de <code>self</code>, que es "
            "donde se atasca todo el mundo: en los dos <code>def</code> "
            "—las marcas <b>2</b> y <b>4</b>— se escribe como primer "
            "parámetro, y al llamar al método —la marca <b>5</b>— <b>no se "
            "escribe</b>. <code>c.larga()</code> va sin "
            "argumentos, y aun así dentro del método <code>self</code> vale "
            "<code>c</code>: lo pone Python por el hecho de haber escrito el "
            "punto. <code>self</code> es «la corrida a la que se lo estás "
            "pidiendo», y es la razón de que un método pueda usar "
            "<code>self.epocas</code> sin que nadie se lo pase.")
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
    _s11_pintar(
        f'<div style="font-family:{_S11_FUENTE};background:linear-gradient(135deg,'
        f'#2e2377,{_S11_AZUL});color:#fff;border-radius:10px;padding:18px 22px;'
        'margin:6px 0 10px">'
        '<div style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;'
        # «Unidad 11» y no «Unidad 4», que es como la llama la planeacion: las
        # portadas publicadas numeran la unidad por la semana desde la 4, y un
        # salto de «Unidad 10» a «Unidad 4» lo reportaria el alumno como error.
        # El NOMBRE del tema si es el de la planeacion, literal. Ver el
        # docstring del generador.
        'opacity:.82">Semana 11 · Unidad 11</div>'
        '<div style="font-size:26px;font-weight:700;margin:2px 0 6px">'
        'Programacion orientada a objetos</div>'
        '<div style="font-size:14.5px;line-height:1.5;opacity:.94">Clases, '
        'atributos, __init__ y metodos: el estado y el comportamiento, juntos.<br>'
        '<span style="opacity:.8">25 puntos · 5 XP · insignia «Quien modela»'
        '</span></div></div>')


# Alias: los cuadernillos 1 y 2 estrenaron dos nombres distintos para lo mismo
# --iniciar() y portada()-- y conviene que los dos funcionen en todas las
# semanas. Que un alumno escriba el de otro cuadernillo y le salte un NameError
# en la PRIMERA celda es la peor bienvenida posible, y ya paso una vez.
iniciar = portada
