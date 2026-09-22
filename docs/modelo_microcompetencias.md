# Modelo de microcompetencias y nivel N1/N2/N3 (Fase 1)

**Aplicada en producción** (Hetzner, curso 36074) desde el despliegue del
2026-09-21, junto con la v6. Va en el bucle de migraciones de
`servidor/instalar.sh`. Es aditiva —no toca `exercise_attempts` ni
`attempt_errors`— y se puede aplicar repetidas veces sin efecto.

Para etiquetar un cuadernillo nuevo, la media página práctica está en
[`etiquetar_cuadernillo_nuevo.md`](etiquetar_cuadernillo_nuevo.md).

---

## 1. La decisión que gobierna todo lo demás

**La competencia no se guarda dentro de cada intento. Se resuelve por JOIN.**

El encargo planteaba denormalizarla. Se descartó por tres razones, y la primera
no es teórica:

1. **Corregir una etiqueta corrige el histórico.** El mapeo de este curso estuvo
   vacío hasta el 2026-09-18, con 686 intentos ya recogidos. Al cargarlo, los
   686 quedaron clasificados retroactivamente sin reprocesar nada. Con la
   etiqueta dentro de cada fila, habrían quedado huérfanos para siempre.
2. **Los notebooks ya entregados no se pueden reetiquetar.** Seis estudiantes
   entregaron `semana_01`. Si la etiqueta viviera en la metadata del `.ipynb`,
   cambiarla exigiría tocar entregas ya recibidas.
3. **Es diseño del curso, no dato del alumno.** Que el ejercicio 4 mida mCC87 es
   una decisión pedagógica que puede cambiar; que el alumno lo falló tres veces
   es un hecho que no.

La etiqueta puede además incluirse en la metadata del `.ipynb` como dato
**informativo y redundante** —útil para leer el notebook suelto—, pero el
backend nunca debe leer de ahí.

---

## 2. Cambios de esquema (`database/migracion_v5.sql`)

Cuatro piezas. Ninguna toca `exercise_attempts` ni `attempt_errors`, así que la
telemetría existente no se mueve.

### 2.1 `competencias.en_alcance`

Columna nueva. El catálogo tiene las siete del microcurrículo, pero el AVA solo
puede medir cuatro con trazas:

| | Oficial | `en_alcance` |
|---|---|---|
| I1 | mCP17 | **sí** |
| I3 | mCC87 | **sí** |
| I4 | mCC103 | **sí** |
| I7 | mCP88 | **sí** |
| I2 | mCC85 | no |
| I5 | mCA14 | no |
| I6 | mCA65 | no |

Hace falta marcarlo en la base y no solo saberlo. Cuando esta columna se
diseñó había **seis ejercicios etiquetados con I5 (mCA14)**, que se evalúa por
autorreporte, y el panel no tenía cómo distinguirlos. Las Fases 5 y 6 los
dejaron en **cero**, pero la columna sigue haciendo falta: es lo que impide que
una etiqueta fuera de alcance vuelva a colarse sin que nadie lo note.

### 2.1 bis Dos definiciones de mCP17, y no dicen lo mismo

Salió al etiquetar, y hay que resolverlo porque decide si siete etiquetas son
legítimas o son inventadas.

| Fuente | Qué dice mCP17 |
|---|---|
| El catálogo, sembrado en la base (`schema_v2.sql:102`) | «Aplica conocimientos de **álgebra lineal, cálculo diferencial e integral y métodos numéricos** para solucionar problemas mediante programación.» |
| El encargo, sección 2 | «**Aplicar conocimientos matemáticos** para la solución de problemas usando programación.» |

Con la del encargo, calcular una tarifa de parqueadero, aplicar un porcentaje
de descuento o corregir una media mal agrupada **sí** son mCP17. Con la del
catálogo, **ninguna lo es** — y entonces mCP17 no la mide ni un solo ejercicio
de las seis semanas, porque en un primer curso de programación no hay álgebra
lineal ni cálculo.

Se etiquetó con la del encargo, que es la instrucción más reciente y específica.
Pero **la descripción del catálogo es la que el panel le enseña al docente**: si
se queda como está, la pantalla pondrá «álgebra lineal, cálculo diferencial e
integral» encima de un ejercicio sobre el recibo del parqueadero.

