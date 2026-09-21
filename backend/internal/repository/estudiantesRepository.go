package repository

import (
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/jmoiron/sqlx"
)

// EstudiantesRepository: quién es cada student_id, y cómo le va.
//
// La identidad la escribe el Hub en cada ingreso LTI (Registrar). Todo lo
// demás sale de cruzar esa tabla con la telemetría y las notas, para que el
// panel del docente pueda listar a su gente por nombre y no por número.
type EstudiantesRepository struct {
	db *sqlx.DB

	// Ver columnaEnAlcance.
	unaVez       sync.Once
	hayEnAlcance bool
}

func NewEstudiantesRepository(db *sqlx.DB) *EstudiantesRepository {
	return &EstudiantesRepository{db: db}
}

// columnaEnAlcance devuelve el trozo de SELECT que lee competencias.en_alcance,
// o un literal si la columna todavía no existe.
//
// Hace falta porque el orden de un despliegue no está garantizado: el instalador
// levanta los contenedores y DESPUÉS aplica las migraciones, así que hay una
// ventana en la que este backend corre contra una base sin la v5. Sin esto, la
// consulta falla entera y el panel se queda sin la sección de competencias —que
// hoy funciona— hasta que alguien mire el log.
//
// El literal es `false`, no `true`: si no se sabe si una competencia es medible,
// lo honrado es no darle nivel. Mejor una pantalla que dice «no se mide con
// trazas» de más que un N3 inventado de menos, sobre todo cuando ese número
// puede acabar congelado en un corte del estudio.
//
// Se comprueba una sola vez: la columna no aparece ni desaparece sola, y hacerlo
// en cada petición sería una consulta extra por carga del panel.
func (r *EstudiantesRepository) columnaEnAlcance() string {
	r.unaVez.Do(func() {
		var existe bool
		err := r.db.Get(&existe, `SELECT EXISTS (
			SELECT 1 FROM information_schema.columns
			 WHERE table_name = 'competencias' AND column_name = 'en_alcance')`)
		if err != nil {
			log.Printf("[panel] no se pudo comprobar competencias.en_alcance: %v", err)
			return
		}
		r.hayEnAlcance = existe
		if !existe {
			log.Println("[panel] competencias.en_alcance no existe todavía (falta la " +
				"migración v5): ninguna competencia recibirá nivel hasta que se aplique")
		}
	})
	if r.hayEnAlcance {
		return "c.en_alcance"
	}
	return "NULL::boolean AS en_alcance"
}

// Ingreso es lo que el Hub sabe de una persona en el momento en que entra.
type Ingreso struct {
	CourseID   string `json:"curso_id"`
	StudentID  string `json:"estudiante_id"`
	Nombre     string `json:"nombre"`
	Email      string `json:"email"`
	UsuarioHub string `json:"usuario_hub"`
	Rol        string `json:"rol"`
	SourcedID  string `json:"lis_result_sourcedid"`
	OutcomeURL string `json:"lis_outcome_service_url"`
}

// Registrar anota un ingreso: crea la ficha la primera vez y después la
// actualiza. El sourcedid de Moodle cambia entre lanzamientos (es por casilla
// del libro de calificaciones), así que siempre se guarda el último; un
// lanzamiento que no lo trae no borra el anterior.
func (r *EstudiantesRepository) Registrar(in Ingreso) error {
	_, err := r.db.NamedExec(`
		INSERT INTO estudiantes
			(course_id, student_id, nombre, email, usuario_hub, rol,
			 lis_result_sourcedid, lis_outcome_service_url,
			 primer_ingreso, ultimo_ingreso, ingresos)
		VALUES
			(:course_id, :student_id, :nombre, :email, :usuario_hub, :rol,
			 NULLIF(:sourcedid, ''), NULLIF(:outcome_url, ''),
			 now(), now(), 1)
		ON CONFLICT (course_id, student_id) DO UPDATE SET
			nombre                  = CASE WHEN EXCLUDED.nombre <> '' THEN EXCLUDED.nombre ELSE estudiantes.nombre END,
			email                   = CASE WHEN EXCLUDED.email  <> '' THEN EXCLUDED.email  ELSE estudiantes.email  END,
			usuario_hub             = CASE WHEN EXCLUDED.usuario_hub <> '' THEN EXCLUDED.usuario_hub ELSE estudiantes.usuario_hub END,
			rol                     = EXCLUDED.rol,
			lis_result_sourcedid    = COALESCE(EXCLUDED.lis_result_sourcedid, estudiantes.lis_result_sourcedid),
			lis_outcome_service_url = COALESCE(EXCLUDED.lis_outcome_service_url, estudiantes.lis_outcome_service_url),
			ultimo_ingreso          = now(),
			ingresos                = estudiantes.ingresos + 1`,
		map[string]any{
			"course_id": in.CourseID, "student_id": in.StudentID,
			"nombre": in.Nombre, "email": in.Email, "usuario_hub": in.UsuarioHub,
			"rol": in.Rol, "sourcedid": in.SourcedID, "outcome_url": in.OutcomeURL,
		})
	if err != nil {
		return fmt.Errorf("no se pudo registrar el ingreso: %w", err)
	}
	return nil
}

