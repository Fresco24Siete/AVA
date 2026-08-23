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
import re
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


def _publicados():
    """Qué hay publicado, según la última consulta al servicio de intercambio.

    La escribe entregar_cuadernillo cada vez que este panel se abre (ver
    PanelHandler.get), así que está al día sin volver a preguntar.
    """
    try:
        import entregar_cuadernillo
        with open(entregar_cuadernillo.PUBLICADOS, encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except Exception:
        return {}


def _activo():
    """Cuál es el cuadernillo de esta semana, AHORA.

    Antes se leía de CUADERNILLO_CODIGO, que el entrypoint fija una sola vez al
    arrancar el contenedor. Publicar con sesiones abiertas no le llegaba a nadie
    hasta el siguiente arranque: el alumno seguía viendo la semana anterior
    marcada, y con el culler en una hora eso es toda una clase. Ahora sale de lo
    último que se consultó al servicio, que se refresca al abrir el panel.
    """
    try:
        import entregar_cuadernillo
        return entregar_cuadernillo.activo_de(_publicados().get("cuadernillos") or {})
    except Exception:
        return os.environ.get("CUADERNILLO_CODIGO", "")

AZUL, TINTA, GRIS, BORDE = "#2a78d6", "#10294d", "#52514e", "#dfe3e8"
VERDE, AMBAR = "#0f8a4a", "#b57200"


def _titulo(codigo):
    # Una version vieja conservada (semana_01_v2) es "Semana 1 (version 2)",
    # no una tarjeta con el codigo crudo.
    version = re.match(r"^(.*)_v(\d+)$", codigo)
    sufijo = ""
    if version:
        codigo, sufijo = version.group(1), f" (versión {version.group(2)})"
    partes = codigo.split("_")
    if len(partes) == 2 and partes[1].isdigit():
        return f"{partes[0].capitalize()} {int(partes[1])}{sufijo}"
    return codigo + sufijo


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
    """Qué ha entregado ya este alumno.

    Lo dice el servicio de intercambio, que es quien recibió la entrega (la
    última consulta queda en la nota local que escribe entregar_cuadernillo).
    Si no hay respuesta del servicio, vale la anotación propia de este panel.
    Sirve para decirle al alumno «ya entregaste esto el martes», que es la
    diferencia entre confiar en el botón y darle diez veces por si acaso.
    """
    try:
        with open(ENTREGAS, encoding="utf-8") as f:
            datos = json.load(f)
    except Exception:
        datos = {}
    for codigo, ts in (_publicados().get("entregas") or {}).items():
        cuando = _hora_legible(ts)
        if cuando:
            datos[codigo] = cuando
    return datos


def _hora_legible(ts):
    """'2026-08-22 21:10:00.123456 UTC' -> '22/08 a las 16:10' (hora de Colombia)."""
    try:
        from datetime import timedelta, timezone
        base = str(ts).rsplit(" ", 1)[0]
        f = datetime.strptime(base, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
        return f.astimezone(timezone(timedelta(hours=-5))).strftime("%d/%m a las %H:%M")
    except Exception:
        return ""


def _anotar_entrega(codigo, cuando):
    datos = _entregas()
    datos[codigo] = cuando
    try:
        with open(ENTREGAS, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)
    except OSError as err:
        log.warning("[panel] no se pudo anotar la entrega: %s", err)


def _tarea_de(codigo):
    """'semana_02_v3' -> 'semana_02'.

    Cuando el docente corrige un cuadernillo, la versión nueva llega al alumno
    como <id>_vN.ipynb. La TAREA de nbgrader sigue siendo <id>: entregar bajo
    el nombre con sufijo crearía una tarea que no existe y nadie calificaría.
    """
    return re.sub(r"_v\d+$", "", codigo)


def _nombre_en_nbgrader(codigo):
    """Con qué nombre tiene que archivarse la entrega de este cuadernillo.

    nbgrader no identifica el notebook por la tarea sino por su nombre de
    archivo: al calificar compara los de submitted/ con los que generó desde
    source/, y si no coinciden aborta con «No notebooks found, did you forget to
    run generate_assignment?», que no dice nada de lo que pasa de verdad.

    En la carpeta del alumno el archivo se llama semana_02.ipynb, porque ahí el
    nombre tiene que decirle a él de qué semana es. El de nbgrader es el que
    liberó el docente, que sale de source/: cuadernillo.ipynb.
    """
    info = (_publicados().get("cuadernillos") or {}).get(_tarea_de(codigo)) or {}
    nombre = str(info.get("notebook", "")).strip()
    return nombre if nombre.endswith(".ipynb") else f"{_tarea_de(codigo)}.ipynb"


def _entregar(codigo, archivo):
    """Manda el cuadernillo del alumno al servicio de intercambio.

    Devuelve (ok, mensaje). De ahí lo recoge el docente con «Collect» en
    formgrader. Quién entrega lo decide el servicio por el token del contenedor,
    no por nada que venga en la petición.
    """
    ruta = os.path.join(CARPETA, archivo)
    try:
        with open(ruta, encoding="utf-8") as f:
            json.load(f)
    except Exception as err:
        log.warning("[panel] no se pudo leer %s: %s", ruta, err)
        return False, "No pude leer tu cuadernillo. ¿Lo guardaste?"

    try:
        from nbexchange_cliente import ava
        ava.entregar(_tarea_de(codigo), {_nombre_en_nbgrader(codigo): ruta})
        return True, ""
    except Exception as err:
        log.warning("[panel] no se pudo entregar %s: %s", codigo, err)
        return False, ("No se pudo entregar ahora mismo. Inténtalo otra vez y, "
                       "si sigue pasando, avisa a tu profesor.")


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


def _tarjeta(nb, d, activo, entregado, base_url):
    """Un cuadernillo, como lo ve el alumno.

    Antes era una fila de tabla con cuatro columnas y dos acciones —abrir y
    entregar— compitiendo por la atención. El alumno no tenía claro qué hacía
    cada una, y entregar desde aquí mandaba el archivo tal como estaba en disco,
    sin guardar lo que acabara de escribir.

    Ahora cada sitio hace una cosa: el panel es para saber dónde vas y abrir; se
    entrega desde dentro del cuadernillo, que es donde estás cuando terminas y
    donde se puede guardar antes de mandar. Aquí solo se dice si ya está
    entregado.
    """
    titulo = html.escape(_titulo(nb["id"]))
    marca = ('<span class="marca">Esta semana</span>' if nb["id"] == activo else "")

    if d.get("origen_nota") == "nbgrader" and d.get("puntos_maximos"):
        nota = (f'<div class="dato"><span class="et">Nota</span>'
                f'<b>{d["puntos_obtenidos"]:g}</b> / {d["puntos_maximos"]:g}</div>')
    else:
        nota = ('<div class="dato"><span class="et">Nota</span>'
                '<span class="tenue">aún sin calificar</span></div>')

    intentados = d.get("ejercicios_intentados", 0)
    if intentados:
        resueltos = d.get("ejercicios_resueltos", 0)
        progreso = (f'<div class="dato"><span class="et">Vas por</span>'
                    f'{_barra(resueltos, intentados)}</div>')
    else:
        progreso = ('<div class="dato"><span class="et">Vas por</span>'
                    '<span class="tenue">sin empezar</span></div>')

    if entregado:
        entrega = (f'<div class="dato"><span class="et">Entrega</span>'
                   f'<span class="ok">Entregado</span> '
                   f'<span class="tenue">el {html.escape(entregado)}</span></div>')
    else:
        entrega = ('<div class="dato"><span class="et">Entrega</span>'
                   '<span class="tenue">sin entregar · el botón está dentro '
                   'del cuadernillo</span></div>')

    abandonos = d.get("abandonos", 0)
    plural = "ejercicio" if abandonos == 1 else "ejercicios"
    pendiente = (f'<div class="aviso-fila">Dejaste {abandonos} {plural} a '
                 f'medias</div>' if abandonos else "")

    return (f'<div class="tarjeta">'
            f'<div class="cabeza"><div><span class="nombre">{titulo}</span>{marca}'
            f'{pendiente}</div>'
            f'<a class="abrir" href="{html.escape(_enlace(nb["archivo"], base_url))}">'
            f'Abrir cuadernillo</a></div>'
            f'<div class="datos">{progreso}{nota}{entrega}</div></div>')


def _html(datos, aviso, base_url="/"):
    por_id = {c["cuadernillo_id"]: c for c in (datos or {}).get("cuadernillos", [])}
    activo = _activo()
    entregadas = _entregas()
    filas = []
    for nb in _cuadernillos_en_disco():
        filas.append(_tarjeta(nb, por_id.get(nb["id"], {}), activo,
                              entregadas.get(nb["id"], ""), base_url))

    if not filas:
        filas = ['<div class="tarjeta"><span class="tenue">Todavía no tienes '
                 'cuadernillos. Aparecerán aquí en cuanto tu profesor publique '
                 'el primero.</span></div>']

    comps = ""
    for c in (datos or {}).get("competencias", []):
        intentados = c["ejercicios_intentados"] or 0
        resueltos = c["ejercicios_resueltos"] or 0
        errores = c["errores"] or 0
        pct = int(100 * resueltos / intentados) if intentados else 0
        color = VERDE if pct >= 70 else (AMBAR if pct >= 40 else "#c8392b")

        # El titular es el numero, no la formulacion del microcurriculo: el
        # alumno esta mirando como va, no leyendo el plan de estudios. La
        # formulacion se queda debajo, que es la que le dice de que va.
        ej = "ejercicio" if intentados == 1 else "ejercicios"
        titular = f'{resueltos} de {intentados} {ej}'

        if resueltos == intentados and intentados:
            pie = "Los resolviste todos."
        elif errores:
            veces = "vez" if errores == 1 else "veces"
            pie = f'Te equivocaste {errores} {veces} por el camino.'
        else:
            pie = "Aún no has acertado ninguno."

        comps += (
            f'<div class="comp">'
            f'<div class="comp-n">{titular}</div>'
            f'<div class="barra"><div class="relleno" style="width:{pct}%;'
            f'background:{color}"></div></div>'
            f'<div class="comp-t">{html.escape(c["descripcion"])}</div>'
            f'<div class="pie">{pie}</div></div>')

    bloque_comp = (f'<h2>Qué has aprendido</h2>'
                   f'<p class="sub2">Cada ejercicio del curso practica una o varias '
                   f'de estas capacidades. Esto es lo que llevas de cada una.</p>'
                   f'<div class="comps">{comps}</div>' if comps else "")

    banda = (f'<div class="banda">{html.escape(aviso)}</div>' if aviso else "")
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
 .lista{{display:flex;flex-direction:column;gap:12px}}
 .tarjeta{{background:#fff;border:1px solid {BORDE};border-radius:8px;
   padding:16px 18px}}
 .cabeza{{display:flex;align-items:center;justify-content:space-between;
   gap:14px;flex-wrap:wrap}}
 .nombre{{font-size:17px;font-weight:650;color:{TINTA}}}
 .abrir{{background:{AZUL};color:#fff;border-radius:5px;padding:8px 16px;
   font-size:14px;font-weight:600;text-decoration:none;white-space:nowrap}}
 .abrir:hover{{filter:brightness(1.08);text-decoration:none}}
 .datos{{display:flex;gap:28px;flex-wrap:wrap;margin-top:14px;
   padding-top:14px;border-top:1px solid {BORDE}}}
 .dato{{font-size:14.5px;color:{TINTA}}}
 .et{{display:block;font-size:12px;color:{GRIS};text-transform:uppercase;
   letter-spacing:.04em;margin-bottom:4px}}
 .ok{{color:{VERDE};font-weight:600}}
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
 .comps{{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}}
 .sub2{{color:{GRIS};font-size:14.5px;margin:-6px 0 14px}}
 .comp{{background:#fff;border:1px solid {BORDE};border-radius:6px;padding:13px 15px}}
 .comp-n{{font-size:19px;font-weight:650;color:{TINTA};margin-bottom:9px}}
 .comp-t{{font-size:13px;color:{GRIS};margin-top:9px;line-height:1.45}}
 .banda{{background:#fdf9ef;border-left:3px solid {AMBAR};padding:11px 15px;
   border-radius:4px;margin-bottom:20px;font-size:14.5px}}
 .hecho{{background:#f0f9f4;border-left:3px solid {VERDE};padding:11px 15px;
   border-radius:4px;margin-bottom:20px;font-size:14.5px}}

</style></head><body><div class="caja">
<h1>Tu progreso{saludo}</h1>
<p class="sub">Tus cuadernillos, en qué vas y tus notas. Lo que respondiste se
conserva siempre.</p>
{banda}
<div class="lista">{''.join(filas)}</div>
{bloque_comp}
</div>
</body></html>"""


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
                          self.settings.get("base_url", "/")))


class EntregarHandler(_BaseHandler):
    """POST /panel/entregar — manda al docente el cuadernillo del alumno.

    Responde JSON; quien pinta el resultado es el propio panel al recargarse. El
    token que autoriza la entrega ante el backend no sale de aquí.
    """
    @web.authenticated
    def post(self):
        try:
            codigo = str((json.loads(self.request.body or b"{}") or {}).get("id", ""))
        except Exception:
            codigo = ""
        codigo = codigo.strip()

        disponibles = {c["id"]: c["archivo"] for c in _cuadernillos_en_disco()}
        self.set_header("Content-Type", "application/json; charset=utf-8")
        if codigo not in disponibles:
            self.finish(json.dumps(
                {"ok": False, "mensaje": "No encontré ese cuadernillo."}))
            return

        ok, error = _entregar(codigo, disponibles[codigo])
        if not ok:
            self.finish(json.dumps({"ok": False, "mensaje": error}))
            return

        cuando = datetime.now().strftime("%d/%m a las %H:%M")
        _anotar_entrega(codigo, cuando)
        self.finish(json.dumps({"ok": True, "mensaje":
                                f"ok:Entregado. Tu profesor ya tiene "
                                f"{_titulo(codigo)}. Puedes seguir trabajando y "
                                f"volver a entregar si lo cambias."}))


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
