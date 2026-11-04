#!/usr/bin/env bash
# Deja el AVA funcionando en este computador, desde cero.
#
# Pensado para el equipo del profesor: instala lo que falte (Docker, Tailscale),
# descarga el AVA, lo configura, lo enciende, hace que arranque solo cada vez
# que se prenda el computador y deja un indicador en la barra de arriba que dice
# si está funcionando.
#
# Se ejecuta así, en una terminal:
#
#     curl -fsSL https://raw.githubusercontent.com/Fresco24Siete/AVA/feat/menu-cuadernillos-y-notas/servidor/instalar-servidor.sh -o instalar-ava.sh && bash instalar-ava.sh
#
# Se descarga entero ANTES de ejecutarse a propósito: si la conexión se corta a
# mitad, no queda una instalación hecha por la mitad.
#
# Se puede repetir las veces que haga falta: no borra nada y no repite lo hecho.
set -euo pipefail

RAMA="${AVA_RAMA:-feat/menu-cuadernillos-y-notas}"
REPO="${AVA_REPO:-https://github.com/Fresco24Siete/AVA.git}"
CARPETA="${AVA_CARPETA:-$HOME/AVA}"
PUERTO_INTERNO=8081
PASOS_TOTAL=8
paso_n=0

verde()  { printf '\033[32m%s\033[0m\n' "$1"; }
rojo()   { printf '\033[31m%s\033[0m\n' "$1"; }
ambar()  { printf '\033[33m%s\033[0m\n' "$1"; }
ok()     { printf '  \033[32m✓\033[0m %s\n' "$1"; }
mal()    { printf '  \033[31m✗\033[0m %s\n' "$1"; }
aviso()  { printf '  \033[33m!\033[0m %s\n' "$1"; }
info()   { printf '    %s\n' "$1"; }
paso()   { paso_n=$((paso_n + 1)); printf '\n\033[1m[%d/%d] %s\033[0m\n' "$paso_n" "$PASOS_TOTAL" "$1"; }

# Si algo revienta, el profesor tiene que saber qué hacer, no ver una traza.
fallo_en_linea() {
    echo
    rojo "════════════════════════════════════════════════════════"
    rojo " La instalación se detuvo en el paso $paso_n de $PASOS_TOTAL."
    rojo "════════════════════════════════════════════════════════"
    echo
    echo " No se dañó nada. Puedes volver a ejecutar este mismo archivo:"
    echo "     bash $0"
    echo " y seguirá desde donde se quedó."
    echo
    echo " Si vuelve a fallar, mándale a Diego esta línea:"
    echo "     falló en el paso $paso_n (línea $1)"
    exit 1
}
trap 'fallo_en_linea $LINENO' ERR

clear 2>/dev/null || true
echo "════════════════════════════════════════════════════════"
echo "  Instalación del AVA — servidor del curso"
echo "  $(date '+%A %d de %B, %H:%M')"
echo "════════════════════════════════════════════════════════"
echo
echo "  Esto va a dejar el AVA funcionando en este computador."
echo "  Tarda entre 10 y 25 minutos, según la conexión."
echo "  Te va a pedir tu contraseña una vez, para instalar programas."
echo

# ---------------------------------------------------------------- 1. la máquina
paso "Revisando el computador"

if [ "$(id -u)" -eq 0 ]; then
    mal "No ejecutes esto con sudo ni como root."
    info "Ábrelo con tu usuario normal: bash $0"
    exit 1
fi
command -v apt-get >/dev/null || { mal "Esto solo funciona en Ubuntu o Debian."; exit 1; }

. /etc/os-release 2>/dev/null || true
ok "Sistema: ${PRETTY_NAME:-desconocido}"

RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
DISCO_GB=$(df -BG --output=avail "$HOME" | tail -1 | tr -dc '0-9')
ok "Memoria: ${RAM_MB} MB · Espacio libre: ${DISCO_GB} GB · Núcleos: $(nproc)"

if [ "$RAM_MB" -lt 4000 ]; then
    mal "Este computador tiene poca memoria (${RAM_MB} MB) para ser el servidor."
    info "Con menos de 4 GB los alumnos van a tener problemas. Se recomienda otro equipo."
    read -r -p "    ¿Seguir de todas formas? (escribe SI) " r
    [ "$r" = "SI" ] || exit 1
