#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 3: «Decidir».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 3 — Operadores y estructuras condicionales.

65 puntos de nbgrader en seis ejercicios, 90 XP lúdicos y la insignia
«Quien decide». Todo lo que aparece aquí se apoya solo en lo de las semanas 1 y
2: variables, tipos, entrada, salida, pseudocódigo y prueba de escritorio. No
hay ciclos —son de la semana 4— ni listas ni funciones propias más allá de las
que ya se escribieron en la semana 1.

Una decisión de diseño: cada estructura aparece **dos veces seguidas**, primero
en pseudocódigo y justo después en Python. No en secciones separadas. La
confusión más cara del semestre es escribir `=` donde va `==`, y se cura viendo
las dos formas pegadas, no en dos capítulos distintos.
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
        codigo="semana_03",
        titulo="Decidir",
        semana=3,
        meta_xp=90,
        insignia="Quien decide",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[
            os.path.join(MOTOR, "pseudo_uis.py"),
            os.path.join(AQUI, "contenido.py"),
        ],
    )

    # =========================================================================
    # Bloque 0 — Portada
    # =========================================================================
    c.md("""# Decidir
### Semana 3 · Unidad 3 · Operadores y estructuras condicionales

Hasta ahora todos tus algoritmos hacían siempre lo mismo: leer, calcular,
escribir. Siempre en el mismo orden, pasara lo que pasara.

Esta semana tus programas empiezan a **decidir**. Y con eso dejan de ser una
receta y empiezan a parecerse a algo que piensa.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Escribir una **expresión booleana** y saber si vale Verdadero o Falso antes de
  ejecutarla.
- Combinar condiciones con **y**, **o** y **no**, y predecir el resultado.
- Escribir un **Si**, un **Si-Sino** y una **cadena Si-Sino Si**, en pseudocódigo
  y en Python.
- Anidar condiciones sin perderte, y saber cuándo **no** conviene anidar.
- Usar los operadores aritméticos —incluidos `div` y `mod`, que son nuevos— y
  saber en qué orden los evalúa la máquina.
- Usar `round`, `abs` y `math.sqrt` para las cuentas, y comparar decimales
  sin que te traicione la coma.

**Lo que NO se te pide todavía:** repetir algo muchas veces. Eso es la semana 4.
Si un ejercicio te pide «para cada uno de los cien estudiantes», te equivocaste
de cuadernillo.

Este cuadernillo tiene **65 puntos** y **90 XP**. La insignia se llama
«Quien decide».
""")

    # =========================================================================
    # Bloque 1 — Calentamiento
    # =========================================================================
    c.seccion(1, "Calentamiento", 4, """Tres preguntas de la semana pasada. No tienen nota: dan XP y te dicen si
puedes seguir o te conviene volver un cuadernillo atrás.""")

    c.code("quiz_eps()")
    c.code("quiz_traza()")
    c.code("quiz_asignacion()")

    # =========================================================================
    # Bloque 2 — El gancho
    # =========================================================================
    c.seccion(2, "¿Puedes matricular la materia?", 4, """En la UIS, para matricular una materia tienen que cumplirse **tres** cosas al
mismo tiempo: haber aprobado el prerrequisito, tener cupo en el grupo y estar a
paz y salvo financiero.

Tres condiciones. Y basta con que falle **una** para que la respuesta sea no.

Antes de leer nada, ejecuta la celda de abajo y mira las cuatro filas. No hace
falta que entiendas la sintaxis todavía: fíjate solo en cuándo sale Verdadero.""")

    c.code('''evaluar(
    "True and True and True",     # aprobó, hay cupo, está a paz y salvo
    "True and False and True",    # no hay cupo
    "True and True and False",    # debe plata
    "False and True and True",    # le falta el prerrequisito
)''')

    c.md("""Una sola vez salió Verdadero: cuando las tres se cumplían. Eso es la palabra
**y**, y es la mitad de lo que vas a aprender hoy. La otra mitad es **o**, que
se conforma con una.

El resto del cuadernillo es ponerle nombre a lo que acabas de ver y aprender a
escribirlo en los dos idiomas del curso.
""")

    # =========================================================================
    # Bloque 3 — Concepto en corto
    # =========================================================================
    c.seccion(3, "Concepto en corto", 15, """Lo que hay que entender antes de tocar nada. Tres ideas, y ninguna es larga.""")

    c.md("""### 3A. Una expresión booleana es una pregunta con dos respuestas posibles

`nota >= 3.0` no es un cálculo: es una **pregunta**. Y como toda pregunta de
sí o no, se contesta con uno de dos valores: **Verdadero** o **Falso**. Nada más.

Ese tipo ya lo conoces: es el `bool` de la semana 1, el de `True` y `False`.

Lo que cambia hoy es que ya no lo vas a escribir a mano, sino **calcularlo**
comparando. Ejecuta y compruébalo:
""")

    c.code('''nota = 4.2

evaluar(
    "4.2 >= 3.0",
    "4.2 == 3.0",
    "4.2 != 3.0",
    "4.2 < 3.0",
)''')

    c.md("""> **El error que va a cometer media clase.** En matemáticas `=` compara. En
> programación `=` **guarda** y `==` compara. Si escribes `if nota = 3.0` Python
> te va a parar en seco con un error de sintaxis. Es de los errores buenos: te
> avisa. El malo sería que funcionara.

### 3B. Los operadores, los tres grupos

Ejecuta la chuleta. No te la aprendas: ejecuta la celda cada vez que dudes.
""")

    c.code("chuleta_operadores()")

    c.md("""Dos de la tabla son nuevos y merecen un momento, porque resuelven problemas que
hasta ahora no sabías plantear:

- **`div`** (en Python `//`) divide y tira los decimales. `7 // 2` es `3`, no
  `3.5`. Sirve para «¿cuántos buses completos de 40 puestos necesito para 130
  personas?».
- **`mod`** (en Python `%`) da el **residuo**. `7 % 2` es `1`. Sirve para «¿este
  número es par?» — lo es cuando `numero % 2 == 0`— y para repartir en turnos.

### 3C. Y, o, no

Ejecuta la celda: el color hace el resumen mejor que cualquier párrafo.
""")

    c.code("tablas_de_verdad()")

    c.md("""Y **no** simplemente le da la vuelta: `no Verdadero` es Falso.

> **Cuidado con la trampa del español.** «Si la nota no es 3 ni 4» **no** se
> escribe `nota != 3 or nota != 4`. Esa condición es Verdadera siempre: si la
> nota es 3, no es 4, así que el `o` se conforma. Lo correcto es `y`:
> `nota != 3 and nota != 4`. Cuando el enunciado dice «ni… ni…», casi siempre va
> **y**.

Compruébalo tú, con `nota = 3`:
""")

    c.code('''evaluar(
    "3 != 3 or 3 != 4",     # la trampa: sale Verdadero y no debería
    "3 != 3 and 3 != 4",    # lo correcto: sale Falso, que es lo que queremos
)''')

    # =========================================================================
    # Bloque 4 — Laboratorio
    # =========================================================================
    c.seccion(4, "Laboratorio", 27, """De aquí en adelante todo se toca. Cada estructura aparece dos veces seguidas:
primero en pseudocódigo, y justo debajo en Python. Léelas juntas — es la forma
más rápida de que se te queden las dos.""")

    c.md("""### 4A. El Si simple: hacer algo, o no hacer nada

**Pseudocódigo**

```
Si nota >= 3.0 Entonces
    Escribir "Aprobaste"
FinSi
```

**Python**

```python
if nota >= 3.0:
    print("Aprobaste")
```

Tres diferencias que hay que ver de una vez:

| | Pseudocódigo | Python |
|---|---|---|
| La palabra | `Si … Entonces` | `if …:` — los dos puntos son obligatorios |
| El cierre | `FinSi` | No hay: cierra la **sangría** |
| Lo de dentro | Va indentado por claridad | Va indentado **por obligación** |

En Python la sangría no es decoración: **es** la sintaxis. Lo que está corrido
cuatro espacios pertenece al `if`; lo que vuelve al margen, no. Ejecuta y mira
la diferencia:
""")

    c.code('''nota = 2.5

if nota >= 3.0:
    print("Esta linea es del if: solo sale si aprobaste")
print("Esta linea NO es del if: sale siempre")''')

    c.md("""### 4B. Si-Sino: dos caminos, siempre se toma uno

**Pseudocódigo**

```
Si nota >= 3.0 Entonces
    Escribir "Aprobaste"
Sino
    Escribir "Reprobaste"
FinSi
```

**Python**

```python
if nota >= 3.0:
    print("Aprobaste")
else:
    print("Reprobaste")
```

Ejecútalo de verdad en el motor de pseudocódigo, que además te dibuja el
diagrama de flujo:
""")

    # El diagrama lo pidió el profesor mirando esta misma sección: «viendo ahí
    # la flechita es más fácil ver por qué sí se ejecuta». Y el párrafo de
    # arriba ya lo prometía desde siempre, así que la celda estaba faltando a
    # su palabra: imprimía la salida y nada más.
    c.code('''ALGORITMO = """
Algoritmo Aprobar
    Definir nota Como Real
    Leer nota
    Si nota >= 3.0 Entonces
        Escribir "Aprobaste"
    Sino
        Escribir "Reprobaste"
    FinSi
FinAlgoritmo
"""

r = ps.ejecutar_pseudo(ALGORITMO, entradas=["3.8"])
print(r.salida)

# El mismo algoritmo, dibujado: cada rombo es una decision y cada flecha, un
# camino. Sigue con el dedo el que toma una nota de 3.8.
ava.figura(ps.diagrama(ALGORITMO), "Si-Sino: dos caminos, y siempre se toma uno")''')

    c.md("""### 4C. La cadena Si-Sino Si: más de dos caminos

Cuando hay tres o más respuestas posibles, encadenas. **El orden importa**: se
prueba de arriba abajo y se queda con la **primera** que se cumple.

**Pseudocódigo**

```
Si nota >= 4.5 Entonces
    Escribir "Excelente"
Sino Si nota >= 3.0 Entonces
    Escribir "Aprobado"
Sino
    Escribir "Reprobado"
FinSi
```

**Python** — aquí `elif` es la abreviatura de `else if`:

```python
if nota >= 4.5:
    print("Excelente")
elif nota >= 3.0:
    print("Aprobado")
else:
    print("Reprobado")
```

> **Por qué el orden importa.** Si pusieras `nota >= 3.0` primero, un 4.8
> entraría por ahí y nunca llegaría a «Excelente»: 4.8 también es mayor que 3.
> En una cadena, **de lo más exigente a lo menos exigente**.

Compruébalo cambiando el 4.8 por otras notas:
""")

    c.code('''nota = 4.8

if nota >= 4.5:
    print("Excelente")
elif nota >= 3.0:
    print("Aprobado")
else:
    print("Reprobado")''')

    c.md("""### 4D. Anidar: una decisión dentro de otra

A veces una respuesta solo tiene sentido si antes se cumplió otra cosa. Eso es
anidar: un `if` **dentro** de otro `if`.

```python
if aprobo_prerrequisito:
    if hay_cupo:
        print("Puedes matricular")
    else:
        print("Aprobaste el prerrequisito, pero no hay cupo")
else:
    print("Primero tienes que aprobar el prerrequisito")
```

> **Cuándo NO anidar.** Si tus dos condiciones tienen que cumplirse a la vez y
> te da igual cuál falló, no anides: únelas con `and`. Estas dos hacen lo mismo,
> y la segunda se lee mejor:
>
> ```python
> if aprobo:
>     if hay_cupo:
>         print("Puedes matricular")
> ```
> ```python
> if aprobo and hay_cupo:
>     print("Puedes matricular")
> ```
>
> Anida solo cuando necesitas **decir algo distinto** en cada caso, como en el
> ejemplo de arriba.

### 4E. Precedencia: en qué orden se evalúa

`2 + 3 * 4` da 14, no 20: la multiplicación va primero. Lo mismo pasa con las
comparaciones y con `y` / `o`. El orden completo, de primero a último:

1. Paréntesis `( )`
2. `*`, `/`, `//`, `%`
3. `+`, `-`
4. Comparaciones: `<`, `<=`, `>`, `>=`, `==`, `!=`
5. `not`, luego `and`, luego `or`

Lo que se te va a olvidar es que **`and` va antes que `or`**. Ejecuta:
""")

    c.code('''evaluar(
    "True or False and False",      # se lee: True or (False and False)
    "(True or False) and False",    # con parentesis cambia todo
)''')

    c.md("""### 4F. Tres funciones para cuentas

Las decisiones de esta semana casi siempre comparan **números**, y tres
funciones aparecen una y otra vez cuando esos números salen de un cálculo:
""")

    c.code('''print("round(3.14159, 2) =", round(3.14159, 2))   # redondea a 2 decimales
print("abs(-7)            =", abs(-7))            # distancia al cero, sin signo

import math
print("math.sqrt(16)      =", math.sqrt(16))      # raiz cuadrada''')

    c.md("""`round` es la que más vas a usar: el dinero se compara redondeado, no con sus
catorce decimales. `abs` sirve para preguntar «¿se parecen?» sin que importe
cuál es mayor: `abs(a - b) < 0.01` es *«a y b son practicamente el mismo
numero»*, y así se comparan los decimales — **nunca** con `==`, porque
`0.1 + 0.2` no da exactamente `0.3`.

Para lo demás —raíces, senos, logaritmos— está `math`, que se pide una sola vez
al principio del programa.
""")

    # =========================================================================
    # Bloque 5 — Ejercicios
    # =========================================================================
    c.seccion(5, "Seis ejercicios", 20, """Aquí se juega tu nota: **65 puntos** en seis ejercicios, de menos a más.

Dos cosas antes de empezar. Si ejecutas una celda de ejercicio sin haberla
tocado te va a salir `NotImplementedError`: no es un fallo, es la marca de «aquí
falta tu parte». Y si te atascas, `pista("E2")` te da hasta tres ayudas
escalonadas — pedirlas no resta puntos.""")

    # --- Ejercicio 1 ------------------------------------------------------
    c.ejercicio(
        numero=1, competencias=['I3'], titulo="Verdadero o falso", estrellas=1, puntos=5,
        enunciado="""Con estos valores:

```python
nota = 3.4
faltas = 2
becado = False
```

Di si cada expresión vale `True` o `False`. **Sin ejecutarla**: piénsala,
escribe tu respuesta y deja que la prueba te corrija.

| | Expresión |
|---|---|
| `a` | `nota >= 3.0` |
| `b` | `faltas > 3` |
| `c` | `nota >= 3.0 and faltas <= 3` |
| `d` | `becado or nota >= 4.5` |
| `e` | `not becado` |""",
        partida='''RESPUESTAS = {
    "a": ...,
    "b": ...,
    "c": ...,
    "d": ...,
    "e": ...,
}''',
        solucion='''RESPUESTAS = {
    "a": True,
    "b": False,
    "c": True,
    "d": False,
    "e": True,
}''',
        pruebas='''assert isinstance(RESPUESTAS, dict), "RESPUESTAS debe seguir siendo un diccionario"
assert set(RESPUESTAS) == set("abcde"), "Deja las cinco llaves: a, b, c, d, e"
assert all(isinstance(v, bool) for v in RESPUESTAS.values()), \\
    "Cada respuesta es True o False, con mayuscula inicial y sin comillas"

# Se corrige aqui mismo, contra huellas: sabes cual fallaste al instante y la
# respuesta no esta escrita en ninguna parte del cuadernillo.
revisar("ejercicio_1", RESPUESTAS, {
    "a": ("39be473ef01fdf30",
          "en `a`: compara 3.4 con 3.0, y fijate en que el `>=` tambien acepta el empate"),
    "b": ("44d3c36b11bc9796",
          "en `b`: faltas vale 2. Preguntate si 2 supera a 3"),
    "c": ("c73dc389c8561f84",
          "en `c` hay un `and`: exige que se cumplan LAS DOS. Resuelvelas por separado"),
    "d": ("76fbe1c53a721795",
          "en `d` hay un `or`: le basta una. Mira si se cumple alguna de las dos"),
    "e": ("f089a59a18219967",
          "en `e`, `not` le da la vuelta. Mira primero cuanto vale becado"),
})''',
        pruebas_ocultas='''assert RESPUESTAS["a"] is True, "3.4 si es mayor o igual que 3.0"
assert RESPUESTAS["b"] is False, "2 no es mayor que 3"
assert RESPUESTAS["c"] is True, "las dos se cumplen, asi que el 'and' se cumple"
assert RESPUESTAS["d"] is False, "becado es False y 3.4 no llega a 4.5: ninguna de las dos"
assert RESPUESTAS["e"] is True, "'not' le da la vuelta a False"''',
        pistas=[
            "Resuelve una comparacion a la vez y anota su valor al lado. Solo cuando "
            "las tengas todas, junta las que llevan 'and' u 'or'.",
            "En `c` y `d` hay dos preguntas unidas. Recuerda: 'and' exige las dos, "
            "'or' se conforma con una.",
            "En `d`, becado vale False y la nota es 3.4, que no llega a 4.5. Si ninguna "
            "de las dos partes se cumple, un 'or' no tiene de donde agarrarse.",
        ],
    )

    # --- Ejercicio 2 ------------------------------------------------------
    c.ejercicio(
        numero=2, competencias=['I3', 'I1'], titulo="Completa el Si en pseudocódigo", estrellas=2, puntos=10,
        enunciado="""El parqueadero de la UIS cobra **$1.200 por hora**, pero si el vehículo estuvo
**más de 8 horas** hay tarifa plana de **$8.000**.

Completa el algoritmo. Guarda el pseudocódigo **completo** en la variable
`ALGORITMO_E2`, como texto entre triples comillas. La prueba lo va a **ejecutar**
de verdad, con el motor del curso.

```
Algoritmo Parqueadero
    Definir horas Como Entero
    Definir total Como Real
    Leer horas
    ...   <- aquí va tu decisión
    Escribir total
FinAlgoritmo
```

Con 5 horas debe salir 6000. Con 10 horas, 8000.""",
        partida='''ALGORITMO_E2 = """
"""''',
        solucion='''ALGORITMO_E2 = """
Algoritmo Parqueadero
    Definir horas Como Entero
    Definir total Como Real
    Leer horas
    Si horas > 8 Entonces
        total <- 8000
    Sino
        total <- horas * 1200
    FinSi
    Escribir total
FinAlgoritmo
"""''',
        pruebas='''assert isinstance(ALGORITMO_E2, str) and ALGORITMO_E2.strip(), \\
    "ALGORITMO_E2 debe ser el pseudocodigo completo, como texto"
_r5 = ps.ejecutar_pseudo(ALGORITMO_E2, entradas=["5"])
assert _r5.ok, "Tu algoritmo no se puede ejecutar. El motor dice: " + _r5.error_corto
assert "6000" in _r5.salida, "Con 5 horas deben salir 6000 (5 x 1200)"
print("Con 5 horas ->", _r5.salida.strip())''',
        pruebas_ocultas='''_r10 = ps.ejecutar_pseudo(ALGORITMO_E2, entradas=["10"])
assert _r10.ok, "Con 10 horas tu algoritmo falla: " + _r10.error_corto
assert "8000" in _r10.salida, "Con 10 horas es tarifa plana: 8000"
_r8 = ps.ejecutar_pseudo(ALGORITMO_E2, entradas=["8"])
assert "9600" in _r8.salida, \\
    "Con 8 exactas todavia se cobra por hora: 8 x 1200 = 9600. La tarifa plana es a partir de MAS de 8"''',
        pistas=[
            "Copia el esqueleto tal cual y sustituye los puntos suspensivos. Ojo: el "
            "texto empieza y termina con triples comillas.",
            "La decision tiene dos caminos y siempre se toma uno, asi que necesitas "
            "`Si ... Entonces ... Sino ... FinSi`.",
            "El enunciado dice MAS de 8 horas. Con 8 exactas todavia se cobra por hora, "
            "asi que la comparacion es `> 8`, no `>= 8`.",
        ],
    )

    # --- Ejercicio 3 ------------------------------------------------------
    c.ejercicio(
        numero=3, competencias=['I3'], titulo="La cadena de notas", estrellas=2, puntos=10,
        enunciado="""En algunos sistemas la nota numérica se traduce a letra:

| Nota | Letra |
|---|---|
| 4.5 o más | `"A"` |
| entre 4.0 y 4.49 | `"B"` |
| entre 3.0 y 3.99 | `"C"` |
| menos de 3.0 | `"F"` |

Escribe `letra(nota)` que devuelva la letra correspondiente.

**El orden de la cadena importa.** Piensa por dónde empezar: si pruebas primero
la condición menos exigente, todas las notas altas se van a colar por ahí.""",
        partida='''def letra(nota):
    ...''',
        solucion='''def letra(nota):
    if nota >= 4.5:
        return "A"
    elif nota >= 4.0:
        return "B"
    elif nota >= 3.0:
        return "C"
    else:
        return "F"''',
        pruebas='''assert callable(letra), "letra debe ser una funcion"
assert letra(4.8) == "A", "4.8 es A"
assert letra(4.2) == "B", "4.2 es B"
assert letra(3.5) == "C", "3.5 es C"
assert letra(2.0) == "F", "2.0 es F"
print("Las cuatro notas de ejemplo dan la letra correcta.")''',
        pruebas_ocultas='''assert letra(4.5) == "A", "4.5 exacto ya es A: la tabla dice '4.5 o mas'"
assert letra(4.49) == "B", "4.49 todavia no llega a A"
assert letra(4.0) == "B", "4.0 exacto es B"
assert letra(3.99) == "C"
assert letra(3.0) == "C", "3.0 exacto es C, no F"
assert letra(2.99) == "F"
assert letra(0.0) == "F"
assert letra(5.0) == "A"''',
        pistas=[
            "Cuatro respuestas posibles significan una cadena de tres preguntas mas un "
            "`else` final para todo lo demas.",
            "Empieza por la condicion MAS exigente. Si preguntas primero `nota >= 3.0`, "
            "un 4.8 entra por ahi y nunca llega a ser A.",
            "Cuidado con los bordes: la tabla dice «4.5 o mas», asi que 4.5 exacto es A. "
            "Eso es `>=`, no `>`.",
        ],
    )

    # --- Ejercicio 4 ------------------------------------------------------
    c.ejercicio(
        numero=4, competencias=['I3', 'I1'], titulo="Precedencia", estrellas=3, puntos=10,
        enunciado="""Cuatro expresiones. Predice el valor de cada una **sin ejecutarla** y guárdalo
en `PRECEDENCIA`.

| | Expresión | Tipo de respuesta |
|---|---|---|
| `p` | `10 - 2 * 3` | un número |
| `q` | `(10 - 2) * 3` | un número |
| `r` | `17 // 5 + 17 % 5` | un número |
| `s` | `False or True and False` | `True` o `False` |

Recuerda el orden: paréntesis, multiplicar y dividir, sumar y restar, comparar,
`not`, `and`, `or`.

Ninguna de las cuatro está resuelta más arriba: hay que razonarlas.""",
        partida='''PRECEDENCIA = {
    "p": ...,
    "q": ...,
    "r": ...,
    "s": ...,
}''',
        solucion='''PRECEDENCIA = {
    "p": 4,
    "q": 24,
    "r": 5,
    "s": False,
}''',
        pruebas='''assert isinstance(PRECEDENCIA, dict) and set(PRECEDENCIA) == set("pqrs"), \\
    "PRECEDENCIA debe tener exactamente las llaves p, q, r y s"
assert isinstance(PRECEDENCIA["s"], bool), "s es una expresion logica: True o False"
assert not isinstance(PRECEDENCIA["p"], bool), "p es un numero, no un booleano"

revisar("ejercicio_4", PRECEDENCIA, {
    "p": ("f1b0ae33fa823af7",
          "en `p`: resuelve primero la multiplicacion y despues la resta"),
    "q": ("cd0714f92b7143e5",
          "en `q` el parentesis va primero. Resuelvelo y multiplica lo que salga"),
    "r": ("55e3aa7476da32aa",
          "en `r`: `//` descarta los decimales y `%` da el residuo. Calculalos por separado antes de sumar"),
    "s": ("a3ad79f6172d6261",
          "en `s`, `and` va antes que `or`: ponle los parentesis que la maquina pone sola y vuelve a leerla"),
})''',
        pruebas_ocultas='''assert PRECEDENCIA["p"] == 4, "la multiplicacion va antes que la resta: 10 - 6"
assert PRECEDENCIA["q"] == 24, "el parentesis manda: 8 * 3"
assert PRECEDENCIA["r"] == 5, "17 // 5 es 3 y 17 % 5 es 2, asi que 3 + 2"
assert PRECEDENCIA["s"] is False, \\
    "'and' va antes que 'or': se lee False or (True and False) = False or False"''',
        pistas=[
            "Reescribe cada expresion poniendole los parentesis que la maquina pone "
            "sola. Cuando los veas, el resultado sale solo.",
            "En `r` hay dos operadores nuevos juntos: `//` descarta decimales y `%` da "
            "el residuo. Calculalos por separado antes de sumar.",
            "En `s`, `and` se evalua antes que `or`. Asi que la maquina lee "
            "`False or (True and False)`: primero resuelve el parentesis, y a un "
            "`or` con las dos falsas no le queda nada que salvar.",
        ],
    )

    # --- Ejercicio 5 ------------------------------------------------------
    c.ejercicio(
        numero=5, competencias=['I3'], titulo="¿Puede matricular?", estrellas=3, puntos=15,
        enunciado="""El del gancho, ahora en serio.

`matricula(aprobo, cupo, paz_y_salvo)` recibe tres booleanos y **devuelve un
texto** explicando la situación. No basta con decir sí o no: hay que decir
**qué** falló, porque un sistema que solo dice «no» es un sistema que genera una
fila en la oficina de registro.

| Situación | Devuelve |
|---|---|
| Las tres se cumplen | `"Matricula aprobada"` |
| No aprobó el prerrequisito | `"Falta el prerrequisito"` |
| Aprobó, pero no hay cupo | `"Sin cupo"` |
| Aprobó, hay cupo, pero debe plata | `"Pendiente financiero"` |

**El orden manda.** Si le falta el prerrequisito, eso es lo primero que hay que
decirle, aunque además deba plata. Y si aprobó pero no hay cupo, el estado
financiero da igual.""",
        partida='''def matricula(aprobo, cupo, paz_y_salvo):
    ...''',
        solucion='''def matricula(aprobo, cupo, paz_y_salvo):
    if not aprobo:
        return "Falta el prerrequisito"
    if not cupo:
        return "Sin cupo"
    if not paz_y_salvo:
        return "Pendiente financiero"
    return "Matricula aprobada"''',
        pruebas='''assert callable(matricula), "matricula debe ser una funcion"
assert matricula(True, True, True) == "Matricula aprobada"
assert matricula(False, True, True) == "Falta el prerrequisito"
assert matricula(True, False, True) == "Sin cupo"
assert matricula(True, True, False) == "Pendiente financiero"
print("Los cuatro casos principales dan el texto correcto.")''',
        pruebas_ocultas='''assert matricula(False, False, False) == "Falta el prerrequisito", \\
    "Si falla todo, lo primero que hay que decirle es lo del prerrequisito"
assert matricula(False, True, False) == "Falta el prerrequisito"
assert matricula(True, False, False) == "Sin cupo", \\
    "Si no hay cupo, el estado financiero da igual"
assert isinstance(matricula(True, True, True), str), "Debe devolver texto"''',
        pistas=[
            "Son cuatro respuestas posibles, asi que necesitas una cadena de decisiones. "
            "Pero fijate en que las tres primeras son 'algo fallo'.",
            "Le da la vuelta al problema: en vez de preguntar «se cumple todo?», ve "
            "descartando. Pregunta primero por lo que puede fallar, en el orden del "
            "enunciado, y deja el «aprobada» para el final.",
            "`if not aprobo: return ...` sale de la funcion en el acto. Si llegas a la "
            "linea siguiente es porque aprobo era True, asi que ya no hace falta "
            "volver a preguntarlo.",
        ],
    )

    # --- Ejercicio 6 ------------------------------------------------------
    c.ejercicio(
        numero=6, competencias=['I3', 'I1'], titulo="El mismo algoritmo, en los dos idiomas", estrellas=4, puntos=15,
        enunciado="""El de cierre, y el más largo. Una tienda aplica descuentos por compra:

| Compra | Descuento |
|---|---|
| $200.000 o más | 15 % |
| entre $100.000 y $199.999 | 10 % |
| menos de $100.000 | ninguno |

Tienes que entregarlo **en los dos idiomas**, porque en un proyecto real primero
se acuerda el algoritmo con quien no programa y después se escribe:

1. `ALGORITMO_E6` — el pseudocódigo completo. Lee la compra, calcula el total a
   pagar y lo escribe. La prueba lo ejecuta con el motor.
2. `total_a_pagar(compra)` — la función de Python. Devuelve el número.

Con 250000 se pagan 212500. Con 150000, 135000. Con 50000, 50000.""",
        partida='''ALGORITMO_E6 = """
"""


def total_a_pagar(compra):
    ...''',
        solucion='''ALGORITMO_E6 = """
Algoritmo Descuento
    Definir compra Como Real
    Definir total Como Real
    Leer compra
    Si compra >= 200000 Entonces
        total <- compra * 0.85
    Sino
        Si compra >= 100000 Entonces
            total <- compra * 0.90
        Sino
            total <- compra
        FinSi
    FinSi
    Escribir total
FinAlgoritmo
"""


def total_a_pagar(compra):
    if compra >= 200000:
        return compra * 0.85
    elif compra >= 100000:
        return compra * 0.90
    return compra''',
        pruebas='''assert isinstance(ALGORITMO_E6, str) and ALGORITMO_E6.strip(), \\
    "ALGORITMO_E6 debe traer el pseudocodigo completo"
_a = ps.ejecutar_pseudo(ALGORITMO_E6, entradas=["250000"])
assert _a.ok, "Tu pseudocodigo no ejecuta. El motor dice: " + _a.error_corto
assert "212500" in _a.salida, "Con 250000 y 15% de descuento se pagan 212500"

assert callable(total_a_pagar), "total_a_pagar debe ser una funcion"
assert abs(total_a_pagar(250000) - 212500) < 0.01, "250000 con 15% son 212500"
assert abs(total_a_pagar(150000) - 135000) < 0.01, "150000 con 10% son 135000"
assert abs(total_a_pagar(50000) - 50000) < 0.01, "Menos de 100000 no lleva descuento"
print("Los dos idiomas coinciden.")''',
        pruebas_ocultas='''_b = ps.ejecutar_pseudo(ALGORITMO_E6, entradas=["150000"])
assert "135000" in _b.salida, "Con 150000 el pseudocodigo debe dar 135000"
_c = ps.ejecutar_pseudo(ALGORITMO_E6, entradas=["50000"])
assert "50000" in _c.salida, "Con 50000 no hay descuento"
assert abs(total_a_pagar(200000) - 170000) < 0.01, \\
    "200000 exactos YA llevan el 15%: la tabla dice '200.000 o mas'"
assert abs(total_a_pagar(100000) - 90000) < 0.01, "100000 exactos llevan el 10%"
assert abs(total_a_pagar(99999) - 99999) < 0.01, "99999 no llega al primer escalon"''',
        pistas=[
            "Hazlo en dos ratos: primero el pseudocodigo, ejecutalo con "
            "`ps.ejecutar_pseudo` hasta que de bien, y solo entonces traducelo.",
            "Pagar con 15% de descuento es pagar el 85%: `compra * 0.85`. Eso te ahorra "
            "restar y es menos propenso a error.",
            "Cuidado con los bordes: 200000 exactos YA entran en el 15%, porque la tabla "
            "dice «o mas». En pseudocodigo el `Sino Si` se escribe anidando otro `Si` "
            "dentro del `Sino`.",
        ],
    )

    # =========================================================================
    # Bloque 6 — El tutor
    # =========================================================================
    c.seccion(6, "Habla con el asistente", 3, """Tienes **cinco preguntas** para todo este cuadernillo. Cinco, no cinco por
ejercicio. Gástalas donde de verdad te atasques.""")

    c.md("""### En qué gastarlas

Guárdalas para los dos últimos, que son los difíciles. Los primeros los resuelve
releer la teoría: si te atascas en una predicción, ejecuta la expresión y mírala;
si te atascas en pseudocódigo, el motor te dice la línea y qué esperaba. Ahí no
hace falta gastar una pregunta.

### Cómo se pregunta bien

Mal: «no me sale el 7».
Bien: «con `matricula(False, True, False)` mi función
devuelve "Pendiente financiero" y esperaba "Falta el prerrequisito". ¿Qué tiene
que ver el orden de mis `if`?»

La segunda le dice al tutor qué probaste, qué salió y qué esperabas. Con eso te
puede responder de verdad; con la primera solo puede adivinar.
""")

    # =========================================================================
    # Bloque 7 — Cierre
    # =========================================================================
    c.seccion(7, "Cierre", 3, """Tres preguntas que solo te interesan a ti. Nadie las corrige.""")

    c.md("""- ¿Sabrías explicarle a alguien de tu casa **por qué** `=` y `==` no son lo
  mismo, sin usar la palabra «programación»?
- De los seis ejercicios, ¿cuál te costó más? ¿Fue por la lógica o por la
  sintaxis? No es lo mismo, y saber cuál de los dos te frena cambia cómo
  estudias la semana que viene.
- ¿Pusiste paréntesis donde dudabas, o los dejaste al azar y confiaste?

### Lo que viene

La semana 4 te da lo único que te falta para escribir cualquier programa:
**repetir**. Con decisiones y repeticiones ya se puede escribir, literalmente,
cualquier algoritmo. Lo demás del semestre es hacerlo bien.

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **Expresión booleana** | Una pregunta que se contesta con Verdadero o Falso |
| **Operador relacional** | El que compara dos valores: `==`, `!=`, `<`, `>`, `<=`, `>=` |
| **Operador lógico** | El que combina respuestas: `and`, `or`, `not` |
| **Precedencia** | El orden en que la máquina evalúa una expresión larga |
| **Anidar** | Meter una decisión dentro de otra |
| **`div` / `//`** | División que descarta los decimales |
| **`mod` / `%`** | El residuo de una división |
""")

    return c


if __name__ == "__main__":
    print(construir().a_dict()["cells"].__len__(), "celdas")
