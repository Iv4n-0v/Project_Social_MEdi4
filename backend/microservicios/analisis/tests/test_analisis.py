def _body(**over):
    body = {"sector": "Moda", "reach": 1500, "time_in_social_media": 2.5, "user_id": 1}
    body.update(over)
    return body


def _create(client, **over):
    return client.post("/analysis/", json=_body(**over))


# ---------- salud ----------
def test_health_y_root(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").json()["servicio"] == "analisis"


# ---------- crear / leer ----------
def test_crear_devuelve_201_con_fecha_y_audita(client):
    r = _create(client, sector="  Moda  ")
    assert r.status_code == 201
    body = r.json()
    assert body["sector"] == "Moda"  # sin espacios sobrantes
    assert body["reach"] == 1500
    assert body["time_in_social_media"] == 2.5
    assert body["user_id"] == 1
    assert body["is_active"] is True
    assert body["date"]  # la asigna el servidor

    audits = client.get(f"/analysis/{body['id']}/audits").json()
    assert [a["action"] for a in audits] == ["CREATE"]


def test_obtener_por_id(client):
    aid = _create(client).json()["id"]
    r = client.get(f"/analysis/{aid}")
    assert r.status_code == 200
    assert r.json()["id"] == aid


def test_obtener_inexistente_es_404(client):
    r = client.get("/analysis/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Analysis not found"


def test_crear_con_datos_invalidos_es_422(client):
    assert _create(client, sector="   ").status_code == 422
    assert _create(client, sector="a" * 101).status_code == 422
    assert _create(client, reach=-1).status_code == 422
    assert _create(client, time_in_social_media=-0.1).status_code == 422
    assert _create(client, user_id=0).status_code == 422
    assert _create(client, user_id=-3).status_code == 422


def test_crear_sin_campos_es_422(client):
    assert client.post("/analysis/", json={}).status_code == 422
    assert client.post("/analysis/", json={"sector": "X"}).status_code == 422


def test_reach_y_tiempo_cero_son_validos(client):
    assert _create(client, reach=0, time_in_social_media=0).status_code == 201


# ---------- listar / filtrar ----------
def test_filtrar_por_usuario(client):
    _create(client, user_id=1)
    _create(client, user_id=2)
    _create(client, user_id=1)
    r = client.get("/analysis/", params={"user_id": 1}).json()
    assert len(r) == 2
    assert {a["user_id"] for a in r} == {1}


def test_sin_filtro_devuelve_todos(client):
    a = _create(client).json()["id"]
    _create(client)
    client.delete(f"/analysis/{a}")
    assert len(client.get("/analysis/").json()) == 2


# ---------- actualizar ----------
def test_actualizar_parcial_no_toca_lo_demas(client):
    aid = _create(client).json()["id"]
    r = client.put(f"/analysis/{aid}", json={"reach": 99})
    assert r.status_code == 200
    body = r.json()
    assert body["reach"] == 99
    assert body["sector"] == "Moda"
    assert body["time_in_social_media"] == 2.5
    assert body["user_id"] == 1


def test_actualizar_no_cambia_el_usuario(client):
    aid = _create(client, user_id=1).json()["id"]
    r = client.put(f"/analysis/{aid}", json={"user_id": 7})
    assert r.json()["user_id"] == 1  # campo ignorado


def test_actualizar_con_datos_invalidos_es_422(client):
    aid = _create(client).json()["id"]
    assert client.put(f"/analysis/{aid}", json={"sector": "  "}).status_code == 422
    assert client.put(f"/analysis/{aid}", json={"reach": -5}).status_code == 422


def test_actualizar_inexistente_es_404(client):
    assert client.put("/analysis/999", json={"reach": 1}).status_code == 404


# ---------- borrado logico + restauracion + auditoria ----------
def test_borrado_logico_no_destruye_el_registro(client):
    aid = _create(client).json()["id"]

    r = client.delete(f"/analysis/{aid}")
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    assert client.get(f"/analysis/{aid}").json()["sector"] == "Moda"
    eliminados = client.get("/analysis/", params={"is_active": False}).json()
    assert [a["id"] for a in eliminados] == [aid]
    assert client.get("/analysis/", params={"is_active": True}).json() == []


def test_restaurar(client):
    aid = _create(client).json()["id"]
    client.delete(f"/analysis/{aid}")

    r = client.post(f"/analysis/{aid}/restore")
    assert r.json()["is_active"] is True
    activos = client.get("/analysis/", params={"is_active": True}).json()
    assert [a["id"] for a in activos] == [aid]


def test_auditoria_registra_todo_el_ciclo(client):
    aid = _create(client).json()["id"]
    client.put(f"/analysis/{aid}", json={"reach": 10})
    client.delete(f"/analysis/{aid}")
    client.post(f"/analysis/{aid}/restore")

    actions = [a["action"] for a in client.get(f"/analysis/{aid}/audits").json()]
    assert actions == ["CREATE", "UPDATE", "DELETE", "RESTORE"]


def test_auditoria_de_inexistente_es_404(client):
    assert client.get("/analysis/999/audits").status_code == 404


def test_eliminar_o_restaurar_inexistente_es_404(client):
    assert client.delete("/analysis/999").status_code == 404
    assert client.post("/analysis/999/restore").status_code == 404
