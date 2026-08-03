package tutor

import (
	"context"
	"fmt"
	"log"
	
	"proxy-go/internal/models"


	"google.golang.org/genai"
)

func ConnecGeminiApi(ctx context.Context, client *genai.Client, data *models.ApiMessage) (string, error) {
	
	prompt := BuildTutorPrompt(
		"Jonh Doe",
		data.NombreEstudiante,
		data.Historial,
		data.ContextoEjercicio,
		data.Mensaje,
	)
	
	result, err := client.Models.GenerateContent(
		ctx, 
		"gemini-2.5-flash",
		genai.Text(prompt),
		nil,
	)

	if err != nil {
		log.Printf("falla en la pregunta a Gemini: %v", err)
		return "", err
	}
	
	return fmt.Sprint(result.Text), nil
}





