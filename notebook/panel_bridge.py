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
import hmac
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

# Las dos preguntas de un toque que acompañan a las estrellas. Se eligieron con
# una regla: no preguntar lo que la telemetría ya sabe. El sistema ya mide
# cuántos intentos costó cada ejercicio y quién se atascó; lo que no puede saber
# es cuánto tiempo le dedicó de verdad —incluido el que trabajó fuera de
# Jupyter— ni POR QUÉ se frenó.
TIEMPOS = [
    (1, "Menos de 1 hora"),
    (2, "Entre 1 y 2 horas"),
    (3, "Entre 2 y 4 horas"),
    (4, "Más de 4 horas"),
]

# Lista cerrada, no texto libre: cada opción es una acción distinta del docente
# (reescribir el enunciado, repasar el concepto, dar más ejemplos de sintaxis,
# explicar los errores del corrector, acortar el cuadernillo). En texto libre
# esto no se podría agrupar.
FRENOS = [
    ("enunciado", "No entendí qué me pedían"),
    ("concepto", "No me quedó claro el tema de la clase"),
    ("sintaxis", "Sabía qué hacer, pero no cómo escribirlo en Python"),
    ("error", "No entendí el error rojo que salía"),
    ("tiempo", "No me alcanzó el tiempo"),
    ("nada", "Nada, me fluyó"),
]
# Donde se guarda la corrección que el docente publicó con «Release Feedback».
# El alumno no tiene otra vía para verla: assignment_list —la extensión de
# nbgrader que la traería— está deshabilitada en su imagen a propósito.
CORRECCIONES = os.path.join(CARPETA, ".ava_correcciones")


def _ruta_correccion(tarea):
    return os.path.join(CORRECCIONES, tarea + ".html")


def _bajar_correccion(tarea):
    """Trae del intercambio la corrección de `tarea` y la deja en disco.

    Devuelve la ruta, o "" si el docente todavía no ha publicado ninguna (o si
    el servicio no responde: entonces vale lo que ya hubiera en disco).
    """
    try:
        from nbexchange_cliente import ava
        archivos = ava.feedback(tarea)
    except Exception as err:
        log.warning("[panel] no se pudo consultar la corrección de %s: %s", tarea, err)
        return ""
    if not archivos:
        return ""
    try:
        os.makedirs(CORRECCIONES, exist_ok=True)
        ruta = _ruta_correccion(tarea)
        with open(ruta, "wb") as f:
            f.write(archivos[0]["contenido"])
        return ruta
    except OSError as err:
        log.warning("[panel] no se pudo guardar la corrección de %s: %s", tarea, err)
        return ""


def _hay_correccion(tarea, calificado):
    """¿Se le puede enseñar al alumno la corrección de este cuadernillo?

    Si ya está en disco, sí y sin preguntar al servicio. Si no, solo se consulta
    cuando la nota ya llegó: antes de calificar no hay nada que traer, y el
    panel se carga en cada visita.
    """
    if os.path.isfile(_ruta_correccion(tarea)):
        return True
    return bool(calificado) and bool(_bajar_correccion(tarea))


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


