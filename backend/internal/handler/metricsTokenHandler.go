package handler

import (
	"log"
	"net/http"
	"proxy-go/internal/auth"

	"github.com/gin-gonic/gin"
)

// MintMetricsTokenRequest es lo que manda el Hub en cada arranque de contenedor
// (ver _mintear_token_estudiante en hub_config/jupyterhub_config.py).
type MintMetricsTokenRequest struct {
	EstudianteID      string `json:"estudiante_id"`
	CursoID           string `json:"curso_id"`
	CuadernilloCodigo string `json:"cuadernillo_codigo"`
	// Vacío para un alumno; "docente" para un instructor. Con ese rol el token
	// abre las rutas de /internal de su curso (panel, notas), y así el
	// contenedor del docente no necesita el token maestro.
	Rol string `json:"rol"`
}

// MetricsTokenHandler acuña los tokens de telemetría.
type MetricsTokenHandler struct {
	secretoFirma string // firma los tokens que se entregan
	tokenMaestro string // autoriza a quien puede pedirlos (solo el Hub)
}

func NewMetricsTokenHandler(secretoFirma, tokenMaestro string) *MetricsTokenHandler {
	if secretoFirma == "" || tokenMaestro == "" {
		log.Println("[metrics] AVISO: falta METRICS_TOKEN_SECRET o METRICS_API_TOKEN; " +
			"el acuñado de tokens responderá 503 y la telemetría no se guardará")
	}
	return &MetricsTokenHandler{secretoFirma: secretoFirma, tokenMaestro: tokenMaestro}
}

// MintHandler responde a POST /internal/lti/mint-metrics-token.
//
// Es un endpoint interno: solo lo llama el Hub, desde la red de Docker, con el
// token maestro. No debe exponerse por Caddy.
func (h *MetricsTokenHandler) MintHandler(c *gin.Context) {
	// Quien puede pedir tokens lo decide middleware.RequireTokenMaestro sobre
	// /internal. Aquí solo queda lo propio de este handler: sin secreto de
	// firma no hay token que acuñar.
	if h.secretoFirma == "" {
		c.JSON(http.StatusServiceUnavailable,
			gin.H{"error": "acuñado de tokens no configurado en el servidor"})
		return
	}

	var input MintMetricsTokenRequest
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Sintaxis inválida en el cuerpo JSON"})
		return
	}
	if input.EstudianteID == "" || input.CursoID == "" {
		c.JSON(http.StatusBadRequest,
			gin.H{"error": "estudiante_id y curso_id son obligatorios"})
		return
	}

	if input.Rol != "" && input.Rol != auth.RolDocente {
		c.JSON(http.StatusBadRequest, gin.H{"error": "rol debe ir vacío o ser 'docente'"})
		return
	}

	token, err := auth.MintConRol(h.secretoFirma, input.EstudianteID, input.CursoID,
		input.CuadernilloCodigo, input.Rol, auth.DuracionPorDefecto)
	if err != nil {
		log.Printf("[metrics] no se pudo acuñar el token: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "no se pudo acuñar el token"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"token": token})
}
