# Suite de telemetría

Prueba el camino completo de un evento, tramo por tramo:

```
custom.js (navegador) → metrics_bridge.py (servidor del alumno) → backend Go → PostgreSQL → /api/mi-progreso y /internal/curso/:curso/panel
   prueba_customjs.js        prueba_puente.sh                  prueba_backend.py
```

```sh
backend/tests/telemetria/correr_todo.sh          # los tres, con resumen y código de salida
```

Cada tramo corre solo:

| Script | Qué prueba | Contra qué | Dura |
|---|---|---|---|
| `prueba_customjs.js` (`node`) | `custom.js` real cargado en Node con un Jupyter simulado: qué captura, qué payload arma, cuándo manda el beacon, cuándo ofrece el rating. 14 casos. | nada (todo en memoria) | 1 s |
| `prueba_puente.sh` | `metrics_bridge.py` real dentro de un contenedor de la imagen del alumno, con un backend stub en el mismo contenedor: autenticación (cookie+xsrf, beacon, token, página ajena), identidad impuesta, ruteo, 204/400/502/503, simulación. 20 casos. | `mi_imagen_jupyterlab:latest`; sin red externa | ~2 min |
| `prueba_backend.py` | backend Go + PostgreSQL vivos: acuñado de tokens, `passed`/`failed`/`sin_validar`, intentos múltiples, medianoche Bogotá/UTC, rating, aislamiento de lectura y escritura, 40 intentos en paralelo, limpieza. 34 casos. | `localhost:8080` y `postgres-db` del compose local | 10 s |

Todo lo que escribe usa `course_id`/`student_id` con prefijo `PRUEBA-` y se borra al
terminar (y al empezar, por si una corrida anterior murió a medias). `correr_todo.sh`
cuenta las filas de las cuatro tablas antes y después y falla si cambiaron.

**Un FALLO en la suite es un bug del sistema, no de la prueba.** A 2026-08-22 fallan
tres casos, los tres bugs confirmados y documentados en `INFORME_TELEMETRIA.md`
(raíz del repo): el rating acepta la identidad del cuerpo (7b, 7c) y el puente
responde 500 a un JSON que no es objeto (d2). Cuando se corrijan, la suite debe pasar
entera sin tocarla.

## Variables

| Variable | Default | Uso |
|---|---|---|
| `API_BASE` | `http://localhost:8080` | backend Go |
| `PG_EXEC` | `docker exec -i postgres-db psql -U $DB_USER -d $DB_NAME -At` | comando que recibe SQL por stdin |
| `METRICS_API_TOKEN`, `METRICS_TOKEN_SECRET`, `DB_USER`, `DB_NAME` | se leen de `.env` | el backend debe correr con esos mismos valores |
| `ENV_FILE` | `<repo>/.env` | de dónde leer lo anterior si no está en el entorno |

Requiere el esquema `database/schema_v2.sql` y el backend con `METRICS_TOKEN_SECRET` y
`METRICS_API_TOKEN` configurados (con el secreto vacío la ingesta no verifica identidad
y los casos de aislamiento no significan nada).
