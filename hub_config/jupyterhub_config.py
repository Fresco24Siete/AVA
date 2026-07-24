import os
import json

# httpx viene instalado en Dockerfile.hub. Antes había un camino alterno con
# urllib.request para cuando faltaba, pero era código muerto y además hacía I/O
# bloqueante dentro de un hook async (congelaba el Hub entero para todos los
# usuarios). Si falta httpx preferimos fallar ruidosamente al construir.
import httpx

from ltiauthenticator.lti11.auth import LTI11Authenticator

c = get_config()

c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
c.DockerSpawner.image = 'mi_imagen_jupyterlab:latest'

network_name = os.environ.get('DOCKER_NETWORK_NAME', 'bridge')
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name
c.DockerSpawner.remove = False

# --- Volúmenes -------------------------------------------------------------
# Por defecto NINGÚN contenedor monta el volumen compartido de nbgrader.
# El montaje se decide por rol dentro de auth_state_a_env(): solo el instructor
# lo recibe. Un estudiante que monte /srv/nbgrader puede leer las soluciones
# maestras (source/) y los envíos de sus compañeros (exchange/) con solo abrir
# el explorador de archivos.
c.DockerSpawner.volumes = {}

NBGRADER_VOLUMEN = {'nbgrader_shared': '/srv/nbgrader'}

# Cuadernillo por defecto si el backend no responde o aún no hay uno activo.
CUADERNILLO_FALLBACK = 'cuadernillo_ejercicios.ipynb'


# --- Autenticador LTI con enrutamiento de roles -----------------------------
class LTIRoleAuthenticator(LTI11Authenticator):
    """
    Extiende LTI11Authenticator para:
      1. Determinar si el usuario es instructor o estudiante según el claim
         'roles' que manda el LMS.
      2. Marcarlo como admin del Hub si es instructor (nbgrader lo exige para
         mostrar el formgrader).
      3. Asignarlo al grupo de JupyterHub correspondiente, por si más adelante
         quieres usar JupyterHubAuthPlugin de nbgrader (grupos
         'formgrade-<curso_id>' / 'nbgrader-<curso_id>').
    """
    manage_groups = True

    async def authenticate(self, handler, data=None):
        auth_model = await super().authenticate(handler, data)
        if auth_model is None:
            return None

        auth_state = auth_model.get('auth_state') or {}
        roles = str(auth_state.get('roles', '')).lower()
        curso_id = str(auth_state.get('context_id', 'curso_default'))

        es_instructor = any(
            rol in roles for rol in ['instructor', 'teachingassistant', 'admin']
        )

        auth_model['admin'] = es_instructor
        auth_model['groups'] = [
            f"formgrade-{curso_id}" if es_instructor else f"nbgrader-{curso_id}"
        ]
        return auth_model


c.JupyterHub.authenticator_class = LTIRoleAuthenticator
c.Authenticator.allow_all = True

# Credenciales LTI desde el entorno. Los valores por defecto son SOLO para
# desarrollo local; en despliegue hay que exportar LTI_CLIENT_KEY y
# LTI_CLIENT_SECRET (y JUPYTERHUB_CRYPT_KEY) desde un .env fuera de git.
_lti_key = os.environ.get('LTI_CLIENT_KEY', 'moodle-llave-publica')
_lti_secret = os.environ.get('LTI_CLIENT_SECRET')
if not _lti_secret:
    _lti_secret = 'secreto-super-seguro-000000'
    print('[jupyterhub_config] AVISO: LTI_CLIENT_SECRET no definido; '
          'usando el secreto de desarrollo. NO usar así en producción.')

c.LTI11Authenticator.consumers = {_lti_key: _lti_secret}
c.LTI11Authenticator.username_key = 'lis_person_contact_email_primary'
c.Authenticator.enable_auth_state = True


async def _resolver_cuadernillo_activo(curso_id, headers, spawner):
    """Pregunta al backend qué cuadernillo está activo AHORA para este curso.

    Devuelve (codigo, archivo). Ante cualquier fallo devuelve ('', '') y el
    llamador aplica el fallback estático.
    """
    base = os.environ.get('CUADERNILLO_ACTIVO_URL',
                          'http://backend_go:8080/internal/cursos')
    url = f'{base}/{curso_id}/cuadernillo-activo'
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            spawner.log.warning(
                'Cuadernillo activo: backend respondió %s para %s',
                resp.status_code, curso_id)
            return '', ''
        data = resp.json()
        # 'notebook_archivo' es opcional: permite que el código de negocio
        # ("semana_1") no tenga que coincidir con el nombre del .ipynb.
        return data.get('cuadernillo_codigo', ''), data.get('notebook_archivo', '')
    except Exception as exc:
        spawner.log.warning('No se pudo resolver el cuadernillo activo: %s', exc)
        return '', ''


async def _mintear_token_estudiante(auth_state, curso_id, cuadernillo_codigo, spawner):
    """Pide al backend un token de métricas acotado a este estudiante."""
    url = os.environ.get('METRICS_MINT_URL',
                         'http://backend_go:8080/internal/lti/mint-metrics-token')
    master_token = os.environ.get('METRICS_API_TOKEN', '')
    payload = {
        'estudiante_id': str(auth_state.get('user_id', '')),
        'curso_id': curso_id,
        'cuadernillo_codigo': cuadernillo_codigo,
    }
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.post(
            url,
            json=payload,
            headers={'Authorization': f'Bearer {master_token}'},
        )
    if resp.status_code != 200:
        raise RuntimeError(
            f'mint-metrics-token respondió {resp.status_code}: {resp.text[:200]}')
    token = resp.json().get('token', '')
    if not token:
        raise RuntimeError('mint-metrics-token respondió 200 pero sin campo "token"')
    return token


