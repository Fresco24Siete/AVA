package repository

import (
	"fmt"

	"github.com/jmoiron/sqlx"
)

type CompetenciasRepository struct {
	db *sqlx.DB
}

func NewCompetenciasRepository(db *sqlx.DB) *CompetenciasRepository {
	return &CompetenciasRepository{db: db}
}

// Reemplazar borra el mapeo anterior de cada cuadernillo recibido e inserta el
// nuevo, todo en una transacción.
//
// Se reemplaza por cuadernillo y no se vacía la tabla entera para poder recargar
// una sola semana sin perder las demás. Y se reemplaza en vez de acumular porque
// si un ejercicio deja de evaluar una competencia, esa fila debe desaparecer.
func (r *CompetenciasRepository) Reemplazar(mapeo map[string]map[string][]string) (int, error) {
	tx, err := r.db.Beginx()
	if err != nil {
		return 0, fmt.Errorf("no se pudo iniciar la transacción: %w", err)
	}
	defer tx.Rollback()

	total := 0
	for cuadernillo, ejercicios := range mapeo {
		if _, err := tx.Exec(
			`DELETE FROM ejercicio_competencias WHERE cuadernillo_id = $1`,
			cuadernillo); err != nil {
			return 0, fmt.Errorf("limpiar %s: %w", cuadernillo, err)
		}
		for ejercicio, competencias := range ejercicios {
			for _, competencia := range competencias {
				if _, err := tx.Exec(
					`INSERT INTO ejercicio_competencias
					   (cuadernillo_id, exercise_id, competencia_id)
					 VALUES ($1, $2, $3)
					 ON CONFLICT DO NOTHING`,
					cuadernillo, ejercicio, competencia); err != nil {
					// Casi siempre: la competencia no existe en el catálogo.
					return 0, fmt.Errorf("insertar %s/%s/%s: %w",
						cuadernillo, ejercicio, competencia, err)
				}
				total++
			}
		}
	}

	return total, tx.Commit()
}
