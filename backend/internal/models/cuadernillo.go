package models

import "time"


type Cuadernillo struct {
	CursoID         string    `json:"curso_id" db:"curso_id"`
	Codigo          string    `json:"codigo" db:"codigo"`
	NotebookArchivo string    `json:"notebook_archivo" db:"notebook_archivo"`
	Activo          bool      `json:"activo" db:"activo"`
	CreadoEn        time.Time `json:"creado_en" db:"creado_en"`
}