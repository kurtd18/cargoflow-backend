import uuid


def _crear_asignar_iniciar(client, headers, empresa_demo):
    resp = client.post(
        "/operaciones",
        json={"cliente_id": empresa_demo["cliente_id"], "servicio_id": empresa_demo["servicio_id"]},
        headers=headers,
    )
    operacion = resp.json()
    client.patch(
        f"/operaciones/{operacion['id']}/asignar",
        json={
            "cuadrilla_id": empresa_demo["cuadrilla_id"], "tarifa_id": empresa_demo["tarifa_id"],
            "criterio_cobro": "cajas", "cantidad_estimada": 500,
        },
        headers=headers,
    )
    return operacion["id"]


def test_actualizar_cantidad_en_curso_es_200(client, auth_headers, empresa_demo):
    op_id = _crear_asignar_iniciar(client, auth_headers, empresa_demo)
    for tipo in ("factura", "pedido"):
        client.post(
            f"/operaciones/{op_id}/evidencias", data={"tipo": tipo},
            files={"archivo": ("e.png", b"x", "image/png")}, headers=auth_headers,
        )
    client.post(f"/operaciones/{op_id}/iniciar", headers=auth_headers)

    resp = client.patch(f"/operaciones/{op_id}/cantidad", json={"cantidad_real": 120}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["cantidad_real"] == 120


def test_actualizar_cantidad_antes_de_iniciar_da_400(client, auth_headers, empresa_demo):
    op_id = _crear_asignar_iniciar(client, auth_headers, empresa_demo)
    resp = client.patch(f"/operaciones/{op_id}/cantidad", json={"cantidad_real": 10}, headers=auth_headers)
    assert resp.status_code == 400


def test_actualizar_cantidad_operacion_inexistente_da_404(client, auth_headers):
    resp = client.patch(f"/operaciones/{uuid.uuid4()}/cantidad", json={"cantidad_real": 10}, headers=auth_headers)
    assert resp.status_code == 404