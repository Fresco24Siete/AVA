import os
import httpx
from ltiauthenticator.lti11.auth import LTI11Authenticator

c = get_config()

c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
c.DockerSpawner.image = 'mi_imagen_jupyterlab:latest'

network_name = os.environ.get('DOCKER_NETWORK_NAME', 'bridge')
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name
c.DockerSpawner.remove = False

# --- Volumen compartido de nbgrader ---------------------------------------
# Todos los contenedores (instructor y estudiantes) montan el mismo volumen,
# porque cada lanzamiento LTI crea un contenedor nuevo y no una cuenta Unix
# persistente. Dentro se organiza por curso: /srv/nbgrader/<curso_id>/...
c.DockerSpawner.volumes = {
    'nbgrader_shared': '/srv/nbgrader',
}


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

c.LTI11Authenticator.consumers = {
    "moodle-llave-publica": "secreto-super-seguro-000000"
}
c.LTI11Authenticator.username_key = 'lis_person_contact_email_primary'
c.Authenticator.enable_auth_state = True


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

    # El cuadernillo activo lo decide el instructor (vía tu backend, no en
    # Moodle -- así puede cambiarlo sin tocar la actividad LTI). Se resuelve
    # en cada login preguntándole al backend cuál está activo AHORA para
    # este curso.
    cuadernillo_id = ''
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                os.environ.get(
                    'CUADERNILLO_ACTIVO_URL',
                    'http://backend_go:8080/internal/cursos'
                ) + f'/{curso_id}/cuadernillo-activo',
                headers={'Authorization': f"Bearer {os.environ.get('METRICS_API_TOKEN', '')}"},
            )
            if resp.status_code == 200:
                cuadernillo_id = resp.json().get('cuadernillo_codigo', '')
    except Exception as exc:
        spawner.log.warning(f"No se pudo resolver el cuadernillo activo: {exc}")

    spawner.environment['CUADERNILLO_ID'] = cuadernillo_id

    # SOLO el contenedor del instructor necesita hablar con el backend para
    # exportar métricas -- y ni siquiera con credenciales de Postgres, sino
    # con un token de servicio hacia un endpoint interno de tu API Go.
    # Los estudiantes NO reciben ningún secreto (tienen shell propia y no
    # deben poder llegar a la base de datos ni al backend directamente).
    if es_instructor:
        spawner.environment['METRICS_API_URL'] = os.environ.get(
            'METRICS_API_URL', 'http://backend_go:8080/internal/metrics'
        )
        spawner.environment['METRICS_API_TOKEN'] = os.environ.get('METRICS_API_TOKEN', '')
    else:
        # Telemetría en tiempo real (errores por celda + tiempos). El Hub
        # llama a tu backend con el token MAESTRO para pedir uno escaneado
        # (corta duración, solo válido para este estudiante+cuadernillo).
        # Ese token escaneado, y SOLO ese, es lo que entra al contenedor del
        # estudiante -- si se filtra, el daño posible está acotado a mandar
        # eventos falsos de un cuadernillo, no a leer ni escribir notas.
        spawner.environment['STUDENT_METRICS_API_URL'] = os.environ.get(
            'STUDENT_METRICS_EVENT_URL', 'http://backend_go:8080/public/metrics/evento'
        )
        try:
            master_url = os.environ.get('METRICS_MINT_URL',
                                         'http://backend_go:8080/internal/lti/mint-metrics-token')
            master_token = os.environ.get('METRICS_API_TOKEN', '')
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    master_url,
                    json={
                        'estudiante_id': str(auth_state.get('user_id', '')),
                        'curso_id': curso_id,
                        'cuadernillo_id': spawner.environment.get('CUADERNILLO_ID', ''),
                    },
                    headers={'Authorization': f'Bearer {master_token}'},
                )
                resp.raise_for_status()
                spawner.environment['STUDENT_METRICS_TOKEN'] = resp.json().get('token', '')
        except Exception as exc:
            # Si el backend no responde, el estudiante igual puede trabajar;
            # solo se pierde la telemetría en tiempo real de esta sesión.
            spawner.log.warning(f"No se pudo mintear STUDENT_METRICS_TOKEN: {exc}")
            spawner.environment['STUDENT_METRICS_TOKEN'] = ''

    if es_instructor:
        # El instructor entra directo al formgrader de SU curso.
        spawner.default_url = '/formgrader'
    else:
        # El estudiante entra directo al cuadernillo activo. El nombre del
        # archivo lo resuelve entrypoint.sh (copia/enlaza el release correcto
        # a work/cuadernillo_actual.ipynb antes de levantar el servidor).
        spawner.default_url = '/notebooks/work/cuadernillo_actual.ipynb'

c.Spawner.auth_state_hook = auth_state_a_env

c.JupyterHub.default_url = '/hub/spawn'

# El Hub debe escuchar en todas las interfaces internas del contenedor
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 8000

# El Hub API también debe ser accesible internamente
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_connect_ip = 'jupyterhub'