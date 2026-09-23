package handler

import (
	"encoding/json"
	"log"
	"net/http"
	"regexp"
	"strings"
	"unicode/utf8"

	"proxy-go/internal/middleware"
	"proxy-go/internal/repository"
	"proxy-go/internal/service"

	"github.com/gin-gonic/gin"
)

// PanelDocenteHandler sirve la analítica del curso al contenedor del docente.
//
// Va en /internal y no en /api a propósito: el kernel del alumno hereda su
// propio token de métricas en el entorno del proceso, así que cualquier ruta de
// /api es alcanzable desde una celda de código. Esta devuelve el rendimiento de
// todo el grupo; solo puede pedirla quien tenga el token maestro, que únicamente
// están el Hub y el contenedor del docente.
type PanelDocenteHandler struct {
	repo        *repository.PanelDocenteRepository
	estudiantes *repository.EstudiantesRepository
}

func NewPanelDocenteHandler(r *repository.PanelDocenteRepository,
	e *repository.EstudiantesRepository) *PanelDocenteHandler {
	return &PanelDocenteHandler{repo: r, estudiantes: e}
}

var estudianteValido = regexp.MustCompile(`^[A-Za-z0-9_.@-]{1,120}$`)

var cursoValido = regexp.MustCompile(`^[A-Za-z0-9_.-]{1,64}$`)

// PanelHandler responde a GET /internal/curso/:curso/panel.
//
// El curso viene en la ruta y se filtra SIEMPRE en el WHERE. Un docente solo
// puede pedir el curso de su token; el maestro, cualquiera.
func (h *PanelDocenteHandler) PanelHandler(c *gin.Context) {
	curso := c.Param("curso")
	if !cursoValido.MatchString(curso) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "curso no válido"})
		return
	}
	if !middleware.CursoAutorizado(c, curso) {
		c.JSON(http.StatusForbidden, gin.H{"error": "ese curso no es el tuyo"})
		return
	}

	// Cada bloque se pide por separado y un fallo no se lleva la página entera:
	// el docente prefiere cuatro secciones y un hueco a una pantalla de error.
	respuesta := gin.H{"curso_id": curso}
	fallos := []string{}

	if v, err := h.repo.PorCuadernillo(curso); err != nil {
		fallos = append(fallos, "cuadernillos")
	} else {
		respuesta["cuadernillos"] = v
	}
	if v, err := h.repo.PorEjercicio(curso); err != nil {
		fallos = append(fallos, "ejercicios")
	} else {
		respuesta["ejercicios"] = v
	}
	if v, err := h.repo.PorCompetencia(curso); err != nil {
		fallos = append(fallos, "competencias")
	} else {
		respuesta["competencias"] = v
	}
	// El nivel de cada persona en cada competencia, en una sola consulta, para
	// que el listado lo enseñe en la fila sin abrir «Ver detalle» de nadie.
	// Es la misma SQL y el mismo cálculo de nivel que la ficha individual.
	if v, err := h.estudiantes.CompetenciasDelCurso(curso); err != nil {
		fallos = append(fallos, "competencias_por_estudiante")
		log.Printf("[panel] competencias por estudiante: %v", err)
	} else {
		for i := range v {
			nivelDe(&v[i].CompetenciaDeEstudiante)
		}
		respuesta["competencias_por_estudiante"] = v
	}
	if v, err := h.repo.PorDia(curso); err != nil {
		fallos = append(fallos, "actividad_por_dia")
	} else {
		respuesta["actividad_por_dia"] = v
	}
	if v, err := h.repo.Malentendidos(curso); err != nil {
		fallos = append(fallos, "malentendidos")
	} else {
		respuesta["malentendidos"] = v
	}
	// Lo que los alumnos dijeron del cuadernillo. Iba a la base desde hacía
	// meses y no se leía en ninguna parte.
	if v, err := h.repo.PorValoracion(curso); err != nil {
		fallos = append(fallos, "valoraciones")
	} else {
		respuesta["valoraciones"] = v
	}
	if v, err := h.repo.PorFreno(curso); err != nil {
		fallos = append(fallos, "frenos")
	} else {
		respuesta["frenos"] = v
	}
	if v, err := h.repo.PorComentario(curso); err != nil {
		fallos = append(fallos, "comentarios")
	} else {
		respuesta["comentarios"] = v
	}
	if v, err := h.repo.EnRiesgo(curso); err != nil {
		fallos = append(fallos, "en_riesgo")
	} else {
		respuesta["en_riesgo"] = v
	}
	if v, err := h.repo.Salud(curso); err != nil {
		fallos = append(fallos, "salud")
	} else {
		respuesta["salud"] = v
	}
	// Quién es quién: el listado y el mapa id -> nombre con el que el panel
	// pone nombre en las demás secciones.
	if v, err := h.estudiantes.Listar(curso); err != nil {
		fallos = append(fallos, "estudiantes")
		log.Printf("[panel] estudiantes: %v", err)
	} else {
		respuesta["estudiantes"] = v
	}
	if v, err := h.estudiantes.Nombres(curso); err != nil {
		fallos = append(fallos, "nombres")
	} else {
		respuesta["nombres"] = v
	}

	if len(fallos) > 0 {
		respuesta["no_disponible"] = fallos
	}
	c.JSON(http.StatusOK, respuesta)
}

