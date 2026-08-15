// tutor_ia.js -- panel del Tutor IA dentro del cuadernillo.
//
// Lo carga custom.js con un <script> apuntando a {base_url}tutor-ia/static/tutor_ia.js,
// ruta que sirve la extensión tutor_bridge.py.
//
// Este archivo SOLO pinta la conversación y arma el contexto del ejercicio.
// Nada de reglas de negocio: el tope de 5 preguntas, la identidad del alumno y
// el historial los maneja el servidor (tutor_bridge.py). El contador que se ve
// aquí es el que devuelve el servidor en cada respuesta, no uno local.

(function () {
    'use strict';

    var estadoServidor = null;   // {habilitado, max, usadas, restantes, ...}
    var enviando = false;
    var panelAbierto = false;

    function jup() {
        return (window.Jupyter && window.Jupyter.notebook) ? window.Jupyter : null;
    }

    function baseUrl() {
        var J = jup();
        return (J && J.notebook.base_url) || '/';
    }

    function escapeHtml(str) {
        return String(str == null ? '' : str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Render mínimo: se respetan saltos de línea, **negrita**, `código` y
    // bloques ```...```. No se mete una librería de markdown por 4 marcas.
    function formatear(texto) {
        var bloques = [];
        var conPlaceholders = String(texto || '').replace(/```(?:[a-zA-Z]*\n)?([\s\S]*?)```/g, function (_, code) {
            bloques.push(code);
            return '\u0000BLOQUE' + (bloques.length - 1) + '\u0000';
        });

        var html = escapeHtml(conPlaceholders)
            .replace(/`([^`\n]+)`/g, '<code style="background:rgba(56,189,248,.12);color:#7dd3fc;padding:1px 5px;border-radius:4px;font-family:\'Fira Code\',monospace;font-size:12px;">$1</code>')
            .replace(/\*\*([^*]+)\*\*/g, '<strong style="color:#e2e8f0;">$1</strong>')
            .replace(/\n/g, '<br>');

        return html.replace(/\u0000BLOQUE(\d+)\u0000/g, function (_, i) {
            return '<pre style="background:#020617;border:1px solid rgba(56,189,248,.2);border-radius:6px;padding:10px;margin:8px 0;overflow-x:auto;font-family:\'Fira Code\',monospace;font-size:12px;color:#7dd3fc;white-space:pre-wrap;">'
                + escapeHtml(bloques[Number(i)]) + '</pre>';
        });
    }

    function limpiar_ansi(str) {
        return (str || '').replace(/[\u001b\u009b][\[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '');
    }

    // --- Contexto ------------------------------------------------------------
    // Al tutor se le manda SOLO la pregunta del estudiante.
    //
    // Antes se le enviaba también el enunciado, el código escrito y —esto era lo
    // grave— la celda de prueba entera, con los assert que llevan la respuesta
    // esperada. Un tutor que ve la respuesta puede regalarla, y de hecho se le
    // estaba pidiendo que no lo hiciera solo por el prompt del sistema.
    //
    // Quitarlo tiene un precio y conviene tenerlo presente: el tutor ya no
    // puede decir "en tu línea 3 falta un paréntesis", porque no ve el código.
    // A cambio responde antes (4.000 caracteres menos por pregunta), cuesta
    // menos y no puede filtrar la solución. Si algún día se quiere devolver
    // parte del contexto, que sea el enunciado y el código del alumno, nunca la
    // celda de prueba.


    // --- Transcripción (solo presentación) -----------------------------------
    function clave_chat() {
        var J = jup();
        var path = (J && J.notebook.notebook_path) || 'notebook';
        return 'tutor-ia:' + path;
    }

    function cargar_chat() {
        try {
            var raw = window.localStorage.getItem(clave_chat());
            var arr = raw ? JSON.parse(raw) : [];
            return Array.isArray(arr) ? arr : [];
        } catch (e) { return []; }
    }

    function guardar_chat(mensajes) {
        try {
            window.localStorage.setItem(clave_chat(), JSON.stringify(mensajes.slice(-40)));
        } catch (e) { /* cuota llena: la conversación se pierde al recargar, no es crítico */ }
    }

    var mensajes = [];

    // --- UI -------------------------------------------------------------------
    function el(id) { return document.getElementById(id); }

    function pintar_mensajes() {
        var cont = el('tutor-ia-mensajes');
        if (!cont) return;

        if (!mensajes.length) {
            cont.innerHTML =
                '<div style="color:#94a3b8;font-size:13px;line-height:1.6;padding:8px 2px;">' +
                    '👋 Soy tu tutor de este cuadernillo. No te voy a dar la solución, ' +
                    'pero sí pistas para que la encuentres tú.<br><br>' +
                    'Tienes <strong style="color:#38bdf8;">' + (estadoServidor ? estadoServidor.max : 5) +
                    ' preguntas</strong> para todo el cuadernillo: úsalas cuando de verdad estés atascado.' +
                '</div>';
            return;
        }

        var html = mensajes.map(function (m) {
            if (m.rol === 'estudiante') {
                return '<div style="display:flex;justify-content:flex-end;margin:10px 0;">' +
                        '<div style="max-width:85%;background:#1e40af;color:#e0f2fe;padding:9px 12px;border-radius:12px 12px 2px 12px;font-size:13px;line-height:1.5;white-space:pre-wrap;word-break:break-word;">' +
                            escapeHtml(m.texto) +
                        '</div></div>';
            }
            if (m.rol === 'error') {
                return '<div style="margin:10px 0;padding:9px 12px;border-radius:8px;background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);color:#fca5a5;font-size:12.5px;line-height:1.5;">⚠️ ' +
                        escapeHtml(m.texto) + '</div>';
            }
            return '<div style="display:flex;gap:8px;margin:10px 0;">' +
                    '<div style="flex:0 0 26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#0ea5e9,#6366f1);display:flex;align-items:center;justify-content:center;font-size:14px;">🤖</div>' +
                    '<div style="flex:1;background:rgba(15,23,42,.9);border:1px solid rgba(148,163,184,.18);color:#cbd5e1;padding:10px 12px;border-radius:12px 12px 12px 2px;font-size:13px;line-height:1.6;word-break:break-word;">' +
                        formatear(m.texto) +
                    '</div></div>';
        }).join('');

        if (enviando) {
            html += '<div style="display:flex;gap:8px;margin:10px 0;align-items:center;color:#94a3b8;font-size:12.5px;">' +
                    '<div style="flex:0 0 26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#0ea5e9,#6366f1);display:flex;align-items:center;justify-content:center;font-size:14px;">🤖</div>' +
                    '<em>Pensando…</em></div>';
        }

        cont.innerHTML = html;
        cont.scrollTop = cont.scrollHeight;
    }

    function actualizar_contador() {
        var badge = el('tutor-ia-restantes');
        var pill = el('tutor-ia-badge');
        if (!estadoServidor) return;

        var r = estadoServidor.restantes;
        if (badge) {
            badge.textContent = r + '/' + estadoServidor.max;
            badge.style.background = r > 0 ? 'rgba(56,189,248,.15)' : 'rgba(239,68,68,.15)';
            badge.style.color = r > 0 ? '#7dd3fc' : '#fca5a5';
            badge.style.borderColor = r > 0 ? 'rgba(56,189,248,.3)' : 'rgba(239,68,68,.3)';
        }
        if (pill) {
            pill.textContent = r;
            pill.style.display = r > 0 ? 'flex' : 'none';
        }

        var input = el('tutor-ia-input');
        var btn = el('tutor-ia-enviar');
        var agotado = r <= 0;
        if (input) {
            input.disabled = agotado || enviando;
            input.placeholder = agotado
                ? 'Ya usaste tus ' + estadoServidor.max + ' preguntas de este cuadernillo.'
                : 'Escribe tu duda (Enter para enviar)…';
        }
        if (btn) {
            btn.disabled = agotado || enviando;
            btn.style.opacity = (agotado || enviando) ? '.45' : '1';
            btn.style.cursor = (agotado || enviando) ? 'not-allowed' : 'pointer';
        }
    }

    function alternar_panel(forzar) {
        var panel = el('tutor-ia-panel');
        if (!panel) return;
        panelAbierto = (typeof forzar === 'boolean') ? forzar : !panelAbierto;
        panel.style.display = panelAbierto ? 'flex' : 'none';
        if (panelAbierto) {
            pintar_mensajes();
            actualizar_contador();
            var input = el('tutor-ia-input');
            if (input && !input.disabled) input.focus();
        }
    }

    async function enviar_pregunta() {
        if (enviando) return;
        var input = el('tutor-ia-input');
        var texto = (input.value || '').trim();
        if (!texto) return;

        mensajes.push({ rol: 'estudiante', texto: texto });
        guardar_chat(mensajes);
        input.value = '';
        enviando = true;
        pintar_mensajes();
        actualizar_contador();

        var payload = { mensaje: texto, contexto: '' };

        try {
            var resp = await fetch(baseUrl() + 'tutor-ia/preguntar', {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            var datos = await resp.json().catch(function () { return {}; });

            if (!resp.ok) {
                mensajes.push({ rol: 'error', texto: datos.error || 'No se pudo consultar al tutor.' });
                // El 429 trae el contador real: si se agotó, que la UI se cierre sola.
                if (typeof datos.restantes === 'number' && estadoServidor) {
                    estadoServidor.restantes = datos.restantes;
                    estadoServidor.usadas = datos.usadas;
                }
            } else {
                mensajes.push({ rol: 'tutor', texto: datos.respuesta });
                if (estadoServidor) {
                    estadoServidor.restantes = datos.restantes;
                    estadoServidor.usadas = datos.usadas;
                }
            }
        } catch (err) {
            mensajes.push({ rol: 'error', texto: 'Falló la conexión con el tutor. Revisa tu red e intenta de nuevo.' });
        } finally {
            enviando = false;
            guardar_chat(mensajes);
            pintar_mensajes();
            actualizar_contador();
        }
    }

    function construir_ui() {
        if (el('tutor-ia-panel')) return;

        var lanzador = document.createElement('button');
        lanzador.id = 'tutor-ia-lanzador';
        lanzador.title = 'Tutor IA del cuadernillo';
        lanzador.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:1000;width:56px;height:56px;border-radius:50%;border:none;cursor:pointer;background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;font-size:24px;box-shadow:0 6px 20px rgba(14,165,233,.4);display:flex;align-items:center;justify-content:center;transition:transform .15s;';
        lanzador.innerHTML = '🤖<span id="tutor-ia-badge" style="position:absolute;top:-2px;right:-2px;min-width:20px;height:20px;border-radius:10px;background:#f43f5e;color:#fff;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;padding:0 5px;border:2px solid #0f172a;"></span>';
        lanzador.addEventListener('mouseenter', function () { lanzador.style.transform = 'scale(1.06)'; });
        lanzador.addEventListener('mouseleave', function () { lanzador.style.transform = 'scale(1)'; });
        lanzador.addEventListener('click', function () { alternar_panel(); });

        var panel = document.createElement('div');
        panel.id = 'tutor-ia-panel';
        panel.style.cssText = 'display:none;position:fixed;bottom:92px;right:24px;z-index:1000;width:400px;max-width:calc(100vw - 48px);height:540px;max-height:calc(100vh - 140px);flex-direction:column;background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);border:1px solid rgba(56,189,248,.25);border-radius:14px;box-shadow:0 20px 50px rgba(0,0,0,.45);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;overflow:hidden;';

        panel.innerHTML = [
            '<div style="padding:14px 16px;border-bottom:1px solid rgba(148,163,184,.15);display:flex;align-items:center;gap:10px;">',
                '<div style="flex:1;">',
                    '<div style="font-size:15px;font-weight:700;color:#e2e8f0;">Tutor IA</div>',
                    '<div style="font-size:11.5px;color:#94a3b8;">Te guía, no te da la respuesta</div>',
                '</div>',
                '<span id="tutor-ia-restantes" title="Preguntas que te quedan en este cuadernillo" style="font-size:12px;font-weight:700;padding:4px 10px;border-radius:20px;background:rgba(56,189,248,.15);color:#7dd3fc;border:1px solid rgba(56,189,248,.3);">–</span>',
                '<button id="tutor-ia-cerrar" title="Cerrar" style="background:none;border:none;color:#94a3b8;font-size:20px;cursor:pointer;line-height:1;padding:0 2px;">×</button>',
            '</div>',
            '<div id="tutor-ia-mensajes" style="flex:1;overflow-y:auto;padding:12px 14px;"></div>',
            '<div style="padding:10px 12px;border-top:1px solid rgba(148,163,184,.15);display:flex;gap:8px;align-items:flex-end;">',
                '<textarea id="tutor-ia-input" rows="2" placeholder="Escribe tu duda (Enter para enviar)…" style="flex:1;box-sizing:border-box;background:#020617;color:#e2e8f0;border:1px solid rgba(148,163,184,.3);border-radius:8px;padding:8px 10px;font-size:13px;resize:none;font-family:inherit;"></textarea>',
                '<button id="tutor-ia-enviar" style="background:#38bdf8;color:#04263a;border:none;border-radius:8px;padding:9px 14px;font-weight:700;font-size:13px;cursor:pointer;">Enviar</button>',
            '</div>'
        ].join('');

        document.body.appendChild(lanzador);
        document.body.appendChild(panel);

        el('tutor-ia-cerrar').addEventListener('click', function () { alternar_panel(false); });
        el('tutor-ia-enviar').addEventListener('click', enviar_pregunta);
        el('tutor-ia-input').addEventListener('keydown', function (ev) {
            // Enter envía, Shift+Enter hace salto de línea. Y stopPropagation
            // porque si no, el notebook se come las teclas como atajos suyos.
            ev.stopPropagation();
            if (ev.key === 'Enter' && !ev.shiftKey) {
                ev.preventDefault();
                enviar_pregunta();
            }
        });
        el('tutor-ia-input').addEventListener('keypress', function (ev) { ev.stopPropagation(); });
        el('tutor-ia-input').addEventListener('keyup', function (ev) { ev.stopPropagation(); });

        mensajes = cargar_chat();
        pintar_mensajes();
        actualizar_contador();
    }

    // --- Arranque -------------------------------------------------------------
    // "Habilitable en el cuadernillo": el instructor lo apaga por notebook con
    //   notebook.metadata.tutor_ia = {"enabled": false}
    // y operaciones lo apaga para todo el curso con TUTOR_IA_HABILITADO=false.
    function habilitado_en_cuadernillo() {
        var J = jup();
        var meta = (J && J.notebook.metadata && J.notebook.metadata.tutor_ia) || null;
        return !(meta && meta.enabled === false);
    }

    async function iniciar() {
        if (!habilitado_en_cuadernillo()) {
            console.log('[tutor-ia] desactivado por metadata del cuadernillo');
            return;
        }

        try {
            var resp = await fetch(baseUrl() + 'tutor-ia/estado', { credentials: 'same-origin' });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            estadoServidor = await resp.json();
        } catch (err) {
            console.warn('[tutor-ia] no se pudo leer el estado del tutor', err);
            return;
        }

        if (!estadoServidor.habilitado) {
            console.log('[tutor-ia] desactivado por configuración del curso');
            return;
        }

        construir_ui();
        console.log('[tutor-ia] listo: ' + estadoServidor.restantes + '/' + estadoServidor.max + ' preguntas disponibles');
    }

    function esperar_notebook() {
        var J = jup();
        if (J && J.notebook._fully_loaded) { iniciar(); return; }
        if (J && J.notebook.events) {
            J.notebook.events.on('notebook_loaded.Notebook', function () { iniciar(); });
            // Si el evento ya pasó antes de que cargara este script, el
            // listener no dispara nunca: se reintenta una vez por si acaso.
            setTimeout(function () { if (!el('tutor-ia-panel')) iniciar(); }, 3000);
            return;
        }
        setTimeout(esperar_notebook, 500);
    }

    esperar_notebook();
})();
