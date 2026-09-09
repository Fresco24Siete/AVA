# Auditoría del AVA 41333 — ciclo de vida del cuadernillo

Hecha el 2026-08-21 por siete auditores en paralelo, cada hallazgo refutado después por
un verificador independiente. 66 hallazgos en bruto -> 52 confirmados, 14 descartados.
Los 52 son ~30 defectos distintos: el informe los agrupa por causa raíz.

## Comprobado a mano contra el despliegue, no solo leído

Estos cinco los verifiqué yo mismo en la VM antes de darlos por buenos:

| Hallazgo | Cómo se comprobó | Resultado |
|---|---|---|
| El enlace del panel no abre nada | `curl` al mismo archivo por las dos rutas dentro del contenedor del alumno | `/user/<x>/inicio.ipynb` -> **404**; `/user/<x>/notebooks/inicio.ipynb` -> **200**. El panel emite la primera forma. |
| El alumno no puede entregar | `Exchange.root` dentro del contenedor vivo del alumno | Apunta a `/home/jovyan/work/nbgrader/exchange`, que **no existe** (el entrypoint borra el symlink) y `/srv/nbgrader` es una carpeta local vacía, no el volumen compartido. |
| Nadie ha entregado nunca | gradebook y exchange en la VM | `inbound`: 0 · `submitted/`: 0 · estudiantes en gradebook: `[]` · `submitted_assignment`: 0 · `cuadernillo_notas`: 0 |
| Las soluciones viajan en la imagen del alumno | leer `/opt/plantillas/*/cuadernillo.ipynb` desde dentro de su contenedor | semana_01: **7 celdas de solución + 7 de prueba**; semana_02: **8 + 8** |
| El `student_id` no casa entre telemetría y notas | código | Telemetría: `user_id` de LTI (`jupyterhub_config.py:138`, en la base `'3135'`). Notas: `registrar_notas.py:103` manda el id de nbgrader, que es el **correo**. El panel consulta por el del token. |

Matiz sobre el primero de la sección 1.1 del informe: `assignment_list` **sí está habilitada**
en la imagen del alumno (solo el instructor la desactiva). Lo que rompe la entrega no es la
extensión, es que el buzón que ve el alumno no es el compartido.

---

# Informe del revisor final — Auditoría del AVA 41333

---

## 1. QUÉ FALTA

Comprobado abriendo los archivos y consultando la VM en solo lectura. Tres cosas: un área entera sin auditar, dos interacciones entre áreas que nadie recorrió, y cuatro afirmaciones que se dieron por buenas.

### 1.1 [CRÍTICO — área no auditada] Ningún alumno puede entregar. La mitad evaluativa del AVA no está cableada.

Los 52 hallazgos auditan cómo llega el cuadernillo al alumno. **Nadie auditó cómo vuelve.** No vuelve.

- `notebook/entrypoint.sh:48-50` desactiva `assignment_list` en la rama del **instructor**, y la rama del alumno (`:78-115`) no lo activa nunca.
- El alumno no monta `/srv/nbgrader` (`hub_config/jupyterhub_config.py:95-97`) y `entrypoint.sh:83` borra el symlink, así que `c.Exchange.root = '/home/jovyan/work/nbgrader/exchange'` (`notebook/nbgrader_config.py:16`) **no existe** en su contenedor.
- Sin terminal (`notebook/jupyter_server_config.py:34`).

No hay ninguna ruta —ni de interfaz, ni de comando, ni de disco— por la que `work/semana_01.ipynb` llegue a `submitted/`.

Verificado en producción:

```
exchange/28053/inbound            → vacío
gradebook.db: student             → []
gradebook.db: submitted_assignment→ 0
postgres: select count(*) from cuadernillo_notas → 0
```

Escenario de fallo: el docente sigue la ayuda que el propio AVA le inyecta (`formgrader_ayuda.js:53-56`, «Collect: trae los cuadernillos que los alumnos entregaron»), pulsa **Collect** → no trae nada; **Autograde** → no califica nada; ejecuta `registrar-notas semana_01` → `[AVISO] 'semana_01' no tiene entregas calificadas` (`registrar_notas.py:89-92`). `cuadernillo_notas` se queda vacía y la columna «Nota» del panel dice **«aún sin calificar» para siempre** (`panel_bridge.py:92-95`). No hay error en ningún log: el sistema se comporta como si los alumnos simplemente no hubieran entregado.

