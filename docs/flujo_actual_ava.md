# Flujo actual del AVA — auditoría previa (Fase 0)

Documento de solo lectura. Nada de lo descrito aquí se ha modificado. Todo lo
que se afirma está verificado contra el código y, donde se indica, contra la
instalación en producción (`jupyteruisproyecto.duckdns.org`, curso `36074`).

Fecha de la auditoría: 2026-09-20.

---

## 0. Respuestas a las preguntas abiertas

Las tres preguntas que el encargo dejaba abiertas tienen respuesta, y dos de
ellas contradicen lo que se daba por supuesto.

### 0.1 ¿El AVA está en LTI 1.3? → **No. Está en LTI 1.1.**

Verificado por tres vías independientes:

```python
# hub_config/jupyterhub_config.py
from ltiauthenticator.lti11.auth import LTI11Authenticator   # línea 12
class LTIRoleAuthenticator(LTI11Authenticator):              # línea 83
c.LTI11Authenticator.consumers = {_lti_key: _lti_secret}     # línea 181
```

- El paquete instalado es `jupyterhub-ltiauthenticator 1.6.3`, que **trae los
  dos módulos** (`lti11/` y `lti13/`). Solo `lti11` está cableado.
- `consumers = {clave: secreto}` es el modelo de LTI 1.1 (clave y secreto
  compartidos, firma OAuth 1.0a). LTI 1.3 usaría OIDC, JWKS y `client_id`.
- En producción, el Hub solo ha registrado la ruta `/hub/lti/launch`, con
  **124 POST reales de Moodle**. No existe `/hub/lti13/`.

**Consecuencia para el plan:** la devolución de notas a Moodle —fuera del
alcance de este encargo— no sería por AGS (que es de 1.3) sino por el
**Basic Outcomes Service** de 1.1, con `lis_result_sourcedid` y
`lis_outcome_service_url`. El AVA ya captura y persiste los dos (ver §6.4).

### 0.2 ¿Qué significan `I3`, `I4`, `I5`? → **Ya existe la tabla, en el esquema.**

No hay que reconstruirla ni re-etiquetar desde cero. La columna
`competencias.codigo_anterior` de `database/schema_v2.sql` (líneas 101-108) es
exactamente la correspondencia pedida:

| Código corto | Código oficial | ¿En alcance? | Descripción |
|---|---|---|---|
| `I1` | **mCP17** | **Sí** | Aplica álgebra lineal, cálculo y métodos numéricos mediante programación |
| `I2` | mCC85 | No | Complejidad computacional e impactos económicos y ambientales |
| `I3` | **mCC87** | **Sí** | Identifica variables, conceptos y aspectos relevantes del problema |
| `I4` | **mCC103** | **Sí** | Reconoce problemas susceptibles de tratamiento algorítmico |
| `I5` | mCA14 | No | Comunica efectivamente a distintas audiencias |
| `I6` | mCA65 | No | Trabaja en equipo, establece objetivos y asume roles |
| `I7` | **mCP88** | **Sí** | Investiga y selecciona fuentes confiables y relevantes |

Las descripciones coinciden literalmente con las del encargo, así que la
correspondencia no es una interpretación: es la misma frase.

> **Ojo con el nombre de la columna.** Se llama `codigo_anterior`, lo que
> sugiere que en su momento se consideró que `mCC87` era el código *viejo* y
> `I3` el nuevo. El encargo asume lo contrario. El mapeo es el mismo en
> cualquier dirección, pero conviene decidir cuál de los dos es el canónico
> antes de escribir más código que dependa de ello.

### 0.3 Umbrales N1/N2/N3 → pendiente de la Fase 1 (queda a criterio técnico).

---

## 1. Hallazgo principal: el etiquetado actual no cuadra con el alcance

Cruzando §0.2 con el mapeo realmente cargado en producción:

