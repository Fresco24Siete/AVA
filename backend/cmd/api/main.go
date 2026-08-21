package main

import (
	"log"
	"os"
	"proxy-go/config"
	"proxy-go/internal/server/router"

	"proxy-go/pkg/database"
)



func main(){


	//cargar variables
	config := config.LoadConfig()

	conexionBD, err := database.ConectarDB(config)

	if err != nil {
		log.Fatal("error al conectar a la base de datos:", err)
	}
	//Configurar el Enrutador
	router := router.ConfigureRouter(conexionBD)

	// Puerto configurable. Dentro de Docker siempre es el 8080 y da igual, pero
	// al levantarlo a mano -- en la maquina del profesor, o para probar contra
	// una base de pruebas -- el 8080 suele estar ocupado por otra cosa.
	puerto := os.Getenv("PORT")
	if puerto == "" {
		puerto = "8080"
	}

	log.Printf("Servidor operando en el puerto %s...", puerto)
	if err := router.Run(":" + puerto); err != nil {
		log.Fatalf("Error al arrancar el servidor: %v", err)
	}
}