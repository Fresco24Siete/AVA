package view

// ExerciseCommonError mapea la vista exercise_common_errors
type ExerciseCommonError struct {
	CourseID      string `db:"course_id" json:"course_id"`
	CuadernilloID string `db:"cuadernillo_id" json:"cuadernillo_id"`
	ExerciseID    string `db:"exercise_id" json:"exercise_id"`
	ErrorType     string `db:"error_type" json:"error_type"`
	Occurrences   int64  `db:"occurrences" json:"occurrences"` // COUNT() es int64
}