package tutor

import (
	"context"
	"errors"
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

// Modelo de repuesto, para cuando el principal está congestionado.
//
// Hace falta porque reintentar el MISMO modelo saturado no sirve de nada: la
// congestión de Google dura minutos, no milisegundos. El 2026-09-22 el tutor
// se quedó mudo en una reunión con el profesor, y el log contaba la historia
// entera: tres intentos contra gemini-3.5-flash, tres 503 «high demand», y un
// minuto largo de espera antes de rendirse. Medido ese mismo día, con la misma
// clave y en el mismo momento: gemini-3.5-flash y gemini-3.8-flash daban 503 a
// los 14-16 s, y gemini-3.5-flash-lite contestaba en 1 s.
//
// Que sea "lite" no es un problema para esta tarea: el tutor da pistas
// socráticas sobre un ejercicio de primer semestre, no escribe el programa.
func modeloAlterno() string {
	if modelo := os.Getenv("TUTOR_MODELO_ALTERNO"); modelo != "" {
		return modelo
	}
	return "gemini-3.5-flash-lite"
}

// ErrCongestionado distingue «Google está saturado» de «esto está roto». Son
// dos cosas distintas para el alumno: una se arregla esperando un minuto y la
// otra no se arregla sola. Antes las dos acababan en el mismo «el tutor no está
// disponible», que no dice qué hacer.
var ErrCongestionado = errors.New("los modelos del tutor están congestionados")

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

	// Se prueban modelos DISTINTOS, no el mismo tres veces. Insistir con uno
	// congestionado solo gasta el tiempo del alumno: son ~15 s por intento, y
	// así se llegaba al minuto antes de decirle que no.
	modelos := []string{modeloTutor()}
	if alt := modeloAlterno(); alt != "" && alt != modelos[0] {
		modelos = append(modelos, alt)
	}

	var err error
	for i, modelo := range modelos {
		var result *genai.GenerateContentResponse
		result, err = client.Models.GenerateContent(ctx, modelo, genai.Text(prompt), nil)

		if err == nil {
			// Text es un MÉTODO, no un campo: fmt.Sprint(result.Text) devolvía el
			// valor de la función ("%!v(func() string=0x14000...)") en vez de la
			// respuesta del tutor. Lo detecta 'go vet'.
			if i > 0 {
				log.Printf("[tutor] respondió el modelo de repuesto (%s)", modelo)
			}
			return result.Text(), nil
		}

		// Un error que no es congestión —una clave mala, un modelo retirado— no
		// se arregla cambiando de modelo: se corta aquí para no esconderlo.
		if !esTransitorio(err) {
			log.Printf("[tutor] %s falló y no es congestión: %v", modelo, err)
			return "", err
		}

		log.Printf("[tutor] %s congestionado: %v", modelo, err)

		if i < len(modelos)-1 {
			select {
			case <-time.After(500 * time.Millisecond):
			case <-ctx.Done():
				return "", ctx.Err()
			}
		}
	}

	log.Printf("[tutor] todos los modelos congestionados (%s): %v",
		strings.Join(modelos, ", "), err)
	return "", ErrCongestionado
}
