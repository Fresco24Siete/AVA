package repository

import (
	"fmt"

	"proxy-go/internal/models"

	"github.com/jmoiron/sqlx"
)

type ExerciseAttempsRepository struct {
	db *sqlx.DB
}

func NewExerciseAttempsRepository(db *sqlx.DB) *ExerciseAttempsRepository {
	return &ExerciseAttempsRepository{db: db}
}

func (repository *ExerciseAttempsRepository) CreateAttemptWithErrors(
	exercise *models.ExerciseAttempt, errores []models.AttemptError) error {

	tx, err := repository.db.Beginx()
	if err != nil {
		return fmt.Errorf("no se pudo iniciar la transacción: %w", err)
	}
	defer tx.Rollback()

	if _, err := tx.NamedExec(`INSERT INTO exercise_attempts
		(id, course_id, cuadernillo_id, exercise_id, student_id, attempt_at, validation_result, received_at,
		 puntos_maximos, codigo_celda, orden)
		VALUES (:id, :course_id, :cuadernillo_id, :exercise_id, :student_id, :attempt_at, :validation_result, :received_at,
		 :puntos_maximos, :codigo_celda, :orden)`,
		exercise); err != nil {
		return fmt.Errorf("insert exercise_attempts: %w", err)
	}

	for i := range errores {
		if _, err := tx.NamedExec(`INSERT INTO attempt_errors
			(id, attempt_id, cell_id, error_type, error_message, occurred_at)
			VALUES (:id, :attempt_id, :cell_id, :error_type, :error_message, :occurred_at)`,
			&errores[i]); err != nil {
			return fmt.Errorf("insert attempt_errors: %w", err)
		}
	}

	return tx.Commit()
}
