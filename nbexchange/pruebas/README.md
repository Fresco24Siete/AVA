# Pruebas del intercambio

## 1. Sin Hub: `prueba_integracion.sh`

```bash
bash nbexchange/pruebas/prueba_integracion.sh
```

Levanta el servicio nbexchange de verdad y un JupyterHub de mentira
(`hub_falso.py`, que solo contesta quién es cada token), y recorre el ciclo
entero con el cliente real dentro de las imágenes del AVA
(`mi_imagen_jupyterlab:latest` y `mi_imagen_jupyterlab_docente:latest`, que
deben estar construidas): publicar → dos alumnos nuevos traen → el docente
corrige y republica `--sin-activar` → entregan → Collect → lo que un alumno no
puede hacer → retirar. Un minuto, sin tocar el despliegue. Termina en `TODO OK`
o con el log del paso que falló.

## 2. Con el Hub real: LTI + DockerSpawner

Es la prueba que cierra el criterio de aceptación («un release seguido de un
fetch desde un contenedor recién creado, sin rebuild, trae el cuadernillo»).
Hecha el 2026-08-22 en local; los pasos, para repetirla:

```bash
# Imágenes con los nombres que espera jupyterhub_config.py
docker build -t mi_imagen_jupyterlab:latest notebook
docker build -t mi_imagen_jupyterlab_docente:latest -f notebook/Dockerfile.docente notebook
docker volume create nbgrader_shared

# .env con DB_*, JUPYTERHUB_CRYPT_KEY, LTI_CLIENT_KEY/SECRET, METRICS_API_TOKEN,
# METRICS_TOKEN_SECRET y NBEXCHANGE_API_TOKEN (openssl rand -hex 32 para los tokens)
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build

# Lanzamientos LTI firmados, sin Moodle (usa LTI_CLIENT_KEY/SECRET del entorno)
set -a; . ./.env; set +a; python3 nbexchange/pruebas/lti_falso.py &
open 'http://localhost:9999/?rol=Instructor&user=9002&email=docente@ejemplo.test&curso=28053'
```

Con el docente dentro:

```bash
DOC=$(docker ps --format '{{.Names}}' | grep jupyter-docente)
docker exec -w /home/jovyan/work/nbgrader/28053 $DOC nbgrader generate_assignment semana_01 --force
docker exec $DOC publicar-cuadernillo semana_01
```

Luego un alumno **nuevo** (otro correo, otro `user`):

```
http://localhost:9999/?rol=Learner&user=3135&email=ana@ejemplo.test&curso=28053
```

Qué se comprobó y cómo:

| Qué | Cómo | Resultado del 2026-08-22 |
|---|---|---|
| El alumno no monta nada compartido | `docker inspect jupyter-ana-… --format '{{json .Mounts}}'` | solo `ava-trabajo-ana-…` → `/home/jovyan/work` |
| Recibe el cuadernillo publicado | `sha256sum` de `work/semana_01.ipynb` en el alumno y de `release/semana_01/cuadernillo.ipynb` en el docente | iguales (`46fd482bbd85`) |
| `CUADERNILLO_CODIGO` | log del contenedor: `[entrypoint] Cuadernillo activo entregado: 'semana_01'` | ✓ |
| Entrega | botón «Guardar y entregar» en el cuadernillo | `Submitted as: 28053 semana_01 …`; en el servicio, `almacen/1/submitted/28053/semana_01/3135/…` |
| Collect | botón de formgrader | `submitted/3135/semana_01/{cuadernillo.ipynb,timestamp.txt}`; gradebook: `('3135','Ana','Local','ana@ejemplo.test','3135')` |
| Nota | `nbgrader autograde` + `registrar-notas semana_01` | `cuadernillo_notas`: `3135 semana_01 3/25`; el panel de Ana: «Nota 3 / 25 · Entregado el 22/08 a las 22:58» |

El identificador del alumno es el mismo en los tres sitios (`3135`: exchange,
gradebook, telemetría), que es lo que hace que la nota le llegue al panel.
