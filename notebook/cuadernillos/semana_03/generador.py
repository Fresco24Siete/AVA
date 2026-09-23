#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 3: «Decidir».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 3 — Operadores y estructuras condicionales.

35 puntos de nbgrader en tres ejercicios, 5 XP lúdicos y la insignia
«Quien decide». Todo lo que aparece aquí se apoya solo en lo de las semanas 1 y
2: variables, tipos, entrada, salida, pseudocódigo y prueba de escritorio. No
hay ciclos —son de la semana 4— ni listas ni funciones propias más allá de las
que ya se escribieron en la semana 1.

Una decisión de diseño: cada estructura aparece **dos veces seguidas**, primero
en pseudocódigo y justo después en Python. No en secciones separadas. La
confusión más cara del semestre es escribir `=` donde va `==`, y se cura viendo
las dos formas pegadas, no en dos capítulos distintos.

Recorte del 2026-09-22 (instrucción del profesor: ~30 minutos y más práctica):
se fue la teoría que ningún ejercicio medía (precedencia, round/abs/sqrt, el
anidado largo), dos de los tres quices de calentamiento y las demostraciones
repetidas. Los ejercicios conservan su NÚMERO porque la semana ya está liberada
y hay telemetría bajo esos ids: quedan el 1, el 2 y el 5; el 3 («La cadena de
notas») se quitó porque medía lo mismo que el 5 —una cadena de decisiones en la
que el orden manda— y el 4 no existe.
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
        meta_xp=5,
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

Hasta ahora tus algoritmos hacían siempre lo mismo: leer, calcular, escribir.
Esta semana empiezan a **decidir**.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Escribir una **expresión booleana** y saber si vale Verdadero o Falso antes de
  ejecutarla.
- Combinar condiciones con **y**, **o** y **no**.
- Escribir un **Si**, un **Si-Sino** y una **cadena Si-Sino Si**, en pseudocódigo
  y en Python.

**Lo que NO se te pide todavía:** repetir algo muchas veces. Eso es la semana 4.

Este cuadernillo tiene **35 puntos** y **5 XP**. La insignia se llama
«Quien decide».
""")

    # =========================================================================
    # Bloque 1 — Calentamiento
    # =========================================================================
    c.seccion(1, "Calentamiento", 1, """Una pregunta de la semana pasada. No tiene nota: da XP y te dice si puedes
seguir.""")

    c.code("quiz_asignacion()")

    # =========================================================================
    # Bloque 2 — El gancho
    # =========================================================================
    c.seccion(2, "¿Puedes matricular la materia?", 2, """En la UIS, para matricular una materia tienen que cumplirse **tres** cosas a
la vez: haber aprobado el prerrequisito, tener cupo y estar a paz y salvo.
Basta con que falle **una** para que la respuesta sea no.

Ejecuta la celda y fíjate solo en cuándo sale Verdadero.""")

    c.code('''evaluar(
    "True and True and True",     # aprobó, hay cupo, está a paz y salvo
    "True and False and True",    # no hay cupo
    "True and True and False",    # debe plata
    "False and True and True",    # le falta el prerrequisito
)''')

    c.md("""Una sola vez salió Verdadero: cuando las tres se cumplían. Eso es la palabra
**y**. La otra mitad de hoy es **o**, que se conforma con una.
""")

    # =========================================================================
    # Bloque 3 — Concepto en corto
    # =========================================================================
    c.seccion(3, "Concepto en corto", 3, """Tres ideas, y ninguna es larga.""")

    c.md("""### 3A. Una expresión booleana es una pregunta con dos respuestas posibles

`nota >= 3.0` no es un cálculo: es una **pregunta**, y se contesta con
**Verdadero** o **Falso**. Es el `bool` de la semana 1, pero ahora lo
**calculas** comparando:
""")

    c.code('''evaluar(
    "4.2 >= 3.0",
    "4.2 == 3.0",
    "4.2 != 3.0",
    "4.2 < 3.0",
)''')

    c.md("""> **El error que va a cometer media clase.** En matemáticas `=` compara. En
> programación `=` **guarda** y `==` compara. Si escribes `if nota = 3.0` Python
> te para en seco con un error de sintaxis.

