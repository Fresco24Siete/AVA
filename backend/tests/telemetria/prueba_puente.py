#!/usr/bin/env python3
"""
Prueba del puente metrics_bridge.py (cuadernillo -> servidor del alumno -> backend).

Se ejecuta DENTRO de un contenedor de mi_imagen_jupyterlab:latest (lo lanza
prueba_puente.sh). No necesita red externa: levanta

  * un backend STUB (http.server) en 127.0.0.1:18999 que guarda cada request y
    responde lo que se le configure (201 / 401 / 500 / no responder);
  * el servidor del alumno ('jupyter server', jupyter_server 1.24) con el
    entorno que pondria el Hub, cargando /etc/jupyter/jupyter_server_config.py
    (que activa metrics_bridge), con --ServerApp.token=xyz en 127.0.0.1:8888.

Luego manda POST a /nbgrader-metrics/evento imitando al navegador y verifica
lo que el stub recibio y lo que el puente contesto.

Codigo de salida: 0 si todos los casos pasan, 1 si alguno falla.
"""
import copy
import http.client
import http.server
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.parse

STUB_PORT = 18999
JUPYTER_PORT = 8888
TOKEN_JUPYTER = "xyz"
TOKEN_BACKEND = "token-de-prueba"

ENTORNO_HUB = {
    "ALUMNO_ID": "PRUEBA-P",
    "ALUMNO_NOMBRE": "Alumno De Prueba",
    "ALUMNO_EMAIL": "prueba-p@ejemplo.test",
    "ALUMNO_ROL": "estudiante",
    "CURSO_ID": "PRUEBA-C1",
    "CUADERNILLO_CODIGO": "semana_prueba",
    "ENVIAR_AL_BACKEND": "true",
    "STUDENT_METRICS_TOKEN": TOKEN_BACKEND,
    "STUDENT_METRICS_API_BASE": f"http://127.0.0.1:{STUB_PORT}",
}

# Payload exacto que arma custom.js en on_finished_execute (custom.js:428-437).
PAYLOAD_ATTEMPT = {
    "tipo_evento": "exercise_attempt",
    "exercise_id": "ejercicio_3",
    "codigo_celda": "test_ejercicio_3",
    "orden": 78,
    "puntos_maximos": 10,
    "attempt_at": "2026-08-22T21:10:00.123Z",
    "validation_result": "failed",
    "errors": [
        {"cell_id": "ejercicio_3", "timestamp": "2026-08-22T21:09:40.001Z",
         "error_type": "NameError",
         "error_message": "NameError: name 'total' is not defined",
         "traceback": "Traceback (most recent call last)\n  File ... NameError: name 'total' is not defined"},
        {"cell_id": "test_ejercicio_3", "timestamp": "2026-08-22T21:10:00.100Z",
         "error_type": "AssertionError",
         "error_message": "AssertionError: Todo programa debe terminar con PARAR",
         "traceback": "Traceback (most recent call last)\n  AssertionError: Todo programa debe terminar con PARAR"},
    ],
}

# Payload del rating (custom.js, enviar_rating_cuadernillo).
PAYLOAD_RATING = {
    "tipo_evento": "cuadernillo_rating",
    "rating": 4,
    "rated_at": "2026-08-22T21:20:00.000Z",
}


# ---------------------------------------------------------------------------
# Backend STUB
# ---------------------------------------------------------------------------
class Stub:
    def __init__(self):
        self.requests = []
        self.modo = 201          # 201 | 401 | 500 | "timeout"
        self.lock = threading.Lock()
        self.httpd = None

    def reset(self, modo=201):
        with self.lock:
            self.requests = []
            self.modo = modo

    def start(self):
        stub = self

        class H(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                cuerpo = self.rfile.read(n) if n else b""
                try:
                    js = json.loads(cuerpo)
                except Exception:
                    js = None
                with stub.lock:
                    stub.requests.append({
                        "method": "POST",
                        "path": self.path,
                        "authorization": self.headers.get("Authorization"),
                        "content_type": self.headers.get("Content-Type"),
                        "body_raw": cuerpo.decode("utf-8", "replace"),
                        "body": js,
                    })
                    modo = stub.modo
                if modo == "timeout":
                    time.sleep(12)       # > request_timeout=5 del puente
                    return
                resp = json.dumps({"stub": True, "codigo": modo}).encode()
                self.send_response(modo)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)

            do_GET = do_POST

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", STUB_PORT), H)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None


