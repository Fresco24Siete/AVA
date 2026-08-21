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

	_, err := repository.db.NamedExec(`INSERT INTO cuadernillo_ratings
									   (id, course_id, cuadernillo_id, student_id, submitted_at, rating, comment)
									   VALUES (:id, :course_id, :cuadernillo_id, :student_id, :submitted_at, :rating, :comment)
									   ON CONFLICT (course_id, cuadernillo_id, student_id)
									   DO UPDATE SET rating = EXCLUDED.rating,
									                 comment = EXCLUDED.comment,
									                 submitted_at = EXCLUDED.submitted_at`, cuadernillo)

	return err
}
