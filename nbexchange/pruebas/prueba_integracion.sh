#!/usr/bin/env bash
# Prueba de integración del exchange: release -> fetch -> submit -> collect,
# con el servicio nbexchange de verdad, el cliente de verdad (dentro de la imagen
# del AVA) y un JupyterHub de mentira que solo responde quién es cada token.
#
#   bash nbexchange/pruebas/prueba_integracion.sh
#
# Levanta tres contenedores en una red propia (hub falso, nbexchange, y uno por
# paso con la imagen del alumno/docente), y los tira al terminar. No toca los
# volúmenes ni la red del despliegue. Tarda ~1 minuto.
#
# Lo que comprueba, en orden:
#   1. El docente publica (publicar-cuadernillo) y el servicio la lista.
#   2. Un alumno NUEVO (contenedor recién creado, sin volumen previo) la trae
#      con entregar-cuadernillo y el contenido es el publicado.
#   3. El docente corrige y republica --sin-activar: el alumno recibe la
#      versión nueva AL LADO (semana_01_v2) y el activo no cambia.
#   4. Dos alumnos entregan; el docente recoge con Collect y cada entrega está
#      bajo el user_id LTI del alumno correcto, con su nombre en el gradebook.
#   5. Un alumno no puede liberar, ni recoger, ni ver otro curso.
#   6. El docente retira la tarea y deja de estar publicada.
set -euo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$AQUI/../.." && pwd)"
IMAGEN_ALUMNO="${IMAGEN_ALUMNO:-mi_imagen_jupyterlab:latest}"
IMAGEN_DOCENTE="${IMAGEN_DOCENTE:-mi_imagen_jupyterlab_docente:latest}"
IMAGEN_NBEX="${IMAGEN_NBEX:-ava-nbexchange:prueba}"
RED="ava-nbex-prueba"
TOKEN_SERVICIO="servicio-$(date +%s)"
CURSO="28053"
OTRO_CURSO="99999"

# Usuarios del Hub falso: token -> {name (correo), groups, auth_state (LTI)}.
USUARIOS='{
  "tok-docente": {"name": "docente@uis.edu.co", "groups": ["formgrade-28053"],
                  "auth_state": {"user_id": "7", "lis_person_name_full": "Docente Prueba",
                                 "lis_person_contact_email_primary": "docente@uis.edu.co",
                                 "context_title": "Curso de prueba"}},
  "tok-ana":     {"name": "ana@uis.edu.co", "groups": ["nbgrader-28053"],
                  "auth_state": {"user_id": "3135", "lis_person_name_full": "Ana Prueba",
                                 "lis_person_contact_email_primary": "ana@uis.edu.co"}},
  "tok-beto":    {"name": "beto@uis.edu.co", "groups": ["nbgrader-28053"],
                  "auth_state": {"user_id": "3136", "lis_person_name_full": "Beto Prueba",
                                 "lis_person_contact_email_primary": "beto@uis.edu.co"}},
  "tok-ajeno":   {"name": "ajeno@uis.edu.co", "groups": ["nbgrader-99999"],
                  "auth_state": {"user_id": "5000", "lis_person_name_full": "Ajeno"}}
}'

limpiar() {
    docker rm -f nbex-prueba hub-falso-prueba >/dev/null 2>&1 || true
    docker volume rm -f nbex-prueba-curso nbex-prueba-ana nbex-prueba-beto nbex-prueba-ajeno >/dev/null 2>&1 || true
    docker network rm "$RED" >/dev/null 2>&1 || true
}
trap limpiar EXIT
limpiar

echo "== Construyendo la imagen del servicio =="
docker build -q -t "$IMAGEN_NBEX" "$RAIZ/nbexchange" >/dev/null

docker network create "$RED" >/dev/null
docker volume create nbex-prueba-curso >/dev/null

docker run -d --name hub-falso-prueba --network "$RED" \
    -e HUB_FALSO_USUARIOS="$USUARIOS" -e HUB_FALSO_TOKEN_SERVICIO="$TOKEN_SERVICIO" \
    -v "$AQUI/hub_falso.py:/hub_falso.py:ro" python:3.12-slim python /hub_falso.py >/dev/null

docker run -d --name nbex-prueba --network "$RED" \
    -e JUPYTERHUB_API_URL=http://hub-falso-prueba:8081/hub/api \
    -e JUPYTERHUB_API_TOKEN="$TOKEN_SERVICIO" \
    -e NBEX_DB_URL=sqlite:////var/nbexchange/nbexchange.sqlite \
    "$IMAGEN_NBEX" >/dev/null

