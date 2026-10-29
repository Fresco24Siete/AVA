#!/usr/bin/env python3
"""Una entrada por tarea en el panel del alumno y en su índice (inicio.ipynb).

Cuando el docente corrige un cuadernillo, la versión nueva llega al lado como
<id>_vN.ipynb (nunca pisa la anterior: el trabajo del alumno está dentro). El
panel listaba TODOS los archivos, así que «Semana 3» salía dos o tres veces, y
la marca «Esta semana», la nota y el progreso —que van por tarea— caían en la
vieja o en ninguna. Esto comprueba que ahora:

  - el panel (`panel_bridge._cuadernillos_en_disco`) y el índice
    (`entregar_cuadernillo.main` -> inicio.ipynb) muestran UNA entrada por
    tarea liberada, apuntando a la versión más nueva;
  - las versiones anteriores siguen en disco y se nombran en una línea aparte;
  - lo que no está liberado no aparece;
  - «Guardar y entregar» manda la versión ABIERTA (custom.js manda su nombre):
    por el camino normal, la más nueva; y un nombre que no esté en disco cae en
    la más nueva, nunca en la base.

Corre sin Jupyter ni red: carpeta temporal, dobles de tornado/jupyter_server y
`_consultar` sustituido (el servicio de intercambio no responde, como cuando
está caído: el módulo tiene que arreglárselas con la nota local).

    python3 backend/tests/telemetria/prueba_indice_versiones.py
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
NOTEBOOK = os.path.join(REPO, "notebook")

ARCHIVOS = ["semana_01.ipynb", "semana_03.ipynb", "semana_03_v2.ipynb",
            "semana_03_v3.ipynb", "semana_04.ipynb", "inicio.ipynb"]
LIBERADAS = {"semana_01", "semana_03"}          # semana_04 no está liberada

fallos = []


def caso(nombre, ok, detalle=""):
    print(("  OK    " if ok else "  FALLO ") + nombre + (f"  -> {detalle}" if detalle and not ok else ""))
    if not ok:
        fallos.append(nombre)


def _doble(nombre, **atributos):
    """Un módulo vacío en sys.modules, con lo justo para que importe."""
    if nombre in sys.modules:
        return sys.modules[nombre]
    modulo = types.ModuleType(nombre)
    for k, v in atributos.items():
        setattr(modulo, k, v)
    sys.modules[nombre] = modulo
    return modulo


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def nb_vacio():
    return json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5})


def preparar(carpeta):
    for a in ARCHIVOS:
        with open(os.path.join(carpeta, a), "w", encoding="utf-8") as f:
            f.write(nb_vacio())
    # La nota local que deja entregar_cuadernillo tras consultar al servicio.
    # Sin `archivo`: así se prueba también el camino de una nota vieja.
    nota = {"consultado": True, "en": "2026-09-21T00:00:00+00:00", "entregas": {},
            "cuadernillos": {
                "semana_01": {"timestamp": "2026-09-01 10:00:00.000000 UTC",
                              "notebook": "cuadernillo.ipynb", "version": "v1aaaa"},
                "semana_03": {"timestamp": "2026-09-15 10:00:00.000000 UTC",
                              "notebook": "cuadernillo.ipynb", "version": "v3cccc"},
            }}
    with open(os.path.join(carpeta, ".ava_publicados.json"), "w", encoding="utf-8") as f:
        json.dump(nota, f)


def main():
    carpeta = tempfile.mkdtemp(prefix="ava-prueba-versiones-")
    try:
        preparar(carpeta)
        os.environ["CUADERNILLO_DESTINO"] = os.path.join(carpeta, "cuadernillo.ipynb")
        os.environ["PANEL_CARPETA"] = carpeta
        os.environ.pop("CUADERNILLO_INICIO", None)
        os.environ["STUDENT_METRICS_TOKEN"] = ""

        # Dobles: panel_bridge importa tornado y el handler base de Jupyter.
        _doble("tornado")
        _doble("tornado.web", authenticated=lambda f: f)
        sys.modules["tornado"].web = sys.modules["tornado.web"]
        _doble("jupyter_server")
        _doble("jupyter_server.base")
        _doble("jupyter_server.base.handlers", JupyterHandler=object)
        sys.path.insert(0, NOTEBOOK)

        ec = _cargar("entregar_cuadernillo", os.path.join(NOTEBOOK, "entregar_cuadernillo.py"))
        pb = _cargar("panel_bridge", os.path.join(NOTEBOOK, "panel_bridge.py"))
        # El servicio no responde: main() se queda con la nota local.
        ec._consultar = lambda publicados: (False, {}, {}, set())

        print("Regla pura del panel (sin nota de vigente):")
        lista = pb.agrupar_por_tarea(sorted(os.listdir(carpeta)), LIBERADAS)
        ids = [c["id"] for c in lista]
        caso("una entrada por tarea liberada, sin repetir", ids == ["semana_01", "semana_03"], ids)
        por_id = {c["id"]: c for c in lista}
        caso("semana_01 apunta a su base", por_id["semana_01"]["archivo"] == "semana_01.ipynb")
        caso("semana_03 apunta a _v3", por_id["semana_03"]["archivo"] == "semana_03_v3.ipynb",
             por_id["semana_03"]["archivo"])
        caso("las anteriores de semana_03 son base y _v2",
             por_id["semana_03"]["anteriores"] == ["semana_03.ipynb", "semana_03_v2.ipynb"],
             por_id["semana_03"]["anteriores"])
        caso("semana_01 no tiene anteriores", por_id["semana_01"]["anteriores"] == [])
        caso("semana_04 (no liberada) no aparece", "semana_04" not in ids)
        caso("la nota de vigente manda si sigue en disco",
             pb.agrupar_por_tarea(["semana_03.ipynb", "semana_03_v2.ipynb"], LIBERADAS,
                                  {"semana_03": {"archivo": "semana_03.ipynb"}})[0]["archivo"]
             == "semana_03.ipynb")
        caso("una nota de vigente que ya no está en disco se ignora",
             pb.agrupar_por_tarea(["semana_03.ipynb", "semana_03_v2.ipynb"], LIBERADAS,
                                  {"semana_03": {"archivo": "semana_03_v9.ipynb"}})[0]["archivo"]
             == "semana_03_v2.ipynb")

        print("Qué archivo elige entregar_cuadernillo para la versión publicada:")
        registro = {"semana_03.ipynb": "v1", "semana_03_v2.ipynb": "v2", "semana_03_v3.ipynb": "v3cccc"}
        caso("la registrada con la versión publicada",
             ec._archivo_vigente("semana_03", "v3cccc", registro) == "semana_03_v3.ipynb")
        caso("una versión nueva va a _v4, nunca encima de lo que tiene",
             ec._archivo_vigente("semana_03", "v4dddd", registro) == "semana_03_v4.ipynb")
        caso("sin registro (perdido), la más nueva por nombre",
             ec._archivo_vigente("semana_03", "v3cccc", {}) == "semana_03_v3.ipynb")
        caso("sin archivos en disco, la base",
             ec._archivo_vigente("semana_09", "v1", {}) == "semana_09.ipynb")
        caso("una base sin registro se asume vigente (no se duplica)",
             ec._archivo_vigente("semana_01", "v1aaaa", {}) == "semana_01.ipynb")

        print("Índice (inicio.ipynb) tras main() con el servicio caído:")
        antes = sorted(a for a in os.listdir(carpeta) if a.endswith(".ipynb"))
        activo = ec.main()
        despues = sorted(a for a in os.listdir(carpeta) if a.endswith(".ipynb"))
        caso("main() no creó ni movió cuadernillos del alumno", antes == despues,
             sorted(set(antes) ^ set(despues)))
        caso("el activo es la tarea, no el archivo", activo == "semana_03", activo)
        with open(os.path.join(carpeta, "inicio.ipynb"), encoding="utf-8") as f:
            indice = "".join(json.load(f)["cells"][0]["source"])
        filas = [l for l in indice.splitlines() if l.startswith("| ") and "---" not in l
                 and "Cuadernillo" not in l]
        caso("dos filas: semana_01 y semana_03, una vez cada una", len(filas) == 2, filas)
        fila3 = next((l for l in filas if "Semana 3" in l), "")
        caso("Semana 3 enlaza a _v3", "[abrir](semana_03_v3.ipynb)" in fila3, fila3)
        caso("Semana 3 lleva la marca «Esta semana»", "**Esta semana**" in fila3)
        caso("la línea de versión anterior nombra base y _v2",
             "versiones anteriores" in fila3 and "semana_03.ipynb" in fila3
             and "semana_03_v2.ipynb" in fila3, fila3)
        caso("la base y _v2 no se enlazan como «abrir»",
             "[abrir](semana_03.ipynb)" not in indice and "[abrir](semana_03_v2.ipynb)" not in indice)
        fila1 = next((l for l in filas if "Semana 1" in l), "")
        caso("Semana 1 enlaza a su base y sin línea de anteriores",
             "[abrir](semana_01.ipynb)" in fila1 and "anterior" not in fila1, fila1)
        caso("semana_04 no está en el índice", "semana_04" not in indice)
        nota = json.load(open(os.path.join(carpeta, ".ava_publicados.json"), encoding="utf-8"))
        caso("la nota anota el vigente y las anteriores de semana_03",
             nota["cuadernillos"]["semana_03"].get("archivo") == "semana_03_v3.ipynb"
             and nota["cuadernillos"]["semana_03"].get("anteriores")
             == ["semana_03.ipynb", "semana_03_v2.ipynb"], nota["cuadernillos"]["semana_03"])

        print("Panel (con la nota que dejó main):")
        lista = pb._cuadernillos_en_disco()
        ids = [c["id"] for c in lista]
        caso("una tarjeta por tarea liberada", ids == ["semana_01", "semana_03"], ids)
        caso("semana_03 abre _v3", {c["id"]: c["archivo"] for c in lista}["semana_03"]
             == "semana_03_v3.ipynb")
        pagina = pb._html(None, "", "/user/x/")
        caso("dos tarjetas en el HTML", pagina.count('<div class="tarjeta">') == 2,
             pagina.count('<div class="tarjeta">'))
        caso("«Esta semana» una sola vez, en Semana 3",
             pagina.count("Esta semana") == 1 and
             pagina.find("Semana 3") < pagina.find("Esta semana") < pagina.find("semana_03_v3.ipynb"))
        caso("el botón abre /notebooks/semana_03_v3.ipynb",
             '/user/x/notebooks/semana_03_v3.ipynb">Abrir cuadernillo' in pagina)
        caso("la línea de anteriores nombra base y _v2 con enlace",
             'class="anteriores"' in pagina and "/notebooks/semana_03.ipynb" in pagina
             and "/notebooks/semana_03_v2.ipynb" in pagina)
        caso("el título no lleva «(versión 3)»", "(versión" not in pagina)
        caso("semana_04 no se ve", "semana_04" not in pagina)

        print("Qué entrega «Guardar y entregar»:")
        caso("desde la versión abierta (_v3) se entrega _v3",
             pb._archivo_a_entregar("semana_03_v3") == ("semana_03", "semana_03_v3.ipynb"))
        caso("un nombre que no está en disco cae en la más nueva (no la base)",
             pb._archivo_a_entregar("semana_03_v9") == ("semana_03", "semana_03_v3.ipynb"),
             pb._archivo_a_entregar("semana_03_v9"))
        caso("desde una versión anterior abierta (_v2) se entrega esa: es lo que guardó",
             pb._archivo_a_entregar("semana_03_v2") == ("semana_03", "semana_03_v2.ipynb"))
        caso("desde la base abierta (custom.js manda 'semana_03') se entrega la base",
             pb._archivo_a_entregar("semana_03") == ("semana_03", "semana_03.ipynb"))
        caso("la tarea de nbgrader siempre es el código base",
             pb._tarea_de("semana_03_v3") == "semana_03")
        caso("una tarea no liberada no se entrega",
             pb._archivo_a_entregar("semana_04") == ("semana_04", None))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)

    print()
    if fallos:
        print(f"FALLARON {len(fallos)}: " + "; ".join(fallos))
        return 1
    print("Todo bien.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
