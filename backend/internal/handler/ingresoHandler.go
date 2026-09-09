package handler

import (
	"log"
	"net/http"

	"proxy-go/internal/repository"

	"github.com/gin-gonic/gin"
)

// IngresoHandler registra quién entró: lo llama el Hub en cada lanzamiento
// LTI, con el token maestro, justo antes de arrancar el contenedor.
//
// Es la única fuente de nombres y correos de la base. La telemetría viaja con
// el user_id numérico de Moodle y nada más; sin esto, el panel del docente solo
// puede enseñar números.
type IngresoHandler struct {
	repo *repository.EstudiantesRepository
}

func NewIngresoHandler(r *repository.EstudiantesRepository) *IngresoHandler {
	return &IngresoHandler{repo: r}
}

// RegistrarHandler responde a POST /internal/lti/ingreso.
func (h *IngresoHandler) RegistrarHandler(c *gin.Context) {
	var in repository.Ingreso
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Sintaxis inválida en el cuerpo JSON"})
		return
	}
	if in.CourseID == "" || in.StudentID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "curso_id y estudiante_id son obligatorios"})
		return
	}
	if in.Rol != "instructor" {
		in.Rol = "estudiante"
	}
	if err := h.repo.Registrar(in); err != nil {
		log.Printf("[ingreso] %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "no se pudo registrar el ingreso"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"ok": true})
}
