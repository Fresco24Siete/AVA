#!/usr/bin/env python3
"""Pruebas de integracion del tramo backend Go -> PostgreSQL -> API de lectura.

Corre contra un backend y una base vivos. Solo usa stdlib (urllib, json,
subprocess). Todo lo que crea lleva course_id/student_id con prefijo PRUEBA- y
se borra al final (caso 11).

Variables de entorno:
  API_BASE              default http://localhost:8080
  PG_EXEC               default "docker exec -i postgres-db psql -U <DB_USER> -d <DB_NAME> -At"
  METRICS_API_TOKEN     token maestro (si falta se lee de <repo>/.env)
  METRICS_TOKEN_SECRET  secreto HMAC (si falta se lee de <repo>/.env; solo para
                        documentar, el script no firma nada)
  ENV_FILE              ruta del .env (default <repo>/.env)
"""
import json
import os
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))


def leer_env(ruta):
    valores = {}
    if not os.path.exists(ruta):
        return valores
    with open(ruta) as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            k, v = linea.split("=", 1)
            valores[k.strip()] = v.strip().strip('"').strip("'")
    return valores


ENV = leer_env(os.environ.get("ENV_FILE", os.path.join(REPO, ".env")))


def cfg(nombre, default=None):
    return os.environ.get(nombre) or ENV.get(nombre) or default


API_BASE = cfg("API_BASE", "http://localhost:8080").rstrip("/")
DB_USER = cfg("DB_USER", "ava")
DB_NAME = cfg("DB_NAME", "ava")
PG_EXEC = cfg("PG_EXEC", f"docker exec -i postgres-db psql -U {DB_USER} -d {DB_NAME} -At")
TOKEN_MAESTRO = cfg("METRICS_API_TOKEN")
SECRETO = cfg("METRICS_TOKEN_SECRET")

PREFIJO = "PRUEBA-"
C1, C2 = "PRUEBA-C1", "PRUEBA-C2"
A, B, C = "PRUEBA-A", "PRUEBA-B", "PRUEBA-C"
CUAD = "PRUEBA-semana_01"

resultados = []   # (nombre, ok, detalle)
hallazgos = []    # textos de bugs/discrepancias detectadas en ejecucion


# ----------------------------------------------------------------- utilidades
def http(metodo, ruta, cuerpo=None, token=None, raw=None):
    """Devuelve (status, json_o_texto). Nunca lanza por status HTTP."""
    datos = None
    cab = {"Content-Type": "application/json"}
    if token is not None:
        cab["Authorization"] = "Bearer " + token
    if raw is not None:
        datos = raw.encode()
    elif cuerpo is not None:
        datos = json.dumps(cuerpo).encode()
    req = urllib.request.Request(API_BASE + ruta, data=datos, method=metodo, headers=cab)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            texto = r.read().decode()
            status = r.status
    except urllib.error.HTTPError as e:
        texto = e.read().decode()
        status = e.code
    try:
        return status, json.loads(texto) if texto else None
    except json.JSONDecodeError:
        return status, texto


def sql(consulta):
    """Ejecuta SQL via PG_EXEC; devuelve lista de filas (listas de str)."""
    p = subprocess.run(PG_EXEC.split() + ["-F", "\t", "-v", "ON_ERROR_STOP=1"],
                       input=consulta, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"psql fallo: {p.stderr.strip()}\nSQL: {consulta}")
    return [l.split("\t") for l in p.stdout.splitlines() if l != ""]


def sql1(consulta):
    filas = sql(consulta)
    return filas[0] if filas else None


def registrar(nombre, ok, detalle=""):
    resultados.append((nombre, ok, detalle))
    print(f"[{'OK' if ok else 'FALLO'}] {nombre}")
    if detalle:
        for linea in str(detalle).splitlines():
            print("       " + linea)


def hallazgo(texto):
    hallazgos.append(texto)
    print("  >> HALLAZGO: " + texto)


