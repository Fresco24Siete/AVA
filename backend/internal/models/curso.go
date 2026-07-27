package models

import "time"

type Curso struct {
	ID       string    `json:"id" db:"id"` 
	Nombre   string    `json:"nombre" db:"nombre"`
	CreadoEn time.Time `json:"creado_en" db:"creado_en"`
}