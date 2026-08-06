import uuid


def _crear_tarifa(client, headers, **overrides):
    body = {
        "servicio_id": overrides.pop("servicio_id"),
        "criterio": overrides.pop("criterio", "cajas"),
        "valor": overrides.pop("valor", 2000),
    }
    body.update(overrides)
    return client.post("/tarifas", json=body, headers=headers)


def test_crear_tarifa_es_201(client, auth_headers, empresa_demo):
    resp = _crear_tarifa(
        client, auth_headers,
        cliente_id=empresa_demo["cliente_credito_id"],
        servicio_id=empresa_demo["servicio_id"],
        criterio="unidades",
        valor=350,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["criterio"] == "unidades"
    assert body["valor"] == 350
    assert body["vigente_hasta"] is None


def test_crear_tarifa_general_sin_cliente_es_201(client, auth_headers, empresa_demo):
    resp = _crear_tarifa(
        client, auth_headers,
        servicio_id=empresa_demo["servicio_id"],
        criterio="toneladas",
        valor=19188,
        categoria_mercancia="fruver",
        concepto="descargue_tonelada",
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["cliente_id"] is None
    assert body["categoria_mercancia"] == "fruver"


def test_listar_tarifas_incluye_generales_para_cualquier_cliente(client, auth_headers, empresa_demo):
    _crear_tarifa(
        client, auth_headers,
        servicio_id=empresa_demo["servicio_id"],
        criterio="toneladas",
        valor=19188,
        categoria_mercancia="fruver",
    )
    resp = client.get("/tarifas", params={"cliente_id": empresa_demo["cliente_id"]}, headers=auth_headers)
    assert resp.status_code == 200
    assert any(t["cliente_id"] is None and t["criterio"] == "toneladas" for t in resp.json())


def test_crear_tarifa_cierra_la_anterior_automaticamente(client, auth_headers, empresa_demo):
    """empresa_demo ya trae una tarifa vigente para (cliente, servicio, 'cajas').
    Crear otra para la misma combinación debe vencer la anterior."""
    resp = _crear_tarifa(
        client, auth_headers,
        cliente_id=empresa_demo["cliente_id"],
        servicio_id=empresa_demo["servicio_id"],
        criterio="cajas",
        valor=2100,
    )
    assert resp.status_code == 201, resp.text

    resp_vieja = client.get(f"/tarifas/{empresa_demo['tarifa_id']}", headers=auth_headers)
    assert resp_vieja.status_code == 200
    assert resp_vieja.json()["vigente_hasta"] is not None


def test_crear_tarifa_vehiculo_sin_tipo_vehiculo_da_422(client, auth_headers, empresa_demo):
    resp = _crear_tarifa(
        client, auth_headers,
        cliente_id=empresa_demo["cliente_id"],
        servicio_id=empresa_demo["servicio_id"],
        criterio="vehiculo",
        valor=50000,
    )
    assert resp.status_code == 422


def test_listar_tarifas_solo_vigentes_por_defecto(client, auth_headers, empresa_demo):
    _crear_tarifa(
        client, auth_headers,
        cliente_id=empresa_demo["cliente_id"],
        servicio_id=empresa_demo["servicio_id"],
        criterio="cajas",
        valor=2200,
    )

    resp = client.get(
        "/tarifas", params={"cliente_id": empresa_demo["cliente_id"]}, headers=auth_headers
    )
    assert resp.status_code == 200
    ids_vigentes = {t["id"] for t in resp.json()}
    assert empresa_demo["tarifa_id"] not in ids_vigentes

    resp_todas = client.get(
        "/tarifas",
        params={"cliente_id": empresa_demo["cliente_id"], "solo_vigentes": False},
        headers=auth_headers,
    )
    ids_todas = {t["id"] for t in resp_todas.json()}
    assert empresa_demo["tarifa_id"] in ids_todas


def test_vencer_tarifa_es_200(client, auth_headers, empresa_demo):
    resp = client.patch(f"/tarifas/{empresa_demo['tarifa_id']}/vencer", json={}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["vigente_hasta"] is not None


def test_vencer_tarifa_ya_vencida_da_400(client, auth_headers, empresa_demo):
    client.patch(f"/tarifas/{empresa_demo['tarifa_id']}/vencer", json={}, headers=auth_headers)

    resp = client.patch(f"/tarifas/{empresa_demo['tarifa_id']}/vencer", json={}, headers=auth_headers)
    assert resp.status_code == 400


def test_consultar_tarifa_inexistente_da_404(client, auth_headers):
    resp = client.get(f"/tarifas/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404