Corolario que degrada tres hallazgos ya escritos: `_envios()` (`borrar_cuadernillo.py:50-65`) **solo puede devolver 0**, porque `submitted/` nunca existe. El bloqueo de borrado por entregas es decorativo, `--forzar` nunca hace falta, y el hallazgo 14 (el conteo ×3) es hoy inalcanzable.

### 1.2 [ALTO — interacción no auditada] Aunque se arregle 1.1, la nota no llegaría al alumno: nbgrader y LTI usan identificadores distintos.

- El token de métricas se acuña con `estudiante_id = auth_state['user_id']`, el id numérico de LTI (`jupyterhub_config.py:138`, `:156-157`). Verificado: `exercise_attempts.student_id = '3135'`.
- `registrar_notas.py:103` envía `student_id = envio.student_id`, que nbgrader toma de `get_username()` → `JUPYTERHUB_USER` → **el correo** (`nbgrader/utils.py`, leído en la imagen que corre hoy; `username_key = lis_person_contact_email_primary`, `jupyterhub_config.py:128`).
- `progresoRepository.go:43-67` busca las notas con `student_id = $1`, que viene del claim del token.

Resultado: la nota se escribe bajo `ritokun60@gmail.com` y se consulta bajo `3135`. Nunca casan. Peor, por el `UNION` de `suyos` (`:44-50`) la nota **ni siquiera crea una fila**: el cuadernillo desaparece del panel si el alumno no tuvo telemetría. El docente ve `[OK] 25 nota(s)`; los 25 alumnos ven «aún sin calificar». Silencioso en los dos extremos.

### 1.3 [MEDIO — interacción no auditada] Borrar un cuadernillo no llega ni al alumno ni a la analítica.

`borrar_cuadernillo.py:59-84` reescribe el manifest y `_carpetas` (`:43-47`) borra `/srv/publicados/<curso>/<tarea>`. Pero:
- el `work/<tarea>.ipynb` del alumno vive en `ava-trabajo-<usuario>` y **nadie lo toca**, y `panel_bridge.py:68-75` lista el disco → el cuadernillo «eliminado» sigue en su página de inicio con enlace;
- `ejercicio_competencias`, `exercise_attempts` y `cuadernillo_notas` de ese id quedan huérfanos, y el panel los sigue cruzando;
- si el borrado era el activo, `CUADERNILLO_CODIGO` pasa a otro id (o a `""`) en el siguiente arranque, y todo lo que el alumno haga en el cuadernillo borrado se etiqueta con el nuevo.

### 1.4 Afirmaciones que se dieron por buenas — comprobadas

| Afirmación | Veredicto |
|---|---|
| «api_go queda expuesto y `/api/exercise/tutorIA` sin token es alcanzable desde internet» (implícito en el h. 50) | **Falso hoy.** `docker-compose.yml:69-70` publica `8080:8080` en `0.0.0.0`, pero el firewall de GCP solo abre 80/443 (verificado: `jupyterhub-web tcp:80,tcp:443`). Es alcanzable desde cualquier contenedor de `moodle_jupyter_net` y desde la VM, no desde fuera. El hallazgo 50 sigue en pie, con ese alcance. |
| «El esquema v2 nunca se crea» (h. 42) | **Cierto.** `docker-compose.yml:108` monta solo `schema.sql`; la base viva tiene las tablas v2 → alguien migró a mano. |
| «custom.js no sabe en qué notebook está» (h. 1, 31) | **Falso, y eso abarata el arreglo.** `custom.js:155-157` (`clave_estado()`) ya usa `Jupyter.notebook.notebook_path` para separar el estado por cuadernillo. El dato está a mano; solo no se mete en el payload. |
| «El manifest de producción tiene fechas» | **Falso.** `abre` y `cierra` son `null` en las dos entradas → los hallazgos de ventana (21, 9) no están activos hoy, pero se activan en cuanto el docente ponga una fecha. |
| Capacidad | La VM es **e2-small, 2 GB, 2 vCPU** (verificado; 504 MB libres con un solo contenedor de docente arriba). Con `MEM_LIMIT_ALUMNO=768M` y ~250 MB reales por alumno, 25 alumnos simultáneos no caben. `PENDIENTES_AVA.md §1.2` lo documenta; ningún hallazgo lo prioriza, y para un curso que empieza es bloqueante. |

