// Package auth acuña y verifica los tokens de telemetría del AVA.
//
// El flujo que documenta notebook/metrics_bridge.py es este: el Hub, al crear el
// contenedor de un alumno, pide un token acotado a ese alumno y ese curso y lo
// inyecta como STUDENT_METRICS_TOKEN. El contenedor lo manda como Bearer en cada
// evento. El backend saca la identidad de los claims del token e IGNORA la que
// venga en el cuerpo.
//
// Ese último punto es la razón de ser de todo esto: el alumno puede leer su
// propio token dentro de su contenedor y hacer POST a mano. Si la identidad
// saliera del cuerpo, podría escribir telemetría a nombre de un compañero.
// Saliendo de los claims, lo peor que puede hacer es falsear su propia traza.
//
// Se firma con HMAC-SHA256 de la biblioteca estándar en vez de JWT para no
// añadir una dependencia por tres campos. El formato es
// base64url(payload).base64url(firma), que es un JWT sin la cabecera.
package auth

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"strings"
	"time"
)

// Duracion por defecto de un token. Un semestre es largo, pero el token se acuña
// en cada arranque de contenedor, así que no hace falta que dure más que una
// sesión de trabajo holgada.
const DuracionPorDefecto = 24 * time.Hour

var (
	ErrTokenMalFormado = errors.New("token mal formado")
	ErrFirmaInvalida   = errors.New("firma inválida")
	ErrTokenExpirado   = errors.New("token expirado")
	ErrSinSecreto      = errors.New("METRICS_TOKEN_SECRET no configurado")
)

// Claims es la identidad que viaja firmada. Nombres cortos para que el token no
// crezca sin motivo.
type Claims struct {
	EstudianteID string `json:"sid"`
	CursoID      string `json:"cid"`
	Cuadernillo  string `json:"nbid,omitempty"`
	// "docente" cuando el token lo acuñó el Hub para un instructor. Un token
	// así abre las rutas de /internal de SU curso (panel, notas), en vez de
	// darle al docente el token maestro, que abre todas las de todos.
	Rol    string `json:"rol,omitempty"`
	Expira int64  `json:"exp"`
}

// RolDocente es el valor del claim `rol` para los tokens de instructor.
const RolDocente = "docente"

func firmar(secreto, mensaje []byte) string {
	mac := hmac.New(sha256.New, secreto)
	mac.Write(mensaje)
	return base64.RawURLEncoding.EncodeToString(mac.Sum(nil))
}

// Mint devuelve un token firmado para ese estudiante y curso.
func Mint(secreto, estudianteID, cursoID, cuadernillo string, duracion time.Duration) (string, error) {
	return MintConRol(secreto, estudianteID, cursoID, cuadernillo, "", duracion)
}

// MintConRol es Mint con el claim `rol` (ver RolDocente).
func MintConRol(secreto, estudianteID, cursoID, cuadernillo, rol string, duracion time.Duration) (string, error) {
	if secreto == "" {
		return "", ErrSinSecreto
	}
	// Solo el cero significa "usa el valor por defecto". Una duración negativa se
	// respeta tal cual: produce un token ya vencido, que falla del lado seguro.
	if duracion == 0 {
		duracion = DuracionPorDefecto
	}
	cuerpo, err := json.Marshal(Claims{
		EstudianteID: estudianteID,
		CursoID:      cursoID,
		Cuadernillo:  cuadernillo,
		Rol:          rol,
		Expira:       time.Now().Add(duracion).Unix(),
	})
	if err != nil {
		return "", err
	}
	codificado := base64.RawURLEncoding.EncodeToString(cuerpo)
	return codificado + "." + firmar([]byte(secreto), []byte(codificado)), nil
}

// Verify comprueba la firma y la expiración, y devuelve los claims.
func Verify(secreto, token string) (*Claims, error) {
	if secreto == "" {
		return nil, ErrSinSecreto
	}
	partes := strings.Split(token, ".")
	if len(partes) != 2 || partes[0] == "" || partes[1] == "" {
		return nil, ErrTokenMalFormado
	}

	// hmac.Equal y no ==: comparar firmas con == filtra información por el
	// tiempo que tarda en fallar.
	esperada := firmar([]byte(secreto), []byte(partes[0]))
	if !hmac.Equal([]byte(esperada), []byte(partes[1])) {
		return nil, ErrFirmaInvalida
	}

	cuerpo, err := base64.RawURLEncoding.DecodeString(partes[0])
	if err != nil {
		return nil, ErrTokenMalFormado
	}
	var claims Claims
	if err := json.Unmarshal(cuerpo, &claims); err != nil {
		return nil, ErrTokenMalFormado
	}
	if claims.Expira > 0 && time.Now().Unix() > claims.Expira {
		return nil, ErrTokenExpirado
	}
	return &claims, nil
}
