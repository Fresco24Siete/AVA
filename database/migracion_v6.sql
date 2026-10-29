-- =============================================================================
-- Migración v6 — alinear la descripción de mCP17 con lo que el AVA mide
-- =============================================================================
--
-- Aplicada a producción el 2026-09-21 y en el bucle de servidor/instalar.sh
-- desde ese día. (La cabecera decía lo contrario hasta el 2026-09-23.)
--
-- EL PROBLEMA
--
-- mCP17 tiene dos definiciones que no dicen lo mismo:
--
--   El catálogo, sembrado en schema_v2.sql:102 y reafirmado en migracion_v2.sql
--     "Aplica conocimientos de álgebra lineal, cálculo diferencial e integral y
--      métodos numéricos para solucionar problemas mediante programación."
--
--   El encargo del curso, sección 2
--     "Aplicar conocimientos matemáticos para la solución de problemas usando
--      programación."
--
-- Con la primera, NINGUNA de las siete etiquetas mCP17 puestas es legítima: en
-- un primer curso de programación no hay álgebra lineal ni cálculo. Con la
-- segunda, calcular la tarifa de un parqueadero, aplicar un porcentaje de
-- descuento o corregir una media mal agrupada sí lo son.
--
-- Se etiquetó con la del encargo, que es la instrucción más reciente y
-- específica. Pero la descripción del catálogo es la que se pinta:
--
--   panelDocenteRepository.go:190  -> guía "Qué mide cada código" del docente
--   progresoRepository.go:127      -> panel del ESTUDIANTE, "Qué has aprendido"
--   panel_docente_bridge.py:848    -> la tarjeta con la barra de progreso
--
-- O sea: hoy la pantalla pone "álgebra lineal, cálculo diferencial e integral"
-- encima de un ejercicio sobre el recibo del parqueadero.
--
-- LAS DOS SALIDAS, Y HAY QUE ELEGIR UNA
--
--   a) Aplicar esta migración: la descripción pasa a decir lo que el AVA mide
--      de verdad, y las siete etiquetas quedan justificadas.
--   b) No aplicarla y quitar las siete etiquetas: mCP17 se queda sin evidencia,
--      como mCC103. El AVA mediría dos microcompetencias en vez de cuatro.
--
-- Lo que NO vale es dejarlo como está: etiquetas puestas y descripción que no
-- las respalda.
--
-- Ojo si se arregla a mano en la base: migracion_v2.sql:43-47 hace
-- ON CONFLICT (id) DO UPDATE SET descripcion = EXCLUDED.descripcion, así que
-- volver a pasar la v2 revierte el cambio. Por eso va como migración y por eso
-- tiene que aplicarse DESPUÉS de la v2.
--
-- Es un UPDATE de un texto. No toca etiquetas, ni intentos, ni notas: se puede
-- revertir con el UPDATE inverso, que queda escrito al final comentado.
-- =============================================================================

UPDATE competencias
   SET descripcion = 'Aplica conocimientos matemáticos para la solución de '
                     'problemas usando programación.'
 WHERE id = 'I1'
   AND descripcion LIKE 'Aplica conocimientos de álgebra lineal%';

COMMENT ON COLUMN competencias.descripcion IS
    'Lo que el panel le enseña al docente y al estudiante. Tiene que describir '
    'lo que los ejercicios etiquetados con esa competencia miden de verdad: si '
    'no, la pantalla afirma algo que el AVA no puede saber.';

-- Para revertir:
--
-- UPDATE competencias
--    SET descripcion = 'Aplica conocimientos de álgebra lineal, cálculo '
--                      'diferencial e integral y métodos numéricos para '
--                      'solucionar problemas mediante programación.'
--  WHERE id = 'I1';
