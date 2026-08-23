package handler

import (
	"log"
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
	repo        *repository.PanelDocenteRepository
	estudiantes *repository.EstudiantesRepository
}

func NewPanelDocenteHandler(r *repository.PanelDocenteRepository,
	e *repository.EstudiantesRepository) *PanelDocenteHandler {
	return &PanelDocenteHandler{repo: r, estudiantes: e}
}

var estudianteValido = regexp.MustCompile(`^[A-Za-z0-9_.@-]{1,120}$`)

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
	// Quién es quién: el listado y el mapa id -> nombre con el que el panel
	// pone nombre en las demás secciones.
	if v, err := h.estudiantes.Listar(curso); err != nil {
		fallos = append(fallos, "estudiantes")
		log.Printf("[panel] estudiantes: %v", err)
	} else {
		respuesta["estudiantes"] = v
	}
	if v, err := h.estudiantes.Nombres(curso); err != nil {
		fallos = append(fallos, "nombres")
	} else {
		respuesta["nombres"] = v
	}

	if len(fallos) > 0 {
		respuesta["no_disponible"] = fallos
	}
	c.JSON(http.StatusOK, respuesta)
}

// FichaHandler responde a GET /internal/curso/:curso/estudiante/:estudiante:
// el recorrido de una persona, ejercicio por ejercicio.
func (h *PanelDocenteHandler) FichaHandler(c *gin.Context) {
	curso, estudiante := c.Param("curso"), c.Param("estudiante")
	if !cursoValido.MatchString(curso) || !estudianteValido.MatchString(estudiante) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "curso o estudiante no válido"})
		return
	}
	if !middleware.CursoAutorizado(c, curso) {
		c.JSON(http.StatusForbidden, gin.H{"error": "ese curso no es el tuyo"})
		return
	}
	ejercicios, err := h.estudiantes.Ficha(curso, estudiante)
	if err != nil {
		log.Printf("[panel] ficha de %s: %v", estudiante, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "no se pudo leer la ficha"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"curso_id": curso, "student_id": estudiante,
		"ejercicios": ejercicios})
}
