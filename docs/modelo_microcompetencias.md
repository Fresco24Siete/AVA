# Modelo de microcompetencias y nivel N1/N2/N3 (Fase 1)

Diseño propuesto. **La migración no se ha aplicado a producción**: solo se ha
probado en una base desechable (ver §6).

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

Hace falta marcarlo en la base y no solo saberlo: hoy hay **seis ejercicios
etiquetados con I5 (mCA14)**, que se evalúa por autorreporte, y el panel no
tiene cómo distinguirlos.

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
| `abandonos` | Las que dieron `sin_validar`: dejó errores y no volvió |
| `primer_intento` / `ultimo_intento` | Para ver evolución |

Los intentos que solo ejecutaron la plantilla sin tocarla
(`NotImplementedError`) **no cuentan**: no son un intento. Es el mismo criterio
que usa la ficha del docente; si no coincidieran, dos secciones de la misma
página se contradirían.

### 2.4 Tabla `corte_competencia`

El nivel vivo sale de la vista y refleja el estado de hoy. Para el estudio
pre/post hace falta además poder decir *«así estaba el grupo el 15 de
septiembre»*, y eso una vista no lo da.

Dos decisiones:

- **Guarda el nivel junto con las señales y los umbrales que lo produjeron.** Si
  mañana se ajustan los umbrales, un corte viejo se puede **recalcular** en vez
  de quedar mintiendo con un número que ya no significa lo mismo.
- **Lo escribe el docente**, pulsando «congelar corte». No lo escribe ningún
  trigger ni ninguna consulta de lectura: un efecto secundario dentro de un GET
  sería imposible de auditar después.

`nivel` admite `NULL`, que significa **«sin evidencia suficiente»** — y es
distinto de estar en N1.

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
es un problema del umbral — es que I4 solo tiene 11 ejercicios repartidos en
seis semanas. Se arregla en la Fase 5 reetiquetando, no bajando el mínimo.

Bajar el mínimo a 1 daría un nivel a todo el mundo y sería un número inventado.

---

## 4. Lo que el backend tiene que añadir (Fase 3-4)

No entra en esta fase, pero queda dicho para que el diseño se entienda entero:

1. `service.NivelCompetencia(senales) → (nivel *int, motivo string)` con los
   umbrales de §3.3.
2. Exponerlo en `GET /internal/curso/:curso/estudiante/:e`, junto a lo que ya
   devuelve.
3. `POST /internal/curso/:curso/corte` para congelar un corte con su etiqueta.
4. En el panel: el nivel al lado de la barra que ya existe, y «sin evidencia
   suficiente» cuando `vistos < 3` — nunca un N1 fingido.

---

## 5. Lo que este modelo NO hace

- **No mide mCP88 (I7).** El encargo dice que no es calificable: se resuelve con
  celdas markdown y una fuente externa. Sin intentos no hay fallos, y sin fallos
  esta fórmula no aplica. Queda `en_alcance = true` en el catálogo, pero su
  nivel será siempre `NULL`. **Hay que decidir por qué otra señal se mide**, o
  aceptar que no se mide.
- **No pondera con pre/post-test ni evidencia complementaria.** Eso es la
  Actividad 3.1 del plan de grado y queda fuera.
- **No toca la devolución de notas a Moodle.** Fuera de alcance, y además sería
  Basic Outcomes (LTI 1.1) y no AGS.

---

## 6. Pruebas hechas

En una base **desechable**, no en producción:

- `schema_v2` + `migracion_v3` + `v4` + `v5` aplican limpias, en orden.
- `v5` aplicada **dos veces**: idempotente.
- `en_alcance` queda correcto en las siete.
- El trigger **acepta** dos competencias y **rechaza** la tercera con el mensaje
  previsto.
- La vista cuenta bien: un ejercicio con dos etiquetas produce fila en las dos,
  y un `sin_validar` sale como abandono, no como fallo.
- Contenedor de prueba eliminado. Producción intacta.
