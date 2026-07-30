package service

import (
	"proxy-go/internal/models"
	"proxy-go/internal/repository"
)


type CuadernilloRatingService struct{
	repository *repository.CuadernilloRatingRepository
}

func NewCuadernilloRatingService (repository *repository.CuadernilloRatingRepository) *CuadernilloRatingService{
	return &CuadernilloRatingService{repository:repository}
}

func(service *CuadernilloRatingService) CreateCuadernilloServicie(cuadernillo *models.CuadernilloRating) error{

	err := service.repository.CreateCuadernilloRepository(cuadernillo)
	//añadir manejo de errores

	return err
}