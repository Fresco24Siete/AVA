"""Contenido propio de la SEMANA 2: «Del problema al algoritmo».

Qué es esto
-----------
`motor/ava_motor.py` trae lo que sirve en todas las semanas (barra de XP,
quices, ordenar, pistas, tarjetas). `motor/pseudo_uis.py` trae el mini-intérprete
de pseudocódigo: ejecutar, traducir a Python, dibujar el diagrama, trazar paso a
paso y el puente a Flowgorithm. **Este módulo no repite nada de eso.** Aquí vive
solo lo que es de esta semana y de ninguna otra:

- las ilustraciones que no son diagramas de flujo (E-P-S, las cajas de memoria,
  las tres viñetas de `x <- x + 1`, la línea de tiempo de la madrugada);
- las tarjetas de referencia (la chuleta del pseudocódigo, la tabla de símbolos,
  la de cobertura del temario, el corte Parte A / Parte B);
- los quices y los ensayos con sus textos;
- `corregir()`, que califica E1 y E2 contra **huellas SHA-256**.

Por qué las huellas: las celdas de prueba de E1 y E2 son visibles y quedan en el
notebook del alumno. Un `assert orden_e1 == ["C", "G", ...]` regala la respuesta
a quien abra la celda de abajo antes de pensar. Con la huella, la prueba dice
**cuántas** posiciones están mal y **por dónde** mirar, sin decir cuál era la
respuesta. Los demás ejercicios no la necesitan: se corrigen **ejecutando** el
pseudocódigo o la función del estudiante, así que no hay nada que copiar.

Cómo se incrusta
----------------
El constructor lee este archivo y lo ejecuta en la celda de arranque, en el
mismo espacio de nombres y **después** del motor y de `pseudo_uis`
(ver `constructor._incrustar`). De ahí salen dos reglas de escritura:

- el objeto `ava` todavía no existe cuando este archivo se ejecuta: se busca en
  tiempo de llamada con `_s2_motor()`, nunca en tiempo de definición;
- los nombres propios van con prefijo `_s2_` / `_S2_` para no pisar los del
  motor ni los de `pseudo_uis`, que comparten espacio de nombres con este
  módulo y usan sus constantes al pintar (`GRIS`, `BORDE`, `_escapar`,
  `_figura`, `_mostrar`…). Redefinir cualquiera de ellos cambiaría en silencio
  el aspecto —o el comportamiento— del intérprete.

Dependencias: biblioteca estándar + `ipywidgets`. **Sin matplotlib**: son unos
80 MB de RAM por kernel y la VM del curso tiene 2 GB para todos a la vez, así
que la gráfica del gancho es un SVG escrito a mano, igual que en la semana 1.
Sin `ipywidgets` el módulo no se cae: degrada a una versión de solo lectura.
"""

import hashlib
import types
import unicodedata

try:  # Igual que el motor: sin widgets se degrada, no se rompe.
    import ipywidgets as _W2
    _S2_HAY_WIDGETS = True
except ImportError:  # pragma: no cover - depende del entorno
    _W2 = None
    _S2_HAY_WIDGETS = False

from IPython.display import HTML as _HTML2, display as _display2


# =============================================================================
# Fachada `ps`
# =============================================================================
# `pseudo_uis.py` no se importa: se ejecuta dentro del notebook, así que sus
# funciones quedan sueltas en el espacio global y `import pseudo_uis` no
# existiría. El cuadernillo, en cambio, las llama siempre como `ps.algo(...)`:
# es lo que el estudiante lee en los mensajes de error del propio motor y en el
# documento del curso, y deja claro de dónde viene cada herramienta. Esta
# fachada reconstruye ese `ps` a partir de lo que haya en el espacio de nombres.
_S2_API_PSEUDO = (
    "ejecutar_pseudo", "traducir_a_python", "diagrama", "tabla_dos_columnas",
    "laboratorio", "trazador", "comparador",
    "guion_flowgorithm", "exportar_flowgorithm",
    "usar_entradas", "restaurar_input", "entradas",
    "Resultado", "Paso", "Error",
)


def _s2_fachada(espacio):
    """Empaqueta la API pública de `pseudo_uis` en un objeto llamado `ps`."""
    return types.SimpleNamespace(
        **{n: espacio[n] for n in _S2_API_PSEUDO if n in espacio}
    )


ps = _s2_fachada(globals())


# =============================================================================
# Identidad visual de la semana 2
# =============================================================================
# Los mismos colores del motor y de los diagramas mermaid, pero con nombres
# propios: `pseudo_uis` define AZUL, VERDE, GRIS… y los usa al dibujar.
_S2_VERDE, _S2_VERDE_OSC = "#008300", "#005400"
_S2_AZUL, _S2_AZUL_OSC = "#2a78d6", "#104281"
_S2_VIOLETA, _S2_VIOLETA_OSC = "#4a3aa7", "#2a1f6b"
_S2_AMBAR, _S2_AMBAR_OSC, _S2_AMBAR_TEXTO = "#eda100", "#8a6d00", "#3a2a00"
_S2_ROJO = "#d03b3b"
_S2_GRIS, _S2_BORDE, _S2_PAPEL = "#52514e", "#dcdcd8", "#f4f4f2"
_S2_TINTA = "#0b0b0b"
_S2_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
_S2_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _s2_pintar(texto):
    _display2(_HTML2(texto))


def _s2_motor():
    """Devuelve el objeto `ava` del cuadernillo, o None si todavía no existe.

    Se resuelve en tiempo de llamada y no al ejecutar el módulo porque el
    constructor crea `ava` después de incrustar este archivo.
    """
    return globals().get("ava")


def _s2_ocultar():
    """Marca la celda actual como andamiaje: su código deja de mostrarse.

    Lo hace el motor con una regla de CSS (`.ava-oculta`). Se usa en las celdas
    que solo pintan una ilustración o que llevan la respuesta de un quiz como
    argumento: mostrarlas sería regalar el ejercicio o llenar la pantalla de
    coordenadas de SVG.
    """
    motor = _s2_motor()
    if motor is not None:
        motor._ocultar_codigo()


def _s2_esc(texto):
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _s2_sumar_xp(clave, xp):
    motor = _s2_motor()
    return 0 if motor is None else motor._sumar(clave, xp)


def _s2_caja(titulo, cuerpo, tipo=""):
    motor = _s2_motor()
    if motor is None:  # pragma: no cover - solo si se usa fuera del cuadernillo
        _s2_pintar(f"<b>{titulo}</b><br>{cuerpo}")
        return
    motor.caja(titulo, cuerpo, tipo)


