#!/usr/bin/env node
'use strict';
// Pruebas de notebook/custom.js (captura de telemetria en el navegador).
// Carga el archivo REAL con vm.runInNewContext sobre un entorno simulado minimo
// (Jupyter falso, document falso, fetch/sendBeacon capturados, localStorage en
// memoria). Sin dependencias npm. Correr: node prueba_customjs.js
//
// No toca el stack docker ni la base de datos: todo ocurre en memoria.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const RUTA_CUSTOM = path.resolve(__dirname, '../../../notebook/custom.js');
const FUENTE = fs.readFileSync(RUTA_CUSTOM, 'utf8');
const ESC = String.fromCharCode(27); // ESC de los codigos ANSI que manda ipykernel

// ---------------------------------------------------------------------------
// DOM falso: lo justo para lo que custom.js toca al cargar y en la tarjeta de
// rating. innerHTML se "parsea" de forma plana (solo tags con id/class/data-v/
// disabled) para que querySelector('#id') / querySelectorAll('.clase') funcionen.
// ---------------------------------------------------------------------------
function crearDocumento() {
  const todos = [];
  let documento;
  class Elemento {
    constructor(tag) {
      this.tagName = tag; this.id = ''; this.className = ''; this.style = {};
      this.children = []; this.parentNode = null; this.dataset = {};
      this.value = ''; this.textContent = ''; this.disabled = false;
      this._inner = ''; this._listeners = {}; this._raizCelda = false;
      todos.push(this);
    }
    get innerHTML() { return this._inner; }
    set innerHTML(html) {
      this._inner = html; this.children = [];
      const re = /<(\w+)([^>]*)>/g; let m;
      while ((m = re.exec(html))) {
        const el = new Elemento(m[1]); const attrs = m[2];
        const id = /\bid="([^"]*)"/.exec(attrs); if (id) el.id = id[1];
        const cls = /\bclass="([^"]*)"/.exec(attrs); if (cls) el.className = cls[1];
        const dv = /\bdata-v="([^"]*)"/.exec(attrs); if (dv) el.dataset.v = dv[1];
        if (/\bdisabled\b/.test(attrs)) el.disabled = true;
        el.parentNode = this; this.children.push(el);
      }
    }
    _desc() { const out = []; (function rec(e) { for (const c of e.children) { out.push(c); rec(c); } })(this); return out; }
    _coincide(el, sel) {
      if (sel[0] === '#') return el.id === sel.slice(1);
      if (sel[0] === '.') return (' ' + el.className + ' ').indexOf(' ' + sel.slice(1) + ' ') >= 0;
      return el.tagName === sel;
    }
    querySelector(sel) { return this._desc().find(e => this._coincide(e, sel)) || null; }
    querySelectorAll(sel) { return this._desc().filter(e => this._coincide(e, sel)); }
    appendChild(c) { c.parentNode = this; this.children.push(c); return c; }
    insertBefore(c) { c.parentNode = this; this.children.unshift(c); return c; }
    remove() { if (this.parentNode) { const i = this.parentNode.children.indexOf(this); if (i >= 0) this.parentNode.children.splice(i, 1); this.parentNode = null; } }
    addEventListener(n, fn) { (this._listeners[n] = this._listeners[n] || []).push(fn); }
    dispatch(n) { (this._listeners[n] || []).forEach(fn => fn({ preventDefault() {} })); }
    _adjunto() { let e = this; while (e.parentNode) e = e.parentNode; return e === documento.body || e === documento.head || e._raizCelda === true; }
  }
  documento = {
    cookie: '_xsrf=abc; otra=x',
    body: null, head: null,
    createElement(tag) { return new Elemento(tag); },
    getElementById(id) { return todos.find(e => e.id === id && e._adjunto()) || null; },
    querySelector() { return null; },
    Elemento,
  };
  documento.body = new Elemento('body'); documento.head = new Elemento('head');
  return documento;
}

