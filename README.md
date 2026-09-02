# AVA — Ambiente Virtual de Aprendizaje

Plataforma del curso **41333 Algoritmos y Programación** (Ingeniería en
Inteligencia Artificial, UIS). El estudiante entra desde Moodle, se le abre su
propio Jupyter con el cuadernillo de la semana, trabaja, entrega, y su nota
vuelve a Moodle. Por debajo, cada intento y cada error quedan registrados para
poder responder una pregunta concreta: **en qué competencia se está atascando
cada estudiante**.

No es un JupyterHub con nbgrader encima. Las piezas propias —el puente de
telemetría, el panel del alumno, el panel del docente, el tutor de IA y el
constructor de cuadernillos— son la mitad del proyecto.

## Qué hace, en una frase por pieza

| Pieza | Para qué |
|---|---|
| **Moodle** | Es la puerta. Autentica por LTI 1.1 y recibe las notas de vuelta |
| **JupyterHub** | Da a cada persona un contenedor propio, con su rol y su cuadernillo |
| **nbgrader** | Publica los cuadernillos y califica las entregas |
| **nbexchange** | El intercambio entre docente y alumnos, por HTTP |
| **Backend Go** | Recibe la telemetría, guarda notas y sirve los paneles |
| **PostgreSQL** | Los eventos: intentos, errores, notas, valoraciones |
| **Caddy** | La puerta de entrada. TLS y la cabecera que permite el marco de Moodle |

## Arquitectura en corto

```
Moodle ──LTI 1.1──> Caddy ──> JupyterHub ──spawn──> contenedor del alumno
                                   │                        │
                                   │                        ├─ custom.js (telemetría)
                                   │                        ├─ panel_bridge (panel del alumno)
                                   │                        └─ tutor_bridge (tutor IA)
                                   │                        │
                                   └──── backend Go <───────┘
                                              │
                                         PostgreSQL
```

El detalle completo está en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Stack

- **Backend:** Go 1.25 · Gin · sqlx · PostgreSQL 16
- **Notebooks:** Python 3.11 · JupyterHub 5.5 · nbclassic 1.3 · nbgrader 0.8.5
- **Intercambio:** nbexchange 2.0.2 (cliente vendorizado en `notebook/nbexchange_cliente/`)
- **Proxy:** Caddy 2.8
- **Orquestación:** Docker Compose · DockerSpawner
- **Tutor IA:** Gemini

## Requisitos previos

- Docker Engine y Docker Compose v2
- Un dominio apuntando a la máquina (para el modo público) **o** Tailscale (para el modo túnel)
- Una actividad *Herramienta externa* en Moodle, con calificación activada
- Opcional: claves de API de Gemini, para el tutor

## Instalación

Todo el ciclo lo hace un script. Es idempotente: se puede repetir.

```bash
git clone https://github.com/Fresco24Siete/AVA.git ~/AVA
cd ~/AVA
bash servidor/instalar.sh
```

Comprueba la máquina, genera los secretos, ajusta los límites de memoria a la
RAM disponible, construye las imágenes **en el orden correcto**, levanta el
stack, aplica las migraciones y verifica que quedó funcionando. Al final imprime
la URL de lanzamiento, la clave y el secreto para pegar en Moodle.

Para solo comprobar, sin tocar nada:

```bash
bash servidor/instalar.sh --verificar
```

### Los dos modos

Lo decide `AVA_DOMINIO` en el `.env`:

- **Vacío → modo túnel.** Para un computador de escritorio detrás de NAT. Caddy
  escucha solo en `127.0.0.1:8081` y el TLS lo pone Tailscale Funnel.
- **Con valor → modo público.** Para un servidor con IP propia. Caddy toma 80 y
  443 y saca el certificado él mismo.

### Levantar a mano

```bash
docker compose -p ava up -d
```

El `.env` fija `COMPOSE_FILE` y `COMPOSE_PROJECT_NAME`, así que un `up` a secas
ya usa los ficheros correctos.