**Decidido el 2026-09-21: se alinea el catálogo** al texto del encargo, con
`database/migracion_v6.sql`, ya conectada al instalador. Es un `UPDATE` de un
texto, acotado con un `LIKE` para que repetirla no haga nada, y con el `UPDATE`
inverso escrito al final por si hay que volver atrás.

El motivo: los ejercicios etiquetados miden de verdad lo que el encargo
describe —calcular una tarifa, aplicar un porcentaje, usar `div` y `mod`—, y la
alternativa era quitar las siete etiquetas y dejar el AVA midiendo **dos
microcompetencias de cuatro**, porque mCC103 ya está en cero.

Si el curso prefiere conservar el texto literal del syllabus, la vuelta atrás
es el `UPDATE` inverso del final de la migración más borrar las siete etiquetas
`I1` de los generadores.

Lo que no vale es dejarlo como está. La descripción no es decorativa: se pinta
en la guía «Qué mide cada código» del docente
(`panelDocenteRepository.go:190`), en la tarjeta con la barra de progreso
(`panel_docente_bridge.py:848`) y en el panel del **estudiante**, bajo «Qué has
aprendido» (`progresoRepository.go:127`). Hoy esa pantalla pondría «álgebra
lineal, cálculo diferencial e integral» encima de un ejercicio sobre el recibo
del parqueadero.

Y un detalle que importa si alguien lo arregla a mano en la base:
`migracion_v2.sql:43-47` hace `ON CONFLICT (id) DO UPDATE SET descripcion =
EXCLUDED.descripcion`, así que volver a pasar la v2 revierte el cambio. Por eso
va como migración y por eso tiene que aplicarse después de la v2.

### 2.2 Tope de dos competencias por ejercicio

Trigger `tope_competencias_por_ejercicio`. La regla ya se cumple —32 ejercicios
con una, 15 con dos— pero nada la forzaba.

Va como trigger y no como `CHECK` porque hay que contar filas hermanas. Es
`DEFERRABLE INITIALLY DEFERRED` para que una carga masiva pueda insertar las dos
filas de un ejercicio y validarse al final.

Mensaje al romperla:

```
ERROR: El ejercicio semana_03/ejercicio_1 tendría más de 2 competencias.
       Un ejercicio que dice medir todo no mide nada: deja 1 o 2.
```

### 2.3 Vista `senales_competencia`

Las señales por estudiante y competencia. **Vista, no tabla**: se calcula al
consultar, nunca queda desfasada y no hay que invalidarla cuando cambia el
mapeo. Con 16 estudiantes y ~700 intentos el coste es irrelevante.

Amplía `errores_por_competencia` con lo que faltaba para poder graduar:

| Columna | Qué es |
|---|---|
| `vistos` | Ejercicios de esa competencia que llegó a intentar de verdad |
| `resueltos` | De esos, cuántos pasó |
| `intentos` | Ejecuciones reales de celda de prueba |
| `fallos` | Las que dieron `failed` |
| `abandonos` | **Ejercicios** que dejó en `sin_validar` y nunca resolvió |
| `primer_intento` / `ultimo_intento` | Para ver evolución |

Los intentos que solo ejecutaron la plantilla sin tocarla
(`NotImplementedError`) **no cuentan**: no son un intento.

Ese criterio rige, con la misma definición, en cuatro sitios — y tiene que ser
la misma, porque los cuatro alimentan números que se ven juntos:

| Dónde | Qué pinta |
|---|---|
| `EstudiantesRepository.Competencias` | «Cómo va por competencia» **y el nivel N1/N2/N3** |
| `EstudiantesRepository.Ficha` | «Su recorrido, ejercicio por ejercicio» |
| `intentosReales` (panel del curso) | listado, en riesgo, por ejercicio |
| `senales_competencia` (esta vista) | hoy **nada**: ver §5 |

Las dos primeras las devuelve el **mismo handler** y se pintan **seguidas en la
misma página**: si divergen, la pantalla se contradice a sí misma sobre el mismo
ejercicio.

La vista comparte el criterio y tiene que seguir compartiéndolo, pero conviene
saber que **hoy no la lee ningún código**: se quedó como consulta de análisis
manual y como base del corte. Eso significa que ninguna prueba la cubre, así que
si alguien cambia el criterio en un sitio y no en ella, nada lo avisará.

