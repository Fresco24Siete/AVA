package repository

import (
	"proxy-go/internal/models"

	"github.com/jmoiron/sqlx"
)

type CuadernilloRatingRepository struct {
	db *sqlx.DB
}

func NewCuadernilloRatingRepository(db *sqlx.DB) *CuadernilloRatingRepository {
	return &CuadernilloRatingRepository{db: db}
}

func (repository *CuadernilloRatingRepository) CreateCuadernilloRepository(cuadernillo *models.CuadernilloRating) error {

	// El alumno puede volver y cambiar su respuesta, o completarla en dos
	// pasos: toca la estrella y se va, y más tarde marca el tiempo. Por eso
	// COALESCE en los campos opcionales: lo que llega ausente no borra lo que
	// ya había contestado antes.
	//
	// El comentario es el caso especial, porque hay que distinguir "no mandé
	// comentario" de "borré el que tenía": ausente (NULL) conserva, vacío borra.
	//
	// OJO al tocar esta consulta: sqlx NO entiende los comentarios SQL, así que
	// un "--" con dos puntos dentro de la cadena lo interpreta como un
	// parámetro con nombre vacío y falla con "could not find name". Los
	// comentarios van aquí fuera.
	_, err := repository.db.NamedExec(`INSERT INTO cuadernillo_ratings
			(id, course_id, cuadernillo_id, student_id, submitted_at,
			 rating, comment, tiempo, freno, entregado, origen)
		VALUES (:id, :course_id, :cuadernillo_id, :student_id, :submitted_at,
			 :rating, :comment, :tiempo, :freno, :entregado, :origen)
		ON CONFLICT (course_id, cuadernillo_id, student_id)
		DO UPDATE SET rating       = EXCLUDED.rating,
		              comment      = CASE WHEN EXCLUDED.comment IS NULL
		                                  THEN cuadernillo_ratings.comment
		                                  ELSE NULLIF(EXCLUDED.comment, '') END,
		              tiempo       = COALESCE(EXCLUDED.tiempo, cuadernillo_ratings.tiempo),
		              freno        = COALESCE(EXCLUDED.freno, cuadernillo_ratings.freno),
		              entregado    = COALESCE(EXCLUDED.entregado, cuadernillo_ratings.entregado),
		              origen       = COALESCE(EXCLUDED.origen, cuadernillo_ratings.origen),
		              submitted_at = EXCLUDED.submitted_at`, cuadernillo)

	return err
}

// MiValoracion: lo que este alumno ya respondió de este cuadernillo, para que
// el panel pueda mostrárselo en vez de volver a preguntárselo. nil si no ha
// valorado.
func (repository *CuadernilloRatingRepository) MiValoracion(curso, cuadernillo, estudiante string) (*models.CuadernilloRating, error) {
	var r models.CuadernilloRating
	err := repository.db.Get(&r, `
		SELECT id, course_id, cuadernillo_id, student_id, submitted_at,
		       rating, comment, tiempo, freno, entregado, origen
		  FROM cuadernillo_ratings
		 WHERE course_id = $1 AND cuadernillo_id = $2 AND student_id = $3`,
		curso, cuadernillo, estudiante)
	if err != nil {
		return nil, err
	}
	return &r, nil
}