fi
if [ "$DISCO_GB" -lt 25 ]; then
    mal "Queda poco espacio en disco: ${DISCO_GB} GB. El AVA necesita unos 20 GB."
    info "Libera espacio y vuelve a ejecutar esto."
    exit 1
fi

# El reloj: si se desvía más de 30 segundos, Moodle no puede entrar y el error
# que ve el profesor no dice nada de la hora.
if ! timedatectl show -p NTPSynchronized --value 2>/dev/null | grep -q yes; then
    aviso "El reloj del computador no se está sincronizando solo."
    info "Se va a activar (si no, los alumnos no podrán entrar desde Moodle)."
    sudo timedatectl set-ntp true 2>/dev/null || aviso "No se pudo activar; revísalo en Configuración › Fecha y hora."
fi
ok "Reloj: $(timedatectl show -p Timezone --value 2>/dev/null || echo '?')"

# Se pide la contraseña UNA vez y se mantiene viva mientras dure la instalación,
# para no interrumpir al profesor cinco veces.
echo
echo "  Necesito tu contraseña para instalar los programas:"
sudo -v
( while true; do sudo -n true; sleep 50; kill -0 "$$" 2>/dev/null || exit; done ) 2>/dev/null &
MANTENER_SUDO=$!
trap 'kill $MANTENER_SUDO 2>/dev/null || true; fallo_en_linea $LINENO' ERR
trap 'kill $MANTENER_SUDO 2>/dev/null || true' EXIT

# ------------------------------------------------------------------ 2. programas
paso "Instalando los programas necesarios"

export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl git python3 openssl \
    python3-gi gir1.2-gtk-3.0 libnotify-bin >/dev/null
ok "herramientas básicas"

# El portapapeles depende del tipo de sesión: xclip no funciona en Wayland, que
# es lo que trae Ubuntu por defecto, y falla en silencio.
SESION="${XDG_SESSION_TYPE:-desconocida}"
if [ "$SESION" = "wayland" ]; then
    sudo apt-get install -y -qq wl-clipboard >/dev/null 2>&1 || true
else
    sudo apt-get install -y -qq xclip >/dev/null 2>&1 || true
fi
ok "escritorio: $SESION"

# El indicador de la barra necesita este puente entre Python y el sistema.
if ! sudo apt-get install -y -qq gir1.2-ayatanaappindicator3-0.1 >/dev/null 2>&1; then
    sudo apt-get install -y -qq gir1.2-appindicator3-0.1 >/dev/null 2>&1 \
        || aviso "sin soporte de indicador: el AVA funcionará, pero sin icono en la barra"
fi
# GNOME no tiene bandeja propia: el icono lo pinta una extensión. En Ubuntu 26.04
# el paquete que la trae es gnome-shell-ubuntu-extensions (el nombre viejo ya es
# solo un alias). Y en equipos ACTUALIZADOS desde una versión anterior suele
# faltar, que es justo el caso de un computador que ya se venía usando.
sudo apt-get install -y -qq --no-install-recommends gnome-shell-ubuntu-extensions \
    >/dev/null 2>&1 || sudo apt-get install -y -qq gnome-shell-extension-appindicator \
    >/dev/null 2>&1 || true

# Instalarla no la activa. Se intenta encender por si el escritorio no es la
# sesión de Ubuntu o si alguien la apagó alguna vez.
for ext in ubuntu-appindicators@ubuntu.com appindicatorsupport@rgcjonas.gmail.com; do
    gnome-extensions enable "$ext" >/dev/null 2>&1 && break
done
if gnome-extensions list --enabled 2>/dev/null | grep -q appindicator; then
    ok "soporte para el icono de la barra (activo)"
    EXTENSION_LISTA=si
else
    aviso "la extensión del icono se instaló pero aún no está activa"
    EXTENSION_LISTA=no
fi

if ! command -v docker >/dev/null; then
    info "instalando Docker (es lo que más tarda)…"
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin >/dev/null
fi
sudo systemctl enable --now docker >/dev/null 2>&1 || true
ok "Docker $(docker --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"

