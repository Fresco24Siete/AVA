# Plan: competencias, notas y panel del estudiante

Qué hay que construir para que el profesor vea **en qué competencia** se atasca
cada estudiante, y para que el estudiante tenga un panel con su progreso y sus
notas en vez de un listado de cuadernillos.

Escrito el 15 de agosto de 2026. **Las cuatro fases están implementadas y
probadas contra un Postgres real** (20 de agosto); el diseño de la base está en
[`database/schema_v2.sql`](database/schema_v2.sql) y la migración en
[`database/migracion_v2.sql`](database/migracion_v2.sql).

## Estado

| Fase | Estado | Qué se probó |
|---|---|---|
| 1. Que los datos quepan | hecho | 3 columnas guardadas, `sin_validar` aceptado, identidad del token |
| 2. Competencias | hecho | 20 relaciones, 3 cargas no duplican, la vista agrupa |
| 3. Notas | hecho | sin token 401, fuera de rango 400, recalificar 60→72 sin duplicar |
| 4. Panel | hecho | aislamiento entre alumnos, degrada sin backend |
| Extra: borrar actividades | hecho | se niega con entregas, respalda, pide confirmación |

**Bugs encontrados al construir**, todos corregidos:

1. La migración no aplicaba: `ALTER COLUMN` bloqueado por la vista `exercise_stats`.
2. El puerto del backend estaba fijo en el código; ahora es `PORT`.
3. El panel ocultaba la nota de un alumno calificado sin telemetría, porque la
   consulta partía de los intentos en vez de la unión con las notas.
4. El panel del docente decía «no hay botón para borrar» justo encima del botón
   de borrar recién añadido.

**Hallazgo de contenido, no de código:** `I7` figura como evidencia principal de
la Semana 1, pero **ningún ejercicio calificable la evalúa** — las fuentes
confiables están en la sección de cierre, que no se califica. O la planeación
promete de más, o falta un ejercicio que pida contrastar una fuente.

---

## Qué se quiere lograr

Hoy la telemetría sabe que un estudiante falló `ejercicio_3` de `semana_02`. Eso
sirve para poco: al profesor no le dice si el problema es que no sabe identificar
variables o que no entiende los tipos de datos.

Lo que se busca:

- **Para el profesor**: en qué competencia falla el grupo y cada estudiante.
- **Para el estudiante**: un panel con sus cuadernillos, su progreso y sus notas.
- **Para el trabajo de grado**: datos que respondan la pregunta de investigación,
  no solo que registren actividad.

---

## Por qué en este orden

La tentación es empezar por el panel, porque es lo que se ve. Sería un error: se
construiría una pantalla que muestra ceros, porque hoy **no existe el dato de
competencia en ninguna parte** y la nota tampoco está en la base.

El orden es: primero que el dato exista, después que se llene solo, después que
se pueda leer, y al final la pantalla.

Cada fase deja algo utilizable aunque la siguiente no se haga.

---

## Fase 1 — Que los datos quepan

**Objetivo:** que la base pueda guardar lo que hoy se descarta.

| Qué | Dónde |
|---|---|
| Migración del esquema | `database/` |
| Guardar `puntos_maximos`, `codigo_celda`, `orden` | `backend/internal/handler/exerciseHandler.go` |
| Aceptar `validation_result = 'sin_validar'` | mismo handler, quitar la validación de la línea 49 |
| Borrar los 12 intentos de prueba | migración |

**Nada cambia en `custom.js` ni en `metrics_bridge.py`.** El navegador ya envía
las tres columnas desde siempre; era el backend el que las tiraba.

**El caso `sin_validar` importa más de lo que parece.** Es lo que manda el
navegador cuando el alumno cierra la pestaña habiendo dejado errores en un
ejercicio que nunca validó: se atascó y se rindió. Hoy el backend lo rechaza con
400 y se pierde. Sin ese dato, **un alumno que peleó media hora con un ejercicio
y otro que ni lo abrió se ven idénticos**.

**Terminada esta fase**: la base guarda todo lo que llega. La vista
`errores_por_competencia` ya se puede consultar, aunque devuelva vacío porque
todavía no hay mapeo.

---

## Fase 2 — Que las competencias se llenen solas

**Objetivo:** que cada ejercicio sepa qué competencia evalúa, sin que nadie lo
mantenga a mano.

El diseño de los cuadernillos ya asigna competencias a cada ejercicio —están en
`plan_cuadernos_ava.md`—, pero ese dato no llega a ninguna parte ejecutable.

