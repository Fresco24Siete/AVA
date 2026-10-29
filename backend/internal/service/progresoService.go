package service

import "proxy-go/internal/repository"

type ProgresoService struct {
	repo *repository.ProgresoRepository
}

func NewProgresoService(repo *repository.ProgresoRepository) *ProgresoService {
	return &ProgresoService{repo: repo}
}

func (s *ProgresoService) Cuadernillos(estudiante, curso string) ([]repository.ResumenCuadernillo, error) {
	return s.repo.PorCuadernillo(estudiante, curso)
}

func (s *ProgresoService) Competencias(estudiante, curso string) ([]repository.ResumenCompetencia, error) {
	return s.repo.PorCompetencia(estudiante, curso)
}
