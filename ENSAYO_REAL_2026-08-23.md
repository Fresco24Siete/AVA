# Ensayo real del AVA — 23 de agosto de 2026

Acta de la revisión completa del sistema en el ambiente real (VM `jupyterhub-lti`,
Moodle `lms.uis.edu.co`, curso 28053 «ALGORITMOS Y PROGRAMACION 2026-1-41333-B01»,
actividad LTI `test_jupyter`), con la VM reiniciada de cero y dos cuentas reales:

- **Instructor**: Bryan (`ritokun60`, LTI id 3651), sesión en el navegador de la app.
- **Estudiante**: Diego (`diegolopezcamacho`, LTI id 3135), sesión en Chrome, con la
  vista de Moodle cambiada a «Estudiante».

Código bajo prueba: rama `feat/menu-cuadernillos-y-notas`, commit `c6f08e5`.

La Parte 1 es el inventario de todo lo que se puede pulsar o ejecutar; la Parte 2 es
el registro de cada acción ejecutada, con el resultado observado y la evidencia en la
base de datos, el exchange o los logs.

## Parte 1 · Inventario de botones, enlaces y acciones

Repositorio: `/Users/diegolopez/Documents/Dev/AVA`
Imagen inspeccionada: `mi_imagen_jupyterlab_docente:latest` → nbgrader **0.8.5** en `/usr/local/lib/python3.11/site-packages/nbgrader/server_extensions/formgrader`

> **Nota de trazabilidad:** la imagen local ya lleva el parche de AVA aplicado (`base.tpl:25` carga `ava_ayuda.js`, que es una copia de `notebook/formgrader_ayuda.js`). Las evidencias de nbgrader se citan con su ruta dentro del contenedor; las de AVA, con su ruta en el repo.

---

### 0. Puerta de entrada: JupyterHub

| Botón/acción | Quién lo ve | Qué hace (endpoint o comando) | Archivo:línea |
|---|---|---|---|
| Entrada LTI desde Moodle (POST) | docente y alumno | `LTIRoleAuthenticator`; decide rol por el claim de roles (`instructor`/`teachingassistant`/`admin` → docente) | `hub_config/jupyterhub_config.py:70-71`, `:133` |
| Página de aterrizaje del Hub | ambos | `c.JupyterHub.default_url = '/hub/spawn'` (arranca el contenedor y redirige) | `hub_config/jupyterhub_config.py:437` |
| Aterrizaje del **docente** tras arrancar | docente | `spawner.default_url = '/formgrader'` | `hub_config/jupyterhub_config.py:411-412` |
| Aterrizaje del **alumno** tras arrancar | alumno | `spawner.default_url = '/panel'` | `hub_config/jupyterhub_config.py:424` |
| Imagen del contenedor según rol | — (automático) | `IMAGEN_DOCENTE` vs `IMAGEN_ALUMNO` | `hub_config/jupyterhub_config.py:314` |
| Marca de admin del Hub (habilita el panel de admin de JupyterHub y formgrader) | docente | `auth_model['admin'] = es_instructor` | `hub_config/jupyterhub_config.py:126` |
| **Cambio de rol entre sesiones** | ambos | Si el rol de LTI difiere del guardado, se actualiza `usuario.admin` en la BD del Hub | `hub_config/jupyterhub_config.py:89-99` |
| Grupo asignado | ambos | `formgrade-<curso>` (docente) / `nbgrader-<curso>` (alumno) | `hub_config/jupyterhub_config.py:128` |
| **Control Panel / Logout / Stop My Server / Start My Server** | ambos | Barra estándar de JupyterHub (`/hub/home`, `/hub/logout`). **No hay override**: `admin_access`, `shutdown_on_logout`, `template_paths` y `logo_file` no están configurados | `hub_config/jupyterhub_config.py` (ausencia comprobada por grep) |
| **Idle culler** (apagado automático) | — (servicio) | `jupyterhub_idle_culler --timeout=3600 --cull-every=300` (`CULL_TIMEOUT`/`CULL_EVERY`); rol `list-and-cull` con scopes `list:users, read:users:activity, read:servers, delete:servers`. No borra datos, solo apaga el servidor | `hub_config/jupyterhub_config.py:501-523` |
| Servicio externo `nbexchange` | — | Registrado con rol `read:users, admin:auth_state`; proxy en `/services/nbexchange/` | `hub_config/jupyterhub_config.py:536-545` |
| Tiempos de arranque | — | `start_timeout=300`, `http_timeout=180` | `hub_config/jupyterhub_config.py:433-434` |

---

### 1. Formgrader — barra lateral (presente en TODAS las páginas)

Solo la ve el **docente** (`formgrader` se habilita solo si `ALUMNO_ROL=instructor`, `notebook/entrypoint.sh:41-44`; se deshabilita para alumno en `:83-86`).

| Botón/acción | Quién lo ve | Qué hace (endpoint) | Archivo:línea |
|---|---|---|---|
| `Manage Assignments` (lateral) | docente | GET `/formgrader/manage_assignments` | `templates/base.tpl:80`; ruta en `handlers.py:288` |
| `Manual Grading` / `Gradebook` (lateral) | docente | GET `/formgrader/gradebook` | `templates/base.tpl:81`, `gradebook_base.tpl:9`; ruta `handlers.py:291` |
| `Manage Students` (lateral) | docente | GET `/formgrader/manage_students` | `templates/base.tpl:82`; ruta `handlers.py:295` |
| Logo Jupyter (decorativo, sin enlace) | docente | — | `templates/base.tpl:46-72` |
| Ordenar/filtrar columnas (DataTables) | docente | Cliente; columnas `no-sort` no ordenan | `static/js/utils.js:79-89` |
| **Bloque de ayuda AVA** (inyectado arriba de todo) | docente | Ver §7 | `templates/base.tpl:25` → `notebook/formgrader_ayuda.js` |

---

### 2. Formgrader — Manage Assignments (`/formgrader/manage_assignments`)

Cabeceras de tabla: Name, Due Date, Status, Edit, Generate, Preview, Release, Collect, # Submissions, Generate Feedback, Release Feedback (`manage_assignments.tpl:82-96`).

| Botón/acción | Quién lo ve | Qué hace (endpoint o comando) | Archivo:línea |
|---|---|---|---|
| `Instructions (click to expand)` | docente | Acordeón Bootstrap, 8 pasos explicativos | `manage_assignments.tpl:33-54` |
| Nombre de la actividad (enlace) | docente | Abre `source/<tarea>`: `/tree/<url_prefix>/<source_path>` o, en Lab, `postMessage('filebrowser:go-to-path')` | `manage_assignments.js:109-116`, `jupyterlab_utils.js:5-10` |
| Columna `Due Date` | docente | Solo lectura (`display_duedate`) | `manage_assignments.js:118-127` |
| Etiqueta `Status`: `draft` / `released` | docente | Solo lectura | `manage_assignments.js:128-136` |
| **Edit** — lápiz `glyphicon-pencil` | docente | Abre modal *Editing \<nombre\>* | `manage_assignments.js:139-144` |
| → Modal Edit: campo `Name` (deshabilitado) | docente | — | `manage_assignments.js:47-51` |
| → Modal Edit: `Due date (optional)` (datetime-local) | docente | — | `manage_assignments.js:53-56` |
| → Modal Edit: `Timezone as UTC offset (optional)` | docente | — | `manage_assignments.js:58-61` |
| → Modal Edit: botón **Save** | docente | PUT `/formgrader/api/assignment/<id>` → `update_or_create_assignment` + `os.makedirs(sourcedir)` | `manage_assignments.js:64-67,381-389`; `apihandlers.py:134-149` |
| → Modal Edit: botón **Cancel** / `×` | docente | Cierra modal | `manage_assignments.js:68-72`, `utils.js:16-22` |
| **Generate** — birrete `glyphicon-education` | docente | POST `/formgrader/api/assignment/<id>/assign` → `api.generate_assignment` | `manage_assignments.js:147-152,237-243`; `apihandlers.py:242-247` |
| → Modal de resultado *Success/Error* con `Log Output` y `Traceback` | docente | Solo lectura | `manage_assignments.js:245-271`; `utils.js:49-72` |
| **Preview** — lupa `glyphicon-search` | docente | Abre `release/<tarea>`: `/tree/<url_prefix>/<release_path>` o `postMessage`. **Solo aparece si existe `release_path`** | `manage_assignments.js:155-170` |
| **Release** — nube arriba `glyphicon-cloud-upload` | docente | POST `/formgrader/api/assignment/<id>/release` → `api.release_assignment` (contra nbexchange) | `manage_assignments.js:175-181,309-315`; `apihandlers.py:258-263` |
| **Unrelease** — aspa `glyphicon-remove` (misma celda cuando el estado es `released`) | docente | POST `/formgrader/api/assignment/<id>/unrelease` | `manage_assignments.js:182-189,273-279`; `apihandlers.py:250-255` |
| **Collect** — nube abajo `glyphicon-cloud-download` (solo si `status === "released"`) | docente | POST `/formgrader/api/assignment/<id>/collect` | `manage_assignments.js:193-202,345-351`; `apihandlers.py:266-271` |
| **# Submissions** (número enlazado; si es 0 es texto plano) | docente | GET `/formgrader/manage_submissions/<tarea>` | `manage_assignments.js:204-213`; ruta `handlers.py:289` |
| **Generate Feedback** — bocadillo `glyphicon-comment` (solo si hay envíos) | docente | POST `/formgrader/api/assignment/<id>/generate_feedback` | `manage_assignments.js:216-223,397-403`; `apihandlers.py:282-287` |
| **Release Feedback** — sobre `glyphicon-envelope` (solo si hay envíos) | docente | POST `/formgrader/api/assignment/<id>/release_feedback` | `manage_assignments.js:226-233,433-439`; `apihandlers.py:290-295` |
| **`+ Add new assignment...`** (pie de tabla) | docente | `createAssignmentModal()` | `manage_assignments.tpl:102-108`, `manage_assignments.js:499` |
| → Modal Add: `Name`, `Due date`, `Timezone` + **Save** / **Cancel** | docente | Save → PUT `/formgrader/api/assignment/<nombre>`. Valida que el nombre no lleve `+` | `manage_assignments.js:501-580` |
| Avisos condicionales: `Windows detected` / `exchange directory does not exist` / `course id has not been set` | docente | Bloquean Release y Collect | `manage_assignments.tpl:59-79` |

