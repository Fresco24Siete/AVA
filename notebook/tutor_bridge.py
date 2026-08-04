"""Puente del Tutor IA entre el notebook del alumno y el backend Go.

Mismo patrón que metrics_bridge.py: el navegador NUNCA habla directo con el
backend. El JS del cuadernillo manda {mensaje, contexto} a este puente, y el
puente arma el JSON de `models.ApiMessage` (nombre_estudiante, mensaje,
historial, contexto) y lo reenvía a POST /api/exercise/tutorIA.

Por qué el puente y no un fetch directo desde el JS:

1. La identidad (nombre del estudiante) viene del contexto LTI, que solo existe
   en el entorno del servidor. El cliente no la manda: la pone el servidor.
2. El límite de 5 preguntas por cuadernillo se cuenta AQUÍ. Si viviera en el
   JS (localStorage), cualquier alumno lo reinicia desde la consola del
   navegador en dos segundos.
3. El token del backend no se expone al navegador.

Alcance del límite (importante para quien lea esto después): el contador es
autoritativo dentro del proceso del servidor del alumno, que el kernel NO puede
tocar. Se persiste a disco solo para sobrevivir reinicios, y al recargar se toma
el MÁXIMO entre memoria y archivo, así que borrar el archivo a media sesión no
devuelve preguntas. Aun así, la defensa definitiva es que el backend cuente las
preguntas por (student_id, cuadernillo_id) y rechace la sexta: mismo criterio
que ya está documentado en metrics_bridge.py para STUDENT_METRICS_TOKEN.
"""

import json
import logging
import os

from tornado import web
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

try:
    # Handler con la autenticación de Jupyter/JupyterHub ya integrada.
    from jupyter_server.base.handlers import JupyterHandler as _BaseHandler
except Exception:  # pragma: no cover - notebook 6 sin jupyter_server
    from notebook.base.handlers import IPythonHandler as _BaseHandler

log = logging.getLogger("tutor_bridge")

# ---------------------------------------------------------------------------
# Identidad congelada al arrancar la extensión (igual que metrics_bridge).
# El kernel es otro proceso: un os.environ[...] = ... dentro de una celda no
# afecta a este proceso.
# ---------------------------------------------------------------------------
IDENTIDAD = {
    "student_id": os.environ.get("ALUMNO_ID"),
    "student_name": os.environ.get("ALUMNO_NOMBRE") or "Estudiante",
    "cuadernillo_id": os.environ.get("CUADERNILLO_CODIGO")
                      or os.environ.get("CUADERNILLO_ID")
                      or "sin_cuadernillo",
}

RUTA_TUTOR = "/api/exercise/tutorIA"

# Tope de preguntas por cuadernillo. Bryan lo fijó en 5.
MAX_PREGUNTAS = int(os.environ.get("TUTOR_MAX_PREGUNTAS", "5"))

# Interruptor global. El cuadernillo puede además apagarlo por metadata
# (notebook.metadata.tutor_ia.enabled = false), eso lo mira el JS.
HABILITADO = os.environ.get("TUTOR_IA_HABILITADO", "true").lower() in ("true", "1", "yes")

# Gemini tarda bastante más que un INSERT de telemetría; 5s (el timeout de
# metrics_bridge) cortaría casi todas las respuestas.
TIMEOUT_SEG = float(os.environ.get("TUTOR_TIMEOUT_SEG", "60"))

# Cuánto historial/contexto se deja pasar. Corta prompts gigantes (y facturas
# gigantes) si un alumno pega un archivo entero en el chat.
MAX_MENSAJE = int(os.environ.get("TUTOR_MAX_MENSAJE", "2000"))
MAX_CONTEXTO = int(os.environ.get("TUTOR_MAX_CONTEXTO", "4000"))
MAX_HISTORIAL = int(os.environ.get("TUTOR_MAX_HISTORIAL", "4000"))

# Fuera de root_dir (/home/jovyan/work), así no aparece en el explorador de
# archivos del alumno.
DIR_ESTADO = os.environ.get("TUTOR_ESTADO_DIR", "/home/jovyan/.tutor_ia")
ARCHIVO_ESTADO = os.path.join(DIR_ESTADO, "estado.json")


def _base_backend():
    base = os.environ.get("TUTOR_API_BASE") or os.environ.get("STUDENT_METRICS_API_BASE")
    if not base:
        vieja = os.environ.get("STUDENT_METRICS_API_URL", "")
        base = vieja.split("/public/")[0].split("/api/")[0] if vieja else "http://api_go:8080"
    return base.rstrip("/")


def _recortar(texto, tope):
    # str() a la fuerza: el cuerpo lo manda el cliente y podría traer un número
    # o un objeto donde se espera texto; sin esto reventaría con 500.
    texto = "" if texto is None else str(texto).strip()
    return texto if len(texto) <= tope else texto[:tope] + "\n[...recortado...]"


