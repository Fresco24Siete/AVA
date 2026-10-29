#!/usr/bin/env python3
"""Construye los cuadernillos del curso y los deja listos para nbgrader.

    python3 notebook/cuadernillos/build.py            # todos
    python3 notebook/cuadernillos/build.py semana_01  # uno solo
    python3 notebook/cuadernillos/build.py --legible  # motor sin comprimir (depuración)

Qué hace y por qué en este orden:

1. Cada `semana_XX/generador.py` describe su cuadernillo en Python y devuelve un
   objeto `Cuadernillo`. El notebook es una salida generada, no una fuente que se
   edite a mano: así el contenido se revisa en un diff legible y no en el JSON de
   un .ipynb.
2. El resultado se escribe en `notebook/notebook_semana/<codigo>/cuadernillo.ipynb`.
   Esa carpeta va a `/opt/plantillas` en la imagen y `entrypoint.sh` la siembra en
   `source/<codigo>` de nbgrader. De ahí el instructor hace «Generate» (que borra
   las soluciones) y publica con `publicar-cuadernillo <codigo>`.
3. Se valida el resultado: pares de celdas de nbgrader bien formados y
   `grade_id` únicos. Un par mal formado no da error visible en Jupyter, pero
   deja el ejercicio fuera de la nota Y fuera de la telemetría.
"""
import importlib.util
import json
import re
import zlib
import base64
import os
import sys

# Sin caché de bytecode, a propósito.
#
# El `.pyc` guarda el mtime de la fuente en SEGUNDOS enteros y lo compara junto
# con el tamaño. Si alguien edita un generador y reconstruye dentro del mismo
# segundo sin cambiar el tamaño —cambiar un «20» por un «95» no lo cambia—,
# Python da la caché por buena y esto construye el cuadernillo VIEJO sin
# que nada avise. Reproducido el 2026-09-22.
#
# Es la misma forma de fallar que dejó al profesor con la semana 03 rota en
# clase: una copia vieja que nadie detecta porque todo dice OK. Construir tarda
# segundos; no vale la pena arriesgarse por ahorrarlos.
sys.dont_write_bytecode = True


def _estimar_minutos(nb):
    """Los minutos que pide el contenido, segun estimar_tiempo.py.

    Se importa en vez de copiarse: si el metodo cambia, tiene que cambiar en un
    solo sitio o las dos cuentas dejan de compararse entre si.
    """
    import estimar_tiempo
    return estimar_tiempo.estimar_nb(nb)["total"]

AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.abspath(os.path.join(AQUI, "..", "notebook_semana"))
# Mapeo ejercicio -> competencias. Va aparte del notebook a propósito: es diseño
# del curso, no dato del alumno, y el backend lo resuelve por JOIN. Así, corregir
# una etiqueta mal puesta corrige todo el histórico ya recogido.
MAPEO = os.path.join(AQUI, "competencias.json")


