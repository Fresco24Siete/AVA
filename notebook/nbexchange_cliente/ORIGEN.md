# De dónde sale esta carpeta

Copia de `nbexchange_jlab/plugins/` del proyecto
<https://github.com/edina/nbexchange_jlab_plugin>, commit
`ad9be431fb9e5148aea424acf90614347eb61565` (2026-08-06), licencia BSD-3
(`LICENSE.upstream`).

Son las clases de intercambio de nbgrader (`ExchangeFactory.*`) que hablan con el
servicio nbexchange por HTTP en vez de copiar carpetas. Se traen copiadas, y no
con `pip install nbexchange_jlab`, por una razón concreta: ese paquete fija
`nbgrader==0.9.5`, `jupyter_server>=2` y JupyterLab 4, y la imagen del AVA corre
nbgrader 0.8.5 sobre el notebook clásico (`notebook<7`, nbclassic). Instalarlo
arrastraría esas versiones y rompería `custom.js`, los widgets y el formgrader
clásico. Las clases en sí solo dependen de `nbgrader.exchange`, `requests`,
`humanize` y `dateutil`, y todo lo que importan existe en 0.8.5.

Cambios respecto al original:

- `exchange.py`: el `import fuzzywuzzy` de `_assignment_not_found` va dentro de
  un `try`, porque esa librería no está en la imagen y el `ImportError` tapaba
  el error real.
- No se copian `course.py` (llama a una ruta `/courses` que el servicio no tiene)
  ni `__init__.py` (el nuestro añade `ava.py`).

`ava.py` es propio del AVA: la autenticación contra el servicio con el token de
JupyterHub y los ayudantes que usan `publicar-cuadernillo`, `entregar-cuadernillo`,
`borrar-cuadernillo` y los paneles.

Para actualizar desde el upstream: copiar los `.py` de `plugins/` encima,
reaplicar el parche de `fuzzywuzzy`, y anotar aquí el commit.