| Código | Oficial | ¿En alcance? | Al auditar (Fase 0) | Tras el recorte (Fase 5) | Tras reetiquetar (Fase 6) |
|---|---|---|---:|---:|---:|
| I3 | mCC87 | Sí | **45** (73 % del total) | **35** | **30** |
| I4 | mCC103 | Sí | **11** | **3** | **0** ← ver abajo |
| I5 | mCA14 | **No** | **6** ← fuera de alcance | **4** | **0** ✔ |
| I1 | mCP17 | **Sí** | **0** ← sin evidencia | **3** | **7** |
| I7 | mCP88 | **Sí** | **0** | **0** | **0** ← no es calificable, a propósito |
| I2, I6 | mCC85, mCA65 | No | 0 | 0 | 0 |

La Fase 5 recortó las semanas 3 a 6 y las re-etiquetó según la planeación
oficial. La Fase 6 hizo lo mismo con las semanas 1 y 2, que no se podían
rediseñar porque ya están liberadas y `semana_01` tiene entregas.

Simulado contra la telemetría real de producción antes de aplicarlo:

| | Antes | Después |
|---|---:|---:|
| mCC87 | 606 intentos | 420 |
| mCC103 | 161 | **0** |
| mCA14 *(fuera de alcance)* | 200 | **0** |
| mCP17 | 0 | **253** |

Y por estudiante: mCC87 la miden los 18; mCP17 pasa de inmedible a **9 de 18**
con evidencia suficiente, y subirá al liberar la semana 3.

### Cómo llega esto a producción (no basta con editar el JSON)

Reetiquetar cambia `notebook/cuadernillos/competencias.json`, y ese archivo
**entra en la imagen del docente al construirla**, no por bind mount:
`notebook/Dockerfile.docente:23` lo copia a `/opt/plantillas/`. Así que hacen
falta tres pasos, en este orden:

1. `git pull` en el servidor.
2. Reconstruir la imagen del docente (`servidor/instalar.sh` lo hace).
3. Dentro del contenedor del docente, ejecutar `cargar-competencias`.

Hasta el paso 3 la base sigue con el mapeo viejo. Y cuando se ejecute, el
cambio es **retroactivo**: la competencia se resuelve por JOIN, así que los
intentos ya recogidos se reclasifican solos, sin reprocesar nada. Simulado
contra los datos reales antes de aplicarlo — las cifras están arriba.

Un aviso para más adelante: esa retroactividad **no** alcanza a
`corte_competencia`. Un corte congelado guarda su nivel y sus señales tal como
estaban, con el mapeo de aquel día. Es lo que se quería —una foto no cambia—,
pero significa que un corte tomado antes de reetiquetar no es comparable con
uno tomado después. Hoy no hay ninguno congelado, así que no hay daño.

### El agujero que queda: mCC103 no la mide nadie

Es el hallazgo de la Fase 6 y no se puede arreglar etiquetando.

mCC103 es *«reconocer problemas de sistemas y organizaciones susceptibles de
tratamiento algorítmico»*. Revisados uno a uno los quince ejercicios de las
semanas 1 y 2, **ninguno pide eso**: piden escribir algoritmos, trazar
variables, convertir tipos y traducir entre pseudocódigo y Python. Reconocer
una situación real como tratable algorítmicamente no se evalúa en ningún sitio.

De las tres etiquetas mCC103 que había, solo una es residuo comprobable: la de
`semana_01/ejercicio_2`, que se arrastró de un ejercicio anterior cuando ese
hueco se rellenó con otro distinto. Hoy pide emparejar editor / terminal /
intérprete / IDE con su definición — que no es reconocer un problema de una
organización, por mucho que aparezca la palabra «sistema». Las otras dos no son
residuo: se pusieron a propósito y siguen sin medir lo que la competencia dice.

Se dejaron sin etiqueta en vez de repartirla a ciegas: un número que no
significa lo que dice es peor que un hueco visible. `build.py` avisa en cada
construcción de qué ejercicios van sin competencia.

