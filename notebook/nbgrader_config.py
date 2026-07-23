import os

c = get_config()

curso_id = os.environ.get('CURSO_ID', 'curso_default')

# Todos los cursos viven bajo el volumen compartido /srv/nbgrader,
# enlazado dentro del workspace del servidor (/home/jovyan/work/nbgrader)
# para que nbgrader valide que la ruta raíz del curso es un subdirectorio
# del notebook server root.
c.CourseDirectory.course_id = curso_id
c.CourseDirectory.root = f'/home/jovyan/work/nbgrader/{curso_id}'

# El exchange (intercambio release/fetch/submit/collect)
c.Exchange.path_includes_course = True
c.Exchange.root = '/home/jovyan/work/nbgrader/exchange'

# Log centralizado
c.NbGrader.logfile = '/home/jovyan/work/nbgrader/logs/nbgrader.log'

# Plugin de exportación hacia backend Go
c.ExportApp.plugin_class = 'api_export.ApiExportPlugin'