`Malentendidos()` es la única excepción, y es deliberada: ver más abajo.

#### Corrección del 2026-09-21: qué es «plantilla» exactamente

La primera versión de esta vista descartaba el intento entero en cuanto
arrastrara un `NotImplementedError`. Medido contra la base de producción,
**ese criterio se equivocaba el 89 % de las veces**, y por un motivo que está
en `custom.js`, no en la base.

El buffer de errores de un ejercicio solo se vacía cuando se consigue **enviar**
un intento (`custom.js:352` y `:370`). El recorrido que el propio cuadernillo le
pide al alumno —ejecutar las celdas en orden— dispara el `NotImplementedError`
de la plantilla y lo deja en el buffer. Cuando después escribe su código y
ejecuta la prueba, **ese intento, que aprueba, arrastra el stub viejo**.

Lo que el criterio viejo descartaba, sobre los datos reales:

| | intentos |
|---|---:|
| Aprobados tirados a la basura | 18 (16 sin un solo error de verdad) |
| Fallos reales que además traían el stub | 23 |
| Plantilla de verdad | **5** |

Y en el panel del docente, que ya usaba ese criterio: **145 ejercicios
resueltos mostrados donde había 152**. Siete resueltos invisibles, repartidos
entre cinco estudiantes.

El criterio correcto, ya aplicado aquí y en
`EstudiantesRepository.Competencias`: es plantilla si **no aprobó** y **todos**
sus errores son `NotImplementedError`. Aprobar prueba que escribió algo; un
error real conviviendo con el stub, también.

`Malentendidos()` en `panelDocenteRepository.go` sigue usando el criterio
estricto **a propósito**, y no debe alinearse con este: allí la pregunta es
«¿qué concepto hay que explicar?», y un `AssertionError` que es consecuencia de
una celda vacía no es un malentendido. Aquí la pregunta es «¿cuánto cubrió?».

#### `abandonos` cuenta ejercicios, no eventos

También corregido el mismo día. El volcado al cerrar la pestaña se dispara cada
vez que el alumno cierra, así que contar eventos repetía el error que el panel
del alumno ya había corregido («recargar la página tres veces sumaba tres»).
Con `AbandonosN3 = 3`, **tres cierres del mismo ejercicio bastaban para sacar
de N3 a alguien que acabó resolviéndolo**. Ahora se cuentan ejercicios
distintos dejados en `sin_validar` que nunca llegaron a `passed`.

### 2.4 Tabla `corte_competencia`

El nivel vivo refleja el estado de hoy y cambia cada vez que alguien entrega.
Para el estudio pre/post hace falta además poder decir *«así estaba el grupo el
15 de septiembre»*, y eso una consulta en vivo no lo da.

Dos decisiones:

- **Guarda el nivel junto con las señales y los umbrales que lo produjeron.** Si
  mañana se ajustan los umbrales, un corte viejo se puede **recalcular** en vez
  de quedar mintiendo con un número que ya no significa lo mismo.
- **Lo escribe el docente**, pulsando «congelar corte». No lo escribe ningún
  trigger ni ninguna consulta de lectura: un efecto secundario dentro de un GET
  sería imposible de auditar después.

`nivel` admite `NULL`, que significa **«no hay nivel»** — y es distinto de estar
en N1. Son dos los casos que lo producen, y el motivo los distingue: que no haya
evidencia suficiente todavía, o que la competencia esté fuera de alcance.

---

## 3. La fórmula

Se calcula en el backend, como pedía el encargo, con los umbrales en una
constante editable.

### 3.1 Por qué no basta con contar fallos

El encargo proponía «a más fallos, nivel más bajo». Contra los datos reales eso
no funciona: **quien más trabaja acumula más fallos**. El estudiante con más
fallos del curso (68) resolvió **los 13 ejercicios** que intentó.

Hay que normalizar. Dos señales:

```
cobertura = resueltos / vistos          ¿resuelve lo que intenta?
costo     = fallos / max(resueltos, 1)  ¿cuánto le cuesta cada uno?
```

### 3.2 Por qué hacen falta las dos

Distribución real de I3 (18 estudiantes):