**Para medirla hace falta un ejercicio que hoy no existe**, del tipo «aquí
tienes tres situaciones de una organización: di cuál se puede resolver con un
algoritmo y por qué». Eso es contenido nuevo, no reetiquetado, y en `semana_01`
además obligaría a re-liberar un cuadernillo con entregas.


Tres problemas, por orden de gravedad:

1. **Seis ejercicios miden `mCA14`**, que el propio encargo excluye porque se
   evalúa por autorreporte y coevaluación, no por trazas. Esas etiquetas no
   deberían existir en el AVA.
2. **`mCP17` no tiene ni un ejercicio**, y el encargo le da evidencia oficial en
   la semana 3. Hoy la semana 3 está etiquetada I3+I4.
3. **`mCC87` (I3) absorbe el 73 %** y está en *todos* los ejercicios de las
   semanas 2 a 6. Con ese reparto, el análisis por competencia dice
   aproximadamente lo mismo que la nota general: pierde poder de diagnóstico
   justo en lo que motiva el trabajo.

Reparto por cuadernillo (producción):

| | I3 | I4 | I5 | Ejercicios |
|---|---|---|---|---|
| semana_01 | 5 | 2 | 2 | 7 |
| semana_02 | 8 | 1 | 2 | 8 |
| semana_03 | 8 | 2 | 1 | 8 |
| semana_04 | 8 | 2 | 0 | 8 |
| semana_05 | 8 | 1 | 1 | 8 |
| semana_06 | 8 | 3 | 0 | 8 |

---

## 2. `custom.js` — la captura en el navegador

`notebook/custom.js`, cargado por nbclassic. **No es una extensión de
navegador**: es el `custom.js` del propio Jupyter clásico.

### 2.1 Qué celdas reconoce

Por metadatos de nbgrader, no por etiquetas ni nombres:

```js
function es_celda_de_prueba(cell) {      // grade_id = "test_ejercicio_1"
    var m = meta_nbgrader(cell);
    return !!(m && m.grade === true && m.grade_id);
}
function es_celda_de_solucion(cell) {    // grade_id = "ejercicio_1"
    var m = meta_nbgrader(cell);
    return !!(m && m.solution === true && m.grade !== true && m.grade_id);
}
```

Los dos se normalizan al mismo código con `normalizar_codigo_ejercicio()`,
idéntico a lo que hace la exportación de nbgrader.

### 2.2 Qué dispara cada envío

| Disparador | Qué hace |
|---|---|
| Error en celda de **solución** | **No envía**: bufferiza el error en `localStorage` |
| Ejecución de celda de **prueba** | **Envía** el intento con todos los errores acumulados |
| `beforeunload` (cerrar pestaña) | **Envía** con `validation_result: "sin_validar"` los ejercicios que nunca se validaron, vía `sendBeacon` |

No hay envío al guardar el notebook ni al pulsar «Guardar y entregar»: ese botón
llama a `panel/entregar`, que es otro camino (nbexchange), no telemetría.

### 2.3 El payload

```js
var payload = {
    tipo_evento: "exercise_attempt",
    cuadernillo: codigo_cuadernillo(),
    exercise_id: cod,
    codigo_celda: grade_id,
    orden: obtener_orden_celda(cell),
    puntos_maximos: nbgrader_meta.points || 1,
    attempt_at: new Date(ahora).toISOString(),
    validation_result: exito ? "passed" : "failed",
    errors: errores_acumulados
};
```

**No lleva identidad ni competencia.** La identidad la añade el servidor
(§3). La competencia no viaja nunca (§4.2).

Destino: `POST <base_url>/nbgrader-metrics/evento`, con `X-XSRFToken` en la
cabecera y `credentials: 'same-origin'`.

### 2.4 Un detalle a tener en cuenta para la Fase 3

`codigo_cuadernillo()` toma el **nombre del archivo**:

```js
var nombre = Jupyter.notebook.notebook_name || '';
return nombre.replace(/\.ipynb$/, '').replace(/_v\d+$/, '');
```

En producción eso ya produjo una fila con `cuadernillo_id = "Fabio"`: un
estudiante trabajó en una copia con su nombre. La consecuencia importante no es
el dato sucio — es que **ese trabajo no se le entrega**, porque
`entregar-cuadernillo` busca `semana_NN.ipynb`.

---

## 3. `metrics_bridge.py` — el puente en el servidor del alumno

Extensión de `jupyter_server` que registra `<base_url>/nbgrader-metrics/evento`.

**Añade la identidad** desde el entorno que inyectó el `auth_state_hook`:

```python
IDENTIDAD = {
    "student_id": os.environ.get("ALUMNO_ID"),
    "student_name": os.environ.get("ALUMNO_NOMBRE"),
    "student_email": os.environ.get("ALUMNO_EMAIL"),
    "course_id": os.environ.get("CURSO_ID"),
    "cuadernillo_id": os.environ.get("CUADERNILLO_CODIGO")
                      or os.environ.get("CUADERNILLO_ID"),
}
```

**Añade el token** (`STUDENT_METRICS_TOKEN`), que nunca llega al navegador, y
**rutea por tipo de evento**:

```python
"exercise_attempt": "/api/exercises/attempts",
"cuadernillo_rating": "/api/cuadernillos/ratings",
```

**Interruptor global:** con `ENVIAR_AL_BACKEND` distinto de `true`, el puente
**devuelve éxito sin enviar nada**. El navegador lo da por bueno y vacía su
buffer. Ya provocó una pérdida total de telemetría en la instalación anterior.

---

## 4. El pipeline de construcción de cuadernillos

### 4.1 Cadena completa

```
semana_NN/generador.py  ──build.py──>  notebook_semana/semana_NN/cuadernillo.ipynb
                        └──────────>  cuadernillos/competencias.json
                                            │
                                    cargar-competencias
                                            ▼
                              POST /internal/competencias  ──>  ejercicio_competencias
```

El `.ipynb` es **salida generada, no fuente**. Se edita el generador.

### 4.2 La competencia NO llega al `.ipynb`, y es deliberado

`constructor.a_dict()` escribe en la metadata del notebook `tutor_ia` y
`ava: {cuadernillo, semana, puntos}` — **nada de competencias**. El motivo está
escrito en `build.py:29-31`:

> *Mapeo ejercicio -> competencias. Va aparte del notebook a propósito: es
> diseño del curso, no dato del alumno, y el backend lo resuelve por JOIN. Así,
> corregir una etiqueta mal puesta corrige todo el histórico ya recogido.*

Y en `cargar_competencias.py`:

> *la competencia NO viaja con cada intento (…) si un ejercicio queda mal
> etiquetado y se corrige más adelante, todo el histórico ya recogido se corrige
> solo. Si viajara en el evento, esos datos serían incorregibles.*

**Esto choca de frente con la Fase 1 y la Fase 3 del encargo**, que piden mover
el etiquetado a la metadata del `.ipynb` y persistir la competencia junto a cada
intento. Ver §8.1.

### 4.3 `build.py` avisa de ejercicios sin etiquetar

```
[AVISO] sin competencia asignada: ejercicio_4
        No fallan, pero no aparecerán en el análisis por competencia.
```

Hoy los seis cuadernillos salen sin avisos: los 37 ejercicios están etiquetados
(eran 47 antes del recorte de la Fase 5).

---

## 5. Backend Go — qué recibe y dónde lo guarda

Módulo `proxy-go`. Rutas en `internal/server/router/route.go`.

