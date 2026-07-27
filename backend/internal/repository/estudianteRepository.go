package repository

import (
	"proxy-go/internal/models"

	"github.com/jmoiron/sqlx"
)


type EstudianteRepository struct{
	db *sqlx.DB
}

func NewEstudianteRepository(db *sqlx.DB) *EstudianteRepository{
	return &EstudianteRepository{db: db}
}

func (repository *EstudianteRepository) CrearEstudiante (estudiante *models.Estudiante) error{
	
	_ , err := repository.db.NamedExec(`INSERT INTO estudiante
										(id, nombre_completo, correo , creado_en)
										VALUES (:id, :nombre_completo, :correo, :creado_en) `, estudiante)

	return err
}