package repository

import (
	"proxy-go/internal/models"

	"github.com/jmoiron/sqlx"
)


type AttemptErrorRepository struct{
	db *sqlx.DB
}

func NewAttemptErrorRepository (db *sqlx.DB) *AttemptErrorRepository{
	return &AttemptErrorRepository{db : db}
}

func (repository *AttemptErrorRepository) CreateErrorRepository(attemp *models.AttemptError) error{
	
	// Nota: la inserción de intento+errores ahora es transaccional dentro de
	// ExerciseAttempsRepository.CreateAttemptWithErrors. Este método queda como
	// utilidad puntual (faltaba el ':' en occurred_at, que lo rompía).
	_, err := repository.db.NamedExec(`INSERT INTO attempt_errors
									   (id, attempt_id, cell_id, error_type, error_message, occurred_at)
									   VALUES (:id, :attempt_id, :cell_id, :error_type, :error_message, :occurred_at)`, attemp)

	return err
}