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
_INSTRUCCIONES = ("Definir", "Constante", "Leer", "Escribir", "Si", "Mientras")
# Universo para el «¿querías decir…?» de difflib: instrucciones + cierres.
_PALABRAS_CLAVE = _INSTRUCCIONES + (
    "Mostrar", "Algoritmo", "FinAlgoritmo", "Entonces", "Sino", "FinSi",
    "Hacer", "FinMientras", "Como",
)

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
        "Mientras/FinMientras.",
        f"escribe {cierre} después de la última instrucción que quieras "
        + ("repetir." if cierre == "FinMientras" else "meter dentro del bloque."))


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


def _ps09(linea, texto):
    return Error(
        "PS09", linea, texto,
        "tu algoritmo lleva 10 000 pasos y no termina: probablemente es un "
        "ciclo infinito.",
        "la condición del Mientras nunca se vuelve falsa porque nada dentro del "
        "ciclo la cambia.",
        "asegúrate de que alguna variable de la condición cambie dentro del ciclo.")


def _ps10(palabra, falta, linea, texto):
    if falta == "Entonces":
        por_que = ("la palabra Entonces marca dónde termina la pregunta y dónde "
                   "empieza lo que se hace si la respuesta es sí.")
        arreglo = "Si saldo > 0 Entonces"
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


def _ps14(nombre, linea, texto, col):
    sano = _RE_ACENTO.sub(lambda m: _SIN_TILDE.get(m.group(), m.group()),
                          nombre).replace(" ", "_")
    return Error(
        "PS14", linea, texto,
        f"'{nombre}' no sirve como nombre de variable.",
        "los nombres van sin espacios y sin tildes. La costumbre es unir las "
        "palabras con guion bajo.",
        sano, col, len(nombre))


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

_CIERRES = {"finsi", "sino", "finmientras", "finalgoritmo"}


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

    # -- utilidades ---------------------------------------------------------
    def _preparar(self):
        for n, texto in enumerate(self.fuente, start=1):
            self.lineas.append((n, texto, _tokenizar_linea(texto, n)))

    def _actual(self):
        return self.lineas[self.i] if self.i < len(self.lineas) else None

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
        if _norm(primera[2].split()[0]) != "algoritmo":
            raise _Alto(_ps13(primera[0], primera[1]))

        self._preparar()
        self._saltar_vacias()
        n, texto, toks = self._actual()
        if len(toks) < 2 or toks[1].tipo != "ident":
            raise _Alto(Error(
                "PS13", n, texto,
                "escribiste 'Algoritmo' pero no le pusiste nombre.",
                "esa línea le pone nombre a lo que estás resolviendo. En el "
                "diagrama de flujo es el óvalo de INICIO.",
                "Algoritmo CostoDeFotocopias", 0, len(toks[0].valor)))
        nombre = toks[1].valor
        self._validar_nombre(nombre, toks[1], texto)
        if len(toks) > 2:
            raise _Alto(self._sobra(toks[2], texto))
        self.i += 1

        cuerpo = self._bloque("Algoritmo", n, "FinAlgoritmo", ("finalgoritmo",))
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
                if palabra_apertura != "Algoritmo":
                    # Estamos dentro de un Si o de un Mientras y aparece el
                    # cierre de un bloque de más afuera: lo que falta no es esta
                    # línea, es el FinSi/FinMientras que nunca se escribió. Se
                    # acusa la apertura, que es donde el estudiante tiene que
                    # mirar.
                    raise _Alto(_ps03(palabra_apertura, linea_apertura, cierre,
                                      n, texto))
                # Cierra un bloque que nadie abrió: se dice al derecho.
                raise _Alto(Error(
                    "PS03", n, texto,
                    f"escribiste '{toks[0].valor}' pero aquí no hay ningún "
                    f"bloque abierto que cerrar.",
                    "todo bloque que se abre se cierra: Algoritmo/FinAlgoritmo, "
                    "Si/FinSi, Mientras/FinMientras. Y al revés: no se cierra lo "
                    "que no se abrió.",
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
                "mientras": self._mientras,
            }.get(clave)
            if despacho:
                return despacho()
            if len(toks) >= 2 and toks[1].es_op("<-"):
                return self._asignar()
            if len(toks) >= 2 and toks[1].es_op("="):
                izq = cabeza.valor
                der = _tokens_a_texto(toks[2:]) or "…"
                raise _Alto(_ps02(n, texto, toks[1].col, izq, der))
            if len(toks) >= 2 and toks[1].tipo == "ident":
                # Dos identificadores seguidos al principio de la línea = un
                # nombre con espacio en medio. Es el caso de PS14.
                raise _Alto(_ps14(f"{cabeza.valor} {toks[1].valor}", n, texto,
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
                raise _Alto(_ps14(f"{toks[j].valor} {toks[j + 1].valor}", n,
                                  texto, toks[j].col))
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
    def _paso(self, st, explicacion):
        self.pasos.append(Paso(len(self.pasos) + 1, st.linea, st.texto.rstrip(),
                               dict(self.memoria), st.id_nodo, explicacion,
                               self.largo))

    def _tic(self, st):
        if self.contador >= MAX_PASOS:
            raise _Alto(_ps09(st.linea, st.texto))
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
                return
            self._lista(st.cuerpo)

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
            elif isinstance(st, _Mientras):
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
}


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
            elif isinstance(st, _Mientras):
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
