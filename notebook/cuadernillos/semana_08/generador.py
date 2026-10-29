#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 8: «Funciones y colecciones».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 8 — Funciones y colecciones.

25 puntos de nbgrader en tres ejercicios (5/10/10), 5 XP y la insignia «Quien
empaqueta». ~30 minutos, teoría breve y ejercicios, siguiendo la pauta del
2026-09-22.

Por qué «Unidad 8» y no «Unidad 3», que es lo que dice la planeación
--------------------------------------------------------------------
La planeación académica titula esta semana «Unidad 3. Funciones y colecciones».
Pero el repositorio numera las unidades por semana, sin una sola excepción:
«Semana 1 · Unidad 1», «Semana 2 · Unidad 2» … «Semana 6 · Unidad 6»
(comprobado con un grep de «Unidad» en las seis portadas). Y la semana 3 ya
publicó «Semana 3 · Unidad 3 · Operadores y estructuras condicionales».

Poner aquí «Unidad 3» le deja al alumno dos cuadernillos distintos con el mismo
número de unidad y nombres distintos en la carpeta —tres contando la semana 7,
que viene con el mismo problema—, y la portada es justo donde lo vería. Entre
ser fiel al rótulo de la planeación y no mentirle al alumno sobre dónde está,
gana lo segundo: la etiqueta de la portada sigue la convención del repo y la
trazabilidad con la planeación se queda escrita aquí, donde la lee quien
mantiene el cuadernillo y no quien lo estudia.

PENDIENTE que no puedo arreglar desde aquí: la semana 7 lleva «Unidad 3» por el
mismo motivo. Mientras no cambie también, la colisión con la semana 3 sigue ahí.
Es una línea en su contenido.py y una en su generador.py.

El gancho, que es un hallazgo y no un adorno
--------------------------------------------
**El alumno escribe funciones con `def` y `return` desde la semana 1, y nunca
nadie se las explicó.** Revisados los seis cuadernillos anteriores, no hay una
sola sección dedicada a funciones: se usan como andamio («escribe
`posicion_de(datos, buscado)`») sin decir qué son. Así que esta semana no
presenta un tema nuevo, le **pone nombre** a lo que el alumno ya hace, y el
cuadernillo abre por ahí. Es un escalón mucho más bajo que empezar de cero, y
permite gastar el tiempo en lo que de verdad es nuevo.

Qué se mide y qué no
--------------------
Tres ejercicios, los tres con I3 (mCC87: identifica variables y aspectos del
problema para armar el algoritmo). **Ninguno lleva I1 (mCP17)**: la planeación
pone mCP17 en las semanas 3, 7, 9, 10, 14 y 15, no en la 8, y aquí no hay un
ejercicio indiscutiblemente matemático — contar palabras y comparar un puntaje
contra un umbral no es aplicar conocimientos matemáticos ni con la definición
más laxa. Un ejercicio sin etiqueta es válido y es honesto; inventar la
evidencia no lo es.

mCA14 (comunicación) y mCA65 (trabajo en equipo), que la planeación nombra para
esta semana, están fuera del alcance del AVA: no se miden con trazas.

La dosificación, porque el temario de la semana no cabe en 30 minutos
---------------------------------------------------------------------
La clase 1 sola pide parámetros posicionales y nombrados, retorno simple y
múltiple, locales y globales, y `*args`/`**kwargs`; la clase 2 añade recursión
y las tres colecciones. Reparto:

- **Se mide** (hay ejercicio): una cabecera con parámetro por defecto —escrita
  por el alumno, no regalada: ver el comentario de `bolsa_de_palabras`—, retorno
  múltiple, conjunto para los distintos y diccionario para asociar clave y
  valor. Es lo que el resultado esperado pide de verdad: «descompone en
  funciones cohesivas y **selecciona** tuplas, diccionarios o conjuntos según la
  naturaleza de los datos».
  Matiz honesto: lo que el alumno **escribe** es la cabecera; la *llamada* por
  nombre la escriben las pruebas, y lo que se mide es que su función la acepte.