---

### 3. Formgrader — Manage Submissions (`/formgrader/manage_submissions/<tarea>`)

Cabeceras: Student Name, Student ID, Timestamp, Status, Score, Autograde, Generate Feedback, Release Feedback (`manage_submissions.tpl:57-68`).

| Botón/acción | Quién lo ve | Qué hace (endpoint o comando) | Archivo:línea |
|---|---|---|---|
| Migas: `Assignments` → `<tarea>` | docente | GET `/formgrader/manage_assignments` | `manage_submissions.tpl:21-26` |
| `Instructions (click to expand)` | docente | Acordeón; explica el autograde por entrega | `manage_submissions.tpl:29-54` |
| → Enlace **command line** dentro de Instructions | docente | Abre `/terminals/1` en pestaña nueva, con `cd "<course_dir>"; nbgrader autograde "<tarea>"` a la vista | `manage_submissions.tpl:44-49` |
| Nombre del estudiante (enlace, **solo si ya está autogradeado**) | docente | GET `/formgrader/manage_students/<sid>/<tarea>` | `manage_submissions.js:54-60` |
| Etiquetas `Status`: `needs autograding` / `needs manual grading` / `graded` | docente | Solo lectura | `manage_submissions.js:76-92` |
| `Score` (`x / y`, solo si autogradeado) | docente | Solo lectura | `manage_submissions.js:94-106` |
| **Autograde** — rayo `glyphicon-flash` (por entrega) | docente | POST `/formgrader/api/submission/<tarea>/<sid>/autograde`. **AVA envuelve este handler**: si `success`, dispara la subida de notas al backend en un hilo | `manage_submissions.js:109-114,133-141`; `apihandlers.py:274-279`; **envoltura AVA**: `notebook/admin_bridge.py:128-162` |
| **Generate Feedback** — bocadillo (por entrega) | docente | POST `/formgrader/api/assignment/<tarea>/<sid>/generate_feedback` | `manage_submissions.js:117-122,175-183`; `apihandlers.py:298-303` |
| **Release Feedback** — sobre (por entrega) | docente | POST `/formgrader/api/assignment/<tarea>/<sid>/release_feedback` | `manage_submissions.js:125-130,217-225`; `apihandlers.py:306-311` |
| Modales de resultado con log/traceback (los tres botones) | docente | Solo lectura | `manage_submissions.js:143-257` |

---

### 4. Formgrader — Manual Grading (3 niveles + página de corrección)

#### 4.1 `/formgrader/gradebook` — lista de actividades

| Botón/acción | Quién lo ve | Qué hace | Archivo:línea |
|---|---|---|---|
| Miga `Manual Grading` (activa) | docente | — | `gradebook_assignments.tpl:7-11` |
| Nombre de la actividad (enlace) | docente | GET `/formgrader/gradebook/<tarea>` | `gradebook_assignments.js:33-35` |
| Columnas Due Date / Submissions / Score | docente | Solo lectura (`GET /formgrader/api/assignments`) | `gradebook_assignments.js:2-5,37-60` |

#### 4.2 `/formgrader/gradebook/<tarea>` — notebooks

| Botón/acción | Quién lo ve | Qué hace | Archivo:línea |
|---|---|---|---|
| Migas: `Manual Grading` → `<tarea>` | docente | — | `gradebook_notebooks.tpl:11-16` |
| Nombre del notebook (enlace) | docente | GET `/formgrader/gradebook/<tarea>/<notebook>` | `gradebook_notebooks.js:37-39` |
| Avg. Score / Code / Written / Task | docente | Solo lectura (`GET /formgrader/api/notebooks/<tarea>`) | `gradebook_notebooks.js:2-5,41-79` |
| Marca ✓ `Needs Manual Grade?` | docente | Solo lectura | `gradebook_notebooks.js:81-90` |

#### 4.3 `/formgrader/gradebook/<tarea>/<notebook>` — entregas

| Botón/acción | Quién lo ve | Qué hace | Archivo:línea |
|---|---|---|---|
| Migas de 3 niveles | docente | — | `gradebook_notebook_submissions.tpl:12-18` |
| **`Show All Names` / `Hide All Names`** (botón único que alterna) | docente | Cliente: hace clic en todos los ojos de la tabla | `gradebook_notebook_submissions.tpl:22`; `gradebook_notebook_submissions.js:194-217` |
| **Ojo abierto** `glyphicon-eye-open` (por fila, tooltip "Show student name") | docente | Cliente: muestra el nombre real | `gradebook_notebook_submissions.js:52-55,37-41,185` |
| **Ojo cerrado** `glyphicon-eye-close` (por fila, tooltip "Hide student name") | docente | Cliente: vuelve a `Submission #N` | `gradebook_notebook_submissions.js:56-59,43-47,186` |
| `Submission #N` / nombre (enlace) | docente | GET `/formgrader/submissions/<submission_id>` | `gradebook_notebook_submissions.js:69-76` |
| Overall/Code/Written/Task Score | docente | Solo lectura (`GET /formgrader/api/submitted_notebooks/<tarea>/<notebook>`) | `gradebook_notebook_submissions.js:2-5,78-116` |
| Marcas ✓ `Needs Manual Grade?`, ✓ `Tests Failed?`, 🚩 `Flagged?` | docente | Solo lectura | `gradebook_notebook_submissions.js:118-149` |

#### 4.4 Página de corrección `/formgrader/submissions/<id>`

| Botón/acción | Quién lo ve | Qué hace (endpoint) | Archivo:línea |
|---|---|---|---|
| **`← Prev`** (tooltip "N remaining") | docente | GET `/formgrader/submissions/<id>/prev` → redirige a la anterior o a la lista si es la primera | `formgrade_macros.html.j2:52-56`; `handlers.py:107-113` (`_prev`) |
| **`Next →`** (tooltip "N remaining") | docente | GET `/formgrader/submissions/<id>/next` | `formgrade_macros.html.j2:96-100`; `handlers.py:98-105` (`_next`) |
| Migas: `Manual Grading` → `<tarea>` → `<notebook>` | docente | — | `formgrade_macros.html.j2:61-64` |
| **`Submission #N` / nombre** (tooltip "Open live notebook") | docente | Abre el `.ipynb` real: `/notebooks/<notebook_path>` o `postMessage('docmanager:open')` en Lab | `formgrade_macros.html.j2:65-87`, `:36-41` |
| **Ojo abierto/cerrado** en la barra (tooltip "Show/Hide student name") | docente | Cliente, `toggle_name()` | `formgrade_macros.html.j2:88-89`, `:24-34`, `:107-108` |
| Cabecera `Submission N / total` | docente | Solo lectura | `formgrade/index.html.j2:33` |
| **Campo de nota** (`input.score`, numérico, `/ puntos`) | docente | `change` → PUT `/formgrader/api/grade/<grade_id>`. Recorta a `[0, max_score]` con parpadeo rojo | `formgrade/index.html.j2:63`; `formgrade_models.js:4,40-72,90-103`; `apihandlers.py:54-71` |
| **Campo extra credit** (`+ __ (extra credit)`) | docente | `change` → mismo PUT con `extra_credit`. Recorta negativos | `formgrade/index.html.j2:66`; `formgrade_models.js:5,58-68` |
| **`Resolve`** (botón ámbar, solo visible si `needs_manual_grade` y ya hay nota manual) | docente | `save` → PUT `/formgrader/api/grade/<id>` (marca como resuelto) | `formgrade/index.html.j2:58`; `formgrade_models.js:8,29-37` |
| **`Full credit`** (botón verde) | docente | PUT con `manual_score = max_score` | `formgrade/index.html.j2:59`; `formgrade_models.js:6,105-109` |
| **`No credit`** (botón rojo) | docente | PUT con `manual_score = 0, extra_credit = 0` | `formgrade/index.html.j2:60`; `formgrade_models.js:7,111-115` |
| **Área de comentarios** (`textarea.comment`, placeholder "Type any comments here (supports Markdown and MathJax)") | docente | `change` → PUT `/formgrader/api/comment/<grade_id>` | `formgrade/index.html.j2:94`; `formgrade_models.js:130,141,152-154`; `apihandlers.py:85-97` |
| Iconos de guardado (✓ / ↻ que se desvanecen) | docente | Feedback visual de PUT en curso/terminado | `formgrade/index.html.j2:55,80`; `formgrade_models.js:74-88` |
| Etiquetas `Student's answer` / `Student's task` / `<grade_id>` | docente | Solo lectura | `formgrade/index.html.j2:74-87` |
| **`?` (interrogante flotante)** | docente | Abre modal *Keyboard shortcuts* | `formgrade/index.html.j2:45`; `formgrade_keyboardmanager.js:14,92-145` |
| Atajo `tab` / `shift-tab` | docente | Salta al siguiente/anterior campo de nota o comentario | `formgrade.js:30-39` |
| Atajo `escape` | docente | Desenfoca y **guarda** el campo actual | `formgrade.js:40-45` |
| Atajo `enter` | docente | Vuelve al último campo usado | `formgrade.js:46-50` |
| Atajo `control-.` / `control-,` | docente | Guarda y va a la siguiente/anterior entrega | `formgrade.js:51-55,61-65,130-156` |
| Atajo `control-shift-.` / `control-shift-,` | docente | Siguiente/anterior entrega **con pruebas fallidas** (`next_incorrect`/`prev_incorrect`) | `formgrade.js:56-60,66-70`; `handlers.py:116-131` |
| **Atajo `control-shift-f` — FLAG** (no hay botón, solo teclado) | docente | POST `/formgrader/api/submitted_notebook/<id>/flag` — **alterna** `flagged`. Mensaje flotante "Submission flagged"/"unflagged" | `formgrade.js:71-75,302-328`; `apihandlers.py:100-112` |
| Página 404 de entrega ("Submission notebook file not found") | docente | Se sirve si falta el `.ipynb` autogradeado | `formgrade_404.tpl:23`; `handlers.py:119-124` |