- **11 de 18 tienen cobertura 1.00** — resolvieron todo lo que intentaron.
- Pero su `costo` va de **0.0 a 5.2**.

La cobertura sola metería a 11 de 18 en el mismo nivel. El coste es lo que
separa *«lo sacó con soltura»* de *«lo sacó a duras penas»*, que es justo la
distinción entre N3 y N2 de la rúbrica.

En los datos, el coste se parte solo: doce estudiantes entre 0.0 y 1.5, cinco
entre 2.4 y 6.0. **El corte natural está en 2.0**, no es un número inventado.

### 3.3 Los umbrales

```go
// backend/internal/service/nivelCompetencia.go
const (
    MinimoEvidencia = 3    // ejercicios vistos; por debajo no se da nivel
    CoberturaN3     = 0.80 // resueltos / vistos
    CoberturaN2     = 0.40
    CostoN3         = 2.0  // fallos por ejercicio resuelto
    AbandonosN3     = 3    // a partir de aquí no es N3
)
```

### 3.4 El cálculo

```
si vistos < MinimoEvidencia          -> nivel = NULL ("sin evidencia suficiente")

cobertura = resueltos / vistos
costo     = fallos / max(resueltos, 1)

si cobertura >= CoberturaN3
   y costo     <  CostoN3
   y abandonos <  AbandonosN3        -> N3
si cobertura >= CoberturaN2          -> N2
en otro caso                         -> N1
```

Correspondencia con la rúbrica del encargo:

| Nivel | Rúbrica | Traducción operativa |
|---|---|---|
| **N3** | «correcto incluso en casos límite» | Resuelve casi todo lo que intenta, con pocos fallos y sin rendirse. Las pruebas ocultas del AVA ya comprueban casos límite, así que pasar **es** manejarlos |
| **N2** | «funciona solo en el caso típico» | Resuelve, pero le cuesta: muchos fallos por ejercicio, o abandonos |
| **N1** | «el algoritmo no resuelve el problema» | No llega a resolver la mayoría |

### 3.5 Ejercicios con dos competencias

**Cuentan enteros en las dos.** No se reparte 0.5 a cada una.

Motivo: la métrica es un cociente (`resueltos / vistos`). Si un ejercicio contara
medio en cada competencia, un estudiante con ejercicios de doble etiqueta
parecería haber trabajado menos que otro con etiquetas simples, cuando hizo
exactamente lo mismo. Y conceptualmente: la competencia se ejerció o no se
ejerció; no se ejerce «a medias» porque el ejercicio también mida otra cosa.

Verificado en la base de prueba: un ejercicio etiquetado `I1`+`I3` produce una
fila completa en cada una.

### 3.6 El mínimo de evidencia, y por qué importa tanto aquí

Con menos de tres ejercicios vistos, un nivel es ruido: un estudiante que
intentó uno y lo falló no está en N1, está sin medir.

Contra los datos de hoy:

| Competencia | Ejercicios vistos (media) | Pares con menos de 3 |
|---|---|---|
| I3 (mCC87) | 7.2 | **1 de 18** |
| I4 (mCC103) | 2.0 | **12 de 18** |
| I5 (mCA14) | 2.5 | **13 de 18** |

O sea: con este mapeo, **I4 no se puede medir para dos tercios del curso**. No
es un problema del umbral — es que I4 no tiene ejercicios suficientes. Se
arregla reetiquetando, no bajando el mínimo.

**Actualización tras las Fases 5 y 6:** el recorte quitó mCC103 de las semanas
3 a 6 —la planeación oficial no le da evidencia ahí— y la dejó con 3
ejercicios en las semanas 1 y 2. Al revisar esos tres uno a uno para la Fase 6,
**ninguno la medía**: dos eran residuo de ejercicios reemplazados sin actualizar
la etiqueta, y el tercero emparejaba editor/terminal/intérprete/IDE con su
definición.

Así que mCC103 se queda en **cero ejercicios**, y no es un descuido: es que
*«reconocer problemas de sistemas y organizaciones susceptibles de tratamiento
algorítmico»* no se pide en ningún cuadernillo. Lo que se pide es escribir
algoritmos, que es mCC87.

