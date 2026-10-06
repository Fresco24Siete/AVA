package service

import (
	"log"
	"sync"

	"proxy-go/internal/models"
	"proxy-go/internal/repository"
)

type ExerciseAttempsService struct {
	repositoryExersice *repository.ExerciseAttempsRepository
	repositoryAttemp   *repository.AttemptErrorRepository
	repositoryComp     *repository.CompetenciasRepository

	// Pares (cuadernillo, ejercicio) por los que ya se avisó. Sin esto, un
	// cuadernillo sin mapeo escribe una línea por cada celda que ejecuta cada
	// alumno —cientos al día— y el aviso se vuelve ruido que nadie lee.
	huerfanosAvisados sync.Map
}

func NewExerciseAttempsService(
	repositoryExersice *repository.ExerciseAttempsRepository,
	repositoryAttemp *repository.AttemptErrorRepository,
	repositoryComp *repository.CompetenciasRepository,
) *ExerciseAttempsService {
	return &ExerciseAttempsService{
		repositoryExersice: repositoryExersice,
		repositoryAttemp:   repositoryAttemp,
		repositoryComp:     repositoryComp,
	}
}

func (service *ExerciseAttempsService) CreateAttemptWithErrors(exercise *models.ExerciseAttempt, attempts []models.AttemptError) error {
	if err := service.repositoryExersice.CreateAttemptWithErrors(exercise, attempts); err != nil {
		return err
	}
	service.avisarSiHuerfano(exercise.CuadernilloID, exercise.ExerciseID)
	return nil
}

// avisarSiHuerfano deja constancia en el log cuando llega telemetría de un
// ejercicio que no está en el catálogo de competencias.
//
// # Por qué avisar y no rechazar
//
// La tentación es responder 400 y así "garantizar" que todo lo que entra es
// medible. Sería el peor error posible: un ejercicio queda sin mapeo por un
// fallo de OPERACIÓN —nadie ejecutó `cargar-competencias` después de publicar
// una semana nueva—, no por un fallo del alumno. Rechazar convertiría un olvido
// del equipo en pérdida permanente del trabajo de un estudiante, que además no
// se entera de nada. La telemetría se guarda siempre.
//
// # Por qué hace falta avisar
//
// Hasta ahora esto fallaba en el silencio más absoluto: el intento se guardaba,
// el alumno recibía 201, y después desaparecía de todo análisis por competencia
// porque el JOIN con ejercicio_competencias es INNER. Ni una línea de log: este
// handler ni siquiera importaba el paquete log. La única pista era un contador
// en la sección de salud del panel, que hay que ir a buscar a propósito.
//
// Es exactamente lo que pasó con la fila de cuadernillo 'Fabio' que lleva meses
// en la base: un alumno trabajando sobre una copia renombrada. Nadie lo supo
// hasta que se miró a mano.
//
// Un fallo al consultar no se propaga: el intento YA está guardado y perder la
// respuesta 201 por un problema del aviso sería cambiar un problema pequeño por
// uno grande.
func (service *ExerciseAttempsService) avisarSiHuerfano(cuadernillo, ejercicio string) {
	if service.repositoryComp == nil {
		return
	}
	clave := cuadernillo + "/" + ejercicio
	if _, visto := service.huerfanosAvisados.Load(clave); visto {
		return
	}

	competencias, err := service.repositoryComp.DeEjercicio(cuadernillo, ejercicio)
	if err != nil {
		log.Printf("telemetria: no se pudo comprobar el mapeo de %s: %v", clave, err)
		return
	}
	if len(competencias) > 0 {
		return
	}

	service.huerfanosAvisados.Store(clave, true)
	log.Printf("telemetria: %s no tiene competencias asignadas. El intento SI se "+
		"guardo, pero no contara en el avance por competencia hasta que se cargue "+
		"el mapeo (cargar-competencias en el contenedor del docente).", clave)
}
