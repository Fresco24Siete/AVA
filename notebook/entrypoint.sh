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
    if ! mkdir -p "/srv/nbgrader/${CURSO_ID}/source" \
                  "/srv/nbgrader/logs" 2>/dev/null; then
        echo "[entrypoint] AVISO: no se pudo escribir en /srv/nbgrader." >&2
        echo "[entrypoint] Suele ser que el volumen 'nbgrader_shared' pertenece a root." >&2
        echo "[entrypoint] Solución: docker volume rm nbgrader_shared (se recrea al vuelo)." >&2
    fi

    # nbgrader exige que la raíz del curso sea subdirectorio del root del server
    ln -sfn /srv/nbgrader /home/jovyan/work/nbgrader
    # Restos de cuando lo publicado se copiaba a un volumen compartido. Ahora se
    # libera en el servicio de intercambio (publicar-cuadernillo).
    rm -f /home/jovyan/work/publicados 2>/dev/null || true

    jupyter nbextension enable    --sys-prefix create_assignment/main || true
    # Las pestanas "Formgrader" y "Courses" del arbol de archivos: sin ellas,
    # desde /tree no habia camino de vuelta a formgrader salvo escribir la URL.
    jupyter nbextension enable    --sys-prefix formgrader/main --section=tree || true
    jupyter nbextension enable    --sys-prefix course_list/main --section=tree || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter serverextension enable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.formgrader || true
    jupyter server extension enable --sys-prefix nbgrader.server_extensions.course_list || true
    jupyter nbextension disable   --sys-prefix assignment_list/main || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.assignment_list || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.assignment_list || true

    # Sembrar los cuadernillos plantilla en source/ la primera vez (cp -n no pisa
    # lo que el profesor ya haya editado desde formgrader). Las plantillas viven
    # en /opt/plantillas (ya NO en work/, para que el alumno no las reciba
    # estáticas).
    #
    # Cada SUBCARPETA de /opt/plantillas es una tarea de nbgrader y su nombre es
    # el cuadernillo_id: 'semana_01/' -> source/semana_01/. Ese mismo id es el
    # que 'publicar-cuadernillo' escribe en el manifest y el que el tutor usa
    # para contar las 5 preguntas por cuadernillo.
    for plantilla in /opt/plantillas/*/; do
        [ -d "$plantilla" ] || continue
        tarea="$(basename "$plantilla")"
        if mkdir -p "/srv/nbgrader/${CURSO_ID}/source/${tarea}" 2>/dev/null; then
            cp -n "$plantilla"*.ipynb \
                  "/srv/nbgrader/${CURSO_ID}/source/${tarea}/" 2>/dev/null || true
            echo "[entrypoint] Cuadernillo disponible en formgrader: ${tarea}"
        fi
    done

    # La plantilla suelta de la demo ya no se siembra. Creaba una actividad
    # 'semana_1' que el docente no habia pedido, indistinguible a simple vista de
    # 'semana_01' —las dos se leen «Semana 1»— y que volvia a aparecer cada vez
    # que el docente entraba, por mucho que la borrara: el mkdir de arriba creaba
    # su carpeta y este cp la rellenaba. Se borro dos veces en produccion y
    # reaparecio las dos.

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
    # La pestaña «Assignments» de nbgrader tampoco: con el exchange por HTTP
    # funcionaría, y el alumno tendría dos formas distintas de traer y entregar
    # el mismo cuadernillo. La del AVA es el panel (entregar-cuadernillo y el
    # botón de entregar dentro del cuadernillo).
    jupyter nbextension disable   --sys-prefix assignment_list/main || true
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.assignment_list || true
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.assignment_list || true

    # Cerrar la puerta a JupyterLab: el alumno solo debe ver el cuadernillo.
    # (En la imagen que está corriendo hoy, jupyterlab 3.6.8 SÍ está activo.)
    jupyter server extension disable --sys-prefix jupyterlab || true
    jupyter serverextension disable --sys-prefix jupyterlab || true

    # Traer los cuadernillos que publicó el instructor (nbgrader manda, no el
    # backend). El script pregunta al servicio de intercambio qué hay liberado
    # para este curso, valida la ventana de tiempo y deja cada uno en
    # work/<id>.ipynb. Devuelve el código del activo, que exportamos para la
    # telemetría. Si el servicio no responde, se queda con lo que ya había.
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
