#imagen ligera de Python basada en Debian/Ubuntu
FROM python:3.11-slim

#curl y Node.js (vital para compilar extensiones de JupyterLab)
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar nbgrader
RUN pip install jupyterlab nbgrader

# Habilitar las extensiones de nbgrader para el profesor (Formgrader)
RUN jupyter server extension enable --sys-prefix nbgrader.server_extensions.formgrader

#directorio de trabajo dentro del contenedor
WORKDIR /app

#JupyterLab
RUN pip install --no-cache-dir jupyterlab

#puerto por defecto de Jupyter
EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port", "8888", "--no-browser", "--allow-root", "--NotebookApp.token=''", "--NotebookApp.password=''"]