"""Pruebas de la capa HTTP (rutas, cookies, codigos de error) con base SQLite temporal.

Necesitan las dependencias reales:  pip install -r requirements-dev.txt
Ejecutar desde la carpeta del servicio:  python -m pytest tests -q
"""
import os
import tempfile
import unittest
import uuid
from http.cookies import SimpleCookie

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.sqlite3"
os.environ["JWT_KEY_FILE"] = f"{_TMP}/jwt.pem"
os.environ["MAIL_MODE"] = "log"
for _k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "FACEBOOK_APP_ID", "FACEBOOK_APP_SECRET"):
    os.environ.pop(_k, None)

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

PWD = "Clave12345"


def _cookie(resp, name="refresh_token"):
    """Lee la cookie del encabezado (el cliente de pruebas no la reenvia solo
    porque su ruta publica es /api/v1/auth y aqui se llama a /auth)."""
    for raw in resp.headers.get_list("set-cookie"):
        c = SimpleCookie()
        c.load(raw)
        if name in c:
            return c[name], raw
    return None, None


def _email():
    return f"{uuid.uuid4().hex[:10]}@mail.test"


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._ctx = TestClient(app)
        cls.client = cls._ctx.__enter__()  # ejecuta el arranque (crea tablas y llave)

    @classmethod
    def tearDownClass(cls):
        cls._ctx.__exit__(None, None, None)

    def register(self, role="visitor", email=None):
        email = email or _email()
        r = self.client.post(
            "/auth/register", json={"email": email, "password": PWD, "name": "Ana", "role": role}
        )
        return email, r

    def bearer(self, r):
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def test_health_and_jwks(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        key = self.client.get("/.well-known/jwks.json").json()["keys"][0]
        self.assertEqual((key["kty"], key["alg"]), ("RSA", "RS256"))
        self.assertNotIn("d", key)

    def test_register_sets_httponly_cookie_and_hides_refresh_from_body(self):
        _, r = self.register("entrepreneur")
        self.assertEqual(r.status_code, 201)
        self.assertNotIn("refresh_token", r.json())
        morsel, raw = _cookie(r)
        self.assertIsNotNone(morsel)
        self.assertIn("httponly", raw.lower())
        self.assertIn("samesite=lax", raw.lower())
        self.assertIn("path=/api/v1/auth", raw.lower())
        self.assertEqual(r.json()["account"]["roles"], ["entrepreneur"])
        self.assertEqual(r.headers["cache-control"], "no-store")

    def test_register_errors(self):
        email, _ = self.register()
        self.assertEqual(self.register(email=email)[1].status_code, 409)
        bad = self.client.post("/auth/register", json={"email": "x", "password": PWD, "name": "A"})
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(self.client.post("/auth/register", json={}).status_code, 422)

    def test_me_requires_a_valid_token(self):
        _, r = self.register()
        ok = self.client.get("/auth/me", headers=self.bearer(r))
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.json()["has_password"])
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        self.assertEqual(self.client.get("/auth/me", headers={"Authorization": "Bearer basura"}).status_code, 401)
        self.assertEqual(self.client.get("/auth/me", headers={"Authorization": "Basic abc"}).status_code, 401)

    def test_login_ok_and_wrong_password(self):
        email, _ = self.register()
        self.assertEqual(self.client.post("/auth/login", json={"email": email, "password": PWD}).status_code, 200)
        bad = self.client.post("/auth/login", json={"email": email, "password": "incorrecta1"})
        self.assertEqual(bad.status_code, 401)
        self.assertEqual(bad.json()["detail"], "Correo o contrasena incorrectos")

    def test_enable_second_role(self):
        _, r = self.register("visitor")
        up = self.client.post("/auth/roles", json={"role": "entrepreneur"}, headers=self.bearer(r))
        self.assertEqual(up.status_code, 200)
        self.assertEqual(sorted(up.json()["account"]["roles"]), ["entrepreneur", "visitor"])
        self.assertEqual(
            self.client.post("/auth/roles", json={"role": "admin"}, headers=self.bearer(r)).status_code, 422
        )
        self.assertEqual(self.client.post("/auth/roles", json={"role": "visitor"}).status_code, 401)

    def test_refresh_rotates_and_reuse_is_rejected(self):
        _, r = self.register()
        first, _ = _cookie(r)
        header = {"Cookie": f"refresh_token={first.value}"}
        again = self.client.post("/auth/refresh", headers=header)
        self.assertEqual(again.status_code, 200)
        second, _ = _cookie(again)
        self.assertNotEqual(first.value, second.value)
        race = self.client.post("/auth/refresh", headers=header)
        self.assertEqual(race.status_code, 401)  # dentro de la ventana de gracia
        self.assertIsNone(_cookie(race)[1])  # no borra la cookie (ya es la nueva)
        bad = self.client.post("/auth/refresh", headers={"Cookie": "refresh_token=inventado"})
        self.assertEqual(bad.status_code, 401)
        _, cleared = _cookie(bad)
        self.assertIn("max-age=0", cleared.lower())  # una cookie invalida si se borra
        self.assertEqual(self.client.post("/auth/refresh").status_code, 401)

    def test_logout_clears_cookie_and_session(self):
        _, r = self.register()
        c, _ = _cookie(r)
        header = {"Cookie": f"refresh_token={c.value}"}
        out = self.client.post("/auth/logout", headers=header)
        self.assertEqual(out.status_code, 204)
        _, cleared = _cookie(out)
        self.assertIn("max-age=0", cleared.lower())
        self.assertEqual(self.client.post("/auth/refresh", headers=header).status_code, 401)
        self.assertEqual(self.client.post("/auth/logout").status_code, 204)

    def test_forgot_password_is_uniform_and_reset_rejects_bad_token(self):
        email, _ = self.register()
        a = self.client.post("/auth/password/forgot", json={"email": email})
        b = self.client.post("/auth/password/forgot", json={"email": "nadie@mail.test"})
        self.assertEqual((a.status_code, b.status_code), (202, 202))
        self.assertEqual(a.json(), b.json())
        bad = self.client.post("/auth/password/reset", json={"token": "x", "new_password": "NuevaClave99"})
        self.assertEqual(bad.status_code, 400)

    def test_oauth_not_configured(self):
        self.assertEqual(self.client.get("/auth/oauth/providers").json(), {"google": False, "facebook": False})
        self.assertEqual(self.client.get("/auth/oauth/google/login").status_code, 503)
        self.assertEqual(self.client.get("/auth/oauth/twitter/login").status_code, 404)

    def test_oauth_callback_error_returns_html_bridge_without_session(self):
        r = self.client.get("/auth/oauth/google/callback?error=access_denied")
        self.assertEqual(r.status_code, 200)
        self.assertIn("oauth_error=", r.text)
        morsel, _ = _cookie(r)
        self.assertIsNone(morsel)  # un inicio de sesion fallido no crea sesion

    def test_my_audits(self):
        _, r = self.register()
        a = self.client.get("/auth/me/audits", headers=self.bearer(r)).json()
        self.assertEqual([x["action"] for x in a], ["REGISTER"])


if __name__ == "__main__":
    unittest.main()
