"""Contenido propio de la SEMANA 1: «Hola, máquina».

Qué es esto
-----------
`motor/ava_motor.py` trae lo que sirve en todas las semanas (barra de XP,
quices, pistas, tarjetas). Este módulo trae lo que solo sirve en la semana 1:
la MiniMáquina, la línea de tiempo, el diagnóstico de entrada, el mapa
conceptual y los correctores de los siete ejercicios.

Se incrusta en la celda de arranque del cuadernillo, **después** del motor y en
el mismo espacio de nombres (ver `constructor._incrustar`). Por eso:

- el objeto `ava` todavía no existe cuando este archivo se ejecuta: se busca en
  tiempo de llamada con `_motor()`, nunca en tiempo de definición;
- los nombres internos van con guion bajo para no pisar los del motor (`AZUL`,
  `VERDE`, `_html`… los usa `ava` al pintar sus tarjetas y cambiarlos de valor
  cambiaría su aspecto).

Dependencias: biblioteca estándar + `ipywidgets`. **Sin matplotlib**: importarlo
cuesta unos 80 MB de RAM por kernel y la VM del curso tiene 2 GB, así que la
gráfica de transistores y el dibujo del mapa conceptual se generan como SVG
escrito a mano desde Python. Sin `ipywidgets` el módulo no se cae: degrada a una
versión de solo lectura, igual que hace el motor.
"""

import datetime
import dis
import hashlib
import inspect
import io
import os
import platform
import sys
import unicodedata

try:  # Igual que el motor: sin widgets se degrada, no se rompe.
    import ipywidgets as W
    HAY_WIDGETS = True
except ImportError:  # pragma: no cover - depende del entorno
    W = None
    HAY_WIDGETS = False

from IPython.display import HTML, display

# --- Identidad visual de la semana 1 ----------------------------------------
# Nombres con guion bajo a propósito: el motor tiene constantes AZUL/VERDE/GRIS
# que usa al pintar, y redefinirlas desde aquí le cambiaría el aspecto.
_VIOLETA_OSC = "#2e2377"
_VIOLETA = "#4a3aa7"
_AZUL = "#2a78d6"
_VERDE = "#0ca30c"
_ROJO = "#d03b3b"
_AMBAR = "#eda100"
_GRIS = "#52514e"
_BORDE = "#dfe3e8"
_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"


def _pintar(texto):
    display(HTML(texto))


def _motor():
    """Devuelve el objeto `ava` del cuadernillo, o None si todavía no existe.

    Se resuelve en tiempo de llamada y no al importar porque este módulo se
    ejecuta antes de que el constructor cree `ava`.
    """
    return globals().get("ava")


def _sumar_xp(clave, xp):
    """Suma XP al motor sin pintar su tarjeta genérica de «Correcto».

    `ava.comprobar()` sumaría el XP igual, pero dibujando un recuadro de
    verificación que aquí no viene a cuento (el diagnóstico no se aprueba ni se
    falla). Se usa el contador del motor para que la barra sea una sola.
    """
    motor = _motor()
    if motor is None:
        return 0
    return motor._sumar(clave, xp)


def _escapar(texto):
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# =============================================================================
# Arranque
# =============================================================================

def iniciar():
    """Tarjeta de bienvenida y confirmación de que el kernel responde.

    Es la primera salida que el estudiante ve producida por su propio kernel:
    sirve de comprobación de que todo funciona antes de pedirle nada.
    """
    _pintar(
        f'<div style="font-family:{_FUENTE};background:linear-gradient(135deg,'
        f'{_VIOLETA_OSC},{_AZUL});color:#fff;border-radius:10px;padding:18px 22px;'
        'margin:6px 0 10px">'
        '<div style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;'
        'opacity:.82">Semana 1 · Unidad 1</div>'
        '<div style="font-size:26px;font-weight:700;margin:2px 0 6px">Hola, máquina</div>'
        '<div style="font-size:14.5px;line-height:1.5;opacity:.94">'
        'De los engranajes a tu primer programa.<br>'
        'Algoritmos y Programación 41333 · Ingeniería en IA · UIS</div></div>'
        f'<div style="font-family:{_FUENTE};font-size:13px;color:{_GRIS}">'
        f'Cuadernillo activado. Kernel: Python {platform.python_version()}</div>'
    )


# =============================================================================
# 3A · Línea de tiempo (D1) y gráfica de transistores (V1)
# =============================================================================

_HITOS = [
    ("~820", "Al-Juarismi",
     "Matemático persa. De su nombre viene la palabra <b>algoritmo</b> y de su "
     "libro, <b>álgebra</b>. Los algoritmos son mil años más viejos que los "
     "computadores."),
    ("1843", "Ada Lovelace",
     "Escribe el <b>primer algoritmo pensado para una máquina</b> (la Máquina "
     "Analítica, que nunca se construyó). Primera programadora de la historia."),
    ("1936", "Alan Turing",
     "Define qué significa <b>computar</b>: una máquina universal que sigue "
     "instrucciones. Toda la informática —incluido este cuadernillo— cabe en esa "
     "idea."),
    ("1945", "ENIAC y sus seis programadoras",
     "Primer gran computador electrónico: 17.000 tubos, 27 toneladas. Se "
     "«programaba» <b>moviendo cables</b>: el software todavía era hardware."),
    ("1957", "FORTRAN",
     "Nace el primer lenguaje de <b>alto nivel</b> de uso masivo. Por primera vez "
     "alguien le escribe a la máquina en algo parecido a matemáticas, y otro "
     "programa lo traduce."),
    ("1969", "Margaret Hamilton",
     "Dirige el software del Apolo 11. Su código sabía <b>recuperarse de "
     "errores</b>; por eso alunizaron. (Los errores importan: guarda esa frase "
     "para la sección 4.)"),
    ("1991", "Guido van Rossum publica Python",
     "El lenguaje que vas a aprender, diseñado para que el código se lea casi "
     "como texto. Ese mismo año nace la World Wide Web."),
    ("HOY", "Tú",
     "Ejecutaste tu primer programa hace diez minutos. La historia sigue y ahora "
     "te incluye."),
]


def linea_de_tiempo():
    """Los ocho hitos de 3A, en HTML.

    En HTML y no como diagrama porque es texto largo: un SVG con estos párrafos
    quedaría ilegible en un teléfono y no se podría seleccionar ni copiar.
    """
    filas = []
    for anio, quien, texto in _HITOS:
        destacado = anio == "HOY"
        color = _VIOLETA_OSC if not destacado else _VERDE
        filas.append(
            f'<div style="display:flex;gap:14px;padding:9px 0;border-bottom:1px solid {_BORDE}">'
            f'<div style="flex:0 0 74px;text-align:right;font-weight:700;color:{color};'
            f'font-size:15px">{anio}</div>'
            f'<div style="flex:0 0 3px;background:{color};border-radius:2px"></div>'
            f'<div style="flex:1"><div style="font-weight:650;color:{_VIOLETA_OSC}">{quien}</div>'
            f'<div style="color:#1c1c1c">{texto}</div></div></div>'
        )
    _pintar(
        f'<div style="font-family:{_FUENTE};font-size:14.5px;line-height:1.5;'
        f'border:1px solid {_BORDE};border-left:4px solid {_VIOLETA};border-radius:6px;'
        f'padding:6px 16px 10px;margin:8px 0">'
        f'<div style="font-weight:650;color:{_VIOLETA_OSC};margin:8px 0 2px;font-size:16px">'
        'Mil años en cinco minutos</div>'
        + "".join(filas)
        + f'<div style="font-size:12.5px;color:{_GRIS};margin-top:10px;font-style:italic">'
        'Llévate una fecha propia a la clase: la línea de tiempo colaborativa se '
        'arma entre todos.</div></div>'
    )


