# Informe: flujo de telemetría de punta a punta

Probado el 2026-08-22 sobre la rama `feat/menu-cuadernillos-y-notas` (HEAD
`c72716c`), en local con el stack completo (`docker-compose.local.yml`: Hub con
LTI, contenedores de alumno y docente, backend Go, PostgreSQL con `schema_v2.sql`,
nbexchange). Dos fuentes de evidencia:

1. **Una sesión real en el navegador** (alumna `3135`, curso `28053`, `semana_01`),
   entrando por LTI, ejecutando celdas en el cuadernillo y mirando la base.
2. **La suite reproducible** `backend/tests/telemetria/correr_todo.sh` (68 casos,
   tres tramos), corrida tres veces con el mismo resultado: 65 OK, 3 FALLO. Los tres
   fallos son bugs del sistema, detallados abajo; la suite está hecha para seguir
   fallando hasta que se corrijan.

El mapa del flujo con evidencia de código (archivo:línea de cada endpoint, payload,
tabla y columna) está en la sección 6. Nada del comportamiento se modificó: las
correcciones se proponen, no se aplican.

## 1. Resumen por tramo

| Tramo | Estado | Evidencia |
|---|---|---|
| Cuadernillo → `custom.js` captura el evento | **Funciona** | Sesión real: 3 intentos sobre `ejercicio_1` (stub → incorrecto → correcto) produjeron 3 POST con `validation_result` `failed`, `failed`, `passed` y `errors[]` de 2, 1 y 0. Suite `prueba_customjs.js`: 14/14. |
| `custom.js` → `metrics_bridge.py` (servidor del alumno) | **Funciona** (1 bug menor) | Sesión real: el puente respondió `204` a los tres. Suite `prueba_puente.sh`: 19/20; autenticación correcta (página ajena → 403), identidad del cuerpo sobrescrita por la del servidor. El fallo: JSON válido pero no objeto → 500 en vez de 400. |
| `metrics_bridge.py` → backend Go → PostgreSQL | **Funciona** en intentos; **falla aislamiento** en ratings | Sesión real: 3 filas en `exercise_attempts` (`3135`, `28053`, `semana_01`) con `attempt_at` del navegador, `received_at` del servidor, `puntos_maximos=3`, `codigo_celda`, `orden=79`, y 3 filas en `attempt_errors` enlazadas. Suite `prueba_backend.py`: 32/34; los dos fallos son el mismo bug: `POST /api/cuadernillos/ratings` guarda el `student_id`/`course_id` que manda el cuerpo. |
| PostgreSQL → `/api/mi-progreso` → panel del alumno | **Funciona** | Sesión real: el panel de Ana muestra «Vas por 1 de 1 · Nota 3/25». Suite: un alumno solo ve lo suyo (casos 8a–8g). |
| PostgreSQL → `/internal/curso/:curso/panel` → panel del docente | **Funciona**, con una salvedad de diseño | Sesión real: «3 intentos registrados de 1 estudiante», malentendido `AssertionError` de `ejercicio_1`. Suite: cada curso solo devuelve sus alumnos (9a, 9b), pero el token del docente no está acotado a un curso (9e). |
| Aislamiento entre alumnos (dos contenedores) | **Funciona en lectura e intentos; falla en ratings** | 40 intentos simultáneos de A y B → 20 y 20, cero cruzados (caso 10). Un alumno puede escribir el rating de otro (7b). |
| Zona horaria | **Funciona** | `23:59:59-05:00` y `00:00:01-05:00` quedan como `04:59:59Z` y `05:00:01Z`; `at time zone 'America/Bogota'` devuelve días 22 y 23 (casos 6.0, 6.1). Todas las columnas son `TIMESTAMPTZ`, todos los contenedores en UTC. |

## 2. Dónde se pierde o corrompe información

