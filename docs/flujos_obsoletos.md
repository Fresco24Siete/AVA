# Flujos obsoletos (Fase 2)

Qué se retiró, por qué, desde cuándo y qué lo reemplaza. **Nada se ha borrado**:
todo queda comentado o marcado, y solo se eliminará cuando se confirme que
ninguna referencia viva depende de ello.

Auditoría: 2026-09-20. Método: búsqueda en todo el repositorio para cada
candidato, más verificación contra los logs de producción del curso `36074`.

---

## Resumen

| | Qué | Acción | Estado |
|---|---|---|---|
| 1 | `api_export.py` como exportador de nbgrader | Registro comentado | **Retirado** |
| 2 | `STUDENT_METRICS_API_URL` en el Hub | Bloque comentado | **Retirado** |
| 3 | `STUDENT_METRICS_EVENT_URL` | Cae con el anterior | **Retirado** |
| 4 | `database/schema.sql` (v1) | Cabecera de histórico | **Marcado** |
| 5 | `competencias.codigo_anterior` | — | **NO es obsoleto** |
| 6 | `cuadernillo_notas.enviado_a_moodle_en` | — | **NO es obsoleto** |
| 7 | `.replace(/_v\d+$/)` en `custom.js` | — | **NO es obsoleto** |
| 8 | `CUADERNILLO_ID` | — | Redundante, pero vivo |

Lo importante de esta tabla está en la mitad de abajo: **cuatro de los ocho
candidatos que parecían muertos no lo están**, y dos de ellos habrían roto algo
al quitarlos.

---

## 1. `api_export.py` — el exportador de nbgrader

**Qué era.** Un plugin registrado en `notebook/nbgrader_config.py` que, al
ejecutar `nbgrader export`, subía el gradebook al backend con un `POST` a
`METRICS_API_URL`.

**Por qué se retira.** Dos motivos independientes, cualquiera de los dos basta:

1. **Nadie lo ejecutaba.** `nbgrader export` no aparece en ningún script,
   Dockerfile ni comando del AVA. La única referencia en todo el repositorio era
   su propio registro: se registraba y no se invocaba.
2. **Apuntaba a una ruta que no existe.** `METRICS_API_URL` valía
   `http://api_go:8080/internal/metrics`. Esa ruta no está definida en
   `route.go`. Si alguien lo hubiera ejecutado, habría fallado.

**Desde cuándo.** Indeterminado. `INFORME_TELEMETRIA.md:75` ya lo señalaba como
histórico junto con `CONTRATO_JSON_BACKEND.md`, que describe endpoints
(`/public/metrics/evento`, `/internal/metrics`) y tablas
(`resultado_ejercicio`, `telemetria_ejercicios`) que nunca existieron.

**Qué lo reemplaza.** `notebook/registrar_notas.py` → `POST /internal/notas`,
disparado por `admin_bridge.py` al envolver el *Autograde* de formgrader.
Verificado en los logs de producción: `/internal/notas` aparece,
`/internal/metrics` no aparece nunca.

**Qué se tocó.**
- `notebook/nbgrader_config.py`: la línea `c.ExportApp.plugin_class = …`
  comentada, con la explicación al lado.
- `notebook/plugins/api_export.py`: cabecera de obsoleto. **El archivo se
  conserva**: si algún día hace falta un exportador, es el punto de partida y ya
  tiene resuelto el formato.

---

## 2 y 3. `STUDENT_METRICS_API_URL` y `STUDENT_METRICS_EVENT_URL`

**Qué eran.** El `auth_state_hook` del Hub exportaba a cada contenedor
`STUDENT_METRICS_API_URL`, con valor por defecto
`http://api_go:8080/public/metrics/evento`.

**Por qué se retiran.**

- **La ruta no existe.** No hay `/public/metrics/evento` en `route.go`. Las
  reales son `/api/exercises/attempts` y `/api/cuadernillos/ratings`.
- **El camino de respaldo no se ejecutaba nunca.** Los únicos que la leían
  —`metrics_bridge._url_backend` y `tutor_bridge`— la usaban solo para deducir la
  base quitándole el path. Y la base ya llega directa en
  `STUDENT_METRICS_API_BASE`, que el Hub pone dos líneas más arriba y **siempre**
  tiene valor.
- **`STUDENT_METRICS_EVENT_URL` no la define nadie.** Aparecía como segunda
  alternativa dentro del mismo bloque y solo se leía. Búsqueda en todo el
  repositorio: una sola aparición, la lectura.

**Qué se tocó.** `hub_config/jupyterhub_config.py`: el bloque comentado con la
explicación.

