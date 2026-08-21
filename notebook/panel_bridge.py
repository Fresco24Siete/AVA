"""Panel de progreso del estudiante, servido por su propio contenedor.

Sustituye al índice de cuadernillos: además de la lista, muestra en qué va, su
nota cuando el docente ya calificó, y cómo le está yendo por competencia.

Tres decisiones que gobiernan este archivo:

**El token nunca llega al navegador.** El panel se arma aquí, en el servidor del
alumno, que ya tiene `STUDENT_METRICS_TOKEN`. Si el HTML consultara el backend
por su cuenta, habría que entregarle ese token a la página y cualquiera podría
leerlo desde la consola.

**Si el backend no responde, el panel se dibuja igual.** Es la puerta de entrada:
un fallo de la analítica no puede dejar al alumno sin acceso a sus cuadernillos.
Lo que falta se marca como no disponible y la lista sigue ahí.

**La nota solo se muestra si es la oficial.** Una cifra deducida de la telemetría
no coincide con la de nbgrader —que ejecuta también las pruebas ocultas— y
enseñarla antes de tiempo genera el reclamo de «el panel decía otra cosa».
"""
import html
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from tornado import web

try:
    from jupyter_server.base.handlers import JupyterHandler as _BaseHandler
except ImportError:                                   # notebook 6 clásico
    from notebook.base.handlers import IPythonHandler as _BaseHandler

log = logging.getLogger(__name__)

BASE = os.environ.get("METRICS_API_BASE",
                      os.environ.get("STUDENT_METRICS_API_BASE", "http://api_go:8080"))
TOKEN = os.environ.get("STUDENT_METRICS_TOKEN", "")
CARPETA = os.environ.get("PANEL_CARPETA", "/home/jovyan/work")
NOMBRE = os.environ.get("ALUMNO_NOMBRE", "")
CURSO = os.environ.get("CURSO_ID", "curso_default")
MANIFEST = (os.environ.get("PUBLICADOS_BASE", "/srv/publicados")
            + f"/{CURSO}/manifest.json")


def _activo():
    """Cuál es el cuadernillo de esta semana, AHORA.

    Antes se leía de CUADERNILLO_CODIGO, que el entrypoint fija una sola vez al
    arrancar el contenedor. Publicar con sesiones abiertas no le llegaba a nadie
    hasta el siguiente arranque: el alumno seguía viendo la semana anterior
    marcada, y con el culler en una hora eso es toda una clase. El manifest está
    montado y leerlo cuesta nada.
    """
    try:
        with open(MANIFEST, encoding="utf-8") as f:
            return str(json.load(f).get("cuadernillo_id", ""))
    except Exception:
        return os.environ.get("CUADERNILLO_CODIGO", "")

AZUL, TINTA, GRIS, BORDE = "#2a78d6", "#10294d", "#52514e", "#dfe3e8"
VERDE, AMBAR = "#0f8a4a", "#b57200"


def _titulo(codigo):
    partes = codigo.split("_")
    if len(partes) == 2 and partes[1].isdigit():
        return f"{partes[0].capitalize()} {int(partes[1])}"
    return codigo


