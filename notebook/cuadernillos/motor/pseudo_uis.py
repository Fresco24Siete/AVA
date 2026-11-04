"""Mini-intérprete de pseudocódigo en español para los cuadernillos del AVA.

Qué es
------
Un lenguaje diminuto —palabras clave en español, cercanas a PSeInt y a
Flowgorithm— que el estudiante escribe, ejecuta, ve dibujado como diagrama de
flujo y traduce a Python sin salir del cuadernillo. El pseudocódigo deja de ser
texto muerto y se vuelve un artefacto **ejecutable y calificable**.

Por qué está escrito así
------------------------
* **Solo biblioteca estándar en el núcleo.** El módulo termina incrustado dentro
  del `.ipynb` que recibe el alumno (un archivo único, sin dónde poner un
  `import`), y además corre en el autograder headless de nbgrader. Una
  dependencia nueva rompería las dos cosas. `ipywidgets` se importa dentro de
  `try/except`, igual que en `ava_motor.py`: sin él la capa visual degrada a
  HTML estático y el núcleo sigue intacto.
* **`ejecutar_pseudo` jamás propaga una excepción.** Es el contrato duro con
  nbgrader: si el estudiante escribe basura, el `assert` del test falla con un
  mensaje pedagógico y la telemetría registra `AssertionError` con texto útil,
  en vez de un `SyntaxError` del motor que nadie sabe leer.
* **Ningún error del estudiante produce un traceback.** Todo camino de fallo
  —análisis, tipos, ejecución, ciclo infinito, cola de entradas vacía— termina
  en un `Error` del catálogo, con *qué pasó*, *por qué* y *cómo lo arreglas*.

Decisiones que la especificación dejaba abiertas están marcadas en el código con
un comentario que empieza por «Decisión:».
"""

import builtins
import difflib
import re
import textwrap
from html import escape as _escapar

# La capa visual es opcional a propósito: el autograder corre sin frontend.
try:  # pragma: no cover - depende del entorno
    import ipywidgets as W
    HAY_WIDGETS = True
except ImportError:  # pragma: no cover
    W = None
    HAY_WIDGETS = False

try:  # pragma: no cover - fuera de Jupyter no hay IPython
    from IPython.display import HTML, display, clear_output
    HAY_IPYTHON = True
except ImportError:  # pragma: no cover
    HTML = None
    HAY_IPYTHON = False

    def display(*_a, **_k):
        pass

    def clear_output(*_a, **_k):
        pass


# ── Paleta ───────────────────────────────────────────────────────────────────
# Los mismos siete colores de `ava_motor.py` y de los diagramas mermaid del
# documento de diseño, para que el cuadernillo se vea como una sola pieza.
VERDE, VERDE_OSC = "#008300", "#005400"
AZUL, AZUL_OSC = "#2a78d6", "#104281"
VIOLETA, VIOLETA_OSC = "#4a3aa7", "#2a1f6b"
AMBAR, AMBAR_OSC, AMBAR_TEXTO = "#eda100", "#8a6d00", "#3a2a00"
GRIS, GRIS_CLARO, BORDE = "#52514e", "#f6f7f9", "#dfe3e8"
ROJO = "#d03b3b"
TINTA = "#0b0b0b"

# ── Léxico del mini-lenguaje ─────────────────────────────────────────────────
TIPOS = ("Entero", "Real", "Cadena", "Logico")

# nombre canónico -> (nombre en Python, aridad implícita 1)
FUNCIONES = {
    "convertiraentero": ("ConvertirAEntero", "int"),
    "convertirareal": ("ConvertirAReal", "float"),
    "convertiratexto": ("ConvertirATexto", "str"),
    "longitud": ("Longitud", "len"),
    "absoluto": ("Absoluto", "abs"),
    "redondear": ("Redondear", "round"),
    "truncar": ("Truncar", "int"),
}

# Las que el catálogo (PS06) nombra como «instrucciones que entiendo».
# 2026-10-05: entra `Para`. El motor solo tenía `Mientras`, y desde el recorte
# del 22-sep ningún texto visible del cuadernillo 4 lo decía: los alumnos
# escribieron el `Para` que traen de PSeInt y el motor les contestó
# «'Para i' no sirve como nombre de variable. Arréglalo: Para_i» (25 veces).
_INSTRUCCIONES = ("Definir", "Constante", "Leer", "Escribir", "Si", "Mientras",
                  "Para")
# Universo para el «¿querías decir…?» de difflib: instrucciones + cierres.
_PALABRAS_CLAVE = _INSTRUCCIONES + (
    "Mostrar", "Algoritmo", "FinAlgoritmo", "Entonces", "Sino", "FinSi",
    "Hacer", "FinMientras", "Como", "FinPara", "Proceso", "FinProceso",
)
# Las palabras de ESTRUCTURA: si una de ellas es la «mitad» de lo que parece un
# nombre con espacio (`Leer Para i`, `total Entonces`), la línea no es un nombre
# partido y unirlas con guion bajo no la arregla (ver `_ps14`).
#
# 2026-10-05, tras la revisión: aquí NO están los tipos, ni `fin`, ni `hasta`,
# ni `algoritmo`, `proceso` o `constante`. Son del lenguaje, pero también son
# sustantivos y adjetivos corrientes, y por tanto mitades verosímiles de un
# nombre: `numero entero`, `valor real`, `hora fin`, `edad hasta`. La primera
# versión de esta tabla las incluía y le contestaba al alumno que 'entero' «no
# puede ser un nombre de variable ni un pedazo de uno», que es falso
# (`numero_entero` y `hora_fin` son nombres válidos, y `fin <- 3` corre). Para
# esas el consejo de siempre —únelas con guion bajo— es el correcto. Tampoco
# están `y`, `o`, `no`, `con` ni `paso`, por la misma razón (`costo y`).
_DE_ESTRUCTURA = {p.lower() for p in _PALABRAS_CLAVE} - {
    "algoritmo", "proceso", "constante"}

MAX_PASOS = 10_000          # tope de ciclo infinito (PS09)
_TOPE_SALIDA = 200_000      # caracteres; evita que un ciclo llene la memoria

_OPS2 = ("<-", "<>", "<=", ">=")
_OPS1 = "=<>+-*/^(),"
_RE_NUM = re.compile(r"\d+(?:\.\d+)?")
# El identificador admite tildes y eñes A PROPÓSITO: si no las aceptara, el
# tokenizador diría «no conozco el símbolo á» y el estudiante no entendería
# nada. Se aceptan aquí para poder dar el mensaje bueno (PS14) más adelante.
_RE_IDENT = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ_][A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ_]*")
_RE_ACENTO = re.compile(r"[ÁÉÍÓÚÜÑáéíóúüñ]")


def _norm(palabra):
    """Palabras clave sin distinguir mayúsculas; los nombres de variable sí."""
    return palabra.lower()


# ── Lo que el alumno trae de PSeInt y este motor NO tiene ────────────────────
# 2026-10-05. Antes, cualquier línea que empezara por dos palabras se tomaba por
# «un nombre de variable con un espacio en medio» (PS14) y el consejo era unir
# las dos con guion bajo. Con `Repetir`, `Segun x Hacer` o `Fin Si` eso produce
# un disparate («Arréglalo: Fin_Si»), y hubo un alumno que lo obedeció al pie de
# la letra y entregó `para_i <- 3 hasta n hacer`. Un consejo falso es peor que
# ninguno: el estudiante le cree al motor.
#
# Aquí están las estructuras de PSeInt que el motor no implementa, cada una con
# lo que hay que escribir en su lugar. La clave va en minúsculas y sin tildes.
_CICLO_QUE_SI = "escribe el ciclo con Mientras o con Para."
_SI_ANIDADO = ("pregunta caso por caso con Si ... Sino ... FinSi (y un Si "
               "dentro del Sino cuando haya más de dos casos).")
_TODO_ADENTRO = ("escribe todas las instrucciones seguidas, dentro de "
                 "Algoritmo ... FinAlgoritmo.")
_NO_TENGO = {
    "repetir": ("Repetir ... Hasta Que", _CICLO_QUE_SI),
    "hasta": ("Hasta Que (el cierre de Repetir)", _CICLO_QUE_SI),
    # `Desde i <- 1 Hasta 5 Hacer` es como se dicta el Para en más de un salón.
    # Sin esta entrada caía en PS14 («Arréglalo: Desde_i»): mismo disparate del
    # incidente, con otra palabra (2026-10-05, revisión).
    "desde": ("el ciclo Desde",
              "es el mismo ciclo Para: cambia la palabra Desde por Para."),
    "findesde": ("el ciclo Desde",
                 "el ciclo se escribe con Para y se cierra con FinPara."),
    "segun": ("Segun", _SI_ANIDADO),
    "caso": ("Segun ni sus casos", _SI_ANIDADO),
    "finsegun": ("Segun", _SI_ANIDADO),
    "funcion": ("funciones propias (Funcion)", _TODO_ADENTRO),
    "finfuncion": ("funciones propias (Funcion)", _TODO_ADENTRO),
    "subproceso": ("subprocesos (SubProceso)", _TODO_ADENTRO),
    "finsubproceso": ("subprocesos (SubProceso)", _TODO_ADENTRO),
    "subalgoritmo": ("subalgoritmos (SubAlgoritmo)", _TODO_ADENTRO),
    "finsubalgoritmo": ("subalgoritmos (SubAlgoritmo)", _TODO_ADENTRO),
    "retornar": ("funciones propias, así que tampoco Retornar", _TODO_ADENTRO),
    "dimension": ("arreglos (Dimension)",
                  "usa una variable suelta para cada dato."),
    "imprimir": ("la instrucción Imprimir",
                 "para mostrar algo en pantalla se usa Escribir."),
    "limpiar": ("pantalla que limpiar", "borra esa línea: no hace falta."),
    "borrar": ("pantalla que borrar", "borra esa línea: no hace falta."),
    "esperar": ("teclas ni tiempos que esperar",
                "borra esa línea: no hace falta."),
}

# Palabras que el motor SÍ conoce pero que no pueden abrir una línea. Tampoco
# son «un nombre de variable con espacio».
_FUERA_DE_SITIO = {
    "entonces": ("Entonces va al final de la línea del Si, no en una línea "
                 "aparte.", "Si saldo > 0 Entonces"),
    "hacer": ("Hacer va al final de la línea del Mientras o del Para, no en "
              "una línea aparte.", "Mientras saldo > 0 Hacer"),
    "como": ("Como solo se usa dentro de un Definir, para decir el tipo.",
             "Definir copias Como Entero"),
    # Solo cuando van las dos juntas (ver `_sentencia`): sueltas, `con` y
    # `paso` pueden ser la mitad de un nombre mal escrito, y eso es PS14.
    "con paso": ("'Con Paso' solo se usa en la línea de un Para, antes de "
                 "Hacer.", "Para i <- 1 Hasta 10 Con Paso 2 Hacer"),
    "algoritmo": ("ya hay un algoritmo abierto, y no se puede abrir otro "
                  "dentro.", "deja un solo Algoritmo ... FinAlgoritmo."),
    "proceso": ("ya hay un algoritmo abierto, y no se puede abrir otro "
                "dentro.", "deja un solo Proceso ... FinProceso."),
}

# `Fin Si`, `Fin Mientras`... con espacio: es como lo dicta más de un profesor
# y como lo escribieron varios alumnos el 5-oct. Se leen igual que pegados.
_SE_CIERRA_CON_FIN = {"si", "mientras", "para", "algoritmo", "proceso"}

# 2026-10-05 (revisión). Palabras que abren una línea de estructura pero que
# también son la primera mitad verosímil de un nombre: `fin semana <- 6`,
# `hasta ahora <- 0`, `caso base <- 1`, `proceso actual <- 2`. Cuando detrás de
# las dos palabras viene una flecha (o un =) y la línea no tiene nada más de
# estructura, es una asignación a un nombre con espacio, y se le contesta con el
# PS14 de siempre y no con «'Fin semana' no cierra ningún bloque». A propósito
# NO están los verbos (`Repetir x <- 3` no es una variable «Repetir x») ni
# `Funcion`, cuya cabecera en PSeInt tiene justo esa forma.
_PRIMERA_MITAD_DE_NOMBRE = {"fin", "hasta", "caso", "algoritmo", "proceso"}

# Con qué otras palabras se abre un ciclo que cuenta, en otros dialectos. El
# motor desplegado hasta el 5-oct aconsejaba pegarlas con guion bajo al nombre
# (`Para_i`, `Desde_i`, `For_i`) y hubo quien obedeció: al proponer la línea
# corregida se desanda ese prefijo (ver `_sin_prefijo`).
_ABREN_UN_CICLO = ("para", "desde", "for", "ciclo", "repetir")
# Lo mismo para el «sino, si...» que este motor no tiene pegado.
_ABREN_UN_SINO_SI = ("sinosi", "elif", "elsif", "elseif")


def _sin_tildes(palabra):
    """`Según` y `Segun` son la misma palabra para buscarla en las tablas."""
    return "".join(_SIN_TILDE.get(c, c) for c in palabra)


def _sin_prefijo(nombre, prefijos):
    """`Para_i` -> `i`, si lo de antes del guion bajo es una de `prefijos`.

    2026-10-05. Solo sirve para redactar el «Arréglalo»: quien entrega
    `para_i <- 3 hasta n hacer` obedeció un consejo del motor viejo, y
    proponerle `Para para_i <- 3 ...` sería encadenar el disparate.
    """
    cabeza, guion, resto = nombre.partition("_")
    if guion and resto and _sin_tildes(_norm(cabeza)) in prefijos:
        return resto
    return nombre


# ═════════════════════════════════════════════════════════════════════════════
# Errores pedagógicos (§6.5)
# ═════════════════════════════════════════════════════════════════════════════

# Las etiquetas van literales, con sus puntos suspensivos, tal como el diseño
# fija el formato de la tarjeta. La sangría de continuación (18 espacios) alinea
# bajo el texto de «Por qué».
_ET_QUE = "  Qué pasó ....: "
_ET_POR = "  Por qué ......: "
_ET_ARR = "  Arréglalo ....: "
_SANGRIA = " " * 18


class Error:
    """Un error del catálogo, listo para mostrarse de tres maneras.

    Nunca es una excepción de Python que el estudiante vea: es un dato que
    viaja dentro de `Resultado`. Guarda la línea y la columna para poder pintar
    la fila del código con los circunflejos debajo del pedazo culpable, que es
    lo que convierte «hay un error» en «mira *aquí*».
    """

    def __init__(self, codigo, linea, texto_linea, que_paso, por_que, arreglalo,
                 col=0, largo=0):
        self.codigo = codigo
        self.linea = linea
        self.texto_linea = texto_linea
        self.que_paso = que_paso
        self.por_que = por_que
        self.arreglalo = arreglalo
        self.col = max(0, col)
        self.largo = max(0, largo)

    # -- Presentación --------------------------------------------------------
    @property
    def error_corto(self):
        """Una sola línea, para meter dentro del `assert` de una celda nbgrader."""
        donde = f"línea {self.linea}: " if self.linea else ""
        return f"[{self.codigo}] {donde}{self.que_paso} Arréglalo: {self.arreglalo}"

    def __str__(self):
        partes = [f"✗ Error en la línea {self.linea}" if self.linea
                  else "✗ Error"]
        if self.texto_linea is not None and self.linea:
            partes.append(f"{self.linea:>5} | {self.texto_linea}")
            if self.largo:
                partes.append(" " * (8 + self.col) + "^" * self.largo)
        partes.append(textwrap.fill(self.que_paso, width=94,
                                    initial_indent=_ET_QUE,
                                    subsequent_indent=_SANGRIA))
        partes.append(textwrap.fill(self.por_que, width=94,
                                    initial_indent=_ET_POR,
                                    subsequent_indent=_SANGRIA))
        partes.append(textwrap.fill(self.arreglalo, width=94,
                                    initial_indent=_ET_ARR,
                                    subsequent_indent=_SANGRIA))
        return "\n".join(partes)

    def html(self):
        """Tarjeta con borde rojo. En el autograder nadie la ve; en el aula, sí."""
        codigo_html = ""
        if self.texto_linea is not None and self.linea:
            fila = f"{self.linea:>5} | {self.texto_linea}"
            marca = (" " * (8 + self.col) + "^" * self.largo) if self.largo else ""
            codigo_html = (
                f'<pre style="margin:6px 0;padding:8px 10px;background:#fff;'
                f'border:1px solid #f0d0d0;border-radius:4px;font-size:13px;'
                f'overflow-x:auto">{_escapar(fila)}'
                + (f"\n{_escapar(marca)}" if marca else "") + "</pre>")
        filas = "".join(
            f'<div style="margin:3px 0"><b style="color:{GRIS}">{etq}</b> {txt}</div>'
            for etq, txt in (("Qué pasó", _escapar(self.que_paso)),
                             ("Por qué", _escapar(self.por_que)),
                             ("Arréglalo", f"<code>{_escapar(self.arreglalo)}</code>")))
        return (
            f'<div style="border:1px solid #f0d0d0;border-left:4px solid {ROJO};'
            f'border-radius:6px;padding:12px 14px;margin:8px 0;background:#fdf4f3;'
            f'font-family:system-ui,-apple-system,sans-serif;font-size:14.5px;'
            f'line-height:1.55;color:{TINTA}">'
            f'<div style="font-weight:650;color:{ROJO};margin-bottom:4px">'
            f'Error en la línea {self.linea} <span style="font-weight:400;'
            f'color:{GRIS};font-size:12px">({self.codigo})</span></div>'
            f'{codigo_html}{filas}</div>')


class _Alto(Exception):
    """Señal interna que aborta análisis o ejecución con un `Error` pedagógico.

    Nunca escapa del módulo: `ejecutar_pseudo` la atrapa y la vuelve
    `Resultado(ok=False)`. Es la pieza que sostiene el contrato de robustez.
    """

    def __init__(self, error):
        super().__init__(error.error_corto)
        self.error = error


def _sugerencia(palabra, universo):
    """«¿querías decir…?» con difflib, comparando sin mayúsculas ni tildes."""
    tabla = {_norm(p): p for p in universo}
    cerca = difflib.get_close_matches(_norm(palabra), list(tabla), n=1, cutoff=0.62)
    return tabla[cerca[0]] if cerca else None


# -- Constructores del catálogo, uno por código -------------------------------
# Cada uno reproduce el texto exacto de §6.5 y rellena las partes variables con
# el contexto real. Se escriben como funciones y no como plantillas sueltas para
# que el sitio donde se dispara el error quede legible en el punto de disparo.

def _ps01(nombre, linea, texto, col, vacia=False, conocidas=()):
    if vacia:
        # Decisión: el catálogo no tiene código para «la caja existe pero está
        # vacía», y §8.2 y §12 lo exigen («te va a decir que la caja copias
        # existe pero está vacía»). Se resuelve como variante de PS01 en vez de
        # abrir un decimoquinto código, porque para el estudiante es el mismo
        # problema: la caja todavía no tiene nada que usar.
        return Error(
            "PS01", linea, texto,
            f"usaste '{nombre}' pero esa caja está vacía todavía.",
            "Definir crea la caja, pero no le mete nada. Antes de usar una "
            "variable hay que guardarle un valor con la flecha <- o leerlo con Leer.",
            f"antes de esta línea escribe:  Leer {nombre}   (o  {nombre} <- 0 )",
            col, len(nombre))
    arreglo = f"agrega arriba:  Definir {nombre} Como Entero"
    parecida = _sugerencia(nombre, conocidas)
    if parecida:
        arreglo += f"   ¿O querías decir '{parecida}'?"
    return Error(
        "PS01", linea, texto,
        f"usaste '{nombre}' pero esa caja no existe todavía.",
        "antes de guardar algo en una variable hay que crearla con Definir, y "
        "decir qué tipo de dato va a guardar.",
        arreglo, col, len(nombre))


def _ps02(linea, texto, col, izquierda, derecha):
    return Error(
        "PS02", linea, texto,
        "usaste el signo = para guardar un valor.",
        "en pseudocódigo el = sirve para PREGUNTAR si dos cosas son iguales. "
        "Para GUARDAR se usa la flecha <-, que apunta hacia la caja.",
        f"{izquierda} <- {derecha}".strip(), col, 1)


def _ps03(palabra, linea_apertura, cierre, linea, texto):
    return Error(
        "PS03", linea, texto,
        f"abriste un bloque con '{palabra}' en la línea {linea_apertura} y "
        f"nunca lo cerraste.",
        "todo bloque que se abre se cierra: Algoritmo/FinAlgoritmo, Si/FinSi, "
        "Mientras/FinMientras, Para/FinPara.",
        f"escribe {cierre} después de la última instrucción que quieras "
        + ("repetir." if cierre in ("FinMientras", "FinPara")
           else "meter dentro del bloque."))


def _ps04(linea, texto, nombre, tipo, valor, col=0, largo=0):
    """Tipo incompatible. El «por qué» cambia según qué chocó con qué."""
    desc = _describir_valor(valor)
    if tipo == "Entero" and isinstance(valor, str):
        por_que = (f'una variable Entera solo guarda números sin decimales. '
                   f'"{valor}" es una palabra, aunque signifique un número.')
        arreglo = (f"{nombre} <- 18   (o define {nombre} Como Cadena si de "
                   f"verdad quieres guardar la palabra)")
    elif tipo == "Entero":
        por_que = ("una variable Entera solo guarda números sin decimales. Si "
                   "necesitas decimales, defínela Como Real.")
        arreglo = f"Definir {nombre} Como Real"
    elif tipo == "Real":
        por_que = ("una variable Real guarda números, con decimales o sin ellos. "
                   "Lo que le estás guardando no es un número.")
        arreglo = f"{nombre} <- 3.5   (o define {nombre} Como Cadena)"
    elif tipo == "Cadena":
        por_que = ('una variable Cadena guarda texto, y el texto va entre '
                   'comillas dobles. Sin comillas es un número, y son cosas '
                   'distintas: "3200" no es 3200.')
        arreglo = f'{nombre} <- "{_formatear(valor)}"'
    else:
        por_que = ("una variable Logico solo guarda Verdadero o Falso, que son "
                   "las dos respuestas posibles a una pregunta de sí o no.")
        arreglo = f"{nombre} <- Verdadero"
    return Error(
        "PS04", linea, texto,
        f"intentaste guardar {desc} en '{nombre}', que definiste Como {tipo}.",
        por_que, arreglo, col, largo)


def _ps05(linea, texto, pedidos, dados, consumidas):
    if pedidos > dados:
        cuenta = f"Tu algoritmo tiene {pedidos} Leer y le diste {dados} datos."
    else:
        # Con un Mientras el conteo estático se queda corto: se dice lo que de
        # verdad pasó en esta ejecución.
        cuenta = (f"Tu algoritmo ya consumió los {consumidas} datos que le "
                  f"diste y volvió a pedir otro.")
    return Error(
        "PS05", linea, texto,
        "el algoritmo pidió un dato con Leer, pero ya no quedan entradas.",
        "cuando ejecutas aquí, tú entregas de antemano lo que el usuario iba a "
        "teclear: eso es la lista 'entradas'. " + cuenta,
        'ejecutar_pseudo(codigo, entradas=["40", "2", "..."])')


def _ps06(que_paso, por_que, arreglalo, linea, texto, col=0, largo=0):
    return Error("PS06", linea, texto, que_paso, por_que, arreglalo, col, largo)


