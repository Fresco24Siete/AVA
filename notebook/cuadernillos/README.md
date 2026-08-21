# Cuadernillos del curso 41333

Aquí se **autoran** los cuadernillos semanales del AVA. Un cuadernillo es el
material de una semana lectiva: la teoría de las dos clases presenciales, el
laboratorio y los ejercicios autocalificados.

El `.ipynb` es una **salida generada**, no una fuente. Se edita el generador de
Python, no el JSON del notebook: así un cambio de contenido se revisa en un diff
legible y no en una línea de 40 000 caracteres.

## Estructura

```
notebook/cuadernillos/
├── build.py              Construye los .ipynb y valida los contratos del AVA
├── constructor.py        Arma el .ipynb con los metadatos que el AVA espera
├── motor/ava_motor.py    Capa lúdica: barra de XP, quices, pistas, verificadores
├── diagramas/
│   ├── mmd/*.mmd         Diagramas de flujo en Mermaid (fuente)
│   ├── svg/*.svg         Renderizados y versionados (lo que se incrusta)
│   └── render.py         mmd -> svg optimizado (necesita Node; solo al autorar)
├── semana_01/generador.py
└── semana_02/generador.py
```

La salida va a `notebook/notebook_semana/<codigo>/cuadernillo.ipynb`, que es lo
que la imagen copia a `/opt/plantillas`.

## Del generador al alumno

```
generador.py                     autoría
   │  build.py
   ▼
notebook_semana/semana_01/cuadernillo.ipynb
   │  docker build ./notebook   (queda en /opt/plantillas/semana_01/)
   ▼
entrypoint.sh (rol instructor)   siembra source/semana_01/ en nbgrader
   │
   ▼
formgrader -> Generate           borra soluciones y pruebas ocultas -> release/
   │
   ▼
publicar-cuadernillo semana_01   escribe el manifest con la ventana de tiempo
   │
   ▼
entrypoint.sh (rol estudiante)   entregar-cuadernillo -> work/cuadernillo.ipynb
```

Dos consecuencias de este camino que condicionan todo el diseño:

- **Al alumno le llega un solo archivo.** `entregar-cuadernillo` copia el
  `.ipynb` y nada más. No hay imágenes, ni módulos, ni `requirements.txt` al
  lado. Por eso los diagramas van incrustados como SVG y el motor lúdico va
  incrustado como código dentro de la primera celda.
- **El nombre de la carpeta es el `cuadernillo_id`.** `semana_01` viaja hasta el
  manifest y de ahí a `CUADERNILLO_CODIGO`, que es la clave con la que el tutor
  cuenta las 5 preguntas por cuadernillo y con la que se etiqueta la telemetría.

## Construir

```bash
python3 notebook/cuadernillos/build.py             # todos
python3 notebook/cuadernillos/build.py semana_01   # uno
python3 notebook/cuadernillos/build.py --legible   # motor sin comprimir, para depurar
```

`build.py` valida antes de darse por bueno: pares de celdas de nbgrader
completos, `grade_id` únicos, prefijo `test_` en las celdas que califican y
`metadata.tutor_ia` presente. Un par mal formado no falla en Jupyter — falla en
silencio, dejando el ejercicio fuera de la nota y fuera de la analítica.

Si cambias un diagrama:

```bash
python3 notebook/cuadernillos/diagramas/render.py            # solo lo que cambió
python3 notebook/cuadernillos/diagramas/render.py --revisar  # sin renderizar
```

Los `.svg` se versionan a propósito: construir un cuadernillo no debe exigir
Node, y el diagrama no debe cambiar solo porque cambió la versión de Mermaid.

### Tres reglas al escribir un `.mmd`

Las tres salieron de renderizar y mirar el resultado, no del manual. Mermaid no
avisa de ninguna: el diagrama sale mal y ya. `render.py --revisar` las comprueba.

1. **`<` y `>` hay que escribirlos como entidad.** `C{saldo >= pasaje}` se dibuja
   como «saldo = pasaje»: el `>` desaparece. Entrecomillar **no** basta; hay que
   escribir `C{"saldo &gt;= pasaje"}`. Un rombo que dice «saldo = pasaje» en un
   curso donde se está enseñando la diferencia entre `=` y `>=` es un problema
   serio, no un detalle estético.
2. **De HTML solo funciona `<br/>`.** Los diagramas se renderizan con texto SVG
   real, no con HTML incrustado, así que `<b>Total</b>` se dibuja con los signos
   a la vista. Para destacar un nodo, cámbiale el color con `style`.
3. **No hace falta tocar la configuración de svgo.** Está fijada conservadora a
   propósito: la de por defecto deja el archivo un 15 % más pequeño pero
   convierte las etiquetas de las aristas («Sí», «No») en cuadrados negros.

## Las dos capas de un ejercicio

Conviene tenerlo claro porque se parecen y no son lo mismo:

| | Motor lúdico (`ava.quiz`, `ava.ordenar`, `ava.comprobar`) | nbgrader (`ejercicio_N` / `test_ejercicio_N`) |
|---|---|---|
| Para qué | Practicar sin miedo: intentos ilimitados, pistas, XP | La nota y la telemetría |
| Dónde corre | En el kernel del alumno | En el kernel del alumno y otra vez al calificar |
| Se puede manipular | Sí, y no importa | La calificación real la rehace el instructor |
| Si desaparece | El cuadernillo pierde gracia | El cuadernillo deja de ser calificable |

Regla: **nada que cuente para la nota depende del motor.**

## Autorar una semana nueva

1. `mkdir notebook/cuadernillos/semana_03` y copia un `generador.py` existente.
2. Define `construir(motor_comprimido=True)` y devuelve el `Cuadernillo`.
3. Los diagramas nuevos, a `diagramas/mmd/` y `render.py`.
4. `build.py semana_03` y revisa que la validación pase.
5. Añade la carpeta a `notebook_semana/` (la crea `build.py`) y reconstruye las
   **dos** imágenes, en este orden:

   ```
   docker build -t mi_imagen_jupyterlab:latest ./notebook
   docker build -t mi_imagen_jupyterlab_docente:latest -f ./notebook/Dockerfile.docente ./notebook
   ```

   Son dos porque las plantillas llevan las soluciones dentro y solo pueden
   viajar en la del docente: el kernel del alumno corre como el mismo usuario
   que las posee, así que si estuvieran en su imagen podría leerlas con un
   `open()` desde una celda. La del docente se construye encima de la del
   alumno, de ahí el orden.

### Al escribir contenido

- Pocos emojis. El peso visual lo llevan los diagramas y las tarjetas del motor.
- Todo ejemplo, en contexto colombiano o de la UIS, sin caricatura.
- Cada ejercicio calificable, con sus tres pistas escalonadas: de la que hace
  pensar a la que casi resuelve.
- Las pruebas visibles enseñan qué se exige; las ocultas evitan que se programe
  contra la prueba.
