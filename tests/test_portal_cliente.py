import uuid


def _crear_operacion_para_cliente(client, headers, empresa_demo, cliente_id, tarifa_id):
    resp = client.post(
        "/operaciones", json={"cliente_id": cliente_id, "servicio_id": empresa_demo["servicio_id"]}, headers=headers
    )
    operacion = resp.json()
    client.patch(
        f"/operaciones/{operacion['id']}/asignar",
        json={
            "cuadrilla_id": empresa_demo["cuadrilla_id"], "tarifa_id": tarifa_id,
            "criterio_cobro": "cajas", "cantidad_estimada": 100,
        },
        headers=headers,
    )
    return operacion["id"]


def test_portal_ve_solo_sus_propias_operaciones(client, auth_headers, portal_headers, empresa_demo):
    _crear_operacion_para_cliente(client, auth_headers, empresa_demo, empresa_demo["cliente_id"], empresa_demo["tarifa_id"])
    # operación de OTRO cliente de la misma empresa -- no debe verla
    _crear_operacion_para_cliente(
        client, auth_headers, empresa_demo, empresa_demo["cliente_credito_id"], empresa_demo["tarifa_credito_id"]
    )

    resp = client.get("/portal/mis-operaciones", headers=portal_headers)
    assert resp.status_code == 200, resp.text
    operaciones = resp.json()
    assert len(operaciones) == 1
    assert operaciones[0]["cliente_id"] == empresa_demo["cliente_id"]


def test_portal_no_puede_ver_operacion_de_otro_cliente(client, auth_headers, portal_headers, empresa_demo):
    op_id_ajeno = _crear_operacion_para_cliente(
        client, auth_headers, empresa_demo, empresa_demo["cliente_credito_id"], empresa_demo["tarifa_credito_id"]
    )
    resp = client.get(f"/portal/mis-operaciones/{op_id_ajeno}", headers=portal_headers)
    assert resp.status_code == 404


def test_portal_no_puede_usar_endpoints_de_staff(client, portal_headers, empresa_demo):
    """Un usuario del portal (rol='cliente') no debe poder crear operaciones
    como si fuera un supervisor interno."""
    resp = client.post(
        "/operaciones",
        json={"cliente_id": empresa_demo["cliente_id"], "servicio_id": empresa_demo["servicio_id"]},
        headers=portal_headers,
    )
    assert resp.status_code == 403


def test_staff_no_puede_usar_endpoints_de_portal(client, auth_headers):
    """Un supervisor no tiene cliente_id -- el portal debe rechazarlo aunque
    su token sea válido."""
    resp = client.get("/portal/mis-operaciones", headers=auth_headers)
    assert resp.status_code == 403


def test_crear_usuario_portal_cliente_inexistente_da_404(client, auth_headers):
    resp = client.post(
        f"/clientes/{uuid.uuid4()}/usuarios",
        json={"nombre": "X", "email": "x@test.demo", "password": "x123456"},
        headers=auth_headers,
    )
    assert resp.status_code == 404