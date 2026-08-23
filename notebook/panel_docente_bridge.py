"""Panel del docente: cómo va el curso, servido por su propio contenedor.

Formgrader responde a «¿qué actividades tengo?» y a nada más. El docente no
tiene forma de ver en qué punto del ciclo está cada cuadernillo —generado,
publicado, con entregas recogidas, calificado— sin recorrer carpetas.

Tres decisiones que gobiernan este archivo:

**Lee disco, y al servicio de intercambio solo para saber qué está publicado.**
Lo demás sale de lo que este contenedor ya monta: `source/`, `release/`,
`submitted/`, `autograded/` y el libro de notas. Lo agregado —cómo va el grupo
por competencia, qué ejercicio se atasca— va en su propia sección, para que un
fallo de la analítica no se lleve por delante lo que el docente necesita para
trabajar hoy. Si el intercambio no responde, la columna «publicado» se marca
como no disponible y el resto se dibuja igual.

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
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

try:
    from jupyter_server.base.handlers import JupyterHandler as _BaseHandler
except ImportError:                                   # notebook 6 clásico
    from notebook.base.handlers import IPythonHandler as _BaseHandler

log = logging.getLogger(__name__)

CURSO = os.environ.get("CURSO_ID", "curso_default")
RAIZ = os.environ.get("NBGRADER_BASE", "/srv/nbgrader") + f"/{CURSO}"

API = (os.environ.get("METRICS_API_BASE")
       or os.environ.get("STUDENT_METRICS_API_BASE")
       or "http://api_go:8080").rstrip("/")
TOKEN_MAESTRO = os.environ.get("METRICS_API_TOKEN", "")

AZUL, TINTA, GRIS, BORDE = "#2a78d6", "#10294d", "#52514e", "#dfe3e8"
VERDE, AMBAR, ROJO = "#0f8a4a", "#b57200", "#c8392b"


# --- Lecturas de disco -------------------------------------------------------

def _carpetas(ruta):
    try:
        return sorted(d.name for d in os.scandir(ruta) if d.is_dir())
    except OSError:
        return []


def _publicados():
    """Qué está liberado en el servicio de intercambio, con su ventana.

    La ventana y la marca de «activar» viajan dentro de la liberación
    (release/<tarea>/ava_publicacion.json, que escribe publicar-cuadernillo), y
    el docente tiene esa carpeta montada: se lee de ahí. Devuelve
    ({tarea: info}, pudo_consultar).
    """
    try:
        from nbexchange_cliente import ava
        liberadas, _ = ava.liberados()
    except Exception as err:
        log.warning("[panel-docente] no se pudo consultar el intercambio: %s", err)
        return {}, False
    publicados = {}
    for tarea, info in liberadas.items():
        pub = ava.leer_publicacion(os.path.join(RAIZ, "release", tarea))
        publicados[tarea] = {
            "id": tarea,
            "timestamp": info["timestamp"],
            "abre": pub.get("abre"),
            "cierra": pub.get("cierra"),
            "activar": pub.get("activar", True),
        }
    return publicados, True


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


async def _analitica():
    """Lo agregado del curso. Devuelve (datos, aviso).

    Se pide con el cliente asincrono y cuatro segundos de tope. El sincrono
    bloquearia el IOLoop del servidor del docente, que es el mismo proceso que
    corre Autograde: una consulta lenta congelaria la calificacion.

    Si no responde, el panel se dibuja igual sin estas secciones. Lo de disco
    —entregas y estado del ciclo— es lo que el docente necesita para trabajar
    hoy, y no puede depender de que la analitica este viva.
    """
    if not TOKEN_MAESTRO:
        return None, ("Esta parte no está configurada en el servidor: falta la "
                      "credencial con la que el panel consulta la analítica.")
    try:
        resp = await AsyncHTTPClient().fetch(HTTPRequest(
            f"{API}/internal/curso/{CURSO}/panel",
            headers={"Authorization": f"Bearer {TOKEN_MAESTRO}"},
            request_timeout=4, connect_timeout=2))
        return json.loads(resp.body.decode("utf-8")), None
    except Exception as err:
        log.warning("[panel-docente] no se pudo consultar la analítica: %s", err)
        return None, ("No se pudo consultar la analítica del curso. Lo de "
                      "arriba —entregas y estado de cada cuadernillo— sale del "
                      "disco y está al día.")


def _ciclo():
    """En qué punto está cada cuadernillo, juntando las cuatro fuentes."""
    publicados, consulto = _publicados()
    try:
        import entregar_cuadernillo
        activo = entregar_cuadernillo.activo_de(publicados) if consulto else ""
    except Exception:
        activo = ""
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
        # Lo que los alumnos entregaron y aún no está en submitted/: el
        # intercambio lo guarda hasta que el docente pulsa «Collect».
        sin_recoger = _sin_recoger(n, consulto) if pub else (0 if consulto else None)
        filas.append({
            "tarea": n,
            "generada": generada,
            "publicada": pub,
            "activa": n == activo,
            "abre": entrada.get("abre"),
            "cierra": entrada.get("cierra"),
            "puntos": tareas_libro.get(n),
            "entregas": ent["total"],
            "sin_recoger": sin_recoger,
            "calificadas": ent["calificadas"],
            "siguiente": _siguiente_paso(generada, pub, ent, sin_recoger),
        })
    return activo, filas


def _sin_recoger(tarea, preguntar):
    """Cuántos alumnos tienen en el intercambio una entrega más nueva que la
    que hay en submitted/ (o ninguna en submitted/). None si no se pudo saber."""
    if not preguntar:
        return None
    try:
        from nbexchange_cliente import ava
        en_exchange = ava.entregas_en_exchange(tarea)
    except Exception as err:
        log.warning("[panel-docente] no se pudo listar entregas de %s: %s", tarea, err)
        return None
    pendientes = 0
    for alumno, ts in en_exchange.items():
        carpeta = os.path.join(RAIZ, "submitted", alumno, tarea)
        try:
            with open(os.path.join(carpeta, "timestamp.txt"), encoding="utf-8") as f:
                recogida = f.read().strip()
        except OSError:
            recogida = ""
        if ts > recogida:
            pendientes += 1
    return pendientes


def _siguiente_paso(generada, publicada, ent, sin_recoger=None):
    """Qué le toca hacer al docente con este cuadernillo. Uno solo, el primero."""
    if not generada:
        return "Generar"
    if not publicada:
        return "Publicar con publicar-cuadernillo"
    if sin_recoger:
        return "Recoger con Collect en formgrader"
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
            f'<td class="num">{_pendientes(f["sin_recoger"])}</td>'
            f'<td class="num">{f["calificadas"] or "—"}</td>'
            f'<td class="sig">{html.escape(f["siguiente"])}</td></tr>')
    return ('<div class="caja"><table>'
            '<tr><th>Cuadernillo</th><th>Generada</th><th>Publicada</th>'
            '<th>Ventana</th><th class="num">Puntos</th>'
            '<th class="num">Recogidas</th><th class="num">Sin recoger</th>'
            '<th class="num">Calificadas</th>'
            '<th>Te toca</th></tr>'
            f'{cuerpo}</table></div>')


def _pendientes(n):
    if n is None:
        return '<span class="tenue" title="El servicio de intercambio no respondió">?</span>'
    return f'<span class="mal">{n}</span>' if n else "—"


def _paso(hecho):
    return ('<span class="bien">sí</span>' if hecho
            else '<span class="tenue">no</span>')



def _seccion_atascos(datos):
    ejercicios = [e for e in (datos or {}).get("ejercicios", [])
                  if e.get("alumnos_atascados")]
    if not ejercicios:
        return ('<div class="caja vacia">Nadie está atascado en ningún '
                'ejercicio ahora mismo. <span class="tenue">Atascado es quien '
                'escribió una respuesta, no le pasó la prueba, y no ha vuelto a '
                'conseguirlo — no quien solo ejecutó la celda vacía.</span></div>')
    filas = ""
    for e in ejercicios[:10]:
        filas += (
            f'<tr><td>{_nombre(e["cuadernillo_id"])}</td>'
            f'<td class="mono">{html.escape(e["exercise_id"])}</td>'
            f'<td class="num">{e["alumnos_que_lo_intentaron"]}</td>'
            f'<td class="num">{e["alumnos_que_lo_resolvieron"]}</td>'
            f'<td class="num"><b class="mal">{e["alumnos_atascados"]}</b></td>'
            f'<td class="num">{e["alumnos_a_medias"] or "—"}</td></tr>')
    return ('<div class="caja"><table>'
            '<tr><th>Cuadernillo</th><th>Ejercicio</th>'
            '<th class="num">Lo intentaron</th><th class="num">Lo resolvieron</th>'
            '<th class="num">Atascados</th><th class="num">A medias</th></tr>'
            f'{filas}</table></div>')


def _seccion_malentendidos(datos):
    lista = [m for m in (datos or {}).get("malentendidos", [])
             if m.get("alumnos", 0) >= 1]
    if not lista:
        return ('<div class="caja vacia">Todavía no hay ningún error que se '
                'repita entre varias personas.</div>')
    filas = ""
    for m in lista[:8]:
        filas += (
            f'<tr><td class="num"><b>{m["alumnos"]}</b></td>'
            f'<td>{_nombre(m["cuadernillo_id"])}</td>'
            f'<td class="mono">{html.escape(m["exercise_id"])}</td>'
            f'<td><b>{html.escape(m["error_type"])}</b>'
            f'<div class="tenue mensaje">{html.escape(m["mensaje"])}</div></td></tr>')
    return ('<div class="caja"><table>'
            '<tr><th class="num">Personas</th><th>Cuadernillo</th>'
            '<th>Ejercicio</th><th>Qué les sale</th></tr>'
            f'{filas}</table></div>')


def _seccion_competencias(datos):
    comps = (datos or {}).get("competencias", [])
    if not comps:
        return ('<div class="caja vacia">Sin datos de competencias.</div>')
    tarjetas = ""
    for c in comps:
        disenados = c.get("ejercicios_disenados", 0)
        alumnos = c.get("alumnos_con_actividad", 0)
        resolvieron = c.get("alumnos_que_resolvieron_alguno", 0)
        if not disenados:
            estado = ('<span class="tenue">Ningún ejercicio la evalúa todavía'
                      '</span>')
            barra = ""
        elif not alumnos:
            estado = f'<span class="tenue">Nadie la ha trabajado aún</span>'
            barra = ""
        else:
            pct = int(100 * resolvieron / alumnos)
            color = VERDE if pct >= 70 else (AMBAR if pct >= 40 else ROJO)
            estado = (f'<b>{resolvieron}</b> de {alumnos} '
                      f'{"estudiante" if alumnos == 1 else "estudiantes"} '
                      f'resolvió alguno')
            barra = (f'<div class="barra"><div class="relleno" '
                     f'style="width:{pct}%;background:{color}"></div></div>')
        tarjetas += (
            f'<div class="comp"><div class="comp-id">{html.escape(c["competencia_id"])}'
            f' · {disenados} ejercicio{"" if disenados == 1 else "s"}</div>'
            f'<div class="comp-e">{estado}</div>{barra}'
            f'<div class="comp-d">{html.escape(c["descripcion"])}</div></div>')
    return f'<div class="comps">{tarjetas}</div>'


def _seccion_riesgo(datos):
    lista = (datos or {}).get("en_riesgo", [])
    if not lista:
        return ('<div class="caja vacia">Nadie aparece peleando en vano. '
                '<span class="tenue">Aquí salen quienes escribieron respuestas '
                'que no les pasan; quien no ha entrado no aparece, porque de esa '
                'persona no hay nada que medir.</span></div>')
    filas = ""
    for a in lista[:8]:
        horas = a.get("horas_desde_ultima_actividad") or 0
        cuando = (f'hace {int(horas)} h' if horas < 48
                  else f'hace {int(horas / 24)} días')
        filas += (f'<tr><td class="mono">{html.escape(a["student_id"])}</td>'
                  f'<td class="num">{a["ejercicios_resueltos"]}</td>'
                  f'<td class="num"><b class="mal">{a["ejercicios_atascados"]}</b></td>'
                  f'<td class="num">{a["ejercicios_a_medias"] or "—"}</td>'
                  f'<td class="tenue">{cuando}</td></tr>')
    return ('<div class="caja"><table>'
            '<tr><th>Estudiante</th><th class="num">Resueltos</th>'
            '<th class="num">Atascados</th><th class="num">A medias</th>'
            '<th>Última vez</th></tr>'
            f'{filas}</table></div>')


def _seccion_salud(datos):
    s = (datos or {}).get("salud") or {}
    if not s:
        return ""
    sin = s.get("ejercicios_sin_competencia", 0)
    aviso = ""
    if sin:
        aviso = (f' · <span class="pend">{sin} ejercicio(s) sin competencia '
                 f'asignada</span>')
    return (f'<p class="sub2">{s.get("intentos_registrados", 0)} intentos '
            f'registrados de {s.get("alumnos_con_telemetria", 0)} '
            f'estudiante(s) · {s.get("relaciones_competencia", 0)} ejercicios '
            f'etiquetados con su competencia{aviso}</p>')


def _html_panel(base_url, datos=None, aviso=None):
    activo, ciclo = _ciclo()
    entregas = _entregas()
    _, notas = _libro()
    ultima = max((e["cuando"] for e in entregas), default=0)
    raiz = base_url.rstrip("/")

    banda_analitica = (f'<div class="banda">{html.escape(aviso)}</div>'
                       if aviso else "")

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
 .mensaje{{font-size:13px;margin-top:3px;max-width:52ch}}
 .comps{{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(270px,1fr))}}
 .comp{{background:#fff;border:1px solid {BORDE};border-radius:8px;padding:14px 16px}}
 .comp-id{{font-size:12px;color:{GRIS};text-transform:uppercase;
   letter-spacing:.04em;margin-bottom:6px}}
 .comp-e{{font-size:15px;color:{TINTA};margin-bottom:8px}}
 .comp-d{{font-size:13px;color:{GRIS};margin-top:9px;line-height:1.45}}
 .barra{{height:7px;background:#e9ecef;border-radius:4px;overflow:hidden}}
 .relleno{{height:100%;border-radius:4px}}
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

{banda_analitica}

<h2>Dónde se atasca el grupo</h2>
<p class="sub2">Ejercicios donde alguien escribió una respuesta y no le pasa la
prueba. Ejecutar la celda vacía no cuenta: eso lo hace todo el mundo al recorrer
el cuadernillo.</p>
{_seccion_atascos(datos)}

<h2>Lo que se están equivocando igual</h2>
<p class="sub2">El mismo error en varias personas. Suele ser un tema para
retomar en clase, no un problema de cada uno.</p>
{_seccion_malentendidos(datos)}

<h2>Quién está peleando solo</h2>
<p class="sub2">Estudiantes con ejercicios donde lo intentaron de verdad y no les
sale.</p>
{_seccion_riesgo(datos)}

<h2>Cómo va el grupo por competencia</h2>
{_seccion_salud(datos)}
{_seccion_competencias(datos)}
</div></body></html>"""


class PanelDocenteHandler(_BaseHandler):
    @web.authenticated
    async def get(self):
        datos, aviso = await _analitica()
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.finish(_html_panel(self.settings.get("base_url", "/"),
                                datos, aviso))


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
