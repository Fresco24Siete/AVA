#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 2: «Del problema al algoritmo».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 2 — Fundamentos para la solución de problemas.

80 puntos de nbgrader en ocho ejercicios, 80 XP lúdicos y la insignia
«Traductora / Traductor de algoritmos». Cubre lo que en la planeación vieja eran
tres cuadernos (planteamiento, pseudocódigo y diagramas), así que va partido en
dos partes con un corte explícito: la Parte A se hace después de la Clase 1 y la
Parte B después de la Clase 2.

Tres decisiones que se salen del documento de diseño y por qué:

- El diseño copiaba `pseudo_uis.py` a `/etc/jupyter/` dentro de la imagen. Aquí
  se **incrusta en el `.ipynb`**, junto al motor y al contenido de la semana
  (`modulos=[...]`), que es lo que ya está construido y probado: así un
  cuadernillo publicado no cambia de intérprete cuando se reconstruye la imagen.
  Como el módulo se ejecuta en el espacio de nombres del notebook y no se
  importa, `contenido.py` reconstruye la fachada `ps` con la que el estudiante
  lo llama.
- La gráfica del gancho era matplotlib; aquí es un SVG escrito en Python puro
  (`grafica_madrugada`), por la misma razón que en la semana 1: matplotlib son
  ~80 MB de RAM por kernel y la VM del curso tiene 2 GB para todos.
- Los widgets del diseño se llamaban `ava.parsons` y `ava.analisis_eps`. En el
  motor de este repositorio son `ava.ordenar` y un ensayo propio de la semana
  (`ensayo_eps`), que es donde vive el formulario E-P-S.
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
        meta_xp=80,
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

Esta semana aprendes a decir lo mismo en tres idiomas: **pseudocódigo** (para
pensar), **diagrama de flujo** (para ver) y **Python** (para ejecutar).

Y hay algo que quizá no te esperas: el pseudocódigo de este cuadernillo **se
ejecuta de verdad**. Lo escribes en español, oprimes un botón y corre.

**Empieza ejecutando la celda de abajo**: haz clic sobre ella y presiona
`Shift+Enter`. Después avanza celda por celda, sin saltarte ninguna.
""")

    c.arranque()
    c.code("portada()")

    c.md("""## Al terminar este cuadernillo vas a poder…

1. Leer un problema en español y decir en voz alta **qué datos entran, qué se
   hace con ellos y qué sale** — sin escribir una sola línea de código.
2. Distinguir una **variable** de una **constante** y de una **restricción**, y
   ponerle a cada una un nombre que se entienda.
3. Escribir un algoritmo en **pseudocódigo en español** y **ejecutarlo aquí
   mismo** para ver si hace lo que creías.
4. Dibujar el **diagrama de flujo** de ese algoritmo usando los cinco símbolos
   correctos, y reconocer cuándo un diagrama está mal armado.
5. Hacer una **prueba de escritorio**: seguir tu propio algoritmo con lápiz y
   papel, instrucción por instrucción, anotando cuánto vale cada variable.
6. Traducir el mismo algoritmo a **Python**, sabiendo que `input()` siempre te
   entrega **texto** y que tú decides con `int()` o `float()` en qué se
   convierte.
7. Explicar por qué `x = x + 2` no es una ecuación mentirosa. 🙂

### Este cuadernillo se hace en dos sentadas

Son 165 minutos y cubre las dos clases de la semana. No intentes hacerlo de una:

| | Cuándo | Qué trae |
|---|---|---|
| **Parte A** | después de la **Clase 1** | secciones 1, 2 y 3 — plantear, analizar, variables y E-P-S |
| **Parte B** | después de la **Clase 2** | secciones 4 a 8 — pseudocódigo, diagramas, memoria, tipos, `input()` y los ocho ejercicios |

Hay una tarjeta que marca el corte cuando llegues.

> **Dos marcadores distintos, no los confundas.** Los **XP** son del juego: los
> ganas con los quices y los ensayos. Los **puntos** son tu nota: salen solo de
> los ocho ejercicios y viajan solos a Moodle.
>
> Este cuadernillo tiene **80 puntos** y **80 XP**. La insignia se llama
> «Traductora / Traductor de algoritmos».
""")

    # =========================================================================
    # Bloque 1 — Sección 1: calentamiento (Parte A)
    # =========================================================================
    c.seccion(1, "Calentamiento", 10, """Cuatro preguntas rápidas de la semana pasada. No tienen nota: dan XP y te
dicen si estás listo para lo de hoy.

Si algo aquí se te atasca, **esa es la señal**: vuelve al cuadernillo de la
Semana 1 antes de seguir. Lo de hoy se apoya en eso.""")

    c.code("quiz_hardware()")
    c.code("quiz_niveles()")

    c.code('''# Esta línea está rota, igual que la de la semana pasada.
# Quítale el # del principio, arréglala y ejecútala.
# print("Buenos días, Bucaramanga)''')

    c.code("orden_errores()")

    c.md("""El tercero es el peligroso. Un error de sintaxis lo ve Python; un error de
lógica solo lo ves **tú**, y solo si haces una prueba de escritorio. Ese es,
casualmente, uno de los temas de hoy.
""")

    # =========================================================================
    # Bloque 2 — Sección 2: el gancho
    # =========================================================================
    c.seccion(2, "¿A qué hora tengo que salir de la casa?", 8, """Vives en **Girón**. Tu primera clase en la UIS es a las **6:00 a. m.** y el
profesor cierra la puerta en punto.

