package tutor

import (
	"context"
	"log"
	"os"

	"google.golang.org/genai"
)

var GeminiClientsPool = make(chan *genai.Client, 2)

func init() {

	Key_1 := os.Getenv("GOOGLE_API_KEY_1")
	Key_2 := os.Getenv("GOOGLE_API_KEY_2")

	keys := []string{Key_1, Key_2}
	
	for _, key := range keys {
		client, err := genai.NewClient(context.Background(), &genai.ClientConfig{
			APIKey:  os.Getenv(key),
			Backend: genai.BackendGeminiAPI,
		})
		
		if err != nil {
			log.Fatalf("Falla crítica al crear el cliente: %v", err) 
		}
		
		GeminiClientsPool <- client
	}
}