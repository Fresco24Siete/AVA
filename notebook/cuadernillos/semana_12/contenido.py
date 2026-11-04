"""Contenido propio de la SEMANA 12: «Modelado de sistemas (UML)».

Qué es esto
-----------
Lo de esta semana y nada más: el quiz del calentamiento, cuatro figuras y la
portada.

- `quiz_responsabilidad()`  el calentamiento. No repasa la sintaxis de la
                            semana 11 —eso ya lo trae el alumno— sino la
                            pregunta que sostiene esta semana entera: un dato
                            que es el mismo para todo el grupo, ¿de quién es?
- `ver_caja_de_clase()`     la anatomía de una caja UML: nombre, atributos,
                            métodos, y con qué línea de Python se escribe cada
                            compartimento.
- `ver_relaciones()`        las tres relaciones (asociación, agregación,
                            composición) con su multiplicidad, y cómo se
                            escribe cada una.
- `ver_prosa_al_modelo()`   la figura que sostiene el cuadernillo: un párrafo
                            de una organización con el ruido tachado, las tres
                            preguntas que se le hacen, y el modelo que sale.
- `ver_diagrama_lote()`     el diagrama de clases del Ejercicio 1. Es el
                            enunciado: el ejercicio pide escribir ESTAS dos
                            clases, y el diagrama es lo que dice cuáles son.

Por qué los diagramas van en SVG escrito a mano
-----------------------------------------------
Un diagrama UML **no se puede autocalificar**: dibujar cajas y flechas no
produce nada que un `assert` pueda mirar, y una imagen subida no emite
telemetría. Así que esta semana el UML vive en la TEORÍA —donde tiene que
verse de verdad, con sus diamantes y su `1..*`— y lo que se califica es el
**modelo en código**.

Eso obliga a que los diagramas estén dibujados y no generados: se pintan antes
de que el alumno importe nada, al alumno le llega **un solo archivo** (no
viajan imágenes), y el contenedor no tiene Node para Mermaid. Las semanas 03 a
10 ya resolvieron esto igual: SVG a mano dentro de `contenido.py`. Los `.mmd`
de `diagramas/` son de la semana 01 y exigen Node en la máquina de quien
autora; aquí no hacía falta añadir esa dependencia.

Los cuatro dominios NO se repiten, y es a propósito
---------------------------------------------------
`ver_relaciones()` y el laboratorio usan conjuntos de datos y particiones;
`ver_prosa_al_modelo()`, la cola de GPU de un laboratorio; el Ejercicio 1,
lotes e imágenes; el 2, experimentos y corridas; el 3, modelos desplegados y
peticiones. Si la figura del método usara el dominio de un ejercicio, ese
ejercicio se resolvería leyendo la figura —lo que el repositorio llama
«se resuelve con Ctrl-F sobre la celda de teoría»— y dejaría de medir nada.

Prefijos `_s12_` en todo lo privado: los módulos de cada semana se cargan en el
MISMO espacio de nombres que el motor, así que un nombre repetido pisaría el de
otra semana sin avisar.

Dependencias: biblioteca estándar. Nada de pandas, numpy ni matplotlib: esta
semana no se dibuja ni se calcula con tablas, y un `import` aquí dejaría el
nombre suelto en el espacio global desde la primera celda.
"""
from IPython.display import HTML as _HTML12, display as _display12

_S12_VIOLETA = "#4a3aa7"
_S12_AZUL = "#2a78d6"
_S12_AMBAR = "#eda100"
_S12_VERDE = "#0ca30c"
_S12_ROJO = "#c0392b"
_S12_GRIS = "#52514e"
_S12_GRIS_SUAVE = "#f4f5f7"
_S12_BORDE = "#dfe3e8"
_S12_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
_S12_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _s12_pintar(html):
    _display12(_HTML12(html))


def _s12_motor():
    return globals().get("ava")


