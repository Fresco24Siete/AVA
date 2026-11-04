#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 10: «Análisis y comunicación de datos».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 10 — Análisis y comunicación de datos.

25 puntos de nbgrader en tres ejercicios (5/10/10), 5 XP y la insignia «Quien
comunica». ~30 minutos, teoría breve y ejercicios, siguiendo la pauta del
2026-09-22.

De dónde sale el contenido (planeación 41333, semana 10, literal)
-----------------------------------------------------------------
Resultado esperado: «Carga datos tabulares, obtiene estadísticas descriptivas y
comunica resultados mediante visualizaciones claras.»
Clase 1 — Matplotlib; selección de gráficos; títulos, ejes, leyendas y
comunicación de resultados; costo de memoria y cómputo.
Clase 2 — DataFrame y tratamiento tabular; lectura de datos; selección,
filtrado y estadísticas descriptivas. Taller práctico.

EL PROBLEMA DE DISEÑO de la semana, y cómo se resuelve
------------------------------------------------------
**Una gráfica no se puede autocalificar por si es bonita.** Pero lo que la
clase 1 pide de verdad —«títulos, ejes, leyendas y comunicación de
resultados»— no es belleza: es **estructura**, y la estructura se lee. Un eje
de matplotlib sabe decir su propio título (`ax.get_title()`), sus dos
etiquetas, si tiene leyenda, y qué altura tiene cada una de sus barras
(`ax.patches`). Así que el ejercicio de 3★ pide una función que **devuelva los
ejes**, y la celda de prueba les vuelve a preguntar.

Dónde está la línea de lo justo: exigir un título **exacto** sería injusto —no
hay una sola forma correcta de titular una gráfica—, exigir que **exista y no
esté vacío** no lo es. Las alturas de las barras sí se exigen exactas, porque
ahí no hay opinión: o dibujas la proporción correcta o no.

Los cuatro `get_*` están comprobados en la imagen del AVA (Python 3.11.18,
matplotlib 3.9.2, pandas 2.2.3) y, lo que importaba de verdad, **siguen
devolviendo lo que se les puso después de que la figura se cierre** — que es lo
que hace el backend inline en cuanto el alumno llama a `plt.show()` dentro de
su función. Comprobado ejecutando los cuatro caminos razonables de solución
(`ax.bar`, `Serie.plot(kind="bar")`, `plt.bar` + `plt.gca()` y un bucle a mano
sobre las clases): los cuatro dan 3 barras con las alturas correctas. Si mañana
alguien cambia la versión de matplotlib de la imagen, esto es lo primero que
hay que volver a probar.

El puente con la semana 9, que es el argumento de la semana
-----------------------------------------------------------
En la semana 9 el alumno cargó un archivo **fila por fila**, descartando las
malas a mano, y pasó los números a NumPy. pandas hace las tres cosas de golpe:
`read_csv`, una condición para filtrar y `describe()`. Es el mismo movimiento
que NumPy frente a los ciclos de la semana 7 — no es magia nueva, es lo mismo
escrito corto. El cuadernillo lo dice con esas palabras y no presume de nada
más.

Lo que **no** se hace: depender de que la semana 9 haya dejado un archivo
escrito. Este cuadernillo escribe el suyo en una celda (`open(..., "w")`, el
patrón del Ejercicio 6 de la semana 01) y lo lee con `read_csv`. Si el archivo
de la semana 9 existe, mejor; si no, aquí no se nota.

El gancho de IA, sin adelantar temario
--------------------------------------
Un DataFrame **es** la tabla con la que se entrena. Filtrar y describir es lo
que se hace **antes** de entrenar, y es donde se descubre que una clase tiene
dos ejemplos y otra seis. El laboratorio lo enseña con el `value_counts()`
antes y después del filtro, que es el desbalance en dos líneas. No se adelanta
ningún modelo: los árboles de decisión son la semana 15, y aquí no se nombran
como algo que ya se sepa.

MICROCOMPETENCIAS
-----------------
- **I1 (mCP17, «aplica conocimientos matemáticos»)** en `tabla_y_media` y en
  `grafica_de_proporciones`: una media y una proporción, las dos calculadas y
  las dos comprobadas con su valor. La planeación pone mCP17 con evidencia en
  las semanas 9 y 10, y aquí es evidencia de verdad.
- **I3 (mCC87, «identifica variables y aspectos del problema para armar el
  algoritmo»)** en `conteo_por_clase` y en `grafica_de_proporciones`: el
  enunciado da una pregunta en español —«¿cuántas fotos usables queda de cada
  clase?»— y hay que traducirla a una condición sobre la tabla y a un resumen.
  mCC87 es transversal de la semana 2 a la 12.
  NO va en `tabla_y_media`, que es la rampa: construir la tabla y pedirle su
  media no es identificar nada. Etiquetarlo ahí sería inflar la cobertura.
- Fuera de alcance, y **no se etiquetan**: mCC85 (complejidad e impacto
  económico y ambiental), que la planeación nombra en las semanas 9 y 10 —el
  laboratorio *muestra* el costo en memoria y en tiempo, pero mostrar no es
  medir—; mCA14 (comunicación), que es la mitad del título de la semana y se
  mide en el taller presencial, no con trazas; y mCC103 (I4), que no
  corresponde a esta semana.

OJO con el número de unidad. La planeación tiene solo CUATRO unidades y la 3
abarca de la semana 3 a la 10: para esta semana dice «Unidad 3. Análisis y
comunicación de datos». Pero los cuadernillos publicados usan unidad = semana
desde la 4 («Unidad 7», «Unidad 8»), así que aquí se sigue esa convención para
que el alumno no vea un salto de «Unidad 9» a «Unidad 3» y lo reporte como
error — ya pasó con la numeración de la semana 3. El NOMBRE del tema sí es el
de la planeación, literal. Está explicado con más detalle en el docstring de la
semana 7.

DOS TABLAS EN CADA CELDA DE PRUEBA VISIBLE, y no es decorado
-----------------------------------------------------------
Las tres celdas visibles llaman a la función con **dos tablas distintas**: otros
nombres de columna, otras clases y otro número de filas. La primera ronda de
revisión de esta semana se rechazó por no hacerlo, y con razón: cuando la única
tabla visible es la del enunciado, cablear el ejemplo —tres barras fijas, los
nombres «sol/lluvia/nube», un divisor 5 copiado del propio mensaje del assert—
aprueba TODO lo visible y suspende en silencio al calificar. Es el fallo de la
semana 7, que costó 10 de 25 puntos sin que el alumno viera nada.

Dicho al revés, que es la regla que hay que respetar: **todo modo de fallo que
comprueben las ocultas tiene que fallar también en las visibles**. Las ocultas de
aquí solo añaden más casos de los mismos modos. Si alguien añade a las ocultas
una comprobación nueva, el caso que la provoca sube también a la celda visible.

