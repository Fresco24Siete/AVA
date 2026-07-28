import json
import logging
import os

from tornado import web
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

# tornado.web.RequestHandler NO tiene self.log (a diferencia del handler base de
# notebook 6). Con jupyter_server hay que usar un logger propio, si no cada POST
# revienta con AttributeError -> 500 y se pierde el evento.
log = logging.getLogger("metrics_bridge")

# ---------------------------------------------------------------------------
# Identidad congelada al arrancar la extensión.
#
# Se leen las variables UNA vez, al cargar el módulo, y no en cada request.
# El kernel del notebook es un proceso aparte, así que un os.environ[...] = ...
# dentro de una celda no afecta a este proceso; congelarlas es defensa en
# profundidad, no la protección principal.
#
# La protección real es del lado del backend: el token de STUDENT_METRICS_TOKEN
# viene acotado a un estudiante/curso concreto, así que el backend debe tomar la
# identidad de los claims del token e IGNORAR estos campos del body. Un alumno
# con acceso a terminal puede leer su propio token y hacer POST a mano.
# ---------------------------------------------------------------------------
# Identidad en inglés, alineada al contrato de la sección 5/6 (course_id,
# student_id, cuadernillo_id). La pone el SERVIDOR desde el contexto LTI; el
# cliente nunca la manda.
IDENTIDAD = {
    "student_id": os.environ.get("ALUMNO_ID"),
    "student_name": os.environ.get("ALUMNO_NOMBRE"),
    "student_email": os.environ.get("ALUMNO_EMAIL"),
    "course_id": os.environ.get("CURSO_ID"),
    # El backend entrega un CÓDIGO de negocio, no un id numérico.
    "cuadernillo_id": os.environ.get("CUADERNILLO_CODIGO")
                      or os.environ.get("CUADERNILLO_ID"),
}

# Ruteo por tipo de evento hacia los endpoints del backend (sección 5).
RUTAS_BACKEND = {
    "exercise_attempt": "/api/exercises/attempts",
    "cuadernillo_rating": "/api/cuadernillos/ratings",
}


def _url_backend(tipo_evento):
    """Arma la URL destino según el tipo de evento. Devuelve None si el tipo no
    tiene ruta conocida."""
    ruta = RUTAS_BACKEND.get(tipo_evento)
    if ruta is None:
        return None
    # Base configurable; por defecto el servicio interno. Se acepta también la
    # variable vieja STUDENT_METRICS_API_URL (se le quita el path si lo trae).
    base = os.environ.get("STUDENT_METRICS_API_BASE")
    if not base:
        vieja = os.environ.get("STUDENT_METRICS_API_URL", "")
        base = vieja.split("/public/")[0].split("/api/")[0] if vieja else "http://backend_go:8080"
    return base.rstrip("/") + ruta


class MetricsEventoHandler(web.RequestHandler):

    def check_xsrf_cookie(self):
        # Endpoint interno de telemetría, mismo origen, dentro del propio server
        # del alumno. jupyter_server (ServerApp) aplica XSRF y rechazaba el POST
        # con 403 ('_xsrf argument missing'), perdiendo el 100% de la telemetría.
        # La protección real de este flujo es el token Bearer que metrics_bridge
        # usa al reenviar al backend, no el XSRF de esta llamada local. Por eso
        # se exime este handler del chequeo.
        return

    async def post(self):
        try:
            evento = json.loads(self.request.body)
        except Exception:
            self.set_status(400)
            self.finish(json.dumps({"error": "json invalido"}))
            return

        enviar_backend = os.environ.get("ENVIAR_AL_BACKEND", "false").lower() in ("true", "1", "yes")

        # La identidad la pone el servidor, nunca el cliente.
        evento.update(IDENTIDAD)

        # tipo_evento es solo el discriminador de ruteo; no forma parte del
        # payload de la sección 5, así que se saca antes de reenviar.
        tipo_evento = evento.pop("tipo_evento", None)
        api_url = _url_backend(tipo_evento)

        if not enviar_backend:
            log.info(
                "[metrics_bridge] ENVIAR_AL_BACKEND=false (Simulación). Evento '%s' -> %s:\n%s",
                tipo_evento, api_url or "(sin ruta)",
                json.dumps(evento, indent=2, ensure_ascii=False)
            )
            self.set_status(200)
            self.finish(json.dumps({"status": "simulado", "enviado": False}))
            return

        if api_url is None:
            log.error("Tipo de evento desconocido '%s'; evento DESCARTADO.", tipo_evento)
            self.set_status(400)
            self.finish(json.dumps({"status": "tipo_desconocido", "enviado": False}))
            return

        token = os.environ.get("STUDENT_METRICS_TOKEN")
        if not token:
            log.error(
                "STUDENT_METRICS_TOKEN no configurado; evento DESCARTADO. "
                "Revisa el mint de token en jupyterhub_config.py."
            )
            self.set_status(503)
            self.finish(json.dumps({"status": "sin_configurar", "enviado": False}))
            return

        # Petición asíncrona: con requests.post (síncrono) cada ejecución de una
        # celda de prueba congelaba el servidor Jupyter del alumno hasta 5s.
        req = HTTPRequest(
            url=api_url,
            method="POST",
            body=json.dumps(evento),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            request_timeout=5,
        )

        try:
            resp = await AsyncHTTPClient().fetch(req, raise_error=False)
        except Exception as exc:
            log.error("No se pudo reenviar evento de métricas: %s", exc)
            self.set_status(502)
            self.finish(json.dumps({"status": "error_red", "enviado": False}))
            return

        if resp.code >= 300:
            cuerpo = (resp.body or b"")[:500].decode("utf-8", "replace")
            log.error(
                "Backend rechazó el evento de métricas: %s %s", resp.code, cuerpo
            )
            self.set_status(502)
            self.finish(json.dumps({"status": "rechazado", "codigo": resp.code}))
            return

        self.set_status(204)
        self.finish()


def _add_route(web_app):
    base_url = web_app.settings.get("base_url", "/")
    route = base_url.rstrip("/") + "/nbgrader-metrics/evento"
    web_app.add_handlers(".*$", [(route, MetricsEventoHandler)])


def _usar_logger_del_app(app):
    # Reemplaza el logger de módulo por el del server (que sí tiene handler a
    # INFO), para que el "Evento capturado" y los errores aparezcan en el log.
    global log
    if getattr(app, "log", None) is not None:
        log = app.log


def load_jupyter_server_extension(nbapp):
    _usar_logger_del_app(nbapp)
    _add_route(nbapp.web_app)


def _load_jupyter_server_extension(server_app):
    _usar_logger_del_app(server_app)
    _add_route(server_app.web_app)


def _jupyter_server_extension_points():
    return [{"module": "metrics_bridge"}]
