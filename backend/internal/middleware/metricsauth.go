// Package middleware protege los endpoints de ingesta de telemetría.
package middleware

import (
	"log"
	"net/http"
	"proxy-go/internal/auth"
	"strings"

	"github.com/gin-gonic/gin"
)

// Claves con las que el middleware deja la identidad verificada en el contexto.
// Los handlers la leen de aquí y no del cuerpo de la petición.
const (
	CtxEstudianteID = "metrics_estudiante_id"
	CtxCursoID      = "metrics_curso_id"
	CtxCuadernillo  = "metrics_cuadernillo"
)

// RequireMetricsToken valida el Bearer que manda metrics_bridge y deja los
// claims en el contexto.
//
// Si `secreto` viene vacío, el middleware deja pasar y solo avisa por el log. Es
// deliberado: el despliegue actual llevaba tiempo funcionando sin token, y hacer
// obligatorio el token de golpe habría dejado a los alumnos sin telemetría en
// mitad de una clase. Con el secreto configurado —que es como debe quedar— la
// validación es estricta.
func RequireMetricsToken(secreto string) gin.HandlerFunc {
	if secreto == "" {
		log.Println("[metrics] AVISO: METRICS_TOKEN_SECRET vacío; la telemetría se acepta SIN verificar identidad")
	}
	return func(c *gin.Context) {
		if secreto == "" {
			c.Next()
			return
		}

		cabecera := c.GetHeader("Authorization")
		token := strings.TrimSpace(strings.TrimPrefix(cabecera, "Bearer"))
		if token == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized,
				gin.H{"error": "falta el token de telemetría"})
			return
		}

		claims, err := auth.Verify(secreto, token)
		if err != nil {
			log.Printf("[metrics] token rechazado: %v", err)
			c.AbortWithStatusJSON(http.StatusUnauthorized,
				gin.H{"error": "token de telemetría inválido"})
			return
		}

		c.Set(CtxEstudianteID, claims.EstudianteID)
		c.Set(CtxCursoID, claims.CursoID)
		c.Set(CtxCuadernillo, claims.Cuadernillo)
		c.Next()
	}
}

// IdentidadVerificada devuelve el estudiante y el curso que vienen del token.
// Si no hay token verificado (secreto sin configurar), devuelve vacío y el
// handler se queda con lo que traiga el cuerpo.
func IdentidadVerificada(c *gin.Context) (estudianteID, cursoID string) {
	if v, ok := c.Get(CtxEstudianteID); ok {
		estudianteID, _ = v.(string)
	}
	if v, ok := c.Get(CtxCursoID); ok {
		cursoID, _ = v.(string)
	}
	return estudianteID, cursoID
}