QUÉ NO SE DA POR SABIDO. El alumno llega con: variables y tipos, condicionales,
ciclos, listas de una y dos dimensiones, funciones (incluido el valor por
defecto y el retorno múltiple), tupla, diccionario y conjunto, y la semana 9 de
NumPy. No se le ha enseñado `try/except`, ni POO, ni nada de las semanas 11 a
16. Así que todo lo que necesita cualquiera de las tres soluciones —`pd.DataFrame`,
`read_csv`, `tabla["columna"]`, `.mean()`, `.max()`, `describe()`, la condición
que filtra, `value_counts()`, `.to_dict()`, `ax.bar` y los cuatro `set_*`— se
enseña antes, en este mismo cuadernillo.

Y lo que **no** se usa aunque dé lástima: la **comprensión de lista**. No se ha
enseñado en ninguna celda de cuerpo del curso (sale solo dentro de celdas de
prueba, que son andamiaje que el alumno no escribe), así que las listas del
laboratorio se construyen con un ciclo y `.append(...)`, que sí se enseñó en la
semana 7. Importa sobre todo en la celda de los dos `ax.bar`: es la celda de la
que el alumno copia para resolver `grafica_de_proporciones`, y no puede traer
sintaxis que nadie le explicó.

El **índice** es el otro sitio donde esta semana se puede mentir sin querer.
Decir «el índice es el número de fila» es cómodo y deja de ser verdad en la
celda siguiente: al filtrar, las filas se quedan con la etiqueta que traían y
el índice sale con huecos, así que `buenas["etiqueta"][1]` revienta con un
`KeyError` pelado. Está dicho donde los huecos se ven —en la celda del filtro— y
con la salida: el índice es una **etiqueta**, y una columna se recorre con
`for valor in columna`, no con números.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(AQUI) not in sys.path:
    sys.path.insert(0, os.path.dirname(AQUI))

from constructor import Cuadernillo  # noqa: E402

MOTOR = os.path.join(os.path.dirname(AQUI), "motor")

# Las doce filas del archivo que escribe el laboratorio. Están aquí, en una
# constante, porque el mismo texto se usa dos veces en el cuadernillo (la celda
# que lo escribe y la prosa que comenta sus números) y porque el desbalance es
# una decisión de diseño, no un dato cualquiera: 6 gatos, 4 perros y 2 aves, y
# tres fotos borrosas que el filtro se lleva. Con el filtro en 0.5 quedan 4, 3 y
# 2, así que el reparto cambia y se puede hablar de él.
# Las cuatro primeras filas están repetidas en contenido.py (_S10_MUESTRA), que
# las dibuja antes de que el archivo exista: si cambias esto, cambia aquello.
CSV = """etiqueta,nitidez,ancho
gato,0.91,320
gato,0.42,256
gato,0.88,320
gato,0.73,512
gato,0.31,128
gato,0.95,320
perro,0.66,256
perro,0.84,320
perro,0.28,160
perro,0.79,512
ave,0.93,320
ave,0.55,256
"""


