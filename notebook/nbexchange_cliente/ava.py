"""Lo propio del AVA sobre el cliente de nbexchange.

Dos cosas viven aquí:

1. Cómo se autentica el contenedor ante el servicio (`AutenticacionJupyterHub`):
   con el token que JupyterHub le dio al arrancar (`JUPYTERHUB_API_TOKEN`). El
   servicio se lo enseña al Hub, y el Hub le dice quién es y a qué grupos
   pertenece; de ahí sale el curso y el rol. Ningún contenedor puede hacerse
   pasar por otro usuario: el token lo acuñó el Hub para ese servidor.

2. Las clases de intercambio con las que nbgrader trabaja de verdad
   (`ExchangeFactory.*` en nbgrader_config.py) y los ayudantes que usan los
   comandos del docente y el entregador del alumno. Envuelven a las clases
   copiadas del upstream para que un servicio caído se vea como un error de
   nbgrader (`ExchangeError`) y no como un traceback de `requests`.

Variables de entorno que importan:

  JUPYTERHUB_API_TOKEN   lo pone el Hub al arrancar el contenedor
  NBEXCHANGE_URL         dónde escucha el servicio (default http://nbexchange:9000)
  CURSO_ID               el context_id de LTI; también es el course_id de nbgrader
"""
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone

import requests
from nbgrader.coursedir import CourseDirectory
from nbgrader.exchange import ExchangeError
from traitlets.config import Config
from traitlets.config.loader import PyFileConfigLoader

from . import collect as _collect
from . import exchange as _exchange
from . import fetch_assignment as _fetch
from . import fetch_feedback as _fetch_feedback
from . import list as _list
from . import release_assignment as _release
from . import release_feedback as _release_feedback
from . import submit as _submit

URL_SERVICIO = os.environ.get("NBEXCHANGE_URL", "http://nbexchange:9000")
CURSO = os.environ.get("CURSO_ID", "curso_default")
CONFIG_NBGRADER = os.environ.get("NBGRADER_CONFIG", "/etc/jupyter/nbgrader_config.py")

# Nombre del fichero que `publicar-cuadernillo` deja junto al notebook liberado
# con la ventana de tiempo. Viaja dentro de la liberación, así que llega al
# alumno por el mismo camino que el cuadernillo y no hace falta otro canal.
FICHERO_PUBLICACION = "ava_publicacion.json"


class AutenticacionJupyterHub(_exchange.BaseApiPlugin):
    """Manda el token del servidor de usuario como `Authorization: token ...`.

    Es lo que el servicio espera (`HubAuth.get_user` del lado de nbexchange).
    Si el token no está, la petición sale sin cabecera y el servicio responde
    403: preferible a inventar una identidad.
    """

    def prep_api_call(self, path):
        url = self.service_url() + path
        token = os.environ.get("JUPYTERHUB_API_TOKEN", "")
        headers = {"Authorization": f"token {token}"} if token else {}
        return url, {}, headers


class _Ava:
    """Mixin: un servicio caído es un `ExchangeError`, no un traceback."""

    def api_request(self, path, method="GET", *args, **kwargs):
        try:
            return super().api_request(path, method, *args, **kwargs)
        except requests.exceptions.Timeout:
            raise                       # las clases del upstream ya lo tratan
        except requests.exceptions.RequestException as err:
            self.fail(f"No se pudo hablar con el servicio de intercambio "
                      f"({self.service_url()}): {err}")


class Exchange(_Ava, _exchange.Exchange):
    pass


class ExchangeList(_Ava, _list.ExchangeList):
    pass


class ExchangeFetchAssignment(_Ava, _fetch.ExchangeFetchAssignment):
    pass


class ExchangeSubmit(_Ava, _submit.ExchangeSubmit):
    pass


class ExchangeCollect(_Ava, _collect.ExchangeCollect):
    pass


class ExchangeReleaseAssignment(_Ava, _release.ExchangeReleaseAssignment):
    pass