### 3B. Los operadores, los tres grupos

Ejecuta la chuleta cada vez que dudes. Dos son nuevos: **`div`** (`//`) divide
y tira los decimales, `7 // 2` es `3`; **`mod`** (`%`) da el residuo, `7 % 2`
es `1`, y por eso «¿es par?» se escribe `numero % 2 == 0`.
""")

    c.code("chuleta_operadores()")

    c.md("""### 3C. Y, o, no

Ejecuta la celda: el color hace el resumen mejor que cualquier párrafo. Y
**no** simplemente le da la vuelta: `no Verdadero` es Falso.
""")

    c.code("tablas_de_verdad()")

    c.md("""> **Cuidado con la trampa del español.** «Si la nota no es 3 ni 4» no se
> escribe `nota != 3 or nota != 4` —eso es Verdadero siempre— sino
> `nota != 3 and nota != 4`. Cuando el enunciado dice «ni… ni…», casi siempre
> va **y**.
""")

    # =========================================================================
    # Bloque 4 — Laboratorio
    # =========================================================================
    c.seccion(4, "Laboratorio", 4, """Cada estructura aparece dos veces seguidas: primero en pseudocódigo, y justo
debajo en Python. Léelas juntas.""")

    c.md("""### 4A. El Si simple: hacer algo, o no hacer nada

```
Si nota >= 3.0 Entonces
    Escribir "Aprobaste"
FinSi
```

```python
if nota >= 3.0:
    print("Aprobaste")
```

`Si … Entonces` es `if …:` —los dos puntos son obligatorios— y `FinSi` no
existe: en Python cierra la **sangría**. Lo que está corrido cuatro espacios
pertenece al `if`; lo que vuelve al margen, no. Ejecuta y mira la diferencia:
""")

    c.code('''nota = 2.5

if nota >= 3.0:
    print("Esta linea es del if: solo sale si aprobaste")
print("Esta linea NO es del if: sale siempre")''')

    c.md("""### 4B. Si-Sino: dos caminos, siempre se toma uno

```
Si nota >= 3.0 Entonces
    Escribir "Aprobaste"
Sino
    Escribir "Reprobaste"
FinSi
```

```python
if nota >= 3.0:
    print("Aprobaste")
else:
    print("Reprobaste")
```