// FichaEstudiante es una fila del listado del docente.
type FichaEstudiante struct {
	StudentID         string     `db:"student_id" json:"student_id"`
	Nombre            string     `db:"nombre" json:"nombre"`
	Email             string     `db:"email" json:"email"`
	Rol               string     `db:"rol" json:"rol"`
	UltimoIngreso     *time.Time `db:"ultimo_ingreso" json:"ultimo_ingreso"`
	Ingresos          int        `db:"ingresos" json:"ingresos"`
	UltimoIntento     *time.Time `db:"ultimo_intento" json:"ultimo_intento"`
	UltimoCuadernillo string     `db:"ultimo_cuadernillo" json:"ultimo_cuadernillo"`
	IntentosReales    int        `db:"intentos_reales" json:"intentos_reales"`
	Resueltos         int        `db:"resueltos" json:"ejercicios_resueltos"`
	Atascados         int        `db:"atascados" json:"ejercicios_atascados"`
	AMedias           int        `db:"a_medias" json:"ejercicios_a_medias"`
	Notas             int        `db:"notas" json:"cuadernillos_calificados"`
	TieneSourcedID    bool       `db:"tiene_sourcedid" json:"devolucion_moodle_posible"`
}

// Listar devuelve a todos los del curso: los registrados por el Hub y, por si
// hubiera telemetría o notas de alguien de antes del registro, también a
// quienes solo existen ahí (sin nombre). Incluye al docente, con su rol, para
// que el listado coincida con lo que el Hub conoce.
func (r *EstudiantesRepository) Listar(curso string) ([]FichaEstudiante, error) {
	salida := []FichaEstudiante{}
	err := r.db.Select(&salida, intentosReales+`,
	    porEjercicio AS (
	        SELECT student_id, cuadernillo_id, exercise_id,
	               bool_or(validation_result = 'passed')                   AS paso,
	               bool_or(validation_result = 'failed' AND NOT stub)      AS intento_real,
	               bool_or(validation_result = 'sin_validar' AND NOT stub) AS a_medias
	          FROM t GROUP BY student_id, cuadernillo_id, exercise_id
	    ),
	    actividad AS (
	        SELECT student_id,
	               COUNT(*) FILTER (WHERE paso)                      AS resueltos,
	               COUNT(*) FILTER (WHERE intento_real AND NOT paso) AS atascados,
	               COUNT(*) FILTER (WHERE a_medias AND NOT paso)     AS a_medias
	          FROM porEjercicio GROUP BY student_id
	    ),
	    ultimo AS (
	        SELECT DISTINCT ON (student_id) student_id, received_at, cuadernillo_id
	          FROM t ORDER BY student_id, received_at DESC
	    ),
	    intentos AS (
	        SELECT student_id, COUNT(*) FILTER (WHERE NOT stub) AS intentos_reales
	          FROM t GROUP BY student_id
	    ),
	    notas AS (
	        SELECT student_id, COUNT(*) AS notas
	          FROM cuadernillo_notas WHERE course_id = $1 GROUP BY student_id
	    ),
	    ids AS (
	        SELECT student_id FROM estudiantes WHERE course_id = $1
	        UNION SELECT student_id FROM t
	        UNION SELECT student_id FROM cuadernillo_notas WHERE course_id = $1
	    )
		SELECT ids.student_id,
		       COALESCE(e.nombre, '')                              AS nombre,
		       COALESCE(e.email, '')                               AS email,
		       COALESCE(e.rol, 'estudiante')                       AS rol,
		       e.ultimo_ingreso,
		       COALESCE(e.ingresos, 0)                             AS ingresos,
		       u.received_at                                       AS ultimo_intento,
		       COALESCE(u.cuadernillo_id, '')                      AS ultimo_cuadernillo,
		       COALESCE(i.intentos_reales, 0)                      AS intentos_reales,
		       COALESCE(a.resueltos, 0)                            AS resueltos,
		       COALESCE(a.atascados, 0)                            AS atascados,
		       COALESCE(a.a_medias, 0)                             AS a_medias,
		       COALESCE(n.notas, 0)                                AS notas,
		       (e.lis_result_sourcedid IS NOT NULL)                AS tiene_sourcedid
		  FROM ids
		  LEFT JOIN estudiantes e ON e.course_id = $1 AND e.student_id = ids.student_id
		  LEFT JOIN actividad  a ON a.student_id = ids.student_id
		  LEFT JOIN ultimo     u ON u.student_id = ids.student_id
		  LEFT JOIN intentos   i ON i.student_id = ids.student_id
		  LEFT JOIN notas      n ON n.student_id = ids.student_id
		 ORDER BY COALESCE(u.received_at, e.ultimo_ingreso) DESC NULLS LAST, ids.student_id`, curso)
	return salida, err
}

