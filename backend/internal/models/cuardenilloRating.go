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
	// Cuánto siente el estudiante que aprendió, de 1 a 5. No es una nota.
	Rating  int16   `db:"rating" json:"rating"`
	Comment *string `db:"comment" json:"comment,omitempty"`

	// Lo que la telemetría no puede saber. Punteros porque el alumno puede
	// contestar solo la primera pregunta e irse: NULL es "no contestó", que no
	// es lo mismo que cero.
	//   Tiempo: 1=<1h  2=1-2h  3=2-4h  4=>4h, incluido lo que hizo fuera de Jupyter.
	//   Freno:  enunciado | concepto | sintaxis | error | tiempo | nada
	Tiempo *int16  `db:"tiempo" json:"tiempo,omitempty"`
	Freno  *string `db:"freno" json:"freno,omitempty"`

	// Las pone el servidor, no el cliente: si ya había entregado al valorar
	// (separa a quien terminó de quien abandonó) y por dónde valoró.
	Entregado *bool   `db:"entregado" json:"entregado,omitempty"`
	Origen    *string `db:"origen" json:"origen,omitempty"`
}
