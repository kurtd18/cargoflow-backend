import uuid


def _crear_y_cerrar_operacion_credito(client, headers, empresa_demo, cantidad_real=480):
    """Flujo completo hasta cerrar con forma_pago='credito' -- usa el
    cliente_credito_id de empresa_demo, que sí está registrado como cliente
    de crédito."""
    resp = client.post(
        "/operaciones",
        json={"cliente_id": empresa_demo["cliente_credito_id"], "servicio_id": empresa_demo["servicio_id"]},
        headers=headers,
    )
    operacion = resp.json()

    client.patch(
        f"/operaciones/{operacion['id']}/asignar",
        json={
            "cuadrilla_id": empresa_demo["cuadrilla_id"],
            "tarifa_id": empresa_demo["tarifa_credito_id"],
            "criterio_cobro": "cajas",
            "cantidad_estimada": 500,
        },
        headers=headers,
    )

    for tipo in ("factura", "pedido"):
        archivo = ("evidencia.png", b"contenido-fake", "image/png")
        client.post(
            f"/operaciones/{operacion['id']}/evidencias",
            data={"tipo": tipo},
            files={"archivo": archivo},
            headers=headers,
        )

    client.post(f"/operaciones/{operacion['id']}/iniciar", headers=headers)

    resp = client.post(
        f"/operaciones/{operacion['id']}/cerrar",
        json={"cantidad_real": cantidad_real, "forma_pago": "credito", "medio_pago": "transferencia"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return operacion["id"]


def test_pago_credito_aparece_en_pendientes(client, auth_headers, empresa_demo):
    _crear_y_cerrar_operacion_credito(client, auth_headers, empresa_demo)

    resp = client.get("/facturacion/pendientes", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    pendientes = resp.json()
    assert len(pendientes) == 1
    assert pendientes[0]["estado"] == "pendiente_cobro"
    assert pendientes[0]["cliente_id"] == empresa_demo["cliente_credito_id"]


def test_pendientes_filtra_por_cliente(client, auth_headers, empresa_demo):
    _crear_y_cerrar_operacion_credito(client, auth_headers, empresa_demo)

    resp = client.get(
        "/facturacion/pendientes", params={"cliente_id": empresa_demo["cliente_id"]}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json() == []  # el pago quedó en cliente_credito_id, no en cliente_id


def test_resumen_agrupa_por_cliente(client, auth_headers, empresa_demo):
    _crear_y_cerrar_operacion_credito(client, auth_headers, empresa_demo, cantidad_real=100)
    _crear_y_cerrar_operacion_credito(client, auth_headers, empresa_demo, cantidad_real=200)

    resp = client.get("/facturacion/resumen", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["cantidad_pagos_pendientes"] == 2
    assert len(body["por_cliente"]) == 1  # ambas operaciones son del mismo cliente_credito_id
    # tarifa 1850 * 100 + 1850 * 200 = 555000
    assert body["total_pendiente"] == 555000


def test_marcar_pagado_saca_del_pendiente(client, auth_headers, empresa_demo):
    _crear_y_cerrar_operacion_credito(client, auth_headers, empresa_demo)

    resp = client.get("/facturacion/pendientes", headers=auth_headers)
    pago_id = resp.json()[0]["id"]

    resp = client.patch(f"/facturacion/pagos/{pago_id}/marcar-pagado", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "pagado"

    resp = client.get("/facturacion/pendientes", headers=auth_headers)
    assert resp.json() == []


def test_marcar_pagado_dos_veces_da_400(client, auth_headers, empresa_demo):
    _crear_y_cerrar_operacion_credito(client, auth_headers, empresa_demo)
    pago_id = client.get("/facturacion/pendientes", headers=auth_headers).json()[0]["id"]

    client.patch(f"/facturacion/pagos/{pago_id}/marcar-pagado", headers=auth_headers)
    resp = client.patch(f"/facturacion/pagos/{pago_id}/marcar-pagado", headers=auth_headers)
    assert resp.status_code == 400


def test_marcar_pagado_inexistente_da_404(client, auth_headers):
    resp = client.patch(f"/facturacion/pagos/{uuid.uuid4()}/marcar-pagado", headers=auth_headers)
    assert resp.status_code == 404