#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 11: «Programación orientada a objetos».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 11 — Programación orientada a objetos.

25 puntos de nbgrader en tres ejercicios (5/10/10), 5 XP y la insignia «Quien
modela». ~30 minutos, teoría breve y ejercicios, siguiendo la pauta del
2026-09-22.

De dónde sale el contenido (planeación 41333, semana 11)
--------------------------------------------------------
Primera semana de POO: `class`, atributos de instancia, `__init__` y `self`,
métodos. Y la pregunta que justifica el tema: para qué agrupar estado y
comportamiento, en vez de pasar un diccionario por todas partes — que es lo que
el alumno sabe hacer desde la semana 8.

Lo que NO entra, y es una decisión: herencia, `property`, `dataclass` y los
métodos de clase o estáticos. Son la segunda semana de POO, no la primera, y el
presupuesto de minutos lo necesita la semana 12.

EL ENCARGO DE ESTA SEMANA: medir I4 (mCC103), que hoy no la mide nadie
----------------------------------------------------------------------
`docs/etiquetar_cuadernillo_nuevo.md` lo deja escrito: de las tres
microcompetencias en alcance, **mCC103 («reconoce problemas de sistemas y
organizaciones susceptibles de tratamiento algorítmico») la miden CERO
ejercicios**, y no se arregla reetiquetando los que hay, porque todos son de
escribir código y mCC103 va de *reconocer*. Diego pidió las semanas 11 y 12
«con más ejercicios de la microcompetencia que falta».

Dos cosas cerraban las salidas fáciles:

1. **El nivel exige 3 ejercicios DISTINTOS intentados** (`MinimoEvidencia = 3`
   en `backend/internal/service/nivelCompetencia.go`). Un ejercicio simbólico no
   mueve a nadie de nivel.
2. **Los quices NO emiten telemetría.** Un «elige cuál de estas tres
   situaciones admite un algoritmo» puesto como quiz se parece mucho a lo que
   describe mCC103 y no cuenta para nada: `custom.js` solo emite desde celdas
   de prueba cuyo `grade_id` empieza por `test_`. Es lo que tumbó la medición de
   I7. Así que tiene que ser un `c.ejercicio(...)` calificable.

**La vía que se siguió**, y es la misma en los dos ejercicios I4 de aquí: el
enunciado da una **descripción en prosa de cómo funciona una organización** y el
alumno tiene que **sacar de ahí el modelo**. Lo que se mide es si reconoció la
estructura: qué entidades hay, **cuál es la variable que decide** y **qué parte
del enunciado es ruido**. Para que eso sea calificable, y no un ejercicio de
redacción:

- La prosa trae datos irrelevantes **a propósito**, mezclados con los que
  deciden. Y no solo texto —el código del lote, el nombre del paciente, la
  aseguradora—, que eso lo descarta cualquiera: trae también **ruido
  numérico**, un número que parece decidir y no decide. Es ahí donde se separa
  quien leyó de quien contó campos.
- La **firma del constructor incluye el ruido**. Si solo recibiera los campos
  que deciden, la propia firma sería la respuesta: el ejercicio pasaría a ser
  «aplica esta fórmula» y mediría I3, no I4.
- **El camino de quien no leyó la prosa tiene que DAR MAL, y dar mal en la
  celda visible.** Esta es la prueba de fuego de la etiqueta, y es la que los
  dos ejercicios suspendían antes del 2026-11-03: si la respuesta ingenua
  —restar los dos campos con pinta de «total» y «hecho», ordenar por el campo
  que se llama «prioridad»— coincide con la correcta, el ejercicio reparte los
  puntos sin que nadie haya reconocido nada, y entonces mide I3 aunque diga I4.
- Las pruebas alimentan casos **con ese ruido dentro** y comprueban el
  **comportamiento**, no la forma: cómo guarde el alumno los datos por dentro
  es su decisión.
- Las OCULTAS repiten los mismos modos de fallo con **otros valores y otro
  dominio**, para que no sirva cablear el ejemplo. No estrenan modos nuevos
  (ver más abajo).
- El enunciado **no dice cuál es la variable decisiva**. Dice qué hace la
  organización, con las palabras de la organización. Decirlo convertiría el
  ejercicio en I3.

Y lo que **no** sirve de medición, aunque lo parezca: el `assert` de dos fichas
con los MISMOS números y distintos textos. Comprueba que el código del lote y
el nombre del paciente no entran en la cuenta, y eso está bien tenerlo, pero no
distingue dos entregas plausibles: cualquier solución que opere con los campos
numéricos lo cumple, y una que compare el día con algo revienta con `TypeError`
antes de dar un resultado. Es ruido de texto, lo descarta cualquiera. Lo que
separa es el ruido **numérico**, y en los dos ejercicios tiene su propio caso
visible.

HONESTIDAD DEL ETIQUETADO, ejercicio por ejercicio
--------------------------------------------------
- **E1 `Experimento` → I3 (mCC87) y nada más.** Es la rampa: escribir una clase
  con `__init__` y un método, con los atributos ya nombrados en el enunciado.
  Eso es **aplicar la sintaxis que acabas de leer**, y etiquetarlo I4 sería
  inflar la cobertura exactamente como advierte el repositorio («hay que validar
  que ese ejercicio de verdad mide la competencia, no ponerlo por llegar al
  número»). I3 sí, y es el mismo criterio con que están etiquetadas las rampas
  de las semanas 6 a 9: hay una regla dicha en español —«mejoró si el error
  final quedó por debajo del inicial»— que hay que traducir a una comparación.
  I1 **no**: una comparación no es aplicar matemáticas.
- **E2 `Lote` → I4 + I3.** La prosa describe cómo trabaja el laboratorio de
  anotación y el alumno modela la ficha. Lo que hay que reconocer es que las
  **dudosas** caen en dos sitios a la vez: ya están dentro de las `anotadas`
  —el anotador les puso etiqueta— y siguen siendo trabajo del lote, porque
  alguien tiene que volver a mirarlas. Así que la cuenta de lo que queda por
  tocar es `(imagenes - anotadas) + dudosas`, y un lote con todo anotado y
  alguna marcada **no está terminado**. El criterio de cierre está dicho como lo
  dice el coordinador («hasta que nadie tiene nada que hacer con él»), no como
  una fórmula.

  Y aquí está la corrección del 2026-11-03, que es la que hace la etiqueta
  defendible: hasta entonces `faltan()` era `imagenes - anotadas` y
  `terminado()` era `anotadas == imagenes`, o sea que **el camino de quien no
  leía la prosa daba la respuesta correcta** y se llevaba los 10 puntos sin
  reconocer nada; las dudosas solo castigaban a quien leía y además se
  equivocaba. Encima la enumeración de la ficha regalaba la contención diciendo
  «cuántas van ya anotadas y cuántas **de esas** quedaron marcadas», antes del
  párrafo que la explica. Ahora los seis campos se listan planos, la contención
  hay que sacarla del párrafo, y el camino ingenuo falla en la **primera** ficha
  de la celda visible con un mensaje que dice qué se dejó sin leer.
- **E3 `ColaDeLectura` → I4 + I3.** La prosa describe una decisión que la jefa
  del servicio **toma a mano cada mañana** y quiere dejar de tomar a mano. El
  alumno tiene que reconocer que eso es un problema de **priorizar**, cuál es el
  criterio que ordena y cuál desempata.

  Y aquí va la otra corrección del 2026-11-03. Antes el enunciado **dictaba la
  regla**: «manda a leer primero el estudio que el modelo marcó más alto y, si
  dos están marcados igual, el que lleve más horas esperando», con el puntaje
  definido cuatro líneas arriba como «el puntaje que le puso el modelo de
  triaje». Eso mapea uno a uno sobre dos campos, no deja ningún paso de
  inferencia, y por el criterio de este mismo docstring convertía el ejercicio
  en I3. Peor: el enunciado presumía en negrita de «tampoco te dice qué dato
  decide» tres líneas antes de decirlo, lo que hace desconfiar a quien lee bien
  y le quema minutos buscando un truco que no existía.

  Ahora la jefa **no da una regla: cuenta dos cosas que le pasaron** —una queja
  por haber dejado para la tarde uno que el triaje traía arriba del todo, y que
  no soporta que el que lleva media mañana esperando ceda el turno a uno que
  acaba de entrar— y no nombra ningún campo. El criterio y el desempate salen de
  ahí.

  El **ruido numérico** también cambió, porque el de antes era flojo: era el
  «número de orden», y el enunciado tiene que decir que el número de orden es lo
  que hay que **devolver**, así que nadie tenía que deducir que no ordena. Ahora
  el ruido es la **prioridad administrativa**: un número de 1 a 3 cuyo nombre
  invita a ordenar por él, que la aseguradora pone por contrato, y que la jefa
  no menciona ni una vez. Quien ordena por él lo ve en rojo en la celda visible,
  y en los dos sentidos (una prioridad 1 que no gana y una prioridad 3 que sí).
- **I1 (mCP17) no se etiqueta en ninguno**, y conviene decir por qué habiendo
  hueco de cobertura: en esta semana no hay matemáticas. Hay comparaciones y una
  resta. Ponerle I1 a una resta es justo lo que el repositorio pide no hacer.
- Fuera de alcance y **sin etiquetar**: I2, I5, I6, I7.

Resultado: **2 etiquetas I4 defendibles**, no tres, y el techo de esta semana
son 2 — el formato son tres ejercicios y el primero es la rampa de sintaxis, que
es I3 y tiene que seguir siéndolo.

