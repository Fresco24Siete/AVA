package models

type ApiMessage struct {

    NombreEstudiante  string `json:"nombre_estudiante"`// revvisar en lti
    Mensaje           string `json:"mensaje"`
    Historial         string `json:"historial"`
    ContextoEjercicio string `json:"contexto"`
}