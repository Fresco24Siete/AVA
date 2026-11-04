package repository

import (
	"fmt"

	"proxy-go/internal/models"

	"github.com/jmoiron/sqlx"
)

type NotasRepository struct {
	db *sqlx.DB
}

func NewNotasRepository(db *sqlx.DB) *NotasRepository {
	return &NotasRepository{db: db}
}

// GuardarLote inserta o actualiza las notas de un cuadernillo.
//
// Es un UPSERT porque recalificar es normal: el docente corrige una prueba, la
// vuelve a ejecutar y la nota cambia. Duplicar filas dejaria dos verdades.
//
// enviado_a_moodle_en NO se pisa al actualizar: si la nota ya viajo a Moodle,
// esa marca es historia y recalificar no la borra.
func (r *NotasRepository) GuardarLote(notas []models.CuadernilloNota) (int, error) {
	if len(notas) == 0 {
		return 0, nil
	}

	tx, err := r.db.Beginx()
	if err != nil {
		return 0, fmt.Errorf("no se pudo iniciar la transacción: %w", err)
	}
	defer tx.Rollback()

	for i := range notas {
		if _, err := tx.NamedExec(`
			INSERT INTO cuadernillo_notas
				(id, course_id, cuadernillo_id, student_id,
				 puntos_obtenidos, puntos_maximos, calificado_en, origen)
			VALUES (:id, :course_id, :cuadernillo_id, :student_id,
				 :puntos_obtenidos, :puntos_maximos, :calificado_en, :origen)
			ON CONFLICT (course_id, cuadernillo_id, student_id) DO UPDATE SET
				puntos_obtenidos = EXCLUDED.puntos_obtenidos,
				puntos_maximos   = EXCLUDED.puntos_maximos,
				calificado_en    = EXCLUDED.calificado_en,
				origen           = EXCLUDED.origen`,
			&notas[i]); err != nil {
			return 0, fmt.Errorf("guardar nota de %s: %w", notas[i].StudentID, err)
		}
	}

	return len(notas), tx.Commit()
}
