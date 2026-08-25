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

# --- 1b. ¿ya hay otro AVA en esta máquina? -----------------------------------
#
# Los contenedores llevan el nombre de la carpeta que los creó. Si ya existe un
# AVA instalado en OTRA carpeta, seguir sería destructivo: este instalador
# generaría un .env nuevo, con otra contraseña de base de datos, y al levantar
# el mismo proyecto de compose los contenedores apuntarían al volumen de datos
# de la instalación anterior, cuya contraseña es la vieja. El resultado es un
# AVA que no arranca y unos datos que parecen perdidos.
#
# Además los contenedores tienen nombre fijo (jupyterhub, postgres-db…), así que
# dos AVA no pueden convivir en la misma máquina de ninguna forma.
OTRA=$(docker ps -a --filter "label=com.docker.compose.project=ava" --format '{{.ID}}' 2>/dev/null | head -1)
if [ -n "$OTRA" ]; then
    CARPETA_ORIGEN=$(docker inspect --format \
        '{{index .Config.Labels "com.docker.compose.project.working_dir"}}' "$OTRA" 2>/dev/null)
    if [ -n "$CARPETA_ORIGEN" ] && [ "$CARPETA_ORIGEN" != "$RAIZ" ]; then
        paso "Ya hay un AVA en este computador"
        mal "está instalado en otra carpeta: $CARPETA_ORIGEN"
        echo
        info "No voy a tocarlo: si siguiera, esa instalación dejaría de funcionar"
        info "y sus cuadernillos, entregas y notas quedarían inaccesibles."
        echo
        info "Para administrar el que ya existe:"
        info "    cd $CARPETA_ORIGEN && bash servidor/instalar.sh"
        echo
        info "Si de verdad quieres empezar de cero y BORRAR lo que hay:"
        info "    cd $CARPETA_ORIGEN && docker compose down -v"
        info "    (eso borra los cuadernillos, las entregas y las notas)"
        echo
        exit 1
    fi
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
# Se generan aquí, como todo lo demás. Antes eran dos valores fijos escritos en
# el script, que vive en un repositorio PÚBLICO. Con el AVA publicado en
# internet por el túnel, eso significa que cualquiera que leyera el repositorio
# podía firmar un lanzamiento LTI contra /hub/lti/launch y entrar como quien
# quisiera —el rol viaja en el propio lanzamiento—, incluso como docente: leer y
# modificar el trabajo de toda la clase y las notas.
# El instalador los muestra al final; hay que copiarlos en la actividad de Moodle.
LTI_CLIENT_KEY=ava-$(openssl rand -hex 6)
LTI_CLIENT_SECRET=$(openssl rand -hex 32)

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

# Un .env viejo —hecho a mano o heredado de una instalación anterior— puede no
# traer esta línea. Sin ella el AVA arranca entero, el alumno no ve ningún error
# y el navegador recibe 200, pero el puente de métricas se queda en modo
# simulación: NADA de lo que hace la clase llega a la base. Se pierde el curso
# completo sin una sola señal. Por eso se añade también a los .env que ya
# existían, en vez de darlo por hecho al crearlo.
if [ -f .env ] && ! grep -q '^ENVIAR_AL_BACKEND=' .env 2>/dev/null && ! $solo_verificar; then
    cat >> .env <<'EOF'

# --- Telemetría (se añadió porque este .env venía sin la línea) ---
ENVIAR_AL_BACKEND=true
EOF
    ok "telemetría activada (el .env venía sin ENVIAR_AL_BACKEND)"
fi

# Si alguien la dejó en "false" a propósito, no se le pisa la decisión: se le
# dice. Apagada, el AVA funciona entero y no guarda absolutamente nada —ni
# valoraciones ni intentos de ejercicio—, y no hay ninguna otra señal.
if [ -f .env ] && grep -qiE '^ENVIAR_AL_BACKEND=[[:space:]]*"?(false|0|no)"?[[:space:]]*$' .env 2>/dev/null; then
    aviso "LA TELEMETRÍA ESTÁ APAGADA (ENVIAR_AL_BACKEND=false en .env)"
    info "El curso puede trabajar un semestre entero sin que se guarde nada:"
    info "no habrá intentos de ejercicio ni valoraciones, y el alumno no ve"
    info "ningún error. Solo déjalo así si estás depurando. Para encenderla:"
    info "    sed -i 's/^ENVIAR_AL_BACKEND=.*/ENVIAR_AL_BACKEND=true/' .env"
    info "    bash servidor/instalar.sh"
fi

