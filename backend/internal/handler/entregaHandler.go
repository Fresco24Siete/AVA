package handler

import (
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"regexp"

	"proxy-go/internal/middleware"

	"github.com/gin-gonic/gin"
)

// EntregaHandler recibe el cuadernillo terminado del alumno y lo deja donde
// nbgrader espera encontrarlo.
//
// Por qué pasa por aquí y no por un volumen compartido, que sería lo obvio:
// dentro de los contenedores todos los alumnos son el mismo usuario del sistema
// (jovyan, uid 1000). Cualquier carpeta que uno pueda escribir, otro la puede
// leer desde una celda de código, y los permisos con los que nbgrader protege su
// buzón —pensados para un servidor con una cuenta por persona— no separan nada
// aquí. Un buzón compartido sería un buzón donde cada quien lee lo de los demás.
//
// El backend sí sabe quién es quién: la identidad sale del token que acuñó el
// Hub con los datos de LTI, no de lo que mande el navegador. Así que el alumno
// manda su cuadernillo por HTTP y este handler lo escribe en submitted/ con el
// identificador verificado. El alumno nunca monta el volumen de nbgrader.
type EntregaHandler struct {
	raiz string // normalmente /srv/nbgrader
}

func NewEntregaHandler(raiz string) *EntregaHandler {
	if raiz == "" {
		raiz = "/srv/nbgrader"
	}
	return &EntregaHandler{raiz: raiz}
}

type EntregaRequest struct {
	CuadernilloID string          `json:"cuadernillo_id"`
	Archivo       string          `json:"archivo"`
	Notebook      json.RawMessage `json:"notebook"`
}

// Nombres que se convierten en rutas: se acotan a lo que de verdad usa el AVA.
// Sin esto, un cuadernillo_id como "../../source" escribiría sobre las
// soluciones del docente.
var nombreSeguro = regexp.MustCompile(`^[A-Za-z0-9_.@-]{1,120}$`)

func seguro(partes ...string) bool {
	for _, p := range partes {
		if p == "" || p == "." || p == ".." || !nombreSeguro.MatchString(p) {
			return false
		}
	}
	return true
}

// RecibirHandler responde a POST /api/entregas.
func (h *EntregaHandler) RecibirHandler(c *gin.Context) {
	estudianteID, cursoID := middleware.IdentidadVerificada(c)
	if estudianteID == "" || cursoID == "" {
		c.JSON(http.StatusUnauthorized,
			gin.H{"error": "no se pudo verificar quién entrega"})
		return
	}

	var input EntregaRequest
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Sintaxis inválida en el cuerpo JSON"})
		return
	}
	if len(input.Notebook) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "falta el cuadernillo"})
		return
	}
	// Tiene que ser un .ipynb: si no, se estaría guardando cualquier cosa con
	// nombre de cuadernillo y el docente lo descubriría al calificar.
	var nb map[string]any
	if err := json.Unmarshal(input.Notebook, &nb); err != nil || nb["cells"] == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "eso no es un cuadernillo válido"})
		return
	}

	archivo := input.Archivo
	if archivo == "" {
		archivo = input.CuadernilloID + ".ipynb"
	}
	if !seguro(cursoID, estudianteID, input.CuadernilloID, archivo) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "nombre no permitido"})
		return
	}

	// nbgrader espera submitted/<alumno>/<tarea>/<notebook>.ipynb. Escribiendo
	// ahí, el docente solo tiene que pulsar Calificar: no hace falta Recoger,
	// porque no hay buzón intermedio del que recoger.
	destino := filepath.Join(h.raiz, cursoID, "submitted", estudianteID, input.CuadernilloID)
	if err := os.MkdirAll(destino, 0o755); err != nil {
		c.JSON(http.StatusInternalServerError,
			gin.H{"error": "no se pudo guardar la entrega"})
		return
	}

	// Se escribe a un temporal y se renombra: si la conexión se corta a mitad,
	// el docente encuentra la entrega anterior entera en vez de un JSON truncado
	// que rompe la calificación de esa persona.
	final := filepath.Join(destino, archivo)
	tmp := final + ".parcial"
	if err := os.WriteFile(tmp, input.Notebook, 0o644); err != nil {
		c.JSON(http.StatusInternalServerError,
			gin.H{"error": "no se pudo guardar la entrega"})
		return
	}
	if err := os.Rename(tmp, final); err != nil {
		os.Remove(tmp)
		c.JSON(http.StatusInternalServerError,
			gin.H{"error": "no se pudo guardar la entrega"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"ok":             true,
		"cuadernillo_id": input.CuadernilloID,
		"bytes":          len(input.Notebook),
	})
}