def _ps06_no_tengo(clave, linea, texto, col, largo):
    """Una estructura de PSeInt que este motor no implementa (2026-10-05).

    Decisión: sale como PS06 («no sé qué me estás diciendo») y no como PS14,
    porque el problema no es el nombre de ninguna variable. Lo que importa es
    que diga las dos cosas que el alumno necesita: que eso aquí no existe, y qué
    se escribe en su lugar.
    """
    que_es, en_su_lugar = _NO_TENGO[clave]
    return _ps06(
        f"este motor no tiene {que_es}.",
        "es un pseudocódigo pequeño a propósito. Las instrucciones que entiendo "
        "son: " + ", ".join(_INSTRUCCIONES) + ".",
        en_su_lugar, linea, texto, col, largo)


def _ps06_fuera_de_sitio(clave, linea, texto, col, largo):
    que_paso, ejemplo = _FUERA_DE_SITIO[clave]
    return _ps06(
        que_paso,
        "cada palabra clave tiene su sitio fijo en la línea; suelta al "
        "principio no dice nada.",
        ejemplo, linea, texto, col, largo)


def _ps06_fin_suelto(segunda, linea, texto, col, largo):
    """`Fin` seguido de algo que no cierra ningún bloque, o `Fin` a secas."""
    escrito = f"Fin {segunda}" if segunda else "Fin"
    return _ps06(
        f"'{escrito}' no cierra ningún bloque de este motor.",
        "cada bloque tiene su propio cierre, y hay que decir cuál se cierra.",
        "usa FinSi, FinMientras, FinPara o FinAlgoritmo, según lo que hayas "
        "abierto.", linea, texto, col, largo)


def _ps06_sino_si(condicion, linea, texto, col, largo, palabra=""):
    """`Si no Si n = 2 Entonces` (o `Sino Si ...`) en una sola línea.

    `palabra` es para cuando venía en una sola palabra (`SinoSi`, `Elif`): ahí
    no hay «un Sino y otro Si» a la vista, y se nombra lo que el alumno puso.
    """
    return _ps06(
        f"este motor no tiene '{palabra}', que es un Sino y otro Si en la "
        f"misma línea." if palabra else
        "escribiste un Sino y otro Si en la misma línea, y este motor no "
        "tiene el 'Sino Si' pegado.",
        "Sino va solo en su línea. La pregunta nueva es otro Si: se escribe en "
        "la línea de abajo y lleva su propio FinSi.",
        f"Sino   y en la línea de abajo:   Si {condicion or 'n = 2'} Entonces "
        f"... FinSi", linea, texto, col, largo)


def _ps06_para(que_paso, ejemplo, linea, texto, col=0, largo=0):
    """Una cabecera de Para a medio escribir. El «por qué» es siempre el mismo:
    las cuatro cosas que un Para tiene que decir."""
    return _ps06(
        que_paso,
        "la línea del Para dice cuatro cosas, en este orden: qué variable "
        "cuenta, desde qué valor (con la flecha <-), Hasta cuál, y Hacer al "
        "final. 'Con Paso' es opcional: sin él cuenta de uno en uno.",
        ejemplo, linea, texto, col, largo)


def _cierra_un_valor(tok):
    """¿Puede ser este token lo último de una cuenta? (`3`, `n`, `)`, "a")"""
    if tok.tipo == "ident":
        return _norm(tok.valor) not in ("y", "o", "no", "mod")
    return tok.tipo in ("num", "cad") or tok.es_op(")")


def _abre_un_valor(tok):
    """¿Puede ser este token lo primero de una cuenta? (`3`, `n`, `(`, `-`)"""
    return tok.tipo in ("num", "cad", "ident") or tok.es_op("(", "-")


def _forma_de_bloque(toks):
    """(cuenta_hasta, termina_en): si la línea tiene forma de abrir un bloque.

    2026-10-05, tras la revisión. Es lo que separa un nombre partido
    (`edad hasta <- 18`) de una estructura mal abierta (`Desde i <- 1 Hasta 5
    Hacer`), sin depender de qué palabra haya al principio.

    `hasta`, `hacer` y `entonces` también valen como nombres de variable, así
    que no basta con encontrar la palabra: en `total = hasta + 1` es un dato.
    Lo que la delata como palabra de estructura es que tenga un VALOR pegado
    delante —`1 Hasta 5`, `x > 3 Hacer`—, cosa que en una cuenta bien escrita
    no pasa nunca, porque entre dos valores siempre hay un operador. (O, para
    Hasta, que venga justo tras la flecha y con un valor detrás: `i <- Hasta
    5` es un Para sin su valor inicial. El signo menos no cuenta ahí como
    valor, porque `x <- hasta - 1` es una resta.)
    """
    def cuenta(k):
        antes = toks[k - 1]
        despues = toks[k + 1] if k + 1 < len(toks) else None
        if _cierra_un_valor(antes):
            return despues is None or _abre_un_valor(despues)
        return antes.es_op("<-", "=") and despues is not None \
            and _abre_un_valor(despues) and not despues.es_op("-")

    cuenta_hasta = any(toks[k].es("Hasta") and cuenta(k)
                       for k in range(2, len(toks)))
    termina_en = ""
    if len(toks) >= 2 and _cierra_un_valor(toks[-2]):
        termina_en = "entonces" if toks[-1].es("Entonces") else \
            "hacer" if toks[-1].es("Hacer") else ""
    return cuenta_hasta, termina_en


_EJEMPLO_PARA = "Para i <- 1 Hasta 10 Hacer"


def _la_cuenta(toks):
    """El árbol de `toks` si, ENTEROS, se analizan como una sola cuenta; si no,
    None.

    2026-10-05, segunda revisión. Es lo que decide si algo que escribió el
    alumno se puede copiar dentro de un «Arréglalo». Antes se copiaba sin
    mirar, y el motor volvía a aconsejar líneas que tampoco corren: `Para i <=
    n Hacer` recibía «Arréglalo: Para i <- <= n Hacer», y `Para i <- 1 a 3
    Hacer`, «Para i <- 1 a 3 Hasta 10 Hacer». Es la misma clase de fallo que el
    «Arréglalo: Para_i» que un alumno obedeció al pie de la letra.

    Se usa el analizador de verdad, no una aproximación: sus métodos de
    expresión no guardan estado, así que uno vacío basta. Ante cualquier duda
    (lista vacía, error, tokens que sobran) la respuesta es que no.
    """
    if not toks:
        return None
    # Una palabra del lenguaje (Entonces, Hacer, FinSi...) nunca forma parte
    # de una cuenta que se vaya a PROPONER: el analizador las admitiría como
    # nombres de variable, y saldría «Mientras i < Entonces Hacer».
    if any(t.tipo == "ident" and _norm(t.valor) in _DE_ESTRUCTURA for t in toks):
        return None
    try:
        arbol, sobra = _Analizador("")._expresion(list(toks), toks[0].linea, "")
    except Exception:
        return None
    return None if sobra else arbol


def _la_pregunta(toks):
    """El texto de `toks` si son UNA pregunta de verdad —una comparación, un
    Y/O o un NO— y se pueden proponer dentro de un `Si … Entonces` o un
    `Mientras … Hacer`; si no, "". Una cuenta a secas (`n - 1`) se analiza
    pero no es una pregunta, y proponer «Mientras n - 1 Hacer» tampoco sirve
    (tercera revisión, 2026-10-05)."""
    arbol = _la_cuenta(toks)
    es = isinstance(arbol, _Bin) and arbol.op in ("=", "<>", "<", "<=", ">",
                                                   ">=", "Y", "O")
    es = es or (isinstance(arbol, _Un) and arbol.op == "NO")
    return _tokens_a_texto(toks) if es else ""


def _para_que_corre(variable, ini=None, fin=None, paso=None, paso_defecto=None):
    """Una cabecera de Para que SIEMPRE se analiza.

    Cada una de las tres cuentas se copia del alumno solo si es una cuenta de
    verdad (`_la_cuenta`); la que no, se sustituye por la del ejemplo de siempre
    (1, 10 y, si se pidió paso, `paso_defecto`). Un paso 0 escrito a la vista
    tampoco se copia: el motor lo rechaza antes de ejecutar.
    """
    def o(toks, defecto):
        return _tokens_a_texto(toks) if _la_cuenta(toks) is not None else defecto

    linea = f"Para {variable} <- {o(ini, '1')} Hasta {o(fin, '10')}"
    if paso is not None or paso_defecto is not None:
        arbol = _la_cuenta(paso)
        cero = isinstance(arbol, _Lit) and _numeros(arbol.valor) \
            and arbol.valor == 0
        valor = paso_defecto if (arbol is None or cero) \
            else _tokens_a_texto(paso)
        if valor:
            linea += f" Con Paso {valor}"
    return linea + " Hacer"


def _partes_de_para(resto):
    """Lo que hay tras la flecha de un Para, partido en (ini, fin, paso) por
    `Hasta` y por la pareja `Con Paso`. None si no hay ningún Hasta. La última
    palabra, si es Hacer o Entonces, no cuenta."""
    medio = list(resto)
    if medio and (medio[-1].es("Hacer") or medio[-1].es("Entonces")):
        medio = medio[:-1]
    corte = next((k for k, t in enumerate(medio) if t.es("Hasta")), None)
    if corte is None:
        return None
    ini, cola = medio[:corte], medio[corte + 1:]
    con = next((k for k in range(len(cola) - 1)
                if cola[k].es("Con") and cola[k + 1].es("Paso")), None)
    if con is None:
        return ini, cola, None
    return ini, cola[:con], cola[con + 2:]


def _cabecera_de_para(variable, resto, valor_suelto=False):
    """La cabecera de Para que se puede armar con lo que el alumno escribió
    después de la variable, o None si no hay nada aprovechable.

    Aprovechable es: un `Hasta` con una cuenta válida a algún lado; dos cuentas
    separadas por `a` o por una coma (`1 a n`, `1, n`: en este lenguaje se dice
    Hasta); o, con `valor_suelto`, una sola cuenta, que hace de valor inicial.
    Eso último solo vale cuando la flecha SÍ estaba: en `Para n veces Hacer`
    lo que sigue a la variable no es un valor inicial y no se toma por tal.
    """
    resto = list(resto)
    if resto and (resto[0].es("Desde") or resto[0].es("De")):
        # `Para i de 1 a n`, `Ciclo i desde 1 hasta n`: el «de» sobra.
        resto = resto[1:]
    partes = _partes_de_para(resto)
    if partes is not None:
        ini, fin, paso = partes
        if _la_cuenta(ini) is None and _la_cuenta(fin) is None:
            return None
        return _para_que_corre(variable, ini, fin, paso)
    medio = resto
    if medio and (medio[-1].es("Hacer") or medio[-1].es("Entonces")):
        medio = medio[:-1]
    for k, t in enumerate(medio):
        if (t.es("a") or t.es_op(",")) and _la_cuenta(medio[:k]) is not None \
                and _la_cuenta(medio[k + 1:]) is not None:
            return _para_que_corre(variable, medio[:k], medio[k + 1:])
    if valor_suelto and _la_cuenta(medio) is not None:
        return _para_que_corre(variable, medio)
    return None


def _para_corregido(variable, resto):
    """La cabecera `Para <variable> <- <resto>`, con lo que el alumno escribió
    después de la flecha (y con su Hacer al final, si no lo traía). Solo si
    `resto` tiene de verdad una cuenta, Hasta y otra cuenta; si no, el ejemplo
    de siempre: nunca se propone una línea que no tenga la forma de un Para.

    (2026-10-05, segunda revisión: «de verdad» se comprueba ahora analizando
    las dos cuentas; antes bastaba con que hubiera un Hasta en medio, y
    `- > 1 Hasta n` pasaba.)"""
    partes = _partes_de_para(resto)
    if partes is None or _la_cuenta(partes[0]) is None \
            or _la_cuenta(partes[1]) is None:
        return _EJEMPLO_PARA
    return _para_que_corre(variable, *partes)


def _ps06_forma_de_bloque(toks, cuenta_hasta, linea, texto):
    """Una línea que abre un bloque con una palabra que el motor no conoce.

    2026-10-05, tras la revisión. `Desde i <- 1 Hasta 5 Hacer`, `Ciclo x > 3
    Hacer` o `Elif n = 2 Entonces` empiezan por dos palabras seguidas, y eso
    bastaba para tomarlas por un nombre con espacio: «Arréglalo: Elif_n». La
    tabla `_NO_TENGO` ataja las palabras que se conocen de antemano, pero una
    lista nunca está completa. Aquí se decide por la FORMA de la línea: la que
    termina en Entonces o en Hacer, o cuenta Hasta un valor, no es un nombre de
    variable, empiece por la palabra que empiece.
    """
    cabeza = toks[0]
    intrusa = (f"empieza por '{cabeza.valor}', que no es una instrucción de "
               f"este motor")
    con_flecha = any(t.es_op("<-") for t in toks)
    if cuenta_hasta or (con_flecha and toks[-1].es("Hacer")):
        # Con una flecha y un Hacer, aunque no se vea el Hasta, lo que se quiso
        # abrir es un ciclo que cuenta: se enseña el Para, no un Mientras con
        # una flecha dentro de la pregunta.
        if not cuenta_hasta:
            return _ps06_para(
                f"esta línea termina en Hacer y guarda un valor con la "
                f"flecha, como un ciclo Para, pero {intrusa}.",
                "Para i <- 1 Hasta 10 Hacer", linea, texto, cabeza.col,
                len(cabeza.valor))
        ejemplo = "Para i <- 1 Hasta 10 Hacer"
        if len(toks) >= 3 and toks[1].tipo == "ident" \
                and toks[2].es_op("<-", "="):
            ejemplo = _para_corregido(toks[1].valor, toks[3:])
        return _ps06_para(
            f"esta línea cuenta 'Hasta' un valor, como un ciclo Para, pero "
            f"{intrusa}.", ejemplo, linea, texto, cabeza.col,
            len(cabeza.valor))
    # Lo que hay en medio se repite como pregunta solo si puede serlo: con una
    # flecha dentro no lo es, y se pone el ejemplo de siempre.
    # Lo que hay en medio se repite como pregunta solo si de verdad es una
    # cuenta (tercera revisión: `For i = 1 to n Hacer` proponía «Mientras i =
    # 1 to n Hacer», que tampoco corre). Y si lo de en medio tiene la forma de
    # una cuenta con `de … a …`, lo que quiso abrir es un Para.
    pregunta = "" if con_flecha else _la_pregunta(toks[1:-1])
    if not pregunta and toks[-1].es("Hacer") and len(toks) >= 3 \
            and toks[1].tipo == "ident":
        como_para = _cabecera_de_para(toks[1].valor, toks[2:])
        if como_para:
            return _ps06_para(
                f"esta línea termina en Hacer y cuenta de un valor a otro, "
                f"como un ciclo Para, pero {intrusa}.",
                como_para, linea, texto, cabeza.col, len(cabeza.valor))
    pregunta = pregunta or "saldo > 0"
    if toks[-1].es("Entonces"):
        return _ps06(
            f"esta línea termina en Entonces, como la de un Si, pero "
            f"{intrusa}.",
            "las preguntas se abren con Si y se cierran con FinSi; para el "
            "otro caso está Sino, solo en su línea. No hay más formas que "
            "esas.",
            f"Si {pregunta} Entonces ... FinSi   (si es el otro caso de un Si "
            f"de arriba: Sino solo en su línea, y este Si en la de abajo)",
            linea, texto, cabeza.col, len(cabeza.valor))
    return _ps06(
        f"esta línea termina en Hacer, como la de un ciclo, pero {intrusa}.",
        "este motor tiene dos ciclos: Mientras <pregunta> Hacer ... "
        "FinMientras, y Para <variable> <- <inicio> Hasta <fin> Hacer ... "
        "FinPara.",
        f"Mientras {pregunta} Hacer", linea, texto, cabeza.col,
        len(cabeza.valor))


def _ps06_falta_la_apertura(toks, cuenta_hasta, linea, texto):
    """`n = 2 Entonces`, `x = 3 Hacer`, `i = 3 Hasta n Hacer`: un Si, un
    Mientras o un Para al que le falta su primera palabra.

    2026-10-05, tras la revisión. Empiezan por `<nombre> =`, y eso bastaba para
    contestar PS02 con un arreglo que tampoco corre: «n <- 2 Entonces». Es
    además donde aterrizaba quien había obedecido el consejo viejo de PS14
    (`SinoSi_n = 2 Entonces`), y de ahí los prefijos que se desandan.
    """
    cabeza = toks[0]
    # Con una flecha más adelante la línea no se puede repetir como pregunta:
    # se deja el valor de ejemplo.
    derecha = [] if any(t.es_op("<-") for t in toks) else toks[2:-1]
    # (Tercera revisión: `i = to n Hacer` proponía «Mientras i = to n Hacer».
    # Lo de la derecha del = solo se repite si es una cuenta.)
    if _la_cuenta(derecha) is None:
        derecha = []
    if cuenta_hasta:
        return _ps06_para(
            "esta línea cuenta 'Hasta' un valor, como un ciclo Para, pero no "
            "empieza por la palabra Para.",
            _para_corregido(_sin_prefijo(cabeza.valor, _ABREN_UN_CICLO),
                            toks[2:]),
            linea, texto, cabeza.col, len(cabeza.valor))
    if toks[-1].es("Entonces"):
        variable = _sin_prefijo(cabeza.valor, _ABREN_UN_SINO_SI)
        pregunta = f"{variable} = {_tokens_a_texto(derecha) or '2'}"
        if variable != cabeza.valor:
            return _ps06_sino_si(pregunta, linea, texto, cabeza.col,
                                 len(cabeza.valor),
                                 palabra=cabeza.valor.partition("_")[0])
        return _ps06(
            "a esta línea le falta la palabra Si al principio.",
            "una línea que termina en Entonces es una pregunta, y las "
            "preguntas se abren con Si. (Aquí el = está bien: pregunta si las "
            "dos cosas son iguales.)",
            f"Si {pregunta} Entonces", linea, texto, cabeza.col,
            len(cabeza.valor))
    return _ps06(
        "a esta línea le falta la palabra Mientras al principio.",
        "una línea que termina en Hacer abre un ciclo, y el ciclo que repite "
        "mientras una pregunta sea cierta se abre con Mientras.",
        f"Mientras {cabeza.valor} = {_tokens_a_texto(derecha) or '0'} Hacer",
        linea, texto, cabeza.col, len(cabeza.valor))


def _ps06_instruccion(palabra, linea, texto, col):
    parecida = _sugerencia(palabra, _PALABRAS_CLAVE)
    return _ps06(
        f"no conozco la instrucción '{palabra}'.",
        "las instrucciones que entiendo son: " + ", ".join(_INSTRUCCIONES) + ".",
        f"¿querías decir {parecida}?" if parecida else
        "revisa la lista de arriba y escribe una de esas.",
        linea, texto, col, len(palabra))


def _ps07(linea, texto, col):
    return Error(
        "PS07", linea, texto,
        f"abriste unas comillas en la línea {linea} y no las cerraste.",
        "todo texto va entre comillas dobles, de principio a fin. Si falta una, "
        "no sé dónde termina la frase.",
        'Escribir "Total a pagar: $", total', col, 1)


def _ps08(linea, texto, nombre, col=0, largo=0):
    if nombre:
        detalle = f"La variable '{nombre}' vale 0 en este momento."
        arreglo = (f"revisa la prueba de escritorio: ¿en qué paso '{nombre}' se "
                   f"volvió 0?")
    else:
        detalle = "Lo que pusiste como divisor vale 0 en este momento."
        arreglo = ("revisa la prueba de escritorio: ¿en qué paso el divisor se "
                   "volvió 0?")
    return Error(
        "PS08", linea, texto,
        "intentaste dividir entre cero.",
        "dividir entre cero no tiene resultado; ni en matemáticas ni en el "
        "computador. " + detalle,
        arreglo, col, largo)


def _ps09(linea, texto, ciclo="Mientras"):
    if ciclo == "Para":
        # 2026-10-05: hablarle de «la condición del Mientras» a quien escribió
        # un Para sería mandarlo a buscar una línea que no existe.
        return Error(
            "PS09", linea, texto,
            "tu algoritmo lleva 10 000 pasos y no termina: probablemente es un "
            "ciclo infinito.",
            "un Para termina cuando su variable pasa del valor final. Este da "
            "demasiadas vueltas, o algo dentro del ciclo le devuelve el valor a "
            "la variable que cuenta.",
            "revisa hasta dónde cuenta el Para, y no le cambies el valor a su "
            "variable dentro del ciclo.")
    return Error(
        "PS09", linea, texto,
        "tu algoritmo lleva 10 000 pasos y no termina: probablemente es un "
        "ciclo infinito.",
        "la condición del Mientras nunca se vuelve falsa porque nada dentro del "
        "ciclo la cambia.",
        "asegúrate de que alguna variable de la condición cambie dentro del ciclo.")


def _ps09_paso_cero(variable, linea, texto, col=0, largo=0):
    """Decisión (2026-10-05): `Con Paso 0` es PS09 y no un código nuevo. Es un
    ciclo infinito visto antes de dar la primera vuelta, y así el alumno no
    tiene que esperar a los 10 000 pasos para enterarse."""
    return Error(
        "PS09", linea, texto,
        f"el paso de este Para vale 0: la variable '{variable}' no avanzaría "
        f"nunca y el ciclo no terminaría.",
        "el paso es lo que se le suma a la variable en cada vuelta. Sumarle 0 "
        "la deja donde estaba, así que jamás llega al valor final.",
        "Con Paso 1 para contar hacia arriba, o Con Paso -1 para contar hacia "
        "abajo.", col, largo)


def _ps10(palabra, falta, linea, texto):
    if falta == "Entonces":
        por_que = ("la palabra Entonces marca dónde termina la pregunta y dónde "
                   "empieza lo que se hace si la respuesta es sí.")
        arreglo = "Si saldo > 0 Entonces"
    elif _norm(palabra) == "para":
        por_que = ("la palabra Hacer marca dónde termina la cuenta del Para y "
                   "dónde empieza lo que se repite en cada vuelta.")
        arreglo = "Para i <- 1 Hasta 10 Hacer"
    else:
        por_que = ("la palabra Hacer marca dónde termina la pregunta y dónde "
                   "empieza lo que se repite mientras la respuesta sea sí.")
        arreglo = "Mientras saldo > 0 Hacer"
    return Error(
        "PS10", linea, texto,
        f"escribiste '{palabra}' pero falta la palabra {falta} al final de la línea.",
        por_que, arreglo)


def _ps11(nombre, linea, texto, col):
    return Error(
        "PS11", linea, texto,
        f"intentaste cambiar {nombre}, que declaraste como Constante.",
        "una constante es un dato que NO cambia durante todo el algoritmo: por "
        "eso se declara aparte y en MAYÚSCULAS.",
        "si necesitas que cambie, decláralo con Definir en vez de Constante.",
        col, len(nombre))


def _ps12(abiertos, cerrados, linea, texto):
    return Error(
        "PS12", linea, texto,
        f"abriste {abiertos} paréntesis y cerraste {cerrados}.",
        "cada ( necesita su ).",
        "total <- (copias * PRECIO) + ANILLADO")


def _ps13(linea, texto):
    return Error(
        "PS13", linea, texto,
        "tu programa no empieza con la línea 'Algoritmo <nombre>'.",
        "esa línea le pone nombre a lo que estás resolviendo. En el diagrama de "
        "flujo es el óvalo de INICIO.",
        "escribe arriba de todo:  Algoritmo MiPrimerAlgoritmo")