| Punto del flujo | Qué pasa | Evidencia |
|---|---|---|
| **Backend** (`cuadernilloRatingHandler.go:29-37`) | La identidad del rating sale del cuerpo, no del token. Un alumno con su propio token puede escribir o pisar (UPSERT) el rating de un compañero o de otro curso. | Suite 7b: token de `PRUEBA-A` + `student_id=PRUEBA-B` → `201`, fila bajo `PRUEBA-B` con `comment='suplantado'`. 7c: `course_id=PRUEBA-C2` → fila en C2. |
| **Navegador** (`custom.js:78-88`, `:440`, `:481-482`) | No mira `resp.ok`, no reintenta; el buffer de errores se vacía antes de enviar. Un 400/403/502 del puente pierde el intento y sus errores en silencio. | Suite customjs 10 y puente auth.1: sin cookie `_xsrf` la cabecera viaja vacía, el puente responde 403 y el navegador no se entera. Fue la causa del commit `502ca9d`. |
| **Navegador** (`custom.js:275`) | La tarjeta de valoración del cuadernillo nunca se ofrece: `verificar_finalizacion_cuadernillo` evalúa la última celda de prueba cuando su `input_prompt_number` todavía es `'*'`. `cuadernillo_ratings` quedará vacía en producción. | Suite customjs 6a (con `'*'` no aparece) vs 6b (con número sí aparece y el POST sale bien). Confirma AUDITORIA 6.6. |
| **Puente** (`metrics_bridge.py:34-42`, `:89`) | `cuadernillo_id` se estampa con el activo al arrancar el contenedor, no con el notebook abierto; el navegador no manda cuál es. Si el alumno abre un cuadernillo anterior, sus intentos se atribuyen al de esta semana. | Suite customjs 9 (el payload no lleva notebook) + backend 2 (`cuadernillo_id` viene del cuerpo). El claim `nbid` del token existe y nadie lo lee (`metricsauth.go:57`). Confirma AUDITORIA 6.1. |
| **Puente** (`metrics_bridge.py:80-89`) | JSON válido que no es objeto (`[1,2,3]`) → `AttributeError` → 500 con traceback en el log. | Suite puente d2. |
| **Backend** (`exerciseHandler.go:31-36`, `:90-98`) | `errors[].timestamp` ausente se guarda como `0001-01-01`; `rating` fuera de 1..5 da 500 (lo para el CHECK de la base, no Go). | Suite 6.ts y 7d. Solo alcanzable con clientes a mano; `custom.js` siempre los manda. |
| **Backend** (`panelDocenteRepository.go:204,212`) | `horas_desde_ultima_actividad` mezcla el reloj del navegador (`attempt_at`) con `now()` de la base: puede salir negativa. | Suite 9a: `-0.79` h con `attempt_at` futuros (el valor depende del reloj al correr). `received_at` sería la referencia fiable. |
| **Descartado por diseño** | `errors[].traceback` no tiene columna y se descarta (`attempt_errors` = id, attempt_id, cell_id, error_type, error_message, occurred_at). Los errores en celdas sin metadata nbgrader (exploración) no se capturan. | Suite 3b y customjs 5. Ya estaba en PENDIENTES 2.3. |

No se encontró pérdida ni corrupción en el camino principal intento → fila.

## 3. Discrepancias entre lo que el código dice y lo que hace

- `metricsauth.go:13-14`: «Los handlers la leen de aquí y no del cuerpo». `cuadernilloRatingHandler.go` no lo hace.
- `exerciseHandler.go:63-66`: «la identidad sale del token, no del cuerpo». Cierto para `student_id`/`course_id`; `cuadernillo_id` (`:79`) sale del cuerpo y el claim `Cuadernillo` es código muerto.
- `tokenmaestro.go:16`: el maestro «nunca sale de la red interna de Docker». `docker-compose.yml` publica `8080:8080` en el host y `api_go` comparte `moodle_jupyter_net` con los contenedores de alumnos (en la VM el firewall de GCP lo tapa desde fuera, no desde dentro).
- `custom.js:204-210` documenta el problema del prompt `'*'` y lo resuelve para el intento (`recien_ejecutada`), pero `:275` lo reintroduce para la finalización.
- `CONTRATO_JSON_BACKEND.md` describe eventos y tablas (`resultado_ejercicio`, `telemetria_ejercicios`, `/public/metrics/evento`, `/internal/metrics`) que no existen; el Hub todavía exporta `STUDENT_METRICS_API_URL` y `METRICS_API_URL` con esas rutas y nadie las usa. Es histórico, pero es lo primero que lee quien llega.

## 4. Aislamiento: respuesta explícita

**¿Un estudiante puede ver datos de otro estudiante?** No. `GET /api/mi-progreso`
toma `student_id` y `course_id` exclusivamente de los claims firmados (HMAC-SHA256
con `METRICS_TOKEN_SECRET`, que el alumno no tiene). Sin token → 401; firma
manipulada → 401; claims reescritos con la firma de otro → 401; `?student_id=`
en la query se ignora; el panel del docente con token de alumno → 401. Dos alumnos
escribiendo a la vez no se cruzan. **Salvedad:** sí puede *escribir* el rating de
otro (bug 1). No puede leerlo.

**¿Un profesor puede ver datos fuera de su curso?** Sí. El panel del docente usa
`METRICS_API_TOKEN`, el token maestro, que es el mismo para todo instructor o TA
de cualquier curso del Hub (`jupyterhub_config.py`, rama instructor) y que no
lleva curso: con él se lee `/internal/curso/<cualquiera>/panel`, se acuñan tokens
de cualquier alumno y se suben notas de cualquier curso. Cada consulta sí filtra
por el curso de la URL (un docente no *mezcla* cursos por accidente), pero nada le
impide pedir otro. Mientras el AVA tenga un solo curso es inocuo; con dos, no.