| Qué | Dónde |
|---|---|
| `ejercicio(..., competencias=["I3","I4"])` | `notebook/cuadernillos/constructor.py` |
| Etiquetar los 15 ejercicios ya escritos | `semana_01/generador.py`, `semana_02/generador.py` |
| Emitir el mapeo al construir | `notebook/cuadernillos/build.py` |
| Comando que lo carga al backend | `notebook/cargar_competencias.py` (nuevo) |
| Endpoint interno que lo recibe | `backend/internal/handler/` |

**Decisión ya tomada y que conviene no revisar:** la competencia **no viaja en
cada intento**. Vive en `ejercicio_competencias` y se resuelve por `JOIN`. Así,
si un ejercicio queda mal etiquetado y se corrige en la semana 8, todo el
histórico se corrige solo. Si viajara en el evento, sería incorregible.

**Terminada esta fase**: el profesor ya puede responder «¿en qué competencia se
está atascando el grupo?» con una consulta, sin que exista ningún panel. Este es
el punto donde el trabajo empieza a rendir.

---

## Fase 3 — Las notas

**Objetivo:** que la nota de cada cuadernillo esté en la base.

La nota real la calcula nbgrader al hacer *Autograde*, y eso ocurre en el
contenedor del docente. Hay que leer su libro de calificaciones y subirla.

| Qué | Dónde |
|---|---|
| Comando que lee el gradebook y publica las notas | `notebook/registrar_notas.py` (nuevo) |
| Endpoint que las recibe | `backend/internal/handler/` |

Esta fase **comparte pieza con la devolución de notas a Moodle**: las dos
necesitan leer el gradebook desde el contenedor del docente. Conviene hacerlas
juntas y no dos veces.

**Terminada esta fase**: hay nota que mostrar, y queda listo el camino para que
viaje a Moodle.

---

## Fase 4 — El panel del estudiante

**Objetivo:** sustituir el índice de cuadernillos por una página con progreso y
notas.

| Qué | Dónde |
|---|---|
| Endpoint de lectura acotado al estudiante | `backend/internal/handler/` |
| Handler que sirve el panel | `notebook/panel_bridge.py` (nuevo) |
| `default_url` apuntando al panel | `hub_config/jupyterhub_config.py` |

**Moodle no es un obstáculo, y eso ya está verificado.** El AVA se abre dentro de
un iframe de Moodle y el `Caddyfile` ya lo permite (`frame-ancestors ...
lms.uis.edu.co`). Una página servida por el propio contenedor del alumno hereda
ese permiso y su autenticación: sin dominios nuevos, sin login nuevo, sin tocar
la configuración del curso. Es una ruta más del servidor que el alumno ya usa,
igual que el panel del tutor.

**El endpoint de lectura debe tomar la identidad del token**, nunca de la
petición — igual que se hizo al escribir. Un estudiante no puede ver los datos de
otro.

---

## Decisiones pendientes

**¿El panel muestra nota antes de que el profesor califique?**
La nota real ejecuta también las pruebas ocultas; una calculada de la telemetría
solo vio las visibles. Los dos números no tienen por qué coincidir, y el reclamo
«el panel decía 4.5» es previsible. Por eso `cuadernillo_notas` lleva la columna
`origen`. Opciones: mostrar solo progreso, o mostrar nota solo cuando
`origen = 'nbgrader'`.

**¿El panel reemplaza el índice o convive con él?**
Reemplazarlo es más limpio, pero convierte el panel en la puerta de entrada: si
falla, el alumno no llega ni a los cuadernillos. Sea cual sea la decisión, el
panel tiene que degradar — si el backend no responde, que muestre igual la lista.

**¿Qué pasa con los datos de prueba?**
Hay 12 intentos y 24 errores de pruebas deliberadas. Al añadir columnas quedan
con nulos. Lo limpio es borrarlos en la migración, antes de que empiece el
semestre.

---

## Riesgos

**El etiquetado se desincroniza.** Si las competencias se mantienen a mano en el
backend, en dos semanas no coinciden con los cuadernillos. Por eso la fase 2
insiste en que el mapeo lo emita `build.py` y no una persona.

**El panel como único acceso.** Ver arriba: tiene que degradar.

**Etiquetar 15 ejercicios es tedioso y silencioso.** Un ejercicio sin competencia
no da error: simplemente no aparece en los análisis. Conviene que `build.py`
avise cuando un ejercicio calificable no tenga ninguna asignada.

---

## Lo que este plan NO cubre

Sigue pendiente lo que está en [`PENDIENTES_AVA.md`](PENDIENTES_AVA.md), y dos
cosas de ahí **bloquean el semestre**, no este plan: las credenciales LTI son las
de desarrollo y están en un repositorio público, y la VM actual aguanta cinco o
seis estudiantes. Ninguna de las dos se resuelve construyendo el panel.