### 1.5 La interacción que nadie recorrió entera

`publicar` → `activo` → `entrega` → `telemetría` → `competencia` → `panel` → `nota`. Seis eslabones, **cuatro fuentes de verdad distintas**:

1. `publicar-cuadernillo` decide «activo» por orden de ejecución (`publicar_cuadernillo.py:102`);
2. `entregar-cuadernillo` lo congela en una variable de entorno al arrancar (`entrypoint.sh:100-110`);
3. `metrics_bridge` la estampa sobre **todo** evento, pisando lo que mande el navegador (`metrics_bridge.py:83`);
4. la competencia se resuelve por `(cuadernillo_id, exercise_id)` — y `exercise_id` es `ejercicio_N`, que **se repite entre semanas** (`ejercicio_competencias` no tiene `course_id` y su PK es `(cuadernillo_id, exercise_id, competencia_id)`);
5. la nota se indexa por **otro** `student_id` (§1.2);
6. y el panel decide qué filas existen **leyendo el disco** (`panel_bridge.py:68-75`).

Los hallazgos 1, 8, 9, 27, 31, 39, 43 no son siete fallos: son siete síntomas de esta cadena.

---

## 2. LA PREGUNTA DE BRYAN

**El atributo es uno solo: la clave de texto `cuadernillo_id` en la raíz de `/srv/publicados/<CURSO_ID>/manifest.json`.** Su valor es el nombre de la carpeta de la tarea en nbgrader (`semana_01`).

| Acción | Dónde | Qué hace |
|---|---|---|
| **Se activa al publicar** | `notebook/publicar_cuadernillo.py:101-107` | Escribe `"cuadernillo_id": assignment` **incondicionalmente**, en cada ejecución, y añade/reemplaza la entrada en `cuadernillos[]` (`:96-99`), ordenada alfabéticamente por id. |
| **Se desactiva al eliminar** | `notebook/borrar_cuadernillo.py:68` y `:72-77` | Saca la entrada de `cuadernillos[]`; si era la activa, pasa el testigo a `publicados[-1]["id"]`, y si la lista queda vacía escribe la cadena vacía `""`. |
| **Se lee** | `entregar_cuadernillo.py:170` → devuelto en `:240` → `entrypoint.sh:100-110` → `CUADERNILLO_CODIGO` / `CUADERNILLO_ID` | De ahí lo leen, **una sola vez al importar el módulo**: `panel_bridge.py:37` (marca «Esta semana»), `tutor_bridge.py:49-51` (cupo de 5 preguntas, con fallback literal `'sin_cuadernillo'`) y `metrics_bridge.py:35`, que lo estampa sobre cada evento en `:83`. |

**Generar (`Generate` de formgrader) no toca este atributo en absoluto.** Generate solo escribe `release/<tarea>/`. El cuadernillo no existe para el alumno hasta que se ejecuta `publicar-cuadernillo`.

### ¿Hay realmente un fallo ahí? Sí. Bryan tiene razón, y el fallo es mayor de lo que sugiere la pregunta.

No hay *un* fallo: hay **tres, y todos vienen de que ese campo hace dos trabajos incompatibles a la vez** — identificar qué contenido está publicado, y etiquetar la sesión de trabajo del alumno.

1. **«Activo» significa «lo último que se ejecutó», no «lo vigente».** `publicar_cuadernillo.py:102` pisa la raíz sin mirar fechas ni cuál era el activo. El flujo que el propio sistema recomienda para corregir una errata (`sembrar-cuadernillo` → Generate → `publicar-cuadernillo semana_01`) **degrada semana_02 a no-activa** sin que el docente lo pida, y republicar sin argumentos de fecha borra además la ventana que tuviera esa tarea (`:96-97`).

2. **Es un valor global de sesión, no del notebook.** `metrics_bridge.py:83` sobrescribe siempre el evento con `IDENTIDAD`. Como el panel lista y enlaza **todos** los `.ipynb` del disco (`panel_bridge.py:68-75`) y los `exercise_id` se repiten entre semanas, el trabajo en un cuadernillo anterior se guarda a nombre de la semana activa: el JOIN con `ejercicio_competencias` devuelve la competencia equivocada, la fila del cuadernillo activo se infla, y un rating tardío **pisa** el anterior (`cuadernilloRatingRepository.go:24-27`, `ON CONFLICT ... DO UPDATE`). Con el manifest actual (`semana_01` y `semana_02`, ambas sin `cierra`) esto ya está ocurriendo. **Y el navegador sí sabe en qué notebook está**: `custom.js:156` usa `Jupyter.notebook.notebook_path`; simplemente no lo manda.

