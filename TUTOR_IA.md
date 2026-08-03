# Tutor IA — extensión de Jupyter

Panel de chat dentro del cuadernillo. El alumno pregunta, el tutor guía con
pistas (nunca da la solución) y tiene **5 preguntas por cuadernillo**.

Se apoya en la base que dejó Bryan en el backend: `models.ApiMessage`,
`handler.TutorHub` y `pkg/tutor.ConnecGeminiApi`.

---

## 1. Flujo

```
Navegador (tutor_ia.js)
    │  POST {base_url}tutor-ia/preguntar
    │  { "mensaje": "...", "contexto": "..." }
    ▼
Servidor del alumno (tutor_bridge.py)   ← aquí se cuenta el límite de 5
    │  POST http://api_go:8080/api/exercise/tutorIA
    │  models.ApiMessage completo
    ▼
Backend Go (TutorHub → ConnecGeminiApi → Gemini 2.5 Flash)
    │  { "resultado": "..." }
    ▼
vuelve al panel: { "respuesta": "...", "usadas": 2, "restantes": 3, "max": 5 }
```

Es el mismo patrón que ya usa la telemetría (`custom.js` → `metrics_bridge.py`
→ backend): **el navegador nunca habla directo con el backend**.

## 2. El JSON que llega al backend

Exactamente `models.ApiMessage`, sin campos de más:

```json
{
  "nombre_estudiante": "Diego López",
  "mensaje": "No entiendo por qué mi recursión no para",
  "historial": "Pista anterior: revisar el caso base…",
  "contexto": "Ejercicio: ejercicio_1\n\nEnunciado:…\n\nCódigo actual del estudiante:…\n\nÚltimo error de ejecución:…"
}
```

Quién pone cada campo:

| Campo | Origen | Por qué |
|---|---|---|
| `nombre_estudiante` | Servidor, de `ALUMNO_NOMBRE` (LTI) | El cliente no puede suplantar a otro alumno |
| `mensaje` | El alumno | Su pregunta, recortada a 2000 caracteres |
| `historial` | Servidor | La respuesta anterior del tutor, guardada por cuadernillo |
| `contexto` | El navegador | Solo el navegador sabe en qué celda va el alumno |

El `contexto` se arma solo: ejercicio actual (`grade_id` de nbgrader),
enunciado, el código que lleva escrito y el último error de ejecución. Sin eso
el tutor responde en el vacío.

Si el cliente intenta mandar `nombre_estudiante` o `historial`, el puente los
ignora — está cubierto por pruebas.

## 3. El límite de 5 preguntas

Se cuenta en `tutor_bridge.py`, **dentro del servidor del alumno**, por
`cuadernillo_id` (el `CUADERNILLO_CODIGO` que resuelve `entregar-cuadernillo`).

- El contador autoritativo vive en memoria del proceso del servidor; el kernel
  del notebook es otro proceso y no puede tocarlo.
- Se persiste en `/home/jovyan/.tutor_ia/estado.json` solo para sobrevivir
  reinicios. Al recargar se toma el máximo entre memoria y archivo, así que
  borrar el archivo a media sesión no devuelve preguntas.
- La pregunta se descuenta **solo si hubo respuesta**: si Gemini o la red
  fallan, el alumno no pierde una de sus 5.
- La pregunta n.º 6 se rechaza con `429` y **nunca sale al backend**, así que no
  gasta cuota de Gemini.
- Dos clics rápidos no cuelan dos preguntas a la vez (guarda de concurrencia; era
  el `// Sin control de condiciones de carrera` de `tutorHub.go`).

**Pendiente para que el límite sea inviolable:** que el backend cuente las
preguntas por `(student_id, cuadernillo_id)` y rechace la sexta. Hoy todo corre
como el usuario `jovyan`, así que un alumno con acceso a ejecutar código podría
manipular el archivo de estado. Es el mismo criterio que ya está documentado en
`metrics_bridge.py` para `STUDENT_METRICS_TOKEN`.

