"""Acciones de administración del docente que nbgrader no ofrece.

Hoy solo una: **eliminar una actividad**. Formgrader no tiene ningún botón para
eso —lo más parecido es «unrelease», que solo vacía el buzón y no borra nada—,
así que la única vía era entrar al servidor y borrar carpetas a mano. Es
exactamente el tipo de operación donde se borra lo que no era.

La lógica vive en `borrar_cuadernillo.py`, el mismo módulo que usa el comando de
terminal: una sola implementación, con su respaldo y su protección de los envíos
de los estudiantes.

**Solo se registra en el contenedor del instructor.** El del alumno ni siquiera
monta el volumen de nbgrader, pero la comprobación de rol se hace igual: una
ruta que borra carpetas no debe existir en el entorno del estudiante ni por
accidente.
"""
import json
import logging
import os

from tornado import web

log = logging.getLogger(__name__)

ES_INSTRUCTOR = os.environ.get("ALUMNO_ROL", "estudiante") == "instructor"


class _Base(web.RequestHandler):
    def check_xsrf_cookie(self):
        # Lo llama el JS de formgrader, que no lleva el token XSRF de Jupyter.
        # La protección real es que esta ruta solo existe en el contenedor del
        # instructor, que es de una sola persona y está tras la sesión del Hub.
        return

    def _responder(self, codigo, cuerpo):
        self.set_status(codigo)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.finish(json.dumps(cuerpo, ensure_ascii=False))


class ActividadesHandler(_Base):
    """GET: qué actividades hay y cuáles tienen envíos de alumnos."""

    def get(self):
        import borrar_cuadernillo as bc

        fuente = os.path.join(bc.RAIZ, "source")
        if not os.path.isdir(fuente):
            self._responder(200, {"actividades": []})
            return

        actividades = []
        for tarea in sorted(os.listdir(fuente)):
            if not os.path.isdir(os.path.join(fuente, tarea)):
                continue
            actividades.append({"id": tarea, "envios": bc._envios(tarea)})
        self._responder(200, {"actividades": actividades})


class BorrarHandler(_Base):
    """POST {"tarea": "...", "forzar": false}"""

    def post(self):
        import borrar_cuadernillo as bc

        try:
            entrada = json.loads(self.request.body.decode("utf-8") or "{}")
        except ValueError:
            self._responder(400, {"error": "El cuerpo no es JSON válido."})
            return

        tarea = str(entrada.get("tarea", "")).strip()
        # El nombre viene del navegador y termina en una ruta de disco: se acota
        # a un nombre de carpeta simple. Sin esto, '../..' borraría otra cosa.
        if not tarea or "/" in tarea or "\\" in tarea or tarea.startswith("."):
            self._responder(400, {"error": "Nombre de actividad no válido."})
            return

        ok, mensajes = bc.borrar(tarea, forzar=bool(entrada.get("forzar")))
        self._responder(200 if ok else 409, {"ok": ok, "mensajes": mensajes})


def _add_routes(web_app):
    raiz = web_app.settings.get("base_url", "/").rstrip("/")
    web_app.add_handlers(".*$", [
        (raiz + "/ava-admin/actividades", ActividadesHandler),
        (raiz + "/ava-admin/borrar", BorrarHandler),
    ])


def load_jupyter_server_extension(nbapp):
    if getattr(nbapp, "log", None) is not None:
        globals()["log"] = nbapp.log
    if not ES_INSTRUCTOR:
        log.info("[admin_bridge] rol estudiante: no se registran rutas de administración.")
        return
    _add_routes(nbapp.web_app)
    log.info("[admin_bridge] listo: el docente puede eliminar actividades desde formgrader.")


def _load_jupyter_server_extension(server_app):
    load_jupyter_server_extension(server_app)