---

### 5. Formgrader — Manage Students

#### 5.1 `/formgrader/manage_students`

| Botón/acción | Quién lo ve | Qué hace | Archivo:línea |
|---|---|---|---|
| Miga `Students` | docente | — | `manage_students.tpl:7-11` |
| Nombre (enlace) | docente | GET `/formgrader/manage_students/<sid>` | `manage_students.js:102-104` |
| Columnas Student ID / Email / Overall Score | docente | Solo lectura (`GET /formgrader/api/students`) | `manage_students.js:5-8,106-125` |
| **Edit Student** — lápiz `glyphicon-pencil` | docente | Abre modal *Editing \<id\>* | `manage_students.js:128-133` |
| → Modal: `Student ID` (deshabilitado), `First name`, `Last name`, `Email` | docente | — | `manage_students.js:38-59` |
| → Modal: **Save** | docente | PUT `/formgrader/api/student/<sid>` | `manage_students.js:62-65,136-151`; `apihandlers.py:209-221` |
| → Modal: **Cancel** / `×` | docente | Cierra | `manage_students.js:66-70` |
| **`+ Add new student...`** (pie) | docente | `createStudentModal()`; Save → PUT `/formgrader/api/student/<id>` | `manage_students.tpl:27-33`; `manage_students.js:184-260` |
| **⚠️ No existe botón "remove/eliminar estudiante"** | — | nbgrader 0.8.5 no lo implementa: `manage_students.js` solo pinta `.edit`, y `apihandlers.py` no expone `DELETE` | `manage_students.js:173-182`; `apihandlers.py:314-348` |

#### 5.2 `/formgrader/manage_students/<sid>` — actividades del estudiante

| Botón/acción | Quién lo ve | Qué hace | Archivo:línea |
|---|---|---|---|
| Migas: `Students` → `<sid>` | docente | — | `manage_students_assignments.tpl:11-16` |
| Nombre de la actividad (enlace **solo si hay entrega autogradeada**; si no, texto `"… (no submission)"` o `"… (not autograded)"`) | docente | GET `/formgrader/manage_students/<sid>/<tarea>` | `manage_students_assignments.js:34-45` |
| Overall/Code/Written/Task Score + ✓ Needs Manual Grade | docente | Solo lectura (`GET /formgrader/api/student_submissions/<sid>`) | `manage_students_assignments.js:2-5,47-96` |

#### 5.3 `/formgrader/manage_students/<sid>/<tarea>` — notebooks del estudiante

| Botón/acción | Quién lo ve | Qué hace | Archivo:línea |
|---|---|---|---|
| Migas de 3 niveles | docente | — | `manage_students_notebook_submissions.tpl:12-18` |
| Notebook ID (enlace; si falta el archivo, texto `"… (file missing)"`) | docente | GET `/formgrader/submissions/<id>` | `manage_students_notebook_submissions.js:38-47` |
| Scores + ✓ Needs Manual Grade + ✓ Tests Failed + 🚩 Flagged | docente | Solo lectura (`GET /formgrader/api/student_notebook_submissions/<sid>/<tarea>`) | `manage_students_notebook_submissions.js:2-5,49-120` |

---

### 6. Endpoints de la API de formgrader (referencia completa)

`nbgrader/server_extensions/formgrader/apihandlers.py:314-348`. Todos exigen `@web.authenticated` + `check_xsrf` + `check_notebook_dir`.

| Método | Ruta | Usado por |
|---|---|---|
| GET | `/formgrader/api/status` | — (salud) |
| GET | `/formgrader/api/assignments` | Manage Assignments, Manual Grading |
| GET/PUT | `/formgrader/api/assignment/<id>` | Edit / Add assignment |
| POST | `/formgrader/api/assignment/<id>/assign` | **Generate** |
| POST | `/formgrader/api/assignment/<id>/release` | **Release** |
| POST | `/formgrader/api/assignment/<id>/unrelease` | **Unrelease** |
| POST | `/formgrader/api/assignment/<id>/collect` | **Collect** |
| POST | `/formgrader/api/assignment/<id>/generate_feedback` | Generate Feedback (todos) |
| POST | `/formgrader/api/assignment/<id>/release_feedback` | Release Feedback (todos) |
| POST | `/formgrader/api/assignment/<id>/<sid>/generate_feedback` | Generate Feedback (uno) |
| POST | `/formgrader/api/assignment/<id>/<sid>/release_feedback` | Release Feedback (uno) |
| GET | `/formgrader/api/notebooks/<tarea>` | Gradebook notebooks |
| GET | `/formgrader/api/submissions/<tarea>` | Manage Submissions |
| GET | `/formgrader/api/submission/<tarea>/<sid>` | refresco de fila |
| POST | `/formgrader/api/submission/<tarea>/<sid>/autograde` | **Autograde** (envuelto por AVA) |
| GET | `/formgrader/api/submitted_notebooks/<tarea>/<nb>` | lista de entregas |
| POST | `/formgrader/api/submitted_notebook/<id>/flag` | **Flag** (`Ctrl+Shift+F`) |
| GET | `/formgrader/api/grades` · GET/PUT `/formgrader/api/grade/<id>` | notas manuales |
| GET | `/formgrader/api/comments` · GET/PUT `/formgrader/api/comment/<id>` | comentarios |
| GET | `/formgrader/api/students` · GET/PUT `/formgrader/api/student/<sid>` | Manage Students |
| GET | `/formgrader/api/student_submissions/<sid>` | ficha del estudiante |
| GET | `/formgrader/api/student_notebook_submissions/<sid>/<tarea>` | notebooks del estudiante |

---

### 7. Bloque de ayuda AVA dentro de formgrader

Inyectado en `.container-fluid` de **todas** las páginas de formgrader (`formgrader_ayuda.js:385-396`). Se reintenta cada 500 ms hasta 20 veces (`:398-407`).

| Botón/acción | Quién lo ve | Qué hace (endpoint o comando) | Archivo:línea |
|---|---|---|---|
| Botón azul **`Ver mi curso`** | docente | Enlace a `<raiz>/panel-docente` | `notebook/formgrader_ayuda.js:123-126` |
| Enlace **`ocultar` / `mostrar`** | docente | Cliente; persiste en `localStorage['ava-ayuda-docente']` | `notebook/formgrader_ayuda.js:129-160` |
| Tabla explicativa: Generate / Preview / Release / Collect / Autograde (con avisos "Cuidado") | docente | Solo texto | `notebook/formgrader_ayuda.js:21-74` |
| Resumen del recorrido completo | docente | Solo texto | `notebook/formgrader_ayuda.js:76-85` |
| **Desplegable `Subir notas al panel del alumno`** | docente | Se llena con GET `/ava-admin/actividades` (solo actividades con `calificadas > 0`) | `notebook/formgrader_ayuda.js:200-223` |
| Botón **`Subir notas`** | docente | POST `/ava-admin/registrar-notas` con `{tarea}` y cabecera `X-XSRFToken`; muestra hasta 8 notas y avisos | `notebook/formgrader_ayuda.js:225-264`; handler `notebook/admin_bridge.py:78-104` |
| **Desplegable `Eliminar una actividad`** (etiquetado con `publicada`, `N con entregas`, `sin notebook`) | docente | GET `/ava-admin/actividades` (con XSRF también en el GET, `:313-321`) | `notebook/formgrader_ayuda.js:318-337` |
| Campo **`escribe el nombre para confirmar`** | docente | Bloquea el borrado si el texto ≠ nombre exacto | `notebook/formgrader_ayuda.js:291-292,342-345` |
| Casilla **`forzar (aunque esté publicada o tenga entregas)`** | docente | Añade `forzar: true` al POST | `notebook/formgrader_ayuda.js:293-295,357` |
| Botón rojo **`Eliminar`** | docente | POST `/ava-admin/borrar` con `{tarea, forzar}` + XSRF; tras el éxito **recarga la página a los 2,5 s** | `notebook/formgrader_ayuda.js:296-298,339-382`; handler `notebook/admin_bridge.py:165-186` |

### Rutas AVA de administración (`notebook/admin_bridge.py:189-195`) — **solo si `ALUMNO_ROL=instructor`** (`:37`, `:201-203`)

