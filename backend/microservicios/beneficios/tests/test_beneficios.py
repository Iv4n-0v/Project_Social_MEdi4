def _create(client, name="Ingresos pasivos", description=None):
    body = {"name": name}
    if description is not None:
        body["description"] = description
    return client.post("/benefits/", json=body)


# ---------- salud ----------
def test_health_y_root(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").json()["servicio"] == "beneficios"


# ---------- crear / leer ----------
def test_crear_beneficio_devuelve_201_y_audita(client):
    r = _create(client, "  Ingresos  ", "Dinero extra")
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Ingresos"  # sin espacios sobrantes
    assert body["description"] == "Dinero extra"
    assert body["is_active"] is True

    audits = client.get(f"/benefits/{body['id']}/audits").json()
    assert [a["action"] for a in audits] == ["CREATE"]


def test_descripcion_es_opcional(client):
    r = _create(client, "Solo nombre")
    assert r.status_code == 201
    assert r.json()["description"] is None


def test_crear_con_nombre_en_blanco_es_422(client):
    assert _create(client, "   ").status_code == 422


def test_crear_sin_nombre_es_422(client):
    assert client.post("/benefits/", json={}).status_code == 422


def test_crear_con_nombre_muy_largo_es_422(client):
    assert _create(client, "a" * 101).status_code == 422


def test_crear_con_descripcion_muy_larga_es_422(client):
    assert _create(client, "X", "d" * 501).status_code == 422


def test_obtener_inexistente_es_404(client):
    r = client.get("/benefits/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Benefit not found"


# ---------- actualizar ----------
def test_actualizar_parcial_no_toca_lo_demas(client):
    bid = _create(client, "A", "desc").json()["id"]
    r = client.put(f"/benefits/{bid}", json={"name": "B"})
    assert r.status_code == 200
    assert r.json()["name"] == "B"
    assert r.json()["description"] == "desc"


def test_actualizar_descripcion(client):
    bid = _create(client, "A", "vieja").json()["id"]
    r = client.put(f"/benefits/{bid}", json={"description": "nueva"})
    assert r.json()["description"] == "nueva"
    assert r.json()["name"] == "A"


def test_actualizar_con_nombre_en_blanco_es_422(client):
    bid = _create(client, "A").json()["id"]
    assert client.put(f"/benefits/{bid}", json={"name": "  "}).status_code == 422


def test_actualizar_inexistente_es_404(client):
    assert client.put("/benefits/999", json={"name": "x"}).status_code == 404


# ---------- borrado logico + restauracion + auditoria ----------
def test_borrado_logico_no_destruye_el_registro(client):
    bid = _create(client).json()["id"]

    r = client.delete(f"/benefits/{bid}")
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    # sigue existiendo y aparece en la lista de eliminados
    assert client.get(f"/benefits/{bid}").status_code == 200
    eliminados = client.get("/benefits/", params={"is_active": False}).json()
    assert [b["id"] for b in eliminados] == [bid]
    assert client.get("/benefits/", params={"is_active": True}).json() == []


def test_restaurar_beneficio(client):
    bid = _create(client).json()["id"]
    client.delete(f"/benefits/{bid}")

    r = client.post(f"/benefits/{bid}/restore")
    assert r.json()["is_active"] is True
    activos = client.get("/benefits/", params={"is_active": True}).json()
    assert [b["id"] for b in activos] == [bid]


def test_auditoria_registra_todo_el_ciclo(client):
    bid = _create(client).json()["id"]
    client.put(f"/benefits/{bid}", json={"name": "Nuevo"})
    client.delete(f"/benefits/{bid}")
    client.post(f"/benefits/{bid}/restore")

    actions = [a["action"] for a in client.get(f"/benefits/{bid}/audits").json()]
    assert actions == ["CREATE", "UPDATE", "DELETE", "RESTORE"]


def test_auditoria_de_inexistente_es_404(client):
    assert client.get("/benefits/999/audits").status_code == 404


def test_eliminar_o_restaurar_inexistente_es_404(client):
    assert client.delete("/benefits/999").status_code == 404
    assert client.post("/benefits/999/restore").status_code == 404


def test_sin_filtro_devuelve_todos(client):
    a = _create(client, "A").json()["id"]
    _create(client, "B")
    client.delete(f"/benefits/{a}")
    assert len(client.get("/benefits/").json()) == 2


# ---------- filtro por ids (para componer metodologia + beneficios) ----------
def test_filtrar_por_ids(client):
    ids = [_create(client, n).json()["id"] for n in ("A", "B", "C")]
    r = client.get("/benefits/", params={"ids": f"{ids[0]},{ids[2]}"})
    assert [b["id"] for b in r.json()] == [ids[0], ids[2]]


def test_filtrar_por_ids_ignora_los_que_no_existen(client):
    bid = _create(client, "A").json()["id"]
    r = client.get("/benefits/", params={"ids": f"{bid},999"})
    assert [b["id"] for b in r.json()] == [bid]


def test_ids_con_formato_invalido_es_422(client):
    assert client.get("/benefits/", params={"ids": "1,abc"}).status_code == 422


def test_ids_vacio_devuelve_lista_vacia(client):
    _create(client, "A")
    assert client.get("/benefits/", params={"ids": ""}).json() == []
