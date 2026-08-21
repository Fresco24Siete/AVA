package handler

import (
	"log"
	"net/http"
	"proxy-go/internal/models"
	"proxy-go/internal/service"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// NotaRequest es una nota tal como la lee registrar-notas del libro de nbgrader.
type NotaRequest struct {
	StudentID       string  `json:"student_id"`
	PuntosObtenidos float64 `json:"puntos_obtenidos"`
	PuntosMaximos   float64 `json:"puntos_maximos"`
}

type NotasLoteRequest struct {
	CourseID      string        `json:"course_id"`
	CuadernilloID string        `json:"cuadernillo_id"`
	Origen        string        `json:"origen"`
	Notas         []NotaRequest `json:"notas"`
}

type NotasHandler struct {
	service      *service.NotasService
	tokenMaestro string
}

func NewNotasHandler(s *service.NotasService, tokenMaestro string) *NotasHandler {
	return &NotasHandler{service: s, tokenMaestro: tokenMaestro}
}

// RegistrarHandler responde a POST /internal/notas.
//
// Interno: lo llama el contenedor del docente tras calificar, con el token
// maestro. Las notas no las manda nunca el navegador del alumno.
func (h *NotasHandler) RegistrarHandler(c *gin.Context) {
	// La autorización la pone middleware.RequireTokenMaestro sobre /internal.

	var input NotasLoteRequest
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Sintaxis inválida en el cuerpo JSON"})
		return
	}
	if input.CourseID == "" || input.CuadernilloID == "" {
		c.JSON(http.StatusBadRequest,
			gin.H{"error": "course_id y cuadernillo_id son obligatorios"})
		return
	}
	if len(input.Notas) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "no viene ninguna nota"})
		return
	}

	origen := input.Origen
	if origen == "" {
		origen = "nbgrader"
	}
	if origen != "nbgrader" && origen != "provisional" {
		c.JSON(http.StatusBadRequest,
			gin.H{"error": "origen debe ser 'nbgrader' o 'provisional'"})
		return
	}

	ahora := time.Now()
	notas := make([]models.CuadernilloNota, 0, len(input.Notas))
	for _, n := range input.Notas {
		if n.StudentID == "" {
			continue // una entrega sin estudiante no significa nada
		}
		// Una nota mayor que el maximo casi siempre es un error de lectura del
		// libro, no un alumno excepcional. Se corta antes de guardarla.
		if n.PuntosMaximos < 0 || n.PuntosObtenidos < 0 ||
			n.PuntosObtenidos > n.PuntosMaximos {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "nota fuera de rango para " + n.StudentID,
			})
			return
		}
		notas = append(notas, models.CuadernilloNota{
			ID:              uuid.New(),
			CourseID:        input.CourseID,
			CuadernilloID:   input.CuadernilloID,
			StudentID:       n.StudentID,
			PuntosObtenidos: n.PuntosObtenidos,
			PuntosMaximos:   n.PuntosMaximos,
			CalificadoEn:    ahora,
			Origen:          origen,
		})
	}

	guardadas, err := h.service.GuardarLote(notas)
	if err != nil {
		log.Printf("[notas] no se pudieron guardar: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "no se pudieron guardar las notas"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":        "notas registradas",
		"cuadernillo_id": input.CuadernilloID,
		"guardadas":      guardadas,
	})
}
