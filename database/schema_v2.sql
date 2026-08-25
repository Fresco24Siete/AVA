-- =========================================================
-- Esquema PostgreSQL del AVA — versión 2
-- =========================================================
-- Amplía el esquema original para poder responder la pregunta que motiva el
-- trabajo de grado: EN QUÉ COMPETENCIA se atasca cada estudiante.
--
-- Los datos de curso, cuadernillo, ejercicio y estudiante no son entidades
-- propias: viven en Moodle y en nbgrader, y aquí se referencian por su código.
-- Lo que sí vive aquí son los EVENTOS y el MAPEO de diseño del curso.
--
-- Importable en drawSQL / dbdiagram.io.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------
-- 1. Intentos de validación                        [SE MODIFICA]
-- ---------------------------------------------------------
CREATE TABLE exercise_attempts (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id          VARCHAR(255) NOT NULL,   -- context_id de LTI
    cuadernillo_id     VARCHAR(255) NOT NULL,
    exercise_id        VARCHAR(255) NOT NULL,
    student_id         VARCHAR(255) NOT NULL,   -- user_id de LTI
    attempt_at         TIMESTAMPTZ  NOT NULL,
    -- 'sin_validar' es un tercer desenlace real, no un valor raro: lo manda
    -- custom.js al cerrar la pestana cuando el alumno dejo errores en un
    -- ejercicio SIN llegar a ejecutar la celda de prueba. Hasta ahora el CHECK
    -- y el backend lo rechazaban con 400, asi que ese evento se perdia -- y es
    -- precisamente la senal de abandono: se atasco y se rindio. Sin el, un
    -- alumno que lucho media hora y otro que ni abrio el ejercicio se ven igual.
    validation_result  VARCHAR(12)  NOT NULL
        CHECK (validation_result IN ('passed', 'failed', 'sin_validar')),
    received_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),

    -- NUEVAS: el navegador ya las envía y el backend las descartaba. Sin
    -- puntos_maximos no hay forma de calcular una nota desde la base.
    puntos_maximos     SMALLINT,
    codigo_celda       VARCHAR(255),            -- test_ejercicio_3
    orden              SMALLINT                 -- posición en el cuadernillo
);

CREATE INDEX idx_attempts_lookup  ON exercise_attempts (course_id, cuadernillo_id, exercise_id);
CREATE INDEX idx_attempts_student ON exercise_attempts (student_id, cuadernillo_id);

-- ---------------------------------------------------------
-- 2. Errores dentro de cada intento                [SIN CAMBIOS]
-- ---------------------------------------------------------
-- No necesita columna de competencia: se resuelve por JOIN. Ese es justo el
-- punto del diseño — ver la tabla 5.
CREATE TABLE attempt_errors (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id    UUID NOT NULL REFERENCES exercise_attempts(id) ON DELETE CASCADE,
    cell_id       VARCHAR(255) NOT NULL,
    error_type    VARCHAR(255) NOT NULL,
    error_message TEXT         NOT NULL,
    occurred_at   TIMESTAMPTZ  NOT NULL
);

CREATE INDEX idx_attempt_errors_attempt ON attempt_errors (attempt_id);
CREATE INDEX idx_attempt_errors_type    ON attempt_errors (error_type);

-- ---------------------------------------------------------
-- 3. Valoración del cuadernillo por el alumno      [SIN CAMBIOS]
-- ---------------------------------------------------------
-- OJO: esto NO es una nota. Es la opinión del estudiante sobre el cuadernillo,
-- de 1 a 5. La nota vive en cuadernillo_notas (tabla 6).
CREATE TABLE cuadernillo_ratings (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id      VARCHAR(255) NOT NULL,
    cuadernillo_id VARCHAR(255) NOT NULL,
    student_id     VARCHAR(255) NOT NULL,
    submitted_at   TIMESTAMPTZ  NOT NULL,
    -- Cuánto siente el ESTUDIANTE que aprendió. No es una nota.
    rating         SMALLINT     NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment        TEXT,
    -- Lo que la telemetría no puede saber: cuánto tiempo le dedicó de verdad
    -- (incluido fuera de Jupyter) y por qué se frenó. Ver migracion_v4.sql.
    tiempo         SMALLINT     CHECK (tiempo BETWEEN 1 AND 4),
    freno          VARCHAR(24)  CHECK (freno IN
        ('enunciado', 'concepto', 'sintaxis', 'error', 'tiempo', 'nada')),
    -- Las pone el servidor, no el alumno.
    entregado      BOOLEAN,
    origen         VARCHAR(16),
    UNIQUE (course_id, cuadernillo_id, student_id)
);

