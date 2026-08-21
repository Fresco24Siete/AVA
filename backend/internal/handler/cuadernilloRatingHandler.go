package handler

import (
	"net/http"
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

	cuadernillo := &models.CuadernilloRating{
		ID:            uuid.New(),
		CourseID:      input.CourseID,
		CuadernilloID: input.CuadernilloID,
		StudentID:     input.StudentID,
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
