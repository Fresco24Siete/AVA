import os

c = get_config()

es_instructor = os.environ.get('ALUMNO_ROL', 'estudiante') == 'instructor'

# Notebook clásico (Notebook 6.x / notebook.notebookapp)
c.NotebookApp.nbserver_extensions = {
    "metrics_bridge": True,
}

# jupyter_server >=1.x (usado por nbclassic)
c.ServerApp.jpserver_extensions = {
    "metrics_bridge": True,
}

if not es_instructor:
    # --- Contención del entorno del estudiante ------------------------------
    # 1. Sin terminales. Es el punto más importante: una terminal en Jupyter es
    #    hija del proceso del servidor, hereda su entorno, y con un simple 'env'
    #    el alumno lee STUDENT_METRICS_TOKEN y puede mandar telemetría falsa
    #    directamente al backend saltándose el puente.
    c.ServerApp.terminals_enabled = False
    c.NotebookApp.terminals_enabled = False

    # 2. Raíz acotada al workspace propio. Junto con NO montar el volumen
    #    nbgrader_shared (ver jupyterhub_config.py), el explorador de archivos
    #    solo puede ver los archivos del propio alumno.
    c.ServerApp.root_dir = '/home/jovyan/work'
    c.NotebookApp.notebook_dir = '/home/jovyan/work'
