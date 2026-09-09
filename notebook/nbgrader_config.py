import os

c = get_config()

curso_id = os.environ.get('CURSO_ID', 'curso_default')
es_instructor = os.environ.get('ALUMNO_ROL', 'estudiante') == 'instructor'

# El curso del docente vive en el volumen compartido /srv/nbgrader, enlazado
# dentro del workspace del servidor (/home/jovyan/work/nbgrader) para que
# nbgrader valide que la raíz del curso es un subdirectorio del root del server.
# El alumno no monta ese volumen: su root de curso apunta a una carpeta propia
# que nunca se usa (él no tiene source/ ni submitted/), pero course_id sí cuenta:
# es lo que el exchange usa para saber de qué curso habla.
c.CourseDirectory.course_id = curso_id
c.CourseDirectory.root = (f'/home/jovyan/work/nbgrader/{curso_id}' if es_instructor
                          else f'/home/jovyan/.nbgrader/{curso_id}')

# --- Exchange: nbexchange por HTTP, no carpetas compartidas -------------------
# El exchange por defecto de nbgrader copia carpetas dentro de un directorio
# compartido. Aquí cada persona corre en su propio contenedor y no hay
# directorio común, así que release/fetch/submit/collect van contra el servicio
# nbexchange (ver NBEXCHANGE.md y docker-compose.yml), autenticados con el
# token que JupyterHub le dio a este contenedor. Las clases están en
# notebook/nbexchange_cliente/ (ORIGEN.md explica por qué van copiadas).
c.ExchangeFactory.exchange           = 'nbexchange_cliente.ava.Exchange'
c.ExchangeFactory.list               = 'nbexchange_cliente.ava.ExchangeList'
c.ExchangeFactory.fetch_assignment   = 'nbexchange_cliente.ava.ExchangeFetchAssignment'
c.ExchangeFactory.submit             = 'nbexchange_cliente.ava.ExchangeSubmit'
c.ExchangeFactory.collect            = 'nbexchange_cliente.ava.ExchangeCollect'
c.ExchangeFactory.release_assignment = 'nbexchange_cliente.ava.ExchangeReleaseAssignment'
c.ExchangeFactory.release_feedback   = 'nbexchange_cliente.ava.ExchangeReleaseFeedback'
c.ExchangeFactory.fetch_feedback     = 'nbexchange_cliente.ava.ExchangeFetchFeedback'

c.Exchange.base_service_url = os.environ.get('NBEXCHANGE_URL', 'http://nbexchange:9000')
c.Exchange.base_path = '/services/nbexchange/'
c.Exchange.api_plugin_class = 'nbexchange_cliente.ava.AutenticacionJupyterHub'
# Sin el curso en la ruta: el alumno trabaja con work/<tarea>.ipynb plano
# (entregar-cuadernillo decide dónde va cada cosa), y el docente no fetchea.
c.Exchange.path_includes_course = False
# Formgrader instancia el exchange en cada petición y llama al servicio para
# listar; si el servicio no responde, que falle pronto y no cuelgue la página.
c.Exchange.api_timeout = 5
# Un cuadernillo pesa ~350 KB. 50 MB por subida sobra y evita que un envío
# desmedido se coma la memoria de la VM (el servicio tiene el mismo tope).
c.Exchange.max_buffer_size = 50 * 1024 * 1024

# Log centralizado (solo el docente tiene esa carpeta).
if es_instructor:
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
