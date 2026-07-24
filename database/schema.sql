-- =============================================================================
-- ESQUEMA DE BASE DE DATOS POSTGRESQL - ECOSISTEMA AVA
-- Integración: LTI + JupyterHub + nbgrader + Backend Go
-- =============================================================================

-- Habilitar extensión para UUIDs si es necesario
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. ENTIDADES DOCENTES Y CURSOS (Gestionadas por Interfaz Web Frontend)
-- =============================================================================

CREATE TABLE IF NOT EXISTS profesor (
    profesor_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo        varchar(50) UNIQUE NOT NULL,
    password_hash text NOT NULL,
    creado_en     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cursos (
    curso_id      int PRIMARY KEY,
    nombre_curso  varchar(150) NOT NULL,
    profesor_id   uuid REFERENCES profesor(profesor_id) ON DELETE SET NULL,
    creado_en     timestamptz NOT NULL DEFAULT now()
);

-- =============================================================================
-- 2. ESTUDIANTES (Poblados dinámicamente desde LTI Launch)
-- =============================================================================

CREATE TABLE IF NOT EXISTS estudiantes (
    estudiante_id   varchar(255) PRIMARY KEY, -- Proviene de 'user_id' de LTI
    nombre_completo varchar(150) NOT NULL,
    correo          varchar(150),
    curso_id        int REFERENCES cursos(curso_id) ON DELETE CASCADE,
    creado_en       timestamptz NOT NULL DEFAULT now(),
    actualizado_en  timestamptz NOT NULL DEFAULT now()
);

-- Tabla intermedia opcional si un estudiante se matricula en múltiples cursos
CREATE TABLE IF NOT EXISTS estudiante_curso (
    estudiante_id varchar(255) REFERENCES estudiantes(estudiante_id) ON DELETE CASCADE,
    curso_id      int REFERENCES cursos(curso_id) ON DELETE CASCADE,
    registrado_en timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (estudiante_id, curso_id)
);

-- =============================================================================
-- 3. PLANTILLAS DE CUADERNILLOS Y EJERCICIOS (Definición de Contenidos)
-- =============================================================================

CREATE TABLE IF NOT EXISTS cuadernillo (
    cuadernillo_id smallserial PRIMARY KEY,
    codigo         varchar(100) NOT NULL,    -- Identificador en nbgrader (ej. 'cuadernillo_ejercicios')
    nombre         varchar(150) NOT NULL,
    curso_id       int REFERENCES cursos(curso_id) ON DELETE CASCADE,
    activo         boolean NOT NULL DEFAULT false, -- Indica el cuadernillo activo para LTI
    creado_en      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (curso_id, codigo)
);

-- REGLA DE NEGOCIO: Solo un cuadernillo puede estar activo a la vez por cada curso
CREATE UNIQUE INDEX IF NOT EXISTS idx_cuadernillo_activo 
ON cuadernillo (curso_id) 
WHERE (activo = true);

CREATE TABLE IF NOT EXISTS ejercicio (
    ejercicio_id   smallserial PRIMARY KEY,
    cuadernillo_id smallint REFERENCES cuadernillo(cuadernillo_id) ON DELETE CASCADE,
    codigo_celda   varchar(100) NOT NULL,    -- grade_id de nbgrader (ej. 'ejercicio_1')
    descripcion    varchar(255),
    puntos_maximos smallint NOT NULL DEFAULT 1,
    orden          smallint NOT NULL DEFAULT 1,
    UNIQUE (cuadernillo_id, codigo_celda)
);

-- =============================================================================
-- 4. INSTANCIAS DE EJECUCIÓN (Métricas de Intentos por Estudiante)
-- =============================================================================

CREATE TABLE IF NOT EXISTS intento_cuadernillo (
    intento_id     bigserial PRIMARY KEY,
    cuadernillo_id smallint REFERENCES cuadernillo(cuadernillo_id) ON DELETE CASCADE,
    estudiante_id  varchar(255) REFERENCES estudiantes(estudiante_id) ON DELETE CASCADE,
    estado         varchar(20) NOT NULL DEFAULT 'en_progreso'
                   CHECK (estado IN ('en_progreso', 'terminado')),
    fecha_inicio   timestamptz NOT NULL DEFAULT now(),
    fecha_fin      timestamptz,
    puntaje_total  smallint DEFAULT 0,
    puntaje_maximo smallint DEFAULT 0,
    creado_en      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (cuadernillo_id, estudiante_id)
);

CREATE TABLE IF NOT EXISTS resultado_ejercicio (
    resultado_id      bigserial PRIMARY KEY,
    intento_id        bigint REFERENCES intento_cuadernillo(intento_id) ON DELETE CASCADE,
    ejercicio_id      smallint REFERENCES ejercicio(ejercicio_id) ON DELETE CASCADE,
    aprobado          boolean NOT NULL DEFAULT false,
    puntos_obtenidos  smallint NOT NULL DEFAULT 0,
    num_intentos      smallint NOT NULL DEFAULT 1,
    duracion_segundos numeric(10,2) DEFAULT 0,
    actualizado_en    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (intento_id, ejercicio_id)
);

-- =============================================================================
-- 5. TRAZABILIDAD DE ERRORES (Telemetría de Fallos por Celda)
-- =============================================================================

CREATE TABLE IF NOT EXISTS error (
    error_id     bigserial PRIMARY KEY,
    resultado_id bigint REFERENCES resultado_ejercicio(resultado_id) ON DELETE CASCADE,
    tipo_error   text NOT NULL,              -- Ej: 'AssertionError', 'ZeroDivisionError'
    mensaje      text,                       -- Mensaje limpio de la excepción
    traceback    text,                       -- Traceback completo si está disponible
    fecha        timestamptz NOT NULL DEFAULT now()
);

-- =============================================================================
-- ÍNDICES PARA OPTIMIZACIÓN DE CONSULTAS Y REPORTES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_estudiantes_curso ON estudiantes(curso_id);
CREATE INDEX IF NOT EXISTS idx_intento_estudiante ON intento_cuadernillo(estudiante_id);
CREATE INDEX IF NOT EXISTS idx_intento_estado ON intento_cuadernillo(estado);
CREATE INDEX IF NOT EXISTS idx_resultado_intento ON resultado_ejercicio(intento_id);
CREATE INDEX IF NOT EXISTS idx_error_resultado ON error(resultado_id);
