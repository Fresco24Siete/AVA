package tutor

import (
	"context"
	"log"
	"os"

	"google.golang.org/genai"
)

// Pool de clientes de Gemini. Cada petición toma uno y lo devuelve al terminar,
// así que el canal hace de semáforo: como máximo se atienden tantas preguntas
// en paralelo como claves haya configuradas.
var GeminiClientsPool = make(chan *genai.Client, 2)

// Cuántos clientes se crearon de verdad. Si es 0, el tutor no está configurado
// y el handler debe responder 503 en vez de quedarse esperando un cliente que
// nunca va a llegar.
var clientesDisponibles int

func init() {

	claves := map[string]string{
		"GOOGLE_API_KEY_1": os.Getenv("GOOGLE_API_KEY_1"),
		"GOOGLE_API_KEY_2": os.Getenv("GOOGLE_API_KEY_2"),
	}

	for nombre, clave := range claves {
		if clave == "" {
			log.Printf("[tutor] %s no está configurada; se omite ese cliente.", nombre)
			continue
		}

		// OJO: aquí va la CLAVE, no os.Getenv(clave). Con os.Getenv se buscaba
		// una variable de entorno *llamada* como la clave, que no existe, así
		// que ambos clientes quedaban con APIKey vacía y NewClient fallaba.
		client, err := genai.NewClient(context.Background(), &genai.ClientConfig{
			APIKey:  clave,
			Backend: genai.BackendGeminiAPI,
		})

		if err != nil {
			// No es log.Fatalf a propósito. Esto corre en un init(), o sea antes
			// de main(): si mata el proceso, se cae TODO el backend (métricas y
			// calificaciones incluidas) porque el tutor no pudo arrancar. Se
			// registra el fallo y la API sigue en pie sin tutor.
			log.Printf("[tutor] no se pudo crear el cliente de %s: %v", nombre, err)
			continue
		}

		GeminiClientsPool <- client
		clientesDisponibles++
	}

	if clientesDisponibles == 0 {
		log.Print("[tutor] sin claves de Gemini válidas: el tutor responderá 503. " +
			"Revisa GOOGLE_API_KEY_1 y GOOGLE_API_KEY_2 en el .env.")
	} else {
		log.Printf("[tutor] %d cliente(s) de Gemini listos.", clientesDisponibles)
	}
}

// HayClientes indica si el tutor quedó configurado al arrancar.
func HayClientes() bool {
	return clientesDisponibles > 0
}
