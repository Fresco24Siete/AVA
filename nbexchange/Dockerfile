# Servicio nbexchange: el exchange de nbgrader por HTTP. Ver NBEXCHANGE.md.
#
# No hay paquete en PyPI ni imagen pública mantenida (la de quay.io es de 2022),
# así que se instala desde el repositorio, fijado a un commit concreto. El
# upstream arranca con supervisord; aquí no hace falta, el propio
# `restart: unless-stopped` del compose hace ese trabajo.
FROM python:3.12-slim

# Commit del tag v2.0.2 (2026-08-17). Para actualizar: cambiar el sha y volver a
# construir; las migraciones de la base corren solas al arrancar (--upgrade-db).
ARG NBEXCHANGE_COMMIT=609d51d5f8d1ccc1ca11e0bfc41cb68f9311b254

# jupyterhub no es dependencia declarada de nbexchange, pero hace falta para
# validar los tokens contra el Hub (HubAuth). Se fija a la misma mayor que corre
# el Hub (jupyterhub/jupyterhub:latest es 5.x).
RUN pip install --no-cache-dir \
        "https://github.com/edina/nbexchange/archive/${NBEXCHANGE_COMMIT}.tar.gz" \
        "jupyterhub>=5,<6" \
        requests

RUN useradd -m -u 1000 nbexchange \
    && mkdir -p /var/nbexchange /etc/config \
    && chown -R nbexchange:nbexchange /var/nbexchange

COPY nbexchange_config.py /etc/config/nbexchange_config.py

USER nbexchange
# Base y almacén de ficheros: un volumen en /var/nbexchange (docker-compose.yml).
VOLUME ["/var/nbexchange"]
EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:9000/services/nbexchange/', timeout=4).status == 200 else 1)"

CMD ["nbexchange", "--upgrade-db"]
