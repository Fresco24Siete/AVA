package middleware

import (
	"crypto/subtle"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

// RequireTokenMaestro protege el grupo /internal.
//
// Ese token es el más poderoso del sistema: con él se acuñan tokens de
// cualquier alumno, se suben notas y se recarga el mapeo de competencias. Solo
// lo tienen el Hub y el contenedor del docente, y nunca sale de la red interna
// de Docker.
//
// Vivía copiado a mano dentro de cada handler de /internal. Tres copias del
// mismo bloque significan tres sitios donde olvidarlo, y el cuarto handler que
// se añada sin él queda abierto sin que nada lo señale. Aquí es una sola línea
// en el router y no se puede olvidar.
//
// Se conservan los dos comportamientos que ya tenía:
//   - 503 si el servidor no tiene token configurado. No es que el cliente se
//     equivoque: es que esta parte del AVA no está montada, y decir 401 mandaría
//     a buscar el fallo donde no está.
//   - comparación en tiempo constante, para no filtrar el token a base de medir
//     cuánto tarda en responder.
func RequireTokenMaestro(tokenMaestro string) gin.HandlerFunc {
	return func(c *gin.Context) {
		if tokenMaestro == "" {
			c.AbortWithStatusJSON(http.StatusServiceUnavailable,
				gin.H{"error": "esta función no está configurada en el servidor"})
			return
		}
		recibido := strings.TrimSpace(
			strings.TrimPrefix(c.GetHeader("Authorization"), "Bearer"))
		if subtle.ConstantTimeCompare([]byte(recibido), []byte(tokenMaestro)) != 1 {
			c.AbortWithStatusJSON(http.StatusUnauthorized,
				gin.H{"error": "no autorizado"})
			return
		}
		c.Next()
	}
}
