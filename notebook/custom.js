// custom.js -- se carga automáticamente en el notebook clásico/nbclassic
// desde <jupyter_config_dir>/custom/custom.js

require(['base/js/namespace', 'base/js/utils'], function (Jupyter, utils) {

    function meta_nbgrader(cell) {
        return (cell && cell.metadata && cell.metadata.nbgrader) ? cell.metadata.nbgrader : null;
    }

    // Celda de PRUEBA (grade: true). Es la que dispara el evento de resultado
    // y la que nbgrader califica. grade_id = "test_ejercicio_1".
    function es_celda_de_prueba(cell) {
        var m = meta_nbgrader(cell);
        return !!(m && m.grade === true && m.grade_id);
    }

    // Celda de SOLUCIÓN (solution: true, grade: false): donde el estudiante
    // escribe SU código. No dispara evento propio, pero SÍ nos interesa su
    // error: es el error real del alumno. grade_id = "ejercicio_1".
    function es_celda_de_solucion(cell) {
        var m = meta_nbgrader(cell);
        return !!(m && m.solution === true && m.grade !== true && m.grade_id);
    }

    // Mantiene compatibilidad con el nombre viejo (celda de prueba).
    function es_celda_de_ejercicio(cell) {
        return es_celda_de_prueba(cell);
    }

    // Cada ejercicio son dos celdas: "ejercicio_1" (solución) y
    // "test_ejercicio_1" (prueba). Solo la de prueba dispara telemetría, así que
    // normalizamos para que el backend tenga una clave de negocio estable e
    // idéntica a la que manda la exportación de nbgrader (api_export.py).
    function normalizar_codigo_ejercicio(grade_id) {
        return grade_id.indexOf('test_') === 0 ? grade_id.slice(5) : grade_id;
    }

    function obtener_orden_celda(cell) {
        if (!Jupyter || !Jupyter.notebook) return 0;
        var cells = Jupyter.notebook.get_cells();
        var index = cells.indexOf(cell);
        return index >= 0 ? index + 1 : 0;
    }

    function limpiar_ansi(str) {
        return (str || '').replace(/[\u001b\u009b][\[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '');
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function enviar_evento(payload) {
        var xsrf = utils.get_cookie ? utils.get_cookie('_xsrf') : '';
        // CORREGIDO: la URL relativa se resolvía contra la URL actual del navegador
        // (p.ej. /user/xxx/notebooks/work/...), no contra la base real del servidor,
        // así que la petición nunca llegaba a la ruta que registra metrics_bridge.py.
        var base_url = (Jupyter && Jupyter.notebook && Jupyter.notebook.base_url) || '/';
        fetch(base_url + 'nbgrader-metrics/evento', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-XSRFToken': xsrf,
            },
            body: JSON.stringify(payload),
        }).catch(function (err) {
            console.warn('[nbgrader-metrics] no se pudo enviar el evento', err);
        });
    }

    function mostrar_feedback_ui(cell, exito, grade_id, num_intentos, tipo_error, mensaje, duracion_seg, payload) {
        if (!cell || !cell.element) return;
        
        // Quitar feedback previo si existía en la celda
        if (typeof cell.element.find === 'function') {
            cell.element.find('.nbgrader-metrics-feedback').remove();
        }

        var jsonFormatted = escapeHtml(JSON.stringify(payload, null, 2));

        var feedbackContainer = document.createElement('div');
        feedbackContainer.className = 'nbgrader-metrics-feedback';
        feedbackContainer.style.cssText = 'margin-top: 12px; margin-bottom: 12px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; transition: all 0.3s ease;';

        var statusHeader = '';
        if (!exito) {
            statusHeader = [
                '<div style="background: linear-gradient(135deg, #1e1e2d 0%, #2d1f2d 100%); border-left: 5px solid #ef4444; border-radius: 8px 8px 0 0; padding: 16px; color: #f8fafc; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);">',
                    '<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">',
                        '<div style="display: flex; align-items: center; gap: 8px;">',
                            '<span style="font-size: 20px;">⚠️</span>',
                            '<strong style="font-size: 15px; color: #fca5a5;">Atención: Error detectado en ' + escapeHtml(grade_id) + '</strong>',
                        '</div>',
                        '<span style="background: rgba(239, 68, 68, 0.2); color: #f87171; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 20px; border: 1px solid rgba(239, 68, 68, 0.3);">',
                            'Intento #' + num_intentos,
                        '</span>',
                    '</div>',
                    '<div style="background: rgba(0, 0, 0, 0.4); border-radius: 6px; padding: 12px; font-family: \'Fira Code\', \'Courier New\', monospace; font-size: 13px; color: #fecaca; word-break: break-word; border: 1px solid rgba(255, 255, 255, 0.05);">',
                        '<div style="color: #ef4444; font-weight: bold; margin-bottom: 4px;">📌 [' + escapeHtml(tipo_error || 'Error') + ']</div>',
                        '<div>' + escapeHtml(mensaje || 'Ocurrió un fallo durante la ejecución de las pruebas.') + '</div>',
                    '</div>',
                    '<div style="margin-top: 10px; font-size: 12px; color: #94a3b8; display: flex; align-items: center; gap: 6px;">',
                        '<span>💡</span> <em>Revisa los datos de prueba y ajusta tu lógica antes de volver a ejecutar.</em>',
                    '</div>',
                '</div>'
            ].join('');
        } else {
            statusHeader = [
                '<div style="background: linear-gradient(135deg, #182825 0%, #1e3a29 100%); border-left: 5px solid #10b981; border-radius: 8px 8px 0 0; padding: 14px 16px; color: #f8fafc; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);">',
                    '<div style="display: flex; align-items: center; justify-content: space-between;">',
                        '<div style="display: flex; align-items: center; gap: 8px;">',
                            '<span style="font-size: 20px;">✅</span>',
                            '<strong style="font-size: 15px; color: #6ee7b7;">¡Excelente! Ejercicio ' + escapeHtml(grade_id) + ' verificado con éxito</strong>',
                        '</div>',
                        '<div style="font-size: 12px; color: #a7f3d0; background: rgba(16, 185, 129, 0.2); padding: 4px 10px; border-radius: 20px; border: 1px solid rgba(16, 185, 129, 0.3);">',
                            num_intentos + (num_intentos === 1 ? ' intento' : ' intentos') + ' • ' + duracion_seg + 's',
                        '</div>',
                    '</div>',
                '</div>'
            ].join('');
        }

        var jsonViewer = [
            '<div style="background: #0f172a; border-radius: 0 0 8px 8px; border: 1px solid rgba(255,255,255,0.08); border-top: none; padding: 10px 14px;">',
                '<details style="color: #94a3b8;">',
                    '<summary style="cursor: pointer; font-size: 12px; font-weight: 600; color: #38bdf8; user-select: none;">',
                        'Ver JSON que se enviaría al Backend (Click para desplegar)',
                    '</summary>',
                    '<pre style="margin-top: 8px; margin-bottom: 0; background: #020617; padding: 12px; border-radius: 6px; font-family: \'Fira Code\', monospace; font-size: 12px; color: #38bdf8; overflow-x: auto; border: 1px solid rgba(56, 189, 248, 0.2);">' + jsonFormatted + '</pre>',
                '</details>',
            '</div>'
        ].join('');

        feedbackContainer.innerHTML = statusHeader + jsonViewer;

        if (cell.element[0]) {
            cell.element[0].appendChild(feedbackContainer);
        } else if (typeof cell.element.append === 'function') {
            cell.element.append(feedbackContainer);
        }
    }

    // --- Estado persistente ------------------------------------------------
    // Antes vivía solo en memoria: al refrescar la pestaña (F5) los contadores
    // volvían a cero y un alumno con 4 intentos fallidos reportaba "1 intento".
    // Se guarda por notebook, así que cada cuadernillo lleva su propia cuenta.
    function clave_estado() {
        var path = (Jupyter && Jupyter.notebook && Jupyter.notebook.notebook_path) || 'notebook';
        return 'nbgrader-metrics:' + path;
    }

    function cargar_estado() {
        try {
            var raw = window.localStorage.getItem(clave_estado());
            var st = raw ? JSON.parse(raw) : {};
            st.intentos = st.intentos || {};       // nº de verificaciones (SOLO para la UI; el backend cuenta)
            st.primer_intento = st.primer_intento || {}; // ts del 1er toque (SOLO UI)
            // errores: buffer POR EJERCICIO. Acumula TODOS los errores de ejecución
            // (celda de solución o de prueba) desde el último intento de validación.
            // Persistido para no perderlo si el alumno recarga o cierra sin validar.
            st.errores = st.errores || {};
            return st;
        } catch (e) {
            return { intentos: {}, primer_intento: {}, errores: {} };
        }
    }

    function guardar_estado(st) {
        try {
            window.localStorage.setItem(clave_estado(), JSON.stringify(st));
        } catch (e) {
            console.warn('[nbgrader-metrics] no se pudo persistir el estado', e);
        }
    }

    var estado = cargar_estado();

    // Fuente única de verdad sobre si una celda de prueba está aprobada.
    // Antes había dos criterios distintos: on_finished_execute miraba solo si
    // había errores, y la verificación de finalización exigía además
    // outputs.length > 0. Eso hacía que una celda con solo asserts (que al pasar
    // no imprime NADA) se reportara como exitosa pero nunca contara como
    // aprobada, y el evento de cuadernillo completado jamás se disparaba.
    function evaluar_celda(cell) {
        var outputs = (cell.output_area && cell.output_area.outputs) || [];
        var errores = outputs.filter(function (o) { return o.output_type === 'error'; });
        var n = cell.input_prompt_number;
        var ejecutada = (n !== undefined && n !== null && n !== '*');
        return {
            ejecutada: ejecutada,
            errores: errores,
            exito: ejecutada && errores.length === 0
        };
    }

    // Extrae el error de una celda (o null si no hubo).
    function extraer_error(cell) {
        var outputs = (cell.output_area && cell.output_area.outputs) || [];
        var errores = outputs.filter(function (o) { return o.output_type === 'error'; });
        if (!errores.length) return null;
        var err = errores[0];
        var tipo = err.ename || 'ExecutionError';
        return {
            tipo_error: tipo,
            mensaje: err.evalue ? (tipo + ': ' + err.evalue) : tipo,
            traceback: (err.traceback && err.traceback.length)
                ? err.traceback.map(limpiar_ansi).join('\n') : null
        };
    }

    // Acumula el error de una celda (solución o prueba) en el buffer del ejercicio.
    // Un objeto por error con el shape de la sección 5.1 (cell_id, timestamp,
    // error_type, error_message). Así NINGÚN error se pierde: se capturan a
    // medida que ocurren, no solo cuando se corre el test.
    function bufferizar_error(cod, cell) {
        var err = extraer_error(cell);
        if (!err) return;
        if (!estado.errores[cod]) estado.errores[cod] = [];
        estado.errores[cod].push({
            cell_id: cell.metadata.nbgrader.grade_id,
            timestamp: new Date().toISOString(),
            error_type: err.tipo_error,
            error_message: err.mensaje,
            traceback: err.traceback
        });
        guardar_estado(estado);
    }

    function verificar_finalizacion_cuadernillo() {
        if (!Jupyter || !Jupyter.notebook) return;
        var cells = Jupyter.notebook.get_cells();
        var evalCells = cells.filter(function (c) {
            return c && c.metadata && c.metadata.nbgrader && c.metadata.nbgrader.grade && c.metadata.nbgrader.grade_id;
        });

        if (evalCells.length === 0) return;

        var puntajeObtenido = 0;
        var puntajeMaximo = 0;
        var todosAprobados = true;

        for (var i = 0; i < evalCells.length; i++) {
            var cell = evalCells[i];
            var pMax = cell.metadata.nbgrader.points || 1;
            puntajeMaximo += pMax;

            if (evaluar_celda(cell).exito) {
                puntajeObtenido += pMax;
            } else {
                todosAprobados = false;
            }
        }

        if (!todosAprobados) return;

        // Cuadernillo completo. En vez de auto-enviar una nota, se le pide al
        // alumno que CALIFIQUE el cuadernillo (retroalimentación 1-5 + comentario,
        // sección 4/5.2). El evento de rating se envía una sola vez por alumno /
        // cuadernillo (flag rating_enviado). Si ya lo calificó o ya se mostró el
        // formulario, no hacemos nada.
        if (estado.rating_enviado) return;
        mostrar_rating_ui();
    }

    // --- UI de calificación del cuadernillo (sección 5.2) ---------------------
    function enviar_rating(rating, comment) {
        if (estado.rating_enviado) return;
        estado.rating_enviado = true;
        guardar_estado(estado);
        enviar_evento({
            tipo_evento: "cuadernillo_rating",
            submitted_at: new Date().toISOString(),
            rating: rating,
            comment: comment || null
        });
        console.log('[nbgrader-metrics] rating del cuadernillo enviado:', rating);
    }

    function mostrar_rating_ui() {
        if (!Jupyter || !Jupyter.notebook) return;
        if (document.getElementById('nbgrader-rating-card')) return; // ya visible

        var cont = document.createElement('div');
        cont.id = 'nbgrader-rating-card';
        cont.style.cssText = 'margin:16px 0;padding:18px;border-radius:10px;background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);border:1px solid rgba(56,189,248,0.25);color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;box-shadow:0 6px 18px rgba(0,0,0,0.25);';

        var estrellas = '';
        for (var s = 1; s <= 5; s++) {
            estrellas += '<span class="nbg-star" data-v="' + s + '" style="cursor:pointer;font-size:30px;color:#475569;transition:color .15s;">★</span>';
        }

        cont.innerHTML =
            '<div style="font-size:16px;font-weight:700;color:#6ee7b7;margin-bottom:4px;">✅ ¡Completaste el cuadernillo!</div>' +
            '<div style="font-size:13px;color:#94a3b8;margin-bottom:12px;">Antes de terminar, calíficalo para ayudarnos a mejorarlo.</div>' +
            '<div id="nbg-stars" style="display:flex;gap:6px;margin-bottom:12px;">' + estrellas + '</div>' +
            '<textarea id="nbg-comment" rows="2" placeholder="Comentario (opcional)" style="width:100%;box-sizing:border-box;background:#020617;color:#e2e8f0;border:1px solid rgba(148,163,184,0.3);border-radius:6px;padding:8px;font-size:13px;resize:vertical;"></textarea>' +
            '<div style="margin-top:10px;display:flex;align-items:center;gap:10px;">' +
                '<button id="nbg-rating-send" disabled style="background:#38bdf8;color:#04263a;border:none;border-radius:6px;padding:8px 16px;font-weight:700;font-size:13px;cursor:not-allowed;opacity:.5;">Enviar calificación</button>' +
                '<span id="nbg-rating-msg" style="font-size:12px;color:#94a3b8;"></span>' +
            '</div>';

        // Insertar al final de la última celda evaluable
        var cells = Jupyter.notebook.get_cells();
        var last = null;
        for (var i = 0; i < cells.length; i++) {
            if (es_celda_de_prueba(cells[i])) last = cells[i];
        }
        var host = last && last.element && last.element[0] ? last.element[0] : document.body;
        host.appendChild(cont);

        var seleccion = 0;
        var stars = cont.querySelectorAll('.nbg-star');
        var btn = cont.querySelector('#nbg-rating-send');
        function pintar(n) {
            for (var k = 0; k < stars.length; k++) {
                stars[k].style.color = (k < n) ? '#fbbf24' : '#475569';
            }
        }
        for (var j = 0; j < stars.length; j++) {
            (function (star) {
                star.addEventListener('mouseenter', function () { pintar(parseInt(star.dataset.v, 10)); });
                star.addEventListener('mouseleave', function () { pintar(seleccion); });
                star.addEventListener('click', function () {
                    seleccion = parseInt(star.dataset.v, 10);
                    pintar(seleccion);
                    btn.disabled = false;
                    btn.style.cursor = 'pointer';
                    btn.style.opacity = '1';
                });
            })(stars[j]);
        }
        btn.addEventListener('click', function () {
            if (seleccion < 1) return;
            var comment = cont.querySelector('#nbg-comment').value.trim();
            enviar_rating(seleccion, comment);
            btn.disabled = true;
            btn.style.cursor = 'default';
            btn.style.opacity = '.5';
            cont.querySelector('#nbg-rating-msg').textContent = '¡Gracias por tu calificación!';
        });
    }

    function on_execute(evt, data) {
        var cell = data.cell;
        var es_prueba = es_celda_de_prueba(cell);
        var es_solucion = es_celda_de_solucion(cell);
        if (!es_prueba && !es_solucion) return;

        // Se cronometra por EJERCICIO (clave de negocio), no por grade_id, para
        // que la celda de solución y la de prueba compartan el mismo reloj.
        // El primer_intento se fija en el primer toque de CUALQUIERA de las dos:
        // así el tiempo cuenta desde que el alumno empezó a trabajar el ejercicio,
        // no desde que corrió el test por primera vez (ese era el bug del tiempo).
        var cod = normalizar_codigo_ejercicio(cell.metadata.nbgrader.grade_id);

        if (!estado.primer_intento[cod]) {
            estado.primer_intento[cod] = Date.now();
        }
        // Solo las corridas de la celda de PRUEBA cuentan como "intentos" de
        // verificación. Ejecutar la solución no es un intento.
        if (es_prueba) {
            estado.intentos[cod] = (estado.intentos[cod] || 0) + 1;
        }
        guardar_estado(estado);
    }

    function on_finished_execute(evt, data) {
        var cell = data.cell;
        var es_solucion = es_celda_de_solucion(cell);
        var es_prueba = es_celda_de_prueba(cell);
        if (!es_solucion && !es_prueba) return;

        var cod = normalizar_codigo_ejercicio(cell.metadata.nbgrader.grade_id);

        // Todo error (celda de solución O de prueba) se ACUMULA en el buffer del
        // ejercicio a medida que ocurre. Así no se pierde ningún error aunque el
        // alumno nunca llegue a correr el test (bug que reportó Bryan).
        bufferizar_error(cod, cell);

        // La celda de solución solo acumula; el ENVÍO se dispara con el test.
        if (!es_prueba) return;

        // --- Celda de PRUEBA (validación): se arma y envía el intento --------
        var grade_id = cell.metadata.nbgrader.grade_id;
        var nbgrader_meta = cell.metadata.nbgrader;
        var exito = evaluar_celda(cell).exito;

        var ahora = Date.now();
        var inicio = estado.primer_intento[cod] || ahora;
        var duracion_seg = Math.round(Math.max(0, (ahora - inicio) / 1000.0) * 100) / 100;
        var num_intentos = estado.intentos[cod] || 1;  // SOLO para la tarjeta visual

        // Todos los errores acumulados desde el intento anterior (incluye el de
        // la propia celda de prueba, ya bufferizado arriba).
        var errores_acumulados = (estado.errores[cod] || []).slice();

        // Payload del intento (sección 5.1). La identidad (course_id, student_id,
        // cuadernillo_id) la agrega metrics_bridge desde el contexto LTI, NO el
        // cliente. attempts_count tampoco: lo cuenta el backend contando eventos.
        var payload = {
            tipo_evento: "exercise_attempt",
            exercise_id: cod,
            codigo_celda: grade_id,
            orden: obtener_orden_celda(cell),
            puntos_maximos: nbgrader_meta.points || 1,
            attempt_at: new Date(ahora).toISOString(),
            validation_result: exito ? "passed" : "failed",
            errors: errores_acumulados
        };

        // El buffer se reinicia tras CADA envío, pase o falle (sección 2.4).
        estado.errores[cod] = [];
        if (exito) {
            delete estado.primer_intento[cod];
            delete estado.intentos[cod];
        }
        guardar_estado(estado);

        // Tarjeta visual: el error más reciente del intento (si hubo).
        var ultimo = errores_acumulados.length ? errores_acumulados[errores_acumulados.length - 1] : null;
        mostrar_feedback_ui(cell, exito, grade_id, num_intentos,
            ultimo ? ultimo.error_type : null,
            ultimo ? ultimo.error_message : null,
            duracion_seg, payload);

        enviar_evento(payload);
        verificar_finalizacion_cuadernillo();
    }

    // Al cerrar/recargar la pestaña, si quedaron errores en buffer de ejercicios
    // que el alumno NUNCA validó (no corrió el test), se envían igual para no
    // perderlos. sendBeacon es lo único confiable durante 'unload'. El endpoint
    // está eximido de XSRF, así que un POST sin headers especiales funciona.
    function flush_errores_pendientes() {
        if (!navigator.sendBeacon) return;
        var base_url = (Jupyter && Jupyter.notebook && Jupyter.notebook.base_url) || '/';
        var url = base_url + 'nbgrader-metrics/evento';
        Object.keys(estado.errores || {}).forEach(function (cod) {
            var errs = estado.errores[cod];
            if (!errs || !errs.length) return;
            var payload = {
                tipo_evento: "exercise_attempt",
                exercise_id: cod,
                attempt_at: new Date().toISOString(),
                validation_result: "sin_validar", // cerró sin correr el test
                errors: errs.slice()
            };
            try {
                navigator.sendBeacon(url, new Blob([JSON.stringify(payload)], { type: 'application/json' }));
                estado.errores[cod] = [];
            } catch (e) { /* best-effort */ }
        });
        guardar_estado(estado);
    }
    window.addEventListener('beforeunload', flush_errores_pendientes);

    if (Jupyter && Jupyter.notebook && Jupyter.notebook.events) {
        Jupyter.notebook.events.on('execute.CodeCell', on_execute);
        Jupyter.notebook.events.on('finished_execute.CodeCell', on_finished_execute);
        console.log('[nbgrader-metrics] listo: telemetría por intento (errors[] acumulados + rating de cuadernillo)');
    }
});