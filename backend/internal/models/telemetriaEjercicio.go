package models

import (
	"time"

	"github.com/google/uuid"
)

type TelemetriaEjercicio struct {
	ID                uuid.UUID  `json:"id" db:"id"`
	EstudianteID      string     `json:"estudiante_id" db:"estudiante_id"`
	CursoID           string     `json:"curso_id" db:"curso_id"`
	CuadernilloCodigo string     `json:"cuadernillo_codigo" db:"cuadernillo_codigo"`
	CodigoEjercicio   string     `json:"codigo_ejercicio" db:"codigo_ejercicio"`
	CodigoCelda       string     `json:"codigo_celda" db:"codigo_celda"`
	Orden             int        `json:"orden" db:"orden"`
	PuntosMaximos     float64    `json:"puntos_maximos" db:"puntos_maximos"`
	Descripcion       string     `json:"descripcion" db:"descripcion"`
	Timestamp         time.Time  `json:"timestamp" db:"timestamp"`
	PrimerIntento     *time.Time `json:"primer_intento" db:"primer_intento"` // Puntero porque puede ser nulo
	NumIntentos       int        `json:"num_intentos" db:"num_intentos"`
	DuracionSegundos  float64    `json:"duracion_segundos" db:"duracion_segundos"`
	Exito             bool       `json:"exito" db:"exito"`
	TipoError         *string    `json:"tipo_error" db:"tipo_error"` // Puntero porque puede ser nulo si hay éxito
	Mensaje           *string    `json:"mensaje" db:"mensaje"`       // Puntero
	Traceback         *string    `json:"traceback" db:"traceback"`   // Puntero
	CreadoEn          time.Time  `json:"creado_en" db:"creado_en"`
}