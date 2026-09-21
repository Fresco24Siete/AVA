# Validación de punta a punta y lista de regresión (Fase 7)

Cierre del encargo de microcompetencias. Aquí está qué se comprobó, **cómo**, y
qué hay que volver a correr antes de cada despliegue.

Todo lo de abajo se ejecutó en un entorno de prueba desechable —Postgres con el
esquema completo más las migraciones v3, v4 y v5, y el backend real—, nunca
contra producción.

---

## 1. La cadena completa, con datos reales

`backend/tests/telemetria/prueba_fase7.py` recorre lo que el encargo pedía
validar, y lo hace con el **mapeo real del curso** y los **identificadores
reales** de un cuadernillo rediseñado, no con datos de juguete:

```
competencias.json  →  POST /internal/competencias      (cargar-competencias)
custom.js          →  POST /api/exercises/attempts     (el navegador del alumno)
                   →  JOIN por (cuadernillo, ejercicio)
                   →  service.NivelCompetencia
                   →  GET /internal/curso/:c/estudiante/:e
```

**13/13 en verde.** Lo que cada caso fija:

| | Comprueba |
|---|---|
| 1 | El mapeo real del curso se carga entero: 37 relaciones |
| 2 | La semana 3 rediseñada tiene sus 6 ejercicios etiquetados |
| 3-4 | Los intentos del cuadernillo rediseñado llegan y se guardan |
| 5 | La competencia se resuelve **por JOIN**, sin viajar en el payload |
| 6 | El panel devuelve nivel y motivo: `N3 · resuelve 5 de 5 con 0.2 fallos por ejercicio` |
| 7 | El intento aprobado que **arrastra el stub** cuenta como visto y resuelto |
| 8 | Las competencias fuera de alcance no reciben nivel |
| 9 | El filtro por semana acota a los ejercicios de esa semana |
| 10 | El corte congela el nivel **junto con los umbrales** que lo produjeron |
| 11 | Regresión: los cuadernillos no tocados siguen guardando métricas |
| 12 | Regresión: un ejercicio sin competencia se guarda igual, no se pierde |
| 13 | Limpieza: no queda nada de la prueba y lo ajeno está intacto |

El caso 7 es el que más vale: es el defecto que motivó media Fase 3 —el panel
contaba 145 ejercicios resueltos donde había 152— comprobado ahora en la cadena
real, no en un `SELECT` a mano.

## 2. Lista de regresión

Lo que hay que correr, con lo que dio la última vez:

| Qué | Cómo | Resultado |
|---|---|---|
| Contratos de nbgrader | `python3 notebook/cuadernillos/build.py` | 6/6 semanas válidas |
| Los ejercicios corren y ninguno está regalado | `python3 notebook/cuadernillos/verificar.py` | 37/37 |
| Captura de telemetría en el navegador | `node backend/tests/telemetria/prueba_customjs.js` | 15/15 |
| Contrato backend ↔ Postgres | `prueba_backend.py` | 71/71 |
| Cadena completa de competencias | `prueba_fase7.py` | 13/13 |
| Cálculo del nivel (fronteras) | `go test ./internal/service/` | 13 casos |
| Compilación | `go build ./... && go vet ./...` | limpio |

Los dos últimos scripts necesitan un backend y una base vivos; las variables de
entorno están en su cabecera.

**`prueba_puente.sh` no hace falta.** Necesita la imagen del alumno, y se
comprobó por `git diff` que los cambios en `metrics_bridge.py` y
`tutor_bridge.py` son **solo comentarios**: no hay comportamiento que pueda
regresar. No se salta por comodidad, se salta porque no prueba nada nuevo.

## 3. Lo que NO se tocó, comprobado por git y no por memoria

El encargo prohibía tocar la autenticación LTI, el login y el reparto de
cuadernillos por nbgrader/nbexchange. Comprobación directa sobre las siete
fases:

```
git diff --name-only 5412c1b~1..HEAD | grep -iE 'lti|nbexchange|entregar|publicar|custom\.js|auth'
  → ningún fichero
```

