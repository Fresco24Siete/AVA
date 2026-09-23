#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 4: «Repetir».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 4 — Estructuras repetitivas e integración del control de flujo.

25 puntos de nbgrader en tres ejercicios, 5 XP y la insignia «Quien automatiza».

Sobre el XP: el motor solo lo da en quices (`ava.quiz`, `ordenar`, `comprobar`),
nunca por aprobar un ejercicio. Con un único quiz de 5 XP la meta es 5; con la
meta antigua de 90 la insignia era inalcanzable.

Recortado el 2026-09-22 por instrucción del profesor: de 78 a ~35 minutos,
menos lectura y más hacer. Se fueron tres ejercicios (el `while` en Python, la
escalera de ciclos anidados y el «todo junto» en dos idiomas), dos quices, la
demostración del ciclo infinito, la de Gauss, el `break` y los ciclos anidados.
Se quedaron el contador de vueltas, las tres variables, el diagrama del
`Mientras` y los tres ejercicios que más enseñan sin repetirse: predecir
vueltas, el Fibonacci generalizado en pseudocódigo y la bandera en Python.

Dos límites que se respetan a propósito y que hay que tener presentes al
editarlo:

- **El motor de pseudocódigo entiende `Mientras`, no `Para`.** El ciclo se
  explica con `Mientras`, que es el que enseña el mecanismo (arranque,
  condición, paso), y el `Para` aparece solo en Python, presentado como lo que
  es — un atajo para cuando ya sabes cuántas vueltas vas a dar.
- **El `for` va siempre con `range()`.** Recorrer listas y cadenas es de la
  semana 6.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(AQUI) not in sys.path:
    sys.path.insert(0, os.path.dirname(AQUI))

from constructor import Cuadernillo, huella  # noqa: E402

MOTOR = os.path.join(os.path.dirname(AQUI), "motor")