# Transistores por chip. Cifras redondeadas de los fabricantes; sirven para ver
# la forma de la curva, no para citarlas en un examen.
_TRANSISTORES = [
    (1971, 2_300, "Intel 4004"),
    (1974, 6_000, "Intel 8080"),
    (1978, 29_000, "Intel 8086"),
    (1982, 134_000, "Intel 80286"),
    (1985, 275_000, "Intel 80386"),
    (1989, 1_180_000, "Intel 80486"),
    (1993, 3_100_000, "Pentium"),
    (1999, 9_500_000, "Pentium III"),
    (2003, 125_000_000, "Pentium 4"),
    (2008, 731_000_000, "Core i7"),
    (2012, 1_400_000_000, "Core i7 Ivy Bridge"),
    (2017, 4_800_000_000, "AMD Ryzen"),
    (2020, 16_000_000_000, "Apple M1"),
    (2023, 134_000_000_000, "Apple M2 Ultra"),
]

_ETIQUETAS_Y = {
    3: "1.000", 4: "10 mil", 5: "100 mil", 6: "1 millón", 7: "10 mill.",
    8: "100 mill.", 9: "1.000 mill.", 10: "10.000 mill.", 11: "100.000 mill.",
}


def _log10(valor):
    """log10 sin importar `math` a lo grande; suficiente para posicionar puntos."""
    exponente = 0
    while valor >= 10:
        valor /= 10.0
        exponente += 1
    # Aproximación de log10 de la mantisa (1..10) por interpolación de la serie.
    # Precisión de sobra para colocar un punto en una gráfica de 400 píxeles.
    x = (valor - 1) / (valor + 1)
    x2 = x * x
    serie = x * (2 + x2 * (2 / 3.0 + x2 * (2 / 5.0 + x2 * 2 / 7.0)))
    return exponente + serie / 2.302585092994046


def grafica_transistores():
    """Gráfica V1: transistores por chip, 1971-2023, en escala logarítmica.

    SVG escrito a mano en vez de matplotlib. No es purismo: matplotlib son ~80 MB
    de RAM por kernel y la VM del curso tiene 2 GB para todos los estudiantes a
    la vez. Una gráfica de una sola serie no justifica ese coste.
    """
    ancho, alto = 720, 400
    izq, der, arriba, abajo = 96, 26, 44, 46
    x0, x1 = 1968.0, 2026.0
    y0, y1 = 3.0, 11.6

    def px(anio):
        return izq + (anio - x0) / (x1 - x0) * (ancho - izq - der)

    def py(valor):
        return alto - abajo - (_log10(valor) - y0) / (y1 - y0) * (alto - arriba - abajo)

    partes = [
        f'<svg viewBox="0 0 {ancho} {alto}" width="100%" style="max-width:{ancho}px;'
        f'font-family:{_FUENTE}" role="img" '
        'aria-label="Transistores por chip entre 1971 y 2023, escala logarítmica">'
    ]
    # Rejilla horizontal: una línea por década, que es lo que hace legible el log.
    for exp in range(3, 12):
        y = py(10 ** exp)
        partes.append(
            f'<line x1="{izq}" y1="{y:.1f}" x2="{ancho - der}" y2="{y:.1f}" '
            f'stroke="{_BORDE}" stroke-width="1"/>'
            f'<text x="{izq - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="11" '
            f'fill="{_GRIS}">{_ETIQUETAS_Y[exp]}</text>'
        )
    for anio in (1971, 1980, 1990, 2000, 2010, 2023):
        x = px(anio)
        partes.append(
            f'<line x1="{x:.1f}" y1="{arriba}" x2="{x:.1f}" y2="{alto - abajo}" '
            f'stroke="{_BORDE}" stroke-width="1" stroke-dasharray="2 4"/>'
            f'<text x="{x:.1f}" y="{alto - abajo + 18}" text-anchor="middle" '
            f'font-size="11" fill="{_GRIS}">{anio}</text>'
        )
    puntos = " ".join(f"{px(a):.1f},{py(v):.1f}" for a, v, _ in _TRANSISTORES)
    partes.append(
        f'<polyline points="{puntos}" fill="none" stroke="{_AZUL}" stroke-width="2.4" '
        'stroke-linejoin="round"/>'
    )
    for anio, valor, nombre in _TRANSISTORES:
        partes.append(
            f'<circle cx="{px(anio):.1f}" cy="{py(valor):.1f}" r="4" fill="{_VIOLETA}"/>'
        )
    # Solo tres etiquetas: los extremos y un punto medio reconocible. Más nombres
    # convierten la gráfica en una sopa de letras y tapan la única idea que tiene
    # que transmitir, que es la pendiente.
    for anio, valor, nombre, dx, dy, anclaje in (
        (1971, 2_300, "Intel 4004 · 2.300", 10, 4, "start"),
        (1993, 3_100_000, "Pentium · 3,1 millones", 8, -10, "start"),
        (2023, 134_000_000_000, "Apple M2 Ultra · 134.000 millones", -8, -12, "end"),
    ):
        partes.append(
            f'<text x="{px(anio) + dx:.1f}" y="{py(valor) + dy:.1f}" '
            f'text-anchor="{anclaje}" font-size="12" font-weight="600" '
            f'fill="{_VIOLETA_OSC}">{nombre}</text>'
        )
    partes.append(
        f'<text x="{izq}" y="24" font-size="15" font-weight="650" fill="{_VIOLETA_OSC}">'
        'Transistores dentro de un solo chip</text>'
        f'<text x="{izq}" y="{alto - 6}" font-size="11.5" fill="{_GRIS}">'
        'Escala logarítmica: cada línea horizontal multiplica por 10. En línea '
        'recta, el crecimiento es exponencial.</text>'
        '</svg>'
    )
    _pintar(
        f'<div style="margin:10px 0">{"".join(partes)}</div>'
        f'<div style="font-family:{_FUENTE};font-size:12.5px;color:{_GRIS};'
        'text-align:center;font-style:italic;margin-bottom:10px">'
        'De 2.300 transistores a 134.000 millones en 52 años: 58 millones de veces '
        'más, en un pedazo de silicio más pequeño.</div>'
    )


# =============================================================================
# 3B · Los tres pisos y la MiniMáquina
# =============================================================================

