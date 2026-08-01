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

	return service.repositoryExersice.CreateAttemptWithErrors(exercise, attempts)
}