def intento(exercise_id, attempt_at, resultado, errors=None, cuadernillo=CUAD,
            student_id=A, course_id=C1, con_celda=True, orden=78, puntos=10):
    """Payload EXACTO que llega al backend: lo que arma custom.js (sin
    tipo_evento, que el puente hace pop) mas la IDENTIDAD que anade
    metrics_bridge.py (student_id, student_name, student_email, course_id,
    cuadernillo_id)."""
    p = {
        "exercise_id": exercise_id,
        "attempt_at": attempt_at,
        "validation_result": resultado,
        "errors": errors or [],
        # identidad que impone metrics_bridge.py (IDENTIDAD)
        "student_id": student_id,
        "student_name": "Alumno de Prueba",
        "student_email": "prueba@ejemplo.test",
        "course_id": course_id,
        "cuadernillo_id": cuadernillo,
    }
    if con_celda:
        p["codigo_celda"] = "test_" + exercise_id
        p["orden"] = orden
        p["puntos_maximos"] = puntos
    return p


def error_de(cell_id, ts, tipo="AssertionError", msg="AssertionError: fallo la prueba"):
    return {"cell_id": cell_id, "timestamp": ts, "error_type": tipo,
            "error_message": msg,
            "traceback": "Traceback (most recent call last)\n  ...\n" + msg}


def contar_ajenos():
    return {
        "exercise_attempts": int(sql1(f"select count(*) from exercise_attempts where course_id not like '{PREFIJO}%'")[0]),
        "attempt_errors": int(sql1(f"select count(*) from attempt_errors e join exercise_attempts a on a.id=e.attempt_id where a.course_id not like '{PREFIJO}%'")[0]),
        "cuadernillo_ratings": int(sql1(f"select count(*) from cuadernillo_ratings where course_id not like '{PREFIJO}%'")[0]),
        "cuadernillo_notas": int(sql1(f"select count(*) from cuadernillo_notas where course_id not like '{PREFIJO}%'")[0]),
    }


def limpiar():
    sql(f"""
        delete from exercise_attempts where course_id like '{PREFIJO}%';
        delete from cuadernillo_ratings where course_id like '{PREFIJO}%';
        delete from cuadernillo_notas where course_id like '{PREFIJO}%';
    """)


def restantes():
    return {
        "exercise_attempts": int(sql1(f"select count(*) from exercise_attempts where course_id like '{PREFIJO}%'")[0]),
        "attempt_errors": int(sql1(f"select count(*) from attempt_errors e join exercise_attempts a on a.id=e.attempt_id where a.course_id like '{PREFIJO}%'")[0]),
        "cuadernillo_ratings": int(sql1(f"select count(*) from cuadernillo_ratings where course_id like '{PREFIJO}%'")[0]),
        "cuadernillo_notas": int(sql1(f"select count(*) from cuadernillo_notas where course_id like '{PREFIJO}%'")[0]),
    }


# ------------------------------------------------------------------- casos
tokens = {}


def caso_1_mint():
    st, r = http("POST", "/internal/lti/mint-metrics-token",
                 {"estudiante_id": A, "curso_id": C1, "cuadernillo_codigo": ""})
    ok = st == 401 or st == 503
    registrar("1a mint sin token maestro -> 401/503", ok, f"status={st} body={r}")

    st, r = http("POST", "/internal/lti/mint-metrics-token",
                 {"estudiante_id": A, "curso_id": C1, "cuadernillo_codigo": ""}, token="no-es-el-maestro")
    registrar("1b mint con token maestro incorrecto -> 401", st == 401, f"status={st} body={r}")

    todo_ok = True
    for sid, cid in ((A, C1), (B, C1), (C, C2)):
        st, r = http("POST", "/internal/lti/mint-metrics-token",
                     {"estudiante_id": sid, "curso_id": cid, "cuadernillo_codigo": ""}, token=TOKEN_MAESTRO)
        tok = (r or {}).get("token") if isinstance(r, dict) else None
        if st != 200 or not tok:
            todo_ok = False
            registrar(f"1c mint {sid}/{cid}", False, f"status={st} body={r}")
            continue
        tokens[sid] = tok
        # decodificar los claims (base64url JSON) solo para evidencia
        import base64
        parte = tok.split(".")[0]
        claims = json.loads(base64.urlsafe_b64decode(parte + "=" * (-len(parte) % 4)))
        coincide = claims.get("sid") == sid and claims.get("cid") == cid
        todo_ok = todo_ok and coincide
        registrar(f"1c mint {sid}/{cid} -> 200 con claims sid/cid", coincide,
                  f"status={st} claims={claims}")
    if not todo_ok:
        print("Sin tokens no se puede seguir.")
        sys.exit(2)