// Nombres devuelve {student_id: nombre} para poner nombre donde hoy hay número.
func (r *EstudiantesRepository) Nombres(curso string) (map[string]string, error) {
	filas := []struct {
		ID     string `db:"student_id"`
		Nombre string `db:"nombre"`
	}{}
	if err := r.db.Select(&filas, `SELECT student_id, nombre FROM estudiantes WHERE course_id = $1`, curso); err != nil {
		return nil, err
	}
	m := make(map[string]string, len(filas))
	for _, f := range filas {
		if f.Nombre != "" {
			m[f.ID] = f.Nombre
		}
	}
	return m, nil
}

// EjercicioDeEstudiante es una fila de la ficha individual.
type EjercicioDeEstudiante struct {
	CuadernilloID string     `db:"cuadernillo_id" json:"cuadernillo_id"`
	EjercicioID   string     `db:"exercise_id" json:"exercise_id"`
	Orden         *int16     `db:"orden" json:"orden"`
	PuntosMax     *int16     `db:"puntos_maximos" json:"puntos_maximos"`
	Intentos      int        `db:"intentos" json:"intentos"`
	Paso          bool       `db:"paso" json:"resuelto"`
	AMedias       bool       `db:"a_medias" json:"a_medias"`
	SoloStub      bool       `db:"solo_stub" json:"solo_ejecuto_vacio"`
	UltimoError   string     `db:"ultimo_error" json:"ultimo_error"`
	UltimoMensaje string     `db:"ultimo_mensaje" json:"ultimo_mensaje"`
	PrimerIntento *time.Time `db:"primero" json:"primer_intento"`
	UltimoIntento *time.Time `db:"ultimo" json:"ultimo_intento"`
}

// Ficha: el recorrido de una persona, ejercicio a ejercicio.
//
// El criterio de `stub` es el mismo que el de Competencias, y tiene que serlo:
// las dos las devuelve el MISMO handler y se pintan seguidas en la misma
// página. Ver allí la explicación larga y las cifras que la justifican.
func (r *EstudiantesRepository) Ficha(curso, estudiante string) ([]EjercicioDeEstudiante, error) {
	salida := []EjercicioDeEstudiante{}
	err := r.db.Select(&salida, `
	    WITH t AS (
	        SELECT a.*,
	               (a.validation_result <> 'passed'
	                AND EXISTS (SELECT 1 FROM attempt_errors e
	                             WHERE e.attempt_id = a.id
	                               AND e.error_type = 'NotImplementedError')
	                AND NOT EXISTS (SELECT 1 FROM attempt_errors e
	                                 WHERE e.attempt_id = a.id
	                                   AND e.error_type <> 'NotImplementedError')) AS stub
	          FROM exercise_attempts a
	         WHERE a.course_id = $1 AND a.student_id = $2
	    ),
	    ultimo_error AS (
	        SELECT DISTINCT ON (t.cuadernillo_id, t.exercise_id)
	               t.cuadernillo_id, t.exercise_id, e.error_type, e.error_message
	          FROM t JOIN attempt_errors e ON e.attempt_id = t.id
	         WHERE NOT t.stub
	         ORDER BY t.cuadernillo_id, t.exercise_id, e.occurred_at DESC
	    )
		SELECT t.cuadernillo_id, t.exercise_id,
		       MIN(t.orden)                                        AS orden,
		       MAX(t.puntos_maximos)                               AS puntos_maximos,
		       COUNT(*) FILTER (WHERE NOT t.stub)                  AS intentos,
		       bool_or(t.validation_result = 'passed')             AS paso,
		       bool_or(t.validation_result = 'sin_validar' AND NOT t.stub)
		           AND NOT bool_or(t.validation_result = 'passed') AS a_medias,
		       bool_and(t.stub)                                    AS solo_stub,
		       COALESCE(MAX(ue.error_type), '')                    AS ultimo_error,
		       COALESCE(MAX(LEFT(ue.error_message, 200)), '')      AS ultimo_mensaje,
		       MIN(t.received_at)                                  AS primero,
		       MAX(t.received_at)                                  AS ultimo
		  FROM t
		  LEFT JOIN ultimo_error ue ON ue.cuadernillo_id = t.cuadernillo_id
		                           AND ue.exercise_id    = t.exercise_id
		 GROUP BY t.cuadernillo_id, t.exercise_id
		 ORDER BY t.cuadernillo_id, MIN(t.orden) NULLS LAST, t.exercise_id`, curso, estudiante)
	return salida, err
}