class _Estado:
    """Contador de preguntas + último turno, por cuadernillo.

    Memoria = autoritativa. Disco = solo para sobrevivir reinicios del server.
    """

    def __init__(self):
        self._mem = {}          # cuadernillo -> {"usadas": int, "historial": str}
        self._ocupado = set()   # cuadernillos con una pregunta en vuelo
        self._cargar()

    def _cargar(self):
        try:
            with open(ARCHIVO_ESTADO, "r", encoding="utf-8") as fh:
                datos = json.load(fh)
            if isinstance(datos, dict):
                for cuadernillo, valor in datos.items():
                    if isinstance(valor, dict):
                        self._mem[cuadernillo] = {
                            "usadas": int(valor.get("usadas", 0)),
                            "historial": str(valor.get("historial", "")),
                        }
        except FileNotFoundError:
            pass
        except Exception as exc:
            log.warning("[tutor_bridge] no se pudo leer el estado previo: %s", exc)

    def _guardar(self):
        try:
            os.makedirs(DIR_ESTADO, exist_ok=True)
            tmp = ARCHIVO_ESTADO + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._mem, fh, ensure_ascii=False)
            os.replace(tmp, ARCHIVO_ESTADO)
        except Exception as exc:
            log.warning("[tutor_bridge] no se pudo persistir el estado: %s", exc)

    def _entrada(self, cuadernillo):
        return self._mem.setdefault(cuadernillo, {"usadas": 0, "historial": ""})

    def usadas(self, cuadernillo):
        return self._entrada(cuadernillo)["usadas"]

    def restantes(self, cuadernillo):
        return max(0, MAX_PREGUNTAS - self.usadas(cuadernillo))

    def historial(self, cuadernillo):
        return self._entrada(cuadernillo)["historial"]

    def registrar_turno(self, cuadernillo, respuesta):
        entrada = self._entrada(cuadernillo)
        entrada["usadas"] += 1
        entrada["historial"] = _recortar(respuesta, MAX_HISTORIAL)
        self._guardar()
        return entrada["usadas"]

    # El servidor del alumno corre en un solo event loop, así que este par
    # tomar/soltar basta para que dos clics rápidos no cuelen 2 preguntas
    # simultáneas saltándose el tope (la condición de carrera que quedaba
    # anotada como pendiente en tutorHub.go).
    def tomar(self, cuadernillo):
        if cuadernillo in self._ocupado:
            return False
        self._ocupado.add(cuadernillo)
        return True

    def soltar(self, cuadernillo):
        self._ocupado.discard(cuadernillo)


ESTADO = _Estado()


class _TutorHandlerBase(_BaseHandler):

    def check_xsrf_cookie(self):
        # Mismo criterio que metrics_bridge: endpoint interno, mismo origen,
        # dentro del propio servidor del alumno. jupyter_server rechazaba estos
        # POST con 403 '_xsrf argument missing'. Aquí el control que importa es
        # @web.authenticated (abajo): sin sesión válida no se gasta cuota de
        # Gemini. El XSRF de una llamada same-origin es un riesgo mucho menor.
        return


class TutorEstadoHandler(_TutorHandlerBase):
    """Cuántas preguntas le quedan al alumno en este cuadernillo."""

    @web.authenticated
    def get(self):
        cuadernillo = IDENTIDAD["cuadernillo_id"]
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps({
            "habilitado": HABILITADO,
            "max": MAX_PREGUNTAS,
            "usadas": ESTADO.usadas(cuadernillo),
            "restantes": ESTADO.restantes(cuadernillo),
            "cuadernillo_id": cuadernillo,
            "nombre_estudiante": IDENTIDAD["student_name"],
        }))


