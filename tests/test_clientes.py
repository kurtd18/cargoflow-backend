import uuid


def test_crear_cliente_credito_es_201(client, auth_headers):
    resp = client.post(
        "/clientes",
        json={"nombre": "Cliente Credito Nuevo", "condicion_pago": "credito", "cupo_credito": 5000000},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["condicion_pago"] == "credito"


def test_crear_cliente_condicion_invalida_da_422(client, auth_headers):
    resp = client.post("/clientes", json={"nombre": "X", "condicion_pago": "efectivo"}, headers=auth_headers)
    assert resp.status_code == 422


def test_listar_clientes_incluye_el_creado(client, auth_headers):
    client.post("/clientes", json={"nombre": "Cliente Listado"}, headers=auth_headers)
    resp = client.get("/clientes", headers=auth_headers)
    assert resp.status_code == 200
    assert any(c["nombre"] == "Cliente Listado" for c in resp.json())


def test_consultar_cliente_inexistente_da_404(client, auth_headers):
    resp = client.get(f"/clientes/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404