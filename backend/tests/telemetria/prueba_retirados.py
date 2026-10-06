#!/usr/bin/env python3
"""Qué pasa con los cuadernillos del alumno cuando una tarea deja de verse liberada.

2026-10-05. Publicar una corrección hace 'retirar -> liberar' en el servicio de
intercambio (así lo exige nbexchange), y durante esos segundos la tarea no está
aunque las demás sigan. `entregar_cuadernillo._limpiar_retirados` corre en el
contenedor de cada alumno en cada carga del panel: al que cargaba justo
entonces se le iba el cuadernillo con su trabajo a archivados/ —que ningún
índice nombraba— o, si no lo había modificado, se le borraba. Con 17 alumnos
conectados en clase eso impedía publicar de día. Esto comprueba que ahora:

  - una ausencia breve que vuelve no mueve nada, llegue la misma versión o una
    corrección (que va al lado como _v2, sin pisar);
  - solo una ausencia continuada de más de 15 minutos archiva, y archivar es
    MOVER: ni lo modificado ni lo no modificado se borran;
  - la corrección del docente (.ava_correcciones/) y la constancia de entrega
    (.ava_entregas.json) siguen ahí después de una retirada;
  - el índice (inicio.ipynb) nombra archivados/ en UNA línea cuando hay algo;
  - una lista vacía del servicio, o el servicio caído, no mueve nada nunca;
  - una anotación ilegible o con fecha futura (reloj hacia atrás) no archiva:
    vuelve a empezar la cuenta.

Corre sin Jupyter ni red, como prueba_indice_versiones.py: carpeta temporal, un
doble de `nbexchange_cliente.ava` (así `_consultar` corre de verdad) y un reloj
que se adelanta a mano en vez de esperar quince minutos.

    python3 backend/tests/telemetria/prueba_retirados.py
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import types
from datetime import datetime, timedelta, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
NOTEBOOK = os.path.join(REPO, "notebook")

T0 = datetime(2026, 10, 5, 15, 0, 0, tzinfo=timezone.utc)      # 10:00 en Bogotá

fallos = []
total = 0


def caso(nombre, ok, detalle=""):
    global total
    total += 1
    print(("  OK    " if ok else "  FALLO ") + nombre + (f"  -> {detalle}" if detalle and not ok else ""))
    if not ok:
        fallos.append(nombre)


class Reloj(datetime):
    """datetime cuyo now() devuelve la hora que diga la prueba."""
    actual = T0

    @classmethod
    def now(cls, tz=None):
        return cls.actual


class Servicio:
    """Doble de nbexchange_cliente.ava: lo que el servicio tiene liberado."""

    def __init__(self):
        self.liberadas = {}       # {codigo: {"timestamp": str, "version": str}}
        self.modo = "normal"      # 'vacio': contesta [] ; 'caido': lanza

    def liberar(self, codigo, version, timestamp):
        self.liberadas[codigo] = {"timestamp": timestamp, "version": version}

    def retirar(self, codigo):
        self.liberadas.pop(codigo, None)

    # --- lo que entregar_cuadernillo usa de `ava` ---
    def liberados(self):
        if self.modo == "caido":
            raise RuntimeError("el servicio no responde")
        if self.modo == "vacio":
            return {}, {}
        return {c: {"timestamp": i["timestamp"]} for c, i in self.liberadas.items()}, {}

    def descargar(self, codigo, destino):
        os.makedirs(destino, exist_ok=True)
        with open(os.path.join(destino, "cuadernillo.ipynb"), "w", encoding="utf-8") as f:
            f.write(plantilla(codigo, self.liberadas[codigo]["version"]))

    def leer_publicacion(self, carpeta):
        codigo = os.path.basename(carpeta)
        return {"notebook": "cuadernillo.ipynb", "version": self.liberadas[codigo]["version"]}


def plantilla(codigo, version):
    return json.dumps({"cells": [{"cell_type": "markdown", "metadata": {},
                                  "source": [f"{codigo} {version}"]}],
                       "metadata": {}, "nbformat": 4, "nbformat_minor": 5})


TRABAJO = json.dumps({"cells": [{"cell_type": "code", "metadata": {}, "outputs": [],
                                 "execution_count": 1,
                                 "source": ["# lo que el alumno ya resolvio\n", "x = 42"]}],
                      "metadata": {}, "nbformat": 4, "nbformat_minor": 5})


def leer(ruta):
    """El texto del archivo, o None si no está: que falte es justo lo que
    esta prueba tiene que poder contar como FALLO, no como traza."""
    try:
        with open(ruta, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def leer_json(ruta):
    try:
        return json.loads(leer(ruta))
    except (TypeError, ValueError):
        return {}


def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)


class Escenario:
    """Una carpeta de alumno recién montada, con su módulo y su servicio.

    El alumno tiene tres tareas liberadas y en disco:
      semana_01  sin tocar (nunca se retira: es la que mantiene la lista no vacía)
      semana_04  CON TRABAJO, en dos versiones (base y _v2), con corrección del
                 docente y constancia de entrega
      semana_06  sin modificar: idéntica a la plantilla registrada
    """

    def __init__(self):
        self.carpeta = tempfile.mkdtemp(prefix="ava-prueba-retirados-")
        os.environ["CUADERNILLO_DESTINO"] = os.path.join(self.carpeta, "cuadernillo.ipynb")
        os.environ.pop("CUADERNILLO_INICIO", None)

        self.servicio = Servicio()
        paquete = types.ModuleType("nbexchange_cliente")
        paquete.ava = self.servicio
        sys.modules["nbexchange_cliente"] = paquete
        sys.modules["nbexchange_cliente.ava"] = self.servicio

        spec = importlib.util.spec_from_file_location(
            "entregar_cuadernillo", os.path.join(NOTEBOOK, "entregar_cuadernillo.py"))
        self.ec = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ec)
        self.ec.datetime = Reloj
        Reloj.actual = T0

        ec = self.ec
        ts = "2026-09-28 10:00:00.000000 UTC"
        for codigo in ("semana_01", "semana_04", "semana_06"):
            self.servicio.liberar(codigo, "v1", ts)
        self.servicio.liberadas["semana_04"]["version"] = "v2"

        escribir(self.ruta("semana_01.ipynb"), plantilla("semana_01", "v1"))
        escribir(self.ruta("semana_04.ipynb"), TRABAJO)
        escribir(self.ruta("semana_04_v2.ipynb"), TRABAJO.replace("42", "43"))
        escribir(self.ruta("semana_06.ipynb"), plantilla("semana_06", "v1"))
        escribir(self.ruta(".ava_correcciones", "semana_04.html"), "<p>8.5 de 10</p>")
        escribir(self.ruta(".ava_entregas.json"),
                 json.dumps({"semana_04": {"en": "2026-10-01T15:00:00+00:00"}}))
        # El registro guarda la version publicada de cada archivo. La de
        # semana_06 es ademas el SHA de lo que hay en disco: «sin modificar»,
        # que es lo que el codigo anterior borraba con os.remove.
        sha06 = ec._sha(self.ruta("semana_06.ipynb"))
        self.servicio.liberadas["semana_06"]["version"] = sha06
        escribir(self.ruta(".ava_versiones.json"), json.dumps({
            "semana_01.ipynb": "v1", "semana_04.ipynb": "v1",
            "semana_04_v2.ipynb": "v2", "semana_06.ipynb": sha06}))
        escribir(self.ruta(".ava_publicados.json"), json.dumps({
            "consultado": True, "en": "2026-10-05T14:00:00+00:00", "entregas": {},
            "cuadernillos": {
                c: {"timestamp": ts, "notebook": "cuadernillo.ipynb",
                    "version": self.servicio.liberadas[c]["version"]}
                for c in ("semana_01", "semana_04", "semana_06")}}))

    def ruta(self, *partes):
        return os.path.join(self.carpeta, *partes)

    def cargar_panel(self, minutos=0, segundos=0):
        """Lo que hace el panel al abrirse, con el reloj en T0 + lo indicado."""
        Reloj.actual = T0 + timedelta(minutes=minutos, seconds=segundos)
        return self.ec.main()

    def cuadernillos(self):
        return sorted(a for a in os.listdir(self.carpeta)
                      if a.endswith(".ipynb") and a != "inicio.ipynb")

    def archivados(self):
        try:
            return sorted(os.listdir(self.ruta("archivados")))
        except OSError:
            return []

    def nota(self):
        return leer_json(self.ruta(".ava_publicados.json"))

    def indice(self):
        with open(self.ruta("inicio.ipynb"), encoding="utf-8") as f:
            return "".join(json.load(f)["cells"][0]["source"])

    def cerrar(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)


TODOS = ["semana_01.ipynb", "semana_04.ipynb", "semana_04_v2.ipynb", "semana_06.ipynb"]


def lineas_archivados(indice):
    return [l for l in indice.splitlines() if "archivados/" in l]


def rebote_misma_version():
    print("Ausencia breve que vuelve (retirar -> liberar de la MISMA versión):")
    e = Escenario()
    try:
        e.servicio.retirar("semana_04")
        e.cargar_panel()
        caso("con la tarea ausente, no se mueve ni se borra ningún cuadernillo",
             e.cuadernillos() == TODOS and e.archivados() == [], (e.cuadernillos(), e.archivados()))
        caso("el trabajo del alumno está intacto", leer(e.ruta("semana_04.ipynb")) == TRABAJO)
        caso("la ausencia queda anotada en la nota local, con su hora",
             e.nota().get("ausentes") == {"semana_04": T0.isoformat()}, e.nota().get("ausentes"))
        caso("el índice no habla de archivados/", lineas_archivados(e.indice()) == [])

        e.servicio.liberar("semana_04", "v2", "2026-10-05 15:00:05.000000 UTC")
        e.cargar_panel(segundos=10)
        caso("al volver, siguen los mismos archivos: ni copia nueva ni archivo",
             e.cuadernillos() == TODOS and e.archivados() == [], (e.cuadernillos(), e.archivados()))
        caso("al volver, la anotación se borra", e.nota().get("ausentes") == {}, e.nota().get("ausentes"))
        fila4 = [l for l in e.indice().splitlines() if "Semana 4" in l]
        caso("el índice vuelve a enlazar Semana 4, una vez, a su versión vigente",
             len(fila4) == 1 and "[abrir](semana_04_v2.ipynb)" in fila4[0], fila4)

        # La cuenta es de ausencia CONTINUADA: una segunda ausencia, veinte
        # minutos despues de la primera, empieza de cero.
        e.servicio.retirar("semana_04")
        e.cargar_panel(minutos=20)
        caso("otra ausencia 20 min después empieza la cuenta de cero: nada se mueve",
             e.cuadernillos() == TODOS and e.archivados() == []
             and e.nota().get("ausentes") == {"semana_04": (T0 + timedelta(minutes=20)).isoformat()},
             (e.cuadernillos(), e.nota().get("ausentes")))
    finally:
        e.cerrar()


def rebote_con_correccion():
    print("Ausencia breve que vuelve con una CORRECCIÓN (versión nueva):")
    e = Escenario()
    try:
        e.servicio.retirar("semana_04")
        e.cargar_panel()
        e.servicio.liberar("semana_04", "v3", "2026-10-05 15:00:05.000000 UTC")
        e.cargar_panel(segundos=10)
        caso("la corrección llega al lado como _v3, sin pisar nada",
             e.cuadernillos() == sorted(TODOS + ["semana_04_v3.ipynb"]) and e.archivados() == [],
             (e.cuadernillos(), e.archivados()))
        caso("lo que el alumno tenía en la base y en _v2 sigue igual",
             leer(e.ruta("semana_04.ipynb")) == TRABAJO
             and leer(e.ruta("semana_04_v2.ipynb")) == TRABAJO.replace("42", "43"))
        caso("_v3 es la plantilla corregida",
             leer(e.ruta("semana_04_v3.ipynb")) == plantilla("semana_04", "v3"))
        fila4 = [l for l in e.indice().splitlines() if "Semana 4" in l]
        caso("una sola fila de Semana 4, que abre _v3 y nombra las anteriores",
             len(fila4) == 1 and "[abrir](semana_04_v3.ipynb)" in fila4[0]
             and "versiones anteriores" in fila4[0] and "semana_04_v2.ipynb" in fila4[0], fila4)
        caso("la anotación se borra", e.nota().get("ausentes") == {})
    finally:
        e.cerrar()


def retirada_de_verdad():
    print("Ausencia de más de 15 minutos (el docente retiró semana_04 y semana_06):")
    e = Escenario()
    try:
        e.servicio.retirar("semana_04")
        e.servicio.retirar("semana_06")
        e.cargar_panel()
        caso("primera vez que faltan: nada se mueve", e.cuadernillos() == TODOS and e.archivados() == [])
        e.cargar_panel(minutos=14, segundos=59)
        caso("a los 14:59 siguen en su sitio", e.cuadernillos() == TODOS and e.archivados() == [],
             (e.cuadernillos(), e.archivados()))
        caso("la anotación conserva la PRIMERA hora, no la de la última comprobación",
             e.nota().get("ausentes") == {"semana_04": T0.isoformat(), "semana_06": T0.isoformat()},
             e.nota().get("ausentes"))

        e.cargar_panel(minutos=16)
        caso("a los 16 min salen de la carpeta de trabajo; semana_01 se queda",
             e.cuadernillos() == ["semana_01.ipynb"], e.cuadernillos())
        caso("los tres archivos están en archivados/: lo modificado (dos versiones de la "
             "misma tarea) y lo NO modificado",
             e.archivados() == ["semana_04.ipynb", "semana_04_v2.ipynb", "semana_06.ipynb"],
             e.archivados())
        caso("el trabajo archivado es, byte a byte, el del alumno",
             e.archivados()[:1] == ["semana_04.ipynb"]
             and leer(e.ruta("archivados", "semana_04.ipynb")) == TRABAJO
             and leer(e.ruta("archivados", "semana_04_v2.ipynb")) == TRABAJO.replace("42", "43"))
        caso("lo no modificado se archivó (antes se borraba con os.remove)",
             os.path.isfile(e.ruta("archivados", "semana_06.ipynb"))
             and leer(e.ruta("archivados", "semana_06.ipynb")) == plantilla("semana_06", "v1"))
        caso("la corrección del docente sigue ahí",
             os.path.isfile(e.ruta(".ava_correcciones", "semana_04.html"))
             and leer(e.ruta(".ava_correcciones", "semana_04.html")) == "<p>8.5 de 10</p>")
        caso("la constancia de entrega sigue ahí",
             leer_json(e.ruta(".ava_entregas.json"))
             == {"semana_04": {"en": "2026-10-01T15:00:00+00:00"}},
             leer(e.ruta(".ava_entregas.json")))
        indice = e.indice()
        caso("el índice nombra archivados/ en UNA línea",
             len(lineas_archivados(indice)) == 1, lineas_archivados(indice))
        linea = (lineas_archivados(indice) or [""])[0]
        caso("esa línea dice que los retiró el docente y enlaza cada archivo",
             "docente" in linea and "retir" in linea
             and all(f"(archivados/{a})" in linea for a in e.archivados()), linea)
        caso("lo archivado no sale como fila de la tabla",
             not any(l.startswith("|") and "emana 4" in l for l in indice.splitlines())
             and "[abrir](semana_01.ipynb)" in indice)
        registro = leer_json(e.ruta(".ava_versiones.json"))
        caso("el registro y la anotación quedan limpios",
             sorted(registro) == ["semana_01.ipynb"] and e.nota().get("ausentes") == {},
             (registro, e.nota().get("ausentes")))

        e.cargar_panel(minutos=17)
        caso("otra carga del panel no cambia nada más, y el índice sigue nombrándolos",
             e.cuadernillos() == ["semana_01.ipynb"] and len(e.archivados()) == 3
             and len(lineas_archivados(e.indice())) == 1, (e.cuadernillos(), e.archivados()))

        # Si el docente la vuelve a liberar despues, llega una copia limpia y
        # lo archivado no se toca.
        e.servicio.liberar("semana_04", "v3", "2026-10-05 16:00:00.000000 UTC")
        e.cargar_panel(minutos=60)
        caso("una liberación posterior llega limpia y lo archivado sigue en archivados/",
             e.cuadernillos() == ["semana_01.ipynb", "semana_04.ipynb"]
             and leer(e.ruta("semana_04.ipynb")) == plantilla("semana_04", "v3")
             and leer(e.ruta("archivados", "semana_04.ipynb")) == TRABAJO, e.cuadernillos())
    finally:
        e.cerrar()


def no_pisa_lo_archivado():
    print("Archivar no pisa lo que ya había en archivados/:")
    e = Escenario()
    try:
        escribir(e.ruta("archivados", "semana_04.ipynb"), "archivado en otra ocasion")
        e.servicio.retirar("semana_04")
        e.cargar_panel()
        e.cargar_panel(minutos=16)
        nombres = e.archivados()
        caso("lo que ya estaba archivado con ese nombre se conserva",
             leer(e.ruta("archivados", "semana_04.ipynb")) == "archivado en otra ocasion")
        otros = [n for n in nombres if n.startswith("semana_04_2026") and n.endswith(".ipynb")]
        caso("el trabajo del alumno entra al lado, con la fecha en el nombre",
             len(otros) == 1 and leer(e.ruta("archivados", otros[0])) == TRABAJO, nombres)
    finally:
        e.cerrar()


def lista_vacia_o_servicio_caido():
    for modo, titulo in (("vacio", "Lista vacía del servicio"), ("caido", "Servicio caído")):
        print(f"{titulo} (nunca es «el docente retiró todo»):")
        e = Escenario()
        try:
            e.servicio.modo = modo
            e.cargar_panel()
            e.cargar_panel(minutos=60)
            caso(f"[{modo}] tras una hora así, nada se movió ni se borró",
                 e.cuadernillos() == TODOS and e.archivados() == [], (e.cuadernillos(), e.archivados()))
            caso(f"[{modo}] no se anotó ninguna ausencia", not e.nota().get("ausentes"),
                 e.nota().get("ausentes"))
            caso(f"[{modo}] corrección y constancia intactas",
                 os.path.isfile(e.ruta(".ava_correcciones", "semana_04.html"))
                 and "semana_04" in leer_json(e.ruta(".ava_entregas.json")))

            # Aunque hubiera una anotacion vieja pendiente: sin una lista
            # valida no se decide nada, y la anotacion se conserva.
            nota = e.nota()
            nota["ausentes"] = {"semana_04": (T0 - timedelta(hours=3)).isoformat()}
            escribir(e.ruta(".ava_publicados.json"), json.dumps(nota))
            e.cargar_panel(minutos=61)
            caso(f"[{modo}] ni con una anotación vencida se archiva sin una lista válida",
                 e.cuadernillos() == TODOS and e.archivados() == []
                 and e.nota().get("ausentes") == nota["ausentes"],
                 (e.cuadernillos(), e.nota().get("ausentes")))
        finally:
            e.cerrar()


def en_la_duda_no_tocar():
    print("Anotaciones corruptas y reloj hacia atrás (en la duda, no tocar):")
    malas = [
        ("texto que no es una fecha", {"semana_04": "ayer por la tarde"}),
        ("un número", {"semana_04": 1759676400}),
        ("null", {"semana_04": None}),
        ("`ausentes` no es un objeto", ["semana_04"]),
        ("fecha futura: el reloj fue hacia atrás", {"semana_04": (T0 + timedelta(hours=2)).isoformat()}),
    ]
    for nombre, ausentes in malas:
        e = Escenario()
        try:
            nota = e.nota()
            nota["ausentes"] = ausentes
            escribir(e.ruta(".ava_publicados.json"), json.dumps(nota))
            e.servicio.retirar("semana_04")
            e.cargar_panel(minutos=30)
            ahora = (T0 + timedelta(minutes=30)).isoformat()
            caso(f"{nombre}: no se archiva, y la cuenta empieza ahora",
                 e.cuadernillos() == TODOS and e.archivados() == []
                 and e.nota().get("ausentes") == {"semana_04": ahora},
                 (e.cuadernillos(), e.nota().get("ausentes")))
            e.cargar_panel(minutos=46)
            caso(f"{nombre}: 16 min después de esa cuenta nueva, sí se archiva",
                 e.archivados() == ["semana_04.ipynb", "semana_04_v2.ipynb"]
                 and leer(e.ruta("archivados", "semana_04.ipynb")) == TRABAJO, e.archivados())
        finally:
            e.cerrar()

    # El reloj retrocede DESPUES de anotar: la anotacion queda en el futuro.
    e = Escenario()
    try:
        e.servicio.retirar("semana_04")
        e.cargar_panel(minutos=30)
        e.cargar_panel(minutos=5)
        caso("el reloj retrocede 25 min tras anotar: no se archiva y se vuelve a anotar",
             e.cuadernillos() == TODOS and e.archivados() == []
             and e.nota().get("ausentes") == {"semana_04": (T0 + timedelta(minutes=5)).isoformat()},
             e.nota().get("ausentes"))
    finally:
        e.cerrar()


def main():
    rebote_misma_version()
    rebote_con_correccion()
    retirada_de_verdad()
    no_pisa_lo_archivado()
    lista_vacia_o_servicio_caido()
    en_la_duda_no_tocar()

    print()
    if fallos:
        print(f"FALLARON {len(fallos)} de {total}: " + "; ".join(fallos))
        return 1
    print(f"Todo bien ({total} casos).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
