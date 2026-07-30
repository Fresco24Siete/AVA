package main

import (
	"log"
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

	//Encender el servidor
	log.Println("Servidor operando en el puerto 8080...")
	if err := router.Run(":8080"); err != nil {
		log.Fatalf("Error al arrancar el servidor: %v", err)
	}
}