# Poder usar Docker sin sudo. El grupo no aplica hasta cerrar sesión, así que en
# esta misma corrida hay que lanzar los comandos con el grupo ya puesto, para no
# obligar a reiniciar a mitad de la instalación.
if ! id -nG "$USER" | tr ' ' '\n' | grep -qx docker; then
    sudo usermod -aG docker "$USER"
    ok "tu usuario ahora puede usar Docker (efectivo al reiniciar sesión)"
fi

# Esto se hacía siempre con "sg", que viene en el paquete login. Ubuntu 26.04 ya
# no lo trae, así que en un computador recién estrenado la instalación moría
# justo aquí: "sg: command not found" seguido de "Docker no responde", que
# además señala al sitio equivocado —Docker estaba perfecto—. Ahora se usa lo
# que haya; sudo está siempre, porque ya se usa para todo lo demás.
if docker ps >/dev/null 2>&1; then
    con_docker() { "$@"; }                       # el grupo ya está activo
elif command -v sg >/dev/null 2>&1 && sg docker -c 'docker ps' >/dev/null 2>&1; then
    con_docker() { sg docker -c "$(printf '%q ' "$@")"; }
elif sudo -E -u "$USER" -g docker docker ps >/dev/null 2>&1; then
    # -E conserva el entorno. Sin él se pierden DISPLAY y WAYLAND_DISPLAY, y el
    # paso del indicador creería que no hay escritorio y no encendería el icono.
    con_docker() { sudo -E -u "$USER" -g docker "$@"; }
else
    # Antes que dejar a medias una instalación —o hacerla como root, que deja el
    # .env y el icono en el sitio equivocado—, se para y se dice qué hacer.
    mal "Docker está instalado, pero tu usuario todavía no puede usarlo."
    info "Cierra sesión y vuelve a entrar (o reinicia el computador), y"
    info "ejecuta otra vez:"
    info "    bash instalar-ava.sh"
    exit 1
fi
d() { con_docker docker "$@"; }
d ps >/dev/null || { mal "Docker no responde."; exit 1; }
ok "Docker responde"

if ! command -v tailscale >/dev/null; then
    info "instalando Tailscale (lo que deja entrar a tus alumnos)…"
    curl -fsSL https://tailscale.com/install.sh | sh >/dev/null 2>&1
fi
ok "Tailscale $(tailscale version 2>/dev/null | head -1)"

# -------------------------------------------------------------------- 3. código
paso "Descargando el AVA"
if [ -d "$CARPETA/.git" ]; then
    git -C "$CARPETA" fetch -q origin
    git -C "$CARPETA" checkout -q "$RAMA"
    git -C "$CARPETA" reset -q --hard "origin/$RAMA"
    ok "actualizado en $CARPETA"
else
    git clone -q --branch "$RAMA" "$REPO" "$CARPETA"
    ok "descargado en $CARPETA"
fi
cd "$CARPETA"

# ---------------------------------------------------------------- 4. instalación
paso "Instalando y encendiendo el AVA (esto tarda)"
con_docker bash servidor/instalar.sh

# --------------------------------------------------------------------- 5. túnel
paso "Publicando el AVA para que entren tus alumnos"

# BackendState dice la verdad; "tailscale status" a secas devuelve 0 aunque esté
# sin autenticar, y entonces el instalador seguiría como si todo estuviera bien.
estado_ts() {
    tailscale status --json 2>/dev/null \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("BackendState",""))' \
        2>/dev/null || echo ""
}

if [ "$(estado_ts)" != "Running" ]; then
    echo
    ambar "  ─────────────────────────────────────────────────────"
    ambar "   Este es el único paso que tienes que hacer tú"
    ambar "  ─────────────────────────────────────────────────────"
    echo
    echo "   Se va a mostrar una dirección web (y un código QR)."
    echo "   Ábrela, entra con tu cuenta —Google o GitHub sirven— y"
    echo "   autoriza este computador. Solo se hace una vez."
    echo
    read -r -p "   Presiona Enter cuando estés listo… " _ || true
    # --qr permite autenticar con el celular sin copiar la dirección a mano.
    sudo tailscale up --hostname=ava-servidor --qr || true
fi