def construir(motor_comprimido=True):
    c = Cuadernillo(
        codigo="semana_10",
        titulo="Análisis y comunicación de datos",
        semana=10,
        meta_xp=5,
        insignia="Quien comunica",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[os.path.join(AQUI, "contenido.py")],
    )

    # «Unidad 10», no «Unidad 3» como la nombra la planeación: las portadas
    # publicadas numeran la unidad por la semana desde la 4. El por qué
    # completo, en el docstring.
    c.md("""# Análisis y comunicación de datos
### Semana 10 · Unidad 10 · Análisis y comunicación de datos

La semana pasada cargaste un archivo **fila por fila**: abrir, partir por las
comas, descartar las malas. Esta semana lo haces en **una línea** y después le
preguntas cosas a esa tabla sin un solo ciclo. Al final, lo único que convierte
un análisis en algo útil para otro: **una gráfica que se entiende sola**.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Crear una tabla con `pd.DataFrame(...)` y leer un archivo con `pd.read_csv(...)`.
- Mirar su **forma**, pedir una columna por su **nombre** y sacarle
  **estadísticas descriptivas** —y las de todas con `describe()`.
- Traducir una pregunta a una **condición** sobre la tabla y quedarte con las
  filas que la cumplen.
- Contar las filas de cada clase y leer ahí el **desbalance** de tus datos.
- Dibujar un diagrama de barras y **rotularlo** —título, los dos ejes y, con dos
  series, leyenda— y **volver a leer** esos rótulos desde los ejes, que es lo que
  hace la celda que te califica.
- Ver lo que esa tabla cuesta en **memoria** y en **tiempo**.

**Un aviso:** esta semana no hay pseudocódigo — el intérprete del curso no conoce
tablas ni gráficas. Todo en Python, con `pandas` y `matplotlib`, que ya vienen
instalados. Son **25 puntos** y **5 XP**; la insignia se llama «Quien comunica».
""")

    # =========================================================================
    c.seccion(1, "Calentamiento", 1, """Una de la semana 7. Sin nota: da XP.""")
    c.code("quiz_columna()")

    # =========================================================================
    # El gancho: el problema antes de la sintaxis. Lo que pesa aquí no es
    # `read_csv`: es que el alumno acaba de hacer eso mismo a mano y se acuerda.
    c.seccion(2, "Treinta líneas en una", 2, """Doce fotos etiquetadas, con su nitidez y su ancho en píxeles. El archivo lo
escribe esta misma celda; la línea que importa es la última:""")

    c.code('''import pandas as pd

FILAS = """''' + CSV + '''"""

with open("fotos_semana10.csv", "w", encoding="utf-8") as archivo:
    archivo.write(FILAS)

tabla = pd.read_csv("fotos_semana10.csv")     # la linea que importa
print(tabla)''')

    c.md("""`pd.read_csv` abrió el archivo, entendió que la primera línea eran los
**nombres** de las columnas, partió las demás por las comas y dedujo que
`etiqueta` es texto y que `nitidez` y `ancho` son números. Todo lo que a mano
cuesta un ciclo, un `split` y una lista de descartes.

La columna de `0, 1, 2, …` de la izquierda es el **índice**: la **etiqueta** de
cada fila. Recién leída del archivo coincide con el número de fila, igual que en
la semana 7 — pero es una etiqueta, y eso se va a notar en cuanto filtremos.
""")

    # =========================================================================
    c.seccion(3, "Concepto en corto", 5, """Un DataFrame es la matriz de la semana 7 con los nombres puestos. Todo lo demás
sale de ahí.""")

    c.md("""### 3A. La misma tabla, con nombres

Ejecuta y míralas lado a lado:
""")

    c.code("ver_tabla_con_nombres()")

    c.md("""Un **DataFrame** es una tabla donde cada columna tiene **nombre** y **tipo**. Eso
le permite calcular sola: una lista de listas no sabe que su columna 1 son
decimales.

```python
tabla.shape           # (12, 3)  — los dos len() de la semana 7
list(tabla.columns)   # ['etiqueta', 'nitidez', 'ancho']
tabla["nitidez"]      # la COLUMNA entera, por su nombre
tabla["nitidez"][3]   # un valor: la columna primero, la ETIQUETA de fila despues
```

Fíjate en el último: en una lista de listas ibas `m[fila][columna]`; aquí la
columna va **primero**, porque es ella la que tiene nombre.

### 3B. Una tabla también se construye a mano

Con un **diccionario** —cada clave, un nombre de columna; cada valor, la lista de
esa columna— tienes una tabla:
""")

    c.code('''registro = {
    "epoca": [1, 2, 3, 4, 5],
    "error": [0.80, 0.55, 0.40, 0.33, 0.30],
}
entrenamiento = pd.DataFrame(registro)
print(entrenamiento)
print("forma:", entrenamiento.shape)
print("error medio:", entrenamiento["error"].mean())
print("error mas alto:", entrenamiento["error"].max())
print()
print(entrenamiento.describe())      # todas, de un golpe''')

    c.md("""`.mean()` y `.max()` son **estadísticas descriptivas**: la columna las calcula
sola, sin acumulador. Y `describe()` las saca **todas** para **todas** las
columnas de números — con los tres **cuartiles**, de los que el 50 % es la
**mediana**. Es lo primero que se mira al recibir datos nuevos.

Una columna también se puede **dividir por un número**, y el resultado es otra
columna con todos sus valores escalados: `entrenamiento["error"] / 0.80` deja el
error entre 0 y 1. Eso es **normalizar**.
""")

    # =========================================================================
    # Los minutos de cada c.seccion no se escriben a ojo: tienen que cuadrar
    # (±15 %) con lo que estima estimar_tiempo.py, y build.py falla si no. Si
    # recortas o añades algo, vuelve a correr `python3 estimar_tiempo.py
    # semana_10` y ajusta estos números.
    c.seccion(4, "Laboratorio", 6, """Las tres cosas que quedan: filtrar, contar y dibujar. Ejecuta cada celda y mira
la salida.""")

    c.md("""### 4A. Filtrar: de una pregunta a una condición

La pieza que más vas a usar, y tiene **dos pasos**. Una comparación sobre una
columna entera no da un `True`: da una columna **de** `True` y `False`, uno por
fila. Y la tabla indexada por esa columna se queda con los `True`:
""")

    c.code('''print((tabla["nitidez"] >= 0.5).head(5))   # paso 1: una columna de True/False

buenas = tabla[tabla["nitidez"] >= 0.5]    # paso 2: solo las filas con True
print(buenas)
print("de", len(tabla), "fotos quedan", len(buenas))''')

    c.md("""Léelo de dentro hacia fuera: `tabla["nitidez"] >= 0.5` es la pregunta y
`tabla[...]` se queda con lo que la cumple. La original **no cambia**.

**Y mira el índice de `buenas`: 0, 2, 3, 5, … con huecos.** Faltan justo las
borrosas. Ese número es la **etiqueta** de la fila, no su posición, y cada fila se
queda con la suya: una tabla filtrada **no vuelve a empezar en 0**. Así que
`buenas["etiqueta"][1]` no te da «la primera que quedó» — revienta, porque la
etiqueta 1 es una de las que se fueron. Para recorrer una columna no uses
números: `for valor in buenas["etiqueta"]`, igual que recorrías una lista en la
semana 4.

### 4B. Contar por clase, y ver el desbalance

`value_counts()` cuenta cuántas veces aparece cada valor de una columna. Sobre
las etiquetas, eso es cuántos ejemplos tienes de cada clase:
""")

    c.code('''print("todas las fotos:")
print(tabla["etiqueta"].value_counts())
print()
print("solo las nitidas:")
print(buenas["etiqueta"].value_counts())
print()
# Esa cuenta es de pandas; con .to_dict() sale como un diccionario de los de
# la semana 8, que ya sabes recorrer y comparar.
print(buenas["etiqueta"].value_counts().to_dict())''')

    c.md("""Antes del filtro: 6 gatos, 4 perros y 2 aves —ya venía torcido—. Después: 4, 3 y
2, porque el filtro no se lleva lo mismo de cada clase.

Eso es el **desbalance**, y es lo primero que hay que saber de unos datos: un
modelo que ve seis gatos y dos aves aprende, sobre todo, a decir «gato».

### 4C. Lo que cuesta: memoria y cómputo

Las tablas de verdad no tienen doce filas. Esta tiene cien mil:
""")

    c.code('''import time

# Una lista por 25000 es esa misma lista repetida 25000 veces: 100.000 filas
# sin escribirlas.
grande = pd.DataFrame({
    "etiqueta": ["gato", "perro", "ave", "pez"] * 25000,
    "nitidez": [0.1, 0.5, 0.9, 0.3] * 25000,
})
print(grande.memory_usage(deep=True))
print("en total:", round(grande.memory_usage(deep=True).sum() / 1e6, 1), "MB")

inicio = time.perf_counter()
total = 0
for valor in grande["nitidez"]:      # a mano, como en la semana 4
    total = total + valor
medio = time.perf_counter()
otro = grande["nitidez"].sum()       # dejando que pandas lo haga
fin = time.perf_counter()

print("el ciclo tardo ", round(medio - inicio, 4), "s")
print("pandas tardo   ", round(fin - medio, 5), "s")
print("misma respuesta:", abs(total - otro) < 1e-6)''')

    c.md("""La columna de texto ocupa varias veces más que la de números con las mismas
filas: cuando una tabla no cabe, casi siempre es por el texto. Y la misma suma no
tarda lo mismo escrita de dos maneras — el ciclo pasa por Python cien mil veces y
`sum()` baja una sola vez a código compilado. De ahí la costumbre de buscar la
operación que trabaja sobre la **columna entera**.

### 4D. Rotular, que es la mitad del trabajo

Una gráfica sin título y con los ejes en blanco no comunica nada. Y esos rótulos
no se quedan solo en la imagen: **se le vuelven a preguntar a los ejes**, y por
eso una gráfica sí se puede calificar. Mira el esquema:
""")

    c.code("ver_rotulos()")

    c.md("""Ahora la de verdad, con los dos conteos de antes juntos. Dos series en la misma
gráfica es el caso en el que hace falta **leyenda**: sin ella no se sabe cuál
barra es cuál.
""")

    c.code('''import matplotlib.pyplot as plt

antes = tabla["etiqueta"].value_counts()
despues = buenas["etiqueta"].value_counts()
clases = list(antes.index)             # los NOMBRES, que son su indice
sitios = range(len(clases))            # 0, 1, 2: un sitio en el eje por clase

# Cuatro listas, con el .append de la semana 7: las dos de alturas y las dos de
# posiciones, que se corren media barra a cada lado para que no se tapen.
izquierda = []
derecha = []
altas_antes = []
altas_despues = []
for i in sitios:
    clase = clases[i]
    izquierda.append(i - 0.2)
    derecha.append(i + 0.2)
    altas_antes.append(antes[clase])        # la cuenta se pide por el NOMBRE
    altas_despues.append(despues[clase])

figura, ax = plt.subplots(figsize=(6, 3.2))
ax.bar(izquierda, altas_antes, width=0.4, label="todas")
ax.bar(derecha, altas_despues, width=0.4, label="nitidez >= 0.5")
ax.set_xticks(list(sitios))
ax.set_xticklabels(clases)
ax.set_title("Fotos por clase, antes y despues de filtrar las borrosas")
ax.set_xlabel("clase")
ax.set_ylabel("cuantas fotos")
ax.legend()
plt.show()

# Y ahora lo que importa: los rotulos se vuelven a leer.
print("titulo:", ax.get_title())
print("eje X: ", ax.get_xlabel(), " | eje Y:", ax.get_ylabel())
print("tiene leyenda:", ax.get_legend() is not None)
print("barras:", len(ax.patches))
for barra in ax.patches:
    print("  una barra de altura", barra.get_height())''')

    c.md("""Las cinco últimas líneas son la clave de la semana. `ax` no es un dibujo: es un
**objeto** que guarda su título, sus dos etiquetas, su leyenda y una barra por
cada `ax.patches`, con su altura. Todo eso se vuelve a leer, y es lo que
comprueba la celda que te califica.

`plt.subplots()` devuelve la figura **y** los ejes; el que usas es `ax`. Y
**elegir el gráfico** es parte del trabajo: barras para comparar cantidades
entre clases, que es lo de aquí; una **línea** (`ax.plot`) para ver cómo baja un
error época a época; un **histograma** (`ax.hist`) para ver cómo se reparten los
valores de una columna.
""")

    # =========================================================================
    # Sin números de ejercicio en la prosa: envejecen en cuanto alguien
    # renumera. Se nombran las funciones, que no cambian de nombre al cambiar
    # de sitio (docs/cuadernillos_semanas_7_a_16.md §4, trampa 2).
    c.seccion(5, "Tres ejercicios", 22, """**25 puntos**, de menos a más: construir la tabla y pedirle un número, traducir
una pregunta a una condición, y dibujar y rotular.""")

    # Por qué este ejercicio devuelve DOS cosas y no solo la media:
    #
    # Si solo pidiera la media, `sum(datos[columna]) / len(datos[columna])` la
    # saca sin tocar pandas y pasaría todas las pruebas. No sería una respuesta
    # incorrecta —el número es el bueno—, pero el ejercicio de la semana del
    # DataFrame no mediría el DataFrame. Devolviendo también la tabla, la prueba
    # puede exigir que sea un `pd.DataFrame` de verdad, y eso no se finge.
    #
    # El retorno múltiple no es un tema nuevo: la semana 8 lo enseñó y
    # `plt.subplots()` lo usa en el laboratorio de arriba.
    #
    # I1 (mCP17) y no I3: hay una media, que es matemática, y no hay ningún
    # aspecto del problema que identificar — la columna viene dada en el
    # argumento. Es la rampa, y etiquetarla con I3 sería inflar la cobertura.
    c.ejercicio(
        numero=1, competencias=['I1'], titulo="La tabla y su media", estrellas=1, puntos=5,
        enunciado="""Un registro de entrenamiento llega como un **diccionario**: cada clave es el
nombre de una columna; cada valor, la lista de esa columna.

Escribe `tabla_y_media(datos, columna)`, que devuelve **dos cosas** en este
orden: la **tabla** construida con ese diccionario y la **media** de la columna
cuyo nombre te pasan.

```python
datos = {"epoca": [1, 2, 3, 4], "error": [0.25, 0.5, 0.75, 0.5]}

t, m = tabla_y_media(datos, "error")   # m vale 0.5
t, m = tabla_y_media(datos, "epoca")   # m vale 2.5, con la MISMA funcion
```

> Dos avisos que te ahorran intentos. Lo primero tiene que ser una tabla de
> pandas de verdad: el diccionario tal cual no pasa. Lo segundo, **un número
> suelto**: con **un** par de corchetes la columna te da un número; con **dos**,
> otra tabla.

Devolver dos cosas con un solo `return` ya lo hiciste la semana pasada.""",
        partida='''import pandas as pd


def tabla_y_media(datos, columna):
    ...''',
        solucion='''import pandas as pd


def tabla_y_media(datos, columna):
    tabla = pd.DataFrame(datos)
    return tabla, tabla[columna].mean()''',
        pruebas='''import pandas as pd

assert callable(tabla_y_media), "tabla_y_media debe ser una funcion"

_datos = {"epoca": [1, 2, 3, 4], "error": [0.25, 0.5, 0.75, 0.5]}
_r = tabla_y_media(_datos, "error")
assert isinstance(_r, tuple) and len(_r) == 2, (
    "Se esperaban DOS cosas: la tabla y la media. Un `return tabla, media` las "
    f"devuelve juntas; tu funcion devolvio {type(_r).__name__}")

_tabla, _media = _r
assert isinstance(_tabla, pd.DataFrame), (
    "Lo primero que devuelves tiene que ser una tabla de pandas, construida con "
    f"pd.DataFrame(datos). Tu devolviste un {type(_tabla).__name__}")
assert _tabla.shape == (4, 2), (
    "La tabla de ese diccionario tiene 4 filas y 2 columnas, o sea shape (4, 2). "
    f"La tuya tiene {_tabla.shape}: si te sale (2, 4), el diccionario da una "
    "columna por clave, no una fila")
assert list(_tabla.columns) == ["epoca", "error"], (
    "Las columnas se llaman como las claves del diccionario: ['epoca', 'error']. "
    f"En la tuya son {list(_tabla.columns)}")

assert isinstance(_media, float), (
    "La media es UN numero suelto. Si te sale una Series o un DataFrame, pediste "
    "la columna con dos pares de corchetes: con uno, tabla[\\"error\\"], te da la "
    f"columna y su .mean() es un numero. Tu devolviste un {type(_media).__name__}")
assert abs(_media - 0.5) < 1e-9, (
    "La media de [0.25, 0.5, 0.75, 0.5] es 0.5. Si te sale 2.0 estas sumando sin "
    f"dividir; si te sale otra cosa, mira que columna estas promediando. "
    f"Tu devolviste {_media}")

_t2, _m2 = tabla_y_media(_datos, "epoca")
assert abs(_m2 - 2.5) < 1e-9, (
    "Con la columna \\"epoca\\" la media es 2.5. Si te sigue saliendo 0.5, tu "
    "funcion no esta usando el argumento `columna`: lo tiene cableado")
assert list(_t2["epoca"]) == [1, 2, 3, 4], (
    "La tabla tiene que traer los mismos numeros del diccionario, en el mismo orden")

# OTRO diccionario: otros nombres de columna y otro numero de filas. Si tu
# funcion solo sabe de "epoca" y "error", o divide entre 4, aqui se nota.
_otra = {"nitidez": [0.91, 0.42, 0.88, 0.73, 0.31], "ancho": [320, 256, 320, 512, 128]}
_t3, _m3 = tabla_y_media(_otra, "nitidez")
assert isinstance(_t3, pd.DataFrame) and _t3.shape == (5, 2), (
    "Esta tabla tiene 5 filas y 2 columnas, o sea shape (5, 2); la tuya tiene "
    f"{getattr(_t3, 'shape', None)}. Las columnas salen de las CLAVES del "
    "diccionario que te pasan, sean las que sean: `pd.DataFrame(datos)` y nada mas")
assert list(_t3.columns) == ["nitidez", "ancho"], (
    "Las columnas de esta tabla se llaman ['nitidez', 'ancho']. En la tuya son "
    f"{list(_t3.columns)}: estas poniendo a mano los nombres del otro ejemplo en "
    "vez de dejar que los ponga el diccionario")
assert abs(_m3 - 0.65) < 1e-9, (
    "La columna \\"nitidez\\" suma 3.25 y tiene 5 filas: su media es 0.65. Si te "
    "sale 0.6 o 0.7 estas redondeando, y la media se devuelve tal cual; si te "
    "sale 0.8125 estas dividiendo entre 4, que eran las filas de la OTRA tabla: "
    "el divisor son las filas de la que te pasan. "
    f"Tu devolviste {_m3}")
_t4, _m4 = tabla_y_media(_otra, "ancho")
assert abs(_m4 - 307.2) < 1e-9, (
    f"La media de [320, 256, 320, 512, 128] es 307.2. Tu devolviste {_m4}")

# Un diccionario de UNA sola columna: tambien es una tabla, de una columna.
_t5, _m5 = tabla_y_media({"error": [0.75]}, "error")
assert _t5.shape == (1, 1), (
    "Un diccionario de una clave y un valor da una tabla de 1 fila y 1 columna, "
    f"shape (1, 1). La tuya tiene {_t5.shape}: no des por supuesto que siempre "
    "hay dos columnas")
assert abs(_m5 - 0.75) < 1e-9, (
    "La media de un solo valor es ese valor: 0.75. Si te sale 0.8, estas "
    f"redondeando. Tu devolviste {_m5}")

assert _datos == {"epoca": [1, 2, 3, 4], "error": [0.25, 0.5, 0.75, 0.5]}, (
    "El diccionario que te pasan no se toca, solo se lee")
assert _otra == {"nitidez": [0.91, 0.42, 0.88, 0.73, 0.31],
                 "ancho": [320, 256, 320, 512, 128]}, (
    "Este tampoco")
print("La tabla se construye bien y la media sale bien en los tres diccionarios.")''',
        # Las ocultas solo anaden MAS casos de los modos de fallo que ya castiga
        # la celda visible: otros nombres de columna, otro numero de filas, una
        # media sensible al redondeo y un diccionario de una sola columna. Si
        # manana se anade aqui un modo nuevo, tiene que subir tambien arriba
        # (trampa 4: en la semana 7 un caso solo-oculto costo 10 de 25 puntos en
        # silencio). Y cada assert lleva mensaje: el alumno los ve al calificar.
        pruebas_ocultas='''_d = {"nitidez": [0.5, 1.0, 0.5, 1.0], "ancho": [100, 200, 300, 400]}
_t, _m = tabla_y_media(_d, "nitidez")
assert isinstance(_t, pd.DataFrame) and _t.shape == (4, 2), (
    "Las columnas y las filas salen del diccionario que te pasan")
assert abs(_m - 0.75) < 1e-9, "La media de [0.5, 1.0, 0.5, 1.0] es 0.75, sin redondear"
_t, _m = tabla_y_media(_d, "ancho")
assert abs(_m - 250.0) < 1e-9, "Una columna de enteros tambien tiene media"
assert isinstance(_m, float), "Y su media sigue siendo un numero suelto"
# Una sola fila y una sola columna: la media de un valor es ese valor.
_t, _m = tabla_y_media({"error": [0.75]}, "error")
assert _t.shape == (1, 1), "Un diccionario de una clave da una tabla de una columna"
assert abs(_m - 0.75) < 1e-9, "Y la media de un solo valor es ese valor: 0.75"
# Valores negativos, que es lo normal en una medida centrada.
_t, _m = tabla_y_media({"z": [-1.0, -3.0, 0.0, 0.0]}, "z")
assert abs(_m - (-1.0)) < 1e-9, "Con negativos la media tambien es negativa"
# Tres columnas, para que no valga dar la forma por supuesta.
_d3 = {"a": [1, 2], "b": [3, 4], "c": [5, 6]}
_t, _m = tabla_y_media(_d3, "c")
assert _t.shape == (2, 3) and list(_t.columns) == ["a", "b", "c"], (
    "Tres claves, tres columnas, y con sus nombres")
assert abs(_m - 5.5) < 1e-9, "La media de [5, 6] es 5.5"
assert _d3 == {"a": [1, 2], "b": [3, 4], "c": [5, 6]}, (
    "El diccionario que te pasan no se toca")''',
        pistas=[
            "Son dos lineas, y la primera es la del laboratorio: construir la tabla a "
            "partir del diccionario y guardarla en una variable.",
            "Una columna se pide por su nombre: `tabla[columna]`. Ojo, `columna` es el "
            "parametro, asi que va SIN comillas — las comillas las pone quien llama. Y "
            "su media es `.mean()`.",
            "Para devolver las dos a la vez, una sola linea: "
            "`return tabla, tabla[columna].mean()`. El orden importa: primero la "
            "tabla, despues la media.",
        ],
    )

    # Por qué este ejercicio devuelve un DICCIONARIO y no la tabla filtrada:
    #
    # Comparar dos DataFrames en un assert es incómodo y los mensajes de error
    # salen ilegibles. Un diccionario {clase: cuantas} se compara exacto, se
    # imprime de un vistazo y es lo que de verdad se quiere saber. De paso
    # obliga a cerrar el camino entero: filtrar, contar y sacar el resultado de
    # pandas a una estructura de Python de las de la semana 8.
    #
    # Y el enunciado NO dice con qué se cuenta. Ese es el I3: la pregunta está
    # en español —«cuántas fotos usables queda de cada clase»— y hay que
    # traducirla a una condición sobre la tabla y a un resumen. El laboratorio
    # enseña `value_counts()`, pero un bucle sobre la columna también vale: lo
    # que se mide es el resultado, no el método. (Comprobado: `value_counts`,
    # `groupby(...).size()` y un bucle con `.get(p, 0) + 1` pasan los tres.)
    #
    # La trampa de la semana está en el enunciado, dicha en voz alta: una clase
    # que se queda sin ninguna fila NO aparece en el diccionario. Es lo que hace
    # `value_counts`, es lo razonable, y si no se dice es una moneda al aire.
    c.ejercicio(
        numero=2, competencias=['I3'], titulo="Cuántas quedan de cada clase",
        estrellas=2, puntos=10,
        enunciado="""Antes de entrenar se tiran los ejemplos malos, y aparece la pregunta que
importa: **¿cuántos ejemplos usables quedan de cada clase?**

Escribe `conteo_por_clase(tabla, minimo)`. Recibe una tabla con una columna
`etiqueta` (la clase, un texto) y una columna `nitidez` (un número), y devuelve
un **diccionario** que asocia cada clase con **cuántas de sus filas tienen una
nitidez mayor o igual que `minimo`**.

```python
tabla = pd.DataFrame({
    "etiqueta": ["habla", "ruido", "habla", "musica"],
    "nitidez":  [0.80,     0.25,    0.50,    0.95],
})

conteo_por_clase(tabla, 0.5)   # {"habla": 2, "musica": 1}
```

Tres cosas que la prueba comprueba y que decides mal si no las lees:

> - **Mayor o igual.** Una nitidez que valga exactamente `minimo` **entra**.
> - **Una clase que se queda sin ninguna fila NO aparece** en el diccionario:
>   arriba, con `minimo=0.5`, «ruido» desaparece — no sale con un `0`.
> - La tabla que te pasan **no se modifica**: filtrar devuelve una nueva.

Con qué lo cuentas es tu decisión; lo que se mide es el diccionario que sale.""",
        partida='''import pandas as pd


def conteo_por_clase(tabla, minimo):
    ...''',
        solucion='''import pandas as pd


def conteo_por_clase(tabla, minimo):
    buenas = tabla[tabla["nitidez"] >= minimo]
    return buenas["etiqueta"].value_counts().to_dict()''',
        # Las pruebas VISIBLES cubren los SEIS modos de fallo, y las ocultas solo
        # anaden mas casos de los mismos. Es deliberado: en la semana 7, unas
        # ocultas que comprobaban un caso que ninguna visible alcanzaba
        # suspendieron en silencio a quien aprobaba a la vista, y fueron 10 de
        # los 25 puntos de la semana. Si manana alguien anade a las ocultas una
        # comprobacion nueva, el caso que la provoca tiene que subir tambien aqui.
        pruebas='''import pandas as pd

assert callable(conteo_por_clase), "conteo_por_clase debe ser una funcion"

_t = pd.DataFrame({
    "etiqueta": ["habla", "ruido", "habla", "musica", "ruido", "habla"],
    "nitidez":  [0.80,     0.25,    0.50,    0.95,     0.70,    0.10],
})
_copia = _t.copy()

_r = conteo_por_clase(_t, 0.5)
assert isinstance(_r, dict), (
    "Se esperaba un diccionario {clase: cuantas}. Si lo que devuelves es una "
    "Series de pandas, le falta pasarla a diccionario; si es None, a tu funcion "
    f"le falta el return. Tu devolviste {type(_r).__name__}")
assert _r == {"habla": 2, "ruido": 1, "musica": 1}, (
    "Con minimo=0.5 pasan la habla de 0.80, la habla de 0.50 (entra: es mayor o "
    "IGUAL), la musica de 0.95 y el ruido de 0.70. O sea "
    '{"habla": 2, "ruido": 1, "musica": 1}. '
    f"Tu devolviste {_r}")

_r3 = conteo_por_clase(_t, 0.51)
assert _r3 == {"habla": 1, "musica": 1, "ruido": 1}, (
    "Con minimo=0.51 la habla de 0.50 se queda fuera y la de 0.80 entra: "
    '{"habla": 1, "musica": 1, "ruido": 1}. Si te sale "habla": 2, tu condicion '
    "esta dejando pasar el 0.50, que es MENOR que 0.51: mira contra que estas "
    "comparando. "
    f"Tu devolviste {_r3}")

_r2 = conteo_por_clase(_t, 0.9)
assert _r2 == {"musica": 1}, (
    'Con minimo=0.9 solo sobrevive la musica de 0.95, asi que el resultado es '
    '{"musica": 1}. Las clases que no dejan ninguna fila NO aparecen: no van '
    f"con un 0. Tu devolviste {_r2}")

_r4 = conteo_por_clase(_t, 0.0)
assert _r4 == {"habla": 3, "ruido": 2, "musica": 1}, (
    "Con minimo=0.0 no se descarta nada y quedan las seis filas: "
    '{"habla": 3, "ruido": 2, "musica": 1}. Si te salen menos, tu condicion '
    f"esta descartando filas que cumplen. Tu devolviste {_r4}")

_r5 = conteo_por_clase(_t, 1.1)
assert _r5 == {}, (
    "Con minimo=1.1 no sobrevive ninguna fila, asi que el diccionario sale "
    f"vacio: {{}}. Tu devolviste {_r5}")

assert _t.equals(_copia), (
    "La tabla que te pasan no se toca, solo se lee: filtrar DEVUELVE una tabla "
    "nueva y la original se queda como estaba")

# OTRA tabla: otras clases, otro numero de filas. Las clases tienen que salir de
# la tabla que recibes, no de la lista de arriba.
_t6 = pd.DataFrame({
    "etiqueta": ["sano", "plaga", "sano", "dudoso", "plaga"],
    "nitidez":  [0.60,   0.95,    0.30,   0.60,     0.45],
})
_r6 = conteo_por_clase(_t6, 0.6)
assert _r6 == {"sano": 1, "plaga": 1, "dudoso": 1}, (
    "En esta tabla las clases se llaman sano, plaga y dudoso. Con minimo=0.6 "
    "entran el sano de 0.60, la plaga de 0.95 y el dudoso de 0.60: "
    '{"sano": 1, "plaga": 1, "dudoso": 1}. Si te sale un diccionario vacio o con '
    "las clases del ejemplo de arriba, tu funcion las tiene cableadas en vez de "
    f"leerlas de la columna. Tu devolviste {_r6}")
_r7 = conteo_por_clase(_t6, 0.61)
assert _r7 == {"plaga": 1}, (
    "Con minimo=0.61 solo queda la plaga de 0.95, y las otras dos clases "
    f'desaparecen enteras: {{"plaga": 1}}. Tu devolviste {_r7}')
print("Las cuentas por clase salen bien en las dos tablas, con el borde justo y con las clases que desaparecen.")''',
        pruebas_ocultas='''_o = pd.DataFrame({
    "etiqueta": ["sano", "plaga", "sano", "plaga", "sano", "dudoso", "plaga", "sano"],
    "nitidez":  [0.40,   0.90,    0.60,   0.60,    0.95,   0.20,     0.10,    0.60],
})
_oc = _o.copy()
assert conteo_por_clase(_o, 0.6) == {"sano": 3, "plaga": 2}, (
    "El borde otra vez: las tres de 0.60 entran, y dudoso desaparece")
assert conteo_por_clase(_o, 0.61) == {"plaga": 1, "sano": 1}
assert conteo_por_clase(_o, 0.0) == {"sano": 4, "plaga": 3, "dudoso": 1}
assert conteo_por_clase(_o, 2.0) == {}
assert _o.equals(_oc), "Tampoco se modifica esta"
# Una sola fila, y una sola clase.
_u = pd.DataFrame({"etiqueta": ["gato"], "nitidez": [0.5]})
assert conteo_por_clase(_u, 0.5) == {"gato": 1}
assert conteo_por_clase(_u, 0.6) == {}
# Una tabla con MAS columnas: las que sobran no estorban.
_x = pd.DataFrame({
    "etiqueta": ["a", "b", "a"],
    "nitidez":  [0.9, 0.9, 0.1],
    "ancho":    [320, 256, 128],
})
assert conteo_por_clase(_x, 0.5) == {"a": 1, "b": 1}
# Y los valores del diccionario son numeros con los que se puede sumar.
assert sum(conteo_por_clase(_x, 0.5).values()) == 2''',
        pistas=[
            "Son dos pasos y el primero es el del laboratorio: quedarte con las "
            "filas que cumplen la condicion, en una tabla nueva.",
            "La condicion va dentro de los corchetes de la tabla: "
            "`tabla[tabla['nitidez'] >= minimo]`. Lo de dentro es una columna de "
            "True y False; lo de fuera se queda con los True.",
            "Sobre esa tabla nueva, cuenta los valores de su columna `etiqueta` "
            "—`value_counts()` lo hace— y pasa el resultado a diccionario con "
            "`.to_dict()`. Las clases que no quedaron no aparecen, que es justo lo "
            "que se pide.",
        ],
    )

    # Por qué este ejercicio es el de 3★ y por qué pide DEVOLVER los ejes:
    #
    # Es el único de los tres que junta las dos mitades del título de la semana:
    # analizar (contar y sacar una proporción, que es la matemática: I1) y
    # comunicar (rotular). Y pide `return ax` porque esa es la única forma de
    # que una gráfica se pueda calificar: con los ejes en la mano, la prueba les
    # vuelve a preguntar su título, sus etiquetas y la altura de cada barra.
    #
    # Lo que la prueba NO hace es exigir un título concreto: eso seria exigir
    # que el alumno adivine una frase. Exige que exista y que no este vacio, que
    # es lo que de verdad separa una grafica que comunica de una que no.
    #
    # «Barras verticales» está dicho en el enunciado y no es un capricho: con
    # `barh` las barras se miden con `get_width()` y no con `get_height()`, asi
    # que una solucion horizontal —razonable en otro contexto— fallaria por una
    # razon que el alumno no podria adivinar. Si se dice, deja de ser injusto.
    c.ejercicio(
        numero=3, competencias=['I3', 'I1'], titulo="Una gráfica que se entiende sola",
        estrellas=3, puntos=10,
        enunciado="""Lo último de un análisis es contárselo a alguien. Y lo que se cuenta aquí es el
**reparto de clases**: no cuántas filas hay de cada una, sino **qué parte del
total** es cada una — la cifra que sí se compara entre conjuntos de distinto
tamaño.

Escribe `grafica_de_proporciones(tabla)`. Recibe una tabla con una columna
`etiqueta` y tiene que:

1. calcular, por clase, sus filas **divididas entre el total**: un número entre
   0 y 1, y los de todas suman 1;
2. dibujar un diagrama de **barras verticales**, una por clase, con esas
   proporciones como altura;
3. ponerle **título** y etiquetar los **dos ejes**;
4. y **devolver los ejes** (`return ax`).

```python
tabla = pd.DataFrame({"etiqueta": ["sol", "lluvia", "sol", "sol", "nube"]})
ax = grafica_de_proporciones(tabla)
# tres barras: sol 0.6, lluvia 0.2, nube 0.2
```

Qué comprueba la prueba, para que no haya sorpresas:

> - que devuelves **unos ejes**, no `None` ni la figura;
> - que `ax.get_title()`, `ax.get_xlabel()` y `ax.get_ylabel()` **no están
>   vacíos** — el texto lo eliges tú, no se compara con ninguna frase;
> - que hay **una barra por clase** y que sus alturas son las **proporciones**, no
>   las cuentas. Esas sí exactas: ahí no hay opinión;
> - y que la tabla que te pasan no se modifica.

Del **orden** de las barras no se exige nada.""",
        partida='''import pandas as pd
import matplotlib.pyplot as plt


def grafica_de_proporciones(tabla):
    ...''',
        solucion='''import pandas as pd
import matplotlib.pyplot as plt


def grafica_de_proporciones(tabla):
    cuentas = tabla["etiqueta"].value_counts()
    proporciones = cuentas / len(tabla)

    figura, ax = plt.subplots()
    ax.bar(list(proporciones.index), list(proporciones.values))
    ax.set_title("Reparto de clases")
    ax.set_xlabel("clase")
    ax.set_ylabel("proporcion del total")
    return ax''',
        pruebas='''import pandas as pd
import matplotlib.pyplot as plt

assert callable(grafica_de_proporciones), "grafica_de_proporciones debe ser una funcion"

_t = pd.DataFrame({"etiqueta": ["sol", "lluvia", "sol", "sol", "nube"]})
_copia = _t.copy()
_ax = grafica_de_proporciones(_t)

assert _ax is not None, (
    "Tu funcion no devolvio nada. Lo ultimo que tiene que hacer es "
    "`return ax`: sin los ejes en la mano no hay nada que revisar")
assert isinstance(_ax, plt.Axes), (
    "Lo que se espera son los EJES, los que da `plt.subplots()` como segunda "
    "cosa (o los que devuelve `.plot(kind=\\"bar\\")`). Si devolviste la figura, "
    f"devuelve el otro. Tu devolviste un {type(_ax).__name__}")

assert _ax.get_title().strip() != "", (
    "La grafica no tiene titulo. Ponle uno con `ax.set_title(\\"...\\")`: el texto "
    "lo eliges tu, pero algo tiene que decir")
assert _ax.get_xlabel().strip() != "", (
    "El eje X esta sin etiquetar: `ax.set_xlabel(\\"...\\")`. Quien mire la "
    "grafica tiene que saber que hay debajo de cada barra")
assert _ax.get_ylabel().strip() != "", (
    "El eje Y esta sin etiquetar: `ax.set_ylabel(\\"...\\")`. Sin eso, una barra "
    "de altura 0.6 no dice si son fotos, por ciento o proporcion")

_alturas = sorted(float(_b.get_height()) for _b in _ax.patches)
assert len(_alturas) == 3, (
    "Son tres clases distintas (sol, lluvia, nube), asi que se esperaban tres "
    f"barras. `ax.patches` tiene {len(_alturas)}")
assert all(abs(_a - _e) < 1e-9 for _a, _e in zip(_alturas, [0.2, 0.2, 0.6])), (
    "Las alturas tienen que ser las PROPORCIONES, y el divisor es el total de "
    "filas de la tabla —aqui 5, pero sale de `len(tabla)`, no es un numero fijo—: "
    "sol 3 de 5 = 0.6, lluvia 1 de 5 = 0.2 y nube 1 de 5 = 0.2. "
    "Si te salen 3, 1 y 1 estas dibujando las "
    "cuentas sin dividirlas entre el total; si te salen las tres iguales, mira "
    "si dibujaste las barras en horizontal, porque se piden verticales. "
    f"Las tuyas, ordenadas, son {_alturas}")
assert abs(sum(_alturas) - 1.0) < 1e-9, (
    "Las proporciones de todas las clases suman 1. Si no te suman 1, el divisor "
    "no es el total de filas de la tabla")

assert _t.equals(_copia), (
    "La tabla que te pasan no se toca, solo se lee")
plt.close("all")

# OTRA tabla, y esta es la que de verdad decide: DOS clases, CUATRO filas y otros
# nombres. Las tres barras y el 5 del ejemplo de arriba no valen aqui.
# Si tu funcion se cae en la linea de abajo con un "shape mismatch", son los
# nombres de las barras, que estan cableados: tienen que salir de la tabla.
_t2 = pd.DataFrame({
    "etiqueta": ["apto", "apto", "no apto", "apto"],
    "nitidez":  [0.9, 0.8, 0.2, 0.7],
})
_copia2 = _t2.copy()
_ax2 = grafica_de_proporciones(_t2)

assert isinstance(_ax2, plt.Axes), (
    "Con esta tabla tambien tienen que salir unos ejes. Tu devolviste un "
    f"{type(_ax2).__name__}")
assert _ax2.get_title().strip() != "", (
    "Esta grafica se quedo sin titulo. Los rotulos se ponen siempre, no solo "
    "para una tabla")
assert _ax2.get_xlabel().strip() != "", "Y el eje X de esta tambien va etiquetado"
assert _ax2.get_ylabel().strip() != "", "Y el eje Y"

_a2 = sorted(float(_b.get_height()) for _b in _ax2.patches)
assert len(_a2) == 2, (
    "Esta tabla tiene DOS clases distintas (apto y no apto), asi que se esperaban "
    f"dos barras y `ax.patches` tiene {len(_a2)}. Si te salen tres, tu funcion "
    "dibuja siempre las mismas barras: cuantas hay sale de la tabla que recibe")
assert all(abs(_x - _y) < 1e-9 for _x, _y in zip(_a2, [0.25, 0.75])), (
    "Aqui apto son 3 de las 4 filas = 0.75 y no apto 1 de 4 = 0.25. Si te salen "
    "0.6 y 0.2, estas dividiendo entre 5, que eran las filas de la OTRA tabla: el "
    "divisor es el total de filas de la tabla que te pasan, `len(tabla)`. "
    f"Las tuyas, ordenadas, son {_a2}")
assert abs(sum(_a2) - 1.0) < 1e-9, (
    "Las proporciones siguen sumando 1 con dos clases")
assert _t2.equals(_copia2), (
    "Esta tabla tampoco se toca")
plt.close("all")
print("La grafica trae sus tres rotulos y dibuja las proporciones correctas en las dos tablas.")''',
        pruebas_ocultas='''# Otra tabla, con dos clases y un reparto distinto, y con columnas de sobra que
# no deben estorbar.
_o = pd.DataFrame({
    "etiqueta": ["apto", "apto", "no apto", "apto"],
    "nitidez":  [0.9, 0.8, 0.2, 0.7],
})
_oc = _o.copy()
_ax2 = grafica_de_proporciones(_o)
assert isinstance(_ax2, plt.Axes)
assert _ax2.get_title().strip() != ""
assert _ax2.get_xlabel().strip() != "" and _ax2.get_ylabel().strip() != ""
_a2 = sorted(float(_b.get_height()) for _b in _ax2.patches)
assert len(_a2) == 2, "Dos clases, dos barras"
assert all(abs(_x - _y) < 1e-9 for _x, _y in zip(_a2, [0.25, 0.75])), (
    "apto es 3 de 4 = 0.75 y no apto 1 de 4 = 0.25")
assert abs(sum(_a2) - 1.0) < 1e-9
assert _o.equals(_oc), "Tampoco se modifica esta"
plt.close("all")

# Una sola clase: una barra de altura 1.0.
_u = pd.DataFrame({"etiqueta": ["gato", "gato", "gato"]})
_ax3 = grafica_de_proporciones(_u)
_a3 = sorted(float(_b.get_height()) for _b in _ax3.patches)
assert len(_a3) == 1 and abs(_a3[0] - 1.0) < 1e-9, (
    "Si todas las filas son de la misma clase, su proporcion es 1.0")
plt.close("all")

# Cuatro clases con el mismo peso: el divisor es el total, no el maximo.
_q = pd.DataFrame({"etiqueta": ["a", "b", "c", "d", "a", "b", "c", "d"]})
_ax4 = grafica_de_proporciones(_q)
_a4 = sorted(float(_b.get_height()) for _b in _ax4.patches)
assert len(_a4) == 4
assert all(abs(_v - 0.25) < 1e-9 for _v in _a4), (
    "Cuatro clases con dos filas cada una: 0.25 cada una. Si te sale 1.0 en "
    "todas, estas dividiendo entre el maximo y no entre el total")
plt.close("all")''',
        pistas=[
            "Tres pasos, y el primero ya lo tienes del laboratorio: contar cuantas "
            "filas hay de cada clase. Lo nuevo es que eso todavia no son las alturas.",
            "Las alturas son esa cuenta dividida entre el total de filas de la "
            "tabla, que es `len(tabla)`.",
            "Para dibujar: `figura, ax = plt.subplots()` y luego "
            "`ax.bar(nombres, alturas)` — los nombres salen del indice de la cuenta "
            "y las alturas, de sus valores. Despues los tres rotulos "
            "(`ax.set_title`, `ax.set_xlabel`, `ax.set_ylabel`) y, lo ultimo de la "
            "funcion, `return ax`, sin indentar de mas: si ya dibuja bien y la "
            "prueba dice que devolviste None, es eso.",
        ],
    )

    # =========================================================================
    c.seccion(6, "Habla con el asistente", 1, """**Cinco preguntas** para todo el cuadernillo.""")

    c.md("""No gastes ninguna en «¿cómo se pone un título?»: eso está en el esquema de los
rótulos. Guárdalas para `grafica_de_proporciones`, y pregunta con los números
delante — un `print` de las proporciones antes de dibujar te dice si el problema
está en la cuenta o en la gráfica.

Mal: «mi gráfica no pasa la prueba».
Bien: «mi `grafica_de_proporciones` dibuja tres barras de altura 3, 1 y 1, y la
prueba espera 0.6, 0.2 y 0.2. Le estoy pasando a `ax.bar` lo que devuelve
`value_counts()`. ¿Entre qué tengo que dividir y en qué línea?»
""")

    # =========================================================================
    c.seccion(7, "Cierre", 1, """Dos preguntas que nadie corrige, y lo que te llevas al taller.""")

    c.md("""- `tabla[tabla["nitidez"] >= 0.5]` tiene dos pares de corchetes. ¿Qué hay dentro
  de cada uno y por qué no se intercambian?
- Para mostrar que el error baja a lo largo de 50 épocas: ¿barras, línea o
  histograma? ¿Y qué va en cada eje?

### Lo que te llevas al taller

En clase se hacen las dos cosas que no sabe medir una celda de prueba:
**construir y criticar** visualizaciones —criticar una gráfica es decir qué no se
entiende de ella— y un **cuaderno reproducible** con su **interpretación
escrita**, que es la evidencia que se entrega.

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **DataFrame** | Una tabla donde cada columna tiene **nombre** y **tipo** |
| `tabla["c"]` | La columna `c` entera, pedida por su nombre |
| **Estadística descriptiva** | Un número que resume una columna: media, máximo… |
| **Filtrar** | Quedarse con las filas que cumplen una condición. Devuelve una tabla **nueva** |
| `value_counts()` | Cuántas veces aparece cada valor de una columna |
| **Desbalance** | Que unas clases tengan muchos más ejemplos que otras |
| **Proporción** | Las filas de una clase entre el total: entre 0 y 1 |
| **Ejes** (`ax`) | Lo que guarda la gráfica: título, etiquetas, leyenda y barras |
""")

    return c
