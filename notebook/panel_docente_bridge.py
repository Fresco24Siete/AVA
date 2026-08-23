"""Panel del docente: quién está en el curso y cómo le va, servido por su propio contenedor.

Formgrader responde a «¿qué actividades tengo?» y a nada más. El docente no
tiene forma de ver quiénes son sus estudiantes, quién ha empezado, en qué punto
del ciclo está cada cuadernillo —generado, publicado, traído, entregado,
recogido, calificado— ni qué ejercicio cuesta, sin recorrer carpetas y bases.

Cuatro fuentes, cada una con lo suyo:

**El backend** (analítica y registro de estudiantes): quién entró y con qué
nombre —lo registra el Hub en cada ingreso LTI—, los intentos y errores de la
telemetría, y las notas subidas. Se pide con un token acotado a este curso.

**El servicio de intercambio** (nbexchange): qué está publicado, quién lo trajo
y quién lo entregó. Es el único que sabe quién ni siquiera ha abierto el
cuadernillo.

**El disco del docente**: `source/`, `release/`, `submitted/`, `autograded/` y el
libro de notas (en solo lectura: `Gradebook` escribe al abrirse y compite por
el lock con un Autograde en marcha).

Si una fuente no responde, su parte se marca como no disponible y el resto se
dibuja igual. Lo de disco es lo que el docente necesita para trabajar hoy y no
puede depender de que la analítica esté viva.

Habla el mismo idioma que el panel del alumno: «Esta semana», «a medias»,
«aún sin calificar». Si el profesor y el alumno miran cifras con nombres
distintos, la conversación en clase empieza por traducir.
"""
import html
import json
import logging
import os
import sqlite3
import time
import urllib.parse
from datetime import datetime, timezone

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
# El token de docente, acotado a este curso, que el Hub acuña al arrancar el
# contenedor. METRICS_API_TOKEN queda como respaldo para un Hub anterior.
TOKEN_DOCENTE = (os.environ.get("METRICS_DOCENTE_TOKEN")
                 or os.environ.get("METRICS_API_TOKEN", ""))

AZUL, TINTA, GRIS, BORDE = "#2a78d6", "#10294d", "#52514e", "#dfe3e8"
VERDE, AMBAR, ROJO = "#0f8a4a", "#b57200", "#c8392b"


# --- Lecturas de disco -------------------------------------------------------

def _carpetas(ruta):
    try:
        return sorted(d.name for d in os.scandir(ruta) if d.is_dir())
    except OSError:
        return []


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
            # La hora real de entrega la deja nbexchange en timestamp.txt; la
            # del archivo es la del Collect.
            entregada = _timestamp_txt(carpeta) or cuando
            salida.append({"alumno": alumno, "tarea": tarea,
                           "cuando": entregada, "recogida": cuando, "bytes": tam,
                           "calificada": _calificada(alumno, tarea, cuando)})
    salida.sort(key=lambda e: e["cuando"], reverse=True)
    return salida


def _timestamp_txt(carpeta):
    """La marca de entrega que nbexchange deja junto al notebook, en epoch."""
    try:
        with open(os.path.join(carpeta, "timestamp.txt"), encoding="utf-8") as f:
            return _epoch_exchange(f.read().strip())
    except OSError:
        return 0