def _leer_mapeo():
    """El mapeo acumula todas las semanas, no solo las que se construyen ahora."""
    try:
        with open(MAPEO, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _escribir_mapeo(mapeo):
    with open(MAPEO, "w", encoding="utf-8") as f:
        json.dump(mapeo, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def _generadores():
    for nombre in sorted(os.listdir(AQUI)):
        ruta = os.path.join(AQUI, nombre, "generador.py")
        if os.path.isdir(os.path.join(AQUI, nombre)) and os.path.exists(ruta):
            yield nombre, ruta


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(f"generador_{nombre}", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    if not hasattr(modulo, "construir"):
        raise AttributeError(f"{ruta} debe definir una función construir(**opciones)")
    return modulo


def _total_del_banner(nb):
    """El total de puntos que la portada le pinta al estudiante, o None.

    Vive en contenido.py, escrito a mano, mientras el de verdad lo suma el
    constructor: dos copias del mismo numero. Se desincronizaron al recortar
    las semanas 03-06 —el banner siguio diciendo 80 puntos cuando ya eran 65,
    55, 50 y 65— y nadie lo vio porque el texto viaja COMPRIMIDO dentro de la
    celda del motor, asi que un grep sobre el .ipynb no lo encuentra.
    """
    for celda in nb["cells"]:
        fuente = "".join(celda.get("source", []))
        for b64 in re.findall(r"b64decode\([\"']([A-Za-z0-9+/=]+)[\"']\)", fuente):
            try:
                texto = zlib.decompress(base64.b64decode(b64)).decode("utf-8", "replace")
            except Exception:
                continue
            m = re.search(r"(\d+) puntos · \d+ XP", texto)
            if m:
                return int(m.group(1))
    return None


def _minutos_declarados(nb):
    """Lo que suman los « · N min» de las cabeceras de seccion."""
    total = 0
    for celda in nb["cells"]:
        if celda.get("cell_type") != "markdown":
            continue
        for m in re.finditer(r"·\s*(\d+)\s*min\b", "".join(celda.get("source", []))):
            total += int(m.group(1))
    return total


def _minutos_en_prosa(nb):
    """Cifras de duración sueltas en el texto, fuera de las cabeceras.

    La guarda de las cabeceras no las ve, y por ahí se escapó una: semana_02
    siguió diciéndole al alumno «Son 165 minutos» cuando ya eran 121, y el
    commit que lo daba por corregido no lo estaba. Un número escrito en prosa
    envejece igual que uno escrito en una cabecera.
    """
    encontrados = []
    for celda in nb["cells"]:
        if celda.get("cell_type") != "markdown":
            continue
        texto = "".join(celda.get("source", []))
        # Dentro de un enunciado, un número de minutos es parte del problema y
        # no una promesa sobre el cuadernillo: semana_02 dice «las 6:00 (que son
        # 360 minutos desde medianoche)» y eso está bien como está.
        if "### Ejercicio" in texto:
            continue
        for m in re.finditer(r"[Ss]on\s+(\d+)\s*minutos", texto):
            encontrados.append(int(m.group(1)))
    return encontrados


def validar(nb):
    """Revisa los contratos que el AVA da por supuestos. Devuelve lista de fallos."""
    fallos = []

    # Y los minutos que anuncia contra los que el contenido de verdad pide.
    # Mismo problema que los puntos, y el que el profesor leyó en pantalla el
    # 2026-09-22: la semana 03 anunciaba 153 minutos para seis ejercicios.
    # El número lo escribe una persona y el contenido lo mueve otra, así que
    # sin esta comprobación vuelve a envejecer en cuanto alguien toque algo.
    for suelto in _minutos_en_prosa(nb):
        if suelto != _minutos_declarados(nb):
            fallos.append(
                f"el texto anuncia «son {suelto} minutos» y las secciones suman "
                f"{_minutos_declarados(nb)}: quita la cifra suelta, que envejece "
                f"sola, o cuádrala")

    declarados = _minutos_declarados(nb)
    if declarados:
        real = _estimar_minutos(nb)
        if abs(declarados - real) > max(5, 0.15 * real):
            fallos.append(
                f"las secciones anuncian {declarados} min y el contenido pide "
                f"unos {real:.0f}: ajusta los minutos de c.seccion(...) "
                f"(`python3 estimar_tiempo.py` los calcula)")

    # El banner de la portada contra la suma real de nbgrader.
    declarado = _total_del_banner(nb)
    if declarado is not None:
        real = sum(c.get("metadata", {}).get("nbgrader", {}).get("points", 0)
                   for c in nb["cells"]
                   if c.get("metadata", {}).get("nbgrader", {}).get("grade"))
        if declarado != int(real):
            fallos.append(
                f"la portada anuncia {declarado} puntos y los ejercicios suman "
                f"{int(real)}: actualiza el total en contenido.py")

    ids = {}
    soluciones, pruebas = set(), set()

    for i, celda in enumerate(nb["cells"]):
        ng = celda.get("metadata", {}).get("nbgrader")
        if not ng:
            continue
        gid = ng.get("grade_id")
        if not gid:
            fallos.append(f"celda {i}: metadata de nbgrader sin grade_id")
            continue
        if gid in ids:
            fallos.append(f"grade_id duplicado '{gid}' (celdas {ids[gid]} y {i})")
        ids[gid] = i
        if ng.get("solution"):
            soluciones.add(gid)
        if ng.get("grade"):
            pruebas.add(gid)
            if not gid.startswith("test_"):
                fallos.append(
                    f"'{gid}' califica pero no empieza por 'test_': custom.js no "
                    f"emitirá telemetría de este ejercicio"
                )
            if not ng.get("points"):
                fallos.append(f"'{gid}' califica pero no tiene points")

    for gid in sorted(soluciones):
        if f"test_{gid}" not in pruebas:
            fallos.append(f"'{gid}' no tiene su celda de prueba 'test_{gid}'")
    for gid in sorted(pruebas):
        base = gid[len("test_"):]
        if base not in soluciones:
            fallos.append(f"'{gid}' no tiene su celda de solución '{base}'")

    if "tutor_ia" not in nb["metadata"]:
        fallos.append("falta metadata.tutor_ia (el panel del tutor no se dibujará)")
    return fallos


def main(argv):
    legible = "--legible" in argv
    pedidos = [a for a in argv if not a.startswith("-")]

    disponibles = dict(_generadores())
    if not disponibles:
        print(f"[ERROR] No hay generadores en {AQUI}")
        return 2
    if pedidos:
        faltan = [p for p in pedidos if p not in disponibles]
        if faltan:
            print(f"[ERROR] No existe: {', '.join(faltan)}")
            print(f"        Disponibles: {', '.join(disponibles)}")
            return 2
        objetivo = {k: disponibles[k] for k in pedidos}
    else:
        objetivo = disponibles

    problemas = 0
    mapeo = _leer_mapeo()
    for nombre, ruta in objetivo.items():
        print(f"\n== {nombre} ==")
        modulo = _cargar(nombre, ruta)
        cuadernillo = modulo.construir(motor_comprimido=not legible)
        salida = os.path.join(DESTINO, cuadernillo.codigo, "cuadernillo.ipynb")
        cuadernillo.escribir(salida)

        # Un ejercicio sin competencia no da ningún error: simplemente
        # desaparece de los análisis. Por eso se avisa aquí.
        # Un ejercicio que deja de existir en el generador no deja de existir
        # en la telemetría: sus intentos siguen en la base bajo su id, y el JOIN
        # que los clasifica necesita la etiqueta. Por eso el mapeo CONSERVA las
        # etiquetas de los ids retirados en vez de borrarlas. Se decide por los
        # ejercicios que existen, no por los etiquetados: si a un ejercicio vivo
        # se le quita la etiqueta a propósito, no hay que resucitársela.
        existentes = {f"ejercicio_{n}" for n, _ in cuadernillo._ejercicios}
        retirados = {k: v for k, v in mapeo.get(cuadernillo.codigo, {}).items()
                     if k not in existentes}
        mapeo[cuadernillo.codigo] = {**retirados, **cuadernillo.competencias}
        if retirados:
            print(f"     Mapeo: se conservan {len(retirados)} id(s) retirado(s) con su "
                  f"etiqueta, por el histórico: {', '.join(sorted(retirados))}")
        sin_etiquetar = [f"ejercicio_{n}" for n, _ in cuadernillo._ejercicios
                         if f"ejercicio_{n}" not in cuadernillo.competencias]
        if sin_etiquetar:
            print(f"     [AVISO] sin competencia asignada: {', '.join(sin_etiquetar)}")
            print( "             No fallan, pero no aparecerán en el análisis por competencia.")
        else:
            print(f"     Competencias: {len(cuadernillo.competencias)} ejercicios etiquetados")

        with open(salida, encoding="utf-8") as f:
            nb = json.load(f)
        fallos = validar(nb)
        if fallos:
            problemas += len(fallos)
            print("     [FALLA LA VALIDACION]")
            for f_ in fallos:
                print(f"       - {f_}")
        else:
            print("     Validación: contratos de nbgrader, telemetría y tutor correctos.")

    _escribir_mapeo(mapeo)
    print(f"\nMapeo de competencias en {os.path.relpath(MAPEO)}")
    print( "Para cargarlo al backend:  cargar-competencias")

    if problemas:
        print(f"\n{problemas} problema(s). Los cuadernillos se escribieron igual, "
              f"pero no los publiques así.")
        return 1
    print("\nListo. Para publicarlos, dentro del contenedor del instructor:")
    for nombre in objetivo:
        print(f"  formgrader -> Generate '{nombre}'  y luego  publicar-cuadernillo {nombre}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