def _tarjeta(nb, d, activo, entregado, base_url, correccion=False):
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
        # Con nota y con corrección publicada, el enlace va pegado a la nota:
        # es lo que el alumno quiere leer justo después de verla.
        ver = ""
        if correccion:
            destino = base_url.rstrip("/") + "/panel/correccion/" + urllib.parse.quote(nb["id"])
            ver = (f' <a class="correccion" href="{html.escape(destino)}" '
                   f'target="_blank" rel="noopener">ver la corrección</a>')
        nota = (f'<div class="dato"><span class="et">Nota</span>'
                f'<b>{d["puntos_obtenidos"]:g}</b> / {d["puntos_maximos"]:g}{ver}</div>')
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

    # La valoración solo se ofrece cuando ya hay algo que valorar: o entregó, o
    # el cuadernillo dejó de ser el de esta semana y no lo entregó. El segundo
    # caso es a propósito: quien abandonó es quien más tiene que contar, y hasta
    # ahora era justo el que no podía decir nada.
    ya_valoro = d.get("valoracion_rating")
    destino = base_url.rstrip("/") + "/panel/valorar/" + urllib.parse.quote(nb["id"])
    if ya_valoro:
        estrellas = "★" * int(ya_valoro) + "☆" * (5 - int(ya_valoro))
        detalle = dict(TIEMPOS).get(d.get("valoracion_tiempo"))
        valoracion = (
            f'<div class="dato"><span class="et">Tu valoración</span>'
            f'<span class="estrellas-mini">{estrellas}</span>'
            + (f' <span class="tenue">· {html.escape(detalle)}</span>' if detalle else "")
            + f' <a class="correccion" href="{html.escape(destino)}">cambiar</a></div>')
    elif entregado:
        valoracion = (
            f'<div class="dato"><span class="et">Tu valoración</span>'
            f'<a class="correccion" href="{html.escape(destino)}">'
            f'Cuéntanos cómo te fue</a> '
            f'<span class="tenue">· 30 segundos, no es una nota</span></div>')
    elif activo and nb["id"] != activo:
        valoracion = (
            f'<div class="dato"><span class="et">Tu valoración</span>'
            f'<a class="correccion" href="{html.escape(destino)}">'
            f'¿Qué pasó con este?</a> '
            f'<span class="tenue">· saber por qué no salió también ayuda</span></div>')
    else:
        valoracion = ""

    abandonos = d.get("abandonos", 0)
    plural = "ejercicio" if abandonos == 1 else "ejercicios"
    pendiente = (f'<div class="aviso-fila">Dejaste {abandonos} {plural} a '
                 f'medias</div>' if abandonos else "")

    return (f'<div class="tarjeta">'
            f'<div class="cabeza"><div><span class="nombre">{titulo}</span>{marca}'
            f'{pendiente}</div>'
            f'<a class="abrir" href="{html.escape(_enlace(nb["archivo"], base_url))}">'
            f'Abrir cuadernillo</a></div>'
            f'<div class="datos">{progreso}{nota}{entrega}{valoracion}</div></div>')


def _html(datos, aviso, base_url="/"):
    por_id = {c["cuadernillo_id"]: c for c in (datos or {}).get("cuadernillos", [])}
    activo = _activo()
    entregadas = _entregas()
    filas = []
    for nb in _cuadernillos_en_disco():
        d = por_id.get(nb["id"], {})
        calificado = d.get("origen_nota") == "nbgrader" and d.get("puntos_maximos")
        filas.append(_tarjeta(nb, d, activo, entregadas.get(nb["id"], ""), base_url,
                              correccion=_hay_correccion(nb["id"], calificado)))

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
 .correccion{{margin-left:8px;font-size:13.5px;color:{AZUL};text-decoration:underline}}
 .estrellas-mini{{color:{AMBAR};letter-spacing:1px}}
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


def _html_valorar(codigo, entregado, previa, base_url, xsrf="", aviso=""):
    """La página donde el alumno valora un cuadernillo.

    Sin una línea de JavaScript, como el resto de este archivo: son radios
    estilados como fichas con `input:checked + label`. Un toque marca, el botón
    envía. Así funciona igual en cualquier navegador y no depende de que cargue
    nada más.

    `xsrf` es el campo oculto que exige Tornado en todo POST. Sin él, el
    servidor del alumno responde «403: '_xsrf' argument missing from POST» y la
    valoración se pierde; lo construye el handler, que es quien tiene la
    petición y puede firmarlo.

    El orden importa: la única pregunta obligatoria va primera y sola, para que
    quien conteste y se vaya deje ya el dato más valioso.
    """
    raiz = base_url.rstrip("/")
    titulo = html.escape(_titulo(codigo))
    prev_rating = (previa or {}).get("rating")
    prev_tiempo = (previa or {}).get("tiempo")
    prev_freno = (previa or {}).get("freno")

    # Las estrellas van en orden inverso en el HTML para poder pintar de dorado
    # la marcada y todas las de su izquierda solo con CSS (~ selecciona hermanos
    # posteriores, así que el 5 se escribe primero).
    estrellas = ""
    for n in (5, 4, 3, 2, 1):
        marcado = " checked" if prev_rating == n else ""
        estrellas += (
            f'<input type="radio" id="e{n}" name="rating" value="{n}" required{marcado}>'
            f'<label for="e{n}" title="{n} de 5">★</label>')

    def fichas(nombre, opciones, previo):
        salida = ""
        for valor, texto in opciones:
            marcado = " checked" if str(previo) == str(valor) else ""
            ident = f"{nombre}_{valor}"
            salida += (
                f'<input type="radio" id="{ident}" name="{nombre}" value="{valor}"{marcado}>'
                f'<label for="{ident}">{html.escape(texto)}</label>')
        return salida

    contexto = ("Ya lo entregaste." if entregado else
                "No alcanzaste a entregarlo, y justo por eso queremos saber qué pasó.")
    banda = f'<div class="banda">{html.escape(aviso)}</div>' if aviso else ""

    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Valorar {titulo}</title>