def caso_2_exito():
    at = "2026-08-22T21:10:00.123Z"
    # a proposito: student_id=B en el cuerpo con el token de A
    p = intento("ejercicio_1", at, "passed", student_id=B, course_id=C2)
    st, r = http("POST", "/api/exercises/attempts", p, token=tokens[A])
    aid = (r or {}).get("attempt_id") if isinstance(r, dict) else None
    fila = sql1(f"""select student_id, course_id, cuadernillo_id, exercise_id, validation_result,
                          puntos_maximos, codigo_celda, orden,
                          to_char(attempt_at at time zone 'UTC','YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
                          received_at is not null, received_at >= now() - interval '2 minutes',
                          received_at > attempt_at
                   from exercise_attempts where id='{aid}'""") if aid else None
    esperado = [A, C1, CUAD, "ejercicio_1", "passed", "10", "test_ejercicio_1", "78", at, "t", "t", "t"]
    ok = st == 201 and fila == esperado
    registrar("2 intento passed: identidad del TOKEN manda sobre el cuerpo, columnas completas", ok,
              f"request student_id={B} course_id={C2} con token de {A}\nstatus={st} body={r}\nfila={fila}\nesperado={esperado}")
    nerr = sql1(f"select count(*) from attempt_errors where attempt_id='{aid}'")[0] if aid else None
    registrar("2b intento passed sin errors -> 0 attempt_errors", nerr == "0", f"attempt_errors={nerr}")


def caso_3_fallo():
    at = "2026-08-22T21:12:00.500Z"
    t1, t2 = "2026-08-22T21:11:40.001Z", "2026-08-22T21:12:00.100Z"
    errs = [error_de("ejercicio_2", t1, "NameError", "NameError: name 'total' is not defined"),
            error_de("test_ejercicio_2", t2, "AssertionError", "AssertionError: Todo programa debe terminar con PARAR")]
    p = intento("ejercicio_2", at, "failed", errors=errs)
    st, r = http("POST", "/api/exercises/attempts", p, token=tokens[A])
    aid = (r or {}).get("attempt_id") if isinstance(r, dict) else None
    filas = sql(f"""select cell_id, error_type, error_message,
                           to_char(occurred_at at time zone 'UTC','YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
                    from attempt_errors where attempt_id='{aid}' order by occurred_at""") if aid else []
    esperado = [["ejercicio_2", "NameError", "NameError: name 'total' is not defined", t1],
                ["test_ejercicio_2", "AssertionError", "AssertionError: Todo programa debe terminar con PARAR", t2]]
    ok = st == 201 and filas == esperado
    registrar("3 intento failed con 2 errors -> 2 attempt_errors enlazadas, occurred_at exacto", ok,
              f"status={st} body={r}\nfilas={filas}")
    cols = [f[0] for f in sql("select column_name from information_schema.columns where table_name='attempt_errors'")]
    registrar("3b traceback se descarta (no hay columna en attempt_errors)", "traceback" not in cols,
              f"columnas attempt_errors={cols}; el backend acepto el payload con traceback (status {st}) y lo ignoro")


def caso_4_multiples():
    base = "2026-08-22T21:2{0}:00.000Z"
    ids = []
    for i, res in enumerate(("failed", "failed", "passed")):
        errs = [error_de("test_ejercicio_3", base.format(i))] if res == "failed" else []
        st, r = http("POST", "/api/exercises/attempts",
                     intento("ejercicio_3", base.format(i), res, errors=errs), token=tokens[A])
        ids.append((st, (r or {}).get("attempt_id")))
    filas = sql(f"""select validation_result, to_char(attempt_at at time zone 'UTC','HH24:MI:SS')
                    from exercise_attempts where student_id='{A}' and course_id='{C1}' and exercise_id='ejercicio_3'
                    order by attempt_at""")
    esperado = [["failed", "21:20:00"], ["failed", "21:21:00"], ["passed", "21:22:00"]]
    distintos = len({i[1] for i in ids}) == 3
    registrar("4 tres intentos del mismo ejercicio -> 3 filas distintas en orden attempt_at",
              filas == esperado and distintos and all(s == 201 for s, _ in ids),
              f"status/ids={ids}\nfilas={filas}")


