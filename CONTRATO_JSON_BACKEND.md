# Contrato JSON: JupyterHub → Backend Go

Mapeo exacto de los JSON que emite el lado de Jupyter contra `database/schema.sql`.
Complementa a `ENDPOINTS_BACKEND.txt` (endpoints y consideraciones). Aquí está el
**campo → columna** para que el backend se escriba sin adivinar.

> Estado actual: `ENVIAR_AL_BACKEND=false` → los eventos se **imprimen** en el log
> del contenedor, no salen a la red. Para ver los JSON reales:
> `docker logs -f <contenedor>` y buscar `Evento capturado`.

---

## Evento 1 — `resultado_ejercicio`  → tabla `telemetria_ejercicios`

**Origen:** `custom.js` (navegador) → `metrics_bridge.py` lo enriquece con la
identidad → `POST /public/metrics/evento`.
**Cuándo:** cada vez que el alumno ejecuta una **celda de prueba** (`grade: true`).

```jsonc
{
  "tipo_evento":       "resultado_ejercicio",   // discriminador (no va a BD)
  "codigo_celda":      "test_ejercicio_1",       // -> codigo_celda
  "codigo_ejercicio":  "ejercicio_1",            // -> codigo_ejercicio  (llave de negocio)
  "orden":             5,                          // -> orden (posición de la celda)
  "puntos_maximos":    5,                          // -> puntos_maximos
  "descripcion":       "test_ejercicio_1",        // -> descripcion
  "timestamp":         "2026-07-25T21:10:00.000Z",// -> timestamp
  "primer_intento":    "2026-07-25T21:06:00.000Z",// -> primer_intento
  "num_intentos":      3,                          // -> num_intentos
  "duracion_segundos": 240.5,                      // -> duracion_segundos
  "exito":             false,                      // -> exito
  "tipo_error":        "TypeError",                // -> tipo_error   (¡el error REAL del alumno!)
  "mensaje":           "TypeError: can only concatenate str (not \"int\") to str",
  "traceback":         "Traceback (most recent call last)...",  // -> traceback (sin ANSI)

  // --- añadidos por metrics_bridge.py desde el entorno del contenedor ---
  "estudiante_id":     "lti-user-123",   // -> estudiante_id  + upsert en `estudiantes`
  "nombre_completo":   "Ana Pérez",      // -> `estudiantes`.nombre_completo
  "correo":            "ana@uni.edu",    // -> `estudiantes`.correo
  "curso_id":          "curso-abc",      // -> curso_id
  "cuadernillo_codigo":"semana_1"        // -> cuadernillo_codigo
}
```

**Novedad importante (fix de esta semana):** `tipo_error/mensaje/traceback` ahora
traen el error de la **celda de solución del alumno** (su error real). Antes solo
llegaba el error de la celda de prueba (casi siempre el mismo `AssertionError`).
Si el alumno se equivoca en su código, ese es el error que se envía; solo si su
código corre limpio pero la lógica falla, se envía el `AssertionError` del test.

**Antes de insertar, el backend debe garantizar las filas padre (FKs):**
1. `cursos(curso_id)` — upsert.
2. `estudiantes(estudiante_id, nombre_completo, correo)` — upsert.
3. `cuadernillos(curso_id, cuadernillo_codigo)` — upsert.
4. `ejercicios(curso_id, cuadernillo_codigo, codigo_ejercicio, codigo_celda, orden, descripcion, puntos_maximos)` — upsert (los datos del ejercicio vienen en este mismo evento).
5. Recién ahí, `INSERT` en `telemetria_ejercicios` (append-only, un registro por corrida).

---

## Evento 2 — `intento_cuadernillo_completado`  → tabla `intentos_cuadernillo`

**Origen:** `custom.js` cuando TODOS los ejercicios quedan aprobados.
Se emite **una sola vez** por navegador (flag en localStorage), pero trátalo como
idempotente igual (otro navegador puede reenviarlo).

```jsonc
{
  "tipo_evento":    "intento_cuadernillo_completado",
  "estado":         "terminado",                  // -> estado
  "fecha_fin":      "2026-07-25T21:30:00.000Z",   // -> fecha_fin
  "puntaje_total":  10,                            // -> puntaje_total
  "puntaje_maximo": 10,                            // -> puntaje_maximo
  // + identidad (estudiante_id, curso_id, cuadernillo_codigo, nombre_completo, correo)
}
```

La tabla tiene `UNIQUE (curso_id, cuadernillo_codigo, estudiante_id)`. Usa **UPSERT**
y conserva la `fecha_fin` original:
```sql
INSERT ... ON CONFLICT (curso_id, cuadernillo_codigo, estudiante_id)
DO UPDATE SET fecha_fin = LEAST(intentos_cuadernillo.fecha_fin, EXCLUDED.fecha_fin),
              puntaje_total = EXCLUDED.puntaje_total;
```