3. **«Desactivado» se codifica de tres formas distintas y nadie valida el valor.** `""` en el manifest (`borrar_cuadernillo.py:77`), variable inexistente en el entorno (`entrypoint.sh:112-115`), y `'sin_cuadernillo'` en el tutor. Y `entregar_cuadernillo.py:240` devuelve `activo` **sin comprobar** que ese cuadernillo esté dentro de ventana ni que se le haya entregado al alumno.

**El matiz que hay que devolverle a Bryan:** el problema no está en «generar» ni en «eliminar» por separado —Generate no interviene, y el borrado hace lo que dice—, sino en que **publicar y eliminar escriben el mismo campo que además etiqueta la telemetría y el cupo del tutor.** Un campo, tres responsabilidades.

**Arreglo mínimo, en orden:**
1. `custom.js` incluye el cuadernillo del notebook en el payload (`Jupyter.notebook.notebook_path` o `notebook.metadata.ava.cuadernillo`, que `constructor.py:285` ya escribe) y `metrics_bridge` solo impone `student_id`/`course_id`; la env queda como último recurso.
2. `publicar-cuadernillo` separa *publicar contenido* de *marcar activo* (`--activar` / `--solo-contenido`) y avisa cuando degrada al activo anterior.
3. `entregar_cuadernillo.py:240` devuelve `activo` solo si está entre los entregados.
4. Un único valor para «sin activo».

---

## 3. ORDEN DE ARREGLO

Para 25 estudiantes y un curso que empieza. Agrupado por causa raíz; los números son los hallazgos del informe. **52 hallazgos son ~30 defectos distintos** — los duplicados están fusionados.

### Bloque 0 — Antes de abrir el curso. Sin esto no hay curso.

| # | Qué | Causa raíz |
|---|---|---|
| **0.1** | **45** — Secreto LTI de desarrollo, público en GitHub. Rotar el par, ponerlo a la vez en `.env` de la VM y en Moodle, y solo entonces hacer que `jupyterhub_config.py:120-127` aborte en vez de avisar. Da admin del Hub + `nbgrader_shared` rw a cualquiera. | — |
| **0.2** | **Capacidad** (`PENDIENTES §1.2`, verificado: e2-small 2 GB). 25 alumnos no caben. Migrar a `e2-standard-2` como mínimo, `e2-standard-4` desde la semana 9. | — |
| **0.3** | **42** — El esquema v2 no se crea nunca (`docker-compose.yml:108`). Un `down -v` o una máquina nueva deja el AVA sin telemetría y sin notas, con 500 permanentes. Montar `migracion_v2.sql` con prefijo numérico. | — |

### Bloque 1 — Expone soluciones / rompe la integridad de la evaluación

| # | Qué |
|---|---|
| **1.1** | **46** — `/opt/plantillas` viaja en la imagen del alumno con soluciones y pruebas ocultas sin limpiar (`Dockerfile:109`). Una celda con `open('/opt/plantillas/semana_01/cuadernillo.ipynb')` da las 7 soluciones y las 2 pruebas ocultas de la semana 1 y las 8 de la 2. **Separar imágenes** (no basta `rm -rf`: queda en la capa). |
| **1.2** | **50** — Misma causa: la contención del alumno (`terminals_enabled=False`, `root_dir`) protege el explorador, no el kernel. Corregir el comentario de `jupyter_server_config.py:26-30` y, sobre todo, **exigir token y cuota en `/api/exercise/tutorIA`** (`route.go:84`, hoy fuera del grupo con `RequireMetricsToken`) — tutor de Gemini ilimitado desde una celda. |
| **1.3** | **52** — `find_user(auth_model['name'])` sin normalizar (`jupyterhub_config.py:91`): un correo con mayúsculas desactiva permanentemente el descarte de contenedor al cambiar de rol → un ex-docente conserva `source/` y `exchange/` en rw. Un `self.normalize_username()`. |

### Bloque 2 — Handlers sin autenticación. Una causa, tres archivos, un arreglo.

