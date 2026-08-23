import os
import json
import sys

# httpx viene instalado en Dockerfile.hub. Antes había un camino alterno con
# urllib.request para cuando faltaba, pero era código muerto y además hacía I/O
# bloqueante dentro de un hook async (congelaba el Hub entero para todos los
# usuarios). Si falta httpx preferimos fallar ruidosamente al construir.
import httpx

from ltiauthenticator.lti11.auth import LTI11Authenticator

c = get_config()

c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
IMAGEN_ALUMNO = os.environ.get('IMAGEN_ALUMNO', 'mi_imagen_jupyterlab:latest')
IMAGEN_DOCENTE = os.environ.get('IMAGEN_DOCENTE', 'mi_imagen_jupyterlab_docente:latest')
c.DockerSpawner.image = IMAGEN_ALUMNO

network_name = os.environ.get('DOCKER_NETWORK_NAME', 'bridge')
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name
# El contenedor se descarta al apagarse. Antes se conservaba, porque era lo
# único que guardaba el trabajo del alumno; desde que cada uno tiene su volumen
# (ava-trabajo-<alumno>, más abajo) el trabajo ya no vive ahí, y conservarlo solo
# traía problemas: el contenedor se quedaba con la imagen y las variables de
# entorno del día que nació, así que reconstruir la imagen o cambiar la
# configuración del Hub no le llegaba a quien ya había entrado alguna vez. Había
# que borrarlo a mano en el servidor para que un arreglo surtiera efecto.
#
# Ahora cada ingreso levanta un contenedor nuevo sobre el mismo volumen: el
# alumno encuentra su trabajo igual que lo dejó y estrena la imagen actual. A
# cambio, lo que instale por su cuenta dentro del contenedor no sobrevive al
# apagado; lo que guarde en su carpeta, sí.
c.DockerSpawner.remove = True

# --- Volúmenes -------------------------------------------------------------
# Por defecto NINGÚN contenedor monta el volumen compartido de nbgrader.
# El montaje se decide por rol dentro de auth_state_a_env(): solo el instructor
# lo recibe. Un estudiante que monte /srv/nbgrader puede leer las soluciones
# maestras (source/) y los envíos de sus compañeros (exchange/) con solo abrir
# el explorador de archivos.
c.DockerSpawner.volumes = {}


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

        # Si el rol cambió desde el último ingreso, hay que TIRAR el contenedor.
        #
        # El Hub, al ver un servidor ya corriendo, redirige a él sin volver a
        # hacer spawn: nunca llega a ejecutarse auth_state_a_env, así que el
        # contenedor sigue con el rol, los montajes y las variables del ingreso
        # anterior. Que el contenedor se descarte al apagarse no basta, porque
        # aquí está encendido.
        #
        # Con el rol de Moodle eso es un problema de seguridad, no de comodidad:
        # el contenedor de instructor monta nbgrader_shared en lectura-escritura
        # —las soluciones y los envíos de todo el curso—, así que un docente que
        # luego entra como estudiante (o alguien a quien le bajan el rol) se los
        # lleva puestos. Al revés falla igual: un estudiante ascendido a monitor
        # no vería el formgrader.
        #
        # `usuario.admin` guarda el rol del ingreso anterior y vive en la base de
        # datos del Hub, así que sobrevive a un reinicio. Comparar contra él es
        # suficiente. Se pierde el trabajo sin guardar de esa sesión, pero solo
        # cuando el rol cambia, que es justo cuando el contenedor no se puede
        # reutilizar.
        usuario = handler.find_user(auth_model['name'])
        if usuario is not None and bool(usuario.admin) != es_instructor:
            self.log.warning(
                "El rol de %s cambió a %s; se descarta su contenedor anterior "
                "para que no conserve los montajes del rol viejo.",
                auth_model['name'], 'instructor' if es_instructor else 'estudiante',
            )
            spawner = usuario.spawner
            if spawner is not None:
                try:
                    if usuario.running:
                        await usuario.stop()
                    await spawner.remove_object()
                except Exception as err:      # no impedir el ingreso por esto
                    self.log.error("No se pudo descartar el contenedor: %s", err)

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