def construir(motor_comprimido=True):
    c = Cuadernillo(
        codigo="semana_04",
        titulo="Repetir",
        semana=4,
        meta_xp=5,
        insignia="Quien automatiza",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[
            os.path.join(MOTOR, "pseudo_uis.py"),
            os.path.join(AQUI, "contenido.py"),
        ],
    )

    c.md("""# Repetir
### Semana 4 · Unidad 4 · Estructuras repetitivas e integración del control de flujo

Sabes calcular y decidir. Te falta una sola cosa: **repetir**.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Escribir un `Mientras` en pseudocódigo, y leer un `while` en Python sabiendo
  **cuándo se detiene**.
- Usar `for` con `range()` y predecir cuántas vueltas da.
- Distinguir un **contador**, un **acumulador** y una **bandera**.

**25 puntos**, **5 XP**, insignia «Quien automatiza».
""")

    # =========================================================================
    c.seccion(1, "Calentamiento", 1, """Una de la semana pasada. Sin nota: da XP.""")
    c.code("quiz_igualdad()")

    # =========================================================================
    c.seccion(2, "Concepto en corto", 2, """Sumar 100 notas sin ciclo son cien líneas; con ciclo, cuatro. Un ciclo tiene
**tres piezas** y ninguna es opcional. Ejecuta y míralas:""")

    c.code('''total = 0
i = 1                    # 1. ARRANQUE   - de donde parte
while i <= 100:          # 2. CONDICION  - mientras sea Verdadero, sigue
    total = total + i    #    (aqui sumariamos la nota i)
    i = i + 1            # 3. PASO       - que cambia en cada vuelta

print("Sumo del 1 al 100 y dio:", total)''')

    c.md("""La condición se comprueba **antes** de cada vuelta: si ya es falsa la primera
vez, el cuerpo no se ejecuta ni una vez.

> **El error más caro: el ciclo infinito.** Sin paso, la condición nunca deja
> de cumplirse; el `[*]` de la celda no se apaga. Se corta con ⏹.

Vuelta a vuelta, cuándo decide salir:
""")

    c.code('vueltas(inicio=1, condicion="i <= 5", paso="i + 1")')

    c.md("""### Contador, acumulador y bandera

Tres variables que se confunden:
""")

    c.code("las_tres_variables()")

    c.md("""> Si querías *contar* aprobados y *sumaste* notas, el programa no falla: da un
> número razonable que no significa nada. Error de lógica de manual.
""")

    # =========================================================================
    c.seccion(3, "Laboratorio", 2, """El ciclo en los dos idiomas, y el atajo de Python.""")

    c.md("""### Mientras / while

| Pseudocódigo | Python |
|---|---|
| `Mientras i <= 5 Hacer` | `while i <= 5:` |
| `    Escribir i` | `    print(i)` |
| `    i <- i + 1` | `    i = i + 1` |
| `FinMientras` | |

Ejecútalo y mira el diagrama:
""")

    # El segundo diagrama de flujo del curso, y el que más falta hacía: en un
    # ciclo lo difícil no es la condición, es ver que hay una flecha que VUELVE
    # HACIA ATRÁS. Dibujada se ve; leyendo `FinMientras`, no.
    c.code('''CONTAR = """
Algoritmo Contar
    Definir i Como Entero
    i <- 1
    Mientras i <= 5 Hacer
        Escribir i
        i <- i + 1
    FinMientras
FinAlgoritmo
"""

r = ps.ejecutar_pseudo(CONTAR)
print(r.salida)

# Mira la flecha que sale del rombo por el "Si", baja, y VUELVE a subir hasta
# el rombo. Esa flecha de vuelta es el ciclo: es lo unico que distingue este
# dibujo del de la semana pasada.
ava.figura(ps.diagrama(CONTAR), "Mientras: la flecha que regresa es el ciclo")''')

    c.md("""### El `for`, que solo existe en Python

Cuando sabes de antemano **cuántas vueltas** vas a dar, `for` junta las tres
piezas en una línea: `for i in range(5):`.

`range(5)` da 0, 1, 2, 3, 4: **cinco** números, desde cero y sin el 5. De ahí
sale el error por uno más frecuente del semestre.

| Escribes | Te da |
|---|---|
| `range(5)` | 0, 1, 2, 3, 4 |
| `range(1, 6)` | 1, 2, 3, 4, 5 |
| `range(0, 10, 2)` | 0, 2, 4, 6, 8 |
""")

    # Única celda ejecutable con `for` de todo el cuadernillo: sin ella el alumno
    # lee sobre el for y nunca corre uno. Es el mismo conteo que el Mientras de
    # arriba, para que compare las dos formas con el mismo resultado delante.
    c.code('''# Las mismas cinco vueltas que el Mientras de arriba, en una sola linea.
for i in range(1, 6):
    print(i)''')

    # =========================================================================
    c.seccion(4, "Tres ejercicios", 28, """**25 puntos**, de menos a más. Si una celda se queda con `[*]`, es un ciclo
infinito: ⏹ y revisa el paso.""")

    c.ejercicio(
        numero=1, competencias=['I3', 'I1'], titulo="¿Cuántas vueltas da?", estrellas=1, puntos=5,
        enunciado="""Sin ejecutar nada, di cuántas veces se ejecuta el cuerpo de cada ciclo.

| | Ciclo |
|---|---|
| `a` | `for i in range(5):` |
| `b` | `for i in range(1, 6):` |
| `c` | `for i in range(0, 10, 2):` |
| `d` | `i = 3` … `while i < 3:` |
| `e` | `i = 0` … `while i < 4:` con `i = i + 1` dentro |

Escribe un número entero en cada una.""",
        partida='''VUELTAS = {
    "a": ...,
    "b": ...,
    "c": ...,
    "d": ...,
    "e": ...,
}''',
        solucion='''VUELTAS = {
    "a": 5,
    "b": 5,
    "c": 5,
    "d": 0,
    "e": 4,
}''',
        pruebas='''assert isinstance(VUELTAS, dict) and set(VUELTAS) == set("abcde"), \\
    "VUELTAS debe tener las cinco llaves: a, b, c, d, e"
assert all(isinstance(v, int) and not isinstance(v, bool) for v in VUELTAS.values()), \\
    "Cada respuesta es un numero entero"
assert all(v >= 0 for v in VUELTAS.values()), "Un ciclo no puede dar vueltas negativas"
# Se corrige aqui mismo, contra huellas: el alumno sabe al instante cual
# fallo y la respuesta no esta escrita en ninguna parte del cuadernillo.
revisar("ejercicio_1", VUELTAS, {
    "a": ("1ec0db0710419a7b",
          "en `a`: escribe los numeros que da `range(5)` y cuentalos"),
    "b": ("aba2bfad9e908ad4",
          "en `b`: `range(1,6)` arranca en 1 y el tope NO entra"),
    "c": ("22348bd4dda64484",
          "en `c` el paso es 2: ve saltando de dos en dos hasta pasarte del tope"),
    "d": ("06e2ff5caaec2757",
          "en `d` la condicion se comprueba ANTES de entrar. Mira cuanto vale i al empezar"),
    "e": ("91c6d8aa669cf6e6",
          "en `e` cuenta las veces que el cuerpo llega a ejecutarse, no las comprobaciones"),
})''',
        pruebas_ocultas='''assert VUELTAS["a"] == 5, "range(5) da 0,1,2,3,4"
assert VUELTAS["b"] == 5, "range(1,6) da 1,2,3,4,5"
assert VUELTAS["c"] == 5, "range(0,10,2) da 0,2,4,6,8"
assert VUELTAS["d"] == 0, "i vale 3 y la condicion pide i < 3: no entra ni una vez"
assert VUELTAS["e"] == 4, "i va 0,1,2,3 y en la cuarta comprobacion i vale 4 y sale"''',
        pistas=[
            "Para los `range`, escribe la lista de numeros que produce y cuentalos. Es "
            "mas seguro que calcularlo de cabeza.",
            "En `d` fijate en el valor de arranque y en la condicion ANTES de contar "
            "vueltas. La condicion se comprueba antes de la primera vuelta.",
            "Un ciclo cuya condicion es falsa desde el principio ejecuta su cuerpo cero "
            "veces. No es un error: es lo normal.",
        ],
    )

    c.ejercicio(
        numero=2, competencias=['I3', 'I1'], titulo="Fibonacci, pero empezando donde tú digas", estrellas=3, puntos=10,
        enunciado="""En Fibonacci cada término es la suma de los dos anteriores: `1, 1, 2, 3, 5,
8, 13...`. Aquí **los dos primeros los lee el usuario.** La regla no cambia;
lo que cambia es por dónde arranca.

Escribe el pseudocódigo en `ALGORITMO_E2`. El algoritmo:

1. Lee tres enteros, **en este orden**: `a`, `b` y `n`.
2. Construye la sucesión donde el término 1 es `a`, el término 2 es `b`, y de
   ahí en adelante cada uno es la suma de los dos anteriores.
3. Escribe el término `n`.

| lee | sucesión | término `n` |
|---|---|---|
| `a=1, b=1, n=7` | 1, 1, 2, 3, 5, 8, **13** | 13 |
| `a=2, b=1, n=6` | 2, 1, 3, 4, 7, **11** | 11 |
| `a=5, b=5, n=4` | 5, 5, 10, **15** | 15 |

Si copias un Fibonacci hecho, la segunda fila te delata.

> Bordes: con `n = 1` la respuesta es `a`, y con `n = 2` es `b`. Ahí el ciclo
> **no da ni una vuelta**.""",
        partida='''ALGORITMO_E2 = """
"""''',
        solucion='''ALGORITMO_E2 = """
Algoritmo FibonacciGeneral
    Definir a, b, n Como Entero
    Definir anterior, actual, siguiente, i Como Entero
    Leer a
    Leer b
    Leer n
    anterior <- a
    actual <- b
    Si n = 1 Entonces
        Escribir anterior
    Sino
        i <- 2
        Mientras i < n Hacer
            siguiente <- anterior + actual
            anterior <- actual
            actual <- siguiente
            i <- i + 1
        FinMientras
        Escribir actual
    FinSi
FinAlgoritmo
"""''',
        pruebas='''assert isinstance(ALGORITMO_E2, str) and ALGORITMO_E2.strip(), \\
    "ALGORITMO_E2 debe traer el pseudocodigo completo, como texto"

def _termino(a, b, n):
    r = ps.ejecutar_pseudo(ALGORITMO_E2, entradas=[str(a), str(b), str(n)])
    assert r.ok, f"Con a={a}, b={b}, n={n} tu algoritmo no ejecuta: " + r.error_corto
    return r.salida.strip()

def _comprobar(a, b, n, esperado):
    # Se compara el numero COMPLETO, no si aparece dentro. Buscando "11" dentro
    # de la salida, un algoritmo que escriba 110 pasaria la prueba.
    obtenido = _termino(a, b, n)
    assert obtenido == esperado, (
        f"Con a={a}, b={b}, n={n} el termino es {esperado}, "
        f"y tu algoritmo escribe {obtenido!r}")

_comprobar(1, 1, 7, "13")
_comprobar(2, 1, 6, "11")   # si copiaste un Fibonacci hecho, esta es la que te delata
_comprobar(5, 5, 4, "15")
print("Las tres sucesiones de la tabla dan el termino correcto.")''',
        pruebas_ocultas='''_comprobar(7, 3, 1, "7")    # n = 1: la respuesta es a, sin dar una sola vuelta
_comprobar(7, 3, 2, "3")    # n = 2: la respuesta es b, sin dar una sola vuelta
_comprobar(7, 3, 3, "10")
_comprobar(0, 0, 9, "0")    # dos semillas en 0: toda la sucesion es 0
_comprobar(1, 1, 12, "144")''',
        pistas=[
            "No guardes la sucesion entera: solo necesitas DOS numeros a la vez, el "
            "anterior y el actual. En cada vuelta los dos corren un puesto.",
            "Para correr un puesto hace falta una tercera variable: si haces "
            "`anterior <- actual` primero, pierdes el valor de anterior y la suma "
            "siguiente sale mal. Calcula `siguiente` ANTES de mover nada.",
            "Arranca el contador en 2, no en 1: los terminos 1 y 2 ya los tienes leidos, "
            "no hay que calcularlos. Con `i <- 2` y `Mientras i < n`, si n es 1 o 2 el "
            "ciclo no entra, que es justo lo que quieres.",
        ],
    )

    c.ejercicio(
        numero=3, competencias=['I3'], titulo="La bandera", estrellas=3, puntos=10,
        enunciado="""`hubo_perdida(primera, ultima)` recorre los enteros desde `primera` hasta
`ultima` (los dos incluidos), tratándolos como notas, y devuelve `True` si
**alguno** es menor que 3, o `False` si ninguno lo es.

Es el uso clásico de una **bandera**: empieza en `False` y solo puede pasar a
`True`. «Hubo al menos una» no se deshace porque después venga una buena.

`hubo_perdida(1, 5)` es `True` (el 1 y el 2 pierden).
`hubo_perdida(3, 5)` es `False`.""",
        partida='''def hubo_perdida(primera, ultima):
    ...''',
        solucion='''def hubo_perdida(primera, ultima):
    encontrada = False
    for nota in range(primera, ultima + 1):
        if nota < 3:
            encontrada = True
    return encontrada''',
        pruebas='''assert callable(hubo_perdida), "hubo_perdida debe ser una funcion"
assert hubo_perdida(1, 5) is True, "Entre 1 y 5 hay notas por debajo de 3"
assert hubo_perdida(3, 5) is False, "Entre 3 y 5 no pierde ninguna"
print("hubo_perdida(1, 5) =", hubo_perdida(1, 5), "· hubo_perdida(3, 5) =", hubo_perdida(3, 5))''',
        pruebas_ocultas='''assert hubo_perdida(2, 2) is True, "El 2 solo ya es perdida"
assert hubo_perdida(3, 3) is False, "3 exacto NO es perdida: la condicion es menor que 3"
assert hubo_perdida(0, 10) is True
assert hubo_perdida(5, 5) is False
assert isinstance(hubo_perdida(1, 5), bool), "Debe devolver True o False, no 1 ni 0"''',
        pistas=[
            "`range(primera, ultima + 1)` incluye los dos extremos. Sin el +1 te dejas "
            "fuera el ultimo.",
            "La bandera se crea ANTES del ciclo, en False. Si la creas dentro, se "
            "reinicia en cada vuelta y siempre te va a devolver lo de la ultima nota.",
            "Solo hay que ponerla en True; no hay que ponerla en False nunca dentro del "
            "ciclo. Si lo haces, una nota buena despues de una mala borra el hallazgo.",
        ],
    )

    # =========================================================================
    c.seccion(5, "Habla con el asistente", 1, """**Cinco preguntas** para todo el cuadernillo.""")

    c.md("""El primero no las necesita: ejecuta `vueltas(...)` otra vez. Guárdalas para el
Fibonacci y la bandera.

Mal: «mi ciclo no para».
Bien: «mi `Mientras i < n` se queda dando vueltas. Dentro tengo la suma y el
cambio de `anterior` y `actual`. ¿Qué me falta?»

La segunda dice qué probaste y qué crees que falla; con la primera solo se
puede adivinar.
""")

    # =========================================================================
    c.seccion(6, "Cierre", 1, """Dos preguntas que nadie corrige.""")

    c.md("""- ¿Sabrías explicar, sin mirar, **por qué** un ciclo se queda dando vueltas
  para siempre? ¿Qué pieza falta?
- ¿Cuándo `while` y cuándo `for`? Lo decide una sola pregunta: ¿sabes cuántas
  vueltas antes de empezar?

**Lo que viene:** la semana 5 es la primera evaluación y un repaso. Secuencia,
decisión y repetición: ya tienes las tres piezas de cualquier programa.
""")

    return c