// FichaHandler responde a GET /internal/curso/:curso/estudiante/:estudiante:
// el recorrido de una persona, ejercicio por ejercicio.
func (h *PanelDocenteHandler) FichaHandler(c *gin.Context) {
	curso, estudiante := c.Param("curso"), c.Param("estudiante")
	if !cursoValido.MatchString(curso) || !estudianteValido.MatchString(estudiante) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "curso o estudiante no válido"})
		return
	}
	if !middleware.CursoAutorizado(c, curso) {
		c.JSON(http.StatusForbidden, gin.H{"error": "ese curso no es el tuyo"})
		return
	}
	ejercicios, err := h.estudiantes.Ficha(curso, estudiante)
	if err != nil {
		log.Printf("[panel] ficha de %s: %v", estudiante, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "no se pudo leer la ficha"})
		return
	}
	// Acota a una semana ("?cuadernillo=semana_03"); vacío = todo el curso.
	// Se valida con el mismo patrón que el curso porque es del mismo tipo:
	// un identificador corto que acaba dentro de un WHERE.
	cuadernillo := c.Query("cuadernillo")
	if cuadernillo != "" && !cursoValido.MatchString(cuadernillo) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "cuadernillo no válido"})
		return
	}

	// El desglose por competencia de ESTA persona. Si falla no se tumba la
	// ficha: el recorrido ejercicio a ejercicio sigue siendo util, y el panel
	// ya sabe pintar la seccion vacia.
	competencias, err := h.estudiantes.Competencias(curso, estudiante, cuadernillo)
	if err != nil {
		log.Printf("[panel] competencias de %s: %v", estudiante, err)
		competencias = nil
	}
	ponerNivel(competencias)

	c.JSON(http.StatusOK, gin.H{"curso_id": curso, "student_id": estudiante,
		"cuadernillo": cuadernillo,
		"ejercicios":  ejercicios, "competencias": competencias})
}

// ponerNivel rellena el nivel N1/N2/N3 de cada competencia.
//
// Se calcula aquí y no en SQL porque los umbrales tienen que poder ajustarse
// sin migrar la base (ver service.NivelCompetencia y
// docs/modelo_microcompetencias.md §3).
//
// Recorre TODAS las filas, incluidas las que no tienen actividad: ahí
// NivelCompetencia devuelve nil con el motivo «sin evidencia suficiente», que
// es justo lo que el panel necesita para no inventarse un N1. Es el caso más
// común al empezar el semestre, no un caso raro.
//
// Las competencias fuera de alcance no reciben nivel NUNCA, por muchas señales
// que tengan. El AVA solo mide con trazas de actividad, y mCC85 no forma parte
// del diseño mientras que mCA14 y mCA65 se evalúan por autorreporte y
// coevaluación: un nivel calculado ahí a partir de fallos no mide la
// competencia, mide otra cosa.
//
// Y no es hipotético: los seis ejercicios etiquetados con I5 (mCA14) llevan
// TAMBIÉN la etiqueta I3, así que su tarjeta sería una recopia de un subconjunto
// de las señales de I3 presentada como una competencia distinta. Pintarla con un
// N3 verde sería afirmar algo que este sistema no puede saber, y al congelar un
// corte ese número entraría en la evidencia del estudio sin forma de
// distinguirlo de los legítimos.
//
// El motivo es distinto del de «sin evidencia suficiente» a propósito: aquel
// dice «todavía no sé», este dice «esto no se mide así». Confundirlos haría
// pensar que basta con que el alumno trabaje más.
func ponerNivel(comps []repository.CompetenciaDeEstudiante) {
	for i := range comps {
		nivelDe(&comps[i])
	}
}

// nivelDe es ponerNivel para UNA fila. Está separado para que el resumen del
// curso entero (CompetenciasDelCurso), que lleva el student_id delante, pase
// por el mismo cálculo exacto que la ficha y el corte.
func nivelDe(c *repository.CompetenciaDeEstudiante) {
	// nil = todavía no se sabe (falta la migración v5). No se da nivel
	// igualmente, pero el motivo dice la verdad en vez de inventar una
	// explicación pedagógica para lo que es un despliegue a medias.
	if c.EnAlcance == nil {
		c.Nivel = nil
		c.Motivo = "el nivel no está disponible todavía en este servidor"
		return
	}
	if !*c.EnAlcance {
		c.Nivel = nil
		c.Motivo = "no se mide con trazas de actividad: " +
			"esta competencia se evalúa por autorreporte y coevaluación"
		return
	}
	nivel, motivo := service.NivelCompetencia(service.SenalesCompetencia{
		Vistos:    c.Vistos,
		Resueltos: c.Resueltos,
		Fallos:    c.Fallos,
		Abandonos: c.Abandonos,
	})
	c.Nivel = nivel
	c.Motivo = motivo
}