// ---------------------------------------------------------------------------
// Celda falsa de nbclassic: solo lo que custom.js lee.
// ---------------------------------------------------------------------------
function celda(doc, opts) {
  const raiz = new doc.Elemento('div'); raiz._raizCelda = true;
  const jq = { 0: raiz, length: 1,
    find() { return { remove() {}, append() {}, length: 0 }; },
    append() {}, addClass() {}, removeClass() {} };
  return {
    cell_type: 'code',
    metadata: opts.nbgrader ? { nbgrader: opts.nbgrader } : {},
    output_area: { outputs: [] },
    input_prompt_number: null,
    get_text() { return opts.texto || ''; },
    element: jq,
  };
}
function errorOutput(ename, evalue) {
  return { output_type: 'error', ename, evalue,
    traceback: [ESC + '[0;31m---------------------------------------------------------------------------' + ESC + '[0m',
      ESC + '[0;31m' + ename + ESC + '[0m  Traceback (most recent call last)',
      ESC + '[0;31m' + ename + ESC + '[0m: ' + evalue] };
}

// ---------------------------------------------------------------------------
// Entorno: carga custom.js de verdad y devuelve los ganchos para manipularlo.
// ---------------------------------------------------------------------------
function cargarEntorno(celdas, opts) {
  opts = opts || {};
  const doc = crearDocumento();
  const fetches = [], beacons = [], timeouts = [], consola = [];
  const almacen = {};
  const localStorage = {
    getItem(k) { return Object.prototype.hasOwnProperty.call(almacen, k) ? almacen[k] : null; },
    setItem(k, v) { almacen[k] = String(v); },
    removeItem(k) { delete almacen[k]; }, _datos: almacen,
  };
  if (opts.estadoPrevio) almacen[opts.estadoPrevio.clave] = JSON.stringify(opts.estadoPrevio.valor);
  const handlers = {};
  const events = {
    on(n, fn) { (handlers[n] = handlers[n] || []).push(fn); },
    one(n, fn) { this.on(n, fn); },
    off() {},
    trigger(n, data) { (handlers[n] || []).forEach(fn => fn({ type: n }, data)); },
  };
  const Jupyter = { notebook: {
    base_url: '/user/x/', notebook_path: opts.notebook_path || 'semana_01.ipynb',
    notebook_name: opts.notebook_name || 'semana_01.ipynb',
    events, get_cells() { return celdas; }, save_notebook() { return Promise.resolve(); },
  } };
  const utils = {};
  const winListeners = {};
  const ventana = {
    localStorage, location: { href: 'http://localhost:8000/user/x/notebooks/semana_01.ipynb', pathname: '/user/x/notebooks/semana_01.ipynb' },
    addEventListener(n, fn) { (winListeners[n] = winListeners[n] || []).push(fn); },
    dispatchEvent(n) { (winListeners[n] || []).forEach(fn => fn({ type: n })); },
  };
  const ctx = {
    window: ventana, document: doc, localStorage,
    navigator: { sendBeacon(url, blob) { beacons.push({ url, body: JSON.parse(blob._texto) }); return true; } },
    Blob: class { constructor(partes) { this._texto = partes.join(''); } },
    fetch(url, options) {
      fetches.push({ url, options, body: options && options.body ? JSON.parse(options.body) : null });
      // opts.respuesta permite simular un puente que rechaza (403, 502...)
      const r = opts.respuesta || { ok: true, status: 204 };
      if (r.error) return Promise.reject(new Error(r.error));
      return Promise.resolve({ ok: r.ok, status: r.status, json() { return Promise.resolve({}); } });
    },
    console: { log(...a) { consola.push(['log', a.join(' ')]); }, warn(...a) { consola.push(['warn', a.join(' ')]); }, error(...a) { consola.push(['error', a.join(' ')]); } },
    setTimeout(fn, ms) { timeouts.push({ fn, ms }); return timeouts.length; },
    Date, JSON, Math, Object, Array, String, Number, parseInt, encodeURIComponent, decodeURIComponent, Promise, isFinite,
    require(deps, cb) { cb(Jupyter, utils); },
  };
  ctx.window.document = doc; ctx.window.navigator = ctx.navigator; ctx.window.fetch = ctx.fetch;
  vm.createContext(ctx);
  vm.runInNewContext(FUENTE, ctx, { filename: 'custom.js' });
  return { doc, fetches, beacons, timeouts, consola, localStorage, events, ventana, Jupyter, handlers };
}