def caso_5_sin_validar():
    at = "2026-08-22T21:30:00.000Z"
    p = intento("ejercicio_4", at, "sin_validar", con_celda=False,
                errors=[error_de("ejercicio_4", "2026-08-22T21:29:00.000Z", "NameError", "NameError: name 'x' is not defined")])
    st, r = http("POST", "/api/exercises/attempts", p, token=tokens[A])
    aid = (r or {}).get("attempt_id") if isinstance(r, dict) else None
    fila = sql1(f"""select validation_result, codigo_celda is null, orden is null, puntos_maximos is null,
                           (select count(*) from attempt_errors where attempt_id='{aid}')
                    from exercise_attempts where id='{aid}'""") if aid else None
    registrar("5 sin_validar (beacon) -> codigo_celda/orden/puntos_maximos NULL, 1 error",
              st == 201 and fila == ["sin_validar", "t", "t", "t", "1"], f"status={st} body={r}\nfila={fila}")


def caso_6_medianoche():
    casos = [("2026-08-22T23:59:59.000-05:00", "2026-08-23 04:59:59", "2026-08-22"),
             ("2026-08-23T00:00:01.000-05:00", "2026-08-23 05:00:01", "2026-08-23")]
    for i, (enviado, utc_esp, dia_local_esp) in enumerate(casos):
        ex = f"ejercicio_medianoche_{i}"
        st, r = http("POST", "/api/exercises/attempts", intento(ex, enviado, "passed"), token=tokens[A])
        aid = (r or {}).get("attempt_id") if isinstance(r, dict) else None
        fila = sql1(f"""select to_char(attempt_at at time zone 'UTC','YYYY-MM-DD HH24:MI:SS'),
                               to_char(attempt_at at time zone 'America/Bogota','YYYY-MM-DD HH24:MI:SS'),
                               to_char(attempt_at at time zone 'America/Bogota','YYYY-MM-DD')
                        from exercise_attempts where id='{aid}'""") if aid else None
        ok = st == 201 and fila is not None and fila[0] == utc_esp and fila[2] == dia_local_esp
        registrar(f"6.{i} attempt_at={enviado} -> UTC {utc_esp}, dia Bogota {dia_local_esp}", ok,
                  f"status={st}\n[utc, bogota, dia_bogota]={fila}")

    # con 'Z'
    st, r = http("POST", "/api/exercises/attempts",
                 intento("ejercicio_z", "2026-08-23T04:59:59Z", "passed"), token=tokens[A])
    aid = (r or {}).get("attempt_id") if isinstance(r, dict) else None
    fila = sql1(f"select to_char(attempt_at at time zone 'UTC','YYYY-MM-DD HH24:MI:SS') from exercise_attempts where id='{aid}'") if aid else None
    registrar("6.z attempt_at con 'Z' se guarda tal cual en UTC", st == 201 and fila == ["2026-08-23 04:59:59"],
              f"status={st} fila={fila}")

    # naive (sin zona): Go time.Time usa RFC3339 estricto -> esperamos 400
    st, r = http("POST", "/api/exercises/attempts",
                 intento("ejercicio_naive", "2026-08-23T04:59:59", "passed"), token=tokens[A])
    fila = sql1(f"select to_char(attempt_at at time zone 'UTC','YYYY-MM-DD HH24:MI:SS') from exercise_attempts where student_id='{A}' and exercise_id='ejercicio_naive'")
    if st == 400:
        registrar("6.naive attempt_at sin zona -> Go lo rechaza con 400 (no se guarda nada)", fila is None,
                  f"status={st} body={r} fila={fila}")
        hallazgo("attempt_at naive (sin zona horaria) -> 400 'Sintaxis inválida en el cuerpo JSON': "
                 "Go time.Time solo acepta RFC3339. custom.js siempre manda toISOString() (con Z), asi que "
                 "no afecta al flujo real; pero un 400 se pierde en silencio (custom.js no mira resp.ok).")
    else:
        registrar("6.naive attempt_at sin zona", False,
                  f"status={st} body={r} fila={fila} (se esperaba 400; Go lo acepto e interpreto como {fila})")
        hallazgo(f"attempt_at naive aceptado con status {st} y guardado como {fila}")

    # timestamp de error ausente -> 0001-01-01 (documentado en el informe, sin validacion en Go)
    e = {"cell_id": "ejercicio_sin_ts", "error_type": "NameError", "error_message": "x"}
    st, r = http("POST", "/api/exercises/attempts",
                 intento("ejercicio_sin_ts", "2026-08-23T05:00:00Z", "failed", errors=[e]), token=tokens[A])
    aid = (r or {}).get("attempt_id") if isinstance(r, dict) else None
    fila = sql1(f"select to_char(occurred_at at time zone 'UTC','YYYY-MM-DD') from attempt_errors where attempt_id='{aid}'") if aid else None
    registrar("6.ts errors[].timestamp ausente -> 400 y no se guarda nada", st == 400 and not aid,
              f"status={st} body={r} occurred_at={fila}")
    if st == 201 and fila and fila[0].startswith("0001"):
        hallazgo("errors[].timestamp ausente se acepta (201) y se guarda occurred_at=0001-01-01: "
                 "exerciseHandler.go no valida que venga.")


