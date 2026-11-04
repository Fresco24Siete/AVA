#!/usr/bin/env bash
# Corre los tres tramos de la suite de telemetria en orden (backend, puente,
# customjs) contra el stack local 'ava' y termina con un resumen.
#
# Uso:  backend/tests/telemetria/correr_todo.sh [imagen_alumno]
#   imagen_alumno: por defecto mi_imagen_jupyterlab:latest (solo la usa el puente).
#
# Variables opcionales: API_BASE, DB_USER, DB_NAME, ENV_FILE (ver prueba_backend.py).
# Codigo de salida: 0 si los tres tramos pasan; 1 si alguno falla o no arranca.
#
# Antes y despues cuenta las filas de las cuatro tablas de telemetria: los
# tramos deben dejar la base exactamente como estaba.
set -u

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$AQUI/../../.." && pwd)"
IMAGEN="${1:-mi_imagen_jupyterlab:latest}"
ENV_FILE="${ENV_FILE:-$REPO/.env}"

# Credenciales de la base: de las variables o del .env del repo.
if [ -z "${DB_USER:-}" ] && [ -f "$ENV_FILE" ]; then
  DB_USER="$(grep -E '^DB_USER=' "$ENV_FILE" | tail -1 | cut -d= -f2- | tr -d '"' )"
fi
if [ -z "${DB_NAME:-}" ] && [ -f "$ENV_FILE" ]; then
  DB_NAME="$(grep -E '^DB_NAME=' "$ENV_FILE" | tail -1 | cut -d= -f2- | tr -d '"' )"
fi
DB_USER="${DB_USER:-ava}"; DB_NAME="${DB_NAME:-ava}"
export DB_USER DB_NAME ENV_FILE

contar() {
  docker exec -i postgres-db psql -U "$DB_USER" -d "$DB_NAME" -At -c \
    "select 'a',count(*) from exercise_attempts union all select 'e',count(*) from attempt_errors union all select 'r',count(*) from cuadernillo_ratings union all select 'n',count(*) from cuadernillo_notas" \
    2>/dev/null | tr '\n' ' '
}

declare -a NOMBRES=() ESTADOS=() CODIGOS=()
registrar() { NOMBRES+=("$1"); CODIGOS+=("$2"); ESTADOS+=("$3"); }

echo "== correr_todo: $(date -u +%Y-%m-%dT%H:%M:%SZ)  repo=$REPO"
ANTES="$(contar)"
echo "== filas antes : $ANTES"

echo; echo "################ TRAMO 1/3: backend (prueba_backend.py) ################"
python3 "$AQUI/prueba_backend.py"; rc=$?
case $rc in 0) registrar backend $rc OK;; 1) registrar backend $rc FALLA;; *) registrar backend $rc "NO ARRANCO";; esac

echo; echo "################ TRAMO 2/3: puente (prueba_puente.sh $IMAGEN) ################"
( cd "$REPO" && "$AQUI/prueba_puente.sh" "$IMAGEN" ); rc=$?
case $rc in 0) registrar puente $rc OK;; *) registrar puente $rc FALLA;; esac

echo; echo "################ TRAMO 3/3: customjs (node prueba_customjs.js) ################"
( cd "$AQUI" && node prueba_customjs.js ); rc=$?
case $rc in 0) registrar customjs $rc OK;; *) registrar customjs $rc FALLA;; esac

DESPUES="$(contar)"
echo; echo "################ RESUMEN ################"
salida=0
for i in "${!NOMBRES[@]}"; do
  printf '  %-9s exit=%s  %s\n' "${NOMBRES[$i]}" "${CODIGOS[$i]}" "${ESTADOS[$i]}"
  [ "${CODIGOS[$i]}" = 0 ] || salida=1
done
echo "  filas antes  : $ANTES"
echo "  filas despues: $DESPUES"
if [ "$ANTES" = "$DESPUES" ]; then
  echo "  base de datos: intacta"
else
  echo "  base de datos: CAMBIO (los tramos no limpiaron)"; salida=1
fi
[ $salida = 0 ] && echo "RESULTADO: TODO OK" || echo "RESULTADO: HAY FALLOS"
exit $salida
