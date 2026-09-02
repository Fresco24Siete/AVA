package handler

import (
	"log"
	"net/http"
	"proxy-go/internal/middleware"
	"proxy-go/internal/repository"
	"proxy-go/internal/service"

	"github.com/gin-gonic/gin"
)

type ProgresoHandler struct {
	service *service.ProgresoService
}

func NewProgresoHandler(s *service.ProgresoService) *ProgresoHandler {
	return &ProgresoHandler{service: s}
}

// MiProgresoHandler responde a GET /api/mi-progreso.
//
// La identidad sale SIEMPRE del token, nunca de un parametro. Es una consulta de
// lectura, y sin esa regla bastaria cambiar un ?student_id= para leer el
// progreso y las notas de un companero.
func (h *ProgresoHandler) MiProgresoHandler(c *gin.Context) {
	estudiante, curso := middleware.IdentidadVerificada(c)
	if estudiante == "" || curso == "" {
		c.JSON(http.StatusUnauthorized,
			gin.H{"error": "el token no identifica a ningún estudiante"})
		return
	}

	cuadernillos, err := h.service.Cuadernillos(estudiante, curso)
	if err != nil {
		log.Printf("[progreso] cuadernillos de %s: %v", estudiante, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "no se pudo leer el progreso"})
		return
	}
	competencias, err := h.service.Competencias(estudiante, curso)
	if err != nil {
		log.Printf("[progreso] competencias de %s: %v", estudiante, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "no se pudo leer el progreso"})
		return
	}

	if cuadernillos == nil {
		cuadernillos = []repository.ResumenCuadernillo{}
	}
	if competencias == nil {
		competencias = []repository.ResumenCompetencia{}
	}

	c.JSON(http.StatusOK, gin.H{
		"cuadernillos": cuadernillos,
		"competencias": competencias,
	})
}