// Simula la secuencia real de nbclassic para ejecutar una celda:
// execute.CodeCell con prompt '*', luego outputs, luego finished_execute.CodeCell.
// promptAlTerminar: que vale input_prompt_number cuando se dispara finished_execute
// (en nbclassic 1.3.3 finished_execute sale de finished_iopub.Kernel, NO de
// _handle_execute_reply, asi que puede seguir valiendo '*').
function ejecutar(env, cell, outputs, promptAlTerminar) {
  cell.input_prompt_number = '*';
  cell.output_area.outputs = [];
  env.events.trigger('execute.CodeCell', { cell });
  cell.output_area.outputs = outputs || [];
  cell.input_prompt_number = promptAlTerminar === undefined ? 7 : promptAlTerminar;
  env.events.trigger('finished_execute.CodeCell', { cell });
}

// ---------------------------------------------------------------------------
// Mini-framework de asercion
// ---------------------------------------------------------------------------
let fallos = 0, total = 0;
const resultados = [];
function caso(nombre, fn) {
  total++;
  try { fn(); resultados.push('OK    ' + nombre); }
  catch (e) { fallos++; resultados.push('FALLO ' + nombre + '\n      ' + (e.stack || e).toString().split('\n').slice(0, 3).join('\n      ')); }
}
function afirmar(cond, msg) { if (!cond) throw new Error('asercion: ' + msg); }
function igual(a, b, msg) { const ja = JSON.stringify(a), jb = JSON.stringify(b); if (ja !== jb) throw new Error((msg || 'igual') + ': esperado ' + jb + ', obtenido ' + ja); }
const ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;

function notebookBasico(doc) {
  const sol1 = celda(doc, { nbgrader: { grade: false, solution: true, locked: false, grade_id: 'ejercicio_1' } });
  const test1 = celda(doc, { nbgrader: { grade: true, solution: false, locked: true, grade_id: 'test_ejercicio_1', points: 3 } });
  const libre = celda(doc, {});
  return { sol1, test1, libre, celdas: [celda(doc, {}), sol1, test1, libre] };
}

// ===========================================================================
caso('0. custom.js se carga en Node y registra los hooks esperados', () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas);
  igual(Object.keys(env.handlers).sort(), ['execute.CodeCell', 'finished_execute.CodeCell', 'notebook_loaded.Notebook'], 'eventos registrados');
  afirmar(env.consola.some(l => l[1].indexOf('[nbgrader-metrics] listo') === 0), 'log de arranque');
  igual(env.fetches.length, 0, 'sin fetch al cargar');
});

caso('1. Intento exitoso -> un fetch exercise_attempt passed con cabeceras', () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.sol1, []);
  igual(env.fetches.length, 0, 'la solucion no envia nada');
  ejecutar(env, nb.test1, []);
  igual(env.fetches.length, 1, 'un solo fetch');
  const f = env.fetches[0];
  igual(f.url, '/user/x/nbgrader-metrics/evento', 'url');
  igual(f.options.method, 'POST'); igual(f.options.credentials, 'same-origin');
  igual(f.options.headers['X-XSRFToken'], 'abc', 'xsrf'); igual(f.options.headers['Content-Type'], 'application/json');
  const b = f.body;
  igual(b.tipo_evento, 'exercise_attempt'); igual(b.exercise_id, 'ejercicio_1'); igual(b.codigo_celda, 'test_ejercicio_1');
  igual(b.orden, 3, 'orden = indice+1 (indice 2)'); igual(b.puntos_maximos, 3); igual(b.validation_result, 'passed'); igual(b.errors, []);
  afirmar(ISO.test(b.attempt_at), 'attempt_at ISO');
  igual(Object.keys(b).sort(), ['attempt_at', 'codigo_celda', 'errors', 'exercise_id', 'orden', 'puntos_maximos', 'tipo_evento', 'validation_result'], 'claves exactas');
});

