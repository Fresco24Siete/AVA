#!/bin/bash
set -e

CURSO_ID="${CURSO_ID:-curso_default}"
ALUMNO_ROL="${ALUMNO_ROL:-estudiante}"
CUADERNILLO_ID="${CUADERNILLO_ID:-}"

mkdir -p "/srv/nbgrader/${CURSO_ID}" "/srv/nbgrader/exchange" "/srv/nbgrader/logs"

if [ "$ALUMNO_ROL" = "instructor" ]; then
    echo "[entrypoint] Rol: instructor. Activando formgrader/create_assignment/course_list."
    jupyter nbextension enable    --sys-prefix create_assignment/main || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter nbextension disable   --sys-prefix assignment_list/main || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.assignment_list || true
else
    echo "[entrypoint] Rol: estudiante. Activando assignment_list."
    jupyter nbextension enable     --sys-prefix assignment_list/main || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.assignment_list || true
    jupyter nbextension disable    --sys-prefix create_assignment/main || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.course_list || true

    # Trae el cuadernillo activo del curso (release publicado por el
    # instructor) directo al workspace del estudiante, sin que tenga que
    # buscarlo ni hacer fetch manual.
    if [ -n "$CUADERNILLO_ID" ]; then
        nbgrader fetch_assignment "$CUADERNILLO_ID" --course "$CURSO_ID" || true
        # normaliza el nombre para que default_url siempre apunte al mismo archivo
        origen=$(find "/home/jovyan/work/${CUADERNILLO_ID}" -maxdepth 1 -name '*.ipynb' | head -n1)
        if [ -n "$origen" ]; then
            cp "$origen" /home/jovyan/work/cuadernillo_actual.ipynb
        fi
    fi
fi

exec "$@"