# =============================================================================
# Portada
# =============================================================================

def portada():
    """Tarjeta de bienvenida: la primera salida que produce el propio kernel."""
    _s2_ocultar()
    _s2_pintar(
        f'<div style="font-family:{_S2_FUENTE};background:linear-gradient(135deg,'
        f'{_S2_VIOLETA_OSC},{_S2_AZUL});color:#fff;border-radius:10px;'
        'padding:18px 22px;margin:6px 0 10px">'
        '<div style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;'
        'opacity:.82">Semana 2 · Unidad 2</div>'
        '<div style="font-size:26px;font-weight:700;margin:2px 0 6px">'
        'Del problema al algoritmo</div>'
        '<div style="font-size:14.5px;line-height:1.5;opacity:.94">'
        'Pseudocódigo para pensar, diagrama para ver, Python para ejecutar.<br>'
        'Algoritmos y Programación 41333 · Ingeniería en IA · UIS</div></div>'
        f'<div style="font-family:{_S2_FUENTE};font-size:13px;color:{_S2_GRIS}">'
        'Cuadernillo activado. El mini-intérprete de pseudocódigo responde a '
        '<code>ps.</code> y el motor de práctica a <code>ava.</code>'
        '</div>'
    )


# =============================================================================
# Sección 2 · El gancho: la línea de tiempo de la madrugada
# =============================================================================
# Barras horizontales apiladas sobre un eje de tiempo real, en SVG escrito a
# mano. Es la misma figura que el diseño pedía en matplotlib: se cambia la
# herramienta, no el dibujo (ver el encabezado del módulo).

_S2_TRAMOS = [
    ("colchón", 15, _S2_AMBAR, "#3a2a00"),
    ("caminata", 8, _S2_AZUL, "#ffffff"),
    ("bus", 45, _S2_VIOLETA, "#ffffff"),
    ("portería", 10, _S2_VERDE, "#ffffff"),
]
_S2_SALIDA_MIN = 282        # 04:42
_S2_CLASE_MIN = 360         # 06:00


def _s2_hhmm(minutos):
    return f"{int(minutos) // 60:02d}:{int(minutos) % 60:02d}"


def grafica_madrugada():
    """Tu madrugada, minuto a minuto: los 78 minutos anteriores a la clase."""
    _s2_ocultar()
    ancho, alto = 760, 260
    izq, der, arriba = 40, 24, 62
    t0, t1 = 240.0, 375.0        # de las 04:00 a las 06:15

    def px(minuto):
        return izq + (minuto - t0) / (t1 - t0) * (ancho - izq - der)

    y_barra, alto_barra = 118, 46
    partes = [
        f'<svg viewBox="0 0 {ancho} {alto}" width="100%" '
        f'style="max-width:{ancho}px;font-family:{_S2_FUENTE}" role="img" '
        'aria-label="Los 78 minutos entre salir de la casa y entrar a clase, '
        'repartidos en colchón, caminata, bus y portería">',
        f'<rect x="0" y="0" width="{ancho}" height="{alto}" fill="#fcfcfb"/>',
        f'<text x="{izq}" y="30" font-size="16" font-weight="650" '
        f'fill="{_S2_VIOLETA_OSC}">Tu madrugada, minuto a minuto '
        '— 78 minutos antes de la clase</text>',
    ]
    # Rejilla: una marca cada media hora, con la hora escrita como HH:MM.
    for minuto in range(240, 376, 15):
        x = px(minuto)
        grueso = minuto % 60 == 0
        partes.append(
            f'<line x1="{x:.1f}" y1="{arriba + 14}" x2="{x:.1f}" '
            f'y2="{y_barra + alto_barra + 8}" stroke="{_S2_BORDE}" '
            f'stroke-width="{2 if grueso else 1}"/>'
        )
        if grueso:
            partes.append(
                f'<text x="{x:.1f}" y="{y_barra + alto_barra + 26}" '
                f'text-anchor="middle" font-size="12" fill="{_S2_GRIS}">'
                f'{_s2_hhmm(minuto)}</text>'
            )
    # Los cuatro tramos, apilados de izquierda a derecha desde la hora de salir.
    cursor = _S2_SALIDA_MIN
    for nombre, duracion, relleno, tinta in _S2_TRAMOS:
        x, w = px(cursor), px(cursor + duracion) - px(cursor)
        partes.append(
            f'<rect x="{x:.1f}" y="{y_barra}" width="{w:.1f}" '
            f'height="{alto_barra}" fill="{relleno}" rx="3"/>'
            f'<text x="{x + w / 2:.1f}" y="{y_barra + alto_barra / 2 + 5:.1f}" '
            f'text-anchor="middle" font-size="13" font-weight="600" '
            f'fill="{tinta}">{"" if w < 40 else nombre}</text>'
            f'<text x="{x + w / 2:.1f}" y="{y_barra - 10}" text-anchor="middle" '
            f'font-size="12" fill="{_S2_GRIS}">'
            f'{nombre + " · " if w < 40 else ""}{duracion} min</text>'
        )
        cursor += duracion
    # La línea del profesor cerrando la puerta.
    x_clase = px(_S2_CLASE_MIN)
    partes.append(
        f'<line x1="{x_clase:.1f}" y1="{arriba}" x2="{x_clase:.1f}" '
        f'y2="{y_barra + alto_barra + 8}" stroke="{_S2_ROJO}" stroke-width="2" '
        'stroke-dasharray="6 4"/>'
        f'<text x="{x_clase - 8:.1f}" y="{arriba + 10}" text-anchor="end" '
        f'font-size="12.5" font-weight="600" fill="{_S2_ROJO}">'
        '6:00 — el profesor cierra la puerta</text>'
    )
    # La anotación con flecha en el extremo izquierdo del apilado.
    x_salida = px(_S2_SALIDA_MIN)
    partes.append(
        f'<path d="M{x_salida + 4:.1f},{y_barra + alto_barra + 50} '
        f'L{x_salida + 4:.1f},{y_barra + alto_barra + 14} '
        f'l-5,9 m5,-9 l5,9" fill="none" stroke="{_S2_VIOLETA_OSC}" '
        'stroke-width="2" stroke-linecap="round"/>'
        f'<text x="{x_salida + 14:.1f}" y="{y_barra + alto_barra + 56}" '
        f'font-size="13" font-weight="600" fill="{_S2_VIOLETA_OSC}">'
        '04:42 — tienes que salir a esta hora</text>'
        f'<text x="{izq}" y="{alto - 10}" font-size="11.5" fill="{_S2_GRIS}">'
        'Cada bloque es un tramo del recorrido. Súmalos y réstaselos a la hora '
        'de la clase: eso es todo el algoritmo.</text>'
        '</svg>'
    )
    _s2_pintar(f'<div style="margin:10px 0">{"".join(partes)}</div>')
    print("Tienes que salir a las 04:42. Y eso si el bus no se demora.")


