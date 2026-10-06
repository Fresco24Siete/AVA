"""Acciones de administración del docente que nbgrader no ofrece.

Dos cosas:

- **Eliminar una actividad.** Formgrader no tiene ningún botón para eso —lo más
  parecido es «unrelease», que solo vacía el buzón y no borra nada—, así que la
  única vía era entrar al servidor y borrar carpetas a mano. Es exactamente el
  tipo de operación donde se borra lo que no era.
- **Subir las notas al panel.** La nota que calcula «Autograde» se queda en el
  gradebook de nbgrader, que el alumno no ve. Había que ejecutar
  `registrar-notas` en un terminal, y nadie lo hacía: el docente pulsaba
  Autograde y el alumno seguía viendo «aún sin calificar». Ahora el propio
  Autograde de formgrader dispara la subida (se envuelve su handler), y hay un
  botón para repetirla.

La lógica vive en `borrar_cuadernillo.py` y `registrar_notas.py`, los mismos
módulos que usan los comandos de terminal: una sola implementación.

**Solo se registra en el contenedor del instructor.** El del alumno ni siquiera
monta el volumen de nbgrader, pero la comprobación de rol se hace igual: una
ruta que borra carpetas no debe existir en el entorno del estudiante ni por
accidente.
"""
import json
import logging
import os

from tornado import web

try:
    from jupyter_server.base.handlers import JupyterHandler as _BaseHandler
except ImportError:                                   # notebook 6 clásico
    from notebook.base.handlers import IPythonHandler as _BaseHandler

log = logging.getLogger(__name__)

ES_INSTRUCTOR = os.environ.get("ALUMNO_ROL", "estudiante") == "instructor"


class _Base(_BaseHandler):
    # Heredaba de tornado.web.RequestHandler y se saltaba el XSRF, con lo que un
    # POST a /ava-admin/borrar sin sesión borraba source/, release/, el buzón, lo
    # publicado y la ficha del gradebook. El comentario anterior decía que la
    # protección era «la sesión del Hub», pero el Hub solo enruta: quien exige
    # sesión es @web.authenticated, aquí abajo. formgrader_ayuda.js manda ahora
    # la cabecera X-XSRFToken.
    def _responder(self, codigo, cuerpo):
        self.set_status(codigo)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.finish(json.dumps(cuerpo, ensure_ascii=False))


class ActividadesHandler(_Base):
    """GET: qué actividades hay y cuáles tienen envíos de alumnos."""

    @web.authenticated
    def get(self):
        import borrar_cuadernillo as bc

        # Lo que hay en source/ y lo que hay en el gradebook, con su estado:
        # una actividad creada desde formgrader con el nombre mal escrito vive
        # en los dos sitios sin notebook, y tiene que poder borrarse igual.
        actividades = bc.actividades()
        for a in actividades:
            a["calificadas"] = _calificadas(a["id"])
        self._responder(200, {"actividades": actividades})


def _calificadas(tarea):
    """Cuántas entregas de la actividad tienen nota en el gradebook."""
    try:
        import registrar_notas
        return len(registrar_notas._notas(tarea))
    except Exception:
        return 0


class NotasHandler(_Base):
    """POST {"tarea": "..."}: sube al backend las notas del gradebook."""

    @web.authenticated
    def post(self):
        import borrar_cuadernillo as bc
        import registrar_notas

        try:
            entrada = json.loads(self.request.body.decode("utf-8") or "{}")
        except ValueError:
            self._responder(400, {"error": "El cuerpo no es JSON válido."})
            return
        tarea = str(entrada.get("tarea", "")).strip()
        if not bc._nombre_valido(tarea):
            self._responder(400, {"error": "Nombre de actividad no válido."})
            return

        r = registrar_notas.registrar(tarea)
        self._responder(200 if r["ok"] else 409, {
            "ok": r["ok"],
            "guardadas": r["guardadas"],
            "notas": [{"student_id": e, "obtenidos": ob, "maximos": mx}
                      for e, ob, mx in sorted(r["notas"])],
            "avisos": r["avisos"],
            "error": r["error"],
        })