class ExchangeReleaseFeedback(_Ava, _release_feedback.ExchangeReleaseFeedback):
    pass


class ExchangeFetchFeedback(_Ava, _fetch_feedback.ExchangeFetchFeedback):
    pass


# --- Ayudantes para los comandos y puentes del AVA ---------------------------

def cargar_config():
    """La misma configuración que carga nbgrader (/etc/jupyter/nbgrader_config.py)."""
    try:
        return PyFileConfigLoader(os.path.basename(CONFIG_NBGRADER),
                                  path=os.path.dirname(CONFIG_NBGRADER)).load_config()
    except Exception:
        return Config()


def _curso(config, assignment_id=None):
    cd = CourseDirectory(config=config)
    cd.course_id = CURSO
    if assignment_id:
        cd.assignment_id = assignment_id
    return cd


def _exchange(clase, config, assignment_id=None, **kwargs):
    obj = clase(coursedir=_curso(config, assignment_id), config=config, **kwargs)
    # Lo que decide la URL y la autenticación: siempre lo nuestro, aunque el
    # nbgrader_config.py que se cargó no lo diga.
    obj.base_service_url = URL_SERVICIO
    obj.api_plugin_class = AutenticacionJupyterHub
    return obj


def _fecha(ts):
    """'2026-08-22 21:10:00.123456 UTC' -> datetime aware (UTC)."""
    if not ts:
        return None
    try:
        base = str(ts).rsplit(" ", 1)[0]
        return datetime.strptime(base, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def liberados(config=None):
    """Qué hay liberado en el exchange para este curso, según el servicio.

    Devuelve {assignment_id: {"timestamp": str, "publicado_en": datetime,
    "notebooks": [nombre sin .ipynb, ...]}} con la liberación MÁS RECIENTE de
    cada tarea. Lo que el servicio marcó como retirado ("unreleased") no viene.

    También devuelve, aparte, las entregas del propio usuario:
    {assignment_id: timestamp de la última entrega}. Para el alumno es la
    constancia de que el docente ya tiene su cuadernillo; para el docente,
    nada (él no entrega).
    """
    config = config if config is not None else cargar_config()
    lister = _exchange(ExchangeList, config)
    acciones = lister.query_exchange() or []
    liberadas, entregadas = {}, {}
    for a in acciones:
        aid = str(a.get("assignment_id", ""))
        ts = str(a.get("timestamp", ""))
        if not aid:
            continue
        if a.get("status") == "released":
            if aid not in liberadas or ts > liberadas[aid]["timestamp"]:
                liberadas[aid] = {
                    "timestamp": ts,
                    "publicado_en": _fecha(ts),
                    "notebooks": [str(n.get("notebook_id", ""))
                                  for n in a.get("notebooks") or []],
                }
        elif a.get("status") == "submitted":
            if ts > entregadas.get(aid, ""):
                entregadas[aid] = ts
    return liberadas, entregadas


def entregas_en_exchange(assignment_id, config=None):
    """Qué entregas de `assignment_id` tiene el servicio (solo docente).

    Devuelve {student_id: timestamp de la última entrega}. Es lo que «Collect»
    traería a submitted/. Lanza ExchangeError si el servicio no responde o no
    reconoce al que pregunta como docente.
    """
    config = config if config is not None else cargar_config()
    ex = _exchange(Exchange, config, assignment_id)
    from urllib.parse import quote_plus
    r = ex.api_request(f"collections?course_id={quote_plus(CURSO)}"
                       f"&assignment_id={quote_plus(assignment_id)}")
    try:
        datos = r.json()
    except ValueError:
        raise ExchangeError(f"Respuesta ilegible del servicio: {r.text[:120]}")
    if not datos.get("success"):
        raise ExchangeError(datos.get("note") or "El servicio no devolvió entregas")
    entregas = {}
    for e in datos.get("value") or []:
        sid, ts = str(e.get("student_id", "")), str(e.get("timestamp", ""))
        if sid and ts > entregas.get(sid, ""):
            entregas[sid] = ts
    return entregas


def descargar(assignment_id, destino, config=None):
    """Trae la última liberación de `assignment_id` a la carpeta `destino`.

    `destino` queda con el contenido de release/<tarea>/ tal como lo liberó el
    docente: el/los .ipynb y, si publicó con ventana, `ava_publicacion.json`.
    Devuelve la ruta donde quedó. Lanza ExchangeError si no se pudo.
    """
    config = config if config is not None else cargar_config()
    raiz = tempfile.mkdtemp(prefix="ava-fetch-")
    try:
        fetcher = _exchange(ExchangeFetchAssignment, config, assignment_id,
                            assignment_dir=raiz, path_includes_course=False,
                            replace_missing_files=True)
        fetcher.start()
        origen = os.path.join(raiz, assignment_id)
        if os.path.isdir(destino):
            shutil.rmtree(destino)
        shutil.copytree(origen, destino)
        return destino
    finally:
        shutil.rmtree(raiz, ignore_errors=True)


def liberar(assignment_id, config=None):
    """`nbgrader release_assignment` contra el servicio (docente).

    Si la tarea ya estaba liberada, primero se retira. No es cosmético: el
    servicio (2.0.2) registra los notebooks de cada liberación con una clave
    única por tarea, y volver a liberar sin retirar choca con ella DESPUÉS de
    haber respondido «Released»: el cliente cree que publicó y el servicio no
    guardó nada. Retirar y liberar es lo que hace el propio formgrader
    (unrelease → release); las entregas ya recibidas no se tocan.
    """
    config = config if config is not None else cargar_config()
    liberadas, _ = liberados(config)
    if assignment_id in liberadas:
        retirar(assignment_id, config)
    _exchange(ExchangeReleaseAssignment, config, assignment_id).start()


def retirar(assignment_id, config=None):
    """Deja de ofrecer la tarea a los alumnos (docente). No borra entregas."""
    config = config if config is not None else cargar_config()
    lister = _exchange(ExchangeList, config, assignment_id)
    lister.remove = True
    lister.start()


def entregar(assignment_id, archivos, config=None):
    """Manda al docente los `archivos` como entrega de `assignment_id` (alumno).

    `archivos` es {nombre_en_nbgrader: ruta_local}. El nombre tiene que ser el
    del notebook que liberó el docente (p.ej. cuadernillo.ipynb): nbgrader
    identifica el notebook por su nombre de archivo al calificar.
    """
    config = config if config is not None else cargar_config()
    raiz = tempfile.mkdtemp(prefix="ava-submit-")
    try:
        carpeta = os.path.join(raiz, assignment_id)
        os.makedirs(carpeta)
        for nombre, ruta in archivos.items():
            shutil.copyfile(ruta, os.path.join(carpeta, nombre))
        submit = _exchange(ExchangeSubmit, config, assignment_id,
                           assignment_dir=raiz, path_includes_course=False,
                           strict=False)
        submit.start()
        return submit.timestamp
    finally:
        shutil.rmtree(raiz, ignore_errors=True)


def leer_publicacion(carpeta):
    """La ventana de tiempo que el docente puso al publicar, si la puso."""
    try:
        with open(os.path.join(carpeta, FICHERO_PUBLICACION), encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


__all__ = [
    "AutenticacionJupyterHub", "ExchangeError",
    "Exchange", "ExchangeList", "ExchangeFetchAssignment", "ExchangeSubmit",
    "ExchangeCollect", "ExchangeReleaseAssignment", "ExchangeReleaseFeedback",
    "ExchangeFetchFeedback",
    "cargar_config", "liberados", "entregas_en_exchange", "descargar", "liberar",
    "retirar", "entregar",
    "leer_publicacion", "FICHERO_PUBLICACION", "URL_SERVICIO",
]
