#!/usr/bin/env python3
"""Cuadernillo de la SEMANA 1: «Hola, máquina».

Curso 41333 Algoritmos y Programación · Ingeniería en IA · UIS 2026-2
Unidad 1 — Fundamentos computacionales y entorno de desarrollo.

25 puntos de nbgrader en siete ejercicios, 70 XP lúdicos y la insignia
«Despegue». El motor (`motor/ava_motor.py`) y el contenido propio de la semana
(`contenido.py`) se incrustan en la celda de arranque: al alumno le llega un
solo archivo.

Dos decisiones que se salen del documento de diseño y por qué:

- El diseño ponía el motor en `/etc/jupyter/ava_s01.py`, dentro de la imagen.
  Aquí se incrusta en el `.ipynb`, que es lo que ya está construido y probado:
  así un cuadernillo publicado no cambia de motor cuando se reconstruye la
  imagen. Por eso las celdas de prueba no importan nada — los nombres ya están
  en el espacio del kernel — y las figuras se muestran con `ava.figura()` en vez
  de con `mostrar("d2_capas")`.
- Las pistas se piden con `pista("E3")` y no con `pista("ejercicio_3")`: la
  clave la fija `constructor.Cuadernillo.ejercicio()`.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(AQUI) not in sys.path:
    sys.path.insert(0, os.path.dirname(AQUI))

from constructor import Cuadernillo  # noqa: E402


def construir(motor_comprimido=True):
    c = Cuadernillo(
        codigo="semana_01",
        titulo="Hola, máquina",
        semana=1,
        meta_xp=70,
        insignia="Despegue",
        tutor_ia=True,
        motor_comprimido=motor_comprimido,
        modulos=[os.path.join(AQUI, "contenido.py")],
    )

    # =========================================================================
    # Bloque 0 — Portada y activación
    # =========================================================================
    c.md("""# Hola, máquina
### Semana 1 · Unidad 1 · Fundamentos computacionales y entorno de desarrollo

Bienvenido a Algoritmos y Programación. Esto que estás viendo es un
**cuadernillo interactivo**: un documento donde el texto y el código conviven y
donde el código se ejecuta aquí mismo, en tu navegador, sin instalar nada.

En los próximos **diez minutos** vas a ejecutar tu primer programa. Hoy. Tú.
Y antes de que termine el cuadernillo vas a saber qué pasa por dentro de la
máquina cuando lo haces.

**Empieza ejecutando la celda de abajo**: haz clic sobre ella y presiona
`Shift+Enter`.
""")

    c.arranque()
    c.code("iniciar()")

    c.md("""## Al terminar este cuadernillo vas a poder…

- Ejecutar código Python en un cuadernillo y explicar **quién lo ejecuta**.
- Guardar valores en **variables** y distinguir los cuatro tipos básicos:
  texto, entero, decimal y booleano.
- Leer un programa **como lo lee el intérprete** —de arriba abajo, una línea a
  la vez— y predecir con qué valores termina.
- Distinguir un **editor**, una **terminal**, un **intérprete** y un **IDE**, y
  decir para qué sirven Python, VS Code y Jupyter sin repetir un eslogan.
- Crear, escribir y leer un **archivo** desde código.
- Reconocer los **tres tipos de error** —sintaxis, ejecución y lógica— y saber
  cuál de los tres nadie te va a avisar.
- Escribir tu primera **función** completa: recibe datos, calcula y devuelve.

**Lo que NO se te pide hoy:** escribir programas largos, memorizar fechas ni
saber nada de antemano. Si nunca has programado, este cuadernillo está escrito
para ti; si ya programaste, los ejercicios 5 a 7 te van a exigir.
""")

    c.md("""> **Dos marcadores distintos, no los confundas.** Los **XP** son del juego: los
> ganas explorando, respondiendo quices y rompiendo cosas. Los **puntos** son tu
> nota: salen solo de los siete ejercicios y viajan solos a Moodle. Puedes
> terminar con 70 XP y 0 puntos, o al revés. Lo ideal es lo primero *y* lo
> segundo.
>
> Este cuadernillo tiene **25 puntos** y **70 XP**. La insignia se llama «Despegue».
""")

    # =========================================================================
    # Bloque 1 — Sección 1: primer éxito y punto de partida
    # =========================================================================
    c.seccion(1, "Tu primer programa", 15, """Desde 1978, casi todo el que aprende a programar empieza igual: haciendo que la
máquina salude. Es un ritual de iniciación y hoy te toca a ti.

Ejecuta la celda de abajo (clic + `Shift+Enter`).""")

    c.code('print("¡Hola, mundo!")')

    c.md("""¿Salió el texto ahí abajo? **Eso fue un programa.** Uno de verdad: una
instrucción (`print`) que le ordenó a un computador mostrar algo, y el
computador obedeció.

Ahora lo importante: los programas **se modifican**. Haz que te salude a ti.
Cambia solo lo que está entre comillas y ejecuta.
""")

    c.code('''mi_nombre = "escribe tu nombre aquí"   # <- cambia SOLO lo que está entre comillas

print("Hola,", mi_nombre + ".", "Bienvenido a Algoritmos y Programación.")''')

    c.md("""Acabas de usar tu primera **variable** (`mi_nombre`): una cajita con nombre
donde guardas un dato. Volveremos a ellas en la semana 2; hoy solo saluda.

Fíjate en algo que va a gobernar todo el semestre: **el computador no adivinó
nada.** Hizo exactamente lo que decía la instrucción, ni más ni menos. Cuando
algo salga mal —y va a salir mal— la causa casi siempre será esa.
""")

    c.md("""### 1.2 Tu punto de partida

Antes de enseñarte nada, quiero saber de dónde arrancas. Esto **no tiene nota y
no se compara con nadie**: es una foto tuya, de hoy, y en la semana 16 la vamos
a volver a mirar juntos.

Aquí no hay respuestas malas. Hay respuestas *de hoy*. Si no sabes algo,
responde lo que te parezca y sigue: exactamente para eso existe el curso.

Responde las siete y presiona el botón del final. **+10 XP por completarlo,
elijas lo que elijas.**
""")

    c.code("diagnostico()")

    c.md("""*En el curso real, este punto de partida —junto con un cuestionario un poco más
completo en Moodle— es la línea base con la que vamos a medir cuánto creciste
durante el semestre. Se usa de forma anónima y con tu consentimiento informado;
el profesor te lo explica en la primera clase, y no participar no afecta tu
nota en absoluto.*
""")

    # =========================================================================
    # Bloque 2 — Sección 2: el gancho
    # =========================================================================
    c.seccion(2, "¿Qué pasó cuando presionaste Shift+Enter?", 5, """Escribiste una línea en español-ish, presionaste dos teclas y apareció un
saludo. Entre esas dos cosas ocurrieron, como mínimo, **siete pasos** repartidos
en cuatro piezas distintas, y ninguna de ellas entiende la palabra `print`.

Ejecuta la celda para verlos.""")

    c.figura("s01_d4_shift_enter",
             "Los tres primeros pasos son software. El cuarto es hardware.")

    c.md("""Los tres primeros pasos son **software**: programas que se pasan tu texto unos a
