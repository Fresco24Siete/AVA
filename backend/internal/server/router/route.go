package router

import (
	"os"
	"proxy-go/internal/handler"
	"proxy-go/internal/middleware"
	"proxy-go/internal/repository"
	"proxy-go/internal/service"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/jmoiron/sqlx"
)


func ConfigureRouter (db *sqlx.DB) *gin.Engine{

	router := gin.Default()

	router.Use(cors.New(cors.Config{
		AllowOrigins: []string{"https://jupyteruisproyecto.duckdns.org"},
		AllowMethods: []string{"GET", "POST"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Authorization"},
		AllowCredentials: true,
    	MaxAge:           12 * time.Hour,
	}))

	//exercise inyection
	exerciseRepository := repository.NewExerciseAttempsRepository(db)
	attempRepository := repository.NewAttemptErrorRepository(db)
	exerciseService :=  service.NewExerciseAttempsService(exerciseRepository, attempRepository)
	exerciseHandler := handler.NewExerciseHandler(exerciseService)

	//Cuadernillo inyection
	cuadernilloRepository := repository.NewCuadernilloRatingRepository(db)
	cuadernilloService := service.NewCuadernilloRatingService(cuadernilloRepository)
	cuadernilloHandler := handler.NewCuadernilloRatingHandler(cuadernilloService)


	// Telemetria: el Hub acuña un token por alumno al crear su contenedor y
	// metrics_bridge lo manda como Bearer en cada evento. Sin esto, el backend
	// aceptaba cualquier POST anonimo y con la identidad puesta en el cuerpo.
	secretoMetricas := os.Getenv("METRICS_TOKEN_SECRET")
	tokenMaestro := os.Getenv("METRICS_API_TOKEN")
	metricsTokenHandler := handler.NewMetricsTokenHandler(secretoMetricas, tokenMaestro)

	// Mapeo ejercicio -> competencias, que emite build.py al construir.
	competenciasRepository := repository.NewCompetenciasRepository(db)
	competenciasService := service.NewCompetenciasService(competenciasRepository)
	competenciasHandler := handler.NewCompetenciasHandler(competenciasService, tokenMaestro)

	// Interno: solo lo llama el Hub por la red de Docker. NO exponer por Caddy.
	interno := router.Group("/internal")
	{
		interno.POST("/lti/mint-metrics-token", metricsTokenHandler.MintHandler)
		interno.POST("/competencias", competenciasHandler.CargarHandler)
	}

	api := router.Group("/api")
	{
		// Ingesta de telemetria: identidad tomada del token, no del cuerpo.
		ingesta := api.Group("")
		ingesta.Use(middleware.RequireMetricsToken(secretoMetricas))
		{
			ingesta.POST("/exercises/attempts", exerciseHandler.CreateAttemptHandler)
			ingesta.POST("/cuadernillos/ratings", cuadernilloHandler.CreateCuadernilloHandler)
		}

		// El tutor no lleva token: lo llama el mismo contenedor del alumno y no
		// escribe nada en la base.
		api.POST("/exercise/tutorIA", handler.ChatHandler)
	}

	return router
}