Ejecútalo en el motor de pseudocódigo, que además te dibuja el diagrama de
flujo:
""")

    # El diagrama lo pidió el profesor mirando esta misma sección: «viendo ahí
    # la flechita es más fácil ver por qué sí se ejecuta».
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

Cuando hay tres o más respuestas, encadenas. Se prueba de arriba abajo y se
queda con la **primera** que se cumple, así que va **de lo más exigente a lo
menos exigente**: si pusieras `nota >= 3.0` primero, un 4.8 entraría por ahí y
nunca llegaría a «Excelente».

```
Si nota >= 4.5 Entonces
    Escribir "Excelente"
Sino Si nota >= 3.0 Entonces
    Escribir "Aprobado"
Sino
    Escribir "Reprobado"
FinSi
```

En Python `elif` es la abreviatura de `else if`. Cambia el 4.8 por otras notas:
""")

    c.code('''nota = 4.8

if nota >= 4.5:
    print("Excelente")
elif nota >= 3.0:
    print("Aprobado")
else:
    print("Reprobado")''')

    c.md("""> **Anidar** es meter un `if` dentro de otro. Hazlo solo cuando necesites
> **decir algo distinto** en cada caso; si las dos condiciones tienen que
> cumplirse a la vez y te da igual cuál falló, únelas con `and`.
""")

    # =========================================================================
    # Bloque 5 — Ejercicios
    # =========================================================================
    c.seccion(5, "Tres ejercicios", 23, """Aquí se juega tu nota: **35 puntos** en tres ejercicios, de menos a más.

Cada celda de solución trae la línea `raise NotImplementedError(...)`: le dice
a la plataforma que el ejercicio **aún no se ha hecho**, para que una plantilla
en blanco nunca cuente como un intento. Escribe tu solución y **bórrala**; si
la dejas, tu código no llega a evaluarse.

Si te atascas, `pista("E1")`, `pista("E2")` o `pista("E5")` te dan hasta tres
ayudas escalonadas — pedirlas no resta puntos.""")

    # --- Ejercicio 1 ------------------------------------------------------
    c.ejercicio(
        numero=1, competencias=['I3'], titulo="Verdadero o falso", estrellas=1, puntos=10,
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
        partida='''# Escribe tu respuesta en cada llave y recuerda borrar la línea raise NotImplementedError
RESPUESTAS = {
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

Completa el algoritmo y guarda el pseudocódigo **completo** en la variable
`ALGORITMO_E2`, como texto entre triples comillas. La prueba lo va a **ejecutar**
con el motor del curso.

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
        partida='''# Escribe tu pseudocódigo completo y recuerda borrar la línea raise NotImplementedError
ALGORITMO_E2 = """
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

    # --- Ejercicio 5 ------------------------------------------------------
    # Conserva su numero de siempre (commit e56c399): la semana esta liberada
    # y la telemetria vive bajo ejercicio_5. Los numeros 3 y 4 no existen.
    c.ejercicio(
        numero=5, competencias=['I3'], titulo="¿Puede matricular?", estrellas=3, puntos=15,
        enunciado="""El del gancho, ahora en serio.

`matricula(aprobo, cupo, paz_y_salvo)` recibe tres booleanos y **devuelve un
texto** explicando la situación: no basta con decir sí o no, hay que decir
**qué** falló.

| Situación | Devuelve |
|---|---|
| Las tres se cumplen | `"Matricula aprobada"` |
| No aprobó el prerrequisito | `"Falta el prerrequisito"` |
| Aprobó, pero no hay cupo | `"Sin cupo"` |
| Aprobó, hay cupo, pero debe plata | `"Pendiente financiero"` |

**El orden manda.** Si le falta el prerrequisito, eso es lo primero que hay que
decirle, aunque además deba plata. Y si aprobó pero no hay cupo, el estado
financiero da igual.""",
        partida='''# Escribe tu función y recuerda borrar la línea raise NotImplementedError
def matricula(aprobo, cupo, paz_y_salvo):
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

    # =========================================================================
    # Bloque 6 — El tutor
    # =========================================================================
    c.seccion(6, "Habla con el asistente", 1, """Tienes **cinco preguntas** para todo este cuadernillo. Guárdalas para el
último ejercicio, que es el difícil: si te atascas en una predicción, ejecuta
la expresión y mírala; si te atascas en pseudocódigo, el motor te dice la
línea y qué esperaba.

Mal: «no me sale el 5». Bien: «con `matricula(False, True, False)` mi función
devuelve "Pendiente financiero" y esperaba "Falta el prerrequisito". ¿Qué tiene
que ver el orden de mis `if`?». La segunda dice qué probaste, qué salió y qué
esperabas; con la primera el tutor solo puede adivinar.""")

    # =========================================================================
    # Bloque 7 — Cierre
    # =========================================================================
    c.seccion(7, "Cierre", 1, """Dos preguntas que solo te interesan a ti. Nadie las corrige.""")

    c.md("""- ¿Sabrías explicarle a alguien de tu casa **por qué** `=` y `==` no son lo
  mismo, sin usar la palabra «programación»?
- De los tres ejercicios, ¿cuál te costó más? ¿Fue por la lógica o por la
  sintaxis? No es lo mismo, y saber cuál te frena cambia cómo estudias.

**Lo que viene:** la semana 4 te da lo único que te falta para escribir
cualquier programa: **repetir**.

| Palabra | Qué significa |
|---|---|
| **Expresión booleana** | Una pregunta que se contesta con Verdadero o Falso |
| **Operador relacional** | El que compara dos valores: `==`, `!=`, `<`, `>`, `<=`, `>=` |
| **Operador lógico** | El que combina respuestas: `and`, `or`, `not` |
| **Anidar** | Meter una decisión dentro de otra |
| **`div` / `//`** | División que descarta los decimales |
| **`mod` / `%`** | El residuo de una división |
""")

    return c


if __name__ == "__main__":
    print(construir().a_dict()["cells"].__len__(), "celdas")
