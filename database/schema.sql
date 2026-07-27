-- =========================================================
-- Esquema PostgreSQL: telemetría de cuadernillos (Jupyter <-> backend)
-- =========================================================
-- No incluye tablas de curso/cuadernillo/ejercicio/estudiante como
-- entidades propias: esos datos viven en Moodle/nbgrader vía LTI.
-- Aquí solo se guardan los EVENTOS que llegan desde Jupyter.

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- para gen_random_uuid()

-- ---------------------------------------------------------
-- 1. Intentos de validación (un registro por cada intento)
-- ---------------------------------------------------------
CREATE TABLE exercise_attempts (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id          VARCHAR(255) NOT NULL,   -- context_id de LTI
    cuadernillo_id     VARCHAR(255) NOT NULL,
    exercise_id        VARCHAR(255) NOT NULL,
    student_id         VARCHAR(255) NOT NULL,   -- user_id de LTI
    attempt_at         TIMESTAMPTZ NOT NULL,    -- momento del intento (lo manda Jupyter)
    validation_result  VARCHAR(10) NOT NULL CHECK (validation_result IN ('passed', 'failed')),
    received_at        TIMESTAMPTZ NOT NULL DEFAULT now() -- momento en que llegó al backend
);

-- Consulta más común del panel: "dame los intentos de este ejercicio en este cuadernillo"
CREATE INDEX idx_attempts_lookup ON exercise_attempts (course_id, cuadernillo_id, exercise_id);
-- Consulta: "dame el historial de un estudiante"
CREATE INDEX idx_attempts_student ON exercise_attempts (student_id, cuadernillo_id);

-- ---------------------------------------------------------
-- 2. Errores capturados dentro de cada intento (1 a N por intento)
-- ---------------------------------------------------------
-- Se normaliza en tabla aparte (en vez de JSONB) porque el panel
-- necesita agrupar/contar por error_type de forma eficiente.
CREATE TABLE attempt_errors (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id    UUID NOT NULL REFERENCES exercise_attempts(id) ON DELETE CASCADE,
    cell_id       VARCHAR(255) NOT NULL,
    error_type    VARCHAR(255) NOT NULL,
    error_message TEXT NOT NULL,
    occurred_at   TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_attempt_errors_attempt ON attempt_errors (attempt_id);
-- Consulta: "cuáles son los errores más frecuentes en este ejercicio"
CREATE INDEX idx_attempt_errors_type ON attempt_errors (error_type);

-- ---------------------------------------------------------
-- 3. Calificación del cuadernillo (una sola vez por estudiante/cuadernillo)
-- ---------------------------------------------------------
CREATE TABLE cuadernillo_ratings (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id      VARCHAR(255) NOT NULL,
    cuadernillo_id VARCHAR(255) NOT NULL,
    student_id     VARCHAR(255) NOT NULL,
    submitted_at   TIMESTAMPTZ NOT NULL,
    rating         SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment        TEXT,
    UNIQUE (course_id, cuadernillo_id, student_id) -- un estudiante califica una sola vez
);

-- =========================================================
-- Vistas para el panel del profesor
-- =========================================================

-- Resumen por ejercicio: intentos totales, estudiantes que lo intentaron,
-- cuántos pasaron. Base para ver qué ejercicios son más difíciles.
CREATE VIEW exercise_stats AS
SELECT
    course_id,
    cuadernillo_id,
    exercise_id,
    COUNT(*)                                                       AS total_attempts,
    COUNT(DISTINCT student_id)                                     AS students_attempted,
    COUNT(*) FILTER (WHERE validation_result = 'passed')           AS passed_attempts,
    COUNT(DISTINCT student_id)
        FILTER (WHERE validation_result = 'passed')                AS students_passed
FROM exercise_attempts
GROUP BY course_id, cuadernillo_id, exercise_id;

-- Errores más comunes por ejercicio, ordenados por frecuencia.
CREATE VIEW exercise_common_errors AS
SELECT
    ea.course_id,
    ea.cuadernillo_id,
    ea.exercise_id,
    ae.error_type,
    COUNT(*) AS occurrences
FROM attempt_errors ae
JOIN exercise_attempts ea ON ea.id = ae.attempt_id
GROUP BY ea.course_id, ea.cuadernillo_id, ea.exercise_id, ae.error_type
ORDER BY occurrences DESC;

-- Calificación promedio por cuadernillo.
CREATE VIEW cuadernillo_rating_summary AS
SELECT
    course_id,
    cuadernillo_id,
    COUNT(*)         AS total_ratings,
    ROUND(AVG(rating), 2) AS avg_rating
FROM cuadernillo_ratings
GROUP BY course_id, cuadernillo_id;