# Tutor IA — lo que falta

Estado: la extensión está completa y probada (ver `TUTOR_IA.md` para el detalle
técnico). Esto es lo que queda antes de darla por entregada.

## Bloqueante

- [ ] **`GOOGLE_API_KEY` en el `.env` de la VM.** Sin ella `/api/exercise/tutorIA`
      responde 500 y el panel muestra "el tutor no está disponible".
- [ ] **Probar contra Gemini de verdad.** Todo lo verificado hasta ahora usó un
      backend simulado que responde con el mismo formato (`{"resultado": "..."}`).
      La ruta, el JSON y el puente están probados; la llamada real a Gemini no.

## Importante

- [ ] **Que el backend cuente las preguntas.** Hoy el tope de 5 lo defiende
      `tutor_bridge.py` dentro del contenedor del alumno. Es sólido contra la
      consola del navegador (probado: la sexta pregunta devuelve 429 y no sale a
      Gemini), pero todo corre como el usuario `jovyan`, así que el límite
      inviolable tiene que vivir en el backend contando por
      `(student_id, cuadernillo_id)`.

- [ ] **Confirmar que `CUADERNILLO_CODIGO` llega al contenedor.** El contador se
      lleva por cuadernillo usando esa variable. Si llega vacía, cae a
      `sin_cuadernillo` y **todos los cuadernillos comparten las mismas 5
      preguntas**. La resuelve `entregar-cuadernillo` desde el manifest de
      `/srv/publicados`; hay que verificarlo en la VM con un cuadernillo
      publicado de verdad.

## Verificar en la VM

- [ ] Reconstruir la imagen del notebook (`docker build ./notebook`) y la del
      backend (`docker compose build api_go`).
- [ ] Abrir un cuadernillo entrando por Moodle (LTI). La demo local corrió
      `jupyter server` directo, no `jupyterhub-singleuser`, así que falta ver el
      panel dentro del flujo real del Hub.
- [ ] Confirmar en el log del contenedor del alumno:
      `[tutor_bridge] listo: 5 preguntas por cuadernillo (habilitado=True)`

## Decisiones para Bryan

- El alias del tutor quedó en `Ava` (variable `TUTOR_ALIAS`). Estaba fijo como
  `"Jonh Doe"` en `connectionGeminiApi.go`.
- La ruta pasó de `GET` a `POST` porque el handler lee el body con
  `ShouldBindJSON` y ningún cliente puede mandar cuerpo en un GET.
- ¿Se guardan las conversaciones del tutor para métricas? Hoy no se persiste
  nada: el historial vive en memoria del contenedor del alumno y se pierde al
  cerrar sesión.
