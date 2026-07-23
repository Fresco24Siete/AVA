// custom.js -- se carga automáticamente en el notebook clásico/nbclassic
// desde <jupyter_config_dir>/custom/custom.js

require(['base/js/namespace', 'base/js/utils'], function (Jupyter, utils) {

    function es_celda_de_ejercicio(cell) {
        return !!(cell && cell.metadata && cell.metadata.nbgrader &&
                  cell.metadata.nbgrader.grade_id);
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
        fetch('nbgrader-metrics/evento', {
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
                        '📡 Ver JSON que se enviaría al Backend (Click para desplegar)',
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

    var primer_intento_time = {};
    var intentos_count = {};

    function on_execute(evt, data) {
        var cell = data.cell;
        if (!es_celda_de_ejercicio(cell)) return;
        var grade_id = cell.metadata.nbgrader.grade_id;

        if (!primer_intento_time[grade_id]) {
            primer_intento_time[grade_id] = Date.now();
        }
        intentos_count[grade_id] = (intentos_count[grade_id] || 0) + 1;
    }

    function on_finished_execute(evt, data) {
        var cell = data.cell;
        if (!es_celda_de_ejercicio(cell)) return;
        var grade_id = cell.metadata.nbgrader.grade_id;

        var outputs = (cell.output_area && cell.output_area.outputs) || [];
        var errores = outputs.filter(function (o) { return o.output_type === 'error'; });
        var exito = errores.length === 0;

        var ahora = Date.now();
        var inicio = primer_intento_time[grade_id] || ahora;
        var duracion_seg = Math.max(0, (ahora - inicio) / 1000.0);
        duracion_seg = Math.round(duracion_seg * 100) / 100;

        var nbgrader_meta = cell.metadata.nbgrader;
        
        var tipo_error = null;
        var mensaje_error = null;
        var traceback_limpio = null;

        if (!exito && errores.length > 0) {
            var err = errores[0];
            tipo_error = err.ename || 'ExecutionError';
            mensaje_error = err.evalue ? (tipo_error + ': ' + err.evalue) : tipo_error;
            if (err.traceback && err.traceback.length) {
                traceback_limpio = err.traceback.map(limpiar_ansi).join('\n');
            }
        }

        var num_intentos = intentos_count[grade_id] || 1;

        var payload = {
            codigo_celda: grade_id,
            orden: obtener_orden_celda(cell),
            puntos_maximos: nbgrader_meta.points || 1,
            descripcion: grade_id,
            timestamp: new Date(ahora).toISOString(),
            primer_intento: new Date(inicio).toISOString(),
            num_intentos: num_intentos,
            duracion_segundos: duracion_seg,
            exito: exito,
            tipo_error: tipo_error,
            mensaje: mensaje_error,
            traceback: traceback_limpio
        };

        // Renderizar tarjeta visual con visor JSON desplegable incorporado
        mostrar_feedback_ui(cell, exito, grade_id, num_intentos, tipo_error, mensaje_error, duracion_seg, payload);

        // Enviar evento de telemetría en tiempo real al puente local
        enviar_evento(payload);
    }

    if (Jupyter && Jupyter.notebook && Jupyter.notebook.events) {
        Jupyter.notebook.events.on('execute.CodeCell', on_execute);
        Jupyter.notebook.events.on('finished_execute.CodeCell', on_finished_execute);
        console.log('[nbgrader-metrics] listo, escuchando celdas de ejercicio con visor JSON interactivo');
    }
});