caso('2. Fallo: NameError en solucion + AssertionError en prueba -> failed con 2 errores en orden', () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.sol1, [errorOutput('NameError', "name 'total' is not defined")]);
  igual(env.fetches.length, 0, 'solucion con error no envia');
  ejecutar(env, nb.test1, [errorOutput('AssertionError', 'Todo programa debe terminar con PARAR')]);
  igual(env.fetches.length, 1);
  const b = env.fetches[0].body;
  igual(b.validation_result, 'failed'); igual(b.errors.length, 2);
  igual(b.errors[0].cell_id, 'ejercicio_1'); igual(b.errors[0].error_type, 'NameError');
  igual(b.errors[0].error_message, "NameError: name 'total' is not defined");
  igual(b.errors[1].cell_id, 'test_ejercicio_1'); igual(b.errors[1].error_type, 'AssertionError');
  igual(b.errors[1].error_message, 'AssertionError: Todo programa debe terminar con PARAR');
  for (const e of b.errors) {
    afirmar(ISO.test(e.timestamp), 'timestamp ISO');
    afirmar(typeof e.traceback === 'string' && e.traceback.indexOf(ESC) < 0, 'traceback sin ANSI');
    afirmar(e.traceback.indexOf('Traceback (most recent call last)') >= 0, 'traceback con contenido');
    igual(Object.keys(e).sort(), ['cell_id', 'error_message', 'error_type', 'timestamp', 'traceback']);
  }
});

caso('3. Multiples intentos failed, failed, passed -> 3 fetch y el buffer se vacia tras cada envio', () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.sol1, [errorOutput('NameError', 'x')]);
  ejecutar(env, nb.test1, [errorOutput('AssertionError', 'a1')]);
  ejecutar(env, nb.sol1, [errorOutput('TypeError', 'y')]);
  ejecutar(env, nb.test1, [errorOutput('AssertionError', 'a2')]);
  ejecutar(env, nb.sol1, []);
  ejecutar(env, nb.test1, []);
  igual(env.fetches.length, 3);
  const [f1, f2, f3] = env.fetches.map(f => f.body);
  igual(f1.validation_result, 'failed'); igual(f1.errors.map(e => e.error_type), ['NameError', 'AssertionError']);
  igual(f2.validation_result, 'failed'); igual(f2.errors.map(e => e.error_type), ['TypeError', 'AssertionError'], '2o intento solo trae sus errores');
  igual(f2.errors.map(e => e.error_message), ['TypeError: y', 'AssertionError: a2']);
  igual(f3.validation_result, 'passed'); igual(f3.errors, []);
  const st = JSON.parse(env.localStorage.getItem('nbgrader-metrics:semana_01.ipynb'));
  igual(st.errores.ejercicio_1, [], 'buffer vacio en localStorage');
  afirmar(!('ejercicio_1' in st.intentos), 'intentos borrado al pasar');
});

caso('4a. sin_validar: solucion con error sin correr la prueba + beforeunload -> sendBeacon', () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.sol1, [errorOutput('NameError', "name 'x' is not defined")]);
  igual(env.fetches.length, 0);
  env.ventana.dispatchEvent('beforeunload');
  igual(env.beacons.length, 1, 'un beacon');
  igual(env.beacons[0].url, '/user/x/nbgrader-metrics/evento?_xsrf=abc');
  const b = env.beacons[0].body;
  igual(b.tipo_evento, 'exercise_attempt'); igual(b.exercise_id, 'ejercicio_1'); igual(b.validation_result, 'sin_validar');
  igual(b.errors.length, 1); igual(b.errors[0].error_type, 'NameError');
  afirmar(!('codigo_celda' in b) && !('orden' in b) && !('puntos_maximos' in b), 'sin codigo_celda/orden/puntos_maximos');
  igual(Object.keys(b).sort(), ['attempt_at', 'errors', 'exercise_id', 'tipo_evento', 'validation_result']);
  igual(env.fetches.length, 0, 'no usa fetch');
  const st = JSON.parse(env.localStorage.getItem('nbgrader-metrics:semana_01.ipynb'));
  igual(st.errores.ejercicio_1, [], 'buffer vaciado tras el beacon');
  env.ventana.dispatchEvent('beforeunload');
  igual(env.beacons.length, 1, 'un segundo unload no reenvia');
});

caso('4b. sin_validar: si el ejercicio ya paso, beforeunload no manda nada', () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.sol1, [errorOutput('NameError', 'x')]);
  ejecutar(env, nb.test1, []);
  igual(env.fetches.length, 1);
  env.ventana.dispatchEvent('beforeunload');
  igual(env.beacons.length, 0, 'ningun beacon');
});

