// Ayuda para el docente dentro de formgrader.
//
// nbgrader presenta cuatro botones con nombres que no dicen nada a quien no
// conoce la herramienta —Generate, Release, Collect, Autograde— y en el orden
// equivocado se pierde trabajo: hacer "Generate" después de recoger envíos
// regenera la versión del alumno. Este archivo explica cada uno donde el docente
// lo va a leer, que es la propia pantalla.
//
// Se inyecta con JavaScript porque nbgrader no ofrece ningún punto de extensión
// para esto. Eso lo vuelve frágil: depende del HTML interno de formgrader, que
// puede cambiar entre versiones. Por eso todo va dentro de comprobaciones y, si
// algo no aparece donde se espera, no se hace nada en vez de romper la página.
// Se probó contra nbgrader 0.8.5.
(function () {
    'use strict';

    var COLOR_BORDE = '#2a78d6';
    var COLOR_AVISO = '#b57200';

    // Qué hace cada paso, en el orden en que hay que hacerlos.
    var PASOS = [
        {
            boton: 'Generate',
            titulo: '1. Generar',
            texto: 'Toma tu versión con las soluciones puestas y crea la del ' +
                   'alumno: borra las soluciones, deja el enunciado y el ' +
                   'andamiaje, y quita las pruebas ocultas. Hazlo cada vez que ' +
                   'edites el cuadernillo.',
            aviso: 'No lo hagas después de recoger envíos: regenera la versión ' +
                   'del alumno y se pierde la correspondencia con lo entregado.'
        },
        {
            boton: 'Preview',
            titulo: 'Previsualizar',
            texto: 'Abre la versión generada, exactamente como la va a ver el ' +
                   'alumno. Úsalo para comprobar que no quedó ninguna solución ' +
                   'a la vista. Solo aparece después de Generar: antes no hay ' +
                   'nada que previsualizar.'
        },
        {
            boton: 'Release',
            titulo: '2. Liberar',
            texto: 'Sube el cuadernillo al servicio de intercambio, y desde ese ' +
                   'momento lo recibe cualquier alumno que entre o abra su ' +
                   'panel, sin que nadie tenga que reconstruir nada. Es lo mismo ' +
                   'que hace el comando <b>publicar-cuadernillo</b>, que además ' +
                   'permite fijar desde cuándo y hasta cuándo está abierto, y ' +
                   'corregir una errata sin quitarle el turno a la semana en ' +
                   'curso (--sin-activar). El último liberado pasa a ser «el de ' +
                   'esta semana».',
            aviso: 'Al volver a pulsarlo dice «unrelease» y lo retira del ' +
                   'servicio: deja de aparecerle a los alumnos, pero quien ya lo ' +
                   'tenga sigue trabajando en él y puede entregarlo.'
        },
        {
            boton: 'Collect',
            titulo: '3. Recoger',
            texto: 'Trae a la carpeta de entregas lo que los alumnos mandaron ' +
                   'con «Entregar» desde su cuadernillo. <b>Hasta que no lo ' +
                   'pulses, Calificar no ve nada.</b> Se puede pulsar las veces ' +
                   'que haga falta: solo trae lo nuevo, y si un alumno volvió a ' +
                   'entregar se queda con su versión más reciente. El panel del ' +
                   'curso dice cuántas entregas hay sin recoger.'
        },
        {
            boton: 'Autograde',
            titulo: '4. Calificar',
            texto: 'Ejecuta las pruebas de cada entrega y pone la nota ' +
                   'automática. Después puedes revisar a mano lo que quieras y ' +
                   'ajustar la calificación.'
        }
    ];

    var RESUMEN =
        '<b>nbgrader no trae forma de borrar una actividad</b>: lo más parecido ' +
        'es retirarla del servicio con Release, que no elimina nada. Para eso ' +
        'está el bloque de abajo, añadido por este AVA. ' +
        'El recorrido completo es: <b>editas el cuadernillo → Generar → ' +
        'Previsualizar → Liberar (o publicar-cuadernillo) → (los alumnos ' +
        'trabajan y entregan) → Recoger → Calificar → registrar-notas</b>. ' +
        'La nota sale solo de las celdas de prueba; los puntos de experiencia y ' +
        'las insignias que ve el alumno no cuentan para nada.';

    // Jupyter deja el token XSRF en una cookie; hay que devolvérselo en la
    // cabecera para que acepte un POST.
    function cookie_xsrf() {
        var m = document.cookie.match(/\b_xsrf=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    function crearPanel() {
        var caja = document.createElement('div');
        caja.id = 'ava-ayuda-docente';
        caja.style.cssText =
            'border:1px solid #dfe3e8;border-left:4px solid ' + COLOR_BORDE + ';' +
            'border-radius:6px;padding:14px 16px;margin:16px 0;background:#f6f7f9;' +
            'font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;' +
            'font-size:14.5px;line-height:1.55;color:#1c1c1c;';

        var filas = PASOS.map(function (p) {
            var aviso = p.aviso
                ? '<div style="color:' + COLOR_AVISO + ';margin-top:3px">' +
                  'Cuidado: ' + p.aviso + '</div>'
                : '';
            return '<tr>' +
                '<td style="padding:6px 12px 6px 0;white-space:nowrap;vertical-align:top">' +
                '<code style="background:#fff;border:1px solid #dfe3e8;border-radius:4px;' +
                'padding:1px 6px">' + p.boton + '</code></td>' +
                '<td style="padding:6px 0;vertical-align:top">' +
                '<b>' + p.titulo + '.</b> ' + p.texto + aviso + '</td></tr>';
        }).join('');

        var raiz = (window.location.pathname.split('/formgrader')[0]) || '';
        caja.innerHTML =
            '<div style="display:flex;align-items:center;justify-content:space-between;' +
            'gap:12px;flex-wrap:wrap;margin-bottom:12px">' +
            '<div><b style="color:#10294d">¿Cómo va el curso?</b> ' +
            '<span style="color:#4a5768">Quién ha entregado, qué falta por ' +
            'calificar y en qué punto está cada cuadernillo.</span></div>' +
            '<a href="' + raiz + '/panel-docente" style="background:#2a78d6;' +
            'color:#fff;border-radius:5px;padding:8px 15px;font-size:14px;' +
            'font-weight:600;text-decoration:none;white-space:nowrap">' +
            'Ver mi curso</a></div>' +
            '<div style="font-weight:650;color:#10294d;margin-bottom:8px">' +
            'Qué hace cada botón ' +
            '<a href="#" id="ava-ayuda-toggle" style="font-weight:400;font-size:13px;' +
            'color:' + COLOR_BORDE + ';text-decoration:none;margin-left:8px">ocultar</a>' +
            '</div>' +
            '<div id="ava-ayuda-cuerpo">' +
            '<table style="border-collapse:collapse;width:100%">' + filas + '</table>' +
            '<div style="margin-top:10px;padding-top:10px;border-top:1px solid #dfe3e8">' +
            RESUMEN + '</div></div>';

        cuerpo_borrado(caja.querySelector('#ava-ayuda-cuerpo'));

        var cuerpo = caja.querySelector('#ava-ayuda-cuerpo');
        var toggle = caja.querySelector('#ava-ayuda-toggle');
        // Se recuerda si el docente lo cerró: útil el primer día, molesto el mes
        // siguiente.
        try {
            if (window.localStorage.getItem('ava-ayuda-docente') === 'oculta') {
                cuerpo.style.display = 'none';
                toggle.textContent = 'mostrar';
            }
        } catch (e) { /* sin localStorage, se muestra siempre */ }

        toggle.onclick = function (ev) {
            ev.preventDefault();
            var oculta = cuerpo.style.display === 'none';
            cuerpo.style.display = oculta ? '' : 'none';
            toggle.textContent = oculta ? 'ocultar' : 'mostrar';
            try {
                window.localStorage.setItem('ava-ayuda-docente',
                                            oculta ? 'visible' : 'oculta');
            } catch (e) { /* da igual */ }
        };
        return caja;
    }

    // --- Eliminar una actividad ---------------------------------------------
    // Formgrader no tiene botón para esto y hasta ahora había que borrar
    // carpetas a mano en el servidor. Se ofrece aquí, con el nombre de la
    // actividad escrito a mano como confirmación: es una operación que borra
    // trabajo, y un clic de más no debería bastar.
    function cuerpo_borrado(destino) {
        if (!destino) return;
        var raiz = (window.location.pathname.split('/formgrader')[0]) || '';

        var caja = document.createElement('div');
        caja.style.cssText =
            'margin-top:14px;padding-top:14px;border-top:1px solid #dfe3e8';
        caja.innerHTML =
            '<div style="font-weight:600;color:#10294d;margin-bottom:6px">' +
            'Eliminar una actividad</div>' +
            '<div style="font-size:14px;color:#4a5768;margin-bottom:8px">' +
            'Borra la actividad y lo publicado de ella. <b>Siempre guarda una ' +
            'copia con fecha antes de borrar.</b> Si tiene entregas de ' +
            'estudiantes, se niega salvo que insistas.</div>' +
            '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
            '<select id="ava-borrar-cual" style="padding:5px 8px;font:14px ' +
            'system-ui,sans-serif;min-width:190px"></select>' +
            '<input id="ava-borrar-conf" placeholder="escribe el nombre para confirmar" ' +
            'style="padding:5px 8px;font:14px system-ui,sans-serif;min-width:230px">' +
            '<button id="ava-borrar-btn" style="padding:6px 12px;font:14px ' +
            'system-ui,sans-serif;background:#c8392b;color:#fff;border:none;' +
            'border-radius:3px;cursor:pointer">Eliminar</button></div>' +
            '<div id="ava-borrar-msg" style="font-size:14px;margin-top:8px"></div>';
        destino.appendChild(caja);

        var sel = caja.querySelector('#ava-borrar-cual');
        var conf = caja.querySelector('#ava-borrar-conf');
        var btn = caja.querySelector('#ava-borrar-btn');
        var msg = caja.querySelector('#ava-borrar-msg');

        function decir(texto, color) {
            msg.style.color = color || '#4a5768';
            msg.innerHTML = texto;
        }

        // Tambien el GET lleva el token XSRF: desde JupyterHub 4.1 una peticion
        // autenticada por cookie que no es una navegacion se trata como anonima
        // si no lo trae, y el servidor la manda al OAuth, que la devuelve sin
        // token, y asi veinte veces hasta que el navegador se rinde. La lista
        // de actividades nunca llegaba a pintarse.
        fetch(raiz + '/ava-admin/actividades', {
            credentials: 'same-origin',
            headers: { 'X-XSRFToken': cookie_xsrf() },
        })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (d) {
                if (!d) { caja.style.display = 'none'; return; }
                d.actividades.forEach(function (a) {
                    var o = document.createElement('option');
                    o.value = a.id;
                    o.textContent = a.id + (a.envios
                        ? '  (' + a.envios + ' con entregas)' : '');
                    sel.appendChild(o);
                });
                if (!d.actividades.length) caja.style.display = 'none';
            })
            .catch(function () { caja.style.display = 'none'; });

        btn.onclick = function () {
            var tarea = sel.value;
            if (!tarea) return;
            if (conf.value.trim() !== tarea) {
                decir('Escribe <b>' + tarea + '</b> en la casilla para confirmar.', '#b57200');
                return;
            }
            btn.disabled = true;
            decir('Borrando…');
            fetch(raiz + '/ava-admin/borrar', {
                method: 'POST',
                credentials: 'same-origin',
                // El endpoint exige sesión y token XSRF: borra trabajo, así que
                // no puede aceptar un POST que venga de cualquier página.
                headers: {
                    'Content-Type': 'application/json',
                    'X-XSRFToken': cookie_xsrf(),
                },
                body: JSON.stringify({ tarea: tarea, forzar: false })
            })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                btn.disabled = false;
                var lista = (d.mensajes || []).map(function (m) {
                    return '<div>' + m + '</div>';
                }).join('');
                if (d.ok) {
                    decir('<b style="color:#0f8a4a">Eliminada.</b>' + lista +
                          '<div style="margin-top:4px">Recarga la página para ' +
                          'actualizar la lista.</div>', '#4a5768');
                } else {
                    decir('<b style="color:#c8392b">No se eliminó.</b>' + lista,
                          '#4a5768');
                }
            })
            .catch(function (e) {
                btn.disabled = false;
                decir('No se pudo contactar al servidor: ' + e, '#c8392b');
            });
        };
    }

    function insertar() {
        if (document.getElementById('ava-ayuda-docente')) return true;
        // Formgrader 0.8.5 monta su contenido en .container-fluid. Se prueban
        // varios selectores porque esto depende del HTML interno de nbgrader, que
        // puede cambiar entre versiones; si ninguno aparece, no se toca nada.
        var destino = document.querySelector('.container-fluid')
                   || document.querySelector('.container')
                   || document.getElementById('main');
        if (!destino) return false;
        destino.insertBefore(crearPanel(), destino.firstChild);
        return true;
    }

    function arrancar() {
        if (insertar()) return;
        // Formgrader pinta su tabla por JavaScript, así que el contenedor puede
        // no existir todavía cuando se carga este archivo. Se reintenta un rato
        // y luego se abandona en silencio.
        var intentos = 0;
        var reloj = setInterval(function () {
            if (insertar() || ++intentos > 20) clearInterval(reloj);
        }, 500);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', arrancar);
    } else {
        arrancar();
    }
})();
