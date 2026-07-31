package service

import (
	"proxy-go/internal/models"
	"proxy-go/internal/repository"
)


type ExerciseAttempsService struct{
	repositoryExersice *repository.ExerciseAttempsRepository
	repositoryAttemp *repository.AttemptErrorRepository
}

func NewExerciseAttempsService (repositoryExersice *repository.ExerciseAttempsRepository, repositoryAttemp *repository.AttemptErrorRepository) *ExerciseAttempsService{
	return &ExerciseAttempsService{
		repositoryExersice:repositoryExersice,
		repositoryAttemp: repositoryAttemp,
	}
}

func (service *ExerciseAttempsService) CreateAttemptWithErrors(exercise *models.ExerciseAttempt, attempts []models.AttemptError) error {
	// Intento + errores en una sola transacción (ver el repositorio). Antes se
	// insertaban por separado y sin transacción: un fallo a mitad dejaba el
	// intento sin (o con parte de) sus errores.
	return service.repositoryExersice.CreateAttemptWithErrors(exercise, attempts)
}