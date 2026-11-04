"""Pruebas del motor de pseudocódigo.

Se usa `unittest` de la biblioteca estándar y no pytest a propósito: estas
pruebas tienen que poder correrse dentro de la imagen del AVA, que solo trae lo
que trae, y desde la máquina de quien mantenga el cuadernillo sin instalar nada.

    python3 -m unittest discover notebook/cuadernillos/motor

Lo que se protege aquí es, sobre todo, el contrato de robustez: ningún
pseudocódigo mal escrito puede producir un traceback, porque al otro lado hay
una celda de nbgrader que quedaría en cero con un mensaje ilegible.
"""

import contextlib
import io
import os
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pseudo_uis as ps  # noqa: E402


SVG = "{http://www.w3.org/2000/svg}"


def silencio():
    """Se traga lo que imprimen las funciones que pintan.

    Varias funciones del motor imprimen a propósito (el eco de `input()`, el
    guion de Flowgorithm, la degradación sin widgets). Sin esto, correr las
    pruebas llenaría la terminal y escondería el resumen de unittest.
    """
    return contextlib.redirect_stdout(io.StringIO())

# El programa de referencia de §6.3, tal cual.
PAPELERIA = """Algoritmo CostoDeFotocopias
    // La papelería de la Carrera 9, frente a la UIS
    Definir copias, total Como Entero
    Constante PRECIO_COPIA <- 100
    Constante ANILLADO <- 2500

    Escribir "¿Cuántas copias vas a sacar?"
    Leer copias

    total <- copias * PRECIO_COPIA + ANILLADO

    Escribir "Total a pagar: $", total
FinAlgoritmo"""


def envolver(cuerpo, nombre="T"):
    """Mete un fragmento dentro de un algoritmo mínimo."""
    return f"Algoritmo {nombre}\n{cuerpo}\nFinAlgoritmo"


class ProgramaDeReferencia(unittest.TestCase):
    """§6.3: el programa del laboratorio ejecuta y da lo que el diseño promete."""

    def test_salida_exacta(self):
        r = ps.ejecutar_pseudo(PAPELERIA, entradas=["40"])
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida,
                         "¿Cuántas copias vas a sacar?\nTotal a pagar: $6500\n")

    def test_memoria_y_tipos(self):
        r = ps.ejecutar_pseudo(PAPELERIA, entradas=["40"])
        self.assertEqual(r.memoria["copias"], 40)
        self.assertEqual(r.memoria["total"], 6500)
        self.assertEqual(r.tipos["total"], "Entero")
        self.assertEqual(r.constantes, {"PRECIO_COPIA", "ANILLADO"})
        self.assertEqual(r.instrucciones_usadas,
                         {"Definir", "Constante", "Escribir", "Leer", "Asignar"})
        self.assertEqual(r.error, None)
        self.assertEqual(r.error_corto, "")

    def test_otras_entradas(self):
        for copias, total in [("1", 2600), ("0", 2500), ("100", 12500)]:
            with self.subTest(copias=copias):
                r = ps.ejecutar_pseudo(PAPELERIA, entradas=[copias])
                self.assertTrue(r.ok, r.error_corto)
                self.assertEqual(r.memoria["total"], total)

    def test_traza_paso_a_paso(self):
        r = ps.ejecutar_pseudo(PAPELERIA, entradas=["40"])
        # Siete instrucciones ejecutables: Definir, dos Constante, Escribir,
        # Leer, la asignación y el Escribir final.
        self.assertEqual(len(r.pasos), 7)
        self.assertEqual([p.n for p in r.pasos], list(range(1, 8)))
        self.assertEqual(r.tabla_traza(["copias", "total"]),
                         [(None, None), (None, None), (None, None),
                          (None, None), (40, None), (40, 6500), (40, 6500)])
        # La salida acumulada crece, no se repite entera en cada paso.
        self.assertEqual(r.pasos[3].salida, "¿Cuántas copias vas a sacar?\n")
        self.assertEqual(r.pasos[-1].salida, r.salida)

    def test_pie_explicativo_sustituye_valores(self):
        """§8.2: el motor pone los valores reales en la frase, como el profesor."""
        r = ps.ejecutar_pseudo(PAPELERIA, entradas=["40"])
        self.assertIn("40 * 100 + 2500 = 6500", r.pasos[5].explicacion)
        self.assertIn("Se creó la constante PRECIO_COPIA con el valor 100",
                      r.pasos[1].explicacion)
        self.assertIn('Se tomó "40" de la cola de entradas', r.pasos[4].explicacion)


class Traductor(unittest.TestCase):
    """§6.4: la tabla de equivalencia, caso por caso."""

    def traducir(self, codigo):
        return ps.traducir_a_python(codigo).split("\n")

    def linea(self, cuerpo, n=2, cabeza=""):
        """La línea `n` del Python que sale de un algoritmo mínimo."""
        return self.traducir(envolver(cabeza + cuerpo if cabeza else cuerpo))[n - 1]

    def test_programa_de_referencia_completo(self):
        esperado = (
            "# --- CostoDeFotocopias ---\n"
            "# La papelería de la Carrera 9, frente a la UIS\n"
            "copias = 0; total = 0\n"
            "PRECIO_COPIA = 100\n"
            "ANILLADO = 2500\n"
            "\n"
            'print("¿Cuántas copias vas a sacar?")\n'
            "copias = int(input())\n"
            "\n"
            "total = copias * PRECIO_COPIA + ANILLADO\n"
            "\n"
            'print("Total a pagar: $", total, sep="")\n')
        self.assertEqual(ps.traducir_a_python(PAPELERIA), esperado)

    def test_cabecera_y_cierre(self):
        py = self.traducir(envolver("    Definir n Como Entero", "MiAlgoritmo"))
        self.assertEqual(py[0], "# --- MiAlgoritmo ---")
        self.assertEqual(len(py), 3)          # la línea de FinAlgoritmo va vacía
        self.assertEqual(py[2].strip(), "")

    def test_comentario(self):
        self.assertEqual(self.linea("    // texto"), "# texto")

    def test_definir_por_tipo(self):
        casos = [("Definir n Como Entero", "n = 0"),
                 ("Definir x Como Real", "x = 0.0"),
                 ("Definir s Como Cadena", 's = ""'),
                 ("Definir b Como Logico", "b = False"),
                 ("Definir a, b Como Entero", "a = 0; b = 0")]
        for pseudo, python in casos:
            with self.subTest(pseudo=pseudo):
                self.assertEqual(self.linea("    " + pseudo), python)

    def test_constante(self):
        self.assertEqual(self.linea("    Constante PASAJE <- 3200"),
                         "PASAJE = 3200")

    def test_leer_segun_el_tipo_declarado(self):
        casos = [("Entero", "copias", "copias = int(input())"),
                 ("Real", "x", "x = float(input())"),
                 ("Cadena", "s", "s = input()")]
        for tipo, nombre, python in casos:
            with self.subTest(tipo=tipo):
                codigo = envolver(f"    Definir {nombre} Como {tipo}\n"
                                  f"    Leer {nombre}")
                self.assertEqual(self.traducir(codigo)[2], python)

    def test_leer_varias_variables(self):
        codigo = envolver("    Definir a, b Como Entero\n    Leer a, b")
        self.assertEqual(self.traducir(codigo)[2],
                         "a = int(input()); b = int(input())")

    def test_escribir(self):
        codigo = envolver("    Definir n Como Entero\n"
                          '    Escribir "Hola ", n')
        self.assertEqual(self.traducir(codigo)[2], 'print("Hola ", n, sep="")')

    def test_escribir_sin_saltar(self):
        codigo = envolver("    Definir x Como Entero\n    Escribir x Sin Saltar")
        self.assertEqual(self.traducir(codigo)[2], 'print(x, end="")')

    def test_asignacion(self):
        codigo = envolver("    Definir a, b, total Como Entero\n"
                          "    total <- a + b")
        self.assertEqual(self.traducir(codigo)[2], "total = a + b")

    def test_bloque_si(self):
        codigo = envolver("    Definir c Como Logico\n"
                          "    Si c Entonces\n"
                          "        Escribir 1\n"
                          "    Sino\n"
                          "        Escribir 2\n"
                          "    FinSi")
        py = self.traducir(codigo)
        self.assertEqual(py[2], "if c:")
        self.assertEqual(py[3], "    print(1)")
        self.assertEqual(py[4], "else:")
        self.assertEqual(py[5], "    print(2)")
        self.assertEqual(py[6], "")          # FinSi cierra con la sangría

    def test_bloque_mientras(self):
        codigo = envolver("    Definir c Como Logico\n"
                          "    Mientras c Hacer\n"
                          "        Escribir 1\n"
                          "    FinMientras")
        py = self.traducir(codigo)
        self.assertEqual(py[2], "while c:")
        self.assertEqual(py[3], "    print(1)")
        self.assertEqual(py[4], "")

    def test_operadores(self):
        casos = [("a = b", "a == b"), ("a <> b", "a != b"),
                 ("a < b Y b > 2", "a < b and b > 2"),
                 ("a < b O b > 2", "a < b or b > 2"),
                 ("NO (a = b)", "not (a == b)"),
                 ("a ^ b", "a ** b"), ("a MOD b", "a % b"),
                 ("a / b", "a / b"), ("a <= b", "a <= b"), ("a >= b", "a >= b")]
        for pseudo, python in casos:
            with self.subTest(pseudo=pseudo):
                codigo = envolver(f"    Definir a, b Como Entero\n"
                                  f"    Si {pseudo} Entonces\n"
                                  f"    FinSi")
                self.assertEqual(self.traducir(codigo)[2], f"if {python}: pass")

    def test_booleanos(self):
        codigo = envolver("    Definir b Como Logico\n"
                          "    b <- Verdadero\n"
                          "    b <- Falso")
        py = self.traducir(codigo)
        self.assertEqual(py[2], "b = True")
        self.assertEqual(py[3], "b = False")

    def test_funciones(self):
        casos = [("ConvertirAEntero(t)", "int(t)"),
                 ("ConvertirAReal(t)", "float(t)"),
                 ("ConvertirATexto(x)", "str(x)"),
                 ("Longitud(t)", "len(t)"),
                 ("Absoluto(x)", "abs(x)"),
                 ("Redondear(x)", "round(x)"),
                 ("Truncar(x)", "int(x)")]
        for pseudo, python in casos:
            with self.subTest(pseudo=pseudo):
                codigo = envolver("    Definir t Como Cadena\n"
                                  "    Definir x, n Como Entero\n"
                                  f"    n <- {pseudo}")
                self.assertEqual(self.traducir(codigo)[3], f"n = {python}")

    def test_el_python_que_sale_de_verdad_compila(self):
        """No basta con que se parezca a Python: tiene que serlo."""
        programas = [PAPELERIA] + [envolver(c) for c in (
            "    Definir a Como Entero\n"
            "    Leer a\n"
            "    Si a > 0 Entonces\n"
            "        Si a > 10 Entonces\n"
            '            Escribir "grande"\n'
            "        Sino\n"
            '            Escribir "chico"\n'
            "        FinSi\n"
            "    Sino\n"
            '        Escribir "cero o menos"\n'
            "    FinSi",
            # Bloques vacíos: Python necesita un `pass` donde el pseudocódigo
            # no necesita nada.
            "    Definir b Como Logico\n"
            "    b <- Falso\n"
            "    Si b Entonces\n    Sino\n    FinSi\n"
            "    Mientras b Hacer\n    FinMientras",
            "    Definir i Como Entero\n"
            "    i <- 0\n"
            "    Mientras i < 4 Hacer\n"
            "        Si i MOD 2 = 0 Entonces\n"
            "            Escribir i\n"
            "        FinSi\n"
            "        i <- i + 1\n"
            "    FinMientras")]
        for codigo in programas:
            with self.subTest(codigo=codigo.split("\n")[0]):
                compile(ps.traducir_a_python(codigo), "<traducido>", "exec")

    def test_no_lanza_con_codigo_roto(self):
        salida = ps.traducir_a_python("esto no es pseudocódigo")
        self.assertTrue(salida.startswith("#"))
        self.assertIn("Algoritmo", salida)


class CatalogoDeErrores(unittest.TestCase):
    """§6.5: cada error del catálogo se dispara y dice lo que debe decir."""

    def fallar(self, codigo, entradas=()):
        r = ps.ejecutar_pseudo(codigo, entradas)
        self.assertFalse(r.ok, "se esperaba un error y el programa corrió")
        self.assertIsNotNone(r.error)
        self.assertTrue(r.error_corto)
        return r.error

    def test_ps01_variable_no_definida(self):
        e = self.fallar(envolver("    Definir x Como Entero\n    x <- gasto + 1"))
        self.assertEqual(e.codigo, "PS01")
        self.assertEqual(e.que_paso,
                         "usaste 'gasto' pero esa caja no existe todavía.")
        self.assertIn("hay que crearla con Definir", e.por_que)
        self.assertIn("Definir gasto Como Entero", e.arreglalo)
        self.assertEqual(e.linea, 3)

    def test_ps01_sugiere_el_nombre_parecido(self):
        e = self.fallar(envolver("    Definir copias Como Entero\n"
                                 "    copias <- 1\n"
                                 "    Escribir copais"))
        self.assertEqual(e.codigo, "PS01")
        self.assertIn("'copias'", e.arreglalo)

    def test_ps01_caja_definida_pero_vacia(self):
        """Quitar el `Leer` del programa de referencia da el mensaje de §12."""
        sin_leer = PAPELERIA.replace("    Leer copias\n", "")
        e = self.fallar(sin_leer)
        self.assertEqual(e.codigo, "PS01")
        self.assertIn("está vacía", e.que_paso)

    def test_ps02_igual_en_vez_de_flecha(self):
        e = self.fallar(envolver("    Definir total, copias Como Entero\n"
                                 "    copias <- 4\n"
                                 "    total = copias * 100"))
        self.assertEqual(e.codigo, "PS02")
        self.assertEqual(e.que_paso, "usaste el signo = para guardar un valor.")
        self.assertIn("PREGUNTAR si dos cosas son iguales", e.por_que)
        self.assertEqual(e.arreglalo, "total <- copias * 100")

    def test_ps03_bloque_sin_cerrar(self):
        e = self.fallar("Algoritmo A\n"
                        "    Definir i Como Entero\n"
                        "    i <- 0\n"
                        "    Mientras i < 3 Hacer\n"
                        "        i <- i + 1\n"
                        "FinAlgoritmo")
        self.assertEqual(e.codigo, "PS03")
        self.assertEqual(
            e.que_paso,
            "abriste un bloque con 'Mientras' en la línea 4 y nunca lo cerraste.")
        self.assertIn("Algoritmo/FinAlgoritmo", e.por_que)
        self.assertIn("FinMientras", e.arreglalo)

    def test_ps03_falta_finalgoritmo(self):
        e = self.fallar("Algoritmo A\n    Definir x Como Entero")
        self.assertEqual(e.codigo, "PS03")
        self.assertIn("'Algoritmo' en la línea 1", e.que_paso)

    def test_ps04_tipo_incompatible(self):
        e = self.fallar(envolver('    Definir edad Como Entero\n'
                                 '    edad <- "dieciocho"'))
        self.assertEqual(e.codigo, "PS04")
        self.assertEqual(
            e.que_paso,
            'intentaste guardar el texto "dieciocho" en \'edad\', que definiste '
            'Como Entero.')
        self.assertIn("solo guarda números sin decimales", e.por_que)
        self.assertIn("edad <- 18", e.arreglalo)

    def test_ps04_tambien_al_leer(self):
        e = self.fallar(envolver("    Definir edad Como Entero\n    Leer edad"),
                        entradas=["dieciocho"])
        self.assertEqual(e.codigo, "PS04")
        self.assertIn('el texto "dieciocho"', e.que_paso)

    def test_ps05_cola_de_entradas_agotada(self):
        e = self.fallar(envolver("    Definir a, b, c Como Entero\n"
                                 "    Leer a\n    Leer b\n    Leer c"),
                        entradas=["1", "2"])
        self.assertEqual(e.codigo, "PS05")
        self.assertEqual(
            e.que_paso,
            "el algoritmo pidió un dato con Leer, pero ya no quedan entradas.")
        self.assertIn("Tu algoritmo tiene 3 Leer y le diste 2 datos.", e.por_que)
        self.assertIn("entradas=", e.arreglalo)

    def test_ps06_instruccion_desconocida(self):
        e = self.fallar(envolver('    Escrbir "hola"'))
        self.assertEqual(e.codigo, "PS06")
        self.assertEqual(e.que_paso, "no conozco la instrucción 'Escrbir'.")
        # 2026-10-05: esta lista terminaba en «Mientras.». Desde que el motor
        # tiene Para, lo nombra entre las instrucciones que entiende.
        self.assertEqual(
            e.por_que,
            "las instrucciones que entiendo son: Definir, Constante, Leer, "
            "Escribir, Si, Mientras, Para.")
        self.assertEqual(e.arreglalo, "¿querías decir Escribir?")

    def test_ps07_comilla_sin_cerrar(self):
        e = self.fallar("Algoritmo A\n"
                        "    Definir total Como Entero\n"
                        '    Escribir "Total a pagar: $, total\n'
                        "FinAlgoritmo")
        self.assertEqual(e.codigo, "PS07")
        self.assertEqual(
            e.que_paso,
            "abriste unas comillas en la línea 3 y no las cerraste.")
        self.assertIn("comillas dobles", e.por_que)

    def test_ps08_division_por_cero(self):
        e = self.fallar(envolver("    Definir n, r Como Entero\n"
                                 "    n <- 0\n"
                                 "    r <- 10 / n"))
        self.assertEqual(e.codigo, "PS08")
        self.assertEqual(e.que_paso, "intentaste dividir entre cero.")
        self.assertIn("La variable 'n' vale 0 en este momento.", e.por_que)
        self.assertIn("prueba de escritorio", e.arreglalo)

    def test_ps08_tambien_con_mod(self):
        e = self.fallar(envolver("    Definir n, r Como Entero\n"
                                 "    n <- 0\n"
                                 "    r <- 10 MOD n"))
        self.assertEqual(e.codigo, "PS08")

    def test_ps09_ciclo_infinito(self):
        e = self.fallar("Algoritmo A\n"
                        "    Definir i Como Entero\n"
                        "    i <- 0\n"
                        "    Mientras i < 3 Hacer\n"
                        "        i <- 0\n"
                        "    FinMientras\n"
                        "FinAlgoritmo")
        self.assertEqual(e.codigo, "PS09")
        self.assertIn("10 000 pasos", e.que_paso)
        self.assertIn("nunca se vuelve falsa", e.por_que)
        self.assertIn("cambie dentro del ciclo", e.arreglalo)

    def test_ps10_falta_entonces(self):
        e = self.fallar(envolver("    Definir s Como Entero\n"
                                 "    s <- 1\n"
                                 "    Si s > 0\n"
                                 "        Escribir s\n"
                                 "    FinSi"))
        self.assertEqual(e.codigo, "PS10")
        self.assertEqual(
            e.que_paso,
            "escribiste 'Si' pero falta la palabra Entonces al final de la línea.")
        self.assertEqual(e.arreglalo, "Si saldo > 0 Entonces")

    def test_ps10_falta_hacer(self):
        e = self.fallar(envolver("    Definir s Como Entero\n"
                                 "    s <- 1\n"
                                 "    Mientras s > 0\n"
                                 "    FinMientras"))
        self.assertEqual(e.codigo, "PS10")
        self.assertIn("falta la palabra Hacer", e.que_paso)

    def test_ps11_constante_reasignada(self):
        e = self.fallar(envolver("    Constante PASAJE <- 3200\n"
                                 "    PASAJE <- 1"))
        self.assertEqual(e.codigo, "PS11")
        self.assertEqual(
            e.que_paso,
            "intentaste cambiar PASAJE, que declaraste como Constante.")
        self.assertIn("MAYÚSCULAS", e.por_que)

    def test_ps12_parentesis_desbalanceados(self):
        e = self.fallar(envolver("    Definir t, c Como Entero\n"
                                 "    c <- 2\n"
                                 "    t <- ((c * 100) + 5"))
        self.assertEqual(e.codigo, "PS12")
        self.assertEqual(e.que_paso, "abriste 2 paréntesis y cerraste 1.")
        self.assertEqual(e.por_que, "cada ( necesita su ).")

    def test_ps13_sin_cabecera(self):
        e = self.fallar("Definir x Como Entero\nx <- 1")
        self.assertEqual(e.codigo, "PS13")
        self.assertEqual(
            e.que_paso, "tu programa no empieza con la línea 'Algoritmo <nombre>'.")
        self.assertIn("óvalo de INICIO", e.por_que)

    def test_ps13_programa_vacio(self):
        self.assertEqual(self.fallar("").codigo, "PS13")
        self.assertEqual(self.fallar("   \n\n  ").codigo, "PS13")

    def test_ps14_nombre_con_espacio(self):
        e = self.fallar(envolver("    Definir costo pasaje Como Entero"))
        self.assertEqual(e.codigo, "PS14")
        self.assertEqual(e.que_paso, "'costo pasaje' no sirve como nombre de "
                                     "variable.")
        self.assertIn("sin espacios y sin tildes", e.por_que)
        self.assertEqual(e.arreglalo, "costo_pasaje")

    def test_ps14_nombre_con_tilde(self):
        e = self.fallar(envolver("    Definir año Como Entero"))
        self.assertEqual(e.codigo, "PS14")
        self.assertEqual(e.arreglalo, "ano")

    def test_tarjeta_de_texto_plano(self):
        """El formato de la tarjeta de §6.5, que es lo que ve el autograder."""
        e = self.fallar(envolver("    Definir total, copias Como Entero\n"
                                 "    copias <- 4\n"
                                 "    total = copias * 100"))
        tarjeta = str(e)
        self.assertIn("✗ Error en la línea 4", tarjeta)
        self.assertIn("    4 |     total = copias * 100", tarjeta)
        self.assertIn("^", tarjeta)
        self.assertIn("Qué pasó ....:", tarjeta)
        self.assertIn("Por qué ......:", tarjeta)
        self.assertIn("Arréglalo ....:", tarjeta)

    def test_tarjeta_html(self):
        e = self.fallar(envolver("    x <- 1"))
        html = e.html()
        self.assertIn(ps.ROJO, html)
        self.assertIn("Qué pasó", html)
        self.assertIn("<div", html)


