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

	// Notas de cuadernillo: las sube el contenedor del docente tras calificar.
	notasRepository := repository.NewNotasRepository(db)
	notasService := service.NewNotasService(notasRepository)
	notasHandler := handler.NewNotasHandler(notasService, tokenMaestro)

	// Entregas: el alumno manda su cuadernillo terminado y el backend lo deja en
	// submitted/ de nbgrader con la identidad que dice el token. Es la unica via
	// de entrega: un volumen compartido no serviria, porque dentro de los
	// contenedores todos los alumnos son el mismo usuario del sistema y podrian
	// leerse entre ellos.
	entregaHandler := handler.NewEntregaHandler(os.Getenv("NBGRADER_BASE"))

	// Progreso del alumno: lectura acotada a quien pregunta, por su token.
	progresoRepository := repository.NewProgresoRepository(db)
	progresoService := service.NewProgresoService(progresoRepository)
	progresoHandler := handler.NewProgresoHandler(progresoService)

	// Interno: solo lo llama el Hub por la red de Docker. NO exponer por Caddy.
	interno := router.Group("/internal")
	{
		interno.POST("/lti/mint-metrics-token", metricsTokenHandler.MintHandler)
		interno.POST("/competencias", competenciasHandler.CargarHandler)
		interno.POST("/notas", notasHandler.RegistrarHandler)
	}

	api := router.Group("/api")
	{
		// Ingesta de telemetria: identidad tomada del token, no del cuerpo.
		ingesta := api.Group("")
		ingesta.Use(middleware.RequireMetricsToken(secretoMetricas))
		{
			ingesta.POST("/exercises/attempts", exerciseHandler.CreateAttemptHandler)
			ingesta.POST("/cuadernillos/ratings", cuadernilloHandler.CreateCuadernilloHandler)
			ingesta.GET("/mi-progreso", progresoHandler.MiProgresoHandler)
			ingesta.POST("/entregas", entregaHandler.RecibirHandler)

			// El tutor tambien va aqui. Estaba fuera, con el argumento de que no
			// escribe en la base, pero lo que gasta es la cuota de Gemini: desde
			// una celda de codigo se podia llamar en bucle sin identificarse.
			// tutor_bridge ya manda el token del alumno.
			ingesta.POST("/exercise/tutorIA", handler.ChatHandler)
		}
	}

	return router
}
