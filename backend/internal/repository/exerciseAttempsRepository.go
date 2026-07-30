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

// CreateAttemptWithErrors inserta el intento y TODOS sus errores en una sola
// transacción. Si falla cualquier inserción, se revierte todo: nunca queda un
// intento a medias sin sus errores. (Era lo que el handler ya asumía.)
//
// Antes el INSERT apuntaba a la tabla equivocada (attempt_errors) y varios
// binds iban sin ':' (student_id, attempt_at, ...), así que jamás persistía.
func (repository *ExerciseAttempsRepository) CreateAttemptWithErrors(
	exercise *models.ExerciseAttempt, errores []models.AttemptError) error {

	tx, err := repository.db.Beginx()
	if err != nil {
		return fmt.Errorf("no se pudo iniciar la transacción: %w", err)
	}
	defer tx.Rollback() // no-op si el Commit ya ocurrió

	if _, err := tx.NamedExec(`INSERT INTO exercise_attempts
		(id, course_id, cuadernillo_id, exercise_id, student_id, attempt_at, validation_result, received_at)
		VALUES (:id, :course_id, :cuadernillo_id, :exercise_id, :student_id, :attempt_at, :validation_result, :received_at)`,
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
