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

- Contar, sin leer, **de dónde salió la computación**: de una idea matemática
  de hace mil años, no de un aparato.
- Señalar qué parte de un sistema es **hardware**, cuál es **software**, cuál
  es un **dato** y cuál es un **proceso** — y no confundirlos nunca más.
- Explicar por qué existen **tres alturas de lenguaje** (máquina, ensamblador,
  alto nivel) y ver la misma suma escrita en las tres.
- Distinguir un **editor**, una **terminal**, un **intérprete** y un **IDE**, y
  decir para qué sirven Python, VS Code y Jupyter sin repetir un eslogan.
- Crear, escribir y leer un **archivo** desde código.
- Reconocer los **tres tipos de error** —sintaxis, ejecución y lógica— y saber
  cuál de los tres nadie te va a avisar.

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
    # Bloque 3A — Historia, hardware y software
    # =========================================================================
    c.seccion(3, "La máquina por dentro", 35, """### 3A. Mil años en cinco minutos

La palabra **algoritmo** no viene de la informática: viene del nombre de una
persona. Y el primer programa de la historia se escribió **un siglo antes** de
que existiera el primer computador. Ejecuta la línea de tiempo.""")

    c.code("linea_de_tiempo()")

    c.md("""Fíjate en el ENIAC: 27 toneladas y 17.000 tubos de vidrio para hacer menos
cuentas que la calculadora de tu celular. ¿Qué cambió? El **transistor**, y el
hecho de que cada año caben más en el mismo pedazo de silicio.
""")

    c.code("grafica_transistores()")

    c.md("""Y mientras el hardware se encogía, el **software** hacía el camino contrario:
subía de altura.

| Época | Cómo se le hablaba a la máquina | Quién traducía |
|---|---|---|
| 1945 | Moviendo cables y interruptores | Nadie: la persona *era* el traductor |
| 1949 | **Lenguaje ensamblador**: `ADD`, `MOV`, `JMP` | Un programa ensamblador |
| 1957–1959 | **FORTRAN, COBOL**: fórmulas y frases | Un compilador |
| 1972 | **C**: alto nivel con control fino de la memoria | Un compilador |
| 1991 | **Python**: código que se lee casi como inglés | Un **intérprete** |
| 2015–hoy | Librerías de IA: describes el modelo, no el cálculo | Capas y capas de lo anterior |

Cada fila de esa tabla es la misma jugada: **alguien escribió un programa para
no tener que volver a escribir lo de abajo a mano.** Eso es, literalmente, la
historia del software.
""")

    c.md("""### Las cuatro cosas que hay dentro de un sistema

Ejecuta el diagrama y quédate con las cuatro palabras: te las van a preguntar
toda la carrera.
""")

    c.figura("s01_d2_capas",
             "Hardware, software, dato y proceso: el ciclo no se acaba nunca.")

    c.md("""| | Qué es | Cómo lo reconoces | Ejemplo en la UIS |
|---|---|---|---|
| **Hardware** | Lo físico | Se puede golpear (no lo hagas) | El portátil de la sala de cómputo, el lector del carné |
| **Software** | Las instrucciones | Se instala, se actualiza, se borra | Moodle, Python, el juego del celular |
| **Dato** | Lo que se guarda y se transforma | Es un valor: un número, un texto, una foto | Tu nota 4.3, tu foto del carné, la placa de un bus |
| **Proceso** | Lo que se hace con los datos | Es un verbo | Calcular el promedio, ordenar por apellido, cobrar el pasaje |

Un error clásico de primer semestre: creer que un archivo de Word es software.
No lo es. **Word es software; tu documento es un dato.** El software es la
receta, el dato es el ingrediente y el proceso es cocinar.
""")

    c.md("""### ¿Y las «aplicaciones informáticas»?

Todo el software del mundo cabe en cuatro cajones. Ejecuta el diagrama.
""")

    c.figura("s01_d7_aplicaciones",
             "Los cuatro cajones, con ejemplos que ya usas en Bucaramanga.")

    c.md("""Detalle que casi nadie nota el primer día: **el software de desarrollo también
es software**. Python, VS Code y Jupyter son programas que sirven para escribir
programas. Estás usando un programa para aprender a hacer programas. Bienvenido
al oficio.
""")

    c.md("Tres preguntas rápidas. No tienen nota: dan XP y te dicen si te quedó claro.")

    c.code('''quiz(
    "Q1", 6,
    "El primer algoritmo pensado para una máquina se escribió…",
    ["un siglo antes de que existiera el primer computador",
     "al mismo tiempo que el ENIAC",
     "cuando se inventó Python",
     "en 1936, con Turing"],
    "un siglo antes de que existiera el primer computador",
    "Ada Lovelace, 1843. La Máquina Analítica para la que lo escribió nunca "
    "llegó a construirse: el algoritmo es anterior al aparato.",
    pistas=["Vuelve a la línea de tiempo: la máquina para la que se escribió ni "
            "siquiera llegó a construirse."],
)''')

    c.code('''quiz(
    "Q2", 6,
    "¿Cuál de estas afirmaciones es FALSA?",
    ["El ENIAC se programaba moviendo cables",
     "Un archivo de Word es software",
     "Un transistor es hardware",
     "Ordenar la lista del curso es un proceso"],
    "Un archivo de Word es software",
    "Word es software; tu documento es un <b>dato</b>. La receta y el "
    "ingrediente no son la misma cosa.",
    pistas=["Tres de las cuatro son ciertas. Piensa en la diferencia entre la "
            "receta y el ingrediente."],
)''')

    c.code('''quiz(
    "Q3", 6,
    "El software que controla los semáforos de la Carrera 27 es…",
    ["una aplicación de usuario",
     "una aplicación especializada de control",
     "un sistema operativo",
     "una herramienta de desarrollo"],
    "una aplicación especializada de control",
    "Nadie se sienta delante de él: gobierna un equipo del mundo real, igual "
    "que el software de un ascensor o de una máquina de la planta.",
    pistas=["No lo usa una persona en un escritorio ni sirve para escribir "
            "programas: gobierna un equipo del mundo real."],
)''')

    # =========================================================================
    # Bloque 3B — Los tres pisos
    # =========================================================================
    c.md("""### 3B. Los tres pisos del edificio

Tu procesador no entiende `print`. No entiende `suma`. No entiende **ninguna
palabra**. Solo entiende números, y ni siquiera en decimal: en binario, unos y
ceros que en el fondo son «hay corriente» y «no hay corriente».

Entonces, ¿cómo diablos funcionó tu programa?

Porque entre tú y el silicio hay **pisos**. Vamos a bajarlos uno por uno, con la
misma cuenta de siempre: **4 + 9**.
""")

    c.md("""#### Piso 3 — Alto nivel: lo que tú escribes

Cerca de una persona, lejos de la máquina. Se lee casi como inglés.
""")

    c.code('''def sumar(a, b):
    return a + b

print(sumar(4, 9))''')

    c.md("""#### Piso 2 — Bajo nivel: lo que entiende la máquina virtual de Python

Antes de ejecutar nada, Python **traduce** tu función a una lista de órdenes
mínimas, cada una tan simple que no se puede partir más: «trae `a`», «trae
`b`», «súmalos», «devuélvelo». Eso se llama **bytecode**, y es el pariente
directo del **lenguaje ensamblador**.

Puedes verlo. En serio. Ejecuta:
""")

    c.code("""import dis
dis.dis(sumar)""")

    c.md("""Léelo así, ignorando los números de la izquierda:

| Orden | Qué significa |
|---|---|
| `RESUME` | «arranca» (papeleo interno de Python; ignóralo) |
| `LOAD_FAST a` | trae el valor de `a` y ponlo sobre la mesa |
| `LOAD_FAST b` | trae el valor de `b` y ponlo sobre la mesa |
| `BINARY_OP +` | toma los dos de la mesa, súmalos, deja el resultado |
| `RETURN_VALUE` | entrega lo que quedó en la mesa |

Cinco órdenes para una suma. **Tú escribiste una línea; la máquina necesitó
cinco pasos.** Y esto todavía no es lenguaje de máquina de verdad: es el
ensamblador de una máquina *imaginaria* (la máquina virtual de Python).

*(Este listado es el de Python 3.11, que es el del AVA. Si en tu computador ves
líneas de más o con otro nombre, ignóralas: dependen de la versión.)*

Si en vez de Python usáramos C++ —que se compila directo al procesador— el
ensamblador real de un Intel se vería así (no lo ejecutes, solo léelo):

```asm
mov  eax, DWORD PTR [rbp-4]   ; trae a
add  eax, DWORD PTR [rbp-8]   ; súmale b
ret                           ; devuelve el resultado
```

¿Ves el parecido? *Trae, suma, devuelve.* Todos los ensambladores del mundo
dicen lo mismo con otras palabras.
""")

    c.md("""#### Piso 1 — Lenguaje de máquina: lo que de verdad viaja

Ni siquiera `LOAD_FAST` existe dentro del computador. Esa palabra es un favor
que nos hace Python para que podamos leer. Lo que hay de verdad son **bytes**.
Míralos:
""")

    c.code('''crudo = sumar.__code__.co_code
print("Los mismos 5 pasos, en bytes:", list(crudo))
print()
print("Y en binario, que es lo único que existe de verdad:")
print(" ".join(format(b, "08b") for b in crudo))''')

    c.md("""Eso —esa fila de unos y ceros— es tu función. No una foto de tu función: **es
tu función**. Cada `1` es un transistor con corriente y cada `0` es uno sin
corriente.

Ahora entiendes la frase completa: *bajar de nivel es acercarse a la máquina y
alejarse de la persona*.
""")

    c.figura("s01_d3_niveles",
             "La misma suma, tres veces. Lo que cambia es a qué altura está escrita.")

    c.code("tres_pisos(sumar)     # los tres paneles, con la MISMA función")

    c.md("""### Maneja tú una máquina de verdad (una pequeñita)

Ver bytes es una cosa; **darle órdenes en su idioma** es otra. Te presento la
**MiniMáquina**: un computador de mentiras con una sola gaveta (el
*acumulador*) y cuatro instrucciones. Su lenguaje de máquina son números:

| Código | Instrucción | Qué hace |
|---|---|---|
| `1 n` | CARGAR n | pone `n` en la gaveta, botando lo que hubiera |
| `2 n` | SUMAR n | le suma `n` a lo que hay en la gaveta |
| `3 0` | MOSTRAR | muestra lo que hay en la gaveta |
| `0 0` | PARAR | apaga la máquina |

Cada instrucción son **dos números**: el código y su argumento. Un programa es
una lista de números y nada más. Ejecuta este y mira la traza:
""")

    c.code('''programa = [1, 4,    # CARGAR 4
            2, 9,    # SUMAR 9
            3, 0,    # MOSTRAR
            0, 0]    # PARAR

MiniMaquina(programa).ejecutar(traza=True)''')

    c.md("""Acabas de **programar en lenguaje de máquina**. Sin comillas, sin metáfora: le
diste a una máquina una lista de números y los obedeció en orden.

Y ahora la moraleja de toda la sección. Estas tres cosas hacen exactamente lo
mismo:

```
[1, 4, 2, 9, 3, 0, 0, 0]        <- lenguaje de máquina  (la máquina feliz, tú perdido)
CARGAR 4 / SUMAR 9 / MOSTRAR    <- ensamblador          (empate incómodo)
print(4 + 9)                    <- alto nivel           (tú feliz, alguien tradujo por ti)
```

Los tres pisos existen porque **alguien tuvo que ceder**. Durante veinte años
cedieron las personas. Desde FORTRAN cede la máquina — y ese «alguien que
traduce» es el intérprete que vas a conocer en un minuto.
""")

    # =========================================================================
    # Bloque 3C — El entorno
    # =========================================================================
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
        numero=1, competencias=['I4'], titulo="Hardware, software, dato o proceso", estrellas=1, puntos=3,
        enunciado="""Esta es la versión individual de la actividad que hicieron en clase. Abajo hay
ocho cosas de la vida real de la UIS. Clasifica cada una escribiendo **una** de
estas cuatro palabras, entre comillas:

`"hardware"` · `"software"` · `"dato"` · `"proceso"`

La primera ya está resuelta como ejemplo. Si dudas, vuelve a la tabla de la
sección 3A: *el software es la receta, el dato es el ingrediente, el proceso es
cocinar y el hardware es la olla.*""",
        partida='''# Reemplaza cada  ...  por una de estas cuatro palabras, entre comillas:
#     "hardware"    "software"    "dato"    "proceso"
CLASIFICACION = {
    "el mouse del portátil":                    "hardware",   # resuelto, de ejemplo
    "WhatsApp":                                 ...,
    "la nota 4.3 de tu primer parcial":         ...,
    "ordenar la lista del curso por apellido":  ...,
    "la pantalla táctil del cajero automático": ...,
    "Windows 11":                               ...,
    "la foto de tu carné de la UIS":            ...,
    "calcular el promedio del semestre":        ...,
}''',
        solucion='''CLASIFICACION = {
    "el mouse del portátil":                    "hardware",
    "WhatsApp":                                 "software",
    "la nota 4.3 de tu primer parcial":         "dato",
    "ordenar la lista del curso por apellido":  "proceso",
    "la pantalla táctil del cajero automático": "hardware",
    "Windows 11":                               "software",
    "la foto de tu carné de la UIS":            "dato",
    "calcular el promedio del semestre":        "proceso",
}''',
        pruebas='''assert isinstance(CLASIFICACION, dict), "CLASIFICACION debe seguir siendo un diccionario"
assert len(CLASIFICACION) == 8, "No agregues ni borres filas: son ocho"
assert all(isinstance(v, str) for v in CLASIFICACION.values()), \\
    "Cada respuesta va entre comillas, como texto"

corregir("ejercicio_1", CLASIFICACION)
print("Ejercicio 1 superado: distingues hardware, software, datos y procesos.")''',
        pistas=[
            "Hazte una pregunta por cada fila: ¿esto lo puedo tocar? Si sí, es hardware.",
            "De las que quedan: ¿es un <i>verbo</i> (algo que se hace) o un <i>valor</i> "
            "(algo que se guarda)? Verbo &rarr; proceso; valor &rarr; dato.",
            "Ejemplo resuelto: «Windows 11» no se puede tocar, no es un valor y no es "
            "una acción que alguien realiza: es un conjunto de instrucciones que se "
            "instala. Aplica ese mismo razonamiento a las demás.",
        ],
    )

    # --- Ejercicio 2 ------------------------------------------------------
    c.ejercicio(
        numero=2, competencias=['I4'], titulo="La escalera de los lenguajes", estrellas=1, puntos=3,
        enunciado="""Los cuatro fragmentos de abajo hacen **lo mismo**: sumar dos números. Lo que
cambia es a qué altura están escritos.

Ordénalos en la lista `NIVELES`, del **más cercano a la máquina** (posición 1)
al **más cercano a una persona** (posición 4). Copia los textos tal cual, con
sus comillas.

```
A)  std::cout << a + b;
B)  10110000 01100001
C)  print(a + b)
D)  MOV AL, 61h
```

Pista conceptual, no técnica: pregúntate en cuál de los cuatro **no aparece
ninguna palabra**, y en cuál se parece más a algo que dirías en voz alta.""",
        partida='''NIVELES = [
    ...,   # 1 = lo más cerca de la máquina
    ...,
    ...,
    ...,   # 4 = lo más cerca de una persona
]''',
        solucion='''NIVELES = [
    "10110000 01100001",
    "MOV AL, 61h",
    "std::cout << a + b;",
    "print(a + b)",
]''',
        pruebas='''assert isinstance(NIVELES, list) and len(NIVELES) == 4, "NIVELES debe ser una lista de 4 textos"
assert all(isinstance(x, str) for x in NIVELES), "Copia los fragmentos como texto, entre comillas"
assert len(set(NIVELES)) == 4, "No repitas fragmentos: cada uno va una sola vez"

corregir("ejercicio_2", NIVELES)
print("Ejercicio 2 superado: ya sabes leer la altura de un lenguaje.")''',
        pistas=[
            "Empieza por los extremos, que son los fáciles: ¿cuál no tiene ni una sola "
            "letra que un humano pueda leer? Ese es el 1.",
            "<code>MOV</code> es una abreviatura de <i>move</i>: es ensamblador, el "
            "piso 2 de la sección 3B.",
            "Quedan dos lenguajes de alto nivel. El que está más abajo es el que se "
            "compila directo al procesador y te obliga a ser más específico; el que "
            "está más arriba es el que estás aprendiendo.",
        ],
    )

    c.md("""*¿Por qué C++ va por debajo de Python?* Porque se compila directo a código de
máquina y te obliga a declarar tipos y detalles que Python resuelve solo. Los
dos son de alto nivel; uno está un escalón más abajo que el otro.
""")

    # --- Ejercicio 3 ------------------------------------------------------
    c.ejercicio(
        numero=3, competencias=['I3', 'I4'], titulo="Escribe en lenguaje de máquina", estrellas=2, puntos=4,
        enunciado="""Tu turno de darle órdenes a la MiniMáquina en su propio idioma. Recuerda su
repertorio completo:

| Código | Instrucción | Qué hace |
|---|---|---|
| `1 n` | CARGAR n | pone `n` en la gaveta |
| `2 n` | SUMAR n | le suma `n` a la gaveta |
| `3 0` | MOSTRAR | muestra lo que hay en la gaveta |
| `0 0` | PARAR | apaga la máquina |

**Escribe el programa que calcule 4 + 9 + 7 y muestre el resultado.**

Tres reglas que la máquina exige:
- se CARGA **una sola vez** (el primer número); los demás se SUMAN
- hay que MOSTRAR antes de PARAR, o nadie verá nada
- todo programa termina con PARAR""",
        partida='''# Escribe la lista completa. La primera instrucción va de regalo:
#   1, 4   significa  CARGAR 4
programa_suma = [
    1, 4,     # CARGAR 4
    # <- sigue tú: SUMAR 9, SUMAR 7, MOSTRAR y PARAR
]''',
        solucion='''programa_suma = [
    1, 4,     # CARGAR 4
    2, 9,     # SUMAR 9
    2, 7,     # SUMAR 7
    3, 0,     # MOSTRAR
    0, 0,     # PARAR
]''',
        pruebas='''assert isinstance(programa_suma, list), "programa_suma tiene que ser una lista"
assert all(isinstance(x, int) for x in programa_suma), "Todo en lenguaje de máquina son números enteros"
assert len(programa_suma) % 2 == 0, "Cada instrucción son DOS números: código y argumento"
assert set(programa_suma[0::2]) <= {0, 1, 2, 3}, \\
    "Usaste un código de instrucción que la MiniMáquina no conoce (solo 0, 1, 2 y 3)"
assert programa_suma[0::2].count(1) == 1, \\
    "Se CARGA una sola vez: los demás números se SUMAN"

_maquina = MiniMaquina(programa_suma)
_salidas = _maquina.ejecutar(traza=False)

assert _maquina.termino_con_parar, "Todo programa debe terminar con PARAR (0, 0)"
assert _salidas, "Tu programa no mostró nada: ¿le pusiste MOSTRAR (3, 0)?"
assert _salidas == [20], f"La MiniMáquina mostró {_salidas} y esperábamos [20]"

print("Ejercicio 3 superado: escribiste y ejecutaste un programa en lenguaje de máquina.")''',
        pistas=[
            "Ya tienes la primera instrucción puesta. Te faltan tres: sumar el segundo "
            "número, sumar el tercero, y mostrar. Y al final, parar.",
            "Cada instrucción ocupa DOS posiciones de la lista. <code>SUMAR 9</code> se "
            "escribe <code>2, 9</code>. MOSTRAR no necesita argumento, pero igual lleva "
            "su segundo número: <code>3, 0</code>.",
            "Tu lista debe tener 10 números en total: 5 instrucciones × 2. Empieza con "
            "<code>1, 4</code> y termina con <code>0, 0</code>.",
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
    c.md("""Antes del último ejercicio, ejecuta esta celda: es el vocabulario cerrado con el
que se arma el mapa. Puedes volver a ella cuando quieras.
""")
    c.code("ver_vocabulario()")

    c.ejercicio(
        numero=7, competencias=['I5'], titulo="Arma tu mapa de la computación", estrellas=4, puntos=4,
        enunciado="""Último ejercicio, y el que más vale la pena. Vas a dibujar el mapa de todo lo
que viste hoy — pero en vez de arrastrar cajitas con el mouse, lo vas a
**escribir**, que es como se representan las ideas cuando una máquina tiene que
entenderlas.

Un mapa conceptual es una lista de **relaciones**, y cada relación es una frase
de tres partes:

```
("intérprete",  "traduce",  "lenguaje de alto nivel")
  ^ de qué        ^ qué hace     ^ con qué
```

que se lee: *«el intérprete traduce el lenguaje de alto nivel»*.

**Tu tarea:** agrega **al menos 6 relaciones tuyas** a las 3 de ejemplo, usando
solo el vocabulario permitido. Ejecuta `ver_vocabulario()` para verlo cuando
quieras.

**Regla de oro:** cada relación tuya tiene que poder leerse en voz alta como una
frase con sentido. Si suena rara al decirla, está mal.

Y cuatro relaciones **no pueden faltar** — son el corazón de esta semana. Si
repasaste la sección 3, ya sabes cuáles son.""",
        partida='''MAPA = [
    ("computador", "se compone de", "hardware"),          # ejemplo
    ("computador", "se compone de", "software"),          # ejemplo
    ("Python", "es un", "lenguaje de alto nivel"),        # ejemplo
    # Agrega aquí abajo AL MENOS 6 relaciones tuyas, una por línea y con esta forma:
    #     ("concepto", "relación", "concepto"),
]''',
        solucion='''MAPA = [
    ("computador", "se compone de", "hardware"),
    ("computador", "se compone de", "software"),
    ("Python", "es un", "lenguaje de alto nivel"),
    ("procesador", "ejecuta", "lenguaje de máquina"),
    ("intérprete", "traduce", "lenguaje de alto nivel"),
    ("IDE", "se compone de", "editor"),
    ("proceso", "produce", "dato"),
    ("hardware", "se compone de", "procesador"),
    ("dato", "se guarda en", "archivo"),
    ("programa", "puede tener", "error de lógica"),
]''',
        pruebas='''assert isinstance(MAPA, list), "MAPA debe ser una lista"
assert len(MAPA) >= 9, f"Tu mapa tiene {len(MAPA)} relaciones y necesita al menos 9 (3 de ejemplo + 6 tuyas)"

for _t in MAPA:
    assert isinstance(_t, tuple) and len(_t) == 3, \\
        f"Cada relación es una tupla de tres textos. Revisa esta: {_t}"
    assert _t[0] in VOCABULARIO, f"'{_t[0]}' no está en el vocabulario. Ejecuta ver_vocabulario()"
    assert _t[2] in VOCABULARIO, f"'{_t[2]}' no está en el vocabulario. Ejecuta ver_vocabulario()"
    assert _t[1] in RELACIONES, f"'{_t[1]}' no es una relación permitida. Ejecuta ver_vocabulario()"
    assert _t[0] != _t[2], f"Un concepto no se relaciona consigo mismo: {_t}"

_conceptos = {t[0] for t in MAPA} | {t[2] for t in MAPA}
assert len(_conceptos) >= 8, f"Usaste {len(_conceptos)} conceptos distintos y necesitas al menos 8"
assert len(set(MAPA)) == len(MAPA), "Hay una relación repetida: cada una va una sola vez"

corregir("ejercicio_7", MAPA)     # comprueba las 4 relaciones nucleares

dibujar_mapa(MAPA)
print("Ejercicio 7 superado. Tu mapa quedó dibujado arriba: revísalo con la rúbrica de abajo.")''',
        pistas=[
            "Recorre el cuadernillo de arriba abajo y por cada sección pregúntate: ¿qué "
            "dos conceptos de esta sección van juntos, y con qué verbo? La sección 3A te "
            "da dos, la 3B te da dos, la 3C te da dos y la 4 te da una.",
            "Las cuatro obligatorias contestan estas cuatro preguntas: ¿qué ejecuta el "
            "lenguaje de máquina? ¿quién traduce el alto nivel? ¿de qué está hecho un "
            "IDE? ¿qué produce un proceso?",
            "Una que ya está resuelta como modelo: "
            "<code>(\"procesador\", \"ejecuta\", \"lenguaje de máquina\")</code>. Te "
            "faltan tres del mismo estilo: mira las columnas de la tabla de la "
            "sección 3C.",
        ],
    )

    c.md("""#### Lo que la máquina NO puede corregirte

El cuadernillo comprueba que tu mapa esté **bien armado**: que uses el
vocabulario, que conectes al menos ocho conceptos y que no se te escapen las
cuatro relaciones que son el corazón de esta semana. Lo que **no** puede
comprobar es si tus otras relaciones son buenas ideas o disparates con buena
ortografía. Eso lo miras tú con la rúbrica de abajo y lo mira el profesor en
clase. Es honesto decírtelo: una máquina puede verificar la forma de una idea,
no su valor.

**Rúbrica de autoevaluación.** Mira tu mapa dibujado y contéstate:

| Criterio | Sí / Todavía no |
|---|---|
| ¿Cada relación mía se puede leer en voz alta como una frase con sentido? | |
| ¿Conecté las dos mitades del mapa (lo físico con lo abstracto), o quedaron dos islas? | |
| ¿Hay algún concepto que quedó suelto, sin ninguna flecha? | |
| ¿Podría explicarle mi mapa a alguien de mi casa en dos minutos? | |
""")

    c.figura("s01_d9_mapa_modelo",
             "Un mapa posible. No es «el» mapa correcto: compara la forma, no las palabras.")

    # =========================================================================
    # Bloque 6 — El reto
    # =========================================================================
    c.seccion(6, "El reto: MiniMáquina 2.0", 10, """*(opcional, sin nota)*

La MiniMáquina sabe cargar, sumar, mostrar y parar. Le falta **restar**.

Abajo está su motor completo — el mismo que ejecutaste en la sección 3B, sin
trucos. Léelo (vas a entender más de lo que crees), y **agrégale la instrucción
`4 n` = RESTAR n**.

No hay verificador ni puntos. Hay algo mejor: si funciona, acabas de ampliar el
repertorio de instrucciones de un procesador. Eso es literalmente diseñar
hardware.

Si te sobran ganas: agrégale también `5 n` = MULTIPLICAR, y después intenta
escribir un programa que calcule el promedio de tres notas usando solo tus
instrucciones. Vas a descubrir por qué se inventaron los lenguajes de alto
nivel.""")

    c.code('''def mi_minimaquina(programa):
    """La MiniMáquina entera. Léela de arriba abajo: es más simple de lo que parece."""
    acumulador = 0          # la única gaveta que tiene la máquina
    mostrados = []          # lo que fue mostrando por el camino
    i = 0                   # dónde va leyendo dentro de la lista

    while i + 1 < len(programa):        # mientras queden instrucciones completas
        codigo = programa[i]            # qué hay que hacer
        argumento = programa[i + 1]     # con qué número

        if codigo == 1:                 # CARGAR
            acumulador = argumento
        elif codigo == 2:               # SUMAR
            acumulador = acumulador + argumento
        elif codigo == 3:               # MOSTRAR
            print("La gaveta tiene:", acumulador)
            mostrados.append(acumulador)
        elif codigo == 0:               # PARAR
            break
        # <- AGREGA AQUÍ TU INSTRUCCIÓN
        #    elif codigo == 4:          # RESTAR
        #        ...

        i = i + 2                       # cada instrucción ocupa dos posiciones

    return mostrados


# 4 + 9 - 6 debería mostrar 7. Mientras RESTAR no exista, la máquina se salta
# esa instrucción y muestra 13. Ejecuta, mira el 13, y arréglalo.
mi_minimaquina([1, 4, 2, 9, 4, 6, 3, 0, 0, 0])''')

    # =========================================================================
    # Bloque 7 — El tutor
    # =========================================================================
    c.seccion(7, "Tus cinco preguntas", 5, """Abajo a la derecha de la pantalla hay un botón con un robot. Es **Ava**, el
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
| 1 y 2 (clasificar, ordenar) | **0** | Son de concepto: la respuesta está en la sección 3. Si dudas, relee — es más rápido |
| 3 (MiniMáquina) | **0–1** | Si el programa no muestra 20, tu pregunta ideal es sobre la tabla de traza |
| 4 (tipos de error) | **0** | La tabla comparativa de la sección 4 lo resuelve |
| 5 (arreglar la lógica) | **1** | Aquí sí vale la pena si no ves qué está mal |
| 6 (archivos) | **1** | El manejo de `open` es nuevo y es normal atascarse |
| 7 (mapa conceptual) | **1–2** | Guarda estas: es el ejercicio abierto |

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
    # Bloque 8 — Cierre
    # =========================================================================
    c.seccion(8, "Cierre", 10, """Antes de reclamar tu insignia, tres preguntas que solo te interesan a ti:

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