| Método | Ruta | Qué hace | Evidencia |
|---|---|---|---|
| GET | `/ava-admin/actividades` | Lista actividades con `publicada`, `envios`, `vacia`, `calificadas` | `admin_bridge.py:53-66` |
| POST | `/ava-admin/borrar` | `borrar_cuadernillo.borrar(tarea, forzar)`; 409 si se niega | `admin_bridge.py:165-186` |
| POST | `/ava-admin/registrar-notas` | `registrar_notas.registrar(tarea)` | `admin_bridge.py:78-104` |
| — | (gancho) `AutogradeHandler.post` | Reescrito: tras un autograde con `success`, lanza hilo que sube notas | `admin_bridge.py:128-162` |

---

### 8. Panel del docente (`/panel-docente`) — `notebook/panel_docente_bridge.py`

Registrado solo para instructor (`:904-910`), protegido con `@web.authenticated` (`:880`, `:888`).

| Botón/acción | Quién lo ve | Qué hace | Archivo:línea |
|---|---|---|---|
| Enlace **`ir a formgrader`** (cabecera) | docente | `<raiz>/formgrader` | `panel_docente_bridge.py:758` |
| Sección **Tus estudiantes** (tabla: Estudiante, Última vez, Va por, Resueltos, Atascados, Entregas, Notas) | docente | Datos de `/internal/curso/<curso>/panel` | `panel_docente_bridge.py:408-455,764-767` |
| **Nombre de cada estudiante** (enlace) | docente | `<raiz>/panel-docente/estudiante/<sid>` | `panel_docente_bridge.py:389-397` |
| Pie "Docentes del curso: …" | docente | Solo lectura | `panel_docente_bridge.py:446-450` |
| Sección **En qué punto está cada cuadernillo** (Generada, Publicada, Puntos, Lo trajeron, Trabajando, Entregaron, Sin recoger, Recogidas, Calificadas, **Te toca**) | docente | Cruce disco + nbexchange | `panel_docente_bridge.py:487-525,769-773` |
| Marca **`Esta semana`** | docente | Solo lectura | `panel_docente_bridge.py:494` |
| Tooltips de cabecera ("Alumnos que lo recibieron…", "Entregas que Collect aún no trajo") | docente | `title=` | `panel_docente_bridge.py:519-522` |
| Sección **Lo que has recogido** (estado `Calificado` / `Sin calificar` / **`Recogida de nuevo después de calificar`**) | docente | Solo lectura | `panel_docente_bridge.py:458-484,775-777` |
| Sección **Qué cuesta y dónde se atascan** | docente | Solo lectura | `panel_docente_bridge.py:545-585,779-784` |
| Sección **Lo que se están equivocando igual** | docente | Solo lectura | `panel_docente_bridge.py:587-605,786-789` |
| Sección **Quién está peleando solo** (nombres enlazados a la ficha) | docente | `<raiz>/panel-docente/estudiante/<sid>` | `panel_docente_bridge.py:648-668,791-794` |
| Sección **Cómo va el grupo por competencia** (+ salud) | docente | Solo lectura, con `title=` por competencia | `panel_docente_bridge.py:607-684,796-798` |
| Banda de aviso cuando el backend no responde | docente | Solo lectura | `panel_docente_bridge.py:749-750` |

### Ficha por estudiante (`/panel-docente/estudiante/<sid>`)

| Botón/acción | Quién lo ve | Qué hace | Archivo:línea |
|---|---|---|---|
| Enlace **`← Tu curso`** | docente | `<raiz>/panel-docente` | `panel_docente_bridge.py:865` |
| Cabecera con correo, id, último ingreso, nº de ingresos | docente | Solo lectura | `panel_docente_bridge.py:813-820` |
| Indicador **`devolución de nota a Moodle posible`** / *"Moodle no mandó casilla de nota"* | docente | Solo lectura | `panel_docente_bridge.py:818-820` |
| Tabla **Sus cuadernillos** (Lo trajo / Entregó / Nota) | docente | Cruce nbexchange + gradebook | `panel_docente_bridge.py:823-834,869-870` |
| Tabla **Su recorrido, ejercicio por ejercicio** (estados: `resuelto`, `solo ejecutó la celda vacía`, `a medias`, `atascado`; Intentos, Última vez, Último error) | docente | `/internal/curso/<curso>/estudiante/<sid>` | `panel_docente_bridge.py:836-862,871-874` |

---

### 9. Panel del alumno (`/panel`) — `notebook/panel_bridge.py`

Registrado **solo si NO es instructor** (`:453-460`), con `@web.authenticated` (`:399`, `:422`). Es la página de aterrizaje del alumno.

| Botón/acción | Quién lo ve | Qué hace (endpoint o comando) | Archivo:línea |
|---|---|---|---|
| Carga del panel (efecto lateral) | alumno | Antes de pintar ejecuta `entregar_cuadernillo.main()` para traer cuadernillos nuevos | `panel_bridge.py:404-409` |
| Botón azul **`Abrir cuadernillo`** (por tarjeta) | alumno | `<base_url>/notebooks/<archivo>` (notebook clásico) | `panel_bridge.py:282-283,220-230` |
| Marca **`Esta semana`** | alumno | Solo lectura | `panel_bridge.py:247` |
| Dato **`Vas por`** (barra de progreso o "sin empezar") | alumno | Solo lectura | `panel_bridge.py:256-263` |
| Dato **`Nota`** (`x / y` o "aún sin calificar") | alumno | Solo lectura; solo si `origen_nota == "nbgrader"` | `panel_bridge.py:249-254` |
| Dato **`Entrega`**: `Entregado el …` o *"sin entregar · el botón está dentro del cuadernillo"* | alumno | Solo lectura — **no hay botón de entregar en el panel, por diseño** | `panel_bridge.py:265-272,233-244` |
| Aviso **`Dejaste N ejercicios a medias`** | alumno | Solo lectura | `panel_bridge.py:274-277` |
| Bloque **`Qué has aprendido`** (competencias, barra + descripción + pie) | alumno | Solo lectura | `panel_bridge.py:301-334` |
| Banda de aviso si el backend falla | alumno | El panel se dibuja igual | `panel_bridge.py:336`, `:419-421` |
| Endpoint **POST `/panel/entregar`** | alumno (lo llama la barra del cuadernillo) | Valida el id contra los cuadernillos en disco → `nbexchange_cliente.ava.entregar` | `panel_bridge.py:416-447,210-217` |

---

### 10. Dentro del cuadernillo del alumno — `notebook/custom.js`

Se carga desde `/home/jovyan/.jupyter/custom/custom.js` (`notebook/Dockerfile:85`).

| Botón/acción | Quién lo ve | Qué hace (endpoint o comando) | Archivo:línea |
|---|---|---|---|
| **Barra superior fija** del cuadernillo (no en `inicio.ipynb`) | alumno | Se inserta en `#notebook-container` | `custom.js:596-625` |
| Enlace **`← Mis cuadernillos`** | alumno | `<base_url>panel` | `custom.js:611-612` |
| Botón azul **`Guardar y entregar`** | alumno | `Jupyter.notebook.save_notebook()` → POST `<base_url>panel/entregar` con `{id}` + `X-XSRFToken` | `custom.js:615-617,629-668` |
| El mismo botón pasa a **`Entregar de nuevo`** tras el éxito | alumno | Reentrega permitida | `custom.js:649-650` |
| Mensajes de la barra: `Guardando…`, `Entregando…`, `Entregado. Tu profesor ya lo tiene.`, `No se pudo entregar.` / `No se pudo entregar ahora mismo.` | alumno | — | `custom.js:632,636,649,653,658` |
| Enlace **`ver el codigo`** en celdas ocultas (tags `ava-oculta` / `ava-motor`) | alumno | Cliente: muestra la celda y quita el aviso | `custom.js:549-577` |
| Tarjeta de retroalimentación por celda de prueba: cabecera **error** con `Intento #N` / **éxito** con `N intentos • Xs` | alumno | Solo lectura, se anexa a la celda | `custom.js:130-188` |
| Desplegable **`Ver JSON que se enviaría al Backend (Click para desplegar)`** | alumno | `<details>` cliente | `custom.js:170-179` |
| **Tarjeta de valoración** *"✅ ¡Completaste el cuadernillo! …"* | alumno | Aparece una sola vez por alumno/cuadernillo (`rating_enviado`) | `custom.js:316-320,342-347,355-357` |
| **5 estrellas ★** (hover + clic) | alumno | Selecciona 1-5; habilita el botón | `custom.js:350-353,377-394` |
| **Textarea `Comentario (opcional)`** | alumno | — | `custom.js:359` |
| Botón **`Enviar calificación`** (deshabilitado hasta elegir estrellas) | alumno | Evento `cuadernillo_rating` → POST `<base_url>nbgrader-metrics/evento` | `custom.js:361,395-403,324-339,97` |
| Mensaje **`¡Gracias por tu calificación!`** | alumno | — | `custom.js:402` |
| Telemetría por ejecución de celda de prueba | alumno | POST `nbgrader-metrics/evento` | `custom.js:97`; handler `notebook/metrics_bridge.py:70,177` |
| Carga del Tutor IA | alumno | `<script src="<base_url>tutor-ia/static/tutor_ia.js">` | `custom.js:675-684` |

> **No existe barra de XP ni insignias en el código actual.** Lo único parecido son las estrellas de valoración y el contador de intentos. El texto de la ayuda del docente sí menciona que "los puntos de experiencia y las insignias que ve el alumno no cuentan para nada" (`formgrader_ayuda.js:84-85`), pero no hay componente que los pinte.

