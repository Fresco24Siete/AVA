"""Motor lúdico de los cuadernillos del AVA.

Qué es y qué NO es
------------------
Este motor pinta la capa de práctica del cuadernillo: quices, problemas de
ordenar, pistas escalonadas, barra de progreso e insignias. Da retroalimentación
inmediata y sin castigo, para que el estudiante se atreva a fallar.

**La nota no sale de aquí.** La nota y la telemetría salen de las celdas de
nbgrader (`grade_id: test_ejercicio_N`), que es lo que leen `custom.js` y
`api_export.py`. Si algún día este motor desaparece, el cuadernillo sigue siendo
calificable. Es deliberado: la capa lúdica corre en el kernel del alumno y él
puede reescribirla; por eso no decide nada que cuente.

Por qué vive en un módulo y no suelto en una celda
--------------------------------------------------
Al alumno solo le llega `work/cuadernillo.ipynb`, un archivo único: no hay dónde
poner un import. El generador de cada cuadernillo **incrusta el código de este
módulo** en la primera celda. Mantenerlo aquí permite editarlo, probarlo y
revisarlo como código normal en vez de como una cadena gigante.

Sin ipywidgets el motor no se cae: degrada a una versión de solo lectura que
muestra el enunciado y explica cómo responder. Así el cuadernillo nunca queda
en blanco por un problema de entorno.
"""

# --- Paleta e identidad visual ----------------------------------------------
# Sobria a propósito: el material visual son los diagramas, no los emojis.
AZUL, AZUL_OSC = "#2a78d6", "#10294d"
VERDE, VERDE_OSC = "#0f8a4a", "#0a5c31"
ROJO, AMBAR = "#c8392b", "#b57200"
GRIS, GRIS_CLARO, BORDE = "#52514e", "#f6f7f9", "#dfe3e8"
VIOLETA = "#5b4bc4"

_CSS = """
<style>
.ava-caja{border:1px solid %(borde)s;border-left:4px solid %(azul)s;border-radius:6px;
  padding:12px 14px;margin:8px 0;background:%(claro)s;font-family:system-ui,-apple-system,
  'Segoe UI',Roboto,sans-serif;font-size:14.5px;line-height:1.55;color:#1c1c1c;}
.ava-caja.ok{border-left-color:%(verde)s;background:#f2faf5;}
.ava-caja.mal{border-left-color:%(rojo)s;background:#fdf4f3;}
.ava-caja.pista{border-left-color:%(ambar)s;background:#fdf9ef;}
.ava-caja.reto{border-left-color:%(violeta)s;background:#f7f5fd;}
.ava-tit{font-weight:650;color:%(azuloscuro)s;margin-bottom:4px;}
.ava-caja.ok .ava-tit{color:%(verdeoscuro)s;}
.ava-caja.mal .ava-tit{color:%(rojo)s;}
.ava-caja.pista .ava-tit{color:%(ambar)s;}
.ava-barra-fondo{height:12px;background:#e9ecef;border-radius:6px;overflow:hidden;}
.ava-barra-relleno{height:100%%;background:linear-gradient(90deg,%(azul)s,%(violeta)s);
  border-radius:6px;transition:width .35s ease;}
.ava-meta{font-family:system-ui,sans-serif;font-size:13px;color:%(gris)s;margin-top:4px;}
.ava-tabla{border-collapse:collapse;font-family:system-ui,sans-serif;font-size:14px;margin:6px 0;}
.ava-tabla th,.ava-tabla td{border:1px solid %(borde)s;padding:6px 10px;text-align:left;}
.ava-tabla th{background:%(claro)s;color:%(azuloscuro)s;font-weight:600;}
.ava-svg{max-width:100%%;height:auto;display:block;margin:10px auto;}
.ava-pie{font-family:system-ui,sans-serif;font-size:12.5px;color:%(gris)s;
  text-align:center;margin-top:-4px;margin-bottom:12px;font-style:italic;}
/* Celdas de andamiaje: se esconde su código. En un quiz el código lleva la
   respuesta correcta como argumento, así que dejarlo a la vista es regalar el
   ejercicio; en una figura son 25 KB de SVG que no aportan nada. */
.cell:has(> .output_wrapper .ava-oculta) > .input{display:none;}
.ava-oculta{display:none;}
</style>
""" % {
    "borde": BORDE, "azul": AZUL, "claro": GRIS_CLARO, "verde": VERDE,
    "rojo": ROJO, "ambar": AMBAR, "violeta": VIOLETA, "azuloscuro": AZUL_OSC,
    "verdeoscuro": VERDE_OSC, "gris": GRIS,
}

