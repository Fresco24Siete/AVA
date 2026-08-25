#!/usr/bin/env python3
"""Indicador del AVA en la barra del sistema.

El profesor no tiene por qué abrir una terminal para saber si sus alumnos
pueden entrar. Este programa vive en la barra superior, mira el servidor cada
minuto y lo dice con un icono: verde si está sirviendo, ámbar si está
arrancando, rojo si está caído.

Corre en la sesión gráfica del profesor, no como servicio del sistema: el icono
solo tiene sentido cuando hay alguien mirando la pantalla. El servidor en sí lo
levanta Docker al encender el equipo, sin depender de esto.

    python3 ava_indicador.py            # normal, se queda en la barra
    python3 ava_indicador.py --estado   # imprime el estado y sale (para probar)
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

CARPETA = os.environ.get("AVA_CARPETA", os.path.expanduser("~/AVA"))
PUERTO = os.environ.get("AVA_PUERTO", "8081")
CADA_SEGUNDOS = 60

VERDE, AMBAR, ROJO, GRIS = "verde", "ambar", "rojo", "gris"

# Iconos del tema del sistema. Se eligen por nombre y no por archivo para que se
# vean bien en cualquier tema y con cualquier escala de pantalla.
ICONOS = {
    VERDE: "emblem-ok-symbolic",
    AMBAR: "content-loading-symbolic",
    ROJO: "dialog-error-symbolic",
    GRIS: "dialog-question-symbolic",
}


def _correr(orden, timeout=15):
    """Ejecuta un comando y devuelve su salida. "" si falla."""
    try:
        r = subprocess.run(orden, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _url_publica():
    """La dirección que el profesor le pasa a sus alumnos, si el túnel está."""
    salida = _correr(["tailscale", "status", "--json"])
    if not salida:
        return ""
    try:
        nombre = json.loads(salida).get("Self", {}).get("DNSName", "").rstrip(".")
    except Exception:
        return ""
    if not nombre:
        return ""
    # Solo se anuncia si el túnel está publicando de verdad; si no, la dirección
    # existiría pero no respondería, y eso confunde más que no decir nada.
    if "Funnel on" not in _correr(["tailscale", "serve", "status"]):
        return ""
    return f"https://{nombre}"


def _contenedores():
    """Cuántos contenedores del AVA están arriba, de los que debería haber."""
    salida = _correr(["docker", "ps", "--filter", "label=com.docker.compose.project=ava",
                      "--format", "{{.Names}}"])
    vivos = [n for n in salida.split("\n") if n.strip()]
    # Los cinco del stack. Los contenedores de alumno (jupyter-*) no cuentan:
    # nacen y mueren solos y su ausencia no es un problema.
    return len([n for n in vivos if not n.startswith("jupyter-")])


def estado():
    """Mira el servidor y devuelve (color, titular, detalle)."""
    if not _correr(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=20):
        return (ROJO, "Docker no está corriendo",
                "El programa que sostiene el AVA no arrancó.")

    arriba = _contenedores()
    if arriba == 0:
        return (ROJO, "El AVA está apagado",
                "Ningún servicio en marcha. Usa «Encender el AVA».")

    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{PUERTO}/hub/login", timeout=8) as r:
            responde = r.status < 500
    except urllib.error.HTTPError as e:
        responde = e.code < 500          # un 302 o un 405 son respuestas sanas
    except Exception:
        responde = False

    if not responde:
        if arriba < 5:
            return (AMBAR, "El AVA está arrancando",
                    f"{arriba} de 5 servicios listos. Suele tardar un minuto.")
        return (ROJO, "El AVA no responde",
                "Los servicios están arriba pero no atienden. Prueba «Reiniciar».")

    url = _url_publica()
    if not url:
        return (AMBAR, "Funciona, pero solo en este computador",
                "Falta publicar el túnel para que entren tus alumnos.")
    return (VERDE, "El AVA está funcionando", f"Tus alumnos pueden entrar en {url}")


def _compose(*args):
    """Un comando de docker compose en la carpeta del AVA."""
    return subprocess.Popen(
        ["docker", "compose", *args], cwd=CARPETA,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main_texto():
    color, titular, detalle = estado()
    print(f"[{color}] {titular}\n{detalle}")
    return 0 if color == VERDE else 1


def main_grafico():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import GLib, Gtk

    # Ubuntu trae Ayatana; el nombre viejo se deja como respaldo por si el
    # equipo es de una versión anterior.
    Indicator = None
    for modulo, version in (("AyatanaAppIndicator3", "0.1"), ("AppIndicator3", "0.1")):
        try:
            gi.require_version(modulo, version)
            Indicator = getattr(__import__("gi.repository", fromlist=[modulo]), modulo)
            break
        except Exception:
            continue
    if Indicator is None:
        print("Falta el soporte de indicadores. Instálalo con:\n"
              "  sudo apt install gir1.2-ayatanaappindicator3-0.1", file=sys.stderr)
        return 2

    ind = Indicator.Indicator.new(
        "ava-servidor", ICONOS[GRIS], Indicator.IndicatorCategory.APPLICATION_STATUS)
    ind.set_status(Indicator.IndicatorStatus.ACTIVE)

    menu = Gtk.Menu()
    item_estado = Gtk.MenuItem(label="Comprobando…")
    item_estado.set_sensitive(False)
    item_detalle = Gtk.MenuItem(label="")
    item_detalle.set_sensitive(False)
    menu.append(item_estado)
    menu.append(item_detalle)
    menu.append(Gtk.SeparatorMenuItem())

    item_copiar = Gtk.MenuItem(label="Copiar la dirección para mis alumnos")
    item_copiar.connect("activate", lambda _: _copiar(_url_publica()))
    menu.append(item_copiar)

    item_abrir = Gtk.MenuItem(label="Abrir el AVA en el navegador")
    item_abrir.connect("activate", lambda _: subprocess.Popen(
        ["xdg-open", _url_publica() or f"http://127.0.0.1:{PUERTO}"]))
    menu.append(item_abrir)

    menu.append(Gtk.SeparatorMenuItem())

    item_encender = Gtk.MenuItem(label="Encender el AVA")
    item_encender.connect("activate", lambda _: _compose("up", "-d"))
    menu.append(item_encender)

    item_reiniciar = Gtk.MenuItem(label="Reiniciar el AVA")
    item_reiniciar.connect("activate", lambda _: _compose("restart"))
    menu.append(item_reiniciar)

    menu.append(Gtk.SeparatorMenuItem())
    item_salir = Gtk.MenuItem(label="Quitar este icono (el AVA sigue funcionando)")
    item_salir.connect("activate", lambda _: Gtk.main_quit())
    menu.append(item_salir)

    menu.show_all()
    ind.set_menu(menu)

    # Para no repetir la misma notificación cada minuto mientras dure una caída.
    ultimo = {"color": None}

    def refrescar():
        color, titular, detalle = estado()
        ind.set_icon_full(ICONOS[color], titular)
        ind.set_title(f"AVA — {titular}")
        item_estado.set_label(titular)
        item_detalle.set_label(detalle)
        item_encender.set_sensitive(color != VERDE)
        item_copiar.set_sensitive(bool(_url_publica()))

        # Solo se avisa al PASAR a rojo, no mientras siga rojo: una notificación
        # cada minuto se vuelve ruido y el profesor la ignora.
        if color == ROJO and ultimo["color"] not in (ROJO, None):
            subprocess.Popen(["notify-send", "-u", "critical", "-i", "dialog-error",
                              "El AVA se cayó", detalle])
        ultimo["color"] = color
        return True

    refrescar()
    GLib.timeout_add_seconds(CADA_SEGUNDOS, refrescar)
    Gtk.main()
    return 0


def _copiar(texto):
    if not texto:
        return
    try:
        from gi.repository import Gdk, Gtk
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(texto, -1)
    except Exception:
        subprocess.run(["xclip", "-selection", "clipboard"], input=texto, text=True)


if __name__ == "__main__":
    sys.exit(main_texto() if "--estado" in sys.argv else main_grafico())
