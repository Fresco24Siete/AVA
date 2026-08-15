package handler

import (
	"net/http"
	"proxy-go/internal/middleware"
	"proxy-go/internal/models"
	"proxy-go/internal/service"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)


type ExerciseHandler struct {
	service *service.ExerciseAttempsService
}

type ExerciseAttemptRequest struct {
	CourseID         string         `json:"course_id"`
	CuadernilloID    string         `json:"cuadernillo_id"`
	ExerciseID       string         `json:"exercise_id"`
	StudentID        string         `json:"student_id"`
	AttemptAt        time.Time      `json:"attempt_at"`
	ValidationResult string         `json:"validation_result"`
	Errors           []AttemptErrorRequest `json:"errors"`
}

type AttemptErrorRequest struct {
	CellID       string    `json:"cell_id"`
	Timestamp    time.Time `json:"timestamp"`
	ErrorType    string    `json:"error_type"`
	ErrorMessage string    `json:"error_message"`
}


func NewExerciseHandler (service *service.ExerciseAttempsService) *ExerciseHandler{
	return &ExerciseHandler{service: service}
}

func (handler *ExerciseHandler) CreateAttemptHandler(c *gin.Context) {

	var input ExerciseAttemptRequest
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Sintaxis inválida en el cuerpo JSON"})
		return
	}

	if input.ValidationResult != "passed" && input.ValidationResult != "failed" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "validation_result debe ser 'passed' o 'failed'"})
		return
	}

	// La identidad sale del token, no del cuerpo. El alumno puede leer su propio
	// token dentro de su contenedor y hacer POST a mano; si nos fiáramos del
	// cuerpo, podría escribir telemetría a nombre de un compañero.
	// Si no hay token verificado (secreto sin configurar) se respeta el cuerpo,
	// que es el comportamiento que había antes.
	studentID, courseID := middleware.IdentidadVerificada(c)
	if studentID == "" {
		studentID = input.StudentID
	}
	if courseID == "" {
		courseID = input.CourseID
	}

	exercise := &models.ExerciseAttempt{
		ID:               uuid.New(),
		CourseID:         courseID,
		CuadernilloID:    input.CuadernilloID,
		ExerciseID:       input.ExerciseID,
		StudentID:        studentID,
		AttemptAt:        input.AttemptAt,
		ValidationResult: input.ValidationResult,
		ReceivedAt:       time.Now(),
	}

	errorsToInsert := make([]models.AttemptError, 0, len(input.Errors))
	for _, e := range input.Errors {
		errorsToInsert = append(errorsToInsert, models.AttemptError{
			ID:           uuid.New(),
			AttemptID:    exercise.ID,
			CellID:       e.CellID,
			ErrorType:    e.ErrorType,
			ErrorMessage: e.ErrorMessage,
			OccurredAt:   e.Timestamp,
		})
	}

	// una sola llamada que inserta exercise + errores en una transacción
	if err := handler.service.CreateAttemptWithErrors(exercise, errorsToInsert); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "fail to save attempt"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"message": "attempt saved", "attempt_id": exercise.ID})
}