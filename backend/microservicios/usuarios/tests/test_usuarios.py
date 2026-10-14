PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def _create(client, name="Ana", **extra):
    data = {"name": name, **extra}
    return client.post("/users/", data=data)


# ---------- salud ----------
def test_health_y_root(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").json()["servicio"] == "usuarios"


# ---------- crear / leer ----------
def test_crear_usuario_devuelve_201_y_audita(client):
    r = _create(client, "Ana", methodology_ids=[3, 1, 3])
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Ana"
    assert body["is_active"] is True
    assert body["methodology_ids"] == [1, 3]  # sin duplicados, ordenado

    audits = client.get(f"/users/{body['id']}/audits").json()
    assert [a["action"] for a in audits] == ["CREATE"]


def test_crear_con_imagen_valida(client, storage):
    r = client.post(
        "/users/",
        data={"name": "Luis"},
        files={"img": ("foto.png", PNG, "image/png")},
    )
    assert r.status_code == 201
    assert r.json()["img"] == "https://fake.test/users/foto.png"
    assert storage.uploads[0][2] == "users"


def test_crear_sin_nombre_es_422(client):
    assert client.post("/users/", data={}).status_code == 422


def test_obtener_inexistente_es_404(client):
    r = client.get("/users/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


# ---------- actualizar ----------
def test_actualizar_nombre_y_metodologias(client):
    uid = _create(client, "Ana", methodology_ids=[1]).json()["id"]
    r = client.put(f"/users/{uid}", json={"name": "Ana M", "methodology_ids": [2, 5]})
    assert r.status_code == 200
    assert r.json()["name"] == "Ana M"
    assert r.json()["methodology_ids"] == [2, 5]


def test_actualizar_parcial_no_toca_lo_demas(client):
    uid = _create(client, "Ana", methodology_ids=[1, 2]).json()["id"]
    r = client.put(f"/users/{uid}", json={"name": "Nuevo"})
    assert r.json()["methodology_ids"] == [1, 2]


def test_actualizar_inexistente_es_404(client):
    assert client.put("/users/999", json={"name": "x"}).status_code == 404


# ---------- borrado logico + restauracion + auditoria ----------
def test_borrado_logico_no_destruye_el_registro(client):
    uid = _create(client, "Ana").json()["id"]

    r = client.delete(f"/users/{uid}")
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    # sigue existiendo y aparece en la lista de eliminados
    assert client.get(f"/users/{uid}").status_code == 200
    eliminados = client.get("/users/", params={"is_active": False}).json()
    assert [u["id"] for u in eliminados] == [uid]
    assert client.get("/users/", params={"is_active": True}).json() == []


def test_restaurar_usuario(client):
    uid = _create(client, "Ana").json()["id"]
    client.delete(f"/users/{uid}")

    r = client.post(f"/users/{uid}/restore")
    assert r.json()["is_active"] is True
    assert [u["id"] for u in client.get("/users/", params={"is_active": True}).json()] == [uid]


def test_auditoria_registra_todo_el_ciclo(client):
    uid = _create(client, "Ana").json()["id"]
    client.put(f"/users/{uid}", json={"name": "Ana 2"})
    client.delete(f"/users/{uid}")
    client.post(f"/users/{uid}/restore")

    actions = [a["action"] for a in client.get(f"/users/{uid}/audits").json()]
    assert actions == ["CREATE", "UPDATE", "DELETE", "RESTORE"]


def test_auditoria_de_usuario_inexistente_es_404(client):
    assert client.get("/users/999/audits").status_code == 404


def test_filtro_sin_parametro_devuelve_todos(client):
    a = _create(client, "A").json()["id"]
    _create(client, "B")
    client.delete(f"/users/{a}")
    assert len(client.get("/users/").json()) == 2


# ---------- imagen ----------
def test_actualizar_imagen(client, storage):
    uid = _create(client, "Ana").json()["id"]
    r = client.put(f"/users/{uid}/image", files={"img": ("nueva.png", PNG, "image/png")})
    assert r.status_code == 200
    assert r.json()["img"].endswith("nueva.png")
    actions = [a["action"] for a in client.get(f"/users/{uid}/audits").json()]
    assert actions[-1] == "UPDATE_IMAGE"


def test_imagen_con_formato_no_permitido_es_415(client):
    uid = _create(client, "Ana").json()["id"]
    r = client.put(f"/users/{uid}/image", files={"img": ("virus.exe", b"MZ", "application/octet-stream")})
    assert r.status_code == 415


def test_imagen_vacia_es_400(client):
    uid = _create(client, "Ana").json()["id"]
    r = client.put(f"/users/{uid}/image", files={"img": ("v.png", b"", "image/png")})
    assert r.status_code == 400


def test_imagen_demasiado_grande_es_413(client):
    uid = _create(client, "Ana").json()["id"]
    grande = b"0" * (5 * 1024 * 1024 + 1)
    r = client.put(f"/users/{uid}/image", files={"img": ("g.png", grande, "image/png")})
    assert r.status_code == 413


def test_fallo_al_subir_responde_502(client):
    from main import app
    from storage import StorageError, get_storage

    class BrokenStorage:
        async def upload(self, content, filename, content_type, folder):
            raise StorageError("No se pudo subir la imagen al almacenamiento")

    app.dependency_overrides[get_storage] = lambda: BrokenStorage()
    r = client.post(
        "/users/", data={"name": "X"}, files={"img": ("a.png", PNG, "image/png")}
    )
    assert r.status_code == 502


# ---------- validacion del nombre ----------
def test_actualizar_con_nombre_en_blanco_es_422(client):
    uid = _create(client, "Ana").json()["id"]
    assert client.put(f"/users/{uid}", json={"name": "   "}).status_code == 422


def test_actualizar_con_nombre_muy_largo_es_422(client):
    uid = _create(client, "Ana").json()["id"]
    assert client.put(f"/users/{uid}", json={"name": "a" * 101}).status_code == 422


def test_crear_con_nombre_en_blanco_es_422(client):
    assert _create(client, "   ").status_code == 422


def test_crear_con_nombre_muy_largo_es_422(client):
    assert _create(client, "a" * 101).status_code == 422


def test_imagen_a_usuario_inexistente_es_404(client):
    r = client.put("/users/999/image", files={"img": ("a.png", PNG, "image/png")})
    assert r.status_code == 404


# ---------- storage sin configurar ----------
def test_storage_sin_configurar_responde_503(client, monkeypatch):
    from storage import SupabaseStorage
    from main import app
    from storage import get_storage

    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    app.dependency_overrides[get_storage] = lambda: SupabaseStorage()
    r = client.post(
        "/users/", data={"name": "X"}, files={"img": ("a.png", PNG, "image/png")}
    )
    assert r.status_code == 503
