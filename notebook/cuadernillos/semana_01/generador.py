#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 1: «Hola, máquina».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 1 — Fundamentos computacionales y entorno de desarrollo.

25 puntos de nbgrader en siete ejercicios, 40 XP lúdicos y la insignia
«Despegue». El motor (`motor/ava_motor.py`) y el contenido propio de la semana
(`contenido.py`) se incrustan en la celda de arranque: al alumno le llega un
solo archivo.

Recorte del 2026-09-22 (instrucción del profesor: cuadernillos más cortos y más
prácticos). Los siete ejercicios están CONGELADOS —ya los entregaron 19
alumnos—: se recortó solo lo que hay alrededor (teoría, demostraciones, quices,
textos de sección). Los 40 XP son los que de verdad se pueden ganar
(diagnóstico 10, tres celdas rotas 24, un quiz 6).

Dos decisiones que se salen del documento de diseño y por qué:

- El diseño ponía el motor en `/etc/jupyter/ava_s01.py`, dentro de la imagen.
  Aquí se incrusta en el `.ipynb`, que es lo que ya está construido y probado:
  así un cuadernillo publicado no cambia de motor cuando se reconstruye la
  imagen. Por eso las celdas de prueba no importan nada — los nombres ya están
  en el espacio del kernel — y las figuras se muestran con `ava.figura()` en vez
  de con `mostrar("d2_capas")`.
- Las pistas se piden con `pista("E3")` y no con `pista("ejercicio_3")`: la
  clave la fija `constructor.Cuadernillo.ejercicio()`.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(AQUI) not in sys.path:
    sys.path.insert(0, os.path.dirname(AQUI))

from constructor import Cuadernillo  # noqa: E402


