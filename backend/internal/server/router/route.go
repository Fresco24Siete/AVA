package router

import (
	"proxy-go/internal/handler"
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
		AllowOrigins: []string{"https://jupyteruisproyecto.dunkdns.org/"},
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


	api := router.Group("/api")
	{
		api.POST("/exercises/attempts", exerciseHandler.CreateAttemptHandler)
		api.POST("cuadernillos/ratings", cuadernilloHandler.CreateCuadernilloHandler)

	}

	return router
}
