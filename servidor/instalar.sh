#!/usr/bin/env bash
# Instala el AVA completo en la máquina donde se ejecute.
#
# Está pensado para una máquina de escritorio detrás de NAT, expuesta con un
# túnel (Tailscale Funnel o Cloudflare), no para la VM con dominio propio. Hace
# todo el ciclo: comprueba la máquina, genera los secretos, ajusta los límites a
# la memoria que haya, construye las imágenes en el orden correcto, levanta el
# stack, prepara la base de datos y verifica que quedó funcionando.
#
#   bash servidor/instalar.sh              # instala o actualiza
#   bash servidor/instalar.sh --verificar  # solo comprueba, no toca nada
#
# Se puede ejecutar las veces que haga falta: no pisa el .env si ya existe, no
# borra volúmenes y no repite lo que ya está hecho. Lo único que NO hace es
# publicar el túnel, porque eso necesita permisos de administrador; al final
# imprime el comando exacto para quien los tenga.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

COMPOSE=(docker compose -p ava -f docker-compose.yml -f servidor/docker-compose.tunel.yml)
PUERTO_INTERNO=8081          # donde escucha Caddy; es lo que se le pasa al túnel
FALLOS=0

# --- cómo se ve esto por pantalla -------------------------------------------
ok()    { printf '  \033[32m✓\033[0m %s\n' "$1"; }
mal()   { printf '  \033[31m✗\033[0m %s\n' "$1"; FALLOS=$((FALLOS + 1)); }
aviso() { printf '  \033[33m!\033[0m %s\n' "$1"; }
info()  { printf '    %s\n' "$1"; }
paso()  { printf '\n\033[1m%s\033[0m\n' "$1"; }

solo_verificar=false
[ "${1:-}" = "--verificar" ] && solo_verificar=true

echo "==========================================================="
echo " Instalación del AVA — $(date '+%Y-%m-%d %H:%M')"
echo " Carpeta: $RAIZ"
echo "==========================================================="

# --- 1. ¿esta máquina sirve? -------------------------------------------------
paso "1. La máquina"

for cmd in docker git openssl python3; do
    command -v "$cmd" >/dev/null || mal "falta $cmd"
done
docker compose version >/dev/null 2>&1 || mal "falta docker compose v2"
docker ps >/dev/null 2>&1 \
    && ok "Docker responde sin sudo" \
    || mal "este usuario no puede usar Docker (¿está en el grupo docker?)"

RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
DISCO_GB=$(df -BG --output=avail "$RAIZ" | tail -1 | tr -dc '0-9')
NUCLEOS=$(nproc)
ok "RAM ${RAM_MB} MB · ${NUCLEOS} núcleos · ${DISCO_GB} GB libres"
[ "$RAM_MB" -lt 4000 ] && aviso "con menos de 4 GB el curso irá justo"
[ "$DISCO_GB" -lt 25 ] && aviso "las imágenes ocupan ~15 GB: quedan ${DISCO_GB} GB"

# El reloj importa más de lo que parece: Moodle firma cada lanzamiento LTI con
# una marca de tiempo y el Hub rechaza las que se desvíen más de 30 segundos.
# Un reloj atrasado se manifiesta como "no puedo entrar" sin más explicación.
if timedatectl show -p NTPSynchronized --value 2>/dev/null | grep -q yes; then
    ok "reloj sincronizado ($(timedatectl show -p Timezone --value 2>/dev/null))"
else
    aviso "el reloj NO está sincronizado; si se desvía, los lanzamientos de Moodle fallarán"
    info "solución: sudo timedatectl set-ntp true"
fi

if [ "$FALLOS" -gt 0 ]; then
    echo; echo "Faltan requisitos. No sigo."; exit 1
fi

if $solo_verificar; then
    paso "Solo verificación: no se instala nada"
fi

# --- 2. secretos y configuración --------------------------------------------
paso "2. Configuración (.env)"

# Se generan una vez y se conservan. Si el .env ya existe NO se toca: rehacer
# JUPYTERHUB_CRYPT_KEY invalidaría el auth_state guardado de todos los usuarios,
# y rehacer METRICS_TOKEN_SECRET dejaría fuera a los contenedores en marcha.
if [ -f .env ]; then
    ok ".env ya existía; se conserva (los secretos no se regeneran)"
else
    if $solo_verificar; then
        aviso "no hay .env (se crearía)"
    else
        umask 077
        cat > .env <<EOF
# Generado por servidor/instalar.sh el $(date '+%Y-%m-%d %H:%M').
# Contiene secretos: no subir a git (.gitignore ya lo excluye).

# --- Cómo se compone el stack en esta máquina ---
# Compose lee estas dos de aquí, así que un "docker compose up" a secas ya usa
# el override del túnel. Sin ellas, cualquiera que levante el stack sin los -f
# arranca Caddy con el Caddyfile de la VM: pide certificado para el dominio
# viejo, publica 80/443 en vez del puerto del túnel, y el AVA deja de responder
# desde fuera con un 502. Pasó el 2026-08-24 y costó encontrarlo.
COMPOSE_PROJECT_NAME=ava
COMPOSE_FILE=docker-compose.yml:servidor/docker-compose.tunel.yml

