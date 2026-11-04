# Cómo acortar los cuadernillos 7 a 16

> **Pautas fijadas por Bryan el 22-sep-2026, tras la reunión con el profesor
> (mandan sobre lo que sigue):**
>
> - Quedan pocas semanas para 16 cuadernillos: **cortos en tiempo (~30 min)**,
>   con **teoría y ejercicios** y nada más. `estimar_tiempo.py` es el juez.
> - Los ejercicios siguen las **temáticas que dio el profesor para las 16
>   semanas**; no se inventan temas.
> - Los enunciados, **en lo posible ligados a la carrera «Ingeniería de IA»**
>   (datos, modelos, clasificación, métricas…), sin cambiar lo que se mide.
> - Solo **tres microcompetencias** se miden con trazas: mCP17 (I1), mCC87 (I3)
>   y mCC103 (I4). Etiqueta I1 solo donde de verdad se aplican matemáticas.
> - Cada cuadernillo lleva las **notas puntuales** que pone el constructor
>   (qué hacer con `raise NotImplementedError`, etc.); no las repitas a mano.
> - Por la semana del 22-sep se llega solo hasta el cuadernillo 6.


**Esto es una indicación, no un trabajo hecho.** Las semanas 7 a 16 no se han
tocado. Aquí queda escrito cómo abordarlas cuando toque, para no tener que
volver a aprender lo que costó aprender en las semanas 3 a 6.

Y una decisión que ya está tomada: **no se les asigna microcompetencia
todavía**. Primero se recortan y se estabilizan; etiquetar un cuadernillo que
va a cambiar es etiquetar dos veces.

---

## 1. El problema que se está resolviendo

Los estudiantes no terminaban los cuadernillos. Ocho ejercicios por semana era
demasiado, y la mitad de la teoría no la necesitaba ningún ejercicio.

Las semanas 3 a 6 pasaron de 32 ejercicios a 22. No se reescribió ninguna: se
quitó lo que sobraba. Esa distinción importa — reescribir desde cero pierde
años de criterio pedagógico acumulado.

## 2. Qué se corta, con el criterio que funcionó

Un ejercicio sobra cuando se cumple alguna de estas, y hay que poder decir
**cuál**:

| Señal | Ejemplo real de las semanas 3-6 |
|---|---|
| **Se resuelve con Ctrl-F** sobre una celda de teoría | «Del español al operador»: su propia pista decía «todos están en la chuleta» |
| **Repite un ejercicio anterior** en otra sintaxis | «El mismo, en Python»: idéntico problema, mismos números, mismas pruebas que el de pseudocódigo |
| **Transcribe la teoría** | «Ordenar por selección»: copiar la celda que lo trae resuelto, quitándole una línea |
| **Solo etiqueta vocabulario**, sin escribir código | «Contador, acumulador o bandera»: emparejar tres palabras |
| **Duplica otra semana** | Los cuatro repasos de la semana 5 repetían las semanas 1 y 2 — uno con las letras permutadas y los mismos datos |

Y la teoría sobra cuando **ningún ejercicio la necesita**. Se comprueba, no se
intuye: busca en los bloques `c.ejercicio(...)` si aparece lo que esa sección
enseña. Así salieron `break`/`continue`/`pass`, los métodos de lista y la
inmutabilidad de las cadenas.

> **Pero mira aguas abajo antes de borrar.** `break` se quitó de la semana 4
> porque ninguna de sus ejercicios lo usaba — y resultó que la semana 6 lo
> necesita en su ejercicio de cierre. Hubo que reponerlo. El análisis por
> semana no basta: un `grep` por las semanas siguientes cuesta diez segundos.

## 3. Qué NO se corta

- **El ejercicio de cierre**, el que integra todo lo de la semana.
- **El de entrada**, el de una estrella. La semana 5 se quedó sin él y ahora
  arranca en dos estrellas: hay un escalón donde antes había una rampa.
- **La única instancia de un concepto.** Aunque parezca que duplica: la semana
  4 perdió su único `while` de Python por parecer redundante con el
  pseudocódigo, y una semana de estructuras repetitivas donde el alumno nunca
  escribe un `while` no tiene sentido.
- **Los ganchos de apertura**: el problema disparador antes de explicar nada.
  Son baratos y son lo que hace que alguien siga leyendo.

## 4. Las trampas que costaron una revisión entera

Todas estas se cometieron y se corrigieron en la fase 5. Están aquí para que no
haya una segunda vez:

1. **`contenido.py` también lleva números.** El total de puntos está escrito
   dos veces: lo suma el constructor y va a mano en el banner de `portada()`.
   Las cuatro semanas quedaron anunciando «80 puntos» cuando ya eran 65, 65,
   50 y 65. Hoy `build.py` lo comprueba y falla si no cuadran, pero el resto
   de duplicaciones no las vigila nadie.
2. **Los números de ejercicio cableados en prosa envejecen.** Pistas, ejemplos
   del tutor y preguntas de cierre que decían «el ejercicio 7». Escribe el
   **nombre de la función**, no el número.
3. **Una prueba VISIBLE puede llevar el número dentro.** Un `print("Ejercicio 8
   verificado")` sobrevivió a la renumeración y lo leía el estudiante.
4. **Los objetivos prometen lo que borraste.** «Al terminar vas a poder usar
   `round`, `abs`, `min`, `max` y `pow`» después de eliminar esa sección.
5. **`verificar.py` puede darte el visto bueno sobre los `.ipynb` viejos.** Si
   `build.py` falló, verificas la versión anterior y no te enteras. Mira
   siempre la salida entera de `build.py`, no solo el resumen.
6. **Renumerar solo es seguro sin entregas.** El `grade_id` es
   `ejercicio_{numero}` y ese mismo string es la `exercise_id` de la
   telemetría. Comprueba en el servidor qué hay en `release/` y en
   `submitted/` **antes** de tocar nada.

## 5. La estructura a la que se llegó

- Teoría breve, la justa para resolver los ejercicios.
- **5 o 6 ejercicios calificables**, de menos a más estrellas.
- Guardar y entregar al principio **y al final** — ya lo inyecta `custom.js`
  en todos los cuadernillos, no hay que añadirlo.
- Metodología ABP: problema disparador → exploración dirigida → ejecución →
  retroalimentación inmediata.

Con una excepción que conviene recordar: **la semana 5 se quedó en cuatro a
propósito**, porque lleva la primera evaluación y repetir dentro del cuadernillo
lo que ya se evalúa aparte no ayuda a nadie. El número sale del contenido real
de la sesión, no de una cuota.

## 6. Cuando llegue el momento de etiquetar

La tabla semana → microcompetencia de la planeación académica 41333 está en
[`modelo_microcompetencias.md`](modelo_microcompetencias.md). Dos avisos que
salieron de aplicarla:

- **No repartas una competencia a ciegas porque la tabla la nombre.** En las
  semanas 1 y 2, la planeación asigna mCC103 y ningún ejercicio la mide: lo que
  piden es escribir algoritmos, no juzgar si un problema de una organización es
  tratable algorítmicamente. Se dejó sin etiquetar y se reportó, en vez de
  inventar evidencia.
- **Un ejercicio sin etiqueta es válido y es honesto.** `build.py` lo avisa en
  cada construcción, así que el hueco queda a la vista en lugar de disimulado
  bajo una etiqueta que no significa nada.
