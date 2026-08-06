def test_crear_usuario_operario_es_201(client, gerente_headers):
    resp = client.post(
        "/usuarios",
        json={"nombre": "Operario Test", "email": "operario1@test.demo", "password": "operario123", "rol": "operario"},
        headers=gerente_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["rol"] == "operario"


def test_crear_usuario_rol_invalido_da_422(client, gerente_headers):
    resp = client.post(
        "/usuarios",
        json={"nombre": "X", "email": "x2@test.demo", "password": "x123456", "rol": "bibliotecario"},
        headers=gerente_headers,
    )
    assert resp.status_code == 422


def test_supervisor_no_puede_crear_usuarios(client, auth_headers):
    resp = client.post(
        "/usuarios",
        json={"nombre": "X", "email": "x3@test.demo", "password": "x123456", "rol": "operario"},
        headers=auth_headers,
    )
    assert resp.status_code == 403


def test_listar_usuarios_incluye_el_creado(client, gerente_headers):
    client.post(
        "/usuarios",
        json={"nombre": "Operario Listado", "email": "operario2@test.demo", "password": "operario123", "rol": "operario"},
        headers=gerente_headers,
    )
    resp = client.get("/usuarios", headers=gerente_headers)
    assert resp.status_code == 200
    assert any(u["nombre"] == "Operario Listado" for u in resp.json())