-- Borra los intentos de prueba deliberados hechos durante el desarrollo.
-- Va APARTE de la migración a propósito: borrar datos nunca debe ser un efecto
-- secundario de aplicar un cambio de esquema.
BEGIN;
DELETE FROM exercise_attempts
 WHERE student_id LIKE 'PRUEBA%'
    OR received_at < '2026-08-16';   -- todo lo anterior al inicio del semestre
COMMIT;