// CompetenciaDeEstudiante es una fila del desglose por competencia de UNA
// persona. Es lo que el panel del curso ya mostraba agregado, pero por alumno.
type CompetenciaDeEstudiante struct {
	CompetenciaID string `db:"competencia_id" json:"competencia_id"`
	Descripcion   string `db:"descripcion"    json:"descripcion"`
	// Cuántos ejercicios de esta competencia existen en total.
	Disenados int `db:"disenados" json:"ejercicios_disenados"`
	// De esos, en cuántos llegó a intentar algo de verdad. Es el denominador
	// honesto: medir sobre los diseñados castigaría a todo el mundo por los
	// cuadernillos que el docente todavía no ha publicado.
	Vistos int `db:"vistos" json:"ejercicios_vistos"`
	// De los vistos, cuántos resolvió.
	Resueltos int `db:"resueltos" json:"ejercicios_resueltos"`
	// Intentos reales e intentos que acabaron en abandono. La diferencia entre
	// "no lo intentó" y "lo intentó y se rindió" son dos conversaciones
	// distintas con el estudiante, y sin esto se ven igual.
	Intentos  int `db:"intentos"  json:"intentos"`
	Abandonos int `db:"abandonos" json:"abandonos"`
	// Intentos que acabaron en 'failed'. NO es lo mismo que Intentos, y
	// confundirlos rompe el nivel: el coste es fallos por ejercicio resuelto,
	// así que alimentarlo con el total de intentos lo infla y baja a N2 a quien
	// merece N3 —justo el error que la fórmula existe para no cometer—.
	Fallos int `db:"fallos" json:"fallos"`

	// Si el AVA puede medir esta competencia con trazas de actividad. Cuatro de
	// las siete sí; mCC85 no forma parte del diseño, y mCA14 y mCA65 se evalúan
	// por autorreporte y coevaluación. Darles un nivel a partir de fallos sería
	// inventarse un dato —y peor aún si ese dato acaba congelado en un corte
	// del estudio, indistinguible de los legítimos—.
	//
	// Sale de competencias.en_alcance (migración v5). Es un puntero porque hay
	// TRES estados, no dos: sí, no, y «todavía no se puede saber» (nil) cuando
	// la migración no está aplicada. Aplanarlo a false haría que el panel le
	// dijera al docente que una competencia se evalúa por autorreporte cuando
	// la verdad es que falta una migración: una explicación falsa es peor que
	// ninguna. Ver columnaEnAlcance.
	EnAlcance *bool `db:"en_alcance" json:"en_alcance"`

	// El nivel NO sale de la consulta: lo calcula service.NivelCompetencia a
	// partir de los campos de arriba, porque los umbrales deben poder ajustarse
	// sin migrar la base. Por eso `db:"-"`.
	//
	// Nivel es un puntero porque nil significa "sin evidencia suficiente", que
	// no es lo mismo que N1 y no puede confundirse con él: decirle al docente
	// "N1" sobre alguien de quien no sabemos nada es peor que callarse.
	Nivel  *int   `db:"-" json:"nivel"`
	Motivo string `db:"-" json:"motivo_nivel"`
}

