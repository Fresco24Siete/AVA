"""Panel del docente: cómo va el curso, servido por su propio contenedor.

Formgrader responde a «¿qué actividades tengo?» y a nada más. El docente no
tiene forma de ver qué le ha llegado ni en qué punto del ciclo está cada
cuadernillo, y desde que el alumno entrega por HTTP —directo a `submitted/`, sin
pasar por el buzón— «Collect» ya no trae nada: una entrega puede estar en disco
sin que nada en la pantalla lo diga.

Tres decisiones que gobiernan este archivo:

**Solo lee disco.** Todo lo que muestra sale de lo que este contenedor ya monta:
`source/`, `release/`, `submitted/`, `autograded/`, el manifest de publicados y
el libro de notas. Sin backend, sin red, sin base de datos. Lo agregado —cómo va
el grupo por competencia, qué ejercicio se atasca— vendrá después y en su propia
sección, para que un fallo de la analítica no se lleve por delante lo que el
docente necesita para trabajar hoy.

**El libro de notas se abre en solo lectura.** `nbgrader.api.Gradebook` escribe
al abrirse —crea el curso si no existe— y compite por el lock con un Autograde
en marcha. Aquí se abre el sqlite con `mode=ro`, que no puede escribir ni
bloquear aunque se quiera.

**Habla el mismo idioma que el panel del alumno.** «Esta semana», «a medias»,
«aún sin calificar». Si el profesor y el alumno miran cifras con nombres
distintos, la conversación en clase empieza por traducir.
"""
import html
import json
import logging
import os
import sqlite3
import time

from tornado import web

try:
    from jupyter_server.base.handlers import JupyterHandler as _BaseHandler
except ImportError:                                   # notebook 6 clásico
    from notebook.base.handlers import IPythonHandler as _BaseHandler

log = logging.getLogger(__name__)

CURSO = os.environ.get("CURSO_ID", "curso_default")
RAIZ = os.environ.get("NBGRADER_BASE", "/srv/nbgrader") + f"/{CURSO}"
MANIFEST = (os.environ.get("PUBLICADOS_BASE", "/srv/publicados")
            + f"/{CURSO}/manifest.json")

AZUL, TINTA, GRIS, BORDE = "#2a78d6", "#10294d", "#52514e", "#dfe3e8"
VERDE, AMBAR, ROJO = "#0f8a4a", "#b57200", "#c8392b"


# --- Lecturas de disco -------------------------------------------------------

def _carpetas(ruta):
    try:
        return sorted(d.name for d in os.scandir(ruta) if d.is_dir())
    except OSError:
        return []


