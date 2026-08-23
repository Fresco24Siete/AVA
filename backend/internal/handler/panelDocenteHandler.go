package handler

import (
	"net/http"
	"regexp"

	"proxy-go/internal/middleware"
	"proxy-go/internal/repository"

	"github.com/gin-gonic/gin"
)

// PanelDocenteHandler sirve la analítica del curso al contenedor del docente.
//
// Va en /internal y no en /api a propósito: el kernel del alumno hereda su
// propio token de métricas en el entorno del proceso, así que cualquier ruta de
// /api es alcanzable desde una celda de código. Esta devuelve el rendimiento de
// todo el grupo; solo puede pedirla quien tenga el token maestro, que únicamente
// están el Hub y el contenedor del docente.
type PanelDocenteHandler struct {
	repo *repository.PanelDocenteRepository
}

func NewPanelDocenteHandler(r *repository.PanelDocenteRepository) *PanelDocenteHandler {
	return &PanelDocenteHandler{repo: r}
}

var cursoValido = regexp.MustCompile(`^[A-Za-z0-9_.-]{1,64}$`)

// PanelHandler responde a GET /internal/curso/:curso/panel.
//
// El curso viene en la ruta y se filtra SIEMPRE en el WHERE. Un docente solo
// puede pedir el curso de su token; el maestro, cualquiera.
func (h *PanelDocenteHandler) PanelHandler(c *gin.Context) {
	curso := c.Param("curso")
	if !cursoValido.MatchString(curso) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "curso no válido"})
		return
	}
	if !middleware.CursoAutorizado(c, curso) {
		c.JSON(http.StatusForbidden, gin.H{"error": "ese curso no es el tuyo"})
		return
	}

	// Cada bloque se pide por separado y un fallo no se lleva la página entera:
	// el docente prefiere cuatro secciones y un hueco a una pantalla de error.
	respuesta := gin.H{"curso_id": curso}
	fallos := []string{}

	if v, err := h.repo.PorCuadernillo(curso); err != nil {
		fallos = append(fallos, "cuadernillos")
	} else {
		respuesta["cuadernillos"] = v
	}
	if v, err := h.repo.PorEjercicio(curso); err != nil {
		fallos = append(fallos, "ejercicios")
	} else {
		respuesta["ejercicios"] = v
	}
	if v, err := h.repo.PorCompetencia(curso); err != nil {
		fallos = append(fallos, "competencias")
	} else {
		respuesta["competencias"] = v
	}
	if v, err := h.repo.Malentendidos(curso); err != nil {
		fallos = append(fallos, "malentendidos")
	} else {
		respuesta["malentendidos"] = v
	}
	if v, err := h.repo.EnRiesgo(curso); err != nil {
		fallos = append(fallos, "en_riesgo")
	} else {
		respuesta["en_riesgo"] = v
	}
	if v, err := h.repo.Salud(curso); err != nil {
		fallos = append(fallos, "salud")
	} else {
		respuesta["salud"] = v
	}

	if len(fallos) > 0 {
		respuesta["no_disponible"] = fallos
	}
	c.JSON(http.StatusOK, respuesta)
}
