package models

import "github.com/google/uuid"



type NotaEjercicio struct {
	NotaCuadernilloID uuid.UUID `json:"nota_cuadernillo_id" db:"nota_cuadernillo_id"`
	CodigoEjercicio   string    `json:"codigo_ejercicio" db:"codigo_ejercicio"`
	CodigoCelda       string    `json:"codigo_celda" db:"codigo_celda"`
	Orden             int       `json:"orden" db:"orden"`
	Descripcion       *string   `json:"descripcion" db:"descripcion"`
	PuntosObtenidos   float64   `json:"puntos_obtenidos" db:"puntos_obtenidos"`
	PuntosMaximos     float64   `json:"puntos_maximos" db:"puntos_maximos"`
	Aprobado          *bool     `json:"aprobado" db:"aprobado"`
}