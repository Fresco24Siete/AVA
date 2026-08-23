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
	CourseID         string                `json:"course_id"`
	CuadernilloID    string                `json:"cuadernillo_id"`
	ExerciseID       string                `json:"exercise_id"`
	StudentID        string                `json:"student_id"`
	AttemptAt        time.Time             `json:"attempt_at"`
	ValidationResult string                `json:"validation_result"`
	PuntosMaximos    *int16                `json:"puntos_maximos"`
	CodigoCelda      *string               `json:"codigo_celda"`
	Orden            *int16                `json:"orden"`
	Errors           []AttemptErrorRequest `json:"errors"`
}

type AttemptErrorRequest struct {
	CellID       string    `json:"cell_id"`
	Timestamp    time.Time `json:"timestamp"`
	ErrorType    string    `json:"error_type"`
	ErrorMessage string    `json:"error_message"`
}

func NewExerciseHandler(service *service.ExerciseAttempsService) *ExerciseHandler {
	return &ExerciseHandler{service: service}
}

func (handler *ExerciseHandler) CreateAttemptHandler(c *gin.Context) {

	var input ExerciseAttemptRequest
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Sintaxis inválida en el cuerpo JSON"})
		return
	}

	// 'sin_validar' es un desenlace real, no un valor raro: lo manda custom.js al
	// cerrar la pestana cuando el alumno dejo errores en un ejercicio SIN llegar
	// a ejecutar la celda de prueba. Rechazarlo, como se hacia antes, perdia la
	// senal de abandono: un alumno que peleo media hora y otro que ni abrio el
	// ejercicio quedaban identicos en los datos.
	switch input.ValidationResult {
	case "passed", "failed", "sin_validar":
	default:
		c.JSON(http.StatusBadRequest,
			gin.H{"error": "validation_result debe ser 'passed', 'failed' o 'sin_validar'"})
		return
	}

	// Un timestamp que no viene se convertía en 0001-01-01 y contaminaba todo
	// lo que ordena por fecha. custom.js siempre los manda; quien no, que se
	// entere.
	if input.ExerciseID == "" || input.AttemptAt.IsZero() {
		c.JSON(http.StatusBadRequest,
			gin.H{"error": "exercise_id y attempt_at son obligatorios"})
		return
	}
	for _, e := range input.Errors {
		if e.Timestamp.IsZero() {
			c.JSON(http.StatusBadRequest,
				gin.H{"error": "cada error debe traer timestamp"})
			return
		}
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
		PuntosMaximos:    input.PuntosMaximos,
		CodigoCelda:      input.CodigoCelda,
		Orden:            input.Orden,
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
