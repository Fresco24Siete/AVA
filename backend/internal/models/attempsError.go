package models

import (
	"time"

	"github.com/google/uuid"
)

type AttemptError struct {
	ID           uuid.UUID `db:"id" json:"id"`
	AttemptID    uuid.UUID `db:"attempt_id" json:"attempt_id"`
	CellID       string    `db:"cell_id" json:"cell_id"`
	ErrorType    string    `db:"error_type" json:"error_type"`
	ErrorMessage string    `db:"error_message" json:"error_message"`
	OccurredAt   time.Time `db:"occurred_at" json:"occurred_at"`
}