Medirla exige un ejercicio nuevo —del tipo «aquí tienes tres situaciones de una
organización: di cuál se puede resolver con un algoritmo y por qué»—, no otra
vuelta de etiquetas. Está en [`flujo_actual_ava.md`](flujo_actual_ava.md) con
el detalle.

Bajar el mínimo a 1 daría un nivel a todo el mundo y sería un número inventado.

---

## 4. Instrumentación (Fase 3) — hecho

La Fase 3 pedía dos cosas: que `custom.js` resolviera la microcompetencia de
cada celda calificable y la metiera en el payload, y que el backend la validara
contra el catálogo al ingerir.

**La primera se resolvió de otra manera, y es la decisión de §1.** La
competencia no viaja con el intento: se resuelve por JOIN sobre el par
`(cuadernillo_id, exercise_id)`. Así que no hubo nada que añadir al payload ni
a `custom.js`. La cadena se verificó carácter a carácter, de punta a punta:

```
constructor.py    grade_id = "test_ejercicio_1"
custom.js:59      quita "test_"         -> "ejercicio_1"
metrics_bridge    no lo toca            -> "ejercicio_1"
exercise_attempts .exercise_id          == ejercicio_competencias.exercise_id
```

Y contra la base de producción: de todos los intentos recogidos, **uno solo**
no encuentra competencia, y es la fila conocida de cuadernillo `Fabio` (un
alumno trabajando sobre una copia renombrada). El JOIN encaja.

**La segunda sí hacía falta, y no como estaba escrita.** No hay tabla de
ejercicios contra la que validar —el esquema declara a propósito que ejercicio
y cuadernillo no son entidades propias— y lo único parecido a un catálogo es
`ejercicio_competencias`. Usarlo para **rechazar** sería el peor error posible:
un ejercicio se queda sin mapeo por un fallo de operación (nadie ejecutó
`cargar-competencias` tras publicar una semana nueva), y rechazar convertiría
un olvido del equipo en pérdida permanente del trabajo de un estudiante, que
además no se enteraría.

Así que se valida para **avisar**, no para rechazar
(`service.avisarSiHuerfano`):

- el intento se guarda siempre y responde 201, como antes;
- si el par no tiene mapeo, queda una línea en el log del backend;
- se avisa **una vez por par**, no una por intento: un cuadernillo sin mapeo
  generaba cientos de líneas al día y el aviso se volvía ruido;
- un fallo al consultar no se propaga: el intento ya está guardado.

Antes esto fallaba en silencio absoluto. El intento se guardaba, el alumno
recibía 201, y después desaparecía de todo análisis por competencia porque el
JOIN es INNER. El handler ni siquiera importaba el paquete `log`. La fila de
`Fabio` lleva desde el 2026-09-14 en la base y nadie lo supo hasta mirarlo a
mano.

## 5. El nivel en el panel (Fase 4) — hecho

1. `service.NivelCompetencia(senales) → (nivel *int, motivo string)` con los
   umbrales de §3.3. Cubierto por trece pruebas de frontera, porque un `>=`
   donde iba un `>` mueve de nivel a estudiantes reales sin que nada falle.
2. Expuesto en `GET /internal/curso/:curso/estudiante/:e`, que gana los campos
   `nivel` y `motivo_nivel` junto a lo que ya devolvía.
3. `POST /internal/curso/:curso/corte` congela un corte con su etiqueta.
4. En el panel: la insignia de nivel encima de la barra, con el motivo debajo
   en palabras que el docente pueda leer tal cual.

### De dónde salen las señales, y por qué no de la vista

El encargo decía «consultando el endpoint/vista de la Fase 1». **No se lee
`senales_competencia`**: el nivel se calcula sobre lo que devuelve
`EstudiantesRepository.Competencias`. Tres razones, y la primera manda:

1. **La vista no está aplicada en producción.** Leer de ella habría dejado sin
   funcionar el bloque de competencias —que hoy sí funciona— hasta el siguiente
   despliegue. Así el nivel entra sin depender de la migración.
2. **Los dos JOIN de la vista son INNER**, así que una competencia que el
   alumno no ha tocado **no produce fila** — no produce fila con nivel `NULL`.
   Son cosas distintas para quien dibuja la pantalla, y `vistos = 0` es el caso
   más común al empezar el semestre. `Competencias` parte del catálogo y hace
   LEFT JOIN, que es justo lo que hace falta.
