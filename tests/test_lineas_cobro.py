def _crear_y_asignar_solo_cuadrilla(client, headers, empresa_demo):
    resp = client.post(
        "/operaciones",
        json={
            "cliente_id": empresa_demo["cliente_id"], "servicio_id": empresa_demo["servicio_id"],
            "categoria_mercancia": "fruver",
        },
        headers=headers,
    )
    operacion = resp.json()
    resp = client.patch(
        f"/operaciones/{operacion['id']}/asignar",
        json={"cuadrilla_id": empresa_demo["cuadrilla_id"]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "asignada"
    return operacion["id"]


def _subir_evidencias_e_iniciar(client, headers, op_id):
    for tipo in ("factura", "pedido"):
        client.post(
            f"/operaciones/{op_id}/evidencias", data={"tipo": tipo},
            files={"archivo": ("e.png", b"x", "image/png")}, headers=headers,
        )
    client.post(f"/operaciones/{op_id}/iniciar", headers=headers)


def test_asignar_sin_tarifa_es_valido(client, auth_headers, empresa_demo):
    op_id = _crear_y_asignar_solo_cuadrilla(client, auth_headers, empresa_demo)
    resp = client.get(f"/operaciones/{op_id}", headers=auth_headers)
    assert resp.json()["estado"] == "asignada"


def test_agregar_linea_y_actualizar_cantidad(client, auth_headers, empresa_demo):
    op_id = _crear_y_asignar_solo_cuadrilla(client, auth_headers, empresa_demo)

    resp = client.post(
        f"/operaciones/{op_id}/lineas",
        json={"tarifa_id": empresa_demo["tarifa_id"], "cantidad_estimada": 50},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    linea_id = resp.json()["id"]

    resp = client.patch(
        f"/operaciones/{op_id}/lineas/{linea_id}/cantidad",
        json={"cantidad_real": 42},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["cantidad_real"] == 42

    resp = client.get(f"/operaciones/{op_id}/lineas", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_cerrar_con_multiples_lineas_suma_la_liquidacion(client, auth_headers, empresa_demo):
    op_id = _crear_y_asignar_solo_cuadrilla(client, auth_headers, empresa_demo)

    resp = client.post(
        "/tarifas",
        json={
            "servicio_id": empresa_demo["servicio_id"], "criterio": "toneladas", "valor": 5000,
            "categoria_mercancia": "fruver", "concepto": "trasvaseo_tonelada",
        },
        headers=auth_headers,
    )
    tarifa_2_id = resp.json()["id"]

    for tarifa_id, cantidad in [(empresa_demo["tarifa_id"], 10), (tarifa_2_id, 3)]:
        resp = client.post(f"/operaciones/{op_id}/lineas", json={"tarifa_id": tarifa_id}, headers=auth_headers)
        linea_id = resp.json()["id"]
        client.patch(
            f"/operaciones/{op_id}/lineas/{linea_id}/cantidad", json={"cantidad_real": cantidad}, headers=auth_headers
        )

    _subir_evidencias_e_iniciar(client, auth_headers, op_id)

    resp = client.post(
        f"/operaciones/{op_id}/cerrar",
        json={"forma_pago": "contado", "medio_pago": "efectivo"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text

    # 10 * 1850 + 3 * 5000 = 18500 + 15000 = 33500
    resp_dash = client.get("/reportes/dashboard", headers=auth_headers)
    assert resp_dash.json()["financiero"]["total_liquidado_historico"] == 33500


def test_cerrar_multiples_lineas_sin_cantidad_da_400(client, auth_headers, empresa_demo):
    op_id = _crear_y_asignar_solo_cuadrilla(client, auth_headers, empresa_demo)
    client.post(f"/operaciones/{op_id}/lineas", json={"tarifa_id": empresa_demo["tarifa_id"]}, headers=auth_headers)

    _subir_evidencias_e_iniciar(client, auth_headers, op_id)

    resp = client.post(
        f"/operaciones/{op_id}/cerrar",
        json={"forma_pago": "contado", "medio_pago": "efectivo"},
        headers=auth_headers,
    )
    assert resp.status_code == 400