def caso_7_rating():
    base = {"course_id": C1, "cuadernillo_id": CUAD, "student_id": A,
            "submitted_at": "2026-08-22T21:40:00.000Z", "rating": 3, "comment": "primero",
            "student_name": "Alumno de Prueba", "student_email": "prueba@ejemplo.test"}
    st1, r1 = http("POST", "/api/cuadernillos/ratings", base, token=tokens[A])
    base2 = dict(base, rating=5, comment=None, submitted_at="2026-08-22T21:41:00.000Z")
    st2, r2 = http("POST", "/api/cuadernillos/ratings", base2, token=tokens[A])
    filas = sql(f"select rating, comment is null, to_char(submitted_at at time zone 'UTC','HH24:MI:SS') from cuadernillo_ratings where student_id='{A}' and course_id='{C1}' and cuadernillo_id='{CUAD}'")
    registrar("7a rating upsert: dos POST mismo alumno/cuadernillo -> 1 fila con el ultimo",
              st1 == 201 and st2 == 201 and filas == [["5", "t", "21:41:00"]],
              f"status={st1},{st2} body={r1},{r2}\nfilas={filas}")

    # NEGATIVO: token de A, student_id=B en el cuerpo
    falso = dict(base, student_id=B, rating=1, comment="suplantado")
    st, r = http("POST", "/api/cuadernillos/ratings", falso, token=tokens[A])
    bajo_b = sql(f"select student_id, rating, comment from cuadernillo_ratings where student_id='{B}' and course_id='{C1}'")
    aislado = len(bajo_b) == 0
    registrar("7b AISLAMIENTO rating: token de A con student_id=B en el cuerpo NO debe guardarse bajo B", aislado,
              f"status={st} body={r}\nfilas bajo {B}={bajo_b}")
    if not aislado:
        hallazgo("FALLO DE AISLAMIENTO en POST /api/cuadernillos/ratings: con el token de PRUEBA-A y "
                 "student_id=PRUEBA-B en el cuerpo se guardo el rating bajo PRUEBA-B. "
                 "backend/internal/handler/cuadernilloRatingHandler.go:29-37 toma CourseID/StudentID del cuerpo "
                 "y nunca llama a middleware.IdentidadVerificada. Correccion: igual que exerciseHandler.go:68-74.")
    # tambien curso ajeno
    falso2 = dict(base, course_id=C2, rating=2, comment="curso ajeno")
    st, r = http("POST", "/api/cuadernillos/ratings", falso2, token=tokens[A])
    en_c2 = sql(f"select student_id, course_id from cuadernillo_ratings where student_id='{A}' and course_id='{C2}'")
    registrar("7c AISLAMIENTO rating: token de A (curso C1) con course_id=C2 NO debe guardarse en C2",
              len(en_c2) == 0, f"status={st} filas en C2={en_c2}")
    # rating fuera de rango
    st, r = http("POST", "/api/cuadernillos/ratings", dict(base, rating=9), token=tokens[A])
    registrar("7d rating=9 fuera de rango -> 400", st == 400, f"status={st} body={r}")
    if st == 500:
        hallazgo("rating fuera de 1..5 responde 500 (CHECK de la DB); deberia ser 400 validado en Go.")


