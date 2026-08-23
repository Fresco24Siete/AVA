package auth

import (
	"strings"
	"testing"
	"time"
)

const secreto = "secreto-de-prueba"

func TestMintYVerify(t *testing.T) {
	token, err := Mint(secreto, "alumno-1", "28053", "semana_01", time.Hour)
	if err != nil {
		t.Fatalf("Mint devolvió error: %v", err)
	}
	claims, err := Verify(secreto, token)
	if err != nil {
		t.Fatalf("Verify devolvió error: %v", err)
	}
	if claims.EstudianteID != "alumno-1" || claims.CursoID != "28053" ||
		claims.Cuadernillo != "semana_01" {
		t.Fatalf("los claims no coinciden: %+v", claims)
	}
}

// Lo que de verdad importa: que no se pueda cambiar el estudiante del token.
func TestFirmaDetectaManipulacion(t *testing.T) {
	token, _ := Mint(secreto, "alumno-1", "28053", "", time.Hour)
	partes := strings.Split(token, ".")
	otro, _ := Mint(secreto, "alumno-2", "28053", "", time.Hour)
	cuerpoAjeno := strings.Split(otro, ".")[0]

	// Cuerpo de otro alumno con la firma del primero.
	if _, err := Verify(secreto, cuerpoAjeno+"."+partes[1]); err != ErrFirmaInvalida {
		t.Fatalf("se aceptó un cuerpo manipulado; error=%v", err)
	}
}

func TestOtroSecretoNoValida(t *testing.T) {
	token, _ := Mint(secreto, "alumno-1", "28053", "", time.Hour)
	if _, err := Verify("otro-secreto", token); err != ErrFirmaInvalida {
		t.Fatalf("validó con el secreto equivocado; error=%v", err)
	}
}

func TestTokenExpirado(t *testing.T) {
	token, _ := Mint(secreto, "alumno-1", "28053", "", -time.Minute)
	if _, err := Verify(secreto, token); err != ErrTokenExpirado {
		t.Fatalf("aceptó un token vencido; error=%v", err)
	}
}

func TestFormatosInvalidos(t *testing.T) {
	for _, caso := range []string{"", "sinpunto", "a.b.c", ".", "a."} {
		if _, err := Verify(secreto, caso); err == nil {
			t.Fatalf("aceptó el token mal formado %q", caso)
		}
	}
}

func TestSinSecreto(t *testing.T) {
	if _, err := Mint("", "a", "b", "", time.Hour); err != ErrSinSecreto {
		t.Fatalf("Mint sin secreto debería fallar; error=%v", err)
	}
	if _, err := Verify("", "lo.que.sea"); err != ErrSinSecreto {
		t.Fatalf("Verify sin secreto debería fallar; error=%v", err)
	}
}

// El token de un alumno no lleva rol; el de un docente lleva "docente". Es lo
// que separa poder leer el panel del curso de no poder.
func TestRolDocente(t *testing.T) {
	alumno, _ := Mint(secreto, "alumno-1", "28053", "", time.Hour)
	claims, err := Verify(secreto, alumno)
	if err != nil || claims.Rol != "" {
		t.Fatalf("el token de alumno no debe llevar rol: %+v, %v", claims, err)
	}
	docente, _ := MintConRol(secreto, "9002", "28053", "", RolDocente, time.Hour)
	claims, err = Verify(secreto, docente)
	if err != nil || claims.Rol != RolDocente || claims.CursoID != "28053" {
		t.Fatalf("el token de docente debe llevar rol y curso: %+v, %v", claims, err)
	}
}