def tres_pisos(func):
    """Muestra la MISMA función en los tres niveles de lenguaje, lado a lado.

    Lo que hace memorable la sección 3B no es la explicación: es ver que las tres
    columnas son la misma cosa. Por eso se generan desde la función real que el
    estudiante acaba de escribir y no desde un texto de ejemplo.
    """
    try:
        fuente = inspect.getsource(func).strip()
    except (OSError, TypeError):  # definida en una celda ya perdida
        fuente = "(no pude recuperar el código fuente de esta función)"
    buzon = io.StringIO()
    try:
        dis.dis(func, file=buzon)
        listado = buzon.getvalue().strip()
    except Exception as err:  # pragma: no cover - depende de la versión de Python
        listado = f"(dis no pudo desensamblar: {err})"
    crudo = getattr(func, "__code__", None)
    binario = (" ".join(format(b, "08b") for b in crudo.co_code)
               if crudo is not None else "(sin bytecode)")

    def panel(titulo, cuerpo, color):
        return (
            f'<div style="flex:1 1 30%;min-width:210px;border:1px solid {_BORDE};'
            f'border-top:3px solid {color};border-radius:6px;padding:8px 10px;'
            'background:#fbfcfd">'
            f'<div style="font-weight:650;color:{color};font-size:13px;'
            f'margin-bottom:4px">{titulo}</div>'
            '<pre style="margin:0;font-size:11.5px;line-height:1.35;white-space:pre-wrap;'
            f'word-break:break-all;color:#1c1c1c">{_escapar(cuerpo)}</pre></div>'
        )

    _pintar(
        f'<div style="font-family:{_FUENTE};margin:10px 0">'
        '<div style="display:flex;gap:10px;flex-wrap:wrap">'
        + panel("Piso 3 · lo que escribiste", fuente, _VERDE)
        + panel("Piso 2 · lo que entiende la máquina virtual", listado, _AZUL)
        + panel("Piso 1 · lo que de verdad viaja", binario, _VIOLETA)
        + '</div>'
        f'<div style="font-size:12.5px;color:{_GRIS};margin-top:6px;text-align:center">'
        'Piso 3 &rarr; Piso 2 lo traduce el <b>intérprete</b>. '
        'Piso 2 &rarr; Piso 1 lo ejecuta la <b>CPU</b>. '
        'Es la misma función tres veces.</div></div>'
    )


_NOMBRES_INSTRUCCION = {1: "CARGAR", 2: "SUMAR", 3: "MOSTRAR", 0: "PARAR"}


class MiniMaquina:
    """Un computador de mentiras con una sola gaveta y cuatro instrucciones.

    Su lenguaje de máquina son números: cada instrucción son dos, el código y su
    argumento. Existe para que el estudiante pueda *programar* en lenguaje de
    máquina en la semana 1, no solo mirar bytes ajenos.

    Atributos públicos tras `ejecutar()`:
      `salidas`             lista de lo que mostró (lo que comprueba el test)
      `termino_con_parar`   True si el programa acabó en PARAR y no por agotarse
      `acumulador`          el contenido final de la gaveta
    """

    LIMITE_PASOS = 500   # una lista corta no puede necesitar más; corta bucles raros

    def __init__(self, programa):
        self.programa = list(programa)
        self.acumulador = 0
        self.salidas = []
        self.termino_con_parar = False
        self.pasos = 0

    def ejecutar(self, traza=False):
        """Ejecuta el programa y devuelve la lista de lo que mostró."""
        self.acumulador = 0
        self.salidas = []
        self.termino_con_parar = False
        self.pasos = 0
        filas = []
        i = 0
        while i + 1 < len(self.programa) and self.pasos < self.LIMITE_PASOS:
            codigo, argumento = self.programa[i], self.programa[i + 1]
            self.pasos += 1
            mostrado = ""
            if codigo == 1:
                self.acumulador = argumento
            elif codigo == 2:
                self.acumulador = self.acumulador + argumento
            elif codigo == 3:
                self.salidas.append(self.acumulador)
                mostrado = f"   -> {self.acumulador}"
            elif codigo == 0:
                self.termino_con_parar = True
            else:
                raise ValueError(
                    f"La MiniMáquina no conoce la instrucción {codigo}. "
                    f"Solo entiende 1 (CARGAR), 2 (SUMAR), 3 (MOSTRAR) y 0 (PARAR)."
                )
            nombre = _NOMBRES_INSTRUCCION[codigo]
            arg = "-" if codigo in (0, 3) else str(argumento)
            # Anchos calzados con el encabezado de abajo: la traza solo enseña
            # algo si las columnas están una debajo de otra.
            filas.append(f"{self.pasos:>4}  {nombre:<11}{arg:>12}{self.acumulador:>13}{mostrado}")
            if codigo == 0:
                break
            i += 2
        if traza:
            print("paso  instrucción   argumento   acumulador")
            for fila in filas:
                print(fila)
            if self.termino_con_parar:
                print(f"Programa terminado. Mostró: {self.salidas}")
            else:
                print("La máquina se quedó sin instrucciones y nunca vio un PARAR (0, 0).")
        return self.salidas


# =============================================================================
# Sección 4 · Laboratorio de los tres errores
# =============================================================================
#
# `registrar` no es una casilla de honor: comprueba de verdad que el estudiante
# arregló la celda. Cada una de las tres deja una huella distinta en el espacio
# de nombres, y esa huella es imposible de dejar si la celda sigue rota.

def _revisar_sintaxis(entorno):
    # Si hay SyntaxError, Python no ejecuta NI UNA línea de la celda: `nota` no
    # llega a existir. Que exista es la prueba de que la celda ya compila.
    if "nota" not in entorno:
        return (False, "Todavía no. La celda del <code>if</code> sigue sin compilar: "
                       "cuando hay un error de sintaxis no se ejecuta ni la primera "
                       "línea, así que <code>nota</code> ni siquiera existe. "
                       "Ponle los dos puntos y vuelve a ejecutarla.")
    return (True, "Arreglaste el error de sintaxis. Fíjate en lo que cambió: ahora "
                  "sí se imprimió la primera línea, que siempre estuvo bien.")


def _revisar_ejecucion(entorno):
    valor = entorno.get("nota_texto", None)
    if isinstance(valor, str):
        return (False, "Todavía no. <code>nota_texto</code> sigue siendo un texto "
                       "(tiene comillas), y por eso no se le puede sumar 1. "
                       "Quítale las comillas y ejecuta otra vez la celda.")
    if not isinstance(valor, (int, float)):
        return (False, "Todavía no. Ejecuta primero la celda de los cuatro pasos y "
                       "luego arréglala: <code>nota_texto</code> tiene que ser un "
                       "número, no un texto.")
    return (True, "Arreglaste el error de ejecución. Salieron los cuatro pasos: el "
                  "programa ya no se estrella a mitad de camino.")


def _revisar_logica(entorno):
    valor = entorno.get("promedio", None)
    if valor is None:
        return (False, "Todavía no. Ejecuta primero la celda del promedio.")
    try:
        if abs(float(valor) - 4.0) < 1e-9:
            return (True, "Cazaste el error de lógica. Y fíjate en cómo lo cazaste: "
                          "no te avisó Python, te avisó un caso cuyo resultado "
                          "conocías de antemano.")
    except (TypeError, ValueError):
        pass
    return (False, "Todavía no. Con tres notas de 4.0 el promedio tiene que dar 4.0 "
                   "y ahora mismo <code>promedio</code> vale otra cosa. Agrupa la "
                   "suma con paréntesis y vuelve a ejecutar las dos celdas.")


_LOGROS_ERRORES = {
    "errores_sintaxis": (8, _revisar_sintaxis),
    "errores_ejecucion": (8, _revisar_ejecucion),
    "errores_logica": (8, _revisar_logica),
}


def registrar(clave):
    """Comprueba que una de las tres celdas rotas quedó arreglada, y da su XP."""
    motor = _motor()
    if clave not in _LOGROS_ERRORES:
        if motor:
            motor.caja("", f"No conozco el logro «{clave}».")
        return
    xp, revisor = _LOGROS_ERRORES[clave]
    ok, mensaje = revisor(globals())
    if motor is None:
        print(("[ok] " if ok else "[--] ") + mensaje)
        return
    if ok:
        ganado = _sumar_xp(clave, xp)
        extra = f" (+{ganado} XP)" if ganado else " (ya lo tenías)"
        motor.caja(f"Conseguido{extra}", mensaje, "ok")
    else:
        motor.caja("Casi", mensaje, "mal")