Causa raíz: heredan de `tornado.web.RequestHandler` en vez de `JupyterHandler`, sin `@web.authenticated`. `jupyter_server` no tiene middleware global; la autenticación la pone cada handler. El proxy del Hub solo enruta.

| # | Qué |
|---|---|
| **2.1** | **36 / 47** — `panel_bridge.py:167`. `GET /user/<correo>/panel` devuelve 200 sin credenciales: nombre, cuadernillos, progreso, abandonos, competencias y la nota de nbgrader cuando exista. El username es el correo institucional. **Fuga de datos académicos de terceros.** |
| **2.2** | **11** — `admin_bridge.py:28`. `POST /ava-admin/borrar` sin sesión ni XSRF borra `source/`, `release/`, el buzón, lo publicado y la ficha del gradebook. Además `json.loads` sin mirar `Content-Type` → CSRF sin preflight. |
| **2.3** | **30 / 48** — `metrics_bridge.py:61`. Inyección anónima de telemetría a nombre del dueño del contenedor, e inserción ilimitada en el Postgres de una VM de 2 GB. |

Un solo cambio los cierra: heredar de `jupyter_server.base.handlers.JupyterHandler`, decorar con `@web.authenticated`, quitar el override de `check_xsrf_cookie` y mandar el token XSRF real desde `custom.js` / `formgrader_ayuda.js` (el patrón correcto ya existe en `tutor_bridge.py:205`).

### Bloque 3 — El alumno se queda sin cuadernillo (no pierde trabajo, pero no puede trabajar)

| # | Qué | Causa raíz |
|---|---|---|
| **3.1** | **5 ≡ 17 ≡ 24 ≡ 25 ≡ 26 ≡ 44 — son el mismo bug.** El aviso «Aún no hay cuadernillo» se escribe en `DESTINO` (`entregar_cuadernillo.py:159-168`), la migración lo asciende a `<activo>.ipynb` (`:184-190`) sin mirar qué contiene, `:205` ya no copia el real, y como la migración no deja entrada en `.ava_versiones.json` el default de `:213` bloquea también toda corrección futura. **Irrecuperable sin SSH.** Alcanza a toda la cohorte que entre antes de la primera publicación — exactamente lo que va a pasar el primer día con 25 alumnos. Arreglo único: no escribir el aviso en `DESTINO` (nombre propio o `metadata.ava_placeholder`) y no migrarlo. | Reutilizar un nombre fijo para dos cosas |
| **3.2** | **37** — `panel_bridge.py:103` emite `<a href="semana_01.ipynb">`, que resuelve a `/user/<x>/semana_01.ipynb` → 404 del catch-all de `jupyter_server`. El panel es la página de aterrizaje y no tiene otra navegación: **hoy ningún alumno puede abrir ningún cuadernillo desde ella**, y va dentro de un iframe de Moodle. `url_path_join(base_url, 'notebooks', quote(archivo))`. | — |
| **3.3** | **4 ≡ 18** — Una fecha sin zona horaria (`2026-08-25`, o ISO sin `Z`) en `publicar-cuadernillo` produce un `TypeError` que aborta la entrega entera, con `exit 0` y `[OK]` en la terminal del docente (`publicar_cuadernillo.py:47-48` no valida; `entregar_cuadernillo.py:51-57` solo captura `ValueError`). Validar al publicar, normalizar a aware en `_parse`, mover el `try` dentro del bucle y quitar el `2>/dev/null` de `entrypoint.sh:100`. Rama B: una fecha imposible anula el cierre en silencio. | — |
| **3.4** | **3 ≡ 51** — La entrega se resuelve una sola vez, en el arranque (`entrypoint.sh:100`). Publicar o corregir con sesiones abiertas no llega hasta el siguiente spawn (1 h de culler o «Stop My Server»). Releer el manifest en cada `GET /panel`. | El activo es una env congelada |

### Bloque 4 — Evaluación: la nota no existe, y no llegaría aunque existiera

