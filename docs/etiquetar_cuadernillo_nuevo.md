# Etiquetar un cuadernillo nuevo (media página, léela entera)

Escrito el 2026-09-22 porque el profesor va a mandar más cuadernillos y Bryan
pidió dejar el mapeo listo «para que no perdamos datos».

**No se pierden.** La competencia **no viaja dentro del intento del alumno**: se
resuelve por JOIN al consultar. Un cuadernillo que llegue sin etiquetar sigue
recogiendo telemetría, y el día que se etiquete, **todo el histórico se
clasifica solo**, sin reprocesar nada. Ya pasó: el mapeo estuvo vacío hasta el
2026-09-18 con 686 intentos recogidos, y al cargarlo los 686 quedaron
clasificados retroactivamente.

Lo que sí se pierde por no etiquetar es el **tiempo** en que el panel del
profesor enseña menos de lo que hay. Nada más.

---

## Los cuatro pasos

1. **En el generador**, cada ejercicio lleva su lista:

   ```python
   c.ejercicio(numero=2, competencias=['I3', 'I1'], titulo="...", ...)
   ```

2. **Construir.** `build.py` emite el mapeo a `notebook/cuadernillos/competencias.json`:

   ```bash
   python3 notebook/cuadernillos/build.py
   ```

3. **Reconstruir la imagen del docente** (el `competencias.json` viaja dentro):

   ```bash
   docker build -t mi_imagen_jupyterlab_docente:latest -f notebook/Dockerfile.docente notebook
   ```

4. **Cargarlo al backend.** Sin este paso el panel no ve nada nuevo, y el backend
   solo deja un aviso en el log (`exerciseAttempsService.go:84-90`), no falla:

   ```bash
   cargar-competencias
   ```

   Desde fuera del contenedor del docente, en el servidor:

   ```bash
   cd ~/AVA && TOK=$(grep -E "^METRICS_API_TOKEN=" .env | cut -d= -f2-) \
     && docker run --rm --network moodle_jupyter_net \
        -e METRICS_API_BASE=http://api_go:8080 -e METRICS_API_TOKEN="$TOK" \
        --entrypoint cargar-competencias mi_imagen_jupyterlab_docente:latest
   ```

Reemplaza el mapeo de los cuadernillos que vengan en el archivo y **no toca los
demás**, así que es seguro correrlo tantas veces como haga falta.

**Si quitas un ejercicio, su etiqueta no se pierde.** `build.py` conserva en el
mapeo los ids que ya no existen en el generador (los marca como retirados al
construir), porque sus intentos siguen en la base bajo ese id y sin la etiqueta
quedarían fuera del análisis. Por lo mismo, **no reutilices un número** para un
ejercicio distinto en una semana que ya tenga telemetría: el id es la identidad.

---

## Los códigos, y cuál de ellos es un problema

| código | microcompetencia | qué mide | estado |
|---|---|---|---|
| `I1` | mCP17 | aplicar conocimientos matemáticos programando | 8 ejercicios, **le falta cobertura** |
| `I3` | mCC87 | identificar variables y aspectos del problema para armar el algoritmo | 30 ejercicios, cubierta |
| `I4` | mCC103 | reconocer qué problemas de una organización admiten tratamiento algorítmico | **0 ejercicios: no la mide nada** |
| `I7` | mCP88 | investigar y seleccionar fuentes confiables | **0, y no es autocalificable** |

Fuera de alcance: `I2` (mCC85), `I5` (mCA14), `I6` (mCA65). No etiquetes con
ellos: el panel los descarta.

**Lo que hay que resolver con el profesor, no a ciegas:**

- **`I4` (mCC103) no la mide ningún ejercicio.** No se arregla reetiquetando lo
  que hay: los 38 ejercicios existentes son de escribir código, y mCC103 va de
  *reconocer* qué situación admite un algoritmo. Hace falta un ejercicio nuevo
  del tipo «aquí tienes tres situaciones de una organización, di cuál se
  resuelve con un algoritmo y por qué». Ese contenido lo tiene que dar el
  profesor.
- **`I1` (mCP17) se queda corta.** El nivel exige 3 ejercicios distintos vistos
  (`MinimoEvidencia` en `backend/internal/service/nivelCompetencia.go`). Hoy solo
  7 de 18 alumnos llegan; la media es 2.89, o sea que **once alumnos están
  clavados en 2 de 3**. Un solo ejercicio `I1` más en las semanas 1 a 3 los mueve
  a todos de golpe. Pero hay que validar con el profesor que ese ejercicio de
  verdad mide «aplicar conocimientos matemáticos», no ponerlo por llegar al número.
- **`I7` (mCP88) es la de las revisiones bibliográficas** y no sale de un
  ejercicio autocalificado. Hay que decidir cómo se evidencia: una entrega
  aparte, una rúbrica del profesor, o se deja fuera de la medición automática y
  se dice así en el informe.

---

## Seis ejercicios siguen sin etiqueta

Son de las dos semanas con más entregas, así que son los que más telemetría
están dejando sin clasificar:

- `semana_01`: ejercicios 1, 2, 4 y 6
- `semana_02`: ejercicios 2 y 6

No los etiqueto a ojo: decidir qué mide cada ejercicio es diseño del curso. O el
profesor dice cuál va con cuál, o se deja escrito que no miden ninguna de las
cuatro y por qué.

---

## Antes de publicar, comprueba

```bash
python3 notebook/cuadernillos/build.py        # valida contratos, puntos y minutos
python3 notebook/cuadernillos/verificar.py    # corre las soluciones y detecta regalados
python3 notebook/cuadernillos/estimar_tiempo.py
```

El profesor pidió cuadernillos de **~30 minutos**. Los seis actuales piden entre
56 y 121. `estimar_tiempo.py` lo calcula del contenido, no de un número escrito
a mano, así que sirve para recortar con datos.