## 5. Bugs confirmados y corrección propuesta (no aplicada)

| # | Severidad | Dónde | Corrección propuesta |
|---|---|---|---|
| 1 | **Alta** | `backend/internal/handler/cuadernilloRatingHandler.go:29-37` | Tras el bind: `studentID, courseID := middleware.IdentidadVerificada(c)` y usarlos si no vienen vacíos, como hace `exerciseHandler.go:68-74`. El puente ya manda la identidad correcta, así que el flujo normal no cambia. |
| 2 | **Alta** | `notebook/custom.js:275` | `verificar_finalizacion_cuadernillo(celda_recien_ejecutada)` y evaluar con `evaluar_celda(cell, cell === celda_recien_ejecutada)`; pasar la celda desde `:455`. |
| 3 | Media | `notebook/custom.js:78-88`, `:440`, `:481-482` | Comprobar `resp.ok`; si falla, reponer los errores en el buffer o encolar el payload en `localStorage` y reintentar en el siguiente evento; avisar en consola con el código HTTP. |
| 4 | Media (diseño) | `tokenmaestro.go`, `panelDocenteHandler.go:31-34`, `jupyterhub_config.py` rama instructor, `docker-compose.yml` (`ports: 8080:8080`) | Acuñar un token de docente con claim de curso y compararlo con `:curso`; `expose` en vez de `ports` para 8080 en producción. |
| 5 | Media | `metrics_bridge.py:34-42`, `:89`; `custom.js` | Que `custom.js` mande `notebook_path` y el puente lo use como `cuadernillo_id` cuando sea uno de los publicados del curso (el dato ya está a mano: `custom.js:554-556`). |
| 6 | Baja | `metrics_bridge.py:80` | `if not isinstance(evento, dict): 400`. |
| 7 | Baja | `cuadernilloRatingHandler.go:20-27`, `exerciseHandler.go:90-98` | Validar `1 <= rating <= 5` y `!timestamp.IsZero()` → 400. |
| 8 | Baja | `panelDocenteRepository.go:204,212` | Usar `received_at` (reloj del servidor) o `GREATEST(0, …)`. |
| 9 | Baja | `metricsauth.go:30-37` | Con `METRICS_TOKEN_SECRET` vacío la ingesta acepta cualquier identidad (deliberado, PENDIENTES §5). Mejor negarse a arrancar. |

## 6. El flujo, con evidencia de código

```
custom.js ──POST {base_url}nbgrader-metrics/evento (cookie de sesión + X-XSRFToken; beacon: ?_xsrf=)──▶
metrics_bridge.py ──POST http://api_go:8080/api/exercises/attempts | /api/cuadernillos/ratings (Bearer STUDENT_METRICS_TOKEN)──▶
Go: RequireMetricsToken → exerciseHandler / cuadernilloRatingHandler → INSERT exercise_attempts + attempt_errors (tx) | UPSERT cuadernillo_ratings ──▶ PostgreSQL
PostgreSQL ◀── GET /api/mi-progreso (Bearer STUDENT_METRICS_TOKEN) ◀── panel_bridge.py (GET /user/<x>/panel)
PostgreSQL ◀── GET /internal/curso/:curso/panel (Bearer METRICS_API_TOKEN) ◀── panel_docente_bridge.py (GET /user/<docente>/panel-docente)
```

**Captura (`notebook/custom.js`).** Hooks `execute.CodeCell` y `finished_execute.CodeCell`
(`:490-491`) y `beforeunload` (`:487`). Celda de prueba = `metadata.nbgrader.grade === true`
con `grade_id` (`:25-28`); de solución = `solution === true` (`:33-36`); `exercise_id` =
`grade_id` sin `test_` (`:47-49`). `passed` = la celda de prueba corrió sin output de tipo
`error` (`:211-222`). Cada error (solución o prueba) se acumula en `errors[]` con
`cell_id`, `timestamp`, `error_type`, `error_message`, `traceback` (`:243-255`), y se manda
entero al ejecutar la prueba:

```json
{"tipo_evento":"exercise_attempt","exercise_id":"ejercicio_1","codigo_celda":"test_ejercicio_1",
 "orden":79,"puntos_maximos":3,"attempt_at":"2026-08-23T03:57:03.560Z","validation_result":"failed",
 "errors":[{"cell_id":"ejercicio_1","timestamp":"…","error_type":"NotImplementedError","error_message":"…","traceback":"…"},
           {"cell_id":"test_ejercicio_1","timestamp":"…","error_type":"AssertionError","error_message":"…","traceback":"…"}]}
```