# =============================================================================
# Sección 3 · Entrada · Proceso · Salida (D2)
# =============================================================================

_S2_EPS = [
    ("ENTRADA", _S2_AZUL, "#ffffff",
     "Los datos que alguien te tiene que dar",
     "hora de clase · minutos de bus · caminata · colchón"),
    ("PROCESO", _S2_VIOLETA, "#ffffff",
     "Lo que se hace con esos datos",
     "sumar los tramos y restarlos a la hora de clase"),
    ("SALIDA", _S2_VERDE, "#ffffff",
     "Lo que el algoritmo entrega",
     "la hora a la que debes salir"),
]


def _s2_lineas_svg(texto, x, y, ancho_caja, tamano, color, salto=16, peso="400"):
    """Parte un texto en líneas que quepan y devuelve los `<text>` ya colocados.

    En SVG no hay ajuste automático de línea: si no se parte a mano, el texto se
    sale de la caja y nadie se entera hasta que el estudiante lo ve cortado.
    """
    cupo = max(8, int(ancho_caja / (tamano * 0.52)))
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if len(prueba) > cupo and actual:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    return "".join(
        f'<text x="{x:.1f}" y="{y + i * salto:.1f}" text-anchor="middle" '
        f'font-size="{tamano}" font-weight="{peso}" fill="{color}">'
        f'{_s2_esc(linea)}</text>'
        for i, linea in enumerate(lineas)
    ), len(lineas)


def figura_eps():
    """Las tres casillas de Entrada · Proceso · Salida, con el caso del gancho."""
    _s2_ocultar()
    ancho, alto = 760, 250
    w_caja, hueco = 216, 32
    x0 = (ancho - (3 * w_caja + 2 * hueco)) / 2
    partes = [
        f'<svg viewBox="0 0 {ancho} {alto}" width="100%" '
        f'style="max-width:{ancho}px;font-family:{_S2_FUENTE}" role="img" '
        'aria-label="Estructura Entrada, Proceso y Salida aplicada al problema '
        'de a qué hora salir de la casa">',
        f'<rect x="0" y="0" width="{ancho}" height="{alto}" fill="#fcfcfb"/>',
    ]
    for i, (rotulo, relleno, tinta, generico, concreto) in enumerate(_S2_EPS):
        x = x0 + i * (w_caja + hueco)
        cx = x + w_caja / 2
        partes.append(
            f'<rect x="{x:.1f}" y="34" width="{w_caja}" height="52" rx="8" '
            f'fill="{relleno}"/>'
            f'<text x="{cx:.1f}" y="66" text-anchor="middle" font-size="18" '
            f'font-weight="700" fill="{tinta}" letter-spacing="1.5">{rotulo}</text>'
        )
        cuerpo, n = _s2_lineas_svg(generico, cx, 112, w_caja - 12, 13, _S2_GRIS)
        partes.append(cuerpo)
        partes.append(
            f'<line x1="{x + 24:.1f}" y1="{112 + n * 16 + 4}" '
            f'x2="{x + w_caja - 24:.1f}" y2="{112 + n * 16 + 4}" '
            f'stroke="{_S2_BORDE}" stroke-width="1"/>'
        )
        detalle, _ = _s2_lineas_svg(
            concreto, cx, 112 + n * 16 + 26, w_caja - 6, 13.5, _S2_TINTA,
            salto=18, peso="600")
        partes.append(detalle)
        if i < 2:
            xf = x + w_caja + hueco / 2
            partes.append(
                f'<path d="M{xf - 9:.1f},60 l14,0 m-6,-6 l6,6 l-6,6" '
                f'fill="none" stroke="{_S2_GRIS}" stroke-width="2.4" '
                'stroke-linecap="round" stroke-linejoin="round"/>'
            )
    partes.append(
        f'<text x="{ancho / 2}" y="{alto - 14}" text-anchor="middle" '
        f'font-size="12.5" fill="{_S2_GRIS}">'
        'Todo algoritmo tiene esta forma. Si no sabes qué va en las tres '
        'casillas, todavía no puedes programarlo.</text></svg>'
    )
    _s2_pintar(f'<div style="margin:10px 0">{"".join(partes)}</div>')


# =============================================================================
# Sección 4.4 · Variables y memoria
# =============================================================================

_S2_CAJAS = [
    (60, "copias", "40", "Entero"),
    (275, "nombre", '"Ana"', "Cadena"),
    (490, "promedio", "3.85", "Real"),
]


def figura_cajas():
    """La memoria como tres cajas de cartón rotuladas por fuera (§9.1)."""
    _s2_ocultar()
    partes = [
        '<svg viewBox="0 0 700 260" width="100%" style="max-width:700px;'
        f'font-family:{_S2_FUENTE}" role="img" aria-label="Tres cajas de '
        'memoria rotuladas copias, nombre y promedio">',
        f'<rect x="20" y="20" width="660" height="220" rx="14" '
        f'fill="{_S2_PAPEL}" stroke="{_S2_BORDE}"/>',
        f'<text x="36" y="44" font-size="12" letter-spacing="2" '
        f'fill="#8a8987">MEMORIA DEL COMPUTADOR</text>',
    ]
    for x, nombre, valor, tipo in _S2_CAJAS:
        partes.append(
            f'<rect x="{x}" y="78" width="150" height="96" rx="8" '
            f'fill="#ffffff" stroke="{_S2_GRIS}" stroke-width="2"/>'
            f'<rect x="{x}" y="52" width="150" height="26" rx="8" '
            f'fill="{_S2_AZUL}"/>'
            f'<text x="{x + 75}" y="70" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#ffffff">' + nombre + '</text>'
            f'<text x="{x + 75}" y="136" text-anchor="middle" font-size="24" '
            f'font-family="{_S2_MONO}" fill="{_S2_TINTA}">'
            + _s2_esc(valor) + '</text>'
            f'<text x="{x + 75}" y="192" text-anchor="middle" font-size="11" '
            f'fill="#8a8987">{tipo}</text>'
        )
    partes.append(
        f'<text x="350" y="232" text-anchor="middle" font-size="13" '
        f'fill="{_S2_GRIS}">El nombre está pintado por fuera. El valor está '
        'adentro. Puedes cambiar el valor sin cambiar la caja — pero el tipo '
        'de caja decide qué le cabe.</text></svg>'
    )
    _s2_pintar(f'<div style="margin:10px 0">{"".join(partes)}</div>')