def _progreso():
    """Consulta el backend. Devuelve (datos, error_legible)."""
    if not TOKEN:
        return None, "Todavía no hay datos de progreso para esta sesión."
    peticion = urllib.request.Request(
        BASE.rstrip("/") + "/api/mi-progreso",
        headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(peticion, timeout=4) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as err:
        log.warning("[panel] el backend respondió %s", err.code)
        return None, "No se pudo consultar tu progreso en este momento."
    except Exception as err:
        log.warning("[panel] no se pudo consultar el progreso: %s", err)
        return None, "No se pudo consultar tu progreso en este momento."


def _cuadernillos_en_disco():
    """Los .ipynb que el alumno tiene entregados, por si el backend no responde."""
    try:
        archivos = sorted(f for f in os.listdir(CARPETA)
                          if f.endswith(".ipynb") and f != "inicio.ipynb")
    except OSError:
        return []
    return [{"archivo": f, "id": f[:-6]} for f in archivos]


def _barra(hechos, total):
    pct = int(100 * hechos / total) if total else 0
    return (f'<div class="barra"><div class="relleno" style="width:{pct}%"></div></div>'
            f'<div class="pie">{hechos} de {total} ejercicios</div>')


ENTREGAS = os.path.join(CARPETA, ".ava_entregas.json")


def _entregas():
    """Qué ha entregado ya este alumno, según su propia carpeta.

    El registro autoritativo es el del docente, en submitted/. Este es solo para
    poder decirle al alumno «ya entregaste esto el martes», que es la diferencia
    entre confiar en el botón y darle diez veces por si acaso.
    """
    try:
        with open(ENTREGAS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _anotar_entrega(codigo, cuando):
    datos = _entregas()
    datos[codigo] = cuando
    try:
        with open(ENTREGAS, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)
    except OSError as err:
        log.warning("[panel] no se pudo anotar la entrega: %s", err)


def _nombre_en_nbgrader(codigo):
    """Con qué nombre tiene que archivarse la entrega de este cuadernillo.

    nbgrader no identifica el notebook por la tarea sino por su nombre de
    archivo: al calificar compara los de submitted/ con los que generó desde
    source/, y si no coinciden aborta con «No notebooks found, did you forget to
    run generate_assignment?», que no dice nada de lo que pasa de verdad.

    En la carpeta del alumno el archivo se llama semana_02.ipynb, porque ahí el
    nombre tiene que decirle a él de qué semana es. El de nbgrader es el del
    manifest, que sale de source/: cuadernillo.ipynb.
    """
    try:
        with open(MANIFEST, encoding="utf-8") as f:
            m = json.load(f)
        for entrada in m.get("cuadernillos") or []:
            if str(entrada.get("id", "")) == codigo:
                nombre = str(entrada.get("notebook", "")).strip()
                if nombre.endswith(".ipynb"):
                    return nombre
        if str(m.get("cuadernillo_id", "")) == codigo:
            nombre = str(m.get("notebook", "")).strip()
            if nombre.endswith(".ipynb"):
                return nombre
    except Exception as err:
        log.warning("[panel] no pude leer el nombre de nbgrader: %s", err)
    return f"{codigo}.ipynb"


def _entregar(codigo, archivo):
    """Manda el cuadernillo del alumno al backend. Devuelve (ok, mensaje)."""
    if not TOKEN:
        return False, ("No se puede entregar en esta sesión: falta la "
                       "credencial. Vuelve a entrar desde Moodle.")
    ruta = os.path.join(CARPETA, archivo)
    try:
        with open(ruta, encoding="utf-8") as f:
            notebook = json.load(f)
    except Exception as err:
        log.warning("[panel] no se pudo leer %s: %s", ruta, err)
        return False, "No pude leer tu cuadernillo. ¿Lo guardaste?"

    cuerpo = json.dumps({"cuadernillo_id": codigo,
                         "archivo": _nombre_en_nbgrader(codigo),
                         "notebook": notebook}).encode("utf-8")
    peticion = urllib.request.Request(
        BASE.rstrip("/") + "/api/entregas", data=cuerpo, method="POST",
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(peticion, timeout=20) as resp:
            json.loads(resp.read().decode("utf-8"))
        return True, ""
    except urllib.error.HTTPError as err:
        log.warning("[panel] el backend rechazó la entrega: %s", err.code)
        return False, ("El servidor rechazó la entrega. Avisa a tu profesor si "
                       "sigue pasando.")
    except Exception as err:
        log.warning("[panel] no se pudo entregar: %s", err)
        return False, "No se pudo entregar ahora mismo. Inténtalo otra vez."


def _enlace(archivo, base_url):
    """URL para abrir un cuadernillo.

    El panel enlazaba el nombre del archivo a secas. Como el panel se sirve en
    /user/<alumno>/panel, el navegador lo resolvía a /user/<alumno>/semana_01.ipynb,
    que no es una ruta de Jupyter: 404. Y el panel es la página de entrada del
    alumno, sin otra navegación, así que ninguno podía abrir ningún cuadernillo.
    La ruta buena es la del notebook clásico, /user/<alumno>/notebooks/<archivo>.
    """
    return "/".join([base_url.rstrip("/"), "notebooks",
                     urllib.parse.quote(archivo)])


def _boton_entregar(codigo, base_url, xsrf, entregado):
    """El botón que manda el cuadernillo al docente.

    Va como formulario y no como fetch a propósito: el token que autoriza la
    entrega vive aquí, en el servidor del alumno, y no baja al navegador. Es la
    misma razón por la que el progreso se consulta desde aquí.
    """
    accion = html.escape("/".join([base_url.rstrip("/"), "panel", "entregar"]))
    ya = (f'<div class="tenue" style="font-size:13px;margin-top:4px">'
          f'Entregado el {html.escape(entregado)}</div>' if entregado else "")
    etiqueta = "Entregar de nuevo" if entregado else "Entregar"
    return (f'<form method="POST" action="{accion}" style="margin:0">'
            f'<input type="hidden" name="_xsrf" value="{html.escape(xsrf)}">'
            f'<input type="hidden" name="id" value="{html.escape(codigo)}">'
            f'<button class="entregar" type="submit">{etiqueta}</button>'
            f'</form>{ya}')


def _html(datos, aviso, base_url="/", xsrf="", mensaje=""):
    por_id = {c["cuadernillo_id"]: c for c in (datos or {}).get("cuadernillos", [])}
    activo = _activo()
    entregadas = _entregas()
    filas = []
    for nb in _cuadernillos_en_disco():
        d = por_id.get(nb["id"], {})
        marca = ('<span class="marca">Esta semana</span>'
                 if nb["id"] == activo else "")
        # Solo la nota oficial. Una provisional no coincide con la de nbgrader.
        if d.get("origen_nota") == "nbgrader" and d.get("puntos_maximos"):
            nota = (f'<b>{d["puntos_obtenidos"]:g}</b> / {d["puntos_maximos"]:g}')
        else:
            nota = '<span class="tenue">aún sin calificar</span>'
        intentados = d.get("ejercicios_intentados", 0)
        progreso = (_barra(d.get("ejercicios_resueltos", 0), intentados)
                    if intentados else '<span class="tenue">sin empezar</span>')
        abandonos = d.get("abandonos", 0)
        pendiente = (f'<div class="aviso-fila">Dejaste {abandonos} ejercicio(s) '
                     f'a medias</div>' if abandonos else "")
        filas.append(
            f'<tr><td><a href="{html.escape(_enlace(nb["archivo"], base_url))}">'
            f'{html.escape(_titulo(nb["id"]))}</a> {marca}{pendiente}</td>'
            f'<td>{progreso}</td><td class="nota">{nota}</td>'
            f'<td class="nota">'
            f'{_boton_entregar(nb["id"], base_url, xsrf, entregadas.get(nb["id"], ""))}'
            f'</td></tr>')

    if not filas:
        filas = ['<tr><td colspan="4" class="tenue">Todavía no tienes '
                 'cuadernillos entregados.</td></tr>']

    comps = ""
    for c in (datos or {}).get("competencias", []):
        total = c["ejercicios_intentados"] or 1
        pct = int(100 * c["ejercicios_resueltos"] / total)
        color = VERDE if pct >= 70 else (AMBAR if pct >= 40 else "#c8392b")
        comps += (
            f'<div class="comp"><div class="comp-t">{html.escape(c["descripcion"])}</div>'
            f'<div class="barra"><div class="relleno" style="width:{pct}%;'
            f'background:{color}"></div></div>'
            f'<div class="pie">{c["ejercicios_resueltos"]} de '
            f'{c["ejercicios_intentados"]} · {c["errores"]} error(es)</div></div>')
    bloque_comp = (f'<h2>Cómo vas por competencia</h2><div class="comps">{comps}</div>'
                   if comps else "")

    banda = (f'<div class="banda">{html.escape(aviso)}</div>' if aviso else "")
    # Resultado de la última entrega. Va arriba del todo: es lo que el alumno
    # está buscando con la mirada justo después de pulsar el botón.
    if mensaje.startswith("ok:"):
        aviso_entrega = (f'<div class="hecho">{html.escape(mensaje[3:])}</div>')
    elif mensaje:
        aviso_entrega = (f'<div class="banda">{html.escape(mensaje)}</div>')
    else:
        aviso_entrega = ""
    saludo = f", {html.escape(NOMBRE.split(' ')[0])}" if NOMBRE else ""

    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Tu progreso</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
 body{{margin:0;background:#f7f8fa;color:#141a22;
   font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
 .caja{{max-width:860px;margin:0 auto;padding:36px 22px 70px}}
 h1{{font-size:27px;margin:0 0 4px;color:{TINTA}}}
 .sub{{color:{GRIS};margin:0 0 26px}}
 h2{{font-size:19px;margin:36px 0 12px;color:{TINTA}}}
 table{{width:100%;border-collapse:collapse;background:#fff;
   border:1px solid {BORDE};border-radius:6px;overflow:hidden}}
 td{{padding:13px 15px;border-bottom:1px solid {BORDE};vertical-align:top}}
 tr:last-child td{{border-bottom:none}}
 a{{color:{AZUL};text-decoration:none;font-weight:600}}
 a:hover{{text-decoration:underline}}
 .marca{{background:{AZUL};color:#fff;font-size:11px;padding:2px 7px;
   border-radius:3px;margin-left:6px;white-space:nowrap}}
 .nota{{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}}
 .tenue{{color:#8b94a1}}
 .barra{{height:7px;background:#e9ecef;border-radius:4px;overflow:hidden;max-width:230px}}
 .relleno{{height:100%;background:{AZUL};border-radius:4px}}
 .pie{{font-size:12.5px;color:{GRIS};margin-top:4px}}
 .aviso-fila{{font-size:13px;color:{AMBAR};margin-top:3px}}
 .comps{{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}}
 .comp{{background:#fff;border:1px solid {BORDE};border-radius:6px;padding:13px 15px}}
 .comp-t{{font-size:13.5px;color:{TINTA};margin-bottom:8px;line-height:1.4}}
 .banda{{background:#fdf9ef;border-left:3px solid {AMBAR};padding:11px 15px;
   border-radius:4px;margin-bottom:20px;font-size:14.5px}}
 .hecho{{background:#f0f9f4;border-left:3px solid {VERDE};padding:11px 15px;
   border-radius:4px;margin-bottom:20px;font-size:14.5px}}
 .entregar{{background:{AZUL};color:#fff;border:none;border-radius:4px;
   padding:7px 14px;font:600 13.5px system-ui,sans-serif;cursor:pointer}}
 .entregar:hover{{filter:brightness(1.08)}}
</style></head><body><div class="caja">
<h1>Tu progreso{saludo}</h1>
<p class="sub">Tus cuadernillos, en qué vas y tus notas. Lo que respondiste se
conserva siempre.</p>
{banda}{aviso_entrega}
<table><tr><td><b>Cuadernillo</b></td><td><b>Progreso</b></td>
<td class="nota"><b>Nota</b></td><td class="nota"><b>Entrega</b></td></tr>
{''.join(filas)}</table>
{bloque_comp}
</div></body></html>"""


class PanelHandler(_BaseHandler):
    # Heredaba de tornado.web.RequestHandler, que no sabe nada de sesiones: un
    # GET a /user/<correo>/panel devolvia 200 sin credenciales, con el nombre del
    # alumno, sus cuadernillos, su progreso y su nota. Y el usuario es el correo
    # institucional, asi que adivinar la URL de un companero era trivial.
    @web.authenticated
    def get(self):
        # Entregar antes de pintar: si el docente publico despues de que este
        # contenedor arrancara, el cuadernillo nuevo aparece aqui sin tener que
        # reiniciar la sesion. No pisa nada, solo copia lo que falta.
        try:
            import entregar_cuadernillo
            entregar_cuadernillo.main()
        except Exception as err:
            self.log.warning("[panel] no se pudo revisar si hay cuadernillos "
                             "nuevos: %s", err)
        datos, aviso = _progreso()
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.finish(_html(datos, aviso,
                          self.settings.get("base_url", "/"),
                          self.xsrf_token.decode("utf-8"),
                          self.get_query_argument("m", "")))


class EntregarHandler(_BaseHandler):
    """POST /panel/entregar — manda al docente el cuadernillo del alumno.

    Formulario normal, no fetch: así el token de la entrega no baja al
    navegador. La protección xsrf es la de Jupyter, con el token que el panel
    incrusta en el formulario.
    """
    @web.authenticated
    def post(self):
        codigo = (self.get_body_argument("id", "") or "").strip()
        disponibles = {c["id"]: c["archivo"] for c in _cuadernillos_en_disco()}
        if codigo not in disponibles:
            self.redirect(self._panel("No encontré ese cuadernillo."))
            return
        ok, error = _entregar(codigo, disponibles[codigo])
        if ok:
            cuando = datetime.now().strftime("%d/%m a las %H:%M")
            _anotar_entrega(codigo, cuando)
            self.redirect(self._panel(
                f"ok:Entregado. Tu profesor ya tiene {_titulo(codigo)}. "
                f"Puedes seguir trabajando y volver a entregar si lo cambias."))
        else:
            self.redirect(self._panel(error))

    def _panel(self, mensaje):
        base = self.settings.get("base_url", "/").rstrip("/")
        return f"{base}/panel?m=" + urllib.parse.quote(mensaje)


def load_jupyter_server_extension(nbapp):
    if getattr(nbapp, "log", None) is not None:
        globals()["log"] = nbapp.log
    if os.environ.get("ALUMNO_ROL", "estudiante") == "instructor":
        log.info("[panel_bridge] rol instructor: el panel de progreso es del alumno.")
        return
    raiz = nbapp.web_app.settings.get("base_url", "/").rstrip("/")
    nbapp.web_app.add_handlers(".*$", [
        (raiz + "/panel", PanelHandler),
        (raiz + "/panel/entregar", EntregarHandler),
    ])
    log.info("[panel_bridge] listo: panel de progreso en %s/panel", raiz)


def _load_jupyter_server_extension(server_app):
    load_jupyter_server_extension(server_app)
