package models

import (
	"time"

	"github.com/google/uuid"
)

type ExerciseAttempt struct {
	ID               uuid.UUID `db:"id" json:"id"`
	CourseID         string    `db:"course_id" json:"course_id"`
	CuadernilloID    string    `db:"cuadernillo_id" json:"cuadernillo_id"`
	ExerciseID       string    `db:"exercise_id" json:"exercise_id"`
	StudentID        string    `db:"student_id" json:"student_id"`
	AttemptAt        time.Time `db:"attempt_at" json:"attempt_at"`
	ValidationResult string    `db:"validation_result" json:"validation_result"` // 'passed' o 'failed'
	ReceivedAt       time.Time `db:"received_at" json:"received_at"`
}