def figura_incremento():
    """Las tres viñetas de `viajes <- viajes + 1`: se lee, se calcula, se guarda."""
    _s2_ocultar()
    partes = [
        '<svg viewBox="0 0 720 180" width="100%" style="max-width:720px;'
        f'font-family:{_S2_FUENTE}" role="img" aria-label="La asignación en '
        'tres pasos: se lee el valor, se calcula afuera y se guarda de vuelta">',
        '<rect x="0" y="0" width="720" height="180" fill="#fcfcfb"/>',
    ]
    for x, titulo, nota in ((40, "1. SE LEE", "saco lo que hay: 3"),
                            (280, "2. SE CALCULA", "la cuenta se hace afuera"),
                            (520, "3. SE GUARDA", "el 3 se perdió para siempre")):
        partes.append(
            f'<text x="{x}" y="30" font-size="12" letter-spacing="1.2" '
            f'fill="#8a8987">{titulo}</text>'
            f'<text x="{x}" y="150" font-size="12" fill="{_S2_GRIS}">{nota}</text>'
        )
    # Viñeta 1: la caja con el 3 adentro, borde azul.
    partes.append(
        f'<rect x="40" y="46" width="150" height="82" rx="8" fill="#ffffff" '
        f'stroke="{_S2_AZUL}" stroke-width="3"/>'
        f'<rect x="40" y="46" width="150" height="24" rx="8" fill="{_S2_AZUL}"/>'
        '<text x="115" y="63" text-anchor="middle" font-size="13" '
        'font-weight="700" fill="#ffffff">viajes</text>'
        f'<text x="115" y="108" text-anchor="middle" font-size="26" '
        f'font-family="{_S2_MONO}" fill="{_S2_TINTA}">3</text>'
    )
    # Viñeta 2: no hay caja; la cuenta ocurre afuera.
    partes.append(
        '<rect x="280" y="46" width="150" height="82" rx="8" fill="none" '
        f'stroke="{_S2_GRIS}" stroke-width="2" stroke-dasharray="5 4"/>'
        f'<text x="355" y="96" text-anchor="middle" font-size="20" '
        f'font-family="{_S2_MONO}" fill="{_S2_TINTA}">3 + 1 = 4</text>'
    )
    # Viñeta 3: la misma caja, con el 4 adentro y el 3 tachado.
    partes.append(
        f'<rect x="520" y="46" width="150" height="82" rx="8" fill="#ffffff" '
        f'stroke="{_S2_VERDE}" stroke-width="3"/>'
        f'<rect x="520" y="46" width="150" height="24" rx="8" '
        f'fill="{_S2_VERDE}"/>'
        '<text x="595" y="63" text-anchor="middle" font-size="13" '
        'font-weight="700" fill="#ffffff">viajes</text>'
        f'<text x="595" y="108" text-anchor="middle" font-size="26" '
        f'font-family="{_S2_MONO}" fill="{_S2_TINTA}">4</text>'
        f'<text x="650" y="90" text-anchor="middle" font-size="16" '
        f'font-family="{_S2_MONO}" fill="#b0afad">3</text>'
        '<line x1="643" y1="86" x2="658" y2="84" stroke="#b0afad" '
        'stroke-width="1.8"/>'
    )
    for x in (232, 472):
        partes.append(
            f'<text x="{x}" y="98" font-size="24" fill="#8a8987">&#8594;</text>'
        )
    partes.append("</svg>")
    _s2_pintar(f'<div style="margin:10px 0">{"".join(partes)}</div>')


# =============================================================================
# Sección 4.1 · La chuleta del pseudocódigo
# =============================================================================

_S2_CHULETA = [
    ("Algoritmo NombreDelAlgoritmo", "&larr; el óvalo INICIO"),
    ("    Definir edad Como Entero",
     "crea una caja (Entero, Real, Cadena, Logico)"),
    ("    Constante IVA &lt;- 19", "un dato que NO cambia; va en MAYÚSCULAS"),
    ("    Leer edad", "pide un dato al usuario &nbsp;(paralelogramo)"),
    ("    Escribir \"Hola \", nombre",
     "muestra en pantalla &nbsp;(paralelogramo)"),
    ("    total &lt;- precio * 2",
     "GUARDA el resultado a la izquierda (rectángulo)"),
    ("    // esto es un comentario", "no se ejecuta; es para ti"),
    ("FinAlgoritmo", "&larr; el óvalo FIN"),
]


def chuleta():
    """Tarjeta de referencia: las seis palabras que alcanzan para toda la semana."""
    _s2_ocultar()
    filas = "".join(
        f'<tr><td style="font-family:{_S2_MONO};font-size:13px;'
        f'color:{_S2_TINTA};padding:3px 18px 3px 0;white-space:pre">{codigo}</td>'
        f'<td style="font-size:13px;color:{_S2_GRIS};padding:3px 0">{nota}</td>'
        '</tr>'
        for codigo, nota in _S2_CHULETA
    )
    _s2_pintar(
        f'<div style="font-family:{_S2_FUENTE};background:{_S2_PAPEL};'
        f'border:1px solid {_S2_BORDE};border-left:4px solid {_S2_VIOLETA};'
        'border-radius:6px;padding:14px 16px;margin:10px 0;overflow-x:auto">'
        '<div style="font-size:12px;letter-spacing:1.6px;color:#8a8987;'
        'margin-bottom:8px">CHULETA DEL PSEUDOCÓDIGO</div>'
        f'<table style="border-collapse:collapse">{filas}</table>'
        f'<div style="margin-top:10px;font-size:13.5px;font-weight:600;'
        f'color:{_S2_ROJO}">&lt;- guarda. = pregunta. Nunca los cambies de '
        'puesto.</div></div>'
    )


# =============================================================================
# Sección 4.3 · La tabla de los cinco símbolos
# =============================================================================