## 4. Cómo se habilita

Dos interruptores, de más general a más específico:

1. **Todo el curso** — `TUTOR_IA_HABILITADO=false` en `.env` y el panel ni se
   dibuja.
2. **Por cuadernillo** — en la metadata del notebook:
   ```json
   "metadata": { "tutor_ia": { "enabled": false } }
   ```
   Ya está puesto en `notebook/notebook_semana/cuadernillo_ejercicios.ipynb` con
   `enabled: true`. El instructor lo cambia desde *Edit → Notebook Metadata*.

Si no se dice nada, el tutor está activo.

## 5. Configuración

En `.env` (ver `.env.example`):

| Variable | Default | Qué hace |
|---|---|---|
| `GOOGLE_API_KEY` | — | **Obligatoria.** Sin ella el backend responde 500 |
| `TUTOR_ALIAS` | `Ava` | Nombre con el que el tutor se presenta |
| `TUTOR_IA_HABILITADO` | `true` | Interruptor de curso |
| `TUTOR_MAX_PREGUNTAS` | `5` | Preguntas por cuadernillo |

Otras, con default razonable, se leen dentro del contenedor del alumno:
`TUTOR_TIMEOUT_SEG` (60 — Gemini tarda mucho más que un INSERT),
`TUTOR_MAX_MENSAJE` (2000), `TUTOR_MAX_CONTEXTO` (4000).

## 6. Archivos

| Archivo | Qué es |
|---|---|
| `notebook/tutor_bridge.py` | Extensión de `jupyter_server`: rutas, límite, identidad, proxy al backend |
| `notebook/tutor_ia.js` | El panel de chat. Solo pinta y arma contexto; cero reglas de negocio |
| `notebook/custom.js` | Carga `tutor_ia.js` (últimas líneas) |
| `notebook/jupyter_server_config.py` | Registra `tutor_bridge` |
| `notebook/Dockerfile` | Copia ambos a `/etc/jupyter` y crea `~/.tutor_ia` |
| `hub_config/jupyterhub_config.py` | Pasa las variables `TUTOR_*` al contenedor del alumno |

Rutas que expone la extensión:

- `GET  {base_url}tutor-ia/estado` → `{habilitado, max, usadas, restantes, …}`
- `POST {base_url}tutor-ia/preguntar` → `{respuesta, usadas, restantes, max}`
- `GET  {base_url}tutor-ia/static/tutor_ia.js` → el JS del panel

Las tres exigen sesión válida de Jupyter (`@web.authenticated`): sin login no se
puede quemar cuota de Gemini.

## 7. Cambios sobre la base del backend

Dos, en el código que dejó Bryan:

1. `route.go`: `api.GET("/exercise/tutorIA")` → **`api.POST`**. El handler lee el
   body con `ShouldBindJSON`, y ni `fetch()` ni el cliente HTTP del puente pueden
   mandar cuerpo en un GET. Sin este cambio la extensión no puede llamarlo.
2. `connectionGeminiApi.go`: el alias fijo `"Jonh Doe"` pasa a leerse de
   `TUTOR_ALIAS` (default `Ava`). Era un placeholder y el tutor se presentaba con
   ese nombre al alumno.

## 8. Para probarlo

```bash
# 1. Poner GOOGLE_API_KEY en .env
# 2. Reconstruir imagen del notebook y backend
docker compose build api_go
docker build -t <imagen-del-notebook> ./notebook
docker compose up -d

# 3. Entrar por Moodle como alumno y abrir el cuadernillo.
#    Abajo a la derecha aparece el botón 🤖 con las preguntas restantes.
```

Verificación rápida en el log del contenedor del alumno:

```
[tutor_bridge] listo: 5 preguntas por cuadernillo (habilitado=True)
```

y en la consola del navegador:

```
[tutor-ia] listo: 5/5 preguntas disponibles
```