class TopeDeIteraciones(unittest.TestCase):
    """El ciclo infinito se corta, y se corta a tiempo."""

    def test_corta_en_el_tope(self):
        r = ps.ejecutar_pseudo(envolver("    Definir i Como Entero\n"
                                        "    i <- 0\n"
                                        "    Mientras i >= 0 Hacer\n"
                                        "        i <- i + 1\n"
                                        "    FinMientras"))
        self.assertFalse(r.ok)
        self.assertEqual(r.error.codigo, "PS09")
        self.assertLessEqual(len(r.pasos), ps.MAX_PASOS)
        # La traza parcial se conserva: el trazador puede mostrar qué pasó.
        self.assertGreater(len(r.pasos), 100)

    def test_un_ciclo_normal_no_se_corta(self):
        r = ps.ejecutar_pseudo(envolver("    Definir i, s Como Entero\n"
                                        "    i <- 0\n"
                                        "    s <- 0\n"
                                        "    Mientras i < 5 Hacer\n"
                                        "        i <- i + 1\n"
                                        "        s <- s + i\n"
                                        "    FinMientras\n"
                                        "    Escribir s"))
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "15\n")

    def test_salida_desbordada_tambien_se_corta(self):
        r = ps.ejecutar_pseudo(envolver("    Definir i Como Entero\n"
                                        "    i <- 0\n"
                                        "    Mientras i >= 0 Hacer\n"
                                        '        Escribir "ruido y más ruido"\n'
                                        "    FinMientras"))
        self.assertFalse(r.ok)
        self.assertEqual(r.error.codigo, "PS09")


class ColaDeEntradas(unittest.TestCase):
    """§11.2: el `input()` de mentiras y la cola del pseudocódigo."""

    def tearDown(self):
        ps.restaurar_input()

    def test_pseudocodigo_consume_en_orden(self):
        r = ps.ejecutar_pseudo(envolver("    Definir a, b Como Entero\n"
                                        "    Leer a, b\n"
                                        '    Escribir a, "-", b'),
                               entradas=["10", "16"])
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "10-16\n")

    def test_pseudocodigo_acepta_valores_no_texto(self):
        """Un descuido común: pasar números en vez de cadenas."""
        r = ps.ejecutar_pseudo(envolver("    Definir a Como Entero\n"
                                        "    Leer a\n    Escribir a"),
                               entradas=[40])
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "40\n")

    def test_pseudocodigo_sin_entradas(self):
        r = ps.ejecutar_pseudo(envolver("    Definir a Como Entero\n    Leer a"))
        self.assertFalse(r.ok)
        self.assertEqual(r.error.codigo, "PS05")

    def test_usar_entradas_y_eco(self):
        ps.usar_entradas(["40"])
        with silencio() as eco:
            valor = input()
        self.assertEqual(valor, "40")
        self.assertEqual(eco.getvalue(), "40\n")   # se ve como si lo teclearan

    def test_usar_entradas_agotada(self):
        ps.usar_entradas([])
        with self.assertRaises(EOFError) as caja, silencio():
            input()
        self.assertIn("la cola de entradas está vacía", str(caja.exception))
        self.assertIn("usar_entradas", str(caja.exception))

    def test_context_manager_restaura(self):
        import builtins
        original = builtins.input
        with ps.entradas(["10", "16", "3200"]), silencio():
            producto = int(input()) * int(input())
        self.assertEqual(producto, 160)
        self.assertIs(builtins.input, original)

    def test_context_manager_restaura_aunque_falle(self):
        import builtins
        original = builtins.input
        with self.assertRaises(ValueError):
            with ps.entradas(["x"]), silencio():
                int(input())
        self.assertIs(builtins.input, original)

    def test_convierte_todo_a_texto(self):
        ps.usar_entradas([40, 3.5, True])
        with silencio():
            leidos = [input(), input(), input()]
        self.assertEqual(leidos, ["40", "3.5", "True"])


class EmisorDeSVG(unittest.TestCase):
    """§7.3: el diagrama se dibuja solo, y con los símbolos correctos."""

    def arbol(self, codigo, resaltar=None):
        svg = ps.diagrama(codigo, resaltar_nodo=resaltar)
        return svg, ET.fromstring(svg)

    def test_svg_bien_formado(self):
        svg, raiz = self.arbol(PAPELERIA)
        self.assertEqual(raiz.tag, SVG + "svg")
        self.assertEqual(raiz.get("role"), "img")
        self.assertTrue(raiz.get("viewBox").startswith("0 0 660 "))
        self.assertIn("max-width:100%", raiz.get("style"))

    def test_accesibilidad(self):
        _, raiz = self.arbol(PAPELERIA)
        titulo = raiz.find(SVG + "title").text
        self.assertEqual(
            titulo,
            "Diagrama de flujo del algoritmo CostoDeFotocopias, 6 bloques")
        desc = raiz.find(SVG + "desc").text
        self.assertTrue(desc.startswith("INICIO →"))
        self.assertTrue(desc.endswith("→ FIN"))

    def test_simbolos_de_la_secuencia(self):
        """Óvalo, paralelogramo y rectángulo, uno por instrucción del flujo."""
        svg, raiz = self.arbol(PAPELERIA)
        grupos = raiz.findall(SVG + "g")
        formas = []
        for g in grupos:
            hijo = [h for h in g if h.tag != SVG + "title" and h.tag != SVG + "text"]
            formas.append(hijo[0])
        # INICIO y FIN son rect con rx = h/2 (óvalo/estadio).
        ovalos = [f for f in formas
                  if f.tag == SVG + "rect" and f.get("rx") == "23"]
        self.assertEqual(len(ovalos), 2)
        # Leer y los dos Escribir son paralelogramos (polígonos de 4 puntos).
        paralelogramos = [f for f in formas if f.tag == SVG + "polygon"]
        self.assertEqual(len(paralelogramos), 3)
        for p in paralelogramos:
            self.assertEqual(len(p.get("points").split()), 4)
        # La asignación es un rectángulo de proceso.
        procesos = [f for f in formas
                    if f.tag == SVG + "rect" and f.get("rx") == "6"]
        self.assertEqual(len(procesos), 1)
        # Definir y Constante NO producen bloque.
        self.assertEqual(len(formas), 6)

    def test_rombo_y_union_en_un_si(self):
        codigo = envolver("    Definir s Como Entero\n"
                          "    s <- 1\n"
                          "    Si s > 0 Entonces\n"
                          '        Escribir "sí"\n'
                          "    Sino\n"
                          '        Escribir "no"\n'
                          "    FinSi")
        svg, raiz = self.arbol(codigo)
        rombos = [p for p in raiz.iter(SVG + "polygon")
                  if len(p.get("points").split()) == 4
                  and p.get("fill") == ps.COLOR["decision"][0]]
        self.assertEqual(len(rombos), 1)
        self.assertEqual(len(list(raiz.iter(SVG + "circle"))), 1)   # la unión
        etiquetas = [t.text for t in raiz.iter(SVG + "text")]
        self.assertIn("Sí", etiquetas)
        self.assertIn("No", etiquetas)

    def test_rombo_con_retorno_en_un_mientras(self):
        codigo = envolver("    Definir i Como Entero\n"
                          "    i <- 0\n"
                          "    Mientras i < 3 Hacer\n"
                          "        i <- i + 1\n"
                          "    FinMientras")
        svg, raiz = self.arbol(codigo)
        # La flecha de retorno es una polilínea de más de dos puntos.
        largas = [p for p in raiz.iter(SVG + "polyline")
                  if len(p.get("points").split()) > 2]
        self.assertTrue(largas, "falta la flecha de retorno del ciclo")

    def test_flechas_con_punta(self):
        svg, raiz = self.arbol(PAPELERIA)
        marcador = raiz.find(SVG + "defs/" + SVG + "marker")
        self.assertEqual(marcador.get("id"), "punta")
        lineas = list(raiz.iter(SVG + "polyline"))
        self.assertEqual(len(lineas), 5)          # 6 bloques, 5 flechas
        for linea in lineas:
            self.assertEqual(linea.get("marker-end"), "url(#punta)")

    def test_resalte_del_nodo_en_ejecucion(self):
        sin_resalte, _ = self.arbol(PAPELERIA)
        con_resalte, raiz = self.arbol(PAPELERIA, resaltar=3)
        self.assertNotEqual(sin_resalte, con_resalte)
        self.assertIn(f'stroke="{ps.RESALTE}" stroke-width="8"', con_resalte)
        self.assertIn(f'stroke="{ps.RESALTE}" stroke-width="3"', con_resalte)

    def test_texto_largo_se_recorta_y_queda_en_el_title(self):
        codigo = envolver('    Definir total Como Entero\n'
                          '    total <- 1\n'
                          '    Escribir "una frase larguísima que no cabe de '
                          'ninguna manera en el bloque"')
        svg, raiz = self.arbol(codigo)
        for texto in raiz.iter(SVG + "text"):
            self.assertLessEqual(len(texto.text), 32)
        self.assertIn("ninguna manera en el bloque", svg)   # completo en el title

    def test_un_si_anidado_ensancha_el_lienzo_en_vez_de_recortarlo(self):
        codigo = envolver("    Definir a Como Entero\n"
                          "    a <- 1\n"
                          "    Si a > 0 Entonces\n"
                          "        Si a > 10 Entonces\n"
                          '            Escribir "grande"\n'
                          "        Sino\n"
                          '            Escribir "chico"\n'
                          "        FinSi\n"
                          "    FinSi")
        svg, raiz = self.arbol(codigo)
        ancho = float(raiz.get("viewBox").split()[2])
        self.assertGreater(ancho, ps.ANCHO)
        # Nada se sale del lienzo por la izquierda.
        for figura in raiz.iter(SVG + "polygon"):
            for punto in figura.get("points").split():
                self.assertGreaterEqual(float(punto.split(",")[0]), 0)

    def test_codigo_roto_devuelve_svg_con_el_mensaje(self):
        svg = ps.diagrama("no soy pseudocódigo")
        raiz = ET.fromstring(svg)
        self.assertEqual(raiz.tag, SVG + "svg")
        self.assertIn("Algoritmo", svg)

    def test_escapa_lo_que_escribio_el_estudiante(self):
        codigo = envolver('    Escribir "<script>&"')
        svg = ps.diagrama(codigo)
        ET.fromstring(svg)
        self.assertNotIn("<script>", svg)

    def test_un_caracter_de_control_no_rompe_el_xml(self):
        """Pegar desde un PDF mete caracteres invisibles que XML no admite."""
        codigo = envolver('    Escribir "hola\x0bmundo\x0c"')
        ET.fromstring(ps.diagrama(codigo))
        codigo_roto = envolver("    Escribir \x0b")
        ET.fromstring(ps.diagrama(codigo_roto))


