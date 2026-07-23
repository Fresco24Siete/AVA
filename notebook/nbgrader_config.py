import os

c = get_config()

curso_id = os.environ.get('CURSO_ID', 'curso_default')

# Todos los cursos viven bajo el volumen compartido, uno por curso_id.
# Estructura que crea nbgrader: /srv/nbgrader/<curso_id>/{source,release,
# submitted,autograded,feedback}
c.CourseDirectory.course_id = curso_id
c.CourseDirectory.root = f'/srv/nbgrader/{curso_id}'

# El exchange (intercambio release/fetch/submit/collect) también compartido,
# separado por curso automáticamente.
c.Exchange.path_includes_course = True
c.Exchange.root = '/srv/nbgrader/exchange'

# Log centralizado, muy recomendado por la doc oficial al usar nbgrader con
# JupyterHub para depurar problemas de permisos/rutas.
c.NbGrader.logfile = '/srv/nbgrader/logs/nbgrader.log'

# Plugin de exportación hacia backend Go
# Este envía el SNAPSHOT FINAL por ejercicio (aprobado/puntos) al terminar
# de autogradear. Los errores y tiempos en vivo, mientras el estudiante
# trabaja, van por un canal aparte -- ver metrics_bridge.py + custom.js.
# NO se conecta directo a Postgres: el contenedor de notebook no debe
# conocer credenciales de base de datos.
# Se invoca manualmente o desde un cron con:
#   nbgrader export --exporter=api_export.ApiExportPlugin
c.ExportApp.plugin_class = 'api_export.ApiExportPlugin'