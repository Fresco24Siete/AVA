"""Constructor de cuadernillos: arma el .ipynb con los metadatos que el AVA espera.

Un cuadernillo del AVA no es un notebook cualquiera. Tiene que cumplir tres
contratos a la vez, y este módulo es el único sitio donde eso está escrito:

1. **nbgrader** — cada ejercicio calificable son dos celdas: la de solución
   (`grade_id: ejercicio_N`, `solution: true`) y la de prueba
   (`grade_id: test_ejercicio_N`, `grade: true`, `points: N`). El instructor
   autora con la solución puesta entre los delimitadores; «Generate» la borra y
   deja el enunciado.
2. **Telemetría** — `custom.js` solo emite eventos desde celdas de prueba cuyo
   `grade_id` empieza por `test_`. Si el par no está bien formado, el ejercicio
   es invisible para la analítica (P6).
3. **Tutor IA** — se habilita por cuadernillo con `metadata.tutor_ia.enabled`.

Y una restricción de entrega: al alumno le llega **un solo archivo**
(`entregar-cuadernillo` copia el .ipynb y nada más). Por eso los diagramas SVG y
el motor lúdico se incrustan dentro del propio notebook.
"""
import ast
import base64
import json
import hashlib
import os
import re
import zlib

AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA_MOTOR = os.path.join(AQUI, "motor", "ava_motor.py")
RUTA_ESQUEMA = os.path.join(AQUI, "..", "..", "database", "schema_v2.sql")


def catalogo_competencias():
    """{codigo: (codigo_oficial, descripcion)} leido de database/schema_v2.sql.

    Se lee del esquema en vez de copiarlo aqui porque es el mismo texto que el
    panel le ensena al docente: dos copias acabarian diciendo cosas distintas
    sobre la misma competencia, y nadie sabria cual vale.
    """
    try:
        with open(RUTA_ESQUEMA, encoding="utf-8") as f:
            sql = f.read()
    except OSError:
        return {}
    filas = re.findall(
        r"\('(I\d)','(m[A-Z]+\d+)','([^']+)'\)", sql)
    return {cod: (oficial, desc) for cod, oficial, desc in filas}


def huella(ejercicio, llave, valor):
    """La huella de una respuesta correcta, calculada al CONSTRUIR.

    Tiene que dar exactamente lo mismo que `ava_motor.huella`, que es la que
    corre dentro del cuadernillo. No se importa de allí porque ava_motor trae
    IPython y aquí, construyendo, no hay IPython.

    Que sean dos copias no se deja al azar: backend/tests/telemetria/
    prueba_huella.py comprueba que coinciden. Si se separaran, el cuadernillo
    diría que TODAS las respuestas están mal y nadie entendería por qué.
    """
    return hashlib.sha256(
        f"{ejercicio}|{llave}|{valor!r}".encode("utf-8")
    ).hexdigest()[:16]
RUTA_SVG = os.path.join(AQUI, "diagramas", "svg")

# Delimitadores en español; deben coincidir con los de notebook/nbgrader_config.py.
# Si no coinciden, «Generate» NO borra la solución y el alumno la recibe hecha.
INICIO_SOL = "### INICIO SOLUCION"
FIN_SOL = "### FIN SOLUCION"
INICIO_TEST_OCULTO = "### INICIO PRUEBAS OCULTAS"
FIN_TEST_OCULTO = "### FIN PRUEBAS OCULTAS"


def cargar_svg(nombre):
    """Devuelve el SVG ya renderizado por diagramas/render.py, listo para incrustar."""
    ruta = os.path.join(RUTA_SVG, nombre + ".svg")
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            f"Falta el diagrama '{nombre}'. Créalo en diagramas/mmd/{nombre}.mmd "
            f"y ejecuta: python3 notebook/cuadernillos/diagramas/render.py"
        )
    with open(ruta, encoding="utf-8") as f:
        return f.read().strip()


