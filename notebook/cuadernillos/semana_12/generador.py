#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 12: «Modelado de sistemas (UML)».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 12 — Modelado de sistemas (UML).

25 puntos de nbgrader en tres ejercicios (5/10/10), 5 XP y la insignia «Quien
modela». ~30 minutos, teoría breve y ejercicios, siguiendo la pauta del
2026-09-22.

EL PROBLEMA DE DISEÑO de la semana, y cómo se resuelve
------------------------------------------------------
**Un diagrama UML no se puede autocalificar.** Dibujar cajas y flechas no
produce nada que un `assert` pueda mirar, y una imagen subida no emite
telemetría. Así que esta semana NO pide «dibuja el diagrama» como ejercicio
calificable. El UML vive en la TEORÍA, dibujado de verdad —cajas con sus tres
compartimentos, diamante lleno y vacío, multiplicidad `1..*`—, y lo que se
califica es el **modelo en código**: las clases, sus atributos y la relación
entre ellas.

Esa restricción, bien aprovechada, es justo lo que mide mCC103: traducir la
descripción de un sistema de una organización a un modelo **es** reconocer que
admite tratamiento algorítmico.

Los diagramas son SVG escrito a mano en `contenido.py`, como las semanas 03 a
10. No se usan los `.mmd` de `diagramas/` (semana 01) porque renderizarlos pide
Node en la máquina de quien autora, y aquí no hacía falta añadir esa
dependencia: los diagramas de clases son cuatro cajas y dos flechas. Nada se
genera en tiempo de ejecución.

MICROCOMPETENCIAS, y por qué estas y no otras
---------------------------------------------
El encargo de esta semana era subir la cobertura de **I4 (mCC103, «reconoce
problemas de sistemas y organizaciones susceptibles de tratamiento
algorítmico»)**, que hasta ahora no medía NINGÚN ejercicio del curso — y
hacerlo sin inflar la etiqueta. `docs/etiquetar_cuadernillo_nuevo.md` avisa de
que no sirve reetiquetar ejercicios de escribir código, porque mCC103 va de
*reconocer* la estructura, no de aplicar sintaxis.

- **E1 `Lote`/`Imagen` → I3, y NO I4.** El diagrama ya está dibujado: no queda
  ninguna situación de una organización que reconocer, solo una estructura dada
  que traducir. Es la rampa, y etiquetarla I4 sería exactamente lo que el
  repositorio llama «ponerlo por llegar al número». Sí es I3: hay que decidir
  qué variable guarda cada clase y que el `1..*` es una lista.
- **E2 `modelar` → I4 + I3.** Solo hay prosa: una empresa, su registrador de
  corridas y la pregunta que hace el jefe. Lo que el alumno tiene que
  reconocer, sin que nadie se lo diga:
  - **Qué agrupa a qué.** El jefe pregunta por un VALOR —«cuántas corridas
    llevamos de `hojas-v2`»— y no por un campo, así que hay que localizar en
    cuál de los seis campos de la línea vive ese valor, con `gpu`, `ticket` y
    `peticion` compitiendo. Sin trampa: el ejemplo del contrato, que tiene que
    ser determinista, CONFIRMA el campo en cuanto se ha elegido
    (`fichas[0].nombre` sale `"voz-a"` y la línea trae `"experimento":
    "voz-a"`). O sea: el reconocimiento es real pero acotado, y lo que ya no
    pasa —hasta el 2026-11-03 sí— es que el enunciado nombre el campo y la
    teoría regale el atajo «lo que va detrás de “de cada”».
  - **Que una corrida es una entidad con identidad.** Una línea no es una
    corrida: el registrador vuelve a escribirla idéntica cuando se reencola, y
    el número ni cuenta ni va seguido. Esto el enunciado no lo resuelve: solo
    da los hechos del registrador. Es la parte más gruesa de la etiqueta.
  - **Qué es ruido**: `gpu`, `ticket` y `minutos`.
- **E3 `auditar` → I4 + I3 + I1.** Una regla de negocio de las que escribe una
  organización, con sus palabras, y lo que hay que reconocer es su
  **estructura**: que los dos números que decide salen de **dos poblaciones
  distintas** del mismo registro —«lo que hemos podido comprobar» es la muestra
  auditada, y «de media tarde en responder» son todas—, y que el campo
  `acierto` de una no auditada no significa nada. Ninguna de las dos cosas está
  dicha; están en «Cómo funciona la casa», contadas como funciona la empresa.
  Lo que aquí **no** se mide, y antes se decía que sí, es la elección del campo
  que agrupa: la regla retira «el modelo», así que el campo lo nombra la propia
  regla, y eso es I3. I1 por la proporción y la media, con el precedente de la
  semana 10, donde una media y una proporción se etiquetaron I1.

El nivel exige **3 ejercicios distintos intentados** (`MinimoEvidencia = 3` en
`backend/internal/service/nivelCompetencia.go`), así que dos ejercicios I4 en
esta semana no bastan por sí solos: suman con los de la semana 11, que trae
otros dos (sus ejercicios 2 y 3). Dos más dos son cuatro, y el umbral son tres.
Lo que **no** se hizo es estirar la etiqueta a E1 para «llegar a tres» en una
sola semana: una etiqueta falsa no se arregla luego, porque al cargarla
clasifica hacia atrás todo el histórico de ese id
(`docs/etiquetar_cuadernillo_nuevo.md`), y el panel diría que mCC103 se mide
cuando lo medido sería mCC87.

**Antes de `cargar-competencias`, comprobar el total.** Esto no se puede dar por
hecho desde aquí: la semana 11 vive en otro worktree, así que un `build.py`
corrido solo con esta semana deja `competencias.json` en I4 = 2 y el panel se
queda por debajo del umbral. El orden es: las dos semanas en el mismo árbol,
`build.py`, contar las etiquetas I4 del `competencias.json` resultante, y solo
entonces cargar. Si no llegan a tres, se decide explícitamente —un cuarto
ejercicio en una de las dos, o una semana más— en vez de publicar la
competencia medida a medias, que es lo que ya tumbó I7.

Y lo que NO cuenta, aunque lo parezca: el quiz del calentamiento es
exactamente una pregunta de mCC103 («¿de quién es este dato?») y **no se
etiqueta**, porque los quices no emiten telemetría. Solo cuentan los
`c.ejercicio(...)`. Esto ya tumbó la medición de I7 y no se repite aquí.

QUÉ SE DA POR SABIDO
--------------------
La semana 11 es POO: el alumno llega con `class`, `__init__`, `self`, atributos
y métodos, y no se le repite nada de eso. Lo nuevo de esta semana es el
**diagrama** (qué dice cada compartimento, qué dice un diamante, qué dice un
`1..*`) y el **reparto**: qué clases hay y de quién es cada dato.

Lo que NO se usa, aunque dé lástima: **herencia**. La semana 11 enseña `class`
y la 13 es algoritmos de búsqueda; una generalización en los ejercicios pediría
sintaxis que puede que nadie haya explicado. En la teoría tampoco aparece: un
diagrama de clases se lee entero con asociación, agregación y composición, y
añadir una cuarta relación por completismo es teoría que ningún ejercicio
necesita (docs/cuadernillos_semanas_7_a_16.md §2). Tampoco **comprensión de
lista**: no se ha enseñado en ninguna celda de cuerpo del curso, así que todas
las listas se construyen con un ciclo y `.append(...)`.

Y nada de `pseudo_uis`: el intérprete del curso no entiende clases ni
definición de funciones. Esta semana es Python puro, sin una sola biblioteca
externa — es la primera desde la 8 que no necesita ninguna.

DOS JUEGOS DE DATOS EN CADA CELDA DE PRUEBA VISIBLE
---------------------------------------------------
La regla que más revisiones ha costado: **todo modo de fallo que castiguen las
ocultas tiene que fallar también en las visibles**. Aquí importa más que nunca,
porque los dos ejercicios de modelado tienen campos de RUIDO, y el ruido es
precisamente lo que invita a programar contra el ejemplo. Por eso:

- Los campos que compiten por ser la clave de agrupación (`gpu` y `ticket` en
  E2, `endpoint` y `cliente` en E3) **ya se contradicen en el primer juego
  visible**: un experimento abarca dos tickets y dos experimentos comparten
  GPU. Agrupar por ellos falla a la vista, no al calificar.
- El orden en que los grupos aparecen por primera vez **no** es el orden
  alfabético que se pide, en los dos ejercicios.
- El segundo juego visible trae otros nombres, otro número de grupos y un campo
  de más que no debe estorbar. Y en E2 trae las corridas numeradas **4, 4 y
  9**: ni empiezan en 1 ni van seguidas. Esto es la corrección del 2026-11-03,
  y era la trampa más cara del cuadernillo — con todos los juegos visibles
  numerados 1..N, `cuantas(): return max(numeros)` pasaba la celda visible
  entera, imprimía la felicitación, y perdía los 10 puntos contra la oculta
  `_D` (una corrida, la 7). El mismo día subió a la visible de E1 el otro caso
  que solo castigaban las ocultas: un `agregar` que se niega a meter dos veces
  la misma Imagen, que es lo que invita a hacer la teoría de la sección 3.