---

### 11. Tutor IA — `notebook/tutor_ia.js` (solo alumno)

| Botón/acción | Quién lo ve | Qué hace (endpoint) | Archivo:línea |
|---|---|---|---|
| **Botón flotante 🤖** (abajo a la derecha, tooltip "Tutor IA del cuadernillo") | alumno | Abre/cierra el panel | `tutor_ia.js:249-256` |
| **Píldora roja** con las preguntas restantes sobre el 🤖 (se oculta al llegar a 0) | alumno | `estadoServidor.restantes` | `tutor_ia.js:253,164-167` |
| **Contador `N/max`** en la cabecera del panel (tooltip "Preguntas que te quedan en este cuadernillo"); vira a rojo al agotarse | alumno | — | `tutor_ia.js:268,152-163` |
| Botón **`×` (Cerrar)** | alumno | Cierra el panel | `tutor_ia.js:269,281` |
| **Textarea de la duda** (`Escribe tu duda (Enter para enviar)…`) | alumno | Enter envía; se **deshabilita** al agotar el cupo con el texto "Ya usaste tus N preguntas de este cuadernillo." | `tutor_ia.js:273,283-291,169-177` |
| Botón **`Enviar`** (se atenúa y bloquea al agotarse o mientras envía) | alumno | POST `<base>tutor-ia/preguntar` con `X-XSRFToken` | `tutor_ia.js:274,282,178-182,198-244` |
| Mensaje de bienvenida ("No te voy a dar la solución, pero sí pistas…" + cupo) | alumno | — | `tutor_ia.js:113-121` |
| Indicador **`Pensando…`** | alumno | — | `tutor_ia.js:142-146` |
| Mensajes de error ⚠️ (incluye el 429 con el contador real) | alumno | — | `tutor_ia.js:131-134,222-228` |
| Consulta inicial de estado | alumno | GET `<base>tutor-ia/estado` | `tutor_ia.js:317`; handler `tutor_bridge.py:344` |
| **Límite: 5 preguntas por cuadernillo** (`TUTOR_MAX_PREGUNTAS`) | alumno | Contado por `CUADERNILLO_CODIGO` | `notebook/tutor_bridge.py:57,162,248` |
| Historial de chat local (últimos 40 mensajes) | alumno | `localStorage` | `tutor_ia.js:100` |

---

### 12. Qué se activa/desactiva por rol — `notebook/entrypoint.sh` y `jupyter_server_config.py`

| Elemento | Docente | Alumno | Evidencia |
|---|---|---|---|
| `formgrader` (extensión y pestaña) | **habilitada** | **deshabilitada** | `entrypoint.sh:41,43` / `:83,85` |
| `course_list` (pestaña *Courses*) | **habilitada** | **deshabilitada** | `entrypoint.sh:42,44` / `:84,86` |
| `create_assignment` (nbextension, barra de metadatos nbgrader en el notebook) | **habilitada** | **deshabilitada** | `entrypoint.sh:40` / `:82` |
| **`assignment_list`** (pestaña *Assignments*: Fetch / Validate / Submit) | **deshabilitada** | **deshabilitada** | `entrypoint.sh:45-47` / `:91-93` |
| JupyterLab | disponible | **deshabilitado** | `entrypoint.sh:97-98` |
| **Terminales** | disponibles (Instructions enlaza a `/terminals/1`) | **`terminals_enabled = False`** | `jupyter_server_config.py:37`; `manage_submissions.tpl:44` |
| Raíz del explorador de archivos | `/home/jovyan` (con symlink `work/nbgrader` → `/srv/nbgrader`) | **acotada a `/home/jovyan/work`** | `entrypoint.sh:35`; `jupyter_server_config.py:42` |
| Volumen `nbgrader_shared` | montado | **no montado** | `entrypoint.sh:8-11`; `jupyterhub_config.py:292` |
| `admin_bridge` (rutas `/ava-admin/*`) | registrado | **no se registran rutas** | `admin_bridge.py:201-203` |
| `panel_docente_bridge` (`/panel-docente`) | registrado | **no** | `panel_docente_bridge.py:904-905` |
| `panel_bridge` (`/panel`, `/panel/entregar`) | **no** | registrado | `panel_bridge.py:453-455` |
| `metrics_bridge`, `tutor_bridge` | cargados | cargados | `jupyter_server_config.py:8-26` |
| Siembra de plantillas en `source/` (`cp -n`) | sí | — | `entrypoint.sh:58-66` |
| Descarga de cuadernillos publicados al arrancar | — | `entregar-cuadernillo` | `entrypoint.sh:105` |

---

### 13. Comandos de terminal

### Docente (imagen `mi_imagen_jupyterlab_docente`, alias en `/usr/local/bin`, `notebook/Dockerfile:100-117`)

| Comando | Quién | Uso y flags | Archivo:línea |
|---|---|---|---|
| `sembrar-cuadernillo` | docente | Sin args: **lista** plantillas y su estado | `sembrar_cuadernillo.py:69-72` |
| `sembrar-cuadernillo <tarea>` | docente | Copia `/opt/plantillas/<tarea>/*.ipynb` → `source/<tarea>/`. Si ya existe, **no toca nada** y avisa | `sembrar_cuadernillo.py:87-91` |
| `sembrar-cuadernillo <tarea> --forzar` | docente | **Reemplaza** `source/<tarea>`; guarda copia con fecha en `respaldos_source/` antes | `sembrar_cuadernillo.py:68,93-105` |
| `publicar-cuadernillo` (sin args) | docente | Imprime el docstring y sale con 1 | `publicar_cuadernillo.py:69-71` |
| `publicar-cuadernillo <tarea>` | docente | Escribe `release/<tarea>/ava_publicacion.json` (id, notebook, ventana, hash del contenido) y llama `ava.liberar(tarea)` | `publicar_cuadernillo.py:97-115` |
| `publicar-cuadernillo <tarea> <abre_iso> <cierra_iso>` | docente | Fija la ventana; valida ISO 8601 y que `cierra > abre` | `publicar_cuadernillo.py:74-78,51-63` |
| `publicar-cuadernillo <tarea> --sin-activar` | docente | Publica **sin** convertirlo en "el de esta semana" | `publicar_cuadernillo.py:67,102,127-129` |
| `borrar-cuadernillo` (sin args) | docente | **Lista** qué hay y qué se borraría | `borrar_cuadernillo.py:294-295` |
| `borrar-cuadernillo <tarea>` | docente | Borra `source/`, `release/` y su ficha en `gradebook.db`; retira la liberación. **Se niega** si está publicada o tiene envíos | `borrar_cuadernillo.py:291-304`; docstring `:1-28` |
| `borrar-cuadernillo <tarea> --forzar` | docente | Borra **también** `submitted/`, `autograded/`, `feedback/`. Copia con fecha en `respaldos_borrados/` antes | `borrar_cuadernillo.py:292,285-286` |
| `registrar-notas` (sin args) | docente | Lista qué cuadernillos tienen notas | `registrar_notas.py:141-143` |
| `registrar-notas <tarea>` | docente | Lee el gradebook y hace POST al backend con `origen='nbgrader'`; imprime las 5 primeras notas y los avisos | `registrar_notas.py:144-160` |
| `cargar-competencias` | docente | Sube `/opt/plantillas/competencias.json` (`COMPETENCIAS_MAPEO`) → POST `/internal/competencias` | `cargar_competencias.py:34-40,62-68` |
| `cargar-competencias <mapeo.json>` | docente | Usa otro archivo. Exige `METRICS_DOCENTE_TOKEN` | `cargar_competencias.py:35,37-39` |
| `nbgrader autograde "<tarea>"` | docente | Sugerido en pantalla desde el acordeón Instructions | `manage_submissions.tpl:48-49` |
| `nbgrader list --remove <tarea>` | docente | Sugerido si nbexchange no respondió durante un borrado | `borrar_cuadernillo.py:282-283` |

### Alumno

| Comando | Quién | Uso | Archivo:línea |
|---|---|---|---|
| `entregar-cuadernillo` | alumno (automático, sin terminal) | Se ejecuta en el arranque del contenedor y en cada carga del panel: pregunta a nbexchange qué hay liberado, valida la ventana y deja `work/<id>.ipynb`. Devuelve el código del cuadernillo activo | `entrypoint.sh:105`; `panel_bridge.py:404-409`; `entregar_cuadernillo.py:222` |
| **Ningún otro** | alumno | `ServerApp.terminals_enabled = False` — el alumno no tiene terminal | `jupyter_server_config.py:37` |

---

### 14. Acciones destructivas o irreversibles

Ordenadas de mayor a menor riesgo.

### Críticas — destruyen trabajo

1. **`Eliminar` con `forzar` marcado** (bloque AVA en formgrader) — borra `source/`, `release/`, `submitted/`, `autograded/`, `feedback/` y la ficha del gradebook, **incluidas las entregas de los alumnos**. Mitigación: hay que escribir el nombre exacto y marcar la casilla; se guarda copia con fecha en `respaldos_borrados/`. Evidencia: `formgrader_ayuda.js:293-298,342-345,357`; `borrar_cuadernillo.py:285-286`, docstring `:22-28`.
2. **`borrar-cuadernillo <tarea> --forzar`** (terminal) — idéntico al anterior sin la confirmación por nombre: un solo comando. `borrar_cuadernillo.py:292`.
3. **`Eliminar` sin forzar** — borra `source/` y `release/` (el trabajo de autoría del docente) y la ficha del gradebook. `borrar_cuadernillo.py:291-304`.
4. **`sembrar-cuadernillo <tarea> --forzar`** — reemplaza `source/<tarea>`, que puede llevar horas de edición desde formgrader. Copia previa en `respaldos_source/`. `sembrar_cuadernillo.py:68,93-105`.

