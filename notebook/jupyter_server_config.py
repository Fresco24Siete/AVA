import os

c = get_config()

es_instructor = os.environ.get('ALUMNO_ROL', 'estudiante') == 'instructor'

# Notebook clásico (Notebook 6.x / notebook.notebookapp)
c.NotebookApp.nbserver_extensions = {
    "metrics_bridge": True,
    "tutor_bridge": True,
    # Solo hace algo si el rol es instructor; él mismo se abstiene si no.
    "admin_bridge": True,
    # Y este solo para el alumno: el panel de progreso es suyo.
    "panel_bridge": True,
    # El del docente, que se abstiene si el rol no es instructor.
    "panel_docente_bridge": True,
}

# jupyter_server >=1.x (usado por nbclassic)
c.ServerApp.jpserver_extensions = {
    "metrics_bridge": True,
    "tutor_bridge": True,
    "admin_bridge": True,
    "panel_bridge": True,
    "panel_docente_bridge": True,
}

if not es_instructor:
    # --- Contención del entorno del estudiante ------------------------------
    # 1. Sin terminales. Es el punto más importante: una terminal en Jupyter es
    #    hija del proceso del servidor, hereda su entorno, y con un simple 'env'
    #    el alumno lee STUDENT_METRICS_TOKEN y puede mandar telemetría falsa
    #    directamente al backend saltándose el puente.
    # El alumno corre nbclassic sobre jupyter_server, así que la config
    # canónica es ServerApp.*. (Antes se ponía también NotebookApp.*, que solo
    # generaba warnings de deprecación porque jupyter_server los reenvía.)
    c.ServerApp.terminals_enabled = False

    # 2. Raíz acotada al workspace propio. Junto con NO montar el volumen
    #    nbgrader_shared (ver jupyterhub_config.py), el explorador de archivos
    #    solo puede ver los archivos del propio alumno.
    c.ServerApp.root_dir = '/home/jovyan/work'

# --- Cookies dentro del marco de Moodle --------------------------------------
# El servidor del alumno emite dos cookies propias: la de sesión de JupyterHub y
# la de xsrf que acompaña a cada POST (entre ellos los de la telemetría). Con el
# SameSite por defecto, el navegador no las devuelve cuando el cuadernillo va
# incrustado en la página de Moodle, así que el alumno entraría y no podría
# ejecutar nada. Van con las mismas opciones que las del Hub, que las manda en
# JUPYTERHUB_COOKIE_OPTIONS.
#
# La de xsrf conserva su ruta —/user/<alumno>/— para que no se pisen entre sí
# ni con la del propio Hub, que vive en /hub/.
_MARCO = {'SameSite': 'None', 'Secure': True}
c.ServerApp.cookie_options = dict(_MARCO)
c.ServerApp.tornado_settings = {
    'xsrf_cookie_kwargs': dict(_MARCO,
                               path=os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '/')),
}
