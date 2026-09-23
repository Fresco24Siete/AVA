package handler

import (
	"log"
	"net/http"
	"proxy-go/internal/middleware"
	"proxy-go/internal/models"
	"proxy-go/internal/service"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type CuadernilloRatingHandler struct {
	service *service.CuadernilloRatingService
}

func NewCuadernilloRatingHandler(service *service.CuadernilloRatingService) *CuadernilloRatingHandler {
	return &CuadernilloRatingHandler{service: service}
}

func (handler *CuadernilloRatingHandler) CreateCuadernilloHandler(c *gin.Context) {

	var input models.CuadernilloRating

	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Sintaxis inválida en el cuerpo JSON"})
		return
	}

	// El rango lo imponía solo el CHECK de la base, que aquí se veía como un
	// 500 sin explicación.
	if input.Rating < 1 || input.Rating > 5 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "rating debe estar entre 1 y 5"})
		return
	}
	if input.CuadernilloID == "" || input.SubmittedAt.IsZero() {
		c.JSON(http.StatusBadRequest,
			gin.H{"error": "cuadernillo_id y submitted_at son obligatorios"})
		return
	}

	// Las dos preguntas opcionales. Se validan aquí y no solo con el CHECK de
	// la base por el mismo motivo que el rating: allí el error llega como un
	// 500 sin explicación. Vacío es "no contestó" y es válido.
	if input.Tiempo != nil && (*input.Tiempo < 1 || *input.Tiempo > 4) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "tiempo debe estar entre 1 y 4"})
		return
	}
	if input.Freno != nil && !frenoValido(*input.Freno) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "freno no está en la lista"})
		return
	}

	// La identidad sale del token, no del cuerpo, igual que en los intentos.
	// Aquí se tomaba del cuerpo: cualquier alumno, con su propio token, podía
	// escribir o pisar (es un UPSERT) la valoración de un compañero o de otro
	// curso. Sin token verificado (secreto sin configurar) se respeta el cuerpo.
	studentID, courseID := middleware.IdentidadVerificada(c)
	if studentID == "" {
		studentID = input.StudentID
	}
	if courseID == "" {
		courseID = input.CourseID
	}

	cuadernillo := &models.CuadernilloRating{
		ID:            uuid.New(),
		CourseID:      courseID,
		CuadernilloID: input.CuadernilloID,
		StudentID:     studentID,
		SubmittedAt:   input.SubmittedAt,
		Rating:        input.Rating,
		Comment:       input.Comment,
		Tiempo:        input.Tiempo,
		Freno:         input.Freno,
		Entregado:     input.Entregado,
		Origen:        input.Origen,
	}

	err := handler.service.CreateCuadernilloServicie(cuadernillo)

	if err != nil {
		// El error se registra: sin esto, cualquier fallo de la base llegaba al
		// alumno como un 500 sin pista y no quedaba rastro en ningún log.
		log.Printf("[rating] no se pudo guardar la valoración de %s en %s: %v",
			studentID, input.CuadernilloID, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "no se pudo guardar la valoración"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"message": "success to create cuadernillo"})

}

// La lista es cerrada a propósito: cada valor es una acción distinta del
// docente (reescribir el enunciado, repasar el concepto en clase, dar más
// ejemplos de sintaxis, explicar los errores del corrector, acortar el
// cuadernillo). Un campo de texto libre aquí no sería agregable.
func frenoValido(f string) bool {
	switch f {
	case "enunciado", "concepto", "sintaxis", "error", "tiempo", "nada":
		return true
	}
	return false
}
