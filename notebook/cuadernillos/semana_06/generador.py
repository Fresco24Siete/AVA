#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 6: «Buscar y ordenar».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 6 — Colecciones lineales, búsqueda y ordenamiento.

65 puntos de nbgrader en seis ejercicios, 95 XP y la insignia «Quien ordena».
Es el más exigente de los seis, y a propósito: cierra la primera mitad.

Dos límites que se respetan y se dicen en voz alta dentro del cuadernillo:

- **El intérprete de pseudocódigo del curso no maneja listas.** Así que aquí el
  pseudocódigo se escribe y se lee —como pide el temario— pero no se ejecuta, y
  todo lo calificable es Python. Se avisa en la sección 4 para que nadie pierda
  media hora peleando con el motor.
- **De los cuatro ordenamientos, el estudiante escribe dos.** Selección y
  burbuja se implementan; merge sort y quicksort se explican y se **miden**,
  pero no se piden. Son recursivos y la recursión no se ha enseñado: exigirlos
  rompería la regla de no usar lo que no se ha visto. Medirlos, en cambio, sí se
  puede, y es donde está la lección que de verdad importa.
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
        codigo="semana_06",
        titulo="Buscar y ordenar",
        semana=6,
        meta_xp=95,
        insignia="Quien ordena",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[os.path.join(AQUI, "contenido.py")],
    )

    c.md("""# Buscar y ordenar
### Semana 6 · Unidad 6 · Colecciones lineales, búsqueda y ordenamiento

Hasta ahora cada variable guardaba **un** dato. Esta semana aprendes a guardar
muchos en una sola, y a hacer con ellos las dos operaciones que sostienen media
informática: **buscar** y **ordenar**.

Y vas a ver, midiéndolo, por qué dos programas que hacen lo mismo pueden costar
uno veinte pasos y el otro un millón.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Crear una **lista**, leer cualquier elemento por su **índice** y cambiarlo.
- Recorrer una lista entera, por índice y de forma directa.
- Escribir una **búsqueda lineal** y una **búsqueda binaria**, y decir qué
  condición hay que cumplir para poder usar la segunda.
- Escribir el ordenamiento de **burbuja**, y leer el de **selección** para ver
  que son la misma familia.
- Explicar, con números en la mano, por qué un algoritmo puede ser mil veces más
  caro que otro dando el mismo resultado.

**Un aviso sobre el pseudocódigo:** el intérprete del curso maneja variables
sueltas, no listas. Así que esta semana el pseudocódigo se lee y se escribe en
papel, pero no lo ejecutes en el motor — no te va a funcionar y no es culpa
tuya. Todo lo que se califica va en Python.

Este cuadernillo tiene **65 puntos** y **95 XP**. La insignia se llama
«Quien ordena».
""")

    # =========================================================================
    c.seccion(1, "Calentamiento", 4, """Tres de la semana pasada.""")
    c.code("quiz_input()")
    c.code("quiz_division()")
    c.code("quiz_estructura()")

    # =========================================================================
    c.seccion(2, "Un nombre entre mil", 4, """Tienes la lista de los 30.000 estudiantes de la UIS, ordenada alfabéticamente,
y buscas uno.

Si la miras uno por uno desde el principio, en el peor caso das 30.000 pasos.
Si haces lo que hace cualquiera con un directorio de papel —abrir por la mitad y
descartar la mitad que sobra— das **quince**.

No es una mejora del doble. Es de dos mil veces. Ejecuta y míralo:""")

    c.code("comparar_busquedas(1000)")

    c.md("""Esa diferencia es de lo que trata la segunda mitad del cuadernillo. Pero antes
hay que aprender a guardar muchos datos en una variable.
""")

    # =========================================================================
    c.seccion(3, "Concepto en corto", 14, """Listas y cadenas. Son lo mismo por dentro: una fila de casillas numeradas.""")

    c.md("""### 3A. La lista y sus índices

Una **lista** guarda varios valores en orden, entre corchetes:

```python
notas = [4.0, 3.5, 2.8, 4.8]
```

Cada casilla tiene un número, su **índice**. Y aquí está el detalle que cuesta:
**se empieza a contar en cero**. Ejecuta y míralo dibujado:
""")

    c.code('''notas = [4.0, 3.5, 2.8, 4.8]
ver_lista(notas, resaltar=0, titulo="notas[0] es la PRIMERA, no la segunda")''')

    c.md("""```python
notas[0]    # 4.0  — la primera
notas[3]    # 4.8  — la cuarta y última
notas[4]    # IndexError: no existe
len(notas)  # 4    — cuántas hay
```

> **El error por uno.** Una lista de 4 elementos tiene índices 0, 1, 2 y 3. El
> índice 4 **no existe** y pedirlo revienta el programa con `IndexError`. El
> último índice siempre es `len(lista) - 1`.

### 3B. Las listas se pueden cambiar

Una lista es **mutable**: puedes cambiarle un elemento después de crearla.
""")

    c.code('''notas = [4.0, 3.5, 2.8, 4.8]
notas[2] = 3.9                    # el 2.8 se convierte en 3.9
print("Ahora la lista es:", notas)''')

    c.md("""Esa mutabilidad es justo lo que hace posible ordenar: los algoritmos de esta
semana no construyen una lista nueva, **mueven los elementos de la que ya
tienes**.

De todo lo que se le puede pedir a una lista, esta semana solo necesitas una
cosa, y ya la has visto: `len(lista)`, que dice cuántos elementos tiene.

### 3C. Recorrer

Con `for` y `range` ya sabes. Pero como la lista sabe cuántos elementos tiene,
se puede recorrer **directamente**, que es más corto y más difícil de romper:

```python
# Con indices — te sirve cuando necesitas saber la POSICIÓN
for i in range(len(notas)):
    print(i, notas[i])

# Directo — te sirve cuando solo te importa el VALOR
for nota in notas:
    print(nota)
```
""")

    c.code('''notas = [4.0, 3.5, 2.8]

print("Con indices:")
for i in range(len(notas)):
    print("  posicion", i, "->", notas[i])

print("Directo:")
for nota in notas:
    print("  ", nota)''')

    # =========================================================================
    c.seccion(4, "Laboratorio", 26, """Las dos búsquedas y los cuatro ordenamientos. Recuerda: el pseudocódigo de esta
sección es para leerlo, no para ejecutarlo — el motor del curso no maneja listas.""")

    c.md("""### 4A. Búsqueda lineal

La obvia: mirar uno por uno desde el principio hasta encontrarlo.

**Pseudocódigo** (para leer, no para ejecutar)

```
Para cada posición i de la lista
    Si lista[i] = buscado Entonces
        Devolver i
    FinSi
FinPara
Devolver -1     // no está
```

**Python**
""")

    c.code('''def buscar_lineal(datos, buscado):
    for i in range(len(datos)):
        if datos[i] == buscado:
            return i
    return -1

nombres = ["Ana", "Bruno", "Carlos", "Diana"]
print("Carlos esta en la posicion", buscar_lineal(nombres, "Carlos"))
print("Zoe esta en la posicion", buscar_lineal(nombres, "Zoe"), "(-1 = no esta)")''')

    c.md("""Funciona **siempre**, esté la lista ordenada o no. Ese es su valor. Su precio:
en el peor caso mira todos los elementos.

### 4B. Búsqueda binaria, y su precondición

La lista se parte por la mitad. Si el del medio es mayor que lo que buscas,
descartas toda la mitad de arriba de un golpe. Y repites.

> **La precondición.** La búsqueda binaria **solo funciona si la lista está
> ordenada**. Sobre una lista desordenada no da error: da una respuesta
> **equivocada**, y eso es peor. Es un error de lógica de manual, de los que no
> avisa nadie.
""")

    c.code('''def buscar_binaria(datos, buscado):
    izquierda = 0
    derecha = len(datos) - 1
    while izquierda <= derecha:
        medio = (izquierda + derecha) // 2
        if datos[medio] == buscado:
            return medio
        if datos[medio] < buscado:
            izquierda = medio + 1      # descarto la mitad de abajo
        else:
            derecha = medio - 1        # descarto la mitad de arriba
    return -1

ordenada = [10, 20, 30, 40, 50, 60, 70]
print("El 60 esta en la posicion", buscar_binaria(ordenada, 60))

desordenada = [50, 10, 70, 20]
print("Sobre una lista DESORDENADA:", buscar_binaria(desordenada, 70), "<- deberia ser 2")''')

    c.md("""Fíjate en la última línea: no dio error, dio una respuesta falsa. Por eso la
precondición hay que comprobarla, no suponerla.

### 4C. Ordenamiento por selección

La idea es la de ordenar cartas en la mano: busca la más pequeña de todas y
ponla primera; busca la más pequeña de las que quedan y ponla segunda; y así.
""")

    c.code('''def ordenar_seleccion(datos):
    datos = list(datos)                 # copia, para no estropear la original
    for i in range(len(datos)):
        menor = i
        for j in range(i + 1, len(datos)):
            if datos[j] < datos[menor]:
                menor = j
        datos[i], datos[menor] = datos[menor], datos[i]     # intercambio
        print("  paso", i + 1, "->", datos)
    return datos

print("Ordenando [5, 2, 9, 1]:")
ordenar_seleccion([5, 2, 9, 1])''')

    c.md("""Esa línea `datos[i], datos[menor] = datos[menor], datos[i]` intercambia dos
elementos. En otros lenguajes hacen falta tres líneas y una variable auxiliar;
Python lo hace en una.

### 4D. Ordenamiento de burbuja

Compara cada pareja de vecinos y los intercambia si están al revés. Repite hasta
que no haya nada que intercambiar. Los valores grandes «suben» hasta el final,
como burbujas — de ahí el nombre.
""")

    c.code('''def ordenar_burbuja(datos):
    datos = list(datos)
    n = len(datos)
    for i in range(n):
        for j in range(n - i - 1):
            if datos[j] > datos[j + 1]:
                datos[j], datos[j + 1] = datos[j + 1], datos[j]
    return datos

print(ordenar_burbuja([5, 2, 9, 1]))''')

    c.md("""### 4E. Merge sort y quicksort: los dos que no vas a escribir todavía

El temario nombra otros dos, y conviene que sepas qué son aunque no los
implementes esta semana:

- **Merge sort** parte la lista en mitades, ordena cada mitad y luego las
  **mezcla** en orden.
- **Quicksort** escoge un elemento como referencia, deja a la izquierda los
  menores y a la derecha los mayores, y repite en cada lado.

Los dos usan una técnica que se llama **recursión** —una función que se llama a
sí misma— y eso no se ha visto todavía. Escribirlos ahora sería usar algo que
nadie te ha explicado, así que no se te va a pedir.

Lo que sí puedes hacer es **medirlos**, y ahí está lo importante:
""")

    c.code("comparar_ordenamientos(200)")

    c.md("""### 4F. Por qué esto no es un detalle técnico

Selección y burbuja tienen un problema: si doblas los datos, el trabajo se
multiplica por **cuatro**. Con 200 elementos son unas 20.000 comparaciones; con
2.000, dos millones.

Merge sort y quicksort crecen mucho más despacio. Por eso son los que están por
dentro del `sorted()` de Python y de prácticamente todo sistema real.

Esa diferencia se paga en tres monedas: **tiempo** de espera del usuario,
**electricidad** del servidor y **dinero** de la factura. Un algoritmo mal
elegido en un sistema que procesa millones de registros al día no es un error de
estilo: es un coste económico y ambiental medible. Por eso «que funcione» no es
suficiente, y esta es la semana en que eso deja de ser una frase y pasa a ser un
número que puedes calcular.
""")

    # =========================================================================
    c.seccion(5, "Seis ejercicios", 21, """**65 puntos**, y el cuadernillo más exigente de los seis. Tómate el tiempo.""")

    c.ejercicio(
        numero=1, competencias=['I3'], titulo="Índices", estrellas=1, puntos=5,
        enunciado="""Con esta lista:

```python
dias = ["lunes", "martes", "miercoles", "jueves", "viernes"]
```

Completa el diccionario. Los cuatro primeros son textos; el quinto es un número.

| Llave | Qué vale |
|---|---|
| `primero` | `dias[0]` |
| `tercero` | `dias[2]` |
| `ultimo` | el último, escrito con su índice |
| `cuantos` | cuántos elementos tiene la lista |
| `indice_ultimo` | el índice del último elemento, como número |""",
        partida='''INDICES = {
    "primero": ...,
    "tercero": ...,
    "ultimo": ...,
    "cuantos": ...,
    "indice_ultimo": ...,
}''',
        solucion='''INDICES = {
    "primero": "lunes",
    "tercero": "miercoles",
    "ultimo": "viernes",
    "cuantos": 5,
    "indice_ultimo": 4,
}''',
        pruebas='''assert isinstance(INDICES, dict), "INDICES debe seguir siendo un diccionario"
assert set(INDICES) == {"primero", "tercero", "ultimo", "cuantos", "indice_ultimo"}, \\
    "No cambies las cinco llaves"
assert isinstance(INDICES["cuantos"], int), "cuantos es un numero, sin comillas"
assert isinstance(INDICES["indice_ultimo"], int), "indice_ultimo es un numero"
# Se corrige aqui mismo, contra huellas: el alumno sabe al instante cual
# fallo y la respuesta no esta escrita en ninguna parte del cuadernillo.
revisar("ejercicio_1", INDICES, {
    "primero": ("9c58237a99158ea4",
          "el indice 0 no es el primero por casualidad: cuenta desde ahi"),
    "tercero": ("5d9c162e61f1ee26",
          "si el 0 es el primero, ¿que indice le toca al tercero?"),
    "ultimo": ("96fbf218dfc2bf94",
          "el ultimo esta al final de la lista: mirala entera"),
    "cuantos": ("807df0d0cd326132",
          "`cuantos` es el total de elementos, no el ultimo indice"),
    "indice_ultimo": ("659c2a0ff2b2e888",
          "ojo: `len(lista)` y el indice del ultimo NO son el mismo numero"),
})''',
        pruebas_ocultas='''assert INDICES["primero"] == "lunes", "El indice 0 es el PRIMERO"
assert INDICES["tercero"] == "miercoles", "El indice 2 es el tercero, porque se cuenta desde 0"
assert INDICES["ultimo"] == "viernes"
assert INDICES["cuantos"] == 5
assert INDICES["indice_ultimo"] == 4, "Cinco elementos, indices 0 a 4"''',
        pistas=[
            "Escribe la lista y numera las casillas empezando por CERO. Con eso las "
            "tres primeras salen solas.",
            "Cuidado con `tercero`: el indice 2 no es el segundo. Cuenta 0, 1, 2 y "
            "senala donde caes.",
            "`cuantos` e `indice_ultimo` no son el mismo numero, y esa es toda la "
            "gracia: hay 5 elementos pero el ultimo indice es 4.",
        ],
    )


    c.ejercicio(
        numero=2, competencias=['I3'], titulo="Buscar sin ordenar, y sin `for`", estrellas=2, puntos=10,
        enunciado="""Escribe `posicion_de(datos, buscado)`: la búsqueda lineal.

Devuelve el **índice** donde está `buscado`, o `-1` si no está. Si aparece más
de una vez, devuelve el de la **primera** aparición.

`posicion_de(["Ana", "Bruno", "Ana"], "Ana")` es `0`, no `2`.

> **La restricción: resuélvelo sin usar `for`.** Ni ciclo `for` ni
> por-comprensión (`[... for ... in ...]`). Usa un `while`, y la celda de
> prueba lo comprueba: si se cuela un `for`, te lo dice.

No es un capricho. Con `for` esto lo escribes de memoria y no piensas nada; con
`while` tienes que poner tú las tres piezas —dónde arranca el índice, hasta
dónde sigue, y quién lo mueve— que es exactamente lo que vas a necesitar en el
Ejercicio 3, donde el índice **no** avanza de uno en uno y el `for` ya no te
sirve.""",
        partida='''def posicion_de(datos, buscado):
    ...''',
        solucion='''def posicion_de(datos, buscado):
    i = 0
    while i < len(datos):
        if datos[i] == buscado:
            return i
        i = i + 1
    return -1''',
        pruebas='''assert callable(posicion_de), "posicion_de debe ser una funcion"
sin_usar(posicion_de, "for")
assert posicion_de(["Ana", "Bruno", "Carlos"], "Bruno") == 1
assert posicion_de(["Ana", "Bruno"], "Zoe") == -1, "Si no esta, devuelve -1"
assert posicion_de(["Ana", "Bruno", "Ana"], "Ana") == 0, "La PRIMERA aparicion"
print("Las tres busquedas dan la posicion correcta, y sin un solo for.")''',
        pruebas_ocultas='''sin_usar(posicion_de, "for")
assert posicion_de([], "Ana") == -1, "En una lista vacia no esta nada"
assert posicion_de([10, 20, 30], 30) == 2
assert posicion_de([10, 20, 30], 10) == 0
assert isinstance(posicion_de([1, 2], 2), int)''',
        pistas=[
            "Las tres piezas del while: `i = 0` antes de entrar, `while i < len(datos)` "
            "para seguir, e `i = i + 1` dentro para avanzar. Si te falta la tercera, "
            "el ciclo no termina nunca.",
            "`return` sale de la funcion en el acto. Si devuelves en cuanto encuentras, "
            "la primera aparicion es la unica que puede salir.",
            "El `return -1` va FUERA del ciclo, al final. Si lo pones dentro, la "
            "funcion se sale en la primera vuelta sin haber mirado el resto.",
        ],
    )

    c.ejercicio(
        numero=3, competencias=['I3'], titulo="Buscar por la mitad", estrellas=3, puntos=10,
        enunciado="""Escribe `busqueda_binaria(datos, buscado)` sobre una lista **ya ordenada**.

Devuelve el índice donde está, o `-1` si no está.

La idea: mira el elemento del medio. Si es el que buscas, listo. Si es menor,
lo que buscas está en la mitad de arriba; si es mayor, en la de abajo. Descarta
la otra mitad y repite.

`busqueda_binaria([10, 20, 30, 40, 50], 40)` es `3`.""",
        partida='''def busqueda_binaria(datos, buscado):
    ...''',
        solucion='''def busqueda_binaria(datos, buscado):
    izquierda = 0
    derecha = len(datos) - 1
    while izquierda <= derecha:
        medio = (izquierda + derecha) // 2
        if datos[medio] == buscado:
            return medio
        if datos[medio] < buscado:
            izquierda = medio + 1
        else:
            derecha = medio - 1
    return -1''',
        pruebas='''assert callable(busqueda_binaria), "busqueda_binaria debe ser una funcion"
assert busqueda_binaria([10, 20, 30, 40, 50], 40) == 3
assert busqueda_binaria([10, 20, 30, 40, 50], 10) == 0, "El primero tambien"
assert busqueda_binaria([10, 20, 30, 40, 50], 99) == -1, "Si no esta, -1"
print("Las tres busquedas binarias dan bien.")''',
        pruebas_ocultas='''assert busqueda_binaria([10, 20, 30, 40, 50], 50) == 4, "El ultimo tambien"
assert busqueda_binaria([], 1) == -1, "Lista vacia: no esta"
assert busqueda_binaria([7], 7) == 0, "Un solo elemento, y es el buscado"
assert busqueda_binaria([7], 3) == -1
_g = list(range(0, 2000, 2))
assert busqueda_binaria(_g, 1998) == 999, "Debe funcionar tambien en listas grandes"
assert busqueda_binaria(_g, 999) == -1, "999 es impar: no esta en la lista"''',
        pistas=[
            "Necesitas dos variables que marquen el trozo que todavia puede contener el "
            "dato: una al principio y otra al final.",
            "El del medio se calcula con `(izquierda + derecha) // 2`. Usa la division "
            "entera: un indice no puede tener decimales.",
            "Cuando descartas, mueve el limite UNA posicion mas alla del medio "
            "(`medio + 1` o `medio - 1`). Si lo dejas en `medio`, el ciclo puede "
            "quedarse dando vueltas sobre el mismo elemento para siempre.",
        ],
    )

    c.ejercicio(
        numero=4, competencias=['I3'], titulo="La precondición", estrellas=2, puntos=10,
        enunciado="""La búsqueda binaria solo sirve si la lista está ordenada. Escribe la función
que lo comprueba.

`esta_ordenada(datos)` devuelve `True` si cada elemento es menor o igual que el
siguiente, y `False` si alguno rompe el orden.

`esta_ordenada([1, 2, 2, 5])` es `True`.
`esta_ordenada([1, 5, 2])` es `False`.

Una lista vacía o de un solo elemento está ordenada: no hay ninguna pareja que
pueda estar mal.""",
        partida='''def esta_ordenada(datos):
    ...''',
        solucion='''def esta_ordenada(datos):
    for i in range(len(datos) - 1):
        if datos[i] > datos[i + 1]:
            return False
    return True''',
        pruebas='''assert callable(esta_ordenada), "esta_ordenada debe ser una funcion"
assert esta_ordenada([1, 2, 2, 5]) is True
assert esta_ordenada([1, 5, 2]) is False
assert esta_ordenada([]) is True, "Una lista vacia esta ordenada"
assert esta_ordenada([7]) is True, "Un solo elemento esta ordenado"
print("Los cuatro casos dan bien.")''',
        pruebas_ocultas='''assert esta_ordenada([5, 4, 3, 2, 1]) is False, "Al reves no esta ordenada"
assert esta_ordenada([1, 1, 1]) is True, "Elementos iguales NO rompen el orden"
assert esta_ordenada([1, 2, 3, 0]) is False, "El fallo esta al final"
assert isinstance(esta_ordenada([1, 2]), bool), "Debe devolver True o False"''',
        pistas=[
            "Compara cada elemento con el SIGUIENTE. Eso significa que el ciclo tiene "
            "que parar uno antes del final, o `datos[i + 1]` se sale de la lista.",
            "`range(len(datos) - 1)` te da exactamente las posiciones que tienen un "
            "siguiente con el que compararse.",
            "En cuanto encuentres una pareja al reves ya puedes devolver False: no hace "
            "falta seguir mirando. El `return True` va al final, fuera del ciclo.",
        ],
    )


    c.ejercicio(
        numero=5, competencias=['I3'], titulo="Burbuja, y cuánto cuesta", estrellas=3, puntos=15,
        enunciado="""`burbuja(datos)` devuelve una **tupla** con dos cosas: la lista ordenada y el
número de **comparaciones** que hizo.

```python
burbuja([3, 1, 2])   ->   ([1, 2, 3], 3)
```

El algoritmo: recorre la lista comparando cada elemento con su vecino de la
derecha e intercambiándolos si están al revés. Repite tantas pasadas como
elementos haya.

Cuenta **una comparación cada vez que comparas dos vecinos**, la intercambies o
no. Con la versión clásica —dos ciclos, el de dentro llegando hasta
`n - i - 1`— una lista de 3 elementos da exactamente 3 comparaciones.""",
        partida='''def burbuja(datos):
    ...''',
        solucion='''def burbuja(datos):
    datos = list(datos)
    comparaciones = 0
    n = len(datos)
    for i in range(n):
        for j in range(n - i - 1):
            comparaciones = comparaciones + 1
            if datos[j] > datos[j + 1]:
                datos[j], datos[j + 1] = datos[j + 1], datos[j]
    return (datos, comparaciones)''',
        pruebas='''assert callable(burbuja), "burbuja debe ser una funcion"
_r = burbuja([3, 1, 2])
assert isinstance(_r, tuple) and len(_r) == 2, "Debe devolver una tupla (lista, comparaciones)"
assert _r[0] == [1, 2, 3], f"La lista ordenada debe ser [1, 2, 3] y dio {_r[0]}"
assert _r[1] == 3, f"Con 3 elementos son 3 comparaciones y contaste {_r[1]}"
print("burbuja([3, 1, 2]) =", _r)''',
        pruebas_ocultas='''assert burbuja([5, 2, 9, 1])[0] == [1, 2, 5, 9]
assert burbuja([])[0] == [] and burbuja([])[1] == 0, "Lista vacia: cero comparaciones"
assert burbuja([1])[1] == 0, "Un solo elemento: nada que comparar"
assert burbuja([2, 1])[1] == 1, "Dos elementos: una comparacion"
assert burbuja([4, 3, 2, 1])[1] == 6, "Cuatro elementos: 3+2+1 = 6 comparaciones"
_o = [3, 1, 2]
burbuja(_o)
assert _o == [3, 1, 2], "No modifiques la lista original"''',
        pistas=[
            "Empieza por hacer que ordene, sin contar nada. Cuando la lista salga bien, "
            "anade el contador: son dos problemas, no uno.",
            "El contador sube JUSTO ANTES del `if`, no dentro. Se cuenta la comparacion "
            "aunque no haya intercambio.",
            "El ciclo de dentro llega hasta `n - i - 1`: en cada pasada el mayor ya "
            "quedo colocado al final, asi que no hace falta volver a mirarlo. Con "
            "4 elementos son 3 + 2 + 1 = 6 comparaciones.",
        ],
    )

    c.ejercicio(
        numero=6, competencias=['I3'], titulo="¿Cuál cuesta menos?", estrellas=4, puntos=15,
        enunciado="""El de cierre, y el que resume la semana. No se te pide escribir un algoritmo
nuevo: se te pide **medir** y sacar la conclusión.

`comparar(datos, buscado)` devuelve un diccionario con cuatro llaves:

| Llave | Qué guarda |
|---|---|
| `pasos_lineal` | cuántos elementos mira la búsqueda lineal hasta encontrarlo (o hasta el final) |
| `pasos_binaria` | cuántas veces parte la lista la búsqueda binaria |
| `se_puede_binaria` | `True` si `datos` está ordenada, `False` si no |
| `mejor` | `"binaria"` si se puede usar **y** hace menos pasos; `"lineal"` en cualquier otro caso |

Cuenta **un paso por cada elemento mirado** en la lineal, y **un paso por cada
vuelta del `while`** en la binaria.

Con `comparar(list(range(100)), 99)`: la lineal da 100 pasos, la binaria 7, está
ordenada, y la mejor es `"binaria"`.

> Si la lista **no** está ordenada, la binaria no se puede usar aunque diera
> menos pasos: daría una respuesta equivocada. En ese caso `mejor` es
> `"lineal"`.""",
        partida='''def comparar(datos, buscado):
    ...''',
        solucion='''def comparar(datos, buscado):
    pasos_lineal = 0
    for i in range(len(datos)):
        pasos_lineal = pasos_lineal + 1
        if datos[i] == buscado:
            break

    pasos_binaria = 0
    izquierda = 0
    derecha = len(datos) - 1
    while izquierda <= derecha:
        pasos_binaria = pasos_binaria + 1
        medio = (izquierda + derecha) // 2
        if datos[medio] == buscado:
            break
        if datos[medio] < buscado:
            izquierda = medio + 1
        else:
            derecha = medio - 1

    ordenada = True
    for i in range(len(datos) - 1):
        if datos[i] > datos[i + 1]:
            ordenada = False

    if ordenada and pasos_binaria < pasos_lineal:
        mejor = "binaria"
    else:
        mejor = "lineal"

    return {
        "pasos_lineal": pasos_lineal,
        "pasos_binaria": pasos_binaria,
        "se_puede_binaria": ordenada,
        "mejor": mejor,
    }''',
        pruebas='''assert callable(comparar), "comparar debe ser una funcion"
_r = comparar(list(range(100)), 99)
assert isinstance(_r, dict), "comparar debe devolver un diccionario"
assert set(_r) == {"pasos_lineal", "pasos_binaria", "se_puede_binaria", "mejor"}, \\
    "Deben estar las cuatro llaves exactas"
assert _r["pasos_lineal"] == 100, f"La lineal mira los 100 y contaste {_r['pasos_lineal']}"
assert _r["se_puede_binaria"] is True, "range(100) esta ordenada"
assert _r["mejor"] == "binaria"
print("comparar(range(100), 99) ->", _r)''',
        pruebas_ocultas='''_a = comparar([5, 1, 9, 3], 9)
assert _a["se_puede_binaria"] is False, "[5, 1, 9, 3] NO esta ordenada"
assert _a["mejor"] == "lineal", "Sin lista ordenada, la binaria no se puede usar"
assert _a["pasos_lineal"] == 3, "Encuentra el 9 en la tercera mirada"
_b = comparar(list(range(100)), 99)
assert _b["pasos_binaria"] == 7, f"La binaria da 7 vueltas y contaste {_b['pasos_binaria']}"
_c = comparar([1, 2, 3], 1)
assert _c["pasos_lineal"] == 1, "El primero se encuentra en un paso"
assert _c["mejor"] == "lineal", "Si la binaria no hace MENOS pasos, gana la lineal"''',
        pistas=[
            "Son cuatro problemas pequenos y los tres primeros ya los resolviste esta "
            "semana: `posicion_de`, `busqueda_binaria` y `esta_ordenada`. Copialos y "
            "anadeles el contador.",
            "Las dos busquedas cuentan pasos aunque NO encuentren el dato: la lineal "
            "cuenta cada elemento mirado y la binaria cada vuelta del while.",
            "La ultima llave tiene dos condiciones unidas: la lista tiene que estar "
            "ordenada Y la binaria tiene que hacer menos pasos. Si falla cualquiera de "
            "las dos, la respuesta es 'lineal'.",
        ],
    )

    # =========================================================================
    c.seccion(6, "Habla con el asistente", 3, """**Cinco preguntas** para todo el cuadernillo. Este es el más difícil de los
seis, así que administra bien.""")

    c.md("""### En qué gastarlas

En los índices y en la búsqueda lineal, ninguna: ejecuta `ver_lista(...)` y
mira dónde cae cada posición. Guárdalas para la binaria —el bucle que no
termina es el error clásico y cuesta verlo solo—, para la burbuja, y para el
último, que reutiliza los anteriores.

### Cómo se pregunta bien

Mal: «la binaria no me funciona».
Bien: «mi `busqueda_binaria([10,20,30], 30)` se queda colgada.
Cuando no encuentro el dato hago `derecha = medio`. ¿Por qué eso no termina?»

La segunda dice el caso exacto, qué escribiste y qué pasó. Con eso el tutor te
puede responder de verdad.
""")

    # =========================================================================
    c.seccion(7, "Cierre", 3, """Cierras la primera mitad del curso. Tres preguntas.""")

    c.md("""- ¿Podrías explicarle a alguien **por qué** la búsqueda binaria necesita que la
  lista esté ordenada? Si la respuesta es «porque si no, no funciona», todavía
  no lo tienes: la pregunta es *por qué* no funciona.
- Entre selección y burbuja, ¿sabrías decir en qué se parecen? Los dos tienen
  dos ciclos anidados y los dos multiplican su trabajo por cuatro al doblar los
  datos. Esa familia se llama «cuadrática», y la vas a volver a ver.
- Mira el resultado de `comparar_ordenamientos(200)`. Si mañana te dieran un
  millón de registros, ¿escribirías tu burbuja o usarías `sorted()`? ¿Y sabrías
  justificar la decisión con números?

### Lo que llevas

Seis semanas. Variables y tipos, análisis de problemas, pseudocódigo y
diagramas, decisiones, repeticiones, colecciones, búsqueda y ordenamiento. Con
eso ya se puede escribir software de verdad — no de juguete.

Lo que viene en la segunda mitad se construye entero encima de esto.

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **Lista** | Una variable que guarda varios valores en orden |
| **Índice** | La posición de un elemento. **Empieza en cero** |
| **`IndexError`** | Pediste una posición que no existe |
| **Mutable** | Que se puede cambiar después de creado. Por eso se puede ordenar una lista en su sitio |
| **Búsqueda lineal** | Mirar uno por uno. Funciona siempre |
| **Búsqueda binaria** | Partir por la mitad. **Solo** sobre listas ordenadas |
| **Precondición** | Lo que tiene que cumplirse para que un algoritmo sea válido |
| **Complejidad** | Cómo crece el trabajo de un algoritmo cuando crecen los datos |
""")

    return c
