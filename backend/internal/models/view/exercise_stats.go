package view

// ExerciseStats mapea la vista exercise_stats
type ExerciseStats struct {
	CourseID          string `db:"course_id" json:"course_id"`
	CuadernilloID     string `db:"cuadernillo_id" json:"cuadernillo_id"`
	ExerciseID        string `db:"exercise_id" json:"exercise_id"`
	TotalAttempts     int64  `db:"total_attempts" json:"total_attempts"`
	StudentsAttempted int64  `db:"students_attempted" json:"students_attempted"`
	PassedAttempts    int64  `db:"passed_attempts" json:"passed_attempts"`
	StudentsPassed    int64  `db:"students_passed" json:"students_passed"`
}