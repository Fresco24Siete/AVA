package handler

import (
	"net/http"
	"proxy-go/internal/models"
	"proxy-go/pkg/tutor"

	"github.com/gin-gonic/gin"
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


	client := <- tutor.GeminiClientsPool
	

	defer func() {
		tutor.GeminiClientsPool <- client
	}()


	respuesta, err := tutor.ConnecGeminiApi(ctx, client, &data)
	
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Error procesando la solicitud en el modelo",
		})
		return
	}

	c.String(http.StatusOK, respuesta)
}