3. **La vista no tiene `disenados`**, el denominador de diseño que la tarjeta
   ya mostraba («3 sin tocar»).

`senales_competencia` sigue siendo útil para lo que se diseñó: mirar el curso
entero de una vez. Las dos comparten el criterio de plantilla corregido en la
Fase 3, y tienen que seguir compartiéndolo.

Se añadió `fallos` a `Competencias`, que no lo tenía. **No es `intentos`**:
el coste de la fórmula es fallos por ejercicio resuelto, así que alimentarlo
con el total de intentos lo infla y baja a N2 a quien merece N3 — justo el
error que la fórmula existe para no cometer.

### El filtro por semana

`?cuadernillo=semana_03` acota el desglose, y el panel lo ofrece como chips que
salen solos de las semanas que el alumno tiene (no de una lista que mantener).

Con un aviso que el propio panel da: **una semana casi nunca da evidencia
suficiente**. Aporta dos o tres ejercicios por competencia, así que el nivel
saldrá «sin medir» casi siempre. No es un fallo del filtro — un nivel calculado
sobre dos ejercicios es ruido. El filtro sirve para mirar la actividad de esa
semana, no para graduar por semana.

Lo de «por grupo» del encargo ya estaba: cada curso es un `course_id` distinto y
todas las consultas lo llevan en el WHERE; un docente solo puede pedir el suyo.

### El corte

Lo dispara el docente desde el panel del curso, con un nombre (`pre`, `post`,
`corte 1`…). Repetir el nombre **sobrescribe**: congelar `pre` dos veces es un
error de dedo, no un dato nuevo.

Reutiliza `Competencias` persona a persona en vez de una consulta propia. Una
consulta distinta para el mismo número acaba divergiendo, y **un corte que no
coincide con lo que el docente estaba viendo no vale para nada**. Todo va en
una transacción: un corte a medias sería peor que no tenerlo.

---

## 6. Lo que este modelo NO hace

- **No mide mCP88 (I7).** El encargo dice que no es calificable: se resuelve con
  celdas markdown y una fuente externa. Sin intentos no hay fallos, y sin fallos
  esta fórmula no aplica. Queda `en_alcance = true` en el catálogo, pero su
  nivel será siempre `NULL`. **Hay que decidir por qué otra señal se mide**, o
  aceptar que no se mide.
- **No da nivel a mCC85, mCA14 ni mCA65** (I2, I5, I6), y eso está cableado, no
  solo escrito: `ponerNivel` deja el nivel en `NULL` con el motivo «no se mide
  con trazas de actividad» en cuanto `en_alcance` es falso.

  No es una precaución teórica. Los ejercicios etiquetados con I5 (mCA14)
  llevan también la etiqueta I3, así que su tarjeta sería una recopia de un
  subconjunto de las señales de I3 presentada como otra competencia. Con un N3
  verde encima, el panel estaría afirmando algo que este sistema no puede saber
  — y al congelar un corte, ese número entraría en la evidencia del estudio sin
  forma de distinguirlo de los legítimos.

  La Fase 5 quitó las dos que había en las semanas 3 a 6. Quedan **cuatro**, en
  las semanas 1 y 2, que se ajustan en la Fase 6.
- **No pondera con pre/post-test ni evidencia complementaria.** Eso es la
  Actividad 3.1 del plan de grado y queda fuera.
- **No toca la devolución de notas a Moodle.** Fuera de alcance, y además sería
  Basic Outcomes (LTI 1.1) y no AGS.

---

## 7. Pruebas hechas

En una base **desechable**, no en producción:

- `schema_v2` + `migracion_v3` + `v4` + `v5` aplican limpias, en orden.
- `v5` aplicada **dos veces**: idempotente.
- `en_alcance` queda correcto en las siete.
- El trigger **acepta** dos competencias y **rechaza** la tercera con el mensaje
  previsto.
- La vista cuenta bien: un ejercicio con dos etiquetas produce fila en las dos,
  y un `sin_validar` sale como abandono, no como fallo.
- Contenedor de prueba eliminado. Producción intacta.

Añadido el 2026-09-21, con los dos criterios corregidos:

