package view

// CuadernilloRatingSummary mapea la vista cuadernillo_rating_summary
type CuadernilloRatingSummary struct {
	CourseID      string  `db:"course_id" json:"course_id"`
	CuadernilloID string  `db:"cuadernillo_id" json:"cuadernillo_id"`
	TotalRatings  int64   `db:"total_ratings" json:"total_ratings"`
	// AVG() en Postgres devuelve un tipo "numeric", que en Go se mapea mejor a float64
	AvgRating     float64 `db:"avg_rating" json:"avg_rating"` 
}