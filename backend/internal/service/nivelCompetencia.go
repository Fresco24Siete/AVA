package service

import "fmt"

// Umbrales del nivel por microcompetencia.
//
// Están aquí, juntos y como constantes, a propósito: el encargo pedía poder
// ajustarlos sin migrar la base, y porque un corte guardado (corte_competencia)
// registra los valores con los que se calculó, para poder recalcularlo si
// mañana cambian en vez de quedarse mintiendo.
//
// De dónde salen: ver docs/modelo_microcompetencias.md §3. En resumen, no son
// intuiciones —salen del corte natural que hacen los datos reales del curso—.
const (
	// Ejercicios vistos por debajo de los cuales NO se da nivel.
	//
	// Con menos de tres, un nivel es ruido: quien intentó uno y lo falló no
	// está en N1, está sin medir. Y la diferencia importa, porque decirle al
	// docente "N1" sobre un alumno del que no sabemos nada es peor que
	// callarse.
	MinimoEvidencia = 3

	// resueltos / vistos. ¿Resuelve lo que intenta?
	CoberturaN3 = 0.80
	CoberturaN2 = 0.40

	// fallos / resueltos. ¿Cuánto le cuesta cada uno?
	//
	// Hace falta además de la cobertura: en los datos reales, once de dieciocho
	// estudiantes tienen cobertura 1.00 en I3 y su coste va de 0.0 a 5.2. La
	// cobertura sola los metería a todos en el mismo nivel; el coste es lo que
	// separa "lo sacó con soltura" de "lo sacó a duras penas".
	CostoN3 = 2.0

	// Ejercicios abandonados (dejados en sin_validar y nunca resueltos) a
	// partir de los cuales ya no es N3.
	AbandonosN3 = 3
)

// SenalesCompetencia son los números crudos de un estudiante en una
// competencia. Los produce la consulta; el nivel NO se calcula en SQL.
type SenalesCompetencia struct {
	Vistos    int
	Resueltos int
	Fallos    int
	Abandonos int
}

// NivelCompetencia traduce las señales a N1/N2/N3.
//
// Devuelve nil cuando no hay evidencia suficiente. nil NO es N1: son cosas
// distintas y quien pinte la pantalla tiene que distinguirlas. Por eso el
// segundo valor explica siempre el porqué, en lenguaje que el docente pueda
// leer tal cual.
//
// El cálculo vive en Go y no en la vista porque los umbrales deben poder
// ajustarse sin migrar la base.
func NivelCompetencia(s SenalesCompetencia) (*int, string) {
	if s.Vistos < MinimoEvidencia {
		return nil, fmt.Sprintf(
			"sin evidencia suficiente: %d de %d ejercicios intentados",
			s.Vistos, MinimoEvidencia)
	}

	cobertura := float64(s.Resueltos) / float64(s.Vistos)

	// max(resueltos, 1): sin esto, quien no resolvió nada divide por cero. Y
	// tratarlo como "coste infinito" tampoco aporta, porque con cobertura 0 ya
	// cae en N1 por la cobertura.
	divisor := s.Resueltos
	if divisor < 1 {
		divisor = 1
	}
	costo := float64(s.Fallos) / float64(divisor)

	n3, n2, n1 := 3, 2, 1

	if cobertura >= CoberturaN3 && costo < CostoN3 && s.Abandonos < AbandonosN3 {
		return &n3, fmt.Sprintf(
			"resuelve %d de %d con %.1f fallos por ejercicio",
			s.Resueltos, s.Vistos, costo)
	}

	// Por qué no llegó a N3, dicho con precisión: si el docente va a hablar con
	// el alumno, "le cuesta" y "se rinde" piden conversaciones distintas.
	if cobertura >= CoberturaN2 {
		switch {
		case s.Abandonos >= AbandonosN3:
			return &n2, fmt.Sprintf(
				"resuelve %d de %d, pero dejó %d sin terminar",
				s.Resueltos, s.Vistos, s.Abandonos)
		case costo >= CostoN3:
			return &n2, fmt.Sprintf(
				"resuelve %d de %d, pero le cuesta: %.1f fallos por ejercicio",
				s.Resueltos, s.Vistos, costo)
		default:
			return &n2, fmt.Sprintf(
				"resuelve %d de %d", s.Resueltos, s.Vistos)
		}
	}

	return &n1, fmt.Sprintf(
		"resuelve %d de %d ejercicios intentados", s.Resueltos, s.Vistos)
}