otros. El cuarto es **hardware**: un pedazo de silicio que solo sabe sumar
números binarios y no tiene idea de que existe el español.

Y es rapidísimo. Ejecuta esto y no toques nada: solo léelo y **predice** cuánto
va a tardar.
""")

    c.code('''import time

inicio = time.perf_counter()
total = 0
for i in range(1_000_000):     # un millón de vueltas
    total = total + i
fin = time.perf_counter()

print("Sumé el primer millón de números.")
print("Resultado:", total)
print("Tardé:", round(fin - inicio, 3), "segundos")''')

    c.md("""Si tú hicieras esas sumas a mano, a una por segundo, sin dormir ni comer,
tardarías **once días y medio**. Tu procesador tardó una fracción de segundo.

Esa desproporción es toda la historia de este curso: la máquina es
absurdamente rápida y absurdamente bruta. **Tú pones la idea; ella pone la
velocidad.** El resto del cuadernillo es entender cómo tu idea llega hasta ese
pedazo de silicio.
""")

    # =========================================================================
    # Bloque 3 — El entorno de Python
    # =========================================================================
    c.seccion(3, "¿Dónde se escribe todo esto?", 25, """Ya ejecutaste código y ya sabes que quien lo ejecuta es el kernel. Falta
ponerle nombre a las herramientas, porque durante el semestre se van a nombrar
todo el tiempo y se confunden con facilidad.

Cuatro palabras, y las tres aplicaciones que vas a usar de verdad.""")

    c.md("""### 3C. ¿Dónde se escribe todo esto?

Cuatro palabras que se confunden todo el tiempo y que a partir de hoy vas a
distinguir:

| Palabra | Qué es | Analogía | Si desaparece… |
|---|---|---|---|
| **Editor** | Un programa para escribir texto (tu código) | El cuaderno | Escribes en Notas y ya, pero sin colores ni ayudas |
| **Terminal** | Una ventana donde le das órdenes escritas al sistema operativo | La ventanilla de atención | Tienes que hacer todo con clics |
| **Intérprete** | El programa que lee tu código **y lo ejecuta línea por línea** | El traductor simultáneo | Tu código es un texto muerto |
| **IDE** | Un paquete que trae editor + terminal + intérprete + depurador | El taller completo | Tienes las herramientas sueltas |

Ejecuta el diagrama para verlo armado.
""")

    c.figura("s01_d5_entorno",
             "El IDE no es una herramienta más: es la caja que contiene a las otras.")

    c.md("""### Los tres nombres que vas a oír todo el semestre

| | Qué es exactamente | Para qué sirve | ¿Lo estás usando ahora? |
|---|---|---|---|
| **Python** | Un **lenguaje** y su **intérprete** (el programa `python`) | Entender y ejecutar tu código | Sí: es el motor debajo de este cuadernillo |
| **VS Code** | Un **editor** que con extensiones se comporta como IDE | Escribir proyectos de varios archivos, en tu propio computador | No: eso lo instalas en la sección 8 |
| **Jupyter** | Un **entorno de cuadernos**: texto + código + resultados en un solo documento | Aprender, explorar datos, mostrar resultados | Sí: esto **es** Jupyter |

Cuidado con una confusión muy común: **Python no es VS Code.** Puedes usar
Python sin VS Code (lo estás haciendo) y puedes tener VS Code sin Python (te
serviría para escribir, no para ejecutar).
""")

    c.md("""### La terminal, sin salir del cuadernillo

En Jupyter, una línea que empieza con `!` no va al intérprete de Python: va
**directo a la terminal del sistema**. Es la forma más segura de conocerla.
Ejecuta la celda y lee cada respuesta.
""")

    c.code("""!pwd                 # "print working directory": ¿en qué carpeta estoy parado?
