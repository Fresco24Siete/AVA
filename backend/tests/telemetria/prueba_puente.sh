#!/usr/bin/env bash
# Prueba del puente metrics_bridge.py dentro de un contenedor del alumno.
#
# Uso:  backend/tests/telemetria/prueba_puente.sh [imagen]
#       (por defecto mi_imagen_jupyterlab:latest)
#
# Lanza un contenedor efimero SIN red externa (--network none), copia
# prueba_puente.py adentro y lo ejecuta: ahi se levantan el backend stub y el
# 'jupyter server' del alumno, y se corren todos los casos. Al terminar (o si
# se interrumpe) el contenedor se elimina. No toca el stack 'ava' ni su base.
set -u

IMAGEN="${1:-mi_imagen_jupyterlab:latest}"
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOMBRE="prueba-puente-metrics-$$"

limpiar() { docker rm -f "$NOMBRE" >/dev/null 2>&1 || true; }
trap limpiar EXIT INT TERM

echo "== contenedor $NOMBRE desde $IMAGEN (sin red externa)"
docker run -d --rm --name "$NOMBRE" --network none \
    --memory 512m \
    --entrypoint sh "$IMAGEN" -c 'sleep 900' >/dev/null || { echo "no se pudo arrancar el contenedor"; exit 2; }

docker cp "$AQUI/prueba_puente.py" "$NOMBRE:/tmp/prueba_puente.py"

# El entorno del Hub lo pone el propio prueba_puente.py (ENTORNO_HUB) al
# lanzar cada 'jupyter server', porque los casos (g) y (h) necesitan variar
# STUDENT_METRICS_TOKEN y ENVIAR_AL_BACKEND.
docker exec -e HOME=/home/jovyan "$NOMBRE" python3 /tmp/prueba_puente.py
CODIGO=$?

if [ "$CODIGO" -ne 0 ]; then
    echo
    echo "== cola del log del jupyter server principal (para diagnostico)"
    docker exec "$NOMBRE" sh -c 'tail -n 60 /tmp/jupyter-principal.log 2>/dev/null'
fi
exit $CODIGO