def _comprimir(fuente):
    return base64.b64encode(zlib.compress(fuente.encode("utf-8"), 9)).decode("ascii")


def _incrustar(rutas, comprimido=True):
    """Código que carga los módulos del cuadernillo en la primera celda.

    Se incrustan y no se importan porque al alumno le llega **un solo archivo**:
    no hay dónde poner un `.py` al lado. La alternativa —copiarlos a
    `/etc/jupyter` en la imagen, que `PYTHONPATH` ya cubre— dejaría celdas más
    limpias, pero ata cada cuadernillo publicado a la versión de la imagen: al
    reconstruirla, los cuadernillos ya entregados cambiarían de motor sin avisar.

    Comprimido, la celda son cinco líneas (una larguísima, que el editor no
    parte) en vez de miles de fontanería. No es ofuscación: la celda dice dónde
    está cada fuente. Con `comprimido=False` se incrusta el código legible, que
    es como se depura.
    """
    fuentes = []
    for ruta in rutas:
        with open(ruta, encoding="utf-8") as f:
            fuentes.append((os.path.basename(ruta), f.read()))

    if not comprimido:
        return "\n\n".join(
            f"# ---- {nombre} " + "-" * max(0, 60 - len(nombre)) + f"\n{src}"
            for nombre, src in fuentes
        )

    lineas = [
        "# Motor del cuadernillo: barra de progreso, pistas y verificadores.",
        "# No necesitas leer este codigo. Ejecutalo una vez (Shift+Enter) y sigue.",
        "# Codigo fuente legible en el repositorio del curso:",
    ]
    lineas += [f"#   notebook/cuadernillos/**/{nombre}" for nombre, _ in fuentes]
    lineas.append("import base64, zlib")
    for _, src in fuentes:
        lineas.append(
            f'exec(zlib.decompress(base64.b64decode("{_comprimir(src)}")).decode("utf-8"))'
        )
    return "\n".join(lineas) + "\n"


# -- Guardas de las celdas de prueba ------------------------------------------
#
# 2026-10-05. El profesor avisó de errores en los cuadernillos 4 y 6 y la
# telemetría enseñó, entre los de verdad, uno que no era del material: alumnos
# que ejecutaban la celda de prueba sin haber ejecutado antes la primera celda
# (8 `NameError: name 'ps' is not defined` de 3 alumnos en la semana 04) o su
# propia celda. Para quien lleva cuatro semanas programando, un NameError sobre
# un nombre que él no escribió no dice «te faltó ejecutar algo»: dice «el
# cuadernillo está roto», y eso fue lo que reportaron.
#
# Las INSTRUCCIONES del principio ya piden ejecutar en orden, pero se leen una
# vez y el error aparece veinte minutos después. Así que cada celda de prueba
# empieza comprobándolo ella misma y, si falta algo, dice QUÉ celda ejecutar
# (con las palabras que el alumno tiene en pantalla: ver `guardas_de_prueba`).
#
# Van escritas dentro de la celda y no en el motor por una razón obvia: el caso
# que atienden es justo el de que el motor no esté cargado.
#
# El nombre que se mira es `ava`. Se comprobó ejecutando la primera celda de
# los seis cuadernillos: `ava` queda en globals() en todos (lo crea
# `_fuente_arranque`, DESPUÉS de cargar el motor y los módulos de la semana, así
# que si `ava` existe también existe todo lo demás). `ps`, el que salía en el
# NameError, no sirve: las semanas 01 y 06 no cargan el intérprete.
NOMBRE_DEL_ARRANQUE = "ava"