caso('5. Celda sin metadata nbgrader con error -> ningun fetch ni buffer (errores de exploracion no se registran)', () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.libre, [errorOutput('ZeroDivisionError', 'division by zero')]);
  igual(env.fetches.length, 0);
  env.ventana.dispatchEvent('beforeunload');
  igual(env.beacons.length, 0);
  // beforeunload siempre persiste (custom.js:485), pero el estado queda sin errores
  igual(JSON.parse(env.localStorage.getItem('nbgrader-metrics:semana_01.ipynb')).errores, {}, 'buffer sin nada');
});

function notebookDosEjercicios(doc) {
  const s1 = celda(doc, { nbgrader: { grade: false, solution: true, grade_id: 'ejercicio_1' } });
  const t1 = celda(doc, { nbgrader: { grade: true, solution: false, grade_id: 'test_ejercicio_1', points: 2 } });
  const s2 = celda(doc, { nbgrader: { grade: false, solution: true, grade_id: 'ejercicio_2' } });
  const t2 = celda(doc, { nbgrader: { grade: true, solution: false, grade_id: 'test_ejercicio_2', points: 4 } });
  return { s1, t1, s2, t2, celdas: [s1, t1, s2, t2] };
}

caso('6a. Rating (AUDITORIA 6.6, corregido): ultima prueba pasa con input_prompt_number="*" en finished_execute -> SI se ofrece la tarjeta', () => {
  const doc = crearDocumento(); const nb = notebookDosEjercicios(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.t1, [], 5);           // ya tiene numero (reply llego antes)
  igual(env.fetches.length, 1); igual(env.fetches[0].body.validation_result, 'passed');
  afirmar(env.doc.getElementById('nbgrader-rating-card') === null, 'con una prueba pendiente no se ofrece');
  ejecutar(env, nb.t2, [], '*');         // como en nbclassic: finished_iopub antes que execute_reply
  igual(env.fetches.length, 2); igual(env.fetches[1].body.validation_result, 'passed', 'el evento si reporta passed');
  const tarjeta = env.doc.getElementById('nbgrader-rating-card');
  afirmar(tarjeta !== null, 'la tarjeta debe ofrecerse aunque el prompt de la celda recien ejecutada sea "*"');
  afirmar(tarjeta.parentNode === nb.t2.element[0], 'insertada en la ultima celda de prueba');
});

caso('6b. Rating: con input_prompt_number numerico en finished_execute SI se ofrece, y enviar hace fetch cuadernillo_rating', () => {
  const doc = crearDocumento(); const nb = notebookDosEjercicios(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.t1, [], 5);
  ejecutar(env, nb.t2, [], 6);
  const tarjeta = env.doc.getElementById('nbgrader-rating-card');
  afirmar(tarjeta !== null, 'tarjeta ofrecida');
  afirmar(tarjeta.parentNode === nb.t2.element[0], 'insertada en la ultima celda de prueba');
  const btn = tarjeta.querySelector('#nbg-rating-send');
  afirmar(btn.disabled === true, 'boton deshabilitado al inicio');
  btn.dispatch('click');
  igual(env.fetches.length, 2, 'click sin estrella no envia');
  const stars = tarjeta.querySelectorAll('.nbg-star'); igual(stars.length, 5);
  stars[3].dispatch('click');
  afirmar(btn.disabled === false, 'boton habilitado tras elegir estrella');
  tarjeta.querySelector('#nbg-comment').value = '  muy bueno  ';
  btn.dispatch('click');
  igual(env.fetches.length, 3);
  const b = env.fetches[2].body;
  igual(b.tipo_evento, 'cuadernillo_rating'); igual(b.rating, 4); igual(b.comment, 'muy bueno');
  afirmar(ISO.test(b.submitted_at), 'submitted_at ISO');
  igual(Object.keys(b).sort(), ['comment', 'rating', 'submitted_at', 'tipo_evento']);
  igual(env.fetches[2].options.headers['X-XSRFToken'], 'abc');
  btn.dispatch('click');
  igual(env.fetches.length, 3, 'no se reenvia el rating');
  const st = JSON.parse(env.localStorage.getItem('nbgrader-metrics:semana_01.ipynb'));
  igual(st.rating_enviado, true);
});