// Competencias: el desglose por competencia de una persona.
//
// Existe porque faltaba justo la vista que el AVA promete: el panel del curso
// decía "4 de 16 estudiantes resolvió alguno" y la ficha individual mostraba
// ejercicio a ejercicio, así que no había forma de responder "este estudiante,
// ¿en qué competencia va atascado?" — que es la pregunta del trabajo de grado.
//
// Los intentos que solo ejecutaron la plantilla sin tocarla (NotImplementedError)
// no cuentan: no son un intento, son un "ejecuté la celda a ver qué pasaba".
//
// Pero "llevaba un NotImplementedError" NO alcanza para declararlo plantilla, y
// medirlo contra los datos reales lo dejó claro. custom.js acumula los errores
// del ejercicio y solo vacía el buffer cuando consigue ENVIAR un intento
// (custom.js:352 y :370). El recorrido normal del alumno es: ejecuta la celda de
// solución con la plantilla intacta —que es lo que el propio cuadernillo le pide
// hacer— y ahí se bufferiza el NotImplementedError; luego escribe su código y
// ejecuta solución y prueba. Ese intento, que APRUEBA, arrastra el stub viejo.
//
// Con el criterio anterior se descartaba entero. En la base de producción eso
// eran 18 intentos aprobados tirados a la basura, 16 de ellos sin un solo error
// de verdad, y 7 ejercicios resueltos que el panel no le mostraba al docente
// (145 en vez de 152). De los 46 intentos que el criterio viejo descartaba, solo
// 5 eran plantilla de verdad: se equivocaba en el 89 % de los casos.
//
// El criterio correcto: un intento es plantilla cuando NO aprobó y TODOS sus
// errores son NotImplementedError. Aprobar es prueba de que el alumno escribió
// algo, y un error real conviviendo con el stub también.
//
// Ojo: Malentendidos() en panelDocenteRepository.go usa a propósito el criterio
// estricto y NO debe alinearse con este. Allí la pregunta es "¿qué concepto hay
// que explicar?", y un AssertionError que es consecuencia de la celda vacía no
// es un malentendido. Aquí la pregunta es "¿cuánto cubrió?", y ahí un ejercicio
// aprobado cuenta siempre.
// El tercer argumento acota a un cuadernillo ("semana_03"); vacío = todo el
// curso. Va como filtro y no como agrupación para no cambiar la forma de la
// respuesta: el panel pide lo mismo con o sin semana.
//
// Aviso honesto sobre filtrar por semana: una semana aporta dos o tres
// ejercicios por competencia, así que casi siempre quedará por debajo del
// mínimo de evidencia y el nivel saldrá vacío. No es un fallo —es la respuesta
// correcta—: un nivel calculado sobre dos ejercicios es ruido. El filtro sirve
// para mirar la ACTIVIDAD de esa semana, no para graduar por semana.
func (r *EstudiantesRepository) Competencias(curso, estudiante, cuadernillo string) ([]CompetenciaDeEstudiante, error) {
	salida := []CompetenciaDeEstudiante{}
	err := r.db.Select(&salida, `
	    WITH reales AS (
	        SELECT a.cuadernillo_id, a.exercise_id, a.validation_result
	          FROM exercise_attempts a
	         WHERE a.course_id = $1 AND a.student_id = $2
	           AND ($3 = '' OR a.cuadernillo_id = $3)
	           -- Plantilla = no aprobó Y todos sus errores son el stub. Se
	           -- conserva si aprobó, si trae algún error de verdad, o si no
	           -- trae ninguno (fallar sin excepción sigue siendo intentarlo).
	           AND (a.validation_result = 'passed'
	                OR EXISTS (SELECT 1 FROM attempt_errors e
	                            WHERE e.attempt_id = a.id
	                              AND e.error_type <> 'NotImplementedError')
	                OR NOT EXISTS (SELECT 1 FROM attempt_errors e
	                                WHERE e.attempt_id = a.id))
	    )
		SELECT c.id AS competencia_id, c.descripcion, `+r.columnaEnAlcance()+`,
		       -- El FILTER no sobra: sin el, COUNT(DISTINCT (a,b)) cuenta la
		       -- tupla (NULL, NULL) que deja el LEFT JOIN cuando la competencia
		       -- no tiene ningun ejercicio, y devuelve 1 en vez de 0.
		       COUNT(DISTINCT (ec.cuadernillo_id, ec.exercise_id))
		           FILTER (WHERE ec.exercise_id IS NOT NULL)              AS disenados,
		       COUNT(DISTINCT (t.cuadernillo_id, t.exercise_id))
		           FILTER (WHERE t.exercise_id IS NOT NULL)               AS vistos,
		       COUNT(DISTINCT (t.cuadernillo_id, t.exercise_id)) FILTER (
		           WHERE t.validation_result = 'passed')                  AS resueltos,
		       COUNT(t.*)                                                 AS intentos,
		       COUNT(t.*) FILTER (
		           WHERE t.validation_result = 'failed')                  AS fallos,
		       -- Ejercicios abandonados, no eventos de abandono. Contar eventos
		       -- repetía el error que el panel del alumno ya corrigió: cerrar la
		       -- pestaña tres veces sumaba tres abandonos del mismo ejercicio.
		       -- Y si acabó resolviéndolo, no lo abandonó.
		       COUNT(DISTINCT (t.cuadernillo_id, t.exercise_id)) FILTER (
		           WHERE t.validation_result = 'sin_validar'
		             AND NOT EXISTS (SELECT 1 FROM reales r
		                              WHERE r.cuadernillo_id = t.cuadernillo_id
		                                AND r.exercise_id    = t.exercise_id
		                                AND r.validation_result = 'passed'))  AS abandonos
		  FROM competencias c
		  -- El filtro de semana va también aquí, no solo sobre los intentos:
		  -- si no, "diseñados" seguiría contando los ejercicios de las otras
		  -- semanas y la tarjeta diría "3 sin tocar" en una semana de dos.
		  LEFT JOIN ejercicio_competencias ec ON ec.competencia_id = c.id
		                    AND ($3 = '' OR ec.cuadernillo_id = $3)
		  LEFT JOIN reales t ON t.cuadernillo_id = ec.cuadernillo_id
		                    AND t.exercise_id    = ec.exercise_id
		 GROUP BY c.id, c.descripcion
		 ORDER BY c.id`, curso, estudiante, cuadernillo)
	return salida, err
}