_S2_SIMBOLOS = [
    ("Óvalo / estadio", "Terminal", _S2_VERDE, "#ffffff",
     "Dónde empieza y dónde termina el algoritmo",
     "Algoritmo / FinAlgoritmo", "(el archivo)",
     "Exactamente <b>un</b> INICIO y <b>al menos un</b> FIN. El INICIO no "
     "recibe flechas; el FIN no las emite."),
    ("Paralelogramo", "Entrada / Salida", _S2_AZUL, "#ffffff",
     "Dato que entra del usuario o resultado que sale a la pantalla",
     "Leer / Escribir", "input() / print()",
     "Una entrada, una flecha adentro y una afuera."),
    ("Rectángulo", "Proceso", _S2_VIOLETA, "#ffffff",
     "Un cálculo o una asignación",
     "total &lt;- a * b", "total = a * b",
     "Un rectángulo = <b>una</b> instrucción. No se meten tres cuentas en una "
     "caja."),
    ("Rombo", "Decisión", _S2_AMBAR, _S2_AMBAR_TEXTO,
     "Una pregunta de sí/no",
     "Si … Entonces", "if …:",
     "Entra <b>una</b> flecha, salen <b>exactamente dos</b>, rotuladas "
     "<b>Sí</b> y <b>No</b>. Las dos ramas se vuelven a unir."),
    ("Flecha", "Flujo", "#8a8987", "#ffffff",
     "El orden en que se ejecuta",
     "(el orden de las líneas)", "(el orden de las líneas)",
     "Siempre tiene punta. Nunca se cruzan si se puede evitar. Nunca queda "
     "una caja sin flecha de salida (salvo el FIN)."),
    ("Círculo pequeño", "Conector", "#8a8987", "#ffffff",
     "Une dos ramas o continúa el diagrama en otra página",
     "—", "—",
     "Uso opcional; en el curso solo aparece como punto de reunión después de "
     "un rombo."),
]


def tabla_simbolos():
    """Los seis símbolos con su significado, su pseudocódigo y su regla."""
    _s2_ocultar()
    cab = "".join(
        f'<th style="border:1px solid {_S2_BORDE};padding:7px 10px;'
        f'background:{_S2_PAPEL};color:{_S2_AZUL_OSC};text-align:left;'
        f'font-weight:600">{c}</th>'
        for c in ("Símbolo", "Nombre", "Qué significa", "Pseudocódigo",
                  "Python", "Regla")
    )
    filas = []
    for forma, nombre, relleno, tinta, que, pseudo, python, regla in _S2_SIMBOLOS:
        celdas = [
            f'<span style="display:inline-block;background:{relleno};'
            f'color:{tinta};border-radius:10px;padding:2px 9px;font-size:12.5px;'
            f'font-weight:600">{forma}</span>',
            f"<b>{nombre}</b>", que,
            f'<code style="font-size:12.5px">{pseudo}</code>',
            f'<code style="font-size:12.5px">{python}</code>', regla,
        ]
        filas.append(
            "<tr>" + "".join(
                f'<td style="border:1px solid {_S2_BORDE};padding:7px 10px;'
                f'vertical-align:top">{c}</td>' for c in celdas) + "</tr>"
        )
    _s2_pintar(
        f'<div style="overflow-x:auto;font-family:{_S2_FUENTE};font-size:13.5px;'
        f'color:{_S2_TINTA};margin:10px 0">'
        f'<table style="border-collapse:collapse;min-width:760px">'
        f"<tr>{cab}</tr>{''.join(filas)}</table></div>"
    )


# =============================================================================
# Corte Parte A / Parte B y tabla de cobertura
# =============================================================================

def tarjeta_corte():
    """El descanso explícito entre la Clase 1 y la Clase 2."""
    _s2_ocultar()
    _s2_pintar(
        f'<div style="font-family:{_S2_FUENTE};background:#fdf9ef;'
        f'border:1px solid {_S2_AMBAR};border-left:6px solid {_S2_AMBAR};'
        'border-radius:8px;padding:16px 20px;margin:14px 0">'
        f'<div style="font-size:17px;font-weight:700;color:{_S2_AMBAR_OSC};'
        'margin-bottom:6px">&#9208; Fin de la Parte A</div>'
        '<div style="font-size:14.5px;line-height:1.55;color:#1c1c1c">'
        'Hasta aquí llega lo de la Clase 1: plantear, analizar y describir con '
        'E-P-S. Si todavía no has tenido la Clase 2, este es un buen punto '
        'para parar. Lo que sigue —pseudocódigo, diagramas, variables y '
        'Python— se entiende mucho mejor después de la sesión de Flowgorithm.'
        '</div></div>'
    )


_S2_COBERTURA = [
    ("Planteamiento del problema", "§3 · Concepto en corto", "E3"),
    ("Requisitos y ficha de análisis", "§3 · La ficha de análisis", "E3"),
    ("Variables, constantes y restricciones", "§3 y §4.4", "E3, E6"),
    ("Metodología comprender-analizar-diseñar-verificar", "§3 · el ciclo", "E3"),
    ("Estructura Entrada-Proceso-Salida", "§3 · E-P-S", "E3"),
    ("Definición de casos de prueba", "§3 y §4.1 (la cola de entradas)", "E4, E8"),
    ("Pseudocódigo", "§4.1 laboratorio", "E1, E4, E8"),
    ("Secuencia de instrucciones", "§4.1 · el orden importa", "E1"),
    ("Símbolos y reglas del diagrama de flujo", "§4.3", "E2"),
    ("Trazado manual (prueba de escritorio)", "§4.2 · el trazador", "E5"),
    ("Uso de Flowgorithm", "§4.3 puente + §6 reto", "reto"),
    ("Variables y memoria", "§4.4 · la caja con nombre", "E5, E6"),
    ("Tipos numéricos, cadenas y booleanos", "§4.5", "E6"),
    ("input, print y conversiones explícitas", "§4.6", "E6, E7, E8"),
    ("Errores de conversión (ValueError)", "§4.7 · Lee el error", "—"),
]