class Robustez(unittest.TestCase):
    """El contrato duro: ningún error del estudiante sale como traceback."""

    BASURA = [
        "", "   ", "\n\n\n", "Algoritmo", "Algoritmo 9", "FinAlgoritmo",
        "Algoritmo A\nFinAlgoritmo", "Algoritmo A\n;;;\nFinAlgoritmo",
        "Algoritmo A\nDefinir\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entreo\nFinAlgoritmo",
        "Algoritmo A\nLeer\nFinAlgoritmo",
        "Algoritmo A\nEscribir\nFinAlgoritmo",
        "Algoritmo A\nEscribir )\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entero\nx <-\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entero\nx <- 1 +\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entero\nx <- Longitud 3\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Cadena\nx <- ConvertirAEntero(\"ab\")\nFinAlgoritmo",
        "Algoritmo A\nSino\nFinAlgoritmo",
        "Algoritmo A\nSi Entonces\nFinSi\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entero\nSi x Entonces\nFinSi\nFinAlgoritmo",
        "Algoritmo A\nMientras Hacer\nFinMientras\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entero\nx <- 2 ^ 999999\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Cadena\nx <- \"a\" + 1\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Logico\nx <- 1 Y 2\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entero\nx <- 1\nx <- x + \"a\"\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entero\nLeer x\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entero\nx <- 3.7\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entero\nDefinir x Como Cadena\nFinAlgoritmo",
        "Algoritmo A\nDefinir x, Como Entero\nFinAlgoritmo",
        "Algoritmo A\nx y z\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entero\nx <- ((((((((((1))))))))))\nFinAlgoritmo",
        "Algoritmo A\nDefinir x Como Entero\nx <- 1 2 3\nFinAlgoritmo",
        "🙂", "Algoritmo A\n\U0001f600\nFinAlgoritmo",
        # 2026-10-05: lo que llegó con el Para, los cierres en dos palabras y
        # Proceso. Cada cabecera a medio escribir es un camino de error nuevo.
        "Proceso", "Proceso A", "Proceso A\nFinProceso", "Proceso A\nFin Proceso",
        "Algoritmo A\nFin\nFinAlgoritmo", "Algoritmo A\nFin Si\nFinAlgoritmo",
        "Algoritmo A\nSi no\nFinAlgoritmo", "Algoritmo A\nFin Algoritmo",
        "Algoritmo A\nPara\nFinAlgoritmo", "Algoritmo A\nPara i\nFinAlgoritmo",
        "Algoritmo A\nPara i <-\nFinAlgoritmo",
        "Algoritmo A\nPara i <- 1 Hasta\nFinAlgoritmo",
        "Algoritmo A\nPara Hasta Hacer\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nPara i <- Hasta Hacer\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nPara i <- 1 Hasta Hacer\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nPara i <- 1 Hasta 3 Con Paso Hacer\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nPara i <- 1 Hasta 3 Con Hacer\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nPara i <- 1 Hasta 3 Hacer\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nDefinir i Como Entero\nPara i <- 1 Hasta 3 Hacer\nFinAlgoritmo",
        "Algoritmo A\nDefinir i Como Entero\nPara i <- 1 Hasta 3 Hacer\nFinSi\nFinAlgoritmo",
        "Algoritmo A\nDefinir i Como Cadena\nPara i <- 1 Hasta 3 Hacer\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nDefinir i Como Entero\nPara i <- \"a\" Hasta 3 Hacer\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nDefinir i Como Entero\nPara i <- 1 Hasta Verdadero Hacer\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nDefinir i Como Entero\nPara i <- 1 Hasta 3 Con Paso \"a\" Hacer\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nDefinir i Como Entero\nPara i <- 1 Hasta 3 Con Paso 0.5 Hacer\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nDefinir i Como Entero\nPara i <- 1 Hasta 3 Con Paso 1 / 0 Hacer\nFinPara\nFinAlgoritmo",
        # El cuerpo le quita el piso a la variable que cuenta.
        "Algoritmo A\nDefinir i Como Entero\nPara i <- 1 Hasta 3 Hacer\nDefinir i Como Entero\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nDefinir i Como Entero\nPara i <- 1 Hasta 3 Hacer\nDefinir i Como Cadena\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nDefinir i Como Entero\nPara i <- 1 Hasta 3 Hacer\nConstante i <- 9\nFinPara\nFinAlgoritmo",
        "Algoritmo A\nRepetir\nHasta Que 1 = 1\nFinAlgoritmo",
        "Algoritmo A\nSegun 3 Hacer\n1: Escribir 1\nFinSegun\nFinAlgoritmo",
        "Algoritmo A\nSi 1 = 1 Entonces\nSino Si 2 = 2 Entonces\nFinSi\nFinAlgoritmo",
        "Algoritmo A\nSi no Si 2 = 2 Entonces\nFinSi\nFinAlgoritmo",
    ]

    def test_nada_lanza(self):
        for codigo in self.BASURA:
            with self.subTest(codigo=codigo[:40]):
                r = ps.ejecutar_pseudo(codigo, entradas=["1"])
                self.assertIsInstance(r, ps.Resultado)
                if not r.ok:
                    self.assertIsInstance(r.error, ps.Error)
                    self.assertTrue(r.error.que_paso)
                    self.assertTrue(r.error.por_que)
                    self.assertTrue(r.error.arreglalo)
                    self.assertNotEqual(r.error.codigo, "PS00",
                                        "el motor se rompió por dentro")
                    self.assertTrue(str(r.error))
                    self.assertTrue(r.error.html())

    def test_las_demas_funciones_tampoco_lanzan(self):
        for codigo in self.BASURA:
            with self.subTest(codigo=codigo[:40]):
                self.assertIsInstance(ps.traducir_a_python(codigo), str)
                ET.fromstring(ps.diagrama(codigo))

    def test_codigo_que_no_es_texto(self):
        for basura in (None, 42, ["Algoritmo A"], {"a": 1}):
            with self.subTest(basura=basura):
                r = ps.ejecutar_pseudo(basura)
                self.assertFalse(r.ok)
                self.assertTrue(r.error_corto)

    def test_ejecuciones_independientes(self):
        """Dos ejecuciones no comparten memoria: cada celda arranca en limpio."""
        codigo = envolver("    Definir x Como Entero\n    x <- 1\n    Escribir x")
        primera = ps.ejecutar_pseudo(codigo)
        segunda = ps.ejecutar_pseudo(codigo)
        self.assertEqual(primera.salida, segunda.salida)
        self.assertIsNot(primera.memoria, segunda.memoria)


class Lenguaje(unittest.TestCase):
    """Reglas del mini-lenguaje que el cuadernillo enseña explícitamente."""

    def correr(self, cuerpo, entradas=()):
        return ps.ejecutar_pseudo(envolver(cuerpo), entradas)

    def test_palabras_clave_sin_distinguir_mayusculas(self):
        r = self.correr("    definir x COMO entero\n    x <- 2\n    ESCRIBIR x")
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "2\n")

    def test_nombres_de_variable_si_distinguen(self):
        r = self.correr("    Definir dato Como Entero\n    Dato <- 1")
        self.assertFalse(r.ok)
        self.assertEqual(r.error.codigo, "PS01")

    def test_mostrar_es_sinonimo_de_escribir(self):
        self.assertEqual(self.correr('    Mostrar "hola"').salida, "hola\n")

    def test_x_igual_a_x_mas_dos(self):
        """El renglón más raro de la programación (§9.2), paso a paso."""
        r = self.correr("    Definir viajes Como Entero\n"
                        "    viajes <- 3\n"
                        "    viajes <- viajes + 1\n"
                        "    viajes <- viajes + 1")
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.tabla_traza(["viajes"]),
                         [(None,), (3,), (4,), (5,)])
        self.assertIn("(3 + 1 = 4)", r.pasos[2].explicacion)

    def test_precedencia_y_parentesis(self):
        r = self.correr("    Definir a, b Como Entero\n"
                        "    a <- 2 + 3 * 4\n"
                        "    b <- (2 + 3) * 4\n"
                        '    Escribir a, " ", b')
        self.assertEqual(r.salida, "14 20\n")

    def test_division_da_decimales(self):
        r = self.correr("    Definir x Como Real\n"
                        "    x <- 7 / 2\n    Escribir x")
        self.assertEqual(r.salida, "3.5\n")

    def test_division_exacta_cabe_en_entero(self):
        r = self.correr("    Definir x Como Entero\n"
                        "    x <- 10 / 2\n    Escribir x")
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "5\n")

    def test_booleanos_se_muestran_en_espanol(self):
        r = self.correr("    Definir b Como Logico\n"
                        "    b <- Verdadero\n    Escribir b")
        self.assertEqual(r.salida, "Verdadero\n")

    def test_sin_saltar(self):
        r = self.correr('    Escribir "a" Sin Saltar\n    Escribir "b"')
        self.assertEqual(r.salida, "ab\n")

    def test_concatenar_textos(self):
        r = self.correr('    Definir s Como Cadena\n'
                        '    s <- "Hola " + "mundo"\n    Escribir s')
        self.assertEqual(r.salida, "Hola mundo\n")

    def test_si_sino(self):
        cuerpo = ("    Definir saldo Como Entero\n"
                  "    Leer saldo\n"
                  "    Si saldo > 0 Entonces\n"
                  '        Escribir "alcanza"\n'
                  "    Sino\n"
                  '        Escribir "no alcanza"\n'
                  "    FinSi")
        self.assertEqual(self.correr(cuerpo, ["5"]).salida, "alcanza\n")
        self.assertEqual(self.correr(cuerpo, ["0"]).salida, "no alcanza\n")

    def test_comentario_al_final_de_una_linea(self):
        r = self.correr("    Definir x Como Entero  // la caja\n"
                        "    x <- 2 // el valor\n"
                        "    Escribir x")
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "2\n")

    def test_las_dobles_barras_dentro_de_un_texto_no_son_comentario(self):
        r = self.correr('    Escribir "http://uis.edu.co"')
        self.assertEqual(r.salida, "http://uis.edu.co\n")

    def test_funciones_de_conversion(self):
        r = self.correr('    Definir t Como Cadena\n'
                        '    Definir n Como Entero\n'
                        '    Definir r Como Real\n'
                        '    t <- "40"\n'
                        '    n <- ConvertirAEntero(t)\n'
                        '    r <- ConvertirAReal("3.5")\n'
                        '    Escribir n + 1, " ", r, " ", Longitud(t)')
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "41 3.5 2\n")


class PuenteFlowgorithm(unittest.TestCase):
    """§7.6: el guion siempre se puede imprimir; el .fprg es XML válido."""

    def test_guion(self):
        with silencio() as buffer:
            ps.guion_flowgorithm(PAPELERIA)
        texto = buffer.getvalue()
        self.assertIn("GUION PARA FLOWGORITHM — CostoDeFotocopias", texto)
        self.assertIn("Declare  copias : Integer", texto)
        self.assertIn("Assign   PRECIO_COPIA = 100", texto)
        self.assertIn("Input    copias", texto)
        self.assertIn('Output   "Total a pagar: $" & total', texto)
        self.assertIn("los textos se unen con &", texto)

    def test_exportar_produce_xml_valido(self):
        import tempfile
        ruta = os.path.join(tempfile.mkdtemp(), "prueba.fprg")
        with silencio():
            devuelto = ps.exportar_flowgorithm(PAPELERIA, ruta)
        self.assertEqual(devuelto, ruta)
        raiz = ET.parse(ruta).getroot()
        self.assertEqual(raiz.tag, "flowgorithm")
        self.assertEqual(raiz.get("fileversion"), "4.2")
        cuerpo = raiz.find("function/body")
        self.assertEqual([h.tag for h in cuerpo],
                         ["declare", "declare", "assign", "assign", "output",
                          "input", "assign", "output"])

    def test_exportar_con_codigo_roto_no_lanza(self):
        with silencio():
            self.assertEqual(ps.exportar_flowgorithm("basura", "/tmp/x.fprg"), "")


class CapaVisual(unittest.TestCase):
    """Las funciones que pintan tienen que sobrevivir sin frontend."""

    def test_html_del_resultado(self):
        r = ps.ejecutar_pseudo(PAPELERIA, entradas=["40"])
        html = r._html()
        self.assertIn("SALIDA", html)
        self.assertIn("Total a pagar", html)
        self.assertIn("copias", html)

    def test_html_del_trazador(self):
        r = ps.ejecutar_pseudo(PAPELERIA, entradas=["40"])
        for n in range(1, len(r.pasos) + 1):
            html = ps._html_trazador(PAPELERIA, r, n)
            self.assertIn("PSEUDOCÓDIGO", html)
            self.assertIn("PYTHON EQUIVALENTE", html)
            self.assertIn("DIAGRAMA", html)
            self.assertIn("MEMORIA", html)
            self.assertIn("Qué acaba de pasar", html)

    def test_la_variable_que_cambio_se_marca(self):
        r = ps.ejecutar_pseudo(PAPELERIA, entradas=["40"])
        html = ps._html_trazador(PAPELERIA, r, 6)      # la asignación de total
        self.assertIn("←", html)
        self.assertIn("#e8f5e8", html)

    def test_funciones_de_pintado_no_lanzan(self):
        with silencio():
            ps.tabla_dos_columnas(PAPELERIA)
            ps.comparador(PAPELERIA)
            ps.trazador(PAPELERIA, ["40"])
            ps.laboratorio(PAPELERIA, ["40"])
            ps.ejecutar_pseudo(PAPELERIA, ["40"]).imprimir()
            ps.ejecutar_pseudo("basura").imprimir()


# ═════════════════════════════════════════════════════════════════════════════
# 2026-10-05 · Lo que salió del aviso del profesor sobre el cuadernillo 4
# ═════════════════════════════════════════════════════════════════════════════
# 97 AssertionError de 10 alumnos en el ejercicio 2 de la semana 4, y 7 de 12
# que no lo habían pasado nunca. No se equivocaban de algoritmo: escribían el
# pseudocódigo de PSeInt que traen aprendido (Para, Fin Si, Proceso...) y el
# motor, que solo sabía Mientras, se lo rechazaba con consejos que no servían.
# Todo lo de aquí abajo protege que eso no vuelva a pasar.

SUMA_CON_PARA = """Algoritmo SumaHastaN
    Definir i, s, n Como Entero
    Leer n
    s <- 0
    Para i <- 1 Hasta n Hacer
        s <- s + i
    FinPara
    Escribir s
FinAlgoritmo"""