caso('6c. Rating: la tarjeta tampoco aparece si otra prueba nunca se ejecuto (prompt null) aunque la ultima pase', () => {
  const doc = crearDocumento(); const nb = notebookDosEjercicios(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.t2, [], 6);
  afirmar(env.doc.getElementById('nbgrader-rating-card') === null);
});

caso('7. Limitacion: prueba VACIA o sin asserts (sin outputs de error) -> passed', () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.test1, []);                                   // sin ningun output
  ejecutar(env, nb.test1, [{ output_type: 'stream', name: 'stdout', text: 'hola\n' }]);  // solo print
  igual(env.fetches.map(f => f.body.validation_result), ['passed', 'passed']);
});

caso('8. Estado por notebook: clave localStorage nbgrader-metrics:<notebook_path>', () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas, { notebook_path: 'work/semana_02.ipynb', notebook_name: 'semana_02.ipynb' });
  ejecutar(env, nb.sol1, [errorOutput('NameError', 'x')]);
  igual(Object.keys(env.localStorage._datos), ['nbgrader-metrics:work/semana_02.ipynb']);
  const st = JSON.parse(env.localStorage._datos['nbgrader-metrics:work/semana_02.ipynb']);
  igual(Object.keys(st).sort(), ['errores', 'intentos', 'primer_intento']);
  igual(st.errores.ejercicio_1.length, 1);
  // y un estado previo persistido (F5) se retoma: el error viejo viaja en el siguiente intento
  const doc2 = crearDocumento(); const nb2 = notebookBasico(doc2);
  const env2 = cargarEntorno(nb2.celdas, { notebook_path: 'work/semana_02.ipynb', estadoPrevio: { clave: 'nbgrader-metrics:work/semana_02.ipynb', valor: st } });
  ejecutar(env2, nb2.test1, []);
  igual(env2.fetches[0].body.errors.length, 1, 'error previo (antes del F5) incluido');
  igual(env2.fetches[0].body.validation_result, 'passed');
});

caso('9. El payload no lleva student_id/course_id/cuadernillo_id ni nombre del notebook', () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.sol1, [errorOutput('NameError', 'x')]);
  ejecutar(env, nb.test1, [errorOutput('AssertionError', 'a')]);
  env.ventana.dispatchEvent('beforeunload');
  ejecutar(env, nb.test1, []);
  const cuerpos = env.fetches.map(f => f.body).concat(env.beacons.map(b => b.body));
  for (const b of cuerpos) {
    for (const k of ['student_id', 'course_id', 'cuadernillo_id', 'notebook', 'notebook_path', 'notebook_name']) afirmar(!(k in b), 'no lleva ' + k);
    afirmar(JSON.stringify(b).indexOf('semana_01') < 0, 'no menciona el notebook');
  }
});

caso('10. Cabecera X-XSRFToken vacia si no hay cookie _xsrf (regresion commit 502ca9d)', () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas);
  env.doc.cookie = 'otra=1';
  ejecutar(env, nb.test1, []);
  igual(env.fetches[0].options.headers['X-XSRFToken'], '', 'viaja vacia: el puente respondera 403');
  afirmar(env.consola.some(l => l[0] === 'warn' && /sin cookie _xsrf/.test(l[1])), 'avisa por consola que no hay cookie');
  env.doc.cookie = '_xsrf=2%7Cabc; x=1';
  ejecutar(env, nb.test1, []);
  igual(env.fetches[1].options.headers['X-XSRFToken'], '2|abc', 'se decodifica la cookie');
});

// ---------------------------------------------------------------------------
// Casos que dependen de la respuesta del fetch (asincrona): se esperan las
// microtareas antes de mirar el estado.
// ---------------------------------------------------------------------------
const tick = () => new Promise(r => setImmediate(r));
const casosAsync = [];
function casoAsync(nombre, fn) { casosAsync.push({ nombre, fn }); }