-- ---------------------------------------------------------
-- 4. Catálogo de competencias                            [NUEVA]
-- ---------------------------------------------------------
-- Los siete indicadores de aprendizaje del microcurrículo oficial. Existe para
-- que el panel muestre la formulación y no un código.
CREATE TABLE competencias (
    id              VARCHAR(8) PRIMARY KEY,      -- I1 … I7
    codigo_anterior VARCHAR(16),                 -- mCC87, mCP17 … (trazas viejas)
    descripcion     TEXT NOT NULL
);

-- El catálogo va sembrado aquí, no solo en la migración: una base creada desde
-- cero arrancaba con la tabla vacía y cargar-competencias fallaba por la clave
-- foránea de ejercicio_competencias, sin que nada lo explicara.
INSERT INTO competencias (id, codigo_anterior, descripcion) VALUES
 ('I1','mCP17','Aplica conocimientos de álgebra lineal, cálculo diferencial e integral y métodos numéricos para solucionar problemas mediante programación.'),
 ('I2','mCC85','Identifica que la complejidad computacional de las soluciones algorítmicas puede generar impactos económicos y ambientales.'),
 ('I3','mCC87','Identifica variables, conceptos y aspectos relevantes de un problema para desarrollar algoritmos que permitan solucionarlo.'),
 ('I4','mCC103','Reconoce problemas de sistemas y organizaciones susceptibles de tratamiento algorítmico.'),
 ('I5','mCA14','Comunica efectivamente a distintas audiencias conceptos, problemas y propuestas de solución de ingeniería.'),
 ('I6','mCA65','Trabaja en equipo, establece objetivos y asume roles para planear y ejecutar actividades de solución de problemas.'),
 ('I7','mCP88','Investiga y selecciona fuentes confiables y relevantes para adquirir los conocimientos que necesita.');

-- ---------------------------------------------------------
-- 5. Qué competencia evalúa cada ejercicio               [NUEVA]
-- ---------------------------------------------------------
-- La pieza clave. NO lleva estudiante: es diseño del curso, no dato de nadie.
--
-- Por eso la competencia no viaja en cada intento: si un ejercicio queda mal
-- etiquetado y se corrige en la semana 8, TODO el histórico se corrige solo,
-- porque la competencia se resuelve al consultar y no quedó congelada.
--
-- La clave compuesta permite que un ejercicio cubra varias competencias.
CREATE TABLE ejercicio_competencias (
    cuadernillo_id VARCHAR(255) NOT NULL,
    exercise_id    VARCHAR(255) NOT NULL,
    competencia_id VARCHAR(8)   NOT NULL REFERENCES competencias(id),
    PRIMARY KEY (cuadernillo_id, exercise_id, competencia_id)
);

CREATE INDEX idx_ejercicio_comp ON ejercicio_competencias (competencia_id);

-- ---------------------------------------------------------
-- 6. Nota del cuadernillo                                [NUEVA]
-- ---------------------------------------------------------
-- La nota real sale de nbgrader tras "Autograde". El UNIQUE permite recalificar
-- sin duplicar.
CREATE TABLE cuadernillo_notas (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id           VARCHAR(255) NOT NULL,
    cuadernillo_id      VARCHAR(255) NOT NULL,
    student_id          VARCHAR(255) NOT NULL,
    puntos_obtenidos    NUMERIC(6,2) NOT NULL,
    puntos_maximos      NUMERIC(6,2) NOT NULL,
    calificado_en       TIMESTAMPTZ  NOT NULL,
    -- 'nbgrader' es la nota oficial; 'provisional' la calculada de la
    -- telemetría, que el alumno puede ver antes de que el docente califique.
    -- Distinguirlas evita el reclamo de "el panel decía otra cosa".
    origen              VARCHAR(20)  NOT NULL DEFAULT 'nbgrader',
    enviado_a_moodle_en TIMESTAMPTZ,             -- devolución de notas por LTI
    UNIQUE (course_id, cuadernillo_id, student_id)
);

