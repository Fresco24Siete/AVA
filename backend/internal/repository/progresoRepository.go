package repository

import "github.com/jmoiron/sqlx"

type ProgresoRepository struct {
	db *sqlx.DB
}

func NewProgresoRepository(db *sqlx.DB) *ProgresoRepository {
	return &ProgresoRepository{db: db}
}

// ResumenCuadernillo es lo que el alumno ve de cada cuadernillo.
type ResumenCuadernillo struct {
	CuadernilloID   string   `db:"cuadernillo_id" json:"cuadernillo_id"`
	EjerciciosOK    int      `db:"ejercicios_ok" json:"ejercicios_resueltos"`
	EjerciciosVistos int     `db:"ejercicios_vistos" json:"ejercicios_intentados"`
	Intentos        int      `db:"intentos" json:"intentos"`
	Abandonos       int      `db:"abandonos" json:"abandonos"`
	PuntosObtenidos *float64 `db:"puntos_obtenidos" json:"puntos_obtenidos,omitempty"`
	PuntosMaximos   *float64 `db:"puntos_maximos" json:"puntos_maximos,omitempty"`
	Origen          *string  `db:"origen" json:"origen_nota,omitempty"`
}

// ResumenCompetencia agrupa el desempeño por indicador de aprendizaje.
type ResumenCompetencia struct {
	CompetenciaID string `db:"competencia_id" json:"competencia_id"`
	Descripcion   string `db:"descripcion" json:"descripcion"`
	Resueltos     int    `db:"resueltos" json:"ejercicios_resueltos"`
	Intentados    int    `db:"intentados" json:"ejercicios_intentados"`
	Errores       int    `db:"errores" json:"errores"`
}

// PorCuadernillo: un ejercicio cuenta como resuelto si ALGUNA vez paso, aunque
// antes fallara. Es lo correcto pedagogicamente -- el alumno acabo sabiendolo --
// y ademas es como lo califica nbgrader.
func (r *ProgresoRepository) PorCuadernillo(estudiante, curso string) ([]ResumenCuadernillo, error) {
	var salida []ResumenCuadernillo
	// Se parte de la UNION de los cuadernillos que aparecen en los intentos y en
	// las notas, no solo de los intentos. Un alumno calificado sin telemetria
	// -- porque trabajo sin conexion, o porque fallo el envio -- tenia nota en la
	// base y el panel le mostraba una lista vacia.
	err := r.db.Select(&salida, `
		WITH suyos AS (
		    SELECT DISTINCT cuadernillo_id FROM exercise_attempts
		     WHERE student_id = $1 AND course_id = $2
		    UNION
		    SELECT DISTINCT cuadernillo_id FROM cuadernillo_notas
		     WHERE student_id = $1 AND course_id = $2
		)
		SELECT s.cuadernillo_id,
		       COUNT(DISTINCT a.exercise_id) FILTER (
		           WHERE a.validation_result = 'passed')          AS ejercicios_ok,
		       COUNT(DISTINCT a.exercise_id)                      AS ejercicios_vistos,
		       COUNT(a.id)                                        AS intentos,
		       COUNT(a.id) FILTER (
		           WHERE a.validation_result = 'sin_validar')     AS abandonos,
		       n.puntos_obtenidos, n.puntos_maximos, n.origen
		FROM suyos s
		LEFT JOIN exercise_attempts a
		       ON a.cuadernillo_id = s.cuadernillo_id
		      AND a.student_id     = $1 AND a.course_id = $2
		LEFT JOIN cuadernillo_notas n
		       ON n.cuadernillo_id = s.cuadernillo_id
		      AND n.student_id     = $1 AND n.course_id = $2
		GROUP BY s.cuadernillo_id, n.puntos_obtenidos, n.puntos_maximos, n.origen
		ORDER BY s.cuadernillo_id`, estudiante, curso)
	return salida, err
}

func (r *ProgresoRepository) PorCompetencia(estudiante, curso string) ([]ResumenCompetencia, error) {
	var salida []ResumenCompetencia
	err := r.db.Select(&salida, `
		SELECT ec.competencia_id, c.descripcion,
		       COUNT(DISTINCT a.exercise_id) FILTER (
		           WHERE a.validation_result = 'passed')  AS resueltos,
		       COUNT(DISTINCT a.exercise_id)              AS intentados,
		       COUNT(e.id)                                AS errores
		FROM exercise_attempts a
		JOIN ejercicio_competencias ec
		       ON ec.cuadernillo_id = a.cuadernillo_id
		      AND ec.exercise_id    = a.exercise_id
		JOIN competencias c ON c.id = ec.competencia_id
		LEFT JOIN attempt_errors e ON e.attempt_id = a.id
		WHERE a.student_id = $1 AND a.course_id = $2
		GROUP BY ec.competencia_id, c.descripcion
		ORDER BY ec.competencia_id`, estudiante, curso)
	return salida, err
}