def tabla_cobertura():
    """«Lo que cubriste hoy»: el temario oficial, tema por tema."""
    _s2_ocultar()
    filas = "".join(
        f'<tr><td style="border:1px solid {_S2_BORDE};padding:6px 10px">{t}</td>'
        f'<td style="border:1px solid {_S2_BORDE};padding:6px 10px;'
        f'color:{_S2_GRIS}">{d}</td>'
        f'<td style="border:1px solid {_S2_BORDE};padding:6px 10px;'
        f'font-weight:600;color:{_S2_VIOLETA_OSC}">{e}</td></tr>'
        for t, d, e in _S2_COBERTURA
    )
    _s2_pintar(
        f'<div style="overflow-x:auto;font-family:{_S2_FUENTE};font-size:13.5px;'
        'margin:10px 0">'
        '<table style="border-collapse:collapse;min-width:640px">'
        + "".join(
            f'<th style="border:1px solid {_S2_BORDE};padding:7px 10px;'
            f'background:{_S2_PAPEL};color:{_S2_AZUL_OSC};text-align:left">'
            f'{c}</th>' for c in ("Tema de la Semana 2", "Dónde lo viste",
                                  "Se evalúa en"))
        + f"{filas}</table></div>"
        f'<div style="font-family:{_S2_FUENTE};font-size:12.5px;'
        f'color:{_S2_GRIS};text-align:center;font-style:italic;margin:6px 0 12px">'
        'Quince temas oficiales, ninguno sin dueño.</div>'
    )


# =============================================================================
# Quices y ensayos
# =============================================================================
# Los textos viven aquí y no en la celda del notebook porque la respuesta
# correcta viaja como argumento: en una celda visible bastaría con leer el
# código para saber qué marcar. La celda queda en una sola línea y el motor
# esconde su código con CSS.

def quiz_hardware():
    """Calentamiento 1 — hardware y software (repaso de la Semana 1)."""
    _s2_motor().quiz(
        "C1", 8,
        "El intérprete de Python que ejecuta este cuadernillo, ¿qué es?",
        ["Hardware", "Software", "Un dato", "Una parte del procesador"],
        "Software",
        "Es un programa: se instala, se actualiza y se ejecuta. Que no se "
        "pueda tocar no lo hace menos real.",
        pistas=["Piensa en la clasificación de la Semana 1: lo que se toca es "
                "hardware; lo que se ejecuta, software."],
    )


def quiz_niveles():
    """Calentamiento 2 — los niveles de lenguaje (repaso de la Semana 1)."""
    _s2_motor().quiz(
        "C2", 8,
        "Ordena de MÁS cercano a la máquina a MÁS cercano al humano:",
        ["lenguaje de máquina &rarr; ensamblador &rarr; Python",
         "Python &rarr; ensamblador &rarr; lenguaje de máquina",
         "ensamblador &rarr; lenguaje de máquina &rarr; Python"],
        "lenguaje de máquina &rarr; ensamblador &rarr; Python",
        "Bajar de nivel es acercarse a la máquina y alejarse de la persona.",
        pistas=["El lenguaje de máquina son unos y ceros; Python se parece al "
                "inglés. El ensamblador queda en la mitad."],
    )


def orden_errores():
    """Calentamiento 4 — los tres tipos de error, por cuándo te enteras."""
    _s2_motor().ordenar(
        "C4", 10,
        {"A": "Error de SINTAXIS — el programa ni siquiera arranca "
              "(te faltó una comilla)",
         "B": "Error de EJECUCIÓN — arranca y se cae a mitad de camino "
              "(dividiste entre cero)",
         "C": "Error de LÓGICA — corre completo, no se queja, y da un "
              "resultado equivocado"},
        ["A", "B", "C"],
        "Antes de arrancar, a mitad de camino, o nunca. El tercero es el "
        "peligroso, y hoy vas a aprender la herramienta que lo caza: la "
        "prueba de escritorio.",
        pistas=["Ordénalos por el momento en que te enteras del problema: "
                "antes de arrancar, a mitad de camino, o nunca."],
    )


def quiz_prediccion():
    """Predicción del PRIMM: cuánto imprime el algoritmo de la papelería."""
    _s2_motor().quiz(
        "P2", 10,
        "¿Cuánto va a imprimir el algoritmo con 40 copias?",
        ["$ 4.000", "$ 6.500", "$ 2.600", "$ 102.500"],
        "$ 6.500",
        "40 &times; 100 = 4.000 de copias, más 2.500 del anillado. El "
        "<code>*</code> se hace antes que el <code>+</code>, igual que en "
        "matemáticas.",
        pistas=["Sigue el orden de las líneas: primero se multiplica, después "
                "se suma el anillado."],
    )


def ensayo_e1():
    """Ensayo de E1: ordenar las siete líneas, con verificación inmediata.

    No da nota: la nota sale de la celda de nbgrader. Sirve para equivocarse
    sin costo antes de escribir la lista definitiva.
    """
    _s2_motor().ordenar(
        "EN1", 12,
        {"A": "Leer copias",
         "B": 'Escribir "Total a pagar: $", total',
         "C": "Algoritmo CostoDeFotocopias",
         "D": "total <- copias * 100 + 2500",
         "E": 'Escribir "¿Cuántas copias vas a sacar?"',
         "F": "FinAlgoritmo",
         "G": "Definir copias, total Como Entero"},
        ["C", "G", "E", "A", "D", "B", "F"],
        "Ese es el orden. Ahora escríbelo como lista de letras en la celda de "
        "E1 — y fíjate en que el corrector no lo va a leer: lo va a "
        "<b>ejecutar</b>.",
        pistas=["La primera línea de cualquier algoritmo es <code>Algoritmo</code> "
                "y la última es <code>FinAlgoritmo</code>.",
                "Antes de usar una caja hay que crearla, y antes de pedirle algo "
                "al usuario hay que decirle qué le vas a pedir.",
                "Cabecera, Definir, el mensaje, el Leer, el cálculo, mostrar el "
                "resultado, FinAlgoritmo."],
    )


def quiz_simbolos():
    """Ensayo de E2: el símbolo que más se confunde."""
    _s2_motor().quiz(
        "EN2", 10,
        "En un diagrama de flujo, la instrucción <code>Leer copias</code> se "
        "dibuja con…",
        ["un rectángulo, porque guarda un dato",
         "un paralelogramo, porque el dato entra desde afuera",
         "un rombo, porque hay que preguntarle al usuario",
         "un óvalo, porque el algoritmo empieza pidiendo datos"],
        "un paralelogramo, porque el dato entra desde afuera",
        "El paralelogramo es la puerta del algoritmo: por ahí entran los datos "
        "(<code>Leer</code>) y por ahí salen los resultados "
        "(<code>Escribir</code>).",
        pistas=["El rectángulo es para cuentas y el rombo para preguntas de "
                "sí/no. ¿Cuál queda para los datos que cruzan la frontera del "
                "programa?"],
    )


