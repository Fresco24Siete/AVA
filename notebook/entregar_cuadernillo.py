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
     (.ava_publicados.json), que el panel lee sin volver a preguntar.
  6. Imprime en stdout el código del cuadernillo activo, que el entrypoint
     exporta como CUADERNILLO_CODIGO para que la telemetría lo etiquete.

Activo = la liberación más reciente que esté en ventana y no se haya publicado
con --sin-activar.

Si el servicio no responde, no falla: se queda con lo que ya tenía en disco y
la nota local, y el panel se dibuja igual. Un fallo del intercambio no puede
dejar al alumno sin sus cuadernillos.

No sobrescribe el trabajo del alumno nunca.
"""
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone

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
# constancia de entrega) sin tener que volver a llamar al servicio.
PUBLICADOS = os.path.join(CARPETA, ".ava_publicados.json")


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
            marca = "**Esta semana**" if c["id"] == activo else ""
            enlace = f"[abrir]({c['archivo']})"
            if c.get("anterior"):
                # Hubo una correccion. Se enlaza la version nueva y, aparte, la
                # que el alumno ya tenia: su trabajo esta ahi y no se toca.
                enlace += (f"<br/>corregido &middot; "
                           f"[tu version anterior]({c['anterior']})")
            lineas.append(f"| {marca} | {_titulo_bonito(c['id'])} | {enlace} |")
        lineas += [
            "",
            "---",
            "",
            "Para abrir uno, haz clic en su enlace. Si un cuadernillo se te "
            "cierra por fecha deja de aparecer aqui, pero lo que ya hiciste no "
            "se borra.",
        ]
    try:
        with open(INICIO, "w", encoding="utf-8") as f:
            json.dump(_nb_markdown("\n".join(lineas)), f, ensure_ascii=False)
    except OSError:
        pass


def _sha(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def _consultar(publicados):
    """Pregunta al servicio y actualiza `publicados` en sitio.

    Devuelve (pudo_consultar, entregas, descargas) donde `descargas` es
    {id: carpeta temporal con la liberación} para lo que hubo que traer. Quien
    llama borra esas carpetas.
    """
    try:
        from nbexchange_cliente import ava
        liberadas, entregas = ava.liberados()
    except Exception:
        return False, {}, {}

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

    # Lo que el docente retiró del servicio deja de estar publicado. El archivo
    # del alumno, si lo tenía, se queda donde está.
    for codigo in list(publicados):
        if codigo not in liberadas:
            del publicados[codigo]
    return True, entregas, descargas


def main():
    nota = _leer_json(PUBLICADOS, {})
    publicados = dict(nota.get("cuadernillos") or {})
    entregas = dict(nota.get("entregas") or {})

    consulto, entregas_nuevas, descargas = _consultar(publicados)
    if consulto:
        entregas = entregas_nuevas

    ahora = datetime.now(timezone.utc)
    registro = _leer_json(REGISTRO, {})
    _migrar_modelo_viejo(activo_de(publicados, ahora))
    entregados = []
    try:
        for codigo in sorted(publicados):
            info = publicados[codigo]
            if not _disponible(info, ahora):
                continue

            archivo = f"{codigo}.ipynb"
            destino = os.path.join(CARPETA, archivo)
            version = info.get("version", "")
            anterior = None

            if os.path.exists(destino):
                if version and registro.get(archivo, version) != version:
                    # El docente corrigio el cuadernillo despues de que este
                    # alumno ya lo tenia. NO se sobrescribe: su trabajo esta
                    # dentro. La version nueva se entrega al lado y el indice
                    # enlaza las dos.
                    anterior = archivo
                    n = 2
                    while os.path.exists(os.path.join(CARPETA, f"{codigo}_v{n}.ipynb")):
                        if registro.get(f"{codigo}_v{n}.ipynb") == version:
                            break          # esa correccion ya se le habia entregado
                        n += 1
                    archivo = f"{codigo}_v{n}.ipynb"
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

            entregados.append({"id": codigo, "archivo": archivo, "anterior": anterior})
    finally:
        for tmp in descargas.values():
            shutil.rmtree(tmp, ignore_errors=True)

    _guardar_json(REGISTRO, registro)
    _guardar_json(PUBLICADOS, {"cuadernillos": publicados, "entregas": entregas,
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
