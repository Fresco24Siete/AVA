import json
import os

from tornado import web
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

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
IDENTIDAD = {
    "estudiante_id": os.environ.get("ALUMNO_ID"),
    "nombre_completo": os.environ.get("ALUMNO_NOMBRE"),
    "correo": os.environ.get("ALUMNO_EMAIL"),
    "curso_id": os.environ.get("CURSO_ID"),
    # El backend entrega un CÓDIGO de negocio, no un id numérico.
    "cuadernillo_codigo": os.environ.get("CUADERNILLO_CODIGO")
                          or os.environ.get("CUADERNILLO_ID"),
}


class MetricsEventoHandler(web.RequestHandler):

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

        if not enviar_backend:
            self.log.info(
                "[metrics_bridge] ENVIAR_AL_BACKEND=false (Simulación activada). Evento capturado:\n%s",
                json.dumps(evento, indent=2, ensure_ascii=False)
            )
            self.set_status(200)
            self.finish(json.dumps({"status": "simulado", "enviado": False}))
            return

        api_url = os.environ.get("STUDENT_METRICS_API_URL")
        token = os.environ.get("STUDENT_METRICS_TOKEN")
        if not api_url or not token:
            self.log.error(
                "STUDENT_METRICS_API_URL/TOKEN no configurados; evento DESCARTADO. "
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
            self.log.error("No se pudo reenviar evento de métricas: %s", exc)
            self.set_status(502)
            self.finish(json.dumps({"status": "error_red", "enviado": False}))
            return

        if resp.code >= 300:
            cuerpo = (resp.body or b"")[:500].decode("utf-8", "replace")
            self.log.error(
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


def load_jupyter_server_extension(nbapp):
    _add_route(nbapp.web_app)


def _load_jupyter_server_extension(server_app):
    _add_route(server_app.web_app)


def _jupyter_server_extension_points():
    return [{"module": "metrics_bridge"}]
