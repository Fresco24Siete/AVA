package handler

import (
	"crypto/subtle"
	"log"
	"net/http"
	"proxy-go/internal/service"
	"strings"

	"github.com/gin-gonic/gin"
)

// CompetenciasRequest es el mapeo que emite build.py al construir los
// cuadernillos: qué indicadores de aprendizaje evalúa cada ejercicio.
//
//	{"semana_02": {"ejercicio_3": ["I3","I5"], ...}, ...}
//
// Va aparte del notebook y no viaja con cada intento a propósito: es diseño del
// curso, no dato del estudiante. Al resolverse por JOIN al consultar, corregir
// una etiqueta mal puesta corrige también todo el histórico ya recogido.
type CompetenciasRequest map[string]map[string][]string

type CompetenciasHandler struct {
	service      *service.CompetenciasService
	tokenMaestro string
}

func NewCompetenciasHandler(s *service.CompetenciasService, tokenMaestro string) *CompetenciasHandler {
	return &CompetenciasHandler{service: s, tokenMaestro: tokenMaestro}
}

// CargarHandler responde a POST /internal/competencias.
//
// Reemplaza el mapeo COMPLETO de cada cuadernillo que venga en el cuerpo, y no
// toca los que no vengan: así se puede recargar una sola semana sin borrar las
// demás. Reemplazar en vez de acumular es deliberado — si un ejercicio deja de
// evaluar una competencia, esa fila tiene que desaparecer.
func (h *CompetenciasHandler) CargarHandler(c *gin.Context) {
	if h.tokenMaestro == "" {
		c.JSON(http.StatusServiceUnavailable,
			gin.H{"error": "carga de competencias no configurada en el servidor"})
		return
	}
	recibido := strings.TrimSpace(strings.TrimPrefix(c.GetHeader("Authorization"), "Bearer"))
	if subtle.ConstantTimeCompare([]byte(recibido), []byte(h.tokenMaestro)) != 1 {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "no autorizado"})
		return
	}

	var input CompetenciasRequest
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Sintaxis inválida en el cuerpo JSON"})
		return
	}
	if len(input) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "el mapeo viene vacío"})
		return
	}

	total, err := h.service.Reemplazar(input)
	if err != nil {
		log.Printf("[competencias] no se pudo cargar el mapeo: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "no se pudo guardar el mapeo"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":      "mapeo cargado",
		"cuadernillos": len(input),
		"relaciones":   total,
	})
}
