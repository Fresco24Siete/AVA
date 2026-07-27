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

func (repository *AttemptErrorRepository) CreateError(attemp *models.AttemptError) error{
	
	_, err := repository.db.NamedExec(`INSERT INTO attempt_errors
									   (id, attempt_id, cell_id,error_type, error_message, occurred_at)
									   VALUES (:id,:attempt_id,:cell_id,:error_type,:error_message, occurred_at)`,attemp)
	
	return err
}