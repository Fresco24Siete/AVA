# Imagen ligera de Python basada en Debian/Ubuntu
FROM python:3.11-slim

# Instalar dependencias del sistema operativo y Node.js (necesario para JupyterLab)
RUN apt-get update && apt-get install -y curl git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalamos notebook y nbclassic. Quitamos jupyterlab de la lista explícitamente.
# requests: para que el plugin de exportación hable con el backend Go por
# HTTP (este contenedor NO se conecta directo a Postgres, por seguridad).
RUN pip install --no-cache-dir "notebook<7" nbclassic nbgrader jupyterhub requests

# Desactivamos la extensión de JupyterLab por si se instaló como dependencia oculta
RUN jupyter server extension disable jupyterlab || true

# Instala (pero no activa todavía) las extensiones de nbgrader; el rol
# exacto que se activa en cada arranque lo decide entrypoint.sh
RUN (jupyter nbextension install --sys-prefix --py nbgrader --overwrite || true) \
    && (jupyter serverextension enable --sys-prefix --py nbgrader || true)

RUN useradd -m -s /bin/bash -u 1000 jovyan

# Configuración global de nbgrader (course_id dinámico vía env) y el plugin
# de exportación hacia Postgres
COPY nbgrader_config.py /etc/jupyter/nbgrader_config.py
COPY plugins/api_export.py /etc/jupyter/api_export.py
COPY metrics_bridge.py /etc/jupyter/metrics_bridge.py
# Tutor IA: la extensión de servidor y el JS del panel, que ella misma sirve
# en {base_url}tutor-ia/static/tutor_ia.js (por eso van al mismo directorio).
COPY tutor_bridge.py /etc/jupyter/tutor_bridge.py
COPY tutor_ia.js /etc/jupyter/tutor_ia.js
COPY jupyter_server_config.py /etc/jupyter/jupyter_server_config.py
ENV PYTHONPATH="/etc/jupyter"

# custom.js debe vivir en el jupyter_config_dir del usuario que corre el
# servidor (jovyan), no en /etc/jupyter
RUN mkdir -p /home/jovyan/.jupyter/custom
COPY custom.js /home/jovyan/.jupyter/custom/custom.js

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
# Entrega del cuadernillo activo (alumno) y publicación (instructor).
COPY entregar_cuadernillo.py /usr/local/bin/entregar-cuadernillo
COPY publicar_cuadernillo.py /usr/local/bin/publicar-cuadernillo
RUN chmod +x /usr/local/bin/entrypoint.sh \
             /usr/local/bin/entregar-cuadernillo \
             /usr/local/bin/publicar-cuadernillo

# Plantillas de cuadernillos: van a /opt/plantillas, NO al work/ del usuario.
# El instructor las usa para sembrar source/ en nbgrader; el alumno NO debe
# tenerlas en su workspace (recibe solo el cuadernillo activo entregado
# dinámicamente en work/cuadernillo.ipynb).
COPY --chown=jovyan:jovyan notebook_semana/ /opt/plantillas/

# Crear /srv/nbgrader y /srv/publicados en la imagen con dueño jovyan: al montar
# volúmenes nombrados vacíos sobre estas rutas, Docker los inicializa copiando
# el dueño de la imagen -> jovyan puede escribir. Sin esto, el volumen queda de
# root y publicar/entregar fallan con PermissionError.
RUN mkdir -p /srv/nbgrader /srv/publicados \
    && chown -R jovyan:jovyan /srv/nbgrader /srv/publicados

# El workspace del alumno debe existir y pertenecer a jovyan. Antes lo creaba
# implícitamente el COPY de notebook_semana; al quitarlo, WORKDIR lo crearía
# como root y jovyan no podría escribir el cuadernillo entregado.
RUN mkdir -p /home/jovyan/work && chown -R jovyan:jovyan /home/jovyan/work

# Estado del tutor (contador de preguntas). Va FUERA de root_dir para que no
# aparezca en el explorador de archivos del alumno.
RUN mkdir -p /home/jovyan/.tutor_ia && chown -R jovyan:jovyan /home/jovyan/.tutor_ia

# entrypoint.sh corre como jovyan y necesita poder (des)activar extensiones
# en cada arranque (el rol cambia según quién haga el LTI launch)
RUN chown -R jovyan:jovyan /usr/local/etc/jupyter /usr/local/share/jupyter /home/jovyan/.jupyter

# Cambiar al usuario jovyan para seguridad y buen funcionamiento
USER jovyan

# Directorio de trabajo del estudiante
WORKDIR /home/jovyan/work

# Puerto estándar de JupyterLab
EXPOSE 8888

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["jupyterhub-singleuser"]