echo -n "Esperando al servicio "
for i in $(seq 1 30); do
    if docker run --rm --network "$RED" python:3.12-slim python -c \
        "import urllib.request;urllib.request.urlopen('http://nbex-prueba:9000/services/nbexchange/',timeout=2)" 2>/dev/null; then
        echo " listo"; break
    fi
    echo -n "."; sleep 1
    [ "$i" = 30 ] && { echo; docker logs nbex-prueba; exit 1; }
done

# Corre un paso de cliente.py dentro de la imagen, con el entorno de ese rol.
#   paso <rol> <token> <volumen-work> [VAR=valor ...]
paso() {
    local rol="$1" token="$2" vol="$3"; shift 3
    local imagen="$IMAGEN_ALUMNO" extra=()
    if [ "$rol" = instructor ]; then
        imagen="$IMAGEN_DOCENTE"
        extra=(-v nbex-prueba-curso:/srv/nbgrader)
    fi
    local paso_nombre="${!#}"
    for kv in "$@"; do [[ "$kv" == *=* ]] && extra+=(-e "$kv"); done
    # (${extra[@]+...}: un array vacío con set -u rompe en bash 3, el de macOS)
    docker run --rm --network "$RED" ${extra[@]+"${extra[@]}"} \
        -v "$vol:/home/jovyan/work" \
        -v "$AQUI/cliente.py:/tmp/cliente.py:ro" \
        -e CURSO_ID="$CURSO" -e ALUMNO_ROL="$rol" -e JUPYTERHUB_API_TOKEN="$token" \
        -e NBEXCHANGE_URL=http://nbex-prueba:9000 -e PRUEBA_OTRO_CURSO="$OTRO_CURSO" \
        --entrypoint bash "$imagen" -c \
        "if [ '$rol' = instructor ]; then mkdir -p /srv/nbgrader/$CURSO && ln -sfn /srv/nbgrader /home/jovyan/work/nbgrader; fi; cd /home/jovyan/work && python /tmp/cliente.py $paso_nombre"
}

fallos=0
comprobar() {
    local nombre="$1"; shift
    if "$@" > /tmp/nbex-prueba-paso.log 2>&1 && grep -q "^OK " /tmp/nbex-prueba-paso.log; then
        echo "[OK]    $nombre"
    else
        echo "[FALLO] $nombre"; fallos=$((fallos+1))
        sed 's/^/        | /' /tmp/nbex-prueba-paso.log | tail -25
    fi
}

echo "== 1. El docente publica =="
comprobar "publicar-cuadernillo semana_01" paso instructor tok-docente nbex-prueba-curso publicar

echo "== 2. Alumnos nuevos la traen (contenedor y volumen recién creados) =="
comprobar "ana trae semana_01" paso estudiante tok-ana nbex-prueba-ana "PRUEBA_ESPERA_TEXTO=versión A" traer
comprobar "beto trae semana_01" paso estudiante tok-beto nbex-prueba-beto "PRUEBA_ESPERA_TEXTO=versión A" traer

echo "== 3. El docente corrige y republica sin activar =="
comprobar "republicar --sin-activar" paso instructor tok-docente nbex-prueba-curso republicar
comprobar "ana recibe semana_01_v2 y el activo sigue" paso estudiante tok-ana nbex-prueba-ana \
    "PRUEBA_ESPERA_ARCHIVO=semana_01_v2.ipynb" "PRUEBA_ESPERA_TEXTO=versión B" "PRUEBA_ESPERA_ACTIVO=semana_01" traer

echo "== 4. Entregan y el docente recoge =="
comprobar "ana entrega" paso estudiante tok-ana nbex-prueba-ana "PRUEBA_ALUMNO=3135" entregar
comprobar "beto entrega" paso estudiante tok-beto nbex-prueba-beto "PRUEBA_ALUMNO=3136" entregar
comprobar "Collect trae submitted/3135 y submitted/3136" paso instructor tok-docente nbex-prueba-curso \
    "PRUEBA_ESPERA_ALUMNOS=3135,3136" recoger

echo "== 5. Lo que un alumno no puede hacer =="
comprobar "alumno: ni liberar, ni recoger, ni otro curso" paso estudiante tok-ajeno nbex-prueba-ajeno prohibido

echo "== 6. El docente retira la tarea =="
comprobar "borrar-cuadernillo la retira del servicio" paso instructor tok-docente nbex-prueba-curso retirar

echo
if [ "$fallos" = 0 ]; then
    echo "TODO OK"
else
    echo "$fallos paso(s) fallaron. Logs del servicio:"
    docker logs nbex-prueba 2>&1 | tail -40
    exit 1
fi
