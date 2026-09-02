#!/usr/bin/env bash
# Diagnóstico de la máquina donde se quiere montar el AVA.
#
# No instala ni cambia nada: solo mira y reporta. Sirve para decidir CÓMO se
# expone el servidor a Moodle, que es lo que condiciona todo lo demás.
#
# Uso:
#   bash diagnostico.sh
set -uo pipefail

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
mal()  { printf '  \033[31m✗\033[0m %s\n' "$1"; }
info() { printf '    %s\n' "$1"; }
tit()  { printf '\n\033[1m%s\033[0m\n' "$1"; }

echo "==============================================="
echo " Diagnóstico para el AVA — $(date '+%Y-%m-%d %H:%M')"
echo "==============================================="

tit "1. La máquina"
if [ -r /etc/os-release ]; then
    . /etc/os-release
    ok "Sistema: ${PRETTY_NAME:-desconocido}"
else
    mal "No se pudo leer /etc/os-release (¿no es Linux?)"
fi
info "Arquitectura: $(uname -m)   Kernel: $(uname -r)"

RAM_MB=$(awk '/MemTotal/{printf "%d", $2/1024}' /proc/meminfo 2>/dev/null || echo 0)
if [ "$RAM_MB" -ge 16000 ]; then
    ok "Memoria: ${RAM_MB} MB — suficiente para un curso completo"
elif [ "$RAM_MB" -ge 8000 ]; then
    ok "Memoria: ${RAM_MB} MB — alcanza, con margen justo"
else
    mal "Memoria: ${RAM_MB} MB — corta para 25 estudiantes (se calcula ~250 MB por alumno activo)"
fi

CPUS=$(nproc 2>/dev/null || echo '?')
info "Núcleos: ${CPUS}"
DISCO=$(df -BG --output=avail / 2>/dev/null | tail -1 | tr -d ' G')
if [ "${DISCO:-0}" -ge 40 ]; then
    ok "Disco libre: ${DISCO} GB"
else
    mal "Disco libre: ${DISCO} GB — conviene tener 40 GB o más"
fi

tit "2. Docker"
if command -v docker >/dev/null 2>&1; then
    ok "Docker instalado: $(docker --version 2>/dev/null | cut -d, -f1)"
    if docker compose version >/dev/null 2>&1; then
        ok "Docker Compose v2 disponible"
    else
        mal "Falta 'docker compose' (plugin v2). El instalador lo pondrá."
    fi
    if docker ps >/dev/null 2>&1; then
        ok "El usuario actual puede usar Docker sin sudo"
    else
        mal "Hace falta sudo para Docker (o añadir el usuario al grupo 'docker')"
    fi
else
    mal "Docker NO está instalado. El instalador se encarga."
fi

tit "3. Arranque automático"
if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
    ok "systemd disponible: el AVA puede levantarse solo al encender"
else
    mal "Sin systemd: habría que arrancarlo a mano tras cada reinicio"
fi

tit "4. Red — esto decide cómo llega Moodle"
IP_LOCAL=$(hostname -I 2>/dev/null | awk '{print $1}')
IP_PUB=$(curl -s --max-time 8 https://api.ipify.org 2>/dev/null || echo '')
info "IP local:   ${IP_LOCAL:-desconocida}"
info "IP pública: ${IP_PUB:-no se pudo averiguar}"

es_privada() {
    case "$1" in
        10.*|192.168.*|172.1[6-9].*|172.2[0-9].*|172.3[0-1].*) return 0 ;;
        100.6[4-9].*|100.[7-9][0-9].*|100.1[0-1][0-9].*|100.12[0-7].*) return 0 ;;
        *) return 1 ;;
    esac
}

if [ -n "$IP_PUB" ] && [ "$IP_LOCAL" = "$IP_PUB" ]; then
    ok "La máquina tiene IP pública directa: se puede publicar sin túnel"
    RECOMENDACION="directo"
elif [ -n "$IP_PUB" ]; then
    mal "Está detrás de un router (NAT): la IP local y la pública no coinciden"
    info "Sin abrir puertos en el router, Moodle no puede alcanzarla."
    RECOMENDACION="tunel"
else
    mal "Sin salida a internet, o bloqueada"
    RECOMENDACION="revisar"
fi

# Puertos ocupados: si algo escucha en 80/443, el AVA chocaría.
for PUERTO in 80 443; do
    if command -v ss >/dev/null 2>&1 && ss -ltn 2>/dev/null | grep -q ":${PUERTO} "; then
        mal "El puerto ${PUERTO} ya está ocupado por otro programa"
    else
        ok "Puerto ${PUERTO} libre"
    fi
done

tit "5. ¿Se puede llegar desde fuera?"
if [ -n "$IP_PUB" ]; then
    RESP=$(curl -s --max-time 12 "https://api.ipify.org" >/dev/null 2>&1 && echo si || echo no)
    info "Salida a internet: ${RESP}"
    info "Para saber si ENTRAN conexiones hay que probar desde fuera; el"
    info "instalador lo resuelve con un túnel, que no necesita abrir puertos."
fi

tit "Resumen"
case "${RECOMENDACION:-revisar}" in
    directo)
        echo "  La máquina es alcanzable directamente. Se puede montar con un"
        echo "  dominio apuntando a ${IP_PUB} y certificado automático."
        ;;
    tunel)
        echo "  Está detrás de NAT, que es lo normal en una casa u oficina."
        echo "  La salida limpia es un TÚNEL: no hay que abrir puertos ni pedirle"
        echo "  nada al proveedor de internet, y da HTTPS con un nombre estable."
        ;;
    *)
        echo "  No se pudo determinar la salida a internet. Revisar la conexión"
        echo "  antes de seguir."
        ;;
esac
echo
echo "  Envíale esta salida completa a Diego."