if [ "$(estado_ts)" = "Running" ]; then
    NOMBRE=$(tailscale status --json 2>/dev/null \
        | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' \
        2>/dev/null || echo "")
    ok "conectado como ${NOMBRE:-?}"

    if tailscale serve status 2>/dev/null | grep -q "$PUERTO_INTERNO"; then
        ok "el túnel ya publica el AVA"
    elif sudo tailscale funnel --bg "$PUERTO_INTERNO" 2>/tmp/ava-funnel.err; then
        ok "publicado en internet"
    else
        # No se traga el error: sin túnel, los alumnos no entran y el profesor
        # tiene que saberlo AHORA, no el día de la clase.
        aviso "No se pudo publicar el túnel todavía."
        info "Suele ser que falta autorizarlo una vez desde la web. El detalle:"
        sed 's/^/      /' /tmp/ava-funnel.err 2>/dev/null | head -6
        info ""
        info "Cuando lo autorices, termina con este comando:"
        info "    sudo tailscale funnel --bg $PUERTO_INTERNO"
    fi
else
    aviso "Tailscale no quedó conectado."
    info "El AVA funciona, pero solo dentro de este computador."
    info "Para que entren tus alumnos, ejecuta después:"
    info "    sudo tailscale up --hostname=ava-servidor --qr"
    info "    sudo tailscale funnel --bg $PUERTO_INTERNO"
fi

# ----------------------------------------------------------------- 6. indicador
# El indicador lo instala, lo enciende y lo refresca servidor/instalar.sh (su
# paso 6), que ya corrió arriba. Antes se hacía aquí, y eso dejaba fuera el
# camino de ACTUALIZAR —que usa instalar.sh a secas— con el resultado de que el
# icono se quedaba con el código viejo, o muerto, sin que nada lo dijera.
# Aquí solo queda la ruta, que la usa la comprobación de más abajo.
DESTINO="$HOME/.local/share/ava"

# ------------------------------------------------------- 7. arranque automático
paso "Dejando que arranque solo al encender el computador"
# Los contenedores tienen restart=unless-stopped, así que Docker los repone al
# arrancar. Lo único que hay que garantizar es que Docker mismo arranque.
sudo systemctl enable docker >/dev/null 2>&1 || true
ok "el AVA se encenderá solo con el computador"

# ------------------------------------------------------------ 8. comprobaciones
paso "Comprobando que todo quedó bien"
sleep 3
# Va por con_docker igual que todo lo demás: el indicador pregunta por Docker, y
# en la primera instalación esta terminal todavía no tiene el grupo. Sin esto,
# "docker info" fallaba y el indicador informaba de un AVA caído, así que el
# instalador cerraba con "todavía no responde del todo" una instalación que
# estaba perfecta. Da miedo y manda a buscar una avería que no existe.
ESTADO_TXT=$(con_docker env AVA_CARPETA="$CARPETA" AVA_PUERTO="$PUERTO_INTERNO" \
    python3 "$DESTINO/ava_indicador.py" --estado 2>/dev/null || true)
echo "$ESTADO_TXT" | sed 's/^/  /'

URL=$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; print("https://"+json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null || echo "")

echo
if echo "$ESTADO_TXT" | grep -q "^\[verde\]"; then
    verde "════════════════════════════════════════════════════════"
    verde "  ¡Listo! El AVA está funcionando."
    verde "════════════════════════════════════════════════════════"
    echo
    echo "  La dirección para tus alumnos:"
    echo "      $URL"
    echo
    echo "  Ponla en Moodle, en la herramienta externa del curso, así:"
    echo "      $URL/hub/lti/launch"
    echo
    if [ "${EXTENSION_LISTA:-no}" = "si" ]; then
        echo "  Arriba a la derecha tienes un icono verde con el estado."
        echo "  Si algún día se pone rojo, haz clic y elige «Reiniciar el AVA»."
    else
        echo "  Falta una cosa para ver el icono de estado en la barra:"
        echo "  cierra sesión y vuelve a entrar (o reinicia el computador)."
        echo "  El AVA sigue funcionando mientras tanto."
    fi
else
    ambar "════════════════════════════════════════════════════════"
    ambar "  El AVA quedó instalado, pero todavía no responde del todo."
    ambar "════════════════════════════════════════════════════════"
    echo
    echo "  Casi siempre es que aún está arrancando. Espera dos minutos"
    echo "  y mira el icono de la barra de arriba."
    echo
    echo "  Si sigue en rojo, ejecuta esto y mándale el resultado a Diego:"
    echo "      cd $CARPETA && bash servidor/instalar.sh --verificar"
fi
echo