def _ps14(nombre, linea, texto, col, o_bien=""):
    """`o_bien` añade la otra lectura posible del mismo descuido (2026-10-05):
    `Leer a b` casi nunca es una variable llamada «a b», son dos variables a
    las que les falta la coma, y aconsejar solo `a_b` sería mandar al alumno a
    un error distinto."""
    # Red de seguridad (2026-10-05): si alguna de las «mitades» del nombre es
    # una palabra de estructura, unirlas con guion bajo no es el arreglo. Los
    # casos conocidos se atajan antes de llegar aquí, con su mensaje propio;
    # esto garantiza que, llegue por donde llegue, PS14 no vuelva a aconsejar un
    # `Para_i` ni un `total_Entonces`.
    #
    # Revisión del mismo día: la red miraba TODAS las palabras del lenguaje, y
    # con eso `numero entero <- 5` y `Leer hora fin` perdían su arreglo
    # (`numero_entero`, `hora_fin`) a cambio de una afirmación falsa. Ahora solo
    # mira las de estructura (ver `_DE_ESTRUCTURA`), y el texto ya no promete
    # nada que el motor no cumpla.
    reservada = next((p for p in nombre.split()
                      if _norm(p) in _DE_ESTRUCTURA), None)
    if reservada and " " in nombre:
        return Error(
            "PS14", linea, texto,
            f"'{nombre}' no sirve como nombre de variable.",
            f"'{reservada}' es una palabra con la que este lenguaje arma sus "
            f"instrucciones, y aquí quedó donde iba el nombre de una variable.",
            "revisa esa línea: va una sola instrucción por línea, y cada "
            "palabra del lenguaje en su sitio.",
            col, len(nombre))
    sano = _RE_ACENTO.sub(lambda m: _SIN_TILDE.get(m.group(), m.group()),
                          nombre).replace(" ", "_")
    return Error(
        "PS14", linea, texto,
        f"'{nombre}' no sirve como nombre de variable.",
        "los nombres van sin espacios y sin tildes. La costumbre es unir las "
        "palabras con guion bajo.",
        sano + (f"   ({o_bien})" if o_bien else ""), col, len(nombre))


_SIN_TILDE = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u",
              "ñ": "n", "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
              "Ü": "U", "Ñ": "N"}


def _err_motor(exc):
    """Red de seguridad: un fallo del propio motor tampoco sale como traceback.

    Decisión: se le da el código PS00, que no está en el catálogo, justamente
    para distinguirlo de los errores del estudiante. Si alguna vez aparece, la
    culpa es nuestra y el texto lo dice.
    """
    return Error(
        "PS00", 1, None,
        "el motor no pudo terminar de procesar tu algoritmo.",
        f"esto es una falla del motor del cuadernillo, no tuya "
        f"({type(exc).__name__}: {exc}).",
        "avísale a tu docente. Mientras tanto, prueba a simplificar la última "
        "línea que escribiste y vuelve a ejecutar.")


def _describir_valor(valor):
    """«el texto "x"», «el número 3.5», «el valor Verdadero» — para PS04."""
    if isinstance(valor, bool):
        return f"el valor {'Verdadero' if valor else 'Falso'}"
    if isinstance(valor, str):
        return f'el texto "{valor}"'
    return f"el número {_formatear(valor)}"


def _formatear(valor):
    """Cómo se ve un valor en la salida y en la tabla de memoria.

    Decisión: los booleanos se muestran en español (Verdadero/Falso) porque el
    alumno los escribió en español; los reales conservan la forma de Python
    (5.0 sigue siendo 5.0) porque §6.4 enseña justamente esa correspondencia y
    esconder el .0 arruinaría la lección de «/ siempre da decimales».
    """
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "Verdadero" if valor else "Falso"
    return str(valor)


# ═════════════════════════════════════════════════════════════════════════════
# Tokenizador
# ═════════════════════════════════════════════════════════════════════════════

class _Token:
    """Un pedazo indivisible de una línea, con su columna para los circunflejos."""

    __slots__ = ("tipo", "valor", "linea", "col")

    def __init__(self, tipo, valor, linea, col):
        self.tipo = tipo        # "num" | "cad" | "ident" | "op"
        self.valor = valor
        self.linea = linea
        self.col = col

    @property
    def largo(self):
        # La cadena perdió sus comillas al tokenizarse; se le devuelven las dos
        # para que la marca de error cubra lo que el estudiante ve escrito.
        return len(str(self.valor)) + (2 if self.tipo == "cad" else 0)

    def es(self, palabra):
        return self.tipo == "ident" and _norm(self.valor) == _norm(palabra)

    def es_op(self, *simbolos):
        return self.tipo == "op" and self.valor in simbolos

    def __repr__(self):  # pragma: no cover - solo para depurar
        return f"<{self.tipo} {self.valor!r} L{self.linea}C{self.col}>"


def _partir_comentario(texto):
    """Separa código y comentario `//`, respetando lo que va entre comillas."""
    dentro = False
    for i, c in enumerate(texto):
        if c == '"':
            dentro = not dentro
        elif not dentro and c == "/" and texto.startswith("//", i):
            return texto[:i], texto[i + 2:]
    return texto, None


def _tokenizar_linea(texto, nlinea):
    codigo, _ = _partir_comentario(texto)
    toks, i, n = [], 0, len(codigo)
    while i < n:
        c = codigo[i]
        if c in " \t":
            i += 1
            continue
        if c == '"':
            fin = codigo.find('"', i + 1)
            if fin == -1:
                raise _Alto(_ps07(nlinea, texto, i))
            toks.append(_Token("cad", codigo[i + 1:fin], nlinea, i))
            i = fin + 1
            continue
        m = _RE_NUM.match(codigo, i)
        if m:
            crudo = m.group()
            valor = float(crudo) if "." in crudo else int(crudo)
            toks.append(_Token("num", valor, nlinea, i))
            i = m.end()
            continue
        m = _RE_IDENT.match(codigo, i)
        if m:
            toks.append(_Token("ident", m.group(), nlinea, i))
            i = m.end()
            continue
        for op in _OPS2:
            if codigo.startswith(op, i):
                toks.append(_Token("op", op, nlinea, i))
                i += len(op)
                break
        else:
            if c in _OPS1:
                toks.append(_Token("op", c, nlinea, i))
                i += 1
                continue
            # Decisión: un símbolo desconocido se cuenta como PS06. El catálogo
            # habla de «palabra clave desconocida», y esto es el mismo apuro
            # («no sé qué me estás diciendo»); abrir un código nuevo por un
            # punto y coma sería multiplicar el catálogo sin ganancia.
            raise _Alto(_ps06(
                f"no conozco el símbolo '{c}'.",
                "los símbolos que entiendo son  +  -  *  /  ^  (  )  ,  "
                "y para comparar  =  <>  <  <=  >  >= , además de la flecha <-.",
                "bórralo. Si querías escribir un texto, ponlo entre comillas dobles.",
                nlinea, texto, i, 1))
    return toks


# ═════════════════════════════════════════════════════════════════════════════
# Árbol de sintaxis
# ═════════════════════════════════════════════════════════════════════════════
# Las sentencias guardan el texto original de su línea y los tokens de sus
# expresiones. Con eso el trazador puede escribir «40 * 100 + 2500 = 6500»
# respetando los paréntesis y los espacios que puso el estudiante, en vez de
# reimprimir una versión canónica que él no reconocería como suya.

class _Nodo:
    __slots__ = ()


class _Algoritmo(_Nodo):
    __slots__ = ("nombre", "cuerpo", "linea", "linea_fin", "texto", "id_nodo",
                 "id_fin")

    def __init__(self, nombre, cuerpo, linea, linea_fin, texto):
        self.nombre, self.cuerpo = nombre, cuerpo
        self.linea, self.linea_fin, self.texto = linea, linea_fin, texto
        self.id_nodo = self.id_fin = 0


class _Definir(_Nodo):
    __slots__ = ("nombres", "tipo", "linea", "texto", "id_nodo")

    def __init__(self, nombres, tipo, linea, texto):
        self.nombres, self.tipo = nombres, tipo
        self.linea, self.texto, self.id_nodo = linea, texto, 0


class _Constante(_Nodo):
    __slots__ = ("nombre", "expr", "toks", "linea", "texto", "id_nodo", "col")

    def __init__(self, nombre, expr, toks, linea, texto, col):
        self.nombre, self.expr, self.toks = nombre, expr, toks
        self.linea, self.texto, self.col, self.id_nodo = linea, texto, col, 0


class _Asignar(_Nodo):
    __slots__ = ("nombre", "expr", "toks", "linea", "texto", "id_nodo", "col")

    def __init__(self, nombre, expr, toks, linea, texto, col):
        self.nombre, self.expr, self.toks = nombre, expr, toks
        self.linea, self.texto, self.col, self.id_nodo = linea, texto, col, 0


class _Leer(_Nodo):
    __slots__ = ("nombres", "cols", "linea", "texto", "id_nodo")

    def __init__(self, nombres, cols, linea, texto):
        self.nombres, self.cols = nombres, cols
        self.linea, self.texto, self.id_nodo = linea, texto, 0


class _Escribir(_Nodo):
    __slots__ = ("partes", "sin_saltar", "linea", "texto", "id_nodo")

    def __init__(self, partes, sin_saltar, linea, texto):
        self.partes = partes           # [(expr, tokens), ...]
        self.sin_saltar = sin_saltar
        self.linea, self.texto, self.id_nodo = linea, texto, 0


class _Si(_Nodo):
    __slots__ = ("cond", "toks", "entonces", "sino", "linea", "linea_sino",
                 "linea_fin", "texto", "id_nodo", "id_union")

    def __init__(self, cond, toks, entonces, sino, linea, linea_sino, linea_fin,
                 texto):
        self.cond, self.toks = cond, toks
        self.entonces, self.sino = entonces, sino
        self.linea, self.linea_sino, self.linea_fin = linea, linea_sino, linea_fin
        self.texto, self.id_nodo, self.id_union = texto, 0, 0


class _Mientras(_Nodo):
    __slots__ = ("cond", "toks", "cuerpo", "linea", "linea_fin", "texto", "id_nodo")

    def __init__(self, cond, toks, cuerpo, linea, linea_fin, texto):
        self.cond, self.toks, self.cuerpo = cond, toks, cuerpo
        self.linea, self.linea_fin, self.texto = linea, linea_fin, texto
        self.id_nodo = 0


class _Para(_Nodo):
    """`Para <var> <- <ini> Hasta <fin> [Con Paso <p>] Hacer ... FinPara`.

    Decisión (2026-10-05): nodo propio, y no «azúcar» que el analizador
    deshaga en asignación + Mientras + incremento. Deshacerlo era menos código,
    pero el traductor a Python va línea a línea (la línea n del pseudocódigo es
    la línea n del Python) y tres sentencias nacidas de una sola línea no tienen
    dónde ponerse; además el alumno vería en la traza y en los errores un
    `Mientras` que él nunca escribió. Con nodo propio, cada consumidor del árbol
    decide cómo lo muestra: el intérprete y el diagrama lo abren en sus tres
    piezas (inicialización, pregunta, incremento) y el traductor lo deja en una
    sola línea, `for ... in range(...)`.

    Por eso lleva TRES ids de diagrama: `id_nodo` es la caja de inicialización,
    `id_cond` el rombo e `id_inc` la caja del incremento.
    """

    __slots__ = ("var", "col", "ini", "toks_ini", "fin", "toks_fin", "paso",
                 "toks_paso", "cuerpo", "linea", "linea_fin", "texto",
                 "texto_fin", "id_nodo", "id_cond", "id_inc")

    def __init__(self, var, col, ini, toks_ini, fin, toks_fin, paso, toks_paso,
                 cuerpo, linea, linea_fin, texto, texto_fin):
        self.var, self.col = var, col
        self.ini, self.toks_ini = ini, toks_ini
        self.fin, self.toks_fin = fin, toks_fin
        self.paso, self.toks_paso = paso, toks_paso     # None: de uno en uno
        self.cuerpo = cuerpo
        self.linea, self.linea_fin = linea, linea_fin
        self.texto, self.texto_fin = texto, texto_fin
        self.id_nodo = self.id_cond = self.id_inc = 0


def _paso_fijo(st):
    """El paso de un Para cuando se sabe sin ejecutar; None si no se sabe.

    Lo necesitan los tres que muestran el Para sin correrlo (diagrama, traductor
    y puente a Flowgorithm) para saber si el ciclo sube (`<=`) o baja (`>=`).
    Se sabe cuando no hay `Con Paso` (vale 1) o cuando es un número escrito a la
    vista; si es una cuenta (`Con Paso salto`), solo se sabe al ejecutar.
    """
    expr, signo = st.paso, 1
    if expr is None:
        return 1
    if isinstance(expr, _Un) and expr.op == "-":
        expr, signo = expr.expr, -1
    if isinstance(expr, _Lit) and _numeros(expr.valor) and expr.valor != 0:
        return signo * expr.valor
    return None


def _textos_del_para(st, a_texto):
    """(inicialización, pregunta, incremento) tal como se leen en el diagrama.

    Es el Para «abierto» en las tres piezas que el alumno dibujaría a mano. La
    pregunta se escribe con el operador de verdad cuando se sabe hacia dónde
    cuenta; si el paso es una cuenta, se dice en palabras para no mentir.
    """
    ini, fin = a_texto(st.toks_ini), a_texto(st.toks_fin)
    paso = _paso_fijo(st)
    if paso is None:
        cuanto = a_texto(st.toks_paso)
        if len(st.toks_paso) > 1:
            cuanto = f"({cuanto})"
        return ini, f"{st.var} no pasó de {fin}", f"{st.var} + {cuanto}"
    return (ini, f"{st.var} {'<=' if paso > 0 else '>='} {fin}",
            f"{st.var} {'+' if paso > 0 else '-'} {_formatear(abs(paso))}")


# -- Expresiones --------------------------------------------------------------
class _Lit(_Nodo):
    __slots__ = ("valor", "tok")

    def __init__(self, valor, tok):
        self.valor, self.tok = valor, tok


class _Var(_Nodo):
    __slots__ = ("nombre", "tok")

    def __init__(self, nombre, tok):
        self.nombre, self.tok = nombre, tok


class _Bin(_Nodo):
    __slots__ = ("op", "izq", "der", "tok")

    def __init__(self, op, izq, der, tok):
        self.op, self.izq, self.der, self.tok = op, izq, der, tok


class _Un(_Nodo):
    __slots__ = ("op", "expr", "tok")

    def __init__(self, op, expr, tok):
        self.op, self.expr, self.tok = op, expr, tok


class _Llamada(_Nodo):
    __slots__ = ("funcion", "arg", "tok")

    def __init__(self, funcion, arg, tok):
        self.funcion, self.arg, self.tok = funcion, arg, tok


# ═════════════════════════════════════════════════════════════════════════════
# Analizador
# ═════════════════════════════════════════════════════════════════════════════

_CIERRES = {"finsi", "sino", "finmientras", "finpara", "finalgoritmo",
            "finproceso"}
# 2026-10-05: `Proceso <nombre> ... FinProceso` es la otra forma que PSeInt da
# para lo mismo, y hay alumnos que la traen aprendida así. Entra como sinónimo.
# Se aceptan también cruzados —`Algoritmo` cerrado con `FinProceso`—: no enseña
# nada castigar eso.
_FIN_DE_PROGRAMA = ("finalgoritmo", "finproceso")


def _juntar_dos_palabras(toks):
    """`Fin Si` -> `FinSi`, y la línea que es solo `Si no` -> `Sino`.

    2026-10-05. Se hace sobre los tokens de la línea, recién tokenizada, y no
    en cada sitio que mira un cierre: así el resto del analizador sigue viendo
    una sola palabra y no hay un segundo camino que mantener.

    Ojo con el `Si no`: solo cuando la línea es EXACTAMENTE esas dos palabras.
    `Si no encontrado Entonces` es un Si legítimo cuya pregunta empieza por NO,
    y convertirlo en un Sino cambiaría lo que hace el programa sin avisar.
    """
    if len(toks) < 2 or toks[0].tipo != "ident" or toks[1].tipo != "ident":
        return toks
    una, otra = _norm(toks[0].valor), _norm(toks[1].valor)
    if una == "fin" and otra in _SE_CIERRA_CON_FIN:
        junto = _Token("ident", toks[0].valor + toks[1].valor,
                       toks[0].linea, toks[0].col)
        return [junto] + toks[2:]
    if una == "si" and otra == "no" and len(toks) == 2:
        return [_Token("ident", "Sino", toks[0].linea, toks[0].col)]
    return toks