| Endpoint | Middleware | Qué hace |
|---|---|---|
| `POST /api/exercises/attempts` | `RequireMetricsToken` | Guarda el intento y sus errores |
| `POST /api/cuadernillos/ratings` | `RequireMetricsToken` | Valoración del alumno (UPSERT) |
| `GET /api/mi-progreso` | `RequireMetricsToken` | Panel del alumno |
| `POST /api/exercise/tutorIA` | `RequireMetricsToken` | Tutor |
| `POST /internal/lti/mint-metrics-token` | `RequireTokenMaestro` | Acuña token por persona |
| `POST /internal/lti/ingreso` | `RequireTokenMaestro` | Registra el ingreso (tabla `estudiantes`) |
| `POST /internal/competencias` | `RequireMaestroODocente` | **Carga el mapeo** |
| `POST /internal/notas` | `RequireMaestroODocente` | Nota oficial de nbgrader |
| `GET /internal/curso/:curso/panel` | `RequireMaestroODocente` | Panel del curso |
| `GET /internal/curso/:curso/estudiante/:e` | `RequireMaestroODocente` | Ficha individual |

### 5.1 `CreateAttemptHandler`, en detalle

Valida con `ShouldBindJSON` y **pisa la identidad del cuerpo con la del token**:

```go
studentID, courseID := middleware.IdentidadVerificada(c)
if studentID == "" { studentID = input.StudentID }
if courseID  == "" { courseID  = input.CourseID }
```

Solo cae al cuerpo si el token no traía identidad, que ocurre si
`METRICS_TOKEN_SECRET` está vacío.

Persiste en `exercise_attempts` (+ `attempt_errors` en cascada).
`validation_result` acepta `passed`, `failed` y `sin_validar`.

### 5.2 Nombre distinto a cada lado del límite

El navegador y el handler llaman `timestamp` a lo que la columna llama
`occurred_at`. El `struct` de Go traduce. No es un fallo, pero confunde.

---

## 6. Base de datos

`database/schema_v2.sql` (el compose monta este; `schema.sql` v1 **no se usa**).

| Tabla | Para qué |
|---|---|
| `exercise_attempts` | Cada validación. `attempt_at` lo sella el navegador; `received_at`, el backend |
| `attempt_errors` | Los errores de cada intento. `ON DELETE CASCADE` |
| `cuadernillo_ratings` | Opinión del alumno (1-5). **No es nota** |
| `competencias` | Catálogo `I1…I7` + `codigo_anterior` (§0.2) |
| `ejercicio_competencias` | **El mapeo.** Clave `(cuadernillo, ejercicio, competencia)` |
| `cuadernillo_notas` | Nota real de nbgrader. `origen` distingue `nbgrader` de `provisional` |
| `estudiantes` | Quién es cada quien + los dos datos LTI de devolución de nota |
| `errores_por_competencia` (vista) | **Ya agrupa por estudiante y competencia** |

### 6.1 La vista que ya responde media Fase 1

```sql
CREATE VIEW errores_por_competencia AS
SELECT a.course_id, a.cuadernillo_id, a.student_id,
       ec.competencia_id, c.descripcion,
       COUNT(*)                                                    AS intentos_totales,
       COUNT(*) FILTER (WHERE a.validation_result = 'failed')      AS intentos_fallidos,
       COUNT(*) FILTER (WHERE a.validation_result = 'sin_validar') AS abandonos,
       COUNT(e.id)                                                 AS errores
FROM exercise_attempts a
JOIN ejercicio_competencias ec ON …
JOIN competencias c ON …
LEFT JOIN attempt_errors e ON …
GROUP BY 1, 2, 3, 4, 5;
```

Es exactamente la señal que la Fase 1 pide para calcular N1/N2/N3: **fallos y
abandonos por estudiante y competencia, sin denormalizar nada**.

### 6.2 Zonas horarias

Todo es `TIMESTAMPTZ`, así que el instante es absoluto. No hay `TZ` configurada
en ningún servicio: los contenedores corren en UTC. Un `SELECT` a mano devuelve
UTC; para hora local, `AT TIME ZONE 'America/Bogota'`.

