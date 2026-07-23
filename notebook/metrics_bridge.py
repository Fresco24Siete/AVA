"""
Puente local: recibe eventos de ejecución de celdas (desde custom.js, mismo
origen que el propio servidor de Jupyter del estudiante) y los reenvía al
backend Go con el token escaneado de ESE estudiante para ESE cuadernillo.

El navegador nunca ve ningún secreto: solo llama a esta ruta local
(/nbgrader-metrics/evento), protegida por la propia sesión/cookie de
Jupyter. Este handler es quien conoce STUDENT_METRICS_TOKEN, leído de una
variable de entorno del contenedor.

Si ENVIAR_AL_BACKEND está en "false" (por defecto), el evento se imprime
bonito en los logs del contenedor para inspección sin fallar por falta de red.
Cuando el backend esté disponible, cambia ENVIAR_AL_BACKEND a "true".
"""
import json
import os

import requests
from tornado import web


class MetricsEventoHandler(web.RequestHandler):

    def post(self):
        try:
            evento = json.loads(self.request.body)
        except Exception:
            self.set_status(400)
            self.finish(json.dumps({"error": "json invalido"}))
            return

        enviar_backend = os.environ.get("ENVIAR_AL_BACKEND", "false").lower() in ("true", "1", "yes")

        evento["estudiante_id"] = os.environ.get("ALUMNO_ID")
        evento["nombre_completo"] = os.environ.get("ALUMNO_NOMBRE")
        evento["correo"] = os.environ.get("ALUMNO_EMAIL")
        evento["curso_id"] = os.environ.get("CURSO_ID")
        evento["cuadernillo_id"] = os.environ.get("CUADERNILLO_ID")

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
            self.log.warning("STUDENT_METRICS_API_URL/TOKEN no configurados; evento descartado")
            self.set_status(204)
            self.finish()
            return

        try:
            requests.post(
                api_url,
                json=evento,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
        except requests.RequestException as exc:
            self.log.warning("No se pudo reenviar evento de métricas: %s", exc)

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