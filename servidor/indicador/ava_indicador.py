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

Tres cosas que parecen detalles y son la diferencia entre que se vea o no:

1. El icono NO se crea al arrancar, sino cuando aparece en el bus el servicio
   `org.kde.StatusNotifierWatcher`, que es quien lo pinta. Si el programa
   arranca antes que la barra —lo normal al iniciar sesión— crear el indicador
   de inmediato hace que no aparezca nunca, y sin ningún error.
2. El sondeo del servidor va en un hilo aparte. Hecho en el hilo de GTK, una
   consulta lenta congela el menú entero mientras el profesor lo tiene abierto.
3. Los iconos son propios y NO terminan en «-symbolic»: a los symbolic GNOME
   les impone el color de la barra, y los tres estados se verían idénticos.
"""
import json
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request

CARPETA = os.environ.get("AVA_CARPETA", os.path.expanduser("~/AVA"))
PUERTO = os.environ.get("AVA_PUERTO", "8081")
CADA_SEGUNDOS = 60
WATCHER = "org.kde.StatusNotifierWatcher"

VERDE, AMBAR, ROJO = "verde", "ambar", "rojo"
ICONOS = {VERDE: "ava-verde", AMBAR: "ava-ambar", ROJO: "ava-rojo"}
CARPETA_ICONOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "iconos")


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


def _servicios_arriba():
    """Cuántos servicios del AVA están en marcha, de los cinco que debe haber."""
    salida = _correr(["docker", "ps", "--filter",
                      "label=com.docker.compose.project=ava", "--format", "{{.Names}}"])
    vivos = [n for n in salida.split("\n") if n.strip()]
    # Los contenedores de alumno (jupyter-*) no cuentan: nacen y mueren solos.
    return len([n for n in vivos if not n.startswith("jupyter-")])


def _alumnos_trabajando():
    """Cuántos alumnos tienen sesión abierta ahora mismo."""
    salida = _correr(["docker", "ps", "--filter", "name=jupyter-", "--format", "{{.Names}}"])
    return len([n for n in salida.split("\n") if n.strip()])


def estado():
    """Mira el servidor y devuelve (color, titular, detalle, url)."""
    if not _correr(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=20):
        return (ROJO, "Docker no está corriendo",
                "El programa que sostiene el AVA no arrancó.", "")

    arriba = _servicios_arriba()
    if arriba == 0:
        return (ROJO, "El AVA está apagado",
                "Ningún servicio en marcha. Usa «Encender el AVA».", "")

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
                    f"{arriba} de 5 servicios listos. Suele tardar un minuto.", "")
        return (ROJO, "El AVA no responde",
                "Los servicios están arriba pero no atienden. Prueba «Reiniciar».", "")

    url = _url_publica()
    if not url:
        return (AMBAR, "Funciona, pero solo en este computador",
                "Falta publicar el túnel para que entren tus alumnos.", "")
    return (VERDE, "El AVA está funcionando", f"Tus alumnos pueden entrar en {url}", url)


def _copiar(texto):
    """Al portapapeles. wl-copy en Wayland, xclip en X11: xclip no sirve en Wayland."""
    if not texto:
        return
    for orden in (["wl-copy"], ["xclip", "-selection", "clipboard"]):
        try:
            subprocess.run(orden, input=texto, text=True, timeout=5, check=True)
            return
        except Exception:
            continue


def _avisar(titulo, cuerpo, urgencia="normal"):
    try:
        subprocess.Popen(["notify-send", "-u", urgencia, "-i", "dialog-information",
                          titulo, cuerpo])
    except Exception:
        pass


def main_texto():
    color, titular, detalle, _ = estado()
    print(f"[{color}] {titular}\n{detalle}")
    return 0 if color == VERDE else 1


def main_grafico():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import GLib, Gio, Gtk

    # Ubuntu trae Ayatana; el nombre viejo se deja como respaldo para equipos
    # con una versión anterior.
    Indicator = None
    for modulo in ("AyatanaAppIndicator3", "AppIndicator3"):
        try:
            gi.require_version(modulo, "0.1")
            Indicator = getattr(__import__("gi.repository", fromlist=[modulo]), modulo)
            break
        except (ValueError, ImportError):
            continue
    if Indicator is None:
        print("Falta el soporte de indicadores. Instálalo con:\n"
              "  sudo apt install gir1.2-ayatanaappindicator3-0.1", file=sys.stderr)
        return 2

    estado_ui = {"ind": None, "color": None, "url": "", "silencio_hasta": 0,
                 "barra": False}

    menu = Gtk.Menu()
    it_estado = Gtk.MenuItem(label="Comprobando…"); it_estado.set_sensitive(False)
    it_detalle = Gtk.MenuItem(label=""); it_detalle.set_sensitive(False)
    it_copiar = Gtk.MenuItem(label="Copiar la dirección para mis alumnos")
    it_abrir = Gtk.MenuItem(label="Abrir el AVA en el navegador")
    it_encender = Gtk.MenuItem(label="Encender el AVA")
    it_reiniciar = Gtk.MenuItem(label="Reiniciar el AVA")
    it_salir = Gtk.MenuItem(label="Quitar este icono (el AVA sigue funcionando)")

    for w in (it_estado, it_detalle, Gtk.SeparatorMenuItem(), it_copiar, it_abrir,
              Gtk.SeparatorMenuItem(), it_encender, it_reiniciar,
              Gtk.SeparatorMenuItem(), it_salir):
        menu.append(w)
    menu.show_all()

    def compose(*args):
        return subprocess.Popen(["docker", "compose", *args], cwd=CARPETA,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def al_reiniciar(_):
        # Reiniciar corta el trabajo de quien esté dentro. Si hay alguien, se
        # pregunta: el profesor no puede saberlo de otro modo.
        n = _alumnos_trabajando()
        if n:
            d = Gtk.MessageDialog(
                transient_for=None, flags=0, message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.NONE,
                text=f"Hay {n} alumno{'' if n == 1 else 's'} trabajando ahora mismo")
            d.format_secondary_text(
                "Si reinicias, se les cortará lo que estén haciendo y tendrán que "
                "volver a entrar. Lo que ya entregaron no se pierde.")
            d.add_buttons("Cancelar", Gtk.ResponseType.CANCEL,
                          "Reiniciar de todos modos", Gtk.ResponseType.OK)
            d.set_keep_above(True)
            respuesta = d.run()
            d.destroy()
            if respuesta != Gtk.ResponseType.OK:
                return
        # Se apaga el aviso de caída un rato: esta caída la provocó él.
        estado_ui["silencio_hasta"] = GLib.get_monotonic_time() + 180 * 1_000_000
        it_reiniciar.set_sensitive(False)
        it_estado.set_label("Reiniciando… espera")
        if estado_ui["ind"]:
            estado_ui["ind"].set_icon_full(ICONOS[AMBAR], "Reiniciando")
        compose("restart")
        GLib.timeout_add_seconds(90, lambda: (it_reiniciar.set_sensitive(True), False)[1])

    it_copiar.connect("activate", lambda _: _copiar(estado_ui["url"]))
    it_abrir.connect("activate", lambda _: subprocess.Popen(
        ["xdg-open", estado_ui["url"] or f"http://127.0.0.1:{PUERTO}"]))
    it_encender.connect("activate", lambda _: compose("up", "-d"))
    it_reiniciar.connect("activate", al_reiniciar)
    it_salir.connect("activate", lambda _: Gtk.main_quit())

    def pintar(color, titular, detalle, url):
        estado_ui["url"] = url
        it_estado.set_label(titular)
        it_detalle.set_label(detalle)
        it_encender.set_sensitive(color != VERDE)
        it_copiar.set_sensitive(bool(url))
        if estado_ui["ind"]:
            estado_ui["ind"].set_icon_full(ICONOS[color], titular)
            estado_ui["ind"].set_title(f"AVA — {titular}")

        # Solo se avisa al PASAR a rojo, no mientras siga rojo: una notificación
        # por minuto se vuelve ruido y el profesor deja de mirarla.
        callado = GLib.get_monotonic_time() < estado_ui["silencio_hasta"]
        if color == ROJO and estado_ui["color"] not in (ROJO, None) and not callado:
            _avisar("El AVA se cayó", detalle, "critical")
        elif color == VERDE and estado_ui["color"] == ROJO:
            _avisar("El AVA volvió a funcionar", "Tus alumnos ya pueden entrar.")
        estado_ui["color"] = color
        return False

    def refrescar():
        # En un hilo: el sondeo puede tardar hasta 20 s entre docker y la red, y
        # hacerlo en el hilo de GTK congelaría el menú abierto todo ese tiempo.
        def trabajo():
            datos = estado()
            GLib.idle_add(pintar, *datos)
        threading.Thread(target=trabajo, daemon=True).start()
        return True

    def barra_lista(*_):
        if estado_ui["ind"] is not None:
            return
        ind = Indicator.Indicator.new(
            "ava-servidor", ICONOS[AMBAR],
            Indicator.IndicatorCategory.APPLICATION_STATUS)
        if os.path.isdir(CARPETA_ICONOS):
            ind.set_icon_theme_path(CARPETA_ICONOS)
        ind.set_status(Indicator.IndicatorStatus.ACTIVE)
        ind.set_menu(menu)          # sin menú el indicador no llega a aparecer
        estado_ui["ind"] = ind
        estado_ui["barra"] = True
        refrescar()

    def barra_perdida(*_):
        # GNOME Shell puede reiniciarse; al volver se crea el indicador de nuevo.
        estado_ui["ind"] = None

    Gio.bus_watch_name(Gio.BusType.SESSION, WATCHER, Gio.BusNameWatcherFlags.NONE,
                       barra_lista, barra_perdida)

    def sin_barra():
        if not estado_ui["barra"]:
            _avisar("El AVA no puede mostrar su icono",
                    "Falta la extensión de indicadores de GNOME. Cierra sesión y "
                    "vuelve a entrar; si sigue igual, avísale a Diego.", "critical")
        return False

    # Fallar con ruido, no en silencio: si al minuto no hay barra, se dice.
    GLib.timeout_add_seconds(60, sin_barra)
    GLib.timeout_add_seconds(CADA_SEGUNDOS, refrescar)
    refrescar()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main_texto() if "--estado" in sys.argv else main_grafico())
