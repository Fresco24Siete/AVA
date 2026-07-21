# Imagen ligera de Python basada en Debian/Ubuntu
FROM python:3.11-slim

# Instalar dependencias del sistema operativo y Node.js (necesario para JupyterLab)
RUN apt-get update && apt-get install -y curl git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --no-cache-dir jupyterlab nbgrader jupyterhub

RUN useradd -m -s /bin/bash -u 1000 jovyan

# Copiar los cuadernillos y darles permisos correctos al usuario jovyan
COPY --chown=jovyan:jovyan notebook_semana/ /home/jovyan/work/

# Cambiar al usuario jovyan para seguridad y buen funcionamiento
USER jovyan

# Directorio de trabajo del estudiante
WORKDIR /home/jovyan/work

# Puerto estándar de JupyterLab
EXPOSE 8888

CMD ["jupyterhub-singleuser"]