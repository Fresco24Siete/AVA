"""Contenido propio de la SEMANA 2: «Del problema al algoritmo».

Qué es esto
-----------
`motor/ava_motor.py` trae lo que sirve en todas las semanas (barra de XP,
quices, ordenar, pistas, tarjetas). `motor/pseudo_uis.py` trae el mini-intérprete
de pseudocódigo: ejecutar, traducir a Python, dibujar el diagrama, trazar paso a
paso y el puente a Flowgorithm. **Este módulo no repite nada de eso.** Aquí vive
solo lo que es de esta semana y de ninguna otra:

- la ilustración de las cajas de memoria (la única que no es un diagrama de
  flujo: las demás las dibuja `ps.diagrama`);
- las tarjetas de referencia (la chuleta del pseudocódigo, la tabla de símbolos,
  el corte Parte A / Parte B);
- el quiz de calentamiento, el de predicción y el ensayo E-P-S con sus textos;
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
80 MB de RAM por kernel y la VM del curso tiene 2 GB para todos a la vez.
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
# Corte Parte A / Parte B
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


# =============================================================================
# Quices y ensayos
# =============================================================================
# Los textos viven aquí y no en la celda del notebook porque la respuesta
# correcta viaja como argumento: en una celda visible bastaría con leer el
# código para saber qué marcar. La celda queda en una sola línea y el motor
# esconde su código con CSS.

def quiz_tipos():
    """Calentamiento 2 — los cuatro tipos básicos (repaso de la Semana 1).

    Sustituye al de niveles de lenguaje, que preguntaba por máquina y
    ensamblador: contenido retirado de la Semana 1. Y de paso arregla un fallo
    de presentación --usaba `&rarr;` en las opciones, y las opciones van a un
    RadioButtons de ipywidgets, que las pinta como TEXTO PLANO: el estudiante
    leía literalmente "&rarr;". Las entidades HTML solo valen dentro de las
    cajas, nunca en las opciones de un quiz.
    """
    _s2_motor().quiz(
        "C2", 8,
        'Escribes `codigo = "2260123"`. ¿De qué tipo es `codigo`?',
        ["Entero (int)", "Decimal (float)", "Texto (str)", "Booleano (bool)"],
        "Texto (str)",
        "Las comillas deciden el tipo. Con comillas es texto, aunque por dentro "
        "parezca un número: por eso `\"25\" + 1` no suma, se estrella.",
        pistas=["Fíjate solo en las comillas. Son lo único que hay que mirar "
                "para saber si Python lo guardó como número o como texto."],
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
    "Reconociste los cinco símbolos del diagrama de flujo y las reglas de uno "
    "bien armado.",
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


# Los cuadernillos 1 y 2 estrenaron dos nombres para la misma tarjeta.
# El alias hace que los dos funcionen en todas las semanas: que un alumno
# escriba el de otro cuadernillo y le salte un NameError en la PRIMERA celda
# es la peor bienvenida posible, y ya paso una vez.
iniciar = portada
