#!/usr/bin/env python3
"""Validacion de punta a punta del modelo de microcompetencias (fase 7).

Lo que prueba prueba_backend.py es el contrato del backend con datos de
juguete. Esto prueba otra cosa: que la cadena COMPLETA funciona con el mapeo
REAL del curso y con los identificadores REALES de un cuadernillo rediseniado.

    competencias.json  ->  POST /internal/competencias   (lo que hace
                                                          cargar-competencias)
    custom.js          ->  POST /api/exercises/attempts  (lo que manda el
                                                          navegador del alumno)
    JOIN por (cuadernillo, ejercicio)
    service.NivelCompetencia
    GET /internal/curso/:c/estudiante/:e  ->  nivel y motivo en el panel

Y la regresion: que los ejercicios que NO se tocaron siguen guardando metricas.

Necesita un backend y una base vivos, con las migraciones v3, v4 y v5
aplicadas (la v5 crea corte_competencia). Mismas variables de entorno que
prueba_backend.py:

    ENV_FILE=/dev/null API_BASE='http://[::1]:8080' \\
    PG_EXEC='docker exec -i <contenedor> psql -U ava -d ava -At' \\
    METRICS_API_TOKEN=... METRICS_TOKEN_SECRET=... \\
    python3 backend/tests/telemetria/prueba_fase7.py

Todo lo que crea lleva el prefijo F7- y se borra al final.
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
MAPEO = os.path.join(REPO, "notebook", "cuadernillos", "competencias.json")


def leer_env(ruta):
    valores = {}
    if not os.path.exists(ruta):
        return valores
    with open(ruta) as f:
        for linea in f:
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                valores[k.strip()] = v.strip().strip('"').strip("'")
    return valores


ENV = leer_env(os.environ.get("ENV_FILE", os.path.join(REPO, ".env")))


def cfg(nombre, default=None):
    return os.environ.get(nombre) or ENV.get(nombre) or default


API = cfg("API_BASE", "http://localhost:8080").rstrip("/")
PG_EXEC = cfg("PG_EXEC", "docker exec -i postgres-db psql -U ava -d ava -At")
MAESTRO = cfg("METRICS_API_TOKEN")

PREFIJO = "F7-"
CURSO = "F7-CURSO"
ANA, BETO = "F7-ana", "F7-beto"

# Token por alumno, acunado por el Hub. La ruta de telemetria NO acepta el token
# maestro: verifica la identidad de quien manda el intento.
tokens = {}

resultados = []


def http(metodo, ruta, cuerpo=None, token=None):
    cab = {"Content-Type": "application/json"}
    if token:
        cab["Authorization"] = "Bearer " + token
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(API + ruta, data=datos, method=metodo, headers=cab)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            texto, status = r.read().decode(), r.status
    except urllib.error.HTTPError as e:
        texto, status = e.read().decode(), e.code
    try:
        return status, json.loads(texto) if texto else None
    except json.JSONDecodeError:
        return status, texto


def sql(consulta):
    p = subprocess.run(PG_EXEC.split() + ["-F", "\t", "-v", "ON_ERROR_STOP=1"],
                       input=consulta, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"psql fallo: {p.stderr.strip()}")
    return [l.split("\t") for l in p.stdout.splitlines() if l]


def ok(nombre, condicion, detalle=""):
    resultados.append((nombre, bool(condicion)))
    print(f"[{'OK' if condicion else 'FALLO'}] {nombre}")
    if detalle:
        for linea in str(detalle).splitlines():
            print("       " + linea)


def intento(cuad, ejercicio, resultado, errores=None, alumno=ANA):
    """El payload EXACTO que llega al backend: lo de custom.js mas la
    identidad que anade metrics_bridge."""
    return {
        "exercise_id": ejercicio,
        "cuadernillo_id": cuad,
        "attempt_at": "2026-09-21T12:00:00.000Z",
        "validation_result": resultado,
        "errors": errores or [],
        "codigo_celda": "test_" + ejercicio,
        "orden": 10, "puntos_maximos": 10,
        "student_id": alumno, "course_id": CURSO,
        "student_name": "Alumno de Prueba", "student_email": "f7@ejemplo.test",
    }


def stub(ejercicio):
    return [{"cell_id": ejercicio, "timestamp": "2026-09-21T11:59:00.000Z",
             "error_type": "NotImplementedError", "error_message": "plantilla",
             "traceback": ""}]


def limpiar():
    sql(f"""
        delete from exercise_attempts where course_id like '{PREFIJO}%';
        delete from corte_competencia where course_id like '{PREFIJO}%';
        delete from ejercicio_competencias where cuadernillo_id like '{PREFIJO}%';
        delete from estudiantes where course_id like '{PREFIJO}%';
    """)


def main():
    if not MAESTRO:
        print("Falta METRICS_API_TOKEN")
        sys.exit(2)

    for alumno in (ANA, BETO):
        st, r = http("POST", "/internal/lti/mint-metrics-token",
                     {"estudiante_id": alumno, "curso_id": CURSO,
                      "cuadernillo_codigo": ""}, token=MAESTRO)
        tokens[alumno] = (r or {}).get("token", "")
        if st != 200 or not tokens[alumno]:
            print(f"No se pudo acunar el token de {alumno}: status={st} body={r}")
            sys.exit(2)

    mapeo = json.load(open(MAPEO, encoding="utf-8"))
    ajenos_antes = int(sql(f"select count(*) from exercise_attempts "
                           f"where course_id not like '{PREFIJO}%'")[0][0])
    limpiar()

    try:
        # ------------------------------------------------------------------
        # 1. El mapeo REAL del curso, cargado como lo hace cargar-competencias.
        #    Se le cambia el prefijo del cuadernillo para no pisar datos reales,
        #    pero los identificadores de ejercicio son los de verdad.
        # ------------------------------------------------------------------
        prefijado = {PREFIJO + sem: ejs for sem, ejs in mapeo.items()}
        st, r = http("POST", "/internal/competencias", prefijado, token=MAESTRO)
        relaciones = (r or {}).get("relaciones", 0)
        ok("1. el mapeo real del curso se carga entero",
           st == 200 and relaciones == sum(len(c) for e in mapeo.values() for c in e.values()),
           f"status={st} relaciones={relaciones}")

        # ------------------------------------------------------------------
        # 2. Un alumno resuelve un cuadernillo REDISENIADO (semana_03), con los
        #    identificadores que produce el constructor tras el recorte.
        # ------------------------------------------------------------------
        s03 = PREFIJO + "semana_03"
        ejercicios = sorted(mapeo["semana_03"], key=lambda e: int(e.split("_")[1]))
        ok("2. la semana 3 rediseniada tiene 6 ejercicios etiquetados",
           len(ejercicios) == 6, f"{ejercicios}")

        # Recorrido realista: ejecuta la plantilla (deja el stub en el buffer),
        # escribe su codigo y aprueba. El intento aprobado ARRASTRA el stub, que
        # es el caso que rompia el criterio viejo.
        for ej in ejercicios[:4]:
            st, _ = http("POST", "/api/exercises/attempts",
                         intento(s03, ej, "passed", stub(ej)), token=tokens[ANA])
            if st != 201:
                ok(f"   intento de {ej}", False, f"status={st}")
        # Uno lo falla de verdad antes de resolverlo.
        http("POST", "/api/exercises/attempts",
             intento(s03, ejercicios[4], "failed",
                     [{"cell_id": ejercicios[4], "timestamp": "2026-09-21T11:00:00.000Z",
                       "error_type": "AssertionError", "error_message": "fallo",
                       "traceback": ""}]), token=tokens[ANA])
        st, _ = http("POST", "/api/exercises/attempts",
                     intento(s03, ejercicios[4], "passed"), token=tokens[ANA])
        ok("3. los intentos del cuadernillo rediseniado se guardan", st == 201, f"status={st}")

        guardados = int(sql(f"select count(*) from exercise_attempts "
                            f"where cuadernillo_id='{s03}'")[0][0])
        ok("4. llegaron los seis intentos a la base", guardados == 6, f"guardados={guardados}")

        # ------------------------------------------------------------------
        # 3. La competencia se resuelve por JOIN, sin viajar en el payload.
        # ------------------------------------------------------------------
        filas = sql(f"""
            select ec.competencia_id, count(*)
              from exercise_attempts a
              join ejercicio_competencias ec
                on ec.cuadernillo_id = a.cuadernillo_id
               and ec.exercise_id    = a.exercise_id
             where a.cuadernillo_id = '{s03}'
             group by 1 order by 1""")
        por_comp = {f[0]: int(f[1]) for f in filas}
        ok("5. la competencia se resuelve por JOIN, sin ir en el payload",
           "I3" in por_comp and "I1" in por_comp,
           f"clasificado en {por_comp}")

        # ------------------------------------------------------------------
        # 4. El nivel llega al panel del docente, con su motivo.
        # ------------------------------------------------------------------
        st, ficha = http("GET", f"/internal/curso/{CURSO}/estudiante/{ANA}", token=MAESTRO)
        comp = {c["competencia_id"]: c for c in (ficha or {}).get("competencias") or []}
        i3 = comp.get("I3", {})
        ok("6. el panel devuelve nivel y motivo para la competencia trabajada",
           st == 200 and i3.get("nivel") in (1, 2, 3) and i3.get("motivo_nivel"),
           f"status={st} I3={ {k: i3.get(k) for k in ('ejercicios_vistos','ejercicios_resueltos','fallos','nivel','motivo_nivel')} }")

        ok("7. el intento aprobado que arrastra el stub SI cuenta",
           i3.get("ejercicios_vistos", 0) >= 4 and i3.get("ejercicios_resueltos", 0) >= 4,
           f"vistos={i3.get('ejercicios_vistos')} resueltos={i3.get('ejercicios_resueltos')}")

        fuera = [c for c in comp.values() if not c.get("en_alcance")]
        ok("8. las competencias fuera de alcance no reciben nivel",
           all(c.get("nivel") is None for c in fuera) and fuera,
           f"fuera de alcance: {[(c['competencia_id'], c.get('nivel')) for c in fuera]}")

        # ------------------------------------------------------------------
        # 5. El filtro por semana acota, y avisa de que no hay evidencia.
        # ------------------------------------------------------------------
        st, f9 = http("GET", f"/internal/curso/{CURSO}/estudiante/{ANA}"
                             f"?cuadernillo={s03}", token=MAESTRO)
        c9 = {c["competencia_id"]: c for c in (f9 or {}).get("competencias") or []}
        ok("9. filtrar por semana acota a los ejercicios de esa semana",
           st == 200 and c9.get("I3", {}).get("ejercicios_disenados") ==
           sum(1 for cs in mapeo["semana_03"].values() if "I3" in cs),
           f"disenados en la semana = {c9.get('I3', {}).get('ejercicios_disenados')}")

        # ------------------------------------------------------------------
        # 6. Congelar un corte guarda el nivel con sus umbrales.
        # ------------------------------------------------------------------
        st, r = http("POST", f"/internal/curso/{CURSO}/corte", {"etiqueta": "pre"}, token=MAESTRO)
        fila = sql(f"select coalesce(nivel::text,'NULO'), umbrales::text "
                   f"from corte_competencia where course_id='{CURSO}' "
                   f"and student_id='{ANA}' and competencia_id='I3' and etiqueta='pre'")
        ok("10. el corte congela el nivel junto con los umbrales que lo produjeron",
           st == 200 and fila and fila[0][0] == str(i3.get("nivel"))
           and "cobertura_n3" in fila[0][1],
           f"status={st} corte={fila[0] if fila else None}")

        # ------------------------------------------------------------------
        # 7. REGRESION: un cuadernillo que NO se toco sigue igual.
        # ------------------------------------------------------------------
        s02 = PREFIJO + "semana_02"
        for ej in sorted(mapeo["semana_02"])[:3]:
            http("POST", "/api/exercises/attempts",
                 intento(s02, ej, "passed", alumno=BETO), token=tokens[BETO])
        n02 = int(sql(f"select count(*) from exercise_attempts "
                      f"where cuadernillo_id='{s02}'")[0][0])
        ok("11. REGRESION: los cuadernillos no tocados siguen guardando metricas",
           n02 == 3, f"intentos de semana_02 = {n02}")

        # ------------------------------------------------------------------
        # 8. REGRESION: un ejercicio SIN etiqueta se sigue guardando.
        #    Seis quedaron asi a proposito en las semanas 1 y 2.
        # ------------------------------------------------------------------
        st, _ = http("POST", "/api/exercises/attempts",
                     intento(PREFIJO + "semana_01", "ejercicio_1", "passed", alumno=BETO),
                     token=tokens[BETO])
        n = int(sql(f"select count(*) from exercise_attempts "
                    f"where cuadernillo_id='{PREFIJO}semana_01' "
                    f"and exercise_id='ejercicio_1'")[0][0])
        ok("12. REGRESION: un ejercicio sin competencia se guarda igual, no se pierde",
           st == 201 and n == 1, f"status={st} guardados={n}")

    finally:
        limpiar()
        ajenos = int(sql(f"select count(*) from exercise_attempts "
                         f"where course_id not like '{PREFIJO}%'")[0][0])
        restan = int(sql(f"select count(*) from exercise_attempts "
                         f"where course_id like '{PREFIJO}%'")[0][0])
        ok("13. limpieza: todo lo de la prueba borrado, lo ajeno intacto",
           restan == 0 and ajenos == ajenos_antes,
           f"restan={restan} ajenos antes/despues={ajenos_antes}/{ajenos}")

    buenos = sum(1 for _, v in resultados if v)
    print(f"\nRESUMEN: {buenos}/{len(resultados)} OK")
    for n_, v in resultados:
        if not v:
            print("  FALLO: " + n_)
    sys.exit(0 if buenos == len(resultados) else 1)


if __name__ == "__main__":
    main()
