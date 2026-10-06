#!/usr/bin/env python3
"""Inyecta la ayuda del docente en las páginas de formgrader.

nbgrader no ofrece ningún punto de extensión para añadir contenido propio a
formgrader, y sus plantillas —a diferencia del notebook— no cargan `custom.js`.
La única vía es añadir el `<script>` a su plantilla base.

Se hace al construir la imagen, no en caliente: así queda registrado en el
Dockerfile, es reproducible, y la versión de nbgrader está fijada, que es lo que
vuelve asumible tocar un archivo de site-packages.

Si nbgrader cambia la estructura de sus plantillas, esto avisa y no hace nada,
en vez de dejar la imagen a medio construir: la ayuda es un extra, y perderla no
justifica que falle el despliegue entero.
"""
import glob
import sys

MARCA = "ava-ayuda-docente"
ETIQUETA = '  <script src="{{ base_url }}/formgrader/static/js/ava_ayuda.js"></script>\n'


def main():
    plantillas = glob.glob(
        "/usr/local/lib/python*/site-packages/nbgrader/"
        "server_extensions/formgrader/templates/base.tpl")
    if not plantillas:
        print("[parchar-formgrader] AVISO: no encontré base.tpl de formgrader; "
              "la ayuda del docente no se instala.")
        return 0

    for ruta in plantillas:
        with open(ruta, encoding="utf-8") as f:
            contenido = f.read()

        if MARCA in contenido or "ava_ayuda.js" in contenido:
            print(f"[parchar-formgrader] ya estaba parcheado: {ruta}")
            continue

        # Va al final del <head>, junto al resto de scripts de formgrader, para
        # que el archivo esté cargado antes de que se pinte la tabla.
        if "</head>" not in contenido:
            print(f"[parchar-formgrader] AVISO: {ruta} no tiene </head>; se omite.")
            continue

        contenido = contenido.replace("</head>", ETIQUETA + "</head>", 1)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        print(f"[parchar-formgrader] ayuda del docente instalada en {ruta}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
