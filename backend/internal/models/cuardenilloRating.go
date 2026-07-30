package models

import (
	"time"

	"github.com/google/uuid"
)

type CuadernilloRating struct {
	ID            uuid.UUID `db:"id" json:"id"`
	CourseID      string    `db:"course_id" json:"course_id"`
	CuadernilloID string    `db:"cuadernillo_id" json:"cuadernillo_id"`
	StudentID     string    `db:"student_id" json:"student_id"`
	SubmittedAt   time.Time `db:"submitted_at" json:"submitted_at"`
	Rating        int16     `db:"rating" json:"rating"`
	Comment       *string   `db:"comment" json:"comment,omitempty"` 
}