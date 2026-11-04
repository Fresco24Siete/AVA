#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 9: «Archivos y arreglos».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 9 — Persistencia y computación numérica.

25 puntos de nbgrader en tres ejercicios (5/10/10), 5 XP y la insignia «Quien
persiste». ~30 minutos, teoría breve y ejercicios, con la pauta del 2026-09-22.

De dónde sale el contenido (planeación 41333, semana 9)
------------------------------------------------------
Clase 1: excepciones, `try-except-else-finally`, validación, archivos de texto,
lectura, escritura y manejo seguro de recursos. Clase 2: arreglos NumPy, forma,
dimensiones, indexación, operaciones vectorizadas, comparación conceptual con
listas y ciclos, matrices y álgebra lineal básica. El resultado esperado:
«construye programas robustos con archivos y excepciones, y utiliza arreglos
NumPy para operaciones numéricas vectorizadas».

EL ORDEN: archivos y excepciones PRIMERO, NumPy después. No es arbitrario. Un
conjunto de datos vive en un archivo, y lo primero que le pasa a cualquiera que
va a entrenar algo es que lo carga y descubre que una fila está mal. Así que el
cuadernillo entra por ahí —un archivo normal, es decir sucio— y NumPy llega
cuando ya hay datos que meterle. Al revés, las excepciones serían una ceremonia
de sintaxis sin un problema detrás.

EL PUENTE, que es el regalo de esta semana
------------------------------------------
En la SEMANA 7 el alumno recorrió matrices a mano con ciclos anidados y escribió
él mismo el máximo por columna (su ejercicio de 2★) y la transposición (su 3★).
NumPy hace las dos en `a.max(axis=0)` y `a.T`. Así se presenta aquí: no como una
librería nueva que hay que aprender, sino como **su propio trabajo de hace dos
semanas devuelto en una línea**. `ver_antes_despues()` lo pone lado a lado, y es
la pieza que justifica la segunda mitad del cuadernillo.

De ahí sale también la «comparación conceptual con listas y ciclos» que pide la
planeación, y se puede MEDIR: `time.perf_counter()` sobre una lista grande
frente al mismo cálculo vectorizado. El número habla solo y no hay que
argumentarlo. Pero se mide en una celda de LABORATORIO y nunca en una prueba:
el tiempo depende de la máquina del alumno y de lo que tenga abierto, así que un
assert sobre tiempos suspendería a gente que lo hizo bien.

TRES LÍMITES que se respetan y que hay que tener presentes al editarlo
---------------------------------------------------------------------
- **`try/except` es nuevo.** Se presenta con el error que el alumno ya conoce de
  memoria —`ValueError` al pasarle «3,5» o «NA» a `float()`— y no con una
  excepción abstracta. La coma decimal no es un ejemplo de laboratorio: en
  Colombia es la forma normal de escribir un decimal, así que todo archivo
  exportado de una hoja de cálculo local trae esa trampa.
- **El intérprete de pseudocódigo del curso no sirve para nada de esto.**
  `Dimension`, `Funcion` y compañía están en la tabla `_NO_TENGO` de
  `motor/pseudo_uis.py`, y de excepciones no tiene ni rastro. Igual que en las
  semanas 6, 7 y 8: esta semana no carga `pseudo_uis.py` y todo lo calificable
  es Python. Se dice dentro del cuadernillo para que nadie pierda media hora.
- **Nada de matplotlib.** La imagen lo trae y funciona, pero la planeación de
  esta semana no pide ninguna gráfica (pide archivos, excepciones y arreglos), y
  una gráfica cuesta minutos del presupuesto de ~30 sin medir nada de hoy.

Lo que NO se finge medir
------------------------
De la clase 1 queda **fuera de los ejercicios** el archivo binario: se nombra en
el glosario como algo que existe y que no se usa esta semana, y ningún objetivo
lo promete. De la clase 2 queda fuera el **tiempo** medido, por lo dicho arriba:
se ejecuta, se mira y no se califica. Y el taller presencial —la aplicación de
registro y consulta— no se autocalifica; está en el cierre como lo que es.

MICROCOMPETENCIAS
-----------------
I3 (mCC87, «identifica variables y aspectos del problema para armar el
algoritmo») en los tres, que es lo que la planeación pone transversal de la
semana 2 a la 12. En `a_numero` el aspecto es *qué puede fallar y qué se
devuelve cuando falla*; en `limpiar_archivo`, *qué es una fila válida* —el
alumno tiene que darse cuenta de que la prueba de validez ES el intento de
conversión, no una revisión de caracteres escrita a mano—; en
`escalar_columnas`, *sobre qué eje se calcula cada estadística*, que es el
`axis=0` y es el error de la semana.

I1 (mCP17, «aplica conocimientos matemáticos») solo en `escalar_columnas`. La
planeación pone mCP17 con evidencia en las semanas 9 y 10, y ahí está: el mínimo
y el máximo por eje, y un reescalado afín de cada columna a [0, 1], que es la
normalización que se le aplica a un conjunto de datos antes de entrenar
cualquier cosa. En los otros dos no hay matemáticas y no se etiqueta: un
ejercicio sin etiqueta es válido y honesto, e inflar la cobertura de I1 la
vuelve inútil para lo único que sirve, que es saber dónde se midió de verdad.

FUERA DE ALCANCE, y por eso no se etiquetan aunque la planeación las nombre en
esta semana: mCC85 (complejidad e impacto económico y ambiental) —el cuadernillo
mide tiempos en el laboratorio, pero medir no es analizar complejidad, y no hay
ejercicio que lo evalúe—; mCP88 (uso de fuentes confiables), que no se puede
medir con una celda de prueba; y mCC103, que no corresponde a esta semana.

OJO con el número de unidad
---------------------------
La planeación 41333 tiene solo CUATRO unidades y la Unidad 3 abarca de la semana
3 a la 10: para esta semana dice «Unidad 3. Persistencia y computación
numérica». Pero los cuadernillos publicados usan unidad = semana desde la 4
(«Unidad 7», «Unidad 8»), así que aquí se sigue esa convención —«Unidad 9»— para
que el alumno no vea un salto y lo reporte como error. El NOMBRE del tema sí es
el de la planeación, literal. Está explicado largo en el docstring de la semana
7; corregir los números de verdad implica tocar semanas ya publicadas y es
decisión del profesor, no de aquí.

