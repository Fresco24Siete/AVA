-- ============================================================================
-- ESQUEMA DE BASE DE DATOS: TELEMETRÍA Y CALIFICACIONES JUPYTER / NBGRADER
-- ============================================================================

-- Habilitar extensión para UUIDs (opcional pero muy útil si usas UUIDs en PKs)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. TABLAS PRINCIPALES (Entidades del Sistema)
-- ----------------------------------------------------------------------------

-- Cursos registrados desde LTI o JupyterHub
CREATE TABLE IF NOT EXISTS cursos (
    curso_id VARCHAR(100) PRIMARY KEY, -- LTI context_id
    nombre VARCHAR(255),
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Estudiantes autenticados mediante LTI
CREATE TABLE IF NOT EXISTS estudiantes (
    estudiante_id VARCHAR(100) PRIMARY KEY, -- LTI user_id
    nombre_completo VARCHAR(255),
    correo VARCHAR(255),
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cuadernillos (Assignments) por Curso
CREATE TABLE IF NOT EXISTS cuadernillos (
    cuadernillo_codigo VARCHAR(100) NOT NULL, -- ej: "semana_1"
    curso_id VARCHAR(100) NOT NULL REFERENCES cursos(curso_id) ON DELETE CASCADE,
    titulo VARCHAR(255),
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (curso_id, cuadernillo_codigo)
);

-- Ejercicios que forman parte de un cuadernillo (Llave de negocio: codigo_ejercicio)
CREATE TABLE IF NOT EXISTS ejercicios (
    curso_id VARCHAR(100) NOT NULL,
    cuadernillo_codigo VARCHAR(100) NOT NULL,
    codigo_ejercicio VARCHAR(100) NOT NULL, -- ej: "ejercicio_1" (sin prefijo test_)
    codigo_celda VARCHAR(100),               -- ej: "test_ejercicio_1"
    orden INT,
    descripcion TEXT,
    puntos_maximos NUMERIC(5, 2) DEFAULT 0.00,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (curso_id, cuadernillo_codigo, codigo_ejercicio),
    FOREIGN KEY (curso_id, cuadernillo_codigo) REFERENCES cuadernillos(curso_id, cuadernillo_codigo) ON DELETE CASCADE
);


-- ----------------------------------------------------------------------------
-- 2. TABLAS DE TELEMETRÍA EN VIVO (/public/metrics/evento)
-- ----------------------------------------------------------------------------

-- Registro detallado de ejecuciones de celdas de prueba en tiempo real
CREATE TABLE IF NOT EXISTS telemetria_ejercicios (
    id BIGSERIAL PRIMARY KEY,
    -- Identidad e Identificadores
    estudiante_id VARCHAR(100) NOT NULL REFERENCES estudiantes(estudiante_id) ON DELETE CASCADE,
    curso_id VARCHAR(100) NOT NULL,
    cuadernillo_codigo VARCHAR(100) NOT NULL,
    codigo_ejercicio VARCHAR(100) NOT NULL,
    codigo_celda VARCHAR(100) NOT NULL,
    
    -- Métricas de la Ejecución
    orden INT,
    puntos_maximos NUMERIC(5, 2),
    descripcion TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    primer_intento TIMESTAMP WITH TIME ZONE,
    num_intentos INT DEFAULT 1,
    duracion_segundos NUMERIC(10, 3),
    exito BOOLEAN NOT NULL,
    
    -- Traza de Errores
    tipo_error VARCHAR(100),
    mensaje TEXT,
    traceback TEXT,
    
    -- Metadatos adicionales creados al recibir
    recibido_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (curso_id, cuadernillo_codigo, codigo_ejercicio) 
        REFERENCES ejercicios(curso_id, cuadernillo_codigo, codigo_ejercicio) ON DELETE CASCADE
);

-- Registro de intentos completados enviados por el frontend
CREATE TABLE IF NOT EXISTS intentos_cuadernillo (
    id BIGSERIAL PRIMARY KEY,
    estudiante_id VARCHAR(100) NOT NULL REFERENCES estudiantes(estudiante_id) ON DELETE CASCADE,
    curso_id VARCHAR(100) NOT NULL,
    cuadernillo_codigo VARCHAR(100) NOT NULL,
    estado VARCHAR(50) NOT NULL, -- ej: "terminado"
    fecha_fin TIMESTAMP WITH TIME ZONE NOT NULL,
    puntaje_total NUMERIC(5, 2),
    puntaje_maximo NUMERIC(5, 2),
    recibido_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (curso_id, cuadernillo_codigo) 
        REFERENCES cuadernillos(curso_id, cuadernillo_codigo) ON DELETE CASCADE,
    -- Restricción opcional si deseas forzar la idempotencia por DB (1 intento por alumno/cuadernillo):
    CONSTRAINT unique_intento_estudiante UNIQUE (curso_id, cuadernillo_codigo, estudiante_id)
);


-- ----------------------------------------------------------------------------
-- 3. TABLAS DE NOTAS OFICIALES NBGRADER (/internal/metrics)
-- ----------------------------------------------------------------------------

-- Cabecera de la entrega oficial evaluada por nbgrader
CREATE TABLE IF NOT EXISTS notas_oficiales_cuadernillo (
    id BIGSERIAL PRIMARY KEY,
    curso_id VARCHAR(100) NOT NULL,
    cuadernillo_codigo VARCHAR(100) NOT NULL,
    estudiante_id VARCHAR(100) NOT NULL REFERENCES estudiantes(estudiante_id) ON DELETE CASCADE,
    estado VARCHAR(50) NOT NULL,
    fecha_fin TIMESTAMP WITH TIME ZONE,
    puntaje_total NUMERIC(5, 2) NOT NULL,
    puntaje_maximo NUMERIC(5, 2) NOT NULL,
    exportado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (curso_id, cuadernillo_codigo) 
        REFERENCES cuadernillos(curso_id, cuadernillo_codigo) ON DELETE CASCADE,
    -- Un estudiante solo tiene un registro oficial final por cuadernillo (actualizable mediante UPSERT)
    CONSTRAINT unique_nota_oficial UNIQUE (curso_id, cuadernillo_codigo, estudiante_id)
);

-- Detalle por ejercicio dentro de la nota oficial nbgrader
CREATE TABLE IF NOT EXISTS notas_oficiales_ejercicios (
    id BIGSERIAL PRIMARY KEY,
    nota_cuadernillo_id BIGINT NOT NULL REFERENCES notas_oficiales_cuadernillo(id) ON DELETE CASCADE,
    codigo_ejercicio VARCHAR(100) NOT NULL,
    codigo_celda VARCHAR(100) NOT NULL,
    orden INT,
    descripcion TEXT,
    puntos_obtenidos NUMERIC(5, 2) NOT NULL,
    puntos_maximos NUMERIC(5, 2) NOT NULL,
    aprobado BOOLEAN NOT NULL
);


-- ----------------------------------------------------------------------------
-- 4. ÍNDICES PARA CONSULTAS Y RENDIMIENTO
-- ----------------------------------------------------------------------------

-- Índices para consultar telemetría rápidamente en dashboards / backend
CREATE INDEX IF NOT EXISTS idx_telemetria_estudiante ON telemetria_ejercicios (estudiante_id);
CREATE INDEX IF NOT EXISTS idx_telemetria_cuadernillo ON telemetria_ejercicios (curso_id, cuadernillo_codigo);
CREATE INDEX IF NOT EXISTS idx_telemetria_ejercicio_clave ON telemetria_ejercicios (curso_id, cuadernillo_codigo, codigo_ejercicio);
CREATE INDEX IF NOT EXISTS idx_telemetria_timestamp ON telemetria_ejercicios (timestamp DESC);

-- Índice para cruzar la nota oficial con la telemetría del alumno
CREATE INDEX IF NOT EXISTS idx_notas_estudiante_cuadernillo ON notas_oficiales_cuadernillo (curso_id, cuadernillo_codigo, estudiante_id);