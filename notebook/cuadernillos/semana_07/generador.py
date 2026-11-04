#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 7: «Matrices».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 3 — Listas bidimensionales y matrices.

25 puntos de nbgrader en tres ejercicios, 5 XP y la insignia «Quien tabula».
Escrito ya con la forma a la que llegó el curso tras el recorte del 2026-09-22:
~30 minutos, teoría breve, tres ejercicios de 1★, 2★ y 3★ y un único quiz de
calentamiento.

De dónde sale el contenido (planeación académica 41333, semana 7): listas
bidimensionales; filas, columnas e índices; creación y recorrido; sumas por
fila y por columna; diagonal y transposición. El resultado esperado habla de
«desarrolla en equipo», que es el taller presencial y no se autocalifica.

TRES LÍMITES que se respetan a propósito, y que hay que tener presentes al
editarlo:

- **El intérprete de pseudocódigo del curso no conoce arreglos.** `Dimension
  m[3,3]` contesta «no conozco el símbolo '['» (comprobado contra
  `motor/pseudo_uis.py`: `Dimension` está en la lista de lo no soportado, y
  tampoco hay `Funcion`). Por eso esta semana no carga `pseudo_uis.py` y lo
  dice en voz alta en los objetivos: todo lo que se escribe y se califica es
  Python. Mismo criterio que la semana 06 con las listas.
- **El alumno NUNCA ha visto una lista de listas.** La sección 3 no explica
  sintaxis: dibuja el modelo mental (una fila es una lista; la matriz es una
  lista de filas; `m[0]` no es un número). Lo que sí trae de antes son los
  ciclos anidados de la semana 4 —la escalera de asteriscos— y la teoría se
  apoya en ellos en vez de volver a explicarlos.
- **`.append()` no se había enseñado** y hace falta para devolver una matriz
  nueva (Ejercicio 3). Se introduce en el laboratorio (4B), en dos líneas y
  usándolo, no como tema.

MICROCOMPETENCIAS. I3 (mCC87, «identifica variables y aspectos del problema
para armar el algoritmo») en los tres: los tres piden decidir qué índice se
mueve y qué índice se queda quieto, que es el aspecto del problema esta semana.
I1 (mCP17, «aplica conocimientos matemáticos») en el 2 y el 3, que es donde hay
matemáticas de verdad: una estadística de una característica —su máximo, que es
el divisor con el que se escala— y una transposición. NO va en el 1, que es
indexado puro — poner I1 ahí sería inflar la cobertura, y la cobertura de I1 va
corta precisamente porque se repartió con cuidado.
mCC103 (I4) no corresponde a esta semana y no se usa. mCA14 y mCA65, que la
planeación nombra para la semana 7, no se pueden medir con trazas: quedan fuera
y el cierre lo dice.