class CicloPara(unittest.TestCase):
    """`Para <var> <- <ini> Hasta <fin> [Con Paso <p>] Hacer ... FinPara`."""

    CABEZA = ("    Definir i, j, n, s, salto Como Entero\n"
              "    Definir x Como Real\n"
              "    Definir t Como Cadena\n")

    def correr(self, cuerpo, entradas=()):
        return ps.ejecutar_pseudo(envolver(self.CABEZA + cuerpo), entradas)

    def salida(self, cuerpo, entradas=()):
        r = self.correr(cuerpo, entradas)
        self.assertTrue(r.ok, r.error_corto)
        return r.salida

    def fallar(self, cuerpo, entradas=()):
        r = self.correr(cuerpo, entradas)
        self.assertFalse(r.ok, "se esperaba un error y el programa corrió")
        return r.error

    # -- lo que hace ---------------------------------------------------------
    def test_el_final_es_inclusivo_y_el_paso_por_defecto_es_uno(self):
        self.assertEqual(self.salida("    Para i <- 1 Hasta 4 Hacer\n"
                                     "        Escribir i\n"
                                     "    FinPara"), "1\n2\n3\n4\n")

    def test_programa_completo(self):
        for n, suma in [("4", "10\n"), ("1", "1\n"), ("0", "0\n"), ("100", "5050\n")]:
            with self.subTest(n=n):
                r = ps.ejecutar_pseudo(SUMA_CON_PARA, entradas=[n])
                self.assertTrue(r.ok, r.error_corto)
                self.assertEqual(r.salida, suma)

    def test_con_paso(self):
        self.assertEqual(self.salida("    Para i <- 1 Hasta 10 Con Paso 3 Hacer\n"
                                     "        Escribir i\n"
                                     "    FinPara"), "1\n4\n7\n10\n")
        # Si el paso se salta el final, no lo pisa: 9 no existe en 0, 4, 8.
        self.assertEqual(self.salida("    Para i <- 0 Hasta 9 Con Paso 4 Hacer\n"
                                     "        Escribir i\n"
                                     "    FinPara"), "0\n4\n8\n")

    def test_paso_negativo_cuenta_hacia_abajo(self):
        """Con paso negativo la pregunta es >=, y el final sigue siendo inclusivo."""
        self.assertEqual(self.salida("    Para i <- 3 Hasta 1 Con Paso -1 Hacer\n"
                                     "        Escribir i\n"
                                     "    FinPara"), "3\n2\n1\n")
        self.assertEqual(self.salida("    Para i <- 10 Hasta 1 Con Paso -4 Hacer\n"
                                     "        Escribir i\n"
                                     "    FinPara"), "10\n6\n2\n")

    def test_cero_vueltas_no_es_un_error(self):
        """Los dos bordes del ejercicio 2 de la semana 4 (n = 1 y n = 2)."""
        for cabecera in ("Para i <- 3 Hasta 2 Hacer",
                         "Para i <- 3 Hasta 1 Hacer",
                         "Para i <- 1 Hasta 3 Con Paso -1 Hacer"):
            with self.subTest(cabecera=cabecera):
                self.assertEqual(
                    self.salida(f"    {cabecera}\n"
                                f'        Escribir "dentro"\n'
                                f"    FinPara\n"
                                f'    Escribir "fuera"'), "fuera\n")

    def test_las_tres_cuentas_son_expresiones(self):
        cuerpo = ("    Leer n\n"
                  "    salto <- 2\n"
                  "    Para i <- n - 4 Hasta (n + 1) * 2 Con Paso salto + 1 Hacer\n"
                  "        Escribir i\n"
                  "    FinPara")
        self.assertEqual(self.salida(cuerpo, ["5"]), "1\n4\n7\n10\n")

    def test_el_paso_puede_ser_una_variable_y_puede_ser_negativa(self):
        cuerpo = ("    Leer salto\n"
                  "    Para i <- 6 Hasta 0 Con Paso salto Hacer\n"
                  "        Escribir i\n"
                  "    FinPara")
        self.assertEqual(self.salida(cuerpo, ["-3"]), "6\n3\n0\n")
        self.assertEqual(self.salida(cuerpo, ["3"]), "")       # sube: no entra

    def test_una_variable_puede_llamarse_paso(self):
        """`Con Paso` se reconoce como pareja; `paso` suelto es un nombre más."""
        r = ps.ejecutar_pseudo(envolver(
            "    Definir i, paso Como Entero\n"
            "    paso <- 2\n"
            "    Para i <- paso Hasta paso * 3 Con Paso paso Hacer\n"
            "        Escribir i\n"
            "    FinPara"))
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "2\n4\n6\n")

    def test_sin_distinguir_mayusculas(self):
        self.assertEqual(self.salida("    para i <- 1 hasta 5 con paso 2 hacer\n"
                                     "        escribir i\n"
                                     "    finpara"), "1\n3\n5\n")
        self.assertEqual(self.salida("    PARA i <- 1 HASTA 2 HACER\n"
                                     "        ESCRIBIR i\n"
                                     "    FINPARA"), "1\n2\n")

    def test_anidados(self):
        cuerpo = ("    Para i <- 1 Hasta 2 Hacer\n"
                  "        Para j <- 1 Hasta 3 Hacer\n"
                  '            Escribir i, "x", j\n'
                  "        FinPara\n"
                  "    FinPara")
        self.assertEqual(self.salida(cuerpo),
                         "1x1\n1x2\n1x3\n2x1\n2x2\n2x3\n")

    def test_convive_con_si_y_con_mientras(self):
        cuerpo = ("    Leer n\n"
                  "    Si n > 0 Entonces\n"
                  "        Para i <- 1 Hasta n Hacer\n"
                  "            s <- 0\n"
                  "            Mientras s < i Hacer\n"
                  "                s <- s + 1\n"
                  "            FinMientras\n"
                  "            Escribir s\n"
                  "        FinPara\n"
                  "    Sino\n"
                  '        Escribir "nada"\n'
                  "    FinSi")
        self.assertEqual(self.salida(cuerpo, ["3"]), "1\n2\n3\n")
        self.assertEqual(self.salida(cuerpo, ["0"]), "nada\n")

    def test_contador_real_con_paso_decimal(self):
        self.assertEqual(self.salida("    Para x <- 1 Hasta 2 Con Paso 0.5 Hacer\n"
                                     "        Escribir x\n"
                                     "    FinPara"), "1.0\n1.5\n2.0\n")

    def test_el_final_y_el_paso_se_calculan_una_sola_vez(self):
        """Como `range()` en Python: cambiar `n` adentro no alarga el ciclo."""
        cuerpo = ("    n <- 3\n"
                  "    Para i <- 1 Hasta n Hacer\n"
                  "        n <- n + 1\n"
                  "    FinPara\n"
                  '    Escribir i, " ", n')
        self.assertEqual(self.salida(cuerpo), "4 6\n")

    def test_la_variable_queda_un_paso_mas_alla_del_final(self):
        """Decisión documentada en `_hacer_para`: como su Mientras equivalente."""
        self.assertEqual(self.salida("    Para i <- 1 Hasta 3 Hacer\n"
                                     "    FinPara\n"
                                     "    Escribir i"), "4\n")
        # Con cero vueltas queda en el valor inicial.
        self.assertEqual(self.salida("    Para i <- 7 Hasta 3 Hacer\n"
                                     "    FinPara\n"
                                     "    Escribir i"), "7\n")

    def test_leer_dentro_de_un_para(self):
        cuerpo = ("    Para i <- 1 Hasta 3 Hacer\n"
                  "        Leer n\n"
                  "        s <- s + n\n"
                  "    FinPara\n"
                  "    Escribir s")
        self.assertEqual(self.salida("    s <- 0\n" + cuerpo, ["5", "6", "7"]),
                         "18\n")
        e = self.fallar("    s <- 0\n" + cuerpo, ["5", "6"])
        self.assertEqual(e.codigo, "PS05")
        self.assertIn("ya consumió los 2 datos", e.por_que)

    def test_cuenta_como_instruccion_usada(self):
        r = ps.ejecutar_pseudo(SUMA_CON_PARA, entradas=["3"])
        self.assertEqual(r.instrucciones_usadas,
                         {"Definir", "Leer", "Asignar", "Para", "Escribir"})
        self.assertNotIn("Mientras", r.instrucciones_usadas)

    # -- la traza ------------------------------------------------------------
    def test_traza_en_tres_piezas(self):
        """Inicialización, pregunta e incremento son pasos distintos, cada uno
        con su bloque del diagrama, para que el trazador los pueda señalar."""
        r = ps.ejecutar_pseudo(SUMA_CON_PARA, entradas=["2"])
        self.assertTrue(r.ok, r.error_corto)
        lineas = [p.linea for p in r.pasos]
        # Definir, Leer, s<-0 | inicia | ¿1<=2? cuerpo inc | ¿2<=2? cuerpo inc
        # | ¿3<=2? | Escribir
        self.assertEqual(lineas, [2, 3, 4, 5, 5, 6, 7, 5, 6, 7, 5, 8])
        self.assertEqual(r.tabla_traza(["i", "s"]),
                         [(None, None), (None, None), (None, 0), (1, 0),
                          (1, 0), (1, 1), (2, 1), (2, 1), (2, 3), (3, 3),
                          (3, 3), (3, 3)])
        inicia, pregunta, _, incremento = r.pasos[3:7]
        self.assertIn("Empezó el Para", inicia.explicacion)
        self.assertIn("de 1 en 1, hasta llegar a 2", inicia.explicacion)
        self.assertIn("Se preguntó si i <= n (1 <= 2)", pregunta.explicacion)
        self.assertIn("SÍ", pregunta.explicacion)
        self.assertIn("'i' pasó de 1 a 2 (1 + 1)", incremento.explicacion)
        self.assertEqual(incremento.texto, "    FinPara")
        self.assertIn("(3 <= 2)", r.pasos[10].explicacion)
        self.assertIn("NO, así que el ciclo terminó", r.pasos[10].explicacion)
        # Tres bloques distintos del diagrama, y la pregunta siempre el mismo.
        self.assertEqual(len({inicia.nodo, pregunta.nodo, incremento.nodo}), 3)
        self.assertEqual(pregunta.nodo, r.pasos[7].nodo)
        self.assertEqual(pregunta.nodo, r.pasos[10].nodo)

    def test_traza_hacia_abajo(self):
        r = self.correr("    Para i <- 4 Hasta 1 Con Paso -2 Hacer\n"
                        "    FinPara")
        self.assertTrue(r.ok, r.error_corto)
        textos = " | ".join(p.explicacion for p in r.pasos)
        self.assertIn("hacia abajo, de 2 en 2, hasta llegar a 1", textos)
        self.assertIn("Se preguntó si i >= 1 (4 >= 1)", textos)
        self.assertIn("'i' pasó de 4 a 2 (4 - 2)", textos)

    def test_el_trazador_pinta_todos_los_pasos(self):
        r = ps.ejecutar_pseudo(SUMA_CON_PARA, entradas=["3"])
        for n in range(1, len(r.pasos) + 1):
            html = ps._html_trazador(SUMA_CON_PARA, r, n)
            self.assertIn("for i in range(1, n + 1):", html)
            self.assertIn(ps.RESALTE, html)        # siempre hay un bloque en rojo
        with silencio() as buffer:
            ps.trazador(SUMA_CON_PARA, ["3"])
        self.assertIn("Empezó el Para", buffer.getvalue())

    # -- el tope de pasos ----------------------------------------------------
    def test_la_guardia_de_ciclo_infinito_tambien_lo_cubre(self):
        e = self.fallar("    Para i <- 1 Hasta 3 Hacer\n"
                        "        i <- 0\n"
                        "    FinPara")
        self.assertEqual(e.codigo, "PS09")
        self.assertIn("10 000 pasos", e.que_paso)
        # Le habla del Para, no de «la condición del Mientras» que no escribió.
        self.assertNotIn("Mientras", e.por_que)
        self.assertIn("un Para termina cuando", e.por_que)
        self.assertIn("no le cambies el valor a su variable", e.arreglalo)

    def test_un_para_demasiado_largo_se_corta_y_conserva_la_traza(self):
        r = self.correr("    Para i <- 1 Hasta 1000000 Hacer\n"
                        "    FinPara")
        self.assertFalse(r.ok)
        self.assertEqual(r.error.codigo, "PS09")
        self.assertLessEqual(len(r.pasos), ps.MAX_PASOS)
        self.assertGreater(len(r.pasos), 100)

    def test_gasta_lo_mismo_que_su_mientras_equivalente(self):
        """4 999 vueltas caben en los 10 000 pasos con Para igual que con Mientras."""
        con_para = self.correr("    Para i <- 1 Hasta 4990 Hacer\n"
                               "    FinPara\n    Escribir i")
        con_mientras = self.correr("    i <- 1\n"
                                   "    Mientras i <= 4990 Hacer\n"
                                   "        i <- i + 1\n"
                                   "    FinMientras\n    Escribir i")
        self.assertTrue(con_para.ok, con_para.error_corto)
        self.assertTrue(con_mientras.ok, con_mientras.error_corto)
        self.assertEqual(con_para.salida, con_mientras.salida)

    def test_ps09_habla_del_ciclo_de_mas_adentro(self):
        e = self.fallar("    Para i <- 1 Hasta 3 Hacer\n"
                        "        s <- 0\n"
                        "        Mientras s < 1 Hacer\n"
                        "        FinMientras\n"
                        "    FinPara")
        self.assertEqual(e.codigo, "PS09")
        self.assertIn("la condición del Mientras", e.por_que)

    # -- los errores de la cabecera ------------------------------------------
    def test_paso_cero_es_un_error_claro(self):
        e = self.fallar("    Para i <- 1 Hasta 3 Con Paso 0 Hacer\n"
                        "        Escribir i\n"
                        "    FinPara")
        self.assertEqual(e.codigo, "PS09")
        self.assertEqual(
            e.que_paso,
            "el paso de este Para vale 0: la variable 'i' no avanzaría nunca y "
            "el ciclo no terminaría.")
        self.assertIn("Con Paso 1", e.arreglalo)
        self.assertIn("Con Paso -1", e.arreglalo)
        self.assertEqual(e.linea, 5)

    def test_paso_cero_calculado_tambien(self):
        """Un 0 que sale de una cuenta se ataja al entrar, sin esperar al tope."""
        r = self.correr("    salto <- 0\n"
                        "    Para i <- 1 Hasta 3 Con Paso salto Hacer\n"
                        "        Escribir i\n"
                        "    FinPara")
        self.assertFalse(r.ok)
        self.assertEqual(r.error.codigo, "PS09")
        self.assertIn("vale 0", r.error.que_paso)
        self.assertEqual(r.salida, "")                 # no dio ni una vuelta
        self.assertLess(len(r.pasos), 10)

    def test_igual_en_vez_de_flecha(self):
        """`Para i = 3 Hasta n Hacer`: se le pide la flecha, como en todo el motor."""
        e = self.fallar("    n <- 5\n"
                        "    Para i = 3 Hasta n Hacer\n"
                        "    FinPara")
        self.assertEqual(e.codigo, "PS02")
        self.assertEqual(e.que_paso, "usaste el signo = para guardar un valor.")
        self.assertIn("la flecha <-", e.por_que)
        self.assertEqual(e.arreglalo, "Para i <- 3 Hasta n Hacer")
        self.assertEqual(e.linea, 6)

    def test_falta_hacer(self):
        e = self.fallar("    Para i <- 1 Hasta 3\n    FinPara")
        self.assertEqual(e.codigo, "PS10")
        self.assertEqual(
            e.que_paso,
            "escribiste 'Para' pero falta la palabra Hacer al final de la línea.")
        self.assertEqual(e.arreglalo, "Para i <- 1 Hasta 10 Hacer")

    def test_falta_finpara(self):
        e = self.fallar("    Para i <- 1 Hasta 3 Hacer\n        Escribir i")
        self.assertEqual(e.codigo, "PS03")
        self.assertIn("abriste un bloque con 'Para' en la línea 5", e.que_paso)
        self.assertIn("Para/FinPara", e.por_que)
        self.assertIn("FinPara", e.arreglalo)

    def test_finpara_sin_para(self):
        e = self.fallar("    FinPara")
        self.assertEqual(e.codigo, "PS03")
        self.assertIn("no hay ningún bloque abierto", e.que_paso)

    def test_cierre_cruzado(self):
        """Un Para cerrado con FinMientras acusa al Para, que es lo que falta cerrar."""
        e = self.fallar("    Para i <- 1 Hasta 3 Hacer\n    FinMientras")
        self.assertEqual(e.codigo, "PS03")
        self.assertIn("'Para'", e.que_paso)
        self.assertIn("FinPara", e.arreglalo)

    def test_cabeceras_a_medio_escribir(self):
        casos = [
            ("Para", "no dijiste qué variable", "Para i <- 1 Hasta 10 Hacer"),
            ("Para i", "falta la flecha <-", "Para i <- 1 Hasta 10 Hacer"),
            ("Para i Desde 1 Hasta 3 Hacer", "falta la flecha <-",
             "Para i <- 1 Hasta 3 Hacer"),
            ("Para i <- 1 Hacer", "le falta la palabra Hasta",
             "Para i <- 1 Hasta 10 Hacer"),
            ("Para i <- Hasta 3 Hacer", "falta el valor donde empieza",
             "Para i <- 1 Hasta 3 Hacer"),
            ("Para i <- 1 Hasta Hacer", "falta el valor final",
             "Para i <- 1 Hasta 10 Hacer"),
            ("Para i <- 1 Hasta 3 Con Paso Hacer", "de cuánto en cuánto",
             "Para i <- 1 Hasta 3 Con Paso 2 Hacer"),
            ("Para i <- 1 Hasta 3 Paso 2 Hacer", "las dos palabras juntas",
             "Para i <- 1 Hasta 3 Con Paso 2 Hacer"),
            ("Para i <- 1 Hasta 3 Con 2 Hacer", "las dos palabras juntas",
             "Para i <- 1 Hasta 3 Con Paso 2 Hacer"),
        ]
        for linea, que_paso, arreglo in casos:
            with self.subTest(linea=linea):
                e = self.fallar(f"    {linea}\n    FinPara")
                self.assertEqual(e.codigo, "PS06")
                self.assertIn(que_paso, e.que_paso)
                self.assertEqual(e.arreglalo, arreglo)
                self.assertIn("la línea del Para dice cuatro cosas", e.por_que)
                self.assertEqual(e.linea, 5)

    def test_la_variable_tiene_que_existir(self):
        e = self.fallar("    Para k <- 1 Hasta 3 Hacer\n    FinPara")
        self.assertEqual(e.codigo, "PS01")
        self.assertIn("Definir k Como Entero", e.arreglalo)

    def test_la_variable_tiene_que_ser_un_numero(self):
        e = self.fallar("    Para t <- 1 Hasta 3 Hacer\n    FinPara")
        self.assertEqual(e.codigo, "PS04")
        self.assertIn("'t', está definida Como Cadena", e.que_paso)
        self.assertEqual(e.arreglalo, "Definir t Como Entero")

    def test_no_se_cuenta_con_textos(self):
        casos = [('Para i <- "uno" Hasta 3 Hacer', 'el texto "uno"'),
                 ('Para i <- 1 Hasta "tres" Hacer', "el valor final"),
                 ('Para i <- 1 Hasta 3 Con Paso "dos" Hacer', "el paso")]
        for linea, pista in casos:
            with self.subTest(linea=linea):
                e = self.fallar(f"    {linea}\n    FinPara")
                self.assertEqual(e.codigo, "PS04")
                self.assertIn(pista, e.que_paso)

    def test_paso_decimal_en_un_contador_entero(self):
        e = self.fallar("    Para i <- 1 Hasta 3 Con Paso 0.5 Hacer\n    FinPara")
        self.assertEqual(e.codigo, "PS04")
        self.assertIn("el número 1.5 en 'i'", e.que_paso)
        self.assertEqual(e.arreglalo, "Definir i Como Real")

    def test_no_se_puede_contar_con_una_constante(self):
        e = ps.ejecutar_pseudo(envolver("    Constante TOPE <- 3\n"
                                        "    Para TOPE <- 1 Hasta 3 Hacer\n"
                                        "    FinPara")).error
        self.assertEqual(e.codigo, "PS11")

    def test_si_el_cuerpo_vacia_la_variable_no_hay_traceback(self):
        """`Definir i` dentro del ciclo deja la caja vacía a mitad de la cuenta."""
        e = self.fallar("    Para i <- 1 Hasta 3 Hacer\n"
                        "        Definir i Como Entero\n"
                        "    FinPara")
        self.assertEqual(e.codigo, "PS01")
        self.assertIn("está vacía", e.que_paso)

    def test_para_cada_no_existe(self):
        e = self.fallar("    Para Cada x De t Hacer\n    FinPara")
        self.assertEqual(e.codigo, "PS06")
        self.assertEqual(e.que_paso, "este motor no tiene 'Para Cada'.")


