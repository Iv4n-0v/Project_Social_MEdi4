"""Pruebas HTTP con SQLite temporal. Requieren dependencias reales:
    pip install -r requirements-dev.txt && python -m pytest tests -q
"""
import os
import tempfile
import unittest

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.sqlite3"

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

A = {"X-User-Id": "101"}
B = {"X-User-Id": "202"}


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._ctx = TestClient(app)
        cls.c = cls._ctx.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._ctx.__exit__(None, None, None)

    def test_01_categories_seeded_and_public(self):
        r = self.c.get("/categories")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.json()), 10)

    def test_02_owner_routes_need_identity(self):
        self.assertEqual(self.c.get("/me/venture").status_code, 401)
        self.assertEqual(self.c.get("/me/favorites").status_code, 401)
        self.assertEqual(self.c.get("/me/venture", headers={"X-User-Id": "abc"}).status_code, 401)

    def test_03_no_venture_yet(self):
        self.assertEqual(self.c.get("/me/venture", headers=A).status_code, 404)

    def test_04_full_flow(self):
        r = self.c.put("/me/venture", json={"name": "Luna Dulce", "description": "Postres", "category_id": 2}, headers=A)
        self.assertEqual(r.status_code, 201)
        vid = r.json()["id"]
        self.assertFalse(r.json()["is_published"])
        # borrador: invisible
        self.assertEqual(self.c.get(f"/ventures/{vid}").status_code, 404)
        self.assertEqual(self.c.put("/me/venture", json={"name": "Luna Dulce 2", "description": "Postres"}, headers=A).status_code, 200)
        # red valida / invalida
        ok = self.c.put("/me/venture/social/instagram", json={"url": "https://instagram.com/luna", "followers": 50}, headers=A)
        self.assertEqual(ok.status_code, 200)
        bad = self.c.put("/me/venture/social/instagram", json={"url": "https://evil.com/x"}, headers=A)
        self.assertEqual(bad.status_code, 422)
        # publicar
        self.assertEqual(self.c.post("/me/venture/publish", headers=A).status_code, 200)
        pub = self.c.get(f"/ventures/{vid}")
        self.assertEqual(pub.status_code, 200)
        self.assertNotIn("owner_account_id", pub.json())
        self.assertEqual(pub.json()["social"][0]["followers"], 50)
        self.assertEqual(self.c.get("/ventures", params={"q": "luna"}).json()["total"], 1)
        # favoritos de otra cuenta
        self.assertEqual(self.c.put(f"/me/favorites/{vid}", headers=B).status_code, 204)
        self.assertEqual(self.c.get("/me/favorite-ids", headers=B).json(), {"ids": [vid]})
        self.assertEqual(self.c.get("/me/favorite-ids", headers=A).json(), {"ids": []})
        # borrar / restaurar
        self.assertEqual(self.c.delete("/me/venture", headers=A).status_code, 200)
        self.assertEqual(self.c.get(f"/ventures/{vid}").status_code, 404)
        self.assertEqual(self.c.put("/me/venture", json={"name": "x"}, headers=A).status_code, 409)
        self.assertEqual(self.c.post("/me/venture/restore", headers=A).status_code, 200)
        self.assertEqual(self.c.get(f"/ventures/{vid}").status_code, 404)  # vuelve como borrador
        acts = [a["action"] for a in self.c.get("/me/venture/audits", headers=A).json()]
        self.assertIn("PUBLISH", acts)
        self.assertIn("RESTORE", acts)

    def test_05_validation(self):
        self.assertEqual(self.c.put("/me/venture", json={"name": "   "}, headers=B).status_code, 422)
        self.assertEqual(self.c.put("/me/venture", json={"name": "ok", "category_id": 9999}, headers=B).status_code, 422)
