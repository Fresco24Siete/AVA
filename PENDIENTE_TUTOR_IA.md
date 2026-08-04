# Tutor IA — lo que falta

Estado: la extensión está completa y probada (ver `TUTOR_IA.md`). Esto es lo que
queda antes de darla por entregada.

## Antes de desplegar en la VM ampliada

- [ ] **Rotar la clave que se compartió por WhatsApp** (`AQ.Ab8RN6...`). Viajó en
      texto plano por el chat, así que hay que darla de baja y emitir otra.
      Ninguna clave va al repo: solo al `.env` de la VM, que está en `.gitignore`.
- [ ] **Confirmar el formato de las claves.** Las de Gemini (AI Studio) empiezan
      por `AIza`. Una que empiece por `AQ.` parece un token temporal, no una API
      key, y `genai.NewClient` con `BackendGeminiAPI` la rechazaría.
- [ ] **Poner `GOOGLE_API_KEY_1` y `GOOGLE_API_KEY_2`** en el `.env` de la VM.
- [ ] **Probar contra Gemini de verdad.** Todo lo verificado usó un backend
      simulado con el mismo formato. La ruta, el JSON y el puente están probados;
      la llamada real a Gemini no.

## Arreglado en `fix/tutor-gemini-pool` (revisar antes de mergear)

Tres cosas del commit `add control Gemini` que impedían arrancar:

- `clientInit.go` hacía `APIKey: os.Getenv(clave)`, buscando una variable de
  entorno *llamada* como la clave. Ambos clientes quedaban con `APIKey` vacía.
- Ese fallo caía en un `log.Fatalf` dentro de `init()`, que corre **antes** de
  `main()`: se moría el proceso entero. No solo el tutor — también métricas y
  calificaciones. Verificado: el backend no arrancaba ni con las dos claves bien
  puestas. Ahora se registra el error y la API sigue en pie sin tutor.
- `ChatHandler` hacía `<-GeminiClientsPool` sin salida: con el pool vacío la
  petición se quedaba colgada. Ahora responde 503 si no hay clientes, y respeta
  la cancelación de la petición.

## Importante

- [ ] **Que el backend cuente las preguntas.** Hoy el tope de 5 lo defiende
      `tutor_bridge.py` dentro del contenedor del alumno. Es sólido contra la
      consola del navegador (probado: la sexta devuelve 429 y no sale a Gemini),
      pero todo corre como el usuario `jovyan`, así que el límite inviolable
      tiene que vivir en el backend contando por `(student_id, cuadernillo_id)`.

- [ ] **Confirmar que `CUADERNILLO_CODIGO` llega al contenedor.** El contador se
      lleva por cuadernillo usando esa variable. Si llega vacía, cae a
      `sin_cuadernillo` y **todos los cuadernillos comparten las mismas 5
      preguntas**. La resuelve `entregar-cuadernillo` desde el manifest de
      `/srv/publicados`; hay que verificarlo con un cuadernillo publicado.

## Verificar en la VM

- [ ] Reconstruir la imagen del notebook (`docker build ./notebook`) y la del
      backend (`docker compose build api_go`).
- [ ] Abrir un cuadernillo entrando por Moodle (LTI). La demo local corrió
      `jupyter server` directo, no `jupyterhub-singleuser`, así que falta ver el
      panel dentro del flujo real del Hub.
- [ ] Confirmar en los logs:
      - `api_go`: `[tutor] 2 cliente(s) de Gemini listos.`
      - contenedor del alumno: `[tutor_bridge] listo: 5 preguntas por cuadernillo`
- [ ] Cambiar el dominio (hoy DuckDNS) — pendiente de Diego.

## Para hablar con Bryan

- **El nombre del tutor.** El prompt de `prompt.go` lo recibe como parámetro;
  hoy vuelve a leerse de `TUTOR_ALIAS` con default `Ava`, porque `"Jonh Doe"`
  estaba fijo en el código y el alumno lo veía en el saludo. Si quieren otro
  nombre, se cambia en el `.env`, sin recompilar.
- **Forma de la respuesta.** `ChatHandler` devuelve texto plano (`c.String`); la
  versión anterior devolvía `{"resultado": ...}`. El puente acepta las dos, pero
  conviene fijar una.
- **¿Se guardan las conversaciones del tutor para métricas?** Hoy no se persiste
  nada: el historial vive en memoria del contenedor del alumno y se pierde al
  cerrar sesión.
