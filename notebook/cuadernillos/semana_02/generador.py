#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 2: «Del problema al algoritmo».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 2 — Fundamentos para la solución de problemas.

80 puntos de nbgrader en ocho ejercicios, 32 XP lúdicos y la insignia
«Traductora / Traductor de algoritmos». Cubre lo que en la planeación vieja eran
tres cuadernos (planteamiento, pseudocódigo y diagramas), así que va partido en
dos partes con un corte explícito: la Parte A se hace después de la Clase 1 y la
Parte B después de la Clase 2.

Recorte del 2026-09-22, por indicación del profesor: menos lectura y menos
demostraciones, más hacer. Los ocho ejercicios están CONGELADOS —19 alumnos ya
entregaron— y no se tocó ninguna llamada `c.ejercicio(...)`. Lo que se fue:
tres de los cuatro quices de calentamiento, la gráfica de la madrugada, las
figuras que repetían lo que ya dibuja `ps.diagrama`, los ensayos previos a E1,
E2 y E3, el segundo trazador, los dos comparadores, el segundo error sembrado,
el Reto B y la tabla de cobertura. Por eso la meta de XP bajó de 80 a 32: es lo
que suman los dos quices y el ensayo que quedan.

Tres decisiones que se salen del documento de diseño y por qué:

- El diseño copiaba `pseudo_uis.py` a `/etc/jupyter/` dentro de la imagen. Aquí
  se **incrusta en el `.ipynb`**, junto al motor y al contenido de la semana
  (`modulos=[...]`), que es lo que ya está construido y probado: así un
  cuadernillo publicado no cambia de intérprete cuando se reconstruye la imagen.
  Como el módulo se ejecuta en el espacio de nombres del notebook y no se
  importa, `contenido.py` reconstruye la fachada `ps` con la que el estudiante
  lo llama.
- Los widgets del diseño se llamaban `ava.parsons` y `ava.analisis_eps`. En el
  motor de este repositorio son `ava.ordenar` y un ensayo propio de la semana
  (`ensayo_eps`), que es donde vive el formulario E-P-S.