# Las credenciales LTI de ejemplo están publicadas en el repositorio. Con el AVA
# expuesto por el túnel, quien las conozca puede firmar un lanzamiento y entrar
# como cualquier persona del curso, docente incluido. No se rotan solas porque
# hay que cambiarlas también en Moodle, y hacerlo por sorpresa dejaría la
# actividad sin funcionar en mitad de una clase. Pero se avisa cada vez.
if [ -f .env ] && grep -qE '^LTI_CLIENT_SECRET=(secreto-super-seguro-000000|cambia-este-secreto)$' .env 2>/dev/null; then
    aviso "LAS CREDENCIALES DE MOODLE SON LAS DE EJEMPLO DEL REPOSITORIO PÚBLICO"
    info "Cualquiera que lea el repositorio puede entrar al AVA como docente."
    info "Cámbialas aquí y luego pega los valores nuevos en la actividad de"
    info "Moodle (herramienta externa → clave y secreto de consumidor):"
    info ""
    info "    sed -i \"s|^LTI_CLIENT_KEY=.*|LTI_CLIENT_KEY=ava-\$(openssl rand -hex 6)|\" .env"
    info "    sed -i \"s|^LTI_CLIENT_SECRET=.*|LTI_CLIENT_SECRET=\$(openssl rand -hex 32)|\" .env"
    info "    bash servidor/instalar.sh"
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

# Los contenedores de alumno y docente NO los levanta compose: los crea el Hub
# al entrar cada persona. Así que reconstruir la imagen no basta: quien tenga uno
# vivo sigue ejecutando el código viejo, y el arreglo que se acaba de instalar
# parece no funcionar. Es la misma clase de fallo mudo que ya nos costó caro.
#
# Se pueden tirar sin miedo: el trabajo del alumno vive en su volumen
# (ava-trabajo-<usuario>), no en el contenedor, y el Hub los da por desechables
# (DockerSpawner.remove = True). Los apagados se borran aquí mismo, porque si no
# reviven con la imagen vieja. Los que están en uso NO se tocan —puede haber
# alguien en mitad de un ejercicio—, pero se avisa en vez de callar.
viejos_parados=0
viejos_vivos=""
for c in $(docker ps -a --filter "name=^/jupyter-" --format '{{.Names}}'); do
    img_c=$(docker inspect --format '{{.Image}}' "$c" 2>/dev/null)
    caduco=true
    for img in mi_imagen_jupyterlab:latest mi_imagen_jupyterlab_docente:latest; do
        [ "$img_c" = "$(docker inspect --format '{{.Id}}' "$img" 2>/dev/null)" ] && caduco=false
    done
    $caduco || continue
    if [ -n "$(docker ps -q --filter "name=^/${c}$")" ]; then
        viejos_vivos="$viejos_vivos $c"
    else
        docker rm -f "$c" >/dev/null 2>&1 && viejos_parados=$((viejos_parados + 1))
    fi
done
[ "$viejos_parados" -gt 0 ] && \
    ok "$viejos_parados contenedor(es) con la imagen vieja retirados (renacen al entrar)"
if [ -n "$viejos_vivos" ]; then
    aviso "hay sesiones abiertas con la imagen ANTERIOR:$viejos_vivos"
    info "Siguen con el código viejo hasta que esa persona salga y vuelva a"
    info "entrar desde Moodle. Su trabajo está a salvo (vive en su volumen)."
    info "Si quieres forzarlo ahora mismo:"
    info "    docker rm -f$viejos_vivos"
fi

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
info "aplicando las migraciones…"
fallo_migracion=0
for m in database/migracion_v3.sql database/migracion_v4.sql; do
    [ -f "$m" ] || continue
    docker exec -i postgres-db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q -v ON_ERROR_STOP=1' \
        < "$m" >/dev/null 2>&1 || { mal "falló $m"; fallo_migracion=1; }
done
[ "$fallo_migracion" -eq 0 ] && ok "esquema al día (v3 y v4)"

# --- 5. ¿quedó funcionando? --------------------------------------------------
paso "5. Comprobaciones"

# Un 302 aquí es lo normal y lo deseable: el Hub manda al login o al flujo LTI.
# Lo que importa es que conteste, no el código exacto; solo un 5xx o un 000 (no
# hubo respuesta) significan que algo está roto.
#
# El bucle de espera comprobaba solo que curl saliera bien, y curl sale bien
# aunque la respuesta sea un 502: Caddy se levanta muchísimo antes que el Hub,
# así que el bucle terminaba en el primer intento y la comprobación cazaba ese
# 502 pasajero. El instalador declaraba rota una instalación que estaba
# perfecta, y el profesor se quedaba sin saber si tenía un AVA o no. Hay que
# esperar a una respuesta que NO sea de servidor caído.
esperar_http() {          # $1 = ruta · $2 = intentos (cada uno son 2 s)
    local ruta="$1" intentos="${2:-60}" codigo=000
    for _ in $(seq 1 "$intentos"); do
        codigo=$(curl -s -o /dev/null -w '%{http_code}' \
                 "http://127.0.0.1:${PUERTO_INTERNO}${ruta}" 2>/dev/null || echo 000)
        if [ "$codigo" != "000" ] && [ "$codigo" -lt 500 ]; then
            echo "$codigo"; return 0
        fi
        sleep 2
    done
    echo "$codigo"; return 1
}

