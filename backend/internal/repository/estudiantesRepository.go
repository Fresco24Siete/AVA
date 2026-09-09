package repository

import (
	"fmt"
	"time"

	"github.com/jmoiron/sqlx"
)

// EstudiantesRepository: quién es cada student_id, y cómo le va.
//
// La identidad la escribe el Hub en cada ingreso LTI (Registrar). Todo lo
// demás sale de cruzar esa tabla con la telemetría y las notas, para que el
// panel del docente pueda listar a su gente por nombre y no por número.
type EstudiantesRepository struct {
	db *sqlx.DB
}

func NewEstudiantesRepository(db *sqlx.DB) *EstudiantesRepository {
	return &EstudiantesRepository{db: db}
}

// Ingreso es lo que el Hub sabe de una persona en el momento en que entra.
type Ingreso struct {
	CourseID   string `json:"curso_id"`
	StudentID  string `json:"estudiante_id"`
	Nombre     string `json:"nombre"`
	Email      string `json:"email"`
	UsuarioHub string `json:"usuario_hub"`
	Rol        string `json:"rol"`
	SourcedID  string `json:"lis_result_sourcedid"`
	OutcomeURL string `json:"lis_outcome_service_url"`
}

// Registrar anota un ingreso: crea la ficha la primera vez y después la
// actualiza. El sourcedid de Moodle cambia entre lanzamientos (es por casilla
// del libro de calificaciones), así que siempre se guarda el último; un
// lanzamiento que no lo trae no borra el anterior.
func (r *EstudiantesRepository) Registrar(in Ingreso) error {
	_, err := r.db.NamedExec(`
		INSERT INTO estudiantes
			(course_id, student_id, nombre, email, usuario_hub, rol,
			 lis_result_sourcedid, lis_outcome_service_url,
			 primer_ingreso, ultimo_ingreso, ingresos)
		VALUES
			(:course_id, :student_id, :nombre, :email, :usuario_hub, :rol,
			 NULLIF(:sourcedid, ''), NULLIF(:outcome_url, ''),
			 now(), now(), 1)
		ON CONFLICT (course_id, student_id) DO UPDATE SET
			nombre                  = CASE WHEN EXCLUDED.nombre <> '' THEN EXCLUDED.nombre ELSE estudiantes.nombre END,
			email                   = CASE WHEN EXCLUDED.email  <> '' THEN EXCLUDED.email  ELSE estudiantes.email  END,
			usuario_hub             = CASE WHEN EXCLUDED.usuario_hub <> '' THEN EXCLUDED.usuario_hub ELSE estudiantes.usuario_hub END,
			rol                     = EXCLUDED.rol,
			lis_result_sourcedid    = COALESCE(EXCLUDED.lis_result_sourcedid, estudiantes.lis_result_sourcedid),
			lis_outcome_service_url = COALESCE(EXCLUDED.lis_outcome_service_url, estudiantes.lis_outcome_service_url),
			ultimo_ingreso          = now(),
			ingresos                = estudiantes.ingresos + 1`,
		map[string]any{
			"course_id": in.CourseID, "student_id": in.StudentID,
			"nombre": in.Nombre, "email": in.Email, "usuario_hub": in.UsuarioHub,
			"rol": in.Rol, "sourcedid": in.SourcedID, "outcome_url": in.OutcomeURL,
		})
	if err != nil {
		return fmt.Errorf("no se pudo registrar el ingreso: %w", err)
	}
	return nil
}

// FichaEstudiante es una fila del listado del docente.
type FichaEstudiante struct {
	StudentID         string     `db:"student_id" json:"student_id"`
	Nombre            string     `db:"nombre" json:"nombre"`
	Email             string     `db:"email" json:"email"`
	Rol               string     `db:"rol" json:"rol"`
	UltimoIngreso     *time.Time `db:"ultimo_ingreso" json:"ultimo_ingreso"`
	Ingresos          int        `db:"ingresos" json:"ingresos"`
	UltimoIntento     *time.Time `db:"ultimo_intento" json:"ultimo_intento"`
	UltimoCuadernillo string     `db:"ultimo_cuadernillo" json:"ultimo_cuadernillo"`
	IntentosReales    int        `db:"intentos_reales" json:"intentos_reales"`
	Resueltos         int        `db:"resueltos" json:"ejercicios_resueltos"`
	Atascados         int        `db:"atascados" json:"ejercicios_atascados"`
	AMedias           int        `db:"a_medias" json:"ejercicios_a_medias"`
	Notas             int        `db:"notas" json:"cuadernillos_calificados"`
	TieneSourcedID    bool       `db:"tiene_sourcedid" json:"devolucion_moodle_posible"`
}

