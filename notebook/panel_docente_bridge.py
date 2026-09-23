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
import re
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
        # La nota de una celda es la manual si el docente la puso (más el
        # extra); si no, la automática. Sumar solo auto_score mostraba 80/80
        # donde formgrader y el backend decían 79/80.
        for alumno, tarea, obtenidos in con.execute("""
                SELECT s.id, a.name,
                       COALESCE(SUM(COALESCE(g.manual_score, g.auto_score, 0)
                                    + COALESCE(g.extra_credit, 0)), 0)
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


async def _backend_post(ruta, cuerpo):
    """POST al backend con el token de docente. Devuelve (json, aviso)."""
    if not TOKEN_DOCENTE:
        return None, ("Esta parte no está configurada en el servidor: falta la "
                      "credencial con la que el panel habla con la analítica.")
    try:
        resp = await AsyncHTTPClient().fetch(HTTPRequest(
            f"{API}{ruta}", method="POST",
            body=json.dumps(cuerpo).encode("utf-8"),
            headers={"Authorization": f"Bearer {TOKEN_DOCENTE}",
                     "Content-Type": "application/json"},
            # Más holgado que los 4 s de la lectura: congelar un corte recorre a
            # todo el grupo, una consulta por persona. Con 16 alumnos sobra.
            request_timeout=30, connect_timeout=2))
        return json.loads(resp.body.decode("utf-8")), None
    except Exception as err:
        log.warning("[panel-docente] no se pudo enviar a %s: %s", ruta, err)
        return None, "No se pudo guardar. Inténtalo de nuevo en un momento."


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

    # Alumnos con telemetría por cuadernillo: los que están trabajando. Y
    # cuántas notas de ese cuadernillo ya están en el backend.
    trabajando = {c.get("cuadernillo_id"): c.get("alumnos_con_actividad", 0)
                  for c in (datos or {}).get("cuadernillos", [])}
    notas_subidas = {c.get("cuadernillo_id"): c.get("notas_subidas", 0)
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
                                         trabajando.get(n, 0), entregado,
                                         notas_subidas.get(n, 0) if datos else None),
        })
    return activo, filas


def _siguiente_paso(generada, publicada, ent, sin_recoger, trabajando, entregado,
                    notas_subidas=None):
    """Qué le toca hacer al docente con este cuadernillo. Uno solo, el primero.

    notas_subidas: cuántas notas de este cuadernillo tiene ya el backend, o
    None si el backend no respondió (entonces no se afirma nada sobre ellas).
    """
    if not generada:
        return "Generar"
    if not publicada:
        return "Publicar (Release en formgrader o publicar-cuadernillo)"
    if sin_recoger:
        return "Recoger con Collect en formgrader"
    if ent["total"] and ent["calificadas"] < ent["total"]:
        return "Calificar (Autograde en formgrader; sube la nota solo)"
    if ent["total"] and ent["calificadas"] == ent["total"]:
        if notas_subidas is None:
            return "Calificado; el backend no respondió para saber si la nota subió"
        if notas_subidas < ent["calificadas"]:
            return (f"Subir notas: {ent['calificadas'] - notas_subidas} sin subir "
                    "(botón «Subir notas» en formgrader)")
        return "Al día: calificado y con las notas en el panel del alumno"
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


# --- Competencias: código, nivel y chips -------------------------------------
#
# Por dentro la competencia es I1…I7 (clave primaria, mapeo, corte). Por fuera
# el docente conoce el código del microcurrículo (mCP17, mCC87, mCC103), que el
# backend manda como `codigo`. Aquí el oficial es la etiqueta y el I-código
# queda como secundario, para que las dos cosas sigan siendo la misma.

# Un color por nivel, el mismo en todas las pestañas, en la ficha y en el JS
# del despliegue: N3 verde (lo saca con soltura), N2 ámbar (lo saca pero le
# cuesta), N1 rojo (no le sale), sin evidencia gris (todavía no se sabe).
NIVEL_CLASE = {3: "n3", 2: "n2", 1: "n1"}
NIVEL_COLOR = {3: "var(--success)", 2: "var(--warning)", 1: "var(--danger)",
               None: "#cbd5e1"}
NIVEL_TEXTO = {3: "N3 · lo resuelve con soltura", 2: "N2 · lo resuelve, pero le cuesta",
               1: "N1 · no le sale todavía", None: "sin evidencia suficiente"}


def _codigo(c):
    """El código oficial (mCP17…), o el interno si el backend aún no lo manda."""
    return c.get("codigo") or c.get("competencia_id", "")


def _etiqueta_comp(c, interno=True):
    """«mCP17» en grande y «I1» al lado en pequeño, salvo que coincidan."""
    oficial, cod = _codigo(c), c.get("competencia_id", "")
    texto = f'<b>{html.escape(oficial)}</b>'
    if interno and cod and cod != oficial:
        texto += f' <span class="mono tenue chico">{html.escape(cod)}</span>'
    return texto


def _competencias_en_alcance(datos):
    """Las competencias que el panel mide, en el orden del catálogo."""
    comps = list((datos or {}).get("competencias") or [])
    if comps:
        return comps
    # Sin la sección del curso, se deducen del resumen por estudiante.
    vistas = {}
    for fila in (datos or {}).get("competencias_por_estudiante") or []:
        vistas.setdefault(fila.get("competencia_id", ""), fila)
    return [vistas[k] for k in sorted(vistas)]


def _niveles_por_estudiante(datos):
    """{student_id: {competencia_id: fila}} a partir del resumen del curso."""
    salida = {}
    for fila in (datos or {}).get("competencias_por_estudiante") or []:
        salida.setdefault(fila.get("student_id", ""), {})[fila.get("competencia_id", "")] = fila
    return salida


def _chip_nivel(comp, fila):
    """Una chip por competencia: código oficial + N1/N2/N3 + resueltos/vistos.

    Es lo que Bryan pidió ver sin clics: «solo se quería saber el avance por
    estudiante». Si no hay nivel, un guion con el motivo en el tooltip, que no
    es lo mismo que N1 y no puede parecerlo.
    """
    oficial = _codigo(comp)
    interno = comp.get("competencia_id", "")
    if not fila:
        titulo = f"{interno} · sin intentos reales todavía"
        return (f'<span class="chip-comp chip-sin" title="{html.escape(titulo)}">'
                f'<span class="chip-cod">{html.escape(oficial)}</span>'
                f'<span class="chip-niv">—</span></span>')
    nivel = fila.get("nivel")
    vistos = fila.get("ejercicios_vistos", 0)
    resueltos = fila.get("ejercicios_resueltos", 0)
    motivo = fila.get("motivo_nivel") or NIVEL_TEXTO[None]
    titulo = f"{interno} · {NIVEL_TEXTO.get(nivel, NIVEL_TEXTO[None])} · {motivo}"
    clase = NIVEL_CLASE.get(nivel, "sin")
    niv = f"N{nivel}" if nivel else "—"
    cuenta = f'<span class="chip-rv">{resueltos}/{vistos}</span>' if vistos else ""
    return (f'<span class="chip-comp chip-{clase}" title="{html.escape(titulo)}">'
            f'<span class="chip-cod">{html.escape(oficial)}</span>'
            f'<span class="chip-niv">{niv}</span>{cuenta}</span>')


def _leyenda_niveles():
    return ('<div class="leyenda">'
            '<span><i class="cuadro" style="background:var(--success)"></i>N3 lo resuelve con soltura</span>'
            '<span><i class="cuadro" style="background:var(--warning)"></i>N2 lo resuelve, pero le cuesta</span>'
            '<span><i class="cuadro" style="background:var(--danger)"></i>N1 no le sale todavía</span>'
            '<span><i class="cuadro" style="background:#cbd5e1"></i>sin evidencia (menos de 3 ejercicios intentados)</span>'
            '</div>')


# --- Gráficos: SVG generado aquí, sin librerías --------------------------------
#
# El panel corre dentro de JupyterHub, sin CDN y con lo que haya en el
# contenedor. Un SVG inline con rectángulos y líneas es suficiente para lo
# que se quiere ver de un vistazo, y no depende de nada.

def _svg_texto(x, y, texto, **at):
    extra = "".join(f' {k.replace("_", "-")}="{html.escape(str(v))}"' for k, v in at.items())
    return f'<text x="{x:g}" y="{y:g}"{extra}>{html.escape(str(texto))}</text>'


def _grafico_niveles(datos, estudiantes):
    """Barra apilada por competencia: cuántos están en N3, N2, N1 o sin evidencia.

    El ancho completo es el grupo entero, para que el hueco gris se lea como lo
    que es: gente de la que todavía no se sabe. Quien no tiene fila en el
    resumen (no ha intentado nada real) cuenta como sin evidencia.
    """
    comps = _competencias_en_alcance(datos)
    por_est = _niveles_por_estudiante(datos)
    ids = [e.get("student_id") for e in estudiantes]
    if not comps or not ids:
        return ""
    total = len(ids)
    ancho, x0, x1, alto_fila, arriba = 680, 118, 556, 34, 10
    alto = arriba + alto_fila * len(comps) + 6
    partes = [f'<svg viewBox="0 0 {ancho} {alto}" class="grafico" role="img" '
              f'aria-label="Distribución de niveles por competencia">']
    for i, comp in enumerate(comps):
        cid = comp.get("competencia_id", "")
        cuenta = {3: 0, 2: 0, 1: 0, None: 0}
        for sid in ids:
            fila = por_est.get(sid, {}).get(cid)
            nivel = fila.get("nivel") if fila else None
            cuenta[nivel if nivel in (1, 2, 3) else None] += 1
        y = arriba + i * alto_fila
        partes.append(_svg_texto(0, y + 20, _codigo(comp), font_size=13, font_weight=700,
                                 fill="var(--text-main)"))
        partes.append(_svg_texto(0, y + 32, cid, font_size=10, fill="var(--text-subtle)"))
        x = x0
        for nivel in (3, 2, 1, None):
            n = cuenta[nivel]
            if not n:
                continue
            w = (x1 - x0) * n / total
            titulo = f"{_codigo(comp)}: {n} de {total} · {NIVEL_TEXTO[nivel]}"
            partes.append(f'<rect x="{x:.1f}" y="{y + 6}" width="{w:.1f}" height="22" '
                          f'fill="{NIVEL_COLOR[nivel]}" rx="3"><title>{html.escape(titulo)}</title></rect>')
            if w >= 26:
                etiqueta = f"{n}" if nivel is None else f"N{nivel} · {n}"
                if w < 54:
                    etiqueta = str(n)
                partes.append(_svg_texto(x + w / 2, y + 21, etiqueta, font_size=11.5,
                                         font_weight=600, text_anchor="middle",
                                         fill="#fff" if nivel else "var(--text-muted)"))
            x += w
        con_nivel = cuenta[3] + cuenta[2] + cuenta[1]
        partes.append(_svg_texto(x1 + 8, y + 21, f"{con_nivel}/{total} con nivel", font_size=11,
                                 fill="var(--text-muted)", text_anchor="start"))
    partes.append("</svg>")
    return ('<div class="caja grafico-caja">'
            '<div class="grafico-titulo">Cuántos estudiantes hay en cada nivel</div>'
            f'{_leyenda_niveles()}{"".join(partes)}'
            '<p class="sub2 chico" style="margin:8px 0 0">Cada barra es el grupo entero '
            f'({total} estudiantes). A la derecha, cuántos tienen ya un nivel medido.</p></div>')


def _grafico_dificultad(items):
    """Barras horizontales por ejercicio: cuántos lo resolvieron y cuántos se
    quedaron atascados, sobre cuántos lo intentaron de verdad.

    Resolvieron + atascados = lo intentaron (quien escribió algo y pasó, o no
    pasó y no volvió a pasar). Ejecutar la celda vacía no está aquí.
    """
    items = [e for e in items if e.get("alumnos_que_lo_intentaron", 0) > 0]
    if not items:
        return ""
    mayor = max(e.get("alumnos_que_lo_intentaron", 0) for e in items) or 1
    ancho, x0, x1, alto_fila, arriba = 680, 200, 540, 26, 6
    alto = arriba + alto_fila * len(items) + 4
    partes = [f'<svg viewBox="0 0 {ancho} {alto}" class="grafico" role="img" '
              f'aria-label="Resueltos y atascados por ejercicio">']
    for i, e in enumerate(items):
        intentaron = e.get("alumnos_que_lo_intentaron", 0)
        resolvieron = e.get("alumnos_que_lo_resolvieron", 0)
        atascados = e.get("alumnos_atascados", 0)
        y = arriba + i * alto_fila
        nombre = e.get("exercise_id", "")
        if e.get("orden"):
            nombre += f'  (celda {e["orden"]})'
        partes.append(_svg_texto(x0 - 8, y + 17, nombre, font_size=12, text_anchor="end",
                                 fill="var(--text-main)", font_family="ui-monospace, Menlo, monospace"))
        largo = (x1 - x0) * intentaron / mayor
        w_ok = largo * resolvieron / intentaron if intentaron else 0
        w_mal = largo - w_ok
        if w_ok > 0:
            partes.append(f'<rect x="{x0}" y="{y + 5}" width="{w_ok:.1f}" height="16" rx="3" '
                          f'fill="var(--success)"><title>{html.escape(nombre)}: {resolvieron} lo resolvieron</title></rect>')
        if w_mal > 0:
            partes.append(f'<rect x="{x0 + w_ok:.1f}" y="{y + 5}" width="{w_mal:.1f}" height="16" rx="3" '
                          f'fill="var(--danger)"><title>{html.escape(nombre)}: {atascados} atascados</title></rect>')
        texto = f"{resolvieron} de {intentaron}"
        if atascados:
            texto += f" · {atascados} atascado{'' if atascados == 1 else 's'}"
        partes.append(_svg_texto(x0 + largo + 8, y + 17, texto, font_size="11.5",
                                 fill="var(--danger)" if atascados else "var(--text-muted)"))
    partes.append("</svg>")
    return ('<div class="grafico-caja grafico-en-grupo">'
            '<div class="leyenda">'
            '<span><i class="cuadro" style="background:var(--success)"></i>lo resolvieron</span>'
            '<span><i class="cuadro" style="background:var(--danger)"></i>atascados (escribieron algo y no les pasa)</span>'
            '<span class="tenue">· el largo de la barra es cuántos lo intentaron</span></div>'
            + "".join(partes) + "</div>")


def _grafico_actividad(datos):
    """Línea de intentos reales por día. Dice si el grupo trabaja repartido en
    la semana o todo la víspera de la entrega."""
    dias = [d for d in (datos or {}).get("actividad_por_dia") or [] if d.get("dia")]
    if len(dias) < 2:
        return ""
    from datetime import date, timedelta
    try:
        inicio = date.fromisoformat(dias[0]["dia"])
        fin = date.fromisoformat(dias[-1]["dia"])
    except ValueError:
        return ""
    por_dia = {d["dia"]: d for d in dias}
    serie = []
    d = inicio
    while d <= fin and len(serie) < 400:
        fila = por_dia.get(d.isoformat(), {})
        serie.append((d, fila.get("intentos_reales", 0), fila.get("alumnos", 0)))
        d += timedelta(days=1)
    ancho, alto = 680, 190
    izq, der, arriba, abajo = 40, 14, 14, 30
    mayor = max(v for _, v, _ in serie) or 1
    # Un techo redondo para el eje: 140 -> 150, 23 -> 25.
    paso = 10 ** max(0, len(str(mayor)) - 1)
    techo = ((mayor + paso - 1) // paso) * paso or 1
    w = ancho - izq - der
    h = alto - arriba - abajo

    def px(i):
        return izq + (w * i / max(1, len(serie) - 1))

    def py(v):
        return arriba + h - h * v / techo

    partes = [f'<svg viewBox="0 0 {ancho} {alto}" class="grafico" role="img" '
              f'aria-label="Intentos reales por día">']
    for k in range(0, 5):
        v = techo * k / 4
        y = py(v)
        partes.append(f'<line x1="{izq}" y1="{y:.1f}" x2="{ancho - der}" y2="{y:.1f}" '
                      f'stroke="var(--border)" stroke-width="1"/>')
        partes.append(_svg_texto(izq - 6, y + 4, f"{v:g}", font_size=10.5, text_anchor="end",
                                 fill="var(--text-subtle)"))
    puntos = [(px(i), py(v)) for i, (_, v, _) in enumerate(serie)]
    linea = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
    partes.append(f'<polygon points="{izq},{py(0):.1f} {linea} {puntos[-1][0]:.1f},{py(0):.1f}" '
                  f'fill="var(--primary)" opacity="0.12"/>')
    partes.append(f'<polyline points="{linea}" fill="none" stroke="var(--primary)" '
                  f'stroke-width="2" stroke-linejoin="round"/>')
    cada = max(1, (len(serie) + 7) // 8)
    for i, (dia, v, alumnos) in enumerate(serie):
        x, y = puntos[i]
        if v:
            partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="var(--primary)">'
                          f'<title>{dia.strftime("%d/%m")}: {v} intentos reales de {alumnos} '
                          f'estudiante{"" if alumnos == 1 else "s"}</title></circle>')
        if i % cada == 0 or i == len(serie) - 1:
            partes.append(_svg_texto(x, alto - 10, dia.strftime("%d/%m"), font_size=10.5,
                                     text_anchor="middle", fill="var(--text-subtle)"))
    partes.append("</svg>")
    total = sum(v for _, v, _ in serie)
    pico = max(serie, key=lambda t: t[1])
    return ('<div class="caja grafico-caja">'
            '<div class="grafico-titulo">Intentos reales por día</div>'
            + "".join(partes) +
            f'<p class="sub2 chico" style="margin:8px 0 0">{total} intentos reales entre el '
            f'{inicio.strftime("%d/%m")} y el {fin.strftime("%d/%m")}. El día de más trabajo fue el '
            f'{pico[0].strftime("%d/%m")} ({pico[1]} intentos de {pico[2]} '
            f'estudiante{"" if pico[2] == 1 else "s"}). Pasa el ratón por un punto para ver el día.</p></div>')


def _iniciales(nombre, sid):
    texto = (nombre or sid or "").strip()
    partes = texto.split()
    if len(partes) >= 2:
        return (partes[0][0] + partes[1][0]).upper()
    elif partes and len(partes[0]) >= 2:
        return partes[0][:2].upper()
    return "??"


def _avatar_color(sid):
    paleta = [
        ("#eff6ff", "#1d4ed8"),  # Azul
        ("#fdf2f8", "#be185d"),  # Rosa
        ("#eef2ff", "#4338ca"),  # Índigo
        ("#f0fdf4", "#15803d"),  # Verde
        ("#fffbeb", "#b45309"),  # Ámbar
        ("#faf5ff", "#7e22ce"),  # Morado
        ("#f0fdfa", "#0f766e"),  # Teal
    ]
    idx = sum(ord(c) for c in (sid or "x")) % len(paleta)
    return paleta[idx]


def _seccion_estudiantes(datos, historial, notas, raiz):
    lista = [e for e in (datos or {}).get("estudiantes", []) if e.get("rol") != "instructor"]
    docentes = [e for e in (datos or {}).get("estudiantes", []) if e.get("rol") == "instructor"]
    if datos is None:
        return ('<div class="caja vacia">El listado sale del backend, que no '
                'respondió.</div>')
    if not lista:
        return ('<div class="caja vacia">Todavía no ha entrado ningún estudiante. '
                'Aparecen aquí en cuanto entran desde Moodle, con su nombre.</div>')

    entregadas = {}
    for tarea, h in (historial or {}).items():
        for sid in h.get("entregado", {}):
            entregadas[sid] = entregadas.get(sid, 0) + 1

    # El nivel por competencia de cada persona viene en el mismo payload
    # (competencias_por_estudiante): una consulta para todo el grupo, no una
    # petición por fila.
    comps_alcance = _competencias_en_alcance(datos)
    niveles = _niveles_por_estudiante(datos)
    hay_niveles = "competencias_por_estudiante" in (datos or {})
    # Con el backend viejo (sin la clave) todas las filas llevan data-nivel=0 y el
    # filtro «Aún sin nivel» enseñaría a todo el mundo: no se emite en ese caso.
    boton_sin_nivel = (
        '<button type="button" class="f-pill" data-filtro="sin_nivel" '
        'onclick="setFiltroEstudiantes(\'sin_nivel\', this)">◌ Aún sin nivel</button>'
    ) if hay_niveles else ""

    filas = ""
    for e in lista:
        sid = e["student_id"]
        safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", sid)
        nombre = e.get("nombre") or sid
        email = e.get("email") or ""
        ultimo_intento = _epoch_iso(e.get("ultimo_intento"))
        ultimo_ingreso = _epoch_iso(e.get("ultimo_ingreso"))
        ultimo = max(ultimo_intento, ultimo_ingreso)

        if e.get("ultimo_cuadernillo"):
            donde = (f'<span class="badge-cuad">{html.escape(_titulo(e["ultimo_cuadernillo"]))}</span> '
                     f'<span class="tenue chico">{_hace(ultimo_intento)}</span>')
        elif ultimo_ingreso:
            donde = '<span class="tenue chico">entró, aún sin intentos</span>'
        else:
            donde = '<span class="tenue chico">nunca ha entrado</span>'

        atascados = e.get("ejercicios_atascados", 0)
        badge_atascados = (f'<span class="pill pill-danger"><b>{atascados}</b> atascados</span>'
                           if atascados else '<span class="tenue">—</span>')

        bg_col, text_col = _avatar_color(sid)
        inics = _iniciales(nombre, sid)
        avatar = (f'<div class="avatar" style="background:{bg_col};color:{text_col}">'
                  f'{html.escape(inics)}</div>')

        notas_alumno = [f"{ob:g}/{mx:g}" for (a, t), (ob, mx) in sorted(notas.items()) if a == sid]
        chips_notas = (f'<span class="badge-nota">{html.escape(" · ".join(notas_alumno))}</span>'
                       if notas_alumno else '<span class="tenue chico">sin notas</span>')

        n_entregas = entregadas.get(sid, 0)
        entregas_badge = (f'<span class="badge-entregas">{n_entregas} entr.</span>'
                          if n_entregas else '<span class="tenue chico">0 entr.</span>')

        resueltos_val = e.get("ejercicios_resueltos", 0)

        if not hay_niveles:
            chips = '<span class="tenue chico" title="El backend no devolvió el resumen por estudiante">no disponible</span>'
        elif comps_alcance:
            chips = "".join(_chip_nivel(c, niveles.get(sid, {}).get(c.get("competencia_id", "")))
                            for c in comps_alcance)
        else:
            chips = '<span class="tenue chico">—</span>'
        mejor_nivel = max((f.get("nivel") or 0 for f in niveles.get(sid, {}).values()), default=0)

        filas += f"""
        <tr class="fila-estudiante" id="fila-{safe_id}"
            data-sid="{html.escape(sid)}"
            data-safeid="{safe_id}"
            data-nombre="{html.escape(nombre.lower())}"
            data-email="{html.escape(email.lower())}"
            data-atascados="{atascados}"
            data-entregas="{n_entregas}"
            data-ingreso="{1 if ultimo else 0}"
            data-nivel="{mejor_nivel}"
            onclick="toggleFilaEstudiante('{html.escape(sid)}', '{safe_id}', '{html.escape(nombre)}', event)">
          <td>
            <div class="estudiante-meta">
              {avatar}
              <div>
                <div class="estudiante-nombre">{html.escape(nombre)}</div>
                <div class="estudiante-sub">{html.escape(email or sid)}</div>
              </div>
            </div>
          </td>
          <td><div class="tiempo-rel">{_hace(ultimo)}</div></td>
          <td>{donde}</td>
          <td class="celda-chips">{chips}</td>
          <td class="num"><span class="badge-resueltos"><b>{resueltos_val}</b> ej.</span></td>
          <td class="num">{badge_atascados}</td>
          <td class="num">{entregas_badge} {chips_notas}</td>
          <td class="col-accion">
            <button type="button" class="btn-desplegar" id="btn-toggle-{safe_id}"
              onclick="toggleFilaEstudiante('{html.escape(sid)}', '{safe_id}', '{html.escape(nombre)}', event)">
              <span>Ver detalle</span> <span class="arrow" id="arrow-{safe_id}">▾</span>
            </button>
          </td>
        </tr>
        <tr class="fila-detalle" id="det-row-{safe_id}" style="display:none">
          <td colspan="8" class="celda-detalle" id="det-box-{safe_id}">
          </td>
        </tr>"""

    pie = ""
    if docentes:
        pie = ('<div class="docentes-lista"><span class="docentes-label">Docentes del curso:</span> '
               + ", ".join(html.escape(d.get("nombre") or d["student_id"]) for d in docentes)
               + "</div>")

    barra_herramientas = f"""
    <div class="toolbar-estudiantes">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="filtro-busqueda-est" placeholder="Buscar por nombre, correo o ID..." oninput="filtrarEstudiantes()">
      </div>
      <div class="filter-pills" id="filtro-pills-est">
        <button type="button" class="f-pill active" data-filtro="todos" onclick="setFiltroEstudiantes('todos', this)">Todos ({len(lista)})</button>
        <button type="button" class="f-pill" data-filtro="atascados" onclick="setFiltroEstudiantes('atascados', this)">⚠️ Con atascados ({sum(1 for e in lista if e.get("ejercicios_atascados", 0) > 0)})</button>
        <button type="button" class="f-pill" data-filtro="al_dia" onclick="setFiltroEstudiantes('al_dia', this)">✅ Al día</button>
        <button type="button" class="f-pill" data-filtro="sin_actividad" onclick="setFiltroEstudiantes('sin_actividad', this)">⏳ Sin actividad</button>
{boton_sin_nivel}
      </div>
    </div>
    """
    leyenda = _leyenda_niveles() if hay_niveles and comps_alcance else ""

    return f"""
    <div class="caja table-container">
      {barra_herramientas}
      {leyenda}
      <div class="table-responsive">
        <table class="tabla-minimalista" id="tabla-estudiantes">
          <thead>
            <tr>
              <th>Estudiante</th>
              <th>Última actividad</th>
              <th>Va por</th>
              <th title="Código oficial de la competencia · nivel de hoy · ejercicios resueltos/intentados">Nivel por competencia</th>
              <th class="num">Resueltos</th>
              <th class="num">Atascados</th>
              <th class="num">Entregas / Notas</th>
              <th class="col-accion">Detalle</th>
            </tr>
          </thead>
          <tbody>
            {filas}
          </tbody>
        </table>
      </div>
      <div id="no-coincidencias-est" class="vacia" style="display:none; text-align:center; padding: 24px;">
        No se encontraron estudiantes que coincidan con la búsqueda.
      </div>
    </div>
    {pie}
    """


def _activo_actual():
    """Cuál es el cuadernillo de esta semana. "" si el intercambio no responde."""
    try:
        import entregar_cuadernillo
        publicados, consulto = _publicados()
        return entregar_cuadernillo.activo_de(publicados) if consulto else ""
    except Exception:
        return ""


def _grupos_por_cuadernillo(items, clave, activo):
    """Agrupa por cuadernillo y ordena: el de esta semana primero, y detrás los
    demás del más reciente al más antiguo.

    Con 16 semanas publicadas, repetir el nombre del cuadernillo en cada fila
    convierte estas tablas en un muro: el docente busca «cómo va la semana en
    curso» y tiene que leerlas enteras. Agrupadas, cada cuadernillo es un
    desplegable y solo el activo se abre solo.
    """
    grupos = {}
    for it in items:
        grupos.setdefault(str(it.get(clave, "") or ""), []).append(it)
    def orden(codigo):
        return (0, "") if codigo == activo else (1, _clave_descendente(codigo))
    return [(c, grupos[c]) for c in sorted(grupos, key=orden)]


def _clave_descendente(codigo):
    """Para ordenar semana_10 antes que semana_02 (y no al revés)."""
    numeros = re.findall(r"\d+", codigo)
    return (-int(numeros[-1]) if numeros else 0, codigo)


def _desplegables(grupos, activo, cabecera, cuerpo_de, resumen_de, antes_de=None):
    """Un <details> por cuadernillo. `cuerpo_de` y `resumen_de` reciben la lista.

    `antes_de`, si se da, recibe la lista y devuelve HTML que va dentro del
    desplegable, encima de la tabla: es donde entra el gráfico del grupo.
    """
    if not grupos:
        return ""
    bloques = ""
    for codigo, items in grupos:
        abierto = " open" if (codigo == activo or len(grupos) == 1) else ""
        marca = '<span class="marca">Esta semana</span>' if codigo == activo else ""
        encima = antes_de(items) if antes_de else ""
        bloques += (
            f'<details class="grupo"{abierto}>'
            f'<summary><span class="gtit">{html.escape(_titulo(codigo))}</span>'
            f'<span class="mono tenue gcod">{html.escape(codigo)}</span>{marca}'
            f'<span class="gres">{resumen_de(items)}</span></summary>'
            f'{encima}'
            f'<div class="gtabla"><table>{cabecera}{cuerpo_de(items)}</table></div>'
            f'</details>')
    return f'<div class="caja grupos">{bloques}</div>'


def _seccion_entregas(entregas, notas, nombres, raiz, activo=""):
    if not entregas:
        return ('<div class="caja vacia">Todavía no has recogido ninguna entrega. '
                'Las que los alumnos manden aparecen en «Sin recoger» abajo; '
                'Collect en formgrader las trae aquí.</div>')

    def cuerpo(items):
        filas = ""
        for e in items:
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
                f'<tr><td>{_persona(e["alumno"], nombres, raiz)}</td>'
                f'<td>{_hace(e["cuando"])}'
                f'<div class="tenue chico">{_fecha_corta(e["cuando"])}</div></td>'
                f'<td class="num">{_tamano(e["bytes"])}</td>'
                f'<td>{estado}</td></tr>')
        return filas

    def resumen(items):
        pendientes = sum(1 for e in items
                         if not e["calificada"][0] or e["calificada"][1])
        texto = f'{len(items)} entrega{"" if len(items) == 1 else "s"}'
        if pendientes:
            texto += f' · <b class="pend">{pendientes} por calificar</b>'
        return texto

    return _desplegables(
        _grupos_por_cuadernillo(entregas, "tarea", activo), activo,
        '<tr><th>Estudiante</th><th>Entregado</th>'
        '<th class="num">Tamaño</th><th>Estado</th></tr>',
        cuerpo, resumen)


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
            f'<td class="sig"><span class="badge-siguiente">{html.escape(f["siguiente"])}</span></td></tr>')
    nota = ("" if hay_historial else
            '<p class="sub2 chico" style="margin-top:10px">El servicio de intercambio no respondió: las '
            'columnas «Lo trajeron» y «Entregaron» no están disponibles.</p>')
    return (f'<div class="caja table-responsive"><table class="tabla-minimalista">'
            '<thead><tr><th>Cuadernillo</th><th>Generada</th><th>Publicada</th>'
            '<th class="num">Puntos</th>'
            '<th class="num" title="Alumnos que lo recibieron en su carpeta">Lo trajeron</th>'
            '<th class="num" title="Alumnos con intentos registrados">Trabajando</th>'
            '<th class="num" title="Alumnos que pulsaron Entregar">Entregaron</th>'
            '<th class="num" title="Entregas que Collect aún no trajo">Sin recoger</th>'
            '<th class="num">Recogidas</th><th class="num">Calificadas</th>'
            '<th>Te toca</th></tr></thead><tbody>'
            f'{cuerpo}</tbody></table></div>{nota}')


def _quiza(n):
    if n is None:
        return '<span class="tenue" title="El servicio de intercambio no respondió">?</span>'
    return _n(n)


def _pendientes(n):
    if n is None:
        return '<span class="tenue" title="El servicio de intercambio no respondió">?</span>'
    return f'<span class="pill pill-danger"><b>{n}</b></span>' if n else '<span class="tenue">—</span>'


def _paso(hecho):
    return ('<span class="pill pill-success">Sí</span>' if hecho
            else '<span class="pill pill-neutral">No</span>')


# Cómo se leen las respuestas del alumno. El orden de FRENOS_TEXTO es el mismo
# que ve el estudiante, para que el docente reconozca lo que le preguntaron.
TIEMPOS_TEXTO = {1: "menos de 1 h", 2: "1 a 2 h", 3: "2 a 4 h", 4: "más de 4 h"}
FRENOS_TEXTO = {
    "enunciado": "No entendían qué se pedía",
    "concepto": "No les quedó claro el tema de la clase",
    "sintaxis": "Sabían qué hacer, no cómo escribirlo",
    "error": "No entendían el error del corrector",
    "tiempo": "No les alcanzó el tiempo",
    "nada": "Les fluyó",
}
# Qué hacer con cada freno. Es la razón de que la lista sea cerrada: cada
# respuesta apunta a una acción distinta sobre el cuadernillo siguiente.
FRENOS_ACCION = {
    "enunciado": "reescribir el enunciado",
    "concepto": "retomarlo en clase",
    "sintaxis": "más ejemplos de código",
    "error": "mensajes de error más claros",
    "tiempo": "acortar el cuadernillo",
    "nada": "—",
}


def _seccion_valoraciones(datos, activo=""):
    """Lo que los alumnos dijeron de cada cuadernillo.

    Es la contraparte de «Qué cuesta y dónde se atascan»: allí está lo que el
    sistema midió, aquí lo que solo se puede saber preguntando. Juntos separan
    dos casos que en la telemetría se ven idénticos: un cuadernillo LARGO
    (mucho tiempo, pocos intentos) de uno DIFÍCIL (mucho tiempo, muchos
    intentos).
    """
    valoraciones = (datos or {}).get("valoraciones", [])
    if not valoraciones:
        return ('<div class="caja vacia">Todavía nadie ha valorado un cuadernillo. '
                '<span class="tenue">Al alumno se le pide en su panel, justo '
                'después de entregar.</span></div>')

    frenos = {}
    for f in (datos or {}).get("frenos", []):
        frenos.setdefault(f["cuadernillo_id"], []).append(f)
    comentarios = {}
    for c in (datos or {}).get("comentarios", []):
        comentarios.setdefault(c["cuadernillo_id"], []).append(c)

    def cuerpo(items):
        v = items[0]
        n = v.get("respuestas", 0)
        aprendizaje = v.get("aprendizaje")
        tiempo = v.get("tiempo_medio")

        estrellas = ""
        if aprendizaje is not None:
            llenas = int(round(float(aprendizaje)))
            estrellas = (f'<span class="estrellas">{"★" * llenas}{"☆" * (5 - llenas)}</span> '
                         f'<b>{float(aprendizaje):.1f}</b>')
        else:
            estrellas = '<span class="tenue">—</span>'

        if tiempo is not None:
            cerca = min(TIEMPOS_TEXTO, key=lambda k: abs(k - float(tiempo)))
            reloj = (f'<b>{TIEMPOS_TEXTO[cerca]}</b> '
                     f'<span class="tenue">({v.get("con_tiempo", 0)} de {n} contestaron)</span>')
        else:
            reloj = '<span class="tenue">nadie contestó</span>'

        quienes = []
        if v.get("de_entregas"):
            quienes.append(f'{v["de_entregas"]} que entregaron')
        if v.get("de_abandonos"):
            quienes.append(f'<b class="mal">{v["de_abandonos"]} que no entregaron</b>')

        filas = (
            f'<tr><td>Cuánto sienten que aprendieron</td>'
            f'<td class="num">{estrellas}</td></tr>'
            f'<tr><td>Tiempo que le dedicaron</td><td class="num">{reloj}</td></tr>'
            f'<tr><td>Quién respondió</td>'
            f'<td class="num">{" · ".join(quienes) or "—"}</td></tr>')

        for f in frenos.get(v["cuadernillo_id"], []):
            etiqueta = FRENOS_TEXTO.get(f["freno"], f["freno"])
            accion = FRENOS_ACCION.get(f["freno"], "")
            marca = "" if f["freno"] == "nada" else ' class="mal"'
            filas += (
                f'<tr><td>{html.escape(etiqueta)} '
                f'<div class="tenue chico">{html.escape(accion)}</div></td>'
                f'<td class="num"><b{marca}>{f["personas"]}</b> '
                f'<span class="tenue">de {n}</span></td></tr>')

        for c in comentarios.get(v["cuadernillo_id"], []):
            quien = ("" if c.get("entregado") is not False
                     else ' <span class="tenue">· no entregó</span>')
            filas += (
                f'<tr><td colspan="2"><div class="tenue chico">Comentario{quien}'
                f'</div>{html.escape(c["comentario"])}</td></tr>')
        return filas

    def resumen(items):
        v = items[0]
        n = v.get("respuestas", 0)
        texto = f'{n} respuesta{"" if n == 1 else "s"}'
        if v.get("aprendizaje") is not None:
            texto += f' · aprendizaje {float(v["aprendizaje"]):.1f}/5'
        return texto

    return _desplegables(
        _grupos_por_cuadernillo(valoraciones, "cuadernillo_id", activo), activo,
        '<tr><th>Qué dijeron</th><th class="num">Cuántos</th></tr>',
        cuerpo, resumen)


def _seccion_dificultad(datos, activo=""):
    ejercicios = (datos or {}).get("ejercicios", [])
    if not ejercicios:
        return ('<div class="caja vacia">Todavía no hay intentos reales en '
                'ningún ejercicio. <span class="tenue">Ejecutar la celda vacía '
                'no cuenta: eso lo hace todo el mundo al recorrer el cuadernillo.'
                '</span></div>')

    def cuerpo(items):
        filas = ""
        for e in items:
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
            orden = (f'<span class="tenue chico">celda {e["orden"]}</span>'
                     if e.get("orden") else "")
            filas += (
                f'<tr><td class="mono">{html.escape(e["exercise_id"])} {orden}</td>'
                f'<td class="num">{_n(e.get("puntos_maximos"))}</td>'
                f'<td class="num">{intentaron}</td>'
                f'<td class="num">{_n(resolvieron)}</td>'
                f'<td class="num">{pct_primera}</td>'
                f'<td class="num">{cuesta}</td>'
                f'<td class="num">{"<b class=mal>%d</b>" % atascados if atascados else _n(0)}</td>'
                f'<td class="num">{_n(e.get("alumnos_a_medias", 0))}</td></tr>')
        return filas

    def resumen(items):
        atascados = sum(e.get("alumnos_atascados", 0) for e in items)
        texto = f'{len(items)} ejercicio{"" if len(items) == 1 else "s"}'
        if atascados:
            texto += f' · <b class="mal">{atascados} atascado{"" if atascados == 1 else "s"}</b>'
        return texto

    return _desplegables(
        _grupos_por_cuadernillo(ejercicios, "cuadernillo_id", activo), activo,
        '<tr><th>Ejercicio</th><th class="num">Puntos</th>'
        '<th class="num">Lo intentaron</th><th class="num">Lo resolvieron</th>'
        '<th class="num" title="De los que lo resolvieron, cuántos a la primera">A la primera</th>'
        '<th class="num" title="Mediana de intentos reales hasta pasar la prueba">Intentos hasta pasar</th>'
        '<th class="num">Atascados</th><th class="num">A medias</th></tr>',
        cuerpo, resumen, antes_de=_grafico_dificultad)


def _seccion_malentendidos(datos, activo=""):
    lista = [m for m in (datos or {}).get("malentendidos", [])
             if m.get("alumnos", 0) >= 1]
    if not lista:
        return ('<div class="caja vacia">Todavía no hay ningún error que se '
                'repita entre varias personas.</div>')

    def cuerpo(items):
        filas = ""
        for m in items[:8]:
            filas += (
                f'<tr><td class="num"><b>{m["alumnos"]}</b></td>'
                f'<td class="mono">{html.escape(m["exercise_id"])}</td>'
                f'<td><b>{html.escape(m["error_type"])}</b>'
                f'<div class="tenue mensaje">{html.escape(m["mensaje"])}</div></td></tr>')
        return filas

    def resumen(items):
        n = min(len(items), 8)
        return f'{n} error{"" if n == 1 else "es"} que se repite{"" if n == 1 else "n"}'

    return _desplegables(
        _grupos_por_cuadernillo(lista, "cuadernillo_id", activo), activo,
        '<tr><th class="num">Personas</th><th>Ejercicio</th>'
        '<th>Qué les sale</th></tr>',
        cuerpo, resumen)


def _guia_competencias(comps):
    """Los siete indicadores con su texto completo, a la vista.

    Hasta ahora los códigos I1…I7 solo se leían pasando el ratón por encima
    («Pasa el ratón para leer cuál es»). Un código no dice nada por sí solo: el
    docente tiene que poder leer qué mide cada uno sin adivinar ni recordar, y
    menos aún con el ratón en una pantalla que va a mirar en clase.

    Se marca cuántos ejercicios tiene cada uno porque es la otra mitad del
    contexto: un indicador con cero ejercicios no es que el curso vaya mal, es
    que todavía no se ha diseñado nada para él.
    """
    if not comps:
        return ""
    filas = ""
    for c in sorted(comps, key=lambda x: x.get("competencia_id", "")):
        n = c.get("ejercicios_disenados", 0)
        cuantos = (f'{n} ejercicio{"" if n == 1 else "s"}' if n
                   else '<span class="tenue">sin ejercicios todavía</span>')
        filas += (f'<tr><td class="mono">{_etiqueta_comp(c)}</td>'
                  f'<td>{html.escape(c.get("descripcion", ""))}</td>'
                  f'<td class="num">{cuantos}</td></tr>')
    codigos = ", ".join(html.escape(_codigo(c)) for c in sorted(comps, key=lambda x: x.get("competencia_id", "")))
    return (f'<details class="caja guia"><summary>Qué mide cada competencia '
            f'({codigos})</summary><table>{filas}</table></details>')


def _seccion_competencias(datos, estudiantes=None):
    comps = (datos or {}).get("competencias", [])
    if not comps:
        return '<div class="caja vacia">Sin datos de competencias.</div>'
    grafico = _grafico_niveles(datos, estudiantes or [])
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
            f'<div class="comp"><div class="comp-id">{_etiqueta_comp(c)}'
            f' · {disenados} ejercicio{"" if disenados == 1 else "s"}</div>'
            f'<div class="comp-e"><b>{resolvieron}</b> de {alumnos} '
            f'{"estudiante" if alumnos == 1 else "estudiantes"} resolvió alguno</div>'
            f'<div class="barra"><div class="relleno" style="width:{pct}%;background:{color}"></div></div>'
            f'<div class="comp-d">{html.escape(c["descripcion"])}</div></div>')
    resto = ""
    if sin_datos:
        resto += ('<p class="sub2">Con ejercicios pero sin actividad todavía: '
                  + ", ".join(f'<b title="{html.escape(c["descripcion"])}">{html.escape(_codigo(c))}</b>'
                              f' ({c["ejercicios_disenados"]})' for c in sin_datos)
                  + '. <span class="tenue">Pasa el ratón para leer cuál es.</span></p>')
    if sin_ejercicios:
        resto += ('<p class="sub2">Sin ningún ejercicio que las evalúe todavía: '
                  + ", ".join(f'<b title="{html.escape(c["descripcion"])}">{html.escape(_codigo(c))}</b>'
                              for c in sin_ejercicios)
                  + '. <span class="tenue">Hasta que se etiqueten ejercicios con ella, nadie puede tener nivel ahí.</span></p>')
    if not tarjetas:
        return f'{grafico}<div class="caja vacia">Nadie ha trabajado aún ningún ejercicio etiquetado.</div>{resto}'
    return (f'{grafico}<h3 class="h3">Cuántos han resuelto algo de cada competencia</h3>'
            f'<p class="sub2">La barra es la parte del grupo con actividad que ya resolvió al menos un ejercicio de esa competencia. No es el nivel: el nivel está arriba y en la fila de cada estudiante.</p>'
            f'<div class="comps">{tarjetas}</div>{resto}')


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


ESTILO = """
  :root {
    --bg-app: #f8fafc;
    --surface: #ffffff;
    --border: #e2e8f0;
    --border-light: #f1f5f9;
    --text-main: #0f172a;
    --text-muted: #64748b;
    --text-subtle: #94a3b8;
    --primary: #2563eb;
    --primary-light: #eff6ff;
    --primary-hover: #1d4ed8;
    --success: #16a34a;
    --success-bg: #f0fdf4;
    --success-border: #bbf7d0;
    --warning: #d97706;
    --warning-bg: #fffbeb;
    --warning-border: #fde68a;
    --danger: #dc2626;
    --danger-bg: #fef2f2;
    --danger-border: #fecaca;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 28px 20px 80px;
    background: var(--bg-app); color: var(--text-main);
    font: 14.5px/1.55 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .marco { max-width: 1240px; margin: 0 auto; }
  
  /* Cabecera y acciones */
  .top-header {
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: 16px; flex-wrap: wrap; margin-bottom: 22px;
  }
  h1 { font-size: 26px; font-weight: 750; margin: 0 0 4px; color: var(--text-main); letter-spacing: -0.02em; }
  .sub { color: var(--text-muted); font-size: 14px; margin: 0; }
  .btn-top-action {
    background: #ffffff; border: 1px solid var(--border); color: var(--text-main);
    padding: 8px 14px; border-radius: 8px; font-size: 13.5px; font-weight: 600;
    text-decoration: none; display: inline-flex; align-items: center; gap: 6px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04); transition: all 0.15s ease;
  }
  .btn-top-action:hover { border-color: var(--primary); color: var(--primary); background: var(--primary-light); text-decoration: none; }
  
  /* KPI Cards */
  .kpi-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 14px; margin-bottom: 28px;
  }
  .kpi-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .kpi-card:hover { transform: translateY(-1px); box-shadow: 0 3px 6px rgba(0,0,0,0.05); }
  .kpi-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .kpi-label { font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }
  .kpi-icon { font-size: 16px; }
  .kpi-val { font-size: 24px; font-weight: 750; color: var(--text-main); line-height: 1.2; letter-spacing: -0.01em; }
  .kpi-sub { font-size: 12.5px; color: var(--text-muted); margin-top: 5px; }
  .kpi-card-danger { border-left: 4px solid var(--danger); }
  .kpi-card-warning { border-left: 4px solid var(--warning); }
  .kpi-card-success { border-left: 4px solid var(--success); }

  /* Tabs principales */
  .tabs-nav {
    display: flex; gap: 6px; border-bottom: 1px solid var(--border);
    margin-bottom: 24px; overflow-x: auto; padding-bottom: 2px;
  }
  .tab-btn {
    background: none; border: none; padding: 10px 16px; font-size: 14px;
    font-weight: 600; color: var(--text-muted); cursor: pointer;
    border-radius: 8px 8px 0 0; border-bottom: 2px solid transparent;
    transition: all 0.15s ease; white-space: nowrap;
    display: inline-flex; align-items: center; gap: 8px;
  }
  .tab-btn:hover { color: var(--text-main); background: #f1f5f9; }
  .tab-btn.active { color: var(--primary); border-bottom-color: var(--primary); background: var(--primary-light); }
  .tab-count {
    background: #e2e8f0; color: var(--text-muted); font-size: 11px;
    padding: 2px 7px; border-radius: 999px; font-weight: 700;
  }
  .tab-btn.active .tab-count { background: #dbeafe; color: #1e40af; }
  .tab-pane { display: none; }
  .tab-pane.active { display: block; animation: fadeIn 0.15s ease; }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

  /* Cajas y tablas minimalistas */
  .caja {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; overflow-x: auto; margin-bottom: 22px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  }
  .vacia { padding: 22px; color: var(--text-muted); font-size: 14px; }
  h2 { font-size: 18px; font-weight: 700; margin: 28px 0 6px; color: var(--text-main); }
  h2:first-child { margin-top: 0; }
  .sub2 { color: var(--text-muted); font-size: 13.5px; margin: 0 0 14px; line-height: 1.5; }
  .chico { font-size: 12px; }
  a { color: var(--primary); text-decoration: none; font-weight: 600; }
  a:hover { text-decoration: underline; }
  
  .table-responsive { overflow-x: auto; }
  .tabla-minimalista { width: 100%; border-collapse: collapse; font-size: 13.5px; }
  .tabla-minimalista th {
    text-align: left; font-size: 11px; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.05em; padding: 11px 16px;
    border-bottom: 1px solid var(--border); font-weight: 700;
    white-space: nowrap; background: #fafbfc;
  }
  .tabla-minimalista td { padding: 12px 16px; border-bottom: 1px solid var(--border-light); vertical-align: middle; }
  .tabla-minimalista tr.fila-estudiante { cursor: pointer; transition: background-color 0.12s ease; }
  .tabla-minimalista tr.fila-estudiante:hover { background-color: #f8fafc; }
  .tabla-minimalista tr:last-child td { border-bottom: none; }
  
  .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; }
  .tenue { color: var(--text-subtle); }
  
  /* Pills y badges */
  .pill {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 8px; border-radius: 999px; font-size: 11.5px; font-weight: 600;
    line-height: 1.35; white-space: nowrap;
  }
  .pill-success { background: var(--success-bg); color: var(--success); border: 1px solid var(--success-border); }
  .pill-warning { background: var(--warning-bg); color: var(--warning); border: 1px solid var(--warning-border); }
  .pill-danger { background: var(--danger-bg); color: var(--danger); border: 1px solid var(--danger-border); }
  .pill-neutral { background: #f1f5f9; color: var(--text-muted); border: 1px solid var(--border); }
  
  .badge-cuad { background: var(--primary-light); color: var(--primary); padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; white-space: nowrap; }
  .badge-resueltos { font-variant-numeric: tabular-nums; color: var(--text-main); font-size: 13.5px; }
  .badge-nota { font-family: ui-monospace, monospace; font-size: 12px; background: #f8fafc; border: 1px solid var(--border); padding: 2px 7px; border-radius: 4px; color: var(--text-main); }
  .badge-entregas { font-size: 12px; font-weight: 600; color: var(--text-muted); }
  .badge-siguiente { background: #f1f5f9; border: 1px solid var(--border); border-radius: 6px; padding: 4px 9px; font-size: 12px; font-weight: 600; color: var(--text-main); display: inline-block; }
  .marca { background: var(--primary); color: #fff; font-size: 11px; padding: 2px 7px; border-radius: 4px; margin-left: 6px; font-weight: 600; white-space: nowrap; }
  .banda { background: #fdf9ef; border-left: 3px solid var(--warning); padding: 12px 16px; border-radius: 6px; margin-bottom: 18px; font-size: 14px; }
  
  /* Toolbar Estudiantes */
  .toolbar-estudiantes {
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
    gap: 12px; padding: 14px 18px; border-bottom: 1px solid var(--border);
    background: #fafbfc;
  }
  .search-box {
    display: flex; align-items: center; gap: 8px; background: #ffffff;
    border: 1px solid #cbd5e1; border-radius: 8px; padding: 6px 12px;
    min-width: 260px; flex: 1; max-width: 380px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  }
  .search-box input { border: none; outline: none; font-size: 13.5px; width: 100%; background: transparent; color: var(--text-main); }
  .filter-pills { display: flex; gap: 6px; flex-wrap: wrap; }
  .f-pill {
    background: #ffffff; border: 1px solid #cbd5e1; border-radius: 20px;
    padding: 5px 12px; font-size: 12px; font-weight: 600; color: #475569;
    cursor: pointer; transition: all 0.15s ease;
  }
  .f-pill:hover { border-color: #94a3b8; color: var(--text-main); }
  .f-pill.active { background: var(--primary); border-color: var(--primary); color: #ffffff; }

  /* Fila estudiante y avatar */
  .estudiante-meta { display: flex; align-items: center; gap: 12px; }
  .avatar {
    width: 34px; height: 34px; border-radius: 50%; display: flex;
    align-items: center; justify-content: center; font-size: 12px;
    font-weight: 700; flex-shrink: 0;
  }
  .estudiante-nombre { font-weight: 650; color: var(--text-main); font-size: 14px; }
  .estudiante-sub { color: var(--text-muted); font-size: 12px; font-family: ui-monospace, monospace; }
  .tiempo-rel { font-size: 13px; color: var(--text-main); white-space: nowrap; }
  .btn-desplegar {
    background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px;
    padding: 5px 10px; font-size: 12px; font-weight: 600; color: #334155;
    cursor: pointer; display: inline-flex; align-items: center; gap: 4px;
    transition: all 0.15s ease;
  }
  .btn-desplegar:hover { border-color: var(--primary); color: var(--primary); background: var(--primary-light); }
  .btn-desplegar.open { background: var(--primary); border-color: var(--primary); color: #ffffff; }
  .btn-desplegar .arrow { font-size: 10px; transition: transform 0.15s ease; }
  .col-accion { text-align: right; width: 110px; }

  /* Acordeón / Drill-down de estudiante */
  .fila-detalle td {
    background: #f8fafc; border-bottom: 2px solid #cbd5e1;
    padding: 16px 20px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
  }
  .drilldown-wrapper {
    background: #ffffff; border: 1px solid var(--border);
    border-radius: 10px; border-left: 4px solid var(--primary);
    padding: 18px 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);
  }
  .drilldown-header {
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid var(--border-light); padding-bottom: 12px;
    margin-bottom: 14px; flex-wrap: wrap; gap: 10px;
  }
  .drilldown-title { font-size: 15.5px; font-weight: 700; color: var(--text-main); }
  .drilldown-sid { font-size: 12.5px; color: var(--text-muted); margin-left: 8px; }
  .drilldown-actions { display: flex; gap: 10px; align-items: center; }
  .btn-link-out {
    font-size: 12.5px; font-weight: 600; color: var(--primary);
    padding: 4px 9px; border-radius: 5px; text-decoration: none;
  }
  .btn-link-out:hover { background: var(--primary-light); text-decoration: none; }
  .btn-close-det {
    background: none; border: 1px solid #cbd5e1; border-radius: 5px;
    font-size: 12px; font-weight: 600; color: var(--text-muted);
    padding: 4px 9px; cursor: pointer;
  }
  .btn-close-det:hover { background: #f1f5f9; color: var(--text-main); }

  .sub-kpis { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
  .sub-kpi {
    background: #f8fafc; border: 1px solid var(--border);
    border-radius: 6px; padding: 7px 12px; font-size: 12.5px; color: #334155;
  }
  .sub-kpi .kpi-num { font-weight: 700; font-size: 14.5px; margin-right: 4px; color: var(--text-main); }
  .sub-kpi.kpi-alerta { background: var(--danger-bg); border-color: var(--danger-border); color: #991b1b; }
  .sub-kpi.kpi-alerta .kpi-num { color: var(--danger); }

  .subtabs-nav {
    display: flex; gap: 6px; border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
  }
  .subtab-btn {
    background: none; border: none; padding: 8px 14px; font-size: 13px;
    font-weight: 600; color: var(--text-muted); cursor: pointer;
    border-radius: 6px 6px 0 0; border-bottom: 2px solid transparent;
  }
  .subtab-btn:hover { color: var(--text-main); }
  .subtab-btn.active { color: var(--primary); border-bottom-color: var(--primary); background: var(--primary-light); }
  
  /* Subtab 1: Microcompetencias */
  .comps-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 12px; margin-bottom: 6px;
  }
  .comp-card-mini {
    background: #ffffff; border: 1px solid var(--border);
    border-radius: 8px; padding: 13px 15px;
  }
  .comp-mini-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
  .comp-mini-id { font-weight: 700; font-size: 14.5px; color: var(--text-main); }
  .comp-mini-reason { font-size: 12px; color: var(--text-muted); line-height: 1.35; margin-bottom: 10px; min-height: 32px; }
  .comp-mini-bar-group { margin-bottom: 8px; }
  .comp-mini-stats { display: flex; justify-content: space-between; font-size: 11.5px; font-weight: 600; color: #334155; margin-bottom: 3px; }
  .progress-bar-bg { background: #e2e8f0; border-radius: 999px; height: 6px; overflow: hidden; }
  .progress-bar-fill { height: 100%; border-radius: 999px; }
  .comp-mini-meta { font-size: 11px; color: var(--text-subtle); }
  .comp-mini-desc { font-size: 11px; color: var(--text-muted); margin-top: 6px; line-height: 1.35; }
  
  /* Subtab 2: Cuadernillos tabla */
  .tabla-sub { width: 100%; border-collapse: collapse; font-size: 13px; }
  .tabla-sub th { background: #fafbfc; padding: 9px 12px; font-size: 11px; text-transform: uppercase; color: var(--text-muted); border-bottom: 1px solid var(--border); text-align: left; }
  .tabla-sub td { padding: 10px 12px; border-bottom: 1px solid var(--border-light); vertical-align: middle; }

  /* Subtab 3: Recorrido y Fallas */
  .ejerc-filter-bar { display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap; }
  .ejerc-f-btn {
    background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px;
    padding: 4px 10px; font-size: 12px; font-weight: 600; color: #475569; cursor: pointer;
  }
  .ejerc-f-btn.active { background: #0f172a; color: #ffffff; border-color: #0f172a; }
  .ejercicios-lista { display: flex; flex-direction: column; gap: 8px; }
  .ejercicio-item {
    background: #ffffff; border: 1px solid var(--border);
    border-radius: 8px; padding: 12px 14px;
  }
  .ejercicio-item.atascado { border-left: 3px solid var(--danger); }
  .ejercicio-item.amedias { border-left: 3px solid var(--warning); }
  .ejercicio-item.resuelto { border-left: 3px solid var(--success); }
  .ejercicio-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
  .ejercicio-cod { font-weight: 700; font-size: 13.5px; color: var(--text-main); }
  .badge-semana { background: #f1f5f9; color: #475569; font-size: 11px; padding: 2px 7px; border-radius: 4px; margin-left: 6px; }
  .ejercicio-meta { display: flex; align-items: center; gap: 10px; }
  .ejercicio-intentos { font-size: 12px; color: var(--text-muted); }
  
  .error-box {
    background: #0f172a; border-radius: 6px; padding: 10px 12px;
    margin-top: 8px; font-family: ui-monospace, SFMono-Regular, monospace; font-size: 12px;
  }
  .error-type { color: #f87171; font-weight: 700; margin-bottom: 4px; }
  .error-code { color: #fecaca; margin: 0; white-space: pre-wrap; word-break: break-word; font-family: inherit; font-size: inherit; }

  .detalle-loading { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 28px; color: var(--text-muted); font-size: 13.5px; }
  .spinner { width: 18px; height: 18px; border: 2px solid #e2e8f0; border-top-color: var(--primary); border-radius: 50%; animation: spin 0.6s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Desplegables de grupos */
  .grupos { overflow: visible; }
  .grupo { border-bottom: 1px solid var(--border); }
  .grupo:last-child { border-bottom: none; }
  .grupo>summary {
    cursor: pointer; padding: 12px 16px; display: flex; align-items: center;
    gap: 8px; flex-wrap: wrap; list-style: none; user-select: none;
  }
  .grupo>summary::-webkit-details-marker { display: none; }
  .grupo>summary::before { content: "▸"; color: var(--text-muted); font-size: 12px; width: 10px; }
  .grupo[open]>summary::before { content: "▾"; }
  .grupo>summary:hover { background: #f8fafc; }
  .grupo[open]>summary { border-bottom: 1px solid var(--border); }
  .gtit { font-weight: 650; color: var(--text-main); font-size: 14.5px; }
  .gcod { font-size: 12px; }
  .gres { margin-left: auto; font-size: 13px; color: var(--text-muted); white-space: nowrap; }
  .gtabla { overflow-x: auto; }
  
  .estrellas { color: var(--warning); letter-spacing: 1px; }
  .guia summary { cursor: pointer; font-weight: 600; color: var(--primary); list-style: none; padding: 10px 14px; }
  .guia summary::-webkit-details-marker { display: none; }
  .guia summary:before { content: '▸ '; color: var(--text-muted); }
  .guia[open] summary:before { content: '▾ '; }
  .guia table { margin-top: 4px; }
  .guia td { vertical-align: top; padding: 8px 12px; font-size: 13px; }

  /* Competencias generales */
  .comps { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); margin-bottom: 14px; }
  .comp { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
  .comp-id { font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em; margin-bottom: 6px; font-weight: 700; }
  .comp-e { font-size: 14px; color: var(--text-main); margin-bottom: 8px; }
  .comp-d { font-size: 12.5px; color: var(--text-muted); margin-top: 9px; line-height: 1.45; }
  .barra { height: 7px; background: #e9ecef; border-radius: 4px; overflow: hidden; }
  .relleno { height: 100%; border-radius: 4px; }
  
  .nivel { display: inline-block; font-size: 18px; font-weight: 700; line-height: 1; padding: 4px 9px; border-radius: 6px; color: #fff; margin-bottom: 8px; }
  .nivel.sinmedir { background: none; color: var(--text-subtle); font-size: 14px; font-weight: 600; padding: 4px 0; }
  .nivel-por { font-size: 12.5px; color: var(--text-muted); margin: -4px 0 10px; line-height: 1.4; }
  .semanas { margin: 0 0 14px; font-size: 13.5px; }
  .semanas a { display: inline-block; padding: 3px 10px; margin: 0 5px 5px 0; border: 1px solid var(--border); border-radius: 999px; text-decoration: none; color: var(--text-main); background: #fff; }
  .semanas a.puesto { background: var(--text-main); color: #fff; border-color: var(--text-main); }
  
  .btn { padding: 8px 16px; border: 0; border-radius: 6px; background: var(--text-main); color: #fff; font-size: 13.5px; font-weight: 600; cursor: pointer; transition: opacity 0.15s; }
  .btn:hover { opacity: .9; }
  .btn:disabled { opacity: .5; cursor: default; }
  .volver { display: inline-flex; align-items: center; gap: 4px; margin-bottom: 14px; font-size: 13.5px; }
  .docentes-lista { margin-top: 14px; font-size: 12.5px; color: var(--text-muted); }
  .docentes-label { font-weight: 600; }

  /* Nivel por competencia: chips en el listado. Un color por nivel, el mismo
     que las pills del despliegue y los gráficos: N3 verde, N2 ámbar, N1 rojo,
     sin evidencia gris. */
  .celda-chips { width: 280px; }
  .chip-comp {
    display: inline-flex; align-items: center; gap: 5px; margin: 2px 6px 2px 0;
    padding: 2px 7px 2px 6px; border-radius: 999px; border: 1px solid var(--border); white-space: nowrap;
    background: #f8fafc; font-size: 12px; line-height: 1.3; cursor: help;
  }
  .chip-cod { font-weight: 700; color: var(--text-main); letter-spacing: .01em; }
  .chip-niv { font-weight: 800; font-size: 11.5px; padding: 1px 6px; border-radius: 999px; color: #fff; background: #cbd5e1; }
  .chip-rv { color: var(--text-muted); font-variant-numeric: tabular-nums; }
  .chip-n3 { background: var(--success-bg); border-color: var(--success-border); }
  .chip-n3 .chip-niv { background: var(--success); }
  .chip-n2 { background: var(--warning-bg); border-color: var(--warning-border); }
  .chip-n2 .chip-niv { background: var(--warning); }
  .chip-n1 { background: var(--danger-bg); border-color: var(--danger-border); }
  .chip-n1 .chip-niv { background: var(--danger); }
  .chip-sin .chip-niv { background: none; color: var(--text-subtle); font-weight: 700; }
  .chip-sin .chip-cod { color: var(--text-muted); font-weight: 600; }

  .leyenda { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 12px; color: var(--text-muted); margin: 0 0 10px; }
  .leyenda .cuadro { display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }
  .table-container > .leyenda { padding: 0 16px 6px; }

  /* Gráficos SVG inline: escalan al ancho de su caja. */
  .grafico { display: block; width: 100%; height: auto; max-width: 820px; font-family: inherit; }
  .grafico-caja { padding: 16px 18px 12px; margin-bottom: 14px; }
  .grafico-en-grupo { padding: 12px 16px 4px; border-bottom: 1px dashed var(--border); }
  .grafico-titulo { font-size: 13px; font-weight: 700; color: var(--text-main); margin-bottom: 8px; }
  .h3 { font-size: 15px; font-weight: 700; margin: 18px 0 4px; color: var(--text-main); }
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
    
    lista_estudiantes = [e for e in (datos or {}).get("estudiantes", []) if e.get("rol") != "instructor"]
    total_estudiantes = len(lista_estudiantes)
    activos_recientes = sum(1 for e in lista_estudiantes if _epoch_iso(e.get("ultimo_intento")) or _epoch_iso(e.get("ultimo_ingreso")))
    total_atascados = sum(e.get("ejercicios_atascados", 0) for e in lista_estudiantes)
    estudiantes_con_atascados = sum(1 for e in lista_estudiantes if e.get("ejercicios_atascados", 0) > 0)
    
    por_calificar = sum(1 for e in entregas if not e["calificada"][0] or e["calificada"][1])
    sin_recoger = sum(f.get("sin_recoger") or 0 for f in ciclo)
    total_pendientes_entrega = por_calificar + sin_recoger

    banda_analitica = (f'<div class="banda">{html.escape(aviso)}</div>' if aviso else "")
    
    # Subtítulo activo
    info_activo = next((f for f in ciclo if f["activa"]), None)
    if info_activo and info_activo.get("cierra"):
        sub_activo = f"Cierra {html.escape(str(info_activo['cierra'])[:16])}"
    elif info_activo and info_activo.get("abre"):
        sub_activo = f"Abre {html.escape(str(info_activo['abre'])[:16])}"
    elif activo:
        sub_activo = "Publicado sin límite de fecha"
    else:
        sub_activo = "Ningún cuadernillo activo"

    cabecera = f"""
    <div class="top-header">
      <div>
        <h1>Tu curso: <span style="font-weight:400">{html.escape(CURSO)}</span></h1>
        <p class="sub">
          Panel de progreso y analítica docente · Última entrega: {_hace(ultima)}
        </p>
      </div>
      <div>
        <a class="btn-top-action" href="{raiz}/formgrader">
          <span>Ir a formgrader</span> <span>↗</span>
        </a>
      </div>
    </div>
    """

    kpis = f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-head">
          <span class="kpi-label">Cuadernillo de la semana</span>
          <span class="kpi-icon">📓</span>
        </div>
        <div class="kpi-val">{html.escape(_titulo(activo)) if activo else '<span class="tenue">Sin activo</span>'}</div>
        <div class="kpi-sub">{sub_activo}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-head">
          <span class="kpi-label">Estudiantes matriculados</span>
          <span class="kpi-icon">👥</span>
        </div>
        <div class="kpi-val">{total_estudiantes}</div>
        <div class="kpi-sub"><b style="color:var(--success)">{activos_recientes}</b> con actividad en plataforma</div>
      </div>
      <div class="kpi-card {'kpi-card-danger' if estudiantes_con_atascados > 0 else 'kpi-card-success'}">
        <div class="kpi-head">
          <span class="kpi-label">Atención requerida</span>
          <span class="kpi-icon">{'⚠️' if estudiantes_con_atascados > 0 else '✅'}</span>
        </div>
        <div class="kpi-val">{estudiantes_con_atascados} <span class="chico tenue">estudiante(s)</span></div>
        <div class="kpi-sub">{total_atascados} ejercicio(s) con bloqueo recurrente</div>
      </div>
      <div class="kpi-card {'kpi-card-warning' if total_pendientes_entrega > 0 else ''}">
        <div class="kpi-head">
          <span class="kpi-label">Entregas por gestionar</span>
          <span class="kpi-icon">📥</span>
        </div>
        <div class="kpi-val">{total_pendientes_entrega}</div>
        <div class="kpi-sub">{por_calificar} por calificar · {sin_recoger} sin recoger</div>
      </div>
    </div>
    """

    tabs_nav = f"""
    <nav class="tabs-nav" role="tablist">
      <button type="button" class="tab-btn active" data-tab="tab-estudiantes" onclick="switchMainTab('tab-estudiantes')" role="tab">
        <span>👥 Estudiantes</span> <span class="tab-count">{total_estudiantes}</span>
      </button>
      <button type="button" class="tab-btn" data-tab="tab-cuadernillos" onclick="switchMainTab('tab-cuadernillos')" role="tab">
        <span>📓 Cuadernillos y Entregas</span> <span class="tab-count">{len(ciclo)}</span>
      </button>
      <button type="button" class="tab-btn" data-tab="tab-diagnostico" onclick="switchMainTab('tab-diagnostico')" role="tab">
        <span>📊 Diagnóstico y Telemetría</span>
      </button>
      <button type="button" class="tab-btn" data-tab="tab-competencias" onclick="switchMainTab('tab-competencias')" role="tab">
        <span>🎯 Competencias y Cortes</span>
      </button>
    </nav>
    """

    # Panel Tab 1: Estudiantes
    pane_estudiantes = f"""
    <div id="tab-estudiantes" class="tab-pane active" role="tabpanel">
      <h2>Listado de estudiantes</h2>
      <p class="sub2">Cada fila lleva el <b>nivel de hoy en cada competencia</b>: código oficial, N1/N2/N3 y ejercicios resueltos/intentados. Un guion es «sin evidencia» (menos de 3 ejercicios intentados), que no es lo mismo que N1. Pasa el ratón por una chip para leer el porqué; haz clic en la fila o en <b>Ver detalle ▾</b> para ver cuadernillos y fallas celda por celda.</p>
      {_seccion_estudiantes(datos, historial, notas, raiz)}
    </div>
    """

    # Panel Tab 2: Cuadernillos y Entregas
    pane_cuadernillos = f"""
    <div id="tab-cuadernillos" class="tab-pane" role="tabpanel">
      <h2>En qué punto está cada cuadernillo</h2>
      <p class="sub2">Generar → Publicar → los alumnos lo traen, trabajan y entregan → Recoger → Calificar → subir notas. La columna <b>Te toca</b> indica la siguiente acción recomendada.</p>
      {_seccion_ciclo(ciclo, hay_historial)}

      <h2>Entregas recogidas en disco</h2>
      <p class="sub2">Entregas que Collect ya trajo a tu carpeta para calificar, agrupadas por cuadernillo.</p>
      {_seccion_entregas(entregas, notas, nombres, raiz, activo)}
    </div>
    """

    # Panel Tab 3: Diagnóstico y Telemetría
    grafico_actividad = (_grafico_actividad(datos) or
                         '<div class="caja vacia">Todavía no hay dos días con intentos '
                         'reales para dibujar la línea.</div>')
    pane_diagnostico = f"""
    <div id="tab-diagnostico" class="tab-pane" role="tabpanel">
      <h2>Cuándo trabajan</h2>
      <p class="sub2">Intentos reales por día (ejecutar la celda vacía no cuenta). Si todo se amontona la víspera del cierre, conviene abrir el cuadernillo antes o recordarlo a mitad de semana.</p>
      {grafico_actividad}

      <h2>Qué cuesta y dónde se atascan</h2>
      <p class="sub2">Por ejercicio: la barra dice cuántos lo intentaron de verdad y cuántos de ellos lo resolvieron (verde) o se quedaron atascados (rojo). En la tabla, cuántos pasaron a la primera y cuántos intentos costó a quienes lo resolvieron. «Atascado» es quien escribió una respuesta que no pasa y no ha vuelto a pasar.</p>
      {_seccion_dificultad(datos, activo)}

      <h2>Lo que se están equivocando igual (Malentendidos comunes)</h2>
      <p class="sub2">El mismo error en varias personas. Suele indicar una laguna conceptual para retomar en clase.</p>
      {_seccion_malentendidos(datos, activo)}

      <h2>Quién está peleando solo</h2>
      <p class="sub2">Estudiantes con alta tasa de fallos recientes que podrían requerir acompañamiento.</p>
      {_seccion_riesgo(datos, nombres, raiz)}

      <h2>Qué dicen ellos del cuadernillo (Valoraciones)</h2>
      <p class="sub2">Percepción subjetiva de aprendizaje (estrellas), tiempo real dedicado, causas de freno reportadas y comentarios directos.</p>
      {_seccion_valoraciones(datos, activo)}
    </div>
    """

    # Panel Tab 4: Competencias y Cortes
    pane_competencias = f"""
    <div id="tab-competencias" class="tab-pane" role="tabpanel">
      <h2>Cómo va el grupo por competencia</h2>
      <p class="sub2">Cada estudiante recibe un nivel por competencia a partir de lo que intentó y resolvió: <b>N3</b> lo resuelve con soltura, <b>N2</b> lo resuelve pero le cuesta (2 o más fallos por ejercicio, o lo deja a medias), <b>N1</b> no le sale. Con menos de 3 ejercicios intentados no hay nivel: es «sin evidencia», no N1. Los códigos son los del microcurrículo (mCP17, mCC87, mCC103); I1, I3, I4 son la clave interna.</p>
      {_seccion_salud(datos)}
      {_seccion_competencias(datos, lista_estudiantes)}
      {_guia_competencias((datos or {}).get('competencias', []))}

      <h2>Congelar un corte</h2>
      <p class="sub2">El nivel de competencias mostrado es el de <b>hoy</b>. Un corte almacena una instantánea con fecha y umbrales para contrastar el avance a lo largo del semestre.</p>
      <p class="sub2">Asigna un nombre descriptivo: <b>pre</b>, <b>post</b>, <b>corte 1</b>… Repetir un nombre sobrescribe ese corte.</p>
      <div class="caja" style="padding: 18px 20px;">
        <label for="corte-etiqueta" style="font-weight:600; margin-right:8px;">Nombre del corte:</label>
        <input id="corte-etiqueta" type="text" maxlength="60" placeholder="corte_1"
               style="padding:8px 12px; border:1px solid var(--border); border-radius:6px; font-size:14px; min-width:200px;">
        <button id="corte-btn" class="btn" style="margin-left:8px;">Congelar el corte de hoy</button>
        <span id="corte-dice" class="sub2" style="margin-left:12px; font-weight:600;" role="status" aria-live="polite"></span>
      </div>
    </div>
    """

    scripts = rf"""
<script>
(function() {{
  var raiz = "{raiz}";
  var cacheEstudiantes = {{}};
  window.currentFiltroEst = "todos";

  function esc(s) {{
    if (s === null || s === undefined) return "";
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }}

  // --- Cambio de pestañas principales ---
  window.switchMainTab = function(tabId) {{
    var tabs = ["tab-estudiantes", "tab-cuadernillos", "tab-diagnostico", "tab-competencias"];
    tabs.forEach(function(t) {{
      var pane = document.getElementById(t);
      var btn = document.querySelector('.tab-btn[data-tab="' + t + '"]');
      if (pane) {{
        if (t === tabId) pane.classList.add("active");
        else pane.classList.remove("active");
      }}
      if (btn) {{
        if (t === tabId) {{
          btn.classList.add("active");
          btn.setAttribute("aria-selected", "true");
        }} else {{
          btn.classList.remove("active");
          btn.setAttribute("aria-selected", "false");
        }}
      }}
    }});
    if (history.replaceState) {{
      history.replaceState(null, null, "#" + tabId.replace("tab-", ""));
    }}
  }};

  // --- Filtro y búsqueda en tabla de estudiantes ---
  window.filtrarEstudiantes = function() {{
    var input = document.getElementById("filtro-busqueda-est");
    var txt = (input ? input.value : "").toLowerCase().trim();
    var filtroPill = window.currentFiltroEst || "todos";
    var filas = document.querySelectorAll(".fila-estudiante");
    var visibles = 0;

    filas.forEach(function(fila) {{
      var sid = fila.getAttribute("data-sid") || "";
      var safeId = fila.getAttribute("data-safeid") || "";
      var nombre = fila.getAttribute("data-nombre") || "";
      var email = fila.getAttribute("data-email") || "";
      var atascados = parseInt(fila.getAttribute("data-atascados") || "0", 10);
      var ingreso = fila.getAttribute("data-ingreso") === "1";
      var nivel = parseInt(fila.getAttribute("data-nivel") || "0", 10);
      var detRow = document.getElementById("det-row-" + safeId);

      var coincideTexto = !txt || nombre.indexOf(txt) !== -1 || email.indexOf(txt) !== -1 || sid.indexOf(txt) !== -1;
      var coincideFiltro = true;
      if (filtroPill === "atascados") {{
        coincideFiltro = atascados > 0;
      }} else if (filtroPill === "al_dia") {{
        coincideFiltro = atascados === 0 && ingreso;
      }} else if (filtroPill === "sin_actividad") {{
        coincideFiltro = !ingreso;
      }} else if (filtroPill === "sin_nivel") {{
        coincideFiltro = nivel === 0;
      }}

      if (coincideTexto && coincideFiltro) {{
        fila.style.display = "";
        visibles++;
      }} else {{
        fila.style.display = "none";
        if (detRow) detRow.style.display = "none";
      }}
    }});

    var noRes = document.getElementById("no-coincidencias-est");
    if (noRes) noRes.style.display = (visibles === 0 ? "block" : "none");
  }};

  window.setFiltroEstudiantes = function(filtro, btn) {{
    window.currentFiltroEst = filtro;
    var pills = document.querySelectorAll("#filtro-pills-est .f-pill");
    pills.forEach(function(p) {{ p.classList.remove("active"); }});
    if (btn) btn.classList.add("active");
    window.filtrarEstudiantes();
  }};

  // --- Despliegue interactivo / Accordion por estudiante ---
  window.toggleFilaEstudiante = function(sid, safeId, nombre, evt) {{
    if (evt) evt.stopPropagation();
    var row = document.getElementById("det-row-" + safeId);
    var arrow = document.getElementById("arrow-" + safeId);
    var btn = document.getElementById("btn-toggle-" + safeId);
    if (!row) return;

    var abierto = row.style.display === "table-row";
    if (abierto) {{
      row.style.display = "none";
      if (arrow) arrow.textContent = "▾";
      if (btn) btn.classList.remove("open");
    }} else {{
      row.style.display = "table-row";
      if (arrow) arrow.textContent = "▴";
      if (btn) btn.classList.add("open");
      if (!cacheEstudiantes[sid]) {{
        cargarDetalleEstudiante(sid, safeId, nombre);
      }} else {{
        renderDetalleEstudiante(sid, safeId, nombre, cacheEstudiantes[sid]);
      }}
    }}
  }};

  function cargarDetalleEstudiante(sid, safeId, nombre) {{
    var box = document.getElementById("det-box-" + safeId);
    if (!box) return;
    box.innerHTML = '<div class="detalle-loading"><div class="spinner"></div><div>Cargando recorrido y microcompetencias de <b>' + esc(nombre) + '</b>…</div></div>';

    fetch(raiz + "/panel-docente/api/estudiante/" + encodeURIComponent(sid))
      .then(function(r) {{
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      }})
      .then(function(data) {{
        cacheEstudiantes[sid] = data;
        renderDetalleEstudiante(sid, safeId, nombre, data);
      }})
      .catch(function(err) {{
        box.innerHTML = '<div class="vacia" style="text-align:center"><p style="color:var(--danger)">No se pudo cargar el detalle del estudiante.</p><button type="button" class="btn btn-sm" onclick="cargarDetalleEstudiante(\'' + esc(sid) + '\', \'' + safeId + '\', \'' + esc(nombre) + '\')">Reintentar</button></div>';
      }});
  }}

  function renderDetalleEstudiante(sid, safeId, nombre, data) {{
    var box = document.getElementById("det-box-" + safeId);
    if (!box) return;

    var comps = data.competencias || [];
    var cuads = data.cuadernillos || [];
    var ejercs = data.ejercicios || [];

    var nAtascados = ejercs.filter(function(e){{ return !e.resuelto && !e.solo_ejecuto_vacio && !e.a_medias; }}).length;
    var nResueltos = ejercs.filter(function(e){{ return e.resuelto; }}).length;
    var nEntregados = cuads.filter(function(c){{ return c.entregado; }}).length;

    var h = '<div class="drilldown-wrapper">';
    h += '<div class="drilldown-header">';
    h += '  <div><span class="drilldown-title">Detalle de aprendizaje: <b>' + esc(nombre) + '</b></span><span class="drilldown-sid mono">(' + esc(sid) + ')</span></div>';
    h += '  <div class="drilldown-actions">';
    h += '    <a class="btn-link-out" href="' + raiz + '/panel-docente/estudiante/' + encodeURIComponent(sid) + '" target="_blank">Abrir ficha completa ↗</a>';
    h += '    <button type="button" class="btn-close-det" onclick="toggleFilaEstudiante(\'' + esc(sid) + '\', \'' + safeId + '\', \'' + esc(nombre) + '\', event)">✕ Cerrar</button>';
    h += '  </div>';
    h += '</div>';

    // Sub-KPIs
    h += '<div class="sub-kpis">';
    h += '  <div class="sub-kpi"><span class="kpi-num">' + nResueltos + '</span> <span class="kpi-txt">ejercicios resueltos</span></div>';
    h += '  <div class="sub-kpi ' + (nAtascados > 0 ? 'kpi-alerta' : '') + '"><span class="kpi-num">' + nAtascados + '</span> <span class="kpi-txt">ejercicios atascados</span></div>';
    h += '  <div class="sub-kpi"><span class="kpi-num">' + nEntregados + '/' + cuads.length + '</span> <span class="kpi-txt">cuadernillos entregados</span></div>';
    h += '</div>';

    // Sub-tabs navigation
    h += '<div class="subtabs-nav" role="tablist">';
    h += '  <button type="button" class="subtab-btn active" id="st-btn-comps-' + safeId + '" onclick="switchSubTab(\'' + safeId + '\', \'comps\')">🎯 Microcompetencias (' + comps.length + ')</button>';
    h += '  <button type="button" class="subtab-btn" id="st-btn-cuads-' + safeId + '" onclick="switchSubTab(\'' + safeId + '\', \'cuads\')">📓 Cuadernillos (' + cuads.length + ')</button>';
    h += '  <button type="button" class="subtab-btn" id="st-btn-ejercs-' + safeId + '" onclick="switchSubTab(\'' + safeId + '\', \'ejercs\')">⚠️ Recorrido y Fallas (' + ejercs.length + ')</button>';
    h += '</div>';

    // Subtab 1: Microcompetencias
    h += '<div class="subtab-pane active" id="st-pane-comps-' + safeId + '">';
    if (!comps.length) {{
      h += '<div class="vacia" style="padding:12px 0">Sin datos de competencias registrados para este estudiante.</div>';
    }} else {{
      h += '<div class="comps-grid">';
      comps.forEach(function(c) {{
        var nivel = c.nivel;
        var badgeClass = nivel === 3 ? "pill-success" : (nivel === 2 ? "pill-warning" : (nivel === 1 ? "pill-danger" : "pill-neutral"));
        var nivelTexto = nivel ? ("Nivel " + nivel) : "Sin medir";
        var vistos = c.ejercicios_vistos || 0;
        var resueltos = c.ejercicios_resueltos || 0;
        var pct = vistos > 0 ? Math.round(100 * resueltos / vistos) : 0;
        var barColor = pct >= 70 ? "var(--success)" : (pct >= 40 ? "var(--warning)" : "var(--danger)");

        h += '<div class="comp-card-mini">';
        h += '  <div class="comp-mini-head">';
        h += '    <span class="comp-mini-id">' + esc(c.codigo || c.competencia_id) + (c.codigo && c.codigo !== c.competencia_id ? ' <span class="mono tenue chico">' + esc(c.competencia_id) + '</span>' : '') + '</span>';
        h += '    <span class="pill ' + badgeClass + '">' + nivelTexto + '</span>';
        h += '  </div>';
        h += '  <div class="comp-mini-reason">' + esc(c.motivo_nivel || 'Sin evidencia suficiente para dictaminar nivel') + '</div>';
        h += '  <div class="comp-mini-bar-group">';
        h += '    <div class="comp-mini-stats"><span>' + resueltos + ' de ' + vistos + ' resueltos</span><span>' + pct + '%</span></div>';
        h += '    <div class="progress-bar-bg"><div class="progress-bar-fill" style="width:' + pct + '%; background:' + barColor + '"></div></div>';
        h += '  </div>';
        h += '  <div class="comp-mini-meta">' + (c.intentos || 0) + ' intento(s) · ' + (c.abandonos || 0) + ' abandono(s)</div>';
        h += '  <div class="comp-mini-desc">' + esc(c.descripcion || '') + '</div>';
        h += '</div>';
      }});
      h += '</div>';
    }}
    h += '</div>';

    // Subtab 2: Cuadernillos
    h += '<div class="subtab-pane" id="st-pane-cuads-' + safeId + '" style="display:none">';
    if (!cuads.length) {{
      h += '<div class="vacia" style="padding:12px 0">No hay cuadernillos registrados en el curso.</div>';
    }} else {{
      h += '<table class="tabla-sub">';
      h += '<thead><tr><th>Cuadernillo</th><th>Descargado</th><th>Entregado</th><th class="num">Nota oficial</th><th>Estado</th></tr></thead><tbody>';
      cuads.forEach(function(q) {{
        var notaTxt = (q.nota_obtenida !== null && q.nota_maxima !== null)
          ? ('<b>' + q.nota_obtenida + '</b> / ' + q.nota_maxima)
          : '<span class="tenue">—</span>';
        var estadoPill = '';
        if (q.reentregada) {{
          estadoPill = '<span class="pill pill-warning">Reentregado tras calificar</span>';
        }} else if (q.calificada) {{
          estadoPill = '<span class="pill pill-success">Calificado</span>';
        }} else if (q.entregado) {{
          estadoPill = '<span class="pill pill-warning">Por calificar</span>';
        }} else if (q.traido) {{
          estadoPill = '<span class="pill pill-neutral">En progreso</span>';
        }} else {{
          estadoPill = '<span class="tenue chico">Sin abrir</span>';
        }}
        h += '<tr>';
        h += '  <td><b>' + esc(q.titulo) + '</b> <span class="mono tenue chico">(' + esc(q.tarea) + ')</span></td>';
        h += '  <td>' + (q.traido_hace ? q.traido_hace : '<span class="tenue">No</span>') + '</td>';
        h += '  <td>' + (q.entregado_hace ? q.entregado_hace : '<span class="tenue">Sin entregar</span>') + '</td>';
        h += '  <td class="num">' + notaTxt + '</td>';
        h += '  <td>' + estadoPill + '</td>';
        h += '</tr>';
      }});
      h += '</tbody></table>';
    }}
    h += '</div>';

    // Subtab 3: Recorrido y Fallas
    h += '<div class="subtab-pane" id="st-pane-ejercs-' + safeId + '" style="display:none">';
    if (!ejercs.length) {{
      h += '<div class="vacia" style="padding:12px 0">El estudiante aún no ha ejecutado ninguna prueba de código en sus cuadernillos.</div>';
    }} else {{
      h += '<div class="ejerc-filter-bar">';
      h += '  <button type="button" class="ejerc-f-btn active" onclick="filtrarEjercicios(\'' + safeId + '\', \'todos\', this)">Todos (' + ejercs.length + ')</button>';
      h += '  <button type="button" class="ejerc-f-btn" onclick="filtrarEjercicios(\'' + safeId + '\', \'fallas\', this)">⚠️ Solo fallas / atascados (' + ejercs.filter(function(e){{ return !e.resuelto; }}).length + ')</button>';
      h += '  <button type="button" class="ejerc-f-btn" onclick="filtrarEjercicios(\'' + safeId + '\', \'resueltos\', this)">✅ Resueltos (' + ejercs.filter(function(e){{ return e.resuelto; }}).length + ')</button>';
      h += '</div>';

      h += '<div class="ejercicios-lista" id="ejerc-list-' + safeId + '">';
      ejercs.forEach(function(e) {{
        var tipoClass = e.resuelto ? "resuelto" : (e.a_medias ? "amedias" : (e.solo_ejecuto_vacio ? "vacio" : "atascado"));
        var pillClass = e.resuelto ? "pill-success" : (e.a_medias ? "pill-warning" : (e.solo_ejecuto_vacio ? "pill-neutral" : "pill-danger"));
        var estadoTexto = e.resuelto ? "Resuelto" : (e.a_medias ? "A medias" : (e.solo_ejecuto_vacio ? "Celda vacía" : "Atascado"));

        h += '<div class="ejercicio-item ' + tipoClass + '" data-estado="' + tipoClass + '">';
        h += '  <div class="ejercicio-header">';
        h += '    <div><span class="mono ejercicio-cod">' + esc(e.exercise_id) + '</span><span class="badge-semana">' + esc(e.cuadernillo_titulo) + '</span></div>';
        h += '    <div class="ejercicio-meta"><span class="pill ' + pillClass + '">' + estadoTexto + '</span><span class="ejercicio-intentos">' + (e.intentos || 0) + ' intento(s)</span><span class="tenue chico">' + esc(e.ultimo_intento_hace || '') + '</span></div>';
        h += '  </div>';

        if (!e.resuelto && (e.ultimo_error || e.ultimo_mensaje)) {{
          h += '<div class="error-box">';
          if (e.ultimo_error) h += '<div class="error-type">📌 ' + esc(e.ultimo_error) + '</div>';
          if (e.ultimo_mensaje) h += '<pre class="error-code">' + esc(e.ultimo_mensaje) + '</pre>';
          h += '</div>';
        }}
        h += '</div>';
      }});
      h += '</div>';
    }}
    h += '</div>';

    h += '</div>'; // drilldown-wrapper
    box.innerHTML = h;
  }}

  window.switchSubTab = function(safeId, tabKey) {{
    var panes = ["comps", "cuads", "ejercs"];
    panes.forEach(function(k) {{
      var p = document.getElementById("st-pane-" + k + "-" + safeId);
      var b = document.getElementById("st-btn-" + k + "-" + safeId);
      if (p) p.style.display = (k === tabKey ? "block" : "none");
      if (b) {{
        if (k === tabKey) b.classList.add("active");
        else b.classList.remove("active");
      }}
    }});
  }};

  window.filtrarEjercicios = function(safeId, tipo, btn) {{
    var parent = btn.parentElement;
    var btns = parent.querySelectorAll(".ejerc-f-btn");
    btns.forEach(function(b){{ b.classList.remove("active"); }});
    btn.classList.add("active");

    var list = document.getElementById("ejerc-list-" + safeId);
    if (!list) return;
    var items = list.querySelectorAll(".ejercicio-item");
    items.forEach(function(item) {{
      var estado = item.getAttribute("data-estado");
      if (tipo === "todos") {{
        item.style.display = "block";
      }} else if (tipo === "fallas") {{
        item.style.display = (estado === "atascado" || estado === "amedias") ? "block" : "none";
      }} else if (tipo === "resueltos") {{
        item.style.display = (estado === "resuelto") ? "block" : "none";
      }}
    }});
  }};

  // Congelar corte
  var btnCorte = document.getElementById("corte-btn");
  var diceCorte = document.getElementById("corte-dice");
  if (btnCorte) {{
    function xsrf() {{
      var m = document.cookie.match(/\\b_xsrf=([^;]+)/);
      return m ? decodeURIComponent(m[1]) : "";
    }}
    btnCorte.addEventListener("click", function () {{
      var etiqueta = (document.getElementById("corte-etiqueta").value || "").trim();
      if (!etiqueta) {{ diceCorte.textContent = "Ponle un nombre al corte."; return; }}
      btnCorte.disabled = true;
      diceCorte.textContent = "Congelando…";
      fetch(raiz + "/panel-docente/corte", {{
        method: "POST",
        credentials: "same-origin",
        headers: {{"Content-Type": "application/json", "X-XSRFToken": xsrf()}},
        body: JSON.stringify({{etiqueta: etiqueta}})
      }}).then(function (r) {{ return r.json().then(function (j) {{ return {{ok: r.ok, cuerpo: j}}; }}); }})
        .then(function (res) {{
          btnCorte.disabled = false;
          diceCorte.textContent = res.ok
            ? ("Corte «" + etiqueta + "» guardado: " + res.cuerpo.filas + " filas.")
            : (res.cuerpo.error || "No se pudo guardar.");
        }})
        .catch(function () {{
          btnCorte.disabled = false;
          diceCorte.textContent = "No se pudo guardar. Inténtalo otra vez.";
        }});
    }});
  }}

  // Activación por hash de URL
  window.addEventListener("DOMContentLoaded", function() {{
    var hash = (window.location.hash || "").replace("#", "");
    if (hash === "cuadernillos") window.switchMainTab("tab-cuadernillos");
    else if (hash === "diagnostico") window.switchMainTab("tab-diagnostico");
    else if (hash === "competencias") window.switchMainTab("tab-competencias");
    else window.switchMainTab("tab-estudiantes");
  }});
}})();
</script>
"""

    cuerpo = f"""
    {cabecera}
    {banda_analitica}
    {kpis}
    {tabs_nav}
    {pane_estudiantes}
    {pane_cuadernillos}
    {pane_diagnostico}
    {pane_competencias}
    {scripts}
    """
    return _pagina("Tu curso", cuerpo)


# --- Ficha de un estudiante --------------------------------------------------------

def _html_ficha(base_url, sid, datos_panel, ficha, historial, aviso, semana=""):
    raiz = base_url.rstrip("/")
    persona = next((e for e in (datos_panel or {}).get("estudiantes", [])
                    if e.get("student_id") == sid), {})
    nombre = persona.get("nombre") or sid
    _, notas = _libro()
    banda = f'<div class="banda">{html.escape(aviso)}</div>' if aviso else ""

    bg_col, text_col = _avatar_color(sid)
    inics = _iniciales(nombre, sid)
    avatar = f'<div class="avatar" style="width:48px;height:48px;font-size:16px;background:{bg_col};color:{text_col}">{html.escape(inics)}</div>'

    moodle_pill = ('<span class="pill pill-success">Devolución Moodle activa</span>'
                   if persona.get("devolucion_moodle_posible") else
                   '<span class="pill pill-neutral">Moodle sin casilla de nota</span>')

    datos_persona = f"""
    <div style="display:flex; align-items:center; gap:16px; margin: 14px 0 20px;">
      {avatar}
      <div>
        <h1 style="margin:0 0 4px; font-size:24px;">{html.escape(nombre)}</h1>
        <div style="font-size:13px; color:var(--text-muted); display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
          <span>{html.escape(persona.get("email", "") or "sin correo")}</span>
          <span class="mono">ID: {html.escape(sid)}</span>
          <span>Último ingreso {_hace(_epoch_iso(persona.get("ultimo_ingreso")))} ({persona.get("ingresos", 0)} accesos)</span>
          {moodle_pill}
        </div>
      </div>
    </div>
    """

    # Por cuadernillo: traído / entregado / nota
    filas_c = ""
    for tarea, h in sorted((historial or {}).items()):
        traido = h.get("traido", {}).get(sid, "")
        entregado = h.get("entregado", {}).get(sid, "")
        nota = notas.get((sid, tarea))
        filas_c += (f'<tr><td><b>{_nombre(tarea)}</b></td>'
                    f'<td>{_hace(_epoch_exchange(traido)) if traido else "<span class=tenue>no lo ha traído</span>"}</td>'
                    f'<td>{_hace(_epoch_exchange(entregado)) if entregado else "<span class=tenue>sin entregar</span>"}</td>'
                    f'<td class="num">{f"<b>{nota[0]:g}</b> / {nota[1]:g}" if nota else "<span class=tenue>aún sin nota</span>"}</td></tr>')
    cuadernillos = (f'<div class="caja table-responsive"><table class="tabla-minimalista"><thead><tr><th>Cuadernillo</th><th>Lo trajo</th>'
                    f'<th>Entregó</th><th class="num">Nota</th></tr></thead><tbody>{filas_c}</tbody></table></div>'
                    if filas_c else '<div class="caja vacia">Sin cuadernillos publicados.</div>')

    ejercicios = (ficha or {}).get("ejercicios", [])
    activo = _activo_actual()

    def cuerpo_recorrido(items):
        filas = ""
        for e in items:
            if e.get("resuelto"):
                estado = '<span class="pill pill-success">Resuelto</span>'
            elif e.get("solo_ejecuto_vacio"):
                estado = '<span class="pill pill-neutral">Celda vacía</span>'
            elif e.get("a_medias"):
                estado = '<span class="pill pill-warning">A medias</span>'
            else:
                estado = '<span class="pill pill-danger">Atascado</span>'
            err = ""
            if e.get("ultimo_error") and not e.get("resuelto"):
                err = (f'<div class="error-box"><div class="error-type">📌 {html.escape(e["ultimo_error"])}</div>'
                       f'<pre class="error-code">{html.escape(e.get("ultimo_mensaje", ""))}</pre></div>')
            filas += (
                f'<tr><td class="mono"><b>{html.escape(e["exercise_id"])}</b></td>'
                f'<td>{estado}</td>'
                f'<td class="num">{_n(e.get("intentos"))}</td>'
                f'<td>{_hace(_epoch_iso(e.get("ultimo_intento")))}</td>'
                f'<td>{err}</td></tr>')
        return filas

    def resumen_recorrido(items):
        resueltos = sum(1 for e in items if e.get("resuelto"))
        atascados = sum(1 for e in items
                        if not e.get("resuelto") and not e.get("solo_ejecuto_vacio")
                        and not e.get("a_medias"))
        texto = f'{resueltos} de {len(items)} resuelto{"" if len(items) == 1 else "s"}'
        if atascados:
            texto += f' · <b style="color:var(--danger)">{atascados} atascado{"" if atascados == 1 else "s"}</b>'
        return texto

    def _tarjetas_competencia(comps):
        con_actividad = [c for c in comps if c.get("ejercicios_vistos")]
        sin_tocar = [c for c in comps
                     if not c.get("ejercicios_vistos") and c.get("ejercicios_disenados")]
        donde = f" en {html.escape(semana.replace('_', ' '))}" if semana else ""
        if not con_actividad:
            if sin_tocar:
                return ('<div class="caja vacia">Todavía no ha intentado ningún '
                        f'ejercicio{donde}, así que no hay nada que medir por '
                        'competencia.</div>')
            return (f'<div class="caja vacia">Sin datos de competencias{donde}.'
                    '</div>')

        tarjetas = ""
        for c in con_actividad:
            vistos = c.get("ejercicios_vistos", 0)
            resueltos = c.get("ejercicios_resueltos", 0)
            intentos = c.get("intentos", 0)
            abandonos = c.get("abandonos", 0)
            faltan = c.get("ejercicios_disenados", 0) - vistos
            pct = int(100 * resueltos / vistos) if vistos else 0
            color = "var(--success)" if pct >= 70 else ("var(--warning)" if pct >= 40 else "var(--danger)")

            detalle = f'{intentos} intento{"" if intentos == 1 else "s"}'
            if abandonos:
                detalle += (f' · <b style="color:var(--danger)">{abandonos} '
                            f'abandono{"" if abandonos == 1 else "s"}</b>')
            if faltan > 0:
                detalle += f' · <span class="tenue">{faltan} sin tocar</span>'

            nivel = c.get("nivel")
            motivo = html.escape(c.get("motivo_nivel", ""))
            if nivel:
                badge_cls = {3: "pill-success", 2: "pill-warning"}.get(nivel, "pill-danger")
                insignia = f'<span class="pill {badge_cls}" style="font-size:13px">Nivel {nivel}</span>'
            else:
                insignia = '<span class="pill pill-neutral" style="font-size:13px">Sin medir</span>'
                color = "#c9ced6"

            tarjetas += (
                f'<div class="comp"><div class="comp-id">'
                f'{_etiqueta_comp(c)} · {vistos} '
                f'ejercicio{"" if vistos == 1 else "s"} trabajado'
                f'{"" if vistos == 1 else "s"}</div>'
                f'<div style="margin: 6px 0 8px">{insignia}</div>'
                f'<div class="nivel-por">{motivo}</div>'
                f'<div class="comp-e"><b>{resueltos}</b> de {vistos} '
                f'resuelto{"" if vistos == 1 else "s"}</div>'
                f'<div class="barra"><div class="relleno" '
                f'style="width:{pct}%;background:{color}"></div></div>'
                f'<div class="comp-e" style="margin-top:8px">{detalle}</div>'
                f'<div class="comp-d">{html.escape(c.get("descripcion", ""))}</div></div>')

        resto = ""
        if sin_tocar:
            resto = ('<p class="sub2">Sin tocar todavía: '
                     + ", ".join(f'<b title="{html.escape(c.get("descripcion", ""))}">{html.escape(_codigo(c))}</b>'
                                 for c in sin_tocar) + '.</p>')
        return f'<div class="comps">{tarjetas}</div>{resto}'

    competencias = _tarjetas_competencia((ficha or {}).get("competencias") or [])

    semanas = sorted({e.get("cuadernillo_id") for e in ejercicios if e.get("cuadernillo_id")})
    if semanas:
        enlace = f'{raiz}/panel-docente/estudiante/{urllib.parse.quote(sid, safe="")}'
        fichas_semana = (f'<a href="{enlace}" '
                         f'class="{"" if semana else "puesto"}">Todo el curso</a>')
        for w in semanas:
            fichas_semana += (
                f'<a href="{enlace}?semana={urllib.parse.quote(w, safe="")}" '
                f'class="{"puesto" if semana == w else ""}">'
                f'{html.escape(w.replace("_", " "))}</a>')
        nota = ('' if not semana else
                '<span class="tenue chico">· una sola semana casi nunca da evidencia '
                'suficiente para un nivel formativo completo</span>')
        filtro_semana = f'<p class="semanas">{fichas_semana} {nota}</p>'
    else:
        filtro_semana = ""

    recorrido = (_desplegables(
        _grupos_por_cuadernillo(ejercicios, "cuadernillo_id", activo), activo,
        '<tr><th>Ejercicio</th><th>Estado</th><th class="num">Intentos</th>'
        '<th>Última vez</th><th>Último error</th></tr>',
        cuerpo_recorrido, resumen_recorrido)
        if ejercicios else
        '<div class="caja vacia">Todavía no ha ejecutado ninguna celda de prueba.</div>')

    cuerpo = f"""
    <a class="volver" href="{raiz}/panel-docente">← Volver al panel del curso</a>
    {datos_persona}
    {banda}
    <h2>Sus cuadernillos</h2>
    {cuadernillos}
    <h2>Cómo va por competencia</h2>
    <p class="sub2">Ejercicios de cada competencia que ha llegado a intentar y su tasa de resolución. Un <b>abandono</b> ocurre cuando se registraron fallos sin validar la celda de prueba.</p>
    {filtro_semana}
    {competencias}
    {_guia_competencias((ficha or {}).get('competencias') or [])}
    <h2>Su recorrido, ejercicio por ejercicio</h2>
    <p class="sub2">Detalle de cada celda de prueba ejecutada, intentos y mensaje exacto del último fallo.</p>
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
        semana = (self.get_argument("semana", "") or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", semana or "x"):
            semana = ""
        ruta = f"/internal/curso/{curso}/estudiante/{urllib.parse.quote(sid, safe='')}"
        if semana:
            ruta += "?cuadernillo=" + urllib.parse.quote(semana, safe="")
        datos, aviso = await _backend(f"/internal/curso/{curso}/panel")
        ficha, aviso2 = await _backend(ruta)
        historial, _ = _historial()
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.finish(_html_ficha(self.settings.get("base_url", "/"), sid, datos, ficha,
                                historial, aviso or aviso2, semana))


class EstudianteDetalleHandler(_BaseHandler):
    """GET /panel-docente/api/estudiante/<sid> — devuelve en JSON las métricas,
    microcompetencias, estado de cuadernillos y recorrido de ejercicios del alumno.
    Permite el despliegue interactivo en el panel sin recargar la página.
    """
    @web.authenticated
    async def get(self, sid):
        sid = urllib.parse.unquote(sid or "").strip()
        curso = urllib.parse.quote(CURSO, safe="")
        ruta = f"/internal/curso/{curso}/estudiante/{urllib.parse.quote(sid, safe='')}"
        ficha, aviso = await _backend(ruta)
        historial, _ = _historial()
        _, notas = _libro()
        entregas_disco = _entregas()
        publicados, _ = _publicados()

        todas_tareas = sorted(set(publicados.keys()) | {t for (a, t) in notas if a == sid}
                              | {e["tarea"] for e in entregas_disco if e["alumno"] == sid})
        cuadernillos_lista = []
        for t in todas_tareas:
            traido = (historial or {}).get(t, {}).get("traido", {}).get(sid, "")
            entregado = (historial or {}).get(t, {}).get("entregado", {}).get(sid, "")
            nota = notas.get((sid, t))
            recogida = next((e for e in entregas_disco if e["alumno"] == sid and e["tarea"] == t), None)
            cuadernillos_lista.append({
                "tarea": t,
                "titulo": _titulo(t),
                "traido": bool(traido),
                "traido_hace": _hace(_epoch_exchange(traido)) if traido else None,
                "entregado": bool(entregado),
                "entregado_hace": _hace(_epoch_exchange(entregado)) if entregado else None,
                "nota_obtenida": nota[0] if nota else None,
                "nota_maxima": nota[1] if nota else None,
                "calificada": bool(recogida["calificada"][0] if recogida else (nota is not None)),
                "reentregada": bool(recogida["calificada"][1] if recogida else False),
            })

        ejercicios_formateados = []
        for e in (ficha or {}).get("ejercicios", []):
            ejercicios_formateados.append({
                "exercise_id": e.get("exercise_id", ""),
                "cuadernillo_id": e.get("cuadernillo_id", ""),
                "cuadernillo_titulo": _titulo(e.get("cuadernillo_id", "")),
                "resuelto": bool(e.get("resuelto")),
                "a_medias": bool(e.get("a_medias")),
                "solo_ejecuto_vacio": bool(e.get("solo_ejecuto_vacio")),
                "intentos": e.get("intentos", 0),
                "ultimo_intento_hace": _hace(_epoch_iso(e.get("ultimo_intento"))),
                "ultimo_error": e.get("ultimo_error", ""),
                "ultimo_mensaje": e.get("ultimo_mensaje", ""),
            })

        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.finish(json.dumps({
            "student_id": sid,
            "competencias": (ficha or {}).get("competencias", []),
            "ejercicios": ejercicios_formateados,
            "cuadernillos": cuadernillos_lista,
            "aviso": aviso,
        }, ensure_ascii=False))


class CorteHandler(_BaseHandler):
    """POST: congela el nivel del grupo tal y como está hoy.

    Es el primer POST de este panel, que hasta ahora solo leía. La protección
    es la misma que usa admin_bridge: @web.authenticated exige sesión, y el
    XSRF lo comprueba la clase base de Jupyter con la cabecera X-XSRFToken que
    manda el navegador. El token NO vale en el cuerpo: Jupyter mira la query y
    las cabeceras, nunca el JSON, y responde un 403 sin explicación.
    """

    @web.authenticated
    async def post(self):
        try:
            cuerpo = json.loads(self.request.body.decode("utf-8") or "{}")
        except ValueError:
            self.set_status(400)
            self.finish(json.dumps({"error": "no se entendió la petición"}))
            return
        # Un JSON válido que no sea un objeto (una lista, un número) reventaba
        # aquí con AttributeError y Tornado lo servía como un 500 con traza en
        # el log. Un error del cliente no debe leerse como un fallo del
        # servidor. Mismo criterio que metrics_bridge.py.
        if not isinstance(cuerpo, dict):
            self.set_status(400)
            self.finish(json.dumps({"error": "no se entendió la petición"}))
            return
        etiqueta = (cuerpo.get("etiqueta") or "").strip()
        if not etiqueta:
            self.set_status(400)
            self.finish(json.dumps({"error": "ponle un nombre al corte"},
                                   ensure_ascii=False))
            return

        curso = urllib.parse.quote(CURSO, safe="")
        datos, aviso = await _backend_post(f"/internal/curso/{curso}/corte",
                                           {"etiqueta": etiqueta})
        self.set_header("Content-Type", "application/json; charset=utf-8")
        if datos is None:
            self.set_status(502)
            self.finish(json.dumps({"error": aviso}, ensure_ascii=False))
            return
        self.finish(json.dumps(datos, ensure_ascii=False))


def load_jupyter_server_extension(nbapp):
    if getattr(nbapp, "log", None) is not None:
        globals()["log"] = nbapp.log
    if os.environ.get("ALUMNO_ROL", "estudiante") != "instructor":
        return
    raiz = nbapp.web_app.settings.get("base_url", "/").rstrip("/")
    nbapp.web_app.add_handlers(".*$", [
        (raiz + "/panel-docente", PanelDocenteHandler),
        (raiz + r"/panel-docente/estudiante/([^/]+)", FichaHandler),
        (raiz + r"/panel-docente/api/estudiante/([^/]+)", EstudianteDetalleHandler),
        (raiz + "/panel-docente/corte", CorteHandler),
    ])
    log.info("[panel_docente_bridge] listo: panel del curso en %s/panel-docente",
             raiz)


def _load_jupyter_server_extension(server_app):
    load_jupyter_server_extension(server_app)