# --- Base de datos ---
DB_USER=ava
DB_PASSWORD=$(openssl rand -hex 24)
DB_NAME=ava
DB_HOST=postgres-database
DB_PORT=5432

# --- JupyterHub ---
JUPYTERHUB_CRYPT_KEY=$(openssl rand -hex 32)

# --- LTI (deben coincidir con la actividad configurada en Moodle) ---
LTI_CLIENT_KEY=moodle-llave-publica
LTI_CLIENT_SECRET=secreto-super-seguro-000000

# --- Telemetría ---
ENVIAR_AL_BACKEND=true
STUDENT_METRICS_API_BASE=http://api_go:8080
METRICS_API_TOKEN=$(openssl rand -hex 32)
METRICS_TOKEN_SECRET=$(openssl rand -hex 32)

# --- Servicio de intercambio ---
NBEXCHANGE_API_TOKEN=$(openssl rand -hex 32)

# --- Tutor IA ---
# Sin claves de Gemini el tutor responde 503 y el resto del AVA funciona igual.
GOOGLE_API_KEY_1=
GOOGLE_API_KEY_2=
TUTOR_ALIAS=Ava
TUTOR_MODELO=gemini-3.5-flash
TUTOR_IA_HABILITADO=true
TUTOR_MAX_PREGUNTAS=5
EOF
        ok ".env creado con secretos nuevos"
    fi
fi

# Los topes de memoria por contenedor se calculan con la RAM real de la máquina.
# En la VM de 2 GB eran 768 MB por alumno; aquí se puede ser generoso sin
# riesgo, porque el tope solo actúa cuando alguien escribe un bucle infinito.
if ! grep -q '^MEM_LIMIT_ALUMNO=' .env 2>/dev/null && [ -f .env ] && ! $solo_verificar; then
    if   [ "$RAM_MB" -ge 24000 ]; then ALU=2048M; INS=4096M
    elif [ "$RAM_MB" -ge 12000 ]; then ALU=1536M; INS=3072M
    elif [ "$RAM_MB" -ge 6000  ]; then ALU=1024M; INS=2048M
    else                               ALU=768M;  INS=1536M
    fi
    cat >> .env <<EOF

# --- Límites por contenedor (calculados con los ${RAM_MB} MB de esta máquina) ---
MEM_LIMIT_ALUMNO=$ALU
MEM_LIMIT_INSTRUCTOR=$INS
EOF
    ok "límites de memoria: alumno $ALU · docente $INS"
fi

if grep -q '^GOOGLE_API_KEY_1=.\+' .env 2>/dev/null; then
    ok "el Tutor IA tiene clave de Gemini"
else
    aviso "sin clave de Gemini el tutor responde 503 y el alumno lee «El tutor no"
    info "está disponible en este momento», que parece una avería del AVA."
    info "Ponlas en .env (GOOGLE_API_KEY_1 y _2) y recrea el backend:"
    info "    docker compose up -d --force-recreate api_go"
fi

if $solo_verificar; then
    paso "Estado actual"
    "${COMPOSE[@]}" ps 2>/dev/null || info "el stack no está levantado"
    exit 0
fi

# --- 3. imágenes -------------------------------------------------------------
paso "3. Construyendo las imágenes"

# ORDEN OBLIGATORIO: la imagen del docente hereda de la del alumno
# (notebook/Dockerfile.docente empieza por FROM mi_imagen_jupyterlab:latest).
# Construir solo la del docente deja dentro el código viejo de notebook/, y el
# fallo aparece mucho después y en otro sitio: costó una hora encontrarlo.
info "alumno (primero: la del docente hereda de ella)…"
docker build -q -t mi_imagen_jupyterlab:latest notebook >/dev/null
ok "mi_imagen_jupyterlab:latest"

info "docente…"
docker build -q -t mi_imagen_jupyterlab_docente:latest -f notebook/Dockerfile.docente notebook >/dev/null
ok "mi_imagen_jupyterlab_docente:latest"

info "hub, servicio de intercambio y backend…"
"${COMPOSE[@]}" build >/dev/null
ok "imágenes de compose"

# --- 4. arranque -------------------------------------------------------------
paso "4. Levantando el stack"

"${COMPOSE[@]}" up -d >/dev/null
ok "contenedores lanzados"

info "esperando a que la base de datos esté sana…"
for _ in $(seq 1 60); do
    docker inspect --format '{{.State.Health.Status}}' postgres-db 2>/dev/null | grep -q healthy && break
    sleep 2
done
docker inspect --format '{{.State.Health.Status}}' postgres-db 2>/dev/null | grep -q healthy \
    && ok "PostgreSQL sano" \
    || mal "PostgreSQL no llegó a estar sano"

