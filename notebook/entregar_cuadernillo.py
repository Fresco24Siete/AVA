#!/usr/bin/env python3
"""Trae al alumno los cuadernillos que el instructor publicó vía nbgrader.

Lo decide el instructor al liberar la tarea en el servicio de intercambio
(nbexchange) con `publicar-cuadernillo`, NO el backend. Este módulo corre en el
contenedor del ALUMNO, al arrancar y cada vez que abre su panel, y:

  1. Pregunta al servicio qué tareas hay liberadas para su curso (lo responde
     para ese alumno y ese curso, autenticado con el token del contenedor).
  2. Trae las que no tenga o hayan cambiado, a una carpeta temporal.
  3. Lee la ventana de tiempo (abre/cierra) que el docente dejó dentro de la
     liberación (ava_publicacion.json) y descarta lo que está fuera de ella.
  4. Deja cada cuadernillo en /home/jovyan/work/<id>.ipynb. Si el alumno ya lo
     tenía y el docente corrigió el contenido, la versión nueva va al lado
     (<id>_v2.ipynb): su trabajo está dentro del anterior y no se toca.
  5. Escribe el índice (inicio.ipynb) y una nota local de qué hay publicado
     (.ava_publicados.json), que el panel lee sin volver a preguntar. En los
     dos aparece UNA entrada por tarea: la versión más nueva; las anteriores
     se nombran en una línea aparte (archivo, anteriores en la nota).
  6. Imprime en stdout el código del cuadernillo activo, que el entrypoint
     exporta como CUADERNILLO_CODIGO para que la telemetría lo etiquete.

Activo = la liberación más reciente que esté en ventana y no se haya publicado
con --sin-activar.

Si el servicio no responde, no falla: se queda con lo que ya tenía en disco y
la nota local, y el panel se dibuja igual. Un fallo del intercambio no puede
dejar al alumno sin sus cuadernillos.

No sobrescribe el trabajo del alumno nunca, y tampoco lo borra: lo que el
docente retira del servicio se MUEVE a archivados/ (que el índice nombra), y
solo cuando lleva ausente un buen rato seguido (ver ESPERA_RETIRADA).
"""
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timedelta, timezone

CURSO = os.environ.get("CURSO_ID", "curso_default")
DESTINO = os.environ.get("CUADERNILLO_DESTINO", "/home/jovyan/work/cuadernillo.ipynb")
CARPETA = os.path.dirname(DESTINO)

# El alumno abre `inicio.ipynb`: un indice con los cuadernillos publicados hasta
# hoy, marcando el de esta semana. Cada cuadernillo vive en `<id>.ipynb`.
INICIO = os.environ.get("CUADERNILLO_INICIO", os.path.join(CARPETA, "inicio.ipynb"))

# Qué versión de cada archivo tiene ya el alumno. Vive en su carpeta de trabajo
# -- es decir, en su volumen -- para sobrevivir a que se recree el contenedor.
REGISTRO = os.path.join(CARPETA, ".ava_versiones.json")

# Qué hay publicado, según la última vez que se pudo preguntar al servicio. Lo
# lee el panel (marca de «Esta semana», nombre del notebook para nbgrader,
# constancia de entrega) sin tener que volver a llamar al servicio. Lleva
# tambien, en `ausentes`, desde cuando falta cada tarea que dejo de verse
# liberada (ver ESPERA_RETIRADA): no hace falta otro fichero para eso.
PUBLICADOS = os.path.join(CARPETA, ".ava_publicados.json")

# A donde van los cuadernillos que el docente retiro del servicio. Se mueven,
# nunca se borran, y el indice (inicio.ipynb) los nombra.
ARCHIVADOS = os.path.join(CARPETA, "archivados")

