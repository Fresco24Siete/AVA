package router

import (
	"os"
	"proxy-go/internal/handler"
	"proxy-go/internal/middleware"
	"proxy-go/internal/repository"
	"proxy-go/internal/service"
	"strings"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/jmoiron/sqlx"
)

func ConfigureRouter(db *sqlx.DB) *gin.Engine {

	router := gin.Default()

	// El origen permitido era el dominio de la primera VM, escrito a mano. Al
	// mudar el AVA de maquina quedaba apuntando a un sitio que ya no existe, y
	// nadie se entera: las llamadas del puente de metricas van de contenedor a
	// contenedor por la red de Docker, sin navegador y por tanto sin CORS. Solo
	// rompe el dia que algo llame desde la pagina del alumno.
	origenes := []string{}
	for _, o := range strings.Split(os.Getenv("CORS_ORIGENES"), ",") {
		if o = strings.TrimSpace(o); o != "" {
			origenes = append(origenes, o)
		}
	}
	if len(origenes) == 0 {
		if d := strings.TrimSpace(os.Getenv("AVA_DOMINIO")); d != "" {
			origenes = append(origenes, "https://"+d)
		}
	}
	corsCfg := cors.Config{
		AllowMethods:     []string{"GET", "POST"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Authorization"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}
	if len(origenes) > 0 {
		corsCfg.AllowOrigins = origenes
		router.Use(cors.New(corsCfg))
	}
	// Sin origenes configurados no se monta CORS: es mas seguro no responder
	// cabeceras de permiso que responderlas con un dominio equivocado.

	//exercise inyection
	exerciseRepository := repository.NewExerciseAttempsRepository(db)
	attempRepository := repository.NewAttemptErrorRepository(db)
	exerciseService := service.NewExerciseAttempsService(exerciseRepository, attempRepository)
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

	// Las entregas de los alumnos ya no pasan por aqui: van al servicio
	// nbexchange (el exchange de nbgrader por HTTP, ver NBEXCHANGE.md), que
	// tambien sabe quien es cada quien por el token del Hub, y el docente las
	// recoge con Collect. Este backend ya no monta el volumen de nbgrader.

	// Analitica del curso para el docente. Va en /internal porque devuelve el
	// rendimiento de todo el grupo: cualquier ruta de /api es alcanzable desde
	// una celda del alumno, que hereda su token en el entorno del proceso.
	panelDocenteRepository := repository.NewPanelDocenteRepository(db)
	// Quien es cada estudiante: lo registra el Hub en cada ingreso LTI, y el
	// panel del docente lo usa para listar a su gente por nombre.
	estudiantesRepository := repository.NewEstudiantesRepository(db)
	panelDocenteHandler := handler.NewPanelDocenteHandler(panelDocenteRepository, estudiantesRepository)
	ingresoHandler := handler.NewIngresoHandler(estudiantesRepository)

	// Progreso del alumno: lectura acotada a quien pregunta, por su token.
	progresoRepository := repository.NewProgresoRepository(db)
	progresoService := service.NewProgresoService(progresoRepository)
	progresoHandler := handler.NewProgresoHandler(progresoService)

	// Interno: solo se llama por la red de Docker. NO exponer por Caddy. La
	// autorizacion va en el grupo, no dentro de cada handler: asi no hay forma
	// de anadir una ruta y olvidarla.
	//
	// Dos niveles. Acunar tokens es cosa del Hub y exige el maestro. Lo demas
	// lo usa el docente desde su contenedor con un token acotado a su curso:
	// el handler comprueba que el curso que pide es el del token.
	interno := router.Group("/internal")
	{
		hub := interno.Group("")
		hub.Use(middleware.RequireTokenMaestro(tokenMaestro))
		hub.POST("/lti/mint-metrics-token", metricsTokenHandler.MintHandler)
		hub.POST("/lti/ingreso", ingresoHandler.RegistrarHandler)

		docente := interno.Group("")
		docente.Use(middleware.RequireMaestroODocente(secretoMetricas, tokenMaestro))
		docente.POST("/competencias", competenciasHandler.CargarHandler)
		docente.POST("/notas", notasHandler.RegistrarHandler)
		docente.GET("/curso/:curso/panel", panelDocenteHandler.PanelHandler)
		docente.GET("/curso/:curso/estudiante/:estudiante", panelDocenteHandler.FichaHandler)
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

			// El tutor tambien va aqui. Estaba fuera, con el argumento de que no
			// escribe en la base, pero lo que gasta es la cuota de Gemini: desde
			// una celda de codigo se podia llamar en bucle sin identificarse.
			// tutor_bridge ya manda el token del alumno.
			ingesta.POST("/exercise/tutorIA", handler.ChatHandler)
		}
	}

	return router
}