def caso_8_mi_progreso():
    # sembrar algo de B (C1) y C (C2)
    http("POST", "/api/exercises/attempts", intento("ejercicio_1", "2026-08-22T22:00:00Z", "failed",
         errors=[error_de("test_ejercicio_1", "2026-08-22T22:00:00Z")], student_id=B), token=tokens[B])
    http("POST", "/api/exercises/attempts", intento("ejercicio_1", "2026-08-22T22:01:00Z", "passed",
         student_id=C, course_id=C2, cuadernillo="PRUEBA-semana_02"), token=tokens[C])

    def resumen(tok):
        st, r = http("GET", "/api/mi-progreso", token=tok)
        return st, r

    st, ra = resumen(tokens[A])
    cu_a = {c["cuadernillo_id"]: c for c in ra.get("cuadernillos", [])} if isinstance(ra, dict) else {}
    # A en C1: ejercicios distintos en CUAD: 1,2,3,4,med0,med1,z,sin_ts = 8; resueltos (passed alguna vez):
    # 1,3,med0,med1,z = 5; intentos totales: 1+1+3+1+2+1+1 = 10; abandonos: ejercicio_4 sin_validar sin passed = 1
    fila_db = sql1(f"""select count(distinct exercise_id) filter (where validation_result='passed'),
                              count(distinct exercise_id), count(*)
                       from exercise_attempts where student_id='{A}' and course_id='{C1}' and cuadernillo_id='{CUAD}'""")
    a = cu_a.get(CUAD, {})
    ok = (st == 200 and list(cu_a) == [CUAD]
          and [str(a.get("ejercicios_resueltos")), str(a.get("ejercicios_intentados")), str(a.get("intentos"))] == fila_db
          and a.get("abandonos") == 1)
    registrar("8a mi-progreso token A -> solo cuadernillos de A coherentes con la base", ok,
              f"status={st} body={json.dumps(ra, ensure_ascii=False)}\ndb(resueltos,intentados,intentos)={fila_db}")

    st, rb = resumen(tokens[B])
    cu_b = {c["cuadernillo_id"]: c for c in rb.get("cuadernillos", [])} if isinstance(rb, dict) else {}
    b = cu_b.get(CUAD, {})
    ok = st == 200 and list(cu_b) == [CUAD] and b.get("ejercicios_resueltos") == 0 and b.get("intentos") == 1
    registrar("8b mi-progreso token B -> solo lo de B (1 intento fallido, 0 resueltos)", ok,
              f"status={st} body={json.dumps(rb, ensure_ascii=False)}")

    st, rc = resumen(tokens[C])
    cu_c = {c["cuadernillo_id"]: c for c in rc.get("cuadernillos", [])} if isinstance(rc, dict) else {}
    ok = st == 200 and list(cu_c) == ["PRUEBA-semana_02"] and CUAD not in cu_c and cu_c["PRUEBA-semana_02"].get("intentos") == 1
    registrar("8c mi-progreso token C (curso C2) -> solo semana_02 de C2, nada de C1", ok,
              f"status={st} body={json.dumps(rc, ensure_ascii=False)}")

    st, r = http("GET", "/api/mi-progreso")
    registrar("8d mi-progreso sin token -> 401", st == 401, f"status={st} body={r}")

    cab, firma = tokens[A].rsplit(".", 1)
    firma_mal = ("A" if firma[0] != "A" else "B") + firma[1:]
    st, r = http("GET", "/api/mi-progreso", token=cab + "." + firma_mal)
    registrar("8e mi-progreso con firma manipulada -> 401", st == 401, f"status={st} body={r}")

    # claims manipulados (sid=B) con la firma de A -> 401
    import base64
    claims = json.loads(base64.urlsafe_b64decode(cab + "=" * (-len(cab) % 4)))
    claims["sid"] = B
    cab_b = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    st, r = http("GET", "/api/mi-progreso", token=cab_b + "." + firma)
    registrar("8f mi-progreso con claims reescritos (sid=B) y firma de A -> 401", st == 401, f"status={st} body={r}")
    st, r = http("GET", "/api/mi-progreso?student_id=" + B, token=tokens[A])
    cu = [c["cuadernillo_id"] for c in r.get("cuadernillos", [])] if isinstance(r, dict) else r
    registrar("8g mi-progreso ignora ?student_id= en la query", st == 200 and cu == [CUAD], f"status={st} cuadernillos={cu}")