Y en el Hub, el único cambio funcional de todo el encargo es retirar la
exportación de `STUDENT_METRICS_API_URL`, que en la Fase 2 se demostró
equivalente: con la variable, sin ella y con la vieja, las tres rutas resuelven
a `http://api_go:8080/api/exercises/attempts`.

### Los cuadernillos con entregas no se han tocado nunca

```
git diff --name-only 5412c1b~1..HEAD -- notebook/notebook_semana/semana_01 \
                                        notebook/notebook_semana/semana_02
  → 0 ficheros
```

`semana_01` tiene 6 entregas reales y `semana_02` está liberada. Re-etiquetarlas
en la Fase 6 no cambió su `.ipynb` porque el parámetro `competencias` no entra
en el notebook: se guarda aparte, en `competencias.json`. Verificado además con
el MD5 de los dos ficheros antes y después — idéntico.

**Consecuencia práctica: no hay que re-generar ni re-liberar nada.** Los
`grade_id` siguen siendo los mismos (14 en `semana_01`, 16 en `semana_02`), así
que `validate`, `submit` y `collect` de nbgrader siguen operando sobre
exactamente los mismos identificadores.

## 4. Las tres preguntas abiertas del encargo, respondidas

El encargo dejaba tres para resolver durante la ejecución:

**1. ¿El AVA está en LTI 1.3?** → **No. Está en LTI 1.1**, y con certeza. El
código importa `LTI11Authenticator`, configura `consumers` con clave y secreto
compartidos (OAuth 1.0a, no OIDC), y en producción hay 124 POST reales de Moodle
a `/hub/lti/launch`. El paquete trae `lti13` pero no está cableado. **El
diagrama C4 y el plan de grado dicen 1.3 y habría que corregirlos.**

**2. ¿Qué significan `I3`, `I4`, `I5`?** → La correspondencia ya existía en el
código: es `competencias.codigo_anterior`, y las descripciones coinciden
literalmente con las oficiales. `I1`=mCP17, `I3`=mCC87, `I4`=mCC103,
`I7`=mCP88; fuera de alcance `I2`=mCC85, `I5`=mCA14, `I6`=mCA65.

**3. ¿Qué umbrales para N1/N2/N3?** → En `service.NivelCompetencia`, como
constantes editables sin migrar la base, y justificados con los datos reales del
curso en `modelo_microcompetencias.md` §3. No cuentan fallos a secas —eso
castiga a quien más trabaja— sino cobertura y coste normalizados.

## 5. Lo que queda pendiente, y es del curso

Dos decisiones que no son técnicas y **no se han tomado por ti**:

1. **`mCP17` tiene dos definiciones que no coinciden.** El catálogo en la base
   dice «álgebra lineal, cálculo diferencial e integral y métodos numéricos»; el
   encargo dice «aplicar conocimientos matemáticos». Con la primera, ninguna de
   las siete etiquetas puestas es legítima. `database/migracion_v6.sql` alinea la
   descripción y está escrita y probada, **sin aplicar y sin conectar al
   instalador**. La otra salida es quitar las siete etiquetas.
2. **`mCC103` se quedó sin evidencia.** Ninguno de los 37 ejercicios pide
   «reconocer problemas de organizaciones tratables algorítmicamente». Medirla
   exige un ejercicio nuevo, no otra vuelta de etiquetas.

Y dos cosas que el despliegue necesita saber:

- **`database/migracion_v5.sql` no está aplicada a producción.** Está en el
  bucle del instalador, así que el próximo despliegue la aplica. Es aditiva,
  pero instala el trigger que limita a 2 competencias por ejercicio.
- **Reetiquetar no llega a la base con `git pull`.** `competencias.json` entra
  en la imagen del docente al construirla (`Dockerfile.docente:23`), no por bind
  mount. Hacen falta tres pasos: `git pull`, reconstruir la imagen, y
  `cargar-competencias` dentro del contenedor del docente.
- Al cargarlo, el contador de «ejercicios sin competencia» del panel pasará de
  **0 a 6**. Es el hueco declarado de la Fase 6, no una avería.
