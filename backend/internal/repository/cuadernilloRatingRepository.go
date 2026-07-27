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

func (repository *CuadernilloRatingRepository) CreateCuadernillo(cuadernillo *models.CuadernilloRating) error{
	
	_, err := repository.db.NamedExec(`INSERT INTO attempt_errors
									   (id,course_id,cuadernillo_id,student_id,submitted_at,rating,comment )
									   VALUES (:id,:course_id,:cuadernillo_id,:student_id,:submitted_at,:rating,:comment )`,cuadernillo)
	
	return err
}