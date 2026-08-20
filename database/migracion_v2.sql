-- Migración al esquema v2 — competencias, notas y datos que se descartaban.
-- Idempotente: se puede correr dos veces sin romper nada.
--
-- Ver database/schema_v2.sql para el esquema completo comentado.
BEGIN;

-- 1. Columnas que el navegador YA enviaba y el backend descartaba.
ALTER TABLE exercise_attempts
    ADD COLUMN IF NOT EXISTS puntos_maximos SMALLINT,
    ADD COLUMN IF NOT EXISTS codigo_celda   VARCHAR(255),
    ADD COLUMN IF NOT EXISTS orden          SMALLINT;

-- 2. 'sin_validar': el alumno se atascó y cerró sin ejecutar la prueba.
--    El CHECK viejo lo rechazaba, así que ese evento se perdía siempre.
--
--    Postgres no deja cambiar el tipo de una columna de la que depende una
--    vista, y exercise_stats la usa. Hay que tirarla y volver a crearla; se
--    recrea idéntica salvo por la línea de abandonos, que ahora tiene sentido.
DROP VIEW IF EXISTS exercise_stats;

ALTER TABLE exercise_attempts
    ALTER COLUMN validation_result TYPE VARCHAR(12);
ALTER TABLE exercise_attempts
    DROP CONSTRAINT IF EXISTS exercise_attempts_validation_result_check;
ALTER TABLE exercise_attempts
    ADD CONSTRAINT exercise_attempts_validation_result_check
    CHECK (validation_result IN ('passed', 'failed', 'sin_validar'));

-- 3. Catálogo de los siete indicadores de aprendizaje del microcurrículo.
CREATE TABLE IF NOT EXISTS competencias (
    id              VARCHAR(8) PRIMARY KEY,
    codigo_anterior VARCHAR(16),
    descripcion     TEXT NOT NULL
);

INSERT INTO competencias (id, codigo_anterior, descripcion) VALUES
 ('I1','mCP17','Aplica conocimientos de álgebra lineal, cálculo diferencial e integral y métodos numéricos para solucionar problemas mediante programación.'),
 ('I2','mCC85','Identifica que la complejidad computacional de las soluciones algorítmicas puede generar impactos económicos y ambientales.'),
 ('I3','mCC87','Identifica variables, conceptos y aspectos relevantes de un problema para desarrollar algoritmos que permitan solucionarlo.'),
 ('I4','mCC103','Reconoce problemas de sistemas y organizaciones susceptibles de tratamiento algorítmico.'),
 ('I5','mCA14','Comunica efectivamente a distintas audiencias conceptos, problemas y propuestas de solución de ingeniería.'),
 ('I6','mCA65','Trabaja en equipo, establece objetivos y asume roles para planear y ejecutar actividades de solución de problemas.'),
 ('I7','mCP88','Investiga y selecciona fuentes confiables y relevantes para adquirir los conocimientos que necesita.')
ON CONFLICT (id) DO UPDATE
    SET descripcion = EXCLUDED.descripcion,
        codigo_anterior = EXCLUDED.codigo_anterior;

-- 4. Qué competencia evalúa cada ejercicio. NO lleva estudiante: es diseño del
--    curso. Por eso corregir una etiqueta corrige todo el histórico.
CREATE TABLE IF NOT EXISTS ejercicio_competencias (
    cuadernillo_id VARCHAR(255) NOT NULL,
    exercise_id    VARCHAR(255) NOT NULL,
    competencia_id VARCHAR(8)   NOT NULL REFERENCES competencias(id),
    PRIMARY KEY (cuadernillo_id, exercise_id, competencia_id)
);
CREATE INDEX IF NOT EXISTS idx_ejercicio_comp ON ejercicio_competencias (competencia_id);

-- 5. Nota del cuadernillo.
CREATE TABLE IF NOT EXISTS cuadernillo_notas (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id           VARCHAR(255) NOT NULL,
    cuadernillo_id      VARCHAR(255) NOT NULL,
    student_id          VARCHAR(255) NOT NULL,
    puntos_obtenidos    NUMERIC(6,2) NOT NULL,
    puntos_maximos      NUMERIC(6,2) NOT NULL,
    calificado_en       TIMESTAMPTZ  NOT NULL,
    origen              VARCHAR(20)  NOT NULL DEFAULT 'nbgrader',
    enviado_a_moodle_en TIMESTAMPTZ,
    UNIQUE (course_id, cuadernillo_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_notas_estudiante ON cuadernillo_notas (student_id, course_id);

-- 6. La consulta que responde la pregunta del trabajo de grado.
CREATE OR REPLACE VIEW errores_por_competencia AS
SELECT a.course_id, a.cuadernillo_id, a.student_id,
       ec.competencia_id, c.descripcion,
       COUNT(*)                                                     AS intentos_totales,
       COUNT(*) FILTER (WHERE a.validation_result = 'failed')       AS intentos_fallidos,
       COUNT(*) FILTER (WHERE a.validation_result = 'sin_validar')  AS abandonos,
       COUNT(e.id)                                                  AS errores
FROM exercise_attempts a
JOIN ejercicio_competencias ec
       ON ec.cuadernillo_id = a.cuadernillo_id
      AND ec.exercise_id    = a.exercise_id
JOIN competencias c ON c.id = ec.competencia_id
LEFT JOIN attempt_errors e ON e.attempt_id = a.id
GROUP BY 1, 2, 3, 4, 5;

-- 6b. Se recrea la vista que hubo que tirar para poder cambiar el tipo.
CREATE VIEW exercise_stats AS
SELECT
    course_id,
    cuadernillo_id,
    exercise_id,
    COUNT(*)                                                       AS total_attempts,
    COUNT(DISTINCT student_id)                                     AS students_attempted,
    COUNT(*) FILTER (WHERE validation_result = 'passed')           AS passed_attempts,
    COUNT(DISTINCT student_id)
        FILTER (WHERE validation_result = 'passed')                AS students_passed,
    -- Nuevo: cuántos se rindieron sin llegar a validar.
    COUNT(*) FILTER (WHERE validation_result = 'sin_validar')      AS abandonos
FROM exercise_attempts
GROUP BY course_id, cuadernillo_id, exercise_id;

-- 7. Aclarar el nombre que confunde: cuadernillo_ratings NO es una nota.
COMMENT ON TABLE cuadernillo_ratings IS
  'Valoración de 1 a 5 que el ESTUDIANTE le da al cuadernillo. No es una nota: la nota está en cuadernillo_notas.';
COMMENT ON TABLE cuadernillo_notas IS
  'Nota de cada estudiante por cuadernillo. origen=nbgrader es la oficial.';

COMMIT;