class _Analizador:
    """Recursivo descendente y orientado a línea, como manda la gramática §6.2.

    Cada sentencia ocupa una línea completa (la gramática las termina con NL),
    así que el análisis se hace sobre listas de tokens por línea. Eso simplifica
    el código y, sobre todo, permite que todo error tenga una línea concreta que
    señalar, que es lo que el estudiante necesita.
    """

    def __init__(self, codigo):
        if not isinstance(codigo, str):
            raise _Alto(Error(
                "PS13", 1, None,
                "lo que le pasaste al motor no es pseudocódigo, es un "
                f"{type(codigo).__name__}.",
                "el pseudocódigo se escribe como texto, entre comillas triples.",
                'ejecutar_pseudo("""Algoritmo MiAlgoritmo\\n...\\nFinAlgoritmo""")'))
        self.fuente = codigo.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        self.lineas = []     # [(n, texto, tokens)]
        self.i = 0
        self.cabecera = "Algoritmo"     # o "Proceso", según lo que escribió

    # -- utilidades ---------------------------------------------------------
    def _preparar(self):
        # 2026-10-05: una línea que no se puede tokenizar ya no tumba el
        # análisis aquí; su error se guarda y se da cuando el analizador LLEGA a
        # esa línea (ver `_actual`). Así los errores salen en el orden en que el
        # alumno lee su programa. Antes, un `1:` de un Segun en la línea 9
        # tapaba con «no conozco el símbolo ':'» el mensaje de la línea 8, que
        # es el que sirve: «este motor no tiene Segun».
        for n, texto in enumerate(self.fuente, start=1):
            try:
                toks = _juntar_dos_palabras(_tokenizar_linea(texto, n))
            except _Alto as alto:
                toks = alto
            self.lineas.append((n, texto, toks))

    def _actual(self):
        if self.i >= len(self.lineas):
            return None
        if isinstance(self.lineas[self.i][2], _Alto):
            raise self.lineas[self.i][2]
        return self.lineas[self.i]

    def _saltar_vacias(self):
        while self.i < len(self.lineas) and not self.lineas[self.i][2]:
            self.i += 1

    # -- programa -----------------------------------------------------------
    def analizar(self):
        # La cabecera se comprueba sobre el texto crudo y ANTES de tokenizar:
        # si el programa no arranca con Algoritmo, ese es el error que hay que
        # dar, aunque más abajo haya comillas sin cerrar.
        primera = None
        for n, texto in enumerate(self.fuente, start=1):
            limpio, _ = _partir_comentario(texto)
            if limpio.strip():
                primera = (n, texto, limpio.strip())
                break
        if primera is None:
            raise _Alto(_ps13(1, self.fuente[0] if self.fuente else ""))
        if _norm(primera[2].split()[0]) not in ("algoritmo", "proceso"):
            raise _Alto(_ps13(primera[0], primera[1]))
        if _norm(primera[2].split()[0]) == "proceso":
            self.cabecera = "Proceso"

        self._preparar()
        self._saltar_vacias()
        n, texto, toks = self._actual()
        if len(toks) < 2 or toks[1].tipo != "ident":
            raise _Alto(Error(
                "PS13", n, texto,
                f"escribiste '{self.cabecera}' pero no le pusiste nombre.",
                "esa línea le pone nombre a lo que estás resolviendo. En el "
                "diagrama de flujo es el óvalo de INICIO.",
                f"{self.cabecera} CostoDeFotocopias", 0, len(toks[0].valor)))
        nombre = toks[1].valor
        self._validar_nombre(nombre, toks[1], texto)
        if len(toks) > 2:
            raise _Alto(self._sobra(toks[2], texto))
        self.i += 1

        # Los mensajes de PS03 nombran el cierre con la misma palabra con que el
        # alumno abrió: a quien escribió Proceso se le pide FinProceso.
        cuerpo = self._bloque(self.cabecera, n, "Fin" + self.cabecera,
                              _FIN_DE_PROGRAMA)
        n_fin = self._actual()[0]
        self.i += 1
        # Decisión: lo que venga después de FinAlgoritmo se ignora. La gramática
        # termina el programa ahí, y señalarlo pediría un decimoquinto código de
        # error que el catálogo no define.
        return _Algoritmo(nombre, cuerpo, n, n_fin, primera[1])

    def _bloque(self, palabra_apertura, linea_apertura, cierre, terminadores):
        """Sentencias hasta un terminador (que NO se consume). PS03 si no llega."""
        cuerpo = []
        while True:
            self._saltar_vacias()
            if self.i >= len(self.lineas):
                ultima = self.lineas[-1] if self.lineas else (1, "", [])
                raise _Alto(_ps03(palabra_apertura, linea_apertura, cierre,
                                  ultima[0], ultima[1]))
            n, texto, toks = self._actual()
            if toks[0].tipo == "ident" and _norm(toks[0].valor) in terminadores:
                return cuerpo
            if toks[0].tipo == "ident" and _norm(toks[0].valor) in _CIERRES:
                if palabra_apertura not in ("Algoritmo", "Proceso"):
                    # Estamos dentro de un Si, de un Mientras o de un Para y
                    # aparece el cierre de un bloque de más afuera: lo que falta
                    # no es esta línea, es el FinSi/FinMientras/FinPara que
                    # nunca se escribió. Se acusa la apertura, que es donde el
                    # estudiante tiene que mirar.
                    raise _Alto(_ps03(palabra_apertura, linea_apertura, cierre,
                                      n, texto))
                # Cierra un bloque que nadie abrió: se dice al derecho.
                raise _Alto(Error(
                    "PS03", n, texto,
                    f"escribiste '{toks[0].valor}' pero aquí no hay ningún "
                    f"bloque abierto que cerrar.",
                    "todo bloque que se abre se cierra: Algoritmo/FinAlgoritmo, "
                    "Si/FinSi, Mientras/FinMientras, Para/FinPara. Y al revés: "
                    "no se cierra lo que no se abrió.",
                    "borra esa línea, o escribe antes la que abre el bloque.",
                    toks[0].col, len(toks[0].valor)))
            cuerpo.append(self._sentencia())

    # -- sentencias ---------------------------------------------------------
    def _sentencia(self):
        n, texto, toks = self._actual()
        self._revisar_parentesis(toks, n, texto)
        cabeza = toks[0]
        if cabeza.tipo == "ident":
            clave = _norm(cabeza.valor)
            despacho = {
                "definir": self._definir, "constante": self._constante,
                "leer": self._leer, "escribir": self._escribir,
                "mostrar": self._escribir, "si": self._si,
                "mientras": self._mientras, "para": self._para,
            }.get(clave)
            if despacho:
                return despacho()
            if len(toks) >= 2 and toks[1].es_op("<-"):
                return self._asignar()
            # 2026-10-05 (revisión): la FORMA del resto de la línea, que es lo
            # que distingue un nombre partido de una estructura mal abierta.
            cuenta_hasta, termina_en = _forma_de_bloque(toks)
            abre_bloque = cuenta_hasta or bool(termina_en)
            if len(toks) >= 2 and toks[1].es_op("="):
                if abre_bloque:
                    raise _Alto(_ps06_falta_la_apertura(toks, cuenta_hasta, n,
                                                        texto))
                izq = cabeza.valor
                der = _tokens_a_texto(toks[2:]) or "…"
                raise _Alto(_ps02(n, texto, toks[1].col, izq, der))
            # 2026-10-05: antes de sospechar de un nombre mal escrito, se mira
            # si la línea empieza por una palabra de estructura. Va DESPUÉS de
            # las dos comprobaciones de arriba a propósito: `caso <- 3` o
            # `hasta <- 10` son asignaciones a variables con nombres legítimos.
            segunda = toks[1] if len(toks) >= 2 and toks[1].tipo == "ident" \
                else None
            ancho = len(texto.rstrip()) - cabeza.col
            llana = _sin_tildes(clave)
            # 2026-10-05 (revisión). Dos palabras, una flecha (o un =) y nada
            # de estructura en el resto: eso es una asignación a un nombre con
            # espacio (`edad hasta <- 18`, `fin semana <- 6`), y le toca el PS14
            # de siempre aunque una de las dos palabras sea también del
            # lenguaje. Solo cede el paso para las palabras de
            # `_PRIMERA_MITAD_DE_NOMBRE`; ver ahí por qué no para todas.
            nombre_partido = (segunda is not None and len(toks) >= 3
                              and toks[2].es_op("<-", "=") and not abre_bloque)
            cede = nombre_partido and llana in _PRIMERA_MITAD_DE_NOMBRE
            if llana in _ABREN_UN_SINO_SI:
                # `SinoSi n = 2 Entonces`, la forma pegada del `Si no Si` que
                # entregó un alumno. Caía en PS14: «Arréglalo: SinoSi_n».
                resto = toks[1:-1] if toks[-1].es("Entonces") else toks[1:]
                if any(t.es_op("<-") for t in resto):
                    resto = []      # con una flecha no es una pregunta
                raise _Alto(_ps06_sino_si(_tokens_a_texto(resto), n, texto,
                                          cabeza.col, len(cabeza.valor),
                                          palabra=cabeza.valor))
            if clave == "fin" and not cede:
                junta = llana + _sin_tildes(_norm(segunda.valor)) if segunda \
                    else ""
                if junta in _NO_TENGO:           # Fin Segun, Fin Funcion...
                    raise _Alto(_ps06_no_tengo(junta, n, texto, cabeza.col,
                                               ancho))
                raise _Alto(_ps06_fin_suelto(segunda.valor if segunda else "",
                                             n, texto, cabeza.col, ancho))
            if llana in _NO_TENGO and not cede:
                raise _Alto(_ps06_no_tengo(llana, n, texto, cabeza.col,
                                           len(cabeza.valor)))
            otra = _norm(segunda.valor) if segunda is not None else ""
            for suelta in (clave, f"{clave} {otra}"):
                if suelta in _FUERA_DE_SITIO and not cede:
                    raise _Alto(_ps06_fuera_de_sitio(
                        suelta, n, texto, cabeza.col, len(cabeza.valor)))
            # Si la SEGUNDA palabra es de estructura, tampoco es un nombre
            # partido: es una instrucción a la que le falta el principio, y
            # unir las dos con guion bajo (`i_Hasta`) no arreglaría nada.
            # (Revisión: salvo que detrás venga la flecha. `edad hasta <- 18`
            # recibía aquí «Arréglalo: Para edad <- 1 Hasta <- 18».)
            if otra == "como" and not nombre_partido:
                raise _Alto(_ps06(
                    "a esta línea le falta la palabra Definir al principio.",
                    "Definir crea una o varias cajas y dice de qué tipo son.",
                    f"Definir {_tokens_a_texto(toks)}", n, texto, cabeza.col,
                    len(cabeza.valor)))
            if otra == "hasta" and not (len(toks) >= 3
                                        and toks[2].es_op("<-", "=")):
                # (Tercera revisión, 2026-10-05: aquí se pegaba lo que
                # hubiera tras Hasta —`i Hasta 10 Entonces` daba «Para i <- 1
                # Hasta 10 Entonces Hacer»—; ahora pasa por la misma
                # validación que todas las demás pistas de Para.)
                raise _Alto(_ps06_para(
                    "esta línea cuenta 'Hasta' un valor, como un ciclo Para, "
                    "pero no empieza por la palabra Para ni dice desde dónde "
                    "cuenta.",
                    _cabecera_de_para(cabeza.valor, toks[1:]) or _EJEMPLO_PARA,
                    n, texto, cabeza.col, len(cabeza.valor)))
            if segunda is not None and abre_bloque:
                raise _Alto(_ps06_forma_de_bloque(toks, cuenta_hasta, n,
                                                  texto))
            if len(toks) == 2 and segunda is not None:
                # `total Entero` o `Entero total`, y nada más: una declaración
                # a la que le faltan Definir y Como (la segunda forma es la de
                # C y la de Java). Sin esto, al sacar los tipos de la red de
                # PS14 habría vuelto el «Arréglalo: total_Entero» del motor
                # viejo.
                tipos = [_norm(t) for t in TIPOS] + ["lógico"]
                tipo, caja = (segunda, cabeza) if otra in tipos else \
                    (cabeza, segunda) if clave in tipos else (None, None)
                if tipo is not None and _norm(caja.valor) not in tipos \
                        and _norm(caja.valor) not in _DE_ESTRUCTURA:
                    raise _Alto(_ps06(
                        "esta línea nombra una variable y un tipo, pero le "
                        "faltan las palabras Definir y Como.",
                        "Definir dice dos cosas: cómo se llama la caja y qué "
                        "tipo de dato guarda. La palabra Como separa las dos.",
                        f"Definir {caja.valor} Como "
                        f"{self._tipo(tipo, n, texto)}",
                        n, texto, cabeza.col, ancho))
            if segunda is not None:
                # Dos identificadores seguidos al principio de la línea = un
                # nombre con espacio en medio. Es el caso de PS14.
                raise _Alto(_ps14(f"{cabeza.valor} {segunda.valor}", n, texto,
                                  cabeza.col))
            raise _Alto(_ps06_instruccion(cabeza.valor, n, texto, cabeza.col))
        raise _Alto(_ps06_instruccion(str(cabeza.valor), n, texto, cabeza.col))

    def _definir(self):
        n, texto, toks = self._actual()
        self.i += 1
        nombres, j = [], 1
        while True:
            if j >= len(toks) or toks[j].tipo != "ident":
                raise _Alto(Error(
                    "PS06", n, texto,
                    "escribiste 'Definir' pero no dijiste qué variable definir.",
                    "Definir crea una o varias cajas y dice de qué tipo son.",
                    "Definir copias Como Entero"))
            if _norm(toks[j].valor) == "como":
                raise _Alto(Error(
                    "PS06", n, texto,
                    "escribiste 'Definir ... Como' sin nombrar ninguna variable.",
                    "Definir crea una o varias cajas y dice de qué tipo son.",
                    "Definir copias Como Entero"))
            self._validar_nombre(toks[j].valor, toks[j], texto)
            if j + 2 == len(toks) and toks[j + 1].tipo == "ident" \
                    and _norm(toks[j + 1].valor) in [_norm(t) for t in TIPOS]:
                # `Definir x Entero`: no es un nombre con espacio, es el Como
                # que se quedó sin escribir. Se deja caer al mensaje de abajo
                # (2026-10-05: antes aconsejaba llamar a la variable `x_Entero`).
                # Solo cuando el tipo es lo ÚLTIMO de la línea (revisión del
                # mismo día): en `Definir valor real, x Como Real` el Como sí
                # está, y decir «le falta la palabra Como» era falso; ahí lo
                # que hay es un nombre con espacio, `valor_real`.
                nombres.append(toks[j].valor)
                j += 1
                break
            if j + 1 < len(toks) and toks[j + 1].tipo == "ident" \
                    and _norm(toks[j + 1].valor) != "como":
                raise _Alto(_ps14(f"{toks[j].valor} {toks[j + 1].valor}", n,
                                  texto, toks[j].col))
            nombres.append(toks[j].valor)
            j += 1
            if j < len(toks) and toks[j].es_op(","):
                j += 1
                continue
            break
        if j >= len(toks) or not toks[j].es("Como"):
            raise _Alto(Error(
                "PS06", n, texto,
                "a este Definir le falta la palabra Como.",
                "Definir dice dos cosas: cómo se llama la caja y qué tipo de "
                "dato guarda. La palabra Como separa las dos.",
                f"Definir {nombres[0]} Como Entero"))
        j += 1
        if j >= len(toks) or toks[j].tipo != "ident":
            raise _Alto(Error(
                "PS06", n, texto,
                "escribiste 'Como' pero no dijiste de qué tipo es la variable.",
                "los tipos que entiendo son: " + ", ".join(TIPOS) + ".",
                f"Definir {nombres[0]} Como Entero"))
        tipo = self._tipo(toks[j], n, texto)
        if j + 1 < len(toks):
            raise _Alto(self._sobra(toks[j + 1], texto))
        return _Definir(nombres, tipo, n, texto)

    def _tipo(self, tok, n, texto):
        canon = {_norm(t): t for t in TIPOS}
        canon["lógico"] = "Logico"      # la tilde se perdona en el tipo
        clave = _norm(tok.valor)
        if clave in canon:
            return canon[clave]
        parecido = _sugerencia(tok.valor, TIPOS)
        raise _Alto(_ps06(
            f"no conozco el tipo '{tok.valor}'.",
            "los tipos que entiendo son: " + ", ".join(TIPOS) + ".",
            f"¿querías decir {parecido}?" if parecido else
            "escribe uno de los cuatro tipos de arriba.",
            n, texto, tok.col, len(tok.valor)))

    def _constante(self):
        n, texto, toks = self._actual()
        self.i += 1
        if len(toks) < 2 or toks[1].tipo != "ident":
            raise _Alto(Error(
                "PS06", n, texto,
                "escribiste 'Constante' pero no le pusiste nombre.",
                "una constante se declara con su nombre en MAYÚSCULAS y su "
                "valor, todo en la misma línea.",
                "Constante PRECIO_COPIA <- 100"))
        nombre = toks[1].valor
        self._validar_nombre(nombre, toks[1], texto)
        # Decisión: la gramática pide el nombre en MAYÚSCULAS (IDENT_MAY), pero
        # aquí solo se enseña la costumbre; no se rechaza el programa por ella.
        # No hay código de error para una convención de estilo, y frenar a un
        # estudiante por escribir `Constante pasaje <- 3200` sería más duro que
        # todo lo demás del catálogo.
        if len(toks) < 3 or not toks[2].es_op("<-"):
            if len(toks) >= 3 and toks[2].es_op("="):
                raise _Alto(_ps02(n, texto, toks[2].col, nombre,
                                  _tokens_a_texto(toks[3:]) or "…"))
            raise _Alto(Error(
                "PS06", n, texto,
                f"a la constante {nombre} no le diste valor.",
                "una constante nace con su valor y ya no cambia: por eso el "
                "valor va en la misma línea de la declaración.",
                f"Constante {nombre} <- 100"))
        expr, resto = self._expresion(toks[3:], n, texto)
        if resto:
            raise _Alto(self._sobra(resto[0], texto))
        return _Constante(nombre, expr, toks[3:], n, texto, toks[1].col)

    def _asignar(self):
        n, texto, toks = self._actual()
        self.i += 1
        nombre = toks[0].valor
        self._validar_nombre(nombre, toks[0], texto)
        if len(toks) < 3:
            raise _Alto(Error(
                "PS06", n, texto,
                f"pusiste la flecha después de '{nombre}' pero no dijiste qué "
                f"guardar.",
                "la flecha <- siempre lleva algo a la derecha: el valor o la "
                "cuenta que se va a guardar en la caja.",
                f"{nombre} <- 0", toks[1].col, 2))
        expr, resto = self._expresion(toks[2:], n, texto)
        if resto and resto[0].es("Hasta"):
            # 2026-10-05: `i <- 3 Hasta n Hacer` es un Para al que le falta la
            # palabra Para, y `para_i <- 3 hasta n hacer` es el mismo Para
            # después de obedecer el consejo viejo de PS14. Decir «sobró algo
            # al final de la línea: 'hasta'» (7 veces en la telemetría) no le
            # explica a nadie qué hacer.
            # (Revisión: también `Desde_i`, `For_i`... que es lo que el motor
            # viejo aconsejaba para esas palabras; y la línea que se propone
            # termina siempre en Hacer.)
            raise _Alto(_ps06_para(
                "esta línea cuenta 'Hasta' un valor, como un ciclo Para, pero "
                "no empieza por la palabra Para.",
                _para_corregido(_sin_prefijo(nombre, _ABREN_UN_CICLO),
                                toks[2:]),
                n, texto, toks[0].col, len(nombre)))
        if resto:
            raise _Alto(self._sobra(resto[0], texto))
        return _Asignar(nombre, expr, toks[2:], n, texto, toks[0].col)

    def _leer(self):
        n, texto, toks = self._actual()
        self.i += 1
        nombres, cols, j = [], [], 1
        while True:
            if j >= len(toks) or toks[j].tipo != "ident":
                raise _Alto(Error(
                    "PS06", n, texto,
                    "escribiste 'Leer' pero no dijiste en qué variable guardar "
                    "el dato.",
                    "Leer toma el siguiente dato de la cola de entradas y lo "
                    "mete en una caja: hay que decirle en cuál.",
                    "Leer copias"))
            self._validar_nombre(toks[j].valor, toks[j], texto)
            if j + 1 < len(toks) and toks[j + 1].tipo == "ident":
                raise _Alto(_ps14(
                    f"{toks[j].valor} {toks[j + 1].valor}", n, texto,
                    toks[j].col,
                    o_bien=f"si son dos variables, sepáralas con coma: Leer "
                           f"{toks[j].valor}, {toks[j + 1].valor}"))
            nombres.append(toks[j].valor)
            cols.append(toks[j].col)
            j += 1
            if j < len(toks) and toks[j].es_op(","):
                j += 1
                continue
            break
        if j < len(toks):
            raise _Alto(self._sobra(toks[j], texto))
        return _Leer(nombres, cols, n, texto)

    def _escribir(self):
        n, texto, toks = self._actual()
        self.i += 1
        cuerpo = toks[1:]
        sin_saltar = False
        if len(cuerpo) >= 2 and cuerpo[-2].es("Sin") and cuerpo[-1].es("Saltar"):
            sin_saltar, cuerpo = True, cuerpo[:-2]
        if not cuerpo:
            raise _Alto(Error(
                "PS06", n, texto,
                f"escribiste '{toks[0].valor}' pero no dijiste qué mostrar.",
                "Escribir necesita al menos una cosa que mostrar: un texto "
                "entre comillas, una variable o una cuenta.",
                'Escribir "Total a pagar: $", total'))
        partes, resto = [], cuerpo
        while True:
            expr, resto = self._expresion(resto, n, texto)
            partes.append((expr, self._recortar(cuerpo, resto)))
            cuerpo = resto
            if resto and resto[0].es_op(","):
                cuerpo = resto = resto[1:]
                continue
            break
        if resto:
            raise _Alto(self._sobra(resto[0], texto))
        return _Escribir(partes, sin_saltar, n, texto)

    @staticmethod
    def _recortar(inicio, resto):
        """Los tokens que consumió la expresión, para poder reimprimirla."""
        return inicio[:len(inicio) - len(resto)] if resto else list(inicio)

    def _si(self):
        n, texto, toks = self._actual()
        self.i += 1
        if len(toks) >= 3 and toks[1].es("NO") and toks[2].es("Si"):
            # 2026-10-05: `Si no Si n = 2 Entonces`, tal cual lo entregó un
            # alumno. Es un `Sino` seguido de otro `Si` en la misma línea. No se
            # convierte en nada (ver `_juntar_dos_palabras`): se le dice cómo se
            # escribe. Sin esto el motor lo leía como un Si cuya pregunta es
            # «NO Si» y contestaba «sobró algo al final de la línea: 'n'».
            condicion = toks[3:-1] if toks[-1].es("Entonces") else toks[3:]
            raise _Alto(_ps06_sino_si(_tokens_a_texto(condicion), n, texto,
                                      toks[0].col,
                                      toks[2].col + 2 - toks[0].col))
        if not (len(toks) >= 2 and toks[-1].es("Entonces")):
            raise _Alto(_ps10(toks[0].valor, "Entonces", n, texto))
        cond_toks = toks[1:-1]
        if not cond_toks:
            raise _Alto(Error(
                "PS06", n, texto,
                "escribiste 'Si ... Entonces' sin ninguna pregunta en medio.",
                "el Si necesita una pregunta que se pueda responder con sí o "
                "con no, como  saldo > 0 .",
                "Si saldo > 0 Entonces"))
        cond, resto = self._expresion(cond_toks, n, texto)
        if resto:
            raise _Alto(self._sobra(resto[0], texto))
        entonces = self._bloque("Si", n, "FinSi", ("sino", "finsi"))
        sino, linea_sino = None, 0
        n_cierre, texto_cierre, toks_cierre = self._actual()
        if _norm(toks_cierre[0].valor) == "sino":
            if len(toks_cierre) > 1:
                # 2026-10-05: lo que venía detrás de Sino en la misma línea se
                # descartaba EN SILENCIO. Con `Sino Si n = 2 Entonces` eso es
                # grave: la segunda pregunta desaparecía y el programa corría
                # haciendo otra cosa que la escrita, sin un solo aviso.
                if toks_cierre[1].es("Si"):
                    resto = toks_cierre[2:-1] if toks_cierre[-1].es("Entonces") \
                        else toks_cierre[2:]
                    raise _Alto(_ps06_sino_si(
                        _tokens_a_texto(resto), n_cierre, texto_cierre,
                        toks_cierre[0].col,
                        toks_cierre[1].col + 2 - toks_cierre[0].col))
                raise _Alto(self._sobra(toks_cierre[1], texto_cierre))
            linea_sino = n_cierre
            self.i += 1
            sino = self._bloque("Si", n, "FinSi", ("finsi",))
            n_cierre = self._actual()[0]
        self.i += 1
        return _Si(cond, cond_toks, entonces, sino, n, linea_sino, n_cierre, texto)

    def _mientras(self):
        n, texto, toks = self._actual()
        self.i += 1
        if not (len(toks) >= 2 and toks[-1].es("Hacer")):
            raise _Alto(_ps10(toks[0].valor, "Hacer", n, texto))
        cond_toks = toks[1:-1]
        if not cond_toks:
            raise _Alto(Error(
                "PS06", n, texto,
                "escribiste 'Mientras ... Hacer' sin ninguna pregunta en medio.",
                "el Mientras repite algo mientras una pregunta siga siendo "
                "cierta: hay que escribir la pregunta.",
                "Mientras saldo > 0 Hacer"))
        cond, resto = self._expresion(cond_toks, n, texto)
        if resto:
            raise _Alto(self._sobra(resto[0], texto))
        cuerpo = self._bloque("Mientras", n, "FinMientras", ("finmientras",))
        n_fin = self._actual()[0]
        self.i += 1
        return _Mientras(cond, cond_toks, cuerpo, n, n_fin, texto)

    def _para(self):
        """`Para <var> <- <ini> Hasta <fin> [Con Paso <p>] Hacer` (2026-10-05).

        Es la sintaxis de PSeInt, que es la que los alumnos traen aprendida. Las
        tres cuentas (<ini>, <fin>, <p>) son expresiones cualesquiera. Cada
        tropiezo posible de la cabecera tiene su mensaje, porque es una línea
        larga y en las entregas del 5-oct apareció escrita de varias maneras.
        """
        n, texto, toks = self._actual()
        self.i += 1
        palabra = toks[0].valor
        if len(toks) < 2 or toks[1].tipo != "ident" \
                or _norm(toks[1].valor) in ("hasta", "hacer", "con"):
            raise _Alto(_ps06_para(
                f"escribiste '{palabra}' pero no dijiste qué variable va a "
                f"llevar la cuenta.",
                "Para i <- 1 Hasta 10 Hacer", n, texto, toks[0].col,
                len(palabra)))
        if toks[1].es("Cada") and not (len(toks) >= 3
                                       and toks[2].es_op("<-", "=")):
            raise _Alto(_ps06(
                "este motor no tiene 'Para Cada'.",
                "el Para de este motor cuenta con una variable, de un valor "
                "hasta otro.",
                "Para i <- 1 Hasta 10 Hacer", n, texto, toks[0].col,
                toks[1].col + len(toks[1].valor) - toks[0].col))
        var = toks[1]
        self._validar_nombre(var.valor, var, texto)
        if len(toks) < 3 or not toks[2].es_op("<-"):
            if len(toks) >= 3 and toks[2].es_op("="):
                # `Para i = 3 Hasta n Hacer`: el mismo descuido de siempre, y se
                # le contesta igual que en el resto del motor (PS02), con la
                # línea ya corregida.
                # (Segunda revisión: lo de la derecha se pasa por
                # `_cabecera_de_para`, para que `Para i = 1 a n Hacer` no reciba
                # una línea que vuelve a fallar al obedecerla.)
                corregida = _cabecera_de_para(var.valor, toks[3:],
                                              valor_suelto=True) \
                    or _para_que_corre(var.valor)
                raise _Alto(_ps02(n, texto, toks[2].col,
                                  f"{palabra} {var.valor}",
                                  corregida.split(" <- ", 1)[1]))
            if len(toks) >= 4 and toks[2].tipo == "ident" \
                    and toks[3].es_op("<-", "="):
                raise _Alto(_ps14(f"{var.valor} {toks[2].valor}", n, texto,
                                  var.col))
            raise _Alto(self._para_sin_flecha(palabra, var, toks[2:], n, texto))
        if not toks[-1].es("Hacer"):
            raise _Alto(_ps10(palabra, "Hacer", n, texto))

        interior = toks[3:-1]
        corte = next((k for k, t in enumerate(interior) if t.es("Hasta")), None)
        if corte is None:
            # Segunda revisión: aquí se pegaba « Hasta 10 Hacer» detrás de lo
            # que hubiera («Para i <- 1 a 3 Hasta 10 Hacer»). Ahora lo del
            # alumno se aprovecha solo si es una cuenta, o dos separadas por
            # `a` o por una coma, que es como se dice en español.
            dicho_con_a = any(t.es("a") or t.es_op(",") for t in interior)
            corregida = _cabecera_de_para(var.valor, interior,
                                          valor_suelto=True)
            raise _Alto(_ps06_para(
                "a este Para le falta la palabra Hasta: no dice hasta qué "
                "valor cuenta." + (" (En este lenguaje el final de la cuenta "
                                   "se anuncia con Hasta, no con 'a' ni con una "
                                   "coma.)" if dicho_con_a and corregida
                                   else ""),
                corregida or _para_que_corre(var.valor), n, texto))
        toks_ini, cola = interior[:corte], interior[corte + 1:]
        # `Con Paso` se busca como PAREJA de palabras: así una variable que se
        # llame `paso` puede usarse en cualquiera de las tres cuentas.
        con = next((k for k in range(len(cola) - 1)
                    if cola[k].es("Con") and cola[k + 1].es("Paso")), None)
        toks_fin = cola if con is None else cola[:con]
        toks_paso = None if con is None else cola[con + 2:]
        if not toks_ini:
            raise _Alto(_ps06_para(
                "a este Para le falta el valor donde empieza la cuenta, entre "
                "la flecha y Hasta.",
                _para_que_corre(var.valor, None, toks_fin, toks_paso),
                n, texto, toks[2].col, 2))
        if not toks_fin:
            raise _Alto(_ps06_para(
                "a este Para le falta el valor final, después de Hasta.",
                _para_que_corre(var.valor, toks_ini),
                n, texto, interior[corte].col, len(interior[corte].valor)))
        if toks_paso is not None and not toks_paso:
            raise _Alto(_ps06_para(
                "escribiste 'Con Paso' pero no dijiste de cuánto en cuánto "
                "cuenta.",
                _para_que_corre(var.valor, toks_ini, toks_fin,
                                paso_defecto="2"),
                n, texto, cola[con].col, len(cola[con].valor)))

        ini, sobra = self._expresion(toks_ini, n, texto)
        if sobra:
            raise _Alto(self._sobra(sobra[0], texto))
        fin, sobra = self._expresion(toks_fin, n, texto)
        if sobra and (sobra[0].es("Paso") or sobra[0].es("Con")):
            # `Hasta 10 Paso 2`: le falta una de las dos palabras.
            raise _Alto(_ps06_para(
                "el paso de un Para se anuncia con las dos palabras juntas: "
                "Con Paso.",
                _para_que_corre(var.valor, toks_ini,
                                self._recortar(toks_fin, sobra), sobra[1:],
                                paso_defecto="2"),
                n, texto, sobra[0].col, len(sobra[0].valor)))
        if sobra:
            raise _Alto(self._sobra(sobra[0], texto))
        paso = None
        if toks_paso is not None:
            paso, sobra = self._expresion(toks_paso, n, texto)
            if sobra:
                raise _Alto(self._sobra(sobra[0], texto))
            if isinstance(paso, _Lit) and _numeros(paso.valor) \
                    and paso.valor == 0:
                # Un 0 escrito a la vista se ataja ya, sin esperar a ejecutar:
                # así el diagrama y el traductor tampoco muestran un ciclo que
                # no puede existir.
                raise _Alto(_ps09_paso_cero(var.valor, n, texto,
                                            toks_paso[0].col, 1))

        cuerpo = self._bloque("Para", n, "FinPara", ("finpara",))
        n_fin, texto_fin, _ = self._actual()
        self.i += 1
        return _Para(var.valor, var.col, ini, toks_ini, fin, toks_fin, paso,
                     toks_paso, cuerpo, n, n_fin, texto, texto_fin)

    def _para_sin_flecha(self, palabra, var, resto, n, texto):
        """`Para i ...` y lo que sigue no es la flecha.

        2026-10-05, segunda revisión. Aquí se armaba el arreglo pegando `<-`
        delante de lo que viniera, y salían líneas que tampoco corren: `Para i
        <= n Hacer` -> «Para i <- <= n Hacer». Hay tres cosas distintas que
        pueden haber pasado, y cada una pide su consejo:

          - la flecha está, pero partida o al revés (`< -`, `->`);
          - lo que viene es una PREGUNTA (`i <= n`): quiso un Mientras;
          - falta la flecha sin más (`Para i 1 Hasta n`, `Para i de 1 a n`).

        En las tres, la línea que se propone se arma con `_cabecera_de_para`,
        que solo copia del alumno lo que de verdad es una cuenta.
        """
        nombre = var.valor
        medio = list(resto)
        if medio and medio[-1].es("Hacer"):
            medio = medio[:-1]
        if medio and (medio[0].es("Desde") or medio[0].es("De")):
            medio = medio[1:]
        if len(medio) >= 2 and (
                (medio[0].es_op("<") and medio[1].es_op("-"))
                or (medio[0].es_op("-") and medio[1].es_op(">"))):
            return _ps06_para(
                f"después de '{palabra} {nombre}' la flecha está mal escrita. "
                f"Es <- : el signo menor y el guion, pegados y en ese orden.",
                _cabecera_de_para(nombre, medio[2:], valor_suelto=True)
                or _para_que_corre(nombre),
                n, texto, medio[0].col,
                medio[1].col + medio[1].largo - medio[0].col)
        if medio and medio[0].es_op("<", "<=", ">", ">=", "<>"):
            signo = medio[0]
            if any(t.es("Hasta") for t in medio):
                # `Para i <= 1 Hasta n Hacer`: iba la flecha y salió otro signo.
                return _ps06_para(
                    f"después de '{palabra} {nombre}' va la flecha <- y "
                    f"escribiste '{signo.valor}'.",
                    _cabecera_de_para(nombre, medio[1:]) or _para_que_corre(nombre),
                    n, texto, signo.col, signo.largo)
            pregunta = [var] + medio
            if _la_cuenta(pregunta) is not None:
                dicho = _tokens_a_texto(pregunta)
                return _ps06(
                    f"después de '{palabra} {nombre}' viene una pregunta "
                    f"({dicho}), y un Para no pregunta: cuenta de un valor "
                    f"Hasta otro.",
                    "para repetir MIENTRAS algo se cumple está el ciclo "
                    "Mientras; el Para es para contar, y su línea dice desde "
                    "qué valor (con la flecha <-) y Hasta cuál.",
                    f"Mientras {dicho} Hacer   (y ciérralo con FinMientras; "
                    f"si lo que querías era contar:  {_EJEMPLO_PARA} ... "
                    f"FinPara)",
                    n, texto, var.col,
                    medio[-1].col + medio[-1].largo - var.col)
        return _ps06_para(
            f"después de '{palabra} {nombre}' falta la flecha <- con el valor "
            f"donde empieza la cuenta.",
            _cabecera_de_para(nombre, medio) or _EJEMPLO_PARA,
            n, texto, var.col, var.largo)

    # -- comprobaciones sueltas ---------------------------------------------
    def _validar_nombre(self, nombre, tok, texto):
        if _RE_ACENTO.search(nombre):
            raise _Alto(_ps14(nombre, tok.linea, texto, tok.col))

    def _revisar_parentesis(self, toks, n, texto):
        abiertos = sum(1 for t in toks if t.es_op("("))
        cerrados = sum(1 for t in toks if t.es_op(")"))
        if abiertos != cerrados:
            raise _Alto(_ps12(abiertos, cerrados, n, texto))

    def _sobra(self, tok, texto):
        """Tokens de más al final de una línea: una instrucción por línea."""
        sobra = _tokens_a_texto([tok])
        return _ps06(
            f"sobró algo al final de la línea: '{sobra}'.",
            "cada instrucción va en su propia línea, y la línea se acaba donde "
            "se acaba la instrucción.",
            "deja una sola instrucción por línea.",
            tok.linea, texto, tok.col, tok.largo)

    # -- expresiones (§6.2) --------------------------------------------------
    def _expresion(self, toks, n, texto):
        return self._or(toks, n, texto)

    def _or(self, toks, n, texto):
        izq, resto = self._and(toks, n, texto)
        while resto and resto[0].es("O"):
            op = resto[0]
            der, resto = self._and(resto[1:], n, texto)
            izq = _Bin("O", izq, der, op)
        return izq, resto

    def _and(self, toks, n, texto):
        izq, resto = self._not(toks, n, texto)
        while resto and resto[0].es("Y"):
            op = resto[0]
            der, resto = self._not(resto[1:], n, texto)
            izq = _Bin("Y", izq, der, op)
        return izq, resto

    def _not(self, toks, n, texto):
        if toks and toks[0].es("NO"):
            op = toks[0]
            expr, resto = self._comparacion(toks[1:], n, texto)
            return _Un("NO", expr, op), resto
        return self._comparacion(toks, n, texto)

    def _comparacion(self, toks, n, texto):
        izq, resto = self._suma(toks, n, texto)
        if resto and resto[0].es_op("=", "<>", "<", "<=", ">", ">="):
            op = resto[0]
            der, resto = self._suma(resto[1:], n, texto)
            izq = _Bin(op.valor, izq, der, op)
        return izq, resto

    def _suma(self, toks, n, texto):
        izq, resto = self._producto(toks, n, texto)
        while resto and resto[0].es_op("+", "-"):
            op = resto[0]
            der, resto = self._producto(resto[1:], n, texto)
            izq = _Bin(op.valor, izq, der, op)
        return izq, resto

    def _producto(self, toks, n, texto):
        izq, resto = self._potencia(toks, n, texto)
        while resto and (resto[0].es_op("*", "/") or resto[0].es("MOD")):
            op = resto[0]
            simbolo = "MOD" if op.tipo == "ident" else op.valor
            der, resto = self._potencia(resto[1:], n, texto)
            izq = _Bin(simbolo, izq, der, op)
        return izq, resto

    def _potencia(self, toks, n, texto):
        base, resto = self._unario(toks, n, texto)
        if resto and resto[0].es_op("^"):
            op = resto[0]
            exp, resto = self._potencia(resto[1:], n, texto)
            return _Bin("^", base, exp, op), resto
        return base, resto

    def _unario(self, toks, n, texto):
        if toks and toks[0].es_op("-"):
            op = toks[0]
            expr, resto = self._primario(toks[1:], n, texto)
            return _Un("-", expr, op), resto
        return self._primario(toks, n, texto)

    def _primario(self, toks, n, texto):
        if not toks:
            raise _Alto(Error(
                "PS06", n, texto,
                "la línea se acaba antes de tiempo: falta el valor.",
                "toda cuenta necesita sus dos lados: después de un signo tiene "
                "que venir un número, un texto o una variable.",
                "total <- copias * 100"))
        tok = toks[0]
        if tok.tipo == "num":
            return _Lit(tok.valor, tok), toks[1:]
        if tok.tipo == "cad":
            return _Lit(tok.valor, tok), toks[1:]
        if tok.es_op("("):
            expr, resto = self._expresion(toks[1:], n, texto)
            if not resto or not resto[0].es_op(")"):
                raise _Alto(_ps12(1, 0, n, texto))
            return expr, resto[1:]
        if tok.tipo == "ident":
            clave = _norm(tok.valor)
            if clave == "verdadero":
                return _Lit(True, tok), toks[1:]
            if clave == "falso":
                return _Lit(False, tok), toks[1:]
            if clave in FUNCIONES:
                if len(toks) < 2 or not toks[1].es_op("("):
                    raise _Alto(_ps06(
                        f"a la función {FUNCIONES[clave][0]} le faltan los "
                        f"paréntesis.",
                        "las funciones reciben su dato entre paréntesis.",
                        f"{FUNCIONES[clave][0]}(dato)",
                        n, texto, tok.col, len(tok.valor)))
                arg, resto = self._expresion(toks[2:], n, texto)
                if not resto or not resto[0].es_op(")"):
                    raise _Alto(_ps12(1, 0, n, texto))
                return _Llamada(FUNCIONES[clave][0], arg, tok), resto[1:]
            self._validar_nombre(tok.valor, tok, texto)
            return _Var(tok.valor, tok), toks[1:]
        if tok.es_op("="):
            raise _Alto(_ps02(n, texto, tok.col, "total",
                              _tokens_a_texto(toks[1:]) or "…"))
        raise _Alto(_ps06(
            f"no esperaba '{tok.valor}' aquí.",
            "en una cuenta van números, textos entre comillas, variables y los "
            "signos + - * / ^ MOD, con paréntesis si hacen falta.",
            "total <- copias * 100 + 2500",
            n, texto, tok.col, tok.largo))


