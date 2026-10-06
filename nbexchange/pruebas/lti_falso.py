#!/usr/bin/env python3
"""Cliente LTI 1.1 falso para el Hub local.

Sirve en http://localhost:9999/ un formulario firmado (OAuth1 HMAC-SHA1) que se
auto-envia a http://localhost:8000/hub/lti/launch. Se firma en cada GET porque
ltiauthenticator rechaza timestamps con mas de 30 s (lti11/validator.py:102) y
nonces repetidos (validator.py:108-113).

  python3 lti_fake.py                 # luego abrir http://localhost:9999/
  http://localhost:9999/?rol=Instructor&user=9002&email=docente@ejemplo.test
  http://localhost:9999/?rol=Learner&user=9001&email=alumno@ejemplo.test

Variables: LTI_CLIENT_KEY / LTI_CLIENT_SECRET (mismos valores que lee el Hub:
jupyterhub_config.py:122-129; sin ellos usa los de desarrollo), HUB_LAUNCH_URL.
"""
import base64, hashlib, hmac, html, os, time, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

URL = os.environ.get("HUB_LAUNCH_URL", "http://localhost:8000/hub/lti/launch")
KEY = os.environ.get("LTI_CLIENT_KEY", "moodle-llave-publica")
SEC = os.environ.get("LTI_CLIENT_SECRET", "secreto-super-seguro-000000")

q = lambda s: urllib.parse.quote(str(s), safe="-._~")

def firmar(p):
    norm = "&".join(f"{q(k)}={q(v)}" for k, v in sorted(p.items()))
    base = "&".join(["POST", q(URL), q(norm)])
    return base64.b64encode(
        hmac.new((q(SEC) + "&").encode(), base.encode(), hashlib.sha1).digest()).decode()

def formulario(qs):
    g = lambda k, d: qs.get(k, [d])[0]
    p = {
        # obligatorios (lti11/constants.py:5-10 + 62-70)
        "lti_message_type": "basic-lti-launch-request",
        "lti_version": "LTI-1p0",
        "resource_link_id": g("rl", "actividad_local_1"),
        "user_id": g("user", "9001"),
        "oauth_consumer_key": KEY,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_nonce": "n%d" % time.time_ns(),
        "oauth_version": "1.0",
        "oauth_callback": "about:blank",
        # los que lee el AVA (jupyterhub_config.py:66-67, 130, 170-175, 185-186)
        "roles": g("rol", "Learner"),
        "context_id": g("curso", "28053"),
        "context_title": g("curso_nombre", "Curso local de prueba"),
        "lis_person_name_full": g("nombre", "Alumno Local"),
        "lis_person_contact_email_primary": g("email", "alumno.local@ejemplo.test"),
        # opcionales: devolucion de notas (solo para ver el log del Hub)
        "lis_result_sourcedid": g("sourcedid", ""),
        "lis_outcome_service_url": g("outcome", ""),
    }
    p = {k: v for k, v in p.items() if v != ""}
    p["oauth_signature"] = firmar(p)
    campos = "".join('<input type="hidden" name="%s" value="%s">' % (html.escape(k), html.escape(v))
                     for k, v in p.items())
    return ('<!doctype html><meta charset="utf-8"><title>LTI falso</title>'
            '<body onload="document.forms[0].submit()">'
            '<p>Lanzando como %s (%s)...</p>'
            '<form method="POST" action="%s">%s</form></body>'
            % (html.escape(p["lis_person_contact_email_primary"]), html.escape(p["roles"]), URL, campos))

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        cuerpo = formulario(qs).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

if __name__ == "__main__":
    print("LTI falso en http://localhost:9999/  ->", URL, "(key:", KEY + ")")
    HTTPServer(("127.0.0.1", 9999), H).serve_forever()