# Cuanto tiene que llevar AUSENTE una tarea, de forma continuada, para tratarla
# como retirada. 2026-10-05: publicar una correccion hace 'retirar -> liberar'
# en el servicio (asi lo exige nbexchange) y durante esos segundos la tarea no
# esta aunque las demas sigan. Al alumno que cargaba su panel justo entonces se
# le iba el cuadernillo, con su trabajo, a archivados/ (o se le borraba): con
# 17 alumnos conectados en clase eso impedia publicar de dia. Quince minutos es
# muchisimo mas que esa ventana y poquisimo para una retirada de verdad, que
# no tiene prisa: nadie pierde nada porque el archivo se quede un rato mas.
ESPERA_RETIRADA = timedelta(minutes=15)


def _leer_json(ruta, por_defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, type(por_defecto)) else por_defecto
    except (OSError, ValueError):
        return por_defecto


def _guardar_json(ruta, datos):
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)
    except OSError:
        pass          # no vale la pena tumbar el arranque por esto


def _parse(ts):
    if not ts:
        return None
    try:
        f = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    return f if f.tzinfo else f.replace(tzinfo=timezone.utc)


def _disponible(entrada, ahora):
    """True si el cuadernillo esta dentro de su ventana de tiempo."""
    abre = _parse(entrada.get("abre"))
    cierra = _parse(entrada.get("cierra"))
    if abre and ahora < abre:
        return False
    if cierra and ahora > cierra:
        return False
    return True


def activo_de(publicados, ahora=None):
    """Cuál es el cuadernillo de esta semana, dado lo publicado.

    El liberado más reciente que está en ventana. Los publicados con
    --sin-activar (una errata corregida) ceden el turno a cualquier otro que
    sí active; solo si no hay ninguno otro, vale el que haya. Lo comparten el
    alumno (panel, telemetría) y el docente (su panel), para que los dos vean
    lo mismo.
    """
    ahora = ahora or datetime.now(timezone.utc)
    disponibles = [(info.get("timestamp", ""), codigo)
                   for codigo, info in publicados.items()
                   if _disponible(info, ahora)]
    activables = [c for c in disponibles
                  if publicados[c[1]].get("activar", True) is not False]
    elegibles = activables or disponibles
    return max(elegibles)[1] if elegibles else ""


def _titulo_bonito(codigo):
    """'semana_01' -> 'Semana 1'. Si no encaja, se devuelve el codigo tal cual."""
    partes = codigo.split("_")
    if len(partes) == 2 and partes[1].isdigit():
        return f"{partes[0].capitalize()} {int(partes[1])}"
    return codigo


def _nb_markdown(texto):
    return {
        "cells": [{"cell_type": "markdown", "metadata": {}, "source": [texto]}],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                    "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5,
    }


def _escribir_indice(entregados, activo):
    """Escribe el indice. Se regenera siempre: no contiene trabajo del alumno."""
    lineas = [
        "# Tus cuadernillos",
        "",
        "Aqui estan todos los cuadernillos publicados del curso. El de **esta "
        "semana** es el que tiene la marca; los anteriores siguen disponibles "
        "para repasar, y lo que ya respondiste en ellos se conserva.",
        "",
    ]
    if not entregados:
        lineas.append("_Todavia no hay ningun cuadernillo publicado._")
    else:
        lineas += ["| | Cuadernillo | Abrir |", "|---|---|---|"]
        for c in entregados:
            # Una fila por tarea, enlazando SOLO la version mas nueva. Si hubo
            # correcciones, las versiones que el alumno ya tenia siguen en su
            # carpeta (nunca se borran ni se mueven) y se nombran en una linea
            # discreta debajo, para que nadie crea que perdio su trabajo.
            marca = "**Esta semana**" if c["id"] == activo else ""
            enlace = f"[abrir]({c['archivo']})"
            anteriores = c.get("anteriores") or ([c["anterior"]] if c.get("anterior") else [])
            if anteriores:
                enlace += "<br/><small>" + _nota_anteriores(anteriores) + "</small>"
            lineas.append(f"| {marca} | {_titulo_bonito(c['id'])} | {enlace} |")
        lineas += [
            "",
            "---",
            "",
            "Para abrir uno, haz clic en su enlace. Si un cuadernillo se te "
            "cierra por fecha deja de aparecer aqui, pero lo que ya hiciste no "
            "se borra.",
        ]
    # 2026-10-05: archivados/ no lo nombraba nadie, asi que un cuadernillo
    # retirado era, para el alumno, un cuadernillo perdido. UNA linea, y solo
    # cuando hay algo dentro; va tambien cuando no queda nada publicado, que es
    # justo cuando mas falta hace.
    archivados = _archivados()
    if archivados:
        lineas += ["", _nota_archivados(archivados)]
    try:
        with open(INICIO, "w", encoding="utf-8") as f:
            json.dump(_nb_markdown("\n".join(lineas)), f, ensure_ascii=False)
    except OSError:
        pass