# Marcas de acierto/error como SVG, no como emoji: se ven igual en todos los
# sistemas y no cambian de estilo según la fuente del navegador.
_ICONO_OK = (
    '<svg width="15" height="15" viewBox="0 0 16 16" style="vertical-align:-2px;margin-right:6px">'
    '<circle cx="8" cy="8" r="7.2" fill="%s"/>'
    '<path d="M4.6 8.3l2.2 2.2 4.6-4.9" fill="none" stroke="#fff" stroke-width="1.9" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>' % VERDE
)
_ICONO_MAL = (
    '<svg width="15" height="15" viewBox="0 0 16 16" style="vertical-align:-2px;margin-right:6px">'
    '<circle cx="8" cy="8" r="7.2" fill="%s"/>'
    '<path d="M5.4 5.4l5.2 5.2M10.6 5.4l-5.2 5.2" fill="none" stroke="#fff" stroke-width="1.9" '
    'stroke-linecap="round"/></svg>' % ROJO
)


try:  # El motor completo necesita ipywidgets; sin él se degrada, no falla.
    import ipywidgets as W
    HAY_WIDGETS = True
except ImportError:  # pragma: no cover - depende del entorno
    W = None
    HAY_WIDGETS = False

from IPython.display import HTML, display


def _html(texto):
    display(HTML(texto))


# Esconder la celda con CSS y no con JavaScript es deliberado: el JS de una
# salida corre una sola vez y en un momento que no controlamos (a veces antes de
# que la celda esté en el DOM), mientras que la regla CSS se aplica siempre, y
# también al recargar la página. Los metadatos no sirven: `jupyter.source_hidden`
# es de JupyterLab, y montar jupyter_contrib_nbextensions solo por esto no
# compensa. `:has()` lo soportan todos los navegadores desde 2023.
_HTML_ESCONDER = """
<style>
.cell:has(> .output_wrapper .ava-motor-marca) > .input{display:none;}
.cell.ava-ver-codigo:has(> .output_wrapper .ava-motor-marca) > .input{display:flex;}
.ava-motor-marca{font:12.5px system-ui,-apple-system,sans-serif;color:%(gris)s;margin:0 0 6px;}
.ava-motor-marca a{color:%(azul)s;text-decoration:none;border-bottom:1px dotted %(azul)s;cursor:pointer;}
</style>
<div class="ava-motor-marca">Motor del cuadernillo activo.
  <a onclick="this.closest('.cell').classList.toggle('ava-ver-codigo');return false;"
     >ver el codigo</a>
</div>
""" % {"gris": GRIS, "azul": AZUL}


def esconder_entrada():
    """Esconde el código de la celda que la llama, dejando un enlace para verlo.

    La usa la celda de arranque: son cientos de líneas de fontanería de widgets
    que no aportan nada a quien está aprendiendo a programar y que, si se
    muestran, ocupan la primera pantalla entera del cuadernillo.
    """
    _html(_HTML_ESCONDER)


