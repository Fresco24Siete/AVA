package models

import "time"

type Estudiante struct {
	ID             string    `json:"id" db:"id"` // LTI user_id
	NombreCompleto string    `json:"nombre_completo" db:"nombre_completo"`
	Correo         string    `json:"correo" db:"correo"`
	CreadoEn       time.Time `json:"creado_en" db:"creado_en"`
}