| # | Qué |
|---|---|
| **4.1** | **NUEVO (§1.1)** — Decidir e implementar el mecanismo de entrega del alumno **antes de que empiece el curso**: habilitar `assignment_list` en la rama de estudiante y montarle el exchange en modo apropiado, o un comando/botón propio que copie `work/<id>.ipynb` a `submitted/<student_id>/<id>/`. Sin esto, Collect, Autograde, `registrar-notas`, la columna «Nota» y la devolución a Moodle son código muerto. |
| **4.2** | **NUEVO (§1.2)** — Unificar el `student_id`: o fijar `CourseDirectory.student_id` / `Exchange.student_id` al `user_id` numérico de LTI, o guardar el mapeo correo↔user_id (la tabla que ya hace falta para `§2.1` de PENDIENTES) y traducir en `registrar_notas.py:103`. |
| **4.3** | **PENDIENTES §2.1** — Devolución a Moodle. Depende de 4.1 y 4.2, y de la decisión de curso: **una actividad LTI por cuadernillo**, o las notas se pisan entre semanas. |

### Bloque 5 — Rompe el flujo del docente

| # | Qué | Causa raíz |
|---|---|---|
| **5.1** | **7 ≡ 12 ≡ 20 ≡ 22 — el mismo bug.** «Eliminar actividad» no es permanente para nada que venga de la imagen: `entrypoint.sh:61-69` resiembra `/opt/plantillas/*`, y `:27` + `:73-76` reponen `semana_1` (la demo, que además el panel titula «Semana 1», igual que `semana_01`). En producción ya se borró dos veces y volvió. Marca persistente (`respaldos_borrados/.no_sembrar`) que el bucle respete, quitar el `mkdir` incondicional de `:27` y el bloque de la demo. | La siembra corre en cada arranque, sin memoria del borrado |
| **5.2** | **2** — Republicar `semana_01` para corregir una errata degrada `semana_02` a no-activa, borra su ventana y desvía la telemetría y el cupo del tutor. `--activar` / `--solo-contenido` + aviso. | Un campo, dos trabajos (§2) |
| **5.3** | **23** — Los cuadernillos declaran `nbformat_minor 5` sin `cell.id` (`constructor.py:288-289`), así que cada `Generate` produce bytes distintos y una `version` nueva → **cada republicación entrega un `_v2` en blanco a los 25 alumnos**, y luego `_v3`, `_v4`. Emitir ids de celda deterministas (o hashear el contenido normalizado). | Huella de bytes, no de contenido |
| **5.4** | **15** — La validación del nombre solo existe en `admin_bridge.py:75`, no en `borrar()` ni en `main()`. `borrar-cuadernillo semana_01/` (autocompletado del shell) borra las carpetas, deja el respaldo en una ruta inservible, no quita la ficha del gradebook ni la entrada del manifest, y reporta `[OK]`. Mover la comprobación al inicio de `borrar()`. | — |
| **5.5** | **13** — Tras borrar, la tabla de formgrader queda viva; el lápiz de metadatos **resucita** la actividad (`os.makedirs(sourcedir)`). `location.reload()` tras `d.ok`. | — |
| **5.6** | **16** — El respaldo no incluye `manifest.json`: se pierden `abre`/`cierra` y el docstring promete que recuperar es «mover una carpeta». | — |
| **5.7** | **8** — Al borrar el activo, el testigo pasa al último **alfabético**, no al más reciente. Alcanzable con `semana_1` y `semana_01` conviviendo. | Orden alfabético como proxy de cronología |

### Bloque 6 — La analítica miente (no pierde trabajo, pero las conclusiones son falsas)