// CorteRequest es lo que manda el docente al congelar un corte.
type CorteRequest struct {
	// 'pre', 'post', 'corte 1'… Es la única forma de comparar dos momentos, así
	// que se exige: un corte sin etiqueta no se puede contrastar con nada.
	Etiqueta string `json:"etiqueta"`
}

// CorteHandler responde a POST /internal/curso/:curso/corte: congela el nivel
// de todo el grupo tal y como está hoy.
//
// Existe porque el nivel que se ve en pantalla es siempre el de HOY, y el
// estudio pre/post necesita poder decir «así estaba el grupo el 15 de
// septiembre». Una vista no da eso.
//
// Lo escribe el docente con una acción explícita, nunca un GET: un efecto
// secundario dentro de una consulta de lectura sería imposible de auditar
// después, y aquí lo que se guarda es evidencia de una investigación.
//
// Se guarda el nivel JUNTO CON las señales y los umbrales que lo produjeron.
// Si mañana se ajustan los umbrales, un corte viejo se puede recalcular en vez
// de quedarse mintiendo con un número que ya no significa lo mismo.
func (h *PanelDocenteHandler) CorteHandler(c *gin.Context) {
	curso := c.Param("curso")
	if !cursoValido.MatchString(curso) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "curso no válido"})
		return
	}
	if !middleware.CursoAutorizado(c, curso) {
		c.JSON(http.StatusForbidden, gin.H{"error": "ese curso no es el tuyo"})
		return
	}

	var input CorteRequest
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Sintaxis inválida en el cuerpo JSON"})
		return
	}
	input.Etiqueta = strings.TrimSpace(input.Etiqueta)
	if input.Etiqueta == "" {
		c.JSON(http.StatusBadRequest,
			gin.H{"error": "hace falta una etiqueta para el corte, por ejemplo 'pre' o 'post'"})
		return
	}
	// Caracteres, no bytes: el formulario del panel limita con maxlength, que
	// cuenta caracteres. Con len() una etiqueta de 60 con tildes se podía
	// teclear entera y el servidor la rechazaba diciendo que pasaba de 60
	// —contradiciendo lo que el docente acababa de contar en pantalla—.
	if utf8.RuneCountInString(input.Etiqueta) > 60 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "la etiqueta no puede pasar de 60 caracteres"})
		return
	}

	gente, err := h.estudiantes.Listar(curso)
	if err != nil {
		log.Printf("[corte] listar %s: %v", curso, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "no se pudo leer el listado del curso"})
		return
	}

	// Los mismos umbrales con los que se pintó la pantalla, guardados con el
	// corte para que sea reproducible.
	umbrales, _ := json.Marshal(map[string]any{
		"minimo_evidencia": service.MinimoEvidencia,
		"cobertura_n3":     service.CoberturaN3,
		"cobertura_n2":     service.CoberturaN2,
		"costo_n3":         service.CostoN3,
		"abandonos_n3":     service.AbandonosN3,
	})

	filas := []repository.FilaCorte{}
	for _, p := range gente {
		if p.Rol == "instructor" || p.Rol == "docente" {
			continue // el nivel del docente no es un dato del estudio
		}
		// Se reutiliza EXACTAMENTE la consulta que alimenta la ficha, y no una
		// propia: así el corte congela lo mismo que el docente estaba viendo.
		// Dos consultas distintas para el mismo número acaban divergiendo, y un
		// corte que no coincide con la pantalla no vale para nada.
		comps, err := h.estudiantes.Competencias(curso, p.StudentID, "")
		if err != nil {
			log.Printf("[corte] competencias de %s: %v", p.StudentID, err)
			c.JSON(http.StatusInternalServerError,
				gin.H{"error": "no se pudo calcular el corte; no se guardó nada"})
			return
		}
		ponerNivel(comps)
		for _, k := range comps {
			filas = append(filas, repository.FilaCorte{
				StudentID: p.StudentID, CompetenciaID: k.CompetenciaID,
				Nivel: k.Nivel, Vistos: k.Vistos, Resueltos: k.Resueltos,
				Intentos: k.Intentos, Fallos: k.Fallos, Abandonos: k.Abandonos,
				Umbrales: umbrales,
			})
		}
	}

	guardadas, err := h.estudiantes.GuardarCorte(curso, input.Etiqueta, filas)
	if err != nil {
		log.Printf("[corte] guardar %s/%s: %v", curso, input.Etiqueta, err)
		c.JSON(http.StatusInternalServerError,
			gin.H{"error": "no se pudo guardar el corte"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "corte congelado",
		"etiqueta": input.Etiqueta, "filas": guardadas})
}