def _subir_notas_en_segundo_plano(tarea):
    """Tras un Autograde: manda las notas sin retener la respuesta a formgrader."""
    import threading

    def _correr():
        try:
            import registrar_notas
            r = registrar_notas.registrar(tarea)
            if r["ok"]:
                log.info("[admin_bridge] notas de '%s' subidas al panel: %d.",
                         tarea, r["guardadas"])
            else:
                log.warning("[admin_bridge] no se subieron las notas de '%s': %s "
                            "(el docente puede repetirlo con «Subir notas»).",
                            tarea, r["error"])
        except Exception:
            log.exception("[admin_bridge] fallo subiendo las notas de '%s'.", tarea)

    threading.Thread(target=_correr, name=f"notas-{tarea}", daemon=True).start()


def _enganchar_autograde():
    """Envuelve el Autograde de formgrader para que, si calificó, suba las notas.

    nbgrader no ofrece ningún gancho «después de calificar»; su handler es una
    línea (`self.write(json.dumps(self.api.autograde(a, s)))`), y la versión de
    nbgrader está fijada en la imagen, así que se reescribe aquí con el envío
    detrás. Si nbgrader cambiara de forma, se avisa y se deja como está: el
    botón «Subir notas» sigue funcionando igual.
    """
    try:
        from nbgrader.server_extensions.formgrader import apihandlers
        Handler = apihandlers.AutogradeHandler
    except Exception as err:                                  # pragma: no cover
        log.warning("[admin_bridge] sin gancho en Autograde (%s): las notas se "
                    "suben con el botón.", err)
        return False

    original = Handler.post
    if getattr(original, "_ava_enganchado", False):
        return True

    def post(self, assignment_id, student_id):
        resultado = self.api.autograde(assignment_id, student_id)
        self.write(json.dumps(resultado))
        if isinstance(resultado, dict) and resultado.get("success"):
            _subir_notas_en_segundo_plano(assignment_id)

    # Conserva los decoradores del original (@web.authenticated, xsrf,
    # check_notebook_dir) envolviendo el cuerpo en vez de la función decorada:
    # tornado aplica los decoradores por fuera, así que se reaplican.
    from nbgrader.server_extensions.formgrader.base import check_notebook_dir, check_xsrf
    nuevo = web.authenticated(check_xsrf(check_notebook_dir(post)))
    nuevo._ava_enganchado = True
    Handler.post = nuevo
    return True


class BorrarHandler(_Base):
    """POST {"tarea": "...", "forzar": false}"""

    @web.authenticated
    def post(self):
        import borrar_cuadernillo as bc

        try:
            entrada = json.loads(self.request.body.decode("utf-8") or "{}")
        except ValueError:
            self._responder(400, {"error": "El cuerpo no es JSON válido."})
            return

        tarea = str(entrada.get("tarea", "")).strip()
        # El nombre viene del navegador y termina en una ruta de disco: se acota
        # a un nombre de carpeta simple (bc.borrar lo vuelve a comprobar).
        if not bc._nombre_valido(tarea):
            self._responder(400, {"error": "Nombre de actividad no válido."})
            return

        ok, mensajes = bc.borrar(tarea, forzar=bool(entrada.get("forzar")))
        self._responder(200 if ok else 409, {"ok": ok, "mensajes": mensajes})


def _add_routes(web_app):
    raiz = web_app.settings.get("base_url", "/").rstrip("/")
    web_app.add_handlers(".*$", [
        (raiz + "/ava-admin/actividades", ActividadesHandler),
        (raiz + "/ava-admin/borrar", BorrarHandler),
        (raiz + "/ava-admin/registrar-notas", NotasHandler),
    ])


def load_jupyter_server_extension(nbapp):
    if getattr(nbapp, "log", None) is not None:
        globals()["log"] = nbapp.log
    if not ES_INSTRUCTOR:
        log.info("[admin_bridge] rol estudiante: no se registran rutas de administración.")
        return
    _add_routes(nbapp.web_app)
    con_gancho = _enganchar_autograde()
    log.info("[admin_bridge] listo: eliminar actividades y subir notas desde "
             "formgrader%s.", " (Autograde las sube solo)" if con_gancho else "")


def _load_jupyter_server_extension(server_app):
    load_jupyter_server_extension(server_app)
