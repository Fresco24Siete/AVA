# Montar el AVA en tu computador

Esta guía deja el AVA funcionando en tu equipo, para que tus estudiantes entren
desde Moodle. Son unos 20 minutos, casi todos de espera.

## Antes de empezar

Tu computador va a ser el servidor del curso, así que conviene que sea el que
vas a tener encendido en clase:

| | Mínimo | Recomendado |
|---|---|---|
| Sistema | Ubuntu 22.04 o más nuevo | Ubuntu 24.04 / 26.04 |
| Memoria | 8 GB | 16 GB o más |
| Espacio libre | 25 GB | 50 GB |
| Internet | cualquiera | por cable, si es posible |

No hace falta que tengas IP fija, ni abrir puertos, ni pedirle nada a tu
proveedor de internet.

## La instalación

Abre una terminal (`Ctrl` + `Alt` + `T`) y pega esta línea:

```bash
curl -fsSL https://raw.githubusercontent.com/Fresco24Siete/AVA/feat/menu-cuadernillos-y-notas/servidor/instalar-servidor.sh -o instalar-ava.sh && bash instalar-ava.sh
```

Te va a pedir tu contraseña una vez, al principio, para instalar programas.
Después casi todo es esperar.

**En algún momento se detiene y te pide entrar con tu cuenta en el navegador.**
Es el único paso donde tienes que hacer algo: es lo que le da al AVA una
dirección de internet para que tus estudiantes lo alcancen. Entra con la cuenta
que quieras (Google o GitHub sirven, es gratis) y vuelve a la terminal.

Al terminar te muestra la dirección de tu servidor. Se ve así:

```
https://ava-servidor.tailXXXXX.ts.net
```

## Conectarlo con Moodle

En tu curso de Moodle, en la herramienta externa (la actividad por la que
entran los estudiantes), cambia la dirección de la herramienta por la tuya
seguida de `/hub/lti/launch`:

```
https://ava-servidor.tailXXXXX.ts.net/hub/lti/launch
```

La clave y el secreto no se tocan: siguen siendo los mismos.

## El icono de la barra

Arriba a la derecha, junto al reloj, te queda un icono con el estado del
servidor.

**Si no lo ves después de instalar, cierra sesión y vuelve a entrar.** El icono
lo dibuja una extensión del escritorio, y una extensión recién instalada no
aparece en una sesión que ya estaba abierta. No basta con reiniciar el AVA.

Los estados son estos:

| Icono | Qué significa | Qué hacer |
|---|---|---|
| ✓ verde | Funcionando. Tus estudiantes pueden entrar. | Nada. |
| ⟳ ámbar | Arrancando, o funcionando solo dentro de este computador. | Esperar un minuto. |
| ✗ rojo | Caído. Tus estudiantes no pueden entrar. | Clic en el icono → **Reiniciar el AVA**. |

Al hacer clic se abre un menú con lo que puedes necesitar: copiar la dirección
para pasársela a tus estudiantes, abrir el AVA, encenderlo o reiniciarlo.

Si el servidor se cae mientras trabajas, te sale un aviso en pantalla. Solo
avisa **cuando se cae**, no cada minuto: si lo ves una vez, es que pasó algo.

## Día a día

**No tienes que hacer nada.** Cada vez que enciendas el computador, el AVA
arranca solo por detrás, antes de que abras nada.

Dos cosas que sí conviene saber:

- **Mientras haya clase, el computador tiene que estar encendido y con
  internet.** Si lo apagas o lo suspendes, tus estudiantes ven un error.
  Vale la pena desactivar la suspensión automática en Configuración › Energía.
- **Si cambias de red** (de la casa a la universidad, por ejemplo), no pasa
  nada: la dirección sigue siendo la misma.

## Si algo va mal

Primero: mira el icono de la barra. Casi todo se arregla con **Reiniciar el
AVA** desde ahí.

Si el icono está rojo y reiniciar no lo arregla, abre una terminal y ejecuta:

```bash
cd ~/AVA && bash servidor/instalar.sh --verificar
```

Eso imprime un diagnóstico. Mándaselo a Diego tal cual: ahí está lo que hace
falta para saber qué pasó.

Y si quieres volver a instalarlo todo desde cero, puedes repetir la línea de
la instalación las veces que quieras: **no borra tu información** (los
cuadernillos, las entregas y las notas se conservan).