info "esperando al Hub…"
if codigo=$(esperar_http /hub/login 60); then
    ok "el Hub responde por Caddy (puerto ${PUERTO_INTERNO}, HTTP $codigo)"
else
    mal "el Hub no responde por el puerto ${PUERTO_INTERNO} (HTTP $codigo)"
fi

# El intercambio se registra en el Hub al arrancar, así que puede tardar un poco
# más que él. Con el Hub ya en pie, 30 intentos son de sobra.
if codigo=$(esperar_http /services/nbexchange/ 30); then
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

# --- 6. el indicador de la barra ---------------------------------------------
# Vivía solo en instalar-servidor.sh, el script del enlace de instalación. Eso
# dejaba fuera el camino de actualizar —que es este script— y el resultado era
# que, tras una actualización, el icono seguía con el código viejo o
# directamente no estaba, sin que nada lo dijera. Aquí se refresca siempre.
paso "6. El indicador de la barra"

INDICADOR="$HOME/.local/share/ava"
if [ ! -f servidor/indicador/ava_indicador.py ]; then
    aviso "no encuentro el indicador en el repositorio; me lo salto"
elif $solo_verificar; then
    if pgrep -f "ava_indicador.py" >/dev/null 2>&1; then
        ok "el indicador está corriendo"
    else
        aviso "el indicador NO está corriendo (no verás el icono en la barra)"
    fi
else
    mkdir -p "$INDICADOR" "$HOME/.config/autostart"
    cp servidor/indicador/ava_indicador.py "$INDICADOR/"
    rm -rf "$INDICADOR/iconos"
    cp -r servidor/indicador/iconos "$INDICADOR/"
    chmod +x "$INDICADOR/ava_indicador.py"

    # Sin X-GNOME-Autostart-Delay: desde GNOME 49 el arranque de sesión lo
    # gestiona systemd, que ignora esa clave. Esperar a que la barra esté lista
    # es trabajo del propio programa, que vigila el bus.
    cat > "$HOME/.config/autostart/ava-indicador.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Estado del AVA
Comment=Indica en la barra superior si el servidor del curso está funcionando
Exec=python3 $INDICADOR/ava_indicador.py
Icon=$INDICADOR/iconos/ava-verde.svg
Terminal=false
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF
    chmod 644 "$HOME/.config/autostart/ava-indicador.desktop"

    # El icono lo pinta una extensión de GNOME. Si está instalada pero apagada,
    # el programa corre y no se ve nada: el fallo más confuso de todos.
    for ext in ubuntu-appindicators@ubuntu.com appindicatorsupport@rgcjonas.gmail.com; do
        gnome-extensions enable "$ext" >/dev/null 2>&1 && break
    done

    if [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
        pkill -f "ava_indicador.py" >/dev/null 2>&1 || true
        (setsid python3 "$INDICADOR/ava_indicador.py" >/dev/null 2>&1 &) || true
        sleep 2
        if pgrep -f "ava_indicador.py" >/dev/null 2>&1; then
            ok "icono encendido en la barra de arriba"
        else
            aviso "el indicador no arrancó. Para ver por qué:"
            info "    python3 $INDICADOR/ava_indicador.py"
        fi
    else
        # Pasa siempre que se instala por SSH. Decirlo evita la conclusión
        # equivocada de que el indicador está roto.
        aviso "sin sesión gráfica aquí: el icono aparecerá al entrar al escritorio"
        info "Si ya estás en el escritorio y no lo ves, ejecútalo a mano:"
        info "    python3 $INDICADOR/ava_indicador.py"
    fi
fi

# --- 7. lo que queda por hacer con permisos de administrador -----------------
paso "7. Para publicarlo en internet"

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

# --- 8. lo que hay que escribir en Moodle ------------------------------------
# El secreto se genera en esta máquina y no existe en ningún otro sitio: si no
# se muestra aquí, la actividad de Moodle no se puede configurar. Sí, queda en
# el historial de la terminal; la alternativa era dejar un secreto conocido.
if [ -f .env ]; then
    paso "8. Datos para la actividad de Moodle"
    lti_k=$(grep -m1 '^LTI_CLIENT_KEY=' .env | cut -d= -f2-)
    lti_s=$(grep -m1 '^LTI_CLIENT_SECRET=' .env | cut -d= -f2-)
    maquina=$(tailscale status --json 2>/dev/null \
              | python3 -c "import json,sys; print(json.load(sys.stdin)['Self']['DNSName'].rstrip('.'))" \
              2>/dev/null || echo "")
    info "En Moodle, «Herramienta externa» del curso:"
    info ""
    info "  URL de lanzamiento    https://${maquina:-<nombre-de-esta-maquina>.ts.net}/hub/lti/launch"
    info "  Clave de consumidor   ${lti_k:-?}"
    info "  Secreto compartido    ${lti_s:-?}"
    info ""
    info "Y en «Privacidad», comparte el nombre y el correo del alumno: sin eso"
    info "el AVA no sabe quién entra y no puede devolver la nota."
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
