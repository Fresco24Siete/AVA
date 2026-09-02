# API del backend y esquema de la base

Backend en Go (`module proxy-go`), Gin + sqlx sobre PostgreSQL 16. Punto de
entrada: `backend/cmd/api/main.go`. Rutas: `backend/internal/server/router/route.go`.

El servicio **no publica puerto al exterior**: solo se le llega por la red
interna de Docker, como `api_go:8080`.

## 1. Autenticación

Tres niveles, con tres middlewares distintos.

| Grupo | Middleware | Quién lo usa |
|---|---|---|
| `/internal` (hub) | `RequireTokenMaestro` | Solo el Hub, con `METRICS_API_TOKEN` |
| `/internal` (docente) | `RequireMaestroODocente` | El Hub o un token con `rol=docente` |
| `/api` | `RequireMetricsToken` | El contenedor de cada persona |

Todos esperan `Authorization: Bearer <token>`.

### El token de métricas

Lo acuña el backend y lo pide el Hub en cada spawn. Formato propio, no JWT:
`base64url(claims JSON) + "." + base64url(HMAC-SHA256)`. Definido en
`backend/internal/auth/metricstoken.go`:

```go
type Claims struct {
	EstudianteID string `json:"sid"`
	CursoID      string `json:"cid"`
	Cuadernillo  string `json:"nbid,omitempty"`
	Rol    string `json:"rol,omitempty"`
	Expira int64  `json:"exp"`
}

const DuracionPorDefecto = 24 * time.Hour
const RolDocente = "docente"
```

Errores que devuelve la verificación: `ErrTokenMalFormado`, `ErrFirmaInvalida`,
`ErrTokenExpirado`, `ErrSinSecreto`.

> **La identidad sale del token, no del cuerpo.** Los handlers llaman a
> `middleware.IdentidadVerificada(c)` y solo caen al cuerpo si el token no traía
> identidad —lo que ocurre si `METRICS_TOKEN_SECRET` está vacío—. Con el secreto
> configurado, un alumno **no puede** escribir a nombre de otro aunque manipule
> el JSON.

### CORS

```go
origenes := []string{}
for _, o := range strings.Split(os.Getenv("CORS_ORIGENES"), ",") { ... }
if len(origenes) == 0 {
    if d := strings.TrimSpace(os.Getenv("AVA_DOMINIO")); d != "" {
        origenes = append(origenes, "https://"+d)
    }
}
```

Sin orígenes configurados **no se monta CORS**: es más seguro no responder
cabeceras de permiso que responderlas con un dominio equivocado. No afecta a la
telemetría, que va de contenedor a contenedor sin navegador.

## 2. Endpoints

### `/internal` — solo el Hub

#### `POST /internal/lti/mint-metrics-token`

Acuña un token acotado a una persona y un curso.

```json
{
  "estudiante_id": "3135",
  "curso_id": "36074",
  "cuadernillo_codigo": "semana_01",
  "rol": "docente"
}
```

`rol` es opcional; con `"docente"` el token abre además las rutas de `/internal`
de **ese** curso.

| Código | Cuándo |
|---|---|
| `200` | Devuelve el token |
| `400` | Cuerpo inválido |
| `401` | Falta o no cuadra el token maestro |
| `500` | `METRICS_TOKEN_SECRET` sin configurar |

#### `POST /internal/lti/ingreso`

Registra quién entró. Lo llama el Hub en cada lanzamiento, antes de acuñar el
token. Alimenta la tabla `estudiantes`: nombre, correo, rol, y los dos datos LTI
que hacen falta para devolver la nota (`lis_result_sourcedid`,
`lis_outcome_service_url`). Es un UPSERT que además incrementa `ingresos` y
mueve `ultimo_ingreso`.

### `/internal` — el Hub o un docente

#### `POST /internal/competencias`

Carga el mapeo ejercicio → competencia (`ejercicio_competencias`). Lo genera
`build.py` en `notebook/cuadernillos/competencias.json` y lo sube el comando
`cargar-competencias`.

> Falla con error de clave foránea si la tabla `competencias` está vacía. Por
> eso el catálogo de los siete indicadores va sembrado en `schema_v2.sql`, no
> solo en la migración.

#### `POST /internal/notas`

Registra la nota oficial de un cuadernillo, la que sale de nbgrader tras
*Autograde*. UPSERT sobre `(course_id, cuadernillo_id, student_id)`: recalificar
no duplica.

#### `GET /internal/curso/:curso/panel`

Los datos del panel del docente: progreso del curso, errores por competencia,
notas y valoraciones.

#### `GET /internal/curso/:curso/estudiante/:estudiante`

La ficha de una persona.

### `/api` — el contenedor de cada persona

#### `POST /api/exercises/attempts`

El intento de un ejercicio, con todos sus errores. Es el corazón de la
telemetría. Estructura en `backend/internal/handler/exerciseHandler.go`:

```go
type ExerciseAttemptRequest struct {
	CourseID         string                `json:"course_id"`
	CuadernilloID    string                `json:"cuadernillo_id"`
	ExerciseID       string                `json:"exercise_id"`
	StudentID        string                `json:"student_id"`
	AttemptAt        time.Time             `json:"attempt_at"`
	ValidationResult string                `json:"validation_result"`
	PuntosMaximos    *int16                `json:"puntos_maximos"`
	CodigoCelda      *string               `json:"codigo_celda"`
	Orden            *int16                `json:"orden"`
	Errors           []AttemptErrorRequest `json:"errors"`
}

type AttemptErrorRequest struct {
	CellID       string    `json:"cell_id"`
	Timestamp    time.Time `json:"timestamp"`
	ErrorType    string    `json:"error_type"`
	ErrorMessage string    `json:"error_message"`
}
```

`validation_result` acepta `passed`, `failed` y `sin_validar`.

> **`sin_validar` es un desenlace real, no un valor raro.** Lo manda `custom.js`
> al cerrar la pestaña cuando el alumno dejó errores en un ejercicio **sin
> llegar a ejecutar la celda de prueba**. Es la señal de abandono: se atascó y
> se rindió. Antes el CHECK y el backend lo rechazaban con 400 y ese evento se
> perdía, así que un alumno que luchó media hora y otro que ni abrió el
> ejercicio se veían igual.

| Código | Cuándo |
|---|---|
| `201` | Guardado |
| `400` | JSON inválido o `validation_result` fuera de la lista |
| `401` | Token ausente, mal firmado o expirado |
| `500` | Fallo al guardar |

#### `POST /api/cuadernillos/ratings`

La valoración del cuadernillo que hace el alumno. **No es una nota**: es su
opinión, de 1 a 5. Handler en `cuadernilloRatingHandler.go`.

Validaciones explícitas, y el motivo está en el código:

```go
// El rango lo imponía solo el CHECK de la base, que aquí se veía como un
// 500 sin explicación.
if input.Rating < 1 || input.Rating > 5 { ... }
if input.CuadernilloID == "" || input.SubmittedAt.IsZero() { ... }
if input.Tiempo != nil && (*input.Tiempo < 1 || *input.Tiempo > 4) { ... }
if input.Freno != nil && !frenoValido(*input.Freno) { ... }
```

`freno` es una lista cerrada a propósito —`enunciado`, `concepto`, `sintaxis`,
`error`, `tiempo`, `nada`— porque cada valor es una acción distinta del docente.
Un campo de texto libre aquí no sería agregable.

`submitted_at` es **obligatorio**. Sin él la respuesta es `400` y la valoración
se pierde: es un fallo que ya ocurrió en producción.

| Código | Cuándo |
|---|---|
| `201` | Guardado (UPSERT: revalorar no duplica) |
| `400` | Rating fuera de 1–5, falta `cuadernillo_id` o `submitted_at`, `tiempo` fuera de 1–4, `freno` fuera de la lista |
| `401` | Token inválido |
| `500` | Fallo al guardar (queda en el log del backend) |

#### `GET /api/mi-progreso`

Lo que el panel del alumno pinta: sus cuadernillos, su avance y su nota cuando
ya está calificada. La identidad sale del token.

#### `POST /api/exercise/tutorIA`

El tutor. Consume cuota de Gemini, por eso exige token: desde una celda se podía
llamar en bucle sin identificarse. El límite de cinco preguntas por cuadernillo
lo cuenta `tutor_bridge` usando `CUADERNILLO_CODIGO`.

Sin `GOOGLE_API_KEY_1` / `_2` responde `503`.

> **Inconsistencia de nombres.** Esta ruta es `/api/exercise/tutorIA`, en
> singular, mientras las otras son plurales (`/api/exercises/attempts`,
> `/api/cuadernillos/ratings`). No rompe nada, pero conviene saberlo antes de
> escribir un cliente de memoria.

## 3. Esquema de la base

Definido en `database/schema_v2.sql`. Migraciones incrementales en
`migracion_v2.sql`, `v3` y `v4`.

> **`database/schema.sql` (v1) está en el repositorio pero NO se usa.** El
> compose monta `schema_v2.sql`. El v1 quedó como traza histórica.

### La idea de diseño

Curso, cuadernillo, ejercicio y estudiante **no son entidades propias**: viven en
Moodle y en nbgrader, y aquí se referencian por su código. Lo que sí vive aquí
son los **eventos** y el **mapeo** de diseño del curso.

### `exercise_attempts` — cada validación