<style>
 *{{box-sizing:border-box}}
 body{{margin:0;padding:28px 20px 60px;background:#f6f7f9;color:{TINTA};
   font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}}
 .caja{{max-width:640px;margin:0 auto}}
 a.volver{{color:{AZUL};text-decoration:none;font-size:14.5px}}
 h1{{font-size:25px;margin:10px 0 4px}}
 .sub{{color:{GRIS};margin:0 0 8px}}
 .aclara{{background:#eef4fd;border-left:3px solid {AZUL};padding:10px 14px;
   border-radius:4px;font-size:14.5px;margin:0 0 22px}}
 .banda{{background:#fdf9ef;border-left:3px solid {AMBAR};padding:10px 14px;
   border-radius:4px;margin-bottom:16px;font-size:14.5px}}
 .grupo{{background:#fff;border:1px solid {BORDE};border-radius:8px;
   padding:18px 20px;margin-bottom:14px}}
 .preg{{font-weight:650;font-size:16px;margin-bottom:2px}}
 .ayuda{{color:{GRIS};font-size:14px;margin-bottom:12px}}
 .opcional{{color:{GRIS};font-weight:400;font-size:14px}}
 /* Estrellas: el input se oculta y la etiqueta es lo que se ve y se toca. */
 .estrellas{{display:flex;flex-direction:row-reverse;justify-content:flex-end;gap:4px}}
 .estrellas input{{position:absolute;opacity:0;width:0;height:0}}
 .estrellas label{{font-size:40px;line-height:1;color:#d8dde3;cursor:pointer;
   transition:color .12s}}
 .estrellas label:hover, .estrellas label:hover ~ label,
 .estrellas input:checked ~ label{{color:{AMBAR}}}
 .estrellas input:focus-visible + label{{outline:2px solid {AZUL};border-radius:4px}}
 .extremos{{display:flex;justify-content:space-between;color:{GRIS};
   font-size:13px;margin-top:2px;max-width:236px}}
 .fichas{{display:flex;flex-wrap:wrap;gap:8px}}
 .fichas input{{position:absolute;opacity:0;width:0;height:0}}
 .fichas label{{border:1px solid {BORDE};background:#fff;border-radius:20px;
   padding:8px 15px;font-size:14.5px;cursor:pointer;transition:all .12s}}
 .fichas label:hover{{border-color:{AZUL};color:{AZUL}}}
 .fichas input:checked + label{{background:{AZUL};border-color:{AZUL};color:#fff}}
 .fichas input:focus-visible + label{{outline:2px solid {AZUL};outline-offset:2px}}
 textarea{{width:100%;min-height:80px;border:1px solid {BORDE};border-radius:6px;
   padding:10px 12px;font:inherit;font-size:14.5px;resize:vertical}}
 .enviar{{background:{AZUL};color:#fff;border:none;border-radius:6px;
   padding:12px 26px;font:inherit;font-size:15.5px;font-weight:600;cursor:pointer}}
 .enviar:hover{{filter:brightness(1.08)}}
 .pie{{color:{GRIS};font-size:13.5px;margin-top:10px}}
</style></head><body><div class="caja">
<a class="volver" href="{raiz}/panel">← Mis cuadernillos</a>
<h1>¿Cómo te fue con {titulo}?</h1>
<p class="sub">{contexto}</p>
<div class="aclara"><b>Esto lo lee tu profesor.</b> No es una nota y no afecta
tu calificación: le sirve para armar mejor el cuadernillo de la otra semana.</div>
{banda}
<form method="post" action="{raiz}/panel/valorar/{urllib.parse.quote(codigo)}">
  {xsrf}
  <div class="grupo">
    <div class="preg">¿Qué tanto sientes que aprendiste?</div>
    <div class="ayuda">Toca una estrella.</div>
    <div class="estrellas">{estrellas}</div>
    <div class="extremos"><span>1 · casi nada</span><span>5 · bastante</span></div>
  </div>

  <div class="grupo">
    <div class="preg">¿Cuánto tiempo le metiste en total?
      <span class="opcional">— opcional</span></div>
    <div class="ayuda">Cuenta también lo que hiciste por fuera de Jupyter.</div>
    <div class="fichas">{fichas("tiempo", TIEMPOS, prev_tiempo)}</div>
  </div>

  <div class="grupo">
    <div class="preg">¿Qué fue lo que más te frenó?
      <span class="opcional">— opcional</span></div>
    <div class="ayuda">Escoge lo que más pesó.</div>
    <div class="fichas">{fichas("freno", FRENOS, prev_freno)}</div>
  </div>

  <div class="grupo">
    <div class="preg">¿Algo más que quieras decirle?
      <span class="opcional">— opcional</span></div>
    <div class="ayuda">Lo que te sirvió, lo que te sobró, lo que no se entendía.</div>
    <textarea name="comment" maxlength="1000"
      placeholder="Escribe aquí si quieres">{html.escape((previa or {}).get("comment") or "")}</textarea>
  </div>

  <button class="enviar" type="submit">Enviar</button>
  <div class="pie">Puedes volver y cambiar tu respuesta cuando quieras.</div>
</form>
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


class CorreccionHandler(_BaseHandler):
    """GET /panel/correccion/<tarea> — la corrección del docente, en HTML.

    Se sirve desde aquí en vez de dejar el archivo en el árbol del alumno: así
    la ruta se valida contra los cuadernillos que tiene, y cada visita trae la
    última versión publicada (el docente puede corregir y volver a publicar).
    """
    @web.authenticated
    def get(self, tarea):
        tarea = urllib.parse.unquote(tarea or "").strip()
        if tarea not in {c["id"] for c in _cuadernillos_en_disco()}:
            self.set_status(404)
            self.set_header("Content-Type", "text/html; charset=utf-8")
            self.finish("<p>No encontré ese cuadernillo.</p>")
            return

        # Se refresca al abrir; si el servicio no responde, vale la copia que
        # ya estaba en disco: una corrección vieja es mejor que un error.
        ruta = _bajar_correccion(tarea) or _ruta_correccion(tarea)
        if not os.path.isfile(ruta):
            self.set_status(404)
            self.set_header("Content-Type", "text/html; charset=utf-8")
            self.finish("<p>Tu profesor todavía no ha publicado la corrección "
                        "de este cuadernillo.</p>")
            return

        with open(ruta, "rb") as f:
            cuerpo = f.read()
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.finish(cuerpo)


class ValorarHandler(_BaseHandler):
    """GET muestra el formulario, POST lo guarda y vuelve al panel.

    La valoración viaja al backend por el mismo camino que la telemetría
    (metrics_bridge), así que la identidad la pone el token del contenedor y no
    el navegador: un alumno no puede valorar por otro aunque manipule el envío.
    """

    def check_xsrf_cookie(self):
        """El token del formulario viaja en el cuerpo, y ahí JupyterHub no lo ve.

        Este es el único POST del AVA que sale de un <form> normal en vez de una
        llamada de custom.js, y por eso solo aquí aparecía el fallo. JupyterHub
        comprueba el XSRF dos veces: la de Tornado, que sí lee el cuerpo, y otra
        al resolver la identidad de la cookie (HubOAuth._get_user_cookie), que
        solo mira la query y las cabeceras. Esa segunda no encontraba el token,
        se tragaba el error —lo deja en debug— y devolvía «sin usuario»; entonces
        @web.authenticated respondía un 403 pelado: página de error sin motivo y
        ni una línea en el log. De ahí lo difícil que fue verlo.

        Hacemos la misma comprobación que haría JupyterHub, pero leyendo el token
        también del cuerpo crudo, que sí está siempre disponible. No se rebaja la
        protección: sigue exigiendo el token que corresponde a esta sesión. (Lo
        contrario que metrics_bridge y tutor_bridge, que la desactivan porque son
        endpoints internos; este guarda lo que escribe el alumno.)
        """
        recibido = (self.get_argument("_xsrf", None)
                    or self.request.headers.get("X-Xsrftoken")
                    or self.request.headers.get("X-Csrftoken")
                    or self._xsrf_del_cuerpo())
        if not recibido:
            raise web.HTTPError(
                403, f"'_xsrf' argument missing from {self.request.method}")
        esperado = self.xsrf_token
        if isinstance(esperado, str):
            esperado = esperado.encode("utf8")
        if not hmac.compare_digest(recibido.encode("utf8"), esperado):
            raise web.HTTPError(
                403,
                f"XSRF cookie does not match {self.request.method} argument")

    def _xsrf_del_cuerpo(self):
        """El _xsrf del cuerpo del POST, parseado a mano.

        `self.request.body` está montado antes de que corra nada del handler, así
        que esto funciona sin depender de cuándo Tornado rellena los argumentos.
        """
        try:
            campos = urllib.parse.parse_qs(
                self.request.body.decode("utf8", "replace"))
        except Exception:
            return None
        valores = campos.get("_xsrf") or []
        return valores[0] if valores else None

    def _valoracion_previa(self, codigo):
        """Lo que ya respondió, si respondió. Sale del backend, que es la verdad."""
        datos, _ = _progreso()
        for c in (datos or {}).get("cuadernillos", []):
            if c.get("cuadernillo_id") == codigo and c.get("valoracion_rating"):
                return {"rating": c.get("valoracion_rating"),
                        "tiempo": c.get("valoracion_tiempo"),
                        "freno": c.get("valoracion_freno"),
                        "comment": None}
        return None

    @web.authenticated
    def get(self, codigo):
        codigo = urllib.parse.unquote(codigo or "").strip()
        if codigo not in {c["id"] for c in _cuadernillos_en_disco()}:
            self.set_status(404)
            self.set_header("Content-Type", "text/html; charset=utf-8")
            self.finish("<p>No encontré ese cuadernillo.</p>")
            return
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.finish(_html_valorar(codigo, bool(_entregas().get(codigo)),
                                  self._valoracion_previa(codigo),
                                  self.settings.get("base_url", "/"),
                                  xsrf=self.xsrf_form_html()))

    @web.authenticated
    def post(self, codigo):
        codigo = urllib.parse.unquote(codigo or "").strip()
        base = self.settings.get("base_url", "/").rstrip("/")
        if codigo not in {c["id"] for c in _cuadernillos_en_disco()}:
            self.set_status(404)
            self.finish("<p>No encontré ese cuadernillo.</p>")
            return

        entregado = bool(_entregas().get(codigo))

        try:
            rating = int(self.get_body_argument("rating"))
        except Exception:
            rating = 0
        if rating < 1 or rating > 5:
            self.set_header("Content-Type", "text/html; charset=utf-8")
            self.finish(_html_valorar(codigo, entregado, self._valoracion_previa(codigo),
                                      self.settings.get("base_url", "/"),
                                      xsrf=self.xsrf_form_html(),
                                      aviso="Toca una estrella para poder enviar."))
            return

        # Los opcionales: vacío es «no contestó», que no es lo mismo que cero.
        tiempo = self.get_body_argument("tiempo", "")
        freno = self.get_body_argument("freno", "")
        comentario = (self.get_body_argument("comment", "") or "").strip()[:1000]

        evento = {
            "tipo_evento": "cuadernillo_rating",
            "cuadernillo": codigo,
            "rating": rating,
            # Se manda siempre, aunque esté vacío: así el alumno puede borrar
            # lo que escribió antes. Ausente significaría «no lo toqué».
            "comment": comentario,
            "entregado": entregado,
            "origen": "panel",
        }
        if tiempo.isdigit() and 1 <= int(tiempo) <= 4:
            evento["tiempo"] = int(tiempo)
        if freno in {f[0] for f in FRENOS}:
            evento["freno"] = freno

        ok = _enviar_valoracion(evento)
        if not ok:
            self.set_header("Content-Type", "text/html; charset=utf-8")
            self.finish(_html_valorar(
                codigo, entregado, self._valoracion_previa(codigo),
                self.settings.get("base_url", "/"), xsrf=self.xsrf_form_html(),
                aviso="No se pudo guardar ahora mismo. Inténtalo otra vez en un momento."))
            return

        self.redirect(base + "/panel")


def _enviar_valoracion(evento):
    """Manda la valoración al backend reutilizando el puente de métricas.

    No se hace una petición HTTP al propio servidor —tendría que autenticarse
    contra sí mismo— sino que se llama a la función del puente, que es quien
    sabe poner la identidad del alumno y el token del contenedor. Con eso, la
    valoración no se puede falsificar desde una celda ni desde el navegador.
    """
    try:
        import metrics_bridge
        return metrics_bridge.enviar_evento_sincrono(evento)
    except Exception as err:
        log.warning("[panel] no se pudo guardar la valoración de %s: %s",
                    evento.get("cuadernillo"), err)
        return False


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
        (raiz + r"/panel/correccion/([^/]+)", CorreccionHandler),
        (raiz + r"/panel/valorar/([^/]+)", ValorarHandler),
    ])
    log.info("[panel_bridge] listo: panel de progreso en %s/panel", raiz)


def _load_jupyter_server_extension(server_app):
    load_jupyter_server_extension(server_app)