# =============================================================================
# Sección 1.2 · Diagnóstico de entrada
# =============================================================================
#
# Es a la vez la evaluación diagnóstica de la semana y la línea base del pre-test
# de la investigación. Tres reglas que condicionan el código:
#   1. No se dice qué ítems acertó (en la semana 16 se repite la foto).
#   2. Los XP se dan por completar, no por acertar.
#   3. Los ítems 1 y 2 no puntúan: son encuesta.
# Las respuestas quedan en RESPUESTAS_DIAGNOSTICO y se imprimen como salida de la
# celda: el .ipynb recogido es el canal por el que llegan a la investigación.

_ITEMS = [
    ("experiencia", "1 · ¿Cuál frase te describe mejor hoy?", [
        "Nunca he programado",
        "He probado algo suelto (Scratch, fórmulas de Excel, un tutorial de YouTube)",
        "He escrito código alguna vez, en algún lenguaje",
        "Programo con cierta comodidad",
    ], None),
    ("acceso", "2 · ¿Con qué computador cuentas para este curso?", [
        "Tengo portátil o de escritorio propio, y puedo instalarle cosas",
        "Tengo computador, pero es compartido o no puedo instalar programas",
        "Uso las salas de cómputo de la UIS",
        "Por ahora solo tengo celular",
    ], None),
    ("dato", "3 · Un computador guarda tu foto del carné. Esa foto es…",
     ["hardware", "dato", "software", "proceso"], 1),
    ("patron", "4 · ¿Qué número sigue?  2, 4, 8, 16, ___",
     ["18", "20", "24", "32"], 3),
    ("espacial", "5 · Un dron mira al Norte. Gira a la derecha, gira a la derecha, "
                 "gira a la izquierda. ¿Hacia dónde mira?",
     ["Norte", "Sur", "Este", "Oeste"], 2),
    ("traza", "6 · Sigue estos dos pasos en orden: primero x = 3, después x = x + 2. "
              "¿Cuánto vale x al final?",
     ["2", "3", "5", "No estoy seguro"], 2),
    ("ambiguedad", "7 · Estas son instrucciones para hacer un arroz. ¿Cuál NO le "
                   "serviría a un robot que obedece al pie de la letra?",
     ["Pon 2 tazas de agua en la olla", "Agrega sal al gusto", "Espera 18 minutos",
      "Apaga la estufa"], 1),
]

_ANIMO = [
    "1 — Con nervios", "2", "3 — Neutral", "4", "5 — Con toda",
]

_FRANJAS = [
    (1, "Estás exactamente donde este curso está diseñado para empezar. Y no es una "
        "frase de consuelo: la mayoría de tus compañeros marcó parecido, y el 90 % de "
        "ellos termina el semestre escribiendo programas que hoy le parecerían magia. "
        "Lo que acabas de responder <b>se entrena</b>, y ese es literalmente el trabajo "
        "de las próximas 16 semanas."),
    (3, "Ya piensas en patrones y en secuencias — que es la materia prima de un "
        "algoritmo. Lo que te falta no es capacidad, es <b>vocabulario</b>: las palabras "
        "y las reglas para decirle a una máquina lo que ya sabes pensar. Eso empieza hoy "
        "mismo."),
    (5, "Traes la intuición lógica afilada. Ojo con la trampa clásica de quien llega "
        "así: creer que por entender rápido no hace falta practicar. En este curso la "
        "nota no la da entender, la da <b>hacer</b>. Los ejercicios 5, 6 y 7 de este "
        "cuadernillo son para ti."),
]


def _mensaje_animo(indice):
    if indice <= 1:
        return ("Los nervios del arranque son normales y no predicen nada: buena parte "
                "del salón llegó igual. Este cuadernillo tiene intentos ilimitados, "
                "tres pistas por ejercicio y un tutor que no se cansa.")
    if indice == 2:
        return "Neutral está bien. Vuelve a mirar esta respuesta en la semana 16."
    return ("Con esa actitud llevas medio curso ganado. Guárdala para la semana 5, que "
            "es cuando aprieta.")


def _tarjeta_diagnostico(respuestas, aciertos):
    intuicion = next(texto for tope, texto in _FRANJAS if aciertos <= tope)
    animo = _mensaje_animo(respuestas["animo"])
    lineas = [
        f'<div style="margin-bottom:8px">{intuicion}</div>',
        f'<div style="margin-bottom:8px">{animo}</div>',
    ]
    if respuestas["acceso"] > 0:
        lineas.append(
            '<div style="margin-bottom:8px">Anotado: no tienes instalación local '
            'garantizada. <b>Nada de la nota de este cuadernillo depende de eso</b> '
            '— mira la sección 8.</div>'
        )
    _pintar(
        f'<div style="font-family:{_FUENTE};font-size:14.5px;line-height:1.55;'
        f'border:1px solid {_BORDE};border-left:4px solid {_VIOLETA};border-radius:6px;'
        'padding:12px 14px;margin:10px 0;background:#f9f8fd">'
        f'<div style="font-weight:650;color:{_VIOLETA_OSC};margin-bottom:6px">'
        'Tu punto de partida</div>'
        + "".join(lineas)
        + f'<div style="font-size:12.5px;color:{_GRIS};margin-top:10px">'
        'Esta foto es tuya. No es una nota ni una etiqueta. No te digo cuáles acertaste '
        'porque en la semana 16 vamos a repetirla, y quiero que sea una foto de verdad.'
        '</div></div>'
    )


def diagnostico():
    """El widget de siete ítems más la pregunta de ánimo, y la tarjeta por franjas."""
    if not HAY_WIDGETS:
        print("Tu punto de partida — responde mentalmente y sigue; "
              "los widgets no están disponibles en este entorno.")
        for _, enunciado, opciones, _ in _ITEMS:
            print("\n" + enunciado)
            for opcion in opciones:
                print("   -", opcion)
        return

    selectores = []
    bloques = []
    for _, enunciado, opciones, _ in _ITEMS:
        radio = W.RadioButtons(options=list(opciones), value=None,
                               layout=W.Layout(width="auto"))
        selectores.append(radio)
        bloques.append(W.VBox([
            W.HTML(f'<div style="font-family:{_FUENTE};font-size:14.5px;'
                   f'font-weight:600;color:{_VIOLETA_OSC};margin-top:6px">{enunciado}</div>'),
            radio,
        ]))
    animo = W.RadioButtons(options=list(_ANIMO), value=None, layout=W.Layout(width="auto"))
    bloques.append(W.VBox([
        W.HTML(f'<div style="font-family:{_FUENTE};font-size:14.5px;font-weight:600;'
               f'color:{_VIOLETA_OSC};margin-top:6px">8 · ¿Cómo llegas anímicamente '
               'a este curso?</div>'),
        animo,
    ]))

    salida = W.Output()
    boton = W.Button(description="Guardar mi punto de partida", button_style="primary",
                     layout=W.Layout(width="260px"))

    def _al_pulsar(_):
        salida.clear_output()
        elegidas = [s.index for s in selectores]
        with salida:
            if None in elegidas or animo.index is None:
                _pintar('<div style="font-family:%s;font-size:14px">Faltan preguntas '
                        'por responder. Ninguna se queda en blanco: si dudas, marca lo '
                        'que te parezca.</div>' % _FUENTE)
                return
            respuestas = {clave: elegidas[i] for i, (clave, _, _, _) in enumerate(_ITEMS)}
            respuestas["animo"] = animo.index
            aciertos = sum(
                1 for i, (_, _, _, correcta) in enumerate(_ITEMS)
                if correcta is not None and elegidas[i] == correcta
            )
            globals()["RESPUESTAS_DIAGNOSTICO"] = dict(respuestas)
            globals()["DIAGNOSTICO_COMPLETO"] = True
            _tarjeta_diagnostico(respuestas, aciertos)
            _sumar_xp("diagnostico", 10)
            motor = _motor()
            if motor is not None:
                motor.barra()
            # Se imprime a propósito: cuando el cuadernillo se recoge, el .ipynb
            # viaja con sus salidas y de ahí se extraen los datos del pre-test.
            # No se envía nada por la red: la telemetría del AVA es anónima y no
            # está pensada para respuestas de un cuestionario.
            print("RESPUESTAS_DIAGNOSTICO =", respuestas)

    boton.on_click(_al_pulsar)
    display(W.VBox(bloques + [boton, salida]))


