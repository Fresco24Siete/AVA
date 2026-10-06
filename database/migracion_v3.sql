-- Migración al esquema v3 — quién es cada estudiante.
-- Idempotente: se puede correr dos veces sin romper nada.
--
-- Hasta aquí la base guardaba intentos, errores, valoraciones y notas por
-- student_id (el user_id numérico de Moodle) y NADA más de la persona: el
-- panel del docente mostraba «3135». El Hub ve nombre y correo en cada
-- lanzamiento LTI; ahora los registra aquí (POST /internal/lti/ingreso).
--
-- De paso guarda lo que la devolución de notas a Moodle va a necesitar: el
-- lis_result_sourcedid del alumno y la URL del servicio de resultados, que
-- solo viajan en su lanzamiento y el docente no tiene cómo ver.
BEGIN;

CREATE TABLE IF NOT EXISTS estudiantes (
    course_id               VARCHAR(255) NOT NULL,   -- context_id de LTI
    student_id              VARCHAR(255) NOT NULL,   -- user_id de LTI
    nombre                  VARCHAR(255) NOT NULL DEFAULT '',
    email                   VARCHAR(255) NOT NULL DEFAULT '',
    usuario_hub             VARCHAR(255) NOT NULL DEFAULT '',  -- el nombre en JupyterHub (el correo)
    rol                     VARCHAR(20)  NOT NULL DEFAULT 'estudiante',  -- estudiante | instructor
    lis_result_sourcedid    TEXT,
    lis_outcome_service_url TEXT,
    primer_ingreso          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    ultimo_ingreso          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    ingresos                INTEGER      NOT NULL DEFAULT 1,
    PRIMARY KEY (course_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_estudiantes_curso ON estudiantes (course_id, ultimo_ingreso DESC);

COMMENT ON TABLE estudiantes IS
  'Quién es cada student_id: lo registra el Hub en cada ingreso LTI. rol=instructor para el docente.';

COMMIT;
