import uuid


def test_crear_proveedor_es_201_con_valores_por_defecto(client, auth_headers):
    resp = client.post("/proveedores", json={"nombre": "Proveedor Nuevo", "nit": "900123456-7"}, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["nivel_riesgo"] == "confiable"
    assert body["nivel_inspeccion_actual"] == "normal"


def test_listar_proveedores_incluye_el_creado(client, auth_headers):
    client.post("/proveedores", json={"nombre": "Proveedor A"}, headers=auth_headers)
    resp = client.get("/proveedores", headers=auth_headers)
    assert resp.status_code == 200
    assert any(p["nombre"] == "Proveedor A" for p in resp.json())


def test_consultar_proveedor_inexistente_da_404(client, auth_headers):
    resp = client.get(f"/proveedores/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404