# =============================================================================
# Ejercicio 7 · Vocabulario, mapa conceptual y dibujo
# =============================================================================

_FAMILIAS = [
    ("Lo físico", "#e8f0fb", _AZUL,
     ["computador", "hardware", "procesador", "memoria"]),
    ("Lo lógico", "#f3eefe", _VIOLETA,
     ["software", "dato", "proceso", "programa", "archivo"]),
    ("Lenguajes", "#e9f7ee", _VERDE,
     ["lenguaje de máquina", "lenguaje ensamblador", "lenguaje de alto nivel", "Python"]),
    ("El entorno", "#fdf6e3", _AMBAR,
     ["intérprete", "compilador", "IDE", "editor", "terminal", "Jupyter", "VS Code"]),
    ("Los errores", "#fdf1f1", _ROJO,
     ["error de sintaxis", "error de ejecución", "error de lógica"]),
]

VOCABULARIO = [concepto for _, _, _, conceptos in _FAMILIAS for concepto in conceptos]

RELACIONES = ["se compone de", "es un", "traduce", "ejecuta", "produce", "usa",
              "se guarda en", "puede tener"]

_COLOR_DE = {c: (relleno, borde)
             for _, relleno, borde, conceptos in _FAMILIAS for c in conceptos}


def ver_vocabulario():
    """Imprime las listas cerradas del ejercicio 7, agrupadas por familia."""
    bloques = []
    for titulo, relleno, borde, conceptos in _FAMILIAS:
        fichas = "".join(
            f'<span style="display:inline-block;background:{relleno};border:1px solid '
            f'{borde};border-radius:12px;padding:2px 9px;margin:2px 3px;font-size:13px">'
            f'{c}</span>' for c in conceptos
        )
        bloques.append(
            f'<div style="margin:6px 0"><div style="font-size:12.5px;font-weight:650;'
            f'color:{borde};text-transform:uppercase;letter-spacing:.05em">{titulo}</div>'
            f'<div>{fichas}</div></div>'
        )
    verbos = "".join(
        f'<span style="display:inline-block;background:#f6f7f9;border:1px solid {_BORDE};'
        f'border-radius:4px;padding:2px 9px;margin:2px 3px;font-size:13px">«{r}»</span>'
        for r in RELACIONES
    )
    _pintar(
        f'<div style="font-family:{_FUENTE};border:1px solid {_BORDE};border-left:4px '
        f'solid {_VIOLETA};border-radius:6px;padding:10px 14px;margin:8px 0">'
        f'<div style="font-weight:650;color:{_VIOLETA_OSC};margin-bottom:4px">'
        f'{len(VOCABULARIO)} conceptos permitidos</div>'
        + "".join(bloques)
        + f'<div style="margin-top:8px"><div style="font-size:12.5px;font-weight:650;'
        f'color:{_GRIS};text-transform:uppercase;letter-spacing:.05em">'
        f'{len(RELACIONES)} relaciones permitidas</div><div>{verbos}</div></div>'
        f'<div style="font-size:12.5px;color:{_GRIS};margin-top:8px">Cópialos tal cual, '
        'con tildes. Fuera de estas listas el test no reconoce la palabra.</div></div>'
    )


def _seno_coseno(vuelta):
    """seno y coseno de `vuelta` (0..1) sin importar `math`.

    Se resuelve con la serie de Taylor sobre el primer cuadrante. Es una
    disposición circular de nodos: la precisión de un píxel sobra.
    """
    tau = 6.283185307179586
    x = (vuelta % 1.0) * tau
    seno = x - x ** 3 / 6 + x ** 5 / 120 - x ** 7 / 5040 + x ** 9 / 362880 - x ** 11 / 39916800
    coseno = 1 - x ** 2 / 2 + x ** 4 / 24 - x ** 6 / 720 + x ** 8 / 40320 - x ** 10 / 3628800
    return seno, coseno


def dibujar_mapa(mapa):
    """Dibuja el mapa conceptual como SVG: conceptos en círculo y flechas rotuladas.

    Sin matplotlib (ver la cabecera del módulo). El dibujo es la mitad del
    ejercicio: una lista de tuplas no se siente un mapa hasta que se ve.
    """
    conceptos = []
    for tripleta in mapa:
        for extremo in (tripleta[0], tripleta[2]):
            if extremo not in conceptos:
                conceptos.append(extremo)
    if not conceptos:
        return

    ancho, alto = 840, 600
    cx, cy = ancho / 2, alto / 2 - 10
    rx, ry = ancho / 2 - 120, alto / 2 - 78
    posiciones = {}
    for i, concepto in enumerate(conceptos):
        seno, coseno = _seno_coseno(i / float(len(conceptos)) - 0.25)
        posiciones[concepto] = (cx + rx * coseno, cy + ry * seno)

    def caja(concepto):
        ancho_caja = min(190, 7.4 * len(concepto) + 20)
        return ancho_caja, 26.0

    def borde_de(concepto, hacia):
        """Punto donde la recta hacia `hacia` sale de la caja de `concepto`."""
        x, y = posiciones[concepto]
        hx, hy = posiciones[hacia]
        dx, dy = hx - x, hy - y
        if dx == 0 and dy == 0:
            return x, y
        w, h = caja(concepto)
        tx = (w / 2 + 4) / abs(dx) if dx else float("inf")
        ty = (h / 2 + 4) / abs(dy) if dy else float("inf")
        t = min(tx, ty)
        return x + dx * t, y + dy * t

    partes = [
        f'<svg viewBox="0 0 {ancho} {alto}" width="100%" style="max-width:{ancho}px;'
        f'font-family:{_FUENTE}" role="img" aria-label="Mapa conceptual de la semana 1">',
        f'<defs><marker id="ava-punta" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{_GRIS}"/></marker></defs>',
    ]
    for origen, verbo, destino in mapa:
        if origen not in posiciones or destino not in posiciones:
            continue
        x1, y1 = borde_de(origen, destino)
        x2, y2 = borde_de(destino, origen)
        partes.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{_GRIS}" stroke-width="1.2" opacity=".62" '
            'marker-end="url(#ava-punta)"/>'
        )
        mx, my = x1 + (x2 - x1) * 0.42, y1 + (y2 - y1) * 0.42
        ancho_texto = 5.6 * len(verbo) + 8
        partes.append(
            f'<rect x="{mx - ancho_texto / 2:.1f}" y="{my - 8:.1f}" '
            f'width="{ancho_texto:.1f}" height="15" rx="3" fill="#ffffff" opacity=".9"/>'
            f'<text x="{mx:.1f}" y="{my + 3.5:.1f}" text-anchor="middle" font-size="10.5" '
            f'fill="{_GRIS}">{_escapar(verbo)}</text>'
        )
    for concepto in conceptos:
        x, y = posiciones[concepto]
        w, h = caja(concepto)
        relleno, borde = _COLOR_DE.get(concepto, ("#f6f7f9", _GRIS))
        partes.append(
            f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" '
            f'height="{h:.1f}" rx="13" fill="{relleno}" stroke="{borde}" stroke-width="1.4"/>'
            f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" font-size="12" '
            f'fill="#10294d">{_escapar(concepto)}</text>'
        )
    leyenda_x = 14
    for titulo, relleno, borde, _ in _FAMILIAS:
        partes.append(
            f'<rect x="{leyenda_x}" y="{alto - 22}" width="11" height="11" rx="3" '
            f'fill="{relleno}" stroke="{borde}"/>'
            f'<text x="{leyenda_x + 16}" y="{alto - 13}" font-size="11" fill="{_GRIS}">'
            f'{titulo}</text>'
        )
        leyenda_x += 30 + 6.2 * len(titulo)
    partes.append("</svg>")
    _pintar(
        f'<div style="margin:10px 0">{"".join(partes)}</div>'
        f'<div style="font-family:{_FUENTE};font-size:12.5px;color:{_GRIS};'
        'text-align:center;font-style:italic;margin-bottom:10px">'
        f'Tu mapa: {len(conceptos)} conceptos y {len(mapa)} relaciones.</div>'
    )


