package repository


import (
	"proxy-go/internal/models"

	"github.com/jmoiron/sqlx"
)


type CuadernilloRatingRepository struct{
	db *sqlx.DB
}

func NewCuadernilloRatingRepository (db *sqlx.DB) *CuadernilloRatingRepository{
	return &CuadernilloRatingRepository{db : db}
}

func (repository *CuadernilloRatingRepository) CreateCuadernilloRepository(cuadernillo *models.CuadernilloRating) error{
	
	// Antes insertaba en la tabla equivocada (attempt_errors). Va a
	// cuadernillo_ratings, y como hay UNIQUE(course_id, cuadernillo_id,
	// student_id) — "un estudiante califica una sola vez" — se hace UPSERT:
	// si vuelve a calificar (otro navegador, reenvío), se actualiza en vez de
	// romper con violación de unicidad.
	_, err := repository.db.NamedExec(`INSERT INTO cuadernillo_ratings
									   (id, course_id, cuadernillo_id, student_id, submitted_at, rating, comment)
									   VALUES (:id, :course_id, :cuadernillo_id, :student_id, :submitted_at, :rating, :comment)
									   ON CONFLICT (course_id, cuadernillo_id, student_id)
									   DO UPDATE SET rating = EXCLUDED.rating,
									                 comment = EXCLUDED.comment,
									                 submitted_at = EXCLUDED.submitted_at`, cuadernillo)

	return err
}