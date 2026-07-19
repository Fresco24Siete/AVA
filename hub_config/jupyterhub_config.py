import os
c = get_config()


c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
c.DockerSpawner.image = 'mi_imagen_jupyterlab:latest'

network_name = os.environ.get('DOCKER_NETWORK_NAME', 'bridge')
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name
c.DockerSpawner.remove = True
c.JupyterHub.authenticator_class = 'ltiauthenticator.lti11.auth.LTI11Authenticator'

c.LTI11Authenticator.consumers = {
    "moodle-llave-publica": "secreto-super-seguro-000000"
}

c.Spawner.default_url = '/lab'
c.LTI11Authenticator.username_key = 'lis_person_contact_email_primary'
c.Authenticator.enable_auth_state = True

async def auth_state_a_env(spawner):
    auth_state = await spawner.user.get_auth_state()
    if not auth_state:
        return
    spawner.environment['ALUMNO_ID']     = str(auth_state.get('user_id', ''))
    spawner.environment['ALUMNO_NOMBRE'] = str(auth_state.get('lis_person_name_full', ''))
    spawner.environment['ALUMNO_EMAIL']  = str(auth_state.get('lis_person_contact_email_primary', ''))
    spawner.environment['ALUMNO_ROL']    = str(auth_state.get('roles', ''))
    spawner.environment['CURSO_ID']      = str(auth_state.get('context_id', ''))
    spawner.environment['CURSO_NOMBRE']  = str(auth_state.get('context_title', ''))

c.Spawner.auth_state_hook = auth_state_a_env


c.Spawner.default_url = '/lab/tree/cuadernillo_datos_lti.ipynb'

# JupyterHub debe escuchar en todas las interfaces internas del contenedor
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 8000

# El Hub API también debe ser accesible internamente
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_connect_ip = 'jupyterhub'