### Altas — rompen la correspondencia con lo entregado

5. **`Generate` (birrete) después de haber recogido envíos** — regenera `release/` y se pierde la correspondencia con lo ya entregado. **No hay confirmación de ningún tipo**, es un clic. La única barrera es el aviso textual del bloque AVA. `manage_assignments.js:147-152,237-243`; aviso en `formgrader_ayuda.js:29-30`.
6. **`Unrelease` (aspa roja)** — retira la actividad del exchange: deja de aparecer a los alumnos. No borra nada del disco, pero quien ya la tenga sigue trabajando en su copia. Un clic, sin confirmación; es el **mismo sitio** donde estaba Release, solo cambia el icono. `manage_assignments.js:182-189,273-279`; `apihandlers.py:250-255`; aviso en `formgrader_ayuda.js:51-53`.

### Medias — sobrescriben o exponen datos

7. **`No credit`** — pone `manual_score=0` y `extra_credit=0` de golpe, sin deshacer. `formgrade_models.js:111-115`.
8. **`Full credit`** — pone la nota máxima, pisando la que hubiera. `formgrade_models.js:105-109`.
9. **`Autograde` (rayo) sobre una entrega ya corregida a mano** — recalcula las notas automáticas. Además, en AVA **dispara automáticamente la subida al backend** en segundo plano: la nota llega al alumno sin paso intermedio. `manage_submissions.js:133-141`; `admin_bridge.py:149-153`.
10. **`Release Feedback` (sobre)** — publica la retroalimentación a los alumnos; una vez enviada, ya la han visto. `manage_assignments.js:433-439`, `manage_submissions.js:217-225`.
11. **`Guardar y entregar` / `Entregar de nuevo`** (alumno) — reentrega y sustituye la versión anterior en el buzón. Reversible reentregando, pero si el docente ya recogió y calificó, el panel lo marca como **"Recogida de nuevo después de calificar"**. `custom.js:629-668`; `panel_docente_bridge.py:466-468`.
12. **`Subir notas`** — sobrescribe en el backend las notas de esa actividad ("la última subida manda"). `formgrader_ayuda.js:180-181,225-264`.
13. **`Add new assignment` con nombre erróneo** — crea carpeta en `source/` y ficha en el gradebook; queda en la lista hasta que se borre explícitamente. Ojo: **el lápiz de una fila de una actividad ya borrada vuelve a crearla vacía** (por eso el borrado recarga la página). `apihandlers.py:144-148`; `formgrader_ayuda.js:369-372`.
14. **Ojo / `Show All Names` / `toggle_name`** — revelan la identidad del estudiante durante la corrección a ciegas. Reversible, pero es una exposición de datos personales. `gradebook_notebook_submissions.js:194-217`; `formgrade_macros.html.j2:88-89`.

### Bajas — reversibles pero fáciles de disparar sin querer

15. **`Ctrl+Shift+F` (flag)** — alterna la marca de la entrega. **No tiene botón visible**: solo se descubre en el modal de atajos, y es fácil de pulsar por accidente. `formgrade.js:71-75,302-328`.
16. **`Release`** — publica a los alumnos. Reversible con Unrelease, pero quien ya la trajo se la queda. `manage_assignments.js:309-315`.
17. **Idle culler** — apaga el servidor tras 1 h sin actividad. No borra datos (el trabajo vive en el volumen del alumno), pero corta la sesión sin previo aviso. `jupyterhub_config.py:501-513`.

### Salvaguardas ausentes que conviene registrar en el acta

- Ni **Generate**, ni **Release/Unrelease**, ni **Collect**, ni **Autograde**, ni **Release Feedback** piden confirmación: son un solo clic sobre un icono de 14 px sin etiqueta de texto (`manage_assignments.js:139-233`).
- **Manage Students no tiene botón de eliminar** en nbgrader 0.8.5 — si el acta lo contempla, no existe (`manage_students.js:173-182`; sin `DELETE` en `apihandlers.py:314-348`).
- El único punto del sistema con **doble confirmación** (escribir el nombre + casilla) es el `Eliminar` de AVA (`formgrader_ayuda.js:342-345`).

## Parte 2 · Registro del ensayo

Hora en UTC (Colombia = UTC−5). «OK» = se comportó como dice el inventario y se comprobó
la evidencia; «HALLAZGO» = algo que no cuadra y queda registrado en la Parte 3.

### 2.0 Reinicio de cero

| # | Acción | Resultado | Evidencia |
|---|---|---|---|
| 0.1 | `docker compose down`, borrado de `ava_postgres-data`, `ava_hub_estado`, `ava_nbexchange_data`, `nbgrader_shared`, `ava-trabajo-*` (autorizado por Diego) | OK | solo queda `ava_caddy_data` (certificados) |
| 0.2 | Reconstrucción de las 5 imágenes (hub, nbexchange, backend, alumno, docente) en `c6f08e5` | OK | `compose build` + `docker build` sin errores |
| 0.3 | `compose up -d`; Postgres inicializa con `schema_v2.sql`; `migracion_v3.sql` idempotente | OK | 11 tablas, 7 competencias, 0 estudiantes; Hub `/hub/login` 302; `/services/nbexchange/` 200; backend «Servidor operando» |

### 2.1 Instructor (Bryan) — entrada y Manage Assignments

| # | Acción (fila del inventario) | Resultado | Evidencia |
|---|---|---|---|
| 1.1 | Bryan entra a Moodle en el navegador de la app y abre `test_jupyter` (§0, entrada LTI). **Desde el iframe de Moodle**, no en ventana nueva | OK — el iframe cargó JupyterHub en este navegador | Hub 16:58:45: `Adding user ritokun60@gmail.com to group(s): {'formgrade-28053'}`; contenedor `mi_imagen_jupyterlab_docente`; backend `POST /internal/lti/ingreso` 200 y `mint-metrics-token` 200; `estudiantes`: `3651 | Bryan Andrey Silva Vergel | instructor | sourcedid=t` |
| 1.2 | Aterrizaje del docente en `/formgrader` con el bloque de ayuda AVA arriba (§1, §7) | OK | `ayuda: true`; lista `semana_01: draft`, `semana_02: draft` (sembradas por el entrypoint) |
| 1.3 | `+ Add new assignment...` → modal «Add New Assignment» (Name, Due date, Timezone, Save/Cancel) con el nombre mal escrito **«Semana 3»** (§2) | OK — reproduce el escenario reportado: fila `Semana 3: draft` y en el desplegable de Eliminar `Semana 3 (sin notebook)` | PUT `/formgrader/api/assignment/Semana 3` |
| 1.4 | Bloque AVA **Eliminar** «Semana 3» sin escribir el nombre (§7) | OK — se niega: «Escribe Semana 3 en la casilla para confirmar.» | — |
| 1.5 | Eliminar «Semana 3» con el nombre escrito, sin forzar | OK — «Eliminada. Copia guardada en …/respaldos_borrados/Semana 3_20260823_170031 · borrado: source · borrado: la ficha en gradebook.db»; la página se recargó sola y la fila desapareció de la tabla de formgrader | lista tras recarga: `semana_01`, `semana_02` |
| 1.6 | **Edit** (lápiz) `semana_01` → modal «Editing semana_01», Due date `2026-09-15T23:59`, timezone `-0500`, Save (§2) | OK | columna Due Date: `2026-09-16 04:59:00 UTC` (= 23:59 Bogotá) |
| 1.7 | **Generate** `semana_01` (§2) | OK — «Successfully created the student version of 'semana_01'» | aparecen Preview (lupa) y Release (nube) |
| 1.8 | **Preview** `semana_01` (§2) | OK — abre `tree/nbgrader/28053/release/semana_01` con `cuadernillo.ipynb` | `/api/contents/nbgrader/28053/release/semana_01` 200 |
| 1.9 | **Release** `semana_01` | OK — «Successfully released 'semana_01'»; estado `released`; la celda Release pasa a aspa (Unrelease) y aparece Collect | exchange: `semana_01 released 3651 17:01:30` |
| 1.10 | **Unrelease** `semana_01` (aspa) y **Release** de nuevo (§2, §14.6) | OK — `draft` y luego `released` otra vez; la re-liberación sí almacena (corrección del trap de nbexchange) | exchange: segunda fila `semana_01 released 3651 17:05:02` |
| 1.11 | **Generate** `semana_02` | OK | «Successfully created the student version of 'semana_02'» |
| 1.12 | Terminal del docente: `publicar-cuadernillo` sin args (ayuda), `publicar-cuadernillo semana_02 2026-08-23T00:00 2026-09-30T23:59`, fecha inválida `2026-13-99`, `cargar-competencias`, `borrar-cuadernillo` (lista), `registrar-notas` (lista), `sembrar-cuadernillo` (lista) (§13) | OK todos — publicado con ventana y `semana_02` como «el de esta semana»; la fecha inválida da `[ERROR] No entiendo la fecha…`; 20 relaciones de competencias; listados coherentes («PUBLICADA», «sin entregas recogidas», «ya en source/») | exchange: `semana_02 released 3651 17:06:49`; backend `POST /internal/competencias` 200. **Nota**: el terminal web (`/terminals/1`) abre y da prompt, pero la escritura sintética de este navegador no llega a xterm; los comandos se ejecutaron con `docker exec` dentro del contenedor de Bryan (mismo entorno y token) |
| 1.13 | Vista de archivos del docente (`/tree`) | **HALLAZGO H1**: no hay pestañas «Formgrader» ni «Courses» en el árbol; desde ahí no hay camino de vuelta a formgrader salvo la URL | `jupyter nbextension list`: solo `create_assignment/main` habilitada; `formgrader/main` y `course_list/main` no |