- De tu casa a la parada: **8 minutos** caminando.
- De la parada a la UIS en bus: **45 minutos** (si el tráfico se porta bien).
- De la portería al salón: **10 minutos**.
- Y quieres un **colchón de 15 minutos**, porque el bus no siempre se porta
  bien.

¿A qué hora suena el despertador?""")

    c.code("grafica_madrugada()")

    c.md("""**Las 4:42.** Ese cálculo lo hiciste de cabeza en veinte segundos.

Ahora hazlo para los **30.000 estudiantes de la UIS**: cada uno vive en un
barrio distinto, toma rutas distintas y tiene clase a horas distintas. Ahí ya no
alcanza la cabeza ni la calculadora. Ahí se necesita **un algoritmo**: una
receta que sirva para todos, escrita una sola vez.

Ejecuta la celda de abajo. No es Python.
""")

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

    c.md("""Lo que acabas de ver **no es Python**. Es **pseudocódigo**: español con reglas.
Y sin embargo se ejecutó, y sin embargo el computador dibujó su diagrama de
flujo sin que nadie lo dibujara.

Eso es lo que vas a saber hacer al final de esta sesión: **escribir un algoritmo
en español, verlo correr, verlo dibujado y traducirlo a Python** — que es
exactamente lo que se hace en la vida real antes de programar cualquier cosa
seria.
""")

    # =========================================================================
    # Bloque 3 — Sección 3: concepto en corto (Parte A)
    # =========================================================================
    c.seccion(3, "Concepto en corto", 30, """Antes de escribir nada hay que pensar. Esta sección es la parte del oficio que
se hace **sin computador**, y es la que el 90 % de los novatos se salta.""")

    c.figura("s02_d1_cadv",
             "Cuatro pasos, siempre los mismos. Y si en «verificar» algo no "
             "cuadra, se devuelve uno a «comprender».")

    c.md("""### Cuatro pasos, siempre los mismos

**1. Comprender.** Vuelve a contar el problema **con tus propias palabras**, sin
mirar el enunciado. Si no puedes, todavía no lo entendiste — y programar sin
entender es la forma más cara de perder una tarde.

**2. Analizar.** Tres preguntas: ¿qué datos **entran**? ¿qué debe **salir**?
¿qué **restricciones** hay (qué valores no tienen sentido)?

**3. Diseñar.** Escribe el **pseudocódigo** y dibuja el **diagrama**. Todavía no
programes. Esta etapa se salta el 90 % de los novatos, y es la razón por la que
se demoran el triple.

**4. Verificar.** Antes de ejecutar nada, haz la **prueba de escritorio**:
recorre tu propio algoritmo con lápiz y papel, con un caso cuyo resultado ya
conozcas. Si no da, arregla el diseño; no el código, que todavía no existe.

Y si en «verificar» algo no cuadra, se devuelve uno a «comprender». Por eso la
flecha punteada del dibujo.
""")

    c.md("""### Un problema bien planteado

Compara estos dos enunciados:

| Mal planteado | Bien planteado |
|---|---|
| «Calcular lo del parqueadero» | «Dado el número de **horas** que un carro estuvo en el parqueadero de la UIS y la **tarifa por hora**, calcular cuánto debe pagar, sabiendo que hay un **recargo fijo** de $1.000 por el uso de la barrera.» |

El segundo dice **qué entra**, **qué sale** y **qué reglas hay**. El primero no
dice nada: ¿lo del parqueadero de quién? ¿cobrado cómo? ¿desde cuándo?

**Tu primer trabajo como programador no es escribir código: es convertir el
primer enunciado en el segundo.** A eso se le llama plantear el problema.
""")

    c.md("""### La ficha de análisis

Antes de diseñar nada, llena estas cinco casillas. Es literalmente el formato
que vas a usar en el ejercicio E3 y en el taller presencial.

| Casilla | Pregunta | Ejemplo (parqueadero) |
|---|---|---|
| **Objetivo** | ¿Qué debe lograr el algoritmo, en una frase? | Calcular el valor a pagar por el parqueadero. |
| **Entradas** | ¿Qué datos necesito que alguien me dé? | `horas`, `tarifa_hora`, `recargo_fijo` |
| **Salidas** | ¿Qué entrego? | `total` |
| **Restricciones** | ¿Qué valores no tienen sentido? | `horas` ≥ 0; `tarifa_hora` > 0; `horas` es un entero |
| **Casos de prueba** | ¿Con qué datos voy a comprobar que funciona? | 3 h a $2.500 + $1.000 → **8.500**; 0 h → **1.000** |

Fíjate en la última fila. **Los casos de prueba se escriben ANTES de
programar**, cuando todavía puedes pensar con calma en qué debería dar. Si los
inventas después, vas a «comprobar» que tu programa hace justo lo que hace.
""")

    c.md("""### Variables, constantes y restricciones

| Concepto | Qué es | En el problema del parqueadero | Cómo se escribe |
|---|---|---|---|
| **Variable** | Un dato que **cambia** de una ejecución a otra | `horas` (cada carro se queda un rato distinto) | `Definir horas Como Entero` |
| **Constante** | Un dato que **no cambia** mientras el algoritmo corre | `TARIFA_HORA <- 2500` | `Constante TARIFA_HORA <- 2500` — en MAYÚSCULAS |
| **Restricción** | Una condición que los datos **deben cumplir** para que el problema tenga sentido | `horas` no puede ser negativa; `horas` es un número entero de horas | Se escribe en la **ficha de análisis**, todavía no en el código (validar es de la Semana 3) |

