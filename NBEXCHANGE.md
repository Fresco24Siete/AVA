# El intercambio de cuadernillos: nbexchange

Cómo llega un cuadernillo del docente al alumno y cómo vuelve, desde que el
exchange de nbgrader dejó de ser una carpeta compartida.

## El problema que resuelve

nbgrader da por hecho que docente y alumnos comparten un disco: «liberar» copia
`release/<tarea>/` a un buzón y «traer» la copia de ahí. En el AVA cada persona
corre en su propio contenedor, sin disco común, así que eso nunca funcionó para
el alumno. Lo que había en su lugar —copiar lo publicado a un volumen montado
solo-lectura en el alumno, y que el alumno entregara por HTTP al backend Go, que
escribía en el volumen del docente— dependía de dos volúmenes compartidos y de
que el backend montara el curso de nbgrader.

Ahora el exchange es un **servicio HTTP**: [nbexchange](https://github.com/edina/nbexchange),
un servicio de JupyterHub que guarda liberaciones y entregas y las sirve por una
API autenticada con los tokens que el propio Hub le da a cada contenedor. El
alumno no monta nada; un contenedor recién creado sobre una imagen de hace un
mes recibe lo que el docente liberó hace un minuto.

```
docente (formgrader / publicar-cuadernillo)
   │  release_assignment          ┌──────────────┐      fetch_assignment   alumno
   └────────────────────────────► │  nbexchange  │ ◄──────────────────── (entregar-cuadernillo,
   ┌──────────────────────────── │  :9000       │ ───────────────────►   al arrancar y al
   │  collect                     └──────┬───────┘      submit            abrir el panel)
   ▼                                     │ ¿quién es este token?
submitted/<user_id>/<tarea>/             ▼
                                   JupyterHub API (/hub/api/user, /hub/api/users/<x>)
```

## Las piezas

| Pieza | Dónde | Qué hace |
|---|---|---|
| Servicio | `nbexchange/Dockerfile`, contenedor `nbexchange` en `docker-compose.yml` | nbexchange 2.0.2 fijado a commit. SQLite + ficheros en el volumen `nbexchange_data`. Solo en `moodle_jupyter_net`, sin puertos publicados. |
| Identidad | `nbexchange/nbexchange_config.py` (`UsuarioAva`) | Con el token que trae cada petición le pregunta al Hub quién es y sus grupos (`formgrade-<curso>` = docente, `nbgrader-<curso>` = alumno). Con el token del servicio lee el `auth_state` y toma el **`user_id` de LTI** como nombre del alumno. |
| Registro en el Hub | `hub_config/jupyterhub_config.py`, `c.JupyterHub.services` + rol `nbexchange` | Servicio externo con `api_token = NBEXCHANGE_API_TOKEN` y scopes `read:users`, `admin:auth_state`. |
| Cliente | `notebook/nbexchange_cliente/` | Las clases de exchange de nbgrader que hablan HTTP (copiadas del plugin upstream, ver `ORIGEN.md`) más `ava.py`: autenticación con `JUPYTERHUB_API_TOKEN` y los ayudantes de los comandos. |
| Config de nbgrader | `notebook/nbgrader_config.py` | `c.ExchangeFactory.*` apunta al cliente; `c.Exchange.base_service_url = NBEXCHANGE_URL`. Igual en la imagen del alumno y en la del docente (la del docente se construye encima). |

### Por qué el alumno se llama por su `user_id` y no por su correo

La telemetría y las notas se guardan por el `user_id` numérico de Moodle
(`ALUMNO_ID`). Si el exchange usara el nombre del Hub —el correo—, `Collect`
dejaría la entrega en `submitted/<correo>/`, nbgrader calificaría a `<correo>`,
`registrar-notas` subiría la nota con ese id y el panel del alumno la buscaría
por el numérico: nunca se encontrarían. Por eso `UsuarioAva` lee el `auth_state`
y devuelve `user_id` como `name`; el correo y el nombre completo van al
gradebook como `email` y `full_name`.

### Por qué SQLite y no el Postgres de telemetría

El servicio guarda unas pocas filas por acción (quién liberó/trajo/entregó qué y
cuándo) y los ficheros van al disco de todos modos. Con SQLite en su propio
volumen el servicio no necesita estar en `backend_db_net` ni compartir nada con
la telemetría. Si algún día hace falta Postgres: cambiar `NBEX_DB_URL` en el
compose a `postgresql://...@postgres-database:5432/nbexchange` (una base
distinta de `ava`), añadir el servicio a `backend_db_net`, y listo; la
configuración la lee de la misma variable.

## El flujo, paso a paso

### Docente

1. Editar el cuadernillo en formgrader (`source/<tarea>/`).
2. **Generate** → `release/<tarea>/` sin soluciones.
3. **Publicar**, de una de dos formas:
   - `publicar-cuadernillo <tarea> [abre] [cierra] [--sin-activar]` en una
     terminal del contenedor del docente. Deja `release/<tarea>/ava_publicacion.json`
     con la ventana y la marca de activación, y libera en el servicio.
   - El botón **Release** de formgrader. Libera igual, sin ventana.
4. Los alumnos trabajan y entregan (desde dentro del cuadernillo).
5. **Collect** en formgrader → `submitted/<user_id>/<tarea>/`. Se puede repetir:
   trae solo lo nuevo. El panel del docente (`/panel-docente`) dice cuántas
   entregas hay sin recoger.
6. **Autograde**: califica y sube las notas al backend (el bloque de ayuda tiene «Subir notas» para repetirlo; `registrar-notas <tarea>` hace lo mismo desde el terminal).

«Activo» (la marca «Esta semana», la etiqueta de la telemetría y el cupo del
tutor) es **la liberación más reciente que esté en ventana**, salvo las hechas
con `--sin-activar`. Para corregir una errata de una semana anterior sin
quitarle el turno a la semana en curso: `publicar-cuadernillo semana_01 --sin-activar`.
El alumno recibe la corrección como `semana_01_v2.ipynb`, al lado de la suya.

Retirar una tarea: `borrar-cuadernillo <tarea>` (o Release otra vez en
formgrader, que hace «unrelease»). Deja de aparecerle al alumno; lo que ya tenga
en su carpeta se queda.

### Alumno

No hace nada distinto. Al arrancar su contenedor, y cada vez que abre su panel,
`entregar-cuadernillo` pregunta al servicio qué hay liberado para su curso, trae
lo que no tenga, respeta la ventana y escribe el índice. Entrega con el botón
de su cuadernillo, que llama a `panel_bridge` → `ava.entregar` → `submit`.

Si el servicio no responde, el alumno sigue viendo lo que ya tenía; el panel
se dibuja igual.

## Operación

### Variables

| Variable | Dónde | Valor |
|---|---|---|
| `NBEXCHANGE_API_TOKEN` | `.env` | `openssl rand -hex 32`. Lo reciben el Hub (registro del servicio) y el servicio (`JUPYTERHUB_API_TOKEN`). |
| `NBEXCHANGE_URL` | compose → Hub → contenedores | `http://nbexchange:9000`. |
| `NBEX_DB_URL`, `NBEX_BASE_STORE`, `NBEX_MAX_BUFFER_SIZE` | compose → servicio | Base, almacén y tope de subida (50 MB; el cliente usa el mismo). |

### Rotar el token

1. Generar uno nuevo: `openssl rand -hex 32`.
2. Ponerlo en `NBEXCHANGE_API_TOKEN` del `.env`.
3. `docker compose up -d jupyterhub nbexchange` (recrea los dos; el Hub
   actualiza el token del servicio en su base al arrancar).

Los contenedores de alumnos y docente no se enteran: ellos se presentan con su
propio `JUPYTERHUB_API_TOKEN`, no con este.

### Comprobar que está vivo

```bash
docker compose ps nbexchange            # healthy
docker compose logs --tail 50 nbexchange
docker exec jupyterhub python -c "import urllib.request;print(urllib.request.urlopen('http://nbexchange:9000/services/nbexchange/').read())"
```

Si el servicio responde 503 con «El servicio no está autorizado en JupyterHub»
o «no puede leer el auth_state», el token no coincide entre `.env`/Hub/servicio,
o el Hub no registró el rol (revisar el aviso de `NBEXCHANGE_API_TOKEN` en el
log del Hub).

### Respaldo

Todo el estado del exchange está en el volumen `nbexchange_data`
(`nbexchange.sqlite` + `almacen/`). Las entregas recogidas ya están también en
`nbgrader_shared` (`submitted/`).

### Actualizar nbexchange

Cambiar `NBEXCHANGE_COMMIT` en `nbexchange/Dockerfile` y reconstruir; el
servicio aplica las migraciones de su base al arrancar (`--upgrade-db`, que
antes hace copia de la SQLite). El cliente copiado en
`notebook/nbexchange_cliente/` se actualiza aparte (ver su `ORIGEN.md`).

## Pruebas

`bash nbexchange/pruebas/prueba_integracion.sh` recorre release → fetch →
republicación → submit ×2 → collect → permisos → unrelease con el servicio real,
el cliente real dentro de las imágenes del AVA y un Hub simulado (solo responde
quién es cada token). Tarda alrededor de un minuto y no toca el despliegue.

La prueba con el Hub real (LTI, DockerSpawner) está descrita en
`nbexchange/pruebas/README.md`.