def _nota_anteriores(anteriores):
    """La linea que acompana a una tarea con correcciones: nombra las versiones
    viejas que el alumno conserva. Texto plano con enlaces; la comparten el
    indice y el panel para que digan lo mismo."""
    enlaces = ", ".join(f"[{a}]({a})" for a in anteriores)
    if len(anteriores) == 1:
        return f"tienes guardada una versión anterior: {enlaces}"
    return f"tienes guardadas versiones anteriores: {enlaces}"


def _archivados():
    """Los cuadernillos que hay en archivados/, por nombre; [] si no hay."""
    try:
        return sorted(a for a in os.listdir(ARCHIVADOS) if a.endswith(".ipynb"))
    except OSError:
        return []


def _nota_archivados(archivados):
    """La linea del indice que dice donde quedo lo que el docente retiro."""
    enlaces = ", ".join(f"[{a}](archivados/{a})" for a in archivados)
    return ("Hay cuadernillos retirados por el docente guardados en la carpeta "
            "`archivados/`; no se borraron, y lo que hubieras hecho en ellos "
            f"sigue ahí: {enlaces}")


def _sha(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def _tarea_de(codigo):
    """'semana_02_v3' -> 'semana_02'."""
    return re.sub(r"_v\d+$", "", codigo)


def _numero_version(archivo):
    """'semana_02_v3.ipynb' -> 3; 'semana_02.ipynb' (la base) -> 1."""
    m = re.search(r"_v(\d+)\.ipynb$", archivo)
    return int(m.group(1)) if m else 1


def versiones_en_disco(tarea, archivos):
    """Los archivos de `archivos` que son versiones de `tarea`, de la mas vieja
    a la mas nueva POR NOMBRE: 'semana_02.ipynb', '_v2', '_v3'...

    Una liberacion nueva nunca pisa la anterior: va al lado como <id>_vN.ipynb
    (ver main). Asi que, salvo un registro perdido, la de numero mas alto es
    la ultima que le llego al alumno.
    """
    propios = [a for a in archivos
               if a.endswith(".ipynb") and _tarea_de(a[:-6]) == tarea]
    return sorted(propios, key=_numero_version)


def _archivo_vigente(codigo, version, registro):
    """En que archivo vive (o va a vivir) la version publicada de `codigo`.

    Reglas, en orden:
      1. Si alguno de los archivos que el alumno ya tiene esta registrado con
         esta misma version, es ese (la mas nueva si hubiera varios).
      2. Si ninguno de sus archivos tiene registro (registro perdido, o de
         otro volumen), se asume que el mas nuevo por nombre es el vigente:
         es el lado seguro, porque lo contrario seria entregarle copias
         repetidas en cada arranque.
      3. Si no, la version publicada es una correccion que aun no tiene: va a
         un archivo nuevo al lado, <codigo>_v{N+1}.ipynb. NUNCA se pisa lo
         que ya tiene, porque su trabajo esta dentro.
    Sin archivos en disco, es la base <codigo>.ipynb.
    """
    try:
        en_disco = versiones_en_disco(codigo, os.listdir(CARPETA))
    except OSError:
        en_disco = []
    if not en_disco:
        return f"{codigo}.ipynb"
    if not version:
        return en_disco[-1]
    for archivo in reversed(en_disco):
        if registro.get(archivo) == version:
            return archivo
    # Un registro vacio ("") no es una version distinta: es que no se sabe.
    if not any(registro.get(a) for a in en_disco):
        return en_disco[-1]
    return f"{codigo}_v{_numero_version(en_disco[-1]) + 1}.ipynb"


def _destino_libre(archivo, ahora):
    """Una ruta dentro de archivados/ que todavia no exista.

    shutil.move sobre un nombre ocupado lo PISA sin avisar, y lo que hay ahi es
    trabajo de un alumno archivado antes: al nuevo se le pone la fecha, y un
    contador si hiciera falta.
    """
    destino = os.path.join(ARCHIVADOS, archivo)
    if not os.path.exists(destino):
        return destino
    base, ext = os.path.splitext(archivo)
    sello = ahora.strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(ARCHIVADOS, f"{base}_{sello}{ext}")
    n = 1
    while os.path.exists(destino):
        n += 1
        destino = os.path.join(ARCHIVADOS, f"{base}_{sello}_{n}{ext}")
    return destino


def _limpiar_retirados(liberadas, registro, previos, ausentes, ahora=None):
    """Archiva los cuadernillos que el docente retiró del servicio.

    Una tarea que el alumno tenía y ya no aparece liberada deja de ser tarea
    activa: sus archivos (todas sus versiones) se MUEVEN a CARPETA/archivados/.

    2026-10-05, tres cosas que antes no eran así y por qué:

      - Antirrebote. Una ausencia sola no es una retirada: publicar una
        corrección retira y vuelve a liberar, y a quien cargaba el panel en
        esos segundos se le iba el cuadernillo de su carpeta. La primera vez
        que una tarea falta solo se anota la hora en `ausentes` (que main()
        guarda en la nota local, .ava_publicados.json); si vuelve, la anotación
        se borra; solo se archiva si en una comprobación posterior sigue
        faltando y pasaron ESPERA_RETIRADA. Con una anotación ilegible, o con
        fecha futura (el reloj fue hacia atrás), la cuenta empieza de nuevo:
        en la duda, no tocar.
      - Nunca se borra un .ipynb. Lo que el alumno no había modificado se
        eliminaba con os.remove; pero «no modificado» se decidía comparando con
        un registro que puede estar perdido o ser de otro volumen, y mover es
        igual de barato y se puede deshacer.
      - No se borran la corrección del docente (.ava_correcciones/<tarea>.html)
        ni la constancia de entrega (.ava_entregas.json): son lo que le queda
        al alumno de una tarea ya entregada y calificada, y una retirada —menos
        aún una de segundos— no es motivo para quitárselas.

    `ausentes` es {tarea: desde cuándo falta, ISO en UTC} y se modifica en
    sitio, igual que `registro`.
    """
    ahora = ahora or datetime.now(timezone.utc)
    faltan = (set(previos.keys()) | {
        _tarea_de(a[:-6]) for a in registro if a.endswith(".ipynb")
    } | set(ausentes.keys())) - liberadas

    # Lo que volvio a estar liberado ya no lleva cuenta.
    for tarea in list(ausentes.keys()):
        if tarea not in faltan:
            del ausentes[tarea]

    codigos_retirados = set()
    for tarea in faltan:
        desde = ausentes.get(tarea)
        desde = _parse(desde) if isinstance(desde, str) else None
        if desde is None or desde > ahora:
            ausentes[tarea] = ahora.isoformat()
        elif ahora - desde >= ESPERA_RETIRADA:
            codigos_retirados.add(tarea)

    if not codigos_retirados:
        return

    try:
        archivos_en_disco = [f for f in os.listdir(CARPETA)
                             if f.endswith(".ipynb") and f != "inicio.ipynb"]
    except OSError:
        return        # no se pudo mirar: se reintenta en la proxima carga

    sin_mover = set()
    for archivo in archivos_en_disco:
        tarea = _tarea_de(archivo[:-6])
        if tarea not in codigos_retirados:
            continue
        try:
            os.makedirs(ARCHIVADOS, exist_ok=True)
            shutil.move(os.path.join(CARPETA, archivo), _destino_libre(archivo, ahora))
        except OSError:
            sin_mover.add(tarea)
            continue
        registro.pop(archivo, None)

    # Lo que se archivo entero deja de llevarse en la cuenta y en el registro.
    # Si algun archivo no se pudo mover, la tarea conserva su anotacion y su
    # registro, y se reintenta en la proxima carga.
    for tarea in codigos_retirados - sin_mover:
        ausentes.pop(tarea, None)
        for archivo in list(registro.keys()):
            if archivo.endswith(".ipynb") and _tarea_de(archivo[:-6]) == tarea:
                del registro[archivo]


def _consultar(publicados):
    """Pregunta al servicio y actualiza `publicados` en sitio.

    Devuelve (pudo_consultar, entregas, descargas, liberadas_codigos) donde
    `descargas` es {id: carpeta temporal con la liberación} para lo que hubo que
    traer. Quien llama borra esas carpetas.
    """
    try:
        from nbexchange_cliente import ava
        liberadas, entregas = ava.liberados()
    except Exception:
        return False, {}, {}, set()

    descargas = {}
    for codigo, info in liberadas.items():
        conocido = publicados.get(codigo, {})
        if conocido.get("timestamp") == info["timestamp"]:
            continue          # ya se sabía de esta liberación
        tmp = tempfile.mkdtemp(prefix="ava-pub-")
        try:
            ava.descargar(codigo, os.path.join(tmp, codigo))
        except Exception:
            shutil.rmtree(tmp, ignore_errors=True)
            continue
        carpeta = os.path.join(tmp, codigo)
        pub = ava.leer_publicacion(carpeta)
        notebooks = sorted(n for n in os.listdir(carpeta) if n.endswith(".ipynb"))
        principal = pub.get("notebook") if pub.get("notebook") in notebooks else (
            notebooks[0] if notebooks else "")
        if not principal:
            shutil.rmtree(tmp, ignore_errors=True)
            continue
        publicados[codigo] = {
            "timestamp": info["timestamp"],
            "notebook": principal,
            "abre": pub.get("abre"),
            "cierra": pub.get("cierra"),
            "activar": pub.get("activar", True),
            "version": str(pub.get("version") or _sha(os.path.join(carpeta, principal))),
        }
        descargas[codigo] = tmp

    # Lo que el docente retiró del servicio deja de estar publicado.
    for codigo in list(publicados):
        if codigo not in liberadas:
            del publicados[codigo]
    return True, entregas, descargas, set(liberadas.keys())


def main():
    nota = _leer_json(PUBLICADOS, {})
    previos = dict(nota.get("cuadernillos") or {})
    publicados = dict(previos)
    entregas = dict(nota.get("entregas") or {})
    # Desde cuando falta cada tarea que dejo de verse liberada (ver
    # _limpiar_retirados). Si la nota trae otra cosa que un objeto, no hay
    # cuenta: se empieza de cero, que es el lado en el que no se toca nada.
    ausentes = nota.get("ausentes")
    ausentes = dict(ausentes) if isinstance(ausentes, dict) else {}

    consulto, entregas_nuevas, descargas, liberadas = _consultar(publicados)
    if consulto:
        entregas = {k: v for k, v in entregas_nuevas.items() if k in liberadas}

    ahora = datetime.now(timezone.utc)
    registro = _leer_json(REGISTRO, {})

    # Una lista vacia nunca significa "el profesor retiro todo": nbexchange
    # devuelve [] tambien cuando contesta HTML (un 403 sin token, un 5xx), y
    # sin esta guarda eso vaciaba la carpeta del alumno en cada carga del panel.
    # Sin consulta valida tampoco se mueve la cuenta de `ausentes`: se guarda
    # tal cual estaba.
    if consulto and liberadas:
        _limpiar_retirados(liberadas, registro, previos, ausentes, ahora)

    _migrar_modelo_viejo(activo_de(publicados, ahora))
    entregados = []
    try:
        for codigo in sorted(publicados):
            info = publicados[codigo]
            if not _disponible(info, ahora):
                continue

            version = info.get("version", "")
            # Si el docente corrigio el cuadernillo despues de que este alumno
            # ya lo tenia, NO se sobrescribe: su trabajo esta dentro. La
            # version nueva va al lado (<codigo>_vN.ipynb) y es la UNICA que
            # se enlaza; las que ya tenia se nombran aparte (ver
            # _escribir_indice) y se quedan donde estan.
            archivo = _archivo_vigente(codigo, version, registro)
            destino = os.path.join(CARPETA, archivo)

            if not os.path.exists(destino):
                origen = _origen(codigo, info, descargas)
                if not origen:
                    continue
                try:
                    shutil.copyfile(origen, destino)
                except OSError:
                    continue
                registro[archivo] = version

            try:
                anteriores = [a for a in versiones_en_disco(codigo, os.listdir(CARPETA))
                              if a != archivo]
            except OSError:
                anteriores = []
            # El panel lee de aqui que archivo abrir y cuales son los viejos,
            # sin repetir esta logica.
            info["archivo"] = archivo
            info["anteriores"] = anteriores
            entregados.append({"id": codigo, "archivo": archivo, "anteriores": anteriores})
    finally:
        for tmp in descargas.values():
            shutil.rmtree(tmp, ignore_errors=True)

    _guardar_json(REGISTRO, registro)
    _guardar_json(PUBLICADOS, {"cuadernillos": publicados, "entregas": entregas,
                               "ausentes": ausentes,
                               "consultado": consulto,
                               "en": datetime.now(timezone.utc).isoformat()})
    activo = activo_de(publicados, ahora)
    _escribir_indice(entregados, activo)

    # El codigo que se devuelve etiqueta la telemetria y el cupo del tutor: es
    # el del cuadernillo de esta semana.
    return activo


def _es_aviso(ruta):
    """True si el .ipynb de esa ruta es un cartel puesto por una version vieja."""
    try:
        with open(ruta, encoding="utf-8") as f:
            return bool(json.load(f).get("metadata", {}).get("ava_aviso"))
    except Exception:
        # Ilegible o no es JSON: se trata como trabajo del alumno, que es el
        # lado seguro en el que equivocarse.
        return False


def _migrar_modelo_viejo(activo):
    """El trabajo del alumno estaba en 'cuadernillo.ipynb' a secas.

    Se renombra al nombre nuevo para que no lo pierda al pasar al indice. Solo
    si de verdad hay trabajo dentro: ahi es donde las versiones viejas
    escribian el cartel de "aun no hay cuadernillo".
    """
    if not activo:
        return
    destino = os.path.join(CARPETA, f"{activo}.ipynb")
    if (os.path.exists(DESTINO) and not os.path.exists(destino)
            and not _es_aviso(DESTINO)):
        try:
            shutil.move(DESTINO, destino)
        except OSError:
            pass


def _origen(codigo, info, descargas):
    """Ruta local del notebook liberado, trayéndolo si hace falta."""
    if codigo not in descargas:
        # Se sabía de esta liberación pero el archivo no está (el alumno lo
        # borró, o el registro es de otro volumen): se vuelve a traer.
        try:
            from nbexchange_cliente import ava
            tmp = tempfile.mkdtemp(prefix="ava-pub-")
            ava.descargar(codigo, os.path.join(tmp, codigo))
            descargas[codigo] = tmp
        except Exception:
            return None
    ruta = os.path.join(descargas[codigo], codigo, info.get("notebook", ""))
    return ruta if os.path.isfile(ruta) else None


if __name__ == "__main__":
    try:
        print(main())
    except Exception:
        # Nunca fallar el arranque del contenedor por esto.
        print("")