**Qué NO se tocó, y por qué.** Las lecturas de respaldo en `metrics_bridge.py` y
`tutor_bridge.py` se dejan tal cual. Ahora son código inalcanzable —la variable
ya no se exporta—, pero quitarlas no aporta nada y sí añade riesgo si alguna vez
se levanta un contenedor fuera del Hub.

---

## 4. `database/schema.sql` (v1)

**Qué era.** El primer esquema de la base.

**Por qué se marca.** `docker-compose.yml:171` monta `schema_v2.sql`, no este.
Leer el v1 creyendo que es el vigente lleva a error: le faltan las tablas de
competencias, notas y estudiantes, y su `CHECK` de `validation_result` no acepta
`sin_validar`.

**Qué se tocó.** Cabecera de histórico. El archivo se conserva como traza del
modelo original.

---

## Candidatos descartados — no son obsoletos

Se documentan **porque parecían muertos** y alguien que repita esta auditoría va
a volver a tropezar con ellos.

### 5. `competencias.codigo_anterior` — cero escrituras, pero imprescindible

Ningún `INSERT` ni `UPDATE` del backend la toca: solo se siembra en el esquema.
Por conteo automático parece muerta.

**Es la tabla de correspondencia entre los códigos cortos y los oficiales del
microcurrículo** (`I3` = `mCC87`, `I1` = `mCP17`…). Es la respuesta a una de las
preguntas abiertas del encargo. Comentarla sería borrar la única documentación
de ese mapeo dentro del código.

El nombre engaña: sugiere que `mCC87` es el código *viejo*. Conviene renombrarla
o documentarla, no retirarla.

### 6. `cuadernillo_notas.enviado_a_moodle_en` — cero escrituras, pero es un gancho

Nadie la escribe porque **nadie hace todavía la devolución de notas a Moodle**.
`notasRepository.go:24` la protege explícitamente de sobrescrituras, lo que
indica que se diseñó a conciencia para una función pendiente.

No es código muerto: es infraestructura de algo sin terminar. Con LTI 1.1, ese
envío sería Basic Outcomes usando `lis_result_sourcedid` y
`lis_outcome_service_url`, que ya se capturan y se guardan en `estudiantes`.

### 7. `.replace(/_v\d+$/, '')` en `custom.js` — **habría roto la telemetría**

Parecía el resto de un esquema de versionado abandonado. **No lo es.**

`entregar_cuadernillo.py` documenta la función: si el alumno ya tenía un
cuadernillo y el docente corrige el contenido, *«la versión nueva va al lado
(`<id>_v2.ipynb`): su trabajo está dentro del anterior y no se toca»*.

`codigo_cuadernillo()` toma el nombre del archivo. Sin ese `replace`, todo lo que
el alumno hiciera en `semana_01_v2.ipynb` se registraría bajo un
`cuadernillo_id` distinto, y su avance quedaría partido en dos sin que nadie se
enterara. **Quitarlo era un bug silencioso.**

### 8. `CUADERNILLO_ID` — redundante, pero vivo

`entrypoint.sh:119` la exporta activamente como alias de `CUADERNILLO_CODIGO`:

```sh
export CUADERNILLO_CODIGO
export CUADERNILLO_ID="$CUADERNILLO_CODIGO"
```

Los dos valen lo mismo, así que las lecturas de respaldo en `metrics_bridge` y
`tutor_bridge` nunca cambian el resultado. Es redundancia, no código muerto.

Se deja. Retirarla obliga a tocar tres archivos para no ganar nada, y el alias
podría estar sosteniendo algo que no se vio en la búsqueda.

---

## Lo que esta auditoría NO encontró

Vale la pena decirlo, porque el encargo anticipaba lo contrario:

- **Ningún handler huérfano.** Los diez endpoints de `route.go` tienen llamador
  vivo; se comprobaron uno por uno contra los logs de producción.
- **Ningún evento duplicado** en `custom.js`. Los tres disparadores —error en
  celda de solución, ejecución de celda de prueba, cierre de pestaña— hacen
  cosas distintas y los tres se usan.
- **Ninguna columna abandonada** salvo las dos de §5 y §6, que resultaron no
  serlo.

Lo que había era **dos caminos que apuntaban a endpoints inexistentes** —restos
de un contrato de API anterior que nunca se implementó— y un puñado de variables
de respaldo que ya no podían activarse.

---

## Pendiente de borrado definitivo

Nada, todavía. Los cuatro elementos retirados quedan comentados o marcados. Se
podrán eliminar cuando pase al menos un curso completo sin que nadie los eche en
falta, y confirmando otra vez por búsqueda que no hay referencias vivas.

Junto con ellos convendría revisar `CONTRATO_JSON_BACKEND.md`, que sigue
describiendo endpoints y tablas que nunca existieron y es, en palabras del
propio `INFORME_TELEMETRIA.md`, *«lo primero que lee quien llega»*.