// Listar devuelve a todos los del curso: los registrados por el Hub y, por si
// hubiera telemetría o notas de alguien de antes del registro, también a
// quienes solo existen ahí (sin nombre). Incluye al docente, con su rol, para
// que el listado coincida con lo que el Hub conoce.
func (r *EstudiantesRepository) Listar(curso string) ([]FichaEstudiante, error) {
	salida := []FichaEstudiante{}
	err := r.db.Select(&salida, intentosReales+`,
	    porEjercicio AS (
	        SELECT student_id, cuadernillo_id, exercise_id,
	               bool_or(validation_result = 'passed')                   AS paso,
	               bool_or(validation_result = 'failed' AND NOT stub)      AS intento_real,
	               bool_or(validation_result = 'sin_validar' AND NOT stub) AS a_medias
	          FROM t GROUP BY student_id, cuadernillo_id, exercise_id
	    ),
	    actividad AS (
	        SELECT student_id,
	               COUNT(*) FILTER (WHERE paso)                      AS resueltos,
	               COUNT(*) FILTER (WHERE intento_real AND NOT paso) AS atascados,
	               COUNT(*) FILTER (WHERE a_medias AND NOT paso)     AS a_medias
	          FROM porEjercicio GROUP BY student_id
	    ),
	    ultimo AS (
	        SELECT DISTINCT ON (student_id) student_id, received_at, cuadernillo_id
	          FROM t ORDER BY student_id, received_at DESC
	    ),
	    intentos AS (
	        SELECT student_id, COUNT(*) FILTER (WHERE NOT stub) AS intentos_reales
	          FROM t GROUP BY student_id
	    ),
	    notas AS (
	        SELECT student_id, COUNT(*) AS notas
	          FROM cuadernillo_notas WHERE course_id = $1 GROUP BY student_id
	    ),
	    ids AS (
	        SELECT student_id FROM estudiantes WHERE course_id = $1
	        UNION SELECT student_id FROM t
	        UNION SELECT student_id FROM cuadernillo_notas WHERE course_id = $1
	    )
		SELECT ids.student_id,
		       COALESCE(e.nombre, '')                              AS nombre,
		       COALESCE(e.email, '')                               AS email,
		       COALESCE(e.rol, 'estudiante')                       AS rol,
		       e.ultimo_ingreso,
		       COALESCE(e.ingresos, 0)                             AS ingresos,
		       u.received_at                                       AS ultimo_intento,
		       COALESCE(u.cuadernillo_id, '')                      AS ultimo_cuadernillo,
		       COALESCE(i.intentos_reales, 0)                      AS intentos_reales,
		       COALESCE(a.resueltos, 0)                            AS resueltos,
		       COALESCE(a.atascados, 0)                            AS atascados,
		       COALESCE(a.a_medias, 0)                             AS a_medias,
		       COALESCE(n.notas, 0)                                AS notas,
		       (e.lis_result_sourcedid IS NOT NULL)                AS tiene_sourcedid
		  FROM ids
		  LEFT JOIN estudiantes e ON e.course_id = $1 AND e.student_id = ids.student_id
		  LEFT JOIN actividad  a ON a.student_id = ids.student_id
		  LEFT JOIN ultimo     u ON u.student_id = ids.student_id
		  LEFT JOIN intentos   i ON i.student_id = ids.student_id
		  LEFT JOIN notas      n ON n.student_id = ids.student_id
		 ORDER BY COALESCE(u.received_at, e.ultimo_ingreso) DESC NULLS LAST, ids.student_id`, curso)
	return salida, err
}

