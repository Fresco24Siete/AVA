#!/usr/bin/env python3
"""Renderiza los diagramas .mmd (Mermaid) a SVG optimizado, listos para embeber.

Al alumno solo le llega un archivo: `work/cuadernillo.ipynb` (lo copia
`entregar-cuadernillo` desde el manifest). No viajan imágenes ni assets. Por eso
los diagramas se pre-renderizan aquí a SVG y el generador del cuadernillo los
inserta **dentro** del notebook.

Se pre-renderiza en vez de dibujar Mermaid en el navegador porque el contenedor
del alumno no tiene Node ni salida a internet garantizada, y porque nbclassic no
ejecuta `<script>` de una celda markdown.

Requiere Node (solo en la máquina de quien autora, nunca en el contenedor):

    python3 notebook/cuadernillos/diagramas/render.py

Los .svg resultantes se versionan en git: así construir un cuadernillo no exige
Node y el diagrama no cambia solo porque cambió la versión de Mermaid.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTES = os.path.join(AQUI, "mmd")
SALIDA = os.path.join(AQUI, "svg")
HUELLAS = os.path.join(AQUI, ".huellas.json")

# Una etiqueta con < o > se corta en silencio: C{saldo >= pasaje} se dibuja como
# «saldo = pasaje» y nadie se entera hasta que un estudiante lee mal la condición.
# Comprobado: entrecomillar NO basta para estos dos, hay que escribir la entidad —
# C{"saldo &gt;= pasaje"}. Otros signos (: ; , %) pasan tal cual.
SOSPECHOSOS = ("<", ">")
REMEDIO = {"<": "&lt;", ">": "&gt;"}

# Los paréntesis son otro caso: sin comillas rompen el parser (y eso Mermaid sí
# lo grita, así que no hace falta avisar), y entre comillas se dibujan bien.
# Comprobado también que la entidad &#40; NO sirve: se dibuja literalmente.
PARENTESIS = ("(", ")")

# Nodo de Mermaid: identificador seguido de su etiqueta entre delimitadores de
# forma. Se capturan los delimitadores para poder quitarlos y quedarse con el
# texto real: A([Inicio]) -> «Inicio», B[/Leer dato/] -> «Leer dato».
# La alternativa `"[^"]*"` va primero a propósito: si la etiqueta está
# entrecomillada hay que llegar hasta la comilla de cierre, no pararse en el
# primer paréntesis que aparezca dentro («print(4 + 9)» es una etiqueta válida).
NODO = re.compile(
    r"\b[A-Za-z_][\w]*\s*"
    r"(\(\(|\(\[|\[\[|\[\(|\{\{|\[|\{|\()"
    r"(\"[^\"]*\"|.+?)"
    r"(\)\)|\]\)|\]\]|\)\]|\}\}|\]|\}|\))"
)
BORDES_FORMA = "/\\<>|"

# Con texto SVG (htmlLabels desactivado) `<br/>` sí parte la línea, pero
# cualquier otra etiqueta HTML se dibuja literalmente: `<b>Total</b>` aparece con
# los signos incluidos. Comprobado renderizando.
HTML_QUE_NO_FUNCIONA = re.compile(r"</?(?!br\b)[a-zA-Z][a-zA-Z0-9]*\b[^>]*>")

CONFIG = {
    "theme": "neutral",
    # htmlLabels:false -> el texto sale como <text> SVG de verdad, no como HTML
    # dentro de un <foreignObject>. Necesario para que el diagrama se vea igual
    # embebido en el notebook y para que svgo pueda comprimirlo.
    "htmlLabels": False,
    "flowchart": {"htmlLabels": False, "curve": "basis", "useMaxWidth": True},
    "themeVariables": {
        "fontFamily": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
        "fontSize": "15px",
        "primaryColor": "#e8f0fb",
        "primaryTextColor": "#10294d",
        "primaryBorderColor": "#2a78d6",
        "lineColor": "#52514e",
        "secondaryColor": "#f3eefe",
        "tertiaryColor": "#fdf6e3",
    },
}


# Mermaid mete su CSS en un <style> con selectores por id y por clase, así que
# los plugins de svgo que renombran ids, mueven estilos o quitan atributos por
# "redundantes" rompen el dibujo sin dar ningún error.
SVGO_CONFIG = """export default {
  multipass: true,
  plugins: [
    { name: 'preset-default',
      params: { overrides: {
        cleanupIds: false,
        inlineStyles: false,
        minifyStyles: false,
        mergeStyles: false,
        removeUnknownsAndDefaults: false,
        removeUselessStrokeAndFill: false,
        removeHiddenElems: false,
        convertShapeToPath: false,
        mergePaths: false,
      }},
    },
  ],
};
"""


def _revisar_etiquetas(nombre, texto):
    """Avisa de etiquetas con caracteres que Mermaid descarta si no van citadas."""
    avisos = []
    for n, linea in enumerate(texto.splitlines(), 1):
        cuerpo = linea.split("%%")[0]
        for apertura, etiqueta, _ in NODO.findall(cuerpo):
            etiqueta = etiqueta.strip().strip(BORDES_FORMA).strip()
            # Los < > de una marca HTML los reporta la comprobación de abajo con
            # su propio consejo; aquí solo interesan los que el autor escribió
            # como comparadores («saldo > pasaje»).
            sin_marcas = re.sub(r"</?[a-zA-Z][a-zA-Z0-9]*\b[^>]*>", "", etiqueta)
            malos = [c for c in SOSPECHOSOS if c in sin_marcas]
            citada = etiqueta.startswith('"') and etiqueta.endswith('"')
            if not citada and any(c in sin_marcas for c in PARENTESIS):
                avisos.append(
                    f"  {nombre}:{n}: la etiqueta «{etiqueta}» tiene paréntesis "
                    f"sin comillas y Mermaid no la sabrá leer. Entrecomíllala: "
                    f'["{sin_marcas}"]. No uses la entidad &#40;, se dibuja literal.'
                )
            if malos:
                arreglo = ", ".join(f"{c} -> {REMEDIO[c]}" for c in sorted(set(malos)))
                avisos.append(
                    f"  {nombre}:{n}: la etiqueta «{etiqueta}» se dibujará mal; "
                    f"Mermaid descarta esos caracteres sin avisar. Usa la entidad "
                    f"({arreglo}). Entrecomillar no basta."
                )
            etiquetas_html = HTML_QUE_NO_FUNCIONA.findall(etiqueta)
            if etiquetas_html:
                avisos.append(
                    f"  {nombre}:{n}: la etiqueta «{etiqueta}» lleva HTML "
                    f"({', '.join(sorted(set(etiquetas_html)))}) que se dibujará "
                    f"literalmente, con los signos incluidos. Solo <br/> funciona; "
                    f"para destacar, usa el color del nodo (style)."
                )
    return avisos


def _huella(texto):
    payload = texto + json.dumps(CONFIG, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _cargar_huellas():
    try:
        with open(HUELLAS, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def main(argv):
    forzar = "--forzar" in argv
    solo_revisar = "--revisar" in argv

    if not shutil.which("npx"):
        print("[ERROR] No encontré 'npx'. Necesitas Node para renderizar los .mmd.")
        print("        Los .svg ya versionados siguen sirviendo: si no cambiaste")
        print("        ningún diagrama, no hace falta ejecutar este script.")
        return 2

    os.makedirs(SALIDA, exist_ok=True)
    fuentes = sorted(
        f for f in os.listdir(FUENTES) if f.endswith(".mmd")
    ) if os.path.isdir(FUENTES) else []
    if not fuentes:
        print(f"[AVISO] No hay diagramas en {FUENTES}")
        return 0

    avisos = []
    for nombre in fuentes:
        with open(os.path.join(FUENTES, nombre), encoding="utf-8") as f:
            avisos += _revisar_etiquetas(nombre, f.read())
    if avisos:
        print("[AVISO] Etiquetas que Mermaid puede truncar:")
        print("\n".join(avisos))
    if solo_revisar:
        return 1 if avisos else 0

    ruta_config = os.path.join(SALIDA, ".mermaid.json")
    with open(ruta_config, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f)
    ruta_svgo = os.path.join(SALIDA, ".svgo.config.mjs")
    with open(ruta_svgo, "w", encoding="utf-8") as f:
        f.write(SVGO_CONFIG)

    huellas = {} if forzar else _cargar_huellas()
    nuevas = dict(huellas)
    hechos, saltados = 0, 0

    for nombre in fuentes:
        base = nombre[:-4]
        origen = os.path.join(FUENTES, nombre)
        destino = os.path.join(SALIDA, base + ".svg")
        with open(origen, encoding="utf-8") as f:
            texto = f.read()
        h = _huella(texto)
        if huellas.get(base) == h and os.path.exists(destino):
            saltados += 1
            continue

        # --svgId: Mermaid mete su CSS con el selector #<id>. Sin un id propio
        # por diagrama, dos diagramas en el mismo notebook se pisan los estilos.
        cmd_mmdc = [
            "npx", "-y", "@mermaid-js/mermaid-cli@11",
            "-i", origen, "-o", destino,
            "-b", "transparent", "-c", ruta_config,
            "--svgId", f"dia-{base}",
        ]
        r = subprocess.run(cmd_mmdc, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[ERROR] Mermaid falló con {nombre}:\n{r.stderr.strip()[:800]}")
            return 3

        # svgo baja el SVG de ~100 KB a ~25 KB. Importa: el SVG va incrustado en
        # el .ipynb, y el notebook entero viaja al navegador del alumno.
        # Con la configuración por defecto de svgo bajaría a 21 KB, pero rompe el
        # dibujo: las etiquetas de las aristas ("Si"/"No") salen como cuadros
        # negros. Comprobado a ojo comparando los tres renderizados.
        r = subprocess.run(
            ["npx", "-y", "svgo@3", "--config", ruta_svgo, "-i", destino, "-o", destino],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"[AVISO] svgo falló con {base}, queda el SVG sin optimizar.")

        nuevas[base] = h
        hechos += 1
        print(f"[OK] {base}.svg  ({os.path.getsize(destino) // 1024} KB)")

    with open(HUELLAS, "w", encoding="utf-8") as f:
        json.dump(nuevas, f, indent=1, sort_keys=True)

    print(f"\n{hechos} diagrama(s) renderizado(s), {saltados} sin cambios.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
