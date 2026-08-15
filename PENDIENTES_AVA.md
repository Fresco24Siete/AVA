# Pendientes del AVA

Estado a 14 de agosto de 2026, después de desplegar los cuadernillos de las
semanas 1 y 2 y probarlos contra Moodle de punta a punta.

Lo que ya funciona no está aquí: esto es solo lo que queda abierto, ordenado por
lo que bloquea a lo que no.

---

## 1. Bloqueantes

### 1.1 Las credenciales LTI son las de desarrollo

`LTI_CLIENT_SECRET` no está definido en la VM, así que JupyterHub arranca con el
secreto de desarrollo que está escrito en `hub_config/jupyterhub_config.py`
(`moodle-llave-publica` / `secreto-super-seguro-000000`), y Moodle está
configurado contra esos mismos valores.

Son públicos: están en el repositorio. Cualquiera que los lea puede fabricar un
lanzamiento LTI válido y entrar como cualquier estudiante o como docente.

Hay que generar credenciales nuevas, ponerlas en el `.env` de la VM y
actualizarlas en la actividad LTI de Moodle. Los dos lados a la vez, o se corta
el acceso.

**Bloquea además la devolución de notas** (§2.1): el envío a Moodle va firmado
con estas credenciales.

### 1.2 La VM no aguanta un curso completo

Medido sobre la imagen actual: un estudiante activo consume **~250 MB** (servidor
más kernel con el cuadernillo ejecutado). La VM es una `e2-small` de 2 GB.

| Escenario | Memoria | Máquina |
|---|---|---|
| 25 estudiantes, semanas 1–8 | ~7 GB | `e2-standard-2` (8 GB) |
| 25 estudiantes, desde la semana 9 | ~11 GB | `e2-standard-4` (16 GB) |

Desde la semana 9 el temario oficial exige NumPy, pandas y Matplotlib, y un
kernel que los importa pasa de ~130 MB a ~350 MB.

Hoy caben unos cinco o seis estudiantes a la vez.

---

## 2. Funcionalidad a medio camino

### 2.1 Devolución de notas a Moodle

Comprobado que **es viable**: el lanzamiento trae `lis_result_sourcedid` y
`lis_outcome_service_url` apuntando a `https://lms.uis.edu.co/ava/mod/lti/service.php`.
El Hub ya los captura y los pasa al contenedor.

Falta la parte difícil: ese identificador es del lanzamiento del **estudiante**,
pero quien califica es el **docente**, en otro contenedor. Hay que guardarlo en
un sitio compartido —Postgres es el natural— y, al calificar, recuperarlo y
enviar la nota firmada con OAuth 1.0 al servicio de resultados.

Depende de §1.1.

### 2.2 El esquema no permite calcular una nota

`exercise_attempts` guarda ocho columnas y **ninguna es el puntaje**. El navegador
envía `puntos_maximos`, `codigo_celda` y `orden`, y el backend los descarta.

Desde la base se sabe quién intentó qué y si pasó, pero no cuánto vale. Hay que
decidir: o se añaden esas columnas, o la nota sale de nbgrader y la base se queda
solo con intentos y errores.

### 2.3 Los errores de exploración no se registran

La telemetría solo mira las celdas de ejercicio. Un estudiante que rompe una
celda del laboratorio experimentando —lo más frecuente, y probablemente lo más
interesante para la investigación— no deja rastro en ninguna parte.

Se comprobó en una sesión real: dos errores de sintaxis en celdas de
demostración, cero filas en la base.

Ampliarlo implica etiquetar esos eventos como exploración para no mezclarlos con
los de evaluación, y cambia el volumen de datos y el contrato con el backend.

---

## 3. Calidad de lo que ya funciona

### 3.1 El tutor tarda demasiado

Entre **42 y 84 segundos** por respuesta. Un estudiante de primer semestre va a
creer que se colgó: no hay ningún aviso de espera mientras tanto.

Parte del retraso eran los 4.000 caracteres de contexto que ya se quitaron; falta
medir cuánto mejoró.

### 3.2 El tutor falla por congestión del modelo

`gemini-3.5-flash` devuelve `503 high demand` de forma intermitente. El backend
reintenta tres veces **siempre contra el mismo modelo**, así que si está
congestionado fallan las tres y se van 80 segundos.

`gemini-3.5-flash-lite` responde bien, está menos congestionado y es más barato.
Con que el reintento caiga ahí, la mayoría de esos fallos desaparecen.

Ojo: `gemini-2.5-flash` y `gemini-2.5-flash-lite` ya **no existen** (404).

### 3.3 Tareas viejas en formgrader

La lista del docente muestra `semana_1` y `testing`, restos de pruebas
anteriores, junto a `semana_01` y `semana_02`. Confunde y conviene limpiarlas.

### 3.4 Datos de prueba en la base

`exercise_attempts` tiene doce intentos y `attempt_errors` veinticuatro errores,
todos de pruebas deliberadas. Hay que limpiarlos antes de que empiece el semestre
para no mezclarlos con los reales.

### 3.5 Flowgorithm sin validar

`exportar_flowgorithm()` genera el `.fprg` pero **nunca se probó** contra la
versión de Flowgorithm de la sala. El camino seguro —el guion impreso para
construir el diagrama a mano— sí está terminado.

---

## 4. Contenido

Faltan los cuadernillos de las **semanas 3 a 16**. El mapa está hecho
(`plan_cuadernos_ava.md` en el Drive del proyecto) y la infraestructura de
autoría sirve para todos: cada semana es una carpeta con su `generador.py`.

Los quince archivos `N00`–`N14` de la planeación anterior siguen en el Drive y ya
no corresponden al mapa nuevo.

---

## 5. Decisiones abiertas

- **`METRICS_TOKEN_SECRET` vacío deja pasar la telemetría sin verificar
  identidad.** Se hizo así para no dejar sin datos a una clase en marcha si el
  despliegue va a medias. En la VM el secreto está puesto y la validación es
  estricta, pero conviene ratificar esa política.
- **El rol `ava` de Postgres es superusuario** y es el mismo con el que se
  conecta la aplicación. Lo habitual sería un rol aplicativo con permisos solo
  sobre las tres tablas.
- **La VM corre la rama `feat/menu-cuadernillos-y-notas`**, no `main`.