(capturado en la sesión real). Al cerrar la pestaña, los ejercicios con errores y sin
prueba ejecutada van por `navigator.sendBeacon` como `sin_validar`, sin `codigo_celda`,
`orden` ni `puntos_maximos` (`:466-483`). El rating va como
`{"tipo_evento":"cuadernillo_rating","rating":4,"comment":null,"submitted_at":"…"}` (`:298-303`).
Estado en `localStorage['nbgrader-metrics:' + notebook_path]` (`:167-170`). El navegador
**no** manda identidad ni cuadernillo.

**Puente (`notebook/metrics_bridge.py`).** `POST {base_url}/nbgrader-metrics/evento`
(`:156-159`), `JupyterHandler` + `@web.authenticated` (`:77-78`); el xsrf lo verifica
jupyter_server (cabecera o `?_xsrf`; `Authorization: token` lo salta). Impone
`student_id=ALUMNO_ID`, `course_id=CURSO_ID`, `cuadernillo_id=CUADERNILLO_CODIGO`,
`student_name`, `student_email` con `evento.update(IDENTIDAD)` (`:34-42`, `:89`); quita
`tipo_evento` (`:93`) y rutea `exercise_attempt → /api/exercises/attempts`,
`cuadernillo_rating → /api/cuadernillos/ratings` (`:45-48`) con `Bearer STUDENT_METRICS_TOKEN`
y timeout 5 s (`:124-136`). Respuestas: 204 OK, 400 json/tipo, 503 sin token, 502 red o
rechazo del backend; con `ENVIAR_AL_BACKEND=false` solo loguea y responde 200 `simulado`.

**Backend (`backend/internal/server/router/route.go`).** `POST /internal/lti/mint-metrics-token`,
`/internal/competencias`, `/internal/notas`, `GET /internal/curso/:curso/panel` bajo
`RequireTokenMaestro`; `POST /api/exercises/attempts`, `POST /api/cuadernillos/ratings`,
`GET /api/mi-progreso`, `POST /api/exercise/tutorIA` bajo `RequireMetricsToken`. El token
es `base64url(claims).base64url(HMAC-SHA256)` con claims `{sid, cid, nbid, exp}`, 24 h
(`auth/metricstoken.go`). `exerciseHandler.go:68-74` toma `student_id`/`course_id` de los
claims; inserta en transacción (`exerciseAttempsRepository.go:22-46`):

```sql
INSERT INTO exercise_attempts (id, course_id, cuadernillo_id, exercise_id, student_id, attempt_at,
  validation_result, received_at, puntos_maximos, codigo_celda, orden) VALUES (…);
INSERT INTO attempt_errors (id, attempt_id, cell_id, error_type, error_message, occurred_at) VALUES (…);  -- por error
```

**Identidad.** LTI 1.1 (`username_key = lis_person_contact_email_primary`) →
`auth_state` → `auth_state_a_env` exporta `ALUMNO_ID = user_id` (numérico), `CURSO_ID =
context_id`, y acuña `STUDENT_METRICS_TOKEN` con `{sid: user_id, cid: context_id}`
(`jupyterhub_config.py`, `_mintear_token_estudiante`). `cuadernillo_id` lo fija
`entregar-cuadernillo` al arrancar (`entrypoint.sh`) → `CUADERNILLO_CODIGO`. En la base:
`student_id='3135'`, `course_id='28053'`, `cuadernillo_id='semana_01'` — la misma clave
con la que nbexchange archiva la entrega y `registrar-notas` sube la nota.

**Base (`database/schema_v2.sql`).** `exercise_attempts` (id, course_id, cuadernillo_id,
exercise_id, student_id, `attempt_at TIMESTAMPTZ`, validation_result ∈ passed/failed/sin_validar,
`received_at TIMESTAMPTZ DEFAULT now()`, puntos_maximos, codigo_celda, orden),
`attempt_errors` (id, attempt_id FK CASCADE, cell_id, error_type, error_message,
`occurred_at TIMESTAMPTZ`), `cuadernillo_ratings` (UNIQUE course/cuadernillo/student),
`competencias`, `ejercicio_competencias`, `cuadernillo_notas`. `attempt_at` y
`occurred_at` los pone el navegador; `received_at` y `calificado_en`, el servidor.

## 7. Cómo repetirlo

```sh
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build   # stack local
backend/tests/telemetria/correr_todo.sh                                           # 68 casos, ~2.5 min
```

Ver `backend/tests/telemetria/README.md`. La sesión real del navegador se repite con
`nbexchange/pruebas/lti_falso.py` (lanzamientos LTI firmados) siguiendo
`nbexchange/pruebas/README.md`.
