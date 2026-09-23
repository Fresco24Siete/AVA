#!/usr/bin/env node
/* Que el tutor reciba el enunciado y el codigo del alumno, y NUNCA la celda de
 * prueba.
 *
 * Esa ultima parte es la que importa y por eso hay una prueba. El contexto se
 * habia quitado entero porque antes viajaba la celda de prueba con sus assert
 * dentro, que llevan la respuesta esperada: un tutor que ve la respuesta puede
 * regalarla. Al devolver el contexto hay que garantizar que esa mitad no vuelve.
 *
 *     node backend/tests/telemetria/prueba_tutor_contexto.js
 */
const fs = require('fs');
const path = require('path');

const RUTA = path.join(__dirname, '..', '..', '..', 'notebook', 'tutor_ia.js');

let pasan = 0, fallan = 0;
function ok(nombre, cond, detalle) {
    if (cond) { pasan++; console.log('OK    ' + nombre); }
    else { fallan++; console.log('FALLO ' + nombre); if (detalle) console.log('      ' + detalle); }
}

// --- Un notebook de mentira con la forma que produce el constructor ---------
function celdaMd(texto) {
    return { cell_type: 'markdown', metadata: {}, get_text: () => texto };
}
function celdaSolucion(n, codigo) {
    return {
        cell_type: 'code',
        metadata: { nbgrader: { grade_id: 'ejercicio_' + n, solution: true, grade: false } },
        get_text: () => codigo,
    };
}
function celdaPrueba(n, codigo) {
    return {
        cell_type: 'code',
        metadata: { nbgrader: { grade_id: 'test_ejercicio_' + n, solution: false, grade: true } },
        get_text: () => codigo,
    };
}

const ENUNCIADO = '### Ejercicio 2 — La cadena de notas\n\nEscribe letra(nota).';
const CODIGO_ALUMNO = 'def letra(nota):\n    if nota >= 4.5:\n        return "A"';
const CELDA_PRUEBA =
    'assert letra(4.5) == "A", "4.5 es A"\n' +
    '### INICIO PRUEBAS OCULTAS\nassert letra(3.99) == "C"\n### FIN PRUEBAS OCULTAS';

const CELDAS = [
    celdaMd('# Cuadernillo'),
    celdaMd(ENUNCIADO),
    celdaSolucion(2, CODIGO_ALUMNO),
    celdaPrueba(2, CELDA_PRUEBA),
];

// --- Se carga tutor_ia.js con un Jupyter falso ------------------------------
function cargar(indiceSeleccionado) {
    const fuente = fs.readFileSync(RUTA, 'utf8');
    const notebook = {
        get_cells: () => CELDAS,
        get_selected_index: () => indiceSeleccionado,
        notebook_path: 'semana_03.ipynb',
        notebook_name: 'semana_03.ipynb',
    };
    const ventana = {
        Jupyter: { notebook, notebook_list: null },
        localStorage: { getItem: () => null, setItem: () => {} },
        document: { querySelector: () => null, getElementById: () => null,
                    addEventListener: () => {}, cookie: '' },
        addEventListener: () => {},
        fetch: () => Promise.resolve({ ok: true, json: () => Promise.resolve({}) }),
    };
    ventana.window = ventana;

    // Se extrae la funcion de contexto y sus ayudantes, que es lo que se prueba.
    // Ejecutar el archivo entero arrastraria todo el pintado de la interfaz.
    const trozos = [];
    for (const nombre of ['function jup(', 'var LIMITE_CONTEXTO',
                          'function celda_de_solucion_actual(', 'function enunciado_de(',
                          'function contexto_del_ejercicio(']) {
        const i = fuente.indexOf(nombre);
        if (i < 0) throw new Error('no se encontro en tutor_ia.js: ' + nombre);
        // hasta la linea en blanco que cierra el bloque de nivel superior
        let fin = fuente.indexOf('\n    }\n', i);
        fin = fin < 0 ? fuente.indexOf('\n', i) : fin + 7;
        trozos.push(fuente.slice(i, fin));
    }
    const cuerpo = trozos.join('\n') + '\n; return contexto_del_ejercicio();';
    return new Function('Jupyter', 'window', 'document', cuerpo)(
        ventana.Jupyter, ventana, ventana.document);
}

// --- Las pruebas -------------------------------------------------------------
const ctx = cargar(2);   // el cursor en la celda de solucion

ok('1. el contexto lleva el enunciado del ejercicio',
   ctx.includes('La cadena de notas'), ctx.slice(0, 120));

ok('2. el contexto lleva el codigo que escribio el alumno',
   ctx.includes('def letra(nota)'), ctx.slice(0, 120));

ok('3. NO lleva la celda de prueba', !ctx.includes('assert letra'), ctx);

ok('4. NO lleva las pruebas ocultas',
   !ctx.includes('PRUEBAS OCULTAS') && !ctx.includes('3.99'), ctx);

// Con el cursor EN la celda de prueba tampoco debe filtrarse: se busca hacia
// arriba y se encuentra la de solucion, no la de prueba.
const ctxDesdePrueba = cargar(3);
ok('5. con el cursor en la celda de prueba, tampoco la manda',
   !ctxDesdePrueba.includes('assert letra'), ctxDesdePrueba);

// Antes de cualquier ejercicio no hay nada que mandar.
const ctxArriba = cargar(0);
ok('6. antes del primer ejercicio el contexto va vacio',
   ctxArriba === '', JSON.stringify(ctxArriba));

console.log('\n' + pasan + '/' + (pasan + fallan) + ' casos OK');
process.exit(fallan ? 1 : 0);