def _analizar(codigo):
    return _Analizador(codigo).analizar()


# ═════════════════════════════════════════════════════════════════════════════
# Reimpresión de expresiones
# ═════════════════════════════════════════════════════════════════════════════
# Se reimprime desde los TOKENS y no desde el árbol para conservar los
# paréntesis que puso el estudiante. En el trazador eso importa: la frase del
# pie tiene que parecerse a lo que él escribió, no a una versión canónica.

def _es_unario(clase_anterior):
    return clase_anterior in (None, "op", "(", ",", "unario")


def _unir(piezas):
    """Junta (texto, clase) con los espacios que uno pondría a mano."""
    salida, anterior = [], None
    for txt, clase in piezas:
        if anterior is None:
            sep = ""
        elif clase in (")", ","):
            sep = ""
        elif anterior in ("(", "unario"):
            sep = ""
        elif anterior == "func" and clase == "(":
            sep = ""
        else:
            sep = " "
        salida.append(sep + txt)
        anterior = clase
    return "".join(salida)


def _piezas(toks, memoria=None, python=False):
    piezas, anterior = [], None
    for t in toks:
        if t.tipo == "cad":
            txt, clase = '"%s"' % t.valor.replace("\\", "\\\\").replace('"', '\\"'), "valor"
        elif t.tipo == "num":
            txt, clase = str(t.valor), "valor"
        elif t.tipo == "ident":
            clave = _norm(t.valor)
            if clave in FUNCIONES:
                txt = FUNCIONES[clave][1] if python else FUNCIONES[clave][0]
                clase = "func"
            elif clave in ("y", "o", "no", "mod"):
                mapa = {"y": "and", "o": "or", "no": "not", "mod": "%"}
                txt = mapa[clave] if python else t.valor.upper()
                clase = "op"
            elif clave in ("verdadero", "falso"):
                cierto = clave == "verdadero"
                txt = ("True" if cierto else "False") if python else \
                    ("Verdadero" if cierto else "Falso")
                clase = "valor"
            elif memoria is not None and t.valor in memoria \
                    and memoria[t.valor] is not None:
                valor = memoria[t.valor]
                txt = '"%s"' % valor if isinstance(valor, str) else _formatear(valor)
                clase = "valor"
            else:
                txt, clase = t.valor, "valor"
        else:
            txt = t.valor
            if txt in ("(", ")", ","):
                clase = txt
            else:
                clase = "unario" if (txt == "-" and _es_unario(anterior)) else "op"
            if python:
                txt = {"=": "==", "<>": "!=", "^": "**"}.get(txt, txt)
        piezas.append((txt, clase))
        anterior = clase
    return piezas


def _tokens_a_texto(toks, memoria=None):
    return _unir(_piezas(toks, memoria=memoria))


def _tokens_a_python(toks):
    return _unir(_piezas(toks, python=True))


# ═════════════════════════════════════════════════════════════════════════════
# Traza
# ═════════════════════════════════════════════════════════════════════════════

class Paso:
    """Una foto del estado justo DESPUÉS de ejecutar una instrucción.

    `salida` es una propiedad y no un atributo guardado porque con el tope de
    10 000 pasos, almacenar en cada paso una copia de todo lo impreso hasta ahí
    sería cuadrático: bastaría un ciclo largo para llenar la memoria del kernel.
    Se guarda el corte y se rebana la salida final, que es una sola cadena
    compartida.
    """

    __slots__ = ("n", "linea", "texto", "memoria", "nodo", "explicacion",
                 "_corte", "_todo")

    def __init__(self, n, linea, texto, memoria, nodo, explicacion, corte):
        self.n, self.linea, self.texto = n, linea, texto
        self.memoria, self.nodo = memoria, nodo
        self.explicacion, self._corte, self._todo = explicacion, corte, ""

    @property
    def salida(self):
        return self._todo[:self._corte]

    def __repr__(self):  # pragma: no cover - solo para depurar
        return f"<Paso {self.n} línea {self.linea}: {self.texto.strip()!r}>"


class Resultado:
    """Todo lo que produjo una ejecución. Nunca contiene una excepción viva.

    Es el único objeto que ven las celdas de nbgrader, y por eso lleva
    `error_corto`: una línea que cabe dentro de un `assert` y que el estudiante
    entiende sin abrir nada más.
    """

    def __init__(self):
        self.ok = True
        self.salida = ""
        self.memoria = {}
        self.tipos = {}
        self.constantes = set()
        self.pasos = []
        self.error = None
        self.error_corto = ""
        self.instrucciones_usadas = set()
        self._nombre = ""

    def tabla_traza(self, variables):
        """Los valores de `variables` después de cada instrucción ejecutable.

        Es exactamente la tabla que se llena a mano en una prueba de escritorio,
        y lo que compara el verificador de E5. Una caja definida pero todavía
        vacía sale como None: es la traducción fiel de «la caja existe pero no
        tiene nada».
        """
        variables = list(variables)
        return [tuple(p.memoria.get(v) for v in variables) for p in self.pasos]

    def imprimir(self):
        """Tarjeta con la salida, la memoria final y el error si lo hubo."""
        if not HAY_IPYTHON:
            print(self._texto_plano())
            return
        display(HTML(self._html()))

    # -- presentación --------------------------------------------------------
    def _texto_plano(self):
        partes = []
        if self.salida:
            partes.append("SALIDA")
            partes.append(self.salida.rstrip("\n"))
        elif self.ok:
            partes.append("SALIDA\n(el algoritmo no mostró nada)")
        if self.memoria:
            partes.append("\nMEMORIA AL TERMINAR")
            for nombre, valor in self.memoria.items():
                marca = " (constante)" if nombre in self.constantes else ""
                texto = "—" if valor is None else _formatear(valor)
                partes.append(f"  {nombre} : {self.tipos.get(nombre, '?')}"
                              f" = {texto}{marca}")
        if self.error is not None:
            partes.append("")
            partes.append(str(self.error))
        return "\n".join(partes)

    def _html(self):
        consola = _escapar(self.salida) if self.salida else \
            '<span style="color:#8a8987">(el algoritmo no mostró nada)</span>'
        bloques = [
            f'<div style="font:12px system-ui;letter-spacing:1.5px;color:{GRIS};'
            f'margin-bottom:4px">SALIDA</div>'
            f'<pre style="background:{TINTA};color:#d7ffd7;padding:10px 12px;'
            f'border-radius:6px;margin:0 0 10px;font-size:13px;line-height:1.5;'
            f'overflow-x:auto;white-space:pre-wrap">{consola}</pre>']
        if self.memoria:
            bloques.append(_html_tabla_memoria(self.memoria, self.tipos,
                                               self.constantes))
        if self.error is not None:
            bloques.append(self.error.html())
        return (f'<div style="border:1px solid {BORDE};border-radius:6px;'
                f'padding:12px 14px;margin:8px 0;background:#fff;'
                f'font-family:system-ui,-apple-system,sans-serif;font-size:14px;'
                f'color:{TINTA}">' + "".join(bloques) + "</div>")


# ═════════════════════════════════════════════════════════════════════════════
# Intérprete
# ═════════════════════════════════════════════════════════════════════════════

_TIPO_DE = {int: "Entero", float: "Real", str: "Cadena", bool: "Logico"}
_CABE_EN = {"Entero": "números enteros", "Real": "números con decimales",
            "Cadena": "texto", "Logico": "los valores Verdadero o Falso"}


