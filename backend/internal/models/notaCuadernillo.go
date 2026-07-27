package models

import (
	"time"

	"github.com/google/uuid"
)


type NotaCuadernillo struct {
	ID                uuid.UUID  `json:"id" db:"id"`
	EstudianteID      string     `json:"estudiante_id" db:"estudiante_id"`
	CursoID           string     `json:"curso_id" db:"curso_id"`
	CuadernilloCodigo string     `json:"cuadernillo_codigo" db:"cuadernillo_codigo"`
	Estado            *string    `json:"estado" db:"estado"`
	FechaFin          *time.Time `json:"fecha_fin" db:"fecha_fin"` // Parseado desde el string de nbgrader
	PuntajeTotal      float64    `json:"puntaje_total" db:"puntaje_total"`
	PuntajeMaximo     float64    `json:"puntaje_maximo" db:"puntaje_maximo"`
	ActualizadoEn     time.Time  `json:"actualizado_en" db:"actualizado_en"`
}