LA ARITMÉTICA, escrita para que nadie construya la semana 12 sobre una cuenta
equivocada: `MinimoEvidencia = 3`, esta semana aporta **2**, así que **la semana
12 tiene que aportar al menos 1 ejercicio I4 defendible** para que el primer
alumno llegue a tener nivel medido en mCC103. Su techo también son 2 (su E1 será
igualmente la rampa), así que hay un ejercicio de margen y ni uno más. Si al
revisar la 12 se cae alguna de sus etiquetas, la competencia se queda en cero
alumnos medidos aunque el `competencias.json` diga I4 en seis sitios: el umbral
cuenta ejercicios **intentados**, no etiquetas emitidas.

QUÉ NO SE DA POR SABIDO
-----------------------
El alumno llega con variables y tipos, condicionales, ciclos, listas (de una y
dos dimensiones), funciones, diccionario/conjunto/tupla, archivos, `try/except`,
NumPy, pandas y Matplotlib. De clases **no sabe nada**: esta es su primera
semana. Así que las cuatro piezas que necesita cualquiera de las tres
soluciones se enseñan antes, en este mismo cuadernillo, y por separado:

| Pieza | Dónde se enseña | Quién la necesita |
|---|---|---|
| `class`, `__init__`, `self`, un método | §3 y la figura de la anatomía | los tres |
| `__repr__` | §3, en la misma clase | ninguno (es para depurar) |
| recorrer una **lista de objetos** y elegir el mejor por un atributo | §4A, sobre una lista suelta | E3 |
| un atributo que **es una lista y crece** | §4B, en una clase sin ninguna prioridad dentro | E3 |

Separadas a propósito: §4A hace el máximo sobre una lista que no es de nadie, y
§4B hace la clase que acumula sin elegir nada. Ninguna de las dos celdas es E3
con una línea menos — E3 es juntarlas, añadir el desempate y, sobre todo, sacar
de la prosa qué va en cada sitio.

Y lo que **no** se usa aunque dé lástima: la comprensión de lista (no se ha
enseñado en ninguna celda de cuerpo del curso) y `sorted(..., key=...)`, que
tampoco. `sorted()` se nombró en la semana 6, pero `key=` y `lambda` no se han
explicado nunca, así que E3 se resuelve con el recorrido de §4A.

OJO con a qué semana apunta §4A, que estuvo mal hasta el 2026-11-03. Decía que
elegir el mejor es «exactamente como la búsqueda lineal de la semana 6», y no lo
es: `buscar_lineal` recorre y **sale en cuanto encuentra** el primero que
cumple. Quien se fiaba del puntero y copiaba esa forma en E3 escribía un `for`
que devuelve el primer estudio apuntado, que es justo lo que el primer `assert`
visible de E3 castiga. El patrón que el alumno de verdad ya escribió a mano es
el `maximo_de_columna` de la semana 7 —y arranca distinto, con
`mayor = matriz[0][c]` en vez de `None`, que es el otro error que E3 hace
reventar—, así que §4A apunta allí, nombra la diferencia del arranque y avisa de
que aquí el ciclo no se sale a la primera.

EL INTÉRPRETE DE PSEUDOCÓDIGO NO SE USA. `pseudo_uis` no entiende listas,
matrices, clases ni definición de funciones, así que esta semana es todo Python.
Tampoco se carga como módulo: solo viaja `contenido.py`.

LA REGLA DE LAS PRUEBAS, que es la que más revisiones ha costado
----------------------------------------------------------------
**Todo modo de fallo que comprueben las ocultas tiene que fallar también en las
visibles.** Las ocultas de aquí solo añaden más casos de los mismos modos, con
otros valores y otro dominio. Si alguien añade a las ocultas una comprobación
nueva, el caso que la provoca sube también a la celda visible. En la semana 7, un
caso que solo estaba en las ocultas costó 10 de 25 puntos en silencio.

La revisión del 2026-11-03 encontró **cinco** sitios donde esto estaba roto en
este mismo cuadernillo, con soluciones plausibles reproducidas que pasaban las
visibles enteras en verde y suspendían al calificar. Los cinco están subidos a
la celda visible, con su mensaje:

| Lo que escribe el alumno | Dónde estaba el caso | Ahora |
|---|---|---|
| `(inicial - final) / inicial * 100 > 0` (E1) | solo oculta: `error_inicial = 0.0` → `ZeroDivisionError` pelado | visible, con mensaje que nombra la división |
| `abs(final) < abs(inicial)` (E1) | solo oculta: errores negativos | visible, con mensaje que nombra `abs()` |
| `puntaje >= mejor and horas >= mejor` (E3) | solo oculta: ningún caso visible exigía que el triaje ganara llevando **menos** horas | visible, con mensaje que dice que ahí va un `or` |
| `mejor_puntaje = 0` como centinela (E3) | solo oculta: el triaje más bajo de la visible era 0.10 | visible, con un estudio de triaje **0.0 y 0 horas** — hacen falta los dos ceros |
| `estudios = []` en el cuerpo de la clase (E3) | estaba en visible, pero **al final**: fallaba antes un `assert` de desempate que informaba del número de otra cola | movido al principio de la celda, antes de que `_c` acumule nada |

Y están en las visibles, además, los modos que más duelen por diseño: el lote
con todo anotado **y dudosas sin revisar** (E2), el camino ingenuo de `faltan()`
fallando ya en la primera ficha (E2), el empate de triaje resuelto por horas en
los **dos** órdenes de inserción (E3) y la prioridad administrativa no
decidiendo, en los dos sentidos (E3).

Y cada `assert` lleva MENSAJE: al calificar, el alumno los lee. Dos reglas
pequeñas que salieron de la misma revisión y que conviene no perder:

1. **El valor se guarda en una variable antes de comparar**, nunca
   `assert cosa.metodo() == x, f"...{cosa.metodo()}"`. Para una solución que
   consume la cola, el f-string informaba del resultado de la TERCERA llamada:
   el alumno leía «tu devolviste None» cuando su método había devuelto 103, y se
   iba a buscar un `return` que no faltaba.
2. **El `assert` que diagnostica un fallo estructural va antes que los que
   diagnostican detalles.** Si el alumno comparte la lista entre colas, el
   mensaje que lo explica solo sirve si se ejecuta: puesto al final de la celda
   nunca llegaba a correr.

OJO con el número de unidad. La planeación tiene solo CUATRO unidades y para
esta semana dice «Unidad 4». Pero los cuadernillos publicados usan unidad =
semana desde la 4 («Unidad 7», «Unidad 10»), así que aquí se sigue esa
convención para que el alumno no vea un salto de «Unidad 10» a «Unidad 4» y lo
reporte como error — ya pasó con la numeración de la semana 3. Está explicado
con más detalle en el docstring de la semana 7.

LA GUARDA «ejecuta primero TU celda» Y LAS CLASES. `nombre_de_la_respuesta` del
constructor deduce `ClassDef`, así que una `partida` que empieza por
`class Experimento:` emite bien la guarda. Comprobado con build.py: los tres
ejercicios la llevan y no sale ningún AVISO.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(AQUI) not in sys.path:
    sys.path.insert(0, os.path.dirname(AQUI))

from constructor import Cuadernillo  # noqa: E402