class _Interprete:

    def __init__(self, alg, entradas):
        self.alg = alg
        self.cola = [str(v) for v in (entradas or ())]
        self.total_entradas = len(self.cola)
        self.consumidas = 0
        self.memoria = {}
        self.tipos = {}
        self.constantes = set()
        self.pasos = []
        self.buffer = []
        self.largo = 0
        self.contador = 0
        # Qué ciclos están abiertos ahora mismo, de afuera hacia adentro. Solo
        # sirve para que PS09 hable del ciclo en el que de verdad está atascado
        # el programa (2026-10-05: antes solo había Mientras y no hacía falta).
        self.ciclos = []
        self.lecturas_declaradas = _contar_lecturas(alg)

    # -- salida --------------------------------------------------------------
    def texto_salida(self):
        return "".join(self.buffer)

    def _imprimir(self, texto):
        self.buffer.append(texto)
        self.largo += len(texto)
        if self.largo > _TOPE_SALIDA:
            # Un ciclo puede llenar la memoria del kernel antes de llegar al
            # tope de pasos; se corta con el mismo mensaje, que es el mismo
            # problema visto desde otro lado.
            raise _Alto(_ps09(self.alg.linea, self.alg.texto))

    # -- traza ---------------------------------------------------------------
    def _paso(self, st, explicacion, nodo=None, linea=None, texto=None):
        # Los tres opcionales existen por el Para: una sola sentencia que deja
        # varios pasos en la traza (inicialización, pregunta, incremento), cada
        # uno con su propio bloque del diagrama, y el incremento además con su
        # propia línea (la de FinPara).
        self.pasos.append(Paso(
            len(self.pasos) + 1,
            st.linea if linea is None else linea,
            (st.texto if texto is None else texto).rstrip(),
            dict(self.memoria), st.id_nodo if nodo is None else nodo,
            explicacion, self.largo))

    def _tic(self, st):
        if self.contador >= MAX_PASOS:
            raise _Alto(_ps09(st.linea, st.texto,
                              self.ciclos[-1] if self.ciclos else "Mientras"))
        self.contador += 1

    # -- ejecución -----------------------------------------------------------
    def correr(self):
        self._lista(self.alg.cuerpo)

    def _lista(self, sentencias):
        for st in sentencias:
            self._ejecutar(st)

    def _ejecutar(self, st):
        self._tic(st)
        if isinstance(st, _Definir):
            return self._hacer_definir(st)
        if isinstance(st, _Constante):
            return self._hacer_constante(st)
        if isinstance(st, _Asignar):
            return self._hacer_asignar(st)
        if isinstance(st, _Leer):
            return self._hacer_leer(st)
        if isinstance(st, _Escribir):
            return self._hacer_escribir(st)
        if isinstance(st, _Si):
            return self._hacer_si(st)
        if isinstance(st, _Mientras):
            return self._hacer_mientras(st)
        if isinstance(st, _Para):
            return self._hacer_para(st)
        raise RuntimeError("sentencia desconocida")   # no alcanzable

    def _hacer_definir(self, st):
        for nombre in st.nombres:
            if nombre in self.constantes:
                raise _Alto(_ps11(nombre, st.linea, st.texto, 0))
            self.memoria[nombre] = None
            self.tipos[nombre] = st.tipo
        if len(st.nombres) == 1:
            frase = (f"Se creó la caja '{st.nombres[0]}'. Está vacía y solo "
                     f"acepta {_CABE_EN[st.tipo]}.")
        else:
            lista = ", ".join(f"'{x}'" for x in st.nombres[:-1])
            frase = (f"Se crearon las cajas {lista} y '{st.nombres[-1]}'. Están "
                     f"vacías y solo aceptan {_CABE_EN[st.tipo]}.")
        self._paso(st, frase)

    def _hacer_constante(self, st):
        if st.nombre in self.constantes:
            raise _Alto(_ps11(st.nombre, st.linea, st.texto, st.col))
        valor = self._evaluar(st.expr, st)
        self.memoria[st.nombre] = valor
        self.tipos[st.nombre] = _TIPO_DE[type(valor)]
        self.constantes.add(st.nombre)
        self._paso(st, f"Se creó la constante {st.nombre} con el valor "
                       f"{_formatear(valor)}. Ya no puede cambiar.")

    def _hacer_asignar(self, st):
        if st.nombre in self.constantes:
            raise _Alto(_ps11(st.nombre, st.linea, st.texto, st.col))
        if st.nombre not in self.tipos:
            raise _Alto(_ps01(st.nombre, st.linea, st.texto, st.col,
                              conocidas=list(self.tipos)))
        antes = dict(self.memoria)
        valor = self._evaluar(st.expr, st)
        valor = self._encajar(valor, self.tipos[st.nombre], st.nombre, st)
        self.memoria[st.nombre] = valor
        cuenta = _tokens_a_texto(st.toks)
        con_valores = _tokens_a_texto(st.toks, memoria=antes)
        if con_valores != cuenta:
            frase = (f"Se calculó {cuenta} ({con_valores} = {_formatear(valor)}) "
                     f"y el resultado se guardó en '{st.nombre}'.")
        else:
            frase = f"Se guardó {_formatear(valor)} en la caja '{st.nombre}'."
        self._paso(st, frase)

    def _hacer_leer(self, st):
        leidos = []
        for nombre, col in zip(st.nombres, st.cols):
            if nombre in self.constantes:
                raise _Alto(_ps11(nombre, st.linea, st.texto, col))
            if nombre not in self.tipos:
                raise _Alto(_ps01(nombre, st.linea, st.texto, col,
                                  conocidas=list(self.tipos)))
            if not self.cola:
                raise _Alto(_ps05(st.linea, st.texto, self.lecturas_declaradas,
                                  self.total_entradas, self.consumidas))
            crudo = self.cola.pop(0)
            self.consumidas += 1
            tipo = self.tipos[nombre]
            self.memoria[nombre] = self._convertir_entrada(crudo, tipo, nombre, st)
            leidos.append((crudo, tipo, nombre))
        frases = [f'Se tomó "{c}" de la cola de entradas, se convirtió a {t} y '
                  f"se guardó en '{v}'." for c, t, v in leidos]
        self._paso(st, " ".join(frases))

    def _hacer_escribir(self, st):
        piezas = [_formatear(self._evaluar(e, st)) for e, _ in st.partes]
        texto = "".join(piezas)
        self._imprimir(texto if st.sin_saltar else texto + "\n")
        self._paso(st, f"Se mostró en pantalla: {texto}")

    def _hacer_si(self, st):
        antes = dict(self.memoria)
        cierto = self._condicion(st.cond, st, "Si")
        pregunta = _tokens_a_texto(st.toks)
        valores = _tokens_a_texto(st.toks, memoria=antes)
        detalle = f" ({valores})" if valores != pregunta else ""
        self._paso(st, f"Se preguntó si {pregunta}{detalle}: la respuesta fue "
                       f"{'SÍ' if cierto else 'NO'}.")
        if cierto:
            self._lista(st.entonces)
        elif st.sino is not None:
            self._lista(st.sino)

    def _hacer_mientras(self, st):
        self.ciclos.append("Mientras")
        while True:
            self._tic(st)
            antes = dict(self.memoria)
            cierto = self._condicion(st.cond, st, "Mientras")
            pregunta = _tokens_a_texto(st.toks)
            valores = _tokens_a_texto(st.toks, memoria=antes)
            detalle = f" ({valores})" if valores != pregunta else ""
            self._paso(st, f"Se preguntó si {pregunta}{detalle}: la respuesta "
                           f"fue {'SÍ, así que se repite el ciclo' if cierto else 'NO, así que el ciclo terminó'}.")
            if not cierto:
                self.ciclos.pop()
                return
            self._lista(st.cuerpo)

    def _hacer_para(self, st):
        """El Para, ejecutado en las tres piezas que muestra el diagrama.

        Decisiones (2026-10-05):

        * **El valor final y el paso se calculan UNA vez, al entrar.** Es lo
          que hace `range()` en Python, que es a donde va el alumno: el
          traductor saca `for i in range(...)` y las dos versiones tienen que
          dar las mismas vueltas. Si el cuerpo cambia la `n` de `Hasta n`, el
          ciclo sigue contando hasta la `n` de cuando empezó.
        * **La variable que cuenta SÍ se relee en cada vuelta.** Si el cuerpo la
          cambia, el ciclo lo nota. Es la manera de que un Para se quede dando
          vueltas, y para eso está el tope de pasos (`_tic` se llama en la
          pregunta y en el incremento, igual que si fuera el Mientras
          equivalente: gasta lo mismo del presupuesto de 10 000).
        * **La variable tiene que existir** (`Definir i Como Entero`), como
          cualquier otra de este motor. Crear cajas a escondidas contradiría lo
          que el cuadernillo lleva tres semanas enseñando, y PS01 ya dice
          exactamente qué línea agregar.
        * Al terminar, la variable queda con el primer valor que NO cumplió la
          pregunta (en `Para i <- 1 Hasta 3` queda en 4), que es lo que deja el
          Mientras equivalente y lo que se lee en el diagrama. En Python
          quedaría en 3: es la única diferencia entre el Para y el `for` que
          sale del traductor, y solo se nota si se usa `i` después del ciclo.

        Ninguna de las cuatro se pudo contrastar contra un PSeInt instalado; se
        eligieron por coherencia con el diagrama y con el traductor.
        """
        var = st.var
        if var in self.constantes:
            raise _Alto(_ps11(var, st.linea, st.texto, st.col))
        if var not in self.tipos:
            raise _Alto(_ps01(var, st.linea, st.texto, st.col,
                              conocidas=list(self.tipos)))
        self._contador_del_para(st, al_entrar=True)
        tipo = self.tipos[var]
        inicial = self._encajar(self._evaluar(st.ini, st), tipo, var, st,
                                st.toks_ini[0].col)
        self.memoria[var] = inicial
        fin = self._numero_del_para(st, st.fin, st.toks_fin, "el valor final")
        paso = 1
        if st.paso is not None:
            paso = self._numero_del_para(st, st.paso, st.toks_paso, "el paso")
            if paso == 0:
                raise _Alto(_ps09_paso_cero(var, st.linea, st.texto,
                                            st.toks_paso[0].col))
        sube = paso > 0
        op = "<=" if sube else ">="
        de_a = _formatear(abs(paso))
        self._paso(st, f"Empezó el Para: se guardó {_formatear(inicial)} en la "
                       f"caja '{var}'. Va a contar hacia "
                       f"{'arriba' if sube else 'abajo'}, de {de_a} en {de_a}, "
                       f"hasta llegar a {_formatear(fin)}.")
        pregunta = f"{var} {op} {_tokens_a_texto(st.toks_fin)}"
        self.ciclos.append("Para")
        while True:
            self._tic(st)
            actual = self._contador_del_para(st)
            cierto = actual <= fin if sube else actual >= fin
            valores = f"{_formatear(actual)} {op} {_formatear(fin)}"
            detalle = f" ({valores})" if valores != pregunta else ""
            self._paso(st, f"Se preguntó si {pregunta}{detalle}: la respuesta "
                           f"fue {'SÍ, así que se da una vuelta' if cierto else 'NO, así que el ciclo terminó'}.",
                       nodo=st.id_cond)
            if not cierto:
                self.ciclos.pop()
                return
            self._lista(st.cuerpo)
            self._tic(st)
            if var in self.constantes:
                raise _Alto(_ps11(var, st.linea, st.texto, st.col))
            actual = self._contador_del_para(st)
            nuevo = self._encajar(actual + paso, self.tipos[var], var, st)
            self.memoria[var] = nuevo
            self._paso(st, f"Terminó la vuelta: '{var}' pasó de "
                           f"{_formatear(actual)} a {_formatear(nuevo)} "
                           f"({_formatear(actual)} {'+' if sube else '-'} "
                           f"{de_a}), y se vuelve a la pregunta del Para.",
                       nodo=st.id_inc, linea=st.linea_fin, texto=st.texto_fin)

    def _contador_del_para(self, st, al_entrar=False):
        """El valor de la variable que cuenta, o el error que explica por qué
        no se puede contar con ella.

        Se llama en cada vuelta y no solo al entrar, porque el cuerpo del ciclo
        puede haberla vuelto a `Definir` (y entonces está vacía, o ya no es un
        número). Sin esta comprobación eso acababa en un `TypeError` de Python,
        es decir, en un PS00: justo lo que el contrato de robustez prohíbe.
        """
        tipo = self.tipos[st.var]
        if tipo not in ("Entero", "Real"):
            raise _Alto(Error(
                "PS04", st.linea, st.texto,
                f"la variable del Para, '{st.var}', está definida Como {tipo}.",
                "un Para cuenta, y solo se puede contar con números.",
                f"Definir {st.var} Como Entero", st.col, len(st.var)))
        valor = self.memoria.get(st.var)
        if valor is None and not al_entrar:
            raise _Alto(_ps01(st.var, st.linea, st.texto, st.col, vacia=True))
        return valor

    def _numero_del_para(self, st, expr, toks, que):
        valor = self._evaluar(expr, st)
        if not _numeros(valor):
            raise _Alto(Error(
                "PS04", st.linea, st.texto,
                f"{que} de este Para no es un número: es "
                f"{_describir_valor(valor)}.",
                "un Para cuenta desde un número hasta otro, sumando un número "
                "en cada vuelta.",
                "Para i <- 1 Hasta 10 Hacer", toks[0].col,
                toks[-1].col + toks[-1].largo - toks[0].col))
        return valor

    def _condicion(self, expr, st, palabra):
        valor = self._evaluar(expr, st)
        if not isinstance(valor, bool):
            raise _Alto(Error(
                "PS04", st.linea, st.texto,
                f"la pregunta del {palabra} no se puede responder con sí o con no.",
                f"{_describir_valor(valor)} no es una respuesta: {palabra} "
                f"necesita una comparación, como  saldo > 0 , que da Verdadero "
                f"o Falso.",
                f"{palabra} saldo > 0 " +
                ("Entonces" if palabra == "Si" else "Hacer")))
        return valor

    # -- tipos ---------------------------------------------------------------
    def _encajar(self, valor, tipo, nombre, st, col=0, largo=0):
        """Comprueba que el valor quepa en la caja, y lo ajusta si toca."""
        if tipo == "Entero":
            if isinstance(valor, bool) or isinstance(valor, str):
                raise _Alto(_ps04(st.linea, st.texto, nombre, tipo, valor, col, largo))
            if isinstance(valor, float):
                # Decisión: 10 / 2 da 5.0 en Python y también aquí. Un real que
                # no tiene decimales entra en una caja Entera sin protestar,
                # porque frenar ahí castigaría al estudiante por usar la
                # división, que es justo lo que §6.4 le pide entender.
                if not valor.is_integer():
                    raise _Alto(_ps04(st.linea, st.texto, nombre, tipo, valor, col, largo))
                return int(valor)
            return valor
        if tipo == "Real":
            if isinstance(valor, bool) or isinstance(valor, str):
                raise _Alto(_ps04(st.linea, st.texto, nombre, tipo, valor, col, largo))
            return float(valor)
        if tipo == "Cadena":
            if not isinstance(valor, str):
                raise _Alto(_ps04(st.linea, st.texto, nombre, tipo, valor, col, largo))
            return valor
        if not isinstance(valor, bool):
            raise _Alto(_ps04(st.linea, st.texto, nombre, tipo, valor, col, largo))
        return valor

    def _convertir_entrada(self, crudo, tipo, nombre, st):
        try:
            if tipo == "Entero":
                return int(crudo.strip())
            if tipo == "Real":
                return float(crudo.strip())
            if tipo == "Cadena":
                return crudo
            clave = crudo.strip().lower()
            if clave in ("verdadero", "true", "si", "sí", "1", "v"):
                return True
            if clave in ("falso", "false", "no", "0", "f"):
                return False
        except ValueError:
            pass
        raise _Alto(_ps04(st.linea, st.texto, nombre, tipo, crudo))

    # -- expresiones ---------------------------------------------------------
    def _evaluar(self, expr, st):
        if isinstance(expr, _Lit):
            return expr.valor
        if isinstance(expr, _Var):
            if expr.nombre not in self.tipos:
                raise _Alto(_ps01(expr.nombre, st.linea, st.texto, expr.tok.col,
                                  conocidas=list(self.tipos)))
            valor = self.memoria.get(expr.nombre)
            if valor is None:
                raise _Alto(_ps01(expr.nombre, st.linea, st.texto, expr.tok.col,
                                  vacia=True))
            return valor
        if isinstance(expr, _Un):
            valor = self._evaluar(expr.expr, st)
            if expr.op == "-":
                if isinstance(valor, (int, float)) and not isinstance(valor, bool):
                    return -valor
                raise _Alto(self._choque_unario("-", valor, st, expr.tok))
            if isinstance(valor, bool):
                return not valor
            raise _Alto(self._choque_unario("NO", valor, st, expr.tok))
        if isinstance(expr, _Llamada):
            return self._llamar(expr, st)
        return self._binaria(expr, st)

    def _binaria(self, expr, st):
        op = expr.op
        if op in ("Y", "O"):
            izq = self._evaluar(expr.izq, st)
            if not isinstance(izq, bool):
                raise _Alto(self._choque_logico(op, izq, st, expr.tok))
            # Y/O evalúan el lado derecho solo si hace falta, como en Python.
            if op == "Y" and not izq:
                return False
            if op == "O" and izq:
                return True
            der = self._evaluar(expr.der, st)
            if not isinstance(der, bool):
                raise _Alto(self._choque_logico(op, der, st, expr.tok))
            return der
        izq = self._evaluar(expr.izq, st)
        der = self._evaluar(expr.der, st)
        if op in ("=", "<>"):
            if _clase(izq) != _clase(der):
                raise _Alto(self._choque(op, izq, der, st, expr.tok))
            return (izq == der) if op == "=" else (izq != der)
        if op in ("<", "<=", ">", ">="):
            if _clase(izq) != _clase(der) or _clase(izq) == "logico":
                raise _Alto(self._choque(op, izq, der, st, expr.tok))
            return {"<": izq < der, "<=": izq <= der,
                    ">": izq > der, ">=": izq >= der}[op]
        if op == "+" and isinstance(izq, str) and isinstance(der, str):
            return izq + der
        if not _numeros(izq, der):
            raise _Alto(self._choque(op, izq, der, st, expr.tok))
        if op == "+":
            return izq + der
        if op == "-":
            return izq - der
        if op == "*":
            return izq * der
        if op in ("/", "MOD"):
            if der == 0:
                culpable = expr.der.nombre if isinstance(expr.der, _Var) else None
                raise _Alto(_ps08(st.linea, st.texto, culpable,
                                  expr.tok.col, 1))
            return izq / der if op == "/" else izq % der
        # Potencia: un exponente disparatado congela el kernel del alumno sin
        # que ningún tope de pasos lo note, así que se ataja aquí.
        if abs(der) > 4096 and abs(izq) > 1:
            raise _Alto(Error(
                "PS09", st.linea, st.texto,
                "esa potencia produce un número tan grande que el computador "
                "no alcanza a escribirlo.",
                "elevar a un exponente enorme multiplica el número por sí mismo "
                "miles de veces: el resultado no cabe en la memoria.",
                "usa un exponente más pequeño."))
        return izq ** der

    def _llamar(self, expr, st):
        valor = self._evaluar(expr.arg, st)
        nombre = expr.funcion
        try:
            if nombre == "ConvertirAEntero":
                return int(valor.strip()) if isinstance(valor, str) else int(valor)
            if nombre == "ConvertirAReal":
                return float(valor.strip()) if isinstance(valor, str) else float(valor)
            if nombre == "ConvertirATexto":
                return _formatear(valor)
            if nombre == "Longitud":
                if not isinstance(valor, str):
                    raise TypeError
                return len(valor)
            if nombre == "Absoluto":
                return abs(valor)
            if nombre == "Redondear":
                return round(valor)
            return int(valor)      # Truncar
        except (ValueError, TypeError, AttributeError):
            esperado = "texto" if nombre == "Longitud" else "número"
            raise _Alto(Error(
                "PS04", st.linea, st.texto,
                f"{nombre} no pudo trabajar con {_describir_valor(valor)}.",
                f"{nombre} espera {esperado}. Convertir un texto a número solo "
                f"funciona si el texto es de verdad un número escrito con "
                f"cifras: \"40\" sí, \"cuarenta\" no.",
                f'{nombre}("40")' if nombre.startswith("Convertir") else
                f"{nombre}(x)", expr.tok.col, len(nombre)))

    # -- mensajes de choque de tipos ----------------------------------------
    def _choque(self, op, izq, der, st, tok):
        verbo = {"+": "sumar", "-": "restar", "*": "multiplicar",
                 "/": "dividir", "MOD": "sacar el residuo de",
                 "^": "elevar"}.get(op, "comparar")
        return Error(
            "PS04", st.linea, st.texto,
            f"intentaste {verbo} {_describir_valor(izq)} y {_describir_valor(der)}.",
            "las cuentas y las comparaciones se hacen entre cosas del mismo "
            "tipo. Un texto y un número son cosas distintas, aunque el texto "
            'parezca un número: "3200" no es 3200.',
            'usa ConvertirAEntero("3200") para volverlo número, o '
            "ConvertirATexto(3200) para volverlo texto.",
            tok.col, len(str(tok.valor)))

    def _choque_logico(self, op, valor, st, tok):
        return Error(
            "PS04", st.linea, st.texto,
            f"usaste {op} con {_describir_valor(valor)}.",
            f"{op} junta dos preguntas, y una pregunta se responde con "
            f"Verdadero o con Falso, no con un número ni con un texto.",
            "Si edad > 17 Y saldo > 0 Entonces", tok.col, len(str(tok.valor)))

    def _choque_unario(self, op, valor, st, tok):
        if op == "-":
            return Error(
                "PS04", st.linea, st.texto,
                f"intentaste ponerle un signo menos a {_describir_valor(valor)}.",
                "el menos delante solo tiene sentido con números.",
                "-copias", tok.col, 1)
        return Error(
            "PS04", st.linea, st.texto,
            f"usaste NO con {_describir_valor(valor)}.",
            "NO le da la vuelta a una respuesta de sí o no, así que solo "
            "funciona con Verdadero o Falso.",
            "Si NO (saldo > 0) Entonces", tok.col, 2)


def _clase(valor):
    if isinstance(valor, bool):
        return "logico"
    if isinstance(valor, str):
        return "texto"
    return "numero"


def _numeros(*valores):
    return all(isinstance(v, (int, float)) and not isinstance(v, bool)
               for v in valores)


def _contar_lecturas(alg):
    """Cuántos datos pide el programa, contando estáticamente (PS05)."""
    total = 0

    def recorrer(lista):
        nonlocal total
        for st in lista:
            if isinstance(st, _Leer):
                total += len(st.nombres)
            elif isinstance(st, _Si):
                recorrer(st.entonces)
                recorrer(st.sino or [])
            elif isinstance(st, (_Mientras, _Para)):
                recorrer(st.cuerpo)

    recorrer(alg.cuerpo)
    return total


def _instrucciones(alg):
    """Qué instrucciones usó el estudiante. Se calcula del árbol, no de la
    ejecución, para que siga sirviendo aunque el programa falle a mitad."""
    usadas = set()

    def recorrer(lista):
        for st in lista:
            if isinstance(st, _Definir):
                usadas.add("Definir")
            elif isinstance(st, _Constante):
                usadas.add("Constante")
            elif isinstance(st, _Asignar):
                usadas.add("Asignar")
            elif isinstance(st, _Leer):
                usadas.add("Leer")
            elif isinstance(st, _Escribir):
                usadas.add("Escribir")
            elif isinstance(st, _Si):
                usadas.add("Si")
                recorrer(st.entonces)
                recorrer(st.sino or [])
            elif isinstance(st, _Mientras):
                usadas.add("Mientras")
                recorrer(st.cuerpo)
            elif isinstance(st, _Para):
                usadas.add("Para")
                recorrer(st.cuerpo)

    recorrer(alg.cuerpo)
    return usadas


# ═════════════════════════════════════════════════════════════════════════════
# API pública: ejecución
# ═════════════════════════════════════════════════════════════════════════════

def ejecutar_pseudo(codigo, entradas=()):
    """Analiza y ejecuta pseudocódigo. NUNCA lanza excepción.

    Parameters
    ----------
    codigo : str
        El pseudocódigo completo, de `Algoritmo` a `FinAlgoritmo`.
    entradas : list[str]
        Lo que el usuario «iba a teclear», en orden. Cada `Leer` consume uno.

    Returns
    -------
    Resultado
        Con `ok=False` y `error` poblado si algo salió mal. Los errores viajan
        como dato justamente para que un `assert` de nbgrader pueda enseñarlos.
    """
    r = Resultado()
    interp = None
    try:
        alg = _analizar(codigo)
        _construir_layout(alg)
        r._nombre = alg.nombre
        r.instrucciones_usadas = _instrucciones(alg)
        interp = _Interprete(alg, entradas)
        interp.correr()
    except _Alto as alto:
        r.error = alto.error
    except RecursionError:
        # Una expresión con miles de paréntesis anidados agota la pila de
        # Python antes de llegar a ningún tope propio.
        r.error = Error(
            "PS12", 1, None,
            "tu expresión tiene demasiados paréntesis anidados.",
            "cada paréntesis abre un nivel, y el motor no puede seguir tantos "
            "niveles a la vez.",
            "parte la cuenta en dos líneas, guardando el resultado intermedio "
            "en otra variable.")
    except Exception as exc:      # red de seguridad: nunca un traceback
        r.error = _err_motor(exc)

    if interp is not None:
        r.salida = interp.texto_salida()
        r.memoria = dict(interp.memoria)
        r.tipos = dict(interp.tipos)
        r.constantes = set(interp.constantes)
        r.pasos = interp.pasos
        for paso in r.pasos:
            paso._todo = r.salida
    r.ok = r.error is None
    r.error_corto = "" if r.ok else r.error.error_corto
    return r


# ═════════════════════════════════════════════════════════════════════════════
# Traductor a Python (§6.4)
# ═════════════════════════════════════════════════════════════════════════════
# El traductor es línea a línea: la línea n del pseudocódigo produce la línea n
# del Python. Es lo que permite poner los dos textos en columnas alineadas fila
# por fila. Cuando una construcción no produce código (FinSi, FinAlgoritmo) se
# emite una línea vacía y el número se conserva.

_VALOR_INICIAL = {"Entero": "0", "Real": "0.0", "Cadena": '""', "Logico": "False"}
_CONVERSION = {"Entero": "int", "Real": "float", "Cadena": "", "Logico": ""}

_NOTAS = {
    "algoritmo": "Python no necesita cabecera: el archivo <i>es</i> el algoritmo.",
    "finalgoritmo": "Tampoco necesita final: se acaba cuando se acaba.",
    "comentario": "El comentario es igual en los dos idiomas, solo cambia el símbolo.",
    "definir": "Python crea la caja en el momento de guardarle algo.",
    "constante": "Python no tiene constantes de verdad: se acuerda escribirlas "
                 "en MAYÚSCULAS.",
    "leer": "Aquí está la diferencia grande: <code>input()</code> siempre "
            "entrega texto, y tú decides con <code>int()</code> en qué se convierte.",
    "escribir": "<code>Escribir</code> con comas pega los pedazos; "
                "<code>sep=\"\"</code> hace lo mismo en Python.",
    "asignar": "<code>&lt;-</code> se vuelve <code>=</code>.",
    "si": "En pseudocódigo <code>=</code> pregunta y <code>&lt;-</code> guarda. "
          "En Python <code>==</code> pregunta y <code>=</code> guarda.",
    "sino": "",
    "finsi": "Python cierra el bloque con la sangría, no con una palabra.",
    "mientras": "",
    "finmientras": "Python cierra el bloque con la sangría, no con una palabra.",
    "para": "<code>range</code> se detiene uno ANTES del segundo número: por "
            "eso el final lleva un <code>+ 1</code> que en el pseudocódigo no "
            "estaba.",
    "finpara": "Python cierra el bloque con la sangría, no con una palabra.",
}


def _para_a_python(st, tipos):
    """La línea `for ... in range(...):` de un Para, y su aviso si lo lleva.

    Decisión (2026-10-05): se traduce a `for` + `range` y no a su `while`
    equivalente. El `while` sería fiel en todos los casos, pero necesita tres
    líneas (inicializar, preguntar, incrementar) y el traductor es línea a
    línea; y sobre todo, `for i in range(...)` es lo que el curso quiere que el
    alumno termine escribiendo. El costo son dos sitios donde `range` no llega:

    * `Hasta` es INCLUSIVO y `range` no: de ahí el `+ 1` (o `- 1` al bajar).
    * `range` solo cuenta con enteros. Si la variable es Real se deja un
      comentario en la misma línea, en vez de fingir que ese Python corre.
    """
    def con_parentesis(toks, texto):
        return texto if len(toks) == 1 else f"({texto})"

    ini = _tokens_a_python(st.toks_ini)
    fin = _tokens_a_python(st.toks_fin)
    paso = _paso_fijo(st)
    un_numero = len(st.toks_fin) == 1 and st.toks_fin[0].tipo == "num" \
        and isinstance(st.toks_fin[0].valor, int)
    if paso is None:
        # No se sabe si sube o baja hasta ejecutar: lo decide el propio Python.
        p = con_parentesis(st.toks_paso, _tokens_a_python(st.toks_paso))
        tope = f"{con_parentesis(st.toks_fin, fin)} + (1 if {p} > 0 else -1)"
        rango = f"{ini}, {tope}, {p}"
    else:
        if un_numero:
            tope = str(st.toks_fin[0].valor + (1 if paso > 0 else -1))
        else:
            tope = (f"{con_parentesis(st.toks_fin, fin)} "
                    f"{'+' if paso > 0 else '-'} 1")
        rango = f"{ini}, {tope}" + ("" if paso == 1 else f", {_formatear(paso)}")
    aviso = ""
    if tipos.get(st.var) == "Real" or isinstance(paso, float):
        aviso = "  # range() solo cuenta con enteros: aquí iría un while"
    return f"for {st.var} in range({rango}):", aviso


