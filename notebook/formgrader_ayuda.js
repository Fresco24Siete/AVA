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
                   'a la vista.'
        },
        {
            boton: 'Release',
            titulo: '2. Liberar',
            texto: 'Deja el cuadernillo disponible para que los alumnos lo ' +
                   'reciban. En este AVA el paso que de verdad se lo entrega es ' +
                   'el comando publicar-cuadernillo, que además define desde ' +
                   'cuándo y hasta cuándo está abierto.'
        },
        {
            boton: 'Collect',
            titulo: '3. Recoger',
            texto: 'Trae los cuadernillos que los alumnos entregaron. Hasta que ' +
                   'no recojas, no hay nada que calificar.'
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
        'El recorrido completo es: <b>editas el cuadernillo → Generar → ' +
        'Previsualizar → Liberar → publicar-cuadernillo → (los alumnos ' +
        'trabajan) → Recoger → Calificar</b>. ' +
        'La nota sale solo de las celdas de prueba; los puntos de experiencia y ' +
        'las insignias que ve el alumno no cuentan para nada.';

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

        caja.innerHTML =
            '<div style="font-weight:650;color:#10294d;margin-bottom:8px">' +
            'Qué hace cada botón ' +
            '<a href="#" id="ava-ayuda-toggle" style="font-weight:400;font-size:13px;' +
            'color:' + COLOR_BORDE + ';text-decoration:none;margin-left:8px">ocultar</a>' +
            '</div>' +
            '<div id="ava-ayuda-cuerpo">' +
            '<table style="border-collapse:collapse;width:100%">' + filas + '</table>' +
            '<div style="margin-top:10px;padding-top:10px;border-top:1px solid #dfe3e8">' +
            RESUMEN + '</div></div>';

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

    function insertar() {
        if (document.getElementById('ava-ayuda-docente')) return true;
        // Formgrader monta su contenido dentro de .container; si no está, es que
        // no estamos en formgrader o cambió el HTML: no se toca nada.
        var destino = document.querySelector('.container') || document.querySelector('#main');
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