def construir(motor_comprimido=True):
    c = Cuadernillo(
        codigo="semana_11",
        titulo="Programación orientada a objetos",
        semana=11,
        meta_xp=5,
        insignia="Quien modela",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[os.path.join(AQUI, "contenido.py")],
    )

    # «Unidad 11», no «Unidad 4» como la nombra la planeación: las portadas
    # publicadas numeran la unidad por la semana desde la 4. El por qué
    # completo, en el docstring.
    c.md("""# Programación orientada a objetos
### Semana 11 · Unidad 11 · Programación orientada a objetos

Desde la semana 8 guardas un registro en un **diccionario** y escribes **aparte**
las funciones que lo usan. Funciona, y nada ata las dos mitades: el diccionario
no sabe qué funciones lo esperan, y las funciones no saben si el diccionario que
les llega trae las claves que necesitan.

Esta semana las atas. Un **objeto** es un dato que trae puesto lo que sabe hacer
con él mismo.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Escribir una **clase** con `class`, y crear **instancias** suyas.
- Guardar datos en `__init__` como **atributos** (`self.algo = algo`) y leerlos
  después con el punto.
- Escribir **métodos**: funciones que viven dentro de la clase y usan los
  atributos de la instancia a la que se las pides.
- Explicar qué es `self` y por qué en la llamada no se escribe.
- Darle a una clase un atributo que es una **lista que crece**, y recorrer una
  lista de objetos para elegir uno.

**25 puntos** y **5 XP**; la insignia se llama «Quien modela». No hay
pseudocódigo: el intérprete del curso no conoce clases.
""")

    # =========================================================================
    c.seccion(1, "Calentamiento", 1, """Una de la semana 8. Sin nota: da XP.""")
    c.code("quiz_dato_y_calculo()")

    # =========================================================================
    # El gancho: el problema antes de la sintaxis. Y sin sembrar un error — la
    # celda no revienta a propósito, porque verificar.py ejecuta todas las
    # celdas del cuerpo y un KeyError aquí contaría como cuadernillo roto.
    c.seccion(2, "Dos mitades que nadie ata", 2, """Esto es lo que sabes hacer hoy. Ejecútalo y mira la última línea:""")

    c.code('''corrida = {"modelo": "resnet", "epocas": 20}

def larga(reg):
    return reg["epocas"] > 10

print("¿fue larga?", larga(corrida))

# Y nada impide que aparezca un registro parecido, pero no igual:
otro = {"modelo": "vit", "iteraciones": 20}      # se llama distinto
print("¿otro trae la clave que larga() espera?", "epocas" in otro)''')

    c.md("""`larga` espera una clave que `otro` no tiene. Nadie avisa hasta que
alguien lo llama y revienta. Y al revés: alguien puede usar `corrida` años sin
enterarse de que `larga` existe.

El arreglo no es acordarse mejor. Es que el dato y lo que se calcula con él
dejen de ser dos cosas:
""")

    c.code("ver_dict_vs_objeto()")

    # =========================================================================
    c.seccion(3, "Concepto en corto", 5, """Una clase es un **molde**. Lo que sale del molde es un **objeto**.""")

    c.md("""Cuatro reglas, y con eso está dicho el tema:

1. **`class Nombre:`** define el molde. En mayúscula, por costumbre. Un molde no
   es un objeto: es de lo que salen.
2. **`__init__`** es lo que corre al crear uno. Recibe los datos y los guarda.
   Se llama así, con los dos guiones bajos a cada lado, y no se llama a mano:
   corre cuando escribes `Nombre(...)`.
3. **`self.algo = algo`** guarda un **atributo**: un dato que se queda pegado a
   ese objeto. Después se lee con el punto, `objeto.algo`.
4. Un **método** es un `def` dentro de la clase, y su primer parámetro es
   `self`. Dentro usa `self.algo` para llegar a sus propios datos.

Y una quinta, que no es del tema pero ahorra tiempo: **`__repr__`** devuelve el
texto con que se ve el objeto al imprimirlo. Sin él, un `print` dice
`<__main__.Corrida object at 0x7f...>`, que no sirve para nada.
""")

    c.code('''class Corrida:
    def __init__(self, modelo, epocas):
        self.modelo = modelo          # atributo, pegado a ESTA corrida
        self.epocas = epocas

    def larga(self):                  # metodo: su primer parametro es self
        return self.epocas > 10

    def __repr__(self):               # como se ve al imprimirla
        return "Corrida(" + self.modelo + ", " + str(self.epocas) + ")"


a = Corrida("resnet", 20)             # aqui corre __init__
b = Corrida("vit", 3)                 # otra, con sus propios datos

print(a, "->", a.larga())
print(b, "->", b.larga())
print("el atributo, con el punto:", a.modelo, "/", b.modelo)''')

    c.md("""Dos objetos de la misma clase, cada uno con **sus** atributos: `a.epocas` es 20
y `b.epocas` es 3, y `larga()` contesta distinto según a quién se le pida. Esa
es toda la idea.

Ahora las cinco piezas, señaladas una por una:
""")

    c.code("ver_anatomia_clase()")

    c.md("""> **Dos errores que vas a cometer esta semana, y los dos dan el mismo susto.**
> Dentro de un método, el atributo se lee **`self.epocas`**, nunca `epocas`
> suelto: sin el `self.` Python dice `NameError`, porque `epocas` solo existió
> mientras corría `__init__`. Y el método se le pide a un objeto —`a.larga()`—,
> no a la clase: `Corrida.larga()` da `TypeError`, porque ahí nadie le dice
> quién es `self`.
""")

    # =========================================================================
    # Los minutos de cada c.seccion no se escriben a ojo: tienen que cuadrar
    # (±15 %) con lo que estima estimar_tiempo.py, y build.py falla si no. Si
    # recortas o añades algo, vuelve a correr `python3 estimar_tiempo.py
    # semana_11` y ajusta estos números.
    c.seccion(4, "Laboratorio", 3, """Las dos cosas que se hacen con objetos en cuanto hay más de uno.""")

    c.md("""### 4A. Una lista de objetos, y elegir uno

Una lista puede guardar objetos igual que guardaba números. Y para elegir el
mejor se recorre **arrastrando un candidato**, como el `maximo_de_columna` que
escribiste en la semana 7 —solo que ahora lo que se compara es un **atributo**,
y el candidato empieza en `None` en vez de en el primer elemento, porque la
lista puede venir vacía:
""")

    c.code('''corridas = [Corrida("resnet", 20), Corrida("vit", 3), Corrida("bert", 45)]

mejor = None                          # todavia no hay candidato
for una in corridas:
    if mejor is None or una.epocas > mejor.epocas:
        mejor = una                   # este le gana al que tenia

print("la mas larga:", mejor)
print("y su modelo, por si solo hace falta eso:", mejor.modelo)''')

    c.md("""`mejor` empieza en `None` porque la lista podría estar vacía, y entonces la
respuesta es que no hay ninguna. Es el mismo patrón del máximo de la semana 7,
con un arranque más seguro: allí el candidato era `matriz[0][c]`, que revienta
si la matriz no tiene filas.

> **Y fíjate en que el ciclo no se sale a la primera.** La búsqueda lineal de la
> semana 6 devolvía en cuanto encontraba lo que buscaba; aquí hay que llegar
> hasta el final, porque hasta la última vuelta puede aparecer uno mejor.

### 4B. Un atributo que es una lista y crece

Un atributo no tiene que ser un número ni un texto. Si en `__init__` pones una
**lista vacía**, la clase puede ir guardando cosas:
""")

    c.code('''class Bitacora:
    def __init__(self):
        self.errores = []             # la lista se crea AQUI, dentro de __init__

    def apuntar(self, error):
        self.errores.append(error)    # crece, llamada a llamada

    def cuantas(self):
        return len(self.errores)


uno = Bitacora()
uno.apuntar(0.80)
uno.apuntar(0.41)

otra = Bitacora()                     # bitacora nueva, lista nueva
otra.apuntar(0.12)

print("uno:", uno.errores, "->", uno.cuantas(), "apuntes")
print("otra:", otra.errores, "->", otra.cuantas(), "apuntes")''')

    c.md("""> **Fíjate en dónde se crea la lista, que es el error más caro de la semana.**
> `self.errores = []` va **dentro de `__init__`**, así que cada `Bitacora()` se
> hace la suya. Si la pones fuera, suelta en el cuerpo de la clase, hay **una
> sola lista para todas** y los apuntes de una aparecen en la otra. Es un fallo
> que no da ningún error: solo respuestas raras.
""")

    # =========================================================================
    # Sin números de ejercicio en la prosa: envejecen en cuanto alguien
    # renumera. Se nombran las clases, que no cambian de nombre al cambiar de
    # sitio (docs/cuadernillos_semanas_7_a_16.md §4, trampa 2).
    #
    # 25 minutos y no 22, que es lo que declaran las semanas 8 a 10 en esta
    # sección. Son los 22 de resolver (1★+2★+3★ según estimar_tiempo.py) más
    # los ~3 de LEER los enunciados, que aquí pesan de verdad: los dos
    # ejercicios I4 traen una descripción en prosa de una organización, y
    # leerla despacio es la mitad del ejercicio. Eran 24 hasta el 2026-11-03;
    # subieron a 25 porque la reescritura de E2 y E3 alargó las dos prosas. El
    # total declarado (38) cuadra con los 38,6 que mide estimar_tiempo.py.
    c.seccion(5, "Tres ejercicios", 25, """**25 puntos**. El primero es sintaxis. Los otros dos te cuentan cómo trabaja
una organización y **no nombran el dato que decide**: sacarlo de ahí —y ver qué
datos de los que te dan no deciden nada— es el ejercicio.""")

    # E1 — la rampa. I3 y solo I3: ver el docstring.
    #
    # La partida es solo `class Experimento:` con un cuerpo `...`. Aqui SI se
    # quiere que el alumno escriba `__init__` y el metodo de su mano: es
    # justamente la destreza de 1 estrella. En E2 y E3 se da el esqueleto, por
    # el motivo contrario (ver sus comentarios).
    #
    # Los atributos se comprueban por su NOMBRE, y es el unico ejercicio de la
    # semana donde se comprueba la forma: en la primera semana de POO, que el
    # dato quede guardado en `self.<nombre>` ES lo que se esta aprendiendo. En
    # E2 y E3 se comprueba solo el comportamiento.
    c.ejercicio(
        numero=1, competencias=['I3'], titulo="La ficha de un experimento",
        estrellas=1, puntos=5,
        enunciado="""Cada vez que se entrena un modelo se apunta cómo fue: con qué nombre se
guardó, cuántas épocas corrió, con qué error empezó y con qué error acabó.

Escribe la clase `Experimento`. Al crear una se le pasan esos cuatro datos, en
este orden, y los guarda en atributos con **estos nombres**: `nombre`,
`epocas`, `error_inicial`, `error_final`.

Y dale un método **`mejoro()`**, sin más argumentos, que devuelva `True` si el
experimento **mejoró** —acabó con menos error del que tenía al empezar— y
`False` si no.

```python
e = Experimento("v1", 20, 0.90, 0.31)
e.nombre          # "v1"
e.error_final     # 0.31
e.mejoro()        # True

malo = Experimento("v2", 5, 0.20, 0.55)
malo.mejoro()     # False: acabo peor de lo que empezo
```

> Un borde que la prueba comprueba: si el error acabó **igual** que empezó, no
> mejoró — es `False`. Y `mejoro()` **devuelve** `True` o `False` con `return`,
> no los imprime.""",
        partida='''class Experimento:
    ...''',
        solucion='''class Experimento:
    def __init__(self, nombre, epocas, error_inicial, error_final):
        self.nombre = nombre
        self.epocas = epocas
        self.error_inicial = error_inicial
        self.error_final = error_final

    def mejoro(self):
        return self.error_final < self.error_inicial''',
        pruebas='''assert isinstance(Experimento, type), (
    "Experimento tiene que ser una CLASE: la primera linea es "
    "`class Experimento:`, sin parentesis y con dos puntos")

_e = Experimento("v1", 20, 0.90, 0.31)

assert _e.nombre == "v1", (
    "Despues de crear el experimento, `e.nombre` tiene que valer 'v1'. Si aqui "
    "sale un AttributeError, `__init__` no guardo el dato: recibirlo como "
    "parametro no basta, hay que escribir `self.nombre = nombre`")
assert _e.epocas == 20, (
    "`e.epocas` tiene que valer 20. Los cuatro datos llegan en el orden del "
    "enunciado: nombre, epocas, error_inicial, error_final")
assert _e.error_inicial == 0.90, (
    "`e.error_inicial` tiene que valer 0.90, que es el TERCER dato. Si te sale "
    "0.31, tienes cambiados el inicial y el final")
assert _e.error_final == 0.31, (
    "`e.error_final` tiene que valer 0.31, que es el CUARTO dato. Si te sale "
    "0.90, tienes cambiados el inicial y el final")

assert callable(getattr(_e, "mejoro", None)), (
    "Falta el metodo `mejoro`. Es un `def mejoro(self):` escrito DENTRO de la "
    "clase, indentado como `__init__`")
_bueno = _e.mejoro()
assert _bueno is True, (
    "Este experimento empezo en 0.90 y acabo en 0.31, asi que mejoro: se "
    "esperaba True. Si sale None, tu metodo imprime en vez de devolver (te "
    "falta `return`); si da NameError, dentro del metodo el atributo se lee "
    f"`self.error_final`, no `error_final` suelto. Tu devolviste {_bueno!r}")

_malo = Experimento("v2", 5, 0.20, 0.55)
_peor = _malo.mejoro()
assert _peor is False, (
    "Este empezo en 0.20 y acabo en 0.55: acabo PEOR, asi que se esperaba "
    f"False. Mira contra que estas comparando. Tu devolviste {_peor!r}")

_igual = Experimento("v3", 8, 0.40, 0.40)
_empate = _igual.mejoro()
assert _empate is False, (
    "Este acabo IGUAL que empezo (0.40 y 0.40) y eso no es mejorar: se "
    "esperaba False. Si te sale True, estas usando <= y se pide < "
    f"(estrictamente menor). Tu devolviste {_empate!r}")

# Tres experimentos vivos a la vez: cada uno con SUS atributos. Si aqui algo
# cambia de valor, estas guardando los datos fuera de la instancia.
assert _e.nombre == "v1" and _malo.nombre == "v2" and _igual.nombre == "v3", (
    "Los tres experimentos existen a la vez y cada uno tiene su propio nombre. "
    "Si los tres te dan el mismo, no estas guardando en `self.`")
assert _e.epocas == 20 and _malo.epocas == 5 and _igual.epocas == 8, (
    "Y sus propias epocas: 20, 5 y 8")
assert _e.mejoro() is True and _malo.mejoro() is False, (
    "Y `mejoro()` contesta segun a quien se le pida: True al primero y False al "
    "segundo. Si los dos te dan lo mismo, el metodo no esta mirando "
    "`self.error_final`")

# OTROS valores, para que no valga cablear los del ejemplo.
_otro = Experimento("exp-2026-11", 300, 2.5, 0.07)
assert _otro.nombre == "exp-2026-11" and _otro.epocas == 300, (
    "Los atributos valen lo que te pasen, sean los que sean: aqui el nombre es "
    "'exp-2026-11' y las epocas 300")
assert _otro.error_inicial == 2.5 and _otro.error_final == 0.07, (
    "Un error no tiene que estar entre 0 y 1: aqui el inicial es 2.5")
assert _otro.mejoro() is True, (
    "De 2.5 a 0.07 hay mejora: True")

# Un error puede valer 0, y puede ser NEGATIVO (una metrica centrada). Los dos
# regimenes estan aqui, en la visible, porque los dos los comprueban las
# ocultas: si solo estuvieran alli, dos soluciones que pasan todo esto en verde
# perderian los 5 puntos al calificar.
_cero = Experimento("v4", 2, 0.0, 0.0)
_mc = _cero.mejoro()
assert _mc is False, (
    "Este empezo y acabo en 0.0, asi que no mejoro: se esperaba False. Y si "
    "esta linea revienta con ZeroDivisionError, estas dividiendo por el error "
    "inicial para sacar un porcentaje de mejora: `mejoro()` solo compara los "
    f"dos numeros, no hace falta dividir. Tu devolviste {_mc!r}")
_neg = Experimento("v5", 3, -0.10, -0.80)
_mn = _neg.mejoro()
assert _mn is True, (
    "Un error puede ser negativo, porque la metrica puede venir centrada: "
    "-0.80 es MENOR que -0.10, asi que este experimento mejoro. Si te sale "
    "False, estas comparando tamanos con `abs()` en vez de los numeros tal "
    f"como vienen. Tu devolviste {_mn!r}")
print("La clase guarda sus cuatro datos y mejoro() contesta bien, incluido el empate.")''',
        # Las ocultas solo repiten los mismos modos con otros valores: cada
        # atributo por su nombre, los tres resultados de mejoro() (mejor, peor,
        # igual), el error que vale 0, el error negativo y varias instancias
        # vivas a la vez. Ningun modo nuevo — los dos ultimos estaban SOLO aqui
        # hasta el 2026-11-03, y asi `(inicial-final)/inicial*100 > 0` pasaba la
        # visible entera y reventaba al calificar con un ZeroDivisionError
        # pelado, sin un assert que lo explicara. Ahora los dos regimenes de
        # valor estan tambien arriba, con mensaje.
        pruebas_ocultas='''_a = Experimento("alfa", 1, 1.0, 0.0)
assert _a.nombre == "alfa" and _a.epocas == 1, "Los cuatro datos, en su orden"
assert _a.error_inicial == 1.0 and _a.error_final == 0.0
assert _a.mejoro() is True, "De 1.0 a 0.0 se mejora"
_b = Experimento("beta", 99, 0.0, 1.0)
assert _b.mejoro() is False, "De 0.0 a 1.0 se empeora"
_c = Experimento("gamma", 7, 0.5, 0.5)
assert _c.mejoro() is False, "Acabar igual no es mejorar: se pide < , no <="
# El error negativo, otra vez: el mismo modo que la visible ya castiga.
_d = Experimento("delta", 4, -0.10, -0.80)
assert _d.mejoro() is True, "-0.80 es menor que -0.10, asi que mejoro"
# Cuatro instancias vivas: ninguna pisa a otra.
assert (_a.nombre, _b.nombre, _c.nombre, _d.nombre) == ("alfa", "beta", "gamma", "delta")
assert (_a.epocas, _b.epocas, _c.epocas, _d.epocas) == (1, 99, 7, 4)
assert [_a.mejoro(), _b.mejoro(), _c.mejoro(), _d.mejoro()] == [True, False, False, True]''',
        pistas=[
            "Son dos bloques dentro de `class Experimento:`. El primero es "
            "`def __init__(self, nombre, epocas, error_inicial, error_final):`, y "
            "dentro, cuatro lineas que empiezan por `self.`.",
            "Guardar un dato es `self.nombre = nombre`: a la izquierda el atributo "
            "que se queda, a la derecha el parametro que llego. Los dos pueden "
            "llamarse igual, no hay problema.",
            "`mejoro` es un `def mejoro(self):` al mismo nivel que `__init__`, y "
            "dentro una sola linea: `return self.error_final < self.error_inicial`. "
            "Con `<`, no con `<=`: acabar igual no es mejorar.",
        ],
    )

    # E2 — el primer I4. Ver el docstring para el argumento completo.
    #
    # Por que el esqueleto SI se da aqui, al contrario que en E1: lo que se mide
    # es el reconocimiento, no la sintaxis. Si el alumno pierde los 10 puntos
    # por escribir `def faltan():` sin `self`, el ejercicio no habra medido
    # mCC103 sino su memoria para la sintaxis que acaba de leer — y eso ya lo
    # mide E1. El esqueleto fija la interfaz y deja intacta la decision.
    #
    # Por que la firma trae las SEIS cosas de la ficha y no solo las que
    # deciden: si recibiera `(imagenes, anotadas)`, la firma seria la respuesta.
    # El ruido tiene que entrar por la puerta para que descartarlo sea una
    # decision del alumno.
    #
    # EL CAMBIO DEL 2026-11-03, y es el que hace que la etiqueta I4 se sostenga.
    # Antes, `faltan()` era `imagenes - anotadas` y `terminado()` era
    # `anotadas == imagenes`: o sea que el camino de quien NO leia la prosa
    # —restar los dos unicos campos con pinta de «total» y «hecho»— daba la
    # respuesta CORRECTA, y se llevaba los 10 puntos sin reconocer nada. Las
    # dudosas solo castigaban a quien leia y ademas se equivocaba. Ahora la
    # prosa dice que volver a mirar una dudosa es trabajo DEL LOTE, asi que:
    #
    #     faltan()    = (imagenes - anotadas) + dudosas
    #     terminado() = faltan() == 0
    #
    # y el camino ingenuo da MAL en la primera ficha de la celda visible, con un
    # mensaje que dice exactamente que se dejo sin leer. Eso es lo que convierte
    # el ejercicio en una medicion: quien no distinguio que una dudosa ya esta
    # anotada Y sigue pendiente, lo ve en rojo antes de entregar.
    #
    # Y la enumeracion de la ficha lista los seis campos PLANOS. Antes decia
    # «cuantas van ya anotadas y cuantas DE ESAS quedaron marcadas como
    # dudosas», o sea que regalaba la contencion dudosas ⊆ anotadas en la propia
    # lista de campos, antes del parrafo que la explica. Si la contencion viene
    # regalada, no hay nada que reconocer.
    #
    # Lo que el assert de las dos fichas con los MISMOS numeros y textos
    # distintos mide, dicho sin inflarlo: que el codigo, el anotador y el dia no
    # entren en la cuenta. Es ruido de TEXTO y lo descarta cualquiera —una
    # comparacion con `dia` revienta con TypeError antes de dar un resultado
    # malo—. No es «la hipotesis de I4 hecha ejecutable», como decia este
    # comentario antes: el que separa de verdad es el de las dudosas.
    c.ejercicio(
        numero=2, competencias=['I4', 'I3'], titulo="La ficha del laboratorio de anotación",
        estrellas=2, puntos=10,
        enunciado="""Lee esto como lo leerías si llegaras nuevo al laboratorio. **No se nombra el
dato que decide: eso lo tienes que ver tú.**

> En el laboratorio de anotación de la facultad se trabaja por **lotes** de
> imágenes. Cada lote lleva pegada una ficha de papel donde el auxiliar apunta,
> a mano, seis cosas: el **código** del lote, el **nombre del anotador** que lo
> tomó, el **día** que entró, cuántas **imágenes** trae en total, cuántas
> **anotadas** lleva y cuántas **dudosas**.
>
> Lo de dudosa funciona así: cuando el anotador no está seguro de una imagen, la
> marca y **sigue adelante**. No la deja en blanco —le pone su etiqueta, y la
> cuenta de anotadas la recoge igual que a cualquier otra—, pero la marca
> significa que alguien tiene que **volver a mirarla**, y ese segundo pase es
> trabajo del lote: lo hace el mismo laboratorio, con el lote abierto encima de
> la mesa.
>
> El coordinador pasa cada mañana, mira las fichas y hace dos preguntas:
> cuántas imágenes de este lote le **quedan a alguien por tocar**, y si el lote
> ya está **terminado**. Lo segundo lo dice siempre con las mismas palabras: «un
> lote no se cierra hasta que nadie tiene nada que hacer con él: ni anotar lo
> que todavía no pasó, ni volver a mirar lo que quedó marcado».

Escribe la clase `Lote`. Recibe los seis datos de la ficha, en el orden en que
el auxiliar los apunta, y contesta las dos preguntas del coordinador con dos
métodos: `faltan()`, que devuelve un número, y `terminado()`, que devuelve
`True` o `False`.

```python
l = Lote("L-204", "Ana", "lunes", 40, 25, 6)
l.faltan()        # un numero
l.terminado()     # True o False
```

> Lo que comprueba la prueba: los dos métodos, con fichas distintas. **Cómo
> guardes los datos por dentro es tu decisión** — no se mira. Y `terminado()`
> devuelve `True` o `False`, no un texto ni un número.""",
        partida='''class Lote:
    def __init__(self, codigo, anotador, dia, imagenes, anotadas, dudosas):
        ...

    def faltan(self):
        ...

    def terminado(self):
        ...''',
        solucion='''class Lote:
    def __init__(self, codigo, anotador, dia, imagenes, anotadas, dudosas):
        self.codigo = codigo
        self.anotador = anotador
        self.dia = dia
        self.imagenes = imagenes
        self.anotadas = anotadas
        self.dudosas = dudosas

    def faltan(self):
        sin_anotar = self.imagenes - self.anotadas
        return sin_anotar + self.dudosas

    def terminado(self):
        return self.faltan() == 0''',
        # Los SEIS modos de fallo estan todos aqui, en la celda visible:
        #   1. no es una clase / faltan los metodos
        #   2. faltan() se olvida de las dudosas (EL CAMINO INGENUO: restar los
        #      dos campos con pinta de total y hecho). Falla en la PRIMERA ficha.
        #   3. faltan() RESTA las dudosas en vez de sumarlas
        #   4. terminado() se olvida de las dudosas: el lote 30/30/9, que parece
        #      cerrado y no lo esta. Es el que separa de verdad.
        #   5. un lote que de verdad esta cerrado (30/30/0) da True: que el
        #      arreglo no sea «terminado() nunca es True»
        #   6. el ruido de texto cambiando el resultado
        # Las ocultas repiten estos mismos con otros numeros y otro laboratorio.
        pruebas='''assert isinstance(Lote, type), (
    "Lote tiene que ser una CLASE: la primera linea es `class Lote:`")

_l = Lote("L-204", "Ana", "lunes", 40, 25, 6)
assert callable(getattr(_l, "faltan", None)), (
    "Falta el metodo `faltan`. Va dentro de la clase, `def faltan(self):`")
assert callable(getattr(_l, "terminado", None)), (
    "Falta el metodo `terminado`. Va dentro de la clase, `def terminado(self):`")

# LA PRIMERA FICHA YA SEPARA: 40 imagenes, 25 anotadas, 6 dudosas.
_f1 = _l.faltan()
assert _f1 == 21, (
    "Este lote trae 40 imagenes y lleva 25 anotadas, asi que hay 15 que no han "
    "pasado por el anotador. Pero 6 de las anotadas quedaron marcadas como "
    "dudosas, y volver a mirarlas es trabajo del lote: a alguien le quedan 15 "
    "+ 6 = 21 imagenes por tocar. Si te sale 15, te dejaste las dudosas: una "
    "dudosa ya esta anotada, y sigue pendiente de una segunda mirada. Si te "
    "sale 9, las estas RESTANDO en vez de sumarlas. Si sale None, al metodo le "
    f"falta `return`. Tu devolviste {_f1!r}")
_t1 = _l.terminado()
assert _t1 is False, (
    "A este lote le quedan 21 imagenes por tocar, asi que no esta terminado: "
    f"se esperaba False. Tu devolviste {_t1!r}")

# EL CASO QUE DECIDE: un lote al que no le falta ninguna POR ANOTAR, y que
# tiene dudosas. Parece cerrado y no lo esta.
_dudoso = Lote("L-205", "Beto", "martes", 30, 30, 9)
_f2 = _dudoso.faltan()
assert _f2 == 9, (
    "El anotador ya paso por las 30 imagenes de este lote, asi que no queda "
    "ninguna por anotar. Pero 9 quedaron marcadas, y el lote no se cierra "
    "hasta que alguien las vuelve a mirar: quedan 9 por tocar. Si te sale 0, "
    "estas contestando solo «cuantas faltan por anotar», que no es lo que "
    f"pregunta el coordinador. Tu devolviste {_f2!r}")
_t2 = _dudoso.terminado()
assert _t2 is False, (
    "Este lote NO esta terminado: le quedan 9 dudosas que alguien tiene que "
    "volver a mirar, y el coordinador no lo cierra hasta que nadie tenga nada "
    "que hacer con el. Si te sale True, estas comparando solo las anotadas con "
    f"el total. Tu devolviste {_t2!r}")

# Y el lote que SI esta cerrado: todo anotado y ninguna marcada. Para que el
# arreglo no sea «terminado() nunca es True».
_limpio = Lote("L-206", "Caro", "miercoles", 30, 30, 0)
_f3 = _limpio.faltan()
assert _f3 == 0, (
    "30 imagenes, 30 anotadas y ninguna dudosa: no queda nada por tocar, o sea "
    f"0. Tu devolviste {_f3!r}")
_t3 = _limpio.terminado()
assert _t3 is True, (
    "Aqui nadie tiene nada que hacer con el lote, asi que esta terminado: "
    f"True. Tu devolviste {_t3!r}")

# Un lote donde TODAS las anotadas son dudosas.
_medias = Lote("L-207", "Dani", "jueves", 50, 20, 20)
_f4 = _medias.faltan()
assert _f4 == 50, (
    "50 imagenes y 20 anotadas: hay 30 sin pasar por el anotador. Y las 20 "
    "anotadas quedaron todas marcadas, asi que hay que volver a mirar 20: 30 + "
    "20 = 50 por tocar. Si te sale 30, te dejaste las dudosas; si te sale 10, "
    f"las restaste. Tu devolviste {_f4!r}")
assert _medias.terminado() is False, (
    "Con 50 imagenes por tocar no esta terminado: False")

# Un lote recien abierto, sin nada anotado y sin nada marcado.
_nuevo = Lote("L-208", "Eli", "viernes", 12, 0, 0)
_f5 = _nuevo.faltan()
assert _f5 == 12, (
    "Un lote sin nada anotado y sin nada marcado tiene las 12 por tocar. Si te "
    f"sale otra cosa, mira que estas sumando. Tu devolviste {_f5!r}")
assert _nuevo.terminado() is False, (
    "Y no esta terminado")

# EL RUIDO DE TEXTO, dicho en un assert: dos fichas con los MISMOS numeros y
# textos distintos contestan lo mismo. El codigo, el anotador y el dia no
# entran en la cuenta.
_x = Lote("L-900", "Ana", "lunes", 18, 11, 4)
_y = Lote("ZZ-1", "Zulma", "domingo", 18, 11, 4)
_fx, _fy = _x.faltan(), _y.faltan()
assert _fx == 11 and _fy == 11, (
    "Las dos fichas traen 18 imagenes, 11 anotadas y 4 dudosas, asi que las "
    "dos tienen 7 + 4 = 11 por tocar, aunque cambien el codigo, el anotador y "
    f"el dia: esos tres no entran en la cuenta. Tu devolviste {_fx!r} y {_fy!r}")
assert _x.terminado() is False and _y.terminado() is False, (
    "Y las dos estan sin terminar, por lo mismo")

# Un lote de una sola imagen, anotada y marcada: todavia hay que volver a ella.
_una = Lote("L-209", "Fabio", "sabado", 1, 1, 1)
_fu, _tu = _una.faltan(), _una.terminado()
assert _fu == 1, (
    "La unica imagen del lote esta anotada, pero quedo marcada: alguien tiene "
    "que volver a mirarla, asi que queda 1 por tocar. Si te sale 0, te dejaste "
    f"la dudosa. Tu devolviste {_fu!r}")
assert _tu is False, (
    "Y por eso NO esta terminado, aunque la unica imagen ya este anotada. "
    f"Tu devolviste {_tu!r}")
print("Las dos preguntas del coordinador salen bien en las siete fichas, dudosas incluidas.")''',
        pruebas_ocultas='''# Otro laboratorio, otros textos y otros numeros: los mismos modos de fallo.
_o = Lote("RX-77", "Mauricio", "2026-11-03", 240, 199, 58)
assert _o.faltan() == 99, (
    "41 sin anotar mas 58 marcadas: 99 por tocar")
assert _o.terminado() is False, "Todavia quedan 99"
_p = Lote("RX-78", "Noelia", "2026-11-04", 240, 240, 240)
assert _p.faltan() == 240, (
    "Un lote entero anotado y entero marcado tiene las 240 esperando una "
    "segunda mirada")
assert _p.terminado() is False, "Y no esta terminado: las dudosas lo detienen"
_p2 = Lote("RX-79", "Olga", "2026-11-05", 240, 240, 0)
assert _p2.faltan() == 0, "Todo anotado y nada marcado: no queda nada"
assert _p2.terminado() is True, "Y ese si esta terminado"
_q = Lote("RX-80", "Omar", "2026-11-06", 7, 0, 0)
assert _q.faltan() == 7 and _q.terminado() is False
# Restar las dudosas en vez de sumarlas tambien se castiga aqui.
_s = Lote("RX-81", "Pia", "2026-11-07", 90, 50, 10)
assert _s.faltan() == 50, "40 sin anotar mas 10 marcadas: 50, no 30"
# El ruido de texto, otra vez: mismos numeros, textos distintos, mismo resultado.
_r1 = Lote("A", "a", "a", 100, 100, 0)
_r2 = Lote("B-999", "Zacarias", "no se sabe", 100, 100, 0)
assert _r1.faltan() == _r2.faltan() == 0
assert _r1.terminado() is True and _r2.terminado() is True
_r3 = Lote("C", "c", "c", 100, 100, 1)
_r4 = Lote("D-1", "Yolanda", "ayer", 100, 100, 1)
assert _r3.faltan() == _r4.faltan() == 1
assert _r3.terminado() is False and _r4.terminado() is False''',
        pistas=[
            "Primero decide, sobre el papel, que numeros de la ficha contestan cada "
            "pregunta. Hay seis datos y no todos deciden; releer el parrafo de las "
            "dudosas vale mas que escribir codigo.",
            "Una imagen dudosa ya esta anotada —el anotador le puso su etiqueta y la "
            "cuenta de anotadas la recoge— y ADEMAS alguien tiene que volver a "
            "mirarla. Asi que no esta en el monton de las que faltan por anotar, "
            "pero sigue siendo trabajo del lote.",
            "`faltan()` junta dos cosas: las imagenes que todavia no pasaron por el "
            "anotador, y las que hay que volver a mirar. Y `terminado()` es cierto "
            "justo cuando eso da cero, asi que te lo puedes apoyar en `faltan()`. El "
            "codigo, el anotador y el dia guardalos si quieres, pero no los uses.",
        ],
    )

    # E3 — el segundo I4, y el de cierre. Ver el docstring.
    #
    # Por que es de 3 estrellas: junta las tres piezas del laboratorio (una
    # clase que acumula, el recorrido que elige un maximo, y leer atributos de
    # objetos) y ninguna celda las trae juntas. Y encima el criterio tiene dos
    # niveles.
    #
    # EL CAMBIO DEL 2026-11-03, y es el que sostiene la etiqueta I4. Antes el
    # enunciado DECIA la regla: «manda a leer primero el estudio que el modelo
    # marco mas alto y, si dos estan marcados igual, el que lleve mas horas
    # esperando», con el puntaje ya definido arriba como «el puntaje que le puso
    # el modelo de triaje». Eso mapea uno a uno sobre dos campos y no deja nada
    # que reconocer: un alumno que leyera solo esa frase y las firmas escribia
    # la respuesta correcta sin entender ni la radiologia ni la organizacion. Y
    # el propio enunciado presumia en negrita de «tampoco te dice que dato
    # decide» tres lineas antes de decirlo, lo que hace desconfiar al que lee
    # bien y le quema minutos buscando un truco que no existe.
    #
    # Ahora la jefa cuenta lo que le PASO y lo que no soporta —una queja por
    # dejar para la tarde uno que el triaje traia arriba; que el que llevaba
    # media manana siga esperando por uno que acaba de entrar— y no nombra
    # ningun campo como regla. El criterio y el desempate hay que sacarlos de
    # ahi, que es exactamente mCC103.
    #
    # Y el ruido numerico ya no descansa en el «numero de orden», que era flojo:
    # el enunciado tiene que decir que el numero de orden es lo que hay que
    # DEVOLVER, asi que nadie tiene que deducir que no ordena. El ruido ahora es
    # la PRIORIDAD ADMINISTRATIVA: un numero de 1 a 3, que se llama «prioridad»
    # —o sea que el nombre invita a ordenar por el—, que la aseguradora asigna
    # por contrato, y que la jefa no menciona ni una vez cuando cuenta como
    # arma la lista. Quien ordena por el lo ve en rojo en la celda visible, en
    # los dos sentidos (prioridad 1 que no gana y prioridad 3 que si gana).
    #
    # Lo que NO se exige, a proposito: ni una segunda clase para el estudio
    # —seria la segunda semana de POO—, ni como se guardan los estudios por
    # dentro. Una lista de tuplas, de diccionarios o de lo que sea pasa igual:
    # lo que se mide es el comportamiento.
    #
    # Y `siguiente()` NO consume. Si consumiera, media clase perderia los puntos
    # por un detalle de interfaz que no es lo que se esta midiendo. Esta dicho
    # en el enunciado y comprobado en la celda visible.
    c.ejercicio(
        numero=3, competencias=['I4', 'I3'], titulo="La lista de lectura del hospital",
        estrellas=3, puntos=10,
        enunciado="""Otra organización, contada igual. Aquí **tampoco se nombra el dato que
decide**: la jefa cuenta lo que hace y lo que no quiere que le vuelva a pasar,
y la regla hay que sacarla de ahí.

> En el servicio de radiología del hospital universitario, cada estudio que
> entra se apunta en una planilla con seis cosas: su **número de orden**, el
> **nombre del paciente**, la **aseguradora** que lo cubre, la **prioridad
> administrativa** que la aseguradora le pone por contrato (1, 2 o 3), las
> **horas** que lleva esperando y el **puntaje** que le puso el modelo de
> triaje — un número entre 0 y 1: cuanto más alto, más probable es que el
> estudio tenga un hallazgo urgente.
>
> La jefa del servicio arma la lista de lectura a mano, cada mañana, con la
> planilla delante. Lleva años haciéndolo y quiere dejar de hacerlo a mano.
> Cuando se le pregunta cómo la arma, no da una regla: cuenta dos cosas.
>
> «El mes pasado se me quedó para la tarde uno que el triaje traía arriba del
> todo. El hallazgo estaba ahí. Acabó en queja de la familia y en comité. De
> eso no se vuelve: desde entonces, ninguno de esos se me queda para después.»
>
> «Y lo otro que no soporto es que, cuando dos me llegan con el triaje marcado
> igual, el que ya llevaba media mañana en la sala siga esperando por uno que
> acaba de entrar.»
>
> El número de orden es el que lleva el sello del hospital y es el que la jefa
> dicta por teléfono a la sala de lectura.

Escribe la clase `ColaDeLectura`, que se crea **vacía** y tiene dos métodos:

- **`anotar(orden, paciente, aseguradora, prioridad, horas, puntaje)`** —
  apunta un estudio, con los datos en el orden de la planilla. Se llama una vez
  por estudio.
- **`siguiente()`** — devuelve el **número de orden** del estudio que toca leer
  ahora. Si no hay ninguno apuntado, devuelve `None`.

```python
cola = ColaDeLectura()
cola.anotar(101, "Ruiz", "Sanitas", 1, 2, 0.42)
cola.anotar(102, "Mejia", "Nueva EPS", 3, 9, 0.91)
cola.siguiente()      # el numero de orden de uno de los dos
```

> Tres cosas de la prueba, para que no haya sorpresas. **`siguiente()` no quita
> nada**: llamarlo dos veces seguidas da lo mismo. **Cada cola guarda sus
> estudios** — dos colas distintas no se mezclan. Y no hay dos estudios que
> coincidan en todos los números, así que la respuesta nunca es ambigua.

Cómo guardes los estudios por dentro es tu decisión; lo que se mide es el
número que sale.""",
        partida='''class ColaDeLectura:
    def __init__(self):
        ...

    def anotar(self, orden, paciente, aseguradora, prioridad, horas, puntaje):
        ...

    def siguiente(self):
        ...''',
        solucion='''class ColaDeLectura:
    def __init__(self):
        self.estudios = []

    def anotar(self, orden, paciente, aseguradora, prioridad, horas, puntaje):
        self.estudios.append((orden, horas, puntaje))

    def siguiente(self):
        mejor = None
        for estudio in self.estudios:
            if mejor is None:
                mejor = estudio
            elif estudio[2] > mejor[2]:
                mejor = estudio
            elif estudio[2] == mejor[2] and estudio[1] > mejor[1]:
                mejor = estudio
        if mejor is None:
            return None
        return mejor[0]''',
        # Los NUEVE modos de fallo, todos en la celda visible. El orden de la
        # celda esta elegido para que cada fallo se diagnostique con SU mensaje:
        #   1. no es una clase / faltan los metodos
        #   2. la cola vacia no da None
        #   3. dos colas comparten la lista (`estudios = []` escrito en el
        #      cuerpo de la clase y no dentro de __init__). VA DE PRIMERO, antes
        #      de que `_c` acumule nada: si la lista es compartida, cualquier
        #      assert posterior contesta con estudios de otra cola y su mensaje
        #      manda al alumno a arreglar un desempate que ya estaba bien.
        #   4. con uno solo, no lo devuelve
        #   5. el triaje no manda (manda el orden de llegada, o el numero de
        #      orden creciente, o decreciente, o las horas, o la prioridad)
        #   6. el empate de triaje no se resuelve por horas — y se comprueba en
        #      los DOS ordenes de insercion, porque «me quedo con el primero que
        #      encuentro» solo falla en uno de los dos
        #   7. siguiente() consume
        #   8. el criterio de dos niveles aplanado en una conjuncion
        #      (`puntaje >= mejor and horas >= mejor`), que es la lectura
        #      literal de «el mas alto, y si empatan el que mas horas». Para que
        #      falle hace falta un estudio que deba ganar llevando MENOS horas
        #      que el que va ganando, y con el de muchas horas apuntado PRIMERO.
        #   9. el acumulador del maximo arrancado en 0 en vez de en None. Para
        #      que falle hacen falta los DOS ceros: puntaje 0.0 y 0 horas.
        # Las ocultas repiten estos mismos con otra planilla y otros numeros.
        #
        # Y todos los asserts guardan el valor en una variable ANTES de
        # comparar: llamar a `siguiente()` otra vez dentro del f-string informa
        # del resultado de la TERCERA llamada, que para una solucion que consume
        # no es el que fallo.
        pruebas='''assert isinstance(ColaDeLectura, type), (
    "ColaDeLectura tiene que ser una CLASE: la primera linea es "
    "`class ColaDeLectura:`")

_c = ColaDeLectura()
assert callable(getattr(_c, "anotar", None)), (
    "Falta el metodo `anotar`. Va dentro de la clase y recibe los seis datos "
    "de la planilla, despues de `self`")
assert callable(getattr(_c, "siguiente", None)), (
    "Falta el metodo `siguiente`. Va dentro de la clase, `def siguiente(self):`")

_s0 = _c.siguiente()
assert _s0 is None, (
    "Una cola recien creada esta vacia y no hay nada que leer: se esperaba "
    "None. Si aqui salta un error, `__init__` no dejo la cola en un estado "
    f"usable (una lista vacia, por ejemplo). Tu devolviste {_s0!r}")

# ESTO VA DE PRIMERO A PROPOSITO: cada cola tiene que guardar SUS estudios. Si
# la lista esta escrita en el cuerpo de la clase, hay una sola para todas, y
# entonces cualquier prueba de mas abajo contestaria con estudios de otra cola
# y su mensaje te mandaria a arreglar un desempate que ya tienes bien.
_f = ColaDeLectura()
_g = ColaDeLectura()
_f.anotar(401, "Esguerra", "Nueva EPS", 2, 1, 0.99)
_sg = _g.siguiente()
assert _sg is None, (
    "Cada cola guarda SUS estudios: en esta no se apunto nada, asi que sigue "
    "vacia y la respuesta es None. Si te sale 401, que se apunto en OTRA cola, "
    "tienes la lista escrita en el cuerpo de la clase en vez de dentro de "
    "`__init__`, y entonces hay UNA sola lista para todas las colas (es el "
    f"error de la nota de 4B). Tu devolviste {_sg!r}")
_sf = _f.siguiente()
assert _sf == 401, (
    "Y la cola donde si se apunto contesta lo suyo: el 401. "
    f"Tu devolviste {_sf!r}")

_c.anotar(101, "Ruiz", "Sanitas", 1, 2, 0.42)
_s1 = _c.siguiente()
assert _s1 == 101, (
    "Con un solo estudio apuntado, el que toca leer es ese, y lo que se "
    "devuelve es su NUMERO DE ORDEN: 101. Si te sale None, `anotar` no esta "
    "guardando nada; si te sale una tupla o un objeto, devuelve solo el "
    f"numero. Tu devolviste {_s1!r}")

_c.anotar(102, "Mejia", "Nueva EPS", 3, 9, 0.91)
_s2 = _c.siguiente()
assert _s2 == 102, (
    "El triaje marco el 102 en 0.91 y el 101 en 0.42: toca el 102, aunque se "
    "apunto despues. Si te sale 101, estas devolviendo el primero que se "
    f"apunto. Tu devolviste {_s2!r}")

# Empate de triaje: el que lleva mas horas. Aqui el que gana se apunto ANTES.
_c.anotar(103, "Torres", "Sura", 1, 1, 0.91)
_s3 = _c.siguiente()
assert _s3 == 102, (
    "El 102 y el 103 estan marcados igual (0.91), asi que decide quien lleva "
    "mas horas en la sala: el 102 lleva 9 y el 103 lleva 1. Se esperaba 102. "
    "Si te sale 103, puede que tu desempate se quede con el ultimo que "
    "encuentra; y puede que `siguiente()` quitara el 102 de la cola en la "
    f"llamada anterior, que solo tiene que consultar. Tu devolviste {_s3!r}")

# Un estudio con MUCHAS horas y triaje bajo: las horas no mandan, desempatan.
# Y de paso, con los cuatro apuntados el 104 es el numero de orden mas alto y
# el 101 el mas bajo, y no toca ninguno de los dos.
_c.anotar(104, "Lopez", "Sanitas", 1, 20, 0.10)
_s4 = _c.siguiente()
assert _s4 == 102, (
    "El 104 lleva 20 horas esperando, mas que nadie, y aun asi no es el que "
    "toca: el triaje lo marco en 0.10. Las horas no mandan, solo DESEMPATAN. "
    "Y si te sale 104 o 101, estas ordenando por el numero de orden: ese es el "
    "sello del hospital y es lo que hay que DEVOLVER, no lo que decide. "
    f"Se esperaba 102 y tu devolviste {_s4!r}")

# siguiente() no consume: dos llamadas seguidas dan lo mismo.
_s5a, _s5b = _c.siguiente(), _c.siguiente()
assert _s5a == 102 and _s5b == 102, (
    "Llamar a `siguiente()` dos veces seguidas tiene que dar lo mismo: solo "
    "CONSULTA la cola, no quita el estudio. Si la segunda te da otra cosa, tu "
    f"metodo esta borrando. Tu devolviste {_s5a!r} y despues {_s5b!r}")

# EL TRIAJE MANDA AUNQUE EL CANDIDATO LLEVE MENOS HORAS QUE EL QUE VA GANANDO.
# El de triaje bajo y muchas horas se apunta PRIMERO: ese orden es lo que
# importa, porque es el que lo deja de titular.
_h = ColaDeLectura()
_h.anotar(201, "Nieto", "Compensar", 1, 30, 0.12)
_h.anotar(202, "Pardo", "Sura", 3, 1, 0.88)
_s6 = _h.siguiente()
assert _s6 == 202, (
    "El 201 lleva 30 horas esperando y el 202 solo 1, pero el triaje marco el "
    "202 en 0.88 contra 0.12: toca el 202. Las horas NO son un requisito, solo "
    "desempatan cuando el triaje marca igual. Si te sale 201, tu condicion le "
    "esta exigiendo al nuevo tener TAMBIEN mas horas que el que va ganando: "
    f"ahi va un `or`, no un `and`. Tu devolviste {_s6!r}")

# Triaje 0.0 y 0 horas, con un solo estudio: sigue siendo el que toca. Hacen
# falta los DOS ceros para que falle el acumulador arrancado en 0.
_i = ColaDeLectura()
_i.anotar(501, "Rojas", "Sanitas", 2, 0, 0.0)
_s7 = _i.siguiente()
assert _s7 == 501, (
    "Es el unico estudio apuntado, asi que toca ese, aunque el triaje lo "
    "marcara en 0.0 y lleve 0 horas esperando. Si te sale None, arrancaste la "
    "busqueda del mejor en 0 (`mejor_puntaje = 0`) y un 0.0 no le gana a un 0: "
    "arranca con `mejor = None` y toma el primer estudio como el mejor que "
    f"tienes, como en 4A. Tu devolviste {_s7!r}")

# LA PRIORIDAD ADMINISTRATIVA NO DECIDE, y se comprueba en los dos sentidos:
# aqui el que toca trae la prioridad mas alta (3) y el que no toca trae la 1.
_j = ColaDeLectura()
_j.anotar(601, "Soto", "Coosalud", 1, 2, 0.20)
_j.anotar(602, "Tamayo", "Sanitas", 3, 2, 0.70)
_s8 = _j.siguiente()
assert _s8 == 602, (
    "El 601 trae prioridad administrativa 1 y el 602 trae 3, y aun asi toca el "
    "602: el triaje lo marco en 0.70 contra 0.20. Esa prioridad la pone la "
    "aseguradora por contrato, y la jefa no la nombra ni una vez cuando cuenta "
    f"como arma la lista. Tu devolviste {_s8!r}")

# Empate otra vez, pero ahora el que gana se apunto DESPUES. Quien se queda con
# «el primero que encuentro» pasa el caso de arriba y falla este. Y el que gana
# trae la prioridad administrativa mas alta, para que tampoco valga usarla.
_d = ColaDeLectura()
_d.anotar(301, "Arias", "Coosalud", 1, 2, 0.60)
_d.anotar(302, "Bravo", "Famisanar", 3, 8, 0.60)
_s9 = _d.siguiente()
assert _s9 == 302, (
    "Los dos estan marcados en 0.60, y el 302 lleva 8 horas contra 2 del 301: "
    "toca el 302, aunque se apunto despues y aunque su prioridad "
    "administrativa sea 3. Si te sale 301, tu desempate se queda con el "
    f"primero que encuentra. Tu devolviste {_s9!r}")

# Y el caso en que el que toca es el de numero de orden MAS BAJO y se apunto
# ultimo: ni «el mayor orden» ni «el ultimo apuntado» valen.
_k = ColaDeLectura()
_k.anotar(710, "Cano", "Sura", 1, 5, 0.33)
_k.anotar(705, "Duran", "Sanitas", 2, 5, 0.77)
_s10 = _k.siguiente()
assert _s10 == 705, (
    "El 705 esta marcado en 0.77 y el 710 en 0.33: toca el 705, que tiene el "
    f"numero de orden mas BAJO. Tu devolviste {_s10!r}")
print("La cola prioriza bien: el triaje manda, las horas desempatan, y ni el numero de orden ni la prioridad administrativa deciden.")''',
        pruebas_ocultas='''# Otra planilla: otro servicio, otros numeros, los mismos modos de fallo.
_o = ColaDeLectura()
assert _o.siguiente() is None, "Vacia sigue siendo None"
_o.anotar(5001, "Quintero", "Compensar", 1, 30, 0.12)
_o.anotar(5002, "Rico", "Sura", 2, 1, 0.88)
_o.anotar(5003, "Salas", "Sanitas", 3, 12, 0.88)
_o.anotar(5004, "Tobon", "Coosalud", 1, 40, 0.05)
assert _o.siguiente() == 5003, (
    "5002 y 5003 estan marcados igual (0.88) y el 5003 lleva 12 horas contra 1: "
    "toca el 5003")
assert _o.siguiente() == 5003, "Y sigue tocando: siguiente() no consume"
_o.anotar(5005, "Uribe", "Famisanar", 3, 0, 0.95)
assert _o.siguiente() == 5005, (
    "El 5005 esta marcado en 0.95, mas que nadie, aunque lleve 0 horas "
    "esperando: el triaje manda")
# El triaje gana llevando MENOS horas, con el de muchas horas apuntado primero.
_t = ColaDeLectura()
_t.anotar(6001, "Vega", "Sura", 1, 48, 0.21)
_t.anotar(6002, "Wills", "Sanitas", 3, 2, 0.64)
assert _t.siguiente() == 6002, (
    "0.64 contra 0.21: el triaje manda aunque el 6002 lleve 2 horas y el 6001 "
    "lleve 48")
# Empate resuelto por horas, con el ganador apuntado primero y despues.
_p = ColaDeLectura()
_p.anotar(1, "a", "x", 1, 9, 0.5)
_p.anotar(2, "b", "y", 3, 3, 0.5)
assert _p.siguiente() == 1, "Empate: gana el de 9 horas, apuntado primero"
_q = ColaDeLectura()
_q.anotar(1, "a", "x", 3, 3, 0.5)
_q.anotar(2, "b", "y", 1, 9, 0.5)
assert _q.siguiente() == 2, "Empate: gana el de 9 horas, apuntado despues"
# Un solo estudio, marcado en 0.0 y con 0 horas: el mismo modo del visible.
_u = ColaDeLectura()
_u.anotar(99999, "Vargas", "Sura", 2, 0, 0.0)
assert _u.siguiente() == 99999, "Con uno solo, toca ese, con el triaje que sea"
# La prioridad administrativa no decide, en los dos sentidos.
_w = ColaDeLectura()
_w.anotar(7001, "Yepes", "Sura", 1, 1, 0.30)
_w.anotar(7002, "Zapata", "Sanitas", 3, 1, 0.80)
assert _w.siguiente() == 7002, "La prioridad 1 no gana: decide el triaje"
_w2 = ColaDeLectura()
_w2.anotar(7003, "Abad", "Sura", 3, 1, 0.80)
_w2.anotar(7004, "Bueno", "Sanitas", 1, 1, 0.30)
assert _w2.siguiente() == 7003, "Ni la prioridad 3 pierde por ser 3"
# Tres colas a la vez, sin mezclarse.
_a, _b, _c2 = ColaDeLectura(), ColaDeLectura(), ColaDeLectura()
_a.anotar(10, "a", "x", 1, 1, 0.9)
_b.anotar(20, "b", "y", 2, 1, 0.9)
assert _a.siguiente() == 10 and _b.siguiente() == 20 and _c2.siguiente() is None, (
    "Cada cola, la suya")
# El ruido de texto no decide: mismos numeros, textos distintos, misma respuesta.
_r1 = ColaDeLectura()
_r2 = ColaDeLectura()
_r1.anotar(7, "Perez", "Sanitas", 1, 4, 0.3)
_r1.anotar(8, "Gomez", "Sura", 2, 2, 0.6)
_r2.anotar(7, "Zapata", "Coosalud", 1, 4, 0.3)
_r2.anotar(8, "Nieto", "Famisanar", 2, 2, 0.6)
assert _r1.siguiente() == _r2.siguiente() == 8, (
    "El paciente y la aseguradora no deciden nada")''',
        pistas=[
            "Antes de escribir nada, decide cual de los seis datos de la planilla "
            "ordena la lista, cual se usa solo cuando hay empate, y cuales no "
            "deciden aunque sean numeros. Las dos cosas que cuenta la jefa son las "
            "dos que no quiere que le pasen: de ahi sale el criterio.",
            "La cola es una clase que acumula, como la `Bitacora` del laboratorio: "
            "en `__init__` una lista vacia —dentro de `__init__`, no fuera— y en "
            "`anotar` un `.append(...)` con lo que te haga falta de cada estudio.",
            "`siguiente()` es el recorrido del maximo del laboratorio, con un "
            "escalon mas: empiezas con `mejor = None`, y un estudio le gana al "
            "mejor que tengas si su puntaje es mayor, O si su puntaje es igual y "
            "sus horas son mas. Fijate en ese «o»: al nuevo no se le pide ganar en "
            "las dos cosas a la vez. Al final devuelve el numero de orden del "
            "mejor, o None si no habia ninguno.",
        ],
    )

    # =========================================================================
    c.seccion(6, "Habla con el asistente", 1, """**Cinco preguntas** para todo el cuadernillo.""")

    c.md("""No gastes ninguna en «¿cómo se escribe un método?»: eso está en la figura de las
cinco piezas. Guárdalas para `ColaDeLectura`, y pregunta con los datos delante
— un `print` de lo que guardaste en la lista te dice si el problema está en
`anotar` o en `siguiente`.

Mal: «mi cola no pasa la prueba».
Bien: «mi `siguiente` devuelve 101 y la prueba espera 102. Guardo los estudios
con `append` y recorro comparando `puntaje`. ¿Por qué se queda con el primero?»
""")

    # =========================================================================
    c.seccion(7, "Cierre", 1, """Dos preguntas que nadie corrige.""")

    c.md("""- En `Lote`, la ficha traía seis datos y las dos respuestas salían de dos. Si
  mañana el coordinador pregunta «¿cuántas dudosas hay que revisar?», ¿cambia la
  clase o solo se le añade un método?
- `ColaDeLectura` guarda estudios dentro. ¿Qué tendría de bueno que cada estudio
  fuera **también** un objeto, con su propia clase, en vez de lo que guardaste tú?

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **Clase** | El molde: `class Lote:`. No es un lote, es de lo que salen |
| **Instancia** / objeto | Uno concreto, salido del molde: `Lote("L-204", ...)` |
| **Atributo** | Un dato pegado a una instancia: `self.imagenes` |
| `__init__` | Lo que corre al crear una instancia y guarda sus atributos |
| `self` | La instancia a la que le estás pidiendo el método. En la llamada no se escribe |
| **Método** | Un `def` dentro de la clase, que usa los atributos de `self` |
| `__repr__` | El texto con que se ve el objeto al imprimirlo |
""")

    return c