- `v5` aplicada **tres veces** seguidas: sigue siendo idempotente.
- Sembrados los tres casos que motivaron la corrección del stub, la vista los
  clasifica como debe:

  | Caso sembrado | Esperado | Obtenido |
  |---|---|---|
  | Aprobado que arrastra el stub viejo | cuenta como visto y resuelto | ✔ |
  | Plantilla de verdad (falló, solo stub) | no cuenta ni como visto | ✔ |
  | Fallo real que además trae el stub | cuenta como visto y fallo | ✔ |

  Resultado: `vistos 2, resueltos 1, fallos 1`. Con el criterio viejo habría
  sido `vistos 0, resueltos 0` — o sea, no medía nada.

- Sembrado el caso de abandonos: un ejercicio cerrado **tres veces** y resuelto
  al final, más otro cerrado dos veces y nunca resuelto. Da `abandonos = 1`,
  no 5.
- Ingesta probada de punta a punta contra el backend real: un par con mapeo
  entra sin avisos; un par huérfano enviado **tres veces** produce **un solo**
  aviso en el log; un segundo par huérfano produce el suyo. Los cinco intentos
  quedaron guardados: no se pierde telemetría.
- `go build`, `go vet`, `go test ./...` y la suite de `custom.js` (15/15) en
  verde tras los cambios.

Y, porque nada de lo anterior era una prueba automática, **el criterio ahora
está cubierto por la suite de integración** (`caso_13_criterio_plantilla` en
`backend/tests/telemetria/prueba_backend.py`), que corre contra un backend y
una base vivos:

| Caso | Comprueba |
|---|---|
| 13a | Aprobado con el stub pegado → cuenta como intento y como resuelto |
| 13b | Plantilla de verdad → no cuenta como intento, sale «solo ejecutó la celda vacía» |
| 13c | Fallo real con el stub pegado → cuenta, y se ve su `AssertionError` |
| 13d | Cinco cierres de dos ejercicios, uno resuelto al final → `abandonos = 1` |
| 13e | Ejercicio sin mapeo → 201 y se guarda igual |

**56/56 en verde**, incluidos los doce casos anteriores: el cambio de criterio
en `Ficha()` no movió ninguno de los números que ya se comprobaban.

Sin estas pruebas, volver al criterio viejo no rompía nada visible — que es
exactamente como llegó a producción la primera vez.

### Fase 4 (2026-09-21)

`service.NivelCompetencia` lleva trece casos de frontera
(`nivelCompetencia_test.go`), que es donde vive el riesgo: un `>=` donde iba un
`>` mueve de nivel a estudiantes reales sin que nada falle. Comprueban que
`0.80` de cobertura entra en N3 y que un coste de exactamente `2.0` ya no,
que tres abandonos justos sacan de N3, que no resolver nada no divide por cero,
y —lo más importante— que **cero actividad devuelve «sin nivel», no N1**.

Y `caso_14_nivel_y_corte` en la suite de integración, contra backend y base
vivos:

| Caso | Comprueba |
|---|---|
| 14a | Cinco de cinco resueltos con poco coste → N3 |
| 14b | Un solo ejercicio visto → `nivel: null`, y null sigue siendo null al pasar por JSON |
| 14c | Toda competencia trae motivo, también las que no ha tocado |
| 14d | `fallos` e `intentos` son campos distintos y no se confunden |
| 14e | Filtrando por semana solo cuentan los ejercicios de esa semana |
| 14f | Una sola semana no da evidencia: pasa de N3 a «sin medir» |
| 14g | Un cuadernillo con caracteres raros → 400, no llega al WHERE |
| 14h–14l | El corte: sin etiqueta 400, guarda nivel y umbrales, repetir etiqueta sobrescribe, y no se puede congelar el corte de otro curso |

**68/68 en verde**, incluidos los 56 anteriores.

El HTML del panel se renderizó con datos sintéticos para los cinco casos (N3,
N2, N1, sin medir, sin tocar) antes de darlo por bueno. Ahí salió un fallo que
no habría dado la cara de otra forma: un `\b` sin escapar dentro del f-string
del JavaScript se convertía en un **backspace real** en el regex de la cookie
XSRF, así que el botón de congelar corte habría respondido 403 siempre. El
barrido de caracteres de control sobre la página generada ahora sale limpio.