class ParaEnElTraductor(unittest.TestCase):
    """El Para sale como una sola línea `for ... in range(...)`, y corre igual."""

    def linea_for(self, cabecera, tipo="Entero"):
        codigo = envolver(f"    Definir i, n, salto Como {tipo}\n"
                          f"    {cabecera}\n"
                          f"        Escribir i\n"
                          f"    FinPara")
        return ps.traducir_a_python(codigo).split("\n")[2]

    def test_range_con_el_mas_uno(self):
        casos = [
            ("Para i <- 1 Hasta 10 Hacer", "for i in range(1, 11):"),
            ("Para i <- 1 Hasta n Hacer", "for i in range(1, n + 1):"),
            ("Para i <- 3 Hasta n Con Paso 1 Hacer", "for i in range(3, n + 1):"),
            ("Para i <- 2 Hasta n - 1 Hacer", "for i in range(2, (n - 1) + 1):"),
            ("Para i <- n * 2 Hasta 20 Con Paso 5 Hacer",
             "for i in range(n * 2, 21, 5):"),
            ("Para i <- 10 Hasta 1 Con Paso -1 Hacer", "for i in range(10, 0, -1):"),
            ("Para i <- n Hasta 0 Con Paso -2 Hacer", "for i in range(n, -1, -2):"),
            ("Para i <- n Hasta salto Con Paso -2 Hacer",
             "for i in range(n, salto - 1, -2):"),
            # Paso que solo se conoce al ejecutar: el signo lo decide Python.
            ("Para i <- 1 Hasta n Con Paso salto Hacer",
             "for i in range(1, n + (1 if salto > 0 else -1), salto):"),
        ]
        for pseudo, python in casos:
            with self.subTest(pseudo=pseudo):
                self.assertEqual(self.linea_for(pseudo), python)

    def test_bloque_completo(self):
        py = ps.traducir_a_python(SUMA_CON_PARA).split("\n")
        self.assertEqual(py[4], "for i in range(1, n + 1):")
        self.assertEqual(py[5], "    s = s + i")
        self.assertEqual(py[6], "")               # FinPara cierra con la sangría
        self.assertEqual(py[7], "print(s)")

    def test_cuerpo_vacio_y_comentario(self):
        codigo = envolver("    Definir i Como Entero\n"
                          "    Para i <- 1 Hasta 3 Hacer   // tres vueltas\n"
                          "    FinPara")
        self.assertEqual(ps.traducir_a_python(codigo).split("\n")[2],
                         "for i in range(1, 4): pass  # tres vueltas")

    def test_contador_real_lleva_aviso(self):
        """`range` no cuenta con decimales, y el traductor no finge que sí."""
        linea = self.linea_for("Para i <- 1 Hasta 2 Hacer", tipo="Real")
        self.assertTrue(linea.startswith("for i in range(1, 3):"))
        self.assertIn("# range() solo cuenta con enteros", linea)

    def test_la_nota_explica_el_mas_uno(self):
        fuente, py, notas, error = ps._traduccion(SUMA_CON_PARA)
        self.assertIsNone(error)
        self.assertIn("uno ANTES", notas[4])
        self.assertIn("sangría", notas[6])

    def test_el_python_traducido_escribe_lo_mismo_que_el_motor(self):
        """La prueba que importa: se ejecutan los dos y se comparan las salidas."""
        cabeceras = ["Para i <- 1 Hasta n Hacer",
                     "Para i <- 3 Hasta n Con Paso 1 Hacer",
                     "Para i <- 0 Hasta n * 2 Con Paso 3 Hacer",
                     "Para i <- n Hasta 1 Con Paso -1 Hacer",
                     "Para i <- n Hasta -n Con Paso -4 Hacer",
                     "Para i <- 2 Hasta n - 1 Hacer",
                     "Para i <- 1 Hasta n Con Paso salto Hacer",
                     "Para i <- n Hasta 1 Con Paso 0 - salto Hacer",
                     "Para i <- 5 Hasta 1 Hacer"]
        for cabecera in cabeceras:
            for n in ("0", "1", "2", "7"):
                with self.subTest(cabecera=cabecera, n=n):
                    codigo = envolver(
                        "    Definir i, j, n, s, salto Como Entero\n"
                        "    Leer n\n"
                        "    salto <- 2\n"
                        "    s <- 0\n"
                        f"    {cabecera}\n"
                        "        Para j <- 1 Hasta 2 Hacer\n"
                        "            s <- s + i * j\n"
                        "        FinPara\n"
                        '        Escribir i, " ", s\n'
                        "    FinPara\n"
                        '    Escribir "fin ", s')
                    r = ps.ejecutar_pseudo(codigo, entradas=[n])
                    self.assertTrue(r.ok, r.error_corto)
                    python = ps.traducir_a_python(codigo)
                    with ps.entradas([n]), silencio() as buffer:
                        exec(compile(python, "<traducido>", "exec"), {})
                    # La primera línea es el eco del `input()` de mentiras.
                    self.assertEqual(buffer.getvalue().split("\n", 1)[1], r.salida)


class ParaEnElDiagrama(unittest.TestCase):
    """Inicialización -> rombo -> cuerpo -> incremento -> flecha de vuelta."""

    def arbol(self, codigo, resaltar=None):
        svg = ps.diagrama(codigo, resaltar_nodo=resaltar)
        return svg, ET.fromstring(svg)

    def test_la_secuencia_de_bloques(self):
        _, raiz = self.arbol(SUMA_CON_PARA)
        self.assertEqual(
            raiz.find(SVG + "desc").text,
            "INICIO → LEER n → s ← 0 → i ← 1 → ¿i <= n? → s ← s + i → "
            "i ← i + 1 → ESCRIBIR s → FIN")
        self.assertEqual(
            raiz.find(SVG + "title").text,
            "Diagrama de flujo del algoritmo SumaHastaN, 9 bloques")

    def test_las_figuras(self):
        _, raiz = self.arbol(SUMA_CON_PARA)
        rombos = [p for p in raiz.iter(SVG + "polygon")
                  if p.get("fill") == ps.COLOR["decision"][0]]
        self.assertEqual(len(rombos), 1)
        # s <- 0, la inicialización, el cuerpo y el incremento: cuatro procesos.
        procesos = [r for r in raiz.iter(SVG + "rect") if r.get("rx") == "6"]
        self.assertEqual(len(procesos), 4)
        etiquetas = [t.text for t in raiz.iter(SVG + "text")]
        self.assertIn("Sí", etiquetas)
        self.assertIn("No", etiquetas)

    def test_la_flecha_de_vuelta_sale_del_incremento_y_llega_al_rombo(self):
        alg = ps._analizar(SUMA_CON_PARA)
        items = ps._construir_layout(alg)
        colocados, aristas = [], []
        ps._disponer(items, ps.CX, ps.MARGEN, None, colocados, aristas)
        donde = {nodo["texto"]: (cx, cy) for nodo, cx, cy in colocados}
        _, y_rombo = donde["¿i <= n?"]
        _, y_inc = donde["i ← i + 1"]
        _, y_ini = donde["i ← 1"]
        self.assertLess(y_ini, y_rombo)                # la inicialización, antes
        self.assertLess(donde["s ← s + i"][1], y_inc)  # el incremento, al final
        alto_rombo, alto_caja = ps.DIM["decision"][1], ps.DIM["proceso"][1]
        arriba_del_rombo = (ps.CX, y_rombo - alto_rombo / 2)
        llegan = [a["pts"] for a in aristas if a["pts"][-1] == arriba_del_rombo]
        # Al rombo llegan dos flechas: la que baja de la inicialización (recta)
        # y la de vuelta, que sale de DEBAJO del incremento y rodea el ciclo.
        self.assertEqual(sorted(len(p) for p in llegan), [2, 5])
        directa, vuelta = sorted(llegan, key=len)
        self.assertEqual(directa[0], (ps.CX, y_ini + alto_caja / 2))
        self.assertEqual(vuelta[0], (ps.CX, y_inc + alto_caja / 2))
        self.assertLess(min(x for x, _ in vuelta), ps.CX)   # rodea por la izquierda

    def test_hacia_abajo_y_con_paso_calculado(self):
        codigo = envolver("    Definir i, n Como Entero\n"
                          "    n <- 2\n"
                          "    Para i <- 9 Hasta 1 Con Paso -3 Hacer\n"
                          "    FinPara\n"
                          "    Para i <- 1 Hasta 9 Con Paso n + 1 Hacer\n"
                          "    FinPara")
        _, raiz = self.arbol(codigo)
        desc = raiz.find(SVG + "desc").text
        self.assertIn("i ← 9 → ¿i >= 1? → i ← i - 3", desc)
        # Sin ejecutar no se sabe si sube o baja: se dice en palabras.
        self.assertIn("i ← 1 → ¿i no pasó de 9? → i ← i + (n + 1)", desc)

    def test_cada_paso_de_la_traza_resalta_un_bloque_que_existe(self):
        r = ps.ejecutar_pseudo(SUMA_CON_PARA, entradas=["2"])
        for paso in r.pasos:
            with self.subTest(paso=paso.n):
                svg = ps.diagrama(SUMA_CON_PARA, resaltar_nodo=paso.nodo)
                ET.fromstring(svg)
                self.assertIn(f'stroke="{ps.RESALTE}" stroke-width="3"', svg)

    def test_para_anidado_no_se_sale_del_lienzo(self):
        codigo = envolver("    Definir i, j Como Entero\n"
                          "    Para i <- 1 Hasta 2 Hacer\n"
                          "        Para j <- 1 Hasta 2 Hacer\n"
                          "            Escribir i * j\n"
                          "        FinPara\n"
                          "    FinPara")
        _, raiz = self.arbol(codigo)
        ancho = float(raiz.get("viewBox").split()[2])
        for linea in raiz.iter(SVG + "polyline"):
            for punto in linea.get("points").split():
                x = float(punto.split(",")[0])
                self.assertGreaterEqual(x, 0)
                self.assertLessEqual(x, ancho)


class ParaEnFlowgorithm(unittest.TestCase):

    def test_guion(self):
        with silencio() as buffer:
            ps.guion_flowgorithm(SUMA_CON_PARA)
        texto = buffer.getvalue()
        self.assertIn("For      i = 1 to n", texto)
        self.assertIn("Assign   s = s + i", texto)
        self.assertIn("EndFor", texto)

    def test_guion_hacia_abajo(self):
        codigo = envolver("    Definir i Como Entero\n"
                          "    Para i <- 9 Hasta 1 Con Paso -3 Hacer\n"
                          "    FinPara")
        with silencio() as buffer:
            ps.guion_flowgorithm(codigo)
        self.assertIn("For      i = 9 to 1 decreasing step 3", buffer.getvalue())

    def test_exportar(self):
        import tempfile
        ruta = os.path.join(tempfile.mkdtemp(), "para.fprg")
        with silencio():
            self.assertEqual(ps.exportar_flowgorithm(SUMA_CON_PARA, ruta), ruta)
        cuerpo = ET.parse(ruta).getroot().find("function/body")
        self.assertEqual([h.tag for h in cuerpo],
                         ["declare", "declare", "declare", "input", "assign",
                          "for", "assign", "output"])
        bloque = cuerpo.find("for")
        self.assertEqual(
            (bloque.get("variable"), bloque.get("start"), bloque.get("end"),
             bloque.get("direction"), bloque.get("step")),
            ("i", "1", "n", "inc", "1"))


class DosPalabras(unittest.TestCase):
    """`Fin Si`, `Fin Mientras`, `Fin Para`, `Fin Algoritmo` y la línea `Si no`."""

    def test_los_cierres_con_espacio_valen_igual(self):
        codigo = ("Algoritmo Cierres\n"
                  "    Definir i, n Como Entero\n"
                  "    Leer n\n"
                  "    Si n > 0 Entonces\n"
                  "        i <- 0\n"
                  "        Mientras i < n Hacer\n"
                  "            i <- i + 1\n"
                  "        Fin Mientras\n"
                  "        Para i <- 1 Hasta n Hacer\n"
                  "            Escribir i\n"
                  "        Fin Para\n"
                  "    Fin Si\n"
                  "Fin Algoritmo")
        r = ps.ejecutar_pseudo(codigo, entradas=["2"])
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "1\n2\n")
        pegado = (codigo.replace("Fin Mientras", "FinMientras")
                  .replace("Fin Para", "FinPara").replace("Fin Si", "FinSi")
                  .replace("Fin Algoritmo", "FinAlgoritmo"))
        self.assertEqual(ps.ejecutar_pseudo(pegado, entradas=["2"]).salida,
                         r.salida)
        # Y los demás consumidores del árbol ven lo mismo en las dos formas.
        self.assertEqual(ps.traducir_a_python(codigo), ps.traducir_a_python(pegado))
        self.assertEqual(ps.diagrama(codigo), ps.diagrama(pegado))

    def test_sin_distinguir_mayusculas_ni_cuantos_espacios(self):
        for cierre in ("fin si", "FIN SI", "Fin si", "fin   Si", "Fin\tSi"):
            with self.subTest(cierre=cierre):
                r = ps.ejecutar_pseudo(envolver(
                    "    Si 1 = 1 Entonces\n"
                    '        Escribir "ok"\n'
                    f"    {cierre}"))
                self.assertTrue(r.ok, r.error_corto)
                self.assertEqual(r.salida, "ok\n")

    def test_si_no_solo_en_su_linea_es_sino(self):
        for sino in ("Si no", "si no", "SI NO", "Si  no   // comentario"):
            with self.subTest(sino=sino):
                cuerpo = ("    Definir saldo Como Entero\n"
                          "    Leer saldo\n"
                          "    Si saldo > 0 Entonces\n"
                          '        Escribir "alcanza"\n'
                          f"    {sino}\n"
                          '        Escribir "no alcanza"\n'
                          "    Fin Si")
                for entrada, esperado in (("5", "alcanza\n"), ("0", "no alcanza\n")):
                    r = ps.ejecutar_pseudo(envolver(cuerpo), [entrada])
                    self.assertTrue(r.ok, r.error_corto)
                    self.assertEqual(r.salida, esperado)

    def test_si_no_con_una_pregunta_sigue_siendo_un_si(self):
        """`Si no <condición> Entonces` NO se convierte en nada: es un Si con NO."""
        cuerpo = ("    Definir listo Como Logico\n"
                  "    listo <- Falso\n"
                  "    Si no listo Entonces\n"
                  '        Escribir "falta"\n'
                  "    Sino\n"
                  '        Escribir "ya"\n'
                  "    FinSi")
        r = ps.ejecutar_pseudo(envolver(cuerpo))
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "falta\n")
        self.assertEqual(ps.traducir_a_python(envolver(cuerpo)).split("\n")[3],
                         "if not listo:")

    def test_un_si_no_suelto_no_tiene_que_cerrar(self):
        e = ps.ejecutar_pseudo(envolver("    Si no")).error
        self.assertEqual(e.codigo, "PS03")
        self.assertIn("no hay ningún bloque abierto", e.que_paso)

    def test_fin_seguido_de_otra_cosa(self):
        e = ps.ejecutar_pseudo(envolver("    Fin Ciclo")).error
        self.assertEqual(e.codigo, "PS06")
        self.assertEqual(e.que_paso,
                         "'Fin Ciclo' no cierra ningún bloque de este motor.")
        self.assertIn("FinSi, FinMientras, FinPara o FinAlgoritmo", e.arreglalo)
        self.assertNotIn("_", e.arreglalo)

    def test_fin_es_un_nombre_de_variable_valido(self):
        """No se le quita a nadie una variable que ya usaba: `fin <- 3` corre."""
        r = ps.ejecutar_pseudo(envolver("    Definir fin, si Como Entero\n"
                                        "    fin <- 3\n"
                                        "    Escribir fin + 1"))
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "4\n")

    def test_sino_y_si_en_la_misma_linea(self):
        """`Si no Si n = 2 Entonces`, literal de una entrega. No se adivina: se explica."""
        for linea in ("Si no Si n = 2 Entonces", "Sino Si n = 2 Entonces",
                      "si no si n = 2 entonces"):
            with self.subTest(linea=linea):
                e = ps.ejecutar_pseudo(envolver(
                    "    Definir n Como Entero\n"
                    "    n <- 2\n"
                    "    Si n = 1 Entonces\n"
                    '        Escribir "uno"\n'
                    f"    {linea}\n"
                    '        Escribir "dos"\n'
                    "    FinSi")).error
                self.assertIsNotNone(e, "corrió, y antes descartaba la pregunta")
                self.assertEqual(e.codigo, "PS06")
                self.assertEqual(e.linea, 6)
                self.assertIn("un Sino y otro Si en la misma línea", e.que_paso)
                self.assertIn("lleva su propio FinSi", e.por_que)
                self.assertEqual(
                    e.arreglalo,
                    "Sino   y en la línea de abajo:   Si n = 2 Entonces ... FinSi")

    def test_ya_no_se_descarta_lo_que_sigue_a_sino(self):
        e = ps.ejecutar_pseudo(envolver(
            "    Si 1 = 2 Entonces\n"
            '    Sino Escribir "x"\n'
            "    FinSi")).error
        self.assertEqual(e.codigo, "PS06")
        self.assertIn("sobró algo al final de la línea: 'Escribir'", e.que_paso)


class ProcesoComoAlgoritmo(unittest.TestCase):
    """`Proceso <nombre> ... FinProceso`: la otra forma que da PSeInt."""

    def test_es_sinonimo(self):
        con_proceso = PAPELERIA.replace("Algoritmo", "Proceso")
        self.assertTrue(con_proceso.startswith("Proceso CostoDeFotocopias"))
        self.assertTrue(con_proceso.endswith("FinProceso"))
        r = ps.ejecutar_pseudo(con_proceso, entradas=["40"])
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, ps.ejecutar_pseudo(PAPELERIA, ["40"]).salida)
        self.assertEqual(ps.traducir_a_python(con_proceso),
                         ps.traducir_a_python(PAPELERIA))
        self.assertEqual(ps.diagrama(con_proceso), ps.diagrama(PAPELERIA))

    def test_minusculas_espacio_y_cruzados(self):
        for abre, cierra in (("proceso", "finproceso"), ("Proceso", "Fin Proceso"),
                             ("Proceso", "FinAlgoritmo"), ("Algoritmo", "FinProceso")):
            with self.subTest(abre=abre, cierra=cierra):
                r = ps.ejecutar_pseudo(f'{abre} Hola\n    Escribir "hola"\n{cierra}')
                self.assertTrue(r.ok, r.error_corto)
                self.assertEqual(r.salida, "hola\n")

    def test_los_errores_hablan_de_proceso(self):
        e = ps.ejecutar_pseudo("Proceso A\n    Definir x Como Entero").error
        self.assertEqual(e.codigo, "PS03")
        self.assertIn("'Proceso' en la línea 1", e.que_paso)
        self.assertIn("FinProceso", e.arreglalo)
        e = ps.ejecutar_pseudo("Proceso\nFinProceso").error
        self.assertEqual(e.codigo, "PS13")
        self.assertEqual(e.que_paso,
                         "escribiste 'Proceso' pero no le pusiste nombre.")

    def test_un_proceso_dentro_de_otro(self):
        e = ps.ejecutar_pseudo("Algoritmo A\nProceso B\nFinProceso").error
        self.assertEqual(e.codigo, "PS06")
        self.assertIn("ya hay un algoritmo abierto", e.que_paso)


