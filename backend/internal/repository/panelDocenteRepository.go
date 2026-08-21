package repository

import (
	"github.com/jmoiron/sqlx"
)

// PanelDocenteRepository responde las preguntas que se hace quien da la clase:
// dónde se atasca el grupo, qué error se repite, quién se está quedando atrás.
//
// Todas las consultas son agregadas y por curso. Ninguna es por alumno: con 25
// estudiantes y 16 semanas, una consulta por persona en cada carga de página
// convierte el panel en la parte lenta del AVA.
//
// # El stub no es un fallo
//
// nbgrader deja en cada celda de solución un `raise NotImplementedError`. El
// alumno lo dispara con solo recorrer el cuadernillo de arriba abajo con
// Shift+Enter, que es literalmente lo que el material le pide hacer. Hoy son la
// mitad de los errores registrados.
//
// Contarlos como dificultad convierte el ranking de «ejercicios que cuestan» en
// el ranking de «ejercicios que más gente abrió», que no sirve para decidir nada.
// Por eso todas las consultas de abajo separan:
//
//	stub = true   -> ni siquiera escribió la respuesta. No cuenta.
//	stub = false y falló -> escribió algo y no le sale. Esto sí es dificultad.
type PanelDocenteRepository struct {
	db *sqlx.DB
}

func NewPanelDocenteRepository(db *sqlx.DB) *PanelDocenteRepository {
	return &PanelDocenteRepository{db: db}
}

// intentosReales es la base de casi todo: cada intento con su marca de stub.
const intentosReales = `
	WITH t AS (
	    SELECT a.id, a.student_id, a.cuadernillo_id, a.exercise_id,
	           a.validation_result, a.attempt_at,
	           EXISTS (SELECT 1 FROM attempt_errors e
	                    WHERE e.attempt_id = a.id
	                      AND e.error_type = 'NotImplementedError') AS stub
	      FROM exercise_attempts a
	     WHERE a.course_id = $1
	)`

type ResumenCuadernilloCurso struct {
	CuadernilloID  string `db:"cuadernillo_id" json:"cuadernillo_id"`
	Alumnos        int    `db:"alumnos" json:"alumnos_con_actividad"`
	IntentosReales int    `db:"intentos_reales" json:"intentos_reales"`
	Ejercicios     int    `db:"ejercicios" json:"ejercicios_distintos"`
}

func (r *PanelDocenteRepository) PorCuadernillo(curso string) ([]ResumenCuadernilloCurso, error) {
	var salida []ResumenCuadernilloCurso
	err := r.db.Select(&salida, intentosReales+`
		SELECT cuadernillo_id,
		       COUNT(DISTINCT student_id)                    AS alumnos,
		       COUNT(*) FILTER (WHERE NOT stub)              AS intentos_reales,
		       COUNT(DISTINCT exercise_id)                   AS ejercicios
		  FROM t
		 GROUP BY cuadernillo_id
		 ORDER BY cuadernillo_id`, curso)
	return salida, err
}

type DificultadEjercicio struct {
	CuadernilloID string `db:"cuadernillo_id" json:"cuadernillo_id"`
	EjercicioID   string `db:"exercise_id" json:"exercise_id"`
	LoIntentaron  int    `db:"lo_intentaron" json:"alumnos_que_lo_intentaron"`
	LoResolvieron int    `db:"lo_resolvieron" json:"alumnos_que_lo_resolvieron"`
	Atascados     int    `db:"atascados" json:"alumnos_atascados"`
	AMedias       int    `db:"a_medias" json:"alumnos_a_medias"`
}