> **Cuidado con el orden de las imágenes.** La del docente hereda de la del
> alumno (`Dockerfile.docente` empieza por `FROM mi_imagen_jupyterlab:latest`).
> Construir solo la del docente deja dentro el código viejo de `notebook/`, y el
> fallo aparece mucho después y en otro sitio.
>
> ```bash
> docker build -t mi_imagen_jupyterlab:latest ./notebook
> docker build -t mi_imagen_jupyterlab_docente:latest -f ./notebook/Dockerfile.docente ./notebook
> ```

## Variables de entorno

Se generan solas al crear el `.env`. La plantilla comentada está en
[.env.example](.env.example).

### Cómo se publica

| Variable | Para qué |
|---|---|
| `AVA_DOMINIO` | Dominio público. Vacío = detrás de un túnel |
| `AVA_MOODLE` | El Moodle que puede embeber el AVA en un marco |
| `COMPOSE_FILE` · `COMPOSE_PROJECT_NAME` | Fijan los ficheros de compose |

### Base de datos

`DB_USER` · `DB_PASSWORD` · `DB_NAME` · `DB_HOST` · `DB_PORT`

> `POSTGRES_PASSWORD` solo se aplica al **inicializar** el volumen. Cambiarla
> después no cambia la contraseña de una base que ya existe.

### JupyterHub y LTI

| Variable | Para qué |
|---|---|
| `JUPYTERHUB_CRYPT_KEY` | Cifra el `auth_state`. Regenerarla invalida las sesiones |
| `LTI_CLIENT_KEY` · `LTI_CLIENT_SECRET` | Deben coincidir con la actividad de Moodle |
| `MEM_LIMIT_ALUMNO` · `MEM_LIMIT_INSTRUCTOR` | Topes por contenedor, calculados con la RAM |

### Telemetría

| Variable | Para qué |
|---|---|
| `ENVIAR_AL_BACKEND` | `false` = modo simulación: **no se guarda nada** |
| `METRICS_API_TOKEN` | Token maestro con el que el Hub pide tokens por alumno |
| `METRICS_TOKEN_SECRET` | Firma los tokens. Vacío = la ingesta no verifica identidad |
| `STUDENT_METRICS_API_BASE` | Base del backend a la que apunta el puente |
| `CORS_ORIGENES` | Orígenes permitidos. Sin valor, no se monta CORS |

> `ENVIAR_AL_BACKEND=false` es silencioso y caro: el AVA funciona entero, el
> alumno no ve ningún error y el navegador recibe 200, pero no se guarda ni un
> intento. El instalador avisa si lo encuentra apagado.

### Tutor IA

`GOOGLE_API_KEY_1` · `GOOGLE_API_KEY_2` · `TUTOR_ALIAS` · `TUTOR_MODELO` ·
`TUTOR_IA_HABILITADO` · `TUTOR_MAX_PREGUNTAS`

Sin claves el tutor responde 503 y el alumno lee «no está disponible», que
parece una avería del AVA.

### Intercambio

`NBEXCHANGE_API_TOKEN` — el mismo que recibe el servicio y con el que el Hub lo
reconoce.

## Cuadernillos

Los `.ipynb` son **salida generada**, no fuente. Se edita el generador en
Python:

```bash
python3 notebook/cuadernillos/build.py             # todos
python3 notebook/cuadernillos/build.py semana_03   # uno
python3 notebook/cuadernillos/verificar.py         # ejecuta y comprueba
```

`build.py` valida los contratos de nbgrader; `verificar.py` **ejecuta** las
celdas y comprueba que la solución pase y que la plantilla del alumno falle.
Detalles en [notebook/cuadernillos/README.md](notebook/cuadernillos/README.md).

## Documentación

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — servicios, redes, LTI y cuadernillos
- [docs/API.md](docs/API.md) — endpoints del backend y esquema de la base
- [docs/TELEMETRIA.md](docs/TELEMETRIA.md) — el pipeline completo, de la celda a la tabla