class LeerVariasVariables(unittest.TestCase):
    """`Leer a, b, n`: una entrada por variable, en orden. El motor ya lo hacía;
    el 5-oct se comprobó y aquí queda la prueba que faltaba."""

    CODIGO = envolver("    Definir a, b, n Como Entero\n"
                      "    Leer a, b, n\n"
                      '    Escribir a, " ", b, " ", n')

    def test_una_entrada_por_variable_en_orden(self):
        r = ps.ejecutar_pseudo(self.CODIGO, entradas=["2", "1", "6"])
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "2 1 6\n")
        self.assertEqual((r.memoria["a"], r.memoria["b"], r.memoria["n"]),
                         (2, 1, 6))
        # Es UNA instrucción: un solo paso en la traza, que cuenta las tres.
        self.assertEqual(len(r.pasos), 3)
        self.assertEqual(r.pasos[1].explicacion.count("Se tomó"), 3)

    def test_equivale_a_tres_leer(self):
        separado = self.CODIGO.replace("Leer a, b, n",
                                       "Leer a\n    Leer b\n    Leer n")
        self.assertEqual(ps.ejecutar_pseudo(separado, ["2", "1", "6"]).salida,
                         ps.ejecutar_pseudo(self.CODIGO, ["2", "1", "6"]).salida)

    def test_si_faltan_entradas_cuenta_las_tres(self):
        e = ps.ejecutar_pseudo(self.CODIGO, entradas=["2", "1"]).error
        self.assertEqual(e.codigo, "PS05")
        self.assertIn("Tu algoritmo tiene 3 Leer y le diste 2 datos.", e.por_que)

    def test_sin_las_comas_dice_como_se_escribe(self):
        e = ps.ejecutar_pseudo(self.CODIGO.replace("Leer a, b, n", "Leer a b n"),
                               entradas=["2", "1", "6"]).error
        self.assertEqual(e.codigo, "PS14")
        self.assertIn("sepáralas con coma: Leer a, b", e.arreglalo)


class ConsejosQueNoSonUnDisparate(unittest.TestCase):
    """PS14 aconsejó «Arréglalo: Para_i» 25 veces, y un alumno lo obedeció."""

    def fallar(self, linea):
        r = ps.ejecutar_pseudo(envolver(
            "    Definir i, n, x, opcion Como Entero\n"
            "    n <- 3\n"
            f"    {linea}"))
        self.assertFalse(r.ok, f"«{linea}» corrió y se esperaba un error")
        return r.error

    def test_estructuras_que_el_motor_no_tiene(self):
        casos = [
            ("Repetir", "Repetir ... Hasta Que", "Mientras o con Para"),
            ("Repetir x", "Repetir ... Hasta Que", "Mientras o con Para"),
            ("repetir", "Repetir ... Hasta Que", "Mientras o con Para"),
            ("Hasta Que i > 3", "Hasta Que", "Mientras o con Para"),
            ("Segun opcion Hacer", "Segun", "Si ... Sino ... FinSi"),
            ("Según opcion Hacer", "Segun", "Si ... Sino ... FinSi"),
            ("Fin Segun", "Segun", "Si ... Sino ... FinSi"),
            ("FinSegun", "Segun", "Si ... Sino ... FinSi"),
            ("Funcion r <- Doble(x)", "funciones propias", "dentro de Algoritmo"),
            ("Función r <- Doble(x)", "funciones propias", "dentro de Algoritmo"),
            ("FinFuncion", "funciones propias", "dentro de Algoritmo"),
            ("Fin Funcion", "funciones propias", "dentro de Algoritmo"),
            ("SubProceso Saludar", "subprocesos", "dentro de Algoritmo"),
            ("Imprimir x", "Imprimir", "se usa Escribir"),
            ("Limpiar Pantalla", "pantalla que limpiar", "borra esa línea"),
            ("Esperar Tecla", "que esperar", "borra esa línea"),
        ]
        for linea, que_falta, en_su_lugar in casos:
            with self.subTest(linea=linea):
                e = self.fallar(linea)
                self.assertEqual(e.codigo, "PS06")
                self.assertTrue(e.que_paso.startswith("este motor no tiene "),
                                e.que_paso)
                self.assertIn(que_falta, e.que_paso)
                self.assertIn(en_su_lugar, e.arreglalo)
                self.assertNotIn("_", e.arreglalo)
                self.assertIn("Mientras, Para.", e.por_que)   # lo que sí hay
                self.assertEqual(e.linea, 4)

    def test_el_error_de_segun_no_lo_tapa_el_de_sus_casos(self):
        """Los casos de un Segun llevan `:`, que el motor no conoce. El error que
        sirve es el de la línea del Segun, que está antes."""
        e = self.fallar("Segun opcion Hacer\n"
                        '        1: Escribir "uno"\n'
                        "        De Otro Modo:\n"
                        '            Escribir "otro"\n'
                        "    FinSegun")
        self.assertEqual(e.linea, 4)
        self.assertEqual(e.que_paso, "este motor no tiene Segun.")

    def test_los_errores_salen_en_el_orden_de_las_lineas(self):
        e = ps.ejecutar_pseudo("Algoritmo A\n"
                               "    Escrbir 1\n"          # línea 2: PS06
                               '    Escribir "sin cerrar\n'  # línea 3: PS07
                               "FinAlgoritmo").error
        self.assertEqual((e.codigo, e.linea), ("PS06", 2))
        # Y lo que hay después de FinAlgoritmo se ignora del todo, como ya
        # decía la «Decisión» del analizador, también si no se puede tokenizar.
        r = ps.ejecutar_pseudo('Algoritmo A\n    Escribir 1\nFinAlgoritmo\n'
                               'apuntes: esto ya no es del algoritmo; "ni esto')
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "1\n")

    def test_una_palabra_del_lenguaje_nunca_se_une_con_guion_bajo(self):
        """La garantía general: sea cual sea la línea, el arreglo que se propone
        no es pegarle un guion bajo a una palabra de estructura.

        2026-10-05, CAMBIADA tras la revisión. La primera versión metía en
        `propias` también a Fin, Hasta, Algoritmo, Proceso y los cuatro tipos, y
        con eso exigía que `Leer hora fin` o `Definir valor real, x Como Real`
        NO recibieran `hora_fin` ni `valor_real`: afirmaba como garantía lo que
        los revisores señalaron como regresión. Esas ocho palabras también son
        sustantivos corrientes; ahora solo se les exige no unirse cuando ABREN
        la línea, y `TambienSonMitadDeUnNombre` (abajo) fija lo demás.
        """
        # Las de estructura: no se unen a nada, estén donde estén.
        propias = ["Para", "Entonces", "Hacer", "Como", "Sino",
                   "FinSi", "FinPara", "FinMientras", "Mientras", "Si", "Definir",
                   "Leer", "Escribir", "Mostrar", "FinAlgoritmo", "FinProceso"]
        # Las que también son un sustantivo o un adjetivo cualquiera.
        sustantivos = ["Fin", "Hasta", "Algoritmo", "Proceso", "Entero", "Real",
                       "Cadena", "Logico"]
        # Las de PSeInt que el motor no tiene: no pueden ABRIR una línea. (Como
        # nombre de variable sí valen —`caso <- 3`—, y por eso no se prueban
        # dentro de un Definir o de un Leer.)
        ajenas = ["Repetir", "Segun", "Funcion", "Dimension", "Caso",
                  "Retornar", "SubProceso", "Imprimir", "Desde", "SinoSi"]
        palabras = propias + sustantivos + ajenas
        otras = ["i", "x", "Si", "Para", "Que", "Hacer", "opcion", "Mientras"]
        lineas = [f"{p} {o}" for p in palabras for o in otras]
        lineas += [f"{o} {p}" for p in propias for o in ("i", "x")]
        lineas += [f"Definir {p} {o} Como Entero" for p in propias
                   for o in ("i", "Si")]
        lineas += [f"Definir {o} {p}" for p in propias for o in ("i", "x")]
        lineas += [f"Leer {p} i" for p in propias]
        lineas += [f"Leer i {p}" for p in propias]
        self.assertGreaterEqual(len(lineas), 400)
        for linea in lineas:
            r = ps.ejecutar_pseudo(envolver(
                "    Definir i, n, x, opcion Como Entero\n"
                f"    {linea}\n"
                "    FinPara"), entradas=["1", "2"])
            if r.ok:
                continue
            with self.subTest(linea=linea):
                self.assertNotEqual(r.error.codigo, "PS00")
                for p in palabras:
                    self.assertNotIn(f"{p}_", r.error.arreglalo)
                    self.assertNotIn(f"_{p}", r.error.arreglalo)

    def test_palabras_fuera_de_sitio(self):
        casos = [("Entonces", "Entonces va al final de la línea del Si"),
                 ("Hacer", "Hacer va al final de la línea del Mientras o del Para"),
                 ("Como Entero", "Como solo se usa dentro de un Definir")]
        for linea, que_paso in casos:
            with self.subTest(linea=linea):
                e = self.fallar(linea)
                self.assertEqual(e.codigo, "PS06")
                self.assertIn(que_paso, e.que_paso)

    def test_instrucciones_a_las_que_les_falta_el_principio(self):
        e = self.fallar("total Como Entero")
        self.assertEqual(e.codigo, "PS06")
        self.assertEqual(e.arreglalo, "Definir total Como Entero")
        e = self.fallar("i Hasta 10 Hacer")
        self.assertEqual(e.codigo, "PS06")
        self.assertEqual(e.arreglalo, "Para i <- 1 Hasta 10 Hacer")
        e = self.fallar("i <- 3 Hasta n Hacer")
        self.assertEqual(e.codigo, "PS06")
        self.assertIn("no empieza por la palabra Para", e.que_paso)
        self.assertEqual(e.arreglalo, "Para i <- 3 Hasta n Hacer")

    def test_definir_sin_como_no_es_un_nombre_con_espacio(self):
        e = self.fallar("Definir total Entero")
        self.assertEqual(e.codigo, "PS06")
        self.assertEqual(e.que_paso, "a este Definir le falta la palabra Como.")
        self.assertEqual(e.arreglalo, "Definir total Como Entero")

    def test_definir_con_como_y_un_nombre_que_termina_en_tipo(self):
        """Revisión del 5-oct: la rama de «falta Como» se disparaba aunque el
        Como estuviera escrito, si el nombre con espacio terminaba en un tipo."""
        casos = [("Definir valor real, y Como Real", "valor real", "valor_real"),
                 ("Definir numero entero Como Entero", "numero entero",
                  "numero_entero"),
                 ("Definir a, lado real Como Real", "lado real", "lado_real"),
                 ("Definir es logico Como Logico", "es logico", "es_logico")]
        for linea, nombre, arreglo in casos:
            with self.subTest(linea=linea):
                e = self.fallar(linea)
                self.assertEqual(e.codigo, "PS14")
                self.assertEqual(e.que_paso,
                                 f"'{nombre}' no sirve como nombre de variable.")
                self.assertEqual(e.arreglalo, arreglo)
                self.assertNotIn("falta la palabra Como", e.que_paso)
        # Y cuando el Como falta de verdad (el tipo es lo último de la línea),
        # se sigue diciendo, también con varias variables.
        e = self.fallar("Definir a, b Entero")
        self.assertEqual(e.que_paso, "a este Definir le falta la palabra Como.")

    def test_ps14_sigue_sirviendo_para_lo_que_era(self):
        """Un nombre de verdad partido en dos se sigue arreglando con guion bajo."""
        e = self.fallar("costo pasaje <- 3200")
        self.assertEqual(e.codigo, "PS14")
        self.assertEqual(e.arreglalo, "costo_pasaje")
        # Y las palabras que sí pueden ser nombres no se le quitan a nadie.
        r = ps.ejecutar_pseudo(envolver(
            "    Definir caso, hasta, paso, con, repetir Como Entero\n"
            "    caso <- 1\n    hasta <- 2\n    paso <- 3\n    con <- 4\n"
            "    repetir <- 5\n"
            "    Escribir caso + hasta + paso + con + repetir"))
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "15\n")


class TambienSonMitadDeUnNombre(unittest.TestCase):
    """Revisión del 5-oct: tipos, `fin` y `hasta` dentro de un nombre con espacio.

    Son palabras del lenguaje, pero `numero entero`, `valor real`, `hora fin` y
    `edad hasta` son nombres que un alumno escribe sin pensar en el lenguaje. El
    arreglo es el de siempre (guion bajo), y el motor no puede contestar con una
    afirmación falsa: `numero_entero` y `hora_fin` son nombres válidos.
    """

    def fallar(self, linea):
        r = ps.ejecutar_pseudo(envolver(
            "    Definir i, n, x Como Entero\n"
            f"    {linea}"), entradas=["1", "2"])
        self.assertFalse(r.ok, f"«{linea}» corrió y se esperaba un error")
        return r.error

    def test_se_arreglan_con_guion_bajo_como_cualquier_otro(self):
        casos = [
            # Los que reprodujeron los revisores, literales.
            ("numero entero <- 5", "numero_entero"),
            ("Leer hora fin", "hora_fin"),
            ("edad hasta <- 18", "edad_hasta"),
            # La misma forma con las demás palabras de ese grupo.
            ("edad hasta = 18", "edad_hasta"),
            ("valor real <- 2.5", "valor_real"),
            ("es logico <- Verdadero", "es_logico"),
            ("Leer nombre cadena", "nombre_cadena"),
            ("numero proceso <- 3", "numero_proceso"),
            ("Para valor real <- 1 Hasta 3 Hacer", "valor_real"),
            # Y cuando la palabra del lenguaje es la PRIMERA mitad.
            ("fin semana <- 6", "fin_semana"),
            ("hasta ahora <- 0", "hasta_ahora"),
            ("caso base <- 1", "caso_base"),
            ("proceso actual <- 2", "proceso_actual"),
            ("Definir fin semana Como Entero", "fin_semana"),
        ]
        for linea, arreglo in casos:
            with self.subTest(linea=linea):
                e = self.fallar(linea)
                self.assertEqual(e.codigo, "PS14")
                self.assertIn("La costumbre es unir las palabras con guion bajo",
                              e.por_que)
                # Lo primero del arreglo es el nombre ya unido (en un Leer va
                # detrás la otra lectura: «si son dos variables...»).
                self.assertEqual(e.arreglalo.split("   ")[0], arreglo)
                # Ni rastro de la afirmación falsa ni del Para inventado.
                self.assertNotIn("no puede ser", e.por_que)
                self.assertNotIn("Hasta <-", e.arreglalo)
                self.assertNotIn("Hasta =", e.arreglalo)

    def test_lo_que_se_aconseja_corre(self):
        """El motor no puede aconsejar un nombre que él mismo rechace."""
        r = ps.ejecutar_pseudo(envolver(
            "    Definir valor_real, hora_fin Como Real\n"
            "    Definir numero_entero, edad_hasta, fin_semana Como Entero\n"
            "    Definir caso_base, hasta_ahora, fin Como Entero\n"
            "    valor_real <- 5\n    hora_fin <- 1\n    numero_entero <- 2\n"
            "    edad_hasta <- 18\n    fin_semana <- 6\n    caso_base <- 1\n"
            "    hasta_ahora <- 0\n    fin <- 3\n"
            "    Escribir valor_real\n"
            "    Escribir numero_entero + edad_hasta + fin_semana + caso_base"
            " + hasta_ahora + fin"))
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "5.0\n30\n")

    def test_la_red_de_ps14_ya_no_promete_lo_que_no_es(self):
        """Con una palabra de ESTRUCTURA de por medio no se aconseja el guion
        bajo, pero tampoco se afirma que la palabra «no puede ser un pedazo de
        un nombre» (`para_i` es, por desgracia, un nombre válido)."""
        for linea, palabra in [("Leer Para i", "Para"), ("Leer i Entonces",
                                                         "Entonces"),
                               ("Definir Si i Como Entero", "Si"),
                               ("total como <- 3", "como")]:
            with self.subTest(linea=linea):
                e = self.fallar(linea)
                self.assertEqual(e.codigo, "PS14")
                self.assertIn(f"'{palabra}' es una palabra con la que este "
                              f"lenguaje arma sus instrucciones", e.por_que)
                self.assertNotIn("_", e.arreglalo)
                self.assertNotIn("no puede ser", e.por_que)
                self.assertNotIn("solo puede ir", e.arreglalo)

    def test_cuando_no_es_un_nombre_se_dice_lo_que_es(self):
        """Las mismas palabras, en líneas que NO tienen forma de asignación."""
        # Un Para sin su principio: sigue recibiendo la cabecera completa...
        e = self.fallar("i Hasta 10 Hacer")
        self.assertEqual(e.arreglalo, "Para i <- 1 Hasta 10 Hacer")
        e = self.fallar("i Hasta 10")
        self.assertEqual(e.arreglalo, "Para i <- 1 Hasta 10 Hacer")
        e = self.fallar("i Hasta")
        self.assertEqual(e.arreglalo, "Para i <- 1 Hasta 10 Hacer")
        # ...un cierre que no cierra nada sigue siendo eso...
        e = self.fallar("Fin semana")
        self.assertIn("no cierra ningún bloque", e.que_paso)
        e = self.fallar("Hasta Que i > 3")
        self.assertIn("este motor no tiene Hasta Que", e.que_paso)
        # ...y `nombre Tipo` o `Tipo nombre` a solas es un Definir a medias.
        for linea in ("total Entero", "Entero total", "total entero"):
            with self.subTest(linea=linea):
                e = self.fallar(linea)
                self.assertEqual(e.codigo, "PS06")
                self.assertIn("le faltan las palabras Definir y Como", e.que_paso)
                self.assertEqual(e.arreglalo, "Definir total Como Entero")
        e = self.fallar("promedio lógico")
        self.assertEqual(e.arreglalo, "Definir promedio Como Logico")


