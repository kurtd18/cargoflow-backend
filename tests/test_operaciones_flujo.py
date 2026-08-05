import io
import uuid


def _crear_operacion(client, headers, empresa_demo, cliente_id=None):
    resp = client.post(
        "/operaciones",
        json={
            "cliente_id": cliente_id or empresa_demo["cliente_id"],
            "servicio_id": empresa_demo["servicio_id"],
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _asignar(client, headers, operacion_id, empresa_demo, tarifa_id=None):
    resp = client.patch(
        f"/operaciones/{operacion_id}/asignar",
        json={
            "cuadrilla_id": empresa_demo["cuadrilla_id"],
            "tarifa_id": tarifa_id or empresa_demo["tarifa_id"],
            "criterio_cobro": "cajas",
            "cantidad_estimada": 500,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _subir_evidencia(client, headers, operacion_id, tipo):
    archivo = ("evidencia.png", io.BytesIO(b"contenido-fake-de-prueba"), "image/png")
    return client.post(
        f"/operaciones/{operacion_id}/evidencias",
        data={"tipo": tipo},
        files={"archivo": archivo},
        headers=headers,
    )


def test_flujo_completo_feliz(client, auth_headers, empresa_demo):
    operacion = _crear_operacion(client, auth_headers, empresa_demo)
    assert operacion["estado"] == "creada"

    operacion = _asignar(client, auth_headers, operacion["id"], empresa_demo)
    assert operacion["estado"] == "asignada"

    for tipo in ("factura", "pedido"):
        resp = _subir_evidencia(client, auth_headers, operacion["id"], tipo)
        assert resp.status_code == 201, resp.text

    resp = client.post(f"/operaciones/{operacion['id']}/iniciar", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "en_curso"

    resp = client.post(
        f"/operaciones/{operacion['id']}/cerrar",
        json={"cantidad_real": 480, "forma_pago": "contado", "medio_pago": "efectivo"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "finalizada"
    assert resp.json()["cantidad_real"] == 480

    resp = client.get(f"/operaciones/{operacion['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "finalizada"


def test_iniciar_sin_evidencias_da_412(client, auth_headers, empresa_demo):
    operacion = _crear_operacion(client, auth_headers, empresa_demo)
    _asignar(client, auth_headers, operacion["id"], empresa_demo)

    resp = client.post(f"/operaciones/{operacion['id']}/iniciar", headers=auth_headers)
    assert resp.status_code == 412
    assert "factura" in resp.json()["detail"]
    assert "pedido" in resp.json()["detail"]


def test_iniciar_con_evidencia_parcial_da_412_con_faltante_correcto(client, auth_headers, empresa_demo):
    operacion = _crear_operacion(client, auth_headers, empresa_demo)
    _asignar(client, auth_headers, operacion["id"], empresa_demo)
    _subir_evidencia(client, auth_headers, operacion["id"], "factura")

    resp = client.post(f"/operaciones/{operacion['id']}/iniciar", headers=auth_headers)
    assert resp.status_code == 412
    detail = resp.json()["detail"]
    assert "pedido" in detail
    assert "factura" not in detail  # ya no debe pedir la que sí se subió


def test_cerrar_sin_iniciar_da_400(client, auth_headers, empresa_demo):
    operacion = _crear_operacion(client, auth_headers, empresa_demo)
    _asignar(client, auth_headers, operacion["id"], empresa_demo)

    resp = client.post(
        f"/operaciones/{operacion['id']}/cerrar",
        json={"cantidad_real": 480, "forma_pago": "contado"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "en_curso" in resp.json()["detail"]


def test_cerrar_credito_con_cliente_sin_condicion_credito_da_400(client, auth_headers, empresa_demo):
    operacion = _crear_operacion(client, auth_headers, empresa_demo)  # cliente "contado"
    _asignar(client, auth_headers, operacion["id"], empresa_demo)
    for tipo in ("factura", "pedido"):
        _subir_evidencia(client, auth_headers, operacion["id"], tipo)
    client.post(f"/operaciones/{operacion['id']}/iniciar", headers=auth_headers)

    resp = client.post(
        f"/operaciones/{operacion['id']}/cerrar",
        json={"cantidad_real": 480, "forma_pago": "credito"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "crédito" in resp.json()["detail"].lower()


def test_cerrar_credito_con_cliente_de_credito_es_200(client, auth_headers, empresa_demo):
    operacion = _crear_operacion(client, auth_headers, empresa_demo, cliente_id=empresa_demo["cliente_credito_id"])
    _asignar(client, auth_headers, operacion["id"], empresa_demo, tarifa_id=empresa_demo["tarifa_credito_id"])

    for tipo in ("factura", "pedido"):
        _subir_evidencia(client, auth_headers, operacion["id"], tipo)
    client.post(f"/operaciones/{operacion['id']}/iniciar", headers=auth_headers)

    resp = client.post(
        f"/operaciones/{operacion['id']}/cerrar",
        json={"cantidad_real": 480, "forma_pago": "credito", "medio_pago": "transferencia"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "finalizada"


def test_asignar_operacion_inexistente_da_404(client, auth_headers, empresa_demo):
    resp = client.patch(
        f"/operaciones/{uuid.uuid4()}/asignar",
        json={
            "cuadrilla_id": empresa_demo["cuadrilla_id"],
            "tarifa_id": empresa_demo["tarifa_id"],
            "criterio_cobro": "cajas",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_iniciar_operacion_inexistente_da_404(client, auth_headers):
    resp = client.post(f"/operaciones/{uuid.uuid4()}/iniciar", headers=auth_headers)
    assert resp.status_code == 404


def test_cerrar_operacion_inexistente_da_404(client, auth_headers):
    resp = client.post(
        f"/operaciones/{uuid.uuid4()}/cerrar",
        json={"cantidad_real": 100, "forma_pago": "contado"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_consultar_operacion_inexistente_da_404(client, auth_headers):
    resp = client.get(f"/operaciones/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404