casoAsync('11a. El puente responde 403 -> los errores del intento vuelven al buffer y se avisa por consola', async () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas, { respuesta: { ok: false, status: 403 } });
  ejecutar(env, nb.sol1, [{ output_type: 'error', ename: 'NameError', evalue: 'x', traceback: ['t'] }]);
  ejecutar(env, nb.test1, [{ output_type: 'error', ename: 'AssertionError', evalue: 'mal', traceback: ['t'] }]);
  igual(env.fetches.length, 1);
  igual(env.fetches[0].body.errors.length, 2);
  let st = JSON.parse(env.localStorage.getItem('nbgrader-metrics:semana_01.ipynb'));
  igual(st.errores.ejercicio_1, [], 'el buffer se vacia al enviar');
  await tick();
  st = JSON.parse(env.localStorage.getItem('nbgrader-metrics:semana_01.ipynb'));
  igual(st.errores.ejercicio_1.map(e => e.error_type), ['NameError', 'AssertionError'], 'tras el 403 los errores vuelven al buffer');
  afirmar(env.consola.some(l => l[0] === 'warn' && /HTTP 403/.test(l[1])), 'avisa con el codigo HTTP');
  // y el siguiente intento los lleva de nuevo
  ejecutar(env, nb.test1, []);
  igual(env.fetches[1].body.errors.map(e => e.error_type), ['NameError', 'AssertionError'], 'viajan con el siguiente intento');
});

casoAsync('11b. Error de red -> igual que un rechazo: se reponen los errores', async () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas, { respuesta: { error: 'Failed to fetch' } });
  ejecutar(env, nb.sol1, [{ output_type: 'error', ename: 'TypeError', evalue: 'x', traceback: ['t'] }]);
  ejecutar(env, nb.test1, []);
  await tick();
  const st = JSON.parse(env.localStorage.getItem('nbgrader-metrics:semana_01.ipynb'));
  igual(st.errores.ejercicio_1.map(e => e.error_type), ['TypeError']);
});

casoAsync('11c. El puente acepta (204) -> el buffer queda vacio y no hay avisos', async () => {
  const doc = crearDocumento(); const nb = notebookBasico(doc);
  const env = cargarEntorno(nb.celdas);
  ejecutar(env, nb.sol1, [{ output_type: 'error', ename: 'TypeError', evalue: 'x', traceback: ['t'] }]);
  ejecutar(env, nb.test1, []);
  await tick();
  const st = JSON.parse(env.localStorage.getItem('nbgrader-metrics:semana_01.ipynb'));
  igual(st.errores.ejercicio_1, []);
  afirmar(!env.consola.some(l => l[0] === 'warn'), 'sin avisos');
});

casoAsync('11d. Rating rechazado por el puente -> se puede volver a enviar', async () => {
  const doc = crearDocumento(); const nb = notebookDosEjercicios(doc);
  const env = cargarEntorno(nb.celdas, { respuesta: { ok: false, status: 502 } });
  ejecutar(env, nb.t1, [], 5); ejecutar(env, nb.t2, [], 6);
  const tarjeta = env.doc.getElementById('nbgrader-rating-card');
  afirmar(tarjeta !== null, 'tarjeta ofrecida');
  tarjeta.querySelectorAll('.nbg-star')[2].dispatch('click');
  tarjeta.querySelector('#nbg-rating-send').dispatch('click');
  let st = JSON.parse(env.localStorage.getItem('nbgrader-metrics:semana_01.ipynb'));
  igual(st.rating_enviado, true, 'se marca como enviado al pulsar');
  await tick();
  st = JSON.parse(env.localStorage.getItem('nbgrader-metrics:semana_01.ipynb'));
  igual(st.rating_enviado, false, 'tras el 502 se desmarca para poder reintentar');
});

(async () => {
  for (const c of casosAsync) {
    total++;
    try { await c.fn(); resultados.push('OK    ' + c.nombre); }
    catch (e) { fallos++; resultados.push('FALLO ' + c.nombre + '\n      ' + (e.stack || e).toString().split('\n').slice(0, 3).join('\n      ')); }
  }
  console.log('custom.js: ' + RUTA_CUSTOM);
  console.log(resultados.join('\n'));
  console.log('\n' + (total - fallos) + '/' + total + ' casos OK' + (fallos ? ', ' + fallos + ' FALLO(S)' : ''));
  process.exit(fallos ? 1 : 0);
})();
