def test_muestra_aql_proveedor_normal(client, auth_headers, proveedor_demo):
    resp = client.get(
        f"/proveedores/{proveedor_demo}/muestra-aql",
        params={"tamano_lote": 300, "nivel_inspeccion_general": "II", "aql": 2.5},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["severidad_actual"] == "normal"
    assert body["codigo_letra"] == "H"
    assert body["tamano_muestra"] == 50


def test_muestra_aql_proveedor_inexistente_da_404(client, auth_headers):
    import uuid
    resp = client.get(
        f"/proveedores/{uuid.uuid4()}/muestra-aql",
        params={"tamano_lote": 300},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_crear_operacion_con_proveedor(client, auth_headers, empresa_demo, proveedor_demo):
    resp = client.post(
        "/operaciones",
        json={
            "cliente_id": empresa_demo["cliente_id"], "servicio_id": empresa_demo["servicio_id"],
            "proveedor_id": proveedor_demo,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["proveedor_id"] == proveedor_demo