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
import base64
import json
import os
import zlib

AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA_MOTOR = os.path.join(AQUI, "motor", "ava_motor.py")
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
        self._i_arranque = None       # dónde va la celda del motor

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
    def arranque(self):
        """Primera celda de código: carga el motor y crea el objeto `ava`.

        Se deja marcada la posición: el contenido definitivo se arma en
        `a_dict()`, cuando ya se conocen las pistas de todos los ejercicios.
        """
        self._i_arranque = len(self.celdas)
        return self.code("", editable=False, etiquetas=("ava-motor",))

    def _fuente_arranque(self):
        fuente = _incrustar([RUTA_MOTOR] + self.modulos, self.motor_comprimido)
        fuente += (
            f'\nava = Motor(titulo={self.titulo!r}, meta_xp={self.meta_xp}, '
            f'insignia={self.insignia!r})\n'
            "quiz, ordenar, comprobar, pista = ava.quiz, ava.ordenar, ava.comprobar, ava.pista\n"
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
                  puntos=5, pistas=(), estrellas=1, pruebas_ocultas=""):
        """Un ejercicio autocalificado: enunciado + celda de solución + celda de prueba.

        `partida` es el código que verá el estudiante (lo que queda tras
        «Generate»); `solucion` es lo que el instructor escribe entre los
        delimitadores. `pruebas` son los asserts visibles — el estudiante los lee
        y sabe qué se le exige. `pruebas_ocultas` son los asserts que solo corren
        al calificar, para que no se pueda programar «contra la prueba».
        """
        clave = f"E{numero}"
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

        cuerpo_test = pruebas.rstrip() + "\n"
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
        return ruta


def _lineas(texto):
    """nbformat guarda el source como lista de líneas con su salto incluido."""
    texto = texto.rstrip("\n") + "\n"
    return texto.splitlines(keepends=True)