# ---------------------------------------------------------------------------
# Servidor del alumno
# ---------------------------------------------------------------------------
class ServidorAlumno:
    def __init__(self, entorno_extra, nombre):
        self.nombre = nombre
        self.env = dict(os.environ)
        self.env.update(ENTORNO_HUB)
        self.env.update(entorno_extra)
        self.proc = None
        self.log_path = f"/tmp/jupyter-{nombre}.log"

    def start(self):
        cmd = [
            "jupyter", "server",
            f"--ServerApp.token={TOKEN_JUPYTER}",
            "--ServerApp.password=",
            "--ServerApp.ip=127.0.0.1",
            f"--ServerApp.port={JUPYTER_PORT}",
            "--ServerApp.port_retries=0",
            "--ServerApp.open_browser=False",
            # Solo el puente bajo prueba; las demas extensiones (tutor, panel,
            # admin) no hacen falta sin Hub y solo ensucian el log.
            "--ServerApp.jpserver_extensions={'metrics_bridge': True}",
        ]
        self.logf = open(self.log_path, "wb")
        self.proc = subprocess.Popen(cmd, env=self.env, stdout=self.logf,
                                     stderr=subprocess.STDOUT,
                                     preexec_fn=os.setsid)
        limite = time.time() + 60
        while time.time() < limite:
            if self.proc.poll() is not None:
                raise RuntimeError(f"jupyter server murio al arrancar; log en {self.log_path}:\n"
                                   + open(self.log_path).read()[-3000:])
            try:
                c = http.client.HTTPConnection("127.0.0.1", JUPYTER_PORT, timeout=2)
                c.request("GET", f"/api/status?token={TOKEN_JUPYTER}")
                r = c.getresponse()
                r.read()
                if r.status == 200:
                    return
            except OSError:
                pass
            time.sleep(0.5)
        raise RuntimeError("jupyter server no respondio en 60 s")

    def stop(self):
        if self.proc and self.proc.poll() is None:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                self.proc.wait()
        self.logf.close()
        # esperar a que el puerto quede libre
        for _ in range(40):
            s = socket.socket()
            try:
                s.connect(("127.0.0.1", JUPYTER_PORT))
                s.close()
                time.sleep(0.25)
            except OSError:
                s.close()
                return

    def log_cola(self, n=1500):
        try:
            return open(self.log_path, errors="replace").read()[-n:]
        except OSError:
            return ""


# ---------------------------------------------------------------------------
# Cliente que imita al navegador
# ---------------------------------------------------------------------------
class Navegador:
    """Hace GET /?token=xyz una vez para que el server le ponga la cookie de
    sesion y la cookie _xsrf, y despues manda POST como custom.js."""

    def __init__(self):
        self.cookies = {}

    def _guardar_cookies(self, resp):
        for k, v in resp.getheaders():
            if k.lower() == "set-cookie":
                par = v.split(";", 1)[0]
                if "=" in par:
                    nombre, valor = par.split("=", 1)
                    self.cookies[nombre.strip()] = valor.strip()

    def iniciar_sesion(self):
        c = http.client.HTTPConnection("127.0.0.1", JUPYTER_PORT, timeout=10)
        c.request("GET", f"/?token={TOKEN_JUPYTER}")
        r = c.getresponse()
        r.read()
        self._guardar_cookies(r)
        # jupyter_server manda la cookie _xsrf en la pagina (tree/lab). Si no
        # vino en '/', se pide una ruta que la fuerce.
        if "_xsrf" not in self.cookies:
            c.request("GET", "/api/status", headers={"Cookie": self.cookie_header()})
            r = c.getresponse()
            r.read()
            self._guardar_cookies(r)
        c.close()
        return dict(self.cookies)

    def cookie_header(self):
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())

    @property
    def xsrf(self):
        return self.cookies.get("_xsrf", "")

    def post(self, cuerpo, modo="cookie+xsrf", query="", raw=None):
        """modo: cookie+xsrf | cookie_sin_xsrf | cookie+xsrf_malo | token |
        token_malo | nada | cookie_beacon (xsrf en la query, sin cabecera)."""
        headers = {"Content-Type": "application/json"}
        if modo in ("cookie+xsrf", "cookie_sin_xsrf", "cookie+xsrf_malo", "cookie_beacon"):
            headers["Cookie"] = self.cookie_header()
        if modo == "cookie+xsrf":
            headers["X-XSRFToken"] = self.xsrf
        if modo == "cookie+xsrf_malo":
            headers["X-XSRFToken"] = "2|deadbeef|0000000000000000000000000000000|0"
        if modo == "token":
            headers["Authorization"] = f"token {TOKEN_JUPYTER}"
        if modo == "token_malo":
            headers["Authorization"] = "token equivocado"
        if modo == "cookie_beacon":
            query = "?_xsrf=" + urllib.parse.quote(self.xsrf, safe="")
        datos = raw if raw is not None else json.dumps(cuerpo).encode()
        c = http.client.HTTPConnection("127.0.0.1", JUPYTER_PORT, timeout=30)
        c.request("POST", "/nbgrader-metrics/evento" + query, body=datos, headers=headers)
        r = c.getresponse()
        cuerpo_resp = r.read()
        c.close()
        try:
            js = json.loads(cuerpo_resp) if cuerpo_resp else None
        except Exception:
            # Las paginas de error de tornado son HTML: se resume para la evidencia.
            texto = cuerpo_resp.decode("utf-8", "replace")
            m = re.search(r"<title>(.*?)</title>", texto, re.S)
            js = f"<html {len(cuerpo_resp)} bytes, title={m.group(1).strip() if m else '?'}>"
        return r.status, js, cuerpo_resp