// Nombres devuelve {student_id: nombre} para poner nombre donde hoy hay número.
func (r *EstudiantesRepository) Nombres(curso string) (map[string]string, error) {
	filas := []struct {
		ID     string `db:"student_id"`
		Nombre string `db:"nombre"`
	}{}
	if err := r.db.Select(&filas, `SELECT student_id, nombre FROM estudiantes WHERE course_id = $1`, curso); err != nil {
		return nil, err
	}
	m := make(map[string]string, len(filas))
	for _, f := range filas {
		if f.Nombre != "" {
			m[f.ID] = f.Nombre
		}
	}
	return m, nil
}

// EjercicioDeEstudiante es una fila de la ficha individual.
type EjercicioDeEstudiante struct {
	CuadernilloID string     `db:"cuadernillo_id" json:"cuadernillo_id"`
	EjercicioID   string     `db:"exercise_id" json:"exercise_id"`
	Orden         *int16     `db:"orden" json:"orden"`
	PuntosMax     *int16     `db:"puntos_maximos" json:"puntos_maximos"`
	Intentos      int        `db:"intentos" json:"intentos"`
	Paso          bool       `db:"paso" json:"resuelto"`
	AMedias       bool       `db:"a_medias" json:"a_medias"`
	SoloStub      bool       `db:"solo_stub" json:"solo_ejecuto_vacio"`
	UltimoError   string     `db:"ultimo_error" json:"ultimo_error"`
	UltimoMensaje string     `db:"ultimo_mensaje" json:"ultimo_mensaje"`
	PrimerIntento *time.Time `db:"primero" json:"primer_intento"`
	UltimoIntento *time.Time `db:"ultimo" json:"ultimo_intento"`
}

// Ficha: el recorrido de una persona, ejercicio a ejercicio.
func (r *EstudiantesRepository) Ficha(curso, estudiante string) ([]EjercicioDeEstudiante, error) {
	salida := []EjercicioDeEstudiante{}
	err := r.db.Select(&salida, `
	    WITH t AS (
	        SELECT a.*,
	               EXISTS (SELECT 1 FROM attempt_errors e
	                        WHERE e.attempt_id = a.id
	                          AND e.error_type = 'NotImplementedError') AS stub
	          FROM exercise_attempts a
	         WHERE a.course_id = $1 AND a.student_id = $2
	    ),
	    ultimo_error AS (
	        SELECT DISTINCT ON (t.cuadernillo_id, t.exercise_id)
	               t.cuadernillo_id, t.exercise_id, e.error_type, e.error_message
	          FROM t JOIN attempt_errors e ON e.attempt_id = t.id
	         WHERE NOT t.stub
	         ORDER BY t.cuadernillo_id, t.exercise_id, e.occurred_at DESC
	    )
		SELECT t.cuadernillo_id, t.exercise_id,
		       MIN(t.orden)                                        AS orden,
		       MAX(t.puntos_maximos)                               AS puntos_maximos,
		       COUNT(*) FILTER (WHERE NOT t.stub)                  AS intentos,
		       bool_or(t.validation_result = 'passed')             AS paso,
		       bool_or(t.validation_result = 'sin_validar' AND NOT t.stub)
		           AND NOT bool_or(t.validation_result = 'passed') AS a_medias,
		       bool_and(t.stub)                                    AS solo_stub,
		       COALESCE(MAX(ue.error_type), '')                    AS ultimo_error,
		       COALESCE(MAX(LEFT(ue.error_message, 200)), '')      AS ultimo_mensaje,
		       MIN(t.received_at)                                  AS primero,
		       MAX(t.received_at)                                  AS ultimo
		  FROM t
		  LEFT JOIN ultimo_error ue ON ue.cuadernillo_id = t.cuadernillo_id
		                           AND ue.exercise_id    = t.exercise_id
		 GROUP BY t.cuadernillo_id, t.exercise_id
		 ORDER BY t.cuadernillo_id, MIN(t.orden) NULLS LAST, t.exercise_id`, curso, estudiante)
	return salida, err
}
