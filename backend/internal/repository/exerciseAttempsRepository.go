package repository


import (
	"proxy-go/internal/models"

	"github.com/jmoiron/sqlx"
)


type ExerciseAttempsRepository struct{
	db *sqlx.DB
}

func NewExerciseAttempsRepository (db *sqlx.DB) *ExerciseAttempsRepository{
	return &ExerciseAttempsRepository{db : db}
}

func (repository *ExerciseAttempsRepository) CreateExercise(exercise *models.ExerciseAttempt) error{
	
	_, err := repository.db.NamedExec(`INSERT INTO attempt_errors
									   (id,course_id,cuadernillo_id,exercise_id,student_id,attempt_at,validation_result, received_at )
									   VALUES (:id,:course_id,:cuadernillo_id,:exercise_id,student_id,attempt_at,validation_result, received_at )`,exercise)
	
	return err
}