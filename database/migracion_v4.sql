-- Migración al esquema v4 — la valoración del cuadernillo deja de ser una nota.
-- Idempotente: se puede correr dos veces sin romper nada.
--
-- Hasta aquí el alumno solo podía decir "4 de 5", y encima solo si aprobaba
-- TODOS los ejercicios (notebook/custom.js). Eso dejaba fuera justo a quien más
-- tiene que contar —el que se atascó y entregó a medias— y le daba al profesor
-- un número que no le dice qué cambiar la semana siguiente.
--
-- Se añaden dos preguntas de un toque y dos marcas que pone el servidor. La
-- regla que las eligió: no preguntar lo que la telemetría ya sabe. El sistema
-- ya mide cuántos intentos costó cada ejercicio y quién se atascó; lo que no
-- puede saber es cuánto tiempo le dedicó de verdad (incluido el que trabajó
-- fuera de Jupyter) ni POR QUÉ se frenó.
BEGIN;

ALTER TABLE cuadernillo_ratings
    -- 1=menos de 1h · 2=entre 1 y 2h · 3=entre 2 y 4h · 4=más de 4h.
    ADD COLUMN IF NOT EXISTS tiempo    SMALLINT CHECK (tiempo BETWEEN 1 AND 4),
    -- Lista cerrada: cada valor es una acción distinta del docente.
    ADD COLUMN IF NOT EXISTS freno     VARCHAR(24) CHECK (freno IN
        ('enunciado', 'concepto', 'sintaxis', 'error', 'tiempo', 'nada')),
    -- Si ya había entregado al valorar. Separa dos poblaciones que no se pueden
    -- promediar juntas: quien terminó y quien abandonó.
    ADD COLUMN IF NOT EXISTS entregado BOOLEAN,
    -- 'panel' o 'notebook': a las dos semanas dice por dónde valora la gente.
    ADD COLUMN IF NOT EXISTS origen    VARCHAR(16);

-- Todas admiten NULL a propósito: las valoraciones que ya existen no las
-- tienen, y el alumno puede contestar solo la primera pregunta e irse.
COMMENT ON COLUMN cuadernillo_ratings.rating IS
    'Cuánto siente el ESTUDIANTE que aprendió, de 1 a 5. No es una nota.';
COMMENT ON COLUMN cuadernillo_ratings.tiempo IS
    '1=<1h 2=1-2h 3=2-4h 4=>4h, en total, incluyendo lo hecho fuera de Jupyter.';
COMMENT ON COLUMN cuadernillo_ratings.freno IS
    'Lo que más lo frenó, lista cerrada. NULL=no contestó; nada=le fluyó.';
COMMENT ON COLUMN cuadernillo_ratings.entregado IS
    'Si al valorar ya había entregado. Separa el abandono al promediar.';

-- Se amplía la vista que ya existía. CREATE OR REPLACE solo deja AÑADIR
-- columnas al final, así que las cuatro primeras quedan como estaban.
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

-- Cuántas personas señalaron cada freno. Es la tabla que el docente mira para
-- decidir qué reescribir: no es lo mismo que no se entienda el enunciado
-- (reescribirlo) a que no sepan traducir a Python (más ejemplos en clase).
CREATE OR REPLACE VIEW cuadernillo_rating_frenos AS
SELECT course_id, cuadernillo_id, freno, COUNT(*) AS personas
FROM cuadernillo_ratings
WHERE freno IS NOT NULL
GROUP BY course_id, cuadernillo_id, freno;

COMMIT;