def _manifest():
    try:
        with open(MANIFEST, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _entregas():
    """Qué hay en submitted/, leyendo solo nombres y fechas.

    No se abre ningún .ipynb: son ~350 KB cada uno y con 25 alumnos por 16
    semanas eso serían 140 MB de JSON por carga de página.
    """
    salida = []
    base = os.path.join(RAIZ, "submitted")
    for alumno in _carpetas(base):
        for tarea in _carpetas(os.path.join(base, alumno)):
            carpeta = os.path.join(base, alumno, tarea)
            cuando = tam = 0
            for f in os.scandir(carpeta):
                if f.name.endswith(".ipynb"):
                    try:
                        st = f.stat()
                        cuando = max(cuando, st.st_mtime)
                        tam += st.st_size
                    except OSError:
                        pass
            salida.append({"alumno": alumno, "tarea": tarea,
                           "cuando": cuando, "bytes": tam,
                           "calificada": _calificada(alumno, tarea, cuando)})
    salida.sort(key=lambda e: e["cuando"], reverse=True)
    return salida


def _calificada(alumno, tarea, entregada_en):
    """(bool calificada, bool reentregada_despues).

    nbgrader no deja fecha de entrega cuando el archivo llega por HTTP en vez de
    por su buzón, así que «¿la calificación es posterior a la entrega?» se
    responde comparando fechas de archivo. Es una heurística del sistema de
    ficheros y la pantalla lo dice.
    """
    carpeta = os.path.join(RAIZ, "autograded", alumno, tarea)
    if not os.path.isdir(carpeta):
        return (False, False)
    calificada_en = 0
    try:
        for f in os.scandir(carpeta):
            if f.name.endswith(".ipynb"):
                calificada_en = max(calificada_en, f.stat().st_mtime)
    except OSError:
        pass
    return (True, bool(calificada_en and entregada_en > calificada_en + 2))


def _libro():
    """Lo que sabe el libro de notas, en solo lectura.

    Devuelve (tareas, notas) donde tareas es {nombre: puntos_maximos} y notas es
    {(alumno, tarea): (obtenidos, maximos)}. Si el libro no existe todavía
    —curso recién montado— devuelve vacíos, no revienta.
    """
    bd = os.path.join(RAIZ, "gradebook.db")
    if not os.path.isfile(bd):
        return {}, {}
    try:
        con = sqlite3.connect(f"file:{bd}?mode=ro", uri=True, timeout=2)
    except sqlite3.Error as err:
        log.warning("[panel-docente] no se pudo leer el libro de notas: %s", err)
        return {}, {}
    tareas, notas = {}, {}
    try:
        # nbgrader guarda las celdas con herencia de tabla unica: base_cell
        # tiene el notebook, y grade_cells —en plural— solo el puntaje, atada
        # por el mismo id. Consultar grade_cell.notebook_id no da cero: da un
        # error de tabla inexistente que se traga el except de abajo y deja la
        # columna de puntos vacia sin decir por que.
        for nombre, maximos in con.execute("""
                SELECT a.name, COALESCE(SUM(gc.max_score), 0)
                  FROM assignment a
                  LEFT JOIN notebook n    ON n.assignment_id = a.id
                  LEFT JOIN base_cell b   ON b.notebook_id = n.id
                  LEFT JOIN grade_cells gc ON gc.id = b.id
                 GROUP BY a.name"""):
            tareas[nombre] = float(maximos or 0)
        for alumno, tarea, obtenidos in con.execute("""
                SELECT s.id, a.name, COALESCE(SUM(g.auto_score), 0)
                  FROM grade g
                  JOIN submitted_notebook sn   ON sn.id = g.notebook_id
                  JOIN submitted_assignment sa ON sa.id = sn.assignment_id
                  JOIN student s               ON s.id = sa.student_id
                  JOIN assignment a            ON a.id = sa.assignment_id
                 GROUP BY s.id, a.name"""):
            notas[(alumno, tarea)] = (float(obtenidos or 0),
                                      tareas.get(tarea, 0.0))
    except sqlite3.Error as err:
        # Un libro de una versión distinta de nbgrader no debe dejar al docente
        # sin panel: se pierde la columna de notas, no la página.
        log.warning("[panel-docente] el libro de notas no se pudo leer entero: %s", err)
    finally:
        con.close()
    return tareas, notas


def _ciclo():
    """En qué punto está cada cuadernillo, juntando las cuatro fuentes."""
    m = _manifest()
    activo = str(m.get("cuadernillo_id", ""))
    publicados = {str(e.get("id", "")): e for e in (m.get("cuadernillos") or [])}
    tareas_libro, _ = _libro()

    entregas_por_tarea = {}
    for e in _entregas():
        d = entregas_por_tarea.setdefault(e["tarea"], {"total": 0, "calificadas": 0})
        d["total"] += 1
        if e["calificada"][0]:
            d["calificadas"] += 1

    nombres = sorted(set(_carpetas(os.path.join(RAIZ, "source")))
                     | set(publicados) | set(tareas_libro))
    filas = []
    for n in nombres:
        generada = os.path.isdir(os.path.join(RAIZ, "release", n))
        pub = n in publicados
        ent = entregas_por_tarea.get(n, {"total": 0, "calificadas": 0})
        entrada = publicados.get(n, {})
        filas.append({
            "tarea": n,
            "generada": generada,
            "publicada": pub,
            "activa": n == activo,
            "abre": entrada.get("abre"),
            "cierra": entrada.get("cierra"),
            "puntos": tareas_libro.get(n),
            "entregas": ent["total"],
            "calificadas": ent["calificadas"],
            "siguiente": _siguiente_paso(generada, pub, ent),
        })
    return activo, filas


def _siguiente_paso(generada, publicada, ent):
    """Qué le toca hacer al docente con este cuadernillo. Uno solo, el primero."""
    if not generada:
        return "Generar"
    if not publicada:
        return "Publicar con publicar-cuadernillo"
    if ent["total"] and ent["calificadas"] < ent["total"]:
        return "Calificar"
    if ent["total"] and ent["calificadas"] == ent["total"]:
        return "Subir notas con registrar-notas"
    return "Esperando entregas"


# --- Presentación ------------------------------------------------------------

def _titulo(codigo):
    partes = codigo.split("_")
    if len(partes) == 2 and partes[1].isdigit():
        return f"{partes[0].capitalize()} {int(partes[1])}"
    return codigo


def _nombre(codigo):
    """Título legible + el identificador real debajo.

    'semana_01' y 'semana_1' se leen los dos como «Semana 1», y en el curso
    conviven: el segundo es la demo vieja. En el panel del alumno eso da igual
    porque solo ve lo publicado, pero el docente trabaja con carpetas y necesita
    saber cuál es cuál antes de borrar o generar.
    """
    bonito = _titulo(codigo)
    if bonito == codigo:
        return f'<b>{html.escape(codigo)}</b>'
    return (f'<b>{html.escape(bonito)}</b>'
            f'<div class="mono tenue">{html.escape(codigo)}</div>')


def _hace(marca):
    if not marca:
        return "—"
    seg = max(0, int(time.time() - marca))
    if seg < 90:
        return "hace un momento"
    if seg < 3600:
        return f"hace {seg // 60} min"
    if seg < 86400:
        h = seg // 3600
        return f"hace {h} hora" + ("" if h == 1 else "s")
    d = seg // 86400
    return f"hace {d} día" + ("" if d == 1 else "s")


def _tamano(b):
    return f"{b / 1024:.0f} KB" if b < 1024 * 1024 else f"{b / 1048576:.1f} MB"


def _seccion_entregas(entregas, notas):
    pendientes = [e for e in entregas if not e["calificada"][0]]
    reentregadas = [e for e in entregas if e["calificada"][1]]

    if not entregas:
        return ('<div class="caja vacia">Todavía no ha entregado nadie. '
                'Cuando lo hagan aparecerán aquí, con la hora, y sin que tengas '
                'que pulsar Recoger: el cuadernillo llega directo.</div>')

    filas = ""
    for e in entregas:
        calificada, reentregada = e["calificada"]
        if reentregada:
            estado = f'<span class="mal">Reentregado después de calificar</span>'
        elif calificada:
            nota = notas.get((e["alumno"], e["tarea"]))
            estado = (f'<span class="bien">Calificado</span> '
                      f'<span class="tenue">{nota[0]:g} / {nota[1]:g}</span>'
                      if nota else '<span class="bien">Calificado</span>')
        else:
            estado = '<span class="pend">Sin calificar</span>'
        filas += (
            f'<tr><td>{_nombre(e["tarea"])}</td>'
            f'<td class="mono">{html.escape(e["alumno"])}</td>'
            f'<td>{_hace(e["cuando"])}</td>'
            f'<td class="num">{_tamano(e["bytes"])}</td>'
            f'<td>{estado}</td></tr>')

    aviso = ""
    if pendientes:
        n = len(pendientes)
        aviso = (f'<div class="banda">Tienes <b>{n}</b> entrega'
                 f'{"" if n == 1 else "s"} sin calificar. Se califican con '
                 f'<b>Calificar</b> en formgrader; no hace falta Recoger, '
                 f'porque el cuadernillo del alumno llega directo.</div>')
    if reentregadas:
        aviso += ('<div class="banda">Alguien volvió a entregar después de que '
                  'calificaras. Vuelve a calificar esa entrega para que la nota '
                  'corresponda a lo último que mandó. <span class="tenue">'
                  '(Deducido de las fechas de los archivos.)</span></div>')

    return (aviso + '<div class="caja"><table>'
            '<tr><th>Cuadernillo</th><th>Estudiante</th><th>Llegó</th>'
            '<th class="num">Tamaño</th><th>Estado</th></tr>'
            f'{filas}</table></div>')


def _seccion_ciclo(filas):
    if not filas:
        return ('<div class="caja vacia">No hay ningún cuadernillo todavía. '
                'Aparecen aquí en cuanto los siembre el contenedor o los crees '
                'en formgrader.</div>')
    cuerpo = ""
    for f in filas:
        marca = '<span class="marca">Esta semana</span>' if f["activa"] else ""
        ventana = "sin fecha de cierre"
        if f["cierra"]:
            ventana = f'cierra {html.escape(str(f["cierra"])[:16])}'
        elif f["abre"]:
            ventana = f'abre {html.escape(str(f["abre"])[:16])}'
        puntos = f'{f["puntos"]:g}' if f["puntos"] else '<span class="tenue">—</span>'
        cuerpo += (
            f'<tr><td>{_nombre(f["tarea"])} {marca}</td>'
            f'<td>{_paso(f["generada"])}</td>'
            f'<td>{_paso(f["publicada"])}</td>'
            f'<td class="tenue">{ventana}</td>'
            f'<td class="num">{puntos}</td>'
            f'<td class="num">{f["entregas"] or "—"}</td>'
            f'<td class="num">{f["calificadas"] or "—"}</td>'
            f'<td class="sig">{html.escape(f["siguiente"])}</td></tr>')
    return ('<div class="caja"><table>'
            '<tr><th>Cuadernillo</th><th>Generada</th><th>Publicada</th>'
            '<th>Ventana</th><th class="num">Puntos</th>'
            '<th class="num">Entregas</th><th class="num">Calificadas</th>'
            '<th>Te toca</th></tr>'
            f'{cuerpo}</table></div>')


def _paso(hecho):
    return ('<span class="bien">sí</span>' if hecho
            else '<span class="tenue">no</span>')


def _html_panel(base_url):
    activo, ciclo = _ciclo()
    entregas = _entregas()
    _, notas = _libro()
    ultima = max((e["cuando"] for e in entregas), default=0)
    raiz = base_url.rstrip("/")

    cabecera = (
        f'<h1>Tu curso</h1>'
        f'<p class="sub">Curso {html.escape(CURSO)} · '
        + (f'esta semana <b>{html.escape(_titulo(activo))}</b>'
           if activo else 'sin cuadernillo activo')
        + f' · última entrega {_hace(ultima)} · '
          f'<a href="{raiz}/formgrader">ir a formgrader</a></p>')

    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tu curso</title><style>
 *{{box-sizing:border-box}}
 body{{margin:0;padding:34px 20px;background:#f7f8fa;color:{TINTA};
   font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
 .marco{{max-width:1080px;margin:0 auto}}
 h1{{font-size:27px;margin:0 0 6px}}
 h2{{font-size:19px;margin:34px 0 6px}}
 .sub{{color:{GRIS};margin:0 0 8px;font-size:15px}}
 .sub2{{color:{GRIS};font-size:14.5px;margin:0 0 14px}}
 a{{color:{AZUL};text-decoration:none;font-weight:600}}
 a:hover{{text-decoration:underline}}
 .caja{{background:#fff;border:1px solid {BORDE};border-radius:8px;
   overflow-x:auto}}
 .vacia{{padding:16px 18px;color:{GRIS}}}
 table{{width:100%;border-collapse:collapse;font-size:14.5px}}
 th{{text-align:left;font-size:12px;color:{GRIS};text-transform:uppercase;
   letter-spacing:.04em;padding:11px 14px;border-bottom:1px solid {BORDE};
   font-weight:600;white-space:nowrap}}
 td{{padding:12px 14px;border-bottom:1px solid {BORDE};vertical-align:top}}
 tr:last-child td{{border-bottom:none}}
 .num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
 .mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13.5px}}
 .tenue{{color:#8b94a1}}
 .bien{{color:{VERDE};font-weight:600}}
 .pend{{color:{AMBAR};font-weight:600}}
 .mal{{color:{ROJO};font-weight:600}}
 .sig{{color:{TINTA};font-weight:600;white-space:nowrap}}
 .marca{{background:{AZUL};color:#fff;font-size:11px;padding:2px 7px;
   border-radius:3px;margin-left:6px;white-space:nowrap}}
 .banda{{background:#fdf9ef;border-left:3px solid {AMBAR};padding:12px 16px;
   border-radius:4px;margin-bottom:14px;font-size:14.5px}}
</style></head><body><div class="marco">
{cabecera}

<h2>Lo que te ha llegado</h2>
<p class="sub2">Entregas de tus estudiantes, la más reciente primero.</p>
{_seccion_entregas(entregas, notas)}

<h2>En qué punto está cada cuadernillo</h2>
<p class="sub2">El recorrido completo es Generar → Publicar → (el alumno trabaja
y entrega) → Calificar → subir notas. La última columna dice cuál es el
siguiente paso de cada uno.</p>
{_seccion_ciclo(ciclo)}
</div></body></html>"""


class PanelDocenteHandler(_BaseHandler):
    @web.authenticated
    def get(self):
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.finish(_html_panel(self.settings.get("base_url", "/")))


def load_jupyter_server_extension(nbapp):
    if getattr(nbapp, "log", None) is not None:
        globals()["log"] = nbapp.log
    if os.environ.get("ALUMNO_ROL", "estudiante") != "instructor":
        return
    raiz = nbapp.web_app.settings.get("base_url", "/").rstrip("/")
    nbapp.web_app.add_handlers(".*$", [(raiz + "/panel-docente",
                                        PanelDocenteHandler)])
    log.info("[panel_docente_bridge] listo: panel del curso en %s/panel-docente",
             raiz)


def _load_jupyter_server_extension(server_app):
    load_jupyter_server_extension(server_app)