- **Se muestra funcionando, sin ejercicio**: `*args`/`**kwargs`, el alcance de
  las variables —**local y global**, las dos mitades que pide la clase 1: una
  celda que falla a propósito para lo local, que es la única forma de que se
  entienda, y tres funciones de tres líneas para lo global— y la recursión.
  Nada de esto se califica; está porque el temario lo nombra y porque se lee en
  código ajeno. La recursión se deja en demostración a
  propósito: es nueva, es delicada, y gastar el ejercicio de 3★ en ella
  sacrificaría la bolsa de palabras, que es el centro de la semana.

Y la selección de estructuras **no se mide emparejando palabras**. Un ejercicio
de «une tupla con su definición» se resuelve con Ctrl-F sobre la tabla de
arriba y no mide nada (es una de las señales de recorte de
docs/cuadernillos_semanas_7_a_16.md §2). Se mide al revés: los enunciados dicen
qué hay que averiguar —«cuántas palabras distintas», «cuántas veces aparece
cada una»— y **callan la estructura**. Elegirla es parte del ejercicio.

El límite que hay que decir en voz alta
---------------------------------------
**El intérprete de pseudocódigo del curso no tiene funciones.** Comprobado
ejecutándolo: `Funcion`, `FinFuncion`, `SubProceso` y `Retornar` están en la
tabla `_NO_TENGO` de `motor/pseudo_uis.py` y responden con el error PS06, y
`Dimension` tampoco existe. La planeación pide «`*args` y `**kwargs` en
pseudocódigo y Python», y en el pseudocódigo del curso eso es imposible. Así
que esta semana el pseudocódigo se lee donde el temario lo pide y **todo lo
calificable es Python**, igual que resolvió la semana 6 lo de las listas. Se
dice dentro del cuadernillo para que nadie pierda media hora peleando con el
motor.
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
        codigo="semana_08",
        titulo="Funciones y colecciones",
        semana=8,
        meta_xp=5,
        insignia="Quien empaqueta",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[os.path.join(AQUI, "contenido.py")],
    )

    # «Unidad 8», no «Unidad 3» como la nombra la planeación: el repo numera la
    # unidad por la semana en las seis portadas anteriores y la semana 3 ya usa
    # ese número con otro nombre. El por qué completo, en el docstring.
    c.md("""# Funciones y colecciones
### Semana 8 · Unidad 8 · Funciones y colecciones

Llevas ocho semanas escribiendo `def` y `return` y nadie te ha dicho todavía
cómo se llama eso que escribes. Esta semana no trae una herramienta nueva: le
pone **nombre** a la que ya usas, le añade lo que te falta, y después te da tres
cajas donde guardar datos según lo que necesites hacer con ellos.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Nombrar las partes de una función: su nombre, sus parámetros y su retorno.
- Escribir la cabecera de una función con un parámetro que trae **valor por
  defecto**, y que por eso acepta el dato **por su nombre** y no solo por su
  posición.
- Devolver **dos valores** con un solo `return` y desempaquetarlos.
- Distinguir una variable **local** de una **global**: por qué lo que creas
  dentro de una función no existe fuera, y por qué asignar dentro no cambia lo
  de fuera.
- **Elegir** entre tupla, diccionario y conjunto según la pregunta que tengas
  que responder.
- Contar frecuencias con un diccionario: una **bolsa de palabras**, que es como
  un modelo de texto ve una frase.
- Leer una función **recursiva** y señalar su caso base.

**Un aviso:** el intérprete de pseudocódigo del curso no tiene funciones — lo
dice él mismo. Aquí todo se ejecuta y se califica en Python. Son **25 puntos** y
**5 XP**; la insignia se llama «Quien empaqueta».
""")

    # =========================================================================
    c.seccion(1, "Calentamiento", 1, """Una sobre algo que llevas haciendo desde la semana 1.""")
    c.code("quiz_retorno()")

    # =========================================================================
    # El gancho. Va antes de cualquier definición: primero el reconocimiento
    # («esto ya lo escribo»), después el vocabulario.
    c.seccion(2, "Esto ya lo escribías", 2, """Una función que podrías haber escrito en cualquiera de los cuadernillos
anteriores, con cada pieza etiquetada. Ejecuta y míralo:""")

    c.code("anatomia()")

    c.md("""Eso es **todo** lo que es una función: un trozo de código con nombre que recibe
datos y devuelve un resultado. Lo nuevo de esta semana son tres cosas que no te
habían hecho falta: un valor **por defecto**, devolver **dos** resultados a la
vez, y saber que lo que creas dentro **se muere** al salir.
""")

    # =========================================================================
    # 7 y no 6: 3C creció al añadir la mitad que faltaba del tema de la clase 1
    # («variables locales Y globales»), y ese minuto es su precio honesto.
    # estimar_tiempo.py es el juez, no este número.
    c.seccion(3, "Parámetros, retorno y alcance", 7, """Lo nuevo, en tres bocados. Ejecuta las celdas y mira la salida.""")

    c.md("""### 3A. Posición y nombre, y un valor por defecto

Al llamar una función los datos entran **por su posición**: el primero va al
primer parámetro. También puedes pasarlos **por su nombre**, y entonces el orden
da igual. Y un parámetro puede traer un valor **por defecto**, que se usa si
quien llama no dice nada:
""")

    # OJO al cambiar este ejemplo: es la MISMA funcion que etiqueta
    # `anatomia()`, a proposito —el alumno acaba de ver sus piezas con nombre—
    # y NO puede parecerse al ejercicio 1. Su primera version era
    # `clasifica(puntaje, umbral=0.5)` con dos `return` de texto: es decir, la
    # solucion del primer ejercicio con dos letras de diferencia en el nombre.
    # Eso es la trampa «transcribe la teoria» del §2 del documento de recorte.
    c.code('''def exactitud(aciertos, total, escala=100):
    return aciertos / total * escala

print(exactitud(41, 50))                            # por posicion; escala usa 100
print(exactitud(41, 50, 1))                         # por posicion los tres
print(exactitud(escala=1, total=50, aciertos=41))   # por nombre: el orden da igual''')

    c.md("""Mira las tres salidas junto a las tres llamadas. La primera no dice nada de
`escala`, así que se usa su valor por defecto, 100, y sale **`82.0`**: el
porcentaje. Las dos últimas sí pasan `escala=1` —una por posición y la otra por
nombre— y las dos dan **`0.82`**: la misma cuenta, expresada como proporción.
Cambiar el orden no cambió nada porque los nombres mandan sobre la posición.

> **Regla de orden:** los parámetros con valor por defecto van **al final**.
> `def f(a=1, b)` es un error de sintaxis.

### 3B. Devolver dos cosas a la vez

Un `return` puede llevar varios valores separados por comas, y quien llama los
**desempaqueta** en varias variables de una sola línea:
""")

    # `evaluar` llama a `exactitud`, la de la celda de arriba. Es a proposito:
    # «descompone una solucion en funciones cohesivas» es la mitad del resultado
    # esperado de la semana, y verlo en dos lineas vale mas que explicarlo.
    c.code('''def evaluar(aciertos, total):
    return aciertos, exactitud(aciertos, total)   # dos valores, separados por coma
                                                  # y una funcion que usa la otra

cuantos, porcentaje = evaluar(41, 50)   # se desempaquetan en dos variables
print("acerto", cuantos, "veces;", porcentaje, "%")

resultado = evaluar(41, 50)             # sin desempaquetar, llega junto
print(resultado, "<- esto es una TUPLA, y el primero es resultado[0]")''')

    c.md("""Eso que te llega junto es una **tupla**: varios datos en un paquete, que se leen
por índice como una lista pero **no se pueden cambiar**. Es la primera de las
tres colecciones de la semana, y aparece sola al devolver dos cosas.

### 3C. Local y global: lo de dentro no existe fuera

Las variables que nacen dentro de una función son **locales**: viven mientras
corre y desaparecen al terminar. Esta celda **falla a propósito** — ejecútala y
lee el error:
""")

    # La etiqueta `error-sembrado` es la convencion de la semana 01 para las
    # celdas que ensenan un error rompiendo codigo adrede: verificar.py exige
    # que SIGAN fallando, porque una celda que deja de dar el error convierte
    # en mentira la explicacion de al lado.
    c.code('''# Esta celda falla a proposito: `interna` nace dentro de la funcion.
def guardar():
    interna = 7
    return interna

guardar()
print(interna)''', etiquetas=("error-sembrado",))

    c.md("""`NameError: name 'interna' is not defined`. Y es una buena noticia: puedes
llamar `i` a una variable dentro de una función sin miedo a pisar la `i` de otra
parte. Lo único que sale es lo que la función **devuelve**:

```python
valor = guardar()    # `interna` se queda dentro; su valor sale en `valor`
print(valor)         # 7
```

Al revés sí hay paso: una función **puede leer** una variable de fuera sin que
se la pases. Lo que no puede es cambiarla por las buenas — si le **asigna** un
valor dentro, lo que hace es crear **otra** variable, local, con el mismo
nombre, y la de fuera se queda como estaba. Esa de fuera es una variable
**global**, y para escribirla de verdad hay que pedirlo:

```python
UMBRAL = 0.5

def leer():
    print(UMBRAL)      # LEE la de fuera: 0.5, y nadie se la paso

def no_la_cambia():
    UMBRAL = 0.9       # crea otra UMBRAL, local; la de fuera sigue en 0.5

def si_la_cambia():
    global UMBRAL      # «la de fuera, no una nueva»
    UMBRAL = 0.9
```

`global` existe, pero se usa poco y con motivo: una función que escribe en
variables de fuera obliga a leerla entera para saber a qué afecta, y eso es lo
contrario de poder usarla sin abrirla. Lo limpio es lo que ya haces desde la
semana 1 — **recibir por parámetro y devolver con `return`**.

### 3D. Dos cosas que conviene haber visto

De esto no hay ejercicio: están porque el temario las nombra y porque las vas a
leer en código ajeno.

- `*notas` recoge en una tupla **cuantos argumentos lleguen** por posición;
  `**datos`, los que lleguen por nombre, en un diccionario.
- Una función que **se llama a sí misma** es **recursión**, y necesita siempre
  un **caso base**: la condición con la que para. Sin él se llama para siempre
  y Python la corta con `RecursionError`.
""")

    c.code('''def promedio(*notas):              # el * recoge CUANTOS lleguen, en una tupla
    return sum(notas) / len(notas)

print(promedio(4.0, 3.5, 5.0))
print(promedio(4.0, 3.5, 5.0, 2.8, 4.9))

def ficha(**datos):                # el ** los recoge por nombre, en un diccionario
    for clave in datos:
        print(" ", clave, "=", datos[clave])

ficha(modelo="arbol", exactitud=0.91)

def cuenta_atras(n):
    if n == 0:                     # EL CASO BASE: aqui para
        print("despegue")
        return
    print(n)
    cuenta_atras(n - 1)            # aqui se llama a si misma, con un n mas pequeno

cuenta_atras(3)''')

    # =========================================================================
    c.seccion(4, "Tupla, diccionario o conjunto", 4, """Las tres cajas de esta semana. Lo que se te pide no es memorizar sus métodos:
es **elegir** la que responde tu pregunta.""")

    c.code("tabla_colecciones()")

    c.md("""Y lo que necesitas de cada una cabe en diez líneas:
""")

    c.code('''clases = ("positiva", "negativa")        # TUPLA: parentesis, no se puede cambiar
print(clases[0], "- tiene", len(clases), "clases")

palabras = ["el", "gato", "y", "el", "perro"]
distintas = set(palabras)                # CONJUNTO: tira las repetidas
print(distintas, "->", len(distintas), "palabras distintas")
print("gato" in distintas)               # `in` responde si esta: True o False

veces = {"gato": 1, "perro": 1}          # DICCIONARIO: clave -> valor
veces["gato"] = veces["gato"] + 1        # se cambia por su clave
print(veces, "el gato aparece", veces["gato"], "veces")
print(veces.get("tortuga", 0), "<- .get devuelve 0 si la clave NO esta")''')

    c.md("""Tres detalles de esas diez líneas que vas a necesitar:

- `len(set(lista))` es la forma corta de «cuántos distintos hay», sin ciclos.
- `diccionario[clave]` **revienta** si la clave no está; `.get(clave, 0)`
  devuelve `0` en su lugar. Por eso `veces[p] = veces.get(p, 0) + 1` funciona
  igual la primera vez que ves una palabra y la quinta.
- Recorrer un diccionario te da sus **claves**; con `.items()`, las dos cosas:

```python
for palabra in veces:                 # solo las claves
    print(palabra)

for palabra, n in veces.items():      # la clave Y su valor
    print(palabra, n)
```

Y ahora las tres sobre los mismos datos:
""")

    c.code('bolsa_y_vocabulario("el gato ve al perro y el perro ve al gato y al raton")')

    # =========================================================================
    # Sin números de ejercicio en la prosa: envejecen en cuanto alguien
    # renumera (trampa 2 de docs/cuadernillos_semanas_7_a_16.md §4). Se nombran
    # las funciones, que no cambian de nombre al cambiar de sitio.
    c.seccion(5, "Tres ejercicios", 22, """**25 puntos**. En `resumen_corpus` y en `bolsa_de_palabras` el enunciado dice
qué hay que averiguar y **no** dice con qué estructura: elegirla es parte del
ejercicio.""")

    c.ejercicio(
        numero=1, competencias=['I3'], titulo="Un umbral que se puede mover", estrellas=1, puntos=5,
        enunciado="""Un clasificador no dice «positiva» o «negativa»: dice un número entre 0 y 1, y
alguien decide a partir de qué número cuenta como positiva. Ese número es el
**umbral**.

Escribe `clasificar(puntaje, umbral=0.5)`:

- devuelve `"positiva"` si `puntaje` es **mayor o igual** que `umbral`,
- devuelve `"negativa"` si no,
- y si quien llama no dice el umbral, vale **0.5**.

```python
clasificar(0.80)                 # "positiva"
clasificar(0.30)                 # "negativa"
clasificar(0.30, umbral=0.20)    # "positiva": con ese umbral, 0.30 ya basta
```

En la tercera llamada el umbral se pasa **por su nombre**. Tu función tiene que
aceptar las dos formas, y para eso basta con escribir bien la cabecera.""",
        partida='''def clasificar(puntaje, umbral=0.5):
    ...''',
        solucion='''def clasificar(puntaje, umbral=0.5):
    if puntaje >= umbral:
        return "positiva"
    return "negativa"''',
        pruebas='''assert callable(clasificar), "clasificar debe ser una funcion"
assert clasificar(0.80) == "positiva", (
    "clasificar(0.80) se esperaba \\"positiva\\": con el umbral por defecto (0.5), "
    "0.80 lo pasa. ¿Tu funcion DEVUELVE el texto con return?")
assert clasificar(0.30) == "negativa", (
    "clasificar(0.30) se esperaba \\"negativa\\": 0.30 no llega a 0.5")
assert clasificar(0.50) == "positiva", (
    "clasificar(0.50) se esperaba \\"positiva\\": el umbral entra, es mayor O IGUAL. "
    "Revisa si escribiste > en vez de >=")
assert clasificar(0.30, umbral=0.20) == "positiva", (
    "clasificar(0.30, umbral=0.20) se esperaba \\"positiva\\". Si aqui sale un "
    "TypeError, tu cabecera no acepta el parametro `umbral`: tiene que llamarse "
    "asi y traer su valor por defecto, `def clasificar(puntaje, umbral=0.5)`")
print("Las cuatro llamadas dan bien, y el umbral se puede mover.")''',
        pruebas_ocultas='''assert clasificar(0.0) == "negativa"
assert clasificar(1.0) == "positiva"
assert clasificar(0.20, 0.20) == "positiva", "El umbral tambien entra por posicion"
assert clasificar(0.90, umbral=0.95) == "negativa", (
    "Con un umbral alto, un puntaje alto puede quedar negativo")
assert isinstance(clasificar(0.7), str), "Devuelve el texto, no True ni False"''',
        pistas=[
            "La cabecera te la dan hecha: no la toques. `umbral=0.5` significa que "
            "si quien llama no lo menciona, dentro vale 0.5. Y dentro es una "
            "variable normal, como `puntaje`.",
            "Dentro son dos lineas: un `if` que compara `puntaje` con `umbral` y "
            "devuelve un texto, y otra que devuelve el otro texto. Los textos van "
            "entre comillas.",
            "«Mayor o igual» es `>=`, no `>`. Si usas `>`, un puntaje que valga "
            "exactamente lo que el umbral se queda fuera, y la prueba te lo dice.",
        ],
    )

    c.ejercicio(
        numero=2, competencias=['I3'], titulo="Cuántas, y cuántas distintas", estrellas=2, puntos=10,
        enunciado="""Antes de entrenar nada con un texto hacen falta dos números: cuántas palabras
tiene y cuántas **distintas**. El segundo es el **vocabulario**, y es el que
decide lo grande que será el modelo.

Escribe `resumen_corpus(palabras)`, que recibe una lista de palabras y
**devuelve los dos números juntos**: primero el total, después cuántas
distintas hay.

```python
resumen_corpus(["el", "gato", "y", "el", "perro"])   # (5, 4)
total, distintas = resumen_corpus(["el", "gato"])    # total vale 2, distintas 2
```

Cinco palabras y cuatro distintas, porque «el» aparece dos veces y en el
vocabulario cuenta una.

> Los dos números van **en ese orden**: primero el total, después las distintas.
> Y para las distintas no hace falta ningún ciclo: una de las tres estructuras
> de arriba tira las repetidas ella sola.""",
        partida='''def resumen_corpus(palabras):
    ...''',
        solucion='''def resumen_corpus(palabras):
    total = len(palabras)
    distintas = len(set(palabras))
    return total, distintas''',
        pruebas='''assert callable(resumen_corpus), "resumen_corpus debe ser una funcion"
_r = resumen_corpus(["el", "gato", "y", "el", "perro"])
assert isinstance(_r, tuple) and len(_r) == 2, (
    "Se esperaban DOS valores. Un `return a, b` los devuelve juntos; "
    f"tu funcion devolvio {_r!r}")
assert _r == (5, 4), (
    'Con ["el", "gato", "y", "el", "perro"] se esperaba (5, 4): cinco palabras '
    'en total y cuatro distintas, porque "el" esta dos veces y en el vocabulario '
    f"cuenta una. Tu funcion devolvio {_r!r}")
assert resumen_corpus(["a", "a", "a"]) == (3, 1), (
    'Con ["a", "a", "a"] se esperaba (3, 1): tres palabras, una sola distinta')
assert resumen_corpus(["a", "b", "c"]) == (3, 3), (
    'Con ["a", "b", "c"] se esperaba (3, 3): si no hay repetidas, los dos '
    "numeros coinciden")
_t, _d = resumen_corpus(["x", "y", "x"])
assert (_t, _d) == (3, 2), "Los dos valores tienen que poder desempaquetarse"
print("Los dos numeros salen bien, y en el orden pedido.")''',
        pruebas_ocultas='''assert resumen_corpus([]) == (0, 0), "Una lista vacia: cero palabras y cero distintas"
assert resumen_corpus(["solo"]) == (1, 1)
_r = resumen_corpus(["b", "a", "b", "c", "a"])
assert _r == (5, 3), "El orden en que vienen las palabras no cambia la cuenta"
assert isinstance(_r[0], int) and isinstance(_r[1], int), "Los dos son numeros enteros"
_entrada = ["el", "el", "gato"]
resumen_corpus(_entrada)
assert _entrada == ["el", "el", "gato"], (
    "Tu funcion no debe modificar la lista que recibe: solo mirarla")''',
        pistas=[
            "El total es directo: `len(palabras)` ya lo da.",
            "Para las distintas, mete la lista en la estructura que no admite "
            "repetidos y cuenta lo que queda dentro. Son dos funciones, una dentro "
            "de la otra, en una sola linea.",
            "Para devolver los dos, una sola linea: `return total, distintas`. El "
            "orden importa — primero el total, despues las distintas — porque la "
            "prueba desempaqueta en ese orden.",
        ],
    )

    c.ejercicio(
        numero=3, competencias=['I3'], titulo="Una bolsa de palabras", estrellas=3, puntos=10,
        enunciado="""Un modelo de texto no lee frases: lee **cuántas veces** aparece cada palabra y
tira el orden. Eso es una **bolsa de palabras**.

Y en la práctica las palabras que aparecen una o dos veces suelen ser ruido y se
**recortan**. Por eso tu función lleva una frecuencia mínima.

Escribe `bolsa_de_palabras(palabras, minimo=1)`:

- recibe una lista de palabras y devuelve **cuántas veces aparece cada una**,
- dejando fuera las que aparezcan **menos de `minimo`** veces,
- y si quien llama no dice `minimo`, no se recorta nada (vale 1).

**La cabecera la escribes tú.** La plantilla te deja la función a medias, con
un solo parámetro: te falta añadir `minimo` **con su valor por defecto**, tal
como está escrita ahí arriba. Es la pieza de la semana, así que esta vez no
viene regalada — y de ella depende que las tres llamadas del ejemplo funcionen.

```python
bolsa_de_palabras(["el", "gato", "el"])              # {"el": 2, "gato": 1}
bolsa_de_palabras(["el", "gato", "el"], minimo=2)    # {"el": 2}
bolsa_de_palabras(["el", "gato", "el"], minimo=5)    # {}
```

> **Otra vez: la estructura la eliges tú.** «Cuántas veces aparece cada una» es
> una pista de las buenas: asocia cada palabra con un número.

Y un consejo de orden, que es lo que hace de esto un ejercicio de tres
estrellas: **no cuentes y recortes en el mismo ciclo**. Mientras cuentas todavía
no sabes cuántas veces va a aparecer una palabra. Cuenta primero; después arma
el resultado con las que pasan el corte.""",
        # La cabecera va A MEDIAS a proposito, y es el arreglo de una revision:
        # el valor por defecto y la llamada por nombre son la cabeza de cartel
        # de la semana, y entregarla entera (como hace el ejercicio de 1★, que
        # es la rampa y ahi esta bien) dejaba al alumno sin escribir ni un
        # `minimo=1` ni una sola llamada nombrada en todo el cuadernillo. Las
        # pruebas —visibles y ocultas— ya pasan `minimo` por nombre y por
        # posicion; con la cabecera regalada no median nada.
        # Sigue siendo Python valido (no un `def bolsa_de_palabras(` partido) a
        # proposito: asi el constructor saca el nombre de la respuesta con ast y
        # la celda de prueba conserva la guarda «ejecuta tu celda».
        partida='''# Completa la cabecera: le falta el segundo parametro, con su valor por
# defecto. El enunciado dice como se llama y cuanto tiene que valer.
def bolsa_de_palabras(palabras):
    ...''',
        solucion='''def bolsa_de_palabras(palabras, minimo=1):
    conteo = {}
    for palabra in palabras:
        conteo[palabra] = conteo.get(palabra, 0) + 1

    bolsa = {}
    for palabra, veces in conteo.items():
        if veces >= minimo:
            bolsa[palabra] = veces
    return bolsa''',
        pruebas='''import inspect

assert callable(bolsa_de_palabras), "bolsa_de_palabras debe ser una funcion"

# La cabecera se revisa primero y aparte. Sin esto, a quien se le olvide
# completarla le reventaria la primera llamada con `minimo=...` en un TypeError
# crudo, que no dice donde esta el problema. (El mismo truco que la semana 02.)
_firma = inspect.signature(bolsa_de_palabras).parameters
assert "minimo" in _firma, (
    "A tu cabecera le falta el parametro `minimo`, y tiene que llamarse "
    "exactamente asi: las pruebas se lo pasan por su nombre. Completala: "
    "`def bolsa_de_palabras(palabras, minimo=1)`")
assert _firma["minimo"].default == 1, (
    "`minimo` ya esta en tu cabecera, pero sin su valor por defecto (o con "
    "otro). Escribe `minimo=1`: es lo que hace que quien no diga nada no "
    "recorte nada")

_b = bolsa_de_palabras(["el", "gato", "el"])
assert isinstance(_b, dict), (
    "Se esperaba un diccionario: asocia cada palabra con su numero de "
    f"apariciones. Tu funcion devolvio {type(_b).__name__}")
assert _b == {"el": 2, "gato": 1}, (
    'Con ["el", "gato", "el"] se esperaba {"el": 2, "gato": 1}. '
    f"Tu funcion devolvio {_b!r}")
assert bolsa_de_palabras(["el", "gato", "el"], minimo=2) == {"el": 2}, (
    'Con minimo=2 solo sobrevive lo que aparece 2 veces o mas: se esperaba '
    '{"el": 2}, sin "gato"')
assert bolsa_de_palabras(["el", "gato", "el"], minimo=5) == {}, (
    "Con minimo=5 no sobrevive nada: se esperaba un diccionario vacio, {}")
assert bolsa_de_palabras(["a", "b", "a", "b", "c"]) == {"a": 2, "b": 2, "c": 1}, (
    "Con minimo por defecto no se recorta nada: tienen que estar las tres")
print("Las cuentas y el recorte, los dos bien.")''',
        pruebas_ocultas='''assert bolsa_de_palabras([]) == {}, "Una lista vacia da una bolsa vacia"
assert bolsa_de_palabras([], minimo=3) == {}
assert bolsa_de_palabras(["uno"]) == {"uno": 1}
# El umbral tambien tiene que entrar por posicion, no solo por nombre.
assert bolsa_de_palabras(["a", "a", "b"], 2) == {"a": 2}, (
    "El `minimo` tambien se pasa por posicion")
# minimo=1 no recorta nada, ni siquiera lo que aparece una sola vez.
assert bolsa_de_palabras(["a", "b", "c"], minimo=1) == {"a": 1, "b": 1, "c": 1}
# Una palabra que llega mucho mas tarde sigue sumando a la misma clave.
_largo = ["x"] * 4 + ["y"] + ["x"]
assert bolsa_de_palabras(_largo) == {"x": 5, "y": 1}
assert bolsa_de_palabras(_largo, minimo=2) == {"x": 5}
# Y no se toca la lista que llega.
_entrada = ["p", "q", "p"]
bolsa_de_palabras(_entrada)
assert _entrada == ["p", "q", "p"], (
    "Tu funcion no debe modificar la lista que recibe: solo mirarla")''',
        pistas=[
            "Son dos pasos y el ORDEN importa: contar TODAS primero, y recortar "
            "cuando ya tengas todas las cuentas. Si recortas mientras cuentas, una "
            "palabra que reaparece despues ya se fue.",
            "Para contar: un diccionario vacio antes del ciclo y, dentro, sumarle "
            "uno a la clave de esa palabra. Lo incomodo es la PRIMERA vez, cuando "
            "la clave no existe: en la teoria hay una de las dos formas de leer un "
            "diccionario que no revienta ahi.",
            "Para recortar, recorre el diccionario con `.items()` —te da la palabra "
            "y su numero a la vez— y construye uno NUEVO con las que cumplen. No "
            "borres claves del que estas recorriendo: Python lo prohibe y te lanza "
            "un RuntimeError.",
        ],
    )

    # =========================================================================
    c.seccion(6, "Habla con el asistente", 1, """**Cinco preguntas** para todo el cuadernillo.""")

    c.md("""Guárdalas para la bolsa de palabras: contar y recortar en el orden equivocado es
el error de la semana y desde dentro no se ve.

Mal: «mi diccionario no me funciona».
Bien: «mi `bolsa_de_palabras(["a","a","a"], minimo=2)` devuelve `{"a": 2}` y
debería devolver `{"a": 3}`. Meto la palabra en la bolsa en cuanto llega a
`minimo`, dentro del mismo `for` que cuenta. ¿Por qué se queda corto?»
""")

    # =========================================================================
    c.seccion(7, "Cierre", 1, """Dos preguntas y el glosario.""")

    c.md("""- Con los nombres de los 30.000 estudiantes de la UIS: para saber si «Ana
  Gómez» está, ¿qué estructura pedirías? Y para saber **cuántas veces** aparece
  cada apellido, ¿la misma?
- Otro podría usar tu `bolsa_de_palabras` sin leerla por dentro: basta saber qué
  recibe y qué devuelve. Eso es **encapsular**. ¿Qué tendrías que escribir al
  lado para que lo hiciera sin preguntarte nada?
- Vuelve a `cuenta_atras`, la función que se llama a sí misma. **Señala la línea
  que le impide hacerlo para siempre.** Esa línea tiene nombre: es el **caso
  base**, y toda función recursiva necesita uno.

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **Parámetro** | El nombre que la función le pone a un dato que recibe |
| **Argumento** | El dato de verdad que le pasas al llamarla |
| **Valor por defecto** | Lo que vale un parámetro si quien llama no lo dice |
| **Encapsular** | Poder usar una función sabiendo qué recibe y qué devuelve, sin leerla |
| **Retorno múltiple** | Varios valores con un solo `return`, separados por comas |
| **Variable local** | La que nace dentro de una función y muere al salir |
| **Variable global** | La que vive fuera de toda función. Dentro se puede **leer**; para escribirla hay que declararla `global` |
| **Tupla** | Varios datos en un paquete que **no se puede cambiar** |
| **Diccionario** | Asocia una **clave** con un **valor**. `{"gato": 3}` |
| **Conjunto** | Los elementos **distintos**; responde rápido si algo está |
| **Recursión** | Una función que se llama a sí misma. Necesita **caso base** |
| **Bolsa de palabras** | Cuántas veces aparece cada palabra, sin el orden |
""")

    return c
