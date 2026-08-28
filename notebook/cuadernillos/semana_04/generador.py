#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 4: «Repetir».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 4 — Estructuras repetitivas e integración del control de flujo.

80 puntos de nbgrader en ocho ejercicios, 90 XP y la insignia «Quien automatiza».

Dos límites que se respetan a propósito y que hay que tener presentes al
editarlo:

- **El motor de pseudocódigo entiende `Mientras`, no `Para`.** En vez de
  disimularlo, el cuadernillo lo aprovecha: el ciclo se explica con `Mientras`,
  que es el que enseña el mecanismo (arranque, condición, paso), y el `Para`
  aparece solo en Python, presentado como lo que es — un atajo para cuando ya
  sabes cuántas vueltas vas a dar.
- **El `for` va siempre con `range()`.** Recorrer listas y cadenas es de la
  semana 6. Un `for nota in notas` aquí estaría usando algo que nadie ha
  explicado.
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
        codigo="semana_04",
        titulo="Repetir",
        semana=4,
        meta_xp=90,
        insignia="Quien automatiza",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[
            os.path.join(MOTOR, "pseudo_uis.py"),
            os.path.join(AQUI, "contenido.py"),
        ],
    )

    c.md("""# Repetir
### Semana 4 · Unidad 4 · Estructuras repetitivas e integración del control de flujo

Sabes hacer que un programa calcule y sabes hacer que decida. Te falta una sola
cosa, y con ella podrás escribir —literalmente— cualquier algoritmo que exista:
**repetir**.

Secuencia, decisión y repetición. Tres estructuras. No hay una cuarta.

**Empieza ejecutando la celda de abajo.**
""")

    c.arranque()
    c.code("iniciar()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Escribir un ciclo `Mientras` en pseudocódigo y un `while` en Python, y saber
  **cuándo se detiene**.
- Usar las tres variables que aparecen en casi todo ciclo: **contador**,
  **acumulador** y **bandera** — y no confundirlas.
- Usar `for` con `range()` cuando sabes de antemano cuántas vueltas hay.
- Cortar o saltar una vuelta con `break` y `continue`, y saber por qué `pass`
  existe.
- Anidar dos ciclos sin perderte.
- Validar una entrada repitiendo hasta que el usuario escriba algo válido.
- Mirar dos soluciones al mismo problema y decir cuál hace **menos
  operaciones** — y por qué eso importa fuera del salón.

**Lo que NO se te pide todavía:** recorrer listas ni cadenas. Eso es la semana 6.
Aquí el `for` va siempre con `range()`.

Este cuadernillo tiene **80 puntos** y **90 XP**. La insignia se llama
«Quien automatiza».
""")

    # =========================================================================
    c.seccion(1, "Calentamiento", 8, """Tres de la semana pasada. Sin nota: dan XP y te dicen si puedes seguir.""")
    c.code("quiz_igualdad()")
    c.code("quiz_cadena()")
    c.code("quiz_precedencia()")

    # =========================================================================
    c.seccion(2, "Cien notas a mano", 8, """El profesor de Cálculo tiene que sacar el promedio de su curso. Son 100
estudiantes.

Sin ciclos, el programa que lo hace tiene **cien líneas** de sumar. Y si el
semestre siguiente el curso tiene 87, hay que reescribirlo.

Con un ciclo son cuatro líneas, y funciona para 100, para 87 y para 3.000.
Ejecuta y mira las cuatro:""")

    c.code('''total = 0
i = 1
while i <= 100:
    total = total + i     # aqui sumariamos la nota i, para el ejemplo sumamos i
    i = i + 1

print("Sumo del 1 al 100 y dio:", total)''')

    c.md("""Eso que acaba de pasar cien veces es un **ciclo**. El resto del cuadernillo es
entender cada una de sus piezas para poder escribirlo tú.
""")

    # =========================================================================
    c.seccion(3, "Concepto en corto", 30, """Un ciclo tiene tres piezas y ninguna es opcional. Si te falta una, o no
arranca, o no para nunca.""")

    c.md("""### 3A. Las tres piezas

```python
i = 1              # 1. ARRANQUE   — de dónde parte
while i <= 100:    # 2. CONDICIÓN  — mientras esto sea Verdadero, sigue
    ...
    i = i + 1      # 3. PASO       — qué cambia en cada vuelta
```

La condición se comprueba **antes** de cada vuelta. Si la primera vez ya es
falsa, el cuerpo no se ejecuta ni una sola vez — y eso está bien, no es un error.

> **El error más caro del cuadernillo: el ciclo infinito.** Si se te olvida el
> paso, la condición nunca deja de cumplirse y el programa se queda dando
> vueltas para siempre. En Jupyter lo reconoces porque el `[*]` a la izquierda
> de la celda no se apaga nunca. Se corta con el botón ⏹ de la barra de arriba.
>
> Es un error de **ejecución**, de los de la semana 1. No te lo va a avisar
> nadie antes de que ocurra.

Ejecuta el contador de vueltas y mira, fila a fila, cuándo decide salir:
""")

    c.code('vueltas(inicio=1, condicion="i <= 5", paso="i + 1")')

    c.md("""Ahora mira qué pasa si el paso está mal puesto. **No lo copies en una celda
tuya**: aquí el contador se detiene solo, pero en un programa de verdad esto no
para nunca.
""")

    c.code('vueltas(inicio=1, condicion="i <= 5", paso="i")   # el paso no cambia nada')

    c.md("""### 3B. Contador, acumulador y bandera

Casi todo ciclo lleva alguna de estas tres. Se parecen y hacen cosas distintas:
""")

    c.code("las_tres_variables()")

    c.md("""> **La confusión que da un número creíble y falso.** Si querías *contar* cuántos
> aprobaron y por descuido *sumaste* sus notas, el programa no falla: te devuelve
> un número perfectamente razonable que no significa nada. Nadie te va a avisar.
> Es un error de lógica de manual.

### 3C. Cuántas operaciones hace

Dos programas pueden dar el mismo resultado y costar cosas muy distintas.
Sumar del 1 al 100 con un ciclo son **100 vueltas**. Con la fórmula de Gauss
—`n * (n + 1) / 2`— es **una** operación.

Con 100 números da igual. Con cien millones, uno tarda un rato largo y el otro
sigue siendo instantáneo. Esa diferencia se paga en tiempo, en electricidad y en
factura de servidor: es la razón de que la eficiencia de un algoritmo sea un
problema económico y ambiental, no solo técnico.

Compruébalo:
""")

    c.code('''n = 100

total = 0
i = 1
vueltas_dadas = 0
while i <= n:
    total = total + i
    vueltas_dadas = vueltas_dadas + 1
    i = i + 1

print("Con ciclo :", total, "en", vueltas_dadas, "vueltas")
print("Con formula:", n * (n + 1) // 2, "en 1 operacion")''')

    # =========================================================================
    c.seccion(4, "Laboratorio", 55, """Cada estructura, primero en pseudocódigo y justo debajo en Python. Con una
excepción que conviene que entiendas.""")

    c.md("""### 4A. Mientras / while

**Pseudocódigo**

```
Mientras i <= 5 Hacer
    Escribir i
    i <- i + 1
FinMientras
```

**Python**

```python
while i <= 5:
    print(i)
    i = i + 1
```

Ejecútalo de verdad en el motor:
""")

    c.code('''r = ps.ejecutar_pseudo("""
Algoritmo Contar
    Definir i Como Entero
    i <- 1
    Mientras i <= 5 Hacer
        Escribir i
        i <- i + 1
    FinMientras
FinAlgoritmo
""")
print(r.salida)''')

    c.md("""### 4B. El `for`, que solo existe en Python

Aquí está la excepción. El pseudocódigo del curso tiene **un solo** ciclo:
`Mientras`. Python tiene dos, y el segundo es un atajo.

Cuando sabes de antemano **cuántas vueltas** vas a dar, escribir arranque,
condición y paso por separado es repetitivo. `for` los junta en una línea:

```python
# Estas dos hacen exactamente lo mismo
i = 0
while i < 5:
    print(i)
    i = i + 1

for i in range(5):
    print(i)
```

`range(5)` da 0, 1, 2, 3, 4 — **cinco** números que empiezan en cero y no
incluyen el 5. Es la fuente de errores por uno más frecuente del semestre.

| Escribes | Te da |
|---|---|
| `range(5)` | 0, 1, 2, 3, 4 |
| `range(1, 6)` | 1, 2, 3, 4, 5 |
| `range(0, 10, 2)` | 0, 2, 4, 6, 8 |

Ejecuta y compruébalo:
""")

    c.code('''for i in range(5):
    print("range(5) da:", i)

print("---")

for i in range(1, 6):
    print("range(1, 6) da:", i)''')

    c.md("""> **Cuál usar.** ¿Sabes cuántas vueltas antes de empezar? `for`. ¿Depende de
> algo que pase dentro —lo que escriba el usuario, si encontraste lo que
> buscabas—? `while`.

### 4C. break, continue y pass

Tres palabras que cambian el recorrido del ciclo:

- **`break`** — sal del ciclo ya, aunque la condición siga siendo verdadera.
- **`continue`** — sáltate el resto de esta vuelta y ve a la siguiente.
- **`pass`** — no hagas nada. Existe porque Python no admite un bloque vacío:
  es un relleno para cuando todavía no escribiste esa parte.

Ejecuta y lee la salida con calma:
""")

    c.code('''print("Con break: paro en cuanto encuentro el 3")
for i in range(10):
    if i == 3:
        break
    print("  ", i)

print("Con continue: me salto los pares")
for i in range(6):
    if i % 2 == 0:
        continue
    print("  ", i)''')

    c.md("""### 4D. Validar hasta que esté bien

El uso más honesto de un `while`: no dejar avanzar al programa hasta que el dato
sirva. Aquí se usa una **bandera**, o directamente la condición:

```python
nota = -1
while nota < 0 or nota > 5:
    nota = float(input("Nota (0 a 5): "))
```

Mientras el usuario escriba disparates, vuelve a preguntar. En cuanto escriba
algo entre 0 y 5, la condición deja de cumplirse y el programa sigue.

### 4E. Ciclos anidados

Un ciclo dentro de otro. El de dentro da **todas** sus vueltas por **cada** vuelta
del de fuera: dos ciclos de 3 vueltas son 9 pasadas, no 6.
""")

    c.code('''for fila in range(1, 4):
    for columna in range(1, 4):
        print(fila, "x", columna, "=", fila * columna)
    print("--- fin de la fila", fila)''')

    # =========================================================================
    c.seccion(5, "Ocho ejercicios", 50, """**80 puntos**, de menos a más. Si te atascas, `pista("E5")` te da hasta tres
ayudas escalonadas y no resta puntos.

Un aviso propio de esta semana: si una celda se queda con `[*]` y no termina,
tienes un ciclo infinito. Córtalo con el botón ⏹ de la barra y revisa el paso.""")

    c.ejercicio(
        numero=1, competencias=['I3'], titulo="¿Cuántas vueltas da?", estrellas=1, puntos=5,
        enunciado="""Sin ejecutar nada, di cuántas veces se ejecuta el cuerpo de cada ciclo.

| | Ciclo |
|---|---|
| `a` | `for i in range(5):` |
| `b` | `for i in range(1, 6):` |
| `c` | `for i in range(0, 10, 2):` |
| `d` | `i = 3` … `while i < 3:` |
| `e` | `i = 0` … `while i < 4:` con `i = i + 1` dentro |

Escribe un número entero en cada una.""",
        partida='''VUELTAS = {
    "a": ...,
    "b": ...,
    "c": ...,
    "d": ...,
    "e": ...,
}''',
        solucion='''VUELTAS = {
    "a": 5,
    "b": 5,
    "c": 5,
    "d": 0,
    "e": 4,
}''',
        pruebas='''assert isinstance(VUELTAS, dict) and set(VUELTAS) == set("abcde"), \\
    "VUELTAS debe tener las cinco llaves: a, b, c, d, e"
assert all(isinstance(v, int) and not isinstance(v, bool) for v in VUELTAS.values()), \\
    "Cada respuesta es un numero entero"
assert all(v >= 0 for v in VUELTAS.values()), "Un ciclo no puede dar vueltas negativas"
print("Formato correcto. Los valores se revisan al calificar.")''',
        pruebas_ocultas='''assert VUELTAS["a"] == 5, "range(5) da 0,1,2,3,4"
assert VUELTAS["b"] == 5, "range(1,6) da 1,2,3,4,5"
assert VUELTAS["c"] == 5, "range(0,10,2) da 0,2,4,6,8"
assert VUELTAS["d"] == 0, "i vale 3 y la condicion pide i < 3: no entra ni una vez"
assert VUELTAS["e"] == 4, "i va 0,1,2,3 y en la cuarta comprobacion i vale 4 y sale"''',
        pistas=[
            "Para los `range`, escribe la lista de numeros que produce y cuentalos. Es "
            "mas seguro que calcularlo de cabeza.",
            "En `d` fijate en el valor de arranque y en la condicion ANTES de contar "
            "vueltas. La condicion se comprueba antes de la primera vuelta.",
            "Un ciclo cuya condicion es falsa desde el principio ejecuta su cuerpo cero "
            "veces. No es un error: es lo normal.",
        ],
    )

    c.ejercicio(
        numero=2, competencias=['I3'], titulo="Contador, acumulador o bandera", estrellas=1, puntos=5,
        enunciado="""Cada situación necesita una de las tres variables. Escribe `"contador"`,
`"acumulador"` o `"bandera"`.

| Llave | Situación |
|---|---|
| `cuantos` | Cuántos estudiantes aprobaron |
| `suma` | La suma de todas las notas del curso |
| `hubo_cero` | Si alguien sacó 0.0, aunque fuera una sola persona |
| `intentos` | Cuántas veces el usuario escribió un dato inválido |
| `promedio_total` | La suma de todos los pagos del mes |""",
        partida='''TIPOS = {
    "cuantos": ...,
    "suma": ...,
    "hubo_cero": ...,
    "intentos": ...,
    "promedio_total": ...,
}''',
        solucion='''TIPOS = {
    "cuantos": "contador",
    "suma": "acumulador",
    "hubo_cero": "bandera",
    "intentos": "contador",
    "promedio_total": "acumulador",
}''',
        pruebas='''assert isinstance(TIPOS, dict), "TIPOS debe seguir siendo un diccionario"
assert set(TIPOS) == {"cuantos", "suma", "hubo_cero", "intentos", "promedio_total"}, \\
    "No cambies las cinco llaves"
_v = {"contador", "acumulador", "bandera"}
assert set(TIPOS.values()) <= _v, "Usa solo: contador, acumulador o bandera"
print("Formato correcto. Las respuestas se revisan al calificar.")''',
        pruebas_ocultas='''assert TIPOS["cuantos"] == "contador"
assert TIPOS["suma"] == "acumulador"
assert TIPOS["hubo_cero"] == "bandera"
assert TIPOS["intentos"] == "contador"
assert TIPOS["promedio_total"] == "acumulador"''',
        pistas=[
            "Hazte una sola pregunta por fila: ¿esto responde CUANTOS, responde CUANTO "
            "suman, o responde SI paso algo?",
            "Contar sube de uno en uno sin importar el valor. Acumular suma el valor que "
            "llega. Si los dos te encajan, mira si el enunciado dice «cuántos» o «la suma».",
            "Solo una de las cinco se contesta con si o no. Esa es la bandera.",
        ],
    )

    c.ejercicio(
        numero=3, competencias=['I3'], titulo="Mientras, en pseudocódigo", estrellas=2, puntos=10,
        enunciado="""Escribe el pseudocódigo completo en `ALGORITMO_E3`. El algoritmo:

1. Lee un número entero `n`.
2. Suma todos los enteros desde 1 hasta `n`.
3. Escribe el total.

Con `n = 5` debe escribir 15 (porque 1+2+3+4+5). Con `n = 10`, 55.

Acuérdate de las tres piezas: arranque, condición y paso. Si te falta el paso,
el motor te va a parar por ciclo infinito — y con razón.""",
        partida='''ALGORITMO_E3 = """
"""''',
        solucion='''ALGORITMO_E3 = """
Algoritmo Sumatoria
    Definir n Como Entero
    Definir total Como Entero
    Definir i Como Entero
    Leer n
    total <- 0
    i <- 1
    Mientras i <= n Hacer
        total <- total + i
        i <- i + 1
    FinMientras
    Escribir total
FinAlgoritmo
"""''',
        pruebas='''assert isinstance(ALGORITMO_E3, str) and ALGORITMO_E3.strip(), \\
    "ALGORITMO_E3 debe traer el pseudocodigo completo, como texto"
_r5 = ps.ejecutar_pseudo(ALGORITMO_E3, entradas=["5"])
assert _r5.ok, "Tu algoritmo no ejecuta. El motor dice: " + _r5.error_corto
assert "15" in _r5.salida, "Con n = 5 el total es 15"
print("Con n = 5 ->", _r5.salida.strip())''',
        pruebas_ocultas='''_r10 = ps.ejecutar_pseudo(ALGORITMO_E3, entradas=["10"])
assert _r10.ok, "Con n = 10 falla: " + _r10.error_corto
assert "55" in _r10.salida, "Con n = 10 el total es 55"
_r1 = ps.ejecutar_pseudo(ALGORITMO_E3, entradas=["1"])
assert "1" in _r1.salida, "Con n = 1 el total es 1"''',
        pistas=[
            "Necesitas tres variables: la que lees (n), la que acumula (total) y la que "
            "cuenta las vueltas (i). Definelas todas antes de usarlas.",
            "El acumulador empieza en 0 y el contador en 1. Si empiezas el acumulador en "
            "1 te va a sobrar uno en el resultado.",
            "El paso `i <- i + 1` va DENTRO del Mientras, como ultima linea. Si lo dejas "
            "fuera, i no cambia nunca y el ciclo no termina.",
        ],
    )

    c.ejercicio(
        numero=4, competencias=['I3'], titulo="El mismo, con while", estrellas=2, puntos=10,
        enunciado="""Traduce el ejercicio 3 a Python, como función.

`sumatoria(n)` recibe un entero y **devuelve** la suma de 1 hasta n. Usa
`while` — el `for` viene en el ejercicio siguiente.

`sumatoria(5)` debe devolver 15. `sumatoria(0)` debe devolver 0: si no hay
números que sumar, la suma es cero, y el ciclo no debe dar ni una vuelta.""",
        partida='''def sumatoria(n):
    ...''',
        solucion='''def sumatoria(n):
    total = 0
    i = 1
    while i <= n:
        total = total + i
        i = i + 1
    return total''',
        pruebas='''assert callable(sumatoria), "sumatoria debe ser una funcion"
assert sumatoria(5) == 15, "1+2+3+4+5 son 15"
assert sumatoria(10) == 55
assert sumatoria(1) == 1
print("sumatoria(5) =", sumatoria(5), "· sumatoria(10) =", sumatoria(10))''',
        pruebas_ocultas='''assert sumatoria(0) == 0, "Sin numeros que sumar, el total es 0 y el ciclo no entra"
assert sumatoria(100) == 5050, "El clasico: del 1 al 100 son 5050"
assert isinstance(sumatoria(5), int), "Debe devolver un entero"''',
        pistas=[
            "La estructura es la misma del pseudocodigo. Cambian las palabras: "
            "`Mientras ... Hacer` pasa a `while ...:` y el `FinMientras` desaparece "
            "porque cierra la sangria.",
            "Las dos variables (total e i) se crean ANTES del while. Si las creas dentro, "
            "se reinician en cada vuelta y nunca acumulan nada.",
            "El `return total` va FUERA del while, al final y sin sangria extra. Si lo "
            "metes dentro, la funcion se sale en la primera vuelta.",
        ],
    )

    c.ejercicio(
        numero=5, competencias=['I3'], titulo="Con for y range", estrellas=2, puntos=10,
        enunciado="""Ahora el mismo problema, pero con `for` — y esta vez sabes de antemano cuántas
vueltas hay, así que es el ciclo adecuado.

`tabla(numero)` devuelve un **texto** con la tabla de multiplicar del 1 al 10,
una línea por resultado, así:

```
3 x 1 = 3
3 x 2 = 6
...
3 x 10 = 30
```

Sin línea en blanco al final. Para unir las líneas te sirve `"\\n"`, que es el
salto de línea: `texto = texto + "3 x 1 = 3" + "\\n"`.""",
        partida='''def tabla(numero):
    ...''',
        solucion='''def tabla(numero):
    lineas = ""
    for i in range(1, 11):
        lineas = lineas + f"{numero} x {i} = {numero * i}"
        if i < 10:
            lineas = lineas + "\\n"
    return lineas''',
        pruebas='''assert callable(tabla), "tabla debe ser una funcion"
_t = tabla(3)
assert isinstance(_t, str), "tabla debe DEVOLVER texto, no imprimirlo"
_filas = _t.split("\\n")
assert len(_filas) == 10, f"La tabla tiene 10 lineas y la tuya tiene {len(_filas)}"
assert _filas[0] == "3 x 1 = 3", f"La primera linea debe ser '3 x 1 = 3' y es '{_filas[0]}'"
assert _filas[9] == "3 x 10 = 30", f"La ultima debe ser '3 x 10 = 30' y es '{_filas[9]}'"
print(_t)''',
        pruebas_ocultas='''_t5 = tabla(5).split("\\n")
assert _t5[0] == "5 x 1 = 5" and _t5[9] == "5 x 10 = 50"
_t0 = tabla(0).split("\\n")
assert len(_t0) == 10 and _t0[0] == "0 x 1 = 0"
assert not tabla(7).endswith("\\n"), "No dejes salto de linea al final"''',
        pistas=[
            "`range(1, 11)` da del 1 al 10. El 11 no entra: ese es el punto que hay que "
            "tener claro con range.",
            "Ve construyendo el texto vuelta a vuelta, empezando por una cadena vacia. "
            "En cada vuelta le sumas la linea nueva.",
            "El salto de linea va entre lineas, no despues de la ultima. Una forma: "
            "anadirlo solo cuando `i < 10`.",
        ],
    )

    c.ejercicio(
        numero=6, competencias=['I3'], titulo="La bandera", estrellas=3, puntos=10,
        enunciado="""`hubo_perdida(primera, ultima)` recorre los números enteros desde `primera`
hasta `ultima` (los dos incluidos), tratándolos como notas, y devuelve `True` si
**alguno** es menor que 3, o `False` si ninguno lo es.

Es el uso clásico de una **bandera**: empieza en `False` y solo puede pasar a
`True`. Nunca vuelve atrás — porque «hubo al menos una» no se deshace porque
después venga una buena.

`hubo_perdida(1, 5)` es `True` (el 1 y el 2 pierden).
`hubo_perdida(3, 5)` es `False`.""",
        partida='''def hubo_perdida(primera, ultima):
    ...''',
        solucion='''def hubo_perdida(primera, ultima):
    encontrada = False
    for nota in range(primera, ultima + 1):
        if nota < 3:
            encontrada = True
    return encontrada''',
        pruebas='''assert callable(hubo_perdida), "hubo_perdida debe ser una funcion"
assert hubo_perdida(1, 5) is True, "Entre 1 y 5 hay notas por debajo de 3"
assert hubo_perdida(3, 5) is False, "Entre 3 y 5 no pierde ninguna"
print("hubo_perdida(1, 5) =", hubo_perdida(1, 5), "· hubo_perdida(3, 5) =", hubo_perdida(3, 5))''',
        pruebas_ocultas='''assert hubo_perdida(2, 2) is True, "El 2 solo ya es perdida"
assert hubo_perdida(3, 3) is False, "3 exacto NO es perdida: la condicion es menor que 3"
assert hubo_perdida(0, 10) is True
assert hubo_perdida(5, 5) is False
assert isinstance(hubo_perdida(1, 5), bool), "Debe devolver True o False, no 1 ni 0"''',
        pistas=[
            "`range(primera, ultima + 1)` incluye los dos extremos. Sin el +1 te dejas "
            "fuera el ultimo.",
            "La bandera se crea ANTES del ciclo, en False. Si la creas dentro, se "
            "reinicia en cada vuelta y siempre te va a devolver lo de la ultima nota.",
            "Solo hay que ponerla en True; no hay que ponerla en False nunca dentro del "
            "ciclo. Si lo haces, una nota buena despues de una mala borra el hallazgo.",
        ],
    )

    c.ejercicio(
        numero=7, competencias=['I3', 'I4'], titulo="Dos ciclos, uno dentro de otro", estrellas=3, puntos=15,
        enunciado="""`escalera(altura)` devuelve un texto con una escalera de asteriscos:

```
*
**
***
```

Eso es `escalera(3)`: tres líneas, la primera con un asterisco y cada una con
uno más. Sin salto de línea al final.

Necesitas dos ciclos: el de fuera cuenta las líneas, el de dentro pone los
asteriscos de cada línea.

> **Atajo que te va a tentar:** en Python `"*" * 3` da `"***"`. Es correcto y
> puedes usarlo — pero haz primero la versión con dos ciclos, porque lo que se
> está enseñando es el anidamiento. La tercera pista te lo explica.""",
        partida='''def escalera(altura):
    ...''',
        solucion='''def escalera(altura):
    lineas = ""
    for fila in range(1, altura + 1):
        for _ in range(fila):
            lineas = lineas + "*"
        if fila < altura:
            lineas = lineas + "\\n"
    return lineas''',
        pruebas='''assert callable(escalera), "escalera debe ser una funcion"
_e = escalera(3)
assert isinstance(_e, str), "escalera debe devolver texto"
assert _e == "*\\n**\\n***", f"escalera(3) debe ser '*\\\\n**\\\\n***' y dio {_e!r}"
print(escalera(4))''',
        pruebas_ocultas='''assert escalera(1) == "*", "Con altura 1 es un solo asterisco, sin salto"
assert escalera(5).split("\\n")[4] == "*****", "La quinta linea lleva cinco"
assert len(escalera(6).split("\\n")) == 6, "Altura 6 son seis lineas"
assert escalera(0) == "", "Altura 0 no dibuja nada"
assert not escalera(4).endswith("\\n"), "Sin salto de linea al final"''',
        pistas=[
            "Empieza por el ciclo de fuera: haz que imprima las tres lineas vacias y "
            "comprueba que son tres. Solo entonces metele el de dentro.",
            "El de dentro tiene que dar tantas vueltas como diga la fila en la que "
            "estas. Si estas en la fila 3, tres asteriscos.",
            "Si usas el atajo `\"*\" * fila` el resultado es correcto y la prueba pasa. "
            "Pero escribe antes la version de dos ciclos: el atajo lo vas a olvidar, y "
            "el anidamiento lo vas a necesitar toda la carrera.",
        ],
    )

    c.ejercicio(
        numero=8, competencias=['I3', 'I4'], titulo="Todo junto, en los dos idiomas", estrellas=4, puntos=15,
        enunciado="""El de cierre junta las tres estructuras: secuencia, decisión y repetición.

Un profesor quiere, de las notas del 1 al `n` (tratando cada entero como una
nota), **cuántas aprobaron** —3 o más— y **cuánto suman todas**.

Dos entregas:

1. `ALGORITMO_E8` — el pseudocódigo. Lee `n`, y escribe **primero** la cantidad
   de aprobadas y **después** la suma total, en dos líneas.
2. `resumen(n)` — la función de Python. Devuelve una **tupla** `(aprobadas, suma)`.
   Una tupla se escribe con paréntesis: `return (2, 7)`.

Con `n = 5`: aprobaron 3 (el 3, el 4 y el 5) y suman 15.""",
        partida='''ALGORITMO_E8 = """
"""


def resumen(n):
    ...''',
        solucion='''ALGORITMO_E8 = """
Algoritmo Resumen
    Definir n Como Entero
    Definir i Como Entero
    Definir aprobadas Como Entero
    Definir suma Como Entero
    Leer n
    aprobadas <- 0
    suma <- 0
    i <- 1
    Mientras i <= n Hacer
        suma <- suma + i
        Si i >= 3 Entonces
            aprobadas <- aprobadas + 1
        FinSi
        i <- i + 1
    FinMientras
    Escribir aprobadas
    Escribir suma
FinAlgoritmo
"""


def resumen(n):
    aprobadas = 0
    suma = 0
    for i in range(1, n + 1):
        suma = suma + i
        if i >= 3:
            aprobadas = aprobadas + 1
    return (aprobadas, suma)''',
        pruebas='''assert isinstance(ALGORITMO_E8, str) and ALGORITMO_E8.strip(), \\
    "ALGORITMO_E8 debe traer el pseudocodigo completo"
_r = ps.ejecutar_pseudo(ALGORITMO_E8, entradas=["5"])
assert _r.ok, "Tu pseudocodigo no ejecuta. El motor dice: " + _r.error_corto
assert "3" in _r.salida and "15" in _r.salida, \\
    "Con n = 5 debe escribir 3 (aprobadas) y 15 (suma)"

assert callable(resumen), "resumen debe ser una funcion"
assert resumen(5) == (3, 15), f"resumen(5) debe ser (3, 15) y dio {resumen(5)}"
print("Pseudocodigo ->", _r.salida.strip().replace(chr(10), " / "))
print("Python       ->", resumen(5))''',
        pruebas_ocultas='''assert resumen(2) == (0, 3), "Con n = 2 no aprueba ninguna y suman 3"
assert resumen(3) == (1, 6), "El 3 exacto SI aprueba: la condicion es 3 o mas"
assert resumen(10) == (8, 55)
assert resumen(0) == (0, 0), "Sin notas, cero y cero"
assert isinstance(resumen(5), tuple) and len(resumen(5)) == 2, \\
    "Debe devolver una tupla de dos valores: (aprobadas, suma)"
_r2 = ps.ejecutar_pseudo(ALGORITMO_E8, entradas=["10"])
assert "8" in _r2.salida and "55" in _r2.salida, "Con n = 10 son 8 aprobadas y 55 de suma"''',
        pistas=[
            "Hazlo por partes: primero que cuente las aprobadas, comprueba que da bien, "
            "y solo despues anade la suma. Dos problemas pequenos, no uno grande.",
            "Dentro del ciclo pasan dos cosas: la suma se hace SIEMPRE y el conteo solo "
            "si la nota llega a 3. Eso es una decision dentro de una repeticion.",
            "Cuidado con el orden de las dos salidas: primero aprobadas, despues la "
            "suma. Y ojo con el borde: la nota 3 exacta aprueba, asi que es `>=`.",
        ],
    )

    # =========================================================================
    c.seccion(6, "Habla con el asistente", 5, """**Cinco preguntas** para todo el cuadernillo.""")

    c.md("""### Presupuesto sugerido

| Ejercicio | Preguntas | Por qué |
|---|---|---|
| 1 y 2 (vueltas, tipos de variable) | **0** | Ejecuta `vueltas(...)` y `las_tres_variables()` otra vez: la respuesta está ahí |
| 3 y 4 (sumatoria) | **0–1** | Si el motor te habla de ciclo infinito, te falta el paso. Eso no necesita tutor |
| 5 (tabla con for) | **0–1** | Casi siempre es el `range`: pregunta por eso |
| 6 (bandera) | **1** | Aquí sí. El detalle de no ponerla nunca en False no es evidente |
| 7 (anidados) | **1** | El de fuera cuenta filas, el de dentro columnas. Si no lo ves, pregunta |
| 8 (todo junto) | **1–2** | Guarda estas. Es el más largo y tiene dos entregas |

### Cómo se pregunta bien

Mal: «mi ciclo no para».
Bien: «en el ejercicio 4, con `sumatoria(5)` mi función se queda colgada. Tengo
`total = total + i` dentro del while. ¿Qué me falta para que `i` cambie?»

La segunda dice qué probaste, qué pasó y qué crees que falla. Con eso el tutor
te puede responder; con la primera solo puede adivinar.
""")

    # =========================================================================
    c.seccion(7, "Cierre", 7, """Tres preguntas que nadie corrige.""")

    c.md("""- ¿Sabrías explicar, sin mirar, **por qué** un ciclo se queda dando vueltas para
  siempre? Si la respuesta es «porque se me olvidó algo», ¿qué algo?
- De los dos ciclos, ¿tienes claro cuándo usar `while` y cuándo `for`? La
  pregunta que lo decide es una sola: ¿sabes cuántas vueltas antes de empezar?
- El ejercicio 7 se podía resolver con `"*" * fila` en una línea. ¿Lo hiciste
  con dos ciclos primero, o fuiste directo al atajo? Las dos respuestas están
  bien; solo conviene que sepas cuál elegiste.

### Lo que viene

La semana 5 no trae estructura nueva: es la primera evaluación y un repaso de
todo lo que llevas. Aprovéchala — con secuencia, decisión y repetición ya tienes
las tres piezas con las que se escribe cualquier programa.

### Glosario de esta semana

| Palabra | Qué significa |
|---|---|
| **Ciclo** | Una parte del programa que se repite |
| **Iteración** | Una vuelta del ciclo |
| **Contador** | Variable que cuenta cuántas veces pasó algo |
| **Acumulador** | Variable que va sumando valores |
| **Bandera** | Variable que recuerda si algo ocurrió alguna vez |
| **Ciclo infinito** | El que nunca deja de cumplir su condición y no para |
| **`range(n)`** | Los números de 0 a n−1. El n **no** entra |
| **Anidar** | Meter un ciclo dentro de otro |
""")

    return c
