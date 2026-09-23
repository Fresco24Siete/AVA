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

// DeEjercicio devuelve las competencias que mide un ejercicio concreto.
//
// La competencia NO viaja dentro del intento: se resuelve por este par
// (cuadernillo, ejercicio), que es la clave de negocio real. 'ejercicio_1'
// existe en las seis semanas, así que el cuadernillo es parte de la clave, no
// un adorno.
//
// Se consulta en la ingesta para poder AVISAR cuando un intento entra sin
// mapeo. No sirve para rechazarlo: ver el comentario de avisarSiHuerfano en
// exerciseAttempsService.go.
func (r *CompetenciasRepository) DeEjercicio(cuadernillo, ejercicio string) ([]string, error) {
	salida := []string{}
	err := r.db.Select(&salida,
		`SELECT competencia_id
		   FROM ejercicio_competencias
		  WHERE cuadernillo_id = $1 AND exercise_id = $2
		  ORDER BY competencia_id`, cuadernillo, ejercicio)
	return salida, err
}