def _calificada(alumno, tarea, recogida_en):
    """(bool calificada, bool reentregada_despues).

    Se compara la fecha del archivo recogido con la del calificado: si se
    volvió a recoger después de calificar, la nota ya no corresponde a lo
    último que mandó.
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
    return (True, bool(calificada_en and recogida_en > calificada_en + 2))


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
        # por el mismo id.
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


# --- El servicio de intercambio ----------------------------------------------

def _publicados():
    """Qué está liberado, con su ventana. Devuelve ({tarea: info}, pudo)."""
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


def _historial():
    """Quién trajo y quién entregó cada tarea. {} si el servicio no responde."""
    try:
        from nbexchange_cliente import ava
        return ava.historial(), True
    except Exception as err:
        log.warning("[panel-docente] no se pudo leer el historial del intercambio: %s", err)
        return {}, False


# --- El backend ----------------------------------------------------------------

async def _backend(ruta):
    """GET al backend con el token de docente. Devuelve (json, aviso)."""
    if not TOKEN_DOCENTE:
        return None, ("Esta parte no está configurada en el servidor: falta la "
                      "credencial con la que el panel consulta la analítica.")
    try:
        resp = await AsyncHTTPClient().fetch(HTTPRequest(
            f"{API}{ruta}",
            headers={"Authorization": f"Bearer {TOKEN_DOCENTE}"},
            request_timeout=4, connect_timeout=2))
        return json.loads(resp.body.decode("utf-8")), None
    except Exception as err:
        log.warning("[panel-docente] no se pudo consultar %s: %s", ruta, err)
        return None, ("No se pudo consultar la analítica del curso. Lo que sale "
                      "del disco y del intercambio está al día.")


# --- Tiempo ----------------------------------------------------------------------

def _epoch_exchange(ts):
    """'2026-08-22 21:10:00.123456 UTC' -> epoch. 0 si no se entiende."""
    try:
        base = str(ts).rsplit(" ", 1)[0]
        return datetime.strptime(base, "%Y-%m-%d %H:%M:%S.%f").replace(
            tzinfo=timezone.utc).timestamp()
    except (ValueError, AttributeError):
        return 0


def _epoch_iso(ts):
    """'2026-08-23T03:57:50.639499Z' -> epoch. 0 si no viene."""
    if not ts:
        return 0
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0


def _hace(marca):
    """Un solo formato de tiempo relativo para todo el panel."""
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
    if d < 14:
        return f"hace {d} día" + ("" if d == 1 else "s")
    return f"hace {d // 7} semanas"


def _fecha_corta(marca):
    """'23/08 16:10' en hora de Colombia."""
    if not marca:
        return "—"
    from datetime import timedelta
    return datetime.fromtimestamp(marca, timezone(timedelta(hours=-5))).strftime("%d/%m %H:%M")


# --- Cruce: el ciclo de cada cuadernillo -------------------------------------------

def _ciclo(datos, historial):
    """En qué punto está cada cuadernillo, juntando las cuatro fuentes."""
    publicados, consulto = _publicados()
    try:
        import entregar_cuadernillo
        activo = entregar_cuadernillo.activo_de(publicados) if consulto else ""
    except Exception:
        activo = ""
    tareas_libro, _ = _libro()

    recogidas = {}
    for e in _entregas():
        d = recogidas.setdefault(e["tarea"], {"total": 0, "calificadas": 0, "recogida": {}})
        d["total"] += 1
        d["recogida"][e["alumno"]] = e["cuando"]
        if e["calificada"][0]:
            d["calificadas"] += 1

    # Alumnos con telemetría por cuadernillo: los que están trabajando.
    trabajando = {c.get("cuadernillo_id"): c.get("alumnos_con_actividad", 0)
                  for c in (datos or {}).get("cuadernillos", [])}

    nombres = sorted(set(_carpetas(os.path.join(RAIZ, "source")))
                     | set(publicados) | set(tareas_libro))
    filas = []
    for n in nombres:
        generada = os.path.isdir(os.path.join(RAIZ, "release", n))
        pub = n in publicados
        ent = recogidas.get(n, {"total": 0, "calificadas": 0, "recogida": {}})
        entrada = publicados.get(n, {})
        h = historial.get(n, {"traido": {}, "entregado": {}}) if historial else None
        traido = len(h["traido"]) if h else None
        entregado = len(h["entregado"]) if h else None
        # Entregas en el servicio más nuevas que lo recogido (o sin recoger).
        sin_recoger = None
        if h:
            sin_recoger = sum(
                1 for alumno, ts in h["entregado"].items()
                if _epoch_exchange(ts) > ent["recogida"].get(alumno, 0) + 1)
        filas.append({
            "tarea": n,
            "generada": generada,
            "publicada": pub,
            "activa": n == activo,
            "abre": entrada.get("abre"),
            "cierra": entrada.get("cierra"),
            "puntos": tareas_libro.get(n),
            "trabajando": trabajando.get(n, 0),
            "traido": traido,
            "entregado": entregado,
            "recogidas": ent["total"],
            "sin_recoger": sin_recoger,
            "calificadas": ent["calificadas"],
            "siguiente": _siguiente_paso(generada, pub, ent, sin_recoger,
                                         trabajando.get(n, 0), entregado),
        })
    return activo, filas


def _siguiente_paso(generada, publicada, ent, sin_recoger, trabajando, entregado):
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
        return "Subir notas (botón «Subir notas» en formgrader, o registrar-notas)"
    if trabajando:
        return f"{trabajando} trabajando, sin entregas"
    return "Esperando que empiecen"


# --- Presentación ------------------------------------------------------------

def _titulo(codigo):
    partes = codigo.split("_")
    if len(partes) == 2 and partes[1].isdigit():
        return f"{partes[0].capitalize()} {int(partes[1])}"
    return codigo


def _nombre(codigo):
    """Título legible + el identificador real debajo."""
    bonito = _titulo(codigo)
    if bonito == codigo:
        return f'<b>{html.escape(codigo)}</b>'
    return (f'<b>{html.escape(bonito)}</b>'
            f'<div class="mono tenue">{html.escape(codigo)}</div>')


def _persona(sid, nombres, raiz, con_enlace=True):
    """Nombre del estudiante (o su id si no se conoce), enlazado a su ficha."""
    nombre = (nombres or {}).get(sid, "")
    texto = html.escape(nombre) if nombre else f'<span class="mono">{html.escape(sid)}</span>'
    if nombre:
        texto += f'<div class="mono tenue">{html.escape(sid)}</div>'
    if not con_enlace:
        return texto
    return f'<a class="persona" href="{raiz}/panel-docente/estudiante/{urllib.parse.quote(sid, safe="")}">{texto}</a>'


def _tamano(b):
    return f"{b / 1024:.0f} KB" if b < 1024 * 1024 else f"{b / 1048576:.1f} MB"


def _n(v, vacio="—"):
    return str(v) if v else f'<span class="tenue">{vacio}</span>'


def _seccion_estudiantes(datos, historial, notas, raiz):
    lista = [e for e in (datos or {}).get("estudiantes", []) if e.get("rol") != "instructor"]
    docentes = [e for e in (datos or {}).get("estudiantes", []) if e.get("rol") == "instructor"]
    if datos is None:
        return ('<div class="caja vacia">El listado sale del backend, que no '
                'respondió.</div>')
    if not lista:
        return ('<div class="caja vacia">Todavía no ha entrado ningún estudiante. '
                'Aparecen aquí en cuanto entran desde Moodle, con su nombre.</div>')

    # Entregas por alumno según el servicio: {sid: n tareas entregadas}
    entregadas = {}
    for tarea, h in (historial or {}).items():
        for sid in h.get("entregado", {}):
            entregadas[sid] = entregadas.get(sid, 0) + 1
    filas = ""
    for e in lista:
        sid = e["student_id"]
        ultimo_intento = _epoch_iso(e.get("ultimo_intento"))
        ultimo_ingreso = _epoch_iso(e.get("ultimo_ingreso"))
        ultimo = max(ultimo_intento, ultimo_ingreso)
        if e.get("ultimo_cuadernillo"):
            donde = (f'{html.escape(_titulo(e["ultimo_cuadernillo"]))} '
                     f'<span class="tenue">{_hace(ultimo_intento)}</span>')
        elif ultimo_ingreso:
            donde = '<span class="tenue">entró, aún sin intentos</span>'
        else:
            donde = '<span class="tenue">nunca ha entrado</span>'
        notas_alumno = [f"{ob:g}/{mx:g}" for (a, t), (ob, mx) in sorted(notas.items()) if a == sid]
        filas += (
            f'<tr><td>{_persona(sid, {sid: e.get("nombre", "")}, raiz)}'
            f'<div class="tenue chico">{html.escape(e.get("email", ""))}</div></td>'
            f'<td>{_hace(ultimo)}</td>'
            f'<td>{donde}</td>'
            f'<td class="num">{_n(e.get("ejercicios_resueltos"))}</td>'
            f'<td class="num">{"<b class=mal>%d</b>" % e["ejercicios_atascados"] if e.get("ejercicios_atascados") else _n(0)}</td>'
            f'<td class="num">{_n(entregadas.get(sid, 0))}</td>'
            f'<td class="num">{html.escape(" · ".join(notas_alumno)) if notas_alumno else _n(0, "aún sin nota")}</td></tr>')
    pie = ""
    if docentes:
        pie = ('<p class="sub2 chico">Docentes del curso: '
               + ", ".join(html.escape(d.get("nombre") or d["student_id"]) for d in docentes)
               + "</p>")
    return (f'<div class="caja"><table>'
            '<tr><th>Estudiante</th><th>Última vez</th><th>Va por</th>'
            '<th class="num">Resueltos</th><th class="num">Atascados</th>'
            '<th class="num">Entregas</th><th class="num">Notas</th></tr>'
            f'{filas}</table></div>{pie}')


def _seccion_entregas(entregas, notas, nombres, raiz):
    if not entregas:
        return ('<div class="caja vacia">Todavía no has recogido ninguna entrega. '
                'Las que los alumnos manden aparecen en «Sin recoger» abajo; '
                'Collect en formgrader las trae aquí.</div>')
    filas = ""
    for e in entregas:
        calificada, reentregada = e["calificada"]
        if reentregada:
            estado = '<span class="mal">Recogida de nuevo después de calificar</span>'
        elif calificada:
            nota = notas.get((e["alumno"], e["tarea"]))
            estado = (f'<span class="bien">Calificado</span> '
                      f'<span class="tenue">{nota[0]:g} / {nota[1]:g}</span>'
                      if nota else '<span class="bien">Calificado</span>')
        else:
            estado = '<span class="pend">Sin calificar</span>'
        filas += (
            f'<tr><td>{_nombre(e["tarea"])}</td>'
            f'<td>{_persona(e["alumno"], nombres, raiz)}</td>'
            f'<td>{_hace(e["cuando"])}<div class="tenue chico">{_fecha_corta(e["cuando"])}</div></td>'
            f'<td class="num">{_tamano(e["bytes"])}</td>'
            f'<td>{estado}</td></tr>')
    return ('<div class="caja"><table>'
            '<tr><th>Cuadernillo</th><th>Estudiante</th><th>Entregado</th>'
            '<th class="num">Tamaño</th><th>Estado</th></tr>'
            f'{filas}</table></div>')


def _seccion_ciclo(filas, hay_historial):
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
            f'<td>{_paso(f["publicada"])}<div class="tenue chico">{ventana}</div></td>'
            f'<td class="num">{puntos}</td>'
            f'<td class="num">{_quiza(f["traido"])}</td>'
            f'<td class="num">{_n(f["trabajando"])}</td>'
            f'<td class="num">{_quiza(f["entregado"])}</td>'
            f'<td class="num">{_pendientes(f["sin_recoger"])}</td>'
            f'<td class="num">{_n(f["recogidas"])}</td>'
            f'<td class="num">{_n(f["calificadas"])}</td>'
            f'<td class="sig">{html.escape(f["siguiente"])}</td></tr>')
    nota = ("" if hay_historial else
            '<p class="sub2 chico">El servicio de intercambio no respondió: las '
            'columnas «Lo trajeron» y «Entregaron» no están disponibles.</p>')
    return (f'<div class="caja"><table>'
            '<tr><th>Cuadernillo</th><th>Generada</th><th>Publicada</th>'
            '<th class="num">Puntos</th>'
            '<th class="num" title="Alumnos que lo recibieron en su carpeta">Lo trajeron</th>'
            '<th class="num" title="Alumnos con intentos registrados">Trabajando</th>'
            '<th class="num" title="Alumnos que pulsaron Entregar">Entregaron</th>'
            '<th class="num" title="Entregas que Collect aún no trajo">Sin recoger</th>'
            '<th class="num">Recogidas</th><th class="num">Calificadas</th>'
            '<th>Te toca</th></tr>'
            f'{cuerpo}</table></div>{nota}')


def _quiza(n):
    if n is None:
        return '<span class="tenue" title="El servicio de intercambio no respondió">?</span>'
    return _n(n)


def _pendientes(n):
    if n is None:
        return '<span class="tenue" title="El servicio de intercambio no respondió">?</span>'
    return f'<span class="mal">{n}</span>' if n else '<span class="tenue">—</span>'


def _paso(hecho):
    return ('<span class="bien">sí</span>' if hecho
            else '<span class="tenue">no</span>')


def _seccion_dificultad(datos):
    ejercicios = (datos or {}).get("ejercicios", [])
    if not ejercicios:
        return ('<div class="caja vacia">Todavía no hay intentos reales en '
                'ningún ejercicio. <span class="tenue">Ejecutar la celda vacía '
                'no cuenta: eso lo hace todo el mundo al recorrer el cuadernillo.'
                '</span></div>')
    filas = ""
    for e in ejercicios:
        intentaron = e.get("alumnos_que_lo_intentaron", 0)
        resolvieron = e.get("alumnos_que_lo_resolvieron", 0)
        primera = e.get("alumnos_que_pasaron_al_primer_intento", 0)
        mediana = e.get("mediana_intentos_hasta_pasar")
        atascados = e.get("alumnos_atascados", 0)
        pct_primera = (f'{100 * primera // resolvieron}%' if resolvieron
                       else '<span class="tenue">—</span>')
        if mediana is None:
            cuesta = '<span class="tenue">—</span>'
        elif mediana <= 1:
            cuesta = '1'
        else:
            cuesta = f'<b>{mediana:g}</b>'
        orden = f'<span class="tenue chico">celda {e["orden"]}</span>' if e.get("orden") else ""
        filas += (
            f'<tr><td>{_nombre(e["cuadernillo_id"])}</td>'
            f'<td class="mono">{html.escape(e["exercise_id"])} {orden}</td>'
            f'<td class="num">{_n(e.get("puntos_maximos"))}</td>'
            f'<td class="num">{intentaron}</td>'
            f'<td class="num">{_n(resolvieron)}</td>'
            f'<td class="num">{pct_primera}</td>'
            f'<td class="num">{cuesta}</td>'
            f'<td class="num">{"<b class=mal>%d</b>" % atascados if atascados else _n(0)}</td>'
            f'<td class="num">{_n(e.get("alumnos_a_medias", 0))}</td></tr>')
    return ('<div class="caja"><table>'
            '<tr><th>Cuadernillo</th><th>Ejercicio</th><th class="num">Puntos</th>'
            '<th class="num">Lo intentaron</th><th class="num">Lo resolvieron</th>'
            '<th class="num" title="De los que lo resolvieron, cuántos a la primera">A la primera</th>'
            '<th class="num" title="Mediana de intentos reales hasta pasar la prueba">Intentos hasta pasar</th>'
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
        return '<div class="caja vacia">Sin datos de competencias.</div>'
    con_datos, sin_datos, sin_ejercicios = [], [], []
    for c in comps:
        if not c.get("ejercicios_disenados"):
            sin_ejercicios.append(c)
        elif not c.get("alumnos_con_actividad"):
            sin_datos.append(c)
        else:
            con_datos.append(c)
    tarjetas = ""
    for c in con_datos:
        disenados = c.get("ejercicios_disenados", 0)
        alumnos = c.get("alumnos_con_actividad", 0)
        resolvieron = c.get("alumnos_que_resolvieron_alguno", 0)
        pct = int(100 * resolvieron / alumnos)
        color = VERDE if pct >= 70 else (AMBAR if pct >= 40 else ROJO)
        tarjetas += (
            f'<div class="comp"><div class="comp-id">{html.escape(c["competencia_id"])}'
            f' · {disenados} ejercicio{"" if disenados == 1 else "s"}</div>'
            f'<div class="comp-e"><b>{resolvieron}</b> de {alumnos} '
            f'{"estudiante" if alumnos == 1 else "estudiantes"} resolvió alguno</div>'
            f'<div class="barra"><div class="relleno" style="width:{pct}%;background:{color}"></div></div>'
            f'<div class="comp-d">{html.escape(c["descripcion"])}</div></div>')
    resto = ""
    if sin_datos:
        resto += ('<p class="sub2">Con ejercicios pero sin actividad todavía: '
                  + ", ".join(f'<b title="{html.escape(c["descripcion"])}">{html.escape(c["competencia_id"])}</b>'
                              f' ({c["ejercicios_disenados"]})' for c in sin_datos)
                  + '. <span class="tenue">Pasa el ratón para leer cuál es.</span></p>')
    if sin_ejercicios:
        resto += ('<p class="sub2">Sin ningún ejercicio que las evalúe: '
                  + ", ".join(f'<b title="{html.escape(c["descripcion"])}">{html.escape(c["competencia_id"])}</b>'
                              for c in sin_ejercicios) + '.</p>')
    if not tarjetas:
        return f'<div class="caja vacia">Nadie ha trabajado aún ningún ejercicio etiquetado.</div>{resto}'
    return f'<div class="comps">{tarjetas}</div>{resto}'


def _seccion_riesgo(datos, nombres, raiz):
    lista = (datos or {}).get("en_riesgo", [])
    if not lista:
        return ('<div class="caja vacia">Nadie aparece peleando en vano. '
                '<span class="tenue">Aquí salen quienes escribieron respuestas '
                'que no les pasan; quien no ha entrado no aparece, porque de esa '
                'persona no hay nada que medir.</span></div>')
    filas = ""
    for a in lista[:8]:
        horas = a.get("horas_desde_ultima_actividad") or 0
        filas += (f'<tr><td>{_persona(a["student_id"], nombres, raiz)}</td>'
                  f'<td class="num">{a["ejercicios_resueltos"]}</td>'
                  f'<td class="num"><b class="mal">{a["ejercicios_atascados"]}</b></td>'
                  f'<td class="num">{_n(a.get("ejercicios_a_medias"))}</td>'
                  f'<td class="tenue">{_hace(time.time() - horas * 3600)}</td></tr>')
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


ESTILO = f"""
 *{{box-sizing:border-box}}
 body{{margin:0;padding:34px 20px;background:#f7f8fa;color:{TINTA};
   font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
 .marco{{max-width:1120px;margin:0 auto}}
 h1{{font-size:27px;margin:0 0 6px}}
 h2{{font-size:19px;margin:34px 0 6px}}
 .sub{{color:{GRIS};margin:0 0 8px;font-size:15px}}
 .sub2{{color:{GRIS};font-size:14.5px;margin:0 0 14px}}
 .chico{{font-size:12.5px}}
 a{{color:{AZUL};text-decoration:none;font-weight:600}}
 a:hover{{text-decoration:underline}}
 a.persona{{color:{TINTA}}}
 a.persona:hover{{color:{AZUL}}}
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
 .comps{{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));margin-bottom:12px}}
 .comp{{background:#fff;border:1px solid {BORDE};border-radius:8px;padding:14px 16px}}
 .comp-id{{font-size:12px;color:{GRIS};text-transform:uppercase;
   letter-spacing:.04em;margin-bottom:6px}}
 .comp-e{{font-size:15px;color:{TINTA};margin-bottom:8px}}
 .comp-d{{font-size:13px;color:{GRIS};margin-top:9px;line-height:1.45}}
 .barra{{height:7px;background:#e9ecef;border-radius:4px;overflow:hidden}}
 .relleno{{height:100%;border-radius:4px}}
 .volver{{display:inline-block;margin-bottom:14px}}
"""


def _pagina(titulo, cuerpo):
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(titulo)}</title><style>{ESTILO}</style></head>
<body><div class="marco">{cuerpo}</div></body></html>"""


def _html_panel(base_url, datos=None, aviso=None):
    historial, hay_historial = _historial()
    activo, ciclo = _ciclo(datos, historial)
    entregas = _entregas()
    _, notas = _libro()
    nombres = (datos or {}).get("nombres") or {}
    ultima = max((e["cuando"] for e in entregas), default=0)
    raiz = base_url.rstrip("/")
    n_est = len([e for e in (datos or {}).get("estudiantes", []) if e.get("rol") != "instructor"])

    banda_analitica = (f'<div class="banda">{html.escape(aviso)}</div>'
                       if aviso else "")
    cabecera = (
        f'<h1>Tu curso</h1>'
        f'<p class="sub">Curso {html.escape(CURSO)} · '
        + (f'esta semana <b>{html.escape(_titulo(activo))}</b>'
           if activo else 'sin cuadernillo activo')
        + (f' · {n_est} estudiante{"" if n_est == 1 else "s"}' if datos else '')
        + f' · última entrega {_hace(ultima)} · '
          f'<a href="{raiz}/formgrader">ir a formgrader</a></p>')

    cuerpo = f"""
{cabecera}
{banda_analitica}

<h2>Tus estudiantes</h2>
<p class="sub2">Quien ha entrado desde Moodle, con su nombre. Haz clic en uno para
ver su recorrido ejercicio por ejercicio.</p>
{_seccion_estudiantes(datos, historial, notas, raiz)}

<h2>En qué punto está cada cuadernillo</h2>
<p class="sub2">Generar → Publicar → los alumnos lo traen, trabajan y entregan →
Recoger → Calificar → subir notas. La última columna dice cuál es el siguiente
paso de cada uno.</p>
{_seccion_ciclo(ciclo, hay_historial)}

<h2>Lo que has recogido</h2>
<p class="sub2">Entregas que Collect ya trajo a tu carpeta, la más reciente primero.</p>
{_seccion_entregas(entregas, notas, nombres, raiz)}

<h2>Qué cuesta y dónde se atascan</h2>
<p class="sub2">Por ejercicio: cuántos lo pasaron a la primera y cuántos intentos
reales les costó a los que lo resolvieron. «Atascado» es quien escribió una
respuesta, no le pasa la prueba y no ha vuelto a conseguirlo. Ejecutar la celda
vacía no cuenta.</p>
{_seccion_dificultad(datos)}

<h2>Lo que se están equivocando igual</h2>
<p class="sub2">El mismo error en varias personas. Suele ser un tema para
retomar en clase, no un problema de cada uno.</p>
{_seccion_malentendidos(datos)}

<h2>Quién está peleando solo</h2>
<p class="sub2">Estudiantes con ejercicios donde lo intentaron de verdad y no les
sale.</p>
{_seccion_riesgo(datos, nombres, raiz)}

<h2>Cómo va el grupo por competencia</h2>
{_seccion_salud(datos)}
{_seccion_competencias(datos)}
"""
    return _pagina("Tu curso", cuerpo)


# --- Ficha de un estudiante --------------------------------------------------------

def _html_ficha(base_url, sid, datos_panel, ficha, historial, aviso):
    raiz = base_url.rstrip("/")
    persona = next((e for e in (datos_panel or {}).get("estudiantes", [])
                    if e.get("student_id") == sid), {})
    nombre = persona.get("nombre") or sid
    _, notas = _libro()
    banda = f'<div class="banda">{html.escape(aviso)}</div>' if aviso else ""

    datos_persona = (
        f'<p class="sub">{html.escape(persona.get("email", "")) or "sin correo"} · '
        f'id <span class="mono">{html.escape(sid)}</span> · '
        f'último ingreso {_hace(_epoch_iso(persona.get("ultimo_ingreso")))}'
        f' ({persona.get("ingresos", 0)} en total)'
        + (' · <span class="bien">devolución de nota a Moodle posible</span>'
           if persona.get("devolucion_moodle_posible") else
           ' · <span class="tenue">Moodle no mandó casilla de nota</span>') + '</p>')

    # Por cuadernillo: traído / entregado / nota
    filas_c = ""
    for tarea, h in sorted((historial or {}).items()):
        traido = h.get("traido", {}).get(sid, "")
        entregado = h.get("entregado", {}).get(sid, "")
        nota = notas.get((sid, tarea))
        filas_c += (f'<tr><td>{_nombre(tarea)}</td>'
                    f'<td>{_hace(_epoch_exchange(traido)) if traido else "<span class=tenue>no lo ha traído</span>"}</td>'
                    f'<td>{_hace(_epoch_exchange(entregado)) if entregado else "<span class=tenue>sin entregar</span>"}</td>'
                    f'<td class="num">{f"{nota[0]:g} / {nota[1]:g}" if nota else "<span class=tenue>aún sin nota</span>"}</td></tr>')
    cuadernillos = (f'<div class="caja"><table><tr><th>Cuadernillo</th><th>Lo trajo</th>'
                    f'<th>Entregó</th><th class="num">Nota</th></tr>{filas_c}</table></div>'
                    if filas_c else '<div class="caja vacia">Sin cuadernillos publicados.</div>')

    ejercicios = (ficha or {}).get("ejercicios", [])
    filas_e = ""
    for e in ejercicios:
        if e.get("resuelto"):
            estado = '<span class="bien">resuelto</span>'
        elif e.get("solo_ejecuto_vacio"):
            estado = '<span class="tenue">solo ejecutó la celda vacía</span>'
        elif e.get("a_medias"):
            estado = '<span class="pend">a medias</span>'
        else:
            estado = '<span class="mal">atascado</span>'
        err = ""
        if e.get("ultimo_error") and not e.get("resuelto"):
            err = (f'<b>{html.escape(e["ultimo_error"])}</b>'
                   f'<div class="tenue mensaje">{html.escape(e.get("ultimo_mensaje", ""))}</div>')
        filas_e += (
            f'<tr><td>{_nombre(e["cuadernillo_id"])}</td>'
            f'<td class="mono">{html.escape(e["exercise_id"])}</td>'
            f'<td>{estado}</td>'
            f'<td class="num">{_n(e.get("intentos"))}</td>'
            f'<td>{_hace(_epoch_iso(e.get("ultimo_intento")))}</td>'
            f'<td>{err}</td></tr>')
    recorrido = (f'<div class="caja"><table><tr><th>Cuadernillo</th><th>Ejercicio</th>'
                 f'<th>Estado</th><th class="num">Intentos</th><th>Última vez</th>'
                 f'<th>Último error</th></tr>{filas_e}</table></div>'
                 if filas_e else
                 '<div class="caja vacia">Todavía no ha ejecutado ninguna celda de prueba.</div>')

    cuerpo = f"""
<a class="volver" href="{raiz}/panel-docente">← Tu curso</a>
<h1>{html.escape(nombre)}</h1>
{datos_persona}
{banda}
<h2>Sus cuadernillos</h2>
{cuadernillos}
<h2>Su recorrido, ejercicio por ejercicio</h2>
<p class="sub2">Un intento es cada vez que ejecutó una celda de prueba con algo
escrito. Los errores son los de su último intento fallido.</p>
{recorrido}
"""
    return _pagina(nombre, cuerpo)


class PanelDocenteHandler(_BaseHandler):
    @web.authenticated
    async def get(self):
        datos, aviso = await _backend(f"/internal/curso/{urllib.parse.quote(CURSO, safe='')}/panel")
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.finish(_html_panel(self.settings.get("base_url", "/"), datos, aviso))


class FichaHandler(_BaseHandler):
    @web.authenticated
    async def get(self, sid):
        sid = urllib.parse.unquote(sid)
        curso = urllib.parse.quote(CURSO, safe="")
        datos, aviso = await _backend(f"/internal/curso/{curso}/panel")
        ficha, aviso2 = await _backend(
            f"/internal/curso/{curso}/estudiante/{urllib.parse.quote(sid, safe='')}")
        historial, _ = _historial()
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.finish(_html_ficha(self.settings.get("base_url", "/"), sid, datos, ficha,
                                historial, aviso or aviso2))


def load_jupyter_server_extension(nbapp):
    if getattr(nbapp, "log", None) is not None:
        globals()["log"] = nbapp.log
    if os.environ.get("ALUMNO_ROL", "estudiante") != "instructor":
        return
    raiz = nbapp.web_app.settings.get("base_url", "/").rstrip("/")
    nbapp.web_app.add_handlers(".*$", [
        (raiz + "/panel-docente", PanelDocenteHandler),
        (raiz + "/panel-docente/estudiante/([^/]+)", FichaHandler),
    ])
    log.info("[panel_docente_bridge] listo: panel del curso en %s/panel-docente",
             raiz)


def _load_jupyter_server_extension(server_app):
    load_jupyter_server_extension(server_app)