def _tipos_declarados(alg):
    tabla = {}

    def recorrer(lista):
        for st in lista:
            if isinstance(st, _Definir):
                for nombre in st.nombres:
                    tabla[nombre] = st.tipo
            elif isinstance(st, _Si):
                recorrer(st.entonces)
                recorrer(st.sino or [])
            elif isinstance(st, (_Mientras, _Para)):
                recorrer(st.cuerpo)

    recorrer(alg.cuerpo)
    return tabla


def _traduccion(codigo):
    """Devuelve (lineas_pseudo, lineas_python, notas, error_o_None)."""
    try:
        alg = _analizar(codigo)
    except _Alto as alto:
        return None, None, None, alto.error
    except Exception as exc:  # pragma: no cover - red de seguridad
        return None, None, None, _err_motor(exc)

    fuente = codigo.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    py = [None] * len(fuente)
    notas = [""] * len(fuente)
    tipos = _tipos_declarados(alg)

    def poner(n, texto, clave=""):
        py[n - 1] = texto
        if clave:
            notas[n - 1] = _NOTAS.get(clave, "")

    def comentario_de(n):
        """El comentario que iba al final de la línea, si lo había."""
        _, com = _partir_comentario(fuente[n - 1])
        return f"  # {com.strip()}" if com and com.strip() else ""

    def recorrer(lista, nivel):
        sangria = "    " * nivel
        for st in lista:
            cola = comentario_de(st.linea)
            if isinstance(st, _Definir):
                inicial = _VALOR_INICIAL[st.tipo]
                # Única regla que produce varias asignaciones: se unen con «;»
                # para no desalinear las dos columnas.
                cuerpo = "; ".join(f"{n} = {inicial}" for n in st.nombres)
                poner(st.linea, sangria + cuerpo + cola, "definir")
            elif isinstance(st, _Constante):
                poner(st.linea,
                      f"{sangria}{st.nombre} = {_tokens_a_python(st.toks)}{cola}",
                      "constante")
            elif isinstance(st, _Asignar):
                poner(st.linea,
                      f"{sangria}{st.nombre} = {_tokens_a_python(st.toks)}{cola}",
                      "asignar")
            elif isinstance(st, _Leer):
                trozos = []
                for nombre in st.nombres:
                    conv = _CONVERSION.get(tipos.get(nombre, "Cadena"), "")
                    if tipos.get(nombre) == "Logico":
                        # §6.4 no cubre Leer sobre un Logico. Se traduce a la
                        # comparación explícita, que es lo que de verdad hace el
                        # intérprete y no esconde nada.
                        trozos.append(f'{nombre} = (input() == "Verdadero")')
                    elif conv:
                        trozos.append(f"{nombre} = {conv}(input())")
                    else:
                        trozos.append(f"{nombre} = input()")
                poner(st.linea, sangria + "; ".join(trozos) + cola, "leer")
            elif isinstance(st, _Escribir):
                args = [_tokens_a_python(toks) for _, toks in st.partes]
                extra = []
                if len(args) > 1:
                    extra.append('sep=""')
                if st.sin_saltar:
                    extra.append('end=""')
                todo = ", ".join(args + extra)
                poner(st.linea, f"{sangria}print({todo}){cola}", "escribir")
            elif isinstance(st, _Si):
                cond = _tokens_a_python(st.toks)
                vacio = " pass" if not st.entonces else ""
                poner(st.linea, f"{sangria}if {cond}:{vacio}{cola}", "si")
                recorrer(st.entonces, nivel + 1)
                if st.linea_sino:
                    vacio = " pass" if not st.sino else ""
                    poner(st.linea_sino, f"{sangria}else:{vacio}", "sino")
                    recorrer(st.sino or [], nivel + 1)
                poner(st.linea_fin, "", "finsi")
            elif isinstance(st, _Mientras):
                cond = _tokens_a_python(st.toks)
                vacio = " pass" if not st.cuerpo else ""
                poner(st.linea, f"{sangria}while {cond}:{vacio}{cola}", "mientras")
                recorrer(st.cuerpo, nivel + 1)
                poner(st.linea_fin, "", "finmientras")
            elif isinstance(st, _Para):
                cabeza, aviso = _para_a_python(st, tipos)
                vacio = " pass" if not st.cuerpo else ""
                poner(st.linea, f"{sangria}{cabeza}{vacio}{aviso}{cola}", "para")
                recorrer(st.cuerpo, nivel + 1)
                poner(st.linea_fin, "", "finpara")

    poner(alg.linea, f"# --- {alg.nombre} ---", "algoritmo")
    poner(alg.linea_fin, "", "finalgoritmo")
    recorrer(alg.cuerpo, 0)

    # Las líneas de comentario suelto heredan la sangría de la primera línea
    # traducida que venga después: es donde el lector espera verlas.
    for i, texto in enumerate(py):
        if texto is not None:
            continue
        crudo = fuente[i].strip()
        if crudo.startswith("//"):
            sangria = ""
            for siguiente in py[i + 1:]:
                if siguiente:
                    sangria = siguiente[:len(siguiente) - len(siguiente.lstrip())]
                    break
            py[i] = f"{sangria}# {crudo[2:].strip()}"
            notas[i] = _NOTAS["comentario"]
        else:
            py[i] = ""
    return fuente, py, notas, None


def traducir_a_python(codigo):
    """Traduce el pseudocódigo a Python, línea por línea (§6.4).

    Si el pseudocódigo no se puede analizar devuelve el mensaje pedagógico
    convertido en comentarios de Python: nunca lanza, porque esta función se
    llama desde botones y desde celdas de andamiaje donde una excepción dejaría
    el cuadernillo a medias.
    """
    _, py, _, error = _traduccion(codigo)
    if error is not None:
        return "\n".join("# " + linea for linea in str(error).split("\n"))
    return "\n".join(py).rstrip() + "\n" if any(py) else ""


def tabla_dos_columnas(codigo):
    """Pinta el panel «pseudocódigo | Python | por qué», fila por fila."""
    fuente, py, notas, error = _traduccion(codigo)
    if error is not None:
        _mostrar(error.html(), str(error))
        return
    filas = []
    for n, (izq, der, nota) in enumerate(zip(fuente, py, notas), start=1):
        if not izq.strip() and not der.strip():
            continue
        filas.append(
            f'<tr><td style="color:{GRIS};text-align:right;padding:4px 8px;'
            f'font-size:12px">{n}</td>'
            f'<td style="padding:4px 10px;font-family:ui-monospace,Menlo,'
            f'monospace;font-size:13px;white-space:pre">{_escapar(izq)}</td>'
            f'<td style="padding:4px 10px;font-family:ui-monospace,Menlo,'
            f'monospace;font-size:13px;white-space:pre;background:#f7fbff">'
            f'{_escapar(der)}</td>'
            f'<td style="padding:4px 10px;font-size:12.5px;color:{GRIS};'
            f'max-width:280px">{nota}</td></tr>')
    tabla = (
        f'<div style="overflow-x:auto"><table style="border-collapse:collapse;'
        f'width:100%;font-family:system-ui,sans-serif">'
        f'<tr><th></th>'
        f'<th style="text-align:left;padding:6px 10px;font-size:12px;'
        f'letter-spacing:1.5px;color:{GRIS};border-bottom:1px solid {BORDE}">'
        f'PSEUDOCÓDIGO</th>'
        f'<th style="text-align:left;padding:6px 10px;font-size:12px;'
        f'letter-spacing:1.5px;color:{AZUL_OSC};border-bottom:1px solid {BORDE};'
        f'background:#f7fbff">PYTHON</th>'
        f'<th style="text-align:left;padding:6px 10px;font-size:12px;'
        f'letter-spacing:1.5px;color:{GRIS};border-bottom:1px solid {BORDE}">'
        f'POR QUÉ</th></tr>' + "".join(filas) + "</table></div>")
    plano = "\n".join(f"{a:<44}{b}" for a, b in zip(fuente, py))
    _mostrar(tabla, plano)


def _mostrar(html_texto, plano=""):
    """Pinta HTML si hay frontend; si no, texto plano. El autograder ve texto."""
    if HAY_IPYTHON:
        display(HTML(html_texto))
    else:
        print(plano or re.sub(r"<[^>]+>", "", html_texto))


def _html_tabla_memoria(memoria, tipos, constantes, cambiada=None):
    """Tabla variable | valor | tipo. La que cambió en este paso lleva ←."""
    if not memoria:
        return (f'<div style="color:{GRIS};font-size:13px">Todavía no hay '
                f'ninguna caja creada.</div>')
    filas = []
    for nombre, valor in memoria.items():
        marca = nombre == cambiada
        fondo = "background:#e8f5e8;" if marca else ""
        if valor is None:
            celda = (f'<span style="color:#b0afad" title="la caja existe pero '
                     f'está vacía">—</span>')
        else:
            celda = _escapar(_formatear(valor))
        tipo = tipos.get(nombre, "")
        if nombre in constantes:
            tipo += " · constante"
        filas.append(
            f'<tr style="{fondo}">'
            f'<td style="padding:4px 10px;border:1px solid {BORDE};'
            f'font-family:ui-monospace,Menlo,monospace">{_escapar(nombre)}</td>'
            f'<td style="padding:4px 10px;border:1px solid {BORDE};'
            f'font-family:ui-monospace,Menlo,monospace">{celda}'
            + (' <b style="color:#0f8a4a">←</b>' if marca else "") + "</td>"
            f'<td style="padding:4px 10px;border:1px solid {BORDE};'
            f'font-size:12px;color:{GRIS}">{_escapar(tipo)}</td></tr>')
    return (f'<table style="border-collapse:collapse;font-family:system-ui,'
            f'sans-serif;font-size:13px;margin:4px 0">'
            f'<tr><th style="padding:4px 10px;border:1px solid {BORDE};'
            f'background:{GRIS_CLARO};text-align:left">variable</th>'
            f'<th style="padding:4px 10px;border:1px solid {BORDE};'
            f'background:{GRIS_CLARO};text-align:left">valor</th>'
            f'<th style="padding:4px 10px;border:1px solid {BORDE};'
            f'background:{GRIS_CLARO};text-align:left">tipo</th></tr>'
            + "".join(filas) + "</table>")


# ═════════════════════════════════════════════════════════════════════════════
# Diagrama de flujo: modelo de nodos y emisor de SVG (§7.3)
# ═════════════════════════════════════════════════════════════════════════════
# Se dibuja con un emisor propio de ~200 líneas en vez de graphviz o mermaid:
# el layout automático de graphviz no respeta la convención didáctica (rombo con
# salidas Sí/No a los lados, retorno del Mientras por la izquierda), mermaid no
# se renderiza en nbclassic, y ninguno de los dos cabe en «sin dependencias».

ANCHO = 660       # ancho del viewBox
CX = 330          # eje central
GAP = 34          # espacio vertical entre un nodo y el siguiente
MARGEN = 24       # margen superior e inferior

DIM = {
    "inicio": (170, 46),
    "fin": (170, 46),
    "lectura": (280, 56),
    "escritura": (280, 56),
    "proceso": (250, 56),
    "decision": (230, 96),
    "union": (14, 14),
}
COLOR = {
    "inicio": ("#008300", "#ffffff"),
    "fin": ("#008300", "#ffffff"),
    "lectura": ("#2a78d6", "#ffffff"),
    "escritura": ("#2a78d6", "#ffffff"),
    "proceso": ("#4a3aa7", "#ffffff"),
    "decision": ("#eda100", "#3a2a00"),
    "union": ("#8a8987", "#8a8987"),
}
_BORDE_NODO = {
    "inicio": VERDE_OSC, "fin": VERDE_OSC, "lectura": AZUL_OSC,
    "escritura": AZUL_OSC, "proceso": VIOLETA_OSC, "decision": AMBAR_OSC,
    "union": "#8a8987",
}
RESALTE = "#d03b3b"
_SESGO = 20            # inclinación del paralelogramo
_TRAZO = "#8a8987"     # color de las flechas
_RAMA = 175            # separación horizontal de las ramas de un Si
_RETORNO = 250         # cuánto se aparta la flecha de retorno del Mientras
_MAX_TEXTO = 32


def _construir_layout(alg):
    """Numera los nodos del diagrama y arma el árbol que dibuja el emisor.

    Decisión: `Definir` y `Constante` NO producen nodo. Un diagrama de flujo
    dibuja el flujo, no las declaraciones —así lo muestra el diagrama de
    referencia del diseño, que cuenta seis bloques para un programa de siete
    instrucciones—. Para que el trazador tenga algo que resaltar mientras se
    declaran las cajas, esas sentencias apuntan al óvalo de INICIO.
    """
    contador = [0]

    def nuevo(tipo, texto, linea):
        contador[0] += 1
        return {"id": contador[0], "tipo": tipo, "texto": texto, "linea": linea}

    inicio = nuevo("inicio", "INICIO", alg.linea)
    alg.id_nodo = inicio["id"]
    items = [{"clase": "simple", "nodo": inicio}]
    items += _items(alg.cuerpo, nuevo, inicio["id"])
    fin = nuevo("fin", "FIN", alg.linea_fin)
    alg.id_fin = fin["id"]
    items.append({"clase": "simple", "nodo": fin})
    return items


def _items(lista, nuevo, id_inicio):
    salida = []
    for st in lista:
        if isinstance(st, (_Definir, _Constante)):
            st.id_nodo = id_inicio
        elif isinstance(st, _Leer):
            nodo = nuevo("lectura", "LEER " + ", ".join(st.nombres), st.linea)
            st.id_nodo = nodo["id"]
            salida.append({"clase": "simple", "nodo": nodo})
        elif isinstance(st, _Escribir):
            texto = "ESCRIBIR " + ", ".join(_tokens_a_texto(t) for _, t in st.partes)
            nodo = nuevo("escritura", texto, st.linea)
            st.id_nodo = nodo["id"]
            salida.append({"clase": "simple", "nodo": nodo})
        elif isinstance(st, _Asignar):
            nodo = nuevo("proceso", f"{st.nombre} ← {_tokens_a_texto(st.toks)}",
                         st.linea)
            st.id_nodo = nodo["id"]
            salida.append({"clase": "simple", "nodo": nodo})
        elif isinstance(st, _Si):
            rombo = nuevo("decision", f"¿{_tokens_a_texto(st.toks)}?", st.linea)
            st.id_nodo = rombo["id"]
            verdadero = _items(st.entonces, nuevo, id_inicio)
            falso = _items(st.sino or [], nuevo, id_inicio)
            union = nuevo("union", "", st.linea_fin)
            st.id_union = union["id"]
            salida.append({"clase": "si", "nodo": rombo, "v": verdadero,
                           "f": falso, "union": union})
        elif isinstance(st, _Mientras):
            rombo = nuevo("decision", f"¿{_tokens_a_texto(st.toks)}?", st.linea)
            st.id_nodo = rombo["id"]
            cuerpo = _items(st.cuerpo, nuevo, id_inicio)
            salida.append({"clase": "mientras", "nodo": rombo, "cuerpo": cuerpo})
        elif isinstance(st, _Para):
            # 2026-10-05: el Para se dibuja ABIERTO, como se dibuja a mano:
            # caja de inicialización -> rombo -> cuerpo -> caja de incremento
            # -> flecha de vuelta al rombo. No hace falta una clase nueva de
            # item ni tocar `_disponer`: la inicialización es un bloque simple
            # que va antes, y lo demás es exactamente un ciclo «mientras» cuyo
            # cuerpo termina en la caja del incremento, de la que sale la
            # flecha de retorno.
            ini, pregunta, incremento = _textos_del_para(st, _tokens_a_texto)
            caja_ini = nuevo("proceso", f"{st.var} ← {ini}", st.linea)
            rombo = nuevo("decision", f"¿{pregunta}?", st.linea)
            cuerpo = _items(st.cuerpo, nuevo, id_inicio)
            caja_inc = nuevo("proceso", f"{st.var} ← {incremento}", st.linea_fin)
            st.id_nodo, st.id_cond = caja_ini["id"], rombo["id"]
            st.id_inc = caja_inc["id"]
            salida.append({"clase": "simple", "nodo": caja_ini})
            salida.append({"clase": "mientras", "nodo": rombo,
                           "cuerpo": cuerpo + [{"clase": "simple",
                                                "nodo": caja_inc}]})
    return salida


def _disponer(items, cx, y0, puerto, colocados, aristas):
    """Coloca los items en columna. Devuelve (alto ocupado, puerto de salida).

    `puerto` es un dict {"pts": [...], "etiqueta": str|None}: el camino que ya
    lleva recorrido la flecha que va a llegar al siguiente nodo. Guardarlo como
    lista de puntos (y no como un punto suelto) es lo que permite que la salida
    «No» de un Mientras rodee el ciclo por la derecha sin cruzarse con nada.
    """
    y = y0
    for it in items:
        clase = it["clase"]
        if clase == "simple":
            nodo = it["nodo"]
            w, h = DIM[nodo["tipo"]]
            cy = y + h / 2
            colocados.append((nodo, cx, cy))
            if puerto:
                aristas.append({"pts": puerto["pts"] + [(cx, cy - h / 2)],
                                "etiqueta": puerto["etiqueta"]})
            puerto = {"pts": [(cx, cy + h / 2)], "etiqueta": None}
            y += h + GAP
        elif clase == "si":
            rombo = it["nodo"]
            w, h = DIM["decision"]
            cy = y + h / 2
            colocados.append((rombo, cx, cy))
            if puerto:
                aristas.append({"pts": puerto["pts"] + [(cx, cy - h / 2)],
                                "etiqueta": puerto["etiqueta"]})
            y += h + GAP
            pv = {"pts": [(cx - w / 2, cy), (cx - _RAMA, cy)], "etiqueta": "Sí"}
            pf = {"pts": [(cx + w / 2, cy), (cx + _RAMA, cy)], "etiqueta": "No"}
            alto_v, pv = _disponer(it["v"], cx - _RAMA, y, pv, colocados, aristas)
            alto_f, pf = _disponer(it["f"], cx + _RAMA, y, pf, colocados, aristas)
            y_union = y + max(alto_v, alto_f) + GAP
            union = it["union"]
            colocados.append((union, cx, y_union))
            aristas.append({"pts": pv["pts"] + [(cx - 7, y_union)],
                            "etiqueta": pv["etiqueta"]})
            aristas.append({"pts": pf["pts"] + [(cx + 7, y_union)],
                            "etiqueta": pf["etiqueta"]})
            puerto = {"pts": [(cx, y_union + 7)], "etiqueta": None}
            y = y_union + 7 + GAP
        else:                                   # mientras
            rombo = it["nodo"]
            w, h = DIM["decision"]
            cy = y + h / 2
            y_arriba = y
            colocados.append((rombo, cx, cy))
            if puerto:
                aristas.append({"pts": puerto["pts"] + [(cx, cy - h / 2)],
                                "etiqueta": puerto["etiqueta"]})
            y += h + GAP
            pc = {"pts": [(cx, cy + h / 2)], "etiqueta": "Sí"}
            alto_c, pc = _disponer(it["cuerpo"], cx, y, pc, colocados, aristas)
            y += alto_c
            y_vuelta = pc["pts"][-1][1]
            aristas.append({"pts": pc["pts"] + [
                (cx - _RETORNO, y_vuelta),
                (cx - _RETORNO, y_arriba - 18),
                (cx, y_arriba - 18),
                (cx, cy - h / 2)], "etiqueta": None})
            puerto = {"pts": [(cx + w / 2, cy), (cx + _RETORNO, cy),
                              (cx + _RETORNO, y), (cx, y)], "etiqueta": "No"}
            y += GAP
    return y - y0, puerto


def _num(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _puntos(pares):
    return " ".join(f"{_num(x)},{_num(y)}" for x, y in pares)


def _figura(tipo, cx, cy, relleno, borde, grosor, opacidad=""):
    w, h = DIM[tipo]
    op = f' opacity="{opacidad}"' if opacidad else ""
    comun = f'fill="{relleno}" stroke="{borde}" stroke-width="{grosor}"{op}'
    if tipo in ("inicio", "fin"):
        return (f'<rect x="{_num(cx - w / 2)}" y="{_num(cy - h / 2)}" '
                f'width="{w}" height="{h}" rx="{_num(h / 2)}" ry="{_num(h / 2)}" '
                f'{comun}/>')
    if tipo in ("lectura", "escritura"):
        pts = [(cx - w / 2 + _SESGO, cy - h / 2), (cx + w / 2, cy - h / 2),
               (cx + w / 2 - _SESGO, cy + h / 2), (cx - w / 2, cy + h / 2)]
        return f'<polygon points="{_puntos(pts)}" {comun}/>'
    if tipo == "proceso":
        return (f'<rect x="{_num(cx - w / 2)}" y="{_num(cy - h / 2)}" '
                f'width="{w}" height="{h}" rx="6" {comun}/>')
    if tipo == "decision":
        pts = [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2),
               (cx - w / 2, cy)]
        return f'<polygon points="{_puntos(pts)}" {comun}/>'
    return f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="7" {comun}/>'


def _recortar_texto(texto):
    return texto if len(texto) <= _MAX_TEXTO else texto[:_MAX_TEXTO - 1] + "…"


# XML no admite los caracteres de control, y un estudiante puede pegar uno sin
# darse cuenta al copiar de un PDF o de Word. Si se cuela, el SVG deja de ser
# XML bien formado y nbclassic no lo pinta: en vez del diagrama aparece la
# etiqueta en crudo. Se limpian al entrar al dibujo, no antes, para que el
# mensaje de error sí pueda seguir señalando la columna exacta del intruso.
_RE_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f￾￿]")


def _texto_svg(texto):
    return _escapar(_RE_CONTROL.sub("", texto))


_DEFS = (
    '<defs><marker id="punta" markerWidth="10" markerHeight="10" refX="8" '
    f'refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="{_TRAZO}"/>'
    "</marker></defs>")


