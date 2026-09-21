#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 5: «Consolidar».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 5 — Primera evaluación y consolidación del entorno Python.

50 puntos de nbgrader en cuatro ejercicios, 85 XP y la insignia «Media vuelta».

Dos decisiones de contenido:

- **La sesión 1 es la primera evaluación, así que aquí NO hay examen.** El
  cuadernillo trae la guía de repaso con la que llegar a él: el mapa de las
  cuatro semanas, la tabla de las tres estructuras y un autodiagnóstico por
  ejes. El primer ejercicio es de repaso a propósito; los otros tres son del
  contenido nuevo de la sesión 2.
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

from constructor import Cuadernillo  # noqa: E402

MOTOR = os.path.join(os.path.dirname(AQUI), "motor")


def construir(motor_comprimido=True):
    c = Cuadernillo(
        codigo="semana_05",
        titulo="Consolidar",
        semana=5,
        meta_xp=85,
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

Media vuelta. Llevas cuatro semanas y ya tienes **las tres estructuras** con las
que se escribe cualquier programa que exista. No es una frase motivadora: es
literal, y en la sección 2 vas a ver por qué.

Esta semana tiene evaluación. Este cuadernillo **no es el examen**: es la guía
con la que llegar a él, y el contenido nuevo de la segunda clase.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Ver las cuatro semanas como **una sola cosa** y no como cuatro temas sueltos.
- Reconocer, en cualquier programa, dónde está la secuencia, dónde la decisión
  y dónde la repetición.
- Contar qué hace Python con tu archivo desde que lo guardas hasta que sale el
  resultado.
- Escribir la **estructura mínima** de un programa Python que pide datos,
  calcula y responde.
- Usar `input()` y convertir lo que devuelve al tipo que necesitas — y explicar
  por qué hay que convertirlo.
- Explicar qué significa que Python decida el tipo **al ejecutar**, y qué
  problema te evita saberlo.

Este cuadernillo tiene **50 puntos** y **85 XP**. La insignia se llama
«Media vuelta».
""")

    # =========================================================================
    c.seccion(1, "Dónde estás", 10, """Antes de repasar, mira el conjunto. Cuatro semanas en una imagen.""")

    c.code("mapa_del_curso()")

    c.md("""Si alguna columna te suena a chino, ese es el cuadernillo al que tienes que
volver **antes** de la evaluación. No después.
""")

    # =========================================================================
    c.seccion(2, "Las tres estructuras", 15, """Aquí está la idea que ordena todo el semestre, y conviene decirla sin adornos.""")

    c.code("las_tres_estructuras()")

    c.md("""Eso no es una simplificación para primer semestre: es un resultado demostrado.
Cualquier algoritmo que se pueda escribir, se puede escribir usando solo esas
tres. Todo lo que veas después —funciones, listas, objetos, redes neuronales—
está construido encima, y por dentro sigue siendo esto.

Míralo en un programa de verdad. Este tiene las tres, y están señaladas:
""")

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
    c.seccion(3, "Autodiagnóstico", 15, """Tres preguntas, una por eje. No tienen nota: te dicen dónde estás flojo
mientras todavía hay tiempo de arreglarlo.""")

    c.code("quiz_errores()")
    c.code("quiz_estructuras()")
    c.code("quiz_ciclo()")

    c.md("""> **Cómo usar esto.** Si fallaste una, no basta con leer la explicación: vuelve
> al cuadernillo de esa semana y **rehaz un ejercicio**. Leer da la sensación de
> haber entendido; escribir es lo que lo demuestra.

### Chuleta para la evaluación

| Si te preguntan… | Acuérdate de… |
|---|---|
| El tipo de un error | ¿Arranca? No → sintaxis. ¿Se estrella? → ejecución. ¿Miente? → lógica |
| `=` frente a `==` | Uno guarda, dos comparan |
| Una cadena `if/elif/else` | Se ejecuta **solo la primera** que se cumple: el orden manda |
| Un ciclo que no para | Falta el paso, o el paso no acerca la condición a ser falsa |
| `range(5)` | Da 0, 1, 2, 3, 4. El 5 **no** entra |
| Contador o acumulador | ¿Cuántos? contador. ¿Cuánto suman? acumulador |
| Precedencia | Paréntesis, `*` `/`, `+` `-`, comparar, `not`, `and`, `or` |
""")

    # =========================================================================
    c.seccion(4, "Qué hace Python con tu archivo", 25, """Contenido nuevo, y es de la segunda clase. Hasta ahora ejecutabas celdas sin
preguntarte qué pasa por debajo. Toca preguntárselo.""")

    c.md("""### 4A. De tu archivo al resultado

Cuando le das a ejecutar, Python hace tres cosas **en este orden**:

1. **Lee** tu archivo entero y comprueba que esté bien escrito. Si hay un
   paréntesis sin cerrar o falta un `:`, para aquí y no ejecuta **nada** — ni
   siquiera la primera línea, aunque esa estuviera bien. Es el error de
   sintaxis de la semana 1.
2. Si pasó la comprobación, lo **traduce** a una forma interna más compacta.
   Eso es asunto suyo y no hace falta que lo veas.
3. **Ejecuta línea a línea**, en orden. Cada línea con los valores que existan
   en ese momento — es exactamente lo que trazaste en la semana 1.

De ahí sale algo que explica un montón de cosas: **un error de la línea 40 no
aparece hasta que la ejecución llega a la línea 40**. Si tu programa se estrella
a la mitad, lo de antes ya pasó de verdad. Los archivos que escribiste están
escritos. Eso no se deshace.

### 4B. La estructura mínima de un programa

Casi todo programa que vas a escribir este semestre tiene la misma forma, y es
la de la semana 2:

```python
# 1. ENTRADA — conseguir los datos
nombre = input("Tu nombre: ")

# 2. PROCESO — calcular
saludo = "Hola, " + nombre

# 3. SALIDA — responder
print(saludo)
```

Entrada, proceso, salida. Lo mismo que dibujabas en pseudocódigo, ahora en
Python y ejecutándose de verdad.

### 4C. `input()` siempre devuelve texto

Esta es la trampa que atrapa a todo el mundo una vez. **Siempre.** Aunque el
usuario escriba `25`, lo que llega es `"25"`, texto.

Y con texto, `+` no suma: **pega**.
""")

    c.code('''ver_tipos(
    '"3" + "4"',      # texto + texto: pega
    "3 + 4",          # numero + numero: suma
    'int("3") + 4',   # convertido a entero: suma
)''')

    c.md("""Por eso hay que **convertir** lo que devuelve `input()` antes de calcular con
ello:

```python
edad = int(input("Tu edad: "))        # a entero
nota = float(input("Tu nota: "))      # a decimal
```

> **Y si el usuario escribe cualquier cosa,** `int("hola")` se estrella con un
> `ValueError`. Es un error de **ejecución**: no lo ves hasta que ocurre. La
> forma de blindarse es repetir la pregunta con un `while` hasta que el dato
> sirva.

### 4D. Python decide el tipo al ejecutar

En Python no declaras el tipo de una variable: se lo pones al asignarla, y él lo
deduce. Eso no significa que el tipo no exista — significa que se decide **al
ejecutar**, no antes.

La consecuencia práctica: una variable puede cambiar de tipo a mitad de programa
sin que nadie te avise. Ejecuta y míralo:
""")

    c.code('''x = 5
print("x vale", x, "y es de tipo", type(x).__name__)

x = "cinco"
print("ahora x vale", x, "y es de tipo", type(x).__name__)''')

    c.md("""No es un error: es cómo funciona. Pero explica la mitad de los errores de
ejecución del semestre — el programa se estrella porque una variable llegó con
un tipo que no esperabas. Cuando eso pase, `type(variable)` es lo primero que
hay que mirar.
""")

    # --- mCP88 (I7): investigar y seleccionar fuentes confiables ------------
    # Va como markdown con una fuente externa real, NO como ejercicio
    # calificable: el encargo lo pide asi y con razon. No se mide con trazas de
    # actividad, asi que I7 no aparecera nunca en competencias.json y su nivel
    # sera siempre nulo. Es deliberado, no un olvido; esta dicho tambien en
    # docs/modelo_microcompetencias.md, seccion "Lo que este modelo NO hace".
    c.md("""### 4E. Compruébalo en la fuente, no en un blog

Todo lo de esta sección lo puedes verificar tú, y conviene que lo hagas al menos
una vez en el semestre. Python tiene documentación **oficial**, escrita por
quien hace el lenguaje, y está en español:

**→ [Glosario de Python — «interpretado»](https://docs.python.org/es/3/glossary.html#term-interpreted)**

Ábrelo y busca la entrada *interpretado*. Vas a ver que la propia documentación
matiza lo que acabas de leer: Python compila a bytecode y ese bytecode se
interpreta, así que la frontera entre «compilado» e «interpretado» no es la
raya limpia que suele contarse.

**Por qué te lo pedimos.** En los próximos cuatro semestres vas a buscar
respuestas de programación cientos de veces, y la diferencia entre resolver un
problema en diez minutos o en dos horas casi siempre es la fuente. Tres señales
de que una fuente aguanta:

| Señal | Qué mirar |
|---|---|
| **Quién la escribe** | ¿Hay autor o institución responsable? La documentación oficial y los libros del curso lo tienen; un foro anónimo, no |
| **De cuándo es** | Python cambia. Una respuesta de 2011 puede ser correcta y estar obsoleta a la vez |
| **Si se puede comprobar** | ¿Puedes ejecutar lo que dice y ver si pasa? Si no, desconfía |

Esto no tiene nota en este cuadernillo. Tiene algo mejor: es lo que te va a
sacar de los atascos cuando ya no haya cuadernillo.
""")

    # =========================================================================
    c.seccion(5, "Cuatro ejercicios", 35, """**50 puntos.** El primero es de repaso y los tres últimos, del contenido
nuevo de esta clase. Esta semana el cuadernillo es corto a propósito: el peso
está en la evaluación, y repetir aquí lo que ya se evalúa aparte no ayuda a
nadie.""")


    c.ejercicio(
        numero=1, competencias=['I3'], titulo="Repaso — la decisión", estrellas=2, puntos=10,
        enunciado="""La UIS cobra la matrícula según el estrato:

| Estrato | Descuento |
|---|---|
| 1 y 2 | 50 % |
| 3 | 30 % |
| 4 en adelante | ninguno |

`matricula(base, estrato)` devuelve lo que hay que pagar.

`matricula(1000000, 1)` es 500000. `matricula(1000000, 3)` es 700000.
`matricula(1000000, 5)` es 1000000.""",
        partida='''def matricula(base, estrato):
    ...''',
        solucion='''def matricula(base, estrato):
    if estrato <= 2:
        return base * 0.5
    elif estrato == 3:
        return base * 0.7
    return base''',
        pruebas='''assert callable(matricula), "matricula debe ser una funcion"
assert abs(matricula(1000000, 1) - 500000) < 0.01
assert abs(matricula(1000000, 3) - 700000) < 0.01
assert abs(matricula(1000000, 5) - 1000000) < 0.01
print("matricula(1000000, 1) =", matricula(1000000, 1))''',
        pruebas_ocultas='''assert abs(matricula(1000000, 2) - 500000) < 0.01, "El estrato 2 tambien lleva 50%"
assert abs(matricula(1000000, 4) - 1000000) < 0.01, "Del 4 en adelante no hay descuento"
assert abs(matricula(800000, 3) - 560000) < 0.01
assert abs(matricula(0, 1) - 0) < 0.01''',
        pistas=[
            "Tres respuestas posibles: una cadena de dos preguntas mas el caso que "
            "sobra.",
            "El primer escalon cubre DOS estratos, el 1 y el 2. Se puede preguntar por "
            "los dos con una sola comparacion.",
            "Pagar con 50% de descuento es pagar el 50%: `base * 0.5`. Con 30% de "
            "descuento, el 70%.",
        ],
    )


    c.ejercicio(
        numero=2, competencias=['I3'], titulo="input devuelve texto", estrellas=2, puntos=10,
        enunciado="""Este programa está mal y **no da error**: por eso es peligroso.

```python
edad = input("Tu edad: ")
print("El ano que viene tendras", edad + 1)
```

Si el usuario escribe `25`, se estrella con `TypeError`. Y si el programa fuera
`edad + "1"`, escribiría `251` sin quejarse.

Escribe `siguiente_edad(texto)` que recibe la edad **como texto** —tal cual la
devuelve `input()`— y devuelve, como **entero**, la edad del año que viene.

`siguiente_edad("25")` debe devolver `26`, el número, no `"251"` ni `"26"`.""",
        partida='''def siguiente_edad(texto):
    ...''',
        solucion='''def siguiente_edad(texto):
    return int(texto) + 1''',
        pruebas='''assert callable(siguiente_edad), "siguiente_edad debe ser una funcion"
_r = siguiente_edad("25")
assert _r == 26, f"siguiente_edad('25') debe dar 26 y dio {_r!r}"
assert isinstance(_r, int), f"Debe devolver un entero y devolvio {type(_r).__name__}"
print("siguiente_edad('25') =", _r, "de tipo", type(_r).__name__)''',
        pruebas_ocultas='''assert siguiente_edad("0") == 1
assert siguiente_edad("99") == 100
assert not isinstance(siguiente_edad("7"), str), "No devuelvas texto: devuelve el numero"
assert siguiente_edad("7") == 8''',
        pistas=[
            "El problema es el tipo: te llega texto y necesitas un numero. Hay una "
            "funcion de una palabra que hace justo esa conversion.",
            "`int(\"25\")` da el entero 25. Solo despues de convertir puedes sumar.",
            "Si sumas primero y conviertes despues, `\"25\" + 1` se estrella antes de "
            "llegar a la conversion. El orden importa: convertir, y entonces sumar.",
        ],
    )

    c.ejercicio(
        numero=3, competencias=['I3'], titulo="¿De qué tipo resulta?", estrellas=3, puntos=15,
        enunciado="""Python decide el tipo al ejecutar. Predice el tipo del **resultado** de cada
expresión y escribe su nombre entre comillas: `"int"`, `"float"`, `"str"` o
`"bool"`.

| | Expresión |
|---|---|
| `a` | `7 + 3` |
| `b` | `7 / 2` |
| `c` | `7 // 2` |
| `d` | `"7" + "3"` |
| `e` | `7 > 3` |
| `f` | `float(7)` |

Cuidado con `b`: en Python la división normal **siempre** da decimales, aunque
la cuenta salga exacta.""",
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
print("Formato correcto. Los tipos se revisan al calificar.")''',
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
        numero=4, competencias=['I3'], titulo="Un programa completo", estrellas=4, puntos=15,
        enunciado="""El de cierre junta todo: entrada, conversión, repetición, decisión y salida.

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
    c.seccion(6, "Habla con el asistente", 5, """**Cinco preguntas** para todo el cuadernillo.""")

    c.md("""### En qué gastarlas

En el repaso, ninguna: si fallas ahí, volver a ese cuadernillo es mejor
inversión que una pregunta. En los de tipos tampoco hacen falta — ejecuta
`ver_tipos(...)` y compruébalo tú, está permitido. Guarda casi todas para el
último, que es el más largo.

Y un consejo para la evaluación: las preguntas que **no** gastes aquí no se
acumulan, pero el tiempo que ganes sí. Si un ejercicio de repaso te sale solo,
úsalo como señal de que ese tema ya lo tienes y estudia otro.
""")

    # =========================================================================
    c.seccion(7, "Cierre", 7, """Tres preguntas antes de la evaluación. Contéstatelas de verdad.""")

    c.md("""- De las cuatro semanas del mapa, ¿cuál te costó más? Esa es la que hay que
  repasar, aunque sea la que menos ganas dan.
- ¿Podrías escribir, ahora mismo y sin mirar, un programa que pida un número y
  diga si es par? Si la respuesta es «creo que sí», pruébalo. «Creo que sí» y
  «sí» no son lo mismo, y la evaluación distingue.
- ¿Cuál de los tres tipos de error te ha frenado más? Si es el de lógica, la
  cura no es estudiar más: es **probar más**.

### Lo que viene

La semana 6 es la más exigente de la primera mitad: listas y cadenas, buscar
dentro de ellas y **cuatro algoritmos de ordenamiento**. Ahí vas a ver por qué
importa que un algoritmo haga menos operaciones que otro — y no como teoría,
sino midiéndolo.

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **Intérprete** | El programa que lee tu código y lo ejecuta línea a línea |
| **Estructura mínima** | Entrada, proceso, salida: la forma de casi todo programa |
| **`input()`** | Pide un dato al usuario. Devuelve **siempre** texto |
| **Conversión** | Pasar un valor de un tipo a otro: `int()`, `float()`, `str()` |
| **Tipado dinámico** | Que Python decida el tipo al ejecutar, no antes |
""")

    return c