### 6.3 Migraciones

`migracion_v2.sql`, `v3`, `v4`. El instalador aplica v3 y v4 en cada ejecución,
de forma idempotente. Cualquier cambio de la Fase 1 debe seguir ese patrón.

### 6.4 Devolución de notas (fuera de alcance, pero conviene saberlo)

`estudiantes` ya guarda `lis_result_sourcedid` y `lis_outcome_service_url`, y
`cuadernillo_notas.enviado_a_moodle_en` existe y está protegida de
sobrescrituras. **No hay código que haga el envío.** La infraestructura está
puesta y falta el último paso — que, siendo LTI 1.1, sería Basic Outcomes y no
AGS.

---

## 7. El panel del docente

**Corrección al encargo:** no lo sirve `admin_bridge.py`. Son dos piezas
distintas:

| Archivo | Ruta | Qué hace |
|---|---|---|
| `notebook/admin_bridge.py` | — | Envuelve el *Autograde* de formgrader para subir las notas al backend, y borra actividades |
| `notebook/panel_docente_bridge.py` | `/user/<docente>/panel-docente` | **El panel**: el ciclo por semana, entregas, dificultad, malentendidos, riesgo, valoraciones y competencias |

Secciones actuales (`_seccion_*`): `ciclo`, `entregas`, `estudiantes`,
`dificultad`, `valoraciones`, `malentendidos`, `riesgo`, `salud`,
`competencias`. Y una ficha individual por estudiante
(`/panel-docente/estudiante/<id>`) con su recorrido ejercicio a ejercicio.

### 7.1 Lo que ya se añadió esta semana

Antes de recibir este encargo se cerraron dos huecos relacionados
(commits `7222d11` y `7158cd5`):

- **Progreso por competencia de cada estudiante** en su ficha: ejercicios
  vistos, resueltos, intentos y **abandonos**, con el mismo diseño de tarjetas
  del panel del curso.
- **Guía visible** con el texto completo de cada código, porque antes solo se
  leían pasando el ratón.

**Lo que falta para la Fase 4 es el nivel N1/N2/N3**, no la vista por estudiante.

---

## 8. Tensiones entre el encargo y el diseño actual

Se listan porque afectan a decisiones de la Fase 1 y conviene resolverlas en el
gate, no a mitad de la implementación.

### 8.1 Persistir la competencia con cada intento

El encargo (Fase 1.1, Fase 3.1) pide mover el etiquetado a la metadata del
`.ipynb` y guardar la competencia junto a cada intento. El diseño actual hace
deliberadamente lo contrario, y documenta el motivo: **una etiqueta mal puesta
se corrige y el histórico entero se corrige con ella**. Denormalizada, no.

Esto no es teórico: el mapeo de este curso **estuvo vacío hasta el 2026-09-18**,
con 686 intentos ya recogidos. Al cargarlo, los 686 quedaron clasificados
retroactivamente sin reprocesar nada. Con la competencia dentro de cada fila,
habrían quedado huérfanos para siempre.

Y hay un segundo motivo: llevar la etiqueta en el `.ipynb` significa que el
notebook **ya entregado** por seis estudiantes lleva dentro una etiqueta que no
se puede cambiar sin invalidar la entrega.

**Recomendación:** mantener el mapeo relacional como fuente de verdad y añadir
solo lo que falta (el nivel derivado). Si aun así quieres la etiqueta en la
metadata, que sea **informativa y redundante**, nunca la fuente de la que lee el
backend.

### 8.2 `mCC103` en las semanas 3-6

El encargo pide explícitamente no forzarla ahí. Hoy **está forzada**: I4
(=mCC103) aparece en las cuatro (2, 2, 1, 3 ejercicios). Habrá que quitarla en
la Fase 5, no solo «no añadirla».

### 8.3 `mCP88` como celda informativa

