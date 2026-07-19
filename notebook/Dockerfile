# Imagen ligera de Python basada en Debian/Ubuntu
FROM python:3.11-slim

# curl y Node.js (vital para compilar extensiones de JupyterLab)
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# CRÍTICO: Instalar 'jupyterhub' junto con jupyterlab y nbgrader. 
# Esto instala el script 'jupyterhub-singleuser' que el Hub necesita para comunicarse.
RUN pip install --no-cache-dir jupyterlab nbgrader jupyterhub

# Habilitar las extensiones de nbgrader para el profesor (Formgrader)
RUN jupyter server extension enable --sys-prefix nbgrader.server_extensions.formgrader

COPY notebook/notebooks/ /home/jovyan/

# Directorio de trabajo dentro del contenedor (DEBE coincidir con la ruta de arriba)
WORKDIR /home/jovyan/

# Puerto estándar de Jupyter que DockerSpawner espera
EXPOSE 8888