# El esquema base lo aplica el propio Postgres la primera vez
# (database/schema_v2.sql va montado en docker-entrypoint-initdb.d), pero la
# migración v3 —la tabla de estudiantes— es posterior y hay que aplicarla
# aparte. Es idempotente: se puede correr siempre.
info "aplicando la migración v3…"
if docker exec -i postgres-db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q -v ON_ERROR_STOP=1' \
        < database/migracion_v3.sql >/dev/null 2>&1; then
    ok "esquema al día"
else
    mal "la migración v3 falló"
fi

# --- 5. ¿quedó funcionando? --------------------------------------------------
paso "5. Comprobaciones"

info "esperando al Hub…"
for _ in $(seq 1 60); do
    curl -sS -o /dev/null "http://127.0.0.1:${PUERTO_INTERNO}/hub/login" 2>/dev/null && break
    sleep 2
done

# Un 302 aquí es lo normal y lo deseable: el Hub manda al login o al flujo LTI.
# Lo que importa es que conteste, no el código exacto; solo un 5xx o un 000 (no
# hubo respuesta) significan que algo está roto.
codigo=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PUERTO_INTERNO}/hub/login" 2>/dev/null || echo 000)
if [ "$codigo" != "000" ] && [ "$codigo" -lt 500 ]; then
    ok "el Hub responde por Caddy (puerto ${PUERTO_INTERNO}, HTTP $codigo)"
else
    mal "el Hub no responde por el puerto ${PUERTO_INTERNO} (HTTP $codigo)"
fi

codigo=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PUERTO_INTERNO}/services/nbexchange/" 2>/dev/null || echo 000)
if [ "$codigo" != "000" ] && [ "$codigo" -lt 500 ]; then
    ok "servicio de intercambio registrado en el Hub (HTTP $codigo)"
else
    mal "el servicio de intercambio no responde (HTTP $codigo)"
fi

tablas=$(docker exec postgres-db sh -c \
    'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "select count(*) from information_schema.tables where table_schema='"'"'public'"'"'"' 2>/dev/null || echo 0)
[ "${tablas:-0}" -ge 11 ] && ok "base de datos con $tablas tablas" \
                          || mal "la base tiene $tablas tablas (se esperaban 11 o más)"

comp=$(docker exec postgres-db sh -c \
    'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "select count(*) from competencias"' 2>/dev/null || echo 0)
[ "${comp:-0}" -ge 7 ] && ok "catálogo de competencias sembrado ($comp)" \
                       || aviso "el catálogo de competencias está vacío: cargar-competencias fallará"

for img in mi_imagen_jupyterlab:latest mi_imagen_jupyterlab_docente:latest; do
    docker image inspect "$img" >/dev/null 2>&1 && ok "imagen $img" || mal "falta la imagen $img"
done

vivos=$("${COMPOSE[@]}" ps --services --filter status=running 2>/dev/null | wc -l)
ok "$vivos servicios en marcha"

# --- 6. lo que queda por hacer con permisos de administrador -----------------
paso "6. Para publicarlo en internet"

if command -v tailscale >/dev/null 2>&1; then
    if tailscale serve status 2>/dev/null | grep -q "${PUERTO_INTERNO}"; then
        ok "el túnel ya está publicando el puerto ${PUERTO_INTERNO}"
        nombre=$(tailscale status --json 2>/dev/null \
                 | python3 -c "import json,sys; print(json.load(sys.stdin)['Self']['DNSName'].rstrip('.'))" 2>/dev/null || echo "")
        [ -n "$nombre" ] && info "URL pública: https://${nombre}"
    else
        aviso "falta publicar el túnel. Un comando, con permisos de administrador:"
        info ""
        info "    sudo tailscale funnel --bg ${PUERTO_INTERNO}"
        info ""
        info "Después, en Moodle, la actividad debe apuntar a:"
        info "    https://<nombre-de-esta-maquina>.ts.net/hub/lti/launch"
    fi
else
    aviso "Tailscale no está instalado; el AVA solo es accesible en esta máquina"
fi

paso "Resumen"
if [ "$FALLOS" -eq 0 ]; then
    printf '  \033[32mTODO OK\033[0m — el AVA está funcionando en esta máquina.\n\n'
    info "ver el estado:   docker compose -p ava ps"
    info "ver los logs:    docker compose -p ava logs -f jupyterhub"
    info "reinstalar:      bash servidor/instalar.sh"
    info "solo comprobar:  bash servidor/instalar.sh --verificar"
    echo
    info "Se levanta solo al encender el equipo: los contenedores tienen"
    info "restart=unless-stopped, así que Docker los repone con el sistema."
else
    printf '  \033[31m%d comprobación(es) fallaron\033[0m — revisa arriba.\n' "$FALLOS"
    info "para ver qué pasó:  docker compose -p ava logs --tail=50"
    exit 1
fi
