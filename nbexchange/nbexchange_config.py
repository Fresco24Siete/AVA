"""Configuración del servicio nbexchange para el AVA.

nbexchange (github.com/edina/nbexchange) es el almacén por HTTP de lo que antes
hacía el exchange de nbgrader copiando carpetas: el docente libera ahí, el alumno
trae de ahí, el alumno entrega ahí y el docente recoge de ahí. Cada contenedor
habla con él con el token que JupyterHub le dio al arrancar, así que no hace
falta ninguna carpeta compartida entre contenedores.

El servicio no sabe nada de JupyterHub por sí mismo: exige una clase que, dada
una petición, diga quién es el usuario, de qué curso y con qué rol. Eso es
`UsuarioAva`, más abajo. Todo lo demás son rutas y tamaños, que salen del
entorno (ver docker-compose.yml).

Variables de entorno:

  JUPYTERHUB_API_URL     http://jupyterhub:8081/hub/api (la API interna del Hub)
  JUPYTERHUB_API_TOKEN   el api_token con el que el Hub registró este servicio
                         (c.JupyterHub.services en jupyterhub_config.py)
  NBEX_DB_URL            sqlite:////var/nbexchange/nbexchange.sqlite
  NBEX_BASE_STORE        /var/nbexchange/almacen
  NBEX_MAX_BUFFER_SIZE   tope de subida en bytes (default 50 MB)
"""
import logging
import os
import threading
import time
from urllib.parse import quote

import requests
from jupyterhub.services.auth import HubAuth
from tornado import web

from nbexchange.handlers.auth.user_handler import BaseUserHandler

c = get_config()  # noqa: F821  (lo inyecta traitlets al cargar el archivo)

log = logging.getLogger("nbexchange.ava")

# --- Identidad ---------------------------------------------------------------

PREFIJO_DOCENTE = "formgrade-"      # grupos que asigna LTIRoleAuthenticator
PREFIJO_ALUMNO = "nbgrader-"        # (hub_config/jupyterhub_config.py)