class EstructurasDeOtroDialecto(unittest.TestCase):
    """Revisión del 5-oct: el disparate de PS14 seguía vivo para las palabras de
    estructura que no estaban en ninguna tabla (`SinoSi`, `Desde`, `Elif`,
    `Ciclo`, `For`). Ahora se decide por la forma de la línea."""

    PALABRAS = ("SinoSi", "Desde", "Elif", "Ciclo", "For", "While", "Loop",
                "Iterar", "PeroSi", "Cuando")

    def fallar(self, linea, dentro_de_si=False):
        if dentro_de_si:
            cuerpo = ("    Si n = 1 Entonces\n"
                      "        Escribir 1\n"
                      f"    {linea}\n"
                      "        Escribir 2\n"
                      "    FinSi")
        else:
            cuerpo = f"    {linea}\n        Escribir i\n    FinPara"
        r = ps.ejecutar_pseudo(envolver(
            "    Definir i, n, x Como Entero\n"
            "    n <- 3\n" + cuerpo))
        self.assertFalse(r.ok, f"«{linea}» corrió y se esperaba un error")
        self.assertNotEqual(r.error.codigo, "PS00")
        return r.error

    def corre(self, cabecera, cierre="FinPara"):
        r = ps.ejecutar_pseudo(envolver(
            "    Definir i, n, x Como Entero\n"
            "    n <- 3\n    x <- 0\n"
            f"    {cabecera}\n        x <- x + 1\n    {cierre}\n"
            "    Escribir x"))
        self.assertTrue(r.ok, f"«{cabecera}»: {r.error_corto}")
        return r.salida

    def test_sinosi_pegado_dentro_de_un_si(self):
        """La forma pegada de lo que un alumno entregó como `Si no Si ...`."""
        for linea in ("SinoSi n = 2 Entonces", "sinosi n = 2 entonces",
                      "SinoSi (n = 2) Entonces", "Elif n = 2 Entonces",
                      "ElseIf n = 2 Entonces"):
            with self.subTest(linea=linea):
                e = self.fallar(linea, dentro_de_si=True)
                self.assertEqual(e.codigo, "PS06")
                self.assertEqual(e.linea, 6)
                palabra = linea.split()[0]
                self.assertIn(f"este motor no tiene '{palabra}'", e.que_paso)
                self.assertIn("Sino va solo en su línea", e.por_que)
                self.assertIn("Sino   y en la línea de abajo:   Si ", e.arreglalo)
                self.assertIn("n = 2", e.arreglalo)
                self.assertIn("Entonces ... FinSi", e.arreglalo)
                self.assertNotIn("_", e.arreglalo)

    def test_el_que_ya_obedecio_sinosi_n(self):
        """El motor viejo aconsejaba `SinoSi_n`; a quien lo obedeció no se le
        contesta ahora «Arréglalo: SinoSi_n <- 2 Entonces»."""
        e = self.fallar("SinoSi_n = 2 Entonces", dentro_de_si=True)
        self.assertEqual(e.codigo, "PS06")
        self.assertIn("este motor no tiene 'SinoSi'", e.que_paso)
        self.assertEqual(e.arreglalo, "Sino   y en la línea de abajo:   "
                                      "Si n = 2 Entonces ... FinSi")

    def test_lo_que_se_aconseja_para_el_sinosi_corre(self):
        r = ps.ejecutar_pseudo(envolver(
            "    Definir n Como Entero\n    n <- 2\n"
            "    Si n = 1 Entonces\n        Escribir 1\n"
            "    Sino\n"
            "        Si n = 2 Entonces\n            Escribir 2\n        FinSi\n"
            "    FinSi"))
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "2\n")

    def test_desde_es_el_para_con_otro_nombre(self):
        e = self.fallar("Desde i <- 1 Hasta 5 Hacer")
        self.assertEqual(e.codigo, "PS06")
        self.assertEqual(e.que_paso, "este motor no tiene el ciclo Desde.")
        self.assertEqual(e.arreglalo, "es el mismo ciclo Para: cambia la "
                                      "palabra Desde por Para.")
        for cierre in ("FinDesde", "Fin Desde", "findesde"):
            with self.subTest(cierre=cierre):
                e = self.fallar(cierre)
                self.assertEqual(e.que_paso, "este motor no tiene el ciclo Desde.")
                self.assertIn("se cierra con FinPara", e.arreglalo)
        # Como nombre de variable, `desde` se le sigue dejando a quien lo use.
        r = ps.ejecutar_pseudo(envolver(
            "    Definir desde, sinosi Como Entero\n"
            "    desde <- 2\n    sinosi <- 3\n    Escribir desde + sinosi"))
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "5\n")

    def test_una_linea_que_cuenta_hasta_no_es_un_nombre(self):
        for palabra in ("Ciclo", "For", "Iterar", "Repite"):
            with self.subTest(palabra=palabra):
                e = self.fallar(f"{palabra} i <- 1 Hasta 5 Hacer")
                self.assertEqual(e.codigo, "PS06")
                self.assertIn("cuenta 'Hasta' un valor, como un ciclo Para",
                              e.que_paso)
                self.assertIn(f"empieza por '{palabra}', que no es una "
                              f"instrucción de este motor", e.que_paso)
                self.assertEqual(e.arreglalo, "Para i <- 1 Hasta 5 Hacer")
                self.assertEqual(self.corre(e.arreglalo), "5\n")
        # Con = en vez de flecha, sin Hacer, o sin flecha: la línea que se
        # propone es siempre una cabecera de Para que corre.
        e = self.fallar("For i = 1 Hasta 5 Hacer")
        self.assertEqual(e.arreglalo, "Para i <- 1 Hasta 5 Hacer")
        e = self.fallar("Ciclo i <- 1 Hasta n")
        self.assertEqual(e.arreglalo, "Para i <- 1 Hasta n Hacer")
        e = self.fallar("Ciclo i <- 1 Hasta n Con Paso 2 Hacer")
        self.assertEqual(e.arreglalo, "Para i <- 1 Hasta n Con Paso 2 Hacer")
        self.assertEqual(self.corre(e.arreglalo), "2\n")
        for coja in ("Ciclo i De 1 Hasta 5 Hacer", "Ciclo i <- Hasta 5 Hacer",
                     "Ciclo i <- 1 Hasta Hacer"):
            with self.subTest(linea=coja):
                e = self.fallar(coja)
                self.assertEqual(e.arreglalo, "Para i <- 1 Hasta 10 Hacer")

    def test_el_que_ya_obedecio_desde_i(self):
        """`Desde_i`, `For_i`, `Ciclo_i`: lo que aconsejaba el motor viejo. Al
        proponer el Para se desanda el prefijo, igual que con `para_i`."""
        for obedecio in ("Desde_i", "For_i", "Ciclo_i", "desde_i", "Para_i"):
            for flecha in ("<-", "="):
                with self.subTest(nombre=obedecio, flecha=flecha):
                    e = self.fallar(f"{obedecio} {flecha} 1 Hasta 5 Hacer")
                    self.assertEqual(e.codigo, "PS06")
                    self.assertIn("no empieza por la palabra Para", e.que_paso)
                    self.assertEqual(e.arreglalo, "Para i <- 1 Hasta 5 Hacer")
        # Un nombre con guion bajo de verdad no se toca.
        e = self.fallar("num_max <- 1 Hasta 5 Hacer")
        self.assertEqual(e.arreglalo, "Para num_max <- 1 Hasta 5 Hacer")

    def test_una_linea_que_termina_en_entonces_no_es_un_nombre(self):
        for palabra in ("Cuando", "PeroSi", "Caso_contrario", "If"):
            with self.subTest(palabra=palabra):
                e = self.fallar(f"{palabra} n = 2 Entonces", dentro_de_si=True)
                self.assertEqual(e.codigo, "PS06")
                self.assertIn("termina en Entonces, como la de un Si",
                              e.que_paso)
                self.assertIn(f"empieza por '{palabra}'", e.que_paso)
                self.assertTrue(e.arreglalo.startswith(
                    "Si n = 2 Entonces ... FinSi"), e.arreglalo)
                self.assertIn("Sino solo en su línea", e.arreglalo)
                self.assertNotIn(f"{palabra}_", e.arreglalo)

    def test_una_linea_que_termina_en_hacer_no_es_un_nombre(self):
        for palabra in ("Ciclo", "While", "Loop", "Repite"):
            with self.subTest(palabra=palabra):
                e = self.fallar(f"{palabra} x > 3 Hacer")
                self.assertEqual(e.codigo, "PS06")
                self.assertIn("termina en Hacer, como la de un ciclo",
                              e.que_paso)
                self.assertIn(f"empieza por '{palabra}'", e.que_paso)
                self.assertIn("Mientras <pregunta> Hacer", e.por_que)
                self.assertIn("Para <variable> <- <inicio> Hasta <fin> Hacer",
                              e.por_que)
                self.assertEqual(e.arreglalo, "Mientras x > 3 Hacer")
                self.assertEqual(self.corre(e.arreglalo, "FinMientras"), "0\n")

    def test_estructuras_a_las_que_les_falta_la_primera_palabra(self):
        """`n = 2 Entonces` recibía PS02 con «Arréglalo: n <- 2 Entonces», que
        tampoco corre. Es además donde aterrizaba quien había obedecido."""
        e = self.fallar("n = 2 Entonces")
        self.assertEqual(e.codigo, "PS06")
        self.assertEqual(e.que_paso,
                         "a esta línea le falta la palabra Si al principio.")
        self.assertEqual(e.arreglalo, "Si n = 2 Entonces")
        e = self.fallar("x = 3 Hacer")
        self.assertEqual(e.que_paso, "a esta línea le falta la palabra "
                                     "Mientras al principio.")
        self.assertEqual(e.arreglalo, "Mientras x = 3 Hacer")
        self.assertEqual(self.corre(e.arreglalo, "FinMientras"), "0\n")
        e = self.fallar("i = 3 Hasta n Hacer")
        self.assertIn("no empieza por la palabra Para", e.que_paso)
        self.assertEqual(e.arreglalo, "Para i <- 3 Hasta n Hacer")
        self.assertEqual(self.corre(e.arreglalo), "1\n")
        # Y el PS02 de siempre no se ha movido.
        e = self.fallar("x = 3")
        self.assertEqual(e.codigo, "PS02")
        self.assertEqual(e.arreglalo, "x <- 3")
        e = self.fallar("x = n + 1")
        self.assertEqual((e.codigo, e.arreglalo), ("PS02", "x <- n + 1"))

    def test_hasta_hacer_y_entonces_como_variables_no_cuentan_como_forma(self):
        """`hasta`, `hacer` y `entonces` valen como nombres de variable (lo fija
        `test_ps14_sigue_sirviendo_para_lo_que_era`). Usadas como DATO en una
        cuenta no convierten la línea en un Para ni en un Mientras: lo que las
        delata como estructura es tener un valor pegado delante."""
        for linea, arreglo in [("x = hasta + 1", "x <- hasta + 1"),
                               ("x = hasta - 1", "x <- hasta - 1"),
                               ("x = hasta", "x <- hasta"),
                               ("x = 3 * hasta + 1", "x <- 3 * hasta + 1"),
                               ("x = (hasta)", "x <- (hasta)"),
                               ("x = hacer", "x <- hacer"),
                               ("x = n + entonces", "x <- n + entonces")]:
            with self.subTest(linea=linea):
                e = self.fallar(linea)
                self.assertEqual((e.codigo, e.arreglalo), ("PS02", arreglo))
        for linea in ("edad max <- hasta + 1", "edad max <- hasta - 1",
                      "edad max <- hacer", "edad max = n + entonces"):
            with self.subTest(linea=linea):
                e = self.fallar(linea)
                self.assertEqual((e.codigo, e.arreglalo), ("PS14", "edad_max"))
        # Y como dato corren, también dentro de la cabecera de un Para.
        r = ps.ejecutar_pseudo(envolver(
            "    Definir hasta, hacer, i, x Como Entero\n"
            "    hasta <- 3\n    hacer <- 1\n    x <- hasta + hacer\n"
            "    Para i <- hacer Hasta hasta Hacer\n"
            "        x <- x + 1\n"
            "    FinPara\n"
            "    Escribir x"))
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "7\n")

    def test_una_flecha_dentro_no_se_repite_como_pregunta(self):
        """Nunca se propone `Mientras i <- 5 Hacer` ni `Si x <- 2 Entonces`."""
        for linea in ("Ciclo i <- 5 Hacer", "i Hasta <- 3 Hacer",
                      "edad hasta <- 18 Hacer", "Ciclo i <- Hasta 5",
                      "x = Hasta 3"):
            with self.subTest(linea=linea):
                e = self.fallar(linea)
                self.assertEqual(e.codigo, "PS06")
                self.assertIn("como un ciclo Para", e.que_paso)
                self.assertEqual(e.arreglalo, "Para i <- 1 Hasta 10 Hacer")
        e = self.fallar("Cuando x <- 2 Entonces", dentro_de_si=True)
        self.assertTrue(e.arreglalo.startswith("Si saldo > 0 Entonces"))
        for linea in ("x = n <- 3 Hacer", "x = n <- 3 Entonces"):
            with self.subTest(linea=linea):
                self.assertNotIn("<-", self.fallar(linea).arreglalo)

    def test_ninguna_palabra_inventada_acaba_pegada_con_guion_bajo(self):
        """La garantía, por forma y no por lista: con cualquier palabra al
        principio, una línea que abre un bloque nunca recibe `Palabra_x`; y si
        el alumno obedece lo que se le dice, tampoco la segunda respuesta."""
        inventadas = self.PALABRAS + ("Zzz", "Bucle", "Otro", "Entero", "caso",
                                      "Fin", "Hasta", "Algoritmo")
        formas = ["{p} i <- 1 Hasta 5 Hacer", "{p} i = 1 Hasta 5 Hacer",
                  "{p} i <- 1 Hasta 5", "{p} i Hasta 5 Hacer",
                  "{p} n = 2 Entonces", "{p} n > 2 Entonces", "{p} x Entonces",
                  "{p} x > 3 Hacer", "{p} x Hacer",
                  "{p}_i <- 1 Hasta 5 Hacer", "{p}_i = 1 Hasta 5 Hacer",
                  "{p}_n = 2 Entonces", "{p}_x = 3 Hacer"]
        vistas = 0
        for p in inventadas:
            for forma in formas:
                linea = forma.format(p=p)
                for dentro in (False, True):
                    r = ps.ejecutar_pseudo(envolver(
                        "    Definir i, n, x Como Entero\n    n <- 3\n"
                        + ("    Si n = 1 Entonces\n        Escribir 1\n"
                           if dentro else "")
                        + f"    {linea}\n        Escribir 2\n"
                        + ("    FinSi" if dentro else "    FinPara")))
                    with self.subTest(linea=linea, dentro=dentro):
                        self.assertFalse(r.ok)
                        e = r.error
                        self.assertNotEqual(e.codigo, "PS00")
                        self.assertNotEqual(e.codigo, "PS14", e.arreglalo)
                        self.assertNotEqual(e.codigo, "PS02", e.arreglalo)
                        # Nada de `Palabra_x`, salvo repetir el nombre que el
                        # propio alumno ya traía con guion bajo.
                        if "_" not in linea:
                            self.assertNotIn("_", e.arreglalo)
                        self.assertNotIn(" <- 2 Entonces", e.arreglalo)
                        self.assertNotIn("Hasta <-", e.arreglalo)
                        vistas += 1
        self.assertEqual(vistas, len(inventadas) * len(formas) * 2)


