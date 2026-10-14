def _create(client, name="Marketing de contenidos", description=None, benefit_ids=None):
    body = {"name": name}
    if description is not None:
        body["description"] = description
    if benefit_ids is not None:
        body["benefit_ids"] = benefit_ids
    return client.post("/methodologies/", json=body)


# ---------- salud ----------
def test_health_y_root(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").json()["servicio"] == "metodologias"


# ---------- crear / leer ----------
def test_crear_devuelve_201_y_audita(client):
    r = _create(client, "  Afiliados  ", "Comisiones", [3, 1, 3])
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Afiliados"  # sin espacios sobrantes
    assert body["description"] == "Comisiones"
    assert body["is_active"] is True
    assert body["benefit_ids"] == [1, 3]  # sin duplicados, ordenado

    audits = client.get(f"/methodologies/{body['id']}/audits").json()
    assert [a["action"] for a in audits] == ["CREATE"]


def test_descripcion_y_beneficios_son_opcionales(client):
    r = _create(client, "Solo nombre")
    assert r.status_code == 201
    assert r.json()["description"] is None
    assert r.json()["benefit_ids"] == []


def test_crear_con_nombre_en_blanco_es_422(client):
    assert _create(client, "   ").status_code == 422


def test_crear_sin_nombre_es_422(client):
    assert client.post("/methodologies/", json={}).status_code == 422


def test_crear_con_nombre_muy_largo_es_422(client):
    assert _create(client, "a" * 101).status_code == 422


def test_crear_con_descripcion_muy_larga_es_422(client):
    assert _create(client, "X", "d" * 501).status_code == 422


def test_beneficios_con_ids_invalidos_es_422(client):
    assert _create(client, "X", benefit_ids=[0]).status_code == 422
    assert _create(client, "X", benefit_ids=[-2]).status_code == 422
    assert (
        client.post(
            "/methodologies/", json={"name": "X", "benefit_ids": ["abc"]}
        ).status_code
        == 422
    )


def test_obtener_inexistente_es_404(client):
    r = client.get("/methodologies/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Methodology not found"


# ---------- actualizar ----------
def test_actualizar_parcial_no_toca_lo_demas(client):
    mid = _create(client, "A", "desc", [1, 2]).json()["id"]
    r = client.put(f"/methodologies/{mid}", json={"name": "B"})
    assert r.status_code == 200
    assert r.json()["name"] == "B"
    assert r.json()["description"] == "desc"
    assert r.json()["benefit_ids"] == [1, 2]


def test_actualizar_reemplaza_los_beneficios(client):
    mid = _create(client, "A", benefit_ids=[1, 2]).json()["id"]
    r = client.put(f"/methodologies/{mid}", json={"benefit_ids": [5, 4]})
    assert r.json()["benefit_ids"] == [4, 5]


def test_actualizar_con_lista_vacia_quita_todos_los_beneficios(client):
    mid = _create(client, "A", benefit_ids=[1, 2]).json()["id"]
    r = client.put(f"/methodologies/{mid}", json={"benefit_ids": []})
    assert r.json()["benefit_ids"] == []


def test_actualizar_con_nombre_en_blanco_es_422(client):
    mid = _create(client, "A").json()["id"]
    assert client.put(f"/methodologies/{mid}", json={"name": "  "}).status_code == 422


def test_actualizar_inexistente_es_404(client):
    assert client.put("/methodologies/999", json={"name": "x"}).status_code == 404


# ---------- borrado logico + restauracion + auditoria ----------
def test_borrado_logico_no_destruye_el_registro_ni_sus_beneficios(client):
    mid = _create(client, benefit_ids=[1, 2]).json()["id"]

    r = client.delete(f"/methodologies/{mid}")
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    # sigue existiendo, con sus beneficios, y aparece en la lista de eliminadas
    assert client.get(f"/methodologies/{mid}").json()["benefit_ids"] == [1, 2]
    eliminadas = client.get("/methodologies/", params={"is_active": False}).json()
    assert [m["id"] for m in eliminadas] == [mid]
    assert client.get("/methodologies/", params={"is_active": True}).json() == []


def test_restaurar(client):
    mid = _create(client).json()["id"]
    client.delete(f"/methodologies/{mid}")

    r = client.post(f"/methodologies/{mid}/restore")
    assert r.json()["is_active"] is True
    activas = client.get("/methodologies/", params={"is_active": True}).json()
    assert [m["id"] for m in activas] == [mid]


def test_auditoria_registra_todo_el_ciclo(client):
    mid = _create(client).json()["id"]
    client.put(f"/methodologies/{mid}", json={"name": "Nueva"})
    client.delete(f"/methodologies/{mid}")
    client.post(f"/methodologies/{mid}/restore")

    actions = [a["action"] for a in client.get(f"/methodologies/{mid}/audits").json()]
    assert actions == ["CREATE", "UPDATE", "DELETE", "RESTORE"]


def test_auditoria_de_inexistente_es_404(client):
    assert client.get("/methodologies/999/audits").status_code == 404


def test_eliminar_o_restaurar_inexistente_es_404(client):
    assert client.delete("/methodologies/999").status_code == 404
    assert client.post("/methodologies/999/restore").status_code == 404


def test_sin_filtro_devuelve_todas(client):
    a = _create(client, "A").json()["id"]
    _create(client, "B")
    client.delete(f"/methodologies/{a}")
    assert len(client.get("/methodologies/").json()) == 2