- Las ocultas solo repiten esos mismos modos con otros valores. Si alguien
  añade a las ocultas una comprobación nueva, el caso que la provoca sube
  también a la celda visible. Y **ningún `assert` de las ocultas va sin
  mensaje**: el alumno no puede depurarlas, solo lee la excepción del informe
  de nbgrader, y un `AssertionError:` pelado no le dice nada (eran 11 el
  2026-11-03).

OJO con el número de unidad. La planeación tiene solo CUATRO unidades y para
esta semana dice «Unidad 4». Pero los cuadernillos publicados usan unidad =
semana desde la 4 («Unidad 10», «Unidad 11»), así que aquí se sigue esa
convención para que el alumno no vea un salto de «Unidad 11» a «Unidad 4» y lo
reporte como error — ya pasó con la numeración de la semana 3. Está explicado
con más detalle en el docstring de la semana 7.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(AQUI) not in sys.path:
    sys.path.insert(0, os.path.dirname(AQUI))

from constructor import Cuadernillo  # noqa: E402


def construir(motor_comprimido=True):
    c = Cuadernillo(
        codigo="semana_12",
        titulo="Modelado de sistemas (UML)",
        semana=12,
        meta_xp=5,
        insignia="Quien modela",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[os.path.join(AQUI, "contenido.py")],
    )

    # «Unidad 12», no «Unidad 4» como la nombra la planeación. El por qué
    # completo, en el docstring.
    c.md("""# Modelado de sistemas (UML)
### Semana 12 · Unidad 12 · Modelado de sistemas (UML)

La semana pasada escribiste clases que alguien te describió. Esta semana nadie
te las describe: te dan **la situación de una organización**, en prosa y con
datos que sobran, y el modelo lo decides tú. El **diagrama de clases** es la
herramienta para decidirlo, y es el idioma en el que un equipo discute un
sistema antes de escribir una línea.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- **Leer un diagrama de clases**: qué dice cada uno de los tres compartimentos
  de una caja, qué dice un diamante y qué dice un `1..*`.
- Escribir en Python la **relación** que el diagrama dibuja, y **recorrerla**
  para contestar una pregunta.
- Sacar un modelo de **un párrafo** que describe cómo funciona una
  organización, distinguiendo lo que decide de lo que es **ruido**.
- Decidir **de quién es cada dato**, que es la decisión que sostiene todo lo
  demás.

Son **25 puntos** y **5 XP**; la insignia se llama «Quien modela». Esta semana
no hay pseudocódigo ni bibliotecas: Python y nada más.
""")

    # =========================================================================
    c.seccion(1, "Calentamiento", 1, """La pregunta que sostiene la semana entera. Sin nota: da XP.""")
    c.code("quiz_responsabilidad()")

    # =========================================================================
    c.seccion(2, "El dibujo que falta", 3, """Ya sabes escribir una clase. Lo que no has visto es cómo se **dibuja** — y es
lo que se usa para decidirla antes de escribirla.""")

    c.md("""Nadie diseña un sistema escribiendo clases y viendo qué sale. Se dibuja
primero: en una hoja caben diez clases y sus relaciones, y en la pantalla caben
dos. Ese dibujo tiene un nombre y una notación estándar —**UML**, *Unified
Modeling Language*— y su pieza central es el **diagrama de clases**.

Una clase se dibuja como una caja de **tres compartimentos**. Mira cuál es cuál
y con qué línea de Python se escribe:
""")

    c.code("ver_caja_de_clase()")

    # =========================================================================
    c.seccion(3, "Las tres relaciones", 5, """Una caja sola no modela nada. Lo que modela es cómo se conectan.""")

    c.code("ver_relaciones()")

    c.md("""Las tres se escriben casi igual en Python, y por eso el dibujo importa: dice
la **intención** —quién manda sobre quién— que el código por sí solo no cuenta.
Lo que no cambia nunca es el `1..*`: **una colección dentro del objeto del lado
`1`**.

Aquí está entera, con la agregación de arriba: un conjunto de datos y sus
particiones.
""")

    c.code('''class Particion:
    def __init__(self, nombre, ejemplos):
        self.nombre = nombre
        self.ejemplos = ejemplos


class ConjuntoDeDatos:
    def __init__(self, nombre):
        self.nombre = nombre
        self.particiones = []                  # el 1..* del diagrama

    def agregar(self, particion):              # la particion ya existia: agregacion
        self.particiones.append(particion)

    def cuantas(self):
        return len(self.particiones)

    def total_ejemplos(self):                  # recorrer la relacion
        total = 0
        for particion in self.particiones:
            total = total + particion.ejemplos
        return total


hojas = ConjuntoDeDatos("hojas-2026")
hojas.agregar(Particion("entrenamiento", 1800))
hojas.agregar(Particion("validacion", 200))
hojas.agregar(Particion("prueba", 200))

print(hojas.nombre, "tiene", hojas.cuantas(), "particiones")
print("ejemplos en total:", hojas.total_ejemplos())
print("la primera se llama:", hojas.particiones[0].nombre)''')

    c.md("""`total_ejemplos` es el método que justifica el modelo: la pregunta que la
organización hace de verdad («¿cuántos ejemplos tengo?») se contesta
**recorriendo la relación**, y vive en la clase que tiene la colección.

Pero los datos no llegan como tres llamadas a `agregar`: llegan como una lista
de **registros**, uno por línea, cada uno con todo repetido. Convertirlos en
objetos son dos piezas: un diccionario para no crear el mismo objeto dos veces,
y un ciclo que reparta cada registro en su sitio.
""")

    c.code('''REGISTROS = [
    {"conjunto": "hojas-2026", "particion": "entrenamiento", "ejemplos": 1800},
    {"conjunto": "voces-2026", "particion": "entrenamiento", "ejemplos": 900},
    {"conjunto": "hojas-2026", "particion": "validacion", "ejemplos": 200},
    {"conjunto": "hojas-2026", "particion": "entrenamiento", "ejemplos": 1800},
]

conjuntos = {}
for registro in REGISTROS:
    nombre = registro["conjunto"]
    if nombre not in conjuntos:
        conjuntos[nombre] = ConjuntoDeDatos(nombre)     # se crea UNA sola vez
    conjuntos[nombre].agregar(Particion(registro["particion"],
                                        registro["ejemplos"]))

for nombre in sorted(conjuntos):          # sorted() de un dict da sus CLAVES
    print(nombre, "->", conjuntos[nombre].cuantas(), "particiones")

# La ultima linea esta repetida. Si lo guardado tiene IDENTIDAD, se guarda POR
# su identidad y la repeticion no duplica nada:
por_identidad = {}
for registro in REGISTROS:
    identidad = (registro["conjunto"], registro["particion"])   # las DOS cosas
    por_identidad[identidad] = registro["ejemplos"]
print(len(por_identidad), "particiones distintas")''')

    c.md("""Dos cosas de esa celda que vas a necesitar hoy:

- `hojas-2026` sale con **3** particiones aunque solo tenga dos distintas: una
  lista guarda lo que le echen, repeticiones incluidas.
- La identidad de una partición no es su nombre: es **el par** conjunto +
  partición, porque «entrenamiento» aparece en los dos conjuntos. Guardar por
  esa identidad es lo que hace que la línea repetida no cuente dos veces.

> `sorted(conjuntos)` sobre un diccionario devuelve **sus claves ordenadas**, no
> sus valores. Es la forma corta de recorrer un diccionario en orden alfabético.
""")

    # =========================================================================
    c.seccion(4, "De la prosa al modelo", 4, """Lo que de verdad llega no es un diagrama: es un párrafo escrito por alguien que
no programa.""")

    c.md("""Y ahí está la diferencia con todo lo que llevas hecho. Un enunciado de clase
viene limpio: todo dato que aparece sirve para algo. La descripción de una
organización **no**: trae el nombre de quien lo pidió, el número de factura, la
sede, el código del proyecto que lo paga. Esos datos existen de verdad en el
sistema; lo que no existe es la obligación de meterlos en tu modelo.

Tres preguntas, en este orden, y sale el modelo:
""")

    c.code("ver_prosa_al_modelo()")

    c.md("""Un atajo que casi siempre funciona: **la pregunta del final dice la
estructura**. «De cada GPU, cuántos minutos» — lo que va detrás de «de cada» es
la clase que agrupa, y lo que se pide es el método que la recorre.
""")

    # =========================================================================
    # Los minutos de cada c.seccion no se escriben a ojo: tienen que cuadrar
    # (±15 %) con lo que estima estimar_tiempo.py, y build.py falla si no. Si
    # recortas o añades algo, vuelve a correr `python3 estimar_tiempo.py
    # semana_12` y ajusta estos números.
    #
    # Sin números de ejercicio en la prosa: envejecen en cuanto alguien
    # renumera. Se nombran las funciones (docs/cuadernillos_semanas_7_a_16.md
    # §4, trampa 2).
    c.seccion(5, "Tres ejercicios", 23, """**25 puntos**, de menos a más: traducir un diagrama que ya está dibujado, sacar
un modelo de un párrafo, y sacar uno de un párrafo con una regla de negocio
dentro.""")

    c.code("ver_diagrama_lote()")

    # E1 es la rampa y va etiquetado I3, NO I4. El diagrama ya esta dibujado:
    # no queda ninguna situacion de una organizacion que reconocer. Sí es I3:
    # hay que decidir que variable guarda cada clase, que el 1..* es una lista
    # y que `nombres()` se contesta recorriendola. Ver el docstring.
    c.ejercicio(
        numero=1, competencias=['I3'], titulo="Del diagrama al código",
        estrellas=1, puntos=5,
        enunciado="""Arriba tienes el diagrama. Escribe esas **dos clases**, tal como las dibuja:
los atributos que dice, los métodos que dice y la relación que dice.

```python
lote = Lote("L-07")
lote.agregar(Imagen("IMG_0041.jpg", 320))
lote.agregar(Imagen("IMG_0042.jpg", 512))

lote.cuantas()    # 2
lote.nombres()    # ["IMG_0041.jpg", "IMG_0042.jpg"]
```

Tres cosas que el dibujo dice y conviene leer despacio:

> - El `1..*` del lado de `Imagen` es la **lista** `imagenes` del Lote, y
>   empieza **vacía**: `Lote("L-07")` se crea sin ninguna imagen.
> - En esa lista van las **Imagen enteras**, no sus nombres: lo dicen el `1..*`
>   del lado de `Imagen` y el método `nombres()`, que a cada una le pide el
>   suyo. `agregar` recibe **una Imagen ya creada** —el diamante está vacío: el
>   Lote agrupa imágenes que crea quien lo llama—, no su nombre y su ancho.
> - `nombres()` devuelve los nombres **en el orden en que se agregaron**, y se
>   saca recorriendo la lista — cada Imagen sabe el suyo.""",
        partida='''# Las dos clases del diagrama van abajo, con tu respuesta. Estas dos lineas
# solo dicen como tienen que llamarse.


class Imagen:
    ...


class Lote:
    ...''',
        solucion='''class Imagen:
    def __init__(self, nombre, ancho):
        self.nombre = nombre
        self.ancho = ancho


class Lote:
    def __init__(self, codigo):
        self.codigo = codigo
        self.imagenes = []

    def agregar(self, imagen):
        self.imagenes.append(imagen)

    def cuantas(self):
        return len(self.imagenes)

    def nombres(self):
        salida = []
        for imagen in self.imagenes:
            salida.append(imagen.nombre)
        return salida''',
        pruebas='''_i = Imagen("IMG_0041.jpg", 320)
assert _i.nombre == "IMG_0041.jpg", (
    "Una Imagen guarda su nombre en el atributo `nombre`, tal como lo escribe "
    f"el diagrama. En la tuya vale {getattr(_i, 'nombre', None)!r}")
assert _i.ancho == 320, (
    "Y su ancho en el atributo `ancho`. El orden de los dos argumentos es el "
    "del diagrama: primero el nombre, despues el ancho. "
    f"En la tuya vale {getattr(_i, 'ancho', None)!r}")

_l = Lote("L-07")
assert _l.codigo == "L-07", (
    "Un Lote guarda su codigo en el atributo `codigo`. En el tuyo vale "
    f"{getattr(_l, 'codigo', None)!r}")
assert _l.cuantas() == 0, (
    "Un Lote recien creado no tiene ninguna imagen: la lista `imagenes` "
    f"empieza vacia, asi que cuantas() vale 0. La tuya devolvio {_l.cuantas()}")
assert _l.nombres() == [], (
    f"Y nombres() de un lote vacio es la lista vacia. Tu devolviste {_l.nombres()}")

_l.agregar(_i)
_l.agregar(Imagen("IMG_0042.jpg", 512))
assert _l.cuantas() == 2, (
    "Despues de agregar dos imagenes, cuantas() vale 2. Si te sale 0, `agregar` "
    "no esta guardando nada en la lista; si te sale 1, la estas reemplazando en "
    f"vez de anadirla. Tu devolviste {_l.cuantas()}")
assert _l.nombres() == ["IMG_0041.jpg", "IMG_0042.jpg"], (
    "nombres() devuelve los NOMBRES de las imagenes, en el orden en que se "
    "agregaron. Si te salen las imagenes enteras, te falta pedirle a cada una "
    "su atributo `nombre` mientras recorres la lista. "
    f"Tu devolviste {_l.nombres()}")

# La relacion del diagrama: en `imagenes` van las Imagen, no sus nombres.
assert _l.imagenes[0] is _i, (
    "El diamante del diagrama apunta a `Imagen`, asi que en la lista "
    "`imagenes` van las IMAGENES enteras, no sus nombres. Lo primero de "
    "`lote.imagenes` tiene que ser la misma Imagen que le pasaste a agregar(). "
    f"Ahi tienes {_l.imagenes[0]!r}")
assert _l.imagenes[1].ancho == 512, (
    "Y por eso el Lote puede preguntarle a cada imagen lo que quiera: la "
    "segunda que agregaste mide 512 de ancho. Si esto falla con un "
    "AttributeError, en la lista no hay Imagen")

# OTRO lote, con otro codigo y otra cantidad de imagenes. Si tu clase guarda
# las imagenes fuera del objeto, aqui aparecen las del lote de arriba.
_otro = Lote("L-99")
_foto = Imagen("foto.png", 64)
_otro.agregar(_foto)
assert _otro.codigo == "L-99", (
    f"Cada Lote guarda el codigo con el que se creo. El tuyo dice {_otro.codigo!r}")
assert _otro.cuantas() == 1, (
    "Este lote tiene UNA imagen, no las del lote anterior. Si te sale 3, la "
    "lista `imagenes` esta compartida entre todos los lotes: tiene que crearse "
    f"dentro de __init__, no fuera de la clase. Tu devolviste {_otro.cuantas()}")
assert _otro.nombres() == ["foto.png"], (
    f"Y sus nombres son solo los suyos. Tu devolviste {_otro.nombres()}")

# La MISMA Imagen agregada dos veces. Este caso esta aqui, en la visible, a
# proposito: la teoria de la seccion 3 acaba de ensenar a guardar POR identidad
# para que una linea repetida no cuente dos veces, y es natural traerse esa idea
# a `agregar`. Aqui no toca, y hasta el 2026-11-03 el unico sitio que lo
# castigaba era una oculta: `if imagen not in self.imagenes` pasaba esta celda
# entera en verde y perdia los 5 puntos al calificar.
_otro.agregar(_foto)
assert _otro.cuantas() == 2, (
    "La misma Imagen agregada dos veces cuenta DOS veces: `imagenes` es una "
    "lista y `agregar` solo anade. Si te sale 1, tu `agregar` comprueba antes "
    "si la imagen «ya estaba»: el Lote no decide eso, y aqui no hay que quitar "
    "repetidos —eso llega en el ejercicio siguiente, y alli se dice—. "
    f"Tu devolviste {_otro.cuantas()}")
assert _otro.nombres() == ["foto.png", "foto.png"], (
    "Y por lo mismo el nombre sale dos veces, una por cada vez que la "
    f"agregaste. Tu devolviste {_otro.nombres()}")

assert _l.cuantas() == 2, (
    "Y el primer lote sigue teniendo sus dos: crear otro Lote no le quita nada")
print("Las dos clases, sus atributos y la relacion del diagrama estan bien.")''',
        # Las ocultas repiten los MISMOS modos con otros valores: otro codigo,
        # otra cantidad, el lote vacio y la lista compartida entre objetos. No
        # estrenan ninguna comprobacion que la celda visible no haga ya.
        pruebas_ocultas='''_a = Lote("X-1")
_b = Lote("X-2")
assert _a.cuantas() == 0 and _b.cuantas() == 0, "Los dos nacen vacios"
_a.agregar(Imagen("uno.jpg", 10))
_a.agregar(Imagen("dos.jpg", 20))
_a.agregar(Imagen("tres.jpg", 30))
assert _a.cuantas() == 3, "Tres agregar, tres imagenes"
assert _b.cuantas() == 0, (
    "Agregar al primero no le anade nada al segundo: la lista se crea dentro "
    "de __init__")
assert _a.nombres() == ["uno.jpg", "dos.jpg", "tres.jpg"], "Y en ese orden"
assert _b.nombres() == [], "El segundo sigue vacio"
assert _a.codigo == "X-1" and _b.codigo == "X-2", "Cada uno con su codigo"
_g = Imagen("grande.tif", 4096)
assert _g.nombre == "grande.tif" and _g.ancho == 4096, (
    "Una Imagen guarda los dos datos que le pasan")
_b.agregar(_g)
assert _b.nombres() == ["grande.tif"] and _b.cuantas() == 1, (
    "El segundo lote tiene ahora UNA imagen, la que le acabas de agregar")
assert _b.imagenes[0] is _g, (
    "En la lista `imagenes` van las Imagen, no sus nombres")
assert _a.imagenes[2].ancho == 30, (
    "Y cada una conserva su ancho dentro del lote")
# Una misma Imagen agregada dos veces cuenta dos veces: es una lista. El mismo
# modo que castiga la celda visible con el lote L-99, con otros valores.
_b.agregar(_g)
assert _b.cuantas() == 2 and _b.nombres() == ["grande.tif", "grande.tif"], (
    "La misma Imagen agregada dos veces cuenta DOS veces: `imagenes` es una "
    "lista y `agregar` solo anade. Si te sale 1, tu `agregar` comprueba antes "
    "si la imagen «ya estaba», y el Lote no decide eso")''',
        pistas=[
            "Son dos clases y la de Imagen es la corta: un __init__ que recibe "
            "nombre y ancho y los guarda en `self`. Nada mas; el diagrama no le "
            "pone metodos.",
            "El Lote guarda su codigo y, ademas, `self.imagenes = []` dentro de "
            "__init__ — vacia, y dentro, para que cada lote tenga la suya. "
            "`agregar` es un `.append` y `cuantas` es un `len`.",
            "Para `nombres()`, el patron del laboratorio: una lista vacia, un "
            "`for imagen in self.imagenes` y un `salida.append(imagen.nombre)` "
            "dentro. Al final, `return salida`.",
        ],
    )

    # E2: I4 + I3. Por que I4 de verdad, y no una etiqueta puesta por llegar al
    # numero:
    #
    #   - No hay diagrama. Lo unico que recibe el alumno es un parrafo sobre
    #     como funciona el registrador de una empresa y la pregunta que hace el
    #     jefe de equipo. Las clases, cual contiene a cual y que atributo es de
    #     cada una los decide el.
    #   - El enunciado NO nombra el campo que agrupa. El jefe pregunta por un
    #     VALOR —«cuantas corridas llevamos de hojas-v2»— y hay que localizar
    #     en que campo vive, con `gpu`, `ticket` y `peticion` compitiendo.
    #     Hasta el 2026-11-03 el enunciado decia «de cada experimento» y «un
    #     objeto por experimento», y la seccion 4 ensena el atajo «lo que va
    #     detras de “de cada” es la clase que agrupa»: la eleccion se resolvia
    #     con Ctrl-F sobre la teoria, que es lo que el repositorio prohibe.
    #     Honestidad: el ejemplo del contrato, que tiene que ser determinista,
    #     confirma el campo en cuanto se ha elegido. El reconocimiento es real
    #     pero acotado, y asi esta dicho en el informe.
    #   - La estructura que hay que reconocer no es solo «uno a muchos»: una
    #     corrida es una ENTIDAD CON IDENTIDAD, y su identidad es el par
    #     (grupo, numero). Quien no lo ve cuenta lineas, y la reencolada le
    #     sobra. Esto el enunciado ya no lo resuelve: antes decia «sigue siendo
    #     UNA SOLA corrida» y el ejemplo traia anotado «la repetida no suma».
    #     Ahora solo da el hecho —el registrador reescribe la linea identica— y
    #     el modo lo castiga la celda VISIBLE, con mensaje.
    #   - Y hay ruido a proposito —`gpu`, `ticket`, `minutos`—, que es lo que
    #     distingue la descripcion de una organizacion de un enunciado de
    #     clase.
    #
    # NO lleva I1: `mejor()` es un maximo, y un maximo no es aplicar
    # conocimientos matematicos. Ponerle I1 seria inflar la otra competencia
    # corta.
    #
    # La prueba comprueba COMPORTAMIENTO, no forma: no exige nombres de clase
    # ni cuantas clases hay. Lo unico que exige de la forma es que lo devuelto
    # sean OBJETOS y no diccionarios, porque es lo que se esta ensenando a
    # hacer y esta dicho en el enunciado.
    c.ejercicio(
        numero=2, competencias=['I4', 'I3'], titulo="Lo que el párrafo no dice",
        estrellas=2, puntos=10,
        enunciado="""**Zafiro Labs** entrena modelos por encargo. Su registrador escribe una línea
cada vez que termina una corrida de entrenamiento, y al final del día el jefe
de equipo recibe la lista entera:

```python
{"experimento": "hojas-v2", "corrida": 1, "exactitud": 0.78,
 "gpu": "A100", "ticket": "OPS-2214", "minutos": 51}
```

Cuatro cosas que hay que saber del registrador, y que no se ven en una línea
suelta:

- Lo mismo se entrena varias veces, con distinta semilla, y cada pasada es una
  **corrida**.
- La numeración de las corridas es interna **de cada experimento**: el número 1
  de uno no tiene nada que ver con el número 1 de otro, así que dos
  experimentos distintos pueden tener los dos su corrida 1. Y dentro de uno
  mismo los números **no tienen por qué ir seguidos** — una corrida cancelada
  deja el suyo sin usar.
- Cuando una corrida se reencola, **el registrador vuelve a escribir su línea,
  idéntica**.
- La GPU se asigna según lo que esté libre, el ticket lo abre quien paga y los
  minutos los mide la máquina.

Lo único que el jefe pregunta: **¿cuántas corridas llevamos de `hojas-v2`, y
qué exactitud alcanzó la mejor? Y lo mismo de todo lo demás que esté
entrenándose.**

Escribe `modelar(lineas)`. Devuelve una **lista** con un objeto por cada una de
esas cosas que se entrenan, **ordenada por su `.nombre`**, y cada objeto
responde:

```python
lineas = [
    {"experimento": "voz-a", "corrida": 3, "exactitud": 0.70,
     "gpu": "A100", "ticket": "OPS-8", "minutos": 11},
    {"experimento": "voz-a", "corrida": 8, "exactitud": 0.40,
     "gpu": "T4", "ticket": "OPS-7", "minutos": 9},
]

fichas = modelar(lineas)
fichas[0].nombre      # "voz-a"  — un atributo, sin parentesis
fichas[0].cuantas()   # 2
fichas[0].mejor()     # 0.70
```

> Las clases que hagan falta, cuántas y cómo se llaman, **lo decides tú**: la
> prueba no mira tu diseño, mira lo que contesta. Lo único que sí exige es que
> lo que devuelves sean **objetos** de una clase tuya — un diccionario o una
> tupla no pasan, porque aquí lo que se practica es modelar.

Y no toques la lista que te pasan: solo se lee.""",
        partida='''# Tu respuesta entera va abajo: las clases que decidas y, al final, `modelar`.
# Esta firma solo dice como tiene que llamarse la funcion.


def modelar(lineas):
    ...''',
        solucion='''class Corrida:
    def __init__(self, numero, exactitud):
        self.numero = numero
        self.exactitud = exactitud


class Experimento:
    def __init__(self, nombre):
        self.nombre = nombre
        self.corridas = {}          # por su numero: la linea repetida no duplica

    def anotar(self, numero, exactitud):
        self.corridas[numero] = Corrida(numero, exactitud)

    def cuantas(self):
        return len(self.corridas)

    def mejor(self):
        alta = None
        for corrida in self.corridas.values():
            if alta is None or corrida.exactitud > alta:
                alta = corrida.exactitud
        return alta


def modelar(lineas):
    experimentos = {}
    for linea in lineas:
        nombre = linea["experimento"]
        if nombre not in experimentos:
            experimentos[nombre] = Experimento(nombre)
        experimentos[nombre].anotar(linea["corrida"], linea["exactitud"])
    fichas = []
    for nombre in sorted(experimentos):
        fichas.append(experimentos[nombre])
    return fichas''',
        # Los modos de fallo que castiga esta celda, todos a la vista:
        #   1. agrupar por gpu o por ticket   -> salen otros nombres y otro numero
        #   2. contar lineas, no corridas     -> hojas-v2 da 4 en vez de 3
        #   3. devolver diccionarios o tuplas -> isinstance
        #   4. ordenar por primera aparicion  -> raices-v1 aparece antes que hojas-v2
        #   5. mejor = la ultima o la de numero mas alto -> la 3 de hojas-v2 es 0.86
        #   6. cablear dos grupos o los nombres del ejemplo -> el segundo juego da uno
        #   7. tropezar con un campo de mas   -> el segundo juego trae "nota"
        #   8. modificar la lista recibida
        pruebas='''assert callable(modelar), "modelar debe ser una funcion"

_A = [
    {"experimento": "raices-v1", "corrida": 1, "exactitud": 0.64,
     "gpu": "A100", "ticket": "OPS-2214", "minutos": 30},
    {"experimento": "hojas-v2", "corrida": 1, "exactitud": 0.78,
     "gpu": "A100", "ticket": "OPS-2214", "minutos": 51},
    {"experimento": "hojas-v2", "corrida": 2, "exactitud": 0.91,
     "gpu": "T4", "ticket": "OPS-2311", "minutos": 44},
    {"experimento": "hojas-v2", "corrida": 2, "exactitud": 0.91,
     "gpu": "T4", "ticket": "OPS-2311", "minutos": 44},
    {"experimento": "raices-v1", "corrida": 2, "exactitud": 0.64,
     "gpu": "A100", "ticket": "OPS-2214", "minutos": 33},
    {"experimento": "hojas-v2", "corrida": 3, "exactitud": 0.86,
     "gpu": "A100", "ticket": "OPS-2214", "minutos": 52},
]
_copia_A = [dict(_x) for _x in _A]

_f = modelar(_A)
assert isinstance(_f, list), (
    "Se esperaba una LISTA de objetos, uno por experimento. Si tu funcion "
    "devuelve un diccionario, saca sus valores a una lista; si devuelve None, "
    f"le falta el return. Tu devolviste {type(_f).__name__}")
assert len(_f) == 2, (
    "En estas seis lineas hay DOS experimentos distintos: hojas-v2 y "
    "raices-v1. Si te salen 6, estas haciendo un objeto por linea; si te salen "
    "2 pero con otros nombres, mira por que campo estas agrupando — la gpu y "
    f"el ticket no identifican un experimento. Tu lista trae {len(_f)}")

for _o in _f:
    assert not isinstance(_o, (dict, list, tuple, set, str, int, float)), (
        "Lo de dentro de la lista tienen que ser OBJETOS de una clase tuya, no "
        f"{type(_o).__name__}. Esta semana va de modelar: crea la clase, "
        "guarda sus datos en __init__ y contesta con metodos")

assert [_o.nombre for _o in _f] == ["hojas-v2", "raices-v1"], (
    "La lista va ordenada POR NOMBRE, y `nombre` es un atributo (sin "
    "parentesis). Si te sale ['raices-v1', 'hojas-v2'], estas devolviendolos "
    "en el orden en que aparecieron por primera vez; ordenalos. Si salen "
    "nombres como 'A100' o 'OPS-2214', estas agrupando por la gpu o por el "
    f"ticket. Los tuyos son {[getattr(_o, 'nombre', None) for _o in _f]}")

assert _f[0].cuantas() == 3, (
    "hojas-v2 tiene las corridas 1, 2 y 3: son TRES. Aparece en cuatro lineas "
    "porque la corrida 2 esta escrita dos veces, y esas dos lineas son la "
    f"misma corrida. Tu devolviste {_f[0].cuantas()}")
assert _f[1].cuantas() == 2, (
    "raices-v1 tiene las corridas 1 y 2: son DOS, aunque las dos alcanzaran la "
    "misma exactitud. Lo que distingue una corrida de otra es su NUMERO, no su "
    f"resultado. Tu devolviste {_f[1].cuantas()}")

assert abs(_f[0].mejor() - 0.91) < 1e-9, (
    "La mejor de hojas-v2 es la corrida 2, con 0.91. Si te sale 0.86 estas "
    "cogiendo la ultima corrida en vez de la mas exacta; si te sale 2.55, las "
    f"estas sumando. Tu devolviste {_f[0].mejor()}")
assert abs(_f[1].mejor() - 0.64) < 1e-9, (
    "Las dos corridas de raices-v1 valen 0.64, asi que la mejor vale 0.64. "
    f"Tu devolviste {_f[1].mejor()}")

assert _A == _copia_A, (
    "La lista que te pasan no se toca, solo se lee")

# OTRO juego: UN solo grupo, una linea repetida, numeros de corrida que no
# empiezan en 1 ni van seguidos, y un campo de mas que no debe estorbar.
#
# Los numeros 4 y 9 estan aqui, en la VISIBLE, a proposito. Hasta el 2026-11-03
# todos los juegos visibles tenian las corridas numeradas 1..N, asi que
# `max(numeros)` coincidia con la cantidad y `cuantas(): return max(...)` pasaba
# esta celda entera en verde — con la felicitacion impresa — y reventaba al
# calificar contra la oculta _D (una sola corrida, la numero 7). Eran los 10
# puntos del ejercicio perdidos sin haber visto nada en rojo. Aqui max daria 9,
# contar lineas daria 3, y la respuesta es 2.
_B = [
    {"experimento": "audio-base", "corrida": 4, "exactitud": 0.55,
     "gpu": "T4", "ticket": "OPS-9", "minutos": 12, "nota": "primera prueba"},
    {"experimento": "audio-base", "corrida": 4, "exactitud": 0.55,
     "gpu": "T4", "ticket": "OPS-9", "minutos": 12, "nota": "primera prueba"},
    {"experimento": "audio-base", "corrida": 9, "exactitud": 0.41,
     "gpu": "A100", "ticket": "OPS-9", "minutos": 20, "nota": "reintento"},
]
_g = modelar(_B)
assert len(_g) == 1 and _g[0].nombre == "audio-base", (
    "Aqui todo lo que se entrena es lo mismo, audio-base, asi que la lista "
    "trae UN objeto. Si te salen dos o ninguno, tu funcion tiene cableado algo "
    f"del juego de arriba. Tu devolviste {[getattr(_o, 'nombre', None) for _o in _g]}")
assert _g[0].cuantas() == 2, (
    "audio-base sale en TRES lineas, pero dos de ellas son la misma corrida, "
    "la 4: hay DOS corridas, la 4 y la 9. Si te sale 3, estas contando lineas "
    "en vez de corridas. Si te sale 9, estas devolviendo el numero mas alto: "
    "el numero IDENTIFICA la corrida, no dice cuantas hay, y no tiene por que "
    f"ir seguido. Tu devolviste {_g[0].cuantas()}")
assert abs(_g[0].mejor() - 0.55) < 1e-9, (
    "La mejor de audio-base es 0.55, la de la corrida 4. Si te sale 0.41 estas "
    "cogiendo la ULTIMA linea, o la corrida de numero mas alto, en vez de la "
    f"mas exacta. Tu devolviste {_g[0].mejor()}")
print("El modelo agrupa bien, cuenta corridas y no lineas, y sale ordenado.")''',
        # Las ocultas repiten los mismos ocho modos con otros valores: otros
        # nombres, tres grupos en vez de dos o uno, otra repeticion, otro campo
        # de mas. Ninguna comprobacion nueva.
        pruebas_ocultas='''_C = [
    {"experimento": "zeta", "corrida": 1, "exactitud": 0.10,
     "gpu": "L4", "ticket": "T-1", "minutos": 5},
    {"experimento": "alfa", "corrida": 1, "exactitud": 0.90,
     "gpu": "L4", "ticket": "T-2", "minutos": 7},
    {"experimento": "beta", "corrida": 1, "exactitud": 0.50,
     "gpu": "A100", "ticket": "T-1", "minutos": 9, "extra": "da igual"},
    {"experimento": "alfa", "corrida": 2, "exactitud": 0.40,
     "gpu": "A100", "ticket": "T-2", "minutos": 8},
    {"experimento": "alfa", "corrida": 2, "exactitud": 0.40,
     "gpu": "A100", "ticket": "T-2", "minutos": 8},
    {"experimento": "zeta", "corrida": 2, "exactitud": 0.10,
     "gpu": "L4", "ticket": "T-1", "minutos": 6},
]
_copia_C = [dict(_x) for _x in _C]
_h = modelar(_C)
assert isinstance(_h, list) and len(_h) == 3, "Tres experimentos distintos"
for _o in _h:
    assert not isinstance(_o, (dict, list, tuple, set, str, int, float)), (
        "Objetos de una clase tuya, no estructuras sueltas")
assert [_o.nombre for _o in _h] == ["alfa", "beta", "zeta"], (
    "Ordenados por nombre, no por aparicion")
assert _h[0].cuantas() == 2, "alfa tiene las corridas 1 y 2; la 2 esta repetida"
assert _h[1].cuantas() == 1, "beta tiene una"
assert _h[2].cuantas() == 2, (
    "zeta tiene dos corridas, aunque las dos valgan lo mismo")
assert abs(_h[0].mejor() - 0.90) < 1e-9, (
    "La mejor de alfa es 0.90, la primera: no es la ultima ni la de numero mas alto")
assert abs(_h[1].mejor() - 0.50) < 1e-9, "beta tiene una sola corrida: 0.50"
assert abs(_h[2].mejor() - 0.10) < 1e-9, "Las dos de zeta valen 0.10"
assert _C == _copia_C, "La lista que te pasan no se toca"

# Un solo grupo con una sola corrida, numerada 7. El mismo modo que ya castiga
# la celda visible con audio-base (corridas 4 y 9), con otro valor.
_D = [{"experimento": "solo", "corrida": 7, "exactitud": 0.33,
       "gpu": "T4", "ticket": "T-9", "minutos": 1}]
_k = modelar(_D)
assert len(_k) == 1 and _k[0].nombre == "solo", (
    "Una sola linea: la lista trae un objeto, llamado 'solo'")
assert _k[0].cuantas() == 1, (
    "Una linea, una corrida, aunque su numero sea 7: el numero identifica la "
    "corrida, no la cuenta")
assert abs(_k[0].mejor() - 0.33) < 1e-9, (
    "Y su mejor exactitud es la de su unica corrida: 0.33")

# Dos experimentos que comparten numeros de corrida: la identidad de una
# corrida es el par (experimento, numero), no el numero suelto.
_E = [
    {"experimento": "uno", "corrida": 1, "exactitud": 0.20,
     "gpu": "T4", "ticket": "T-3", "minutos": 2},
    {"experimento": "dos", "corrida": 1, "exactitud": 0.80,
     "gpu": "T4", "ticket": "T-3", "minutos": 2},
    {"experimento": "uno", "corrida": 2, "exactitud": 0.60,
     "gpu": "T4", "ticket": "T-3", "minutos": 2},
]
_m = modelar(_E)
assert [_o.nombre for _o in _m] == ["dos", "uno"], (
    "Ordenados por nombre: 'dos' va antes que 'uno', aunque 'uno' aparezca "
    "primero en la lista")
assert _m[0].cuantas() == 1 and _m[1].cuantas() == 2, (
    "La corrida 1 de 'uno' y la corrida 1 de 'dos' son corridas distintas: si "
    "guardas las corridas por su numero, el diccionario va DENTRO de cada "
    "grupo, no uno solo para todos")
assert abs(_m[0].mejor() - 0.80) < 1e-9 and abs(_m[1].mejor() - 0.60) < 1e-9, (
    "La mejor de 'dos' es 0.80 y la de 'uno' es 0.60, cada una entre las "
    "suyas")''',
        pistas=[
            "Antes de escribir nada, hazle al parrafo las tres preguntas de la "
            "figura de la seccion 4: que cosas hay y cual agrupa a las otras, "
            "que dato decide cada respuesta, y que sobra. Y una cuarta, que es "
            "la que desatasca: ¿en que campo de la linea aparece «hojas-v2»?",
            "El esqueleto es el del laboratorio: un diccionario `experimentos`, "
            "un `for` sobre las lineas, y `if nombre not in experimentos:` para "
            "crear el objeto UNA sola vez. Lo que cambia es que ahi dentro se "
            "guardaba en una lista.",
            "Cuenta cuantas lineas trae el ejemplo del jefe y cuantas corridas "
            "son. Si guardas las corridas en una lista, la reencolada entra dos "
            "veces; guardalas en un diccionario con el NUMERO de corrida como "
            "clave —uno dentro de cada grupo, porque el mismo numero puede "
            "salir en dos sitios— y la repeticion se escribe encima de si "
            "misma. Ese numero identifica la corrida: no lo uses para contar, "
            "que no tiene por que ir seguido. Al final, `for nombre in "
            "sorted(experimentos)` y un `.append` a la lista que devuelves.",
        ],
    )

    # E3: I4 + I3 + I1. Por que I4 de verdad:
    #
    #   - Otra vez solo prosa, y esta vez con una regla de negocio de las que
    #     escribe una organizacion: dos condiciones unidas por un «o», con dos
    #     umbrales de distinto filo.
    #   - Lo que hay que reconocer no es la regla (esa se da, como se daria en
    #     una reunion) sino su ESTRUCTURA: que los dos numeros de la regla se
    #     calculan sobre POBLACIONES DISTINTAS del mismo registro, y que el
    #     campo `acierto` de una peticion no auditada no significa nada.
    #     Desde el 2026-11-03 la regla esta escrita como la diria el equipo
    #     —«que acierte en menos del 80 % de lo que hemos podido comprobar, o
    #     que de media tarde mas de 300 ms en responder»— y ya no nombra las
    #     dos poblaciones ni el campo de cada una. Antes decia «su exactitud
    #     sobre las peticiones AUDITADAS» y «la latencia media de TODAS sus
    #     peticiones»: era una especificacion, y transcribirla daba los 10
    #     puntos sin reconocer nada. Los dos datos que hacen falta siguen
    #     estando, en «Como funciona la casa», contados como funciona la casa.
    #     La pista 2 tampoco reparte ya las poblaciones: manda a releer.
    #   - La garantia de que ninguna division revienta esta redactada sin
    #     nombrar de QUE es denominador cada cosa. Hasta el 2026-11-03 decia
    #     «todo modelo tiene al menos una peticion AUDITADA, asi que
    #     `exactitud()` nunca se queda sin denominador», y eso emparejaba la
    #     poblacion con su numero: regalaba justo lo que el ejercicio mide.
    #   - Lo que aqui NO se mide: elegir el campo que agrupa. La regla retira
    #     «el modelo», asi que el campo lo nombra la regla misma. Descartar
    #     `endpoint` y `cliente` es I3, y como I3 esta contado.
    #
    # I1 por la proporcion y la media: dos estadisticas sobre dos denominadores
    # distintos, que es justo donde se aplica (o no) el concepto. Precedente:
    # en la semana 10 una media y una proporcion se etiquetaron I1.
    c.ejercicio(
        numero=3, competencias=['I4', 'I3', 'I1'],
        titulo="Una regla de negocio, en código", estrellas=3, puntos=10,
        enunciado="""**Zafiro Labs** tiene varios modelos atendiendo peticiones en producción. De
cada petición atendida queda una línea:

```python
{"modelo": "maleza-v3", "endpoint": "api-sur", "peticion": "R-1",
 "acierto": True, "latencia_ms": 250, "auditada": True, "cliente": "Agrosat"}
```

Cómo funciona la casa:

- Revisar una petición a mano cuesta dinero, así que **solo se audita una
  muestra**. `auditada` dice si un humano la revisó.
- `acierto` solo quiere decir algo en las auditadas. En las demás viene en
  `False` **porque nadie lo miró**, no porque el modelo fallara.
- El endpoint depende de dónde esté el cliente, y un mismo modelo atiende por
  varios.

Y la regla que el equipo acordó para la revisión mensual, con sus palabras:

> **Se retira** el modelo que **acierte en menos del 80 % de lo que hemos
> podido comprobar**, **o** que **de media tarde más de 300 ms en responder**.

Escribe `auditar(registros)`. Devuelve una **lista** con un objeto por cada cosa
que esa revisión retira o deja, **ordenada por su `.nombre`**, y cada objeto
responde:

```python
registros = [
    {"modelo": "hojas-prod", "endpoint": "api-norte", "peticion": "R-11",
     "acierto": True, "latencia_ms": 100, "auditada": True,
     "cliente": "Ecopetrol"},
    {"modelo": "hojas-prod", "endpoint": "api-norte", "peticion": "R-12",
     "acierto": False, "latencia_ms": 100, "auditada": True,
     "cliente": "Ecopetrol"},
]

fichas = auditar(registros)
fichas[0].nombre             # "hojas-prod"  — atributo, sin parentesis
fichas[0].exactitud()        # 0.5   — entre 0 y 1, no en por ciento
fichas[0].latencia_media()   # 100.0 — en milisegundos
fichas[0].se_retira()        # True  — la regla de arriba
```

> - «Menos del 80 %» quiere decir que **80 % exacto se queda**; «más de 300
>   ms», que **300 exactos se quedan**. Las dos cosas están escogidas: la
>   revisión se pelea siempre en el borde.
> - De cada modelo del registro queda **algo comprobado a mano**, y ninguno
>   aparece con cero peticiones: no te hará falta proteger ninguna división.
> - Las clases, cuántas y cómo se llaman, **las decides tú**; lo que devuelves
>   tiene que ser una lista de **objetos**, no de diccionarios. Y la lista que
>   te pasan no se toca.""",
        partida='''# Tu respuesta entera va abajo: las clases que decidas y, al final, `auditar`.
# Esta firma solo dice como tiene que llamarse la funcion.


def auditar(registros):
    ...''',
        solucion='''class Peticion:
    def __init__(self, acierto, latencia, auditada):
        self.acierto = acierto
        self.latencia = latencia
        self.auditada = auditada


class Modelo:
    def __init__(self, nombre):
        self.nombre = nombre
        self.peticiones = []

    def agregar(self, peticion):
        self.peticiones.append(peticion)

    def exactitud(self):
        auditadas = 0
        aciertos = 0
        for peticion in self.peticiones:
            if peticion.auditada:
                auditadas = auditadas + 1
                if peticion.acierto:
                    aciertos = aciertos + 1
        return aciertos / auditadas

    def latencia_media(self):
        total = 0
        for peticion in self.peticiones:
            total = total + peticion.latencia
        return total / len(self.peticiones)

    def se_retira(self):
        return self.exactitud() < 0.8 or self.latencia_media() > 300


def auditar(registros):
    modelos = {}
    for registro in registros:
        nombre = registro["modelo"]
        if nombre not in modelos:
            modelos[nombre] = Modelo(nombre)
        modelos[nombre].agregar(Peticion(registro["acierto"],
                                         registro["latencia_ms"],
                                         registro["auditada"]))
    fichas = []
    for nombre in sorted(modelos):
        fichas.append(modelos[nombre])
    return fichas''',
        # Los modos de fallo que castiga esta celda, todos a la vista:
        #   1. agrupar por endpoint o por cliente -> otros nombres, otro numero
        #   2. exactitud sobre TODAS las peticiones -> maleza-v3 daria 4/6
        #   3. latencia solo sobre las auditadas    -> suelos-beta daria 200
        #   4. usar >= 0.8 / >= 300 en vez de < 0.8 / > 300 -> maleza-v3 y voz-pro
        #   5. exactitud en por ciento              -> 80.0 en vez de 0.8
        #   6. devolver diccionarios                -> isinstance
        #   7. ordenar por primera aparicion        -> maleza-v3 aparece primero
        #   8. cablear tres modelos o sus nombres   -> el segundo juego trae otros
        #   9. tropezar con un campo de mas         -> el segundo juego trae "region"
        #  10. modificar la lista recibida
        pruebas='''assert callable(auditar), "auditar debe ser una funcion"

_A = [
    # maleza-v3: 4 aciertos de 5 auditadas = 0.80 justo, y latencia media de
    # sus SEIS peticiones = 300.0 justo. Los dos bordes: no se retira.
    {"modelo": "maleza-v3", "endpoint": "api-sur", "peticion": "R-1",
     "acierto": True, "latencia_ms": 250, "auditada": True, "cliente": "Agrosat"},
    {"modelo": "maleza-v3", "endpoint": "api-sur", "peticion": "R-2",
     "acierto": True, "latencia_ms": 250, "auditada": True, "cliente": "Agrosat"},
    {"modelo": "maleza-v3", "endpoint": "api-norte", "peticion": "R-3",
     "acierto": True, "latencia_ms": 350, "auditada": True, "cliente": "Ecopetrol"},
    {"modelo": "maleza-v3", "endpoint": "api-sur", "peticion": "R-4",
     "acierto": True, "latencia_ms": 350, "auditada": True, "cliente": "Agrosat"},
    {"modelo": "maleza-v3", "endpoint": "api-sur", "peticion": "R-5",
     "acierto": False, "latencia_ms": 300, "auditada": True, "cliente": "Agrosat"},
    {"modelo": "maleza-v3", "endpoint": "api-norte", "peticion": "R-6",
     "acierto": False, "latencia_ms": 300, "auditada": False, "cliente": "Ecopetrol"},
    # suelos-beta: acierta en las 2 auditadas, pero las 2 sin auditar son
    # lentisimas y la media de las CUATRO se va a 550.
    {"modelo": "suelos-beta", "endpoint": "api-sur", "peticion": "R-7",
     "acierto": True, "latencia_ms": 200, "auditada": True, "cliente": "Agrosat"},
    {"modelo": "suelos-beta", "endpoint": "api-sur", "peticion": "R-8",
     "acierto": True, "latencia_ms": 200, "auditada": True, "cliente": "Agrosat"},
    {"modelo": "suelos-beta", "endpoint": "api-sur", "peticion": "R-9",
     "acierto": False, "latencia_ms": 900, "auditada": False, "cliente": "Agrosat"},
    {"modelo": "suelos-beta", "endpoint": "api-sur", "peticion": "R-10",
     "acierto": False, "latencia_ms": 900, "auditada": False, "cliente": "Agrosat"},
    # hojas-prod: rapidisimo, pero acierta la mitad de las auditadas.
    {"modelo": "hojas-prod", "endpoint": "api-norte", "peticion": "R-11",
     "acierto": True, "latencia_ms": 100, "auditada": True, "cliente": "Ecopetrol"},
    {"modelo": "hojas-prod", "endpoint": "api-norte", "peticion": "R-12",
     "acierto": False, "latencia_ms": 100, "auditada": True, "cliente": "Ecopetrol"},
]
_copia_A = [dict(_x) for _x in _A]

_f = auditar(_A)
assert isinstance(_f, list), (
    "Se esperaba una LISTA de objetos, uno por modelo. Si devuelves un "
    "diccionario, saca sus valores a una lista; si devuelves None, te falta el "
    f"return. Tu devolviste {type(_f).__name__}")
for _o in _f:
    assert not isinstance(_o, (dict, list, tuple, set, str, int, float)), (
        "Lo de dentro de la lista tienen que ser OBJETOS de una clase tuya, no "
        f"{type(_o).__name__}")
assert [_o.nombre for _o in _f] == ["hojas-prod", "maleza-v3", "suelos-beta"], (
    "Son TRES modelos y la lista va ordenada por nombre. Si te salen "
    "'api-sur' o 'Agrosat', estas agrupando por el endpoint o por el cliente, "
    "y ninguno de los dos identifica un modelo. Si te sale el orden "
    "maleza-v3, suelos-beta, hojas-prod, los estas devolviendo en el orden en "
    f"que aparecieron. Los tuyos son {[getattr(_o, 'nombre', None) for _o in _f]}")

_hojas, _maleza, _suelos = _f

assert abs(_maleza.exactitud() - 0.8) < 1e-9, (
    "maleza-v3 tiene SEIS peticiones, pero solo CINCO auditadas, y acierta en "
    "cuatro: su exactitud es 4/5 = 0.8. Si te sale 0.666..., estas dividiendo "
    "entre las seis, y la sexta nadie la miro. Si te sale 80.0, lo estas dando "
    f"en por ciento y se pide entre 0 y 1. Tu devolviste {_maleza.exactitud()}")
assert abs(_maleza.latencia_media() - 300.0) < 1e-9, (
    "La latencia media va sobre TODAS las peticiones, auditadas o no: "
    f"(250+250+350+350+300+300)/6 = 300.0. Tu devolviste {_maleza.latencia_media()}")
assert isinstance(_maleza.se_retira(), bool), (
    "se_retira() contesta True o False. Si te sale otra cosa, probablemente "
    "estas devolviendo el resultado de un print o te falta el return. "
    f"Tu devolviste un {type(_maleza.se_retira()).__name__}")
assert _maleza.se_retira() is False, (
    "maleza-v3 esta justo en los dos bordes y los dos la salvan: 0.8 LLEGA al "
    "80 % y 300.0 no PASA de 300. Si te sale True, mira los simbolos: se "
    f"retira con exactitud < 0.8 o con latencia > 300. Tu devolviste {_maleza.se_retira()}")

assert abs(_suelos.exactitud() - 1.0) < 1e-9, (
    "suelos-beta acierta en las DOS peticiones auditadas: 2/2 = 1.0. Si te "
    "sale 0.5, estas contando tambien las dos sin auditar, que traen acierto "
    f"False porque nadie las miro. Tu devolviste {_suelos.exactitud()}")
assert abs(_suelos.latencia_media() - 550.0) < 1e-9, (
    "La media de (200+200+900+900)/4 es 550.0. Si te sale 200.0, estas "
    "promediando solo las auditadas, y la latencia va sobre todas. "
    f"Tu devolviste {_suelos.latencia_media()}")
assert _suelos.se_retira() is True, (
    "suelos-beta no falla ni una auditada, pero 550 pasa de 300: se retira. "
    f"Tu devolviste {_suelos.se_retira()}")

assert abs(_hojas.exactitud() - 0.5) < 1e-9, (
    f"hojas-prod acierta 1 de sus 2 auditadas: 0.5. Tu devolviste {_hojas.exactitud()}")
assert abs(_hojas.latencia_media() - 100.0) < 1e-9, (
    f"Y su latencia media es 100.0. Tu devolviste {_hojas.latencia_media()}")
assert _hojas.se_retira() is True, (
    "hojas-prod es rapidisimo, pero 0.5 no llega al 80 %: se retira. Las dos "
    f"condiciones van con «o», no con «y». Tu devolviste {_hojas.se_retira()}")

assert _A == _copia_A, "La lista que te pasan no se toca, solo se lee"

# OTRO juego: DOS modelos, otros nombres, un campo de mas, y el borde de la
# latencia por los dos lados. Los dos aciertan todo lo auditado, asi que aqui
# solo decide la latencia.
_B = [
    {"modelo": "voz-pro", "endpoint": "api-centro", "peticion": "Q-1",
     "acierto": True, "latencia_ms": 301, "auditada": True,
     "cliente": "Caja", "region": "andina"},
    {"modelo": "voz-pro", "endpoint": "api-centro", "peticion": "Q-2",
     "acierto": True, "latencia_ms": 299, "auditada": True,
     "cliente": "Caja", "region": "andina"},
    {"modelo": "ocr-lite", "endpoint": "api-centro", "peticion": "Q-3",
     "acierto": True, "latencia_ms": 302, "auditada": True,
     "cliente": "Caja", "region": "andina"},
    {"modelo": "ocr-lite", "endpoint": "api-centro", "peticion": "Q-4",
     "acierto": True, "latencia_ms": 299, "auditada": True,
     "cliente": "Caja", "region": "andina"},
]
_g = auditar(_B)
assert [_o.nombre for _o in _g] == ["ocr-lite", "voz-pro"], (
    "Aqui hay dos modelos, ocr-lite y voz-pro, en ese orden alfabetico. Si te "
    "salen tres o los del juego de arriba, tu funcion los tiene cableados. "
    f"Los tuyos son {[getattr(_o, 'nombre', None) for _o in _g]}")
assert abs(_g[1].latencia_media() - 300.0) < 1e-9, (
    f"(301+299)/2 = 300.0. Tu devolviste {_g[1].latencia_media()}")
assert _g[1].se_retira() is False, (
    "voz-pro se queda en 300.0 exactos, que no PASA de 300: no se retira")
assert abs(_g[0].latencia_media() - 300.5) < 1e-9, (
    f"(302+299)/2 = 300.5. Tu devolviste {_g[0].latencia_media()}")
assert _g[0].se_retira() is True, (
    "ocr-lite acierta todo lo auditado, pero 300.5 si pasa de 300: se retira")
print("Los tres numeros salen bien, la regla respeta los dos bordes y la lista sale ordenada.")''',
        # Las ocultas repiten los mismos diez modos con otros valores: otros
        # nombres, cuatro modelos, otro denominador en la exactitud, los dos
        # bordes otra vez y campos de mas. Ninguna comprobacion nueva.
        pruebas_ocultas='''_C = [
    # "delta": 8 aciertos de 10 auditadas = 0.8 justo; latencia baja.
    {"modelo": "delta", "endpoint": "e1", "peticion": "P-%d" % _i,
     "acierto": _i < 8, "latencia_ms": 10, "auditada": True, "cliente": "c1"}
    for _i in range(10)
]
_C = _C + [
    # "alfa": una sola auditada y la falla -> 0.0; rapidisimo igual.
    {"modelo": "alfa", "endpoint": "e2", "peticion": "P-20",
     "acierto": False, "latencia_ms": 5, "auditada": True, "cliente": "c2"},
    {"modelo": "alfa", "endpoint": "e2", "peticion": "P-21",
     "acierto": False, "latencia_ms": 5, "auditada": False, "cliente": "c2"},
    # "omega": perfecto en lo auditado y justo en el borde de latencia.
    {"modelo": "omega", "endpoint": "e1", "peticion": "P-30",
     "acierto": True, "latencia_ms": 200, "auditada": True, "cliente": "c3",
     "sobra": 1},
    {"modelo": "omega", "endpoint": "e2", "peticion": "P-31",
     "acierto": False, "latencia_ms": 400, "auditada": False, "cliente": "c3",
     "sobra": 2},
]
_copia_C = [dict(_x) for _x in _C]
_h = auditar(_C)
assert isinstance(_h, list) and len(_h) == 3, "Tres modelos distintos"
for _o in _h:
    assert not isinstance(_o, (dict, list, tuple, set, str, int, float)), (
        "Objetos de una clase tuya")
assert [_o.nombre for _o in _h] == ["alfa", "delta", "omega"], (
    "Ordenados por nombre, no por aparicion ni por endpoint")

_alfa, _delta, _omega = _h
assert abs(_delta.exactitud() - 0.8) < 1e-9, "8 de 10 auditadas es 0.8 justo"
assert abs(_delta.latencia_media() - 10.0) < 1e-9, (
    "Las diez peticiones de delta tardaron 10 ms, asi que su media es 10.0")
assert _delta.se_retira() is False, "0.8 LLEGA al 80 %: delta se queda"
assert abs(_alfa.exactitud() - 0.0) < 1e-9, (
    "alfa falla su unica auditada; la otra no se cuenta aunque traiga False")
assert abs(_alfa.latencia_media() - 5.0) < 1e-9, "La media va sobre las dos"
assert _alfa.se_retira() is True, "0.0 no llega al 80 %"
assert abs(_omega.exactitud() - 1.0) < 1e-9, (
    "omega acierta su unica auditada; la no auditada no resta")
assert abs(_omega.latencia_media() - 300.0) < 1e-9, (
    "(200+400)/2 = 300.0, y la no auditada tambien cuenta para la latencia")
assert _omega.se_retira() is False, "300.0 no PASA de 300"
assert _C == _copia_C, "La lista que te pasan no se toca"

# Un solo modelo, una sola peticion. Los mismos modos de la celda visible
# (el borde de la latencia por arriba, con ocr-lite y sus 300.5), con otro valor.
_D = [{"modelo": "solo", "endpoint": "e", "peticion": "P", "acierto": True,
       "latencia_ms": 301, "auditada": True, "cliente": "c"}]
_k = auditar(_D)
assert len(_k) == 1 and _k[0].nombre == "solo", (
    "Un solo registro: la lista trae un objeto, llamado 'solo'")
assert abs(_k[0].exactitud() - 1.0) < 1e-9, (
    "Su unica peticion esta auditada y acerto: 1/1 = 1.0")
assert abs(_k[0].latencia_media() - 301.0) < 1e-9, (
    "Y la media de una sola peticion de 301 ms es 301.0")
assert _k[0].se_retira() is True, "301 pasa de 300, aunque acierte todo"''',
        pistas=[
            "Empieza por el esqueleto que ya usaste: un diccionario de modelos, "
            "crear el objeto la primera vez que aparece su nombre, y meterle "
            "dentro lo que trae cada linea. El endpoint y el cliente no "
            "identifican nada.",
            "Los dos numeros de la regla no se cuentan sobre lo mismo. Vuelve "
            "a «Como funciona la casa» y contesta dos cosas: de que peticiones "
            "se sabe de verdad si acertaron, y cuales de ellas tardaron en "
            "responder. Cada una de las dos respuestas es el denominador de uno "
            "de los dos numeros, y no son el mismo.",
            "`se_retira` es una sola linea con un `or`, y cada mitad tiene su "
            "simbolo: «no llega al 80 %» es `exactitud() < 0.8` (con 0.8 justo "
            "NO se retira) y «pasa de 300» es `latencia_media() > 300` (con 300 "
            "justo tampoco). Si te fallan los bordes, estas usando `<=` o `>=`.",
        ],
    )

    # =========================================================================
    c.seccion(6, "Habla con el asistente", 1, """**Cinco preguntas** para todo el cuadernillo.""")

    c.md("""No gastes ninguna en «¿cómo se escribe una clase?»: eso es de la semana
pasada. Guárdalas para el reparto, que es lo difícil de hoy, y pregunta con el
modelo delante — no con el error.

Mal: «mi `auditar` no pasa la prueba».
Bien: «hice una clase Modelo con una lista de peticiones. Mi `exactitud()`
divide los aciertos entre `len(self.peticiones)` y la prueba espera 0.8 donde
yo saco 0.666. ¿Qué peticiones tengo que estar contando abajo?»
""")

    # =========================================================================
    c.seccion(7, "Cierre", 1, """Dos preguntas que nadie corrige, y el glosario.""")

    c.md("""- En el diagrama del primer ejercicio, el diamante del lado del `Lote` está
  **vacío**. Si lo hubieran dibujado lleno, ¿qué cambiaría en tu código? ¿Y qué
  cambiaría en lo que el diagrama **promete**? (Pista: mira quién crea la
  `Imagen` en el ejemplo del enunciado.)
- `auditar` devuelve objetos con tres métodos. Si mañana el equipo añade una
  tercera condición a la regla, ¿en cuántos sitios hay que tocar? ¿Y si la
  exactitud estuviera calculada fuera de la clase?

### Lo que te llevas al taller

En clase se hace lo que no sabe medir una celda de prueba: **dibujar** el
diagrama de un sistema que alguien describe en voz alta, y defender por qué esa
clase y no otra. El código de hoy es la mitad; la otra mitad es el dibujo.

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **UML** | La notación estándar para dibujar un sistema antes de escribirlo |
| **Diagrama de clases** | Las clases, sus atributos, sus métodos y cómo se relacionan |
| **Asociación** | A conoce a B; los dos existen por su cuenta |
| **Agregación** | A agrupa B que ya existían y siguen sin él (diamante vacío) |
| **Composición** | A es dueño de sus B: los crea y mueren con él (diamante lleno) |
| **Multiplicidad** | Cuántos participan: `1`, `0..1`, `1..*`, `*` |
| **Ruido** | Un dato real del sistema que no hace falta para contestar |
| **Identidad** | Lo que distingue un objeto de otro; a veces son dos campos, no uno |
""")

    return c
