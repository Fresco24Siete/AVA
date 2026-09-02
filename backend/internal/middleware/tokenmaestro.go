package middleware

import (
	"crypto/subtle"
	"log"
	"net/http"
	"proxy-go/internal/auth"
	"strings"

	"github.com/gin-gonic/gin"
)

// CtxMaestro marca en el contexto que quien llama trae el token maestro (el
// Hub). Un docente no lo trae: trae un token con rol docente y curso.
const CtxMaestro = "metrics_maestro"

// RequireTokenMaestro protege el grupo /internal.
//
// Ese token es el más poderoso del sistema: con él se acuñan tokens de
// cualquier alumno. Solo lo tiene el Hub. El contenedor del docente recibe en
// cambio un token con rol docente acotado a su curso (ver RequireMaestroODocente).
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

// RequireMaestroODocente protege las rutas de /internal que usa el docente:
// el panel del curso, las notas, el mapeo de competencias.
//
// Deja pasar al token maestro (el Hub, o quien administre) y a un token de
// telemetría con rol docente, que el Hub acuña al arrancar el contenedor del
// instructor con SU curso dentro. Lo que el docente puede ver y escribir queda
// así acotado a ese curso: el handler compara el curso de la petición con
// CursoVerificado(c), y si no coincide responde 403. Antes todo instructor
// recibía el token maestro y con él podía leer el panel de cualquier curso y
// subir notas de cualquier curso.
func RequireMaestroODocente(secreto, tokenMaestro string) gin.HandlerFunc {
	return func(c *gin.Context) {
		recibido := strings.TrimSpace(
			strings.TrimPrefix(c.GetHeader("Authorization"), "Bearer"))
		if recibido == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized,
				gin.H{"error": "falta el token"})
			return
		}
		if tokenMaestro != "" &&
			subtle.ConstantTimeCompare([]byte(recibido), []byte(tokenMaestro)) == 1 {
			c.Set(CtxMaestro, true)
			c.Next()
			return
		}
		if secreto == "" {
			c.AbortWithStatusJSON(http.StatusServiceUnavailable,
				gin.H{"error": "esta función no está configurada en el servidor"})
			return
		}
		claims, err := auth.Verify(secreto, recibido)
		if err != nil || claims.Rol != auth.RolDocente || claims.CursoID == "" {
			if err != nil {
				log.Printf("[metrics] token de docente rechazado: %v", err)
			}
			c.AbortWithStatusJSON(http.StatusUnauthorized,
				gin.H{"error": "no autorizado"})
			return
		}
		c.Set(CtxEstudianteID, claims.EstudianteID)
		c.Set(CtxCursoID, claims.CursoID)
		c.Next()
	}
}

// EsMaestro dice si la petición trae el token maestro.
func EsMaestro(c *gin.Context) bool {
	v, ok := c.Get(CtxMaestro)
	return ok && v == true
}

// CursoAutorizado dice si quien llama puede tocar ese curso: el maestro puede
// con todos; un docente, solo con el suyo.
func CursoAutorizado(c *gin.Context, curso string) bool {
	if EsMaestro(c) {
		return true
	}
	_, cursoToken := IdentidadVerificada(c)
	return cursoToken != "" && cursoToken == curso
}
