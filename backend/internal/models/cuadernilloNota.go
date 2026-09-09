package models

import (
	"time"

	"github.com/google/uuid"
)

// CuadernilloNota es la nota de un estudiante en un cuadernillo.
//
// Origen distingue la nota oficial de nbgrader -- la que sale de "Autograde",
// ejecutando tambien las pruebas ocultas -- de una provisional deducida de la
// telemetria, que solo vio las pruebas visibles. Los dos numeros no tienen por
// que coincidir, y mezclarlos genera el reclamo de "el panel decia otra cosa".
type CuadernilloNota struct {
	ID               uuid.UUID  `db:"id" json:"id"`
	CourseID         string     `db:"course_id" json:"course_id"`
	CuadernilloID    string     `db:"cuadernillo_id" json:"cuadernillo_id"`
	StudentID        string     `db:"student_id" json:"student_id"`
	PuntosObtenidos  float64    `db:"puntos_obtenidos" json:"puntos_obtenidos"`
	PuntosMaximos    float64    `db:"puntos_maximos" json:"puntos_maximos"`
	CalificadoEn     time.Time  `db:"calificado_en" json:"calificado_en"`
	Origen           string     `db:"origen" json:"origen"`
	EnviadoAMoodleEn *time.Time `db:"enviado_a_moodle_en" json:"enviado_a_moodle_en,omitempty"`
}
