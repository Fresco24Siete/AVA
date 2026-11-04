package service

import "testing"

// Las fronteras importan más que los casos cómodos: un umbral mal escrito
// (>= donde iba >) mueve de nivel a estudiantes reales sin que nada falle.
func TestNivelCompetencia(t *testing.T) {
	casos := []struct {
		nombre   string
		senales  SenalesCompetencia
		esperado *int // nil = sin evidencia suficiente
	}{
		{
			// Lo más importante de toda la función: sin evidencia NO es N1.
			"cero actividad no da nivel, y no es N1",
			SenalesCompetencia{}, nil,
		},
		{
			"justo por debajo del mínimo de evidencia",
			SenalesCompetencia{Vistos: 2, Resueltos: 2}, nil,
		},
		{
			"justo en el mínimo de evidencia, ya se puede medir",
			SenalesCompetencia{Vistos: 3, Resueltos: 3}, ptr(3),
		},
		{
			"cobertura exactamente en el umbral de N3 entra en N3",
			SenalesCompetencia{Vistos: 5, Resueltos: 4, Fallos: 4}, ptr(3),
		},
		{
			// 3/5 = 0.60: pasa N2, no llega a N3.
			"cobertura justo por debajo del umbral de N3 se queda en N2",
			SenalesCompetencia{Vistos: 5, Resueltos: 3}, ptr(2),
		},
		{
			// 8/4 = 2.0, y el umbral es estricto: 2.0 ya NO es N3.
			"coste exactamente en el umbral NO es N3",
			SenalesCompetencia{Vistos: 4, Resueltos: 4, Fallos: 8}, ptr(2),
		},
		{
			"coste justo por debajo del umbral sí es N3",
			SenalesCompetencia{Vistos: 4, Resueltos: 4, Fallos: 7}, ptr(3),
		},
		{
			"abandonos exactamente en el umbral NO es N3",
			SenalesCompetencia{Vistos: 4, Resueltos: 4, Abandonos: 3}, ptr(2),
		},
		{
			"abandonos justo por debajo sí es N3",
			SenalesCompetencia{Vistos: 4, Resueltos: 4, Abandonos: 2}, ptr(3),
		},
		{
			// 2/5 = 0.40, justo en el umbral de N2.
			"cobertura exactamente en el umbral de N2 entra en N2",
			SenalesCompetencia{Vistos: 5, Resueltos: 2}, ptr(2),
		},
		{
			// 1/5 = 0.20.
			"cobertura por debajo del umbral de N2 cae a N1",
			SenalesCompetencia{Vistos: 5, Resueltos: 1}, ptr(1),
		},
		{
			// El caso que divide por cero si nadie lo protege.
			"lo intentó y no resolvió nada: N1, sin reventar",
			SenalesCompetencia{Vistos: 6, Resueltos: 0, Fallos: 30}, ptr(1),
		},
		{
			// Quien más trabaja acumula más fallos, y contarlos a secas lo
			// hundiría. Con coste 1.9 sigue siendo N3.
			"muchos fallos pero lo resuelve todo con soltura: N3",
			SenalesCompetencia{Vistos: 13, Resueltos: 13, Fallos: 25}, ptr(3),
		},
		{
			// El estudiante real que justificó la fórmula: 68 fallos y los 13
			// ejercicios que intentó, resueltos. Contar fallos a secas lo
			// pondría en N1, que es justo el error que se quería evitar. La
			// fórmula lo deja en N2: resuelve todo, pero le cuesta 5.2 fallos
			// por ejercicio, y esa distinción entre "lo domina" y "lo saca a
			// duras penas" es la razón de que el coste exista.
			"el caso real de 68 fallos: N2, ni N3 ni N1",
			SenalesCompetencia{Vistos: 13, Resueltos: 13, Fallos: 68}, ptr(2),
		},
	}

	for _, c := range casos {
		t.Run(c.nombre, func(t *testing.T) {
			nivel, motivo := NivelCompetencia(c.senales)
			if !mismoNivel(nivel, c.esperado) {
				t.Errorf("nivel = %s, se esperaba %s (señales %+v)",
					texto(nivel), texto(c.esperado), c.senales)
			}
			if motivo == "" {
				t.Error("el motivo nunca debe ir vacío: es lo que lee el docente")
			}
		})
	}
}

// El motivo no es decorativo: se pinta en el panel. Si un nivel N2 no dice por
// qué no llegó a N3, el docente no sabe si hablar de método o de constancia.
func TestMotivoDistingueCostoDeAbandono(t *testing.T) {
	_, porCosto := NivelCompetencia(SenalesCompetencia{Vistos: 4, Resueltos: 4, Fallos: 8})
	_, porAbandono := NivelCompetencia(SenalesCompetencia{Vistos: 4, Resueltos: 4, Abandonos: 3})
	if porCosto == porAbandono {
		t.Errorf("dos N2 por causas distintas dan el mismo motivo: %q", porCosto)
	}
}

func ptr(n int) *int { return &n }

func mismoNivel(a, b *int) bool {
	if a == nil || b == nil {
		return a == nil && b == nil
	}
	return *a == *b
}

func texto(n *int) string {
	if n == nil {
		return "sin nivel"
	}
	return string(rune('0' + *n))
}
