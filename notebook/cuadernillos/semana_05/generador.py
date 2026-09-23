#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 5: «Consolidar».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 5 — Primera evaluación y consolidación del entorno Python.

30 puntos de nbgrader en dos ejercicios, 5 XP y la insignia «Media vuelta».

Recortado el 2026-09-22 por pedido del profesor: de 56 a ~35 minutos. Se fue
el ejercicio de repaso del if/elif (ya lo mide la semana 3), el de convertir
un solo `input()` (lo mide el de cierre, que convierte una lista entera), dos
de los tres quices y la teoría repetida. Se quedan la tabla de tipos con
feedback inmediato y el programa completo.

Dos decisiones de contenido:

- **La sesión 1 es la primera evaluación, así que aquí NO hay examen.** El
  cuadernillo trae la guía de repaso con la que llegar a él: el mapa de las
  cuatro semanas, un programa con las tres estructuras señaladas y un
  autodiagnóstico. Los dos ejercicios son del contenido nuevo de la sesión 2.
- El temario de la sesión 2 dice «lenguaje compilado e interpretado». Como el
  profesor pidió que no haya comparaciones entre lenguajes ni temas de bajo
  nivel, aquí se cuenta **solo qué hace Python con tu archivo** —lee, comprueba,
  ejecuta línea a línea— sin ponerlo al lado de ningún otro lenguaje. Se cubre
  el fondo del tema sin el contenido que quedó fuera.
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
        codigo="semana_05",
        titulo="Consolidar",
        semana=5,
        meta_xp=5,
        insignia="Media vuelta",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[
            os.path.join(MOTOR, "pseudo_uis.py"),
            os.path.join(AQUI, "contenido.py"),
        ],
    )

    c.md("""# Consolidar
### Semana 5 · Unidad 5 · Primera evaluación y consolidación del entorno Python

Media vuelta. Esta semana tiene evaluación. Este cuadernillo **no es el
examen**: es la guía corta para llegar a él, y el contenido nuevo de la segunda
clase.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Reconocer, en cualquier programa, la secuencia, la decisión y la repetición.
- Contar qué hace Python con tu archivo, y por qué `input()` hay que convertirlo.
- Explicar qué significa que Python decida el tipo **al ejecutar**.

Este cuadernillo tiene **30 puntos** y **5 XP**. La insignia se llama
«Media vuelta».
""")

    # =========================================================================
    c.seccion(1, "Dónde estás", 1, """Cuatro semanas en una imagen. Si alguna columna te suena a chino, ese es el
cuadernillo al que volver **antes** de la evaluación.""")

    c.code("mapa_del_curso()")

    # =========================================================================
    c.seccion(2, "Las tres estructuras", 1, """Secuencia, decisión y repetición. No hay una cuarta: cualquier algoritmo se
escribe con estas tres. Míralas en un programa de verdad, señaladas.""")

    c.code('''# SECUENCIA: una linea detras de otra
total = 0
aprobadas = 0

# REPETICION: esto se ejecuta cinco veces
for nota in range(1, 6):
    total = total + nota

    # DECISION: dentro de la repeticion
    if nota >= 3:
        aprobadas = aprobadas + 1

# SECUENCIA otra vez
print("Suma:", total, "· Aprobadas:", aprobadas)''')

    # =========================================================================
    c.seccion(3, "Autodiagnóstico", 2, """Una pregunta sin nota. Si la fallas, vuelve a la semana 1 y **rehaz un
ejercicio**: leer da la sensación de haber entendido; escribir lo demuestra.""")

    c.code("quiz_errores()")

    c.md("""### Chuleta para la evaluación

| Si te preguntan… | Acuérdate de… |
|---|---|
| El tipo de un error | ¿Arranca? No → sintaxis. ¿Se estrella? → ejecución. ¿Miente? → lógica |
| `=` frente a `==` | Uno guarda, dos comparan |
| `if/elif/else` | Se ejecuta **solo la primera** que se cumple |
""")

    # =========================================================================
    c.seccion(4, "Qué hace Python con tu archivo", 5, """Contenido nuevo, de la segunda clase.""")

    c.md("""### 4A. De tu archivo al resultado

Cuando le das a ejecutar, Python hace tres cosas **en este orden**:

1. **Lee** tu archivo entero y comprueba que esté bien escrito. Si falta un
   `:`, para aquí y no ejecuta **nada**: error de sintaxis.
2. Lo **traduce** a una forma interna más compacta. Asunto suyo.
3. **Ejecuta línea a línea**, en orden.

Por eso un error de la línea 40 **no aparece hasta que la ejecución llega
ahí**: lo de antes ya pasó de verdad.

### 4B. La estructura mínima de un programa

Entrada, proceso, salida, como en la semana 2:

```python
nombre = input("Tu nombre: ")   # ENTRADA
saludo = "Hola, " + nombre      # PROCESO
print(saludo)                   # SALIDA
```

### 4C. `input()` siempre devuelve texto

Aunque el usuario escriba `25`, lo que llega es `"25"`, texto. Y con texto,
`+` no suma: **pega**.
""")

    c.code('''ver_tipos(
    '"3" + "4"',      # texto + texto: pega
    "3 + 4",          # numero + numero: suma
    'int("3") + 4',   # convertido a entero: suma
)''')

    c.md("""Por eso hay que **convertir** lo que devuelve `input()` antes de calcular:

```python
edad = int(input("Tu edad: "))        # a entero
nota = float(input("Tu nota: "))      # a decimal
```

> Si el usuario escribe `hola`, `int("hola")` se estrella: error de **ejecución**.

### 4D. Python decide el tipo al ejecutar

Python decide el tipo de cada variable **al ejecutar**, así que puede cambiar
a mitad de programa sin avisar. Y ojo: `/` da **siempre** decimal, aunque
salga exacto; `//` descarta los decimales y da entero. Ejecuta y míralo:
""")

    c.code('''x = 5
print("x vale", x, "y es de tipo", type(x).__name__)

x = "cinco"
print("ahora x vale", x, "y es de tipo", type(x).__name__)''')

    c.md("""No es un error: es cómo funciona. Cuando un programa se estrelle porque una
variable llegó con un tipo que no esperabas, `type(variable)` es lo primero que
hay que mirar.
""")

    # --- mCP88 (I7): investigar y seleccionar fuentes confiables ------------
    # Va como markdown con una fuente externa real, NO como ejercicio
    # calificable: el encargo lo pide asi y con razon. No se mide con trazas de
    # actividad, asi que I7 no aparecera nunca en competencias.json y su nivel
    # sera siempre nulo. Es deliberado, no un olvido; esta dicho tambien en
    # docs/modelo_microcompetencias.md, seccion "Lo que este modelo NO hace".
    c.md("""### 4E. Compruébalo en la fuente, no en un blog

Python tiene documentación **oficial** en español. Ábrela y busca *interpretado*:

**→ [Glosario de Python — «interpretado»](https://docs.python.org/es/3/glossary.html#term-interpreted)**

Tres señales de que una fuente aguanta: **quién la escribe**, **de cuándo es**
y **si se puede comprobar** ejecutándolo. No tiene nota: es lo que te saca de
los atascos cuando ya no haya cuadernillo.
""")

    # =========================================================================
    c.seccion(5, "Dos ejercicios", 26, """**30 puntos**, los dos del contenido nuevo. El peso de la semana está en la
evaluación.""")

    c.ejercicio(
        numero=1, competencias=['I3'], titulo="¿De qué tipo resulta?", estrellas=3, puntos=15,
        enunciado="""Predice el tipo del **resultado** de cada expresión y escribe su nombre entre
comillas: `"int"`, `"float"`, `"str"` o `"bool"`.

| | Expresión |
|---|---|
| `a` | `7 + 3` |
| `b` | `7 / 2` |
| `c` | `7 // 2` |
| `d` | `"7" + "3"` |
| `e` | `7 > 3` |
| `f` | `float(7)` |""",
        partida='''TIPOS = {
    "a": ...,
    "b": ...,
    "c": ...,
    "d": ...,
    "e": ...,
    "f": ...,
}''',
        solucion='''TIPOS = {
    "a": "int",
    "b": "float",
    "c": "int",
    "d": "str",
    "e": "bool",
    "f": "float",
}''',
        pruebas='''assert isinstance(TIPOS, dict) and set(TIPOS) == set("abcdef"), \\
    "TIPOS debe tener las seis llaves, de la a a la f"
assert set(TIPOS.values()) <= {"int", "float", "str", "bool"}, \\
    "Usa solo: int, float, str o bool, entre comillas"
# Se corrige aqui mismo, contra huellas: el alumno sabe al instante cual
# fallo y la respuesta no esta escrita en ninguna parte del cuadernillo.
revisar("ejercicio_3", TIPOS, {
    "a": ("8a37d9fcc243af62",
          "en `a`: dos enteros que se suman, ¿que puede salir?"),
    "b": ("db69953c22532bb0",
          "en `b` hay una `/`. Esa division tiene una regla propia: miralo en la seccion 4D"),
    "c": ("d0e3731ba11761b2",
          "en `c` el operador es `//`, que descarta los decimales"),
    "d": ("32faabd1d354cf72",
          "en `d` los dos lados son texto. `+` sobre texto no suma"),
    "e": ("ddbed1d7432e5cc3",
          "en `e` hay una comparacion, y una comparacion responde una pregunta de si o no"),
    "f": ("bbd258c25868f9a7",
          "en `f` mezcla un entero con un decimal: el resultado se queda con el mas ancho"),
})''',
        pruebas_ocultas='''assert TIPOS["a"] == "int", "entero + entero da entero"
assert TIPOS["b"] == "float", "la division / SIEMPRE da decimales, aunque salga exacta"
assert TIPOS["c"] == "int", "// descarta decimales y devuelve entero"
assert TIPOS["d"] == "str", "texto + texto pega y da texto"
assert TIPOS["e"] == "bool", "una comparacion siempre da True o False"
assert TIPOS["f"] == "float", "float() convierte a decimal, aunque el numero sea entero"''',
        pistas=[
            "Si dudas de alguna, ejecuta `ver_tipos('7 / 2')` en una celda nueva y "
            "compruebalo. Esta permitido: el ejercicio es entender, no adivinar.",
            "Las dos divisiones dan tipos distintos, y esa es la trampa. Una conserva "
            "los decimales y la otra los tira.",
            "Una comparacion nunca devuelve un numero: devuelve una respuesta de si o "
            "no. Y `float(7)` convierte aunque no haga falta: 7.0 sigue siendo decimal.",
        ],
    )

    c.ejercicio(
        numero=2, competencias=['I3'], titulo="Un programa completo", estrellas=4, puntos=15,
        enunciado="""Junta todo: conversión, repetición, decisión y salida.

`boletin(textos)` recibe una lista de notas **como texto** —tal cual llegarían
de `input()`— y devuelve un texto de tres líneas:

```
Notas: 3
Promedio: 3.50
Estado: Aprobado
```

Las reglas:

1. Convierte cada texto a número decimal.
2. `Notas:` es cuántas hay.
3. `Promedio:` con **dos decimales**.
4. `Estado:` es `Aprobado` si el promedio llega a 3.0, y `Reprobado` si no.
5. Las tres líneas separadas por `\\n`, sin salto al final.

Con `["4.0", "3.5", "2.5"]` el promedio es 3.33 y el estado Aprobado.

> Puedes recorrer la lista con `for i in range(len(textos))` y sacar cada
> elemento con `textos[i]`. Recorrerla directamente es de la semana 6.""",
        partida='''def boletin(textos):
    ...''',
        solucion='''def boletin(textos):
    suma = 0
    for i in range(len(textos)):
        suma = suma + float(textos[i])
    cuantas = len(textos)
    promedio = suma / cuantas
    estado = "Aprobado" if promedio >= 3.0 else "Reprobado"
    return f"Notas: {cuantas}\\nPromedio: {promedio:.2f}\\nEstado: {estado}"''',
        pruebas='''assert callable(boletin), "boletin debe ser una funcion"
_b = boletin(["4.0", "3.5", "2.5"])
assert isinstance(_b, str), "boletin debe DEVOLVER texto"
_l = _b.split("\\n")
assert len(_l) == 3, f"Deben ser tres lineas y tu devolviste {len(_l)}"
assert _l[0] == "Notas: 3", f"La primera linea debe ser 'Notas: 3' y es '{_l[0]}'"
assert _l[1] == "Promedio: 3.33", f"La segunda debe ser 'Promedio: 3.33' y es '{_l[1]}'"
assert _l[2] == "Estado: Aprobado", f"La tercera debe ser 'Estado: Aprobado' y es '{_l[2]}'"
print(_b)''',
        pruebas_ocultas='''_r = boletin(["2.0", "2.5"]).split("\\n")
assert _r[0] == "Notas: 2" and _r[1] == "Promedio: 2.25" and _r[2] == "Estado: Reprobado"
_u = boletin(["3.0"]).split("\\n")
assert _u[1] == "Promedio: 3.00", "Los dos decimales se muestran aunque sean ceros"
assert _u[2] == "Estado: Aprobado", "3.0 exacto aprueba"
assert boletin(["5.0", "5.0"]).endswith("Estado: Aprobado")
assert not boletin(["4.0"]).endswith("\\n"), "Sin salto de linea al final"''',
        pistas=[
            "Resuelvelo por partes y comprueba cada una antes de seguir: primero la "
            "suma, luego el promedio, luego el estado, y solo al final el texto.",
            "Cada elemento de la lista es texto: hay que convertirlo con `float(...)` "
            "ANTES de sumarlo, o Python los va a pegar en vez de sumarlos.",
            "Los dos decimales salen con `f\"{promedio:.2f}\"`. Y el salto de linea "
            "dentro de una f-string se escribe `\\\\n`.",
        ],
    )

    # =========================================================================
    c.seccion(6, "Habla con el asistente", 1, """**Cinco preguntas** para todo el cuadernillo. En el de tipos no hacen falta:
ejecuta `ver_tipos(...)` y compruébalo tú. Guárdalas para el último.""")

    # =========================================================================
    c.seccion(7, "Cierre", 2, """Dos preguntas antes de la evaluación.""")

    c.md("""- De las cuatro semanas del mapa, ¿cuál te costó más? Esa es la que hay que
  repasar.
- ¿Podrías escribir, sin mirar, un programa que pida un número y diga si es
  par? Si la respuesta es «creo que sí», pruébalo.

**Lo que viene:** la semana 6, listas y cadenas, buscar y **ordenar**.

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **`input()`** | Pide un dato al usuario. Devuelve **siempre** texto |
| **Conversión** | Pasar un valor de un tipo a otro: `int()`, `float()`, `str()` |
| **Tipado dinámico** | Que Python decida el tipo al ejecutar, no antes |
""")

    return c
