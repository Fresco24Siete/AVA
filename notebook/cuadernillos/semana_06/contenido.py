"""Contenido propio de la SEMANA 6: «Buscar y ordenar».

Qué es esto
-----------
Aquí vive solo lo de esta semana: los quices del calentamiento, la lista
dibujada con sus índices, y el medidor de operaciones — que es el corazón
pedagógico del cuadernillo.

Un límite que condiciona el diseño: **el intérprete de pseudocódigo del curso no
maneja listas** (`pseudo_uis` solo conoce variables sueltas). Así que en esta
semana el pseudocódigo se escribe y se lee, como pide el temario, pero no se
ejecuta; todo lo calificable es Python. Se dice explícitamente en el cuadernillo
para que nadie pierda media hora peleando con el motor.

Y una decisión pedagógica: de los cuatro ordenamientos del temario, el
estudiante **escribe** selección y burbuja, y **mide** merge y quicksort sin
escribirlos. Los dos últimos son recursivos, y la recursión no se ha enseñado.
Pedir que los implemente sería romper la regla de no usar lo que no se ha visto;
pero medirlos sí se puede, y es donde está la lección que importa.

Dependencias: biblioteca estándar. Sin matplotlib.
"""
from IPython.display import HTML as _HTML6, display as _display6

_S6_VIOLETA = "#4a3aa7"
_S6_AZUL = "#2a78d6"
_S6_VERDE = "#0ca30c"
_S6_ROJO = "#d03b3b"
_S6_AMBAR = "#eda100"
_S6_GRIS = "#52514e"
_S6_BORDE = "#dfe3e8"
_S6_FUENTE = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
_S6_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def _s6_pintar(html):
    _display6(_HTML6(html))


def _s6_motor():
    return globals().get("ava")


