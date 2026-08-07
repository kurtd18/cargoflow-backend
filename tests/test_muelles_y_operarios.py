def test_disponibilidad_muelles_todos_libres_al_inicio(client, auth_headers):
    resp = client.get("/muelles/disponibilidad", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    muelles = resp.json()
    assert len(muelles) == 20
    assert all(m["disponible"] for m in muelles)


def test_muelle_ocupado_cuando_hay_operacion_activa(client, auth_headers, empresa_demo):
    client.post(
        "/operaciones",
        json={"cliente_id": empresa_demo["cliente_id"], "servicio_id": empresa_demo["servicio_id"], "muelle": "Muelle 5"},
        headers=auth_headers,
    )
    resp = client.get("/muelles/disponibilidad", headers=auth_headers)
    muelle5 = next(m for m in resp.json() if m["muelle"] == "Muelle 5")
    assert muelle5["disponible"] is False
    assert muelle5["cliente_nombre"] == "Cliente Contado"


def test_crear_operario_es_201(client, auth_headers):
    resp = client.post(
        "/operarios",
        json={"nombre": "Juan Perez", "cedula": "123456789", "tipo_sangre": "O+"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["tipo_sangre"] == "O+"


def test_crear_operario_tipo_sangre_invalido_da_422(client, auth_headers):
    resp = client.post(
        "/operarios",
        json={"nombre": "X", "cedula": "1", "tipo_sangre": "Z+"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_asignar_operario_a_cuadrilla(client, auth_headers, empresa_demo):
    resp = client.post("/operarios", json={"nombre": "Ana Gomez", "cedula": "987654321"}, headers=auth_headers)
    operario_id = resp.json()["id"]

    resp = client.patch(
        f"/operarios/{operario_id}/cuadrilla",
        json={"cuadrilla_id": empresa_demo["cuadrilla_id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["cuadrilla_id"] == empresa_demo["cuadrilla_id"]

    resp = client.get("/operarios", params={"cuadrilla_id": empresa_demo["cuadrilla_id"]}, headers=auth_headers)
    assert any(o["id"] == operario_id for o in resp.json())