Las restricciones no se programan hoy —para eso hacen falta los condicionales,
que llegan la semana entrante— pero **sí se escriben hoy**. Un problema mal
delimitado produce un programa que funciona con los datos del profesor y explota
con los del mundo real.
""")

    c.code("figura_cajas()")

    c.md("""### Cómo se llama una variable

**Reglas que obliga el computador:** sin espacios, sin tildes ni eñes, no
empieza por número, no se llama igual que una palabra reservada (`print`,
`input`, `if`…).

**Reglas que obliga la decencia:** en minúsculas, palabras unidas con guion
bajo, y que se entienda: `costo_pasaje`, `total_a_pagar`, `minutos_bus`.

Tres nombres que no debes usar nunca, aunque funcionen: **`x`** (¿x de qué?),
**`dato1`** (¿dato de qué?) y **`aux`** (auxiliar de qué). El código se escribe
una vez y se lee veinte.
""")

    c.code("figura_eps()")

    c.md("""### E-P-S aplicado al problema de esta mañana

| | El problema de esta mañana |
|---|---|
| **Entrada** | `hora_clase_min` = 360 · `minutos_bus` = 45 · `minutos_caminata` = 8 |
| **Constantes** | `PORTERIA` = 10 · `COLCHON` = 15 |
| **Proceso** | `trayecto <- minutos_bus + minutos_caminata + PORTERIA` ⏎ `salida_min <- hora_clase_min - trayecto - COLCHON` |
| **Salida** | `salida_min` = 282, o sea las **4:42** |
| **Restricciones** | los minutos no pueden ser negativos; `salida_min` debería dar más de 0 (si no, tocaría salir el día anterior) |
| **Casos de prueba** | (360, 45, 8) → 282 · (420, 60, 5) → 330 |

Ahora te toca a ti. Ensaya con el formulario de abajo: es el mismo que vas a
llenar en el ejercicio E3.
""")

    c.code("ensayo_eps()")

    c.md("""### ¿Por qué tres formas de escribir lo mismo?

Porque sirven para cosas distintas y en momentos distintos.

- **El pseudocódigo** es para **pensar**. No tiene compilador, así que no te
  castiga por un punto y coma; te deja concentrarte en la lógica. Y como está en
  español, se lo puedes mostrar a alguien que no programa.
- **El diagrama de flujo** es para **ver**. Un rombo con dos flechas te muestra
  de un vistazo que hay dos caminos; en texto, esa misma idea hay que
  reconstruirla leyendo.
- **Python** es para **ejecutar**. Es el único de los tres que el computador
  entiende de verdad.

Un buen programador se mueve entre los tres todo el tiempo. Y en un examen
escrito —donde no hay computador— los dos primeros son los únicos que tienes.
""")

    c.figura("s02_d7_tres_idiomas",
             "Las tres representaciones del mismo algoritmo. Se va de una a "
             "otra todo el tiempo.")

    c.code("ps.comparador(CODIGO_GANCHO)", etiquetas=("ava-figura",))

    c.code("tarjeta_corte()")

    # =========================================================================
    # Bloque 4 — Sección 4: laboratorio (Parte B)
    # =========================================================================
    c.seccion(4, "Laboratorio", 55, """Bienvenido a la Parte B. De aquí en adelante todo se toca.

El hilo es un solo programa —el de la papelería de la Carrera 9— y con él vas a
hacer cuatro cosas, en este orden: **predecir** qué hace, **ejecutarlo**,
**investigarlo** rompiéndolo a propósito y **modificarlo**.""")

    c.md("""### 4.1 Pseudocódigo: español con reglas

El pseudocódigo es un punto medio entre el español y un lenguaje de
programación. Es lo bastante libre para escribirlo rápido y lo bastante estricto
para que no queden ambigüedades.

Compara:

| Español de todos los días | Pseudocódigo |
|---|---|
| «pregúntale cuántas copias y cóbrale» | `Escribir "¿Cuántas copias?"` ⏎ `Leer copias` ⏎ `total <- copias * PRECIO_COPIA + ANILLADO` ⏎ `Escribir "Total: $", total` |

La primera frase se la puedes decir a un cajero, y funciona porque el cajero
**rellena los huecos** con su experiencia: sabe cuánto vale la copia, sabe que
hay que cobrar el anillado, sabe que hay que decirle el total en voz alta. **El
computador no rellena huecos.** Todo lo que no digas, no pasa.

Con **seis palabras** te alcanza para todo lo de hoy: `Algoritmo`, `Definir`,
`Constante`, `Leer`, `Escribir` y la flecha `<-`.
""")

    c.code("chuleta()")

    c.md("""### Predecir *(no ejecutes todavía)*

```
Algoritmo CostoDeFotocopias
    // La papelería de la Carrera 9, frente a la UIS
    Definir copias, total Como Entero
    Constante PRECIO_COPIA <- 100
    Constante ANILLADO <- 2500

    Escribir "¿Cuántas copias vas a sacar?"
    Leer copias

    total <- copias * PRECIO_COPIA + ANILLADO

    Escribir "Total a pagar: $", total
FinAlgoritmo
```

Vas a sacar **40 copias** y las vas a mandar a anillar. Antes de ejecutar nada,
responde:
""")

    c.code("quiz_prediccion()")

    c.md("""### Ejecutar

