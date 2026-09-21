-- =========================================================
-- Migración v5 — nivel por microcompetencia
-- =========================================================
-- Añade lo mínimo para poder decir, por estudiante y microcompetencia, en qué
-- nivel está (N1/N2/N3), SIN denormalizar la competencia dentro de cada intento.
--
-- Por qué no se denormaliza, que es la decisión de diseño que gobierna todo lo
-- de abajo: la competencia de un ejercicio es DISEÑO DEL CURSO, no un dato del
-- alumno. Si viajara dentro de cada fila de exercise_attempts, corregir una
-- etiqueta mal puesta dejaría todo el histórico ya recogido con la etiqueta
-- vieja, y sería incorregible.
--
-- No es hipotético: el mapeo de este curso estuvo VACÍO hasta el 2026-09-18,
-- con 686 intentos ya recogidos. Al cargarlo, los 686 quedaron clasificados
-- retroactivamente sin reprocesar nada. Con la etiqueta dentro de cada fila,
-- habrían quedado huérfanos para siempre.
--
-- Idempotente: se puede aplicar las veces que haga falta.

-- ---------------------------------------------------------
-- 1. Qué microcompetencias instrumenta el AVA
-- ---------------------------------------------------------
-- El catálogo tiene las siete del microcurrículo, pero el AVA solo puede medir
-- cuatro con trazas de actividad. Las otras tres se evalúan por autorreporte y
-- coevaluación (mCA14, mCA65) o no forman parte del diseño (mCC85), así que
-- darles un nivel a partir de fallos sería inventarse un dato.
--
-- Hace falta marcarlo en la base, no solo saberlo: hoy hay 6 ejercicios
-- etiquetados con I5 (mCA14), que está fuera de alcance, y el panel no tiene
-- forma de distinguirlos.
ALTER TABLE competencias
    ADD COLUMN IF NOT EXISTS en_alcance BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN competencias.en_alcance IS
    'TRUE si el AVA la instrumenta con trazas de actividad. Las demás se '
    'evalúan por autorreporte o coevaluación y no reciben nivel.';

-- I1=mCP17, I3=mCC87, I4=mCC103, I7=mCP88 (ver competencias.codigo_anterior).
UPDATE competencias SET en_alcance = TRUE  WHERE id IN ('I1', 'I3', 'I4', 'I7');
UPDATE competencias SET en_alcance = FALSE WHERE id IN ('I2', 'I5', 'I6');

-- ---------------------------------------------------------
-- 2. Como mucho dos competencias por ejercicio
-- ---------------------------------------------------------
-- Es una regla de diseño del curso: un ejercicio que dice medir cuatro cosas no
-- mide ninguna. Hoy se cumple (32 ejercicios con una, 15 con dos) pero nada la
-- forzaba, así que se podía romper sin que nadie se enterara hasta ver el panel.
--
-- Va como trigger y no como CHECK porque hay que contar filas hermanas, que un
-- CHECK no puede ver.
CREATE OR REPLACE FUNCTION competencias_por_ejercicio() RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT count(*) FROM ejercicio_competencias
         WHERE cuadernillo_id = NEW.cuadernillo_id
           AND exercise_id    = NEW.exercise_id) > 2 THEN
        RAISE EXCEPTION
            'El ejercicio %/% tendría más de 2 competencias. Un ejercicio que '
            'dice medir todo no mide nada: deja 1 o 2.',
            NEW.cuadernillo_id, NEW.exercise_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tope_competencias_por_ejercicio ON ejercicio_competencias;
CREATE CONSTRAINT TRIGGER tope_competencias_por_ejercicio
    AFTER INSERT OR UPDATE ON ejercicio_competencias
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION competencias_por_ejercicio();