def caso_9_panel_docente():
    def alumnos_en(panel):
        ids = set()
        texto = json.dumps(panel)
        for m in re.findall(r'"PRUEBA-[A-Z]"', texto):
            ids.add(m.strip('"'))
        return ids

    st, p1 = http("GET", f"/internal/curso/{C1}/panel", token=TOKEN_MAESTRO)
    ids1 = alumnos_en(p1)
    cuads1 = {c["cuadernillo_id"] for c in p1.get("cuadernillos", [])} if isinstance(p1, dict) else set()
    salud1 = p1.get("salud", {}) if isinstance(p1, dict) else {}
    ok = (st == 200 and C not in ids1 and cuads1 == {CUAD}
          and salud1.get("alumnos_con_telemetria") == 2 and "PRUEBA-semana_02" not in cuads1)
    registrar("9a panel C1 -> 2 alumnos con telemetria (A,B), nunca C ni semana_02 de C2", ok,
              f"status={st} cuadernillos={sorted(cuads1)} student_ids visibles={sorted(ids1)} salud={salud1}\n"
              f"en_riesgo={p1.get('en_riesgo') if isinstance(p1, dict) else None}")

    st, p2 = http("GET", f"/internal/curso/{C2}/panel", token=TOKEN_MAESTRO)
    ids2 = alumnos_en(p2)
    cuads2 = {c["cuadernillo_id"] for c in p2.get("cuadernillos", [])} if isinstance(p2, dict) else set()
    salud2 = p2.get("salud", {}) if isinstance(p2, dict) else {}
    ok = st == 200 and cuads2 == {"PRUEBA-semana_02"} and salud2.get("alumnos_con_telemetria") == 1 and not (ids2 & {A, B})
    registrar("9b panel C2 -> solo C (1 alumno, semana_02)", ok,
              f"status={st} cuadernillos={sorted(cuads2)} student_ids visibles={sorted(ids2)} salud={salud2}")

    st, r = http("GET", f"/internal/curso/{C1}/panel")
    registrar("9c panel sin token maestro -> 401", st == 401, f"status={st} body={r}")
    st, r = http("GET", f"/internal/curso/{C1}/panel", token=tokens[A])
    registrar("9d panel con token de ALUMNO -> 401", st == 401, f"status={st} body={r}")

    # El maestro (solo el Hub lo tiene) lee cualquier curso: es quien administra.
    st_real, real = http("GET", "/internal/curso/28053/panel", token=TOKEN_MAESTRO)
    registrar("9e el token maestro (del Hub) lee cualquier curso, p.ej. 28053", st_real == 200,
              f"status={st_real} salud={real.get('salud') if isinstance(real, dict) else real}")

    # El docente recibe un token con rol docente acotado a SU curso: lee el
    # suyo, no el de al lado, y no sube notas ajenas. Con un token de alumno
    # (sin rol) no entra.
    st, r = http("POST", "/internal/lti/mint-metrics-token",
                 {"estudiante_id": "PRUEBA-DOC", "curso_id": C1, "cuadernillo_codigo": "", "rol": "docente"},
                 token=TOKEN_MAESTRO)
    tok_doc = (r or {}).get("token") if isinstance(r, dict) else None
    registrar("9f mint con rol docente -> 200", st == 200 and bool(tok_doc), f"status={st} body={r}")
    if tok_doc:
        st, r = http("GET", f"/internal/curso/{C1}/panel", token=tok_doc)
        registrar("9g docente de C1 lee el panel de C1 -> 200", st == 200 and isinstance(r, dict) and r.get("curso_id") == C1,
                  f"status={st} curso_id={r.get('curso_id') if isinstance(r, dict) else r}")
        st, r = http("GET", f"/internal/curso/{C2}/panel", token=tok_doc)
        registrar("9h docente de C1 pide el panel de C2 -> 403", st == 403, f"status={st} body={r}")
        st, r = http("POST", "/internal/notas",
                     {"course_id": C2, "cuadernillo_id": "PRUEBA-semana_02", "origen": "nbgrader",
                      "notas": [{"student_id": C, "puntos_obtenidos": 1, "puntos_maximos": 10}]}, token=tok_doc)
        en_c2 = sql(f"select count(*) from cuadernillo_notas where course_id='{C2}'")
        registrar("9i docente de C1 sube notas de C2 -> 403 y nada guardado", st == 403 and en_c2 == [["0"]],
                  f"status={st} body={r} notas en C2={en_c2}")
        st, r = http("POST", "/internal/notas",
                     {"course_id": C1, "cuadernillo_id": CUAD, "origen": "nbgrader",
                      "notas": [{"student_id": A, "puntos_obtenidos": 7, "puntos_maximos": 10}]}, token=tok_doc)
        en_c1 = sql(f"select student_id, puntos_obtenidos from cuadernillo_notas where course_id='{C1}'")
        registrar("9j docente de C1 sube notas de C1 -> 201 y guardadas", st in (200, 201) and en_c1 == [[A, "7.00"]],
                  f"status={st} body={r} notas en C1={en_c1}")
        st, r = http("POST", "/internal/lti/mint-metrics-token",
                     {"estudiante_id": "PRUEBA-X", "curso_id": C1, "cuadernillo_codigo": ""}, token=tok_doc)
        registrar("9k docente no puede acunar tokens (solo el maestro) -> 401", st == 401, f"status={st} body={r}")
    st, r = http("POST", "/internal/lti/mint-metrics-token",
                 {"estudiante_id": "PRUEBA-DOC", "curso_id": C1, "cuadernillo_codigo": "", "rol": "rector"},
                 token=TOKEN_MAESTRO)
    registrar("9l mint con un rol desconocido -> 400", st == 400, f"status={st} body={r}")
    # relaciones_competencia en salud es global, no por curso
    if isinstance(p1, dict) and isinstance(p2, dict):
        r1, r2 = salud1.get("relaciones_competencia"), salud2.get("relaciones_competencia")
        if r1 == r2 and r1:
            hallazgo(f"salud.relaciones_competencia es igual en C1 y C2 ({r1}): cuenta ejercicio_competencias entero, "
                     "sin filtrar por curso (panelDocenteRepository.go ~:241; la tabla no tiene course_id).")