Ahora sí. El `"40"` de la última línea es lo que el usuario iba a teclear.
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

    c.md("""### Investigar

Sobre la celda de arriba (cámbiala y reejecútala cuantas veces quieras):

1. Cambia `entradas=["40"]` por `entradas=["1"]`. ¿Tiene sentido el resultado?
   ¿Y con `["0"]`?
2. Sube `PRECIO_COPIA` a 150. ¿Cuántas líneas tuviste que tocar? Esa es
   exactamente la razón por la que existen las constantes.
3. **Borra la línea `Leer copias`** y ejecuta. Lee el error con calma: te va a
   decir que la caja `copias` existe pero está vacía.
4. **Cambia `total <- copias * PRECIO_COPIA` por `total = copias *
   PRECIO_COPIA`** (signo igual en vez de flecha) y ejecuta. Guarda ese mensaje
   en la memoria: lo vas a volver a ver.
5. Sube la línea `Leer copias` **arriba** del `Escribir "¿Cuántas copias...?"`.
   El programa sigue funcionando… pero ahora le pide el dato al usuario **antes
   de decirle qué quiere**. Eso no es un error de sintaxis: es un **error de
   lógica**. El computador no te va a avisar.
""")

    c.md("""### Modificar — ahora escribes tú

Este es tu banco de trabajo. Escribe pseudocódigo a la izquierda, pon las
entradas a la derecha y usa los cuatro botones. **Reto de calentamiento:** haz
que el algoritmo también muestre cuánto cuestan las copias **sin** el anillado.
""")

    c.code('ps.laboratorio(PAPELERIA, entradas=["40"])', etiquetas=("ava-figura",))

    c.md("""### 4.2 Prueba de escritorio (trazado manual)

Es seguir tu propio algoritmo **como si tú fueras el computador**: instrucción
por instrucción, anotando en una tabla cuánto vale cada variable después de cada
paso.

Suena primitivo. Es la herramienta más poderosa que vas a aprender este
semestre, por una razón: **encuentra los errores de lógica**, que son los únicos
que el computador no te va a señalar. Cuando un programa «corre pero da mal», la
prueba de escritorio es lo que lo salva.

Con el trazador de abajo puedes ver una hecha por el computador. Después te va a
tocar hacerlas tú, en papel, en el examen. Fíjate bien en **cuándo** cambia cada
caja.
""")

    c.code('ps.trazador(PAPELERIA, entradas=["40"])', etiquetas=("ava-figura",))

    c.md("""### La misma tabla, en tu cuaderno

| Paso | Instrucción | `copias` | `total` | Salida |
|---|---|---|---|---|
| 1 | `Definir copias, total Como Entero` | — | — | |
| 2 | `Constante PRECIO_COPIA <- 100` | — | — | |
| 3 | `Constante ANILLADO <- 2500` | — | — | |
| 4 | `Escribir "¿Cuántas copias...?"` | — | — | ¿Cuántas copias vas a sacar? |
| 5 | `Leer copias` | 40 | — | |
| 6 | `total <- copias * PRECIO_COPIA + ANILLADO` | 40 | 6500 | |
| 7 | `Escribir "Total a pagar: $", total` | 40 | 6500 | Total a pagar: $6500 |

Tres reglas para que la tabla sirva:

1. **Una fila por instrucción ejecutada**, no por línea escrita.
2. En cada fila, el valor de **todas** las variables, incluso las que no
   cambiaron. Así se ve de un vistazo cuál cambió.
3. Un guion (`—`) significa «la caja existe pero está vacía». No es cero: cero
   es un valor.
""")

    c.md("""### 4.3 Los cinco símbolos del diagrama de flujo

Un diagrama de flujo no es un dibujo bonito: es un lenguaje, y tiene exactamente
cinco palabras.
""")

    c.figura("s02_d3_simbolos",
             "Los cinco símbolos. La forma dice qué hace el bloque, antes de "
             "leer una sola letra.")

    c.code("tabla_simbolos()")

    c.md("""Y este es el diagrama del programa que acabas de ejecutar. **No lo dibujó
nadie**: lo dedujo el computador de tu pseudocódigo.
""")

    c.code("display(HTML(ps.diagrama(PAPELERIA)))", etiquetas=("ava-figura",))

    c.figura("s02_d5_papeleria",
             "El mismo algoritmo dibujado a mano con la convención de la clase. "
             "Compara los dos: son el mismo diagrama.")

    c.md("""### Reglas para que un diagrama de flujo sea correcto

1. **Un solo INICIO.** Si tu diagrama tiene dos puntos de arranque, no es un
   algoritmo: son dos.
2. **Todo camino llega al FIN.** Si una rama se queda colgando, hay un caso que
   tu algoritmo no resuelve.
3. **Las flechas tienen punta y una sola dirección.** Una línea sin punta no
   dice nada.
4. **Del rombo salen dos flechas rotuladas, y solo dos.** Si necesitas tres
   respuestas, necesitas dos rombos.
5. **Una caja, una instrucción.** El diagrama debe poder leerse en voz alta como
   una lista de órdenes.

Dos diagramas que rompen esas reglas:
""")

    c.figura("s02_d6a_rombo_mudo",
             "Del rombo sale una sola flecha: el algoritmo no dice qué hacer "
             "cuando la respuesta es No.")

    c.figura("s02_d6b_caja_multiple",
             "Dos cosas están mal: la caja roja hace cuatro cosas —debería ser "
             "cuatro cajas— y hay un segundo FIN al que no llega ninguna "
             "flecha. Si nadie puede llegar ahí, sobra.")

    c.md("""### El diagrama no se dibuja: se deduce

Vuelve al banco de trabajo (la celda del editor), cámbiale una línea a tu
pseudocódigo y oprime **Ver diagrama**. El dibujo cambia solo.

Eso es lo que hay que entender: **el diagrama de flujo no es una tarea aparte,
es una foto de tu algoritmo**. Si el diagrama queda raro, no es que lo hayas
dibujado mal: es que el algoritmo está raro.
""")

    c.md("""### 4.3.4 El puente a Flowgorithm

| Nuestro pseudocódigo | Bloque de Flowgorithm | Forma en pantalla | Menú |
|---|---|---|---|
| `Algoritmo` / `FinAlgoritmo` | *Main* (ya viene puesto) | óvalos verdes arriba y abajo | — |
| `Definir x Como Entero` | **Declare** · `x` · tipo `Integer` | rectángulo con esquinas dobles | clic derecho → Declare |
| `Constante PASAJE <- 3200` | **Assign** en MAYÚSCULAS (Flowgorithm no tiene constantes) | rectángulo | clic derecho → Assign |
| `Leer x` | **Input** · variable `x` | paralelogramo | clic derecho → Input |
| `Escribir e` | **Output** · expresión `e` | paralelogramo | clic derecho → Output |
| `x <- expr` | **Assign** · `x` ← `expr` | rectángulo | clic derecho → Assign |
| `Si c Entonces … Sino … FinSi` | **If** con ramas *True* / *False* | rombo | clic derecho → If |
| `Mientras c Hacer … FinMientras` | **While** | rombo con retorno | clic derecho → While |
| `Entero / Real / Cadena / Logico` | `Integer / Real / String / Boolean` | — | — |
| `Verdadero / Falso` | `true / false` | — | — |
| `<>` | `!=` | — | — |
| `Y / O / NO` | `AND / OR / NOT` | — | — |

**Flowgorithm no corre aquí, y está bien.** Flowgorithm es un programa de
escritorio para Windows; este cuadernillo vive en un navegador sobre Linux. En
la Clase 2 vas a construir el diagrama en Flowgorithm en los equipos de la sala.
Lo que haces aquí es **llegar con el algoritmo ya pensado y probado**: el
diagrama que ves arriba lo dibujó el computador a partir de tu pseudocódigo, así
que armarlo en Flowgorithm es copiar bloque por bloque usando esta tabla.
""")

    c.md("""### 4.4 Una variable es una caja con nombre""")

    c.code("figura_cajas()")

    c.md("""Cuando escribes `copias <- 40`, el computador hace tres cosas: busca la caja
rotulada `copias`, **bota lo que hubiera adentro** y mete el 40. No hay
«historial»: el valor anterior desaparece. Por eso el orden de las instrucciones
lo es todo.

El **nombre** lo eliges tú, y es lo único que vas a ver dentro de seis meses
cuando releas tu propio código. `x`, `dato1` y `aux` no le dicen nada a nadie.
`costo_pasaje` sí.
""")

    c.code("figura_incremento()")

    c.md("""### El renglón más raro de toda la programación

```
viajes <- viajes + 1
```

En la clase de matemáticas, `x = x + 1` es **falso siempre**: no hay número que
sea igual a sí mismo más uno. En programación esa línea no es una ecuación: es
**una orden**, y se lee de derecha a izquierda:

1. **Primero** se mira qué hay adentro de la caja `viajes` (digamos, 3).
2. **Después** se calcula `3 + 1`, que da 4.
3. **Por último** se guarda el 4 en la caja `viajes`, borrando el 3.

Por eso escribimos `<-` y no `=`: la flecha **apunta hacia la caja**. Cuando
pases a Python vas a escribir `viajes = viajes + 1`, con un signo igual que en
realidad significa lo mismo que la flecha. Recuérdalo así: **en programación,
`=` no pregunta, ordena.**
""")

    c.code('''# Ejecuta esto tal cual. Después cambia el orden de las dos últimas líneas
# y vuelve a ejecutar: ¿por qué cambia el resultado?
viajes = 3
print("Antes: ", viajes)
viajes = viajes + 1
print("Después:", viajes)''')

    c.code('''ps.trazador("""Algoritmo ContarViajes
    Definir viajes Como Entero
    viajes <- 3
    viajes <- viajes + 1
    viajes <- viajes + 1
    Escribir "Total de viajes: ", viajes
FinAlgoritmo""")''', etiquetas=("ava-figura",))

    c.md("""### 4.5 Tipos: qué le cabe a cada caja

| Pseudocódigo | Python | Qué guarda | Ejemplos | Cuidado |
|---|---|---|---|---|
| `Entero` | `int` | números sin decimales | `40`, `-3`, `0` | `3200` sin puntos ni comas: `3.200` es otra cosa |
| `Real` | `float` | números con decimales | `3.85`, `-0.5` | el separador decimal es el **punto**, no la coma |
| `Cadena` | `str` | texto | `"Ana"`, `"3200"` | `"3200"` es texto, **no** es el número 3200 |
| `Logico` | `bool` | verdadero o falso | `Verdadero`, `Falso` | en Python se escriben `True` y `False`, con mayúscula |
""")

    c.code('''# type() te dice de qué tipo es una caja. Ejecuta y mira la diferencia
# entre el número 3200 y el texto "3200".
print(type(3200))       # <class 'int'>
print(type(3.85))       # <class 'float'>
print(type("3200"))     # <class 'str'>
print(type(True))       # <class 'bool'>

# Y ahora la trampa clásica:
print(3200 + 100)       # 3300  -> suma
print("3200" + "100")   # 3200100 -> ¡pega los textos!''')

    c.md("""**`"3200" + "100"` da `3200100`.** No es un error de Python: es que a los
textos, el `+` los **pega**. Si lo que quieres es sumar, primero tienes que
convertir el texto en número. Eso es una **conversión explícita**, y «explícita»
significa que la pides tú, a mano, con todas sus letras.

### Las tres conversiones

| Quiero pasar de… | …a | Python | Pseudocódigo | Falla si… |
|---|---|---|---|---|
| texto | entero | `int("40")` → `40` | `ConvertirAEntero("40")` | el texto no es un número entero: `int("cuarenta")`, `int("3.5")`, `int("")` |
| texto | real | `float("3.85")` → `3.85` | `ConvertirAReal("3.85")` | el texto no parece un número: `float("tres")` |
| número | texto | `str(40)` → `"40"` | `ConvertirATexto(40)` | nunca falla |
""")

    c.code('''# Ida y vuelta entre tipos. Ejecuta y mira los tipos que imprime.
texto = "3200"
numero = int(texto)          # texto -> entero
otra_vez = str(numero)       # entero -> texto

print(texto, type(texto))
print(numero, type(numero))
print(otra_vez, type(otra_vez))
print("¿Son iguales?", texto == otra_vez)

# Y ahora, la conversión que decide si sumas o pegas:
print(int("3200") + int("100"))   # 3300
print("3200" + "100")             # 3200100''')

    c.md("""### 4.6 `Leer` y `Escribir`, `input()` y `print()`

En pseudocódigo, `Leer copias` sabe que tiene que guardar un **número** porque
arriba escribiste `Definir copias Como Entero`. Le dijiste de qué tipo era la
caja antes de llenarla.

Mira las dos columnas, fila por fila:
""")

    c.code("ps.comparador(PAPELERIA)", etiquetas=("ava-figura",))

    c.md("""### Por qué aquí no tecleas

En este cuadernillo tu programa **no te va a preguntar nada**: los datos que el
usuario iba a teclear se los entregas tú de antemano, en una lista.

```python
ps.usar_entradas(["40"])     # esto es "el usuario va a teclear 40"
copias = int(input())        # y esto es exactamente el input() de siempre
```

Tres razones, y las tres son buenas:

1. **Puedes probar el mismo programa con muchos usuarios distintos, en un
   segundo.** Cambias la lista y vuelves a ejecutar. Esa lista tiene nombre
   propio en ingeniería: es un **caso de prueba**, justo lo que definiste en la
   ficha de análisis de la Parte A. Un programa serio se prueba con diez casos,
   no con uno; nadie va a teclear diez veces a mano.
2. **Tus pruebas se pueden repetir.** Si el corrector automático tuviera que
   teclear, no podría corregir. Todo el software profesional del mundo se prueba
   así: los datos entran desde un archivo o una lista, no desde un teclado.
3. **El código es idéntico.** `input()` sigue siendo `input()`. Cuando corras
   este mismo programa en tu computador, en VS Code, te va a preguntar de
   verdad, y no tendrás que cambiarle **ni una letra**.

Y el detalle que sí tienes que grabarte:

> **`input()` siempre te entrega TEXTO.** Aunque el usuario teclee `40`, lo que
> llega a tu programa es `"40"`, con comillas. Si quieres sumar, tú decides:
> `int(input())`.

¿Y por qué en pseudocódigo `Leer copias` sí sabe que es un número? Porque arriba
escribiste `Definir copias Como Entero`: **le dijiste de qué tipo era la caja
antes de llenarla**. Python no tiene esa declaración, así que no puede adivinar,
y te pasa la responsabilidad a ti. Ese es, en una frase, todo el asunto de las
conversiones explícitas.

Y una costumbre profesional, ya que estamos: fíjate en que casi todos los
ejercicios de hoy te piden una **función con parámetros**
(`hora_de_salida(hora_clase, bus, ...)`) en vez de una función que pregunta. Es
a propósito: una función que recibe sus datos se puede probar, reutilizar y
combinar; una que pregunta, no.
""")

    c.code('''# El MISMO algoritmo de la papelería, ahora en Python.
# Compara línea por línea con el pseudocódigo de arriba.
ps.usar_entradas(["40"])          # esto es "el usuario va a teclear 40"

PRECIO_COPIA = 100
ANILLADO = 2500

print("¿Cuántas copias vas a sacar?")
copias = int(input())             # input() da TEXTO; int() lo vuelve número

total = copias * PRECIO_COPIA + ANILLADO

print("Total a pagar: $", total, sep="")''')

    c.md("""### `print()` hace más de lo que parece

```python
print("Total:", 6500)             # Total: 6500      <- pone un espacio entre los pedazos
print("Total:", 6500, sep="")     # Total:6500       <- sin separador
print("Total: $", 6500, sep="")   # Total: $6500
print("cargando", end="")         # no salta de línea al terminar
```

`sep` es lo que `print` mete **entre** los pedazos (por defecto, un espacio) y
`end` es lo que pone **al final** (por defecto, un salto de línea). El
`Escribir` del pseudocódigo se comporta como `sep=""`: pega los pedazos tal cual.
""")

    c.md("""### 4.7 Lee el error

Las dos celdas que siguen **fallan a propósito**. Ejecútalas, lee el mensaje
rojo con calma y después arréglalas. Aprender a leer un error es la mitad del
oficio.
""")

    c.code('''# Esta celda falla a propósito. Ejecútala y lee el mensaje rojo antes de arreglarla.
edad_escrita = "diecinueve"
edad = int(edad_escrita)
print("El año entrante cumples", edad + 1)''', etiquetas=("error-sembrado",))

    c.md("""```
ValueError: invalid literal for int() with base 10: 'diecinueve'
```

Se lee de abajo hacia arriba. La última línea es el diagnóstico: **`ValueError`**
significa *«el tipo de dato era el correcto (un texto) pero el valor no me
sirve»*. Y te muestra exactamente cuál: `'diecinueve'`.

`int()` sabe convertir `"19"`, pero no sabe español. Tampoco sabe convertir
`"19.5"` (eso es `float()`) ni `""` (una cadena vacía no es ningún número).

Compáralo con el `NameError` de la semana pasada: aquel decía *«ese nombre no
existe»*; este dice *«el nombre existe, pero lo que tiene adentro no me sirve»*.
Aprender a distinguir los apellidos de los errores (`NameError`, `TypeError`,
`ValueError`, `SyntaxError`) te ahorra horas.

**Arréglalo:** cambia `"diecinueve"` por `"19"` y ejecuta otra vez.
""")

    c.code('''# Y este es el otro clásico. ¿Cuál es la diferencia con el de arriba?
edad = "19"
print("El año entrante cumples", edad + 1)   # TypeError''',
           etiquetas=("error-sembrado",))

    c.md("""```
TypeError: can only concatenate str (not "int") to str
```

Aquí ni siquiera intentaste convertir: le pediste a Python que sumara un texto y
un número, y se negó. Otros lenguajes adivinan en estos casos —y por adivinar
producen errores silenciosos que aparecen tres meses después—. Python prefiere
frenar.

| Error | Qué te está diciendo | Ejemplo típico |
|---|---|---|
| `SyntaxError` | «no entendí ni siquiera lo que escribiste» | falta una comilla o un paréntesis |
| `NameError` | «ese nombre no existe» | escribiste `gasto_semanal` y la variable es `gasto_semana` |
| `TypeError` | «esos dos tipos no se pueden mezclar así» | `"19" + 1` |
| `ValueError` | «el tipo está bien, pero ese valor no me sirve» | `int("diecinueve")` |

Cuando algo falle, lee **la última línea primero**: ahí está el apellido del
error y el diagnóstico. Las de arriba solo dicen dónde.
""")

    # =========================================================================
    # Bloque 5 — Sección 5: los ocho ejercicios (80 puntos)
    # =========================================================================
    c.seccion(5, "Ocho ejercicios", 50, """Aquí es donde se juega tu nota: **80 puntos** repartidos en ocho ejercicios.
Cada uno son dos celdas — la tuya y la de prueba.

Tres reglas de la casa:

- **Los intentos no restan.** Ejecuta la celda de prueba tantas veces como
  quieras.
- **Las pistas tampoco.** Cada ejercicio trae tres, de la que hace pensar a la
  que casi resuelve. Se piden con `pista("E1")`, `pista("E2")`… y **no gastan
  preguntas del tutor**.
- Si ejecutas una celda de ejercicio sin haberla tocado, te va a salir
  `NotImplementedError`. No es un fallo del cuadernillo: es un error de
  ejecución **puesto a propósito** que significa «aquí falta tu parte». Bórralo
  cuando escribas tu respuesta.

Varios ejercicios se corrigen **ejecutando** tu pseudocódigo, no leyéndolo. Si
el orden está mal, te lo va a decir el propio intérprete.""")

    # --- Ensayo de E1 -----------------------------------------------------
    c.md("""Antes del ejercicio 1, un ensayo sin nota para equivocarte gratis:
""")
    c.code("ensayo_e1()")

    # --- Ejercicio 1 ------------------------------------------------------
    c.ejercicio(
        numero=1, titulo="Ordena el algoritmo", estrellas=1, puntos=5,
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

    # --- Ensayo de E2 -----------------------------------------------------
    c.code("quiz_simbolos()")

    # --- Ejercicio 2 ------------------------------------------------------
    c.ejercicio(
        numero=2, titulo="Cada símbolo con su significado", estrellas=1, puntos=5,
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

    # --- Ensayo de E3 -----------------------------------------------------
    c.code("quiz_ficha()")

    # --- Ejercicio 3 ------------------------------------------------------
    c.ejercicio(
        numero=3, titulo="La ficha de análisis", estrellas=2, puntos=10,
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
        numero=4, titulo="Completa el pseudocódigo", estrellas=2, puntos=10,
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
        numero=5, titulo="Prueba de escritorio", estrellas=2, puntos=10,
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
        numero=6, titulo="Tipos y conversiones", estrellas=3, puntos=10,
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
    c.figura("s02_d4_gancho",
             "El algoritmo del gancho, dibujado. Es el que vas a traducir a "
             "Python en el ejercicio 7.")

    c.ejercicio(
        numero=7, titulo="Traduce el algoritmo a Python", estrellas=3, puntos=15,
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
        numero=8, titulo="El mismo algoritmo, en los dos idiomas",
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
    c.seccion(6, "El reto", None, """*(opcional, sin nota)*

### Reto A — Llévate tu diagrama a la clase

El algoritmo que escribiste en E8 es tuyo. Ejecuta la celda de abajo y vas a
obtener dos cosas:

1. **El guion**: la lista exacta de bloques que tienes que arrastrar en
   Flowgorithm, en orden.
2. **El archivo `mi_algoritmo.fprg`**: descárgalo desde el explorador de
   archivos de Jupyter (menú *File → Open*, después clic derecho sobre el
   archivo → *Download*) y ábrelo en la sala de cómputo.

En la Clase 2 vas a construir ese mismo diagrama y a ejecutarlo dentro de
Flowgorithm. Vas a llegar con la tarea medio hecha, y —más importante— vas a
poder comparar: **el mismo algoritmo en dos herramientas distintas se ve
distinto y hace lo mismo.**

> **Si el `.fprg` no abre**, no pierdas el tiempo peleando con él: el formato
> depende de la versión de Flowgorithm instalada en la sala. El guion impreso no
> depende de nada y es el camino seguro.""")

    c.code('''# Si todavía no hiciste E8, se usa el algoritmo de la papelería.
mi_algoritmo = pseudo_e8 if "pseudo_e8" in globals() else PAPELERIA

ps.guion_flowgorithm(mi_algoritmo)
ps.exportar_flowgorithm(mi_algoritmo, "mi_algoritmo.fprg")''')

    c.md("""### Reto B — Un vistazo a la semana entrante *(míralo, no lo estudies)*

Todo lo de hoy fue **secuencia**: una instrucción detrás de otra, sin desvíos.
La semana entrante aparece el rombo, y con él la palabra `Si`:

```
Algoritmo AlcanzaElSaldo
    Definir saldo Como Entero
    Constante PASAJE <- 3200

    Escribir "¿Cuánto tienes en la tarjeta?"
    Leer saldo

    Si saldo >= PASAJE Entonces
        Escribir "Te alcanza. Sube tranquilo."
    Sino
        Escribir "No te alcanza. Toca recargar."
    FinSi
FinAlgoritmo
```

Ejecuta la celda de abajo con `["12000"]` y después con `["1500"]`, y mira el
diagrama: vas a ver el rombo con sus dos flechas, **Sí** y **No**. No tienes que
entenderlo hoy. Solo mira cómo se ve un algoritmo que toma decisiones.
""")

    c.code('''RETO_SI = """Algoritmo AlcanzaElSaldo
    Definir saldo Como Entero
    Constante PASAJE <- 3200

    Escribir "¿Cuánto tienes en la tarjeta?"
    Leer saldo

    Si saldo >= PASAJE Entonces
        Escribir "Te alcanza. Sube tranquilo."
    Sino
        Escribir "No te alcanza. Toca recargar."
    FinSi
FinAlgoritmo"""

# Cambia "12000" por "1500" y vuelve a ejecutar.
ps.trazador(RETO_SI, entradas=["12000"])''', etiquetas=("ava-figura",))

    # =========================================================================
    # Bloque 7 — Sección 7: el tutor
    # =========================================================================
    c.seccion(7, "Habla con el asistente", 5, """Tienes **5 preguntas** en este cuadernillo (las ves en el botón de abajo a la
derecha). Cinco no es poco: es justo lo que alcanza si preguntas bien. Aquí van
cinco que valen la pena, una por cada cosa importante de hoy:

1. *«Te voy a explicar con mis palabras qué es la estructura
   Entrada-Proceso-Salida. Dime qué me está faltando, sin darme la respuesta
   completa.»*
2. *«Escribí este pseudocódigo [pégalo]. No me lo corrijas: hazme tres preguntas
   que me ayuden a encontrar yo mismo el error.»*
3. *«Mi diagrama de flujo tiene un rombo del que sale una sola flecha. ¿Por qué
   eso está mal? Explícamelo con un ejemplo de la vida diaria.»*
4. *«Hice la prueba de escritorio del ejercicio 5 y me dio distinto al
   corrector. Pregúntame paso por paso qué anoté, para que yo vea dónde me
   desvié.»*
5. *«¿Por qué `input()` siempre devuelve texto? Dame otro ejemplo, distinto al
   del cuadernillo, donde eso cause un error.»*

**Lo que no vale la pena preguntar:** *«dame la respuesta del E7»*. Te la va a
dar —está programado para no hacerlo, pero eventualmente cede—, y el día del
parcial el que va a estar sentado ahí eres tú.

Fíjate en el patrón de las cinco: ninguna pide una solución. Todas piden **que
te pregunte a ti**. Ese es el uso que sirve.

Y antes de gastar una: **haz clic en la celda del ejercicio donde estás
atascado**. El panel toma solo el enunciado, tu código y el último error. Si
preguntas desde otra parte, el asistente responde a ciegas.""")

    # =========================================================================
    # Bloque 8 — Sección 8: cierre
    # =========================================================================
    c.seccion(8, "Cierre", 7, """Antes de reclamar tu insignia, marca honestamente lo que ya puedes hacer. Esto
no tiene nota: es tu plan para la semana.""")

    c.code("radar_salida()")

    c.md("""### Lo que cubriste hoy""")

    c.code("tabla_cobertura()")

    c.md("""### Para profundizar *(fuentes confiables)*

- **PSeInt** (`pseint.sourceforge.net`) — el intérprete de pseudocódigo en
  español más usado en Latinoamérica. La sintaxis que aprendiste hoy es
  prácticamente la suya: si lo instalas, ya sabes usarlo.
- **Flowgorithm** (`flowgorithm.org`) — el que van a usar en la sala. La sección
  *Documentation* tiene la referencia de cada bloque.
- *How to Think Like a Computer Scientist* (Runestone Academy), capítulos 1 y 2
  — libro de CS1 abierto, con ejercicios ejecutables.
- **Python Tutor** (`pythontutor.com`) — visualiza la memoria de un programa de
  Python paso a paso, igual que el trazador de hoy pero para Python de verdad.
  Muy recomendado para las próximas semanas.
""")

    c.code("cierre()")

    return c


if __name__ == "__main__":  # pragma: no cover - atajo para autorar
    construir().escribir(
        os.path.join(os.path.dirname(os.path.dirname(AQUI)),
                     "notebook_semana", "semana_02", "cuadernillo.ipynb"))