def _s6_escapar(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# =============================================================================
# Calentamiento
# =============================================================================
def quiz_input():
    ava = _s6_motor()
    if ava is None:
        return
    return ava.quiz(
        "s6_input", 5,
        "El usuario escribe 25 en un `input()`. ¿Qué tipo tiene lo que llega?",
        ["int", "float", "str", "Depende de lo que escriba"],
        2,
        "`input()` devuelve SIEMPRE texto, aunque el usuario escriba números. "
        "Por eso hay que convertirlo con `int()` o `float()` antes de calcular.",
    )


def quiz_division():
    ava = _s6_motor()
    if ava is None:
        return
    return ava.quiz(
        "s6_division", 5,
        "¿Qué tipo devuelve `8 / 2` en Python?",
        ["int, porque da 4 exacto", "float, siempre", "str", "Depende"],
        1,
        "La división `/` devuelve decimales SIEMPRE, aunque la cuenta sea "
        "exacta: `8 / 2` es `4.0`, no `4`. El entero lo daría `8 // 2`.",
    )


def quiz_estructura():
    ava = _s6_motor()
    if ava is None:
        return
    return ava.quiz(
        "s6_estructura", 5,
        "En un ciclo, ¿dónde se crea el acumulador?",
        ["Dentro del ciclo, en cada vuelta", "Antes del ciclo, una sola vez",
         "Después del ciclo", "Da igual"],
        1,
        "Si lo creas dentro, se reinicia en cada vuelta y nunca acumula nada. "
        "Va antes, una sola vez.",
    )


# =============================================================================
# La lista, dibujada con sus índices
# =============================================================================
def ver_lista(datos, resaltar=None, titulo=""):
    """Dibuja una lista con su índice debajo de cada casilla.

    Existe porque el error de la semana es el de índice: el primer elemento es
    el CERO, y verlo dibujado lo cura más rápido que leerlo tres veces.
    """
    celdas, indices = [], []
    for i, valor in enumerate(datos):
        activo = (resaltar is not None and i == resaltar)
        fondo = _S6_AMBAR if activo else "#ffffff"
        color = "#ffffff" if activo else "#0b0b0b"
        celdas.append(
            f'<td style="border:1px solid {_S6_BORDE};padding:9px 16px;'
            f'text-align:center;font-family:{_S6_MONO};font-size:14px;'
            f'background:{fondo};color:{color}">{_s6_escapar(valor)}</td>')
        indices.append(
            f'<td style="padding:3px 16px;text-align:center;'
            f'font:12px {_S6_MONO};color:'
            f'{_S6_AMBAR if activo else _S6_GRIS}">{i}</td>')
    cabecera = (f'<div style="font:600 13.5px {_S6_FUENTE};color:{_S6_VIOLETA};'
                f'margin-bottom:4px">{_s6_escapar(titulo)}</div>' if titulo else "")
    _s6_pintar(
        f'<div style="margin:10px 0">{cabecera}'
        f'<table style="border-collapse:collapse">'
        f'<tr>{"".join(celdas)}</tr><tr>{"".join(indices)}</tr></table>'
        f'<div style="font:12px {_S6_FUENTE};color:{_S6_GRIS};margin-top:3px">'
        f'La fila de abajo es el índice. El primero es el <b>cero</b>.</div></div>')


# =============================================================================
# El medidor de operaciones
# =============================================================================
# Esta es la pieza que justifica el cuadernillo entero. La complejidad no se
# entiende con una fórmula: se entiende viendo que un algoritmo hace 500.000
# comparaciones donde otro hace 20, con los mismos datos.
def _s6_lineal(datos, buscado):
    pasos = 0
    for i in range(len(datos)):
        pasos += 1
        if datos[i] == buscado:
            return i, pasos
    return -1, pasos


def _s6_binaria(datos, buscado):
    pasos, izq, der = 0, 0, len(datos) - 1
    while izq <= der:
        pasos += 1
        medio = (izq + der) // 2
        if datos[medio] == buscado:
            return medio, pasos
        if datos[medio] < buscado:
            izq = medio + 1
        else:
            der = medio - 1
    return -1, pasos


def comparar_busquedas(tamano=1000):
    """Busca el PEOR caso en una lista ordenada y cuenta pasos con cada método."""
    datos = list(range(tamano))
    buscado = tamano - 1                     # el último: el peor caso de la lineal
    _, pasos_l = _s6_lineal(datos, buscado)
    _, pasos_b = _s6_binaria(datos, buscado)
    filas = [("Búsqueda lineal", pasos_l, _S6_ROJO,
              "mira uno por uno desde el principio"),
             ("Búsqueda binaria", pasos_b, _S6_VERDE,
              "parte la lista por la mitad cada vez")]
    cuerpo = "".join(
        f'<tr><td style="padding:8px 16px;font:600 14px {_S6_FUENTE};color:{color};'
        f'border-bottom:1px solid {_S6_BORDE}">{nombre}</td>'
        f'<td style="padding:8px 16px;text-align:right;font-family:{_S6_MONO};'
        f'font-size:15px;font-weight:600;color:{color};'
        f'border-bottom:1px solid {_S6_BORDE}">{pasos}</td>'
        f'<td style="padding:8px 16px;font:13px {_S6_FUENTE};color:{_S6_GRIS};'
        f'border-bottom:1px solid {_S6_BORDE}">{que}</td></tr>'
        for nombre, pasos, color, que in filas)
    veces = pasos_l / pasos_b if pasos_b else 0
    _s6_pintar(
        f'<div style="font:600 14px {_S6_FUENTE};color:{_S6_VIOLETA};margin:8px 0 4px">'
        f'Buscar el último elemento en una lista ordenada de {tamano:,} números'
        f'</div>'
        f'<table style="border-collapse:collapse;border:1px solid {_S6_BORDE}">'
        f'{cuerpo}</table>'
        f'<p style="font:14px {_S6_FUENTE};max-width:640px;margin-top:8px">'
        f'La binaria hizo <b>{veces:.0f} veces</b> menos trabajo. Y cuanto más '
        f'grande la lista, mayor la diferencia: con un millón de datos la lineal '
        f'necesita un millón de pasos y la binaria unos veinte.</p>'.replace(",", "."))


def _s6_seleccion(datos):
    datos, comparaciones = list(datos), 0
    for i in range(len(datos)):
        menor = i
        for j in range(i + 1, len(datos)):
            comparaciones += 1
            if datos[j] < datos[menor]:
                menor = j
        datos[i], datos[menor] = datos[menor], datos[i]
    return datos, comparaciones


def _s6_burbuja(datos):
    datos, comparaciones = list(datos), 0
    n = len(datos)
    for i in range(n):
        for j in range(n - i - 1):
            comparaciones += 1
            if datos[j] > datos[j + 1]:
                datos[j], datos[j + 1] = datos[j + 1], datos[j]
    return datos, comparaciones


def comparar_ordenamientos(tamano=200):
    """Ordena la MISMA lista con los dos métodos y cuenta comparaciones.

    Se usa una lista al revés —el peor caso— para que la diferencia con lo que
    hace Python por dentro sea evidente y no una casualidad de los datos.
    """
    original = list(range(tamano, 0, -1))
    _, c_sel = _s6_seleccion(original)
    _, c_bur = _s6_burbuja(original)
    filas = [("Selección", c_sel, _S6_AMBAR),
             ("Burbuja", c_bur, _S6_ROJO),
             ("sorted() de Python", tamano, _S6_VERDE)]
    cuerpo = "".join(
        f'<tr><td style="padding:8px 16px;font:600 14px {_S6_FUENTE};color:{color};'
        f'border-bottom:1px solid {_S6_BORDE}">{nombre}</td>'
        f'<td style="padding:8px 16px;text-align:right;font-family:{_S6_MONO};'
        f'font-size:15px;font-weight:600;border-bottom:1px solid {_S6_BORDE}">'
        f'{n:,}</td></tr>'.replace(",", ".")
        for nombre, n, color in filas)
    _s6_pintar(
        f'<div style="font:600 14px {_S6_FUENTE};color:{_S6_VIOLETA};margin:8px 0 4px">'
        f'Ordenar {tamano} números que vienen al revés — comparaciones que hace cada uno'
        f'</div>'
        f'<table style="border-collapse:collapse;border:1px solid {_S6_BORDE}">'
        f'{cuerpo}</table>'
        f'<p style="font:13.5px {_S6_FUENTE};color:{_S6_GRIS};max-width:660px;'
        f'margin-top:8px">La cifra de <code>sorted()</code> es orientativa: por '
        f'dentro usa un método más listo, de la familia de merge sort. Lo que '
        f'importa no es el número exacto sino el orden de magnitud — y que al '
        f'doblar los datos, los dos primeros multiplican su trabajo por cuatro, '
        f'y el tercero no.</p>')