def _s12_escapar(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _s12_titulo(texto):
    return (f'<div style="font:600 13.5px {_S12_FUENTE};color:{_S12_VIOLETA};'
            f'margin-bottom:4px">{texto}</div>')


def _s12_pie(texto):
    return (f'<div style="font:12.5px {_S12_FUENTE};color:{_S12_GRIS};'
            f'margin-top:6px;max-width:680px">{texto}</div>')


# =============================================================================
# Calentamiento
# =============================================================================
def quiz_responsabilidad():
    """La pregunta que sostiene la semana, hecha antes de explicar nada.

    No es un repaso de la semana 11: la sintaxis de `class` ya la trae. Lo que
    se pregunta es de QUIÉN es un dato, que es la decisión que el alumno va a
    tomar mal tres veces si no la ve aquí — y aquí no cuesta nota.
    """
    ava = _s12_motor()
    if ava is None:
        return
    return ava.quiz(
        "s12_responsabilidad", 5,
        "Un lote de imágenes tiene un código y una fecha de entrega. Cada "
        "imagen del lote tiene un nombre y un ancho. Las 400 imágenes del lote "
        "se entregan el mismo día. ¿Dónde vive la fecha de entrega?",
        ["en cada Imagen", "en el Lote", "en las dos, por seguridad",
         "en ninguna: es un dato del cliente"],
        1,
        "Un dato que vale lo mismo para todo el grupo es del grupo, no de cada "
        "miembro. Guardarlo 400 veces no solo gasta: permite que el sistema se "
        "contradiga, porque nada impide que dos imágenes del mismo lote acaben "
        "con fechas distintas. Decidir de quién es cada dato es la mitad del "
        "trabajo de modelar, y es lo que vas a hacer hoy tres veces.",
    )


# =============================================================================
# Figura 1: la anatomía de una caja UML
# =============================================================================
_S12_FILA = 19


def _s12_caja(x, y, ancho, nombre, atributos, metodos, numerar=False):
    """Una caja de clase UML: tres compartimentos. Devuelve (svg, alto)."""
    alto_nombre = 28
    alto_atr = _S12_FILA * max(1, len(atributos)) + 10
    alto_met = _S12_FILA * max(1, len(metodos)) + 10
    alto = alto_nombre + alto_atr + alto_met

    partes = [
        f'<rect x="{x}" y="{y}" width="{ancho}" height="{alto}" rx="3" '
        f'fill="#ffffff" stroke="{_S12_GRIS}" stroke-width="1.4"/>',
        f'<rect x="{x}" y="{y}" width="{ancho}" height="{alto_nombre}" rx="3" '
        f'fill="{_S12_GRIS_SUAVE}" stroke="{_S12_GRIS}" stroke-width="1.4"/>',
        f'<text x="{x + ancho / 2}" y="{y + 19}" text-anchor="middle" '
        f'font-family="{_S12_FUENTE}" font-size="13.5" font-weight="700" '
        f'fill="#0b0b0b">{_s12_escapar(nombre)}</text>',
    ]
    tope_atr = y + alto_nombre
    for i, texto in enumerate(atributos):
        partes.append(
            f'<text x="{x + 10}" y="{tope_atr + 18 + i * _S12_FILA}" '
            f'font-family="{_S12_MONO}" font-size="11.5" '
            f'fill="{_S12_VIOLETA}">{_s12_escapar(texto)}</text>')
    tope_met = tope_atr + alto_atr
    partes.append(
        f'<line x1="{x}" y1="{tope_met}" x2="{x + ancho}" y2="{tope_met}" '
        f'stroke="{_S12_GRIS}" stroke-width="1.4"/>')
    for i, texto in enumerate(metodos):
        partes.append(
            f'<text x="{x + 10}" y="{tope_met + 18 + i * _S12_FILA}" '
            f'font-family="{_S12_MONO}" font-size="11.5" '
            f'fill="{_S12_VERDE}">{_s12_escapar(texto)}</text>')

    if numerar:
        for n, cy in (("1", y + 14), ("2", tope_atr + 14),
                      ("3", tope_met + 14)):
            partes.append(_s12_marca(x - 15, cy, n))
    return "".join(partes), alto


def _s12_marca(x, y, n):
    return (f'<circle cx="{x}" cy="{y}" r="10" fill="{_S12_AMBAR}"/>'
            f'<text x="{x}" y="{y + 4}" text-anchor="middle" '
            f'font-family="{_S12_MONO}" font-size="12" font-weight="700" '
            f'fill="#ffffff">{n}</text>')


_S12_COMPARTIMENTOS = [
    ("1", "Nombre", "qué clase es", "class Particion:"),
    ("2", "Atributos", "los datos de cada objeto",
     "self.nombre = nombre   (en __init__)"),
    ("3", "Métodos", "las preguntas que sabe contestar", "def es_grande(self):"),
]


def ver_caja_de_clase():
    """La caja UML y, al lado, con qué línea de Python se escribe cada parte.

    Hace falta porque el alumno ya sabe escribir una clase pero no ha visto
    nunca el dibujo: sin esta tabla, los tres compartimentos son decoración.
    """
    caja, alto = _s12_caja(
        26, 14, 210, "Particion",
        ["nombre: str", "ejemplos: int"],
        ["es_grande(): bool"],
        numerar=True)
    svg = (f'<svg viewBox="0 0 250 {alto + 28}" width="250" '
           f'height="{alto + 28}" xmlns="http://www.w3.org/2000/svg" '
           'role="img" aria-label="Caja de clase UML con sus tres '
           'compartimentos numerados: nombre, atributos y metodos.">'
           + caja + '</svg>')
    filas = "".join(
        f'<tr><td style="padding:5px 10px 5px 0;text-align:center">'
        f'<span style="display:inline-block;width:19px;height:19px;'
        f'line-height:19px;border-radius:50%;background:{_S12_AMBAR};'
        f'color:#fff;font:700 11.5px {_S12_MONO}">{n}</span></td>'
        f'<td style="padding:5px 12px 5px 0;text-align:left;'
        f'font:600 13px {_S12_FUENTE}">'
        f'{parte}</td>'
        f'<td style="padding:5px 12px 5px 0;text-align:left;'
        f'font:12.5px {_S12_FUENTE};color:{_S12_GRIS}">{que}</td>'
        f'<td style="padding:5px 0;text-align:left;font:12.5px {_S12_MONO};'
        f'color:{_S12_AZUL}">{_s12_escapar(py)}</td></tr>'
        for n, parte, que, py in _S12_COMPARTIMENTOS)
    _s12_pintar(
        '<div style="margin:10px 0">'
        + _s12_titulo("Una caja de clase, compartimento por compartimento")
        + '<div style="display:inline-block;vertical-align:middle">'
        + svg + '</div>'
        + '<div style="display:inline-block;vertical-align:middle;'
          'margin-left:16px">'
        + '<table style="border-collapse:collapse">'
        + f'<tr><td></td>'
          f'<td style="text-align:left;padding:0 12px 6px 0;font:600 11px {_S12_FUENTE};'
          f'color:{_S12_GRIS};text-transform:uppercase;letter-spacing:.05em">'
          f'compartimento</td>'
          f'<td style="text-align:left;padding:0 12px 6px 0;'
          f'font:600 11px {_S12_FUENTE};color:{_S12_GRIS};'
          f'text-transform:uppercase;letter-spacing:.05em">qué es</td>'
          f'<td style="text-align:left;padding:0 0 6px 0;'
          f'font:600 11px {_S12_FUENTE};color:{_S12_AZUL};'
          f'text-transform:uppercase;letter-spacing:.05em">en Python</td></tr>'
        + filas + '</table></div>'
        + _s12_pie(
            "Los tipos (<code>str</code>, <code>int</code>, "
            "<code>bool</code>) van en el dibujo para que se lea sin ejecutar "
            "nada; Python no los exige. Y fíjate en el reparto: arriba lo que "
            "el objeto <b>sabe</b>, abajo lo que el objeto <b>contesta</b>.")
        + "</div>")


# =============================================================================
# Figura 2: las tres relaciones
# =============================================================================
def _s12_flecha(x1, x2, y, adorno, izq, der):
    """Una línea de relación con su adorno y su multiplicidad a cada punta."""
    partes = []
    if adorno == "diamante_lleno":
        partes.append(
            f'<polygon points="{x1},{y} {x1 + 11},{y - 7} {x1 + 22},{y} '
            f'{x1 + 11},{y + 7}" fill="{_S12_GRIS}" stroke="{_S12_GRIS}"/>')
        inicio = x1 + 22
    elif adorno == "diamante_vacio":
        partes.append(
            f'<polygon points="{x1},{y} {x1 + 11},{y - 7} {x1 + 22},{y} '
            f'{x1 + 11},{y + 7}" fill="#ffffff" stroke="{_S12_GRIS}" '
            'stroke-width="1.4"/>')
        inicio = x1 + 22
    else:
        inicio = x1
    partes.append(
        f'<line x1="{inicio}" y1="{y}" x2="{x2 - 10}" y2="{y}" '
        f'stroke="{_S12_GRIS}" stroke-width="1.4"/>')
    partes.append(
        f'<polyline points="{x2 - 10},{y - 6} {x2},{y} {x2 - 10},{y + 6}" '
        f'fill="none" stroke="{_S12_GRIS}" stroke-width="1.4"/>')
    partes.append(
        f'<text x="{inicio + 6}" y="{y - 8}" font-family="{_S12_MONO}" '
        f'font-size="11.5" font-weight="700" fill="{_S12_ROJO}">'
        f'{_s12_escapar(izq)}</text>')
    partes.append(
        f'<text x="{x2 - 16}" y="{y - 8}" text-anchor="end" '
        f'font-family="{_S12_MONO}" font-size="11.5" font-weight="700" '
        f'fill="{_S12_ROJO}">{_s12_escapar(der)}</text>')
    return "".join(partes)


_S12_RELACIONES = [
    ("asociación", "linea", "1", "1",
     "A <b>conoce</b> a B. Los dos existen por su cuenta.",
     "self.b = b"),
    ("agregación", "diamante_vacio", "1", "1..*",
     "A <b>agrupa</b> varios B, pero los B ya existían y siguen existiendo "
     "si A desaparece.",
     "self.bes = []  y  agregar(b)"),
    ("composición", "diamante_lleno", "1", "1..*",
     "A es <b>dueño</b> de sus B: los crea él y no tienen sentido sin él.",
     "self.bes = []  y A crea cada b"),
]


def ver_relaciones():
    """Las tres relaciones, su adorno, su multiplicidad y su línea de Python.

    La columna de Python es la que convierte el dibujo en algo que se puede
    escribir: en Python las tres se parecen mucho, y lo que de verdad cambia es
    quién CREA el objeto y quién lo GUARDA. Si eso no se dice, el alumno cree
    que el diamante es un adorno.
    """
    alto_fila = 62
    svg_filas = []
    for i, (nombre, adorno, izq, der, _, _) in enumerate(_S12_RELACIONES):
        y = 34 + i * alto_fila
        svg_filas.append(
            f'<rect x="4" y="{y - 17}" width="52" height="34" rx="3" '
            f'fill="{_S12_GRIS_SUAVE}" stroke="{_S12_GRIS}" '
            'stroke-width="1.3"/>'
            f'<text x="30" y="{y + 5}" text-anchor="middle" '
            f'font-family="{_S12_FUENTE}" font-size="13" font-weight="700">A'
            '</text>'
            + _s12_flecha(58, 196, y, adorno, izq, der)
            + f'<rect x="196" y="{y - 17}" width="52" height="34" rx="3" '
              f'fill="{_S12_GRIS_SUAVE}" stroke="{_S12_GRIS}" '
              'stroke-width="1.3"/>'
              f'<text x="222" y="{y + 5}" text-anchor="middle" '
              f'font-family="{_S12_FUENTE}" font-size="13" '
              'font-weight="700">B</text>'
            + f'<text x="130" y="{y + 28}" text-anchor="middle" '
              f'font-family="{_S12_FUENTE}" font-size="11.5" '
              f'fill="{_S12_VIOLETA}" font-weight="600">{nombre}</text>')
    svg = (f'<svg viewBox="0 0 258 {34 + len(_S12_RELACIONES) * alto_fila}" '
           f'width="258" height="{34 + len(_S12_RELACIONES) * alto_fila}" '
           'xmlns="http://www.w3.org/2000/svg" role="img" '
           'aria-label="Las tres relaciones UML entre dos clases A y B: '
           'asociacion con linea simple, agregacion con diamante vacio y '
           'composicion con diamante lleno.">'
           + "".join(svg_filas) + '</svg>')
    filas = "".join(
        f'<tr><td style="padding:6px 12px 6px 0;text-align:left;'
        f'font:600 13px {_S12_FUENTE};color:{_S12_VIOLETA};'
        f'white-space:nowrap">{nombre}</td>'
        f'<td style="padding:6px 12px 6px 0;text-align:left;'
        f'font:12.5px {_S12_FUENTE};color:{_S12_GRIS};'
        f'max-width:300px">{que}</td>'
        f'<td style="padding:6px 0;text-align:left;font:12.5px {_S12_MONO};'
        f'color:{_S12_AZUL};white-space:nowrap">{_s12_escapar(py)}</td></tr>'
        for nombre, _, _, _, que, py in _S12_RELACIONES)
    _s12_pintar(
        '<div style="margin:10px 0">'
        + _s12_titulo("Las tres relaciones, y qué línea de Python es cada una")
        + '<div style="display:inline-block;vertical-align:top">'
        + svg + '</div>'
        + '<div style="display:inline-block;vertical-align:top;'
          'margin-left:16px;padding-top:14px">'
        + '<table style="border-collapse:collapse">' + filas + '</table>'
        + f'<div style="font:12.5px {_S12_FUENTE};color:{_S12_GRIS};'
          f'margin-top:10px;max-width:420px">Los números rojos son la '
          '<b>multiplicidad</b>: cuántos objetos de ese lado participan. '
          '<code>1</code> uno exactamente, <code>0..1</code> uno o ninguno, '
          '<code>1..*</code> uno o más, <code>*</code> cualquier cantidad, '
          'cero incluida.</div>'
        + '</div>'
        + _s12_pie(
            "Mira la columna azul: en Python las tres se escriben casi igual. "
            "Lo que cambia es <b>quién crea</b> el objeto y <b>quién lo "
            "guarda</b>. El diagrama dice la intención; el código la cumple. "
            "Y un <code>1..*</code> siempre es lo mismo: una lista (o un "
            "diccionario) dentro del objeto del lado <code>1</code>.")
        + "</div>")


# =============================================================================
# Figura 3: de la prosa al modelo. La pieza clave del cuadernillo.
# =============================================================================
# El dominio es la cola de GPU de un laboratorio, y no el de ningun ejercicio,
# a proposito: si fuera el de uno, ese ejercicio se resolveria leyendo esta
# figura. Ver el docstring del modulo.
_S12_PROSA = [
    ("El laboratorio tiene tres GPU y los investigadores ", False),
    ("encolan trabajos", True),
    (". De cada trabajo se guarda ", False),
    ("quién lo lanzó", "ruido"),
    (", ", False),
    ("en qué GPU corrió", True),
    (", ", False),
    ("cuántos minutos duró", "clave"),
    (" y ", False),
    ("el código del proyecto que lo paga", "ruido"),
    (". El director quiere saber, ", False),
    ("de cada GPU", True),
    (", ", False),
    ("cuántos minutos se usó", "clave"),
    (".", False),
]

_S12_PREGUNTAS = [
    ("1", "¿Qué cosas hay, y cuál agrupa a las otras?",
     "Los sustantivos que se repiten y tienen datos propios. "
     "Aquí: <b>GPU</b> y <b>Trabajo</b>. Y la pregunta del final dice cuál "
     "agrupa: «de cada GPU».", _S12_AZUL),
    ("2", "¿Qué dato decide la respuesta?",
     "El que aparece en la pregunta del final: los <b>minutos</b>. "
     "Ese es el que no puede faltar en el modelo.", _S12_VERDE),
    ("3", "¿Qué sobra?",
     "Todo lo que no hace falta para contestar: el investigador y el proyecto "
     "que paga. Son datos de verdad del sistema, pero <b>no de este "
     "modelo</b>.", _S12_ROJO),
]


def ver_prosa_al_modelo():
    """El método de la semana: tres preguntas sobre un párrafo, y el modelo.

    Es la pieza que convierte «modela este sistema» en algo que se puede
    hacer. Y es deliberado que el párrafo traiga ruido: en un enunciado de
    clase todo dato sirve, y en una descripción de verdad, no. Reconocer qué
    sobra es la mitad del trabajo, y es lo que miden los ejercicios 2 y 3.
    """
    trozos = []
    for texto, marca in _S12_PROSA:
        if marca == "ruido":
            trozos.append(
                f'<span style="color:{_S12_ROJO};text-decoration:line-through;'
                f'opacity:.75">{texto}</span>')
        elif marca == "clave":
            trozos.append(
                f'<span style="background:#e3f6e3;color:#0a6b0a;'
                f'font-weight:600;padding:0 2px">{texto}</span>')
        elif marca is True:
            trozos.append(
                f'<span style="background:#e6effb;color:#1b4f8f;'
                f'font-weight:600;padding:0 2px">{texto}</span>')
        else:
            trozos.append(texto)
    parrafo = (f'<div style="font:14px/1.65 {_S12_FUENTE};color:#0b0b0b;'
               f'background:#ffffff;border:1px solid {_S12_BORDE};'
               f'border-left:4px solid {_S12_VIOLETA};border-radius:4px;'
               f'padding:12px 14px;max-width:470px">'
               + "".join(trozos) + '</div>')

    gpu, alto_gpu = _s12_caja(
        8, 12, 180, "GPU", ["modelo: str", "trabajos: list"],
        ["agregar(trabajo)", "minutos_usados(): int"])
    # El hueco entre las dos cajas es donde va el conector vertical: diamante
    # (20 px), linea (16) y punta de flecha (10). Si se cambia, se descuadra.
    y0 = 12 + alto_gpu
    trabajo, alto_tr = _s12_caja(
        8, y0 + 46, 180, "Trabajo", ["minutos: int"], [])
    alto_svg = y0 + 46 + alto_tr + 12
    svg = (f'<svg viewBox="0 0 196 {alto_svg}" width="196" '
           f'height="{alto_svg}" xmlns="http://www.w3.org/2000/svg" '
           'role="img" aria-label="Modelo que sale del parrafo: la clase GPU '
           'agrupa uno o mas Trabajo, con relacion de agregacion.">'
           + gpu + trabajo
           # Diamante VACIO: AGREGACION. El parrafo dice que los investigadores
           # «encolan trabajos», o sea que el trabajo ya existe y lo crea otro
           # —igual que el `agregar(particion)` del laboratorio—. Hasta el
           # 2026-11-03 iba lleno (composicion) y se contradecia con la tabla de
           # la seccion 3, que define el lleno como «A es dueno: los crea el».
           + f'<polygon points="98,{y0} 105,{y0 + 10} 98,{y0 + 20} '
             f'91,{y0 + 10}" fill="#ffffff" stroke="{_S12_GRIS}" '
             'stroke-width="1.4"/>'
             f'<line x1="98" y1="{y0 + 20}" x2="98" y2="{y0 + 46}" '
             f'stroke="{_S12_GRIS}" stroke-width="1.4"/>'
             f'<polyline points="92,{y0 + 36} 98,{y0 + 46} 104,{y0 + 36}" '
             f'fill="none" stroke="{_S12_GRIS}" stroke-width="1.4"/>'
             f'<text x="108" y="{y0 + 16}" font-family="{_S12_MONO}" '
             f'font-size="11.5" font-weight="700" fill="{_S12_ROJO}">1</text>'
             f'<text x="108" y="{y0 + 44}" font-family="{_S12_MONO}" '
             f'font-size="11.5" font-weight="700" fill="{_S12_ROJO}">1..*'
             '</text>'
           + '</svg>')

    preguntas = "".join(
        f'<tr><td style="padding:6px 10px 6px 0;vertical-align:top;'
        f'text-align:left">'
        f'<span style="display:inline-block;width:19px;height:19px;'
        f'line-height:19px;text-align:center;border-radius:50%;'
        f'background:{color};color:#fff;font:700 11.5px {_S12_MONO}">{n}'
        '</span></td>'
        f'<td style="padding:6px 0;vertical-align:top;text-align:left;'
        f'max-width:430px">'
        f'<div style="font:600 13px {_S12_FUENTE};color:#0b0b0b">{pregunta}'
        '</div>'
        f'<div style="font:12.5px/1.5 {_S12_FUENTE};color:{_S12_GRIS}">'
        f'{respuesta}</div></td></tr>'
        for n, pregunta, respuesta, color in _S12_PREGUNTAS)

    _s12_pintar(
        '<div style="margin:10px 0">'
        + _s12_titulo("De un párrafo de la organización, al modelo")
        + '<div style="display:inline-block;vertical-align:top">' + parrafo
        + '<table style="border-collapse:collapse;margin-top:10px">'
        + preguntas + '</table></div>'
        + '<div style="display:inline-block;vertical-align:top;'
          'margin-left:18px">'
        + f'<div style="font:600 11px {_S12_FUENTE};color:{_S12_GRIS};'
          f'text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px">'
          'el modelo que sale</div>'
        + svg + '</div>'
        + _s12_pie(
            "Lo <span style=\"color:#1b4f8f;font-weight:600\">azul</span> es "
            "estructura, lo <span style=\"color:#0a6b0a;font-weight:600\">"
            "verde</span> es el dato que decide y lo "
            "<span style=\"color:#c0392b;font-weight:600\">tachado</span> es "
            "<b>ruido</b>: aparece en la descripción porque el sistema de "
            "verdad lo guarda, no porque haga falta aquí. Una descripción de "
            "una organización siempre trae ruido — un enunciado de clase, "
            "casi nunca. Esa es la diferencia que entrenan los dos últimos "
            "ejercicios.")
        + "</div>")


# =============================================================================
# Figura 4: el diagrama del Ejercicio 1. Es el enunciado.
# =============================================================================
def ver_diagrama_lote():
    """El diagrama de clases que el Ejercicio 1 pide traducir a código.

    Va en una figura y no en el texto del enunciado porque un diagrama de
    clases es un dibujo: el `1..*` del lado de `Imagen` es lo que dice que
    `imagenes` es una lista. Escrito en prosa, eso serían tres frases y el
    ejercicio dejaría de ser «traduce el diagrama».

    El diamante va VACÍO desde el 2026-11-03. Antes iba lleno, y eso decía
    composición —«el Lote crea sus imágenes»— cuando el enunciado hace
    `lote.agregar(Imagen("IMG_0041.jpg", 320))`: la Imagen la crea quien llama,
    que es la definición de agregación en la tabla de la sección 3. Con el
    diamante lleno, el alumno que se aprendió la tabla no podía reconciliarla
    con el dibujo, y la pregunta del cierre le pedía justo eso.
    """
    imagen, alto_img = _s12_caja(
        345, 46, 200, "Imagen", ["nombre: str", "ancho: int"], [])
    lote, alto_lote = _s12_caja(
        18, 14, 230, "Lote", ["codigo: str", "imagenes: list"],
        ["agregar(imagen)", "cuantas(): int", "nombres(): list"])
    # La relacion va a media altura de las dos cajas, que no empiezan a la
    # misma y: el Lote tiene un compartimento de metodos mas alto.
    y = (14 * 2 + alto_lote + 46 * 2 + alto_img) // 4
    alto_svg = max(14 + alto_lote, 46 + alto_img) + 14
    svg = (f'<svg viewBox="0 0 555 {alto_svg}" '
           f'width="555" height="{alto_svg}" '
           'xmlns="http://www.w3.org/2000/svg" role="img" '
           'aria-label="Diagrama de clases: Lote, con codigo e imagenes, '
           'agrupa por agregacion una o mas Imagen, con nombre y ancho.">'
           + lote + imagen
           + _s12_flecha(248, 345, y, "diamante_vacio", "1", "1..*")
           + '</svg>')
    _s12_pintar(
        '<div style="margin:10px 0">'
        + _s12_titulo("Diagrama de clases del Ejercicio 1")
        + svg
        + _s12_pie(
            "Todo lo que necesitas está en el dibujo: dos clases, los "
            "atributos de cada una (arriba, en violeta), los métodos del Lote "
            "(abajo, en verde) y la relación. El diamante <b>vacío</b> dice "
            "que el Lote <b>agrupa</b> imágenes que ya existían —las crea "
            "quien llama a <code>agregar</code>—, y el <code>1..*</code> que "
            "son <b>varias</b>: o sea, una lista dentro del Lote. La Imagen no "
            "tiene métodos: solo guarda sus dos datos.")
        + "</div>")


# =============================================================================
# Portada
# =============================================================================
def portada():
    """Tarjeta de bienvenida: la primera salida que produce el propio kernel.

    OJO: los «25 puntos» de aqui son la SEGUNDA copia del total. La primera la
    suma el constructor a partir de los ejercicios, y build.py falla si no
    cuadran (se desincronizaron en las semanas 03-06 y nadie lo vio, porque
    este texto viaja comprimido dentro de la celda del motor).
    """
    _s12_pintar(
        f'<div style="font-family:{_S12_FUENTE};background:linear-gradient('
        f'135deg,#2e2377,{_S12_AZUL});color:#fff;border-radius:10px;'
        'padding:18px 22px;margin:6px 0 10px">'
        '<div style="font-size:13px;letter-spacing:.09em;'
        # «Unidad 12» y no «Unidad 4»: las portadas publicadas numeran la
        # unidad por la semana desde la 4, y un salto de «Unidad 11» a
        # «Unidad 4» lo reportaria el alumno como error. Ver el docstring del
        # generador.
        'text-transform:uppercase;opacity:.82">Semana 12 · Unidad 12</div>'
        '<div style="font-size:26px;font-weight:700;margin:2px 0 6px">'
        'Modelado de sistemas (UML)</div>'
        '<div style="font-size:14.5px;line-height:1.5;opacity:.94">'
        'Diagramas de clases, relaciones y multiplicidad: de la descripcion '
        'de un sistema al modelo en codigo.<br>'
        '<span style="opacity:.8">25 puntos · 5 XP · insignia '
        '«Quien modela»</span></div></div>')


# Alias: los cuadernillos 1 y 2 estrenaron dos nombres distintos para lo mismo
# --iniciar() y portada()-- y conviene que los dos funcionen en todas las
# semanas. Que un alumno escriba el de otro cuadernillo y le salte un NameError
# en la PRIMERA celda es la peor bienvenida posible, y ya paso una vez.
iniciar = portada