// PorEjercicio: dónde se atasca el grupo.
//
// «Atascado» es quien escribió una respuesta, falló, y nunca llegó a pasar. No
// entra quien solo ejecutó la celda vacía, ni quien acabó resolviéndolo.
func (r *PanelDocenteRepository) PorEjercicio(curso string) ([]DificultadEjercicio, error) {
	var salida []DificultadEjercicio
	err := r.db.Select(&salida, intentosReales+`,
	    porAlumno AS (
	        SELECT cuadernillo_id, exercise_id, student_id,
	               bool_or(validation_result = 'passed')                  AS paso,
	               bool_or(validation_result = 'failed' AND NOT stub)     AS intento_real,
	               bool_or(validation_result = 'sin_validar' AND NOT stub) AS a_medias
	          FROM t
	         GROUP BY cuadernillo_id, exercise_id, student_id
	    )
		SELECT cuadernillo_id, exercise_id,
		       COUNT(*) FILTER (WHERE intento_real OR paso)          AS lo_intentaron,
		       COUNT(*) FILTER (WHERE paso)                          AS lo_resolvieron,
		       COUNT(*) FILTER (WHERE intento_real AND NOT paso)     AS atascados,
		       COUNT(*) FILTER (WHERE a_medias AND NOT paso)         AS a_medias
		  FROM porAlumno
		 GROUP BY cuadernillo_id, exercise_id
		HAVING COUNT(*) FILTER (WHERE intento_real OR paso) > 0
		 ORDER BY atascados DESC, cuadernillo_id, exercise_id`, curso)
	return salida, err
}

type CompetenciaCurso struct {
	CompetenciaID string `db:"competencia_id" json:"competencia_id"`
	Descripcion   string `db:"descripcion" json:"descripcion"`
	Ejercicios    int    `db:"ejercicios" json:"ejercicios_disenados"`
	Alumnos       int    `db:"alumnos" json:"alumnos_con_actividad"`
	Resolvieron   int    `db:"resolvieron" json:"alumnos_que_resolvieron_alguno"`
}

// PorCompetencia sale del catálogo, no de la telemetría: una competencia para la
// que aún no se ha diseñado ningún ejercicio tiene que aparecer en cero, no
// desaparecer. Que I7 no tenga evidencia es justo lo que el docente necesita ver.
func (r *PanelDocenteRepository) PorCompetencia(curso string) ([]CompetenciaCurso, error) {
	var salida []CompetenciaCurso
	err := r.db.Select(&salida, `
		SELECT c.id AS competencia_id, c.descripcion,
		       COUNT(DISTINCT (ec.cuadernillo_id, ec.exercise_id))   AS ejercicios,
		       COUNT(DISTINCT a.student_id)                          AS alumnos,
		       COUNT(DISTINCT a.student_id) FILTER (
		           WHERE a.validation_result = 'passed')             AS resolvieron
		  FROM competencias c
		  LEFT JOIN ejercicio_competencias ec ON ec.competencia_id = c.id
		  LEFT JOIN exercise_attempts a
		         ON a.cuadernillo_id = ec.cuadernillo_id
		        AND a.exercise_id    = ec.exercise_id
		        AND a.course_id      = $1
		 GROUP BY c.id, c.descripcion
		 ORDER BY c.id`, curso)
	return salida, err
}

type Malentendido struct {
	CuadernilloID string `db:"cuadernillo_id" json:"cuadernillo_id"`
	EjercicioID   string `db:"exercise_id" json:"exercise_id"`
	Tipo          string `db:"error_type" json:"error_type"`
	Mensaje       string `db:"mensaje" json:"mensaje"`
	Alumnos       int    `db:"alumnos" json:"alumnos"`
	Veces         int    `db:"veces" json:"veces"`
}

// Malentendidos: el mismo error, en varias personas. Es la lista de la que sale
// «esto lo explico otra vez el lunes».
//
// Se agrupa por mensaje y no solo por tipo: diez AssertionError distintos son
// diez cosas distintas, y el mensaje de una prueba de nbgrader es la frase que
// el docente escribió para explicar qué se esperaba.
func (r *PanelDocenteRepository) Malentendidos(curso string) ([]Malentendido, error) {
	var salida []Malentendido
	err := r.db.Select(&salida, `
		SELECT a.cuadernillo_id, a.exercise_id, e.error_type,
		       left(e.error_message, 180)      AS mensaje,
		       COUNT(DISTINCT a.student_id)    AS alumnos,
		       COUNT(*)                        AS veces
		  FROM attempt_errors e
		  JOIN exercise_attempts a ON a.id = e.attempt_id
		 WHERE a.course_id = $1
		   AND e.error_type <> 'NotImplementedError'
		 GROUP BY a.cuadernillo_id, a.exercise_id, e.error_type,
		          left(e.error_message, 180)
		 ORDER BY COUNT(DISTINCT a.student_id) DESC, COUNT(*) DESC
		 LIMIT 15`, curso)
	return salida, err
}

