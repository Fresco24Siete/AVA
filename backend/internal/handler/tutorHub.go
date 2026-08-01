package handler

import (
	"net/http"
	"proxy-go/internal/models"
	"proxy-go/pkg/tutor"

	"github.com/gin-gonic/gin"
)

//Sin control de condiciones de carrera

func TutorHub(c *gin.Context){

	var input models.ApiMessage

	if err := c.ShouldBindJSON(&input) ; err != nil{
		c.JSON(http.StatusBadRequest, gin.H{"error": "Sintaxis inválida en el cuerpo JSON"})
		return
	}

	respuesta, err := tutor.ConnecGeminiApi(&input)

	if err != nil{
		c.JSON(http.StatusInternalServerError, gin.H{"error" : "fail to create cuaderniilo"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
    "resultado": respuesta,
	})

}