# --- Servicio de intercambio (nbexchange) -------------------------------------
# El exchange de nbgrader por HTTP: el docente libera ahí, el alumno trae de ahí
# y entrega ahí, el docente recoge de ahí. Corre como un contenedor más
# (docker-compose.yml) y se registra como servicio del Hub más abajo. El token
# es el mismo de los dos lados: con él el servicio le pide al Hub quién es cada
# usuario que lo llama. Generarlo: openssl rand -hex 32. Rotarlo: NBEXCHANGE.md.
_NBEXCHANGE_URL = os.environ.get('NBEXCHANGE_URL', 'http://nbexchange:9000')
_NBEXCHANGE_TOKEN = os.environ.get('NBEXCHANGE_API_TOKEN', '')
if not _NBEXCHANGE_TOKEN:
    print('[jupyterhub_config] AVISO: NBEXCHANGE_API_TOKEN no definido; el servicio '
          'nbexchange no queda registrado y nadie podrá liberar ni entregar '
          'cuadernillos.')


async def _mintear_token_estudiante(auth_state, curso_id, cuadernillo_codigo, spawner,
                                    rol=''):
    """Pide al backend un token de métricas acotado a esta persona y este curso.

    Con rol='docente' el token abre además las rutas de /internal de SU curso
    (panel, notas, competencias). Es lo que recibe el instructor en vez del
    token maestro, que abría las de todos los cursos.
    """
    url = os.environ.get('METRICS_MINT_URL',
                         'http://api_go:8080/internal/lti/mint-metrics-token')
    master_token = os.environ.get('METRICS_API_TOKEN', '')
    payload = {
        'estudiante_id': str(auth_state.get('user_id', '')),
        'curso_id': curso_id,
        'cuadernillo_codigo': cuadernillo_codigo,
        'rol': rol,
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


async def _registrar_ingreso(auth_state, curso_id, es_instructor, spawner):
    """Le dice al backend quién acaba de entrar.

    Es la única fuente de nombres y correos que tiene la base: la telemetría
    viaja con el user_id numérico de Moodle y nada más, así que sin esto el
    panel del docente solo puede enseñar números. De paso guarda el sourcedid
    y la URL del servicio de resultados, que solo viajan en este lanzamiento y
    que la devolución de notas a Moodle va a necesitar. Si el backend no
    responde, se registra en el log y el arranque sigue: un ingreso sin ficha
    es mejor que un alumno sin contenedor.
    """
    url = os.environ.get('METRICS_INGRESO_URL',
                         'http://api_go:8080/internal/lti/ingreso')
    master_token = os.environ.get('METRICS_API_TOKEN', '')
    payload = {
        'curso_id': curso_id,
        'estudiante_id': str(auth_state.get('user_id', '')),
        'nombre': str(auth_state.get('lis_person_name_full', '') or ''),
        'email': str(auth_state.get('lis_person_contact_email_primary', '') or ''),
        'usuario_hub': spawner.user.name,
        'rol': 'instructor' if es_instructor else 'estudiante',
        'lis_result_sourcedid': str(auth_state.get('lis_result_sourcedid', '') or ''),
        'lis_outcome_service_url': str(auth_state.get('lis_outcome_service_url', '') or ''),
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(url, json=payload,
                                     headers={'Authorization': f'Bearer {master_token}'})
        if resp.status_code != 200:
            spawner.log.warning('No se pudo registrar el ingreso de %s: %s %s',
                                spawner.user.name, resp.status_code, resp.text[:120])
    except Exception as exc:
        spawner.log.warning('No se pudo registrar el ingreso de %s: %s', spawner.user.name, exc)


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

    # --- Devolución de notas a Moodle ---------------------------------------
    # Para escribir una nota en el libro de calificaciones de Moodle hacen falta
    # dos datos que SOLO viajan en el lanzamiento LTI y que hasta ahora se
    # descartaban: a dónde se manda la nota y a qué casilla corresponde.
    #
    # Moodle solo los envía si la actividad LTI tiene calificación configurada.
    # Si faltan, no es un fallo del AVA: es que la actividad está sin nota, y
    # entonces la devolución automática es imposible. Por eso se registra.
    sourcedid = str(auth_state.get('lis_result_sourcedid', '') or '')
    outcome_url = str(auth_state.get('lis_outcome_service_url', '') or '')
    spawner.environment['LTI_RESULT_SOURCEDID'] = sourcedid
    spawner.environment['LTI_OUTCOME_SERVICE_URL'] = outcome_url

    if es_instructor:
        pass          # al docente no se le devuelve nota
    elif sourcedid and outcome_url:
        spawner.log.info(
            'Devolución de notas disponible para %s: Moodle mandó sourcedid y '
            'servicio de resultados.', spawner.user.name)
    else:
        spawner.log.warning(
            'Devolución de notas NO disponible para %s: el lanzamiento no trae '
            'lis_result_sourcedid (%s) ni lis_outcome_service_url (%s). '
            'Revisa que la actividad LTI de Moodle tenga calificación activada.',
            spawner.user.name, bool(sourcedid), bool(outcome_url))
    spawner.environment['ENVIAR_AL_BACKEND'] = os.environ.get('ENVIAR_AL_BACKEND', 'false')

    # Quién entró, con nombre: para el listado del docente y para la
    # devolución de notas. Va antes de acuñar tokens y no bloquea el arranque.
    await _registrar_ingreso(auth_state, curso_id, es_instructor, spawner)

    # --- Tutor IA -----------------------------------------------------------
    # Interruptor de curso y tope de preguntas por cuadernillo. El cuadernillo
    # puede además apagarlo por metadata (notebook.metadata.tutor_ia.enabled).
    # Quien cuenta las preguntas es tutor_bridge.py dentro del contenedor.
    spawner.environment['TUTOR_IA_HABILITADO'] = os.environ.get('TUTOR_IA_HABILITADO', 'true')
    spawner.environment['TUTOR_MAX_PREGUNTAS'] = os.environ.get('TUTOR_MAX_PREGUNTAS', '5')
    spawner.environment['TUTOR_API_BASE'] = os.environ.get(
        'TUTOR_API_BASE', os.environ.get('STUDENT_METRICS_API_BASE', 'http://api_go:8080')
    )

    # Montaje por rol:
    #   - instructor: nbgrader_shared (su curso de nbgrader: source/, release/,
    #     submitted/, gradebook.db), rw.
    #   - estudiante: ningún volumen compartido. Lo que el docente libera le
    #     llega por el servicio nbexchange, y lo que entrega vuelve por el mismo
    #     camino (ver NBEXCHANGE.md). Antes había un volumen de «publicados»
    #     montado solo-lectura en el alumno; ya no hace falta.
    # El trabajo de cada persona va a un volumen propio, montado en su carpeta de
    # trabajo. Hasta ahora vivía SOLO dentro del contenedor: lo único que lo
    # conservaba entre sesiones era que nadie lo borrara. Un `docker rm` o un
    # `docker system prune` —que es una limpieza rutinaria— se llevaba por
    # delante el semestre entero de todo el curso. Ya pasó una vez en pruebas.
    #
    # Con el volumen, el contenedor vuelve a ser desechable y el trabajo no.
    # DockerSpawner escapa el nombre de usuario al construir el del volumen, así
    # que un correo con @ y puntos no lo rompe.
    volumen_trabajo = {'ava-trabajo-{username}': '/home/jovyan/work'}

    # La imagen tambien depende del rol. Las plantillas de los cuadernillos son
    # la version de origen —con soluciones y pruebas ocultas— y mientras vivieron
    # en la imagen comun, un alumno podia leerlas desde una celda: su kernel
    # corre como el mismo usuario que las posee. Ahora solo viajan en la imagen
    # del docente (notebook/Dockerfile.docente).
    spawner.image = (IMAGEN_DOCENTE if es_instructor else IMAGEN_ALUMNO)

    if es_instructor:
        spawner.volumes = dict(volumen_trabajo, **{
            'nbgrader_shared': '/srv/nbgrader',
        })
    else:
        spawner.volumes = dict(volumen_trabajo)

    # Dónde escucha el servicio de intercambio. Lo leen nbgrader_config.py y los
    # comandos del AVA; el token con el que se presentan es JUPYTERHUB_API_TOKEN,
    # que el propio Hub pone en cada contenedor.
    spawner.environment['NBEXCHANGE_URL'] = _NBEXCHANGE_URL

    # Tope de memoria por contenedor.
    #
    # Sin esto, un solo estudiante tumba la clase entera, y no es hipotético: la
    # semana 4 del temario enseña ciclos `while`, así que alguien va a escribir
    # un bucle infinito que acumule en una lista. Con el tope, se queda sin
    # memoria él y los demás siguen trabajando.
    #
    # 768 MB deja holgura sobre los ~250 MB que consume una sesión normal y sobre
    # los ~400 MB de las semanas 9 y 10, cuando entran NumPy y pandas. Al docente
    # se le da más porque al calificar ejecuta todas las entregas.
    spawner.mem_limit = os.environ.get(
        'MEM_LIMIT_INSTRUCTOR' if es_instructor else 'MEM_LIMIT_ALUMNO',
        '1536M' if es_instructor else '768M')

    # QUÉ cuadernillo está activo lo decide nbgrader/instructor: es el último
    # que liberó en el exchange y está dentro de su ventana (publicar-cuadernillo
    # -> nbexchange -> entregar-cuadernillo), NO el backend. El entrypoint del
    # alumno lo resuelve y exporta CUADERNILLO_CODIGO. Por eso el Hub ya NO le
    # pregunta al backend cuál está activo: esa "doble responsabilidad"
    # backend<->nbgrader era justo lo que había que eliminar.

    if es_instructor:
        # El docente recibe un token acotado a su curso, no el maestro. Con el
        # maestro, cualquier instructor de cualquier curso del Hub podía leer el
        # panel de los demás, subir notas ajenas y acuñar tokens de cualquier
        # alumno; y el contenedor del docente tiene terminal, así que el token
        # está a un `env` de distancia. Lo leen registrar-notas,
        # cargar-competencias y el panel del curso (METRICS_DOCENTE_TOKEN).
        try:
            spawner.environment['METRICS_DOCENTE_TOKEN'] = await _mintear_token_estudiante(
                auth_state, curso_id, '', spawner, rol='docente')
        except Exception as exc:
            spawner.log.error('No se pudo acuñar METRICS_DOCENTE_TOKEN para %s: %s. '
                              'El docente no podrá subir notas ni ver el panel del curso.',
                              spawner.user.name, exc)
            spawner.environment['METRICS_DOCENTE_TOKEN'] = ''
    else:
        # El alumno debe quedarse en el notebook clásico. Sin esto, JupyterHub
        # arranca SingleUserLabApp (JupyterLab) y el alumno puede irse a /lab.
        #
        # Se usa jupyter_server.serverapp.ServerApp (NO nbclassic.notebookapp,
        # que carece de login_handler_class y hace crashear make_singleuser_app
        # de jupyterhub con AttributeError -> el contenedor del alumno moría con
        # Exit 1). Con ServerApp:
        #   - jupyterhub-singleuser arranca bien,
        #   - se carga jupyter_server_config.py (terminal off, root_dir),
        #   - nbclassic sirve /notebooks/<cuadernillo>,
        #   - jupyterlab está deshabilitado -> /lab da 404.
        spawner.environment['JUPYTERHUB_SINGLEUSER_APP'] = os.environ.get(
            'SINGLEUSER_APP', 'jupyter_server.serverapp.ServerApp'
        )

        # Base del backend a la que metrics_bridge reenvía (le agrega la ruta de
        # sección 5). El nombre del servicio en docker-compose es 'api_go'.
        spawner.environment['STUDENT_METRICS_API_BASE'] = os.environ.get(
            'STUDENT_METRICS_API_BASE', 'http://api_go:8080'
        )
        # Compat: algunos consumidores viejos leen la URL completa.
        spawner.environment['STUDENT_METRICS_API_URL'] = (
            os.environ.get('STUDENT_METRICS_API_URL')
            or os.environ.get('STUDENT_METRICS_EVENT_URL')
            or 'http://api_go:8080/public/metrics/evento'
        )

        try:
            # El token va acotado a estudiante+curso (el cuadernillo lo resuelve
            # el entrypoint, el Hub ya no lo conoce en este punto).
            spawner.environment['STUDENT_METRICS_TOKEN'] = await _mintear_token_estudiante(
                auth_state, curso_id, '', spawner)
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
        # El alumno aterriza en su panel de progreso: los cuadernillos
        # publicados, en qué va, su nota cuando ya se calificó, y cómo le está
        # yendo por competencia. Lo sirve panel_bridge desde su propio
        # contenedor, así que hereda su sesión y no necesita login aparte.
        #
        # El panel se dibuja aunque el backend no responda -- es la puerta de
        # entrada, y un fallo de la analítica no puede dejar al alumno sin
        # acceso a sus cuadernillos. Si alguna vez hay que revertir, el índice
        # 'inicio.ipynb' se sigue generando: basta cambiar esta línea por
        # '/notebooks/inicio.ipynb'.
        spawner.default_url = '/panel'

c.Spawner.auth_state_hook = auth_state_a_env

# --- Tiempos de arranque --------------------------------------------------
# La VM es una e2-micro (2 vCPU compartidas, 1 GB RAM). El servidor de usuario
# arranca bien pero tarda: con el default de 30 s el Hub lo mataba (Exit 137)
# antes de que respondiera a /api. Se suben los márgenes. Si algún día se pasa
# a una máquina más holgada, se pueden bajar de nuevo.
c.Spawner.start_timeout = 300   # espera a que el contenedor arranque
c.Spawner.http_timeout = 180    # espera a que el server responda tras arrancar
                                # (el arranque en frío en e2-micro llegó a ~120s)

c.JupyterHub.default_url = '/hub/spawn'

c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 8000

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_connect_ip = 'jupyterhub'

# --- Cookies dentro del marco de Moodle --------------------------------------
# Moodle puede abrir la actividad externa incrustada en su propia página. Para el
# navegador eso es un sitio ajeno dentro de otro, y una cookie con el SameSite
# por defecto (Lax) se guarda pero no se devuelve. El resultado es un bucle que
# no dice lo que pasa: el POST de LTI autentica bien, el siguiente GET llega sin
# sesión, el Hub manda a /hub/login, /hub/login manda al login del autenticador
# —que en LTI solo acepta POST— y el alumno ve «405 : Method Not Allowed».
#
# SameSite=None hace que la cookie viaje también incrustada; exige Secure, que se
# cumple porque de cara al navegador todo va por HTTPS. A cambio se pierde la
# protección de origen que da SameSite, por eso el Hub 5 mantiene su cookie xsrf
# —que hereda estas mismas opciones— como segunda barrera.
#
# Ojo: Safari, y Chrome cuando el usuario bloquea cookies de terceros, no
# entregan NINGUNA cookie ajena dentro de un marco, con SameSite=None o sin él.
# Para que no dependa del navegador, la actividad en Moodle debe abrirse en
# «Ventana nueva» (Contenedor de lanzamiento). Esto es la red de seguridad.
c.JupyterHub.tornado_settings = {
    'cookie_options': {'SameSite': 'None', 'Secure': True},
}

# El servidor del alumno pone además las suyas —la de su sesión y la de xsrf que
# acompaña a cada POST, telemetría incluida— y le pasa lo mismo. No hay que
# repetirlo: el Hub le entrega estas opciones al spawner y este las reenvía al
# contenedor en JUPYTERHUB_COOKIE_OPTIONS. Sí hay que tenerlo presente al
# desplegar: un contenedor que ya existía conserva el entorno con el que nació,
# así que hasta que no se rehaga sigue emitiendo las cookies viejas.

# --- Estado del Hub entre despliegues ----------------------------------------
# Por defecto el Hub guarda su base y su secreto de cookies dentro del propio
# contenedor, así que cada `up --force-recreate` los borraba. Se notaba poco con
# un usuario —volver a entrar desde Moodle rehace el usuario y su grupo— pero el
# Hub también perdía el registro de qué servidores estaban vivos: los
# contenedores de los alumnos seguían corriendo sin que el Hub lo supiera, y al
# volver a entrar levantaba otro sobre el mismo volumen. Con 25 estudiantes eso
# es memoria consumida por contenedores que ya nadie mira.
#
# Con esto la base y el secreto viven en un volumen: un redespliegue ya no cierra
# la sesión de nadie ni deja contenedores huérfanos.
_ESTADO = '/srv/jupyterhub/data'
os.makedirs(_ESTADO, exist_ok=True)
c.JupyterHub.db_url = f'sqlite:///{_ESTADO}/jupyterhub.sqlite'
c.JupyterHub.cookie_secret_file = f'{_ESTADO}/jupyterhub_cookie_secret'

# --- Apagado de contenedores inactivos ---------------------------------------
# Un contenedor de alumno se quedaba vivo indefinidamente desde que entraba, así
# que la memoria de la máquina se dimensionaba para TODOS los que hubieran
# entrado alguna vez, no para los que están trabajando. Con 25 estudiantes eso es
# la diferencia entre necesitar 8 GB o no.
#
# El culler apaga el servidor de quien lleva un rato sin actividad. No borra
# nada: el trabajo vive en su volumen, y al volver a entrar se levanta otra vez.
#
# Se le dan permisos acotados en vez de hacerlo admin del Hub (JupyterHub 5
# permite roles con alcances concretos): solo puede listar usuarios, leer su
# actividad y apagar servidores.
_CULL_INACTIVO = int(os.environ.get('CULL_TIMEOUT', '3600'))    # 1 hora sin actividad
_CULL_CADA = int(os.environ.get('CULL_EVERY', '300'))           # revisar cada 5 min

c.JupyterHub.services = [
    {
        'name': 'idle-culler',
        'command': [
            sys.executable, '-m', 'jupyterhub_idle_culler',
            f'--timeout={_CULL_INACTIVO}',
            f'--cull-every={_CULL_CADA}',
        ],
    },
]

c.JupyterHub.load_roles = [
    {
        'name': 'list-and-cull',
        'scopes': [
            'list:users', 'read:users:activity', 'read:servers', 'delete:servers',
        ],
        'services': ['idle-culler'],
    },
]

# --- nbexchange como servicio del Hub -----------------------------------------
# Servicio EXTERNO (tiene url, no command): lo levanta docker-compose, no el Hub.
# Registrarlo hace dos cosas: el Hub conoce su api_token, con el que el servicio
# consulta `/hub/api/users/<nombre>`; y el proxy del Hub enruta
# /services/nbexchange/ hacia él, por si algún día hace falta llegarle desde
# fuera (hoy los contenedores le hablan directo por la red interna).
#
# El rol acota lo que puede hacer con ese token: leer usuarios y su auth_state.
# Lo segundo es lo que le permite guardar a cada alumno bajo su user_id de LTI,
# el mismo que lleva la telemetría y la nota (ver nbexchange/nbexchange_config.py).
if _NBEXCHANGE_TOKEN:
    c.JupyterHub.services.append({
        'name': 'nbexchange',
        'url': _NBEXCHANGE_URL,
        'api_token': _NBEXCHANGE_TOKEN,
        'display': False,
    })
    c.JupyterHub.load_roles.append({
        'name': 'nbexchange',
        'scopes': ['read:users', 'admin:auth_state'],
        'services': ['nbexchange'],
    })