El encargo dice que nunca es calificable. Correcto y coherente con el estado
actual (I7 = 0 ejercicios). Pero conviene decidir **cómo se mide entonces**: si
no genera intentos, no puede tener nivel N1/N2/N3 derivado de fallos. O se
excluye del cálculo, o se mide por otra señal.

### 8.4 LTI

Ver §0.1. Ninguna decisión del encargo depende de esto, pero el diagrama C4 y el
plan de grado deberían corregirse: dicen 1.3 y es 1.1.

---

## 9. Candidatos a código obsoleto

Con evidencia. **Nada se ha tocado.**

| Candidato | Evidencia | Recomendación |
|---|---|---|
| `database/schema.sql` (v1) | El compose monta `schema_v2.sql`. Ninguna referencia viva | Comentar cabecera como histórico |
| `competencias.codigo_anterior` | **0 escrituras** en el backend. Solo se siembra | **NO tocar**: es la tabla de correspondencia de §0.2. Documentarla, no borrarla |
| `cuadernillo_notas.enviado_a_moodle_en` | **0 escrituras**. Nadie hace el envío | Conservar: es el gancho de una función pendiente, no código muerto |
| `STUDENT_METRICS_API_URL` | 3 archivos, pero `metrics_bridge` la usa solo como *fallback* de `STUDENT_METRICS_API_BASE` | Candidata real a retirar |
| `CUADERNILLO_ID` | Fallback de `CUADERNILLO_CODIGO` en `metrics_bridge.IDENTIDAD` | Candidata real a retirar |
| `.replace(/_v\d+$/, '')` en `codigo_cuadernillo()` | Quita un sufijo `_vN` que ningún cuadernillo usa hoy | Verificar si quedó de un esquema de versionado anterior |
| Etiquetas `I5` (mCA14) | 6 ejercicios con una competencia fuera de alcance | Re-etiquetar en Fase 5/6 |

**Ninguno de estos es un handler huérfano ni un endpoint sin uso.** Los diez
endpoints de §5 tienen llamador vivo; lo comprobé ruta por ruta. El «código
obsoleto» que el encargo anticipaba, en la práctica, no existe: lo que hay son
variables de respaldo y una columna mal nombrada.

---

## 10. Estado de los cuadernillos (producción, curso `36074`)

| Semana | Ejercicios | `source` | `release` | Entregas | Telemetría | Margen para rediseñar |
|---|---|---|---|---|---|---|
| semana_01 | 7 (25 pts) | sí | **sí** | **6 recogidas** | 16 alumnos · 429 intentos | Solo re-etiquetar (Fase 6) |
| semana_02 | 8 (80 pts) | sí | **sí** | en el intercambio, sin recoger | 9 alumnos · 267 intentos | Solo re-etiquetar (Fase 6) |
| semana_03 | 8 (80 pts) | sí | no | — | — | **Libre** |
| semana_04 | 8 (80 pts) | sí | no | — | — | **Libre** |
| semana_05 | 8 (80 pts) | sí | no | — | — | **Libre** |
| semana_06 | 8 (80 pts) | sí | no | — | — | **Libre** |

Se confirma la condición de la Fase 5: **semana_03 a semana_06 están en borrador
y sin entregas**, así que hay libertad total. semana_01 y semana_02 no.

Una nota sobre la semana_02: hay entregas en el intercambio pero el docente
todavía no ha ejecutado *Collect*, así que `submitted/` de nbgrader solo tiene
semana_01. Cuando recoja, esas entregas llevarán el notebook tal como está hoy.

---

## 11. Qué queda instrumentado hoy, en una frase

El AVA **ya sabe**, por estudiante y por competencia, cuántos ejercicios vio,
cuántos resolvió, cuántos intentos hizo y cuántas veces se rindió sin validar.
Lo que **no** sabe es traducir eso a un nivel N1/N2/N3 — y eso es exactamente lo
que falta construir.