OJO con el número de unidad. La planeación 41333 tiene solo CUATRO unidades, y
la Unidad 3 abarca de la semana 3 a la 10: para esta semana dice «Unidad 3.
Listas bidimensionales y matrices». Pero los cuadernillos publicados usan
unidad = semana desde la semana 4 (la 4 dice «Unidad 4», la 6 «Unidad 6»), así
que aquí se sigue esa convención para que el alumno no vea un salto de «Unidad
6» a «Unidad 3» y lo reporte como error — ya pasó con la numeración 1, 2, 5 de
la semana 3. El título del tema sí es el de la planeación, literal. Corregir los
números de verdad implica tocar las semanas 4, 5 y 6, que están publicadas: es
decisión del profesor, no de aquí.
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
        codigo="semana_07",
        titulo="Matrices",
        semana=7,
        meta_xp=5,
        insignia="Quien tabula",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[os.path.join(AQUI, "contenido.py")],
    )

    c.md("""# Matrices
### Semana 7 · Unidad 7 · Listas bidimensionales y matrices

La semana pasada una variable pasó a guardar muchos datos **en fila**. Pero los
datos de verdad vienen en **tabla**: una hoja de cálculo, un registro de
calificaciones, un conjunto de entrenamiento. Esta semana aprendes a guardar una
tabla y a recorrerla.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Guardar una tabla en una **lista de listas** y leer cualquier celda con sus
  **dos** índices: `m[fila][columna]`.
- Recorrer una matriz entera con dos **ciclos anidados**, y recorrer una sola
  fila o una sola **columna**.
- Recorrer una **columna** —que en un conjunto de datos es una
  **característica**— para sacar una estadística de ella: su promedio y su
  **máximo**. Y **transponer** la matriz entera.

**Un aviso:** el intérprete de pseudocódigo del curso no conoce arreglos, así
que `Dimension m[3,3]` no se puede ejecutar. Esta semana todo se escribe y se
califica en Python. Son **25 puntos** y **5 XP**; la insignia se llama «Quien
tabula».
""")

    # =========================================================================
    c.seccion(1, "Calentamiento", 1, """Una de la semana pasada. Sin nota: da XP.""")
    c.code("quiz_recorrido()")

    # =========================================================================
    # El gancho de apertura: el problema antes de la sintaxis. Es barato y es lo
    # que hace que alguien siga leyendo (docs/cuadernillos_semanas_7_a_16.md §3).
    c.seccion(2, "Una tabla no cabe en una lista", 2, """Cuatro estudiantes y tres datos de cada uno. Ejecuta y mira la tabla:""")

    c.code("ver_tabla_datos()")

    c.md("""Con lo de la semana pasada tendrías que abrir **tres listas sueltas** —una por
columna— y llevar a mano la cuenta de que el elemento 2 de las tres es el mismo
estudiante. La salida es guardar la tabla **entera** en una sola variable, como
una lista cuyos elementos son listas. Ejecútala:
""")

    # Esta celda es EJECUTABLE y no un bloque de markdown, a propósito.
    # El 2026-10-05 la semana 06 dejó `dias` viviendo solo dentro de un bloque
    # de texto: la teoría de más abajo decía `dias[0]`, el alumno lo escribía
    # —que es justo lo que queremos que haga— y recibía un NameError. Aquí pasa
    # lo mismo con `datos`, que es el nombre con el que hablan la sección 3 y
    # todo el laboratorio, así que tiene que existir de verdad desde aquí.
    # De paso, el print adelanta los dos `len` que la sección 3B explica.
    c.code('''datos = [
    [12, 5, 1],
    [ 9, 7, 0],
    [15, 3, 1],
    [ 8, 6, 0],
]
print("Guardada una matriz de", len(datos), "filas y", len(datos[0]), "columnas")''')

    c.md("""Eso es una **matriz**, y ya es un **conjunto de datos** en el sentido que vas a
usar el resto de la carrera: cada **fila** es un **ejemplo** y cada **columna**,
una **característica**.
""")

    # =========================================================================
    c.seccion(3, "Concepto en corto", 4, """Una matriz es una lista cuyos elementos son listas. Todo lo demás sale de ahí.""")

    c.md("""### 3A. El modelo mental

Lee esto despacio, porque es el truco entero:

- Una **fila** es una lista: `[12, 5, 1]`.
- La **matriz** es una lista **de filas**: `[[12, 5, 1], [9, 7, 0], ...]`.
- Por eso `datos[0]` **no es un número**: es la primera fila, que es una lista
  completa. Para llegar hasta un número hacen falta **dos** índices.

```python
datos[0]        # [12, 5, 1]  — la primera FILA, que es una lista
datos[0][2]     # 1           — fila 0, columna 2: ahora sí, un número
len(datos)      # 4           — cuántas FILAS tiene la matriz
len(datos[0])   # 3           — cuántas COLUMNAS tiene esa fila
```

El orden no cambia nunca: **primero la fila, después la columna**. Ejecuta y
míralo dibujado:
""")

    c.code('ver_matriz(datos, resaltar=(1, 2), '
           'titulo="Los dos indices, y una celda marcada")')

    c.md("""### 3B. Las filas y las columnas no se cuentan igual

`len(matriz)` cuenta **filas**, porque los elementos de la matriz son filas; las
columnas se cuentan **dentro** de una fila, con `len(matriz[0])`. Todas las
filas de este curso tienen el mismo ancho, así que basta mirar la primera.
Confundir estos dos `len` es el error de la semana.
""")

    # =========================================================================
    # Los minutos de cada c.seccion no se escriben a ojo: tienen que cuadrar
    # (±15 %) con lo que estima estimar_tiempo.py, y build.py falla si no. Estos
    # suman 37, que es lo que pide el contenido. Si recortas o añades algo,
    # vuelve a correr `python3 estimar_tiempo.py semana_07` y ajusta aquí.
    c.seccion(4, "Laboratorio", 6, """Los recorridos de la semana. Ejecuta cada celda y mira la salida.""")

    c.md("""### 4A. Recorrer la matriz entera

Los ciclos anidados ya los tienes de la escalera de asteriscos: el de **fuera**
elige la fila y el de **dentro** recorre las columnas de esa fila.
""")

    c.code('''datos = [[12, 5, 1], [9, 7, 0], [15, 3, 1], [8, 6, 0]]

for f in range(len(datos)):
    for c in range(len(datos[f])):
        print("fila", f, "columna", c, "->", datos[f][c])''')

    c.md("""Fíjate en el orden: las tres celdas de la fila 0, después las de la fila 1, y
así. El ciclo de dentro es el que se mueve más rápido, igual que en la escalera.

### 4B. Un total por fila

Fijas la fila y mueves solo la columna. Para guardar los resultados hace falta
una pieza nueva: una lista que **arranca vacía** y a la que se añade al final
con `.append(...)`.
""")

    c.code('''datos = [[12, 5, 1], [9, 7, 0], [15, 3, 1], [8, 6, 0]]

totales = []                       # arranca vacia
for f in range(len(datos)):
    total = 0                      # el acumulador de la semana 4, pero por fila
    for c in range(len(datos[f])):
        total = total + datos[f][c]
    totales.append(total)          # un numero mas al final de la lista
print(totales)''')

    c.md("""`totales` tiene un número por fila: un total por ejemplo.

### 4C. Un total por columna

El único paso incómodo de la semana. El índice que se mueve es el de la
**fila**, y el de la columna se queda **quieto**: una columna se lee de arriba
abajo, no de izquierda a derecha.
""")

    c.code('''datos = [[12, 5, 1], [9, 7, 0], [15, 3, 1], [8, 6, 0]]

c = 0                              # la columna que miro: "horas de estudio"
total = 0
for f in range(len(datos)):
    total = total + datos[f][c]    # la f se mueve, la c no
print("total de la columna", c, ":", total)
print("promedio:", total / len(datos))''')

    c.md("""Ese promedio es una **estadística por característica**: lo primero que se mira
al recibir unos datos nuevos.

### 4D. La diagonal, y por qué importa

En una matriz **cuadrada** —tantas filas como columnas— las celdas donde los dos
índices coinciden forman la **diagonal**. Un solo ciclo las recorre:

```python
cuadrada = [[8, 1, 1],
            [2, 7, 1],
            [0, 2, 8]]

aciertos = 0
for i in range(len(cuadrada)):
    aciertos = aciertos + cuadrada[i][i]   # la celda [i][i]
print(aciertos)                            # 23
```

Si una matriz cuadrada cuenta, para cada clase real, cuántas veces un modelo
predijo cada clase, su diagonal son los **aciertos** y todo lo demás, errores.
Ejecuta:
""")

    c.code("ver_confusion()")

    c.md("""Esa tabla se llama **matriz de confusión** y la vuelves a ver en la semana 15,
con árboles de decisión. Su diagonal dividida entre el total se llama
**exactitud**.

### 4E. Transponer

**Transponer** es cambiar las filas por las columnas: lo que estaba en `m[f][c]`
acaba en `m[c][f]`. Ejecuta y mira el antes y el después:
""")

    c.code("ver_transpuesta()")

    c.md("""Un conjunto de datos se guarda como «ejemplos × características», y hay
herramientas que lo quieren al revés. Transponer es el paso que lleva de uno al
otro sin tocar un solo número.
""")

    # =========================================================================
    c.seccion(5, "Tres ejercicios", 22, """**25 puntos**, de menos a más. El primero te hace leer la matriz, el segundo la
recorre y el tercero la reconstruye.""")

    # Por qué este ejercicio NO usa `datos`, la matriz de la teoría:
    #
    # La escribió usándola, y la sección 3A anota precisamente `datos[0]`,
    # `datos[0][2]`, `len(datos)` y `len(datos[0])` con su resultado al lado.
    # Eso regalaba cuatro de las cinco respuestas: el ejercicio se resolvía con
    # Ctrl-F sobre una celda de teoría, que es la PRIMERA señal de que un
    # ejercicio sobra (docs/cuadernillos_semanas_7_a_16.md §2). La semana 06
    # evita lo mismo a propósito: su teoría anota `notas` y su primer ejercicio
    # pregunta por `dias`.
    #
    # `muestras` es otra matriz y, sobre todo, de otra FORMA: 3 x 4 donde la de
    # la teoría es 4 x 3. Así el que copie el «4 filas y 3 columnas» de arriba
    # se lleva las dos respuestas cruzadas, y el que cuente acierta.
    c.ejercicio(
        numero=1, competencias=['I3'], titulo="Leer la tabla", estrellas=1, puntos=5,
        enunciado="""Esta matriz está escrita al principio de tu celda, para que la tengas delante
mientras respondes. **No es la de la teoría**: tiene otra forma, así que los
números de arriba no te sirven y toca contar.

Completa el diccionario. `filas`, `columnas`, `arriba_derecha` y
`abajo_izquierda` son **números** (van sin comillas y sin corchetes);
`primera_fila` es una **lista** entera. Cada valor lo puedes escribir a mano o
sacarlo de la matriz (`muestras[0]`, `len(muestras)`): las dos formas valen.

| Llave | Qué vale |
|---|---|
| `filas` | cuántas filas tiene `muestras` |
| `columnas` | cuántas columnas tiene `muestras` |
| `primera_fila` | la primera fila completa, que es una lista |
| `arriba_derecha` | el número de la primera fila, última columna |
| `abajo_izquierda` | el número de la última fila, primera columna |""",
        partida='''# Tres muestras y cuatro mediciones de cada una.
muestras = [
    [21, 4, 9, 2],
    [17, 6, 3, 1],
    [25, 2, 7, 5],
]

CELDAS = {
    "filas": ...,
    "columnas": ...,
    "primera_fila": ...,
    "arriba_derecha": ...,
    "abajo_izquierda": ...,
}''',
        solucion='''CELDAS = {
    "filas": 3,
    "columnas": 4,
    "primera_fila": [21, 4, 9, 2],
    "arriba_derecha": 2,
    "abajo_izquierda": 25,
}''',
        # Las pruebas visibles NO nombran `muestras` a proposito. El constructor
        # deduce de la partida el nombre para la guarda «ejecuta TU celda»
        # cruzandolo con los nombres que usa la prueba: si la prueba usara
        # `muestras`, la guarda apuntaria a la lista que ya viene dada en vez de
        # a la respuesta. Asi apunta a CELDAS, que es lo que el alumno escribe.
        pruebas='''assert isinstance(CELDAS, dict), "CELDAS debe seguir siendo un diccionario"
assert set(CELDAS) == {"filas", "columnas", "primera_fila", "arriba_derecha",
                       "abajo_izquierda"}, "No cambies las cinco llaves"
# Los tres puntos de la plantilla son "todavia sin responder", no una respuesta
# mala: se dice asi, en vez de «Tu pusiste Ellipsis».
_sin_responder = [k for k, v in CELDAS.items() if v is ...]
assert not _sin_responder, (
    "Te falta responder: " + ", ".join(_sin_responder) +
    ". Cambia los tres puntos (...) por tu respuesta.")
for _llave in ("filas", "columnas", "arriba_derecha", "abajo_izquierda"):
    assert isinstance(CELDAS[_llave], int), (
        f"{_llave} es un numero suelto: va SIN comillas y SIN corchetes. "
        f"Tu pusiste {CELDAS[_llave]!r}")
assert isinstance(CELDAS["primera_fila"], list), (
    "primera_fila es la fila COMPLETA, o sea una lista entera y no uno de sus "
    f"numeros. Tu pusiste {CELDAS['primera_fila']!r}")
# Se corrige aqui mismo, contra huellas: el alumno sabe al instante cual fallo
# sin que se le diga el valor. Las cinco respuestas salen de LEER la matriz que
# tiene delante, y de ninguna otra parte: ninguna celda de teoria del cuadernillo
# habla de `muestras` ni trae sus numeros, asi que no hay nada que copiar.
revisar("ejercicio_1", CELDAS, {
    "filas": ("33af4f74091be9f7",
          "`len(matriz)` cuenta los elementos de la matriz, y sus elementos son filas"),
    "columnas": ("d17532201950712a",
          "las columnas no se cuentan sobre la matriz: se cuentan DENTRO de una fila"),
    "primera_fila": ("cbdca038e802aa73",
          "con un solo indice no llegas a un numero: llegas a la fila entera"),
    "arriba_derecha": ("ebcbe78ea1ac57e3",
          "arriba a la derecha: la fila 0 y la ULTIMA columna, en ese orden"),
    "abajo_izquierda": ("b21c3768f3725db6",
          "abajo a la izquierda: la ULTIMA fila y la columna 0, en ese orden"),
})''',
        pruebas_ocultas='''assert CELDAS["filas"] == 3, "muestras tiene tres filas: len(muestras)"
assert CELDAS["columnas"] == 4, "Tiene cuatro columnas: len(muestras[0])"
assert CELDAS["primera_fila"] == [21, 4, 9, 2], "muestras[0] es la fila completa"
assert CELDAS["arriba_derecha"] == 2, "Fila 0, ultima columna: muestras[0][3]"
assert CELDAS["abajo_izquierda"] == 25, "Ultima fila, columna 0: muestras[2][0]"''',
        pistas=[
            "Dibujala en papel y numera las filas por la izquierda y las columnas "
            "por arriba, las dos desde CERO. Cuenta sobre ESTA matriz: la de la "
            "teoria tiene otra forma.",
            "`len(muestras)` cuenta FILAS, porque los elementos de la matriz son "
            "filas. Para las columnas tienes que mirar dentro de una: "
            "`len(muestras[0])`.",
            "«Arriba a la derecha» es la fila 0 y la ULTIMA columna; «abajo a la "
            "izquierda» es la ULTIMA fila y la columna 0. Si los confundes, te sale "
            "el numero del otro, y los dos existen.",
        ],
    )

    # Por qué este ejercicio pide el MÁXIMO y no el promedio por columna:
    #
    # El promedio por columna ya está resuelto, con acumulador y división, en la
    # celda 4C del laboratorio. Pedirlo aquí era pedir que se copiara esa celda
    # dentro de un `def`, y la restricción «sin sum» no creaba ninguna distancia
    # precisamente porque 4C ya está escrita con acumulador. El máximo recorre
    # la misma columna con el mismo índice —que es lo que mide I3— pero con otro
    # patrón: no se acumula, se COMPARA y se guarda un candidato, que es la
    # búsqueda lineal de la semana 06 vista de otra manera. En el cuadernillo no
    # hay ninguna celda de la que copiarlo.
    #
    # Y se va la restricción por nombre. `sin_usar(f, "sum")` trata «sum» como
    # NOMBRE (motor/ava_motor.py: cualquier ast.Name con ese id), así que
    # rechazaba al alumno que hacía exactamente lo pedido —un acumulador— pero
    # lo llamaba `sum`. Aquí el enunciado empuja el patrón y las pruebas miden
    # el resultado; una respuesta correcta no se puede caer por el nombre de una
    # variable.
    #
    # I1 (mCP17) se mantiene: el máximo de una columna es una estadística de la
    # característica —un extremo, que se calcula comparando— y es el divisor con
    # el que se escala esa característica. El enunciado lo dice en una línea,
    # para que el número tenga para qué servir.
    c.ejercicio(
        numero=2, competencias=['I3', 'I1'], titulo="El máximo de una característica",
        estrellas=2, puntos=10,
        enunciado="""Escribe `maximo_de_columna(matriz, c)`: el valor **más grande** de la columna
número `c`.

El recorrido es el de la columna del laboratorio —el índice que se mueve es el
de la **fila** y la `c` se queda quieta—, pero aquí no hay nada que sumar: hay
que **comparar**. Te quedas con un candidato y lo cambias solo cuando aparece
algo mayor, como en la búsqueda de la semana pasada.

`maximo_de_columna([[6, 10], [2, 90], [4, 30]], 1)` es `90`, porque la columna 1
son el 10, el 90 y el 30.

> **Cuidado con el arranque.** Una característica puede ser **negativa** —una
> medida a la que se le ha quitado su promedio lo es la mitad de las veces—, así
> que un candidato que arranque en `0` devolvería `0` en una columna de puros
> negativos, y el `0` no está en la columna. Arranca en el **primer valor** de
> la columna. La celda de prueba te lo comprueba con negativos.

Y para qué sirve: en una característica sin negativos, dividir cada valor de la
columna entre el máximo de esa columna la deja entera entre 0 y 1, que es como
se le entregan los datos a casi cualquier modelo. Esto que calculas es el
divisor.""",
        partida='''def maximo_de_columna(matriz, c):
    ...''',
        solucion='''def maximo_de_columna(matriz, c):
    mayor = matriz[0][c]
    for f in range(len(matriz)):
        if matriz[f][c] > mayor:
            mayor = matriz[f][c]
    return mayor''',
        # Las pruebas VISIBLES cubren los CUATRO modos de fallo, y las ocultas solo
        # anaden mas casos de los mismos. Es a proposito: la version anterior
        # aprobaba a la vista dos soluciones que las ocultas suspendian, y el
        # alumno perdia 10 de los 25 puntos de la semana sin haber visto un solo
        # aviso. Si manana alguien anade a las ocultas una comprobacion nueva,
        # el caso que la provoca tiene que subir tambien aqui.
        pruebas='''assert callable(maximo_de_columna), "maximo_de_columna debe ser una funcion"
_m = [[6, 10], [2, 90], [4, 30]]
assert maximo_de_columna(_m, 1) == 90, (
    "En [[6, 10], [2, 90], [4, 30]] la columna 1 son el 10, el 90 y el 30, y el "
    "mayor es 90. ¿Tu funcion DEVUELVE el resultado con return? ¿Y estas leyendo "
    "matriz[f][c], con la fila primero?")
assert maximo_de_columna(_m, 0) == 6, (
    "La columna 0 son el 6, el 2 y el 4: el mayor es 6, y esta en la PRIMERA "
    "fila. Si te sale 12, estas sumando en vez de comparar")
assert maximo_de_columna([[-5, 1], [-2, 2], [-9, 3]], 0) == -2, (
    "Toda esa columna es negativa y su mayor es -2. Si tu candidato arranca en 0, "
    "te devuelve 0, que no esta en la columna: arrancalo en el primer valor")
assert maximo_de_columna([[1, 2], [3, 4], [5, 6]], 0) == 5, (
    "La columna 0 son el 1, el 3 y el 5: el mayor es 5 y esta en la ULTIMA fila. "
    "Si te sale 3, tu ciclo se para una fila antes de llegar al final: "
    "`range(len(matriz))` llega hasta la ultima, `range(len(matriz) - 1)` no")
assert _m == [[6, 10], [2, 90], [4, 30]], (
    "La matriz que te pasan no se toca, solo se lee: tu funcion la cambio de "
    "sitio las filas o les cambio un valor")
print("Los maximos por columna salen bien, tambien con negativos.")''',
        pruebas_ocultas='''assert maximo_de_columna([[7, 8, 9]], 2) == 9, (
    "Una matriz de una sola fila tambien es una matriz")
assert maximo_de_columna([[4]], 0) == 4, (
    "Una matriz de 1 x 1: el maximo de su unica columna es su unico valor")
_b = [[1, 2, 3], [4, 5, 6], [10, 11, 12], [7, 8, 9]]
assert maximo_de_columna(_b, 0) == 10
assert maximo_de_columna(_b, 1) == 11
assert maximo_de_columna(_b, 2) == 12
assert _b == [[1, 2, 3], [4, 5, 6], [10, 11, 12], [7, 8, 9]]
_n = [[-1.5, 0.0], [-3.5, -2.0], [-0.5, -8.0]]
assert maximo_de_columna(_n, 0) == -0.5, "Con decimales negativos tambien"
assert maximo_de_columna(_n, 1) == 0.0
assert _n == [[-1.5, 0.0], [-3.5, -2.0], [-0.5, -8.0]]''',
        pistas=[
            "Antes del ciclo, un candidato: `mayor = matriz[0][c]`, el primer valor "
            "de la columna. Dentro, una sola pregunta: ¿el que estoy mirando es "
            "mayor que el candidato?",
            "El ciclo recorre las FILAS, no las columnas: `for f in range(len(matriz))`. "
            "La `c` no se toca dentro del ciclo.",
            "Si te sale `IndexError`, seguramente escribiste `matriz[c][f]`: el primer "
            "indice es siempre la fila. Y el `return mayor` va FUERA del ciclo; si lo "
            "pones dentro, la funcion se corta en la primera vuelta.",
        ],
    )

    c.ejercicio(
        numero=3, competencias=['I3', 'I1'], titulo="Transponer", estrellas=3, puntos=10,
        enunciado="""Escribe `transponer(matriz)`: devuelve una matriz **nueva** con las filas y las
columnas cambiadas. Lo que estaba en `matriz[f][c]` tiene que acabar en el
`[c][f]` del resultado.

`transponer([[1, 2, 3], [4, 5, 6]])` es `[[1, 4], [2, 5], [3, 6]]`: entra de
2 × 3 y sale de 3 × 2.

Dos cosas más que comprueba la prueba: la matriz que te pasan **no se modifica**
(construyes una nueva y la devuelves), y el resultado es una lista **de listas**,
con una fila por cada columna de la original.

Una pieza que ya usaste en el laboratorio: una lista se construye empezando
vacía y añadiendo al final con `.append(...)`.""",
        partida='''def transponer(matriz):
    ...''',
        solucion='''def transponer(matriz):
    filas = len(matriz)
    columnas = len(matriz[0])
    nueva = []
    for c in range(columnas):
        fila_nueva = []
        for f in range(filas):
            fila_nueva.append(matriz[f][c])
        nueva.append(fila_nueva)
    return nueva''',
        pruebas='''assert callable(transponer), "transponer debe ser una funcion"
_m = [[1, 2, 3], [4, 5, 6]]
assert transponer(_m) == [[1, 4], [2, 5], [3, 6]], (
    "transponer([[1, 2, 3], [4, 5, 6]]) tiene que dar [[1, 4], [2, 5], [3, 6]]: "
    "TRES filas de dos numeros. Si te salen dos filas de tres, la estas "
    "devolviendo tal como entro")
assert _m == [[1, 2, 3], [4, 5, 6]], (
    "La matriz original no se toca: tu funcion la cambio por dentro")
assert transponer([[7]]) == [[7]], (
    "Una matriz de 1 x 1 transpuesta es ella misma, pero tiene que seguir "
    "siendo una lista de listas")
print("La transpuesta sale bien y la matriz original queda intacta.")''',
        pruebas_ocultas='''assert transponer([[1, 2], [3, 4], [5, 6]]) == [[1, 3, 5], [2, 4, 6]]
assert transponer([[1, 2, 3, 4]]) == [[1], [2], [3], [4]], (
    "Una sola fila de cuatro se vuelve cuatro filas de uno")
_c = [[1, 2], [3, 4]]
assert transponer(_c) == [[1, 3], [2, 4]], "Tambien con una matriz cuadrada"
assert _c == [[1, 2], [3, 4]], "Ni la cuadrada se modifica"
_t = transponer([[1, 2, 3], [4, 5, 6]])
assert isinstance(_t, list) and all(isinstance(_f, list) for _f in _t), (
    "El resultado es una lista de listas")
_g = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
assert transponer(_g) == [[1, 4, 7, 10], [2, 5, 8, 11], [3, 6, 9, 12]]
assert transponer(transponer(_g)) == _g, "Transponer dos veces devuelve la original"''',
        pistas=[
            "El resultado tiene tantas filas como COLUMNAS tenia la original. Empieza "
            "calculando los dos tamanos: `len(matriz)` y `len(matriz[0])`.",
            "Necesitas dos listas vacias, y en dos sitios distintos: una para el "
            "resultado, antes de todo; y otra para la fila que estas construyendo, al "
            "principio de cada vuelta del ciclo de fuera.",
            "El ciclo de fuera recorre las columnas de la original y el de dentro, sus "
            "filas. Dentro anades `matriz[f][c]` a la fila que estas construyendo; al "
            "terminar el ciclo de dentro, anades esa fila al resultado.",
        ],
    )

    # =========================================================================
    c.seccion(6, "Habla con el asistente", 1, """**Cinco preguntas** para todo el cuadernillo.""")

    c.md("""En los índices no gastes ninguna: ejecuta `ver_matriz(datos, resaltar=(0, 2))`
y cambia esa pareja —primero la fila, después la columna— para ver dónde cae
cada celda. Guárdalas para `transponer`, y pregunta con los números delante.

Mal: «no me sale transponer».
Bien: «mi `transponer` devuelve una matriz de 2 × 3 y yo esperaba 3 × 2.
¿Cómo compruebo, dentro de la función, cuántas filas y cuántas columnas estoy
creando?»
""")

    # =========================================================================
    c.seccion(7, "Cierre", 1, """Dos preguntas que nadie corrige, y lo que te llevas al taller.""")

    c.md("""- Sin ejecutar nada: ¿qué forma tiene `transponer(transponer(m))`? Si no te sale
  al instante, vuelve al dibujo del antes y el después.
- `len(m)` y `len(m[0])` no cuentan lo mismo. ¿Sabrías decir en una frase cuál
  cuenta qué?

### Lo que te llevas al taller

La clase presencial es un **laboratorio en equipo**: indicadores de una tabla con
los **roles repartidos** y una **bitácora** de quién hizo qué. Este cuadernillo
no lo califica —el trabajo de un equipo no se mide con una celda de prueba—,
pero sí te deja corriendo lo que necesitas allí.

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **Matriz** | Una lista cuyos elementos son listas: una tabla |
| **Fila / columna** | Un elemento de la matriz, que es otra lista / las celdas en la misma posición de todas las filas |
| `m[f][c]` | La celda de la fila `f` y la columna `c`. **Primero la fila** |
| **Matriz cuadrada** | La que tiene tantas filas como columnas |
| **Diagonal** | Las celdas donde los dos índices coinciden |
| **Transponer** | Cambiar las filas por las columnas |
| **Ejemplo / característica** | En un conjunto de datos, lo que guarda cada fila y lo que guarda cada columna |
""")

    return c
