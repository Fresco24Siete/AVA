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

# --- Delimitadores en español -------------------------------------------------
# Sin esto, 'Generate' borra la celda de solución ENTERA y la reemplaza por el
# stub en inglés: el alumno pierde también el andamiaje (la firma de la función,
# los datos del enunciado) y lee "YOUR CODE HERE". Con delimitadores, solo se
# reemplaza lo que está entre ellos.
# Deben coincidir con las constantes de notebook/cuadernillos/constructor.py.
c.ClearSolutions.begin_solution_delimeter = 'INICIO SOLUCION'
c.ClearSolutions.end_solution_delimeter = 'FIN SOLUCION'
# El texto del stub lo lee un estudiante de primer semestre en su primera semana,
# y es lo primero que ve fallar. Que diga qué significa, y no solo que falló.
c.ClearSolutions.code_stub = {
    'python': '# ESCRIBE TU CODIGO AQUI y borra la linea de abajo\n'
              'raise NotImplementedError("Todavia no has escrito tu respuesta")',
}
c.ClearSolutions.text_stub = 'ESCRIBE TU RESPUESTA AQUI'

# Pruebas ocultas: los asserts que solo corren al calificar, para que no se pueda
# programar "contra la prueba".
c.ClearHiddenTests.begin_test_delimeter = 'INICIO PRUEBAS OCULTAS'
c.ClearHiddenTests.end_test_delimeter = 'FIN PRUEBAS OCULTAS'