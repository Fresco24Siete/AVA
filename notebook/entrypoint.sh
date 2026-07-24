#!/bin/bash
set -e

CURSO_ID="${CURSO_ID:-curso_default}"
ALUMNO_ROL="${ALUMNO_ROL:-estudiante}"

# Asegurar directorios en el volumen compartido
mkdir -p "/srv/nbgrader/${CURSO_ID}" "/srv/nbgrader/exchange" "/srv/nbgrader/logs"

# Enlazar /srv/nbgrader a /home/jovyan/work/nbgrader para mantener la estructura interna
mkdir -p /home/jovyan/work
ln -sfn /srv/nbgrader /home/jovyan/work/nbgrader

if [ "$ALUMNO_ROL" = "instructor" ]; then
    echo "[entrypoint] Rol: instructor. Activando extensiones de formgrader."
    jupyter nbextension enable    --sys-prefix create_assignment/main || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter nbextension disable   --sys-prefix assignment_list/main || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.assignment_list || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.assignment_list || true

    # Crear carpetas base para el profesor
    mkdir -p "/srv/nbgrader/${CURSO_ID}/source/semana_1"
    
    if [ -f "/home/jovyan/work/cuadernillo_ejercicios.ipynb" ]; then
        cp -n "/home/jovyan/work/cuadernillo_ejercicios.ipynb" "/srv/nbgrader/${CURSO_ID}/source/semana_1/cuadernillo_ejercicios.ipynb" 2>/dev/null || true
    fi

else
    echo "[entrypoint] Rol: estudiante. Preparando entorno estático."
    jupyter nbextension disable    --sys-prefix create_assignment/main || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.course_list || true

    # Copiar automáticamente el cuadernillo estático de la semana al espacio de trabajo del alumno
    if [ -d "/home/jovyan/work/notebook_semana" ]; then
        cp -rn /home/jovyan/work/notebook_semana/* /home/jovyan/work/ 2>/dev/null || true
    fi
fi

exec "$@"