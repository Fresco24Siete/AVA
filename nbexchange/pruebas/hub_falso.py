"""Un JupyterHub de mentira, con lo justo para probar el servicio nbexchange.

Responde a lo único que nbexchange le pide al Hub de verdad:

  GET /hub/api/user              con el token de un contenedor -> quién es y sus grupos
  GET /hub/api/users/<nombre>    con el token del servicio     -> el auth_state (LTI)

Los usuarios y tokens salen de la variable HUB_FALSO_USUARIOS (JSON). Sirve para
correr la prueba de integración sin LTI ni Docker-in-Docker; el Hub real se
prueba aparte, con el stack completo.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote

USUARIOS = json.loads(os.environ.get("HUB_FALSO_USUARIOS", "{}"))
TOKEN_SERVICIO = os.environ.get("HUB_FALSO_TOKEN_SERVICIO", "")
POR_NOMBRE = {u["name"]: u for u in USUARIOS.values()}


class Hub(BaseHTTPRequestHandler):
    def _json(self, codigo, cuerpo):
        datos = json.dumps(cuerpo).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _token(self):
        cab = self.headers.get("Authorization", "")
        partes = cab.split(None, 1)
        return partes[1] if len(partes) == 2 and partes[0].lower() in ("token", "bearer") else ""

    def do_GET(self):
        ruta = self.path.split("?", 1)[0]
        token = self._token()
        if ruta == "/hub/api/user":
            u = USUARIOS.get(token)
            if not u:
                return self._json(403, {"message": "token desconocido"})
            return self._json(200, {"kind": "user", "name": u["name"],
                                    "groups": u.get("groups", []), "admin": False})
        if ruta.startswith("/hub/api/users/"):
            if token != TOKEN_SERVICIO:
                return self._json(403, {"message": "no es el token del servicio"})
            nombre = unquote(ruta[len("/hub/api/users/"):])
            u = POR_NOMBRE.get(nombre)
            if not u:
                return self._json(404, {"message": "no existe"})
            modelo = {"kind": "user", "name": nombre, "groups": u.get("groups", [])}
            if os.environ.get("HUB_FALSO_SIN_AUTH_STATE") != "1":
                modelo["auth_state"] = u.get("auth_state", {})
            return self._json(200, modelo)
        return self._json(404, {"message": "ruta desconocida"})

    def log_message(self, fmt, *args):
        print("[hub_falso]", fmt % args, flush=True)


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8081), Hub).serve_forever()