class LoQueEscribieronLosAlumnos(unittest.TestCase):
    """Las formas LITERALES de las entregas del ejercicio 2 de la semana 4.

    Cada una es un Fibonacci generalizado completo (lee a, b y n; escribe el
    término n) armado alrededor de la línea que el alumno escribió. Las que son
    pseudocódigo válido de PSeInt tienen que pasar los cinco casos de la prueba
    del cuadernillo, incluidos los dos bordes ocultos; las que no, tienen que
    fallar con un mensaje que diga cómo se arregla.
    """

    # (a, b, n) -> término n. Los tres visibles y los dos ocultos de s04 E2.
    CASOS = [((1, 1, 7), "13"), ((2, 1, 6), "11"), ((5, 5, 4), "15"),
             ((7, 3, 1), "7"), ((7, 3, 2), "3")]

    DEFINIR = ("    Definir a, b, n Como Entero\n"
               "    Definir anterior, actual, siguiente, i Como Entero\n")
    LEER = "    Leer a\n    Leer b\n    Leer n\n"
    VUELTA = ("            siguiente <- anterior + actual\n"
              "            anterior <- actual\n"
              "            actual <- siguiente\n")

    def programa(self, abre_ciclo, cierra_ciclo, sino="Sino", finsi="FinSi",
                 leer=None, antes_del_ciclo="", extra_vuelta=""):
        return ("Algoritmo FibonacciGeneral\n" + self.DEFINIR
                + (leer or self.LEER)
                + "    anterior <- a\n"
                  "    actual <- b\n"
                  "    Si n = 1 Entonces\n"
                  "        Escribir anterior\n"
                + f"    {sino}\n"
                + antes_del_ciclo
                + f"        {abre_ciclo}\n"
                + self.VUELTA + extra_vuelta
                + f"        {cierra_ciclo}\n"
                  "        Escribir actual\n"
                + f"    {finsi}\n"
                  "FinAlgoritmo")

    def debe_pasar(self, codigo):
        for (a, b, n), esperado in self.CASOS:
            with self.subTest(a=a, b=b, n=n):
                r = ps.ejecutar_pseudo(codigo, entradas=[str(a), str(b), str(n)])
                self.assertTrue(r.ok, r.error_corto)
                self.assertEqual(r.salida.strip(), esperado)

    def debe_fallar(self, codigo):
        r = ps.ejecutar_pseudo(codigo, entradas=["1", "1", "7"])
        self.assertFalse(r.ok, "corrió, y se esperaba un error con su arreglo")
        self.assertNotEqual(r.error.codigo, "PS00")
        return r.error

    def test_1_para_con_paso_y_finpara(self):
        self.debe_pasar(self.programa("Para i <- 3 Hasta n Con Paso 1 Hacer",
                                      "FinPara"))

    def test_2_todo_en_minusculas(self):
        codigo = self.programa("para i <- 3 hasta n hacer", "finpara").lower()
        self.assertIn("algoritmo fibonaccigeneral", codigo)
        self.assertIn("finalgoritmo", codigo)
        self.debe_pasar(codigo)

    def test_3_para_con_igual_y_fin_para(self):
        e = self.debe_fallar(self.programa("Para i = 3 Hasta n Hacer", "Fin Para"))
        self.assertEqual(e.codigo, "PS02")
        self.assertEqual(e.arreglalo, "Para i <- 3 Hasta n Hacer")
        self.assertEqual(
            e.error_corto,
            "[PS02] línea 12: usaste el signo = para guardar un valor. "
            "Arréglalo: Para i <- 3 Hasta n Hacer")
        # Corregido el =, el mismo programa (con su `Fin Para`) pasa.
        self.debe_pasar(self.programa("Para i <- 3 Hasta n Hacer", "Fin Para"))

    def test_4_el_que_obedecio_la_pista_vieja(self):
        """`para_i <- 3 hasta n hacer ... fin para`: se le devuelve al Para."""
        e = self.debe_fallar(self.programa("para_i <- 3 hasta n hacer", "fin para"))
        self.assertEqual(e.codigo, "PS06")
        self.assertIn("no empieza por la palabra Para", e.que_paso)
        # (Segunda revisión: el arreglo sale en la forma canónica, `Hasta` y
        # `Hacer` con mayúscula, porque ahora se ARMA validando cada cuenta en
        # vez de copiar la línea del alumno tal cual. Corre igual.)
        self.assertEqual(e.arreglalo, "Para i <- 3 Hasta n Hacer")
        self.assertNotIn("sobró algo", e.que_paso)
        self.debe_pasar(self.programa(e.arreglalo, "fin para"))

    def test_5_fin_si_y_fin_mientras_con_espacio(self):
        self.debe_pasar(self.programa(
            "Mientras i < n Hacer", "Fin Mientras", finsi="Fin Si",
            antes_del_ciclo="        i <- 2\n",
            extra_vuelta="            i <- i + 1\n"))
        self.debe_pasar(self.programa(
            "Mientras i < n Hacer", "fin mientras", finsi="fin si",
            antes_del_ciclo="        i <- 2\n",
            extra_vuelta="            i <- i + 1\n"))

    def test_6_si_no_con_espacio(self):
        # Solo en su línea, `Si no` es el Sino de toda la vida.
        self.debe_pasar(self.programa("Para i <- 3 Hasta n Hacer", "FinPara",
                                      sino="Si no"))
        # Seguido de otro Si en la misma línea, como en la entrega, no.
        e = self.debe_fallar(self.programa(
            "Para i <- 3 Hasta n Hacer", "FinPara",
            sino="Si no Si n = 2 Entonces"))
        self.assertEqual(e.codigo, "PS06")
        self.assertIn("un Sino y otro Si en la misma línea", e.que_paso)
        self.assertIn("Si n = 2 Entonces ... FinSi", e.arreglalo)

    def test_7_leer_tres_en_una_linea(self):
        self.debe_pasar(self.programa("Para i <- 3 Hasta n Hacer", "FinPara",
                                      leer="    Leer a, b, n\n"))

    def test_8_sin_algoritmo_ni_finalgoritmo(self):
        completo = self.programa("Para i <- 3 Hasta n Hacer", "FinPara")
        sin_marco = "\n".join(completo.split("\n")[1:-1])
        e = self.debe_fallar(sin_marco)
        self.assertEqual(e.codigo, "PS13")
        self.assertIn("Algoritmo MiPrimerAlgoritmo", e.arreglalo)
        e = self.debe_fallar("\n".join(completo.split("\n")[:-1]))
        self.assertEqual(e.codigo, "PS03")
        self.assertIn("FinAlgoritmo", e.arreglalo)

    def test_las_formas_de_pseint_todas_juntas(self):
        """Proceso, Leer en una línea, Para con paso, `Si no` y cierres con espacio."""
        self.debe_pasar(
            "Proceso FibonacciGeneral\n" + self.DEFINIR
            + "    // los dos primeros los da el usuario\n"
              "    Leer a, b, n\n"
              "    anterior <- a\n"
              "    actual <- b\n"
              "    Si n = 1 Entonces\n"
              "        Escribir anterior\n"
              "    Si no\n"
              "        Para i <- 3 Hasta n Con Paso 1 Hacer\n"
            + self.VUELTA
            + "        Fin Para\n"
              "        Escribir actual\n"
              "    Fin Si\n"
              "Fin Proceso")

    def test_escribir_antes_de_leer_se_ve_en_la_salida(self):
        """Comprobado el 5-oct: el letrero queda en la salida, antes del dato."""
        r = ps.ejecutar_pseudo(envolver("    Definir a Como Entero\n"
                                        '    Escribir "Dame a"\n'
                                        "    Leer a\n"
                                        "    Escribir a"), entradas=["7"])
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida, "Dame a\n7\n")

    def test_la_solucion_de_referencia_con_mientras_sigue_pasando(self):
        self.debe_pasar(self.programa(
            "Mientras i < n Hacer", "FinMientras",
            antes_del_ciclo="        i <- 2\n",
            extra_vuelta="            i <- i + 1\n"))



class ElArregloDeUnParaSiempreCorre(unittest.TestCase):
    """2026-10-05, segunda revisión del arreglo de los cuadernillos 4 y 6.

    La primera versión del Para armaba su «Arréglalo» pegando trozos de lo que
    el alumno había escrito, sin comprobar que quedara un Para: `Para i <= n
    Hacer` recibía «Para i <- <= n Hacer», y obedeciéndolo al pie de la letra
    —que es lo que hizo el alumno del `para_i`— se llegaba en tres pasos a un
    callejón sin salida. Estas pruebas fijan el invariante: si el arreglo que
    se propone empieza por Para o por Mientras, ESA LÍNEA se analiza.
    """

    MOLDE = ("Algoritmo T\n"
             "    Definir i, j, n, veces Como Entero\n"
             "    n <- 3\n"
             "    i <- 1\n"
             "    veces <- 2\n"
             "    {linea}\n"
             "        Escribir i\n"
             "{mueve}"
             "    {cierre}\n"
             "FinAlgoritmo")
    LINEA_DE_LA_CABECERA = 6

    def correr(self, linea, cierre="FinPara", mueve=""):
        return ps.ejecutar_pseudo(self.MOLDE.format(linea=linea, cierre=cierre,
                                                    mueve=mueve))

    def arreglo_de(self, linea):
        r = self.correr(linea)
        self.assertFalse(r.ok, f"{linea!r} corrió y se esperaba un error")
        self.assertEqual(r.error.linea, self.LINEA_DE_LA_CABECERA, r.error_corto)
        return r.error

    def comprobar_que_corre(self, arreglo):
        """La primera mitad del arreglo (lo que va antes de un paréntesis de
        aclaración) puesta en el lugar de la línea mala."""
        linea = arreglo.split("   ")[0]
        # El invariante es SINTÁCTICO: la cabecera se analiza. Que luego una
        # variable no exista (PS01: `saldo` es el marcador del ejemplo, o una
        # variable que el alumno nunca definió) o que el ciclo no termine
        # (PS09) son errores de ejecución, con su propio mensaje claro.
        aceptables = ("PS01", "PS09")
        if linea.startswith("Mientras "):
            self.assertRegex(linea, r"^Mientras .+ Hacer$")
            r = self.correr(linea, "FinMientras", "        i <- i + 1\n")
        else:
            self.assertRegex(
                linea, r"^Para \w+ <- .+ Hasta .+?( Con Paso .+)? Hacer$")
            r = self.correr(linea)
        self.assertTrue(r.ok or r.error.codigo in aceptables,
                        f"{linea!r} -> {r.error_corto}")
        if not r.ok:
            self.assertNotEqual(r.error.linea, self.LINEA_DE_LA_CABECERA - 1)

    # Las líneas exactas con las que la revisión tumbó la versión anterior, y
    # lo que se les contesta ahora.
    DE_LA_REVISION = [
        ("Para i <= n Hacer", "Mientras i <= n Hacer"),
        ("Para i < 3 Hacer", "Mientras i < 3 Hacer"),
        ("Para i < - 1 Hasta n Hacer", "Para i <- 1 Hasta n Hacer"),
        ("Para i -> 1 Hasta n Hacer", "Para i <- 1 Hasta n Hacer"),
        ("Para i de 1 a n Hacer", "Para i <- 1 Hasta n Hacer"),
        ("Para i en n Hacer", "Para i <- 1 Hasta 10 Hacer"),
        ("Para n veces Hacer", "Para i <- 1 Hasta 10 Hacer"),
        ("Para i Hasta 3 Hacer", "Para i <- 1 Hasta 3 Hacer"),
        ("Para i <- 1 a 3 Hacer", "Para i <- 1 Hasta 3 Hacer"),
        ("Para i <- 1, 3 Hacer", "Para i <- 1 Hasta 3 Hacer"),
        ("Para i <- 1 Mientras i <= 3 Hacer", "Para i <- 1 Hasta 10 Hacer"),
        ("Para i = 1 a n Hacer", "Para i <- 1 Hasta n Hacer"),
        ("Para i <= 1 Hasta n Hacer", "Para i <- 1 Hasta n Hacer"),
        ("Para i <- 1 Hacer", "Para i <- 1 Hasta 10 Hacer"),
        ("Para i <- 1 Hasta 3 Con Paso 0 Hacer", None),      # paso cero: PS09
    ]

    def test_las_lineas_de_la_revision(self):
        for linea, esperado in self.DE_LA_REVISION:
            with self.subTest(linea=linea):
                e = self.arreglo_de(linea)
                if esperado is None:
                    continue
                self.assertEqual(e.arreglalo.split("   ")[0], esperado)
                self.assertNotIn("<- <", e.arreglalo)
                self.assertNotIn("<- -", e.arreglalo.replace("<- -1", ""))
                self.comprobar_que_corre(e.arreglalo)

    def test_obedecer_el_arreglo_converge_en_un_paso(self):
        """Lo que hizo el alumno del `para_i`: copiar el arreglo tal cual. Con
        la versión anterior, `Para i <= n Hacer` necesitaba tres pasos y
        acababa en un consejo sobre otra cosa."""
        for linea, _ in self.DE_LA_REVISION:
            with self.subTest(linea=linea):
                e = self.arreglo_de(linea)
                primera = e.arreglalo.split("   ")[0]
                if primera.startswith(("Para ", "Mientras ")):
                    self.comprobar_que_corre(primera)

    def test_la_pregunta_recibe_un_mientras_y_dice_como_cerrarlo(self):
        e = self.arreglo_de("Para i <= n Hacer")
        self.assertEqual(e.codigo, "PS06")
        self.assertIn("un Para no pregunta", e.que_paso)
        self.assertIn("FinMientras", e.arreglalo)
        self.assertIn("Para i <- 1 Hasta 10 Hacer", e.arreglalo)

    def test_decir_a_en_vez_de_hasta_se_explica(self):
        e = self.arreglo_de("Para i <- 1 a 3 Hacer")
        self.assertIn("se anuncia con Hasta", e.que_paso)
        # ...pero una variable que se llame `a` sigue siendo una variable.
        r = ps.ejecutar_pseudo(
            "Algoritmo T\n    Definir a, i Como Entero\n    a <- 2\n"
            "    Para i <- a Hasta 3 Hacer\n        Escribir i\n    FinPara\n"
            "FinAlgoritmo")
        self.assertTrue(r.ok, r.error_corto)
        self.assertEqual(r.salida.split(), ["2", "3"])

    def test_garantia_por_combinacion(self):
        """Ninguna cabecera de Para, por mal escrita que esté, recibe como
        arreglo una línea Para/Mientras que no se analice. 4 x 9 x 6 x 9 x 2
        formas; las que resultan ser un Para válido simplemente corren."""
        # Tercera revisión: las pistas se arman en varias puertas, no solo
        # en la de `Para`. Entran las líneas que empiezan por la variable
        # (`i Hasta 10 Entonces`), por una palabra ajena (`For`, `Ciclo`,
        # `Desde`) o por un Para con tilde, que es otra palabra.
        palabras = ["Para", "para", "PARA", "Pára", "For", "Ciclo", "Desde", ""]
        flechas = ["<-", "", "<", "<=", "< -", "->", "=", "de", "desde"]
        inicios = ["1", "", "n - 1", "1 a 3", "1, 3", "(n"]
        finales = ["Hasta n", "", "Hasta", "Hasta n Con Paso 2", "Hasta n Con Paso",
                   "Hasta n Paso 2", "a n", "Hasta n Con Paso 0", "Mientras i < 3",
                   "to n", "Hasta n, 2", "Hasta n Hasta 10", "Hasta n MOD"]
        cierres = ["Hacer", "", "Entonces", "Hacer FinPara"]
        vistas = propuestas = 0
        for p in palabras:
            for f in flechas:
                for ini in inicios:
                    for fin in finales:
                        for c in cierres:
                            linea = " ".join(x for x in (p.strip(), "i", f, ini, fin, c) if x)
                            r = self.correr(linea)
                            vistas += 1
                            if r.ok:
                                continue
                            # PS00 es el motor reventando por dentro: no puede
                            # salir NUNCA, y menos pasar por «error en otra
                            # línea». (Esta comprobación existe porque la
                            # primera versión de este arreglo lo hacía con
                            # `Para i < 3 Hacer`.)
                            self.assertNotEqual(r.error.codigo, "PS00",
                                                f"{linea!r} revienta el motor")
                            if r.error.linea != self.LINEA_DE_LA_CABECERA:
                                continue
                            primera = r.error.arreglalo.split("   ")[0]
                            if not primera.startswith(("Para ", "Mientras ")):
                                continue
                            propuestas += 1
                            with self.subTest(linea=linea, arreglo=primera):
                                self.comprobar_que_corre(primera)
        self.assertEqual(vistas, 8 * 9 * 6 * 13 * 4)
        self.assertGreater(propuestas, 6000, "la batería dejó de ejercitar el arreglo")

    def test_las_otras_puertas_de_la_tercera_revision(self):
        """Las líneas exactas con las que la tercera revisión tumbó la segunda:
        no empiezan por Para y aun así recibían un Para o un Mientras que no
        se analiza."""
        casos = [
            ("i Hasta 10 Entonces", "Para i <- 1 Hasta 10 Hacer"),
            ("i Hasta n Hacer FinPara", None),
            ("i Hasta n, 2 Hacer", "Para i <- 1 Hasta 10 Hacer"),
            ("i Hasta n Hasta 10 Hacer", "Para i <- 1 Hasta 10 Hacer"),
            ("i Hasta n MOD Hacer", "Para i <- 1 Hasta 10 Hacer"),
            ("i Hasta n Con Paso 0 Hacer", "Para i <- 1 Hasta n Hacer"),
            ("For i = 1 to n Hacer", None),
            ("For i de 1 a n Hacer", "Para i <- 1 Hasta n Hacer"),
            ("Bucle i de 1 a n Hacer", "Para i <- 1 Hasta n Hacer"),
            ("Ciclo i de 1 a 3 Hacer", "Para i <- 1 Hasta 3 Hacer"),
            ("Repite i, n Hacer", None),
        ]
        for linea, esperado in casos:
            with self.subTest(linea=linea):
                e = self.arreglo_de(linea)
                primera = e.arreglalo.split("   ")[0]
                if esperado is not None:
                    self.assertEqual(primera, esperado)
                if primera.startswith(("Para ", "Mientras ")):
                    self.comprobar_que_corre(primera)

if __name__ == "__main__":
    unittest.main(verbosity=2)
