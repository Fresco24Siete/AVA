#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 6: «Buscar y ordenar».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 6 — Colecciones lineales, búsqueda y ordenamiento.

25 puntos de nbgrader en tres ejercicios, 5 XP y la insignia «Quien ordena».
Recortado a ~30 minutos por instrucción del profesor (2026-09-22): menos
teoría, una demostración por concepto y solo los ejercicios que no repiten lo
que otro ya mide.

Dos límites que se respetan dentro del cuadernillo:

- **El intérprete de pseudocódigo del curso no maneja listas.** Todo lo que se
  ejecuta y se califica es Python.
- **Ordenar se lee y se mide, no se escribe.** La burbuja se muestra y se
  compara con `sorted()`; merge sort y quicksort son recursivos y la recursión
  no se ha enseñado. Los ejercicios calificables son los de búsqueda: la lineal
  con `while` (a propósito, sin `for`) y la binaria, que es la razón de que la
  lineal se haga con `while`.
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
        meta_xp=5,
        insignia="Quien ordena",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[os.path.join(AQUI, "contenido.py")],
    )

    c.md("""# Buscar y ordenar
### Semana 6 · Unidad 6 · Colecciones lineales, búsqueda y ordenamiento

Hasta ahora cada variable guardaba **un** dato. Esta semana guardas muchos en
una sola, y haces con ellos las dos operaciones que sostienen media informática:
**buscar** y **ordenar**.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Crear una **lista** y leer cualquier elemento por su **índice**.
- Escribir una **búsqueda lineal** y una **búsqueda binaria**, y decir qué
  condición hay que cumplir para poder usar la segunda.
- Leer el ordenamiento de **burbuja** y medir, con números en la mano, por qué
  un algoritmo puede ser mil veces más caro que otro dando el mismo resultado.

**Un aviso:** el intérprete de pseudocódigo del curso no maneja listas. Esta
semana todo se ejecuta y se califica en Python. Son **25 puntos** y **5 XP**;
la insignia se llama «Quien ordena».
""")

    # =========================================================================
    c.seccion(1, "Calentamiento", 1, """Una de la semana pasada.""")
    c.code("quiz_estructura()")

    # =========================================================================
    c.seccion(2, "Un nombre entre mil", 2, """Tienes la lista de los 30.000 estudiantes de la UIS, ordenada alfabéticamente,
y buscas uno. Mirando uno por uno, en el peor caso das 30.000 pasos. Abriendo
por la mitad y descartando la mitad que sobra —como en un directorio de papel—
das **quince**. Ejecuta y míralo:""")

    c.code("comparar_busquedas(1000)")

    # =========================================================================
    c.seccion(3, "Concepto en corto", 3, """Una lista es una fila de casillas numeradas.""")

    c.md("""### 3A. La lista y sus índices

Una **lista** guarda varios valores en orden, entre corchetes. Cada casilla
tiene un número, su **índice**, y **se empieza a contar en cero**. Ejecuta y
míralo dibujado:
""")

    c.code('''notas = [4.0, 3.5, 2.8, 4.8]
ver_lista(notas, resaltar=0, titulo="notas[0] es la PRIMERA, no la segunda")''')

    c.md("""```python
notas[0]    # 4.0  — la primera
notas[3]    # 4.8  — la cuarta y última
notas[4]    # IndexError: no existe
len(notas)  # 4    — cuántas hay
notas[2] = 3.9   # las listas se pueden cambiar: por eso se pueden ordenar
```

> **El error por uno.** Una lista de 4 elementos tiene índices 0, 1, 2 y 3. El
> último índice siempre es `len(lista) - 1`.

### 3B. Recorrer

```python
for i in range(len(notas)):   # por índice: cuando necesitas la POSICIÓN
    print(i, notas[i])

for nota in notas:            # directo: cuando solo importa el VALOR
    print(nota)
```
""")

    # =========================================================================
    c.seccion(4, "Laboratorio", 4, """Las dos búsquedas y un ordenamiento. Ejecuta cada celda y mira la salida.""")

    c.md("""### 4A. Búsqueda lineal

Mirar uno por uno desde el principio hasta encontrarlo. Funciona **siempre**,
esté la lista ordenada o no; su precio es que en el peor caso mira todos.
""")

    c.code('''def buscar_lineal(datos, buscado):
    for i in range(len(datos)):
        if datos[i] == buscado:
            return i
    return -1

nombres = ["Ana", "Bruno", "Carlos", "Diana"]
print("Carlos esta en la posicion", buscar_lineal(nombres, "Carlos"))
print("Zoe esta en la posicion", buscar_lineal(nombres, "Zoe"), "(-1 = no esta)")''')

    c.md("""### 4B. Búsqueda binaria, y su precondición

Mira el del medio. Si es mayor que lo que buscas, descartas toda esa mitad de
un golpe. Y repites.

> **La precondición.** La búsqueda binaria **solo funciona si la lista está
> ordenada**. Sobre una lista desordenada no da error: da una respuesta
> **equivocada**, y eso es peor.
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
print("Sobre una lista DESORDENADA, buscando el 50:", buscar_binaria(desordenada, 50),
      "<- dice que NO esta, y el 50 es el primero de la lista")''')

    c.md("""Fíjate en la última línea: no dio error, dio una respuesta falsa.

### 4C. Ordenamiento de burbuja

Compara cada pareja de vecinos y los intercambia si están al revés; los grandes
«suben» hasta el final. `datos[j], datos[j + 1] = datos[j + 1], datos[j]`
intercambia dos elementos en una sola línea.
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

    c.md("""### 4D. Cuánto cuesta

Selección (buscar el menor y ponerlo primero) es de la misma familia que
burbuja: dos ciclos anidados, y si doblas los datos el trabajo se multiplica
por **cuatro**. Merge sort y quicksort —los que usa `sorted()` por dentro—
crecen mucho más despacio, pero son recursivos y no se escriben todavía. Lo que
sí puedes hacer es **medirlos**:
""")

    c.code("comparar_ordenamientos(200)")

    c.md("""Esa diferencia se paga en **tiempo**, **electricidad** y **dinero**. Por eso
«que funcione» no es suficiente, y esta semana eso pasa a ser un número.
""")

    # =========================================================================
    c.seccion(5, "Tres ejercicios", 22, """**25 puntos**. El 2 y el 3 van juntos: el `while` del 2 es el que necesitas en el 3.""")

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
        numero=3, competencias=['I3', 'I1'], titulo="Buscar por la mitad", estrellas=3, puntos=10,
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

    # =========================================================================
    c.seccion(6, "Habla con el asistente", 1, """**Cinco preguntas** para todo el cuadernillo.""")

    c.md("""En los índices, ninguna: ejecuta `ver_lista(...)` y mira dónde cae cada
posición. Guárdalas para la binaria: el bucle que no termina es el error clásico
y cuesta verlo solo.

Mal: «la binaria no me funciona».
Bien: «mi `busqueda_binaria([10,20,30], 30)` se queda colgada.
Cuando no encuentro el dato hago `derecha = medio`. ¿Por qué eso no termina?»
""")

    # =========================================================================
    c.seccion(7, "Cierre", 1, """Cierras la primera mitad del curso. Dos preguntas.""")

    c.md("""- ¿Podrías explicarle a alguien **por qué** la búsqueda binaria necesita que la
  lista esté ordenada? Si la respuesta es «porque si no, no funciona», todavía
  no lo tienes.
- Mira el resultado de `comparar_ordenamientos(200)`. Con un millón de
  registros, ¿escribirías una burbuja a mano o usarías `sorted()`? ¿Sabrías justificarlo
  con números?

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **Lista** | Una variable que guarda varios valores en orden |
| **Índice** | La posición de un elemento. **Empieza en cero** |
| **Búsqueda lineal** | Mirar uno por uno. Funciona siempre |
| **Búsqueda binaria** | Partir por la mitad. **Solo** sobre listas ordenadas |
| **Precondición** | Lo que tiene que cumplirse para que un algoritmo sea válido |
| **Complejidad** | Cómo crece el trabajo de un algoritmo cuando crecen los datos |
""")

    return c