class UsuarioAva(BaseUserHandler):
    """Quién llama, de qué curso y con qué rol, según JupyterHub.

    Dos consultas al Hub por petición (las dos con caché):

    1. Con el token que trae la petición —el del servidor de usuario del que
       viene— el Hub dice QUIÉN es (`name`, que es el correo) y a qué GRUPOS
       pertenece. Los grupos los puso el autenticador LTI al entrar:
       `formgrade-<curso>` si Moodle lo mandó como docente, `nbgrader-<curso>`
       si como alumno. De ahí salen curso y rol, y nadie puede falsearlos desde
       dentro del contenedor: el token lo acuñó el Hub.

    2. Con el token PROPIO del servicio, el Hub entrega además el `auth_state`
       del usuario: los datos del lanzamiento LTI. De ahí sale el `user_id`
       numérico de Moodle, que es el nombre con el que el exchange guarda a esa
       persona. Es el mismo identificador con el que se guarda su telemetría y
       su nota (ver jupyterhub_config.py: `ALUMNO_ID`), así que `submitted/`,
       `exercise_attempts` y `cuadernillo_notas` cruzan por la misma clave. Si
       se usara el correo, la nota se registraría bajo un nombre y el panel la
       buscaría por otro.

    Si el Hub no entrega el `auth_state` —el servicio no está registrado, o sin
    el scope `admin:auth_state`— se responde 503 y se dice por qué. Es
    preferible a seguir con el correo y dejar las entregas bajo otro nombre sin
    que nadie lo note.
    """

    # El Hub se consulta mucho (formgrader instancia el exchange en cada
    # petición). Cinco minutos de caché por token y por usuario bastan: un
    # cambio de rol en Moodle ya obliga a reentrar, y eso descarta el
    # contenedor y su token (LTIRoleAuthenticator.authenticate).
    SEGUNDOS_CACHE = 300

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hub = HubAuth()
        self.hub.cache_max_age = self.SEGUNDOS_CACHE
        self.api_url = os.environ.get("JUPYTERHUB_API_URL", "http://jupyterhub:8081/hub/api").rstrip("/")
        self.api_token = os.environ.get("JUPYTERHUB_API_TOKEN", "")
        self._auth_state = {}           # name -> (vence, datos)
        self._candado = threading.Lock()
        if not self.api_token:
            log.error("JUPYTERHUB_API_TOKEN vacío: el servicio no podrá leer el "
                      "auth_state de los usuarios y responderá 503.")

    # -- 1. quién llama, según su propio token ---------------------------------
    def _modelo_hub(self, request):
        try:
            modelo = self.hub.get_user(request)
        except Exception as err:            # el Hub no contesta
            log.error("No se pudo consultar al Hub: %s", err)
            raise web.HTTPError(503, reason="JupyterHub no responde")
        if not modelo or not modelo.get("name"):
            raise web.HTTPError(403, reason="Petición sin token válido de JupyterHub")
        return modelo

    @staticmethod
    def _curso_y_rol(grupos, curso_pedido):
        """De los grupos del Hub, el curso/rol que corresponde a esta petición."""
        cursos = {}
        for g in grupos or []:
            if g.startswith(PREFIJO_DOCENTE):
                cursos[g[len(PREFIJO_DOCENTE):]] = "Instructor"
            elif g.startswith(PREFIJO_ALUMNO):
                cursos.setdefault(g[len(PREFIJO_ALUMNO):], "Student")
        if curso_pedido and curso_pedido in cursos:
            return curso_pedido, cursos[curso_pedido]
        if len(cursos) == 1:
            return next(iter(cursos.items()))
        return None, None

    # -- 2. sus datos de LTI, con el token del servicio --------------------------
    def _auth_state_de(self, nombre):
        ahora = time.time()
        with self._candado:
            vence, datos = self._auth_state.get(nombre, (0, None))
            if vence > ahora:
                return datos
        try:
            r = requests.get(f"{self.api_url}/users/{quote(nombre, safe='')}",
                             headers={"Authorization": f"token {self.api_token}"},
                             timeout=5)
        except requests.RequestException as err:
            log.error("No se pudo pedir al Hub los datos de %s: %s", nombre, err)
            raise web.HTTPError(503, reason="JupyterHub no responde")
        if r.status_code != 200:
            log.error("El Hub respondió %s al pedir /users/%s con el token del "
                      "servicio. ¿Está registrado nbexchange en c.JupyterHub.services "
                      "con el rol 'nbexchange' (read:users, admin:auth_state)?",
                      r.status_code, nombre)
            raise web.HTTPError(503, reason="El servicio no está autorizado en JupyterHub")
        modelo = r.json() or {}
        if "auth_state" not in modelo:
            log.error("El Hub no incluye auth_state para %s: al rol del servicio "
                      "le falta el scope admin:auth_state.", nombre)
            raise web.HTTPError(503, reason="El servicio no puede leer el auth_state")
        datos = modelo.get("auth_state") or {}
        with self._candado:
            self._auth_state[nombre] = (ahora + self.SEGUNDOS_CACHE, datos)
        return datos

    # -- lo que nbexchange espera ----------------------------------------------
    def get_current_user(self, request):
        modelo = self._modelo_hub(request)
        nombre_hub = modelo["name"]
        curso_pedido = request.get_argument("course_id", None)
        curso, rol = self._curso_y_rol(modelo.get("groups"), curso_pedido)
        if not curso:
            log.warning("%s pidió el curso %r y no pertenece a él (grupos: %s)",
                        nombre_hub, curso_pedido, modelo.get("groups"))
            raise web.HTTPError(403, reason="No perteneces a ese curso")

        lti = self._auth_state_de(nombre_hub)
        user_id = str(lti.get("user_id") or "").strip()
        if not user_id:
            # Un usuario del Hub sin lanzamiento LTI (p.ej. creado a mano). No
            # hay con qué cruzarlo con la telemetría; que se note.
            log.error("%s no tiene user_id de LTI en su auth_state", nombre_hub)
            raise web.HTTPError(403, reason="Usuario sin identidad LTI")

        return {
            "name": user_id,
            "full_name": str(lti.get("lis_person_name_full") or ""),
            "email": str(lti.get("lis_person_contact_email_primary") or nombre_hub),
            "lms_user_id": user_id,
            "course_id": curso,
            "course_title": str(lti.get("context_title") or curso),
            "course_role": rol,
            "org_id": 1,
        }


c.NbExchange.user_plugin_class = UsuarioAva

# --- Rutas y tamaños ----------------------------------------------------------

# OJO: el servicio lee la URL de la base en DOS sitios. Los handlers abren el
# motor desde la variable de entorno NBEX_DB_URL al importar el módulo
# (nbexchange/database.py); `c.NbExchange.db_url` solo lo usa el arranque para
# las migraciones. Si solo se pone uno, las migraciones van a una base y las
# peticiones a otra (una SQLite en memoria que se pierde al reiniciar), y no
# falla nada ruidosamente. Por eso los dos salen de la misma variable.
c.NbExchange.db_url = os.environ.get("NBEX_DB_URL", "sqlite:////var/nbexchange/nbexchange.sqlite")
c.NbExchange.base_storage_location = os.environ.get("NBEX_BASE_STORE", "/var/nbexchange/almacen")
c.NbExchange.base_url = os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "/services/nbexchange/")
c.NbExchange.max_buffer_size = int(os.environ.get("NBEX_MAX_BUFFER_SIZE", str(50 * 1024 * 1024)))
c.NbExchange.timezone = "UTC"
c.NbExchange.upgrade_db = True
