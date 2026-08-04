package tutor

import (
	"context"
	"log"
	"os"
	"strings"
	"time"

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

// Modelo de Gemini. Sale del entorno porque Google retira modelos: "gemini-2.5-flash"
// estaba fijo aquí y dejó de estar disponible para cuentas nuevas, así que la API
// devolvía 404 y el tutor no respondía. Cambiarlo no debería exigir recompilar.
func modeloTutor() string {
	if modelo := os.Getenv("TUTOR_MODELO"); modelo != "" {
		return modelo
	}
	return "gemini-3.5-flash"
}

// Gemini devuelve 503 UNAVAILABLE ("high demand") de forma intermitente cuando el
// modelo está congestionado. Medido: el modelo más nuevo fallaba 1 de cada 3
// llamadas. Sin reintento, al alumno le aparece "el tutor no está disponible"
// aunque todo esté bien configurado.
func esTransitorio(err error) bool {
	msg := strings.ToUpper(err.Error())
	return strings.Contains(msg, "UNAVAILABLE") ||
		strings.Contains(msg, "RESOURCE_EXHAUSTED") ||
		strings.Contains(msg, "HIGH DEMAND") ||
		strings.Contains(msg, "ERROR 503") ||
		strings.Contains(msg, "ERROR 429")
}

func ConnecGeminiApi(ctx context.Context, client *genai.Client, data *models.ApiMessage) (string, error) {

	prompt := BuildTutorPrompt(
		aliasTutor(),
		data.NombreEstudiante,
		data.Historial,
		data.ContextoEjercicio,
		data.Mensaje,
	)
	
	modelo := modeloTutor()
	var err error

	// Hasta 3 intentos ante congestión del modelo. Las esperas son cortas porque
	// hay un alumno esperando la respuesta en pantalla.
	for intento := 1; intento <= 3; intento++ {
		var result *genai.GenerateContentResponse
		result, err = client.Models.GenerateContent(ctx, modelo, genai.Text(prompt), nil)

		if err == nil {
			// Text es un MÉTODO, no un campo: fmt.Sprint(result.Text) devolvía el
			// valor de la función ("%!v(func() string=0x14000...)") en vez de la
			// respuesta del tutor. Lo detecta 'go vet'.
			return result.Text(), nil
		}

		if !esTransitorio(err) {
			break
		}

		log.Printf("Gemini congestionado (intento %d/3): %v", intento, err)

		select {
		case <-time.After(time.Duration(intento) * time.Second):
		case <-ctx.Done():
			return "", ctx.Err()
		}
	}

	log.Printf("falla en la pregunta a Gemini: %v", err)
	return "", err
}