!ls -l               # lista lo que hay en esta carpeta, con detalles
!python --version    # ¿qué intérprete de Python tengo instalado?
!which python        # ¿y dónde está ese programa exactamente?""")

    c.md("""Léelo con calma, porque acabas de ver **tres cosas del temario oficial de la
semana** en cuatro líneas:

- `pwd` te contestó algo como `/home/jovyan/work`. Esa es tu **carpeta de
  trabajo**: cuando un programa dice `abrir("notas.txt")` sin más señas, lo
  busca ahí. A eso se le llama *ruta relativa*.
- `ls` te mostró tus archivos. Ahí está `cuadernillo.ipynb`: **este documento es
  un archivo**, igual que cualquier otro.
- `python --version` te contestó `Python 3.11.x`: ese es el **intérprete** del
  que hablábamos, y `which` te dijo en qué carpeta vive el programa.

Un archivo tiene **nombre**, **extensión** (`.txt`, `.py`, `.ipynb`), **ruta** y
**contenido**. La extensión no cambia lo que el archivo *es*: es una promesa
sobre lo que hay adentro.
""")

    c.figura("s01_d6_archivos",
             "Abrir, hacer algo, cerrar. Dos veces: una para escribir y otra para leer.")

    c.code('''# Crea un archivo, escribe en él y vuelve a leerlo. Tres verbos: abrir, escribir, cerrar.
with open("prueba.txt", "w", encoding="utf-8") as f:
    f.write("Mi primer archivo creado con código.\\n")

print(open("prueba.txt", encoding="utf-8").read())
!ls -l prueba.txt''')

    c.code('''quiz(
    "Q4", 6,
    "Estás en la sala de cómputo y quieres ejecutar un archivo <code>tarea.py</code> "
    "que ya escribiste. ¿Qué necesitas SÍ o SÍ?",
    ["Un editor", "El intérprete de Python", "Un IDE", "Una terminal"],
    "El intérprete de Python",
    "Escribir el archivo ya lo hiciste. Para <b>ejecutarlo</b> solo hay un "
    "candidato: el intérprete. El editor, el IDE y la terminal son comodidades.",
    pistas=["Fíjate en el verbo: no quieres *escribirlo* otra vez, quieres "
            "*ejecutarlo*. ¿Cuál de los cuatro es el único que ejecuta?"],
)''')

    # =========================================================================
    # Bloque 4 — Los tres errores
    # =========================================================================
    c.seccion(4, "Los tres errores", 20, """Vas a equivocarte muchísimo este semestre. No es una amenaza, es aritmética:
equivocarse es el 80 % de programar, también para quien lleva veinte años.

Lo que separa a quien avanza de quien se bloquea no es equivocarse menos: es
**saber qué clase de error tiene enfrente**. Hay exactamente tres, y se
comportan de forma muy distinta.

Las tres celdas que siguen están rotas **a propósito**. Ejecútalas tal cual. No
puedes dañar nada: si algo se enreda, `Kernel → Restart` y el cuadernillo queda
como nuevo.""")

    c.md("""### Error 1 de 3 — de sintaxis

**Predice antes de ejecutar:** en la celda de abajo hay dos líneas. La segunda
está mal escrita. ¿Crees que la primera alcanzará a imprimirse?

Ejecuta y compruébalo.
""")

    c.code('''print("Esta línea está perfecta. ¿Se imprimirá?")

nota = 4.2
if nota >= 3.0
    print("Aprobado")''')

    c.md("""**No se imprimió nada.** Ni siquiera la primera línea, que estaba perfecta.

Esa es la firma del **error de sintaxis**: Python revisa **todo** el texto antes
de ejecutar **una sola línea**, como quien lee un párrafo completo antes de
empezar a leerlo en voz alta. Si encuentra algo que no es español —perdón, que
no es Python— se planta y no arranca.

Cómo se lee el mensaje, de arriba abajo:

| Parte | Qué te está diciendo |
|---|---|
| `Cell In[12], line 4` | **dónde**: celda 12, línea 4 |
| `if nota >= 3.0` | la línea culpable, copiada |
| `^` | el dedo señalando el punto exacto |
| `SyntaxError: expected ':'` | **qué**: esperaba dos puntos |

Python te dijo qué le falta, en qué línea y en qué carácter. Es lo más parecido
a un profesor particular que vas a encontrar gratis.

**Los cuatro sospechosos de siempre:** falta `:` al final de un `if`/`for`/`def`;
falta una comilla; falta un paréntesis de cierre; falta o sobra una sangría.

Arregla la celda de arriba (ponle los dos puntos), ejecútala de nuevo y mira
cómo ahora **sí** se imprime la primera línea. Después ejecuta la celda de abajo
para cobrar tus XP.
""")

    c.code('registrar("errores_sintaxis")   # +8 XP cuando la celda de arriba compile')

    c.md("""### Error 2 de 3 — de ejecución

**Predice:** la celda de abajo tiene cuatro `print` numerados. ¿Cuántos alcanzan
a salir?
""")

    c.code('''print("Paso 1: recibo la nota del parcial")
nota_texto = "4.2"

print("Paso 2: la muestro tal cual ->", nota_texto)
print("Paso 3: le sumo un punto  ->", nota_texto + 1)
print("Paso 4: aquí nunca llego")''')

    c.md("""**Salieron dos de cuatro.** Ahí está toda la diferencia con el error anterior:
aquí el programa **sí arrancó**, corrió un rato y se estrelló en la línea 5.
Nunca llegó al paso 4.

A esto se le llama **error de ejecución** (o *de tiempo de ejecución*, o
*excepción*). La sintaxis estaba impecable: el problema apareció cuando los
**datos reales** llegaron a la instrucción.

Cómo se lee un traceback: **de abajo hacia arriba**.

1. **La última línea es la respuesta.** `TypeError: can only concatenate str
   (not "int") to str`. Traducido: «me pediste pegar un texto con un número, y
   eso no lo sé hacer».
2. **La flecha `---->` es el lugar.** Señala la línea exacta.
3. Lo de arriba es el camino que trajo el programa hasta ahí. Hoy no lo
   necesitas; en la semana 9 sí.

¿Por qué falló? `nota_texto` es `"4.2"` **con comillas**: para Python es un
texto, no un número. Un texto y un número no se suman, igual que no se suman
tres manzanas y la palabra «manzana».

**Los cuatro sospechosos de siempre:**

| Mensaje | Qué pasó |
|---|---|
| `NameError` | usaste un nombre que no existe (¿lo escribiste mal? ¿olvidaste comillas?) |
| `TypeError` | mezclaste tipos que no se mezclan |
| `ZeroDivisionError` | dividiste por cero |
| `IndexError` | pediste el elemento 4 de una lista de 3 |

**Arréglalo:** quítale las comillas a `"4.2"` para que sea un número de verdad,
y ejecuta otra vez. Deben salir los cuatro pasos.
""")

    c.code('registrar("errores_ejecucion")   # +8 XP cuando la celda de arriba corra entera')

    c.md("""### Error 3 de 3 — de lógica *(el peligroso)*

**Predice, y esta vez apúntalo mentalmente:** si sacaste 4.0, 4.0 y 4.0 en tus
tres parciales, ¿cuál es tu promedio?

Ya lo sabes: 4.0. No hace falta calculadora. Ahora ejecuta la celda.
""")

    c.code('''n1, n2, n3 = 4.0, 4.0, 4.0

promedio = n1 + n2 + n3 / 3

print("Tu promedio del semestre es:", promedio)''')

    c.md("""Léelo otra vez: **9.33 de promedio, con tres notas de 4.0.**

Y ahora lo verdaderamente inquietante: **¿dónde está el mensaje rojo?**

No hay. No hay error de sintaxis (la línea está perfectamente escrita) ni error
de ejecución (sumar y dividir números es legal). Python hizo **exactamente** lo
que le pediste: por la regla de precedencia, primero dividió `n3 / 3` y después
sumó. `4.0 + 4.0 + 1.333…`

Tú querías `(n1 + n2 + n3) / 3`. Escribiste otra cosa. Y la máquina, que no
tiene opinión sobre tus promedios, obedeció sin chistar.

Eso es un **error de lógica**: el programa corre, entrega un resultado, y el
resultado está mal. **Nadie te avisa. Nunca.**

#### ¿Y entonces cómo se cazan?

Instalando tu propia alarma. Un **caso de prueba** es una situación cuyo
resultado correcto conoces de antemano, como los tres cuatros. Ejecuta:
""")

    c.code('assert promedio == 4.0, "Con tres notas de 4.0 el promedio TIENE que dar 4.0"')

    c.md("""**Acabas de fabricar el mensaje rojo que Python no te iba a dar.** Eso es
`assert`: una frase que dice «esto tiene que ser cierto; si no lo es, grita».

Y aquí está el secreto del cuadernillo: **las celdas de prueba de los ejercicios
que vienen son exactamente esto.** Cuando ejecutes `test_ejercicio_1` y te
salga verde, es que un montón de `assert` que escribimos nosotros se
cumplieron. Cuando salga rojo, uno falló y te dirá cuál.

Ahora **arregla** la celda del promedio (paréntesis) y vuelve a ejecutar las dos
celdas: la del promedio y la del `assert`. Cuando el `assert` no diga nada,
ganaste: en programación, **el silencio es la buena noticia**.
""")

    c.code('registrar("errores_logica")   # +8 XP cuando el assert pase')

    c.md("""### Los tres, uno al lado del otro

| | **Sintaxis** | **Ejecución** | **Lógica** |
|---|---|---|---|
| ¿Cuándo aparece? | Antes de ejecutar nada | A mitad del programa | Nunca «aparece» |
| ¿Alcanzó a correr algo? | No, ni una línea | Sí, hasta el punto del choque | Sí, **todo** |
| ¿Quién te avisa? | Python, con `SyntaxError` | Python, con un traceback | **Nadie. Solo tú.** |
| ¿Dónde miras? | La línea y el `^` | La última línea del traceback | Tus casos de prueba |
| Analogía | Una frase sin verbo: no se entiende | Una receta que pide un huevo y no hay huevos | Una receta que sale perfecta… de otro plato |
| Se caza con | Leer el mensaje | Leer el mensaje | `assert` y casos conocidos |

Ejecuta el árbol de decisión y guárdalo: te va a servir todo el semestre.
""")

    c.figura("s01_d8_arbol_errores",
             "Cuatro preguntas y sabes con cuál de los tres estás peleando.")

    c.md("""#### Un error de lógica de 125 millones de dólares

En 1999 la NASA perdió la sonda **Mars Climate Orbiter**. El software no falló:
corrió perfecto, sin un solo mensaje de error, durante nueve meses de viaje. El
problema fue que un equipo entregaba los datos de empuje en libras-fuerza y el
otro los leía como si fueran newtons. La sonda entró demasiado bajo en la
atmósfera de Marte y se desintegró.

Ni sintaxis, ni ejecución. **Lógica.** Nadie avisó.

Por eso, a partir de hoy, la pregunta que te vas a hacer siempre no es «¿corrió
mi programa?» sino **«¿corrió, y además está bien?»**.
""")

    c.code('''quiz(
    "Q5", 6,
    "Tu programa calcula el 15 % de descuento sobre $80.000 y muestra $79.985. "
    "No aparece ningún mensaje de error. ¿Qué tipo de error tienes?",
    ["De sintaxis", "De ejecución", "De lógica",
     "Ninguno: si no hay mensaje, no hay error"],
    "De lógica",
    "Corrió entero y sin quejarse, y entregó un número equivocado. Esa es la "
    "firma exacta del error de lógica.",
    pistas=["Haz la cuenta a mano: el 15 % de 80.000 son 12.000, así que el "
            "precio con descuento debería ser 68.000. El programa corrió sin "
            "quejarse… y entregó otra cosa."],
)''')

    # =========================================================================
    # Bloque 5 — Los siete ejercicios (25 puntos)
    # =========================================================================
    c.seccion(5, "Siete ejercicios", 35, """Aquí es donde se juega tu nota: **25 puntos** repartidos en siete ejercicios.
Cada uno son dos celdas — la tuya y la de prueba — y la de prueba es solo un
montón de `assert` como el que acabas de fabricar.

Tres reglas de la casa:

- **Los intentos no restan.** Ejecuta la celda de prueba tantas veces como
  quieras.
- **Las pistas tampoco.** Cada ejercicio trae tres, de la que hace pensar a la
  que casi resuelve. Se piden con `pista("E1")`, `pista("E2")`…
- Si ejecutas una celda de ejercicio sin haberla tocado, te va a salir
  `NotImplementedError: ...`. No es un fallo del cuadernillo: es un error de
  ejecución **puesto a propósito** que significa «aquí falta tu parte». Bórralo
  cuando escribas tu respuesta.
""")

    # --- Ejercicio 1 ------------------------------------------------------
    c.ejercicio(
        numero=1, competencias=['I3'], titulo="Tu ficha de estudiante", estrellas=1, puntos=3,
        enunciado="""Una **variable** es un nombre que guarda un valor. Se crea con `=`, que aquí no
significa «es igual a» sino «guarda esto»:

```python
ciudad = "Bucaramanga"
```

Python distingue cuatro tipos que vas a usar todo el semestre:

| Tipo | Qué guarda | Ejemplo |
|---|---|---|
| `str` | Texto, siempre entre comillas | `"Ana"` |
| `int` | Un número entero, sin decimales | `2026` |
| `float` | Un número con decimales | `4.2` |
| `bool` | Verdadero o falso, sin comillas | `True` |

Crea **tu** ficha con esos cuatro nombres exactos. Los valores son tuyos, pero
el tipo tiene que ser el correcto:

- `nombre` — tu nombre, como texto
- `codigo` — tu código estudiantil, como número entero
- `promedio` — el promedio que te gustaría sacar, con decimales
- `primer_semestre` — `True` o `False`

**Cuidado con el clásico:** `codigo = "2026"` **no** es un entero, es texto con
forma de número. Las comillas cambian el tipo.""",
        partida='''nombre = ...
codigo = ...
promedio = ...
primer_semestre = ...''',
        solucion='''nombre = "Ana Maria"
codigo = 2260123
promedio = 4.2
primer_semestre = True''',
        pruebas='''assert isinstance(nombre, str) and nombre.strip(), \\
    "nombre debe ser texto entre comillas y no puede quedar vacio"
assert isinstance(codigo, int) and not isinstance(codigo, bool), \\
    "codigo debe ser un entero SIN comillas (2260123, no \\"2260123\\")"
assert isinstance(promedio, float), \\
    "promedio debe llevar decimales (4.2), no ser entero (4)"
assert isinstance(primer_semestre, bool), \\
    "primer_semestre debe ser True o False, sin comillas"
print("Ejercicio 1 verificado: cuatro variables, cuatro tipos correctos.")''',
        pruebas_ocultas='''assert 0.0 <= promedio <= 5.0, "En la UIS el promedio va de 0.0 a 5.0"
assert codigo > 0, "El codigo estudiantil es un numero positivo"''',
        pistas=[
            "Las comillas deciden el tipo. Con comillas es texto; sin comillas, Python "
            "lo lee como numero. Pregúntate para cada línea: ¿esto necesita comillas?",
            "Un `float` necesita el punto decimal, aunque sea `4.0`. Si escribes `4` a "
            "secas, Python lo guarda como `int` y la prueba te lo va a decir.",
            "`True` y `False` van con mayúscula inicial y sin comillas. `\"True\"` con "
            "comillas es texto, no un booleano.",
        ],
    )

    # --- Ejercicio 2 ------------------------------------------------------
    c.ejercicio(
        numero=2, competencias=['I4'], titulo="Cada herramienta con su oficio", estrellas=1, puntos=3,
        enunciado="""Vuelve a la sección 3 si hace falta. Completa el diccionario emparejando cada
herramienta con **lo único que la distingue de las otras tres**.

Las cuatro respuestas posibles, escritas exactamente así:

- `"escribir"` — sirve para escribir y guardar el texto del programa
- `"ordenar"` — sirve para darle órdenes escritas al sistema operativo
- `"ejecutar"` — es el único que lee tu código y lo convierte en acciones
- `"todo_junto"` — es un paquete que trae a los otros tres dentro""",
        partida='''HERRAMIENTAS = {
    "editor": ...,
    "terminal": ...,
    "interprete": ...,
    "ide": ...,
}''',
        solucion='''HERRAMIENTAS = {
    "editor": "escribir",
    "terminal": "ordenar",
    "interprete": "ejecutar",
    "ide": "todo_junto",
}''',
        pruebas='''assert isinstance(HERRAMIENTAS, dict), "HERRAMIENTAS debe seguir siendo un diccionario"
assert set(HERRAMIENTAS) == {"editor", "terminal", "interprete", "ide"}, \\
    "No cambies las cuatro llaves: editor, terminal, interprete, ide"
_validas = {"escribir", "ordenar", "ejecutar", "todo_junto"}
assert set(HERRAMIENTAS.values()) <= _validas, \\
    "Usa solo estas cuatro respuestas: escribir, ordenar, ejecutar, todo_junto"
assert len(set(HERRAMIENTAS.values())) == 4, \\
    "Cada herramienta hace algo distinto: no repitas ninguna respuesta"
print("Ejercicio 2 verificado: ya no vas a confundir las cuatro.")''',
        pruebas_ocultas='''assert HERRAMIENTAS["interprete"] == "ejecutar"
assert HERRAMIENTAS["ide"] == "todo_junto"
assert HERRAMIENTAS["editor"] == "escribir"
assert HERRAMIENTAS["terminal"] == "ordenar"''',
        pistas=[
            "Empieza por el que tienes más claro y ve descartando: como las cuatro "
            "respuestas son distintas, cada acierto te reduce el problema.",
            "Solo uno de los cuatro **hace** algo con tu código; los otros tres te "
            "ayudan a escribirlo, guardarlo o lanzarlo.",
            "El IDE no es una quinta herramienta: es la caja que contiene a las otras. "
            "Y la terminal no entiende Python, entiende órdenes del sistema.",
        ],
    )

    # --- Ejercicio 3 ------------------------------------------------------
    c.ejercicio(
        numero=3, competencias=['I3'], titulo="Traza el intérprete", estrellas=2, puntos=4,
        enunciado="""El intérprete lee **de arriba abajo, una línea a la vez**, y cada línea se
ejecuta con los valores que existen *en ese momento*. Eso hace que reasignar una
variable no cambie lo que ya se calculó con ella.

Lee este programa **sin ejecutarlo**:

```python
a = 10
b = 3
suma = a + b
a = 100
doble = suma * 2
b = suma
```

¿Con qué valores termina cada variable? Escríbelos en `TRAZA`.

**La trampa está en `suma`.** Se calculó cuando `a` valía 10. Cambiar `a`
después no vuelve atrás a recalcularla: el intérprete ya pasó por esa línea y
no regresa.""",
        partida='''TRAZA = {
    "a": ...,
    "b": ...,
    "suma": ...,
    "doble": ...,
}''',
        solucion='''TRAZA = {
    "a": 100,
    "b": 13,
    "suma": 13,
    "doble": 26,
}''',
        pruebas='''assert isinstance(TRAZA, dict) and set(TRAZA) == {"a", "b", "suma", "doble"}, \\
    "TRAZA debe tener exactamente las llaves a, b, suma y doble"
assert all(isinstance(v, int) for v in TRAZA.values()), \\
    "Los cuatro valores son numeros enteros, sin comillas"
assert TRAZA["suma"] == 13, \\
    "suma se calculo con a=10 y b=3, ANTES de que a cambiara"
assert TRAZA["a"] == 100, "La ultima linea que toca 'a' le deja 100"
print("Ejercicio 3 verificado: sabes leer un programa como lo lee la maquina.")''',
        pruebas_ocultas='''assert TRAZA["doble"] == 26, "doble es suma * 2, y suma vale 13"
assert TRAZA["b"] == 13, "la ultima linea le asigna a b el valor de suma"''',
        pistas=[
            "Coge lápiz y papel y haz una tabla con una columna por variable y una fila "
            "por línea. Ve rellenándola línea a línea, sin adelantarte.",
            "Cuando llegues a `a = 100`, pregúntate: ¿esto cambia el valor que ya quedó "
            "guardado en `suma`? La respuesta es no, y ahí está todo el ejercicio.",
            "Las dos últimas líneas usan `suma`, que vale 13 desde la línea tres. Así "
            "que `doble` es 26 y `b` termina valiendo lo mismo que `suma`.",
        ],
    )
    # --- Ejercicio 4 ------------------------------------------------------
    c.ejercicio(
        numero=4, competencias=['I3'], titulo="Diagnostica los tres", estrellas=2, puntos=3,
        enunciado="""Tres programas, tres problemas distintos. **No los ejecutes**: diagnostícalos
leyendo, que es lo que vas a tener que hacer toda tu vida profesional.

**Programa A**
```python
nota = 4.2
if nota >= 3.0
    print("Aprobado")
```

**Programa B**
```python
notas = [4.0, 3.5, 2.8]
print("La cuarta nota del curso es:", notas[3])
```

**Programa C**
```python
precio = 80000
descuento = 15          # el almacén da 15 % de descuento
final = precio - descuento
print("Precio final:", final)
```

Escribe para cada uno **una** de estas tres palabras, entre comillas:
`"sintaxis"` · `"ejecucion"` · `"logica"` (sin tildes, para no pelear con el
teclado).""",
        partida='''DIAGNOSTICO = {
    "A": ...,
    "B": ...,
    "C": ...,
}''',
        solucion='''DIAGNOSTICO = {
    "A": "sintaxis",
    "B": "ejecucion",
    "C": "logica",
}''',
        pruebas='''assert isinstance(DIAGNOSTICO, dict) and set(DIAGNOSTICO) == {"A", "B", "C"}, \\
    "DIAGNOSTICO debe tener exactamente las llaves 'A', 'B' y 'C'"
assert all(v in {"sintaxis", "ejecucion", "logica"} for v in DIAGNOSTICO.values()), \\
    "Usa solo estas tres palabras, sin tildes: sintaxis, ejecucion, logica"

corregir("ejercicio_4", DIAGNOSTICO)
print("Ejercicio 4 superado: sabes distinguir los tres errores sin ejecutarlos.")''',
        pistas=[
            "Hazte siempre la misma pregunta en este orden: ¿arranca? Si no arranca, es "
            "de sintaxis. Si arranca y se estrella, es de ejecución. Si arranca, termina "
            "y miente, es de lógica.",
            "Solo uno de los tres programas termina sin ningún mensaje rojo. Ese es el "
            "peligroso.",
            "Programa A: le falta un signo de puntuación. Programa B: la lista tiene "
            "tres elementos y le pide el cuarto. Programa C: corre perfecto y da 79.985.",
        ],
    )

    # --- Ejercicio 5 ------------------------------------------------------
    c.ejercicio(
        numero=5, competencias=['I3', 'I5'], titulo="Caza el error que nadie te va a señalar", estrellas=3, puntos=4,
        enunciado="""Abajo hay una función que debería calcular el promedio de tres notas. Corre sin
quejarse. Y está mal.

Dos cosas que hacer:

1. **Arregla la línea del cálculo.** Recuerda el promedio de los tres cuatros.
2. **Escribe entre las comillas triples** —eso se llama *docstring*— qué hace
   la función y cuál era el error. Una o dos frases tuyas, no copiadas.

Sobre la primera línea, `def promedio_de_tres(n1, n2, n3):` — no te asustes:
significa «receta que recibe tres notas». Te la damos hecha; en la semana 8
aprenderás a escribirla tú. Hoy solo trabaja adentro.""",
        partida='''def promedio_de_tres(n1, n2, n3):
    """ESCRIBE AQUÍ, con tus palabras, qué hace esta función y cuál era el error de lógica que arreglaste."""
    resultado = n1 + n2 + n3 / 3     # <- aquí está el error de lógica
    return resultado''',
        solucion='''def promedio_de_tres(n1, n2, n3):
    """Devuelve el promedio de tres notas.

    El error de lógica era de precedencia: sin paréntesis Python dividía solo la
    tercera nota antes de sumar, así que el resultado no era un promedio.
    """
    resultado = (n1 + n2 + n3) / 3
    return resultado''',
        pruebas='''# Cuatro casos de prueba: situaciones cuyo resultado correcto conocemos de antemano.
assert abs(promedio_de_tres(4.0, 4.0, 4.0) - 4.0) < 1e-9, \\
    "Con tres notas de 4.0 el promedio TIENE que dar 4.0"
assert abs(promedio_de_tres(3.0, 4.0, 5.0) - 4.0) < 1e-9, \\
    "Con 3.0, 4.0 y 5.0 el promedio es 4.0"
assert abs(promedio_de_tres(0.0, 0.0, 3.0) - 1.0) < 1e-9, \\
    "Revisa: ¿estás dividiendo la SUMA de las tres, o solo la última?"
assert abs(promedio_de_tres(5.0, 5.0, 5.0) - 5.0) < 1e-9, \\
    "Con tres cincos el promedio es 5.0"

_doc = (promedio_de_tres.__doc__ or "").strip()
assert "ESCRIBE AQUÍ" not in _doc, "Reemplaza el texto de ejemplo por tu propia explicación"
assert len(_doc) >= 40, "Tu explicación es muy corta: escribe al menos una frase completa"

print("Ejercicio 5 superado: cazaste y documentaste un error que Python nunca iba a señalar.")''',
        pruebas_ocultas='''# Un caso más, que el estudiante no ve: con cuatro casos visibles todavía se
# podría intentar acertar de memoria; con este quinto hay que calcular de verdad.
assert abs(promedio_de_tres(1.0, 2.0, 4.5) - 2.5) < 1e-9''',
        pistas=[
            "Python divide antes de sumar, siempre. En <code>n1 + n2 + n3 / 3</code> "
            "solo se está dividiendo <code>n3</code>. ¿Cómo le dices a Python «primero "
            "suma las tres»?",
            "El signo que agrupa operaciones y obliga a hacerlas primero es el paréntesis.",
            "La línea correcta agrupa las tres notas antes de dividir: "
            "<code>resultado = ( … ) / 3</code>. Y no olvides el docstring: sin él, el "
            "test sigue en rojo aunque el cálculo esté bien.",
        ],
    )

    c.md("""*¿Notaste que te probamos con cuatro casos distintos y no con uno?* Con un solo
caso podrías haber escrito `resultado = 4.0` y pasar. Con cuatro, la única forma
de pasar es calcular de verdad. Así se evita hacer trampa… y así se diseñan las
pruebas en la vida real.
""")

    # --- Ejercicio 6 ------------------------------------------------------
    c.ejercicio(
        numero=6, competencias=['I4'], titulo="Crea un archivo con código", estrellas=3, puntos=4,
        enunciado="""Hasta ahora todo lo que has hecho vive en la memoria y desaparece cuando se
apaga el kernel. Vamos a dejar algo **escrito en el disco**.

Completa la función para que:

1. **cree** el archivo `bitacora_semana1.txt` en tu carpeta de trabajo,
2. **escriba** exactamente tres líneas:
   · la primera, el nombre que recibe la función
   · la segunda, el texto `Semana 1: fundamentos computacionales`
   · la tercera, lo que quieras contar sobre esta semana (mínimo una palabra),
3. **lo vuelva a leer** y devuelva su contenido completo.

Las tres partes de trabajar con archivos: **abrir**, **hacer algo**, **cerrar**.
El `with` de abajo cierra por ti aunque algo falle — por eso se usa siempre.
Cada línea termina en `\\n`, que es como se escribe «salto de línea».""",
        partida='''def crear_bitacora(nombre_estudiante):
    """Crea bitacora_semana1.txt con tres líneas y devuelve su contenido."""
    # 1. Abre el archivo en modo "w" con un bloque  with open(...) as archivo:
    #    y escribe las tres líneas. Cada una termina en \\n
    # 2. Vuelve a abrirlo, ahora en modo "r", y léelo entero con archivo.read()
    # 3. Devuelve lo leído con  return''',
        solucion='''def crear_bitacora(nombre_estudiante):
    """Crea bitacora_semana1.txt con tres líneas y devuelve su contenido."""
    with open("bitacora_semana1.txt", "w", encoding="utf-8") as archivo:
        archivo.write(nombre_estudiante + "\\n")
        archivo.write("Semana 1: fundamentos computacionales\\n")
        archivo.write("Lo que más me costó fue distinguir los tres errores.\\n")

    with open("bitacora_semana1.txt", "r", encoding="utf-8") as archivo:
        contenido = archivo.read()

    return contenido''',
        pruebas='''import os

_contenido = crear_bitacora("Ana Gómez")

assert os.path.exists("bitacora_semana1.txt"), \\
    "No encuentro bitacora_semana1.txt en la carpeta de trabajo. ¿Lo creaste con open(..., 'w')?"
assert isinstance(_contenido, str) and _contenido.strip(), \\
    "La función debe DEVOLVER (return) lo que quedó escrito en el archivo"

_lineas = [l for l in _contenido.strip().split("\\n") if l.strip()]
assert len(_lineas) == 3, f"El archivo debe tener 3 líneas y encontré {len(_lineas)}. ¿Pusiste el \\\\n al final de cada una?"
assert "Ana Gómez" in _lineas[0], "La primera línea debe ser el nombre que RECIBE la función"
assert "Semana 1: fundamentos computacionales" in _lineas[1], "La segunda línea debe ir tal cual el enunciado"

with open("bitacora_semana1.txt", "r", encoding="utf-8") as _f:
    assert _f.read() == _contenido, \\
        "Lo que devuelves tiene que ser EXACTAMENTE lo que quedó guardado en el disco"

# Segunda llamada con otro nombre: el archivo debe reescribirse, no quedarse con el anterior.
_c2 = crear_bitacora("Luis Peña")
assert "Luis Peña" in _c2 and "Ana Gómez" not in _c2, \\
    "Tu función debe usar el nombre que recibe, no uno fijo escrito a mano"

print("Ejercicio 6 superado: creaste, escribiste y leíste un archivo. Eso es gestión de archivos.")''',
        pruebas_ocultas='''# Tercer nombre, con tilde y sin espacios, para descartar cualquier atajo.
_c3 = crear_bitacora("Zulma Ríos")
assert "Zulma Ríos" in _c3 and "Luis Peña" not in _c3''',
        pistas=[
            "Ya tienes el esqueleto. Necesitas dos bloques <code>with</code>: uno con "
            "<code>\"w\"</code> para escribir y otro con <code>\"r\"</code> para leer.",
            "<code>archivo.write(texto)</code> escribe. Para que cada cosa quede en su "
            "propia línea, el texto tiene que terminar en <code>\\n</code>. Y para leer "
            "todo de una vez: <code>archivo.read()</code>.",
            "La primera línea se escribe así: "
            "<code>archivo.write(nombre_estudiante + \"\\n\")</code> — usando el "
            "parámetro, no tu nombre escrito a mano. Y no olvides el "
            "<code>return contenido</code> al final.",
        ],
    )

    c.md("""Ejecuta `!ls -l` y ahí está tu archivo, con su tamaño y su fecha. Ábrelo desde
el explorador de archivos de Jupyter (la pestaña del principio) y verás el
mismo texto. **Una sola cosa, vista desde tres lugares distintos**: tu código,
la terminal y el explorador.
""")

    # --- Ejercicio 7 ------------------------------------------------------
    c.ejercicio(
        numero=7, competencias=['I3', 'I5'], titulo="Tu primer programa completo", estrellas=4, puntos=4,
        enunciado="""El ejercicio final junta todo lo de hoy: variables, tipos, cálculo y texto.

Escribe la función `ficha(nombre, notas)` que recibe:

- `nombre`: el nombre del estudiante, como texto
- `notas`: una lista de números, por ejemplo `[4.0, 3.5, 2.8]`

y **devuelve** (no imprime) una sola línea de texto con este formato exacto:

```
Ana: promedio 3.43 — Aprobado
```

Las reglas:

1. El promedio es la suma de las notas dividida entre cuántas hay.
2. Se muestra con **dos decimales**.
3. El estado es `Aprobado` si el promedio es **mayor o igual a 3.0**, y
   `Reprobado` si no.
4. Entre el promedio y el estado va un guion largo con un espacio a cada lado:
   ` — `. Cópialo de aquí para no pelear con el teclado.

**Dos avisos.** `return` **devuelve** un valor a quien llamó la función; `print`
lo muestra en pantalla y devuelve nada. Aquí se pide `return`. Y para los dos
decimales te sirve `round(promedio, 2)`, aunque hay una forma más directa que
puedes buscar: se llama *f-string*.""",
        partida='''def ficha(nombre, notas):
    ...''',
        solucion='''def ficha(nombre, notas):
    promedio = sum(notas) / len(notas)
    estado = "Aprobado" if promedio >= 3.0 else "Reprobado"
    return f"{nombre}: promedio {promedio:.2f} — {estado}"''',
        pruebas='''assert callable(ficha), "ficha debe ser una funcion definida con def"
_r = ficha("Ana", [4.0, 3.5, 2.8])
assert isinstance(_r, str), "ficha debe DEVOLVER texto con return, no imprimirlo con print"
assert _r == "Ana: promedio 3.43 — Aprobado", \\
    "Con ('Ana', [4.0, 3.5, 2.8]) se espera exactamente: Ana: promedio 3.43 — Aprobado"
print("Ejercicio 7 verificado:", _r)''',
        pruebas_ocultas='''assert ficha("Luis", [2.0, 2.5]) == "Luis: promedio 2.25 — Reprobado"
assert ficha("Sara", [3.0]) == "Sara: promedio 3.00 — Aprobado", \\
    "Exactamente 3.0 aprueba, y los decimales se muestran aunque sean ceros"
assert ficha("Jose", [5.0, 5.0, 5.0]) == "Jose: promedio 5.00 — Aprobado"''',
        pistas=[
            "Divide el problema en tres pasos y resuelvelos por separado: primero el "
            "promedio, luego el estado, y solo al final arma el texto.",
            "Para el promedio tienes `sum(notas)` y `len(notas)` ya hechas en Python. "
            "Para el estado necesitas decidir entre dos textos segun una condicion.",
            "El formato con dos decimales sale con `f\"{promedio:.2f}\"`. Y ojo con el "
            "estado: la nota 3.0 exacta APRUEBA, asi que la comparacion es `>=`, no `>`.",
        ],
    )
    # =========================================================================
    # Bloque 6 — El tutor
    # =========================================================================
    c.seccion(6, "Tus cinco preguntas", 5, """Abajo a la derecha de la pantalla hay un botón con un robot. Es **Ava**, el
tutor de inteligencia artificial del curso. Tres cosas que tienes que saber
antes de tocarlo:

**1. Tienes cinco preguntas por cuadernillo. Cinco. No cinco por ejercicio.**
El contador va abajo en el panel. Se gasta una pregunta solo cuando Ava
alcanza a responder: si se cae la conexión, no pierdes nada.

**2. Ava no te va a dar la respuesta, ni suplicándole.** Está configurado como
tutor socrático: responde con preguntas y pistas. No es tacañería. En la
evaluación escrita —que pesa el 30 %— Ava no entra contigo al salón. Cada vez
que le pides la solución, el que aprende es él; cada vez que le pides una
pregunta, el que aprende eres tú.

**3. Ava ve tu pantalla, pero solo si le apuntas.** Antes de preguntar, **haz
clic en la celda del ejercicio en el que estás atascado**. El panel toma
automáticamente el enunciado, el código que llevas escrito y el último error
que te salió. Si preguntas desde cualquier otra parte del cuadernillo, Ava
responde a ciegas y gastas una pregunta en un «¿en qué ejercicio vas?».""")

    c.md("""### Antes de gastar una pregunta, haz estas tres cosas

Son gratis y resuelven, con mucho, la mayoría de los atascos:

1. **Lee la última línea del mensaje rojo.** Esa línea es la respuesta. Todo lo
   de arriba es contexto.
2. **Usa las tres pistas del ejercicio** (`pista("E3")`). Van de lo
   general a lo concreto y no cuestan nada.
3. **Explícale tu código en voz alta a la pared.** Suena ridículo y funciona:
   la mitad de los errores aparecen solos al obligarte a decir qué hace cada
   línea. Los programadores le dicen «depuración del patito de hule».

### Presupuesto sugerido para este cuadernillo

| Ejercicio | Preguntas sugeridas | Por qué |
|---|---|---|
| 1 (variables y tipos) | **0** | Las comillas deciden el tipo: está explicado en el enunciado |
| 2 (las cuatro herramientas) | **0** | Es de concepto y la respuesta está en la sección 3. Si dudas, relee — es más rápido |
| 3 (trazar el intérprete) | **0–1** | Si tu traza no cuadra, la pregunta buena es sobre el orden de ejecución, no sobre el resultado |
| 4 (tipos de error) | **0** | La tabla comparativa de la sección 4 lo resuelve |
| 5 (arreglar la lógica) | **1** | Aquí sí vale la pena si no ves qué está mal |
| 6 (archivos) | **1** | El manejo de `open` es nuevo y es normal atascarse |
| 7 (tu primera función) | **1–2** | Guarda estas: es el ejercicio más largo del cuadernillo |

### Cómo se pregunta bien

| Pregunta que te va a servir | Pregunta que desperdicia el turno |
|---|---|
| «Me sale `TypeError: can only concatenate str to str` en el ejercicio 5. **No me des la solución: hazme una pregunta** que me ayude a ver qué tipo de dato tengo.» | «Hazme el ejercicio 5.» |
| «Creo que mi error es de lógica porque no sale mensaje rojo pero el número está mal. ¿Cómo compruebo si tengo razón?» | «¿Está bien mi código?» *(sin decir cuál ni qué esperabas)* |
| «Explícame con **otra analogía** la diferencia entre intérprete y compilador; la del traductor no me quedó clara.» | «Explícame todo el cuadernillo.» |
| «Mi mapa conceptual tiene 9 relaciones y el test dice que falta conectar 'procesador'. ¿Qué preguntas debería hacerme sobre el procesador?» | «Dame las 9 relaciones del mapa.» |
| «Voy a decirte lo que **creo** que hace mi código línea por línea. Dime en cuál me equivoco.» | «Corrige esto.» *(pegando el código sin más)* |

Fíjate en el patrón de la columna buena: **dice dónde está, qué esperaba, qué
pasó, y pide una pregunta en vez de una respuesta.**
""")

    c.code('''quiz(
    "A1", 6,
    "Llevas 20 minutos atascado en el ejercicio 6 y te quedan 2 preguntas. "
    "¿Cuál es la mejor jugada?",
    ["Pedirle a Ava el código resuelto y copiarlo",
     "Hacer clic en la celda del ejercicio 6 y pedirle a Ava que me haga preguntas "
     "sobre lo que ya escribí",
     "Preguntarle a Ava desde donde esté, sin seleccionar nada",
     "Saltarme el ejercicio"],
    "Hacer clic en la celda del ejercicio 6 y pedirle a Ava que me haga preguntas "
    "sobre lo que ya escribí",
    "Le diste contexto (la celda) y le pediste el tipo de ayuda que sí te deja "
    "aprendiendo. Las dos cosas, en una sola pregunta.",
    pistas=["Dos cosas importan aquí: <b>dónde</b> haces clic antes de preguntar y "
            "<b>qué</b> le pides. Solo una opción acierta en las dos."],
)''')

    # =========================================================================
    # Bloque 7 — Cierre
    # =========================================================================
    c.seccion(7, "Cierre", 10, """Antes de reclamar tu insignia, tres preguntas que solo te interesan a ti:

1. **¿Qué puedes hacer hoy que no podías esta mañana?** (respóndete en voz
   alta; si la respuesta es «nada», vuelve a la sección 3B)
2. **¿Cuál de los tres tipos de error te parece más peligroso, y por qué?**
3. **Si tuvieras que explicarle a alguien de tu casa qué es el software, ¿qué
   ejemplo usarías?**""")

    c.md("""## Tu entorno de trabajo

Este cuadernillo corre en un computador de la universidad al que entras por el
navegador. Alguien —nosotros— ya instaló ahí Python, Jupyter y todo lo demás,
y por eso hoy pudiste programar a los diez minutos sin pelear con un instalador.

Eso es deliberado: **en la semana 1 nadie debería perder su primera clase
porque un `.exe` falló.**

Pero también sería mentirte decir que ya tienes un entorno. El día que quieras
programar sin internet, hacer tu proyecto final, o trabajar después de que este
curso termine, vas a necesitar **tu propio Python**. Por eso la lista tiene dos
columnas:

| | **Columna A — El entorno del AVA** | **Columna B — Tu entorno local** |
|---|---|---|
| Dónde | En el navegador, servidor de la UIS | En tu computador |
| Quién lo instaló | Nosotros | Tú, en la clase 2 |
| Para qué sirve | Aprender y **ser calificado** | Trabajar por tu cuenta, sin internet |
| ¿De aquí sale tu nota? | **Sí** | **No** |
| ¿Es obligatorio? | Sí, y ya lo tienes | Sí para tu formación, **no para tu nota de hoy** |

### Columna B — la instalación local, con dos rutas honestas

**Ruta 1 — Tengo computador y puedo instalar** *(en la clase 2 o en casa)*

1. Instala **Python** desde `python.org/downloads`. En Windows, marca la
   casilla **«Add python.exe to PATH»** en la primera pantalla. Es la casilla
   que, si no marcas, te va a costar media hora después.
2. Abre una **terminal** (en Windows: `cmd`; en Mac/Linux: Terminal) y escribe
   `python --version`. Si contesta con un número, ganaste.
3. Instala **VS Code** desde `code.visualstudio.com` y, dentro, la extensión
   **Python** de Microsoft.
4. Crea una carpeta `algoritmos-uis` y dentro un archivo `hola.py` con una
   línea: `print("Hola desde mi propio computador")`.
5. Ejecútalo de **tres formas distintas**, que es el punto del ejercicio:
   · desde la terminal, con `python hola.py`
   · desde VS Code, con el botón de ejecutar
   · desde Jupyter, instalándolo con `pip install notebook` y corriendo
     `jupyter notebook`
6. Fíjate en lo que **no** cambia: las tres veces es el mismo intérprete
   ejecutando el mismo archivo. Editor, terminal y cuaderno son tres puertas al
   mismo cuarto.

**Ruta 2 — No tengo computador propio, o no puedo instalar**

Esto no te deja atrás y no te cuesta un punto. Tienes tres opciones, en orden:

1. **La sala de cómputo de la UIS**, en la franja de la clase 2: el profesor
   reserva 20 minutos para hacer la ruta 1 en equipo. Es la opción oficial.
2. **Versión portátil**: WinPython y VS Code Portable caben en una USB y no
   requieren permisos de administrador.
3. **Ninguna por ahora**: sigue con la columna A, que es la que califica, y
   haz la ruta 1 cuando puedas. Avísale al profesor por Moodle para que lo
   sepa; no es un problema, es información.
""")

    c.code("""verificar_entorno()     # columna A, automática
lista_comprobacion()    # columna B, autodeclarada + texto para Moodle""")

    c.code("reclamar_insignia()")

    c.md("""### Para profundizar — y para aprender a elegir fuentes

Una competencia de este curso es **investigar en fuentes confiables**, no en el
primer video que salga. Cuatro para empezar:

- **Computer History Museum** (`computerhistory.org`) — la historia completa,
  con documentos originales. Es un museo: no le paga nadie por convencerte.
- **La documentación oficial de Python** (`docs.python.org/es/3/`) — en
  español. Aburrida y exacta: la fuente definitiva cuando algo no funciona.
- **How to Think Like a Computer Scientist**, edición Runestone — libro de CS1
  abierto, gratuito e interactivo.
- **Real Python** (`realpython.com`) — tutoriales serios, con autor firmado.

**Cómo saber si una fuente es confiable**, en tres preguntas:
*¿quién la publica y qué gana con eso?* · *¿dice de dónde saca lo que afirma?*
· *¿de cuándo es?* (en informática, cinco años es una eternidad).

Y una advertencia específica de 2026: **la IA generativa también es una fuente,
y es una fuente que se equivoca con mucha seguridad.** Ava incluido. Todo lo
que te diga sobre un dato concreto —una fecha, una función, un parámetro—
verifícalo en la documentación oficial. Toma treinta segundos.
""")

    c.md("""---
*Semana 1 · AVA Algoritmos y Programación 41333 · UIS 2026-2*
*Puntos de este cuadernillo: 25. XP: 70. Tu nota viaja sola a Moodle.*
""")

    return c


if __name__ == "__main__":
    construir().escribir(
        os.path.join(os.path.dirname(os.path.dirname(AQUI)),
                     "notebook_semana", "semana_01", "cuadernillo.ipynb")
    )