# ---------------------------------------------------------------------------
# Marco de casos
# ---------------------------------------------------------------------------
RESULTADOS = []


def caso(nombre, condiciones, evidencia):
    """condiciones: lista de (descripcion, bool)."""
    fallas = [d for d, ok in condiciones if not ok]
    ok = not fallas
    RESULTADOS.append((nombre, ok))
    print(f"\n[{'OK' if ok else 'FALLO'}] {nombre}")
    for d, b in condiciones:
        print(f"    {'ok ' if b else 'XX '} {d}")
    print("    evidencia: " + json.dumps(evidencia, ensure_ascii=False, default=str)[:1400])
    return ok


def esperar_stub(stub, n=1, seg=8):
    limite = time.time() + seg
    while time.time() < limite:
        with stub.lock:
            if len(stub.requests) >= n:
                return copy.deepcopy(stub.requests)
        time.sleep(0.05)
    with stub.lock:
        return copy.deepcopy(stub.requests)


def main():
    stub = Stub()
    stub.start()
    print(f"stub backend escuchando en 127.0.0.1:{STUB_PORT}")

    servidor = ServidorAlumno({}, "principal")
    try:
        servidor.start()
        print(f"jupyter server listo en 127.0.0.1:{JUPYTER_PORT} (log: {servidor.log_path})")
        nav = Navegador()
        cookies = nav.iniciar_sesion()
        print("cookies recibidas tras GET /?token=xyz:", sorted(cookies))

        # ---- Autenticacion: las dos formas y el rechazo -----------------------
        stub.reset(201)
        st, js, _ = nav.post(PAYLOAD_ATTEMPT, modo="nada")
        reqs = esperar_stub(stub, 1, seg=1)
        caso("auth.0 sin cookie de sesion ni xsrf (pagina ajena) -> 403 y el stub no recibe nada",
             [("status 403", st == 403), ("stub sin requests", len(reqs) == 0)],
             {"status": st, "cuerpo": js, "stub_requests": len(reqs)})

        stub.reset(201)
        st, js, _ = nav.post(PAYLOAD_ATTEMPT, modo="cookie_sin_xsrf")
        reqs = esperar_stub(stub, 1, seg=1)
        caso("auth.1 cookie de sesion SIN X-XSRFToken -> 403",
             [("status 403", st == 403), ("stub sin requests", len(reqs) == 0)],
             {"status": st, "cuerpo": js, "stub_requests": len(reqs)})

        stub.reset(201)
        st, js, _ = nav.post(PAYLOAD_ATTEMPT, modo="cookie+xsrf_malo")
        reqs = esperar_stub(stub, 1, seg=1)
        caso("auth.2 cookie de sesion con X-XSRFToken que no coincide -> 403",
             [("status 403", st == 403), ("stub sin requests", len(reqs) == 0)],
             {"status": st, "cuerpo": js, "stub_requests": len(reqs)})

        stub.reset(201)
        st, js, _ = nav.post(PAYLOAD_ATTEMPT, modo="token_malo")
        reqs = esperar_stub(stub, 1, seg=1)
        caso("auth.3 'Authorization: token equivocado' sin cookies -> 403",
             [("status 403", st == 403), ("stub sin requests", len(reqs) == 0)],
             {"status": st, "cuerpo": js, "stub_requests": len(reqs)})

        stub.reset(201)
        st, js, _ = nav.post(PAYLOAD_ATTEMPT, modo="token")
        reqs = esperar_stub(stub, 1)
        caso("auth.4 'Authorization: token xyz' sin cookie ni xsrf -> aceptado (token_authenticated salta el xsrf)",
             [("status 204", st == 204), ("stub recibio 1 request", len(reqs) == 1)],
             {"status": st, "stub_requests": len(reqs)})

        # ---- (a) exercise_attempt como custom.js (cookie + X-XSRFToken) ------
        stub.reset(201)
        enviado = copy.deepcopy(PAYLOAD_ATTEMPT)
        enviado["student_id"] = "otro"          # el navegador intenta suplantar
        enviado["course_id"] = "OTRO-CURSO"
        st, js, raw = nav.post(enviado, modo="cookie+xsrf")
        reqs = esperar_stub(stub, 1)
        r = reqs[0] if reqs else {}
        b = r.get("body") or {}
        conds = [
            ("respuesta al navegador 204", st == 204),
            ("respuesta sin cuerpo", raw == b""),
            ("stub recibio exactamente 1 request", len(reqs) == 1),
            ("POST /api/exercises/attempts", r.get("method") == "POST" and r.get("path") == "/api/exercises/attempts"),
            ("Authorization: Bearer token-de-prueba", r.get("authorization") == f"Bearer {TOKEN_BACKEND}"),
            ("Content-Type: application/json", (r.get("content_type") or "").startswith("application/json")),
            ("student_id=PRUEBA-P (sobrescribe 'otro')", b.get("student_id") == "PRUEBA-P"),
            ("course_id=PRUEBA-C1 (sobrescribe 'OTRO-CURSO')", b.get("course_id") == "PRUEBA-C1"),
            ("cuadernillo_id=semana_prueba", b.get("cuadernillo_id") == "semana_prueba"),
            ("student_name", b.get("student_name") == ENTORNO_HUB["ALUMNO_NOMBRE"]),
            ("student_email", b.get("student_email") == ENTORNO_HUB["ALUMNO_EMAIL"]),
            ("SIN tipo_evento", "tipo_evento" not in b),
            ("exercise_id intacto", b.get("exercise_id") == "ejercicio_3"),
            ("codigo_celda intacto", b.get("codigo_celda") == "test_ejercicio_3"),
            ("orden intacto", b.get("orden") == 78),
            ("puntos_maximos intacto", b.get("puntos_maximos") == 10),
            ("attempt_at intacto", b.get("attempt_at") == PAYLOAD_ATTEMPT["attempt_at"]),
            ("validation_result intacto", b.get("validation_result") == "failed"),
            ("errors[] intacto con traceback", b.get("errors") == PAYLOAD_ATTEMPT["errors"]),
        ]
        caso("(a) exercise_attempt con cookie+X-XSRFToken -> stub recibe el intento con identidad del servidor",
             conds, {"status": st, "stub": r})

        # ---- (b) cuadernillo_rating -------------------------------------------
        stub.reset(201)
        st, js, raw = nav.post(PAYLOAD_RATING, modo="cookie+xsrf")
        reqs = esperar_stub(stub, 1)
        r = reqs[0] if reqs else {}
        b = r.get("body") or {}
        caso("(b) cuadernillo_rating -> POST /api/cuadernillos/ratings",
             [("status 204", st == 204),
              ("path /api/cuadernillos/ratings", r.get("path") == "/api/cuadernillos/ratings"),
              ("Bearer", r.get("authorization") == f"Bearer {TOKEN_BACKEND}"),
              ("rating=4 intacto", b.get("rating") == 4),
              ("rated_at intacto", b.get("rated_at") == PAYLOAD_RATING["rated_at"]),
              ("identidad agregada", b.get("student_id") == "PRUEBA-P" and b.get("course_id") == "PRUEBA-C1"
               and b.get("cuadernillo_id") == "semana_prueba"),
              ("SIN tipo_evento", "tipo_evento" not in b)],
             {"status": st, "stub": r})

        # ---- (c) tipo_evento desconocido ---------------------------------------
        stub.reset(201)
        st, js, _ = nav.post({"tipo_evento": "lo_que_sea", "x": 1}, modo="cookie+xsrf")
        reqs = esperar_stub(stub, 1, seg=1)
        caso("(c) tipo_evento desconocido -> 400 tipo_desconocido, stub no recibe nada",
             [("status 400", st == 400),
              ("status tipo_desconocido", isinstance(js, dict) and js.get("status") == "tipo_desconocido"),
              ("stub sin requests", len(reqs) == 0)],
             {"status": st, "cuerpo": js, "stub_requests": len(reqs)})

        stub.reset(201)
        st, js, _ = nav.post({"exercise_id": "ejercicio_1"}, modo="cookie+xsrf")
        reqs = esperar_stub(stub, 1, seg=1)
        caso("(c2) sin tipo_evento -> 400 tipo_desconocido",
             [("status 400", st == 400), ("stub sin requests", len(reqs) == 0)],
             {"status": st, "cuerpo": js})

        # ---- (d) JSON invalido --------------------------------------------------
        stub.reset(201)
        st, js, _ = nav.post(None, modo="cookie+xsrf", raw=b"{esto no es json")
        reqs = esperar_stub(stub, 1, seg=1)
        caso("(d) JSON invalido -> 400 'json invalido'",
             [("status 400", st == 400),
              ("error json invalido", isinstance(js, dict) and js.get("error") == "json invalido"),
              ("stub sin requests", len(reqs) == 0)],
             {"status": st, "cuerpo": js})

        stub.reset(201)
        st, js, _ = nav.post(None, modo="cookie+xsrf", raw=b"[1,2,3]")
        reqs = esperar_stub(stub, 1, seg=1)
        caso("(d2) JSON valido pero no objeto ([1,2,3]) -> deberia ser 400, no 500",
             [("status 400", st == 400), ("stub sin requests", len(reqs) == 0)],
             {"status": st, "cuerpo": js,
              "log_server": [l for l in servidor.log_cola(1500).splitlines() if "Error" in l or "metrics_bridge" in l]})

        # ---- (e) backend 401 ----------------------------------------------------
        stub.reset(401)
        st, js, _ = nav.post(PAYLOAD_ATTEMPT, modo="cookie+xsrf")
        reqs = esperar_stub(stub, 1)
        caso("(e) stub responde 401 -> puente 502 {status: rechazado, codigo: 401}",
             [("status 502", st == 502),
              ("cuerpo rechazado/401", js == {"status": "rechazado", "codigo": 401}),
              ("stub recibio el intento", len(reqs) == 1)],
             {"status": st, "cuerpo": js})

        stub.reset(500)
        st, js, _ = nav.post(PAYLOAD_ATTEMPT, modo="cookie+xsrf")
        reqs = esperar_stub(stub, 1)
        caso("(e2) stub responde 500 -> puente 502 {status: rechazado, codigo: 500}",
             [("status 502", st == 502),
              ("cuerpo rechazado/500", js == {"status": "rechazado", "codigo": 500})],
             {"status": st, "cuerpo": js})

        # ---- (f) backend no responde --------------------------------------------
        stub.reset("timeout")
        t0 = time.time()
        st, js, _ = nav.post(PAYLOAD_ATTEMPT, modo="cookie+xsrf")
        dt = time.time() - t0
        caso("(f1) stub acepta la conexion pero no responde (timeout) -> 502 error_red en ~5 s",
             [("status 502", st == 502),
              ("status error_red", isinstance(js, dict) and js.get("status") == "error_red"),
              ("tardo entre 4 y 9 s (request_timeout=5)", 4 <= dt <= 9)],
             {"status": st, "cuerpo": js, "segundos": round(dt, 2)})

        stub.stop()          # puerto cerrado
        time.sleep(0.3)
        st, js, _ = nav.post(PAYLOAD_ATTEMPT, modo="cookie+xsrf")
        caso("(f2) puerto del backend cerrado (connection refused) -> 502 error_red",
             [("status 502", st == 502),
              ("status error_red", isinstance(js, dict) and js.get("status") == "error_red")],
             {"status": st, "cuerpo": js})
        stub = Stub()
        stub.start()

        # ---- (i) beacon: _xsrf en la query, sin cabecera -------------------------
        stub.reset(201)
        beacon = {"tipo_evento": "exercise_attempt", "exercise_id": "ejercicio_5",
                  "attempt_at": "2026-08-22T21:30:00.000Z", "validation_result": "sin_validar",
                  "errors": PAYLOAD_ATTEMPT["errors"][:1]}
        st, js, raw = nav.post(beacon, modo="cookie_beacon")
        reqs = esperar_stub(stub, 1)
        r = reqs[0] if reqs else {}
        b = r.get("body") or {}
        caso("(i) sendBeacon: POST ?_xsrf=<cookie> sin X-XSRFToken -> aceptado (204) y reenviado",
             [("status 204", st == 204),
              ("stub recibio 1 request en /api/exercises/attempts", len(reqs) == 1 and r.get("path") == "/api/exercises/attempts"),
              ("validation_result sin_validar intacto", b.get("validation_result") == "sin_validar"),
              ("identidad del servidor", b.get("student_id") == "PRUEBA-P")],
             {"status": st, "stub": r})

        stub.reset(201)
        st, js, _ = nav.post(beacon, modo="cookie_sin_xsrf", query="?_xsrf=2|aa|bb|0")
        reqs = esperar_stub(stub, 1, seg=1)
        caso("(i2) beacon con _xsrf falso en la query -> 403",
             [("status 403", st == 403), ("stub sin requests", len(reqs) == 0)],
             {"status": st, "cuerpo": js})

    finally:
        servidor.stop()

    # ---- (g) STUDENT_METRICS_TOKEN vacio (server reiniciado con otro env) ------
    servidor_g = ServidorAlumno({"STUDENT_METRICS_TOKEN": ""}, "sin-token")
    try:
        servidor_g.start()
        nav = Navegador()
        nav.iniciar_sesion()
        stub.reset(201)
        st, js, _ = nav.post(PAYLOAD_ATTEMPT, modo="cookie+xsrf")
        reqs = esperar_stub(stub, 1, seg=1)
        caso("(g) STUDENT_METRICS_TOKEN vacio -> 503 sin_configurar, stub no recibe nada",
             [("status 503", st == 503),
              ("status sin_configurar", js == {"status": "sin_configurar", "enviado": False}),
              ("stub sin requests", len(reqs) == 0)],
             {"status": st, "cuerpo": js, "stub_requests": len(reqs)})
    finally:
        servidor_g.stop()

    # ---- (h) ENVIAR_AL_BACKEND=false ---------------------------------------------
    servidor_h = ServidorAlumno({"ENVIAR_AL_BACKEND": "false"}, "simulado")
    try:
        servidor_h.start()
        nav = Navegador()
        nav.iniciar_sesion()
        stub.reset(201)
        st, js, _ = nav.post(PAYLOAD_ATTEMPT, modo="cookie+xsrf")
        reqs = esperar_stub(stub, 1, seg=1)
        caso("(h) ENVIAR_AL_BACKEND=false -> 200 {status: simulado}, stub no recibe nada",
             [("status 200", st == 200),
              ("cuerpo simulado", js == {"status": "simulado", "enviado": False}),
              ("stub sin requests", len(reqs) == 0)],
             {"status": st, "cuerpo": js, "stub_requests": len(reqs)})

        stub.reset(201)
        st, js, _ = nav.post({"tipo_evento": "desconocido"}, modo="cookie+xsrf")
        caso("(h2) ENVIAR_AL_BACKEND=false con tipo desconocido -> 200 simulado (la simulacion va antes del ruteo)",
             [("status 200", st == 200), ("simulado", isinstance(js, dict) and js.get("status") == "simulado")],
             {"status": st, "cuerpo": js})
    finally:
        servidor_h.stop()
        stub.stop()

    print("\n=== RESUMEN ===")
    ok = sum(1 for _, b in RESULTADOS if b)
    for n, b in RESULTADOS:
        print(f"  {'OK   ' if b else 'FALLO'} {n}")
    print(f"{ok}/{len(RESULTADOS)} casos OK")
    return 0 if ok == len(RESULTADOS) else 1


if __name__ == "__main__":
    sys.exit(main())
