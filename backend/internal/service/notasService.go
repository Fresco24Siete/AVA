package service

import (
	"proxy-go/internal/models"
	"proxy-go/internal/repository"
)

type NotasService struct {
	repo *repository.NotasRepository
}

func NewNotasService(repo *repository.NotasRepository) *NotasService {
	return &NotasService{repo: repo}
}

func (s *NotasService) GuardarLote(notas []models.CuadernilloNota) (int, error) {
	return s.repo.GuardarLote(notas)
}