def caso_10_paralelo():
    N = 20
    fallos = {A: [], B: []}

    def enviar(sid, i):
        at = f"2026-08-22T23:{i:02d}:00.000Z"
        st, r = http("POST", "/api/exercises/attempts",
                     intento(f"ejercicio_par_{i}", at, "passed", student_id=sid, cuadernillo="PRUEBA-paralelo"),
                     token=tokens[sid])
        if st != 201:
            fallos[sid].append((i, st, r))

    hilos = []
    for i in range(N):
        for sid in (A, B):
            t = threading.Thread(target=enviar, args=(sid, i))
            hilos.append(t)
    for t in hilos:
        t.start()
    for t in hilos:
        t.join()
    filas = sql(f"select student_id, count(*) from exercise_attempts where cuadernillo_id='PRUEBA-paralelo' group by 1 order by 1")
    cruz = sql(f"select count(*) from exercise_attempts where cuadernillo_id='PRUEBA-paralelo' and student_id not in ('{A}','{B}')")
    ok = filas == [[A, str(N)], [B, str(N)]] and cruz == [["0"]] and not fallos[A] and not fallos[B]
    registrar(f"10 {N}+{N} intentos en paralelo (40 hilos) -> 20 y 20, cero cruzados", ok,
              f"conteo={filas} cruzados={cruz[0][0]} fallos_http={fallos}")


def caso_11_limpieza(ajenos_antes):
    antes = restantes()
    limpiar()
    despues = restantes()
    ajenos_despues = contar_ajenos()
    ok = all(v == 0 for v in despues.values()) and ajenos_despues == ajenos_antes
    registrar("11 limpieza: todo lo PRUEBA-% borrado (cascade a attempt_errors), cursos ajenos intactos", ok,
              f"PRUEBA antes={antes}\nPRUEBA despues={despues}\najenos antes={ajenos_antes}\najenos despues={ajenos_despues}")


# --------------------------------------------------------------------- main
def main():
    print(f"API_BASE={API_BASE}")
    print(f"PG_EXEC={PG_EXEC}")
    print(f"token maestro: {'si' if TOKEN_MAESTRO else 'NO'}; secreto: {'si' if SECRETO else 'NO'}")
    if not TOKEN_MAESTRO:
        print("Falta METRICS_API_TOKEN (entorno o .env)")
        sys.exit(2)
    tz = sql1("show timezone")[0]
    print(f"timezone de la base: {tz}")

    ajenos_antes = contar_ajenos()
    # Empieza limpio por si una corrida anterior murio a medias.
    limpiar()
    try:
        caso_1_mint()
        caso_2_exito()
        caso_3_fallo()
        caso_4_multiples()
        caso_5_sin_validar()
        caso_6_medianoche()
        caso_7_rating()
        caso_8_mi_progreso()
        caso_9_panel_docente()
        caso_10_paralelo()
    finally:
        caso_11_limpieza(ajenos_antes)

    total = len(resultados)
    oks = sum(1 for _, ok, _ in resultados if ok)
    print(f"\nRESUMEN: {oks}/{total} OK")
    for n, ok, _ in resultados:
        if not ok:
            print("  FALLO: " + n)
    if hallazgos:
        print("\nHALLAZGOS:")
        for h in hallazgos:
            print("  - " + h)
    sys.exit(0 if oks == total else 1)


if __name__ == "__main__":
    main()