- Sin matplotlib, por la misma razón que en la semana 1: son ~80 MB de RAM por
  kernel y la VM del curso tiene 2 GB para todos.
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
        codigo="semana_02",
        titulo="Del problema al algoritmo",
        semana=2,
        meta_xp=32,
        insignia="Traductora / Traductor de algoritmos",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[
            os.path.join(MOTOR, "pseudo_uis.py"),
            os.path.join(AQUI, "contenido.py"),
        ],
    )

    # =========================================================================
    # Bloque 0 — Portada y activación
    # =========================================================================
    c.md("""# Del problema al algoritmo
### Semana 2 · Unidad 2 · Fundamentos para la solución de problemas

Esta semana dices lo mismo en tres idiomas: **pseudocódigo** (para pensar),
**diagrama de flujo** (para ver) y **Python** (para ejecutar). Y el pseudocódigo
de este cuadernillo **se ejecuta de verdad**.

**Empieza ejecutando la celda de abajo** (`Shift+Enter`) y avanza celda por
celda, sin saltarte ninguna.
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar vas a poder…

1. Leer un problema y decir **qué entra, qué se hace y qué sale**.
2. Escribir un algoritmo en **pseudocódigo en español**, ejecutarlo y ver su
   **diagrama de flujo**.
3. Hacer una **prueba de escritorio** con lápiz y papel.
4. Traducirlo a **Python**, sabiendo que `input()` siempre entrega **texto**.

### Se hace en dos partes

| | Cuándo | Qué trae |
|---|---|---|
| **Parte A** | después de la **Clase 1** | secciones 1 a 3: plantear, analizar, E-P-S |
| **Parte B** | después de la **Clase 2** | secciones 4 a 8: pseudocódigo, diagramas, tipos, `input()` y los ocho ejercicios |

Es hora y media en total, casi toda en los ejercicios. Una tarjeta marca el
corte.

> Los **XP** son del juego (los dos quices y el ensayo). Los **puntos** son tu nota:
> salen solo de los ocho ejercicios. Este cuadernillo tiene **80 puntos** y
> **32 XP**; la insignia es «Traductora / Traductor de algoritmos».
""")

    # =========================================================================
    # Bloque 1 — Sección 1: calentamiento (Parte A)
    # =========================================================================
    c.seccion(1, "Calentamiento", 1, """Una pregunta de la semana pasada. No tiene nota: da XP y, si se te atasca,
vuelve al cuadernillo de la Semana 1 antes de seguir.""")

    c.code("quiz_tipos()")

    # =========================================================================
    # Bloque 2 — Sección 2: el gancho
    # =========================================================================
    c.seccion(2, "¿A qué hora tengo que salir de la casa?", 1,"""Vives en **Girón** y tu clase en la UIS es a las **6:00 a. m.** Caminas
**8 minutos** a la parada, el bus tarda **45**, de la portería al salón son
**10** y quieres un **colchón de 15**. ¿A qué hora sales?

**Las 4:42.** Lo hiciste de cabeza. Ahora hazlo para los 30.000 estudiantes de
la UIS, cada uno con su ruta y su hora: ahí hace falta **un algoritmo**, una
receta escrita una sola vez que sirva para todos.

Ejecuta la celda de abajo. No es Python: es **pseudocódigo**, español con
reglas. Y sin embargo corre, y el computador dibuja su diagrama solo.""")

    c.code('''CODIGO_GANCHO = """Algoritmo AQueHoraSalgo
    Definir hora_clase_min, minutos_bus, minutos_caminata Como Entero
    Definir trayecto, salida_min Como Entero
    Constante PORTERIA <- 10
    Constante COLCHON  <- 15

    Escribir "¿A qué hora es tu clase? (en minutos desde medianoche)"
    Leer hora_clase_min
    Escribir "¿Cuántos minutos de bus?"
    Leer minutos_bus
    Escribir "¿Cuántos minutos caminando hasta la parada?"
    Leer minutos_caminata

    trayecto <- minutos_bus + minutos_caminata + PORTERIA
    salida_min <- hora_clase_min - trayecto - COLCHON

    Escribir "Debes salir a los ", salida_min, " minutos desde medianoche"
FinAlgoritmo"""

ps.ejecutar_pseudo(CODIGO_GANCHO, entradas=["360", "45", "8"]).imprimir()
display(HTML(ps.diagrama(CODIGO_GANCHO)))   # el diagrama se dibuja SOLO''',
           etiquetas=("ava-figura",))

    # =========================================================================
    # Bloque 3 — Sección 3: concepto en corto (Parte A)
    # =========================================================================
    c.seccion(3, "Concepto en corto", 3, """Antes de escribir código hay que pensar. Cuatro pasos, siempre los mismos:

1. **Comprender**: cuenta el problema con tus palabras, sin mirar el enunciado.
2. **Analizar**: ¿qué datos **entran**? ¿qué **sale**? ¿qué **restricciones** hay?
3. **Diseñar**: escribe el pseudocódigo y mira el diagrama. Todavía no programes.
4. **Verificar**: prueba de escritorio con un caso cuyo resultado ya conozcas.
   Si no da, vuelve a comprender.""")

    c.md("""### La ficha de análisis

Es el formato del ejercicio E3 y del taller presencial. Ejemplo: *en el
parqueadero de la UIS se cobra una tarifa por hora más un recargo fijo por la
barrera; dadas las horas, calcular cuánto se paga.*

| Casilla | Pregunta | Ejemplo (parqueadero) |
|---|---|---|
| **Objetivo** | ¿Qué debe lograr, en una frase? | Calcular el valor a pagar. |
| **Entradas** | ¿Qué datos me tienen que dar? | `horas`, `tarifa_hora`, `recargo_fijo` |
| **Salidas** | ¿Qué entrego? | `total` |
| **Restricciones** | ¿Qué valores no tienen sentido? | `horas` ≥ 0; `tarifa_hora` > 0 |
| **Casos de prueba** | ¿Con qué datos compruebo? | 3 h a $2.500 + $1.000 → **8.500**; 0 h → **1.000** |

Los casos de prueba se escriben **antes** de programar. Y tres cosas que no se
confunden: una **variable** cambia de una ejecución a otra (`horas`); una
**constante** no cambia mientras el algoritmo corre y va en MAYÚSCULAS
(`TARIFA_HORA <- 2500`); una **restricción** se escribe en la ficha, todavía no
en el código (validar es de la Semana 3).

Los nombres de variable van en minúsculas, con guion bajo, sin tildes y que se
entiendan: `costo_pasaje`, no `x` ni `dato1`.

Ahora te toca a ti: clasifica los datos del problema de esta mañana.
""")

    # El recorte quitó figura_eps() y el bloque largo que explicaba la sigla, pero
    # el ensayo de abajo y el ejercicio 3 (congelado: 19 entregas) la exigen. Esta
    # es la versión mínima: la sigla, su significado y el problema de esta mañana
    # ya descompuesto, para que el alumno vea una vez cómo se llena antes de llenarlo.
    c.md("""### E-P-S: Entrada · Proceso · Salida

Antes de escribir un algoritmo se separa el problema en tres partes: qué **entra**
(los datos que te dan), qué **proceso** se hace con ellos (las operaciones, en orden),
y qué **sale** (el resultado). Las **constantes** son datos fijos que no se leen.
El problema de esta mañana, descompuesto así:

| | El problema de esta mañana |
|---|---|
| **Entrada** | `hora_clase_min` = 360 · `minutos_bus` = 45 · `minutos_caminata` = 8 |
| **Constantes** | `PORTERIA` = 10 · `COLCHON` = 15 |
| **Proceso** | `trayecto <- minutos_bus + minutos_caminata + PORTERIA` ⏎ `salida_min <- hora_clase_min - trayecto - COLCHON` |
| **Salida** | `salida_min` = 282, o sea las **4:42** |

Ahora te toca a ti: el formulario de abajo es el mismo que vas a llenar en el ejercicio 3.
""")

    c.code("ensayo_eps()")

    c.code("tarjeta_corte()")

    # =========================================================================
    # Bloque 4 — Sección 4: laboratorio (Parte B)
    # =========================================================================
    c.seccion(4, "Laboratorio", 11, """Bienvenido a la Parte B. De aquí en adelante todo se toca. El hilo es un solo
programa —el de la papelería de la Carrera 9— y con él vas a **predecir**,
**ejecutar**, **investigar** y **modificar**.""")

    c.md("""### 4.1 Pseudocódigo: español con reglas

Al cajero le dices «pregúntale cuántas copias y cóbrale» y él rellena los
huecos. **El computador no rellena huecos**: todo lo que no digas, no pasa. Con
seis palabras te alcanza para hoy: `Algoritmo`, `Definir`, `Constante`, `Leer`,
`Escribir` y la flecha `<-`.
""")

    c.code("chuleta()")

    c.md("""### Predecir *(no ejecutes todavía)*

```
Algoritmo CostoDeFotocopias
    Definir copias, total Como Entero
    Constante PRECIO_COPIA <- 100
    Constante ANILLADO <- 2500

    Escribir "¿Cuántas copias vas a sacar?"
    Leer copias

    total <- copias * PRECIO_COPIA + ANILLADO

    Escribir "Total a pagar: $", total
FinAlgoritmo
```

Vas a sacar **40 copias** anilladas. Antes de ejecutar, responde:
""")

    c.code("quiz_prediccion()")

    c.md("""### Ejecutar e investigar

El `"40"` es lo que el usuario iba a teclear. Ejecuta, y después cámbiala y
reejecútala:

1. Pon `entradas=["0"]`. ¿Tiene sentido el resultado?
2. **Borra la línea `Leer copias`**: la caja existe pero está vacía. Lee el error.
3. Sube `Leer copias` **arriba** del `Escribir`. Sigue funcionando, pero pide el
   dato antes de decir qué quiere: eso es un **error de lógica**, y el
   computador no te avisa.
""")

    c.code('''PAPELERIA = """Algoritmo CostoDeFotocopias
    // La papelería de la Carrera 9, frente a la UIS
    Definir copias, total Como Entero
    Constante PRECIO_COPIA <- 100
    Constante ANILLADO <- 2500

    Escribir "¿Cuántas copias vas a sacar?"
    Leer copias

    total <- copias * PRECIO_COPIA + ANILLADO

    Escribir "Total a pagar: $", total
FinAlgoritmo"""

# El "40" es lo que el usuario iba a teclear. Cámbialo y vuelve a ejecutar.
ps.ejecutar_pseudo(PAPELERIA, entradas=["40"]).imprimir()''')

    c.md("""### Modificar — ahora escribes tú

Tu banco de trabajo: pseudocódigo a la izquierda, entradas a la derecha, cuatro
botones. **Reto:** haz que también muestre cuánto cuestan las copias **sin** el
anillado.
""")

    c.code('ps.laboratorio(PAPELERIA, entradas=["40"])', etiquetas=("ava-figura",))

    c.md("""### 4.2 Prueba de escritorio (trazado manual)

Es seguir tu algoritmo **como si tú fueras el computador**, anotando cuánto vale
cada variable después de cada instrucción. Es la herramienta que caza los
**errores de lógica**, los únicos que el computador no señala. Mira una hecha
por el trazador; en el examen la haces tú, en papel.
""")

    c.code('ps.trazador(PAPELERIA, entradas=["40"])', etiquetas=("ava-figura",))

    c.md("""Tres reglas para que la tabla sirva: **una fila por instrucción ejecutada**;
en cada fila, el valor de **todas** las variables; y un guion (`—`) cuando la
caja existe pero está vacía. No es cero: cero es un valor.

### 4.3 Los cinco símbolos del diagrama de flujo

Un diagrama de flujo es un lenguaje con cinco palabras:
""")

    c.code("tabla_simbolos()")

    c.md("""Este es el diagrama del programa que acabas de ejecutar. **No lo dibujó
nadie**: lo dedujo el computador de tu pseudocódigo. Si el diagrama queda raro,
el algoritmo está raro.
""")

    c.code("display(HTML(ps.diagrama(PAPELERIA)))", etiquetas=("ava-figura",))

    c.md("""Reglas de un diagrama bien armado: **un solo INICIO**; **todo camino llega al
FIN**; las flechas tienen punta y una sola dirección; **del rombo salen dos
flechas rotuladas, y solo dos**; **una caja, una instrucción**.

**El puente a Flowgorithm.** En la Clase 2 armas este mismo diagrama en
Flowgorithm, bloque por bloque:

| Nuestro pseudocódigo | Bloque de Flowgorithm | Forma |
|---|---|---|
| `Algoritmo` / `FinAlgoritmo` | *Main* (ya viene puesto) | óvalos verdes |
| `Definir x Como Entero` | **Declare** · `x` · `Integer` | rectángulo de esquinas dobles |
| `Constante PASAJE <- 3200` | **Assign** en MAYÚSCULAS (no hay constantes) | rectángulo |
| `Leer x` / `Escribir e` | **Input** / **Output** | paralelogramo |
| `x <- expr` | **Assign** · `x` ← `expr` | rectángulo |
| `Entero / Real / Cadena / Logico` | `Integer / Real / String / Boolean` | — |

### 4.4 Una variable es una caja con nombre
""")

    c.code("figura_cajas()")

    c.md("""`copias <- 40` busca la caja `copias`, **bota lo que hubiera adentro** y mete
el 40. No hay historial. Por eso el renglón más raro de la programación,
`viajes <- viajes + 1`, no es una ecuación falsa: es una **orden** que se lee de
derecha a izquierda —mira qué hay en la caja, súmale 1, guarda el resultado en
la misma caja—. En Python es `viajes = viajes + 1`: **`=` no pregunta, ordena.**
""")

    c.code('''# Ejecuta esto tal cual. Después cambia el orden de las dos últimas líneas
# y vuelve a ejecutar: ¿por qué cambia el resultado?
viajes = 3
print("Antes: ", viajes)
viajes = viajes + 1
print("Después:", viajes)''')

    c.md("""### 4.5 Tipos: qué le cabe a cada caja

| Pseudocódigo | Python | Qué guarda | Ejemplos | Cuidado |
|---|---|---|---|---|
| `Entero` | `int` | sin decimales | `40`, `-3` | `3200` sin puntos: `3.200` es otra cosa |
| `Real` | `float` | con decimales | `3.85` | el separador decimal es el **punto** |
| `Cadena` | `str` | texto | `"Ana"`, `"3200"` | `"3200"` es texto, **no** el número |
| `Logico` | `bool` | verdadero o falso | `True`, `False` | con mayúscula inicial |

Para pasar de texto a número la conversión es **explícita**: la pides tú, con
`int("40")`, `float("3.85")` o, al revés, `str(40)`.
""")

    c.code('''# type() te dice de qué tipo es una caja. Ejecuta y mira la diferencia.
print(type(3200), type(3.85), type("3200"), type(True))

print(3200 + 100)                 # 3300    -> suma
print("3200" + "100")             # 3200100 -> ¡pega los textos!
print(int("3200") + int("100"))   # 3300    -> la conversión decide''')

    c.md("""### 4.6 `Leer` y `Escribir`, `input()` y `print()`

En este cuadernillo tu programa **no te pregunta nada**: lo que el usuario iba a
teclear se lo entregas de antemano, en una lista, con `ps.usar_entradas([...])`.
Esa lista es un **caso de prueba**, se puede repetir, y el código es idéntico al
que correrías en VS Code: `input()` sigue siendo `input()`.

> **`input()` siempre te entrega TEXTO.** Aunque el usuario teclee `40`, llega
> `"40"`. Si quieres sumar, tú decides: `int(input())`. En pseudocódigo `Leer`
> sabía el tipo porque lo declaraste con `Definir`; Python no lo adivina.

Por eso casi todos los ejercicios de hoy te piden una **función con parámetros**
en vez de una que pregunta: la que recibe sus datos se puede probar.
""")

    c.code('''# El MISMO algoritmo de la papelería, ahora en Python.
ps.usar_entradas(["40"])          # esto es "el usuario va a teclear 40"

PRECIO_COPIA = 100
ANILLADO = 2500

print("¿Cuántas copias vas a sacar?")
copias = int(input())             # input() da TEXTO; int() lo vuelve número

total = copias * PRECIO_COPIA + ANILLADO

print("Total a pagar: $", total, sep="")   # sep="" pega los pedazos, como Escribir''')

    c.md("""### 4.7 Lee el error

La celda que sigue **falla a propósito**. Ejecútala, lee la **última línea** del
mensaje rojo (ahí está el apellido del error) y arréglala cambiando
`"diecinueve"` por `"19"`.
""")

    c.code('''# Esta celda falla a propósito. Ejecútala y lee el mensaje rojo antes de arreglarla.
edad_escrita = "diecinueve"
edad = int(edad_escrita)
print("El año entrante cumples", edad + 1)''', etiquetas=("error-sembrado",))

    c.md("""| Error | Qué te está diciendo | Ejemplo típico |
|---|---|---|
| `SyntaxError` | «no entendí lo que escribiste» | falta una comilla |
| `NameError` | «ese nombre no existe» | `gasto_semanal` por `gasto_semana` |
| `TypeError` | «esos dos tipos no se mezclan así» | `"19" + 1` |
| `ValueError` | «el tipo está bien, el valor no me sirve» | `int("diecinueve")` |
""")

    # =========================================================================
    # Bloque 5 — Sección 5: los ocho ejercicios (80 puntos)
    # =========================================================================
    c.seccion(5, "Ocho ejercicios", 73, """Aquí se juega tu nota: **80 puntos** en ocho ejercicios, cada uno con dos
celdas: la tuya y la de prueba.

- **Los intentos no restan** y **las pistas tampoco**: `pista("E1")`,
  `pista("E2")`… no gastan preguntas del tutor.
- Una celda sin tocar da `NotImplementedError`: significa «aquí falta tu parte».
- Varios ejercicios se corrigen **ejecutando** tu pseudocódigo, no leyéndolo.""")

    # --- Ejercicio 1 ------------------------------------------------------
    c.ejercicio(
        numero=1, competencias=['I3'], titulo="Ordena el algoritmo", estrellas=1, puntos=5,
        enunciado="""Las siete líneas del algoritmo de la papelería quedaron revueltas:

```
A)     Leer copias
B)     Escribir "Total a pagar: $", total
C) Algoritmo CostoDeFotocopias
D)     total <- copias * 100 + 2500
E)     Escribir "¿Cuántas copias vas a sacar?"
F) FinAlgoritmo
G)     Definir copias, total Como Entero
```

Escribe en `orden_e1` la lista de letras en el orden correcto. Por ejemplo, si
creyeras que va primero la B y después la A, escribirías `["B", "A", ...]`.

**Pista gratis:** un algoritmo no puede usar una caja que todavía no existe, ni
imprimir un resultado que todavía no calculó.

El corrector no va a leer tu lista: va a **armar el pseudocódigo con tu orden y
ejecutarlo**.""",
        partida='''# Escribe la lista de letras en el orden correcto.
orden_e1 = []''',
        solucion='''orden_e1 = ["C", "G", "E", "A", "D", "B", "F"]''',
        pruebas='''LINEAS_E1 = {
    "A": "    Leer copias",
    "B": '    Escribir "Total a pagar: $", total',
    "C": "Algoritmo CostoDeFotocopias",
    "D": "    total <- copias * 100 + 2500",
    "E": '    Escribir "¿Cuántas copias vas a sacar?"',
    "F": "FinAlgoritmo",
    "G": "    Definir copias, total Como Entero",
}

assert isinstance(orden_e1, list), "orden_e1 debe ser una lista, por ejemplo ['C', 'G', ...]"
assert len(orden_e1) == 7, f"El algoritmo tiene 7 líneas y tú pusiste {len(orden_e1)}"
assert sorted(orden_e1) == list("ABCDEFG"), "Usa cada letra exactamente una vez, de la A a la G"
assert orden_e1[0] == "C", "Todo algoritmo empieza por su cabecera: la línea Algoritmo"
assert orden_e1[-1] == "F", "Y termina por FinAlgoritmo"

# El corrector no lee el orden: arma el algoritmo con él y lo ejecuta.
codigo_e1 = "\\n".join(LINEAS_E1[letra] for letra in orden_e1)
r_e1 = ps.ejecutar_pseudo(codigo_e1, entradas=["40"])
assert r_e1.ok, "Tu orden no se puede ejecutar. El motor dice: " + r_e1.error_corto
assert "6500" in r_e1.salida, (
    "Tu orden ejecuta, pero no da el total correcto. Con 40 copias debe salir 6500. "
    "Revisa que el cálculo ocurra DESPUÉS de leer las copias.")

corregir("ejercicio_1", orden_e1)
print("E1 correcto: el algoritmo quedó en orden y se ejecuta.")''',
        pistas=[
            "Empieza por lo que nunca cambia: la primera línea de cualquier "
            "algoritmo es <code>Algoritmo</code> y la última es "
            "<code>FinAlgoritmo</code>.",
            "Antes de usar una caja hay que crearla: <code>Definir</code> va antes "
            "que <code>Leer</code>. Y antes de pedirle algo al usuario, hay que "
            "decirle qué le vas a pedir.",
            "El orden es: cabecera, Definir, el mensaje, el Leer, el cálculo, "
            "mostrar el resultado, FinAlgoritmo.",
        ],
    )

    # --- Ejercicio 2 ------------------------------------------------------
    c.ejercicio(
        numero=2, competencias=[], titulo="Cada símbolo con su significado", estrellas=1, puntos=5,
        enunciado="""Completa el diccionario `simbolos_e2` emparejando cada forma con lo que
representa. Los valores posibles son exactamente estos cinco textos:

`"inicio_fin"` · `"entrada_salida"` · `"proceso"` · `"decision"` · `"flujo"`

Cada significado se usa **una sola vez**. Si dudas, vuelve a la tabla de los
cinco símbolos de la sección 4.3.""",
        partida='''# Empareja cada símbolo con su significado.
simbolos_e2 = {
    "ovalo":         ...,
    "paralelogramo": ...,
    "rectangulo":    ...,
    "rombo":         ...,
    "flecha":        ...,
}''',
        solucion='''simbolos_e2 = {
    "ovalo":         "inicio_fin",
    "paralelogramo": "entrada_salida",
    "rectangulo":    "proceso",
    "rombo":         "decision",
    "flecha":        "flujo",
}''',
        pruebas='''VALIDOS_E2 = {"inicio_fin", "entrada_salida", "proceso", "decision", "flujo"}

assert isinstance(simbolos_e2, dict), "simbolos_e2 debe ser un diccionario"
assert set(simbolos_e2.keys()) == {"ovalo", "paralelogramo", "rectangulo", "rombo", "flecha"}, (
    "Las claves deben ser exactamente: ovalo, paralelogramo, rectangulo, rombo, flecha")
assert all(isinstance(v, str) for v in simbolos_e2.values()), (
    "Cada significado va entre comillas, como texto. Los cinco válidos son: "
    + ", ".join(sorted(VALIDOS_E2)))
assert set(simbolos_e2.values()) == VALIDOS_E2, (
    "Cada significado se usa una sola vez, y los cinco tienen que aparecer. Son: "
    + ", ".join(sorted(VALIDOS_E2)))

corregir("ejercicio_2", simbolos_e2)
print("E2 correcto: ya reconoces los cinco símbolos.")''',
        pistas=[
            "Piensa en la forma: ¿cuál de las cinco se parece a una puerta por "
            "donde entra y sale algo?",
            "El rombo tiene cuatro puntas: una para entrar y dos para salir (la "
            "cuarta no se usa). Solo una de las cinco opciones necesita dos "
            "salidas.",
            "Óvalo, el que abre y cierra. Paralelogramo, el que deja pasar datos. "
            "Rectángulo, el que calcula. Rombo, el que pregunta. Flecha, la que "
            "ordena.",
        ],
    )

    # --- Ejercicio 3 ------------------------------------------------------
    c.ejercicio(
        numero=3, competencias=['I3', 'I1'], titulo="La ficha de análisis", estrellas=2, puntos=10,
        enunciado="""**Problema:** *En el parqueadero de la UIS se cobra una **tarifa por hora** y,
además, un **recargo fijo** por el uso de la barrera. Dado el número de
**horas** que estuvo el carro, calcular cuánto debe pagar.*

Llena el diccionario `ficha_e3` con los cinco campos de la ficha de análisis:

- `"entradas"`: la lista de los **nombres de variable** de los datos que entran
  (en minúsculas, con guion bajo, sin tildes).
- `"proceso"`: **una sola línea de pseudocódigo** que calcule el resultado
  usando esos nombres y guardándolo en `total`.
- `"salida"`: la lista con el nombre de lo que se entrega.
- `"restricciones"`: una lista con al menos **dos** restricciones, escritas como
  frases.
- `"casos_prueba"`: una lista de al menos **dos** tuplas `(horas, tarifa_hora,
  recargo_fijo, total_esperado)`.

Los nombres de las entradas están fijados a propósito (el corrector los necesita
exactos): **`horas`**, **`tarifa_hora`**, **`recargo_fijo`**.

Tu línea de proceso no se lee: **se ejecuta** dentro de un algoritmo de verdad.""",
        partida='''ficha_e3 = {
    "entradas": [...],
    "proceso": "...",
    "salida": [...],
    "restricciones": [...],
    "casos_prueba": [...],
}''',
        solucion='''ficha_e3 = {
    "entradas": ["horas", "tarifa_hora", "recargo_fijo"],
    "proceso": "total <- horas * tarifa_hora + recargo_fijo",
    "salida": ["total"],
    "restricciones": [
        "horas no puede ser negativa",
        "tarifa_hora debe ser mayor que cero",
    ],
    "casos_prueba": [
        (3, 2500, 1000, 8500),
        (0, 2500, 1000, 1000),
    ],
}''',
        pruebas='''assert isinstance(ficha_e3, dict), "ficha_e3 debe ser un diccionario"
faltan_e3 = {"entradas", "proceso", "salida", "restricciones", "casos_prueba"} - set(ficha_e3)
assert not faltan_e3, "Te faltan campos en la ficha: " + ", ".join(sorted(faltan_e3))

assert set(ficha_e3["entradas"]) == {"horas", "tarifa_hora", "recargo_fijo"}, (
    "Las entradas deben ser exactamente horas, tarifa_hora y recargo_fijo. "
    "Si pusiste 'total', recuerda que eso SALE, no entra.")
assert ficha_e3["salida"] == ["total"], "La salida es una sola cosa: ['total']"

assert len(ficha_e3["restricciones"]) >= 2, (
    "Escribe al menos dos restricciones: valores que NO tendrían sentido en este problema.")
assert all(isinstance(t, str) and len(t.strip()) >= 10 for t in ficha_e3["restricciones"]), (
    "Cada restricción debe ser una frase, no una palabra suelta.")

# El proceso se comprueba EJECUTÁNDOLO.
proceso_e3 = ficha_e3["proceso"]
assert isinstance(proceso_e3, str), "El proceso es una línea de pseudocódigo, en texto"
assert "<-" in proceso_e3, "En pseudocódigo se guarda con la flecha <-, no con ="
assert proceso_e3.split("<-")[0].strip() == "total", "El resultado debe guardarse en 'total'"

programa_e3 = (
    "Algoritmo Parqueadero\\n"
    "    Definir horas, tarifa_hora, recargo_fijo, total Como Entero\\n"
    "    horas <- 3\\n"
    "    tarifa_hora <- 2500\\n"
    "    recargo_fijo <- 1000\\n"
    f"    {proceso_e3.strip()}\\n"
    "    Escribir total\\n"
    "FinAlgoritmo")
r_e3 = ps.ejecutar_pseudo(programa_e3)
assert r_e3.ok, "Tu línea de proceso no se puede ejecutar. El motor dice: " + r_e3.error_corto
assert r_e3.memoria["total"] == 8500, (
    f"Con 3 horas a $2.500 y $1.000 de recargo el total es 8500, y tu proceso dio "
    f"{r_e3.memoria['total']}. Revisa si multiplicaste antes de sumar.")

assert len(ficha_e3["casos_prueba"]) >= 2, "Define al menos dos casos de prueba."
for caso in ficha_e3["casos_prueba"]:
    assert len(caso) == 4, "Cada caso es (horas, tarifa_hora, recargo_fijo, total_esperado)"
    h, t, rc, esperado = caso
    assert h * t + rc == esperado, (
        f"El caso {caso} no cuadra: con {h} horas a {t} más {rc} el total sería {h * t + rc}.")
print("E3 correcto: la ficha está completa y tu proceso da el resultado esperado.")''',
        pistas=[
            "Una entrada es un dato que <b>alguien te tiene que dar</b>. Un "
            "resultado que tú calculas no es una entrada.",
            "El proceso es una sola línea con la forma <code>total &lt;- … * … + "
            "…</code>. Piensa qué se multiplica y qué se suma.",
            "<code>total &lt;- horas * tarifa_hora + recargo_fijo</code>. Y para "
            "los casos de prueba, uno fácil es 3 horas a $2.500 con $1.000 de "
            "recargo: 8.500.",
        ],
    )

    # --- Ejercicio 4 ------------------------------------------------------
    c.ejercicio(
        numero=4, competencias=['I1'], titulo="Completa el pseudocódigo", estrellas=2, puntos=10,
        enunciado="""Este algoritmo calcula **cuánto te sobra en la tarjeta de Metrolínea** después
de una semana. Le falta una línea: la que hace la cuenta.

Reemplaza los tres guiones bajos `___` por la expresión correcta. **No cambies
nada más**: ni los nombres, ni el orden, ni los mensajes.

El corrector va a **ejecutar tu pseudocódigo** con dos recargas distintas:

| Recargas | Debe sobrar |
|---|---|
| $25.000 | $5.800 |
| $50.000 | $30.800 |""",
        partida="""pseudo_e4 = \"\"\"Algoritmo RecargaMetrolinea
    Definir saldo, sobra Como Entero
    Constante PASAJE <- 3200
    Constante VIAJES <- 6

    Escribir "¿Cuánto vas a recargar?"
    Leer saldo

    sobra <- ___

    Escribir "Te sobran $", sobra
FinAlgoritmo\"\"\"""",
        solucion="""pseudo_e4 = \"\"\"Algoritmo RecargaMetrolinea
    Definir saldo, sobra Como Entero
    Constante PASAJE <- 3200
    Constante VIAJES <- 6

    Escribir "¿Cuánto vas a recargar?"
    Leer saldo

    sobra <- saldo - VIAJES * PASAJE

    Escribir "Te sobran $", sobra
FinAlgoritmo\"\"\"""",
        pruebas='''assert isinstance(pseudo_e4, str), "pseudo_e4 debe seguir siendo una cadena de texto"
assert "___" not in pseudo_e4, "Todavía quedan guiones bajos ___ sin reemplazar."
assert "Constante PASAJE <- 3200" in pseudo_e4, "No cambies las constantes del algoritmo."

for recarga, esperado in [("25000", 5800), ("50000", 30800)]:
    r_e4 = ps.ejecutar_pseudo(pseudo_e4, entradas=[recarga])
    assert r_e4.ok, (
        f"Con una recarga de ${recarga} tu algoritmo falla. El motor dice: {r_e4.error_corto}")
    assert "sobra" in r_e4.memoria, "El resultado debe quedar guardado en la variable 'sobra'."
    assert r_e4.memoria["sobra"] == esperado, (
        f"Con ${recarga} deben sobrar ${esperado}, y tu algoritmo dejó {r_e4.memoria['sobra']}. "
        f"Recuerda: son 6 viajes a $3.200 cada uno.")
    assert str(esperado) in r_e4.salida, (
        "El algoritmo calcula bien pero no está mostrando el resultado. "
        "Revisa la línea Escribir.")
print("E4 correcto: tu pseudocódigo se ejecuta y da lo esperado en los dos casos.")''',
        pistas=[
            "Lo que sobra es lo que recargaste <b>menos</b> lo que te vas a "
            "gastar. ¿Y cuánto te vas a gastar?",
            "El gasto son dos operaciones en una sola línea: los viajes "
            "multiplicados por el pasaje. Y eso se le resta al saldo.",
            "<code>sobra &lt;- saldo - VIAJES * PASAJE</code>. Puedes escribirlo "
            "con paréntesis si te da más claridad: <code>saldo - (VIAJES * "
            "PASAJE)</code>; da lo mismo, porque el <code>*</code> se hace antes "
            "que el <code>-</code>.",
        ],
    )

    # --- Ejercicio 5 ------------------------------------------------------
    c.ejercicio(
        numero=5, competencias=['I3'], titulo="Prueba de escritorio", estrellas=2, puntos=10,
        enunciado="""Este algoritmo descuenta dos pasajes de una tarjeta de Metrolínea:

```
1  Algoritmo ViajesDeLaSemana
2      Definir saldo, viajes Como Entero
3      Constante PASAJE <- 3200
4      saldo <- 12000
5      viajes <- 0
6      saldo <- saldo - PASAJE
7      viajes <- viajes + 1
8      saldo <- saldo - PASAJE
9      viajes <- viajes + 1
10     Escribir "Saldo final: ", saldo
11 FinAlgoritmo
```

**Hazlo a mano, en papel.** Recorre las instrucciones de la 2 a la 10 y anota,
después de cada una, cuánto valen `saldo` y `viajes`. Después escribe esa tabla
en `traza_e5` como una lista de **9 tuplas** `(saldo, viajes)`, una por
instrucción ejecutada.

Usa **`None`** cuando la caja exista pero todavía esté vacía. `None` no es lo
mismo que 0: cero es un valor; `None` es «no hay nada adentro».

**Nota de honestidad.** Sí, podrías ejecutar el algoritmo con el trazador y
copiar la respuesta. También podrías copiar un examen. El día del parcial no vas
a tener trazador, y esta es exactamente la destreza que se evalúa allá. Hazla a
mano.""",
        partida='''# Una tupla (saldo, viajes) por cada instrucción ejecutada, de la línea 2 a la 10.
traza_e5 = [
    (None, None),   # 2  Definir saldo, viajes Como Entero
    # ...y así hasta la línea 10. Son 9 filas en total.
]''',
        solucion='''traza_e5 = [
    (None,  None),   # 2  Definir saldo, viajes Como Entero
    (None,  None),   # 3  Constante PASAJE <- 3200
    (12000, None),   # 4  saldo <- 12000
    (12000, 0),      # 5  viajes <- 0
    (8800,  0),      # 6  saldo <- saldo - PASAJE
    (8800,  1),      # 7  viajes <- viajes + 1
    (5600,  1),      # 8  saldo <- saldo - PASAJE
    (5600,  2),      # 9  viajes <- viajes + 1
    (5600,  2),      # 10 Escribir "Saldo final: ", saldo
]''',
        pruebas='''CODIGO_E5 = """Algoritmo ViajesDeLaSemana
    Definir saldo, viajes Como Entero
    Constante PASAJE <- 3200
    saldo <- 12000
    viajes <- 0
    saldo <- saldo - PASAJE
    viajes <- viajes + 1
    saldo <- saldo - PASAJE
    viajes <- viajes + 1
    Escribir "Saldo final: ", saldo
FinAlgoritmo"""

# La respuesta NO está escrita aquí: se calcula ejecutando el algoritmo.
esperada_e5 = ps.ejecutar_pseudo(CODIGO_E5).tabla_traza(["saldo", "viajes"])

assert isinstance(traza_e5, list), "traza_e5 debe ser una lista de tuplas"
assert len(traza_e5) == len(esperada_e5), (
    f"El algoritmo ejecuta {len(esperada_e5)} instrucciones y tu tabla tiene "
    f"{len(traza_e5)} filas. Cuenta desde el Definir (línea 2) hasta el Escribir (línea 10).")

for i, (mia, ok) in enumerate(zip(traza_e5, esperada_e5), start=2):
    assert isinstance(mia, (tuple, list)) and len(mia) == 2, (
        f"La fila de la línea {i} debe ser una tupla (saldo, viajes)")
    assert tuple(mia) == tuple(ok), (
        f"Después de la línea {i} debería quedar saldo={ok[0]} y viajes={ok[1]}, "
        f"pero tú anotaste saldo={mia[0]} y viajes={mia[1]}. "
        "Revisa esa instrucción: ¿qué caja toca y con qué valor?")
print("E5 correcto: tu prueba de escritorio coincide paso a paso con la ejecución real.")''',
        pistas=[
            "<code>Definir</code> crea la caja pero no le mete nada: en esas filas "
            "los dos valores son <code>None</code>. <code>Constante</code> tampoco "
            "toca <code>saldo</code> ni <code>viajes</code>.",
            "<code>saldo &lt;- saldo - PASAJE</code> se lee de derecha a izquierda: "
            "primero se mira cuánto hay en <code>saldo</code> (12.000), se le resta "
            "3.200, y <b>ese</b> resultado vuelve a la caja.",
            "Después de la línea 6, <code>saldo</code> vale 8.800. Después de la 8, "
            "vale 5.600. Y <code>viajes</code> va 0, 1, 2. La última fila (el "
            "<code>Escribir</code>) no cambia nada: se repiten los mismos valores.",
        ],
    )

    # --- Ejercicio 6 ------------------------------------------------------
    c.ejercicio(
        numero=6, competencias=[], titulo="Tipos y conversiones", estrellas=3, puntos=10,
        enunciado="""Un formulario web te entrega los datos de un estudiante. **Todo llega como
texto**, porque así funcionan los formularios (y `input()`):

```python
datos = {"nombre": "Valentina", "edad": "19", "promedio": "3.85"}
```

Crea estas cinco variables, cada una **del tipo correcto**:

| Variable | Qué debe contener | Tipo |
|---|---|---|
| `nombre_e6` | el nombre, tal cual | `str` |
| `edad_e6` | la edad como número entero | `int` |
| `promedio_e6` | el promedio como número con decimales | `float` |
| `es_becada_e6` | `True` si el promedio es **mayor o igual a 4.0** | `bool` |
| `ficha_e6` | el texto `"Valentina tiene 19 anos"` armado con las variables anteriores | `str` |

Para `ficha_e6` **no escribas el texto a mano**: constrúyelo pegando las
variables, y usa `str()` donde haga falta. (Sin tilde en «anos», para no pelear
con las tildes todavía.)""",
        partida='''datos = {"nombre": "Valentina", "edad": "19", "promedio": "3.85"}

nombre_e6 = ...
edad_e6 = ...
promedio_e6 = ...
es_becada_e6 = ...
ficha_e6 = ...''',
        solucion='''nombre_e6 = datos["nombre"]
edad_e6 = int(datos["edad"])
promedio_e6 = float(datos["promedio"])
es_becada_e6 = promedio_e6 >= 4.0
ficha_e6 = nombre_e6 + " tiene " + str(edad_e6) + " anos"''',
        pruebas='''assert type(nombre_e6) is str, "nombre_e6 debe ser texto (str)"
assert nombre_e6 == "Valentina", "nombre_e6 debe salir de datos['nombre']"

assert type(edad_e6) is int, (
    f"edad_e6 debe ser un entero (int) y es {type(edad_e6).__name__}. "
    "Recuerda que datos['edad'] es el TEXTO '19': hay que convertirlo con int().")
assert edad_e6 == 19, "edad_e6 debe valer 19"

assert type(promedio_e6) is float, (
    f"promedio_e6 debe ser un número con decimales (float) y es {type(promedio_e6).__name__}. "
    "Se convierte con float(), no con int(): int('3.85') ni siquiera funciona.")
assert abs(promedio_e6 - 3.85) < 1e-9, "promedio_e6 debe valer 3.85"

assert type(es_becada_e6) is bool, (
    f"es_becada_e6 debe ser True o False (bool) y es {type(es_becada_e6).__name__}. "
    "Una comparación como  promedio_e6 >= 4.0  ya da un bool.")
assert es_becada_e6 is False, (
    "Con promedio 3.85 la respuesta es False: 3.85 no llega a 4.0. "
    "Ojo, escribe False (mayúscula inicial), no 'False' entre comillas.")

assert type(ficha_e6) is str, "ficha_e6 debe ser texto"
assert ficha_e6 == "Valentina tiene 19 anos", (
    f"ficha_e6 debe quedar exactamente 'Valentina tiene 19 anos' y quedó '{ficha_e6}'. "
    "Cuida los espacios: 'tiene ' lleva espacio al final.")
print("E6 correcto: cada dato quedó en su tipo y la ficha se armó bien.")''',
        pistas=[
            "<code>datos[\"edad\"]</code> es el texto <code>\"19\"</code>, no el "
            "número 19. Fíjate en las comillas: eso siempre te dice que es un "
            "<code>str</code>.",
            "Hay tres conversiones: <code>int()</code>, <code>float()</code> y "
            "<code>str()</code>. Necesitas las tres en este ejercicio.",
            "<code>es_becada_e6</code> no se escribe a mano: es el resultado de "
            "una comparación, <code>promedio_e6 &gt;= 4.0</code>. Y para "
            "<code>ficha_e6</code>, <code>edad_e6</code> es un número: hay que "
            "volverlo texto con <code>str()</code> antes de pegarlo.",
        ],
    )

    # --- Ejercicio 7 ------------------------------------------------------
    c.ejercicio(
        numero=7, competencias=['I3', 'I1'], titulo="Traduce el algoritmo a Python", estrellas=3, puntos=15,
        enunciado="""Este es el algoritmo del gancho, el de «¿a qué hora salgo de la casa?»:

```
Algoritmo AQueHoraSalgo
    Definir hora_clase_min, minutos_bus, minutos_caminata Como Entero
    Definir trayecto, salida_min Como Entero
    Constante PORTERIA <- 10
    Constante COLCHON  <- 15

    trayecto   <- minutos_bus + minutos_caminata + PORTERIA
    salida_min <- hora_clase_min - trayecto - COLCHON
FinAlgoritmo
```

Escríbelo como una **función de Python** que reciba los tres datos y
**retorne** `salida_min`:

```python
def hora_de_salida(hora_clase_min, minutos_bus, minutos_caminata):
    ...
```

Las dos constantes van **dentro** de la función, en mayúsculas. La función **no
imprime nada y no pregunta nada**: solo recibe y retorna. (Ya sabes por qué: una
función que recibe sus datos se puede probar; una que pregunta, no.)

Comprobación rápida: con la clase a las 6:00 (que son 360 minutos desde
medianoche), 45 de bus y 8 de caminata, debe retornar **282**, que son las
4:42.""",
        partida='''def hora_de_salida(hora_clase_min, minutos_bus, minutos_caminata):
    # Las dos constantes van aquí adentro, en mayúsculas.
    # Después las dos cuentas del pseudocódigo, y al final: return salida_min
    ...''',
        solucion='''def hora_de_salida(hora_clase_min, minutos_bus, minutos_caminata):
    PORTERIA = 10
    COLCHON = 15
    trayecto = minutos_bus + minutos_caminata + PORTERIA
    salida_min = hora_clase_min - trayecto - COLCHON
    return salida_min''',
        pruebas='''import inspect

assert callable(hora_de_salida), "hora_de_salida debe ser una función"
firma_e7 = list(inspect.signature(hora_de_salida).parameters)
assert firma_e7 == ["hora_clase_min", "minutos_bus", "minutos_caminata"], (
    f"La función debe recibir exactamente (hora_clase_min, minutos_bus, minutos_caminata) "
    f"y la tuya recibe {firma_e7}")

CASOS_E7 = [
    ((360, 45,  8), 282),   # clase a las 6:00, el caso del gancho -> 4:42
    ((420, 60,  5), 330),   # clase a las 7:00 desde más lejos     -> 5:30
    ((360,  0,  0), 335),   # vives al frente: solo portería y colchón
    ((480, 30, 12), 413),   # clase a las 8:00
]
for args_e7, esperado_e7 in CASOS_E7:
    obtenido_e7 = hora_de_salida(*args_e7)
    assert obtenido_e7 is not None, (
        "Tu función no retorna nada. ¿Se te olvidó la palabra return?")
    assert obtenido_e7 == esperado_e7, (
        f"Con hora_clase_min={args_e7[0]}, bus={args_e7[1]} y caminata={args_e7[2]} "
        f"debe retornar {esperado_e7} y retornó {obtenido_e7}. "
        "Acuérdate de restar TAMBIÉN los 10 de portería y los 15 de colchón.")

# La función de Python y el pseudocódigo tienen que dar lo mismo.
REFERENCIA_E7 = """Algoritmo AQueHoraSalgo
    Definir hora_clase_min, minutos_bus, minutos_caminata Como Entero
    Definir trayecto, salida_min Como Entero
    Constante PORTERIA <- 10
    Constante COLCHON  <- 15
    Leer hora_clase_min
    Leer minutos_bus
    Leer minutos_caminata
    trayecto   <- minutos_bus + minutos_caminata + PORTERIA
    salida_min <- hora_clase_min - trayecto - COLCHON
    Escribir salida_min
FinAlgoritmo"""
r_e7 = ps.ejecutar_pseudo(REFERENCIA_E7, entradas=["390", "50", "7"])
assert hora_de_salida(390, 50, 7) == r_e7.memoria["salida_min"], (
    "Tu función en Python y el pseudocódigo del enunciado dan resultados distintos. "
    "Compáralos línea por línea.")
print("E7 correcto: tu traducción a Python coincide con el pseudocódigo en los 5 casos.")''',
        pistas=[
            "Cada línea del pseudocódigo se convierte en una línea de Python. "
            "<code>&lt;-</code> se vuelve <code>=</code>, y las dos constantes se "
            "escriben igual, en mayúsculas.",
            "El pseudocódigo hace la cuenta en dos pasos: primero arma "
            "<code>trayecto</code>, después calcula <code>salida_min</code>. Copia "
            "esos dos pasos tal cual; no intentes hacerlo todo en una línea.",
            "La última línea de la función tiene que ser <code>return "
            "salida_min</code>. Sin <code>return</code>, la función calcula bien y "
            "después bota el resultado a la basura.",
        ],
    )

    # --- Ejercicio 8 ------------------------------------------------------
    c.ejercicio(
        numero=8, competencias=['I3', 'I1'], titulo="El mismo algoritmo, en los dos idiomas",
        estrellas=4, puntos=15,
        enunciado="""**Problema:** *Calcular cuánto vas a gastar en pasajes durante todo el
semestre.* Entran tres datos: cuántos **viajes haces por semana**, cuántas
**semanas** dura el semestre y cuánto cuesta el **pasaje**. Sale un solo número:
el **gasto total**.

Esta es la evidencia de la semana: el mismo algoritmo escrito en los tres
idiomas. El diagrama lo dibuja el computador a partir de tu pseudocódigo, así
que te toca escribir dos cosas:

**1. `pseudo_e8`** — el algoritmo en pseudocódigo, con `Definir`, tres `Leer`
(en el orden viajes → semanas → pasaje), el cálculo, y un `Escribir` que muestre
el total. El resultado debe quedar en una variable llamada **`total`**.

**2. `gasto_semestre()`** — una función de Python que **lee los tres datos con
`input()`** y **retorna** el total como entero.

```python
def gasto_semestre():
    viajes = int(input())
    ...
```

No te preocupes por teclear: el corrector le pasa los datos con
`ps.entradas([...])`, tal como practicaste en el laboratorio. Tu `input()` es un
`input()` de verdad.

Comprobación: 10 viajes por semana, 16 semanas, pasaje de $3.200 →
**$512.000**.""",
        partida='''# 1. Tu algoritmo en pseudocódigo. Completa lo que falta.
pseudo_e8 = """Algoritmo GastoDelSemestre
    Definir viajes, semanas, pasaje, total Como Entero

    Escribir "¿Cuántos viajes haces por semana?"
    Leer viajes

FinAlgoritmo"""


# 2. El mismo algoritmo como función de Python.
def gasto_semestre():
    viajes = int(input())
    ...''',
        solucion='''pseudo_e8 = """Algoritmo GastoDelSemestre
    Definir viajes, semanas, pasaje, total Como Entero

    Escribir "¿Cuántos viajes haces por semana?"
    Leer viajes
    Escribir "¿Cuántas semanas dura el semestre?"
    Leer semanas
    Escribir "¿Cuánto cuesta el pasaje?"
    Leer pasaje

    total <- viajes * semanas * pasaje

    Escribir "Vas a gastar $", total
FinAlgoritmo"""


def gasto_semestre():
    viajes = int(input())
    semanas = int(input())
    pasaje = int(input())
    return viajes * semanas * pasaje''',
        pruebas='''import inspect
from IPython.display import HTML, display

CASOS_E8 = [
    (["10", "16", "3200"], 512000),
    (["4",  "18", "2900"], 208800),
    (["0",  "16", "3200"], 0),
]

# -- Parte 1: el pseudocódigo -------------------------------------------------
assert isinstance(pseudo_e8, str) and pseudo_e8.strip(), "pseudo_e8 debe ser tu algoritmo en texto"
usadas_e8 = ps.ejecutar_pseudo(pseudo_e8, entradas=["10", "16", "3200"]).instrucciones_usadas
for palabra in ("Definir", "Leer", "Escribir", "Asignar"):
    assert palabra in usadas_e8, (
        f"A tu pseudocódigo le falta al menos un(a) {palabra}. "
        "El algoritmo tiene que definir las cajas, leer los tres datos, calcular y mostrar.")

for entradas_caso, esperado_e8 in CASOS_E8:
    r_e8 = ps.ejecutar_pseudo(pseudo_e8, entradas=entradas_caso)
    assert r_e8.ok, (
        f"Tu pseudocódigo falla con las entradas {entradas_caso}. "
        f"El motor dice: {r_e8.error_corto}")
    assert "total" in r_e8.memoria, (
        "El resultado debe quedar guardado en una variable llamada 'total'")
    assert r_e8.memoria["total"] == esperado_e8, (
        f"Con {entradas_caso[0]} viajes, {entradas_caso[1]} semanas y pasaje de "
        f"${entradas_caso[2]} el total es {esperado_e8}, y tu algoritmo dio "
        f"{r_e8.memoria['total']}.")
    assert str(esperado_e8) in r_e8.salida, (
        "Tu algoritmo calcula bien pero no muestra el total. Revisa el Escribir del final.")

# -- Parte 2: la función de Python --------------------------------------------
assert callable(gasto_semestre), "gasto_semestre debe ser una función"
assert list(inspect.signature(gasto_semestre).parameters) == [], (
    "gasto_semestre() no recibe parámetros: los tres datos los pide con input()")

for entradas_caso, esperado_e8 in CASOS_E8:
    with ps.entradas(entradas_caso):
        obtenido_e8 = gasto_semestre()
    assert obtenido_e8 is not None, "A tu función le falta el return"
    assert obtenido_e8 == esperado_e8, (
        f"Con las entradas {entradas_caso} debe retornar {esperado_e8} "
        f"y retornó {obtenido_e8}.")
    assert type(obtenido_e8) is int, (
        f"El total debe ser un entero (int) y es {type(obtenido_e8).__name__}. "
        "Si usaste float() en vez de int() al convertir, ahí está el problema.")

# -- Parte 3: los dos idiomas tienen que decir lo mismo -----------------------
with ps.entradas(["7", "16", "3500"]):
    py_e8 = gasto_semestre()
pseudo_total_e8 = ps.ejecutar_pseudo(pseudo_e8, entradas=["7", "16", "3500"]).memoria["total"]
assert py_e8 == pseudo_total_e8, (
    f"Tu pseudocódigo da {pseudo_total_e8} y tu Python da {py_e8} con los mismos datos. "
    "Son el mismo algoritmo: tienen que coincidir siempre.")
print("E8 correcto. Escribiste el mismo algoritmo en dos idiomas y los dos dicen lo mismo.")
print("Mira su diagrama de flujo:")
display(HTML(ps.diagrama(pseudo_e8)))''',
        pistas=[
            "Empieza por el pseudocódigo, que es el que puedes ejecutar y corregir "
            "rápido. Tres <code>Leer</code> seguidos, en el mismo orden en que el "
            "corrector te va a dar los datos.",
            "El cálculo es una sola multiplicación de tres factores: <code>total "
            "&lt;- viajes * semanas * pasaje</code>. Y en Python, exactamente lo "
            "mismo con <code>=</code>.",
            "En la función, cada <code>input()</code> te entrega TEXTO: los tres "
            "van envueltos en <code>int()</code>. Y la última línea es "
            "<code>return viajes * semanas * pasaje</code> (o <code>return "
            "total</code> si lo guardaste antes).",
        ],
    )

    # =========================================================================
    # Bloque 6 — Sección 6: el reto
    # =========================================================================
    c.seccion(6, "El reto", 1, """*(opcional, sin nota)* **Llévate tu diagrama a la clase.** La celda de abajo
imprime el **guion** —los bloques que tienes que arrastrar en Flowgorithm, en
orden— y deja el archivo `mi_algoritmo.fprg` (descárgalo desde *File → Open*,
clic derecho → *Download*). Si el `.fprg` no abre en la sala, el guion impreso
es el camino seguro.""")

    c.code('''# Si todavía no hiciste E8, se usa el algoritmo de la papelería.
mi_algoritmo = pseudo_e8 if "pseudo_e8" in globals() else PAPELERIA

ps.guion_flowgorithm(mi_algoritmo)
ps.exportar_flowgorithm(mi_algoritmo, "mi_algoritmo.fprg")''')

    # =========================================================================
    # Bloque 7 — Sección 7: el tutor
    # =========================================================================
    c.seccion(7, "Habla con el asistente", 1, """Tienes **5 preguntas** en este cuadernillo (botón de abajo a la derecha). Dos
que valen la pena:

1. *«Escribí este pseudocódigo [pégalo]. No me lo corrijas: hazme tres preguntas
   que me ayuden a encontrar yo mismo el error.»*
2. *«Hice la prueba de escritorio del ejercicio 5 y me dio distinto al
   corrector. Pregúntame paso por paso qué anoté.»*

Ninguna pide la solución: todas piden **que te pregunte a ti**. Y antes de
gastar una, **haz clic en la celda del ejercicio donde estás atascado**: el
panel toma el enunciado, tu código y el último error.""")

    # =========================================================================
    # Bloque 8 — Sección 8: cierre
    # =========================================================================
    c.seccion(8, "Cierre", 1, """Marca honestamente lo que ya puedes hacer. No tiene nota: es tu plan para la
semana.""")

    c.code("radar_salida()")

    c.code("cierre()")

    return c


if __name__ == "__main__":  # pragma: no cover - atajo para autorar
    construir().escribir(
        os.path.join(os.path.dirname(os.path.dirname(AQUI)),
                     "notebook_semana", "semana_02", "cuadernillo.ipynb"))
