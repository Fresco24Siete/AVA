#!/bin/bash
set -e

CURSO_ID="${CURSO_ID:-curso_default}"
ALUMNO_ROL="${ALUMNO_ROL:-estudiante}"
CUADERNILLO_ID="${CUADERNILLO_ID:-}"

# Asegurar directorios en el volumen compartido
mkdir -p "/srv/nbgrader/${CURSO_ID}" "/srv/nbgrader/exchange" "/srv/nbgrader/logs"

# Enlazar /srv/nbgrader a /home/jovyan/work/nbgrader para que la raíz del curso
# sea reconocida como subdirectorio de /home/jovyan/work por nbgrader
mkdir -p /home/jovyan/work
ln -sfn /srv/nbgrader /home/jovyan/work/nbgrader

if [ "$ALUMNO_ROL" = "instructor" ]; then
    echo "[entrypoint] Rol: instructor. Activando formgrader/create_assignment/course_list."
    jupyter nbextension enable    --sys-prefix create_assignment/main || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter nbextension disable   --sys-prefix assignment_list/main || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.assignment_list || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.assignment_list || true

    # Poblar automáticamente las tareas de muestra de notebook_semana en la carpeta source del curso
    mkdir -p "/srv/nbgrader/${CURSO_ID}/source/semana_1"
    mkdir -p "/srv/nbgrader/${CURSO_ID}/source/poc_backend"

    if [ -f "/home/jovyan/work/cuadernillo_ejercicios.ipynb" ]; then
        cp -n "/home/jovyan/work/cuadernillo_ejercicios.ipynb" "/srv/nbgrader/${CURSO_ID}/source/semana_1/cuadernillo_ejercicios.ipynb" 2>/dev/null || true
    fi
    if [ -f "/home/jovyan/work/cuadernillo_poc_backend.ipynb" ]; then
        cp -n "/home/jovyan/work/cuadernillo_poc_backend.ipynb" "/srv/nbgrader/${CURSO_ID}/source/poc_backend/cuadernillo_poc_backend.ipynb" 2>/dev/null || true
    fi
else
    echo "[entrypoint] Rol: estudiante. Activando assignment_list."
    jupyter nbextension enable     --sys-prefix assignment_list/main || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.assignment_list || true
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.assignment_list || true
    jupyter nbextension disable    --sys-prefix create_assignment/main || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.course_list || true

    # Trae el cuadernillo activo del curso (release publicado por el instructor)
    if [ -n "$CUADERNILLO_ID" ]; then
        nbgrader fetch_assignment "$CUADERNILLO_ID" --course "$CURSO_ID" || true
        origen=$(find "/home/jovyan/work/${CUADERNILLO_ID}" -maxdepth 1 -name '*.ipynb' 2>/dev/null | head -n1)
        if [ -n "$origen" ]; then
            cp "$origen" /home/jovyan/work/cuadernillo_actual.ipynb
        fi
    fi
fi

exec "$@"