def test_crear_y_listar_servicio(client, auth_headers):
    resp = client.post("/servicios", json={"nombre": "Picking"}, headers=auth_headers)
    assert resp.status_code == 201, resp.text

    resp = client.get("/servicios", headers=auth_headers)
    assert resp.status_code == 200
    assert any(s["nombre"] == "Picking" for s in resp.json())


def test_crear_cuadrilla_nace_disponible(client, auth_headers):
    resp = client.post("/cuadrillas", json={"nombre": "Cuadrilla B"}, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    assert resp.json()["estado"] == "disponible"


def test_listar_cuadrillas_filtra_por_estado(client, auth_headers):
    client.post("/cuadrillas", json={"nombre": "Cuadrilla C"}, headers=auth_headers)
    resp = client.get("/cuadrillas", params={"estado": "disponible"}, headers=auth_headers)
    assert resp.status_code == 200
    assert any(c["nombre"] == "Cuadrilla C" for c in resp.json())


def test_crear_y_listar_tipo_vehiculo(client, auth_headers):
    resp = client.post("/tipos-vehiculo", json={"nombre": "Turbo largo", "tarifa_base": 148540}, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    assert resp.json()["tarifa_base"] == 148540

    resp = client.get("/tipos-vehiculo", headers=auth_headers)
    assert resp.status_code == 200
    assert any(t["nombre"] == "Turbo largo" for t in resp.json())