class Motor:
    """Estado y componentes de un cuadernillo.

    Parameters
    ----------
    titulo : str
        Nombre del cuadernillo, para la barra de progreso y la insignia.
    meta_xp : int
        XP con el que se considera cumplida la práctica de la sesión.
    insignia : str
        Nombre de la insignia que se otorga al llegar a la meta.
    """

    def __init__(self, titulo, meta_xp=100, insignia="Sesión completada"):
        self.titulo = titulo
        self.meta_xp = meta_xp
        self.insignia = insignia
        self.xp = 0
        self._resueltos = set()     # claves ya acertadas: no suman XP dos veces
        self._pistas = {}           # clave -> pistas ya mostradas
        self._banco_pistas = {}     # clave -> lista de pistas
        self._barras = []           # widgets de barra vivos, para refrescarlos
        _html(_CSS)

    # -- XP y progreso ------------------------------------------------------
    def _sumar(self, clave, xp):
        """Suma XP una sola vez por clave. Reintentar nunca resta."""
        if clave in self._resueltos or xp <= 0:
            return 0
        self._resueltos.add(clave)
        self.xp += xp
        self._refrescar_barras()
        return xp

    def _fragmento_barra(self):
        pct = min(100, round(100 * self.xp / self.meta_xp)) if self.meta_xp else 0
        logro = (
            f'<span style="color:{VERDE};font-weight:600">Meta alcanzada: {self.insignia}</span>'
            if self.xp >= self.meta_xp else
            f"{self.meta_xp - self.xp} XP para la insignia «{self.insignia}»"
        )
        return (
            f'<div class="ava-barra-fondo"><div class="ava-barra-relleno" '
            f'style="width:{pct}%"></div></div>'
            f'<div class="ava-meta"><b>{self.xp}</b> / {self.meta_xp} XP &nbsp;·&nbsp; {logro}</div>'
        )

    def barra(self):
        """Barra de progreso que se actualiza sola al resolver ejercicios."""
        if not HAY_WIDGETS:
            _html(self._fragmento_barra())
            return
        w = W.HTML(self._fragmento_barra())
        self._barras.append(w)
        display(w)

    def _refrescar_barras(self):
        for w in self._barras:
            w.value = self._fragmento_barra()

    # -- Bloques de contenido ----------------------------------------------
    def _ocultar_codigo(self):
        """Marca la celda actual como andamiaje: su código deja de mostrarse."""
        _html('<div class="ava-oculta"></div>')

    def caja(self, titulo, cuerpo, tipo=""):
        """Recuadro de apoyo: nota, advertencia, reto, retroalimentación."""
        clase = ("ava-caja " + tipo).strip()
        tit = f'<div class="ava-tit">{titulo}</div>' if titulo else ""
        _html(f'<div class="{clase}">{tit}{cuerpo}</div>')

    def figura(self, svg, pie=""):
        """Muestra un diagrama ya renderizado (SVG incrustado) con su pie."""
        self._ocultar_codigo()
        _html(f'<div class="ava-svg">{svg}</div>'
              + (f'<div class="ava-pie">{pie}</div>' if pie else ""))

    def tabla(self, encabezados, filas):
        cab = "".join(f"<th>{c}</th>" for c in encabezados)
        cuerpo = "".join(
            "<tr>" + "".join(f"<td>{c}</td>" for c in fila) + "</tr>" for fila in filas
        )
        _html(f'<table class="ava-tabla"><tr>{cab}</tr>{cuerpo}</table>')

    # -- Pistas -------------------------------------------------------------
    def registrar_pistas(self, clave, pistas):
        """Guarda las pistas escalonadas de un ejercicio (de suave a directa)."""
        self._banco_pistas[clave] = list(pistas)

    def _boton_pista(self, clave, salida):
        pistas = self._banco_pistas.get(clave, [])
        if not pistas or not HAY_WIDGETS:
            return None
        boton = W.Button(description=f"Pista (0/{len(pistas)})",
                         layout=W.Layout(width="150px"))

        def _al_pulsar(_):
            n = self._pistas.get(clave, 0)
            if n >= len(pistas):
                return
            self._pistas[clave] = n + 1
            boton.description = f"Pista ({n + 1}/{len(pistas)})"
            if n + 1 == len(pistas):
                boton.disabled = True
            with salida:
                _html(f'<div class="ava-caja pista"><div class="ava-tit">'
                      f'Pista {n + 1} de {len(pistas)}</div>{pistas[n]}</div>')

        boton.on_click(_al_pulsar)
        return boton

    # -- Componentes interactivos -------------------------------------------
    def quiz(self, clave, xp, pregunta, opciones, correcta, explicacion="", pistas=()):
        """Pregunta de opción múltiple con verificación inmediata."""
        self._ocultar_codigo()
        if pistas:
            self.registrar_pistas(clave, pistas)
        if not HAY_WIDGETS:
            self.caja(pregunta, "<br>".join(f"• {o}" for o in opciones))
            return
        radio = W.RadioButtons(options=list(opciones), value=None,
                               layout=W.Layout(width="auto"))
        salida = W.Output()
        verificar = W.Button(description="Verificar", button_style="primary",
                             layout=W.Layout(width="130px"))

        def _al_verificar(_):
            salida.clear_output()
            with salida:
                if radio.value is None:
                    _html('<div class="ava-caja">Elige una opción antes de verificar.</div>')
                elif radio.value == correcta:
                    ganado = self._sumar(clave, xp)
                    extra = f" (+{ganado} XP)" if ganado else " (ya lo tenías)"
                    _html(f'<div class="ava-caja ok"><div class="ava-tit">'
                          f'{_ICONO_OK}Correcto{extra}</div>{explicacion}</div>')
                else:
                    _html(f'<div class="ava-caja mal"><div class="ava-tit">'
                          f'{_ICONO_MAL}Todavía no</div>Vuelve a leer con calma e '
                          f'inténtalo otra vez. Los intentos no restan.</div>')

        verificar.on_click(_al_verificar)
        botones = [verificar]
        pista = self._boton_pista(clave, salida)
        if pista:
            botones.append(pista)
        self.caja("", f"<b>{pregunta}</b>")
        display(W.VBox([radio, W.HBox(botones), salida]))

    def ordenar(self, clave, xp, piezas, orden_correcto, explicacion="", pistas=()):
        """Problema tipo Parsons: ordenar pasos dados, sin escribir sintaxis.

        `piezas` es un dict {etiqueta: texto} y `orden_correcto` la lista de
        etiquetas en el orden esperado.
        """
        self._ocultar_codigo()
        if pistas:
            self.registrar_pistas(clave, pistas)
        etiquetas = list(piezas)
        if not HAY_WIDGETS:
            self.caja("Ordena estos pasos",
                      "<br>".join(f"<b>{k}</b>. {v}" for k, v in piezas.items()))
            return
        selectores = [
            W.Dropdown(options=[("—", None)] + [(f"{k}. {piezas[k]}", k) for k in etiquetas],
                       value=None, description=f"Paso {i + 1}:",
                       style={"description_width": "70px"},
                       layout=W.Layout(width="560px"))
            for i in range(len(orden_correcto))
        ]
        salida = W.Output()
        verificar = W.Button(description="Verificar", button_style="primary",
                             layout=W.Layout(width="130px"))

        def _al_verificar(_):
            salida.clear_output()
            elegido = [s.value for s in selectores]
            with salida:
                if None in elegido:
                    _html('<div class="ava-caja">Faltan pasos por elegir.</div>')
                elif len(set(elegido)) != len(elegido):
                    _html('<div class="ava-caja mal"><div class="ava-tit">'
                          f'{_ICONO_MAL}Repetiste un paso</div>Cada paso se usa una sola vez.</div>')
                elif elegido == list(orden_correcto):
                    ganado = self._sumar(clave, xp)
                    extra = f" (+{ganado} XP)" if ganado else " (ya lo tenías)"
                    _html(f'<div class="ava-caja ok"><div class="ava-tit">'
                          f'{_ICONO_OK}Ese es el orden{extra}</div>{explicacion}</div>')
                else:
                    # Decir CUÁNTOS van bien, no cuáles: se mantiene el reto.
                    bien = sum(1 for a, b in zip(elegido, orden_correcto) if a == b)
                    _html(f'<div class="ava-caja mal"><div class="ava-tit">'
                          f'{_ICONO_MAL}Todavía no</div>Tienes {bien} de '
                          f'{len(orden_correcto)} pasos en su sitio. Pregúntate cuál '
                          f'no puede ocurrir sin que otro haya ocurrido antes.</div>')

        verificar.on_click(_al_verificar)
        botones = [verificar]
        pista = self._boton_pista(clave, salida)
        if pista:
            botones.append(pista)
        display(W.VBox(selectores + [W.HBox(botones), salida]))

    def comprobar(self, clave, xp, prueba, valor, ok="", pistas=()):
        """Verificador de una respuesta calculada por el estudiante en su celda.

        `prueba` es una función que recibe el valor y devuelve True/False, o una
        tupla (False, "por qué está mal") para explicar el fallo.
        """
        if pistas:
            self.registrar_pistas(clave, pistas)
        try:
            resultado = prueba(valor)
        except Exception as err:  # el estudiante puede pasar cualquier cosa
            resultado = (False, f"Tu respuesta rompió el verificador: <code>{err}</code>")
        detalle = ""
        if isinstance(resultado, tuple):
            resultado, detalle = resultado
        if resultado:
            ganado = self._sumar(clave, xp)
            extra = f" (+{ganado} XP)" if ganado else " (ya lo tenías)"
            self.caja(f"{_ICONO_OK}Correcto{extra}", ok or "Sigue al siguiente.", "ok")
        else:
            cuerpo = detalle or "Revisa tu resultado y vuelve a ejecutar la celda."
            if self._banco_pistas.get(clave):
                cuerpo += (" Si te atascas, ejecuta <code>pista(\"%s\")</code>." % clave)
            self.caja(f"{_ICONO_MAL}Todavía no", cuerpo, "mal")

    def pista(self, clave):
        """Pista siguiente sin widgets: pensada para llamarse desde una celda."""
        pistas = self._banco_pistas.get(clave, [])
        if not pistas:
            self.caja("", f"No hay pistas registradas para {clave}.")
            return
        n = self._pistas.get(clave, 0)
        if n >= len(pistas):
            self.caja("Ya viste todas las pistas",
                      "Este es buen momento para preguntarle al asistente — pero "
                      "pídele que te <b>pregunte</b>, no que te resuelva.", "pista")
            return
        self._pistas[clave] = n + 1
        self.caja(f"Pista {n + 1} de {len(pistas)}", pistas[n], "pista")

    # -- Cierre --------------------------------------------------------------
    def radar(self, afirmaciones, mensaje=""):
        """Autoevaluación de cierre. No da XP ni nota: es el espejo del alumno."""
        if not HAY_WIDGETS:
            self.caja("Marca lo que ya puedas hacer",
                      "<br>".join(f"• {a}" for a in afirmaciones))
            return
        casillas = [W.Checkbox(description=a, indent=False,
                               layout=W.Layout(width="max-content"))
                    for a in afirmaciones]
        salida = W.Output()
        boton = W.Button(description="Ver mi radar", layout=W.Layout(width="150px"))

        def _al_pulsar(_):
            salida.clear_output()
            marcadas = sum(c.value for c in casillas)
            faltan = [c.description for c in casillas if not c.value]
            with salida:
                if not faltan:
                    _html('<div class="ava-caja ok"><div class="ava-tit">'
                          f'{_ICONO_OK}Todo marcado</div>{mensaje}</div>')
                else:
                    lista = "".join(f"<li>{t}</li>" for t in faltan)
                    _html('<div class="ava-caja pista"><div class="ava-tit">'
                          f'{marcadas} de {len(casillas)}</div>Lo que falta no es un '
                          f'problema, es tu plan de la semana:<ul>{lista}</ul>'
                          'Empieza por ahí con el asistente o en la próxima clase.</div>')

        boton.on_click(_al_pulsar)
        display(W.VBox(casillas + [boton, salida]))

    def cerrar(self, logros, puente=""):
        """Tarjeta final: insignia si llegó a la meta, y puente a la sesión siguiente."""
        lista = "".join(f"<li>{l}</li>" for l in logros)
        if self.xp >= self.meta_xp:
            estado = (f'<div style="color:{VERDE};font-weight:600">'
                      f'Insignia obtenida: {self.insignia} ({self.xp} XP)</div>')
        else:
            estado = (f'<div style="color:{GRIS}">Llevas {self.xp} de {self.meta_xp} XP. '
                      f'Puedes volver a cualquier ejercicio: los intentos no restan.</div>')
        self.caja(f"Cierre — {self.titulo}",
                  f"<ul>{lista}</ul>{estado}"
                  + (f'<div style="margin-top:8px">{puente}</div>' if puente else ""),
                  "reto")
