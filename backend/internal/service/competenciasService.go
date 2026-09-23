package service

import "proxy-go/internal/repository"

type CompetenciasService struct {
	repo *repository.CompetenciasRepository
}

func NewCompetenciasService(repo *repository.CompetenciasRepository) *CompetenciasService {
	return &CompetenciasService{repo: repo}
}

// Reemplazar cambia el mapeo de los cuadernillos indicados y devuelve cuántas
// relaciones quedaron guardadas.
func (s *CompetenciasService) Reemplazar(mapeo map[string]map[string][]string) (int, error) {
	return s.repo.Reemplazar(mapeo)
}
