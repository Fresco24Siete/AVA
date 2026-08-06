#!/bin/bash
set -e

CURSO_ID="${CURSO_ID:-curso_default}"
ALUMNO_ROL="${ALUMNO_ROL:-estudiante}"

# ---------------------------------------------------------------------------
# IMPORTANTE: el volumen compartido /srv/nbgrader SOLO se monta en contenedores
# de instructor (ver jupyterhub_config.py). En el contenedor de un estudiante
# esa ruta no existe, y no debe existir: ahí viven las soluciones del profesor
# y los envíos de los demás alumnos.
#
# Por eso todo lo relacionado con /srv/nbgrader vive dentro de la rama
# 'instructor'. Antes se hacía mkdir + symlink para AMBOS roles, lo que
# (a) filtraba las soluciones a los alumnos y (b) tumbaba el contenedor si el
# volumen tenía dueño root: mkdir fallaba y 'set -e' mataba el arranque.
# ---------------------------------------------------------------------------

mkdir -p /home/jovyan/work

if [ "$ALUMNO_ROL" = "instructor" ]; then
    echo "[entrypoint] Rol: instructor. Activando extensiones de formgrader."

    # Estos mkdir NO deben ser fatales: si el volumen nbgrader_shared quedó con
    # dueño root de una build anterior, preferimos arrancar y dejar el error en
    # el log a que el contenedor muera sin explicación.
    if ! mkdir -p "/srv/nbgrader/${CURSO_ID}/source/semana_1" \
                  "/srv/nbgrader/exchange" \
                  "/srv/nbgrader/logs" 2>/dev/null; then
        echo "[entrypoint] AVISO: no se pudo escribir en /srv/nbgrader." >&2
        echo "[entrypoint] Suele ser que el volumen 'nbgrader_shared' pertenece a root." >&2
        echo "[entrypoint] Solución: docker volume rm nbgrader_shared (se recrea al vuelo)." >&2
    fi

    # nbgrader exige que la raíz del curso sea subdirectorio del root del server
    ln -sfn /srv/nbgrader /home/jovyan/work/nbgrader

    # Carpeta de cuadernillos PUBLICADOS (versión liberada, sin soluciones) que
    # verán los alumnos. El instructor publica ahí con 'publicar-cuadernillo'.
    mkdir -p "/srv/publicados/${CURSO_ID}" 2>/dev/null || true
    ln -sfn "/srv/publicados/${CURSO_ID}" /home/jovyan/work/publicados 2>/dev/null || true

    jupyter nbextension enable    --sys-prefix create_assignment/main || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter nbextension disable   --sys-prefix assignment_list/main || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.assignment_list || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.assignment_list || true

    # Sembrar el cuadernillo plantilla en source/ la primera vez (cp -n no pisa
    # lo que el profesor ya haya editado desde formgrader). La plantilla vive en
    # /opt/plantillas (ya NO en work/, para que el alumno no la reciba estática).
    if [ -f "/opt/plantillas/cuadernillo_ejercicios.ipynb" ]; then
        cp -n "/opt/plantillas/cuadernillo_ejercicios.ipynb" \
              "/srv/nbgrader/${CURSO_ID}/source/semana_1/cuadernillo_ejercicios.ipynb" 2>/dev/null || true
    fi

else
    echo "[entrypoint] Rol: estudiante. Preparando entorno estático."

    # El alumno no monta /srv/nbgrader. Si quedó un symlink colgado de una
    # imagen anterior, lo quitamos para que no muestre un enlace roto.
    rm -f /home/jovyan/work/nbgrader 2>/dev/null || true

    jupyter nbextension disable    --sys-prefix create_assignment/main || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.course_list || true

    # Cerrar la puerta a JupyterLab: el alumno solo debe ver el cuadernillo.
    # (En la imagen que está corriendo hoy, jupyterlab 3.6.8 SÍ está activo.)
    jupyter server extension disable --sys-prefix jupyterlab || true
    jupyter serverextension disable --sys-prefix jupyterlab || true

    # Entregar el cuadernillo ACTIVO que publicó el instructor (nbgrader manda,
    # no el backend). El script lee el manifest del volumen de publicados,
    # valida la ventana de tiempo y deja el notebook en work/cuadernillo.ipynb.
    # Devuelve el código del cuadernillo, que exportamos para la telemetría.
    CODIGO_ENTREGADO="$(python3 /usr/local/bin/entregar-cuadernillo 2>/dev/null || echo '')"
    # Solo se pisa el valor si la entrega devolvió algo. Antes, un fallo de
    # entregar-cuadernillo dejaba CUADERNILLO_CODIGO vacío aunque el Hub hubiera
    # pasado uno; el tutor cuenta las 5 preguntas POR cuadernillo usando esta
    # variable, así que con el valor vacío todos los cuadernillos comparten un
    # único cupo de 5.
    if [ -n "$CODIGO_ENTREGADO" ]; then
        CUADERNILLO_CODIGO="$CODIGO_ENTREGADO"
    fi
    export CUADERNILLO_CODIGO
    export CUADERNILLO_ID="$CUADERNILLO_CODIGO"
    echo "[entrypoint] Cuadernillo activo entregado: '${CUADERNILLO_CODIGO:-(ninguno)}'"
    if [ -z "$CUADERNILLO_CODIGO" ]; then
        echo "[entrypoint] AVISO: sin código de cuadernillo. El tutor contará las 5" >&2
        echo "[entrypoint] preguntas de forma global, no por cuadernillo." >&2
    fi
fi

exec "$@"