CREATE INDEX idx_notas_estudiante ON cuadernillo_notas (student_id, course_id);

-- ---------------------------------------------------------
-- 6b. Quién es cada estudiante                           [NUEVA, v3]
-- ---------------------------------------------------------
-- Lo registra el Hub en cada ingreso LTI (POST /internal/lti/ingreso). Sin
-- esto el panel del docente solo podía mostrar el user_id numérico. Guarda
-- también el sourcedid y la URL del servicio de resultados de Moodle, que solo
-- viajan en el lanzamiento del alumno y hacen falta para devolverle la nota.
CREATE TABLE estudiantes (
    course_id               VARCHAR(255) NOT NULL,   -- context_id de LTI
    student_id              VARCHAR(255) NOT NULL,   -- user_id de LTI
    nombre                  VARCHAR(255) NOT NULL DEFAULT '',
    email                   VARCHAR(255) NOT NULL DEFAULT '',
    usuario_hub             VARCHAR(255) NOT NULL DEFAULT '',
    rol                     VARCHAR(20)  NOT NULL DEFAULT 'estudiante',
    lis_result_sourcedid    TEXT,
    lis_outcome_service_url TEXT,
    primer_ingreso          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    ultimo_ingreso          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    ingresos                INTEGER      NOT NULL DEFAULT 1,
    PRIMARY KEY (course_id, student_id)
);

CREATE INDEX idx_estudiantes_curso ON estudiantes (course_id, ultimo_ingreso DESC);

-- ---------------------------------------------------------
-- 7. La consulta que justifica todo lo anterior
-- ---------------------------------------------------------
-- Responde "¿en qué competencia se está atascando?" sin necesidad de que exista
-- todavía ningún panel.
CREATE VIEW errores_por_competencia AS
SELECT a.course_id,
       a.cuadernillo_id,
       a.student_id,
       ec.competencia_id,
       c.descripcion,
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

-- ---------------------------------------------------------
-- 8. Vistas que venían del esquema v1
-- ---------------------------------------------------------
-- Estaban solo en schema.sql. Mientras el compose montaba el v1 como semilla no
-- se notaba; al pasar la semilla a este archivo, una base recreada nacía sin
-- ellas. Este archivo tiene que ser el esquema COMPLETO, no el delta.

CREATE OR REPLACE VIEW exercise_stats AS
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

CREATE OR REPLACE VIEW exercise_common_errors AS
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

CREATE OR REPLACE VIEW cuadernillo_rating_summary AS
SELECT
    course_id,
    cuadernillo_id,
    COUNT(*)                                   AS total_ratings,
    ROUND(AVG(rating), 2)                      AS avg_rating,
    ROUND(AVG(tiempo), 2)                      AS avg_tiempo,
    COUNT(tiempo)                              AS con_tiempo,
    COUNT(comment)                             AS con_comentario,
    COUNT(*) FILTER (WHERE entregado)          AS de_entregas,
    COUNT(*) FILTER (WHERE entregado IS FALSE) AS de_no_entregas
FROM cuadernillo_ratings
GROUP BY course_id, cuadernillo_id;

-- Cuántas personas señalaron cada freno: es lo que le dice al docente QUÉ
-- reescribir. No es lo mismo que no se entienda el enunciado a que no sepan
-- traducir la idea a Python.
CREATE OR REPLACE VIEW cuadernillo_rating_frenos AS
SELECT course_id, cuadernillo_id, freno, COUNT(*) AS personas
FROM cuadernillo_ratings
WHERE freno IS NOT NULL
GROUP BY course_id, cuadernillo_id, freno;
