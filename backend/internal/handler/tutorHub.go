package handler

import (
	"net/http"
	"proxy-go/internal/models"
	"proxy-go/pkg/tutor"

	"github.com/gin-gonic/gin"
	"google.golang.org/genai"
)

func ChatHandler(c *gin.Context) {

	ctx := c.Request.Context()

	var data models.ApiMessage
	if err := c.ShouldBindJSON(&data); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Datos inválidos o JSON malformado",
		})
		return
	}

	// Sin claves configuradas el pool está vacío para siempre. Sin este corte,
	// el <-pool de abajo bloquea la petición hasta que el alumno se cansa.
	if !tutor.HayClientes() {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"error": "El tutor no está configurado en este momento",
		})
		return
	}

	// Espera a que se libere un cliente, pero sin quedarse colgado si el alumno
	// cierra la pestaña o se agota el timeout de la petición.
	var client *genai.Client
	select {
	case client = <-tutor.GeminiClientsPool:
		defer func() { tutor.GeminiClientsPool <- client }()
	case <-ctx.Done():
		c.JSON(http.StatusGatewayTimeout, gin.H{
			"error": "El tutor está ocupado, intenta de nuevo",
		})
		return
	}

	respuesta, err := tutor.ConnecGeminiApi(ctx, client, &data)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Error procesando la solicitud en el modelo",
		})
		return
	}

	c.String(http.StatusOK, respuesta)
}