AVISO para quien edite: los ejercicios de esta semana ESCRIBEN ARCHIVOS en la
carpeta de trabajo (`medidas_s9.txt` en el laboratorio, `s9_*.txt` en las
pruebas). Todos se abren en modo `"w"`, que reescribe desde cero, así que
ejecutar una celda dos veces da lo mismo que ejecutarla una — y eso importa,
porque el alumno reintenta y el autocalificador corre el cuadernillo entero otra
vez. Si alguien cambia un `"w"` por un `"a"`, la segunda ejecución falla.
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
        codigo="semana_09",
        titulo="Archivos y arreglos",
        semana=9,
        meta_xp=5,
        insignia="Quien persiste",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[os.path.join(AQUI, "contenido.py")],
    )

    c.md("""# Archivos y arreglos
### Semana 9 · Unidad 9 · Persistencia y computación numérica

Ya escribiste un archivo en la semana 1 —`bitacora_semana1.txt`, que sigue en tu
carpeta—, así que sabes que lo guardado en disco sobrevive al kernel. Esta
semana escribes otro y lo recorres **línea por línea** para procesarlo, porque
todo archivo de verdad trae alguna fila mala y hay que conseguir que un error
**no detenga** el programa. Después llega NumPy.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    # Revisados uno por uno al final, contra lo que el cuadernillo trae de
    # verdad (trampa 3 del §4): el binario NO está aquí, porque solo se nombra
    # en el glosario; los tiempos SÍ, porque hay una celda que los mide; el
    # producto matriz-vector NO, porque se ve pasar y no se practica.
    c.md("""## Al terminar este cuadernillo vas a poder…

- Convertir un texto a número **sin que el programa se caiga** si no es un
  número: `try` / `except ValueError`.
- Decir qué bloque de un `try` / `except` / `else` / `finally` corre cuando algo
  falla y cuál cuando no.
- **Escribir** un archivo, **leerlo** línea por línea y quedarte solo con las
  líneas que sirven.
- Pasar una lista de listas a **arreglo NumPy** y leer su **forma** y una
  **columna** entera sin un solo ciclo.
- Hacer en una línea el máximo por columna y la transposición que en la semana 7
  te costaron dos ciclos anidados. Y **medir** cuánto más rápido es.
- **Escalar** una columna entera con una sola operación.

**Un aviso:** el pseudocódigo del curso no tiene arreglos ni excepciones; aquí
todo es Python. Son **25 puntos** y **5 XP**; la insignia, «Quien persiste».
""")

    # =========================================================================
    c.seccion(1, "Calentamiento", 1, """Una de la semana 7. Sin nota: da XP.""")
    c.code("quiz_columna()")

    # =========================================================================
    # El gancho: el problema antes de la sintaxis (§3 del documento de recorte).
    # Primero el archivo sucio, después el error que ya conoce, y solo entonces
    # la palabra `try`.
    c.seccion(2, "Un archivo de verdad está sucio", 2, """Alguien midió una temperatura siete veces y guardó las medidas. Ejecuta y mira
lo que quedó en el archivo:""")

    c.code("ver_archivo_sucio()")

    c.md("""Tres de siete no se pueden convertir, y ese archivo no está roto: así llegan
todos. Ejecuta y mira el error que ya conoces de memoria:
""")

    # La etiqueta `error-sembrado` es la convención de la semana 01 para las
    # celdas que enseñan un error rompiendo código adrede: verificar.py exige
    # que SIGAN fallando, porque una celda que deja de dar el error convierte en
    # mentira la explicación de al lado.
    c.code('''# Esta celda falla adrede. Lee el nombre del error y lo que dice.
float("3,5")''', etiquetas=("error-sembrado",))

    c.md("""`ValueError: could not convert string to float: '3,5'`. Una coma decimal, que es
como escribe los decimales cualquier hoja de cálculo en Colombia.

Lo importante no es el error: es **dónde para**. Si pasa en la fila 3 de un
archivo de mil, las otras 997 no se procesan.
""")

    # =========================================================================
    c.seccion(3, "Que el error no detenga el programa", 4, """La herramienta se llama **excepción**, y son cuatro palabras.""")

    c.md("""Un `try` dice «intenta esto, y si revienta no te mueras: ve al `except`».
Ejecuta y mira lo que pasa con las siete medidas, y después con los dos bloques
que le faltan:
""")

    # Las dos demostraciones en una sola celda: el ciclo con try/except y, justo
    # debajo, la funcion que ensena `else` y `finally`. Van juntas porque el
    # presupuesto de la semana no da para dos celdas y porque lo que de verdad
    # explica el `finally` no es el texto sino el ORDEN de las lineas que
    # imprime, que se lee de un tiron en una salida sola.
    c.code('''crudas = ["21.4", "19.8", "3,5", "22.1", "NA", "", "20.6"]

buenas = []
descartadas = 0
for texto in crudas:
    try:
        buenas.append(float(texto))     # lo que puede fallar
    except ValueError:                  # el plan B, solo para ESE error
        descartadas = descartadas + 1

print(buenas)
print("descartadas:", descartadas, "de", len(crudas))


# Los dos bloques que faltan: `else` y `finally`. Y de paso, VALIDAR: no basta
# con que el dato se pueda convertir, tambien tiene que tener sentido.
def validar(texto):
    """Devuelve DOS cosas (como en la semana 8): el valor y el motivo."""
    try:
        numero = float(texto)
    except ValueError:
        return None, "no es un numero"
    else:
        # El `else` corre SOLO si el try no fallo. Aqui ya hay numero, asi que
        # tiene sentido preguntar si es una temperatura creible.
        if numero < -90 or numero > 60:
            return None, "fuera del rango de temperaturas"
        return numero, "ok"
    finally:
        # El `finally` corre SIEMPRE: con error, sin error, y hasta con return.
        print("  revisado:", repr(texto))

for dato in ["21.4", "siete", "500"]:
    valor, motivo = validar(dato)
    print("   ->", valor, "|", motivo)''')

    c.md("""Las cuatro buenas pasaron y las tres malas no detuvieron nada. Y `except
ValueError` nombra **el error concreto**: si algún día aparece otro, te enteras
en vez de taparlo.

Mira ahora el final de la salida: el `finally` se imprime en los dos casos,
**incluso después del `return`**. Por eso es donde se cierra lo que quedó
abierto. Esta tabla lo resume:
""")

    c.code("ver_flujo_try()")

    c.md("""Y **validar**, que es la palabra que usa el temario, no es más que esto: antes
de usar un dato, intentar convertirlo y decidir qué hacer si no se puede.
""")

    # =========================================================================
    c.seccion(4, "Archivos: escribir y volver a leer", 3, """Vuelves al `with open(...)` de la semana 1, ahora recorriendo el archivo **línea
por línea**. Eso y el `\\n` pegado al final de cada una es lo nuevo; el resto es
repaso.""")

    c.md("""Tres pasos: **abrir**, **hacer algo**, **cerrar**. El `with` cierra por ti
aunque algo falle en medio —igual que el `finally`—, y por eso se usa siempre.
El modo `"w"` escribe y reescribe desde cero; el `"r"` lee. Cada línea termina
en `\\n`.
""")

    c.code('''medidas = ["21.4", "19.8", "3,5", "22.1", "NA", "", "20.6"]

with open("medidas_s9.txt", "w", encoding="utf-8") as archivo:
    for texto in medidas:
        archivo.write(texto + "\\n")

with open("medidas_s9.txt", "r", encoding="utf-8") as archivo:
    print(archivo.read())

# Y asi se procesa: linea por linea, como una lista.
with open("medidas_s9.txt", "r", encoding="utf-8") as archivo:
    for linea in archivo:
        print(repr(linea), "->", len(linea), "caracteres")''')

    c.md("""Mira el `repr`: cada línea **se trae su `\\n` pegado**. Es la sorpresa de la
semana, y sale gratis: `float("21.4\\n")` funciona —`float` aguanta los espacios
y los saltos de los extremos— y `float("\\n")` lanza `ValueError`, que es lo que
quieres que haga una línea vacía.
""")

    # =========================================================================
    c.seccion(5, "NumPy: la semana 7, en una línea", 4, """Ya tienes datos cargados. Ahora las cuentas.""")

    c.md("""Un **arreglo** de NumPy es una tabla de números con una diferencia que lo cambia
todo: las operaciones se le aplican **entera**, de un golpe, sin que tú escribas
el ciclo. Se llama **vectorizar**.
""")

    c.code('''import numpy as np

m = [[12, 5, 1], [9, 7, 0], [15, 3, 1], [8, 6, 0]]
a = np.array(m)              # la lista de listas se convierte en arreglo

print(a)
print("forma:", a.shape)     # (filas, columnas) — los dos len de la semana 7, juntos
print("dimensiones:", a.ndim)
print("una celda:", a[2, 0])  # fila 2, columna 0. Antes: m[2][0]
print("la columna 0:", a[:, 0])   # los dos puntos significan "todas las filas"''')

    c.md("""`a[:, 0]` es la columna entera, y en la semana 7 eso era un ciclo. Compara:
""")

    c.code("ver_antes_despues()")

    c.md("""Las operaciones se aplican a todo el arreglo a la vez. `axis=0` significa **una
respuesta por columna**; `axis=1`, una por fila.
""")

    c.code('''print("por columna, el maximo:  ", a.max(axis=0))
print("por columna, el minimo:  ", a.min(axis=0))
print("por columna, el promedio:", a.mean(axis=0))
print()
print("transponer, que en la semana 7 te costo dos ciclos anidados:")
print(a.T)
print()
print("el doble de todo:")
print(a * 2)
print()
print("centrar: a cada valor se le quita el promedio de SU columna")
print(a - a.mean(axis=0))
print()
pesos = np.array([0.5, 2.0, 10.0])
print("matriz por vector, un puntaje por fila:", a @ pesos)''')

    c.md("""Párate en el centrado. `a.mean(axis=0)` son **tres** números y `a` tiene
**doce**: NumPy estira los tres a lo ancho de las cuatro filas y resta cada uno
en su columna. Se llama **difusión**, y es lo que te deja transformar una tabla
entera sin un índice a la vista.

Y la última línea: `@` multiplica matrices. Le da a cada característica un peso
y devuelve un número por fila. Esa operación —matriz por vector— está debajo de
casi todo lo que calcula un modelo, y vuelve más adelante en el curso.
""")

    c.md("""### ¿Y de verdad es más rápido?

Mídelo. `time.perf_counter()` es un reloj en segundos: la diferencia entre dos
lecturas es lo que tardó lo de en medio.
""")

    c.code('''import time

n = 500000
lista = list(range(n))
arreglo = np.arange(n)

inicio = time.perf_counter()
total = 0
for x in lista:
    total = total + x
con_ciclo = time.perf_counter() - inicio

inicio = time.perf_counter()
total_np = arreglo.sum()
con_numpy = time.perf_counter() - inicio

print("mismo resultado:", total == total_np)
print("con un ciclo de Python:", round(con_ciclo, 4), "s")
print("con NumPy vectorizado:", round(con_numpy, 6), "s")
print("veces mas rapido:", round(con_ciclo / con_numpy))''')

    c.md("""Tu número depende de tu máquina, pero el orden de magnitud no cambia: el ciclo
de Python revisa en cada vuelta de qué tipo es el número que va a sumar, y el
arreglo tiene un solo tipo para todo y baja a código compilado. Mismo cálculo y
misma respuesta; la diferencia es **quién escribe el ciclo**.
""")

    # =========================================================================
    # Sin números de ejercicio en la prosa (trampa 2 del §4): se nombran las
    # funciones, que no cambian de nombre al cambiar de sitio.
    c.seccion(6, "Tres ejercicios", 22, """**25 puntos**, de menos a más. `a_numero` convierte un dato, `limpiar_archivo`
convierte un archivo entero, y `escalar_columnas` hace cuentas sobre lo que
quedó.""")

    # Por qué el de 1★ es la conversión suelta y no algo más grande:
    #
    # `try/except` es la primera estructura nueva en tres semanas, y la rampa
    # tiene que medir SOLO eso: ningún archivo, ningún ciclo, ninguna
    # estructura. Si falla, falla por lo que se está enseñando y el alumno lo
    # sabe al instante. Y la pieza que sale de aquí es la que `limpiar_archivo`
    # necesita dentro, así que el de 2★ arranca con medio camino hecho.
    #
    # Los casos de la prueba son los del archivo del gancho, con otros números:
    # la coma decimal, el texto y la línea vacía. No hay nada que copiar de la
    # teoría, porque la celda del laboratorio los mete en una LISTA con un ciclo
    # y aquí lo que se pide es una función que recibe UN texto.
    c.ejercicio(
        numero=1, competencias=['I3'], titulo="Convertir sin caerse", estrellas=1, puntos=5,
        enunciado="""Escribe `a_numero(texto)`: recibe un texto y

- devuelve el **número** (un `float`) si el texto se puede convertir,
- devuelve `None` si no se puede.

Y lo importante: **no se cae nunca**. Pase lo que pase devuelve algo y el
programa sigue.

```python
a_numero("21.4")    # 21.4
a_numero("3,5")     # None — coma decimal
a_numero("NA")      # None
a_numero("")        # None
```

> Ojo con la tentación de revisar el texto a mano para decidir si «parece» un
> número: hay más formas de escribir uno de las que vas a pensar (`-4`, `1e3`,
> `  7.5  ` con espacios) y las fallarías todas. La forma de saber si `float`
> puede convertirlo es **pedirle que lo convierta** y estar listo para que no
> pueda. Eso es lo que se mide aquí.""",
        partida='''def a_numero(texto):
    ...''',
        solucion='''def a_numero(texto):
    try:
        return float(texto)
    except ValueError:
        return None''',
        # Las pruebas VISIBLES cubren TODOS los modos de fallo que comprueban
        # las ocultas (trampa 4 del §4), y esto costó una revisión: faltaban
        # tres y eran justo los que distinguen «intentar la conversión» de
        # «revisar el texto a mano», que es lo único que mide el ejercicio.
        #   - el punto («21.4») y el signo («-4»), que tumban un `isdigit`;
        #   - los espacios de los extremos («  7.5  »);
        #   - el CERO, porque quien escriba `return float(texto) or None`, o
        #     filtre con un `if`, devuelve None para el 0 y aprueba todo lo
        #     demás;
        #   - la notación científica («1e3»), que el propio enunciado nombra y
        #     que un validador de caracteres escrito a mano rechaza;
        #   - y «12.5.6», que tiene todos sus caracteres de número y no es un
        #     número: es el caso que demuestra que mirar el texto no basta.
        #   - y «3.5 grados», el que costo la segunda revision: empieza por un
        #     numero y no lo es, asi que `float(texto.split()[0])` aprobaba las
        #     diez visibles y suspendia solo al calificar.
        # Las ocultas repiten los mismos modos con otros valores, que es para
        # lo que sirven, y ninguna estrena uno nuevo. Comprobado recorriendo
        # las ocultas una por una contra las visibles.
        pruebas='''assert callable(a_numero), "a_numero debe ser una funcion"
assert a_numero("21.4") == 21.4, (
    'a_numero("21.4") se esperaba 21.4. ¿Tu funcion DEVUELVE el numero con '
    "return? Y si estas revisando el texto a mano, el punto decimal no es un "
    "digito: `\\"21.4\\".isdigit()` es False")
assert a_numero("-4") == -4.0, (
    'a_numero("-4") se esperaba -4.0: el signo menos tambien forma parte de un '
    "numero")
assert a_numero("3,5") is None, (
    'a_numero("3,5") se esperaba None, porque float no entiende la coma '
    "decimal. Si aqui te salta un ValueError, te falta el try/except; si te "
    "devuelve 0, estas devolviendo el numero equivocado")
assert a_numero("NA") is None, 'a_numero("NA") se esperaba None'
assert a_numero("") is None, (
    'a_numero("") se esperaba None: un texto vacio no es un numero')
assert a_numero("  7.5  ") == 7.5, (
    'a_numero("  7.5  ") se esperaba 7.5: float aguanta los espacios de los '
    "extremos, y por eso conviene dejarle a el la decision")
assert a_numero("0") == 0.0, (
    'a_numero("0") se esperaba 0.0: el cero es un numero, igual que cualquier '
    "otro, y lo que se devuelve es 0.0 y no None")
assert a_numero("1e3") == 1000.0, (
    'a_numero("1e3") se esperaba 1000.0: la notacion cientifica tambien es un '
    "numero y float la entiende sin problema. Si aqui te sale None es porque "
    "estas revisando los caracteres del texto en vez de intentar la conversion")
assert a_numero("3.5 grados") is None, (
    'a_numero("3.5 grados") se esperaba None: el texto empieza por un numero '
    "pero no ES un numero. Si aqui te devuelve 3.5, estas partiendo el texto y "
    "convirtiendo solo el primer trozo; lo que se pide es convertir el texto "
    "COMPLETO o rendirse")
assert a_numero("   ") is None, (
    'a_numero("   ") se esperaba None: solo espacios no es un numero')
assert a_numero("12.5.6") is None, (
    'a_numero("12.5.6") se esperaba None: todos sus caracteres son de numero y '
    "aun asi no es un numero, porque lleva dos puntos decimales. Solo float "
    "sabe decidir esto bien")
print("Convierte lo que se puede y devuelve None con lo que no, sin caerse.")''',
        pruebas_ocultas='''assert a_numero("0") == 0.0, "El cero es un numero: 0.0, no None"
assert a_numero("2E-2") == 0.02, "La notacion cientifica tambien es un numero"
assert a_numero("-0.25") == -0.25
assert a_numero("21.4\\n") == 21.4, (
    "Con el salto de linea pegado tambien, que es como llega leyendo un archivo")
assert a_numero("   ") is None, "Solo espacios no es un numero"
assert a_numero("1.2.3") is None, "Dos puntos decimales no son un numero"
assert a_numero("3.5 grados") is None
assert isinstance(a_numero("7"), float), "Devuelve un float, no un texto"''',
        pistas=[
            "Dos bloques: `try:` con la conversion dentro, y `except ValueError:` "
            "debajo con lo que se hace si no se pudo.",
            "El `return` puede ir dentro del `try`: si `float(texto)` funciona, "
            "devuelve ahi mismo y no se llega al `except`.",
            "En el `except` va `return None`. Y nombra el error, "
            "`except ValueError:`, en vez de un `except:` pelado: asi, si algun dia "
            "aparece otro error distinto, te enteras en vez de taparlo.",
        ],
    )

    # Por qué este ejercicio junta las dos mitades en vez de solo leer:
    #
    # El resultado esperado de la semana dice «programas robustos CON ARCHIVOS y
    # excepciones», y la evidencia que pide la planeación es «aplicación
    # persistente con pruebas de excepción». Un ejercicio que solo lee un
    # archivo que le dan hecho no es persistencia: es lectura. Aquí el alumno
    # abre en `"r"`, decide qué sirve y vuelve a abrir en `"w"` — las tres cosas
    # que hace cualquier paso de limpieza de datos.
    #
    # Y no se puede copiar de la teoría. En el laboratorio hay un ciclo con
    # try/except SOBRE UNA LISTA, y por otro lado un `with open` que escribe y
    # lee SIN ninguna validación. Aquí hay que juntarlos, que es trabajo de
    # verdad y no transcripción (trampa 6 del §4).
    #
    # Dónde está el I3: en darse cuenta de que «fila válida» no se decide
    # mirando los caracteres, sino intentando la conversión. El enunciado se
    # cuida de NO decir «usa try»: dice la regla y deja que el alumno vea que
    # la prueba de validez es el intento. Quien escriba un validador a mano
    # falla con el negativo, que está en la prueba visible.
    c.ejercicio(
        numero=2, competencias=['I3'], titulo="Dejar solo lo que sirve", estrellas=2, puntos=10,
        enunciado="""Ahora el archivo entero. Escribe
`limpiar_archivo(ruta_entrada, ruta_salida)`:

1. Lee `ruta_entrada` **línea por línea**: trae un número por línea, y algunas
   no lo son.
2. Una línea **sirve** si se puede convertir a número; si no, se descarta sin
   detener nada.
3. **Devuelve** la lista de los que sirven, en el orden en que aparecían.
4. Y los deja **escritos** en `ruta_salida`, uno por línea.

Con un archivo que contenga `21.4`, `19.8`, `3,5` y `22.1`, una por línea, la
llamada devuelve `[21.4, 19.8, 22.1]` y deja esos tres en `ruta_salida`. La
prueba reabre tu salida y convierte lo que escribiste, así que el formato exacto
da igual mientras sea un número por línea.

> **Abre la salida en modo `"w"`**, que reescribe desde cero. Con `"a"`, que
> añade al final, la segunda vez que ejecutes la celda saldrían los números
> repetidos — y vas a ejecutarla varias veces.

Para probar a mano tienes `medidas_s9.txt`, que creaste en el laboratorio.""",
        partida='''def limpiar_archivo(ruta_entrada, ruta_salida):
    ...''',
        solucion='''def limpiar_archivo(ruta_entrada, ruta_salida):
    numeros = []
    with open(ruta_entrada, "r", encoding="utf-8") as entrada:
        for linea in entrada:
            try:
                numeros.append(float(linea))
            except ValueError:
                pass

    with open(ruta_salida, "w", encoding="utf-8") as salida:
        for numero in numeros:
            salida.write(str(numero) + "\\n")

    return numeros''',
        # El fixture lo escribe la prueba, no el alumno: asi no depende de que
        # haya ejecutado el laboratorio ni del orden en que corra el
        # autocalificador. Se abre en "w", de modo que ejecutar la celda dos
        # veces deja exactamente el mismo archivo.
        #
        # DOS cosas del fixture son deliberadas, y las dos son trampa 4 del §4:
        #
        # - El CERO. Reusar `a_numero` del ejercicio anterior y filtrar con
        #   `if v:` descarta el 0.0, porque 0.0 es falso; y ese es el camino al
        #   que el cuadernillo EMPUJA, porque el ejercicio anterior devuelve
        #   None al fallar. Sin un cero aqui, ese error pasa todo lo visible y
        #   suspende solo al calificar: 10 puntos en silencio. Costo una
        #   revision entera.
        # - Que la ULTIMA linea sea valida y SIN salto final: es el off-by-one
        #   de esta semana. Quien procese `read()` partiendo por "\\n" y
        #   descarte el ultimo trozo, o quien se pare una linea antes, lo ve
        #   aqui y no al calificar.
        pruebas='''import os

_entrada = "s9_entrada.txt"
_salida = "s9_salida.txt"
with open(_entrada, "w", encoding="utf-8") as _f:
    _f.write("21.4\\n19.8\\n3,5\\n22.1\\nNA\\n\\n   \\n0\\n-3.5")

# La salida se borra ANTES de llamar: si no, un intento anterior deja el
# archivo escrito y una solucion que lee y filtra bien pero NO escribe pasa
# esta capa apoyandose en un archivo rancio (costo la segunda revision).
if os.path.exists(_salida):
    os.remove(_salida)

assert callable(limpiar_archivo), "limpiar_archivo debe ser una funcion"
_r = limpiar_archivo(_entrada, _salida)
assert isinstance(_r, list), (
    "Se esperaba que DEVOLVIERAS la lista de los numeros que sirven. "
    f"Tu funcion devolvio {type(_r).__name__}")
assert _r == [21.4, 19.8, 22.1, 0.0, -3.5], (
    "De ese archivo sirven cinco lineas y se esperaba "
    "[21.4, 19.8, 22.1, 0.0, -3.5], en ese orden. "
    f"Tu funcion devolvio {_r!r}.\\n"
    "  - Si te falta el 0.0: `if numero:` descarta el cero, porque 0.0 es "
    "falso en Python. Lo que hay que preguntar es si HAY numero, y eso se "
    "escribe `if numero is not None:`.\\n"
    "  - Si te falta el -3.5: es la ULTIMA linea y no termina en salto de "
    "linea, igual que el final de cualquier archivo. No la dejes fuera.\\n"
    "  - Si te sobra algo: la coma decimal, las letras, la linea vacia y la de "
    "solo espacios no se pueden convertir, asi que ninguna sirve.\\n"
    "  - Si te salta un ValueError: la linea mala tiene que descartarse, no "
    "detener la funcion")
assert os.path.exists(_salida), (
    f"No encuentro {_salida}. La funcion tambien tiene que ESCRIBIR los "
    'numeros buenos: abrela con open(ruta_salida, "w", encoding="utf-8")')
with open(_salida, "r", encoding="utf-8") as _f:
    _escritas = [l for l in _f.read().split("\\n") if l.strip()]
assert len(_escritas) == 5, (
    f"En {_salida} se esperaban 5 lineas con un numero cada una y encontre "
    f"{len(_escritas)}. ¿Le pusiste el salto de linea a cada una?")
assert [float(l) for l in _escritas] == _r, (
    f"Lo que escribiste en {_salida} no son los mismos numeros que devuelves. "
    f"Escribiste {_escritas!r} y devolviste {_r!r}")
# Dos veces seguidas tiene que dar lo mismo: el alumno reintenta y el
# autocalificador vuelve a correr la celda.
assert limpiar_archivo(_entrada, _salida) == _r, (
    "Llamarla dos veces da un resultado distinto. ¿Abriste la salida en modo "
    '"a" (anadir) en vez de "w" (reescribir)?')
with open(_salida, "r", encoding="utf-8") as _f:
    assert len([l for l in _f.read().split("\\n") if l.strip()]) == 5, (
        f"Tras llamarla dos veces, {_salida} tiene las lineas repetidas: "
        'abrela en modo "w", que reescribe desde cero')
# Un archivo donde NADA sirve: la lista vacia tambien es una respuesta. Se
# reusan los dos mismos nombres, reescritos: asi esta celda no te llena la
# carpeta de archivos de prueba.
with open(_entrada, "w", encoding="utf-8") as _f:
    _f.write("NA\\nsin dato\\n\\n")
assert limpiar_archivo(_entrada, _salida) == [], (
    "Si ninguna linea sirve, se devuelve la lista vacia, []")
assert os.path.exists(_salida), (
    "El archivo de salida se crea igual, aunque quede vacio")
print("Lee, descarta lo que no sirve, devuelve y escribe. Y dos veces da lo mismo.")''',
        # Todos los casos reusan el MISMO par de archivos, reescrito cada vez
        # en modo "w": el ejercicio deja dos ficheros en la carpeta del alumno,
        # no una docena, y volver a correr la celda da lo mismo.
        pruebas_ocultas='''def _sembrar(texto):
    with open(_entrada, "w", encoding="utf-8") as _f:
        _f.write(texto)


_sembrar("1\\n2.5\\nabc\\n-7\\n0\\n")
assert limpiar_archivo(_entrada, _salida) == [1.0, 2.5, -7.0, 0.0], (
    "El cero sirve: es un numero como cualquier otro")
with open(_salida, "r", encoding="utf-8") as _f:
    assert [float(l) for l in _f.read().split("\\n") if l.strip()] == [
        1.0, 2.5, -7.0, 0.0]
# Un archivo de una sola linea, y valida.
_sembrar("42.0")
assert limpiar_archivo(_entrada, _salida) == [42.0]
# Y uno vacio del todo.
_sembrar("")
assert limpiar_archivo(_entrada, _salida) == []
assert os.path.exists(_salida)
# El orden es el del archivo, no uno ordenado.
_sembrar("9\\n1\\nx\\n5\\n")
assert limpiar_archivo(_entrada, _salida) == [9.0, 1.0, 5.0], (
    "Se devuelven en el orden en que aparecen, sin ordenarlos")
_t = limpiar_archivo(_entrada, _salida)
assert all(isinstance(_v, float) for _v in _t), "Son numeros, no textos"''',
        pistas=[
            "Son dos bloques `with open(...)` seguidos, como en el laboratorio: uno "
            "en modo \"r\" para leer y otro en modo \"w\" para escribir. En medio, una "
            "lista que empieza vacia.",
            "El ciclo que lee es `for linea in entrada:`. Para decidir si la linea "
            "sirve, no la mires: intenta convertirla con `float(...)` dentro de un "
            "`try`, y en el `except ValueError` no hagas nada (`pass` vale).",
            "Para escribir, otro ciclo sobre la lista que te quedo: "
            "`salida.write(str(numero) + \"\\n\")`. El salto de linea es lo que hace "
            "que cada numero caiga en su propia linea. Y el `return` de la lista va "
            "al final, fuera de los dos `with`.",
        ],
    )

    # Por qué el de 3★ es un reescalado por columna y no un promedio:
    #
    # Un promedio por columna es `a.mean(axis=0)` y ya está escrito en el
    # laboratorio: se resolvería copiando una línea. El reescalado obliga a
    # combinar cuatro cosas —convertir la lista en arreglo, el mínimo y el
    # máximo POR EJE, la resta difundida y la división— y ninguna celda del
    # cuadernillo lo tiene junto. El laboratorio enseña la difusión CENTRANDO
    # (restar el promedio), que es otra transformación igual de estándar: el
    # alumno tiene que ver que el mínimo se usa igual que el promedio y que
    # además hay que dividir. Eso es transferir, no copiar.
    #
    # Dónde está el I1: el mínimo y el máximo por eje y un reescalado afín de
    # cada columna al intervalo [0, 1]. Es la normalización que se le hace a un
    # conjunto de datos antes de entrenar, y es matemáticas de verdad, no una
    # cuenta de adorno.
    #
    # Dónde está el I3: en el EJE. El error de la semana es escalar con el
    # mínimo y el máximo de toda la tabla en vez de los de cada columna, y las
    # dos pruebas por columna lo cazan. Identificar sobre qué se calcula cada
    # estadística es exactamente mCC87.
    #
    # La restricción «sin for» es la lección, no un capricho, y por eso va en la
    # prueba VISIBLE. Ojo: `sin_usar(f, "for")` mira el ÁRBOL, así que tapa
    # también las por-comprensión; es lo que se quiere. Y no es la restricción
    # por NOMBRE que se retiró de la semana 7 (`sin_usar(f, "sum")` rechazaba a
    # quien llamara `sum` a una variable): aquí se prohíbe una estructura, que no
    # se puede cumplir por accidente ni incumplir por el nombre de una variable.
    c.ejercicio(
        numero=3, competencias=['I3', 'I1'], titulo="Escalar cada columna", estrellas=3, puntos=10,
        enunciado="""Las columnas de un conjunto de datos vienen en unidades distintas: una va de 0 a
3 y la de al lado, de 0 a 50.000, y casi cualquier modelo le hace más caso a la
segunda solo por ser más grande. El arreglo: **escalar** cada columna para que
todas vayan de 0 a 1.

Escribe `escalar_columnas(datos)` — **la cabecera también**, que esta vez la
plantilla no te la da: `def escalar_columnas(datos):`, con ese nombre exacto.
Recibe una **lista de listas** de números y devuelve un **arreglo NumPy** de la
misma forma, donde cada valor se sustituye por

> el valor **menos el mínimo de su columna**, dividido entre el **recorrido** de
> su columna (su máximo menos su mínimo).

Así el mínimo de cada columna queda en **0** y el máximo, en **1**.

```python
escalar_columnas([[10, 1], [20, 3], [30, 2]])
# [[0.  0. ]
#  [0.5 1. ]
#  [1.  0.5]]
```

La primera columna es 10, 20 y 30: mínimo 10, recorrido 20, así que el 10 queda
en 0, el 30 en 1 y el 20 en medio. Cada columna se escala **con sus propios**
mínimo y máximo, no con los de toda la tabla.

Y tiene que funcionar con **cualquier número de columnas** —una, dos, tres o
diez—, no con las dos del ejemplo. No las resuelvas una por una: `axis=0` las
hace todas a la vez, sean las que sean.

> **La restricción: ni un `for`.** Ni ciclo ni por-comprensión. Con ciclos has
> vuelto a escribir la semana 7, y la gracia de un arreglo es que esto son
> cuatro operaciones sobre la tabla entera. La prueba lo comprueba.

Y da por hecho que ninguna columna tiene todos sus valores iguales, así que el
recorrido nunca es cero. La lista que recibes no se modifica: `np.array(...)` ya
te da una copia.""",
        # La plantilla NO trae el `def`, y eso es deliberado. `sin_usar` mira el
        # arbol de la CELDA y se queda con la PRIMERA definicion que encuentra
        # con ese nombre (`_definiciones_de` usa `setdefault`). Si la plantilla
        # trajera `def escalar_columnas(datos):` con un cuerpo `...`, la celda
        # del alumno acabaria con DOS definiciones —la de la plantilla y la
        # suya— y la restriccion se comprobaria contra el `...`: es decir, no se
        # comprobaria nada y una solucion con ciclos aprobaria. Comprobado:
        # pasaba. Dejando solo el import, en la celda hay una unica definicion
        # —la del alumno— y la restriccion muerde.
        #
        # El precio es que esta celda se queda sin la guarda «ejecuta TU celda»
        # (build.py lo avisa, porque de la plantilla no sale un nombre), asi que
        # la prueba trae la suya escrita a mano, mas abajo, con el nombre exacto
        # que hay que escribir.
        partida='''import numpy as np''',
        solucion='''def escalar_columnas(datos):
    a = np.array(datos, dtype=float)
    minimos = a.min(axis=0)
    recorridos = a.max(axis=0) - minimos
    return (a - minimos) / recorridos''',
        # numpy se importa tambien aqui: la celda de prueba tiene que correr
        # aunque alguien le borre el import de arriba al pegar su respuesta.
        #
        # Las pruebas VISIBLES cubren los TRES modos de fallo que importan y
        # que las ocultas repiten (trampa 4 del §4):
        #   - escalar con el minimo y el maximo de TODA la tabla en vez de los
        #     de cada columna. Las dos columnas de `_d` tienen minimos y
        #     maximos distintos entre si, asi que con un solo numero global
        #     ninguna de las dos sale bien;
        #   - hacerlo por filas, `axis=1`, que lo cazan las dos comprobaciones
        #     de min y max por columna;
        #   - y resolver un numero FIJO de columnas, que es lo que faltaba y
        #     costo una revision: con un solo caso visible de dos columnas,
        #     escalar la 0 y la 1 a mano y juntarlas con `.T` cumplia la
        #     restriccion, pasaba todo lo visible y suspendia al calificar. De
        #     ahi el caso de tres columnas y el de una sola, los dos visibles.
        pruebas='''import numpy as np

# Esta celda no lleva la guarda automatica «ejecuta TU celda» (la plantilla no
# define ningun nombre, por lo explicado arriba), asi que va escrita aqui.
assert "escalar_columnas" in globals(), (
    "No encuentro `escalar_columnas`. Ejecuta primero TU celda (la de arriba, "
    "donde va tu respuesta) y despues esta. Y escribe la funcion con ese nombre "
    "exacto: def escalar_columnas(datos):")
assert callable(escalar_columnas), "escalar_columnas debe ser una funcion"
sin_usar(escalar_columnas, "for")

_d = [[12, 5], [9, 7], [15, 3], [8, 6]]
_r = escalar_columnas(_d)
assert isinstance(_r, np.ndarray), (
    "Se esperaba un arreglo de NumPy. Convierte la lista de listas con "
    f"np.array(datos) y devuelve el resultado de la cuenta. Tu funcion "
    f"devolvio {type(_r).__name__}")
assert _r.shape == (4, 2), (
    f"La forma tiene que ser la misma que entro, (4, 2), y la tuya es {_r.shape}")
# Columna 0: minimo 8, maximo 15, recorrido 7.
assert np.allclose(_r[:, 0], [4 / 7, 1 / 7, 1.0, 0.0]), (
    "La columna 0 es 12, 9, 15, 8: su minimo es 8 y su recorrido 7, asi que "
    "tiene que quedar [0.571, 0.143, 1.0, 0.0]. Si no te sale, lo mas probable "
    "es que estes usando el minimo y el maximo de TODA la tabla: cada columna "
    "se escala con los suyos, y eso es lo que hace axis=0.\\n"
    f"  Tu columna 0 quedo en {_r[:, 0]}")
# Columna 1: minimo 3, maximo 7, recorrido 4. Otros numeros que la columna 0, de
# modo que un minimo global no puede acertar las dos.
assert np.allclose(_r[:, 1], [0.5, 1.0, 0.0, 0.75]), (
    "La columna 1 es 5, 7, 3, 6: su minimo es 3 y su recorrido 4, asi que tiene "
    "que quedar [0.5, 1.0, 0.0, 0.75].\\n"
    f"  Tu columna 1 quedo en {_r[:, 1]}")
assert np.allclose(_r.min(axis=0), [0.0, 0.0]), (
    "Despues de escalar, el minimo de CADA columna tiene que ser 0 y el tuyo es "
    f"{_r.min(axis=0)}. Si usaste axis=1, escalaste por filas en vez de por "
    "columnas")
assert np.allclose(_r.max(axis=0), [1.0, 1.0]), (
    "Y el maximo de CADA columna tiene que ser 1; el tuyo es "
    f"{_r.max(axis=0)}")
assert _d == [[12, 5], [9, 7], [15, 3], [8, 6]], (
    "La lista que te pasan no se toca: np.array(datos) ya te da una copia para "
    "trabajar")

# TRES columnas, y de escalas disparatadas: es el caso del enunciado, el que
# motiva el ejercicio. Y es el que distingue operar por EJE de resolver la
# columna 0 y la 1 una por una: lo segundo cumple la restriccion y aun asi esta
# mal, porque la funcion tiene que servir para cualquier numero de columnas.
_g = [[0, 0, 0], [1, 100, 50000], [2, 200, 100000]]
_rg = escalar_columnas(_g)
assert _rg.shape == (3, 3), (
    "Con tres columnas la forma tiene que seguir siendo la que entro, (3, 3), y "
    f"la tuya es {_rg.shape}. La funcion tiene que servir para CUALQUIER numero "
    "de columnas: si estas escalando la columna 0 y la 1 por separado y "
    "juntandolas, con tres se te cae. `axis=0` las hace todas a la vez, sean "
    "las que sean")
assert np.allclose(_rg, [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.0, 1.0, 1.0]]), (
    "Esas tres columnas van de 0 a 2, de 0 a 200 y de 0 a 100000, y despues de "
    "escalar las tres tienen que quedar en [0, 0.5, 1]: para eso sirve "
    f"escalar. Tu resultado fue\\n{_rg}")
# Y el otro extremo, una sola columna.
assert np.allclose(escalar_columnas([[4], [8], [6]]), [[0.0], [1.0], [0.5]]), (
    "Con una sola columna tambien: [[4], [8], [6]] se escala a "
    "[[0.0], [1.0], [0.5]]. Si aqui te salta un IndexError, estas yendo a "
    "buscar columnas por su indice en vez de operar sobre la tabla entera")
print("Cada columna escalada con sus propios minimo y maximo, sean dos o diez, "
      "y sin un solo for.")''',
        pruebas_ocultas='''import numpy as np

sin_usar(escalar_columnas, "for")
_e = escalar_columnas([[10, 1], [20, 3], [30, 2]])
assert np.allclose(_e, [[0.0, 0.0], [0.5, 1.0], [1.0, 0.5]]), (
    "El ejemplo del enunciado")
# Con negativos y decimales: el minimo negativo se resta igual.
_n = [[-5.0, 2.0], [-1.0, 10.0], [-3.0, 6.0]]
_rn = escalar_columnas(_n)
assert np.allclose(_rn, [[0.0, 0.0], [1.0, 1.0], [0.5, 0.5]]), (
    "Con valores negativos tambien: restar un minimo negativo suma")
assert _n == [[-5.0, 2.0], [-1.0, 10.0], [-3.0, 6.0]]
# Tres columnas de rangos muy distintos, que es el caso que motiva el ejercicio.
_g = [[0, 0, 0], [1, 100, 50000], [2, 200, 100000]]
_rg = escalar_columnas(_g)
assert _rg.shape == (3, 3), (
    "La forma que entra es la que sale: con tres columnas, (3, 3). La funcion "
    "tiene que servir para cualquier numero de columnas")
assert np.allclose(_rg, [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.0, 1.0, 1.0]]), (
    "Tres columnas con escalas muy distintas acaban las tres entre 0 y 1")
# Una sola columna.
assert np.allclose(escalar_columnas([[4], [8], [6]]), [[0.0], [1.0], [0.5]]), (
    "Con una sola columna tambien")
# Y muchas: cinco columnas, para que no quede duda de que no hay un numero
# magico de columnas metido en la solucion.
_m5 = [[1, 10, 100, 1000, 10000], [3, 30, 300, 3000, 30000],
       [2, 20, 200, 2000, 20000]]
assert np.allclose(escalar_columnas(_m5),
                   [[0.0] * 5, [1.0] * 5, [0.5] * 5]), (
    "Con cinco columnas igual: no hay un numero de columnas fijo")
# Y el resultado es de decimales, no de enteros: la division lo exige.
assert _rg.dtype.kind == "f", "El resultado son decimales"''',
        pistas=[
            "Primero convierte: `a = np.array(datos, dtype=float)`. Lo demas se hace "
            "sobre `a`, nunca sobre `datos`.",
            "El minimo de cada columna es `a.min(axis=0)` y el maximo, "
            "`a.max(axis=0)`. Los dos son una fila de numeros, uno por columna: el "
            "recorrido es su resta.",
            "La cuenta entera cabe en una linea: `(a - minimos) / recorridos`. NumPy "
            "estira esas filas de numeros a lo ancho de todas las filas de `a` —la "
            "difusion del laboratorio— y cada columna se escala con los suyos. Si lo "
            "estas haciendo con ciclos, no es que este mal: es que la restriccion lo "
            "prohibe y la prueba te lo dira.",
        ],
    )

    # =========================================================================
    c.seccion(7, "Habla con el asistente", 1, """**Cinco preguntas** para todo el cuadernillo.""")

    c.md("""No gastes ninguna en «¿por qué me da `ValueError`?»: eso lo contesta el propio
error, que dice qué valor no pudo convertir. Guárdalas para `escalar_columnas`,
donde el resultado sale con la forma correcta y los números mal.

Mal: «no me funciona NumPy».
Bien: «mi `escalar_columnas` devuelve la forma correcta, pero el mínimo de la
segunda columna me sale 0.4 y debería ser 0. ¿Qué diferencia hay entre
`a.min()` y `a.min(axis=0)`?»
""")

    # =========================================================================
    c.seccion(8, "Cierre", 1, """Dos preguntas que nadie corrige, y lo que te llevas al taller.""")

    c.md("""- Un `except ValueError` tapa ese error y ninguno más. Si el archivo que abres
  **no existe**, el error no es `ValueError`: ¿querrías que `limpiar_archivo` lo
  tapara también, o que te avisara?
- `a.min()` y `a.min(axis=0)` no devuelven lo mismo ni la misma **cantidad** de
  números. ¿Sabrías decir en una frase qué devuelve cada uno?

### Lo que te llevas al taller

Un **laboratorio**: una aplicación que registra y consulta datos con
persistencia y manejo de errores, y esos datos convertidos a arreglos para
comparar el cálculo con ciclos contra el vectorizado. Lleva corriendo tu
`limpiar_archivo`: es por donde entran los datos.

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **Excepción** | Un error que interrumpe el programa. `ValueError` es uno |
| `try` / `except` | Intenta algo y, si da ese error, haz el plan B en vez de morir |
| `else` / `finally` | Corre solo si **no** falló / corre **siempre** |
| **Validar** | Comprobar que un dato sirve antes de usarlo |
| `with open(...)` | Abre un archivo y lo **cierra** al salir, aunque algo falle |
| **Modo** `"r"` / `"w"` | Leer / escribir desde cero. Hay uno **binario** para lo que no es texto: no lo usas esta semana |
| **Persistencia** | Que los datos sobrevivan al programa, porque están en el disco |
| **Arreglo** (NumPy) | Tabla de números de un solo tipo, que se opera entera de un golpe |
| **Forma** (`shape`) | Cuántas filas y columnas tiene, en una tupla |
| **Vectorizar** | Aplicar la operación al arreglo completo, sin escribir el ciclo |
| `axis=0` / `axis=1` | Una respuesta por **columna** / una por **fila** |
| **Difusión** | Que una fila de números se estire sobre todas las filas de la tabla |
| **Escalar** una columna | Llevarla entera al intervalo de 0 a 1, con su mínimo y su máximo |
""")

    return c