# =============================================================================
# Corrección con clave hasheada
# =============================================================================
#
# La celda de prueba es visible para el estudiante. Cuando la respuesta se puede
# copiar (una clasificación, un orden, unas tripletas) el test no puede
# contenerla, así que aquí solo viven huellas SHA-256: leer el módulo no revela
# nada. No es criptografía seria — es una barrera proporcional al problema, la
# misma postura que `metrics_bridge.py` documenta para su token.
#
# Cuando la corrección es de comportamiento (una función que calcula, un archivo
# que existe) se usan `assert` normales en la celda de prueba: no filtran nada y
# de paso enseñan a leer un assert.

def _normalizar(valor):
    """Baja a minúsculas, quita tildes y colapsa espacios, recursivamente.

    Así «Hardware », «hardware» y «HARDWARE» son la misma respuesta: la
    corrección evalúa el concepto, no la pulsación de teclas.
    """
    if isinstance(valor, str):
        texto = unicodedata.normalize("NFKD", valor.strip().lower())
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        return " ".join(texto.split())
    if isinstance(valor, dict):
        return {_normalizar(k): _normalizar(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_normalizar(x) for x in valor]
    return valor


def _huella(*partes):
    """Huella SHA-256 de una respuesta ya normalizada.

    Las partes se concatenan con el nombre del ejercicio y la llave: así dos
    respuestas iguales en ejercicios distintos no comparten huella y nadie puede
    deducir «estas dos filas son la misma palabra» comparando el módulo.
    """
    texto = "|".join(repr(_normalizar(p)) for p in partes)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# --- Huellas de las respuestas ------------------------------------------------
# Estas tablas se generan con un script de autoría que nunca viaja al alumno.
# Aquí solo hay huellas: quien lea el módulo no aprende ninguna respuesta.

# Ejercicio 1: una huella por fila, para poder decir CUÁL está mal sin decir cuál
# es la respuesta. Las llaves van en claro porque son el enunciado, no la clave.
_E1_LLAVES = {
    'el mouse del portatil':
        "66a45f8f36fc141f9d9c787aad9d767f27efc7d4727b88dde7cefcc35c5fbc3a",
    'whatsapp':
        "c3695e1dec7c6186c129563e49d7b0076119e2bef44072845e58a9b8acbdc849",
    'la nota 4.3 de tu primer parcial':
        "49540526f8ac85b8285587ed61163d105b83ba2bdd80713b65ad1caca5ac3421",
    'ordenar la lista del curso por apellido':
        "171f6b6795f43f911ed0504177acdc7c83d2f63bfa203575c7053a522f503f8a",
    'la pantalla tactil del cajero automatico':
        "a69e7c4cff11f801a738e54173dd548394e57c0463b912423473ec985d7c9249",
    'windows 11':
        "4c6167c83874ab7ab416f2df67d7c9fec000fc1125977430b61cd5b8721843bb",
    'la foto de tu carne de la uis':
        "ebd28a62bb80c81c3bddfb2fe699826969396daadbf48a34741667ab32bea387",
    'calcular el promedio del semestre':
        "858c569a8b5163514c14df06bd1c2d916762bdcc823a9bca70f5850c6f4d31a6",
}

# Ejercicio 2: además del orden correcto se guardan los dos errores típicos
# (invertido y medios cambiados) para poder dar una pista distinta a cada uno,
# y las huellas de las cuatro piezas sueltas para detectar una copia mal hecha.
_E2 = {
    "ok": "b261950d2b892814893dee80550f7c5a1ab7a1a53d74ad860af2189830113d1e",
    "invertido": "4798f8278de8748a407bad25e04ea538161601f1c4a01aa6444b42c615f8b2b2",
    "medios": "237cf55c04304600fa5ff41525a67101e906796f532a24e8ce226f0f1611e1ab",
    "primero": "e284523f24eaf953360c87933e0357f6b5869d18c62dd4305e818f0385fa0be4",
    "ultimo": "eb24e1eb8c1630560e07e3d32dd3a80d8f298ee1b6238901fac75c7aa596de8f",
    "piezas": [
        "19325c5d60f2d71d1d379d61cf6d317b619a191e6aef77ae4b0b80d49daaa788",
        "e284523f24eaf953360c87933e0357f6b5869d18c62dd4305e818f0385fa0be4",
        "eb24e1eb8c1630560e07e3d32dd3a80d8f298ee1b6238901fac75c7aa596de8f",
        "ed862201965ac6f77c19596e1ee52c2c71f248962bd140ff73a03bcbffd55cd7",
    ],
}

# Ejercicio 4: cada programa mal diagnosticado tiene su propia pregunta.
_E4_LLAVES = {
    'a': (
        "d12030d5ccb9062bb1ce669f22eae99582fb491f3ededab66b2b8661f0aae0b6",
        'Programa A: fíjate en el final de la línea del `if`. ¿Alcanzaría Python '
        'siquiera a empezar a ejecutar?',
    ),
    'b': (
        "9fc2040e1d2ab627ac83f092e47ef331ec9a2db8530acb7981aabd6d742f04c0",
        'Programa B: la lista tiene tres notas. ¿El programa está mal *escrito* o mal '
        '*pensado*, o simplemente le pide algo que no existe cuando ya está corriendo?',
    ),
    'c': (
        "f9b1f8b12f3e7d632aaeefd9a429c748829d364066f2ddd119c4ec7cff7787e4",
        'Programa C: haz la cuenta a mano. 15 % de 80.000 no es 15. ¿Python tiene forma '
        'de saber que te equivocaste?',
    ),
}

# Ejercicio 7: el par de conceptos va en claro y solo el verbo va hasheado. Es
# deliberado: el mensaje de fallo debe poder nombrar qué falta conectar sin
# regalar la relación entera.
_E7_NUCLEO = (
    ('procesador', 'lenguaje de máquina',
     "86779664cb6202ef2d2df713c0cd150a25206055495512bc4bd0b838e07f4c6a"),
    ('intérprete', 'lenguaje de alto nivel',
     "8aff76a4c9abd71e9def5463d0436037429fe050b306029385d83aeebd63e50e"),
    ('IDE', 'editor',
     "5ee954102b7180ddc17cdd8b3f221a564cdb20c645acfa3adf95da43dd4b6b3b"),
    ('proceso', 'dato',
     "a9bb5ffb3926e390006b6d6bd44398ec41e52a7c685351730e5789b6782d5b3f"),
)

_E1_COLETILLA = "Pregúntate si es la receta o el ingrediente."


def _plural(nombres):
    if len(nombres) == 1:
        return "Revisa esta: " + nombres[0] + "."
    if len(nombres) == 2:
        return "Revisa estas dos: " + ", ".join(nombres) + "."
    return f"Revisa estas {len(nombres)}: " + ", ".join(nombres) + "."


def _corregir_1(respuesta):
    esperadas = set(_E1_LLAVES)
    if {_normalizar(k) for k in respuesta} != esperadas:
        raise AssertionError(
            "No agregues, borres ni cambies las filas: son las ocho del enunciado, "
            "escritas tal cual."
        )
    malas = [f"'{k}'" for k, v in respuesta.items()
             if _huella("ejercicio_1", k, v) != _E1_LLAVES[_normalizar(k)]]
    if malas:
        raise AssertionError(_plural(malas) + " " + _E1_COLETILLA)


def _corregir_2(respuesta):
    if sorted(_huella("ejercicio_2", "pieza", x) for x in respuesta) != _E2["piezas"]:
        raise AssertionError(
            "Alguno de los cuatro textos no está copiado tal cual. Cópialos con sus "
            "comillas, sin cambiar ni un espacio ni un signo."
        )
    entera = _huella("ejercicio_2", "orden", respuesta)
    if entera == _E2["ok"]:
        return
    if entera == _E2["invertido"]:
        raise AssertionError(
            "Lo tienes exactamente al revés. La posición 1 es la más cercana a la "
            "máquina, no a ti."
        )
    if entera == _E2["medios"]:
        raise AssertionError(
            "Los extremos están bien, pero los dos del medio están cambiados. ¿Cuál de "
            "los dos necesita que TÚ le digas dónde guardar cada cosa?"
        )
    if (_huella("ejercicio_2", "pieza", respuesta[0]) != _E2["primero"]
            or _huella("ejercicio_2", "pieza", respuesta[-1]) != _E2["ultimo"]):
        raise AssertionError(
            "Empieza por los extremos, que son los fáciles: uno de los cuatro no tiene "
            "ni una letra que una persona pueda leer, y otro se lee casi como una frase. "
            "Esos son el 1 y el 4."
        )
    raise AssertionError(
        "Todavía no. Ordena de abajo hacia arriba: primero lo único que entiende el "
        "procesador, al final lo que entiende una persona."
    )


def _corregir_4(respuesta):
    malas = []
    for llave, (huella, mensaje) in _E4_LLAVES.items():
        valor = respuesta.get(llave.upper(), respuesta.get(llave))
        if _huella("ejercicio_4", llave, valor) != huella:
            malas.append(mensaje)
    if malas:
        raise AssertionError(" · ".join(malas))


def _corregir_7(respuesta):
    faltan = []
    for origen, destino, huella_verbo in _E7_NUCLEO:
        pares = [t for t in respuesta
                 if _normalizar(t[0]) == _normalizar(origen)
                 and _normalizar(t[2]) == _normalizar(destino)]
        if not pares:
            faltan.append(f"Te falta decir algo que conecte '{origen}' con '{destino}'.")
        elif not any(_huella("ejercicio_7", origen, destino, t[1]) == huella_verbo
                     for t in pares):
            faltan.append(
                f"Conectaste '{origen}' con '{destino}', pero con un verbo que no es el "
                f"que vimos en clase. Léela en voz alta: ¿suena a lo que dijo la "
                f"sección 3?"
            )
    if faltan:
        raise AssertionError(" ".join(faltan))


_CORRECTORES = {
    "ejercicio_1": _corregir_1,
    "ejercicio_2": _corregir_2,
    "ejercicio_4": _corregir_4,
    "ejercicio_7": _corregir_7,
}


def corregir(clave, respuesta):
    """Compara contra la clave hasheada y lanza AssertionError si algo falla.

    El mensaje dice **qué** está mal (cuál fila, cuál par de conceptos) y nunca
    **cuál** era la respuesta: la celda de prueba es visible y el mensaje también.
    """
    if clave not in _CORRECTORES:
        raise AssertionError(f"No hay clave registrada para '{clave}'.")
    _CORRECTORES[clave](respuesta)


# =============================================================================
# Sección 8 · Entorno de trabajo
# =============================================================================

def verificar_entorno():
    """Columna A de la lista de comprobación: se ejecuta, no se marca a mano.

    El microcurrículo pide una lista de comprobación del entorno. La del AVA no
    es una casilla de honor: es código que pregunta al sistema y responde con lo
    que encuentra.
    """
    filas = []

    filas.append(("Intérprete de Python", True, platform.python_version()))

    sistema = platform.system() or "desconocido"
    en_contenedor = os.path.exists("/.dockerenv")
    filas.append(("Sistema operativo", True,
                  sistema + (" (contenedor)" if en_contenedor else "")))

    carpeta = os.getcwd()
    filas.append(("Carpeta de trabajo", True, carpeta))

    cuadernillos = [f for f in sorted(os.listdir(carpeta)) if f.endswith(".ipynb")]
    filas.append(("Este cuadernillo", bool(cuadernillos),
                  cuadernillos[0] if cuadernillos else "no lo veo desde aquí"))

    if HAY_WIDGETS:
        filas.append(("Widgets interactivos (ipywidgets)", True,
                      getattr(W, "__version__", "instalado")))
    else:
        filas.append(("Widgets interactivos (ipywidgets)", False, "no disponible"))

    # Sin matplotlib a propósito: los diagramas y la gráfica de esta semana son
    # SVG generado aquí mismo, para no gastar 80 MB de RAM por kernel.
    filas.append(("Diagramas y gráficas", True, "SVG incrustado, sin dependencias"))

    try:
        prueba = os.path.join(carpeta, ".ava_prueba_escritura")
        with open(prueba, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(prueba)
        escritura = (True, "sí (prueba realizada y borrada)")
    except OSError as err:
        escritura = (False, f"no ({err.__class__.__name__})")
    filas.append(("Permiso de escritura de archivos",) + escritura)

    cuadernillo = os.environ.get("CUADERNILLO_CODIGO", "")
    if cuadernillo:
        filas.append(("Tutor de IA", True, f"disponible, 5 preguntas ({cuadernillo})"))
    else:
        filas.append(("Tutor de IA", True, "disponible dentro del AVA, 5 preguntas"))

    print("Entorno del AVA")
    ancho = max(len(nombre) for nombre, _, _ in filas)
    for nombre, ok, detalle in filas:
        marca = "ok" if ok else "--"
        puntos = "." * (ancho - len(nombre) + 3)
        print(f"  [{marca}] {nombre} {puntos} {detalle}")
    fallos = [n for n, ok, _ in filas if not ok]
    if not fallos:
        print("Tu entorno del AVA está completo. Nada que instalar.")
    elif "Widgets interactivos (ipywidgets)" in fallos:
        print("Los widgets no están dibujándose. Avísale al profesor: es un problema "
              "del servidor, no tuyo. Los ejercicios calificables funcionan igual.")
    else:
        print("Algo del entorno no responde. Avísale al profesor; no es culpa tuya.")


_CASILLAS_LOCAL = [
    "Instalé Python desde python.org (y marqué «Add python.exe to PATH» en Windows)",
    "`python --version` me contesta con un número en la terminal",
    "Instalé VS Code y la extensión Python de Microsoft",
    "Creé la carpeta algoritmos-uis con un archivo hola.py",
    "Ejecuté hola.py desde la terminal",
    "Ejecuté hola.py desde VS Code",
    "Ejecuté hola.py desde Jupyter",
]


def lista_comprobacion():
    """Columna B: la instalación local, autodeclarada, con su texto para Moodle.

    No cambia la nota, y eso está escrito en el cuadernillo. Se registra porque
    es una evidencia del microcurrículo, no porque decida nada.
    """
    if not HAY_WIDGETS:
        print("Lista de comprobación del entorno local (columna B):")
        for texto in _CASILLAS_LOCAL:
            print("   [ ]", texto)
        print("\nCopia esta lista en el foro de Moodle indicando qué cumpliste.")
        return

    ruta = W.RadioButtons(
        options=[
            ("Ruta 1 — tengo computador y ya instalé (o estoy instalando)", 1),
            ("Ruta 2 — no tengo computador propio o no puedo instalar", 2),
        ],
        value=None, layout=W.Layout(width="auto"),
    )
    casillas = [W.Checkbox(description=t, indent=False, value=False,
                           layout=W.Layout(width="max-content"))
                for t in _CASILLAS_LOCAL]
    version = W.Text(description="Versión:", placeholder="3.12.4",
                     style={"description_width": "70px"},
                     layout=W.Layout(width="260px"))
    observacion = W.Textarea(
        description="", placeholder="Una línea sobre cómo te fue (opcional)",
        layout=W.Layout(width="560px", height="52px"),
    )
    salida = W.Output()
    boton = W.Button(description="Generar mi texto para Moodle", button_style="primary",
                     layout=W.Layout(width="260px"))

    def _al_pulsar(_):
        salida.clear_output()
        with salida:
            if ruta.value is None:
                print("Elige primero la ruta 1 o la ruta 2. Ninguna de las dos resta "
                      "puntos: son dos situaciones reales.")
                return
            hoy = datetime.date.today().isoformat()
            nombre = os.environ.get("ALUMNO_NOMBRE", "<escribe tu nombre>")
            if ruta.value == 1:
                marcadas = [t for c, t in zip(casillas, _CASILLAS_LOCAL) if c.value]
                formas = [f for c, f in zip(casillas[4:], ["terminal", "VS Code", "Jupyter"])
                          if c.value]
                local = (f"ruta 1 · Python {version.value or '(sin anotar)'} · "
                         f"VS Code {'sí' if casillas[2].value else 'todavía no'} · "
                         f"hola.py ejecutado desde "
                         f"{', '.join(formas) if formas else '(todavía ninguna forma)'}")
                pendiente = len(_CASILLAS_LOCAL) - len(marcadas)
            else:
                local = "ruta 2 — pendiente, se hará en sala de cómputo"
                pendiente = 0
            print("LISTA DE COMPROBACIÓN — SEMANA 1")
            print(f"Estudiante: {nombre}")
            print(f"Entorno del AVA: verificado automáticamente el {hoy} (8/8)")
            print(f"Entorno local: {local}")
            print(f"Observación del estudiante: {observacion.value.strip() or '(sin observación)'}")
            print()
            print("Copia el bloque de arriba en el foro «Lista de comprobación» de "
                  "Moodle. Ninguna de las dos rutas cambia tu nota de este cuadernillo.")
            if pendiente:
                print(f"({pendiente} punto(s) de la ruta 1 todavía sin marcar: "
                      "puedes volver aquí cuando los completes.)")

    boton.on_click(_al_pulsar)
    display(W.VBox([
        W.HTML(f'<div style="font-family:{_FUENTE};font-size:14px;font-weight:600;'
               f'color:{_VIOLETA_OSC}">¿Cuál es tu situación?</div>'),
        ruta,
        W.HTML(f'<div style="font-family:{_FUENTE};font-size:14px;font-weight:600;'
               f'color:{_VIOLETA_OSC};margin-top:6px">Si elegiste la ruta 1, marca lo '
               'que ya hiciste</div>'),
        W.VBox(casillas), version,
        W.HTML(f'<div style="font-family:{_FUENTE};font-size:14px;font-weight:600;'
               f'color:{_VIOLETA_OSC};margin-top:6px">Observación</div>'),
        observacion, boton, salida,
    ]))


# Alias: el diseño llama `checklist_local()` a la columna B. El nombre en español
# es el bueno; el otro se mantiene por si alguien copia una celda del diseño.
checklist_local = lista_comprobacion


_LOGROS_INSIGNIA = [
    "Ejecuté y modifiqué mi primer programa",
    "Vi la misma suma en los tres niveles de lenguaje",
    "Programé la MiniMáquina en lenguaje de máquina",
    "Rompí las tres celdas y leí los tres errores",
    "Creé un archivo desde código",
    "Armé mi mapa conceptual",
]

_PUENTE = ("<b>Próxima parada &rarr; Semana 2: De problemas a algoritmos.</b> La semana "
           "que viene vamos a pensar como programadores… casi sin tocar el teclado.")


def reclamar_insignia():
    """Seis casillas de cierre; con las seis marcadas se pide la insignia al motor."""
    motor = _motor()
    if not HAY_WIDGETS or motor is None:
        if motor is not None:
            motor.cerrar(_LOGROS_INSIGNIA, _PUENTE)
        else:
            print("Logros de la semana 1:")
            for logro in _LOGROS_INSIGNIA:
                print("   -", logro)
        return
    casillas = [W.Checkbox(description=t, indent=False,
                           layout=W.Layout(width="max-content"))
                for t in _LOGROS_INSIGNIA]
    salida = W.Output()
    boton = W.Button(description="Reclamar la insignia", button_style="primary",
                     layout=W.Layout(width="200px"))

    def _al_pulsar(_):
        salida.clear_output()
        faltan = [c.description for c in casillas if not c.value]
        with salida:
            if faltan:
                lista = "".join(f"<li>{t}</li>" for t in faltan)
                _pintar(
                    f'<div style="font-family:{_FUENTE};font-size:14.5px;border:1px solid '
                    f'{_BORDE};border-left:4px solid {_AMBAR};border-radius:6px;'
                    'padding:12px 14px;background:#fdf9ef">'
                    f'<div style="font-weight:650;color:{_AMBAR}">Te falta poco</div>'
                    f'<ul>{lista}</ul>Vuelve a esas secciones: no hay prisa y los '
                    'intentos no restan.</div>'
                )
                return
            motor.cerrar(_LOGROS_INSIGNIA, _PUENTE)

    boton.on_click(_al_pulsar)
    display(W.VBox(casillas + [boton, salida]))