| Columna | Tipo | Nota |
|---|---|---|
| `id` | `UUID` | `gen_random_uuid()` |
| `course_id` | `VARCHAR(255)` | el `context_id` de LTI |
| `cuadernillo_id` · `exercise_id` | `VARCHAR(255)` | |
| `student_id` | `VARCHAR(255)` | el `user_id` de LTI |
| `attempt_at` | `TIMESTAMPTZ` | lo sella el **navegador** |
| `validation_result` | `VARCHAR(12)` | CHECK: `passed`, `failed`, `sin_validar` |
| `received_at` | `TIMESTAMPTZ` | `DEFAULT now()` — lo sella el **backend** |
| `puntos_maximos` | `SMALLINT` | sin esto no se puede calcular una nota desde la base |
| `codigo_celda` | `VARCHAR(255)` | `test_ejercicio_3` |
| `orden` | `SMALLINT` | posición en el cuadernillo |

Índices: `(course_id, cuadernillo_id, exercise_id)` y `(student_id, cuadernillo_id)`.

### `attempt_errors` — los errores de cada intento

`attempt_id` con `ON DELETE CASCADE`. No lleva columna de competencia: se
resuelve por JOIN, y ese es el punto del diseño.

> **Nombre distinto a cada lado.** El navegador y el handler lo llaman
> `timestamp`; la columna se llama `occurred_at`. El `struct` de Go hace de
> traductor (`Timestamp time.Time` con `db:"occurred_at"`). No es un fallo, pero
> confunde al leer los dos lados seguidos.

### `cuadernillo_ratings` — la opinión del alumno

`UNIQUE (course_id, cuadernillo_id, student_id)`. `rating` 1–5, `tiempo` 1–4,
`freno` en lista cerrada. `entregado` y `origen` **las pone el servidor**, no el
alumno.

### `competencias` y `ejercicio_competencias`

Los siete indicadores del microcurrículo (`I1`…`I7`) y el mapeo. Clave compuesta
`(cuadernillo_id, exercise_id, competencia_id)`: un ejercicio puede cubrir
varias competencias.

### `cuadernillo_notas` — la nota real

`UNIQUE (course_id, cuadernillo_id, student_id)` permite recalificar sin
duplicar. `origen` distingue `nbgrader` (la oficial) de `provisional` (la
calculada de la telemetría, que el alumno ve antes de que el docente califique).

> Distinguirlas evita el reclamo de «el panel decía otra cosa».

### `estudiantes` — quién es cada quien

La llena el Hub en cada ingreso. Sin ella el panel del docente solo podía
mostrar el `user_id` numérico. Guarda también `lis_result_sourcedid` y
`lis_outcome_service_url`, que solo viajan en el lanzamiento del alumno.

### `errores_por_competencia` — la vista que justifica todo

Responde «¿en qué competencia se está atascando?» sin necesidad de panel:

```sql
CREATE VIEW errores_por_competencia AS
SELECT a.course_id, a.cuadernillo_id, a.student_id,
       ec.competencia_id, c.descripcion,
       COUNT(*)                                                     AS intentos_totales,
       COUNT(*) FILTER (WHERE a.validation_result = 'failed')       AS intentos_fallidos,
       COUNT(*) FILTER (WHERE a.validation_result = 'sin_validar')  AS abandonos,
       COUNT(e.id)                                                  AS errores
FROM exercise_attempts a
JOIN ejercicio_competencias ec
       ON ec.cuadernillo_id = a.cuadernillo_id
      AND ec.exercise_id    = a.exercise_id
JOIN competencias c ON c.id = ec.competencia_id
LEFT JOIN attempt_errors e ON e.attempt_id = a.id
GROUP BY 1, 2, 3, 4, 5;
```

## 4. Zonas horarias

**Todas las columnas de tiempo son `TIMESTAMPTZ`.** PostgreSQL guarda un
instante absoluto en UTC y convierte a la zona de la sesión al leer, así que el
dato no es ambiguo aunque el servidor cambie de zona.

Hay **tres relojes distintos** y conviene no confundirlos:

| Columna | Quién la sella | Ojo con |
|---|---|---|
| `attempt_at` | el **navegador** del alumno | `new Date().toISOString()`. Si el reloj del portátil está desviado, este dato lo está |
| `received_at` | el **backend** | `time.Now()` del contenedor |
| `occurred_at` | el **navegador** | el momento del error |
| `submitted_at` | el **servidor del alumno** | se sella en `panel_bridge`, no en el navegador, porque el docente lo va a leer |

> **No hay `TZ` configurada en ningún servicio.** No hay ninguna en
> `docker-compose.yml` ni en los Dockerfiles, así que los contenedores corren en
> UTC. Como todo es `TIMESTAMPTZ` no se pierde información, pero un `SELECT`
> hecho a mano devuelve horas en UTC, no en `America/Bogota`. Para leerlas en
> hora local:
>
> ```sql
> SELECT attempt_at AT TIME ZONE 'America/Bogota' FROM exercise_attempts;
> ```

Y una consecuencia que sí muerde, fuera de la base: **Moodle firma cada
lanzamiento LTI con una marca de tiempo y el Hub rechaza las que se desvíen más
de 30 segundos**. Un reloj sin sincronizar se manifiesta como «no puedo entrar»
sin ninguna explicación. El instalador lo comprueba y lo arregla con
`timedatectl set-ntp true`.
