package tutor

import (
	"context"
	"log"
	"os"

	"proxy-go/internal/models"


	"google.golang.org/genai"
)

// Nombre con el que el tutor se presenta al estudiante. Sale del entorno para
// no recompilar por cambiarlo; "Jonh Doe" era un placeholder y el alumno lo
// veía tal cual en el saludo.
func aliasTutor() string {
	if alias := os.Getenv("TUTOR_ALIAS"); alias != "" {
		return alias
	}
	return "Ava"
}

func ConnecGeminiApi(ctx context.Context, client *genai.Client, data *models.ApiMessage) (string, error) {

	prompt := BuildTutorPrompt(
		aliasTutor(),
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
	
	// Text es un MÉTODO, no un campo: fmt.Sprint(result.Text) devolvía el valor
	// de la función ("%!v(func() string=0x14000...)") en vez de la respuesta del
	// tutor. Lo detecta 'go vet'.
	return result.Text(), nil
}