def nombre_de_la_respuesta(partida, pruebas):
    """El nombre que la celda del alumno define y la prueba usa, o None.

    Se deduce de la `partida`: la primera función (`def nombre(`) o la primera
    asignación (`NOMBRE = ...`) de nivel superior. Con una condición más: que
    las pruebas visibles usen ese nombre. Sin ella la guarda apuntaría mal en
    las partidas que empiezan dando un dato —`datos = {...}` en semana_02 E6,
    `dias = [...]` en semana_06 E1— y, peor, podría exigir un nombre que la
    prueba nunca pidió. Con ella la guarda no puede hacer fallar a nadie que no
    fuera a fallar igual: si el nombre falta, la prueba ya daba NameError; lo
    único que cambia es el mensaje.

    Se mira el árbol de sintaxis y no el texto, porque hay partidas que son una
    cadena con pseudocódigo dentro y una línea suya en la columna 0 no es una
    asignación de Python. Si la partida o las pruebas no se pueden analizar, o
    ningún nombre cumple, devuelve None y ese ejercicio se queda sin esta
    guarda: es preferible a una que mienta.
    """
    try:
        cuerpo = ast.parse(partida).body
        usados = {n.id for n in ast.walk(ast.parse(pruebas))
                  if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    except SyntaxError:
        return None
    for nodo in cuerpo:
        if isinstance(nodo, ast.FunctionDef):
            definidos = [nodo.name]
        elif isinstance(nodo, ast.Assign):
            definidos = [t.id for t in nodo.targets if isinstance(t, ast.Name)]
        else:
            continue
        for nombre in definidos:
            if nombre in usados:
                return nombre
    return None


def nombres_que_deja_el_arranque(rutas):
    """Los nombres que la primera celda ya deja en globals() antes de que el
    alumno escriba nada: todo lo que definen, a nivel superior, los módulos
    incrustados.

    Hace falta porque el arranque los carga con `exec()` en el MISMO espacio de
    nombres del cuadernillo. Si la respuesta de un ejercicio se llama igual que
    uno de ellos, pasan dos cosas: la guarda «ejecuta TU celda» no puede saltar
    nunca (el nombre existe siempre), y la respuesta del alumno PISA un nombre
    del motor. No es hipotético: al poner las guardas (2026-10-05) apareció en
    semana_05 E1, cuya respuesta se llama `TIPOS`, igual que la tupla de tipos
    de `pseudo_uis.py`. Tras ejecutar su celda, el intérprete contesta «no
    conozco el tipo 'Entero'» a cualquier `Definir`. Hoy no se nota porque
    semana_05 no ejecuta pseudocódigo después de ese ejercicio.

    No se entra en funciones ni en clases: lo que se define dentro no llega a
    globals().
    """
    nombres = set()

    def recoger(nodos):
        for nodo in nodos:
            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nombres.add(nodo.name)
                continue
            if isinstance(nodo, (ast.Import, ast.ImportFrom)):
                nombres.update((a.asname or a.name).split(".")[0] for a in nodo.names)
                continue
            for campo in ("targets", "target"):
                valor = getattr(nodo, campo, None)
                for destino in (valor if isinstance(valor, list) else [valor]):
                    if destino is not None:
                        nombres.update(n.id for n in ast.walk(destino)
                                       if isinstance(n, ast.Name))
            # if / try / for / with de nivel superior: su cuerpo también es global.
            for campo in ("body", "orelse", "finalbody"):
                recoger(getattr(nodo, campo, []) or [])
            for manejador in getattr(nodo, "handlers", []) or []:
                recoger(manejador.body)

    for ruta in rutas:
        with open(ruta, encoding="utf-8") as f:
            recoger(ast.parse(f.read()).body)
    return nombres


def guardas_de_prueba(nombre_respuesta=None):
    """Las líneas con que empieza toda celda de prueba (ver el comentario de arriba).

    Son `assert` y no `raise` a propósito: es la forma que el alumno ya ve en el
    resto de la celda, y a la telemetría le llega como un AssertionError con un
    mensaje que se puede contar, en vez de un NameError que no dice de qué fue.

    El texto no lleva `print(`: `ejercicio()` decide si añade la despedida
    mirando si la celda ya imprime algo.

    El primer mensaje NO dice «ejecuta la primera celda de código», que es lo
    que decía en su primera versión (2026-10-05, corregido el mismo día en la
    revisión). El alumno no ve esa celda como código: va etiquetada
    `ava-motor`, `notebook/custom.js` (esconder_andamiaje) le esconde la entrada
    y deja la línea «Celda del cuadernillo. ver el codigo», y una vez ejecutada
    el motor (`motor/ava_motor.py`, _HTML_ESCONDER) deja como salida «Motor del
    cuadernillo activo», texto que se guarda en el .ipynb y sigue a la vista
    con un kernel nuevo aunque ya no sea verdad. La primera celda de código que
    él VE es `portada()` (`iniciar()` en la semana 01); quien obedecía el
    mensaje la ejecutaba, recibía `NameError: name 'portada' is not defined` y
    al volver a la prueba le salía la misma guarda. Por eso el mensaje:
      - pone primero el camino del menú, que no depende de encontrar nada;
      - nombra la celda por los dos textos que el alumno tiene en pantalla, y
        dice «la primera» porque las celdas `ava-oculta` (quices) llevan el
        mismo rótulo «Celda del cuadernillo» y la del motor va antes que todas;
      - avisa de que el rótulo «activo» puede estar mintiendo.
    Si alguno de esos dos rótulos cambia en custom.js o en ava_motor.py, hay
    que cambiarlo también aquí.
    """
    lineas = [
        "# Antes de revisar tu respuesta: ¿estan ejecutadas las celdas de arriba?",
        f'assert "{NOMBRE_DEL_ARRANQUE}" in globals(), (',
        '    "El motor del cuadernillo no esta cargado en esta sesion (aunque arriba "',
        '    "diga \'Motor del cuadernillo activo\'). Para cargarlo: menu Kernel -> "',
        '    "Restart & Run All. O, sin reiniciar: sube al principio del cuadernillo, "',
        '    "haz clic sobre la primera linea que dice \'Celda del cuadernillo\' o "',
        '    "\'Motor del cuadernillo activo\' y pulsa Shift+Enter. Despues ejecuta "',
        '    "otra vez tu celda y esta.")',
    ]
    if nombre_respuesta:
        lineas += [
            f'assert "{nombre_respuesta}" in globals(), (',
            f'    "No encuentro `{nombre_respuesta}`. Ejecuta primero TU celda (la de arriba, donde "',
            '    "va tu respuesta) y despues esta. Si tu celda dio error, arreglalo antes; y "',
            f'    "no le cambies el nombre a `{nombre_respuesta}`.")',
        ]
    # La línea en blanco separa las guardas de la prueba: quien lea la celda
    # tiene que ver dónde acaba «¿ejecutaste lo de arriba?» y dónde empieza lo
    # que se le exige a su respuesta.
    return "\n".join(lineas) + "\n\n"


class Cuadernillo:
    """Acumula celdas y las escribe como un .ipynb válido para el AVA."""

    def __init__(self, codigo, titulo, semana, meta_xp=100,
                 insignia="Sesión completada", tutor_ia=True, motor_comprimido=True,
                 modulos=()):
        self.codigo = codigo          # ej. "semana_01": es el cuadernillo_id de nbgrader
        self.titulo = titulo
        self.semana = semana
        self.meta_xp = meta_xp
        self.insignia = insignia
        self.tutor_ia = tutor_ia
        self.motor_comprimido = motor_comprimido
        # Módulos propios de la semana (contenido, mini-intérprete…) que se
        # incrustan junto al motor. Rutas a .py; se cargan en el mismo espacio de
        # nombres, en orden, después del motor.
        self.modulos = list(modulos)
        self.celdas = []
        self._ejercicios = []         # (numero, puntos) para el resumen final
        self._pistas = {}             # clave -> pistas; se inyectan en el arranque
        # exercise_id -> [competencias]. No va dentro del notebook ni viaja con
        # cada intento: se emite aparte y se carga al backend, que lo resuelve
        # por JOIN. Así, corregir una etiqueta corrige todo el histórico.
        self.competencias = {}
        self._i_arranque = None       # dónde va la celda del motor
        self._nota_respuesta_puesta = False   # «Cómo se responde», una sola vez
        # Ejercicios cuya celda de prueba va sin la guarda «ejecuta TU celda»:
        # los que no dan un nombre limpio en su partida, y los que dan uno que
        # el arranque ya define (clave, nombre). Se avisa de los dos al escribir.
        self._sin_guarda_respuesta = []
        self._respuestas_que_pisan = []
        self._nombres_arranque = None     # se calcula una vez, al primer ejercicio

    # -- Celdas simples ------------------------------------------------------
    def md(self, texto):
        """Celda de texto."""
        self.celdas.append({
            "cell_type": "markdown", "metadata": {}, "source": _lineas(texto),
        })
        return self

    # Llamadas cuyo código NO puede quedar a la vista: llevan la respuesta
    # correcta como argumento, o son 25 KB de SVG. El motor esconde la celda en
    # cuanto se ejecuta, pero eso llega tarde para quien va leyendo sin ejecutar;
    # la etiqueta permite que custom.js la esconda desde que se abre el notebook.
    _DELATORAS = ("quiz(", "ordenar(", "ava.quiz(", "ava.ordenar(", "ava.figura(")

    def code(self, fuente, editable=True, etiquetas=()):
        """Celda de código sin calificación (demostración, laboratorio, juego)."""
        meta = {}
        etiquetas = list(etiquetas)
        if any(d in fuente for d in self._DELATORAS) and "ava-oculta" not in etiquetas:
            etiquetas.append("ava-oculta")
        if etiquetas:
            meta["tags"] = list(etiquetas)
        if not editable:
            meta["editable"] = False
            meta["deletable"] = False
        self.celdas.append({
            "cell_type": "code", "metadata": meta, "execution_count": None,
            "outputs": [], "source": _lineas(fuente),
        })
        return self

    def seccion(self, numero, titulo, minutos=None, entradilla=""):
        """Encabezado de una de las secciones de la anatomía del cuadernillo."""
        tiempo = f" · {minutos} min" if minutos else ""
        cuerpo = f"---\n\n## {numero}. {titulo}{tiempo}\n"
        if entradilla:
            cuerpo += "\n" + entradilla + "\n"
        return self.md(cuerpo)

    # -- Piezas del motor ----------------------------------------------------
    # Va delante de la celda del motor, que es lo primero de todo cuadernillo,
    # así que sale en los seis sin tener que acordarse en cada generador.
    #
    # Las dos cosas que dice salieron de la primera clase real: seis estudiantes
    # trabajaron el cuadernillo entero y no llegó ni una entrega --terminaban,
    # daban por hecho que con eso bastaba, y cerraban--, y varios ejecutaban
    # celdas sueltas sin correr las de arriba, lo que rompe todo porque cada
    # celda usa lo que dejaron las anteriores.
    INSTRUCCIONES = """> ### Antes de empezar, dos cosas
>
> **1. Ejecuta las celdas en orden, de arriba abajo.** Una por una, con
> `Shift+Enter`. Cada celda usa lo que dejaron las de arriba, así que saltarte
> una hace que las siguientes fallen aunque estén bien escritas.
>
> **2. Al terminar, entrega.** Tu trabajo **no le llega a tu profesor** hasta que
> pulses **Guardar y entregar** — el botón está arriba y también al final del
> cuadernillo. Puedes entregar las veces que quieras: siempre cuenta la última.
"""

    # Va justo antes del PRIMER ejercicio de cada cuadernillo, una sola vez.
    #
    # Lo pidió el profesor (22-sep): notas puntuales «para que los estudiantes
    # no se confundan», con el ejemplo del raise NotImplementedError. Hasta
    # ahora solo la semana 03 lo explicaba, y lo hacía en su propio generador;
    # aquí sale en todos sin que cada semana tenga que acordarse.
    #
    # Lo que ve el alumno debajo de su plantilla lo pone «Generate» según
    # notebook/nbgrader_config.py (ClearSolutions.code_stub): un comentario
    # «ESCRIBE TU CODIGO AQUI y borra la linea de abajo» y la línea
    # raise NotImplementedError("Todavia no has escrito tu respuesta").
    # Esta nota explica esa línea; no se repite como comentario en la celda,
    # porque el stub ya trae el suyo justo encima del raise.
    NOTA_RESPUESTA = """> ### Cómo se responde un ejercicio
>
> Cada ejercicio son dos celdas. La primera es **la tuya**: trae la línea
> `raise NotImplementedError(...)`, que solo significa «aquí falta tu
> respuesta». **Bórrala** y escribe tu código en su lugar; si la dejas, tu
> solución no llega a evaluarse. Ejecuta tu celda y después la **celda de
> prueba** de abajo: ella te dice si vas bien, y puedes repetirla las veces
> que quieras. Si te atascas, `pista("{clave}")`. No cambies el nombre de la
> función ni muevas celdas.
"""

    def arranque(self):
        """Primera celda de código: carga el motor y crea el objeto `ava`.

        Se deja marcada la posición: el contenido definitivo se arma en
        `a_dict()`, cuando ya se conocen las pistas de todos los ejercicios.
        """
        self.md(self.INSTRUCCIONES)
        self._i_competencias = len(self.celdas)
        self.md("")                      # se rellena en a_dict()
        self._i_arranque = len(self.celdas)
        return self.code("", editable=False, etiquetas=("ava-motor",))

    def _texto_competencias(self):
        """Qué microcompetencia mide este cuadernillo, dicho al principio.

        Lo pidió el profesor: «sería bueno incluir a qué tipo de
        microcompetencia le estamos apuntando en este cuadernillo; así queda
        explícito para nosotros y, cuando se haga la recopilación de
        información, saber si lo medí o no lo medí».

        Se arma de las etiquetas REALES de los ejercicios, no de una lista
        escrita aparte: así no puede decir una cosa y medir otra.
        """
        usadas = sorted({c for cs in self.competencias.values() for c in cs})
        if not usadas:
            return ""

        catalogo = catalogo_competencias()
        cuantos = {}
        for cs in self.competencias.values():
            for c in cs:
                cuantos[c] = cuantos.get(c, 0) + 1

        filas = []
        for cod in usadas:
            oficial, desc = catalogo.get(cod, (cod, ""))
            n = cuantos[cod]
            filas.append(f"| **{oficial}** | {desc} | {n} |")

        return (
            "### Qué mide este cuadernillo\n\n"
            "Cada ejercicio calificable está asociado a una microcompetencia del "
            "programa. Estas son las de esta sesión:\n\n"
            "| Microcompetencia | Qué significa | Ejercicios |\n"
            "|---|---|---:|\n"
            + "\n".join(filas)
            + "\n\nNo hace falta que hagas nada con esto: está aquí para que sepas "
              "qué se está midiendo y por qué estos ejercicios y no otros.\n"
        )

    def _fuente_arranque(self):
        fuente = _incrustar([RUTA_MOTOR] + self.modulos, self.motor_comprimido)
        fuente += (
            f'\nava = Motor(titulo={self.titulo!r}, meta_xp={self.meta_xp}, '
            f'insignia={self.insignia!r})\n'
            "quiz, ordenar, comprobar, pista = ava.quiz, ava.ordenar, ava.comprobar, ava.pista\n"
            # revisar() y huella() NO se importan: el motor se incrusta con
            # exec(), asi que sus funciones de nivel superior ya estan en el
            # espacio global del cuadernillo. Un import fallaria, porque no
            # existe ningun modulo 'ava_motor' que importar.
        )
        if self._pistas:
            # Las pistas viajan comprimidas y se registran aquí, no junto a cada
            # ejercicio: en una celda visible el estudiante las lee antes de
            # intentarlo y dejan de ser pistas.
            payload = base64.b64encode(
                zlib.compress(json.dumps(self._pistas, ensure_ascii=False).encode("utf-8"), 9)
            ).decode("ascii")
            fuente += (
                "\n# Pistas de los ejercicios. Van comprimidas para no destriparlas:\n"
                "# se piden una a una con pista(\"E1\"), o con el boton Pista.\n"
                "import json as _json\n"
                f'for _c, _p in _json.loads(zlib.decompress(base64.b64decode("{payload}"))'
                '.decode("utf-8")).items():\n'
                "    ava.registrar_pistas(_c, _p)\n"
            )
        # esconder_entrada() deja esta celda reducida a un enlace: son cientos de
        # líneas de fontanería que no aportan a quien aprende a programar.
        fuente += "\nava.barra()\nesconder_entrada()\n"
        return fuente

    def figura(self, nombre, pie=""):
        """Diagrama pre-renderizado, incrustado y mostrado desde una celda de código.

        Va en una celda de código y no en markdown a propósito: nbclassic sanea
        el HTML de las celdas de texto de un notebook que aún no es de confianza,
        y ahí el SVG se perdería. La salida que produce el propio kernel del
        alumno siempre se pinta.
        """
        svg = cargar_svg(nombre)
        return self.code(
            f"# Diagrama: {nombre}\nava.figura({svg!r}, {pie!r})\n",
            editable=False, etiquetas=("ava-figura",),
        )

    # -- Ejercicios calificables --------------------------------------------
    def ejercicio(self, numero, titulo, enunciado, partida, solucion, pruebas,
                  puntos=5, pistas=(), estrellas=1, pruebas_ocultas="",
                  competencias=()):
        """Un ejercicio autocalificado: enunciado + celda de solución + celda de prueba.

        `partida` es el código que verá el estudiante (lo que queda tras
        «Generate»); `solucion` es lo que el instructor escribe entre los
        delimitadores. `pruebas` son los asserts visibles — el estudiante los lee
        y sabe qué se le exige. `pruebas_ocultas` son los asserts que solo corren
        al calificar, para que no se pueda programar «contra la prueba».
        """
        clave = f"E{numero}"
        if not self._nota_respuesta_puesta:
            self.md(self.NOTA_RESPUESTA.format(clave=clave))
            self._nota_respuesta_puesta = True
        nivel = "★" * estrellas + "☆" * (4 - estrellas)
        ayuda = (f'\n\n> ¿Atascado? Ejecuta `pista("{clave}")` en una celda nueva. '
                 f"Hay {len(pistas)}, de la que hace pensar a la que casi resuelve. "
                 "Pedirlas no resta puntos.") if pistas else ""
        self.md(
            f"### Ejercicio {numero} — {titulo}\n\n"
            f"*Dificultad {nivel} · {puntos} puntos*\n\n{enunciado}{ayuda}"
        )
        if pistas:
            self._pistas[clave] = list(pistas)

        cuerpo_sol = (
            f"{partida}\n{INICIO_SOL}\n{solucion}\n{FIN_SOL}\n"
            if partida else f"{INICIO_SOL}\n{solucion}\n{FIN_SOL}\n"
        )
        self.celdas.append({
            "cell_type": "code",
            "metadata": {"nbgrader": {
                "grade": False, "grade_id": f"ejercicio_{numero}", "locked": False,
                "schema_version": 3, "solution": True, "task": False,
            }},
            "execution_count": None, "outputs": [], "source": _lineas(cuerpo_sol),
        })

        # Las guardas van lo primero de la celda (2026-10-05): si falta ejecutar
        # algo de arriba, que lo diga antes de que la primera línea de la prueba
        # reviente con un NameError. No cambian qué se comprueba.
        nombre_respuesta = nombre_de_la_respuesta(partida, pruebas)
        if self._nombres_arranque is None:
            # Lo que definen los módulos incrustados, más lo que añade
            # `_fuente_arranque` por su cuenta.
            self._nombres_arranque = nombres_que_deja_el_arranque(
                [RUTA_MOTOR] + self.modulos
            ) | {NOMBRE_DEL_ARRANQUE, "quiz", "ordenar", "comprobar", "pista",
                 "base64", "zlib"}
        if not nombre_respuesta:
            self._sin_guarda_respuesta.append(clave)
        elif nombre_respuesta in self._nombres_arranque:
            # El nombre existe desde la primera celda: la guarda sería una línea
            # muerta. Y que exista ya es, por sí solo, un problema del que avisar.
            self._respuestas_que_pisan.append((clave, nombre_respuesta))
            nombre_respuesta = None
        cuerpo_test = guardas_de_prueba(nombre_respuesta) + pruebas.rstrip() + "\n"
        if pruebas_ocultas:
            cuerpo_test += (f"{INICIO_TEST_OCULTO}\n{pruebas_ocultas.rstrip()}\n"
                            f"{FIN_TEST_OCULTO}\n")
        # Si la prueba ya se despide con su propio mensaje, no se le añade otro:
        # dos líneas de felicitación seguidas se leen como un fallo del material.
        if "print(" not in cuerpo_test:
            cuerpo_test += f'print("Ejercicio {numero} verificado.")\n'
        self.celdas.append({
            "cell_type": "code",
            "metadata": {"nbgrader": {
                "grade": True, "grade_id": f"test_ejercicio_{numero}", "locked": True,
                "points": puntos, "schema_version": 3, "solution": False, "task": False,
            }},
            "execution_count": None, "outputs": [], "source": _lineas(cuerpo_test),
        })
        self._ejercicios.append((numero, puntos))
        if competencias:
            self.competencias[f"ejercicio_{numero}"] = list(competencias)
        return self

    # -- Salida --------------------------------------------------------------
    def total_puntos(self):
        return sum(p for _, p in self._ejercicios)

    def a_dict(self):
        if self._i_arranque is None:
            raise RuntimeError(
                "El cuadernillo no llama a arranque(): sin el motor no hay barra "
                "de progreso, ni pistas, ni verificadores."
            )
        self.celdas[self._i_arranque]["source"] = _lineas(self._fuente_arranque())
        if getattr(self, "_i_competencias", None) is not None:
            texto = self._texto_competencias()
            if texto:
                self.celdas[self._i_competencias]["source"] = _lineas(texto)
            else:
                # Sin etiquetas no se deja una celda vacia en medio.
                self.celdas.pop(self._i_competencias)
        return {
            "cells": self.celdas,
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python",
                               "name": "python3"},
                "language_info": {"name": "python"},
                # Interruptor del tutor por cuadernillo (ver TUTOR_IA.md, §4).
                "tutor_ia": {"enabled": bool(self.tutor_ia)},
                "ava": {"cuadernillo": self.codigo, "semana": self.semana,
                        "puntos": self.total_puntos()},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }

    def escribir(self, ruta):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.a_dict(), f, ensure_ascii=False, indent=1)
            f.write("\n")
        kb = os.path.getsize(ruta) // 1024
        print(f"[OK] {ruta}")
        print(f"     {len(self.celdas)} celdas · {len(self._ejercicios)} ejercicios "
              f"calificables · {self.total_puntos()} puntos · {kb} KB")
        if self._sin_guarda_respuesta:
            print("     [AVISO] sin la guarda «ejecuta tu celda» (de la partida no "
                  f"sale un nombre limpio): {', '.join(self._sin_guarda_respuesta)}")
        for clave, nombre in self._respuestas_que_pisan:
            print(f"     [AVISO] {clave}: la respuesta se llama `{nombre}`, y la primera "
                  f"celda YA define `{nombre}`.")
            print( "             Va sin la guarda «ejecuta tu celda» (no podría saltar), y al "
                   "responder el alumno pisa ese nombre del motor.")
        return ruta


def _lineas(texto):
    """nbformat guarda el source como lista de líneas con su salto incluido."""
    texto = texto.rstrip("\n") + "\n"
    return texto.splitlines(keepends=True)