---

## Evento 3 — Exportación nbgrader  → `notas_oficiales_cuadernillo` + `notas_oficiales_ejercicios`

**Origen:** `plugins/api_export.py` (contenedor del **instructor**) cuando el
profesor corre `nbgrader export` → `POST /internal/metrics`.
**Auth:** `METRICS_API_TOKEN` (token de servicio, NO el del alumno).

```jsonc
{
  "curso_id":           "curso-abc",     // -> notas_oficiales_cuadernillo.curso_id
  "cuadernillo_codigo": "semana_1",      // -> cuadernillo_codigo
  "estudiante_id":      "lti-user-123",  // -> estudiante_id
  "estado":             "terminado",     // -> estado
  "fecha_fin":          "2026-07-25 21:30:00",  // -> fecha_fin  (str de nbgrader, NO ISO)
  "puntaje_total":      8.0,             // -> puntaje_total
  "puntaje_maximo":     10.0,            // -> puntaje_maximo
  "ejercicios": [                        // -> N filas en notas_oficiales_ejercicios
    {
      "codigo_celda":     "test_ejercicio_1",  // -> codigo_celda
      "codigo_ejercicio": "ejercicio_1",       // -> codigo_ejercicio
      "orden":            1,                    // -> orden
      "descripcion":      "test_ejercicio_1",  // -> descripcion
      "puntos_obtenidos": 5.0,                 // -> puntos_obtenidos
      "puntos_maximos":   5.0,                 // -> puntos_maximos
      "aprobado":         true                 // -> aprobado
    }
  ]
}
```

Header → `notas_oficiales_cuadernillo` con **UPSERT** sobre
`UNIQUE (curso_id, cuadernillo_codigo, estudiante_id)`; cada ejercicio →
`notas_oficiales_ejercicios` con `nota_cuadernillo_id` de la fila padre.

---

## Notas de consistencia para el backend

- **`codigo_ejercicio` es la llave que cruza todo.** Telemetría y exportación
  mandan el MISMO valor (`ejercicio_1`, sin prefijo `test_`). Úsala como llave de
  negocio en `ejercicios`.
- **`orden` difiere entre fuentes.** En telemetría es la posición de la celda en el
  notebook; en la exportación es el índice de la nota nbgrader (1,2,3...). Toma el
  de la **exportación** como canónico para `ejercicios.orden`.
- **Telemetría vs. nota oficial son cosas distintas.** La telemetría dice "la celda
  corrió sin error"; nbgrader dice "vale 5/5 tras autograding". Van a tablas
  separadas a propósito (`telemetria_*` vs `notas_oficiales_*`). Para calificar,
  manda nbgrader.
- **Idempotencia:** `telemetria_ejercicios` es append-only; `intentos_cuadernillo` y
  `notas_oficiales_cuadernillo` son UPSERT por sus constraints UNIQUE.

---

## Decisiones de arquitectura resueltas

### 1. Activación del cuadernillo: nbgrader vs. backend

**Decisión: nbgrader es dueño del CONTENIDO y la CALIFICACIÓN; el backend es dueño
de la ACTIVACIÓN (puntero) y el ACCESO (token). No compiten.**

- El instructor autora en `source/<assignment>/` y hace **Generate** (produce
  `release/` sin soluciones).
- El backend solo guarda un puntero: *"para el curso X, el activo es `semana_1`"*.
  No define el contenido del notebook.
- En el spawn, el hub pregunta el activo (`/internal/cursos/{id}/cuadernillo-activo`),
  entrega ese cuadernillo y mintea el token scoped a él.
- Telemetría y notas usan la misma llave: el nombre del assignment = `cuadernillo_codigo`.

**Pendiente de decidir (entrega del notebook al alumno):** como el alumno ya no
monta `/srv/nbgrader` (seguridad), hay dos opciones para hacerle llegar la versión
`release/`:
- **(a) corto plazo:** copiar en el spawn solo `release/<activo>/<nb>` al `work/` del
  alumno (seguro, no tiene soluciones).
- **(b) a futuro:** el backend guarda/sirve la versión release y el alumno la baja
  con su token.

Hoy, sin backend, el alumno recibe el cuadernillo estático que viene en la imagen.
Cuando exista el backend, implementar (a).

### 2. ¿Eliminar el número de intentos por cuadernillo?

**Sí — y el esquema ya lo refleja.** `intentos_cuadernillo` NO tiene columna de
intentos; los intentos solo existen a nivel **ejercicio** (`telemetria_ejercicios.num_intentos`).
Es lo correcto: "intentos de un ejercicio" (cuántas veces corriste el test) es señal
real; "intentos de un cuadernillo entero" es ambiguo. El cuadernillo se modela con
estado + `fecha_fin` + puntaje, no con un contador.