// FilaCorte es una fila del corte que se congela: el nivel de una persona en
// una competencia, junto con las señales y los umbrales que lo produjeron.
type FilaCorte struct {
	StudentID     string
	CompetenciaID string
	Nivel         *int
	Vistos        int
	Resueltos     int
	Intentos      int
	Fallos        int
	Abandonos     int
	Umbrales      []byte // JSON
}

// GuardarCorte congela un corte del curso entero.
//
// Todo en UNA transacción: un corte a medias —la mitad del grupo con los
// números de hoy y la otra mitad sin escribir— sería peor que no tenerlo,
// porque al compararlo con el siguiente nadie sabría qué parte es real.
//
// Vuelve a escribir sobre la misma etiqueta si ya existe. Congelar "pre" dos
// veces el mismo día es un error de dedo, no un dato nuevo, y acumular las dos
// versiones obligaría a adivinar cuál vale. Quien quiera conservar las dos usa
// dos etiquetas.
func (r *EstudiantesRepository) GuardarCorte(curso, etiqueta string, filas []FilaCorte) (int, error) {
	tx, err := r.db.Beginx()
	if err != nil {
		return 0, fmt.Errorf("no se pudo iniciar la transacción: %w", err)
	}
	defer tx.Rollback()

	for _, f := range filas {
		if _, err := tx.Exec(`
			INSERT INTO corte_competencia
			    (course_id, student_id, competencia_id, etiqueta, nivel,
			     vistos, resueltos, intentos, fallos, abandonos, umbrales)
			VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
			ON CONFLICT (course_id, student_id, competencia_id, etiqueta)
			DO UPDATE SET tomado_en = now(), nivel = EXCLUDED.nivel,
			              vistos    = EXCLUDED.vistos,
			              resueltos = EXCLUDED.resueltos,
			              intentos  = EXCLUDED.intentos,
			              fallos    = EXCLUDED.fallos,
			              abandonos = EXCLUDED.abandonos,
			              umbrales  = EXCLUDED.umbrales`,
			curso, f.StudentID, f.CompetenciaID, etiqueta, f.Nivel,
			f.Vistos, f.Resueltos, f.Intentos, f.Fallos, f.Abandonos, f.Umbrales,
		); err != nil {
			return 0, fmt.Errorf("guardar %s/%s: %w", f.StudentID, f.CompetenciaID, err)
		}
	}
	return len(filas), tx.Commit()
}