| # | Qué | Causa raíz |
|---|---|---|
| **6.1** | **1 ≡ 31 ≡ 9** — La telemetría se etiqueta con el cuadernillo activo de la sesión, no con el notebook. Competencia equivocada, fila inflada, rating sobrescrito. **El arreglo es una línea en `custom.js`**, que ya tiene `notebook_path` (`:156`). | §2 |
| **6.2** | **39** — `COUNT(DISTINCT a.exercise_id)` sin el cuadernillo (`progresoRepository.go:75,77`): los `ejercicio_N` de semanas distintas se fusionan; `errores` (`:78`) no se colapsa → barra verde al 100 % con 15 errores debajo. `COUNT(DISTINCT (a.cuadernillo_id, a.exercise_id))`. | `exercise_id` tratado como clave global |
| **6.3** | **33 ≡ 40** — `beforeunload` convierte F5 y cambiar de notebook en «abandono» (`custom.js:449-470`), y `progresoRepository.go:56` cuenta **eventos** sin descartar los que después pasaron → «Dejaste N ejercicio(s) a medias» no se apaga nunca. Etiqueta propia para el volcado + `COUNT(DISTINCT ...) FILTER` con `NOT EXISTS ('passed')`. | — |
| **6.4** | **34** — El `NotImplementedError` del stub de nbgrader se bufferiza como error del alumno y produce un intento `failed` por ejercicio recorrido con Shift+Enter — que es literalmente lo que el material pide. Hoy es el 100 % de las 12 filas de producción. | — |
| **6.5** | **32** — El buffer de errores se vacía y se persiste **antes** de enviar (`custom.js:427-433`), y `enviar_evento` no mira `resp.ok` ni reintenta: cualquier 502 pierde el intento y sus errores para siempre. Enviar primero, limpiar después de un 2xx, cola en `localStorage`. | — |
| **6.6** | **35** — `verificar_finalizacion_cuadernillo` evalúa sin el flag `recien_ejecutada` (`custom.js:262`) y solo se invoca justo tras ejecutar una celda de prueba, cuando esa celda aún tiene `In [*]`: **la tarjeta de estrellas no puede aparecer nunca** y `cuadernillo_ratings` quedará siempre vacía. | — |
| **6.7** | **38** — El denominador de la barra es `ejercicios_intentados` (`panel_bridge.py:96`, `:113`): resolver 1 de 7 pinta 100 % y «1 de 1 ejercicios», y el semáforo de competencias sale verde. Devolver el total real desde `ejercicio_competencias`. | — |
| **6.8** | **6 ≡ 19 ≡ 28 ≡ 43 ≡ 27** — La versión `""` en `.ava_versiones.json` se lee como «versión distinta» (`entregar_cuadernillo.py:213`) → `_v2` espurios; y el panel deriva el id del nombre de archivo (`panel_bridge.py:75`) → la marca «Esta semana» se queda en la versión vieja y la corregida aparece anónima y eternamente «sin empezar». Afecta ya a un volumen real (`ritokun60`). Arreglo doble: `registro.get(archivo) or version`, y que `_cuadernillos_en_disco` agrupe por código base quitando `_vN`. | Versión vacía ≠ desconocida; id derivado del nombre de fichero |
| **6.9** | **29** — Renombrar el `.ipynb` hace que el siguiente arranque entregue una copia en blanco con el nombre canónico. | Detección por nombre de fichero |

### Bloque 7 — Resto

| # | Qué |
|---|---|
| **7.1** | **10 ≡ 49** — El cupo de 5 preguntas del tutor vive en `/home/jovyan/.tutor_ia`, fuera del único volumen, y con `remove = True` muere en cada apagado → 5 preguntas de Gemini nuevas por arranque, sin tope acumulado. El arreglo real, que el propio docstring señala, es contar en el backend por `(student_id, cuadernillo_id)`; eso exige añadir `student_id` a `models.ApiMessage`. Es el mismo cambio que 1.2. |
| **7.2** | **21** — Cerrar la fecha ya ni siquiera oculta el cuadernillo, porque el panel lee el disco y no el manifest. Y `formgrader_ayuda.js:49-50` le recomienda al docente ese mecanismo como forma de «retirarlo de verdad». Corregir el texto y decidir si «cerrar» debe impedir trabajar. |
| **7.3** | **41** — `PanelHandler.get` es síncrono y hace `urlopen` bloqueante en el IOLoop (`panel_bridge.py:168`): hasta 4 s congelando el kernel y el autoguardado del alumno cuando el backend tarda. `async def` + `AsyncHTTPClient`. |
| **7.4** | **14** — El conteo de entregas suma pares (etapa, alumno) en vez de estudiantes distintos. **Inalcanzable hoy** (§1.1); arreglar cuando se arregle 4.1. |

---

### Resumen ejecutivo en una frase

Lo que hay que arreglar antes de abrir el curso son **cinco cosas**: rotar el secreto LTI, agrandar la VM, sacar `/opt/plantillas` de la imagen del alumno, autenticar los tres handlers crudos, y arreglar el notebook-placeholder que va a envenenar el cuadernillo de todo alumno que entre antes de la primera publicación (3.1). Lo que hay que **decidir** antes de abrir el curso, porque no es un arreglo sino un diseño que falta entero, es **cómo entregan los alumnos** (4.1) y **con qué identificador** (4.2): hoy la mitad evaluativa del AVA no está conectada, y ninguna de las 52 líneas de la auditoría lo había visto.