### 2.2 Estudiante (Diego) — entrada, cuadernillos, tutor, telemetría, valoración y entrega

| # | Acción (fila del inventario) | Resultado | Evidencia |
|---|---|---|---|
| 2.1 | Diego lanza `test_jupyter` desde Moodle con la vista «Estudiante» (§0) | OK | Hub 17:07:50: grupo `nbgrader-28053`; contenedor `mi_imagen_jupyterlab:latest`; `estudiantes`: `3135 | Diego Alejandro Lopez Camacho | estudiante`; exchange: `fetched semana_02` y `fetched semana_01` a las 17:08:20 |
| 2.2 | Aterrizaje en `/panel` (§9): dos tarjetas, «Semana 2 · Esta semana», «Abrir cuadernillo» → `/notebooks/semana_0N.ipynb` | OK | `.ava_publicados.json`: `semana_02` con ventana 23-ago → 30-sep, `semana_01` sin ventana |
| 2.3 | Dentro de `semana_01` (§10, §12): barra con «← Mis cuadernillos» y «Guardar y entregar»; 15 enlaces «ver el codigo»; botón flotante del Tutor IA | OK | — |
| 2.4 | Lo que el alumno **no** puede hacer (§12): crear terminal, listar `nbgrader/`, abrir `/formgrader`, `/ava-admin/actividades`, `/panel-docente` | OK — todo 404 | `POST /api/terminals` 404; `/api/contents/nbgrader` 404; `/formgrader` 404; `/ava-admin/actividades` 404; `/panel-docente` 404 |
| 2.5 | Tutor IA (§11): `GET tutor-ia/estado` → 5/5; pregunta real «¿Qué diferencia hay entre un dato y un proceso?…» desde `semana_01` | OK como flujo — respondió con una analogía de cocina sin dar la solución; contador pasó a `4/5` | **HALLAZGO H2**: el estado dice `cuadernillo_id: semana_02` estando en `semana_01`: el cupo se cuenta por `CUADERNILLO_CODIGO` del arranque, no por el cuadernillo abierto. **HALLAZGO H3**: la respuesta mostró al alumno el bloque interno «Estado de la sesión (Historial para la siguiente interacción)»; `_quitar_bloque_estado` no reconoce esa redacción |
| 2.6 | `semana_02`: ejercicios 1–8 con variaciones (ej1 falla→pasa, ej6 primero con `int('3.85')` sin correr la prueba, el resto bien) (§10) | OK — 9 eventos, todos `204` en el puente, con `cuadernillo: semana_02` desde el navegador | `exercise_attempts`: 9 filas (8 passed, 1 failed, 8 ejercicios distintos); `attempt_errors`: 2 |
| 2.7 | Tarjeta de valoración al completar los 8 (§10): 4 estrellas + comentario → «Enviar calificación» → «¡Gracias por tu calificación!» | OK | `cuadernillo_ratings`: `3135 | semana_02 | 4 | Me gustó que el pseudocódigo…`; evento `cuadernillo_rating` 204 |
| 2.8 | «Guardar y entregar» (§10) | OK — «Entregado. Tu profesor ya lo tiene.», el botón pasa a «Entregar de nuevo» | exchange: `semana_02 submitted 3135 17:13:50` |
| 2.9 | Panel del alumno tras entregar (§9) | OK — «8 de 8 ejercicios», «Entregado el 23/08 a las 12:13», Nota «aún sin calificar» (correcto: aún no hay Autograde); competencias «Los resolviste todos» | — |

### 2.3 Instructor — recoger, calificar, corregir a mano y devolver

| # | Acción (fila del inventario) | Resultado | Evidencia |
|---|---|---|---|
| 3.1 | **Collect** `semana_02` (§2) | OK | «Processing 1 submissions … Collecting submission: 3135 semana_02»; la columna # Submissions pasa a `1` y se vuelve enlace |
| 3.2 | **Autograde** de la entrega (§3) | OK — `needs autograding` → `graded 80 / 80` | modal «Successfully autograded…» |
| 3.3 | Subida automática de la nota tras Autograde (gancho AVA de §7) | OK — sin ejecutar ningún comando | docente: `[admin_bridge] notas de 'semana_02' subidas al panel: 1`; backend `POST /internal/notas` 200; `cuadernillo_notas`: `3135 | semana_02 | 80 | 80 | 17:15:50` |
| 3.4 | Manual Grading: los tres niveles (§4.1–4.3) | OK — lista de actividades → notebooks (`cuadernillo 80/80`) → entregas | migas `Manual Grading / semana_02 / cuadernillo` |
| 3.5 | **Show All Names / Hide All Names** y el **ojo** por fila (§4.3) | OK — `Submission #1` ⇄ `Camacho, Diego Alejandro Lopez`; el botón alterna su etiqueta | — |
| 3.6 | Página de corrección (§4.4): 8 campos de nota, 8 de extra credit, 8 de comentario, `Resolve` / `Full credit` / `No credit` por celda, `← Prev` / `Next →` | OK | — |
| 3.7 | Nota manual `3` en ejercicio_1; **extra credit** `1` en ejercicio_2; **No credit** y luego **Full credit** en ejercicio_3; comentario en ejercicio_1 | OK — API: `test_ejercicio_1 auto=5 manual=3`; `test_ejercicio_2 extra=1`; `test_ejercicio_3 manual=0 → 10`; comentario guardado en `ejercicio_1` | `GET /formgrader/api/grades?submission_id=…` |
| 3.8 | Modal **`?`** de atajos y **`Ctrl+Shift+F`** (flag, §4.4 y §14.15) | OK — «Submission flagged»; `flagged: true` en la API | — |
| 3.9 | Botón **Subir notas** del bloque AVA tras corregir a mano (§7) | OK — «Subidas 1 nota(s) de semana_02. 3135: 79 / 80» | la nota manual pisa la automática, como debe |
| 3.10 | **Generate Feedback** y **Release Feedback** por entrega (§3) | OK — genera `feedback/3135/semana_02/` y sube al exchange | «Successfully released feedback … Successfully uploaded feedback for assignment» |
| 3.11 | **Manage Students**: listado, lápiz **Edit Student** (id deshabilitado, nombre/apellido/correo editables), Save, `+ Add new student…` presente | OK | fila `Camacho, Diego Alejandro Lopez | 3135 | diegolopezcamacho@gmail.com | 79 / 105` |
| 3.12 | Páginas por estudiante (§5.2, §5.3) | OK | `student_submissions/3135`: `semana_01 0/0 auto=false`, `semana_02 79/80 auto=true`; `student_notebook_submissions`: `score=79 failed=false flagged=true` |
| 3.13 | Panel del docente y ficha individual (§8) | OK — roster con nombre y correo, ciclo por cuadernillo, entregas, dificultad por ejercicio, malentendidos agrupados, riesgo, competencias; la ficha lista los 8 ejercicios de Diego | «1 estudiante · última entrega hace 6 min»; ficha: «devolución de nota a Moodle posible» |

### 2.4 Reentrega del alumno y segunda recogida

| # | Acción | Resultado | Evidencia |
|---|---|---|---|
| 4.1 | Diego edita una celda y pulsa **«Entregar de nuevo»** (§10) | OK — «Entregado. Tu profesor ya lo tiene.» | exchange: segundo `submitted` 17:21:39 |
| 4.2 | El panel del docente detecta la entrega nueva | OK — «Te toca: **Recoger con Collect en formgrader**», columna «sin recoger» = 1 | — |
| 4.3 | **Collect** de nuevo | OK — «Updating submission: 3135 semana_02» (no duplica) | — |
| 4.4 | **Autograde** de la versión nueva | OK — vuelve a `needs manual grading` con `79 / 80`: las notas manuales, el extra y el flag **sobreviven** al re-autograde | `manual=3`, `extra=1`, `flagged=true` |
| 4.5 | Segunda subida automática de notas | OK | `[admin_bridge] notas de 'semana_02' subidas al panel: 1`; `cuadernillo_notas` → `79.00 / 80.00` a las 17:22:42 |

### 2.5 Borrado de actividades y restauración

| # | Acción | Resultado | Evidencia |
|---|---|---|---|
| 5.1 | Eliminar `semana_01` (publicada) sin forzar | OK — se niega con el texto de siempre | «está PUBLICADA … o insiste con «forzar»» |
| 5.2 | Eliminar `semana_02` (publicada **y con entregas**) sin forzar | OK — se niega | mismo mensaje |
| 5.3 | Eliminar `semana_01` **con «forzar»** (§14.1) | OK — «borrado: source · release · la ficha en gradebook.db · **retirada del intercambio**»; respaldo en `respaldos_borrados/semana_01_20260823_172333` | exchange: `semana_01 active=0`, `semana_02 active=1` |
| 5.4 | Restaurar: `sembrar-cuadernillo semana_01` → **Generate** → **Release** → `publicar-cuadernillo semana_01 --sin-activar` (§13) | OK — vuelve a la lista como `released`, y `semana_02` **sigue siendo «esta semana»** | panel del alumno: «Semana 2 · Esta semana» |
| 5.5 | El alumno recibe la re-liberación como versión nueva | OK — aparece una tarjeta `semana_01_v2` sin pisar su trabajo anterior | `.ava_publicados.json` y `work/` con `semana_01.ipynb` y `semana_01_v2.ipynb` |

### 2.6 JupyterHub: Control Panel, parada y arranque

| # | Acción | Resultado | Evidencia |
|---|---|---|---|
| 6.1 | **Stop My Server** desde `/hub/home` (§0) | OK — el botón pasa a «Start My Server» | — |
| 6.2 | **Start My Server** justo después | **HALLAZGO H6** — «Spawn failed: 409 … name already in use» | ver Parte 3 |
| 6.3 | Tras el arreglo (`dbcf336`): Stop y Start **encadenados** por API | OK — `204` y `202`, contenedor arriba en ~30 s, sin 409 ni borrado forzado | logs del Hub sin «409 Client» ni «sigue ahí» |
| 6.4 | El trabajo del alumno sobrevive a parar y arrancar (volumen `ava-trabajo-…`) | OK — `work/` conserva `inicio.ipynb`, `semana_01.ipynb`, `semana_01_v2.ipynb`, `semana_02.ipynb` y la edición de la reentrega | `grep -c "reentrega de prueba"` = 1 |
| 6.5 | Logout / Token / Home de la barra del Hub | Presentes y accesibles (no se cerró sesión para no perder el ensayo) | — |

### 2.7 Verificación de los arreglos, en el mismo ambiente

Todo lo de abajo se comprobó **después** de desplegar `5fd252e` + `dbcf336` en la VM y reconstruir las imágenes, con las mismas dos cuentas.

| Hallazgo | Cómo se verificó | Resultado |
|---|---|---|
| H1 pestañas | Bryan entra y abre `/tree` | Pestañas **Files · Running · Clusters · Formgrader · Courses** |
| H2 cupo del tutor | Diego pregunta desde `semana_01` | El cupo baja en `semana_01` (`usadas 1`) y `semana_02` sigue en `0` |
| H3 bloque de estado | Misma respuesta del tutor | El último mensaje ya no contiene «Estado de la sesión / Historial para la siguiente» |
| H4 nota manual | Panel del docente y ficha | `79/80` en roster, entregas y panel del alumno (antes `80/80`) |
| H5 título de versión | Panel del alumno | «**Semana 1 (versión 2)**» en vez de `semana_01_v2` |
| H6 carrera del spawn | Stop + Start encadenados | Sin 409; el contenedor arranca solo |

## Parte 3 · Hallazgos

Numerados en el orden en que aparecieron. **Los ocho están corregidos, desplegados y
verificados** en este mismo ambiente, con las mismas dos cuentas.

| # | Qué pasaba | Por qué importa | Estado |
|---|---|---|---|
| **H1** | El árbol de archivos del docente no tenía las pestañas **Formgrader** ni **Courses**. `entrypoint.sh` habilitaba las *server extensions* pero no las *nbextensions* de la sección `tree`. | Desde `/tree` no había forma de volver a formgrader salvo escribir la URL a mano. | Corregido (`5fd252e`) y verificado |
| **H2** | El Tutor IA contaba el cupo de 5 preguntas por el `CUADERNILLO_CODIGO` **del arranque del contenedor**, no por el cuadernillo abierto. Preguntar desde `semana_01` gastaba el cupo de `semana_02`. | Un alumno podía quedarse sin tutor en un cuadernillo sin haberlo usado nunca ahí; y un cuadernillo publicado después del arranque compartía contador con el anterior. Mismo fallo que ya se había corregido en la telemetría. | Corregido (`5fd252e`) y verificado |
| **H3** | La respuesta del tutor mostraba al alumno el bloque interno «Estado de la sesión (Historial para la siguiente interacción)». `_quitar_bloque_estado` solo conocía otras redacciones. | Le adelanta al alumno lo que el tutor espera que responda, y expone contabilidad interna. | Corregido (`5fd252e`) y verificado |
| **H4** | El panel del docente sumaba solo `auto_score` del gradebook: una entrega corregida a mano se mostraba como **80/80** mientras formgrader y el backend decían **79/80**. | Dos cifras distintas para la misma nota, y la del panel es la que el docente mira a diario. | Corregido (`5fd252e`) y verificado |
| **H5** | Una versión conservada se mostraba al alumno como `semana_01_v2`, en crudo. | Ruido en la única pantalla que ve el alumno. | Corregido (`5fd252e`) y verificado |
| **H6** | **Stop My Server → Start My Server** seguidos fallaban con `409 … name already in use`: Docker borra el contenedor en segundo plano y el nuevo `create` llegaba antes. Con 30 s de espera todavía fallaba en esta VM. | El alumno se queda sin servidor y con un error en pantalla, en el botón más visible del Hub. Es el mismo fallo que el del cambio de rol (`cdd3281`), pero por otra vía. | Corregido (`5fd252e` + `dbcf336`: spawner propio que espera hasta 90 s y fuerza el borrado a los 10 s) y verificado |
| **H8** | El **cupo de 5 preguntas del Tutor IA se reiniciaba** cada vez que el contenedor se recreaba: parar y arrancar el servidor desde el Control Panel, cambiar de rol o un despliegue devolvían al alumno sus 5 preguntas. El contador vivía en `/home/jovyan/.tutor_ia`, fuera del único volumen que se conserva (`ava-trabajo-<alumno>` → `/home/jovyan/work`). | El tope existe para controlar el gasto de Gemini, y se saltaba con dos clics. | Corregido (`3e02af8`: el estado vive en `work/.ava_tutor`, oculto igual que el resto) y verificado |
| **H7** | **Release Feedback** subía la retroalimentación al exchange, pero **el alumno no tenía ninguna forma de recuperarla**: `assignment_list` está deshabilitada en su imagen (por diseño) y ni el panel, ni `entregar-cuadernillo`, ni `custom.js` llamaban a `fetch_feedback`. | El docente creía que devolvió la corrección y el alumno nunca la veía. | Corregido (`4f8659d`) y verificado |

### 2.8 Verificación de H7, con las dos cuentas

| # | Acción | Resultado | Evidencia |
|---|---|---|---|
| 8.1 | Con la corrección publicada **antes** de la reentrega, el alumno no ve nada | Correcto, no es fallo: el servicio devuelve `{"success": true, "feedback": []}` porque nbexchange ata cada feedback al *checksum* de la entrega, y esa entrega ya no es la vigente | consulta directa al servicio desde el contenedor del alumno |
| 8.2 | Bryan repite **Generate Feedback** + **Release Feedback** sobre la entrega vigente | OK | «Successfully released feedback for 'semana_02' for student '3135'» |
| 8.3 | Panel del alumno | OK — junto a la nota aparece **«79 / 80 · ver la corrección»** | enlace `/panel/correccion/semana_02` |
| 8.4 | El alumno abre la corrección | OK — el HTML de nbgrader con el desglose real: `cuadernillo (Score: 79.0 / 80.0)`, `Test cell (Score: 3.0 / 5.0)` (la nota que Bryan puso a mano), `Test cell (Score: 6.0 / 5.0)` (con el extra credit) y **el comentario del docente**: «revisa el orden de las lecturas» | 862 KB de HTML servidos desde `/panel/correccion/<tarea>` |

> **Para el manual del docente:** si un alumno **vuelve a entregar** después de que se publicó la corrección, hay que **repetir Generate Feedback + Release Feedback**. No es un fallo del AVA: nbexchange no le devuelve al alumno la corrección de una entrega que ya no es la suya.

### 2.9 Segunda vuelta: lo que faltaba por ejercitar

| # | Acción | Resultado | Evidencia |
|---|---|---|---|
| 9.1 | Agotar el cupo del Tutor IA: 5 preguntas y una sexta (§11) | OK — la sexta responde **429** «Ya usaste tus 5 preguntas de este cuadernillo», con `restantes: 0` | estado del tutor: `usadas 5, restantes 0` |
| 9.2 | Al hacerlo se descubrió que el contador **se reiniciaba** al recrear el contenedor | **HALLAZGO H8** — ver Parte 3 | vivía en `/home/jovyan/.tutor_ia`, fuera del volumen `ava-trabajo-<alumno>` |
| 9.3 | Tras el arreglo (`3e02af8`): 1 pregunta usada → **Stop My Server → Start My Server** | OK — el estado sobrevive: `{"semana_01": {"usadas": 1, …}}` en `work/.ava_tutor/estado.json` | 0 errores 409 en el reinicio |

### Notas del ensayo (no son fallos del AVA)

- **nbgrader 0.8.5 no tiene botón para eliminar un estudiante**: `manage_students.js` solo pinta el lápiz y la API no expone `DELETE`. Si hace falta, habría que añadirlo como se añadió el borrado de actividades.
- **El flag de una entrega solo existe como atajo `Ctrl+Shift+F`**, sin botón visible: se descubre únicamente en el modal `?`.
- **Ni Generate, ni Release/Unrelease, ni Collect, ni Autograde, ni Release Feedback piden confirmación.** El único punto con doble confirmación (escribir el nombre + casilla «forzar») es el Eliminar de AVA.
- El **terminal web** del docente abre y da prompt, pero no acepta la escritura sintética de este navegador; los comandos del §13 se ejecutaron con `docker exec` dentro del contenedor de Bryan, mismo entorno y mismo token.
- La sesión de `gcloud` caducó al final del ensayo; lo verificado después de ese momento se hizo por HTTPS contra el Hub, sin SSH.
