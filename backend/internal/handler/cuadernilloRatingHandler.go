package handler

import (
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
	}

	err := handler.service.CreateCuadernilloServicie(cuadernillo)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "fail to create cuaderniilo"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"message": "success to create cuadernillo"})

}