type AlumnoEnRiesgo struct {
	EstudianteID string  `db:"student_id" json:"student_id"`
	Resueltos    int     `db:"resueltos" json:"ejercicios_resueltos"`
	Atascados    int     `db:"atascados" json:"ejercicios_atascados"`
	AMedias      int     `db:"a_medias" json:"ejercicios_a_medias"`
	UltimaHoras  float64 `db:"ultima_horas" json:"horas_desde_ultima_actividad"`
}

// EnRiesgo: quien lo intenta y no le sale. No es una lista de vagos —quien no ha
// entrado no aparece aquí, porque de ese no hay nada que medir— sino de gente
// que está peleando sola.
func (r *PanelDocenteRepository) EnRiesgo(curso string) ([]AlumnoEnRiesgo, error) {
	var salida []AlumnoEnRiesgo
	err := r.db.Select(&salida, intentosReales+`,
	    porAlumno AS (
	        SELECT student_id, cuadernillo_id, exercise_id,
	               bool_or(validation_result = 'passed')                   AS paso,
	               bool_or(validation_result = 'failed' AND NOT stub)      AS intento_real,
	               bool_or(validation_result = 'sin_validar' AND NOT stub) AS a_medias,
	               max(attempt_at)                                         AS ultima
	          FROM t
	         GROUP BY student_id, cuadernillo_id, exercise_id
	    )
		SELECT student_id,
		       COUNT(*) FILTER (WHERE paso)                        AS resueltos,
		       COUNT(*) FILTER (WHERE intento_real AND NOT paso)   AS atascados,
		       COUNT(*) FILTER (WHERE a_medias AND NOT paso)       AS a_medias,
		       EXTRACT(EPOCH FROM (now() - max(ultima))) / 3600.0  AS ultima_horas
		  FROM porAlumno
		 GROUP BY student_id
		HAVING COUNT(*) FILTER (WHERE intento_real AND NOT paso) > 0
		    OR COUNT(*) FILTER (WHERE a_medias AND NOT paso) > 0
		 ORDER BY 3 DESC, 4 DESC
		 LIMIT 10`, curso)
	return salida, err
}

type SaludDato struct {
	Intentos       int     `db:"intentos" json:"intentos_registrados"`
	Alumnos        int     `db:"alumnos" json:"alumnos_con_telemetria"`
	UltimoEvento   *string `db:"ultimo_evento" json:"ultimo_evento"`
	Relaciones     int     `db:"relaciones" json:"relaciones_competencia"`
	SinCompetencia int     `db:"sin_competencia" json:"ejercicios_sin_competencia"`
}

// Salud: si el panel muestra ceros, esto dice si es que nadie ha trabajado o es
// que el dato no está llegando. Sin esta sección, un fallo de la telemetría se
// lee como «mis estudiantes no hacen nada».
func (r *PanelDocenteRepository) Salud(curso string) (SaludDato, error) {
	var s SaludDato
	err := r.db.Get(&s, `
		SELECT (SELECT COUNT(*) FROM exercise_attempts WHERE course_id = $1) AS intentos,
		       (SELECT COUNT(DISTINCT student_id) FROM exercise_attempts
		         WHERE course_id = $1)                                        AS alumnos,
		       (SELECT to_char(max(received_at), 'YYYY-MM-DD"T"HH24:MI:SSZ')
		          FROM exercise_attempts WHERE course_id = $1)                AS ultimo_evento,
		       (SELECT COUNT(*) FROM ejercicio_competencias)                  AS relaciones,
		       (SELECT COUNT(*) FROM (
		            SELECT DISTINCT a.cuadernillo_id, a.exercise_id
		              FROM exercise_attempts a
		             WHERE a.course_id = $1
		               AND NOT EXISTS (
		                   SELECT 1 FROM ejercicio_competencias ec
		                    WHERE ec.cuadernillo_id = a.cuadernillo_id
		                      AND ec.exercise_id    = a.exercise_id)
		        ) x)                                                          AS sin_competencia`,
		curso)
	return s, err
}