-- ---------------------------------------------------------
-- 3. Las señales por estudiante y competencia
-- ---------------------------------------------------------
-- Es una VISTA, no una tabla: se calcula al consultar y por tanto nunca queda
-- desfasada, ni hace falta invalidarla cuando cambia el mapeo o llega un
-- intento nuevo. Con 16 estudiantes y ~700 intentos el coste es irrelevante.
--
-- Amplía errores_por_competencia (que ya agrupaba por estudiante) con lo que
-- faltaba para poder graduar: cuántos ejercicios VIO y cuántos RESOLVIÓ. Sin
-- eso solo se puede contar fallos, y contar fallos a secas castiga a quien más
-- trabaja.
--
-- Los intentos que solo ejecutaron la plantilla sin tocarla
-- (NotImplementedError) no cuentan: no son un intento, son "ejecuté la celda a
-- ver qué pasaba".
--
-- CORREGIDO antes de aplicar nada (2026-09-21). La primera versión de esta
-- vista descartaba el intento entero en cuanto llevara un NotImplementedError,
-- y medido contra los datos reales resultó estar mal el 89 % de las veces.
--
-- El motivo está en custom.js: el buffer de errores del ejercicio solo se vacía
-- cuando se consigue ENVIAR un intento (custom.js:352 y :370). El recorrido que
-- el propio cuadernillo le pide al alumno —ejecutar las celdas en orden— dispara
-- el NotImplementedError de la plantilla y lo deja en el buffer; cuando después
-- escribe su código y ejecuta la prueba, ese intento APROBADO arrastra el stub
-- viejo. En la base de producción eran 18 intentos aprobados, 16 de ellos sin un
-- solo error de verdad. De los 46 intentos que el criterio viejo descartaba,
-- solo 5 eran plantilla: los otros 41 eran trabajo real.
--
-- Criterio correcto: es plantilla si NO aprobó Y todos sus errores son
-- NotImplementedError. Aprobar prueba que escribió algo; un error real
-- conviviendo con el stub, también.
--
-- Este criterio es el mismo que usa EstudiantesRepository.Competencias, y tienen
-- que coincidir o dos secciones de la misma página se contradicen. NO es el de
-- Malentendidos(), que descarta en estricto a propósito porque allí la pregunta
-- es otra: qué concepto explicar, no cuánto cubrió el alumno.
CREATE OR REPLACE VIEW senales_competencia AS
WITH reales AS (
    SELECT a.course_id, a.student_id, a.cuadernillo_id, a.exercise_id,
           a.validation_result, a.received_at
      FROM exercise_attempts a
     WHERE a.validation_result = 'passed'
        OR EXISTS (SELECT 1 FROM attempt_errors e
                    WHERE e.attempt_id = a.id
                      AND e.error_type <> 'NotImplementedError')
        OR NOT EXISTS (SELECT 1 FROM attempt_errors e
                        WHERE e.attempt_id = a.id)
)
SELECT t.course_id,
       t.student_id,
       c.id                        AS competencia_id,
       c.codigo_anterior           AS codigo_oficial,
       c.descripcion,
       c.en_alcance,
       -- Cuántos ejercicios de esta competencia llegó a intentar de verdad.
       count(DISTINCT (t.cuadernillo_id, t.exercise_id))                    AS vistos,
       count(DISTINCT (t.cuadernillo_id, t.exercise_id))
           FILTER (WHERE t.validation_result = 'passed')                    AS resueltos,
       count(*)                                                             AS intentos,
       count(*) FILTER (WHERE t.validation_result = 'failed')               AS fallos,
       -- Un 'sin_validar' es que dejó errores y no llegó a ejecutar la prueba:
       -- se atascó y se rindió. No es lo mismo que fallar.
       --
       -- Se cuentan EJERCICIOS abandonados, no eventos: el volcado al cerrar la
       -- pestaña se dispara cada vez que el alumno cierra, y contar eventos
       -- repetía el error que el panel del alumno ya corrigió (recargar tres
       -- veces sumaba tres). Con AbandonosN3 = 3, tres cierres del mismo
       -- ejercicio bastaban para sacar de N3 a alguien que lo resolvió. Y si
       -- acabó resolviéndolo, no lo abandonó.
       count(DISTINCT (t.cuadernillo_id, t.exercise_id)) FILTER (
           WHERE t.validation_result = 'sin_validar'
             AND NOT EXISTS (SELECT 1 FROM reales r
                              WHERE r.course_id  = t.course_id
                                AND r.student_id = t.student_id
                                AND r.cuadernillo_id = t.cuadernillo_id
                                AND r.exercise_id    = t.exercise_id
                                AND r.validation_result = 'passed'))        AS abandonos,
       min(t.received_at)                                                   AS primer_intento,
       max(t.received_at)                                                   AS ultimo_intento
  FROM reales t
  JOIN ejercicio_competencias ec
         ON ec.cuadernillo_id = t.cuadernillo_id
        AND ec.exercise_id    = t.exercise_id
  JOIN competencias c ON c.id = ec.competencia_id
 GROUP BY t.course_id, t.student_id, c.id, c.codigo_anterior, c.descripcion, c.en_alcance;

COMMENT ON VIEW senales_competencia IS
    'Señales crudas por estudiante y competencia. El NIVEL no se calcula aquí: '
    'lo calcula el backend, porque los umbrales deben poder ajustarse sin '
    'migrar la base.';

-- ---------------------------------------------------------
-- 4. Cortes congelados
-- ---------------------------------------------------------
-- El nivel vivo sale de la vista de arriba y siempre refleja el estado de hoy.
-- Para el estudio pre/post hace falta además poder decir "así estaba el grupo
-- el 15 de septiembre", y eso una vista no lo da.
--
-- Se guarda el nivel JUNTO CON las señales que lo produjeron, a propósito: si
-- mañana se ajustan los umbrales, un corte viejo se puede RECALCULAR en vez de
-- quedar mintiendo con un número que ya no significa lo mismo.
--
-- No lo escribe ningún trigger ni ninguna consulta de lectura: lo escribe el
-- docente cuando decide congelar un corte. Un efecto secundario en un GET sería
-- imposible de auditar después.
CREATE TABLE IF NOT EXISTS corte_competencia (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id      VARCHAR(255) NOT NULL,
    student_id     VARCHAR(255) NOT NULL,
    competencia_id VARCHAR(8)   NOT NULL REFERENCES competencias(id),
    tomado_en      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    etiqueta       VARCHAR(60)  NOT NULL DEFAULT '',   -- 'pre', 'post', 'corte 1'…
    -- El nivel: 1, 2 o 3. NULL cuando no había evidencia suficiente, que es
    -- distinto de estar en N1 y hay que poder distinguirlo.
    nivel          SMALLINT     CHECK (nivel IS NULL OR nivel BETWEEN 1 AND 3),
    vistos         INTEGER      NOT NULL DEFAULT 0,
    resueltos      INTEGER      NOT NULL DEFAULT 0,
    intentos       INTEGER      NOT NULL DEFAULT 0,
    fallos         INTEGER      NOT NULL DEFAULT 0,
    abandonos      INTEGER      NOT NULL DEFAULT 0,
    -- Con qué umbrales se calculó. Sin esto, un corte viejo es irreproducible.
    umbrales       JSONB        NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (course_id, student_id, competencia_id, etiqueta)
);

CREATE INDEX IF NOT EXISTS idx_corte_curso
    ON corte_competencia (course_id, tomado_en DESC);
CREATE INDEX IF NOT EXISTS idx_corte_estudiante
    ON corte_competencia (course_id, student_id);