def _emitir_svg(items, nombre, resaltar=None):
    colocados, aristas = [], []
    _disponer(items, CX, MARGEN, None, colocados, aristas)

    xs, ys = [], []
    for nodo, cx, cy in colocados:
        w, h = DIM[nodo["tipo"]]
        xs += [cx - w / 2, cx + w / 2]
        ys += [cy - h / 2, cy + h / 2]
    for arista in aristas:
        for x, y in arista["pts"]:
            xs.append(x)
            ys.append(y)
    # El viewBox nominal es 660 de ancho; si un Si anidado se sale, se ensancha
    # en vez de recortar el dibujo. Vale más un diagrama ancho que uno mutilado.
    dx = max(0.0, MARGEN - min(xs)) if xs else 0.0
    dy = max(0.0, MARGEN - min(ys)) if ys else 0.0
    ancho = max(ANCHO, (max(xs) + dx + MARGEN) if xs else ANCHO)
    alto = (max(ys) + dy + MARGEN) if ys else 2 * MARGEN

    partes = [_DEFS]
    for arista in aristas:
        pts = [(x + dx, y + dy) for x, y in arista["pts"]]
        partes.append(f'<polyline points="{_puntos(pts)}" fill="none" '
                      f'stroke="{_TRAZO}" stroke-width="2.2" '
                      f'marker-end="url(#punta)"/>')
        if arista["etiqueta"]:
            (x1, y1), (x2, y2) = pts[0], pts[1]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            partes.append(
                f'<text x="{_num(mx)}" y="{_num(my - 6)}" font-family="system-ui,'
                f'sans-serif" font-size="12" fill="{GRIS}" text-anchor="middle">'
                f'{_texto_svg(arista["etiqueta"])}</text>')
    for nodo, cx, cy in colocados:
        x, y = cx + dx, cy + dy
        tipo = nodo["tipo"]
        relleno, color_texto = COLOR[tipo]
        partes.append(f'<g><title>{_texto_svg(nodo["texto"] or "unión de ramas")}'
                      f'</title>')
        if resaltar is not None and nodo["id"] == resaltar:
            partes.append(_figura(tipo, x, y, "none", RESALTE, 8, "0.35"))
            partes.append(_figura(tipo, x, y, relleno, RESALTE, 3))
        else:
            partes.append(_figura(tipo, x, y, relleno, _BORDE_NODO[tipo], 1.5))
        if nodo["texto"]:
            partes.append(
                f'<text x="{_num(x)}" y="{_num(y)}" font-family="system-ui,'
                f'sans-serif" font-size="13" fill="{color_texto}" '
                f'text-anchor="middle" dominant-baseline="middle">'
                f'{_texto_svg(_recortar_texto(nodo["texto"]))}</text>')
        partes.append("</g>")

    bloques = [n for n, _, _ in colocados if n["tipo"] != "union"]
    secuencia = " → ".join(n["texto"] for n in bloques)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'viewBox="0 0 {_num(ancho)} {_num(alto)}" width="{_num(ancho)}" '
        f'style="max-width:100%;height:auto">'
        f'<title>Diagrama de flujo del algoritmo {_texto_svg(nombre)}, '
        f'{len(bloques)} bloques</title>'
        f'<desc>{_texto_svg(secuencia)}</desc>' + "".join(partes) + "</svg>")


def _svg_aviso(error):
    """Un diagrama que no se pudo dibujar sigue diciendo algo útil."""
    lineas = textwrap.wrap(f"{error.que_paso} {error.arreglalo}", width=64)[:4]
    filas = "".join(
        f'<text x="24" y="{62 + 20 * i}" font-family="system-ui,sans-serif" '
        f'font-size="13" fill="{GRIS}">{_texto_svg(t)}</text>'
        for i, t in enumerate(lineas))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'viewBox="0 0 {ANCHO} {70 + 20 * len(lineas)}" '
        f'style="max-width:100%;height:auto">'
        f'<title>No se pudo dibujar el diagrama</title>'
        f'<desc>{_texto_svg(error.error_corto)}</desc>'
        f'<rect x="2" y="2" width="{ANCHO - 4}" height="{66 + 20 * len(lineas)}" '
        f'rx="8" fill="#fdf4f3" stroke="{ROJO}"/>'
        f'<text x="24" y="34" font-family="system-ui,sans-serif" font-size="14" '
        f'font-weight="600" fill="{ROJO}">Todavía no puedo dibujar el diagrama '
        f'(línea {error.linea})</text>{filas}</svg>')


def diagrama(codigo, resaltar_nodo=None):
    """Devuelve el SVG del diagrama de flujo del pseudocódigo.

    `resaltar_nodo` pinta un bloque con borde rojo: es lo que usa el trazador
    para señalar en qué parte del diagrama va la ejecución. Nunca lanza: si el
    pseudocódigo no se puede analizar, devuelve un SVG con el mensaje del error.
    """
    try:
        alg = _analizar(codigo)
        items = _construir_layout(alg)
        return _emitir_svg(items, alg.nombre, resaltar_nodo)
    except _Alto as alto:
        return _svg_aviso(alto.error)
    except Exception as exc:  # pragma: no cover - red de seguridad
        return _svg_aviso(_err_motor(exc))


# ═════════════════════════════════════════════════════════════════════════════
# El trazador y el laboratorio (§8)
# ═════════════════════════════════════════════════════════════════════════════
# Cero JavaScript propio: en nbclassic el JS de una salida corre una sola vez,
# no sobrevive al guardado del notebook y se pierde al reejecutar la celda. Todo
# se re-pinta desde Python dentro de un Output, y `clear_output(wait=True)`
# evita el parpadeo en blanco que le haría perder el hilo visual al estudiante.

_SIN_VALOR = object()

_PANEL = ("flex:1 1 300px;min-width:280px;border:1px solid %s;border-radius:6px;"
          "padding:10px 12px;background:#fff" % BORDE)
# El panel del código pesa el doble: es el único que lleva líneas largas
# («Definir copias, total Como Entero») y, con los tres repartidos por igual, hay
# que leerlo con la barra de scroll horizontal, que es justo lo que no se quiere
# mientras se sigue la ejecución paso a paso.
_PANEL_CODIGO = _PANEL.replace("flex:1 1 300px", "flex:2 1 420px")
_ROTULO = ("font:12px system-ui,sans-serif;letter-spacing:1.5px;color:%s;"
           "margin-bottom:6px" % GRIS)


def _panel_codigo(lineas, actual, rotulo):
    filas = []
    for n, texto in enumerate(lineas, start=1):
        if n == actual:
            estilo = (f"background:#fff3cd;border-left:4px solid {AMBAR};"
                      f"padding-left:4px;color:{TINTA}")
            marca = "▶"
        elif n < actual:
            estilo = f"border-left:4px solid transparent;padding-left:4px;color:{GRIS}"
            marca = " "
        else:
            estilo = "border-left:4px solid transparent;padding-left:4px;color:#b0afad"
            marca = " "
        filas.append(f'<div style="{estilo}">'
                     f'<span style="color:#b0afad">{n:>2}</span> {marca} '
                     f'{_escapar(texto) or "&nbsp;"}</div>')
    return (f'<div style="{_ROTULO}">{rotulo}</div>'
            f'<div style="font-family:ui-monospace,Menlo,monospace;font-size:12.5px;'
            f'line-height:1.6;white-space:pre;overflow-x:auto">'
            + "".join(filas) + "</div>")


def _html_trazador(codigo, r, n):
    paso = r.pasos[n - 1]
    previo = r.pasos[n - 2].memoria if n >= 2 else {}
    cambiada = None
    for nombre, valor in paso.memoria.items():
        if previo.get(nombre, _SIN_VALOR) != valor:
            cambiada = nombre
    fuente, py, _, error = _traduccion(codigo)
    if error is not None:      # no debería pasar: r.ok ya se comprobó
        return error.html()

    consola = _escapar(paso.salida) or \
        '<span style="color:#5a5a5a">(todavía no se ha mostrado nada)</span>'
    izquierda = (
        f'<div style="{_PANEL_CODIGO}">'
        + _panel_codigo(fuente, paso.linea, "PSEUDOCÓDIGO")
        + f'<div style="border-top:1px dashed {BORDE};margin:10px 0 8px"></div>'
        + _panel_codigo(py, paso.linea, "PYTHON EQUIVALENTE") + "</div>")
    centro = (f'<div style="{_PANEL}"><div style="{_ROTULO}">DIAGRAMA</div>'
              + diagrama(codigo, resaltar_nodo=paso.nodo) + "</div>")
    derecha = (
        f'<div style="{_PANEL}"><div style="{_ROTULO}">MEMORIA</div>'
        + _html_tabla_memoria(paso.memoria, r.tipos, r.constantes, cambiada)
        + f'<div style="{_ROTULO};margin-top:12px">SALIDA HASTA AHORA</div>'
        f'<pre style="background:{TINTA};color:#d7ffd7;padding:8px 10px;'
        f'border-radius:6px;margin:0;font-size:12.5px;line-height:1.5;'
        f'white-space:pre-wrap;min-height:40px">{consola}</pre></div>')
    pie = (f'<div style="margin-top:10px;padding:10px 12px;background:{GRIS_CLARO};'
           f'border-left:4px solid {AZUL};border-radius:4px;'
           f'font:14px system-ui,sans-serif;color:{TINTA}">'
           f'<b style="color:{AZUL_OSC}">Qué acaba de pasar:</b> '
           f'{_escapar(paso.explicacion)}</div>')
    return (f'<div style="font-family:system-ui,-apple-system,sans-serif">'
            f'<div style="display:flex;flex-wrap:wrap;gap:14px">'
            f'{izquierda}{centro}{derecha}</div>{pie}</div>')


def _texto_trazador(r):
    """Versión sin frontend: la traza completa como texto. La ve el autograder."""
    filas = [f"{p.n:>3}. línea {p.linea:>3} | {p.texto.strip()}"
             f"\n      {p.explicacion}" for p in r.pasos]
    return "PRUEBA DE ESCRITORIO\n" + "\n".join(filas)


def trazador(codigo, entradas=()):
    """Prueba de escritorio paso a paso: pseudocódigo, diagrama y memoria.

    Es la pieza más visual del cuadernillo: en cada paso re-pinta los tres
    paneles completos, con la línea actual resaltada, el bloque del diagrama en
    rojo y la variable que acaba de cambiar marcada con una flecha.
    """
    r = ejecutar_pseudo(codigo, entradas)
    if not r.ok:
        _mostrar(r.error.html(), str(r.error))
        return
    if not r.pasos:
        _mostrar(f'<div style="color:{GRIS}">Este algoritmo no tiene ninguna '
                 f'instrucción que trazar.</div>',
                 "Este algoritmo no tiene ninguna instrucción que trazar.")
        return
    if not (HAY_WIDGETS and HAY_IPYTHON):
        # Sin widgets no se pierde la lección: se imprime la traza entera.
        print(_texto_trazador(r))
        return

    salida = W.Output()
    slider = W.IntSlider(value=1, min=1, max=len(r.pasos), description="Paso:",
                         continuous_update=False, layout=W.Layout(width="380px"))
    b_ant = W.Button(description="◀ Anterior", layout=W.Layout(width="120px"))
    b_sig = W.Button(description="Siguiente ▶", button_style="primary",
                     layout=W.Layout(width="120px"))
    b_ini = W.Button(description="⟲ Reiniciar", layout=W.Layout(width="120px"))

    def pintar(_=None):
        with salida:
            clear_output(wait=True)
            display(HTML(_html_trazador(codigo, r, slider.value)))

    slider.observe(pintar, names="value")
    b_ant.on_click(lambda _: setattr(slider, "value", max(slider.min, slider.value - 1)))
    b_sig.on_click(lambda _: setattr(slider, "value", min(slider.max, slider.value + 1)))
    b_ini.on_click(lambda _: setattr(slider, "value", 1))
    display(W.VBox([W.HBox([b_ant, slider, b_sig, b_ini]), salida]))
    pintar()


def laboratorio(codigo_inicial="", entradas=()):
    """Editor libre: el estudiante escribe su pseudocódigo y lo ejecuta aquí.

    Los cuatro botones escriben en la misma salida. El de «Trazar» abre el
    trazador con lo que acaba de escribir: es la costura que hace que el
    ejecutar, el traducir, el dibujar y el trazar se sientan una sola cosa.
    """
    if not (HAY_WIDGETS and HAY_IPYTHON):
        r = ejecutar_pseudo(codigo_inicial, entradas)
        r.imprimir()
        return

    editor = W.Textarea(value=codigo_inicial, rows=14,
                        layout=W.Layout(width="52%", height="300px"))
    editor.add_class("ava-mono")
    cola = W.Textarea(value="\n".join(str(v) for v in (entradas or ())), rows=6,
                      description="", layout=W.Layout(width="22%", height="300px"))
    salida = W.Output()
    b_ejecutar = W.Button(description="▶ Ejecutar", button_style="primary",
                          layout=W.Layout(width="130px"))
    b_python = W.Button(description="Ver Python", layout=W.Layout(width="130px"))
    b_diagrama = W.Button(description="Ver diagrama", layout=W.Layout(width="130px"))
    b_trazar = W.Button(description="Trazar", layout=W.Layout(width="130px"))

    def _entradas():
        return [x for x in cola.value.split("\n") if x.strip() != ""]

    def _con_salida(funcion):
        def envuelto(_):
            with salida:
                clear_output(wait=True)
                funcion()
        return envuelto

    b_ejecutar.on_click(_con_salida(
        lambda: ejecutar_pseudo(editor.value, _entradas()).imprimir()))
    b_python.on_click(_con_salida(
        lambda: display(HTML(
            f'<pre style="background:{GRIS_CLARO};border:1px solid {BORDE};'
            f'border-radius:6px;padding:10px 12px;font-size:13px;overflow-x:auto">'
            f'{_escapar(traducir_a_python(editor.value))}</pre>'))))
    b_diagrama.on_click(_con_salida(
        lambda: display(HTML(diagrama(editor.value)))))
    b_trazar.on_click(_con_salida(
        lambda: trazador(editor.value, _entradas())))

    display(HTML(
        f'<style>.ava-mono textarea{{font-family:ui-monospace,Menlo,monospace;'
        f'font-size:13px}}</style>'
        f'<div style="font:13px system-ui;color:{GRIS};margin-bottom:4px">'
        f'Tu pseudocódigo a la izquierda; a la derecha, lo que el usuario iba a '
        f'teclear (uno por línea).</div>'))
    display(W.VBox([W.HBox([editor, cola]),
                    W.HBox([b_ejecutar, b_python, b_diagrama, b_trazar]),
                    salida]))


def comparador(codigo):
    """Pseudocódigo y Python, fila por fila, con la nota de por qué cambia."""
    _mostrar(
        f'<div style="font:13px system-ui;color:{GRIS};margin:6px 0">'
        f'El mismo algoritmo dicho en dos idiomas. Cada fila del pseudocódigo '
        f'produce exactamente una fila de Python.</div>', "")
    tabla_dos_columnas(codigo)


# ═════════════════════════════════════════════════════════════════════════════
# Puente a Flowgorithm (§7.6)
# ═════════════════════════════════════════════════════════════════════════════
# Flowgorithm es una aplicación de escritorio solo para Windows y el AVA corre
# en un contenedor Linux servido por navegador: no se puede embeber. Lo que se
# puede hacer es que el estudiante llegue a la sala con el algoritmo ya pensado.

_TIPO_FLOW = {"Entero": "Integer", "Real": "Real", "Cadena": "String",
              "Logico": "Boolean"}


def _tokens_a_flow(toks):
    piezas = []
    for txt, clase in _piezas(toks):
        if clase == "op":
            txt = {"<>": "!=", "Y": "AND", "O": "OR", "NO": "NOT"}.get(txt, txt)
        elif clase == "valor" and txt in ("Verdadero", "Falso"):
            txt = "true" if txt == "Verdadero" else "false"
        piezas.append((txt, clase))
    return _unir(piezas)


def _bloques_flowgorithm(alg):
    """(clase, texto) de cada bloque, en el orden en que se arrastran."""
    bloques = []

    def recorrer(lista):
        for st in lista:
            if isinstance(st, _Definir):
                for nombre in st.nombres:
                    bloques.append(("Declare", nombre, _TIPO_FLOW[st.tipo]))
            elif isinstance(st, _Constante):
                bloques.append(("Assign", st.nombre, _tokens_a_flow(st.toks)))
            elif isinstance(st, _Asignar):
                bloques.append(("Assign", st.nombre, _tokens_a_flow(st.toks)))
            elif isinstance(st, _Leer):
                for nombre in st.nombres:
                    bloques.append(("Input", nombre, ""))
            elif isinstance(st, _Escribir):
                # En Flowgorithm los pedazos de texto se unen con &, no con coma.
                expr = " & ".join(_tokens_a_flow(t) for _, t in st.partes)
                bloques.append(("Output", expr, ""))
            elif isinstance(st, _Si):
                bloques.append(("If", _tokens_a_flow(st.toks), ""))
                recorrer(st.entonces)
                if st.sino:
                    bloques.append(("Else", "", ""))
                    recorrer(st.sino)
                bloques.append(("EndIf", "", ""))
            elif isinstance(st, _Mientras):
                bloques.append(("While", _tokens_a_flow(st.toks), ""))
                recorrer(st.cuerpo)
                bloques.append(("EndWhile", "", ""))
            elif isinstance(st, _Para):
                # Flowgorithm tiene su propio bloque For, con las mismas cuatro
                # casillas: variable, valor inicial, valor final y paso (más la
                # dirección, que allá se elige aparte y el paso va sin signo).
                ini, fin = _tokens_a_flow(st.toks_ini), _tokens_a_flow(st.toks_fin)
                paso = _paso_fijo(st)
                if paso is None:
                    cuanto, baja = _tokens_a_flow(st.toks_paso), False
                else:
                    cuanto, baja = _formatear(abs(paso)), paso < 0
                bloques.append(("For", f"{st.var} = {ini} to {fin}"
                                       + (" decreasing" if baja else "")
                                       + ("" if cuanto == "1" else f" step {cuanto}"),
                                (st.var, ini, fin, "dec" if baja else "inc",
                                 cuanto)))
                recorrer(st.cuerpo)
                bloques.append(("EndFor", "", ""))

    recorrer(alg.cuerpo)
    return bloques


def guion_flowgorithm(codigo):
    """Imprime la lista de bloques a arrastrar en Flowgorithm, en orden.

    Este es el respaldo que no puede fallar: no depende de que el formato del
    archivo `.fprg` coincida con la versión instalada en la sala.
    """
    try:
        alg = _analizar(codigo)
    except _Alto as alto:
        _mostrar(alto.error.html(), str(alto.error))
        return
    bloques = _bloques_flowgorithm(alg)
    ancho = max([len(b[1]) for b in bloques if b[0] == "Declare"] or [1])
    lineas = [f"GUION PARA FLOWGORITHM — {alg.nombre}",
              "Abre Flowgorithm, y entre el óvalo Main y el óvalo End inserta, "
              "en este orden:", ""]
    for i, (clase, uno, dos) in enumerate(bloques, start=1):
        if clase == "Declare":
            detalle = f"{uno.ljust(ancho)} : {dos}"
        elif clase == "Assign":
            detalle = f"{uno} = {dos}"
        else:
            detalle = uno
        lineas.append(f"  {i:>2}. {clase.ljust(9)}{detalle}".rstrip())
    lineas += ["", "Ojo: en Flowgorithm los textos se unen con &, no con coma."]
    print("\n".join(lineas))


def exportar_flowgorithm(codigo, ruta):
    """Escribe un archivo `.fprg` que se abre en Flowgorithm. Devuelve la ruta.

    Aviso: el formato está escrito contra `fileversion="4.2"`. Mientras no se
    valide contra la versión instalada en la sala de la UIS, el camino confiable
    es `guion_flowgorithm`, que no puede fallar porque no depende del formato.
    Devuelve "" si el pseudocódigo no se pudo analizar.
    """
    try:
        alg = _analizar(codigo)
    except _Alto as alto:
        _mostrar(alto.error.html(), str(alto.error))
        return ""
    cuerpo = []
    for clase, uno, dos in _bloques_flowgorithm(alg):
        if clase == "Declare":
            cuerpo.append(f'            <declare name="{_escapar(uno, True)}" '
                          f'type="{dos}" array="False" size=""/>')
        elif clase == "Assign":
            cuerpo.append(f'            <assign variable="{_escapar(uno, True)}" '
                          f'expression="{_escapar(dos, True)}"/>')
        elif clase == "Input":
            cuerpo.append(f'            <input variable="{_escapar(uno, True)}"/>')
        elif clase == "Output":
            cuerpo.append(f'            <output expression="{_escapar(uno, True)}" '
                          f'newline="True"/>')
        elif clase == "If":
            cuerpo.append(f'            <if expression="{_escapar(uno, True)}">'
                          f'<then/><else/></if>')
        elif clase == "While":
            cuerpo.append(f'            <while expression="{_escapar(uno, True)}">'
                          f'</while>')
        elif clase == "For":
            variable, ini, fin, direccion, cuanto = dos
            cuerpo.append(
                f'            <for variable="{_escapar(variable, True)}" '
                f'start="{_escapar(ini, True)}" end="{_escapar(fin, True)}" '
                f'direction="{direccion}" step="{_escapar(cuanto, True)}"></for>')
    xml = ('<?xml version="1.0"?>\n'
           '<flowgorithm fileversion="4.2">\n'
           '    <attributes>\n'
           f'        <attribute name="name" value="{_escapar(alg.nombre, True)}"/>\n'
           '        <attribute name="authors" value="UIS 41333"/>\n'
           '        <attribute name="created" value=""/>\n'
           '    </attributes>\n'
           '    <function name="Main" type="None" variable="">\n'
           '        <parameters/>\n'
           '        <body>\n' + "\n".join(cuerpo) + "\n"
           '        </body>\n'
           '    </function>\n'
           '</flowgorithm>\n')
    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(xml)
    except OSError as exc:
        _mostrar(f'<div style="color:{ROJO}">No pude escribir el archivo: '
                 f'{_escapar(str(exc))}</div>', f"No pude escribir el archivo: {exc}")
        return ""
    print(f"Archivo escrito: {ruta}\n"
          f"Descárgalo desde el explorador de Jupyter y ábrelo en Flowgorithm.\n"
          f"Si esa versión no lo abre, usa guion_flowgorithm(codigo).")
    return ruta


# ═════════════════════════════════════════════════════════════════════════════
# La cola de entradas para Python (§11.2)
# ═════════════════════════════════════════════════════════════════════════════
# `input()` bloquea el kernel esperando a alguien que teclee. En un cuadernillo
# autocalificado eso rompe tres cosas a la vez: la autocalificación (nbgrader
# corre headless), la telemetría (el evento de la celda nunca cierra) y la
# experiencia (un «Run All» deja el kernel colgado). Se sustituye por una cola
# que el estudiante declara de antemano, que además es la definición de «caso de
# prueba»: el código no cambia ni una letra, solo de dónde salen los datos.

_COLA = []
_INPUT_REAL = builtins.input


def _input_de_mentiras(prompt=""):
    if prompt:
        print(prompt, end="")
    if not _COLA:
        raise EOFError(
            "Tu programa pidió un dato con input(), pero la cola de entradas "
            "está vacía.\n"
            "Llama antes a  ps.usar_entradas([...])  con tantos valores como "
            "input() tengas.")
    valor = _COLA.pop(0)
    print(valor)          # el eco: se ve igual que si alguien lo hubiera tecleado
    return valor


def usar_entradas(valores):
    """Instala el `input()` de mentiras y carga la cola con estos valores."""
    global _COLA
    _COLA = [str(v) for v in valores]
    builtins.input = _input_de_mentiras


def restaurar_input():
    """Devuelve `input()` al de siempre."""
    builtins.input = _INPUT_REAL


class entradas:
    """Context manager para las celdas de prueba: `with ps.entradas([...]):`.

    Se prefiere en los tests porque restaura `input()` incluso si el assert
    falla, y así una celda no le deja el kernel trucado a la siguiente.
    """

    def __init__(self, valores):
        self.valores = valores

    def __enter__(self):
        usar_entradas(self.valores)
        return self

    def __exit__(self, *_e):
        restaurar_input()
        return False