def quiz_ficha():
    """Ensayo de E3: qué es y qué no es una entrada."""
    _s2_motor().quiz(
        "EN3", 8,
        "En el problema del parqueadero, ¿cuál de estos <b>no</b> es una "
        "entrada?",
        ["las horas que estuvo el carro", "la tarifa por hora",
         "el recargo fijo de la barrera", "el total a pagar"],
        "el total a pagar",
        "El total no entra: <b>sale</b>. Una entrada es un dato que alguien "
        "te tiene que dar; un resultado que tú calculas es una salida.",
        pistas=["Pregúntate cuál de los cuatro puedes calcular tú a partir de "
                "los otros tres."],
    )


# --- Ensayo del formulario E-P-S ---------------------------------------------

_S2_ETIQUETAS_EPS = ["ENTRADA", "CONSTANTE", "PROCESO", "SALIDA"]

_S2_ITEMS_EPS = [
    ("la hora a la que empieza tu clase", "ENTRADA"),
    ("los minutos que gastas dentro del bus", "ENTRADA"),
    ("los 10 minutos de la portería al salón", "CONSTANTE"),
    ("los 15 minutos de colchón", "CONSTANTE"),
    ("sumar los tramos y restárselos a la hora de clase", "PROCESO"),
    ("la hora a la que tienes que salir de la casa", "SALIDA"),
]

_S2_PISTA_EPS = (
    "Una <b>entrada</b> cambia de una persona a otra; una <b>constante</b> es "
    "la misma para todos y la fija el problema; el <b>proceso</b> es un verbo; "
    "la <b>salida</b> es lo único que el algoritmo entrega al final."
)


def ensayo_eps():
    """Formulario de análisis: clasifica los seis datos del problema del gancho."""
    _s2_ocultar()
    motor = _s2_motor()
    motor.registrar_pistas("P1", [_S2_PISTA_EPS])
    if not _S2_HAY_WIDGETS:  # pragma: no cover - depende del entorno
        motor.caja("Clasifica cada dato",
                   "<br>".join(f"• {t}" for t, _ in _S2_ITEMS_EPS))
        return
    # La etiqueta va en un HTML aparte y no en `description`: ipywidgets recorta
    # las descripciones largas con puntos suspensivos y aquí el texto del ítem
    # ES la pregunta.
    selectores = [
        _W2.Dropdown(options=[("—", None)] + [(e, e) for e in _S2_ETIQUETAS_EPS],
                     value=None, layout=_W2.Layout(width="180px"))
        for _ in _S2_ITEMS_EPS
    ]
    filas = [
        _W2.HBox([_W2.HTML(f'<div style="font:14px {_S2_FUENTE};padding-top:4px">'
                           f'{texto}</div>',
                           layout=_W2.Layout(width="360px")), selector])
        for (texto, _), selector in zip(_S2_ITEMS_EPS, selectores)
    ]
    salida = _W2.Output()
    boton = _W2.Button(description="Verificar", button_style="primary",
                       layout=_W2.Layout(width="130px"))

    def _al_verificar(_):
        salida.clear_output()
        elegido = [s.value for s in selectores]
        with salida:
            if None in elegido:
                _s2_pintar('<div class="ava-caja">Falta clasificar alguno.</div>')
                return
            malos = [texto for (texto, ok), mio in zip(_S2_ITEMS_EPS, elegido)
                     if mio != ok]
            if not malos:
                ganado = _s2_sumar_xp("P1", 14)
                extra = f" (+{ganado} XP)" if ganado else " (ya lo tenías)"
                _s2_pintar(
                    f'<div class="ava-caja ok"><div class="ava-tit">'
                    f'Ficha completa{extra}</div>Esa es exactamente la ficha de '
                    'análisis del ejercicio E3 y la del taller presencial. '
                    'Fíjate en que la llenaste <b>sin escribir una sola línea '
                    'de código</b>.</div>')
            else:
                lista = "".join(f"<li>{t}</li>" for t in malos)
                _s2_pintar(
                    f'<div class="ava-caja mal"><div class="ava-tit">'
                    f'{len(malos)} de {len(_S2_ITEMS_EPS)} por revisar</div>'
                    f'<ul>{lista}</ul>{_S2_PISTA_EPS}</div>')

    boton.on_click(_al_verificar)
    botones = [boton]
    pista = motor._boton_pista("P1", salida)
    if pista:
        botones.append(pista)
    motor.caja("", "<b>El problema de esta mañana, casilla por casilla.</b> "
                   "¿Cada uno de estos seis qué es?")
    _display2(_W2.VBox(filas + [_W2.HBox(botones), salida]))


# =============================================================================
# Cierre
# =============================================================================

_S2_RADAR = [
    "Puedo llenar una ficha de análisis (objetivo, entradas, salidas, "
    "restricciones, casos de prueba) de un problema nuevo.  [§3]",
    "Sé escribir un algoritmo en pseudocódigo con Definir, Leer, Escribir "
    "y <-.  [§4.1]",
    "Reconozco los cinco símbolos del diagrama de flujo y sé qué significa "
    "cada uno.  [§4.3]",
    "Puedo hacer una prueba de escritorio en papel y decir cuánto vale cada "
    "variable en cada paso.  [§4.2]",
    "Entiendo por qué viajes = viajes + 1 no es una ecuación falsa.  [§4.4]",
    "Sé que input() devuelve texto y sé convertirlo con int() o float().  [§4.6]",
]

_S2_LOGROS = [
    "Ejecutaste pseudocódigo en español y lo viste dibujarse solo.",
    "Llenaste una ficha de análisis: objetivo, entradas, salidas, "
    "restricciones y casos de prueba.",
    "Hiciste una prueba de escritorio a mano y la comparaste con la real.",
    "Reconociste los cinco símbolos del diagrama de flujo y dos diagramas mal "
    "armados.",
    "Tradujiste el mismo algoritmo a Python y comprobaste que dicen lo mismo.",
    "Entendiste por qué <code>input()</code> siempre devuelve texto.",
]

_S2_PUENTE = (
    "<b>Próxima parada &rarr; Semana 3: el rombo.</b> Hoy todo fue "
    "<b>secuencia</b>: una instrucción detrás de otra. La semana entrante "
    "llegan los operadores, las expresiones booleanas y "
    "<code>Si … Entonces … Sino</code>, en pseudocódigo y en Python. Tu "
    "algoritmo va a poder tomar decisiones — y tu prueba de escritorio va a "
    "tener que seguir dos caminos. <b>Guarda tu pseudocódigo del E8: lo vas a "
    "volver a abrir.</b>"
)