def construir(motor_comprimido=True):
    c = Cuadernillo(
        codigo="semana_01",
        titulo="Hola, máquina",
        semana=1,
        meta_xp=40,
        insignia="Despegue",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[os.path.join(AQUI, "contenido.py")],
    )

    # =========================================================================
    # Bloque 0 — Portada y activación
    # =========================================================================
    c.md("""# Hola, máquina
### Semana 1 · Unidad 1 · Fundamentos computacionales y entorno de desarrollo

Esto es un **cuadernillo interactivo**: el texto y el código conviven, y el
código se ejecuta aquí mismo, en tu navegador. Hoy ejecutas tu primer programa
y sabes qué pasa por dentro de la máquina cuando lo haces.

**Empieza ejecutando la celda de abajo**: haz clic sobre ella y presiona
`Shift+Enter`.
""")

    c.arranque()
    c.code("iniciar()")

    c.md("""**Al terminar vas a poder:** ejecutar código y decir **quién lo ejecuta**;
guardar valores en **variables** de cuatro tipos; leer un programa **como lo lee
el intérprete**; distinguir **editor, terminal, intérprete e IDE**; crear y leer
un **archivo** desde código; reconocer los **tres tipos de error**; y escribir
tu primera **función** completa.

> Los **XP** son del juego: los ganas respondiendo y rompiendo cosas. Los
> **puntos** son tu nota: salen solo de los siete ejercicios y viajan solos a
> Moodle. Este cuadernillo tiene **25 puntos** y **40 XP**; la insignia se llama
> «Despegue».
""")

    # =========================================================================
    # Bloque 1 — Sección 1: primer éxito y punto de partida
    # =========================================================================
    c.seccion(1, "Tu primer programa", 4, """Casi todo el que aprende a programar empieza haciendo que la máquina salude.
Ejecuta la celda (clic + `Shift+Enter`). Después cambia lo que está entre
comillas por tu nombre y vuelve a ejecutarla.""")

    c.code('''mi_nombre = "escribe tu nombre aquí"   # <- cambia SOLO lo que está entre comillas

print("¡Hola, mundo!")
print("Hola,", mi_nombre + ".", "Bienvenido a Algoritmos y Programación.")''')

    c.md("""**Eso fue un programa**: una instrucción (`print`) y el computador obedeció. Y
usaste tu primera **variable** (`mi_nombre`): un nombre que guarda un dato.

Fíjate en que el computador **no adivinó nada**: hizo exactamente lo que decía
la instrucción. Cuando algo salga mal, la causa casi siempre será esa.

### 1.2 Tu punto de partida

Siete preguntas **sin nota** sobre de dónde arrancas; en la semana 16 las
volvemos a mirar. Responde lo que te parezca y presiona el botón del final:
**+10 XP**. *Se usa de forma anónima y con tu consentimiento; no participar no
afecta tu nota.*
""")

    c.code("diagnostico()")

    # =========================================================================
    # Bloque 2 — Sección 2: el gancho
    # =========================================================================
    c.seccion(2, "¿Qué pasó cuando presionaste Shift+Enter?", 1, """Escribiste una línea, presionaste dos teclas y apareció un saludo. Entre las dos
cosas hay cuatro piezas, y ninguna entiende la palabra `print`: las tres
primeras son **software** y la cuarta es **hardware**, un pedazo de silicio que
solo sabe sumar en binario. **Tú pones la idea; ella pone la velocidad.**

Ejecuta la celda para verlas.""")

    c.figura("s01_d4_shift_enter",
             "Los tres primeros pasos son software. El cuarto es hardware.")

    # =========================================================================
    # Bloque 3 — El entorno de Python
    # =========================================================================
    c.seccion(3, "¿Dónde se escribe todo esto?", 3, """Quien ejecuta tu código es el **intérprete** (el kernel de este cuadernillo).
Cuatro palabras que se confunden todo el tiempo:

| Palabra | Qué es | Analogía |
|---|---|---|
| **Editor** | Un programa para escribir el texto de tu código | El cuaderno |
| **Terminal** | Una ventana donde le das órdenes escritas al sistema operativo | La ventanilla de atención |
| **Intérprete** | El programa que lee tu código **y lo ejecuta línea por línea** | El traductor simultáneo |
| **IDE** | Un paquete que trae editor + terminal + intérprete + depurador | El taller completo |

Ejecuta el diagrama para verlo armado.""")

    c.figura("s01_d5_entorno",
             "El IDE no es una herramienta más: es la caja que contiene a las otras.")

    c.md("""Y los tres nombres que vas a oír todo el semestre:

| | Qué es exactamente | ¿Lo estás usando ahora? |
|---|---|---|
| **Python** | Un **lenguaje** y su **intérprete** (el programa `python`) | Sí: es el motor debajo de este cuadernillo |
| **VS Code** | Un **editor** que con extensiones se comporta como IDE | No: lo instalas en tu computador (sección 7) |
| **Jupyter** | Un **entorno de cuadernos**: texto + código + resultados en un solo documento | Sí: esto **es** Jupyter |

**Python no es VS Code**: puedes usar Python sin VS Code (lo estás haciendo).

### La terminal, sin salir del cuadernillo

Una línea que empieza con `!` no va al intérprete de Python: va **directo a la
terminal del sistema**. Ejecuta la celda y lee cada respuesta.
""")

    c.code("""!pwd                 # "print working directory": ¿en qué carpeta estoy parado?
!ls -l               # lista lo que hay en esta carpeta, con detalles
!python --version    # ¿qué intérprete de Python tengo instalado?
!which python        # ¿y dónde está ese programa exactamente?""")

    c.md("""- `pwd`: tu **carpeta de trabajo**. Un programa que dice `open("notas.txt")`
  sin más señas lo busca ahí.
- `ls`: tus archivos. Ahí está `cuadernillo.ipynb`: **este documento es un
  archivo**, con nombre, extensión (`.ipynb`), ruta y contenido.
- `python --version` y `which python`: el **intérprete**, y en qué carpeta vive.

Crear un archivo desde código son tres verbos: **abrir, hacer algo, cerrar**.
""")

    c.code('''# Crea un archivo, escribe en él y vuelve a leerlo. Tres verbos: abrir, escribir, cerrar.
with open("prueba.txt", "w", encoding="utf-8") as f:
    f.write("Mi primer archivo creado con código.\\n")

print(open("prueba.txt", encoding="utf-8").read())
!ls -l prueba.txt''')

    # =========================================================================
    # Bloque 4 — Los tres errores
    # =========================================================================
    c.seccion(4, "Los tres errores", 7, """Equivocarse es el 80 % de programar, también para quien lleva veinte años. Lo
que separa a quien avanza de quien se bloquea es **saber qué clase de error
tiene enfrente**. Hay exactamente tres.

Las tres celdas que siguen están rotas **a propósito**. Ejecútalas tal cual; si
algo se enreda, `Kernel → Restart` y el cuadernillo queda como nuevo.""")

    c.md("""### Error 1 de 3 — de sintaxis

**Predice antes de ejecutar:** la segunda línea está mal escrita. ¿Se imprimirá
la primera?
""")

    c.code('''print("Esta línea está perfecta. ¿Se imprimirá?")

nota = 4.2
if nota >= 3.0
    print("Aprobado")''', etiquetas=("error-sembrado",))

    c.md("""**No se imprimió nada**, ni siquiera la primera línea. Python revisa **todo** el
texto antes de ejecutar **una sola línea**; si algo no es Python, se planta y no
arranca. El mensaje te dice **dónde** (`line 4`, y el `^` señala el carácter) y
**qué** (`SyntaxError: expected ':'`).

Arregla la celda de arriba (ponle los dos puntos), ejecútala de nuevo y cobra
tus XP en la celda de abajo.
""")

    c.code('registrar("errores_sintaxis")   # +8 XP cuando la celda de arriba compile')

    c.md("""### Error 2 de 3 — de ejecución

**Predice:** cuatro `print` numerados. ¿Cuántos alcanzan a salir?
""")

    c.code('''print("Paso 1: recibo la nota del parcial")
nota_texto = "4.2"

print("Paso 2: la muestro tal cual ->", nota_texto)
print("Paso 3: le sumo un punto  ->", nota_texto + 1)
print("Paso 4: aquí nunca llego")''', etiquetas=("error-sembrado",))

    c.md("""**Salieron dos de cuatro.** Aquí el programa **sí arrancó** y se estrelló a
mitad de camino: **error de ejecución**. El traceback se lee **de abajo hacia
arriba**: la última línea es la respuesta (`TypeError`: «me pediste pegar un
texto con un número») y la flecha `---->` es el lugar. `nota_texto` es `"4.2"`
**con comillas**: para Python es texto, no número.

**Arréglalo:** quítale las comillas a `"4.2"` y ejecuta otra vez. Deben salir
los cuatro pasos.
""")

    c.code('registrar("errores_ejecucion")   # +8 XP cuando la celda de arriba corra entera')

    c.md("""### Error 3 de 3 — de lógica *(el peligroso)*

**Predice:** con 4.0, 4.0 y 4.0 en tus tres parciales, ¿cuál es tu promedio?
Ya lo sabes. Ahora ejecuta la celda.
""")

    c.code('''n1, n2, n3 = 4.0, 4.0, 4.0

promedio = n1 + n2 + n3 / 3

print("Tu promedio del semestre es:", promedio)''')

    c.md("""**9.33 de promedio con tres notas de 4.0, y ningún mensaje rojo.** La línea
está bien escrita y sumar y dividir es legal: Python hizo **exactamente** lo que
le pediste. Por precedencia, primero dividió `n3 / 3` y después sumó. Tú querías
`(n1 + n2 + n3) / 3`.

Eso es un **error de lógica**: el programa corre, entrega un resultado, y el
resultado está mal. **Nadie te avisa.** Se cazan con tu propia alarma: un **caso
de prueba** cuyo resultado conoces de antemano, como los tres cuatros. Ejecuta:
""")

    c.code('assert promedio == 4.0, "Con tres notas de 4.0 el promedio TIENE que dar 4.0"',
           etiquetas=("error-sembrado",))

    c.md("""**Acabas de fabricar el mensaje rojo que Python no te iba a dar.** Eso es
`assert`: «esto tiene que ser cierto; si no, grita». **Las celdas de prueba de
los ejercicios que vienen son exactamente esto.**

Ahora **arregla** la celda del promedio (paréntesis) y vuelve a ejecutar las dos
celdas. Cuando el `assert` no diga nada, ganaste: **el silencio es la buena
noticia**.
""")

    c.code('registrar("errores_logica")   # +8 XP cuando el assert pase')

    c.md("""### Los tres, uno al lado del otro

| | **Sintaxis** | **Ejecución** | **Lógica** |
|---|---|---|---|
| ¿Cuándo aparece? | Antes de ejecutar nada | A mitad del programa | Nunca «aparece» |
| ¿Alcanzó a correr algo? | No, ni una línea | Sí, hasta el choque | Sí, **todo** |
| ¿Quién te avisa? | Python, con `SyntaxError` | Python, con un traceback | **Nadie. Solo tú.** |
| Se caza con | Leer el mensaje | La última línea del traceback | `assert` y casos conocidos |

Ejecuta el árbol de decisión: te sirve todo el semestre.
""")

    c.figura("s01_d8_arbol_errores",
             "Cuatro preguntas y sabes con cuál de los tres estás peleando.")

    c.code('''quiz(
    "Q5", 6,
    "Tu programa calcula el 15 % de descuento sobre $80.000 y muestra $79.985. "
    "No aparece ningún mensaje de error. ¿Qué tipo de error tienes?",
    ["De sintaxis", "De ejecución", "De lógica",
     "Ninguno: si no hay mensaje, no hay error"],
    "De lógica",
    "Corrió entero y sin quejarse, y entregó un número equivocado. Esa es la "
    "firma exacta del error de lógica.",
    pistas=["Haz la cuenta a mano: el 15 % de 80.000 son 12.000, así que el "
            "precio con descuento debería ser 68.000. El programa corrió sin "
            "quejarse… y entregó otra cosa."],
)''')

    # =========================================================================
    # Bloque 5 — Los siete ejercicios (25 puntos)
    # =========================================================================
    c.seccion(5, "Siete ejercicios", 65, """Aquí es donde se juega tu nota: **25 puntos** en siete ejercicios. Cada uno son
dos celdas —la tuya y la de prueba— y la de prueba es un montón de `assert`
como el que acabas de fabricar.

- **Los intentos no restan.** Ejecuta la celda de prueba las veces que quieras.
- **Las pistas tampoco.** Se piden con `pista("E1")`, `pista("E2")`…
- Una celda de ejercicio sin tocar da `NotImplementedError`: es un error de
  ejecución **puesto a propósito** que significa «aquí falta tu parte». Bórralo
  cuando escribas tu respuesta.
""")

    # --- Ejercicio 1 ------------------------------------------------------
    c.ejercicio(
        numero=1, competencias=[], titulo="Tu ficha de estudiante", estrellas=1, puntos=3,
        enunciado="""Una **variable** es un nombre que guarda un valor. Se crea con `=`, que aquí no
significa «es igual a» sino «guarda esto»:

```python
ciudad = "Bucaramanga"
```

Python distingue cuatro tipos que vas a usar todo el semestre:

| Tipo | Qué guarda | Ejemplo |
|---|---|---|
| `str` | Texto, siempre entre comillas | `"Ana"` |
| `int` | Un número entero, sin decimales | `2026` |
| `float` | Un número con decimales | `4.2` |
| `bool` | Verdadero o falso, sin comillas | `True` |

Crea **tu** ficha con esos cuatro nombres exactos. Los valores son tuyos, pero
el tipo tiene que ser el correcto:

- `nombre` — tu nombre, como texto
- `codigo` — tu código estudiantil, como número entero
- `promedio` — el promedio que te gustaría sacar, con decimales
- `primer_semestre` — `True` o `False`

**Cuidado con el clásico:** `codigo = "2026"` **no** es un entero, es texto con
forma de número. Las comillas cambian el tipo.""",
        partida='''nombre = ...
codigo = ...
promedio = ...
primer_semestre = ...''',
        solucion='''nombre = "Ana Maria"
codigo = 2260123
promedio = 4.2
primer_semestre = True''',
        pruebas='''assert isinstance(nombre, str) and nombre.strip(), \\
    "nombre debe ser texto entre comillas y no puede quedar vacio"
assert isinstance(codigo, int) and not isinstance(codigo, bool), \\
    "codigo debe ser un entero SIN comillas (2260123, no \\"2260123\\")"
assert isinstance(promedio, float), \\
    "promedio debe llevar decimales (4.2), no ser entero (4)"
assert isinstance(primer_semestre, bool), \\
    "primer_semestre debe ser True o False, sin comillas"
print("Ejercicio 1 verificado: cuatro variables, cuatro tipos correctos.")''',
        pruebas_ocultas='''assert 0.0 <= promedio <= 5.0, "En la UIS el promedio va de 0.0 a 5.0"
assert codigo > 0, "El codigo estudiantil es un numero positivo"''',
        pistas=[
            "Las comillas deciden el tipo. Con comillas es texto; sin comillas, Python "
            "lo lee como numero. Pregúntate para cada línea: ¿esto necesita comillas?",
            "Un `float` necesita el punto decimal, aunque sea `4.0`. Si escribes `4` a "
            "secas, Python lo guarda como `int` y la prueba te lo va a decir.",
            "`True` y `False` van con mayúscula inicial y sin comillas. `\"True\"` con "
            "comillas es texto, no un booleano.",
        ],
    )

    # --- Ejercicio 2 ------------------------------------------------------
    c.ejercicio(
        numero=2, competencias=[], titulo="Cada herramienta con su oficio", estrellas=1, puntos=3,
        enunciado="""Vuelve a la sección 3 si hace falta. Completa el diccionario emparejando cada
herramienta con **lo único que la distingue de las otras tres**.

Las cuatro respuestas posibles, escritas exactamente así:

- `"escribir"` — sirve para escribir y guardar el texto del programa
- `"ordenar"` — sirve para darle órdenes escritas al sistema operativo
- `"ejecutar"` — es el único que lee tu código y lo convierte en acciones
- `"todo_junto"` — es un paquete que trae a los otros tres dentro""",
        partida='''HERRAMIENTAS = {
    "editor": ...,
    "terminal": ...,
    "interprete": ...,
    "ide": ...,
}''',
        solucion='''HERRAMIENTAS = {
    "editor": "escribir",
    "terminal": "ordenar",
    "interprete": "ejecutar",
    "ide": "todo_junto",
}''',
        pruebas='''assert isinstance(HERRAMIENTAS, dict), "HERRAMIENTAS debe seguir siendo un diccionario"
assert set(HERRAMIENTAS) == {"editor", "terminal", "interprete", "ide"}, \\
    "No cambies las cuatro llaves: editor, terminal, interprete, ide"
_validas = {"escribir", "ordenar", "ejecutar", "todo_junto"}
assert set(HERRAMIENTAS.values()) <= _validas, \\
    "Usa solo estas cuatro respuestas: escribir, ordenar, ejecutar, todo_junto"
assert len(set(HERRAMIENTAS.values())) == 4, \\
    "Cada herramienta hace algo distinto: no repitas ninguna respuesta"
print("Ejercicio 2 verificado: ya no vas a confundir las cuatro.")''',
        pruebas_ocultas='''assert HERRAMIENTAS["interprete"] == "ejecutar"
assert HERRAMIENTAS["ide"] == "todo_junto"
assert HERRAMIENTAS["editor"] == "escribir"
assert HERRAMIENTAS["terminal"] == "ordenar"''',
        pistas=[
            "Empieza por el que tienes más claro y ve descartando: como las cuatro "
            "respuestas son distintas, cada acierto te reduce el problema.",
            "Solo uno de los cuatro **hace** algo con tu código; los otros tres te "
            "ayudan a escribirlo, guardarlo o lanzarlo.",
            "El IDE no es una quinta herramienta: es la caja que contiene a las otras. "
            "Y la terminal no entiende Python, entiende órdenes del sistema.",
        ],
    )

    # --- Ejercicio 3 ------------------------------------------------------
    c.ejercicio(
        numero=3, competencias=['I3'], titulo="Traza el intérprete", estrellas=2, puntos=4,
        enunciado="""El intérprete lee **de arriba abajo, una línea a la vez**, y cada línea se
ejecuta con los valores que existen *en ese momento*. Eso hace que reasignar una
variable no cambie lo que ya se calculó con ella.

Lee este programa **sin ejecutarlo**:

```python
a = 10
b = 3
suma = a + b
a = 100
doble = suma * 2
b = suma
```

¿Con qué valores termina cada variable? Escríbelos en `TRAZA`.

**La trampa está en `suma`.** Se calculó cuando `a` valía 10. Cambiar `a`
después no vuelve atrás a recalcularla: el intérprete ya pasó por esa línea y
no regresa.""",
        partida='''TRAZA = {
    "a": ...,
    "b": ...,
    "suma": ...,
    "doble": ...,
}''',
        solucion='''TRAZA = {
    "a": 100,
    "b": 13,
    "suma": 13,
    "doble": 26,
}''',
        pruebas='''assert isinstance(TRAZA, dict) and set(TRAZA) == {"a", "b", "suma", "doble"}, \\
    "TRAZA debe tener exactamente las llaves a, b, suma y doble"
assert all(isinstance(v, int) for v in TRAZA.values()), \\
    "Los cuatro valores son numeros enteros, sin comillas"
assert TRAZA["suma"] == 13, \\
    "suma se calculo con a=10 y b=3, ANTES de que a cambiara"
assert TRAZA["a"] == 100, "La ultima linea que toca 'a' le deja 100"
print("Ejercicio 3 verificado: sabes leer un programa como lo lee la maquina.")''',
        pruebas_ocultas='''assert TRAZA["doble"] == 26, "doble es suma * 2, y suma vale 13"
assert TRAZA["b"] == 13, "la ultima linea le asigna a b el valor de suma"''',
        pistas=[
            "Coge lápiz y papel y haz una tabla con una columna por variable y una fila "
            "por línea. Ve rellenándola línea a línea, sin adelantarte.",
            "Cuando llegues a `a = 100`, pregúntate: ¿esto cambia el valor que ya quedó "
            "guardado en `suma`? La respuesta es no, y ahí está todo el ejercicio.",
            "Las dos últimas líneas usan `suma`, que vale 13 desde la línea tres. Así "
            "que `doble` es 26 y `b` termina valiendo lo mismo que `suma`.",
        ],
    )

    # --- Ejercicio 4 ------------------------------------------------------
    c.ejercicio(
        numero=4, competencias=[], titulo="Diagnostica los tres", estrellas=2, puntos=3,
        enunciado="""Tres programas, tres problemas distintos. **No los ejecutes**: diagnostícalos
leyendo, que es lo que vas a tener que hacer toda tu vida profesional.

**Programa A**
```python
nota = 4.2
if nota >= 3.0
    print("Aprobado")
```

**Programa B**
```python
notas = [4.0, 3.5, 2.8]
print("La cuarta nota del curso es:", notas[3])
```

**Programa C**
```python
precio = 80000
descuento = 15          # el almacén da 15 % de descuento
final = precio - descuento
print("Precio final:", final)
```

Escribe para cada uno **una** de estas tres palabras, entre comillas:
`"sintaxis"` · `"ejecucion"` · `"logica"` (sin tildes, para no pelear con el
teclado).""",
        partida='''DIAGNOSTICO = {
    "A": ...,
    "B": ...,
    "C": ...,
}''',
        solucion='''DIAGNOSTICO = {
    "A": "sintaxis",
    "B": "ejecucion",
    "C": "logica",
}''',
        pruebas='''assert isinstance(DIAGNOSTICO, dict) and set(DIAGNOSTICO) == {"A", "B", "C"}, \\
    "DIAGNOSTICO debe tener exactamente las llaves 'A', 'B' y 'C'"
assert all(v in {"sintaxis", "ejecucion", "logica"} for v in DIAGNOSTICO.values()), \\
    "Usa solo estas tres palabras, sin tildes: sintaxis, ejecucion, logica"

corregir("ejercicio_4", DIAGNOSTICO)
print("Ejercicio 4 superado: sabes distinguir los tres errores sin ejecutarlos.")''',
        pistas=[
            "Hazte siempre la misma pregunta en este orden: ¿arranca? Si no arranca, es "
            "de sintaxis. Si arranca y se estrella, es de ejecución. Si arranca, termina "
            "y miente, es de lógica.",
            "Solo uno de los tres programas termina sin ningún mensaje rojo. Ese es el "
            "peligroso.",
            "Programa A: le falta un signo de puntuación. Programa B: la lista tiene "
            "tres elementos y le pide el cuarto. Programa C: corre perfecto y da 79.985.",
        ],
    )

    # --- Ejercicio 5 ------------------------------------------------------
    c.ejercicio(
        numero=5, competencias=['I3', 'I1'], titulo="Caza el error que nadie te va a señalar", estrellas=3, puntos=4,
        enunciado="""Abajo hay una función que debería calcular el promedio de tres notas. Corre sin
quejarse. Y está mal.

Dos cosas que hacer:

1. **Arregla la línea del cálculo.** Recuerda el promedio de los tres cuatros.
2. **Escribe entre las comillas triples** —eso se llama *docstring*— qué hace
   la función y cuál era el error. Una o dos frases tuyas, no copiadas.

Sobre la primera línea, `def promedio_de_tres(n1, n2, n3):` — no te asustes:
significa «receta que recibe tres notas». Te la damos hecha; en la semana 8
aprenderás a escribirla tú. Hoy solo trabaja adentro.""",
        partida='''def promedio_de_tres(n1, n2, n3):
    """ESCRIBE AQUÍ, con tus palabras, qué hace esta función y cuál era el error de lógica que arreglaste."""
    resultado = n1 + n2 + n3 / 3     # <- aquí está el error de lógica
    return resultado''',
        solucion='''def promedio_de_tres(n1, n2, n3):
    """Devuelve el promedio de tres notas.

    El error de lógica era de precedencia: sin paréntesis Python dividía solo la
    tercera nota antes de sumar, así que el resultado no era un promedio.
    """
    resultado = (n1 + n2 + n3) / 3
    return resultado''',
        pruebas='''# Cuatro casos de prueba: situaciones cuyo resultado correcto conocemos de antemano.
assert abs(promedio_de_tres(4.0, 4.0, 4.0) - 4.0) < 1e-9, \\
    "Con tres notas de 4.0 el promedio TIENE que dar 4.0"
assert abs(promedio_de_tres(3.0, 4.0, 5.0) - 4.0) < 1e-9, \\
    "Con 3.0, 4.0 y 5.0 el promedio es 4.0"
assert abs(promedio_de_tres(0.0, 0.0, 3.0) - 1.0) < 1e-9, \\
    "Revisa: ¿estás dividiendo la SUMA de las tres, o solo la última?"
assert abs(promedio_de_tres(5.0, 5.0, 5.0) - 5.0) < 1e-9, \\
    "Con tres cincos el promedio es 5.0"

_doc = (promedio_de_tres.__doc__ or "").strip()
assert "ESCRIBE AQUÍ" not in _doc, "Reemplaza el texto de ejemplo por tu propia explicación"
assert len(_doc) >= 40, "Tu explicación es muy corta: escribe al menos una frase completa"

print("Ejercicio 5 superado: cazaste y documentaste un error que Python nunca iba a señalar.")''',
        pruebas_ocultas='''# Un caso más, que el estudiante no ve: con cuatro casos visibles todavía se
# podría intentar acertar de memoria; con este quinto hay que calcular de verdad.
assert abs(promedio_de_tres(1.0, 2.0, 4.5) - 2.5) < 1e-9''',
        pistas=[
            "Python divide antes de sumar, siempre. En <code>n1 + n2 + n3 / 3</code> "
            "solo se está dividiendo <code>n3</code>. ¿Cómo le dices a Python «primero "
            "suma las tres»?",
            "El signo que agrupa operaciones y obliga a hacerlas primero es el paréntesis.",
            "La línea correcta agrupa las tres notas antes de dividir: "
            "<code>resultado = ( … ) / 3</code>. Y no olvides el docstring: sin él, el "
            "test sigue en rojo aunque el cálculo esté bien.",
        ],
    )

    # --- Ejercicio 6 ------------------------------------------------------
    c.ejercicio(
        numero=6, competencias=[], titulo="Crea un archivo con código", estrellas=3, puntos=4,
        enunciado="""Hasta ahora todo lo que has hecho vive en la memoria y desaparece cuando se
apaga el kernel. Vamos a dejar algo **escrito en el disco**.

Completa la función para que:

1. **cree** el archivo `bitacora_semana1.txt` en tu carpeta de trabajo,
2. **escriba** exactamente tres líneas:
   · la primera, el nombre que recibe la función
   · la segunda, el texto `Semana 1: fundamentos computacionales`
   · la tercera, lo que quieras contar sobre esta semana (mínimo una palabra),
3. **lo vuelva a leer** y devuelva su contenido completo.

Las tres partes de trabajar con archivos: **abrir**, **hacer algo**, **cerrar**.
El `with` de abajo cierra por ti aunque algo falle — por eso se usa siempre.
Cada línea termina en `\\n`, que es como se escribe «salto de línea».""",
        partida='''def crear_bitacora(nombre_estudiante):
    """Crea bitacora_semana1.txt con tres líneas y devuelve su contenido."""
    # 1. Abre el archivo en modo "w" con un bloque  with open(...) as archivo:
    #    y escribe las tres líneas. Cada una termina en \\n
    # 2. Vuelve a abrirlo, ahora en modo "r", y léelo entero con archivo.read()
    # 3. Devuelve lo leído con  return''',
        solucion='''def crear_bitacora(nombre_estudiante):
    """Crea bitacora_semana1.txt con tres líneas y devuelve su contenido."""
    with open("bitacora_semana1.txt", "w", encoding="utf-8") as archivo:
        archivo.write(nombre_estudiante + "\\n")
        archivo.write("Semana 1: fundamentos computacionales\\n")
        archivo.write("Lo que más me costó fue distinguir los tres errores.\\n")

    with open("bitacora_semana1.txt", "r", encoding="utf-8") as archivo:
        contenido = archivo.read()

    return contenido''',
        pruebas='''import os

_contenido = crear_bitacora("Ana Gómez")

assert os.path.exists("bitacora_semana1.txt"), \\
    "No encuentro bitacora_semana1.txt en la carpeta de trabajo. ¿Lo creaste con open(..., 'w')?"
assert isinstance(_contenido, str) and _contenido.strip(), \\
    "La función debe DEVOLVER (return) lo que quedó escrito en el archivo"

_lineas = [l for l in _contenido.strip().split("\\n") if l.strip()]
assert len(_lineas) == 3, f"El archivo debe tener 3 líneas y encontré {len(_lineas)}. ¿Pusiste el \\\\n al final de cada una?"
assert "Ana Gómez" in _lineas[0], "La primera línea debe ser el nombre que RECIBE la función"
assert "Semana 1: fundamentos computacionales" in _lineas[1], "La segunda línea debe ir tal cual el enunciado"

with open("bitacora_semana1.txt", "r", encoding="utf-8") as _f:
    assert _f.read() == _contenido, \\
        "Lo que devuelves tiene que ser EXACTAMENTE lo que quedó guardado en el disco"

# Segunda llamada con otro nombre: el archivo debe reescribirse, no quedarse con el anterior.
_c2 = crear_bitacora("Luis Peña")
assert "Luis Peña" in _c2 and "Ana Gómez" not in _c2, \\
    "Tu función debe usar el nombre que recibe, no uno fijo escrito a mano"

print("Ejercicio 6 superado: creaste, escribiste y leíste un archivo. Eso es gestión de archivos.")''',
        pruebas_ocultas='''# Tercer nombre, con tilde y sin espacios, para descartar cualquier atajo.
_c3 = crear_bitacora("Zulma Ríos")
assert "Zulma Ríos" in _c3 and "Luis Peña" not in _c3''',
        pistas=[
            "Ya tienes el esqueleto. Necesitas dos bloques <code>with</code>: uno con "
            "<code>\"w\"</code> para escribir y otro con <code>\"r\"</code> para leer.",
            "<code>archivo.write(texto)</code> escribe. Para que cada cosa quede en su "
            "propia línea, el texto tiene que terminar en <code>\\n</code>. Y para leer "
            "todo de una vez: <code>archivo.read()</code>.",
            "La primera línea se escribe así: "
            "<code>archivo.write(nombre_estudiante + \"\\n\")</code> — usando el "
            "parámetro, no tu nombre escrito a mano. Y no olvides el "
            "<code>return contenido</code> al final.",
        ],
    )

    # --- Ejercicio 7 ------------------------------------------------------
    c.ejercicio(
        numero=7, competencias=['I3', 'I1'], titulo="Tu primer programa completo", estrellas=4, puntos=4,
        enunciado="""El ejercicio final junta todo lo de hoy: variables, tipos, cálculo y texto.

Escribe la función `ficha(nombre, notas)` que recibe:

- `nombre`: el nombre del estudiante, como texto
- `notas`: una lista de números, por ejemplo `[4.0, 3.5, 2.8]`

y **devuelve** (no imprime) una sola línea de texto con este formato exacto:

```
Ana: promedio 3.43 — Aprobado
```

Las reglas:

1. El promedio es la suma de las notas dividida entre cuántas hay.
2. Se muestra con **dos decimales**.
3. El estado es `Aprobado` si el promedio es **mayor o igual a 3.0**, y
   `Reprobado` si no.
4. Entre el promedio y el estado va un guion largo con un espacio a cada lado:
   ` — `. Cópialo de aquí para no pelear con el teclado.

**Dos avisos.** `return` **devuelve** un valor a quien llamó la función; `print`
lo muestra en pantalla y devuelve nada. Aquí se pide `return`. Y para los dos
decimales te sirve `round(promedio, 2)`, aunque hay una forma más directa que
puedes buscar: se llama *f-string*.""",
        partida='''def ficha(nombre, notas):
    ...''',
        solucion='''def ficha(nombre, notas):
    promedio = sum(notas) / len(notas)
    estado = "Aprobado" if promedio >= 3.0 else "Reprobado"
    return f"{nombre}: promedio {promedio:.2f} — {estado}"''',
        pruebas='''assert callable(ficha), "ficha debe ser una funcion definida con def"
_r = ficha("Ana", [4.0, 3.5, 2.8])
assert isinstance(_r, str), "ficha debe DEVOLVER texto con return, no imprimirlo con print"
assert _r == "Ana: promedio 3.43 — Aprobado", \\
    "Con ('Ana', [4.0, 3.5, 2.8]) se espera exactamente: Ana: promedio 3.43 — Aprobado"
print("Ejercicio 7 verificado:", _r)''',
        pruebas_ocultas='''assert ficha("Luis", [2.0, 2.5]) == "Luis: promedio 2.25 — Reprobado"
assert ficha("Sara", [3.0]) == "Sara: promedio 3.00 — Aprobado", \\
    "Exactamente 3.0 aprueba, y los decimales se muestran aunque sean ceros"
assert ficha("Jose", [5.0, 5.0, 5.0]) == "Jose: promedio 5.00 — Aprobado"''',
        pistas=[
            "Divide el problema en tres pasos y resuelvelos por separado: primero el "
            "promedio, luego el estado, y solo al final arma el texto.",
            "Para el promedio tienes `sum(notas)` y `len(notas)` ya hechas en Python. "
            "Para el estado necesitas decidir entre dos textos segun una condicion.",
            "El formato con dos decimales sale con `f\"{promedio:.2f}\"`. Y ojo con el "
            "estado: la nota 3.0 exacta APRUEBA, asi que la comparacion es `>=`, no `>`.",
        ],
    )

    # =========================================================================
    # Bloque 6 — El tutor de IA
    # =========================================================================
    c.seccion(6, "Tus cinco preguntas", 1, """Abajo a la derecha hay un botón con un robot. Es **Ava**, el tutor de
inteligencia artificial del curso. Tres cosas antes de tocarlo:

1. **Tienes cinco preguntas por cuadernillo**, no por ejercicio. Se gasta una
   solo cuando Ava alcanza a responder.
2. **Ava no te da la respuesta**: responde con preguntas y pistas. En la
   evaluación escrita Ava no entra contigo al salón.
3. **Haz clic en la celda del ejercicio** antes de preguntar: así Ava ve el
   enunciado, tu código y tu último error.

Antes de gastar una pregunta, lee la última línea del mensaje rojo y pide las
pistas del ejercicio (`pista("E3")`): son gratis. Y pregunta bien: «Me sale
`TypeError` en el ejercicio 5. **No me des la solución: hazme una pregunta** que
me ayude a ver qué tipo de dato tengo», no «Hazme el ejercicio 5».""")

    # =========================================================================
    # Bloque 7 — Cierre
    # =========================================================================
    c.seccion(7, "Cierre", 3, """Antes de reclamar tu insignia, respóndete en voz alta: **¿qué puedes hacer hoy
que no podías esta mañana?** y **¿cuál de los tres tipos de error te parece más
peligroso, y por qué?**""")

    c.md("""## Tu entorno de trabajo

Este cuadernillo corre en un servidor de la UIS donde ya está instalado todo, y
**de aquí sale tu nota**. Para trabajar por tu cuenta y sin internet necesitas
**tu propio Python**: se instala en la clase 2 y **no cuenta para la nota**.

**Ruta 1 — Tengo computador y puedo instalar**

1. Instala **Python** desde `python.org/downloads`. En Windows, marca la casilla
   **«Add python.exe to PATH»** en la primera pantalla.
2. Abre una **terminal** (`cmd` en Windows; Terminal en Mac/Linux) y escribe
   `python --version`. Si contesta con un número, ganaste.
3. Instala **VS Code** desde `code.visualstudio.com` y, dentro, la extensión
   **Python** de Microsoft.
4. Crea la carpeta `algoritmos-uis` y dentro un archivo `hola.py` con una línea:
   `print("Hola desde mi propio computador")`.
5. Ejecútalo de **tres formas**: `python hola.py` en la terminal, el botón de
   ejecutar de VS Code, y Jupyter (`pip install notebook` y luego
   `jupyter notebook`). Las tres veces es el mismo intérprete: editor, terminal
   y cuaderno son tres puertas al mismo cuarto.

**Ruta 2 — No tengo computador propio, o no puedo instalar:** la sala de cómputo
en la clase 2 (el profesor reserva 20 minutos para hacer la ruta 1 en equipo), o
WinPython y VS Code Portable en una USB. Avísale al profesor por Moodle; no es
un problema, es información.
""")

    c.code("""verificar_entorno()     # el entorno del AVA, automático
lista_comprobacion()    # tu entorno local, autodeclarado + texto para Moodle""")

    c.code("reclamar_insignia()")

    c.md("""**Para profundizar**, en fuentes confiables: la documentación oficial de Python
(`docs.python.org/es/3/`), *How to Think Like a Computer Scientist* (edición
Runestone, gratuita) y Real Python (`realpython.com`). La IA generativa —Ava
incluido— también es una fuente, y se equivoca con mucha seguridad: todo dato
concreto que te dé, verifícalo en la documentación oficial.

---
*Semana 1 · AVA Algoritmos y Programación 41333 · UIS 2026-2*
*Puntos de este cuadernillo: 25. XP: 40. Tu nota viaja sola a Moodle.*
""")

    return c


if __name__ == "__main__":
    construir().escribir(
        os.path.join(os.path.dirname(os.path.dirname(AQUI)),
                     "notebook_semana", "semana_01", "cuadernillo.ipynb")
    )