class TutorPreguntaHandler(_TutorHandlerBase):
    """Recibe la pregunta del alumno y la reenvía al backend como ApiMessage."""

    def _responder(self, codigo, cuerpo):
        self.set_status(codigo)
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps(cuerpo, ensure_ascii=False))

    @web.authenticated
    async def post(self):
        if not HABILITADO:
            self._responder(403, {"error": "El tutor IA está deshabilitado en este curso."})
            return

        try:
            entrada = json.loads(self.request.body)
        except Exception:
            self._responder(400, {"error": "json invalido"})
            return

        mensaje = _recortar(entrada.get("mensaje"), MAX_MENSAJE)
        if not mensaje:
            self._responder(400, {"error": "El mensaje viene vacío."})
            return

        cuadernillo = IDENTIDAD["cuadernillo_id"]

        if ESTADO.restantes(cuadernillo) <= 0:
            self._responder(429, {
                "error": "Ya usaste tus %d preguntas de este cuadernillo." % MAX_PREGUNTAS,
                "restantes": 0,
                "usadas": ESTADO.usadas(cuadernillo),
                "max": MAX_PREGUNTAS,
            })
            return

        if not ESTADO.tomar(cuadernillo):
            self._responder(409, {"error": "Espera la respuesta anterior antes de preguntar de nuevo."})
            return

        try:
            # ESTE es el JSON del contrato: models.ApiMessage tal cual.
            # nombre_estudiante e historial los pone el servidor; el cliente
            # solo aporta su pregunta y el contexto del ejercicio.
            api_message = {
                "nombre_estudiante": IDENTIDAD["student_name"],
                "mensaje": mensaje,
                "historial": ESTADO.historial(cuadernillo),
                "contexto": _recortar(entrada.get("contexto"), MAX_CONTEXTO),
            }

            url = _base_backend() + RUTA_TUTOR
            headers = {"Content-Type": "application/json"}
            token = os.environ.get("STUDENT_METRICS_TOKEN")
            if token:
                headers["Authorization"] = "Bearer %s" % token

            req = HTTPRequest(
                url=url,
                method="POST",
                body=json.dumps(api_message, ensure_ascii=False),
                headers=headers,
                request_timeout=TIMEOUT_SEG,
            )

            try:
                resp = await AsyncHTTPClient().fetch(req, raise_error=False)
            except Exception as exc:
                log.error("[tutor_bridge] no se pudo consultar al tutor: %s", exc)
                self._responder(502, {"error": "No se pudo contactar al tutor. Intenta de nuevo."})
                return

            if resp.code >= 300:
                cuerpo = (resp.body or b"")[:500].decode("utf-8", "replace")
                log.error("[tutor_bridge] el backend rechazó la pregunta: %s %s", resp.code, cuerpo)
                self._responder(502, {"error": "El tutor no está disponible en este momento."})
                return

            # El backend ha respondido de las dos formas: antes JSON con
            # {"resultado": "..."} y ahora texto plano (ChatHandler usa
            # c.String). Se aceptan ambas para que un cambio de forma allá no
            # deje al alumno sin tutor.
            cuerpo = (resp.body or b"").decode("utf-8", "replace").strip()
            try:
                datos = json.loads(cuerpo)
            except Exception:
                datos = None

            if isinstance(datos, dict):
                respuesta = (datos.get("resultado") or datos.get("respuesta") or "").strip()
            else:
                respuesta = cuerpo
            if not respuesta:
                log.error("[tutor_bridge] respuesta vacía del backend: %s", (resp.body or b"")[:300])
                self._responder(502, {"error": "El tutor devolvió una respuesta vacía."})
                return

            # Solo se descuenta la pregunta cuando SÍ hubo respuesta: si Gemini
            # o la red fallan, el alumno no pierde una de sus 5.
            usadas = ESTADO.registrar_turno(cuadernillo, respuesta)

            self._responder(200, {
                "respuesta": respuesta,
                "usadas": usadas,
                "restantes": max(0, MAX_PREGUNTAS - usadas),
                "max": MAX_PREGUNTAS,
            })
        finally:
            ESTADO.soltar(cuadernillo)


def _add_routes(web_app):
    base_url = web_app.settings.get("base_url", "/")
    raiz = base_url.rstrip("/")
    # El JS del panel lo sirve la propia extensión. Se probó dejarlo en el
    # directorio custom/, pero que ese directorio se sirva depende de la
    # versión de nbclassic; así la ruta está bajo nuestro control.
    # El patrón fija el nombre del archivo a propósito: con (.*) esta ruta
    # serviría CUALQUIER archivo del directorio (nbgrader_config.py,
    # jupyter_server_config.py, el propio tutor_bridge.py...) a quien pidiera.
    estatico = os.path.dirname(os.path.abspath(__file__))
    web_app.add_handlers(".*$", [
        (raiz + "/tutor-ia/estado", TutorEstadoHandler),
        (raiz + "/tutor-ia/preguntar", TutorPreguntaHandler),
        (raiz + r"/tutor-ia/static/(tutor_ia\.js)", web.StaticFileHandler, {"path": estatico}),
    ])


def _usar_logger_del_app(app):
    global log
    if getattr(app, "log", None) is not None:
        log = app.log


def load_jupyter_server_extension(nbapp):
    _usar_logger_del_app(nbapp)
    _add_routes(nbapp.web_app)
    log.info("[tutor_bridge] listo: %d preguntas por cuadernillo (habilitado=%s)",
             MAX_PREGUNTAS, HABILITADO)


def _load_jupyter_server_extension(server_app):
    load_jupyter_server_extension(server_app)


def _jupyter_server_extension_points():
    return [{"module": "tutor_bridge"}]