def radar_salida():
    """Autoevaluación de cierre. Cada casilla lleva la sección a la que volver."""
    _s2_ocultar()
    _s2_motor().radar(
        _S2_RADAR,
        "Las seis marcadas. Eso es exactamente lo que pedía la semana: decir "
        "lo mismo en tres idiomas y comprobar que dicen lo mismo.",
    )


def cierre():
    """Tarjeta final: insignia si llegó a la meta, y puente a la Semana 3."""
    _s2_ocultar()
    _s2_motor().cerrar(_S2_LOGROS, _S2_PUENTE)


# =============================================================================
# Corrección con huellas (E1 y E2)
# =============================================================================
# Solo estos dos ejercicios la necesitan: son los únicos cuya respuesta cabría
# escrita dentro de la celda de prueba, que el alumno puede leer. Los demás se
# corrigen ejecutando el pseudocódigo o la función, así que la prueba no
# contiene ninguna respuesta que copiar.

def _s2_normalizar(valor):
    """Baja a minúsculas, quita tildes y colapsa espacios, recursivamente."""
    if isinstance(valor, str):
        texto = unicodedata.normalize("NFKD", valor.strip().lower())
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        return " ".join(texto.split())
    if isinstance(valor, dict):
        return {_s2_normalizar(k): _s2_normalizar(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_s2_normalizar(x) for x in valor]
    return valor


def _s2_huella(*partes):
    """Huella SHA-256 de una respuesta ya normalizada.

    Las partes llevan el nombre del ejercicio y la posición, así que dos
    respuestas iguales en sitios distintos no comparten huella: nadie puede
    deducir «estas dos casillas son la misma palabra» comparando el módulo.
    """
    texto = "|".join(repr(_s2_normalizar(p)) for p in partes)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# --- Huellas de las respuestas -----------------------------------------------
# Generadas con el script de autoría (nunca viaja al alumno). Aquí solo hay
# huellas: quien lea este módulo no aprende ninguna respuesta.

# E1: una huella por posición, para poder decir CUÁNTAS están en su sitio sin
# decir cuáles.
_S2_E1_POSICIONES = [
    "672b4c80f5d3b1b35ff75eae5819609234926ac8c3ba474f3ac2028a8e9967fd",
    "3e8f4e5fb247f20ea889254dc93645afcb1625d0c3e0edba2910fd86dfd3091d",
    "dcfe04b4d466b67c2c0b433f65257d40ca39217babbe104574827a8a3d6f1e26",
    "84e6d9acc81265debf78394974746149823520c1a8cc1035770614e1cb355b39",
    "dd467f8c5207a6d4d09f24c4f1018ccc46c3c3565b8d0c08df0a154d3e13adf5",
    "0de55ab9ab572c944dad78911d7c913987679a299bbda81986eb0c82ab9a6a9a",
    "8f96f7f914cee2d3a619bc09252915c51b8df5bddd0a8e20172a7bdad000828c",
]

# E2: una huella por forma, para poder decir CUÁLES están mal emparejadas y dar
# un empujón distinto en cada una, sin nombrar el significado correcto.
_S2_E2_LLAVES = {
    "ovalo":
        "ab382e13db01c6a57bd11390e6f768c048cc272950794563c6011a70c63608b6",
    "paralelogramo":
        "9ee8397087cabed3671b0c44fdfdbe0925bf850996e560634c45ffd76c7708af",
    "rectangulo":
        "ee845bf8dd746af460a79ef53533e3d92ea952e0832342ebebc8690825b24ef3",
    "rombo":
        "45f12c15640aa43f7da5e0541abce75e91cc3296b9c66aa8cf24ef1721f8cb80",
    "flecha":
        "30550ec3c90ccdf2abe5e57d6d630f278d9e0f87fe347272091a5ff6ad88f76d",
}

_S2_E1_MENSAJES = (
    "Todo algoritmo empieza por su cabecera y termina por FinAlgoritmo: esas "
    "dos son gratis.",
    "Antes de usar una caja hay que crearla, y antes de pedirle un dato al "
    "usuario hay que decirle qué le vas a pedir.",
    "Y el resultado no se puede mostrar antes de calcularlo.",
)

_S2_E2_MENSAJES = {
    "ovalo": "El óvalo es la forma redondeada: piensa en dónde arranca y dónde "
             "acaba el algoritmo.",
    "paralelogramo": "El paralelogramo es el rectángulo torcido: por ahí cruza "
                     "algo entre el usuario y el programa.",
    "rectangulo": "El rectángulo recto no pregunta ni muestra nada: guarda una "
                  "cuenta.",
    "rombo": "Del rombo salen dos flechas rotuladas. ¿Qué instrucción necesita "
             "dos caminos?",
    "flecha": "La flecha no calcula nada: solo dice qué va después de qué.",
}


def _s2_corregir_1(respuesta):
    bien = sum(1 for i, letra in enumerate(respuesta)
               if i < len(_S2_E1_POSICIONES)
               and _s2_huella("ejercicio_1", i, letra) == _S2_E1_POSICIONES[i])
    if bien == len(_S2_E1_POSICIONES):
        return
    faltan = len(_S2_E1_POSICIONES) - bien
    mensaje = _S2_E1_MENSAJES[min(bien // 3, len(_S2_E1_MENSAJES) - 1)]
    raise AssertionError(
        f"Tienes {bien} de {len(_S2_E1_POSICIONES)} líneas en su sitio y te "
        f"faltan {faltan}. {mensaje}"
    )


def _s2_corregir_2(respuesta):
    malas = [_S2_E2_MENSAJES[clave] for clave, huella in _S2_E2_LLAVES.items()
             if _s2_huella("ejercicio_2", clave,
                           respuesta.get(clave)) != huella]
    if malas:
        cuantas = ("Hay una forma mal emparejada." if len(malas) == 1
                   else f"Hay {len(malas)} formas mal emparejadas.")
        raise AssertionError(cuantas + " " + " ".join(malas))


_S2_CORRECTORES = {
    "ejercicio_1": _s2_corregir_1,
    "ejercicio_2": _s2_corregir_2,
}


def corregir(clave, respuesta):
    """Compara contra la clave hasheada y lanza AssertionError si algo falla.

    El mensaje dice **cuántas** están mal y **por dónde** mirar, y nunca cuál
    era la respuesta: la celda de prueba es visible y el mensaje también.
    """
    if clave not in _S2_CORRECTORES:
        raise AssertionError(f"No hay clave registrada para '{clave}'.")
    _S2_CORRECTORES[clave](respuesta)
