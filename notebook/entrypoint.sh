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

    jupyter nbextension enable    --sys-prefix create_assignment/main || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter nbextension disable   --sys-prefix assignment_list/main || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.assignment_list || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.assignment_list || true

    # Sembrar el cuadernillo plantilla en source/ la primera vez (cp -n no pisa
    # lo que el profesor ya haya editado desde formgrader).
    if [ -f "/home/jovyan/work/cuadernillo_ejercicios.ipynb" ]; then
        cp -n "/home/jovyan/work/cuadernillo_ejercicios.ipynb" \
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

    # Copiar el cuadernillo estático de la semana al espacio de trabajo
    if [ -d "/home/jovyan/work/notebook_semana" ]; then
        cp -rn /home/jovyan/work/notebook_semana/* /home/jovyan/work/ 2>/dev/null || true
    fi
fi

exec "$@"
