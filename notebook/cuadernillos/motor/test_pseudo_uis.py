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
        self.assertEqual(
            e.por_que,
            "las instrucciones que entiendo son: Definir, Constante, Leer, "
            "Escribir, Si, Mientras.")
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