# --- Variables de entorno + ruteo del contenedor según rol ------------------
async def auth_state_a_env(spawner, auth_state):
    if not auth_state:
        return

    curso_id = str(auth_state.get('context_id', 'curso_default'))
    roles = str(auth_state.get('roles', '')).lower()
    es_instructor = any(
        rol in roles for rol in ['instructor', 'teachingassistant', 'admin']
    )

    spawner.environment['ALUMNO_ID']      = str(auth_state.get('user_id', ''))
    spawner.environment['ALUMNO_NOMBRE']  = str(auth_state.get('lis_person_name_full', ''))
    spawner.environment['ALUMNO_EMAIL']   = str(auth_state.get('lis_person_contact_email_primary', ''))
    spawner.environment['ALUMNO_ROL']     = 'instructor' if es_instructor else 'estudiante'
    spawner.environment['CURSO_ID']       = curso_id
    spawner.environment['CURSO_NOMBRE']   = str(auth_state.get('context_title', ''))
    spawner.environment['ENVIAR_AL_BACKEND'] = os.environ.get('ENVIAR_AL_BACKEND', 'false')

    # Solo el instructor monta el volumen con soluciones y envíos.
    spawner.volumes = dict(NBGRADER_VOLUMEN) if es_instructor else {}

    headers = {'Authorization': f"Bearer {os.environ.get('METRICS_API_TOKEN', '')}"}
    cuadernillo_codigo, cuadernillo_archivo = await _resolver_cuadernillo_activo(
        curso_id, headers, spawner)

    # CUADERNILLO_CODIGO es el nombre canónico (el backend devuelve un CÓDIGO
    # de negocio, no un id numérico). CUADERNILLO_ID se mantiene por
    # compatibilidad con notebooks/plugins que aún lo lean.
    spawner.environment['CUADERNILLO_CODIGO'] = cuadernillo_codigo
    spawner.environment['CUADERNILLO_ID']     = cuadernillo_codigo

    if es_instructor:
        spawner.environment['METRICS_API_URL'] = os.environ.get(
            'METRICS_API_URL', 'http://backend_go:8080/internal/metrics'
        )
        spawner.environment['METRICS_API_TOKEN'] = os.environ.get('METRICS_API_TOKEN', '')
    else:
        # El alumno debe quedarse en el notebook clásico. Sin esto, JupyterHub
        # arranca SingleUserLabApp (JupyterLab) y el alumno puede irse a /lab,
        # abrir un explorador de archivos completo y una terminal.
        spawner.environment['JUPYTERHUB_SINGLEUSER_APP'] = os.environ.get(
            'SINGLEUSER_APP', 'nbclassic.notebookapp.NotebookApp'
        )

        # El Hub puede recibir la URL con cualquiera de los dos nombres; dentro
        # del contenedor del alumno siempre se llama STUDENT_METRICS_API_URL.
        spawner.environment['STUDENT_METRICS_API_URL'] = (
            os.environ.get('STUDENT_METRICS_API_URL')
            or os.environ.get('STUDENT_METRICS_EVENT_URL')
            or 'http://backend_go:8080/public/metrics/evento'
        )

        try:
            spawner.environment['STUDENT_METRICS_TOKEN'] = await _mintear_token_estudiante(
                auth_state, curso_id, cuadernillo_codigo, spawner)
        except Exception as exc:
            # Sin token, el 100% de la telemetría de esta sesión se descarta.
            # Es un fallo grave, no un warning: que se vea en los logs.
            spawner.log.error('No se pudo mintear STUDENT_METRICS_TOKEN: %s', exc)
            spawner.environment['STUDENT_METRICS_TOKEN'] = ''

            # Política configurable: si la telemetría es obligatoria, abortar el
            # spawn en vez de dejar al alumno trabajar sin que se registre nada.
            if os.environ.get('METRICS_REQUERIDO', 'false').lower() in ('true', '1', 'yes'):
                raise RuntimeError(
                    'No se pudo emitir el token de métricas y METRICS_REQUERIDO=true. '
                    'Intenta de nuevo en unos minutos o avisa al docente.'
                ) from exc

    if es_instructor:
        spawner.default_url = '/formgrader'
    else:
        # El destino debe seguir al cuadernillo activo que reportó el backend;
        # si se deja fijo, CUADERNILLO_CODIGO dice una cosa y el alumno abre otra.
        archivo = cuadernillo_archivo or (
            f'{cuadernillo_codigo}.ipynb' if cuadernillo_codigo else CUADERNILLO_FALLBACK
        )
        spawner.default_url = f'/notebooks/work/{archivo}'

c.Spawner.auth_state_hook = auth_state_a_env

# --- Tiempos de arranque --------------------------------------------------
# La VM es una e2-micro (2 vCPU compartidas, 1 GB RAM). El servidor de usuario
# arranca bien pero tarda: con el default de 30 s el Hub lo mataba (Exit 137)
# antes de que respondiera a /api. Se suben los márgenes. Si algún día se pasa
# a una máquina más holgada, se pueden bajar de nuevo.
c.Spawner.start_timeout = 300   # espera a que el contenedor arranque
c.Spawner.http_timeout = 120    # espera a que el server responda tras arrancar

c.JupyterHub.default_url = '/hub/spawn'

c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 8000

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_connect_ip = 'jupyterhub'
