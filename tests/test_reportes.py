def test_dashboard_vacio_no_rompe(client, auth_headers):
    """Sin ninguna operación todavía, el dashboard debe responder con ceros
    y None en los promedios -- no debe dividir por cero ni tronar."""
    resp = client.get("/reportes/dashboard", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["operaciones"]["total"] == 0
    assert body["operaciones"]["tiempo_promedio_ciclo_minutos"] is None
    assert body["calidad"]["total_inspecciones"] == 0
    assert body["calidad"]["tasa_aceptacion_pct"] is None
    assert body["financiero"]["total_liquidado_historico"] == 0
    assert body["financiero"]["total_pendiente_cobro"] == 0


def test_dashboard_cuenta_operaciones_por_estado(client, auth_headers, empresa_demo):
    client.post(
        "/operaciones",
        json={"cliente_id": empresa_demo["cliente_id"], "servicio_id": empresa_demo["servicio_id"]},
        headers=auth_headers,
    )
    resp = client.post(
        "/operaciones",
        json={"cliente_id": empresa_demo["cliente_id"], "servicio_id": empresa_demo["servicio_id"]},
        headers=auth_headers,
    )
    operacion2 = resp.json()
    client.patch(
        f"/operaciones/{operacion2['id']}/asignar",
        json={
            "cuadrilla_id": empresa_demo["cuadrilla_id"],
            "tarifa_id": empresa_demo["tarifa_id"],
            "criterio_cobro": "cajas",
        },
        headers=auth_headers,
    )

    resp = client.get("/reportes/dashboard", headers=auth_headers)
    body = resp.json()
    assert body["operaciones"]["total"] == 2
    assert body["operaciones"]["por_estado"]["creada"] == 1
    assert body["operaciones"]["por_estado"]["asignada"] == 1


def test_dashboard_calcula_tiempo_operativo_de_operacion_cerrada(client, auth_headers, empresa_demo):
    resp = client.post(
        "/operaciones",
        json={"cliente_id": empresa_demo["cliente_id"], "servicio_id": empresa_demo["servicio_id"]},
        headers=auth_headers,
    )
    operacion = resp.json()
    client.patch(
        f"/operaciones/{operacion['id']}/asignar",
        json={
            "cuadrilla_id": empresa_demo["cuadrilla_id"],
            "tarifa_id": empresa_demo["tarifa_id"],
            "criterio_cobro": "cajas",
        },
        headers=auth_headers,
    )
    for tipo in ("factura", "pedido"):
        client.post(
            f"/operaciones/{operacion['id']}/evidencias",
            data={"tipo": tipo},
            files={"archivo": ("e.png", b"x", "image/png")},
            headers=auth_headers,
        )
    client.post(f"/operaciones/{operacion['id']}/iniciar", headers=auth_headers)
    client.post(
        f"/operaciones/{operacion['id']}/cerrar",
        json={"cantidad_real": 100, "forma_pago": "contado"},
        headers=auth_headers,
    )

    resp = client.get("/reportes/dashboard", headers=auth_headers)
    body = resp.json()
    assert body["operaciones"]["tiempo_promedio_operativo_minutos"] is not None
    assert body["operaciones"]["tiempo_promedio_operativo_minutos"] >= 0
    assert body["financiero"]["total_liquidado_historico"] == 185000  # 1850 * 100


def test_dashboard_calidad_refleja_inspecciones(client, auth_headers, proveedor_demo):
    for defectos in (0, 8):  # una aceptada, una rechazada (codigo H: Ac=7, Re=8)
        client.post(
            "/aql/inspecciones",
            json={
                "proveedor_id": proveedor_demo,
                "tamano_lote": 300,
                "nivel_inspeccion_general": "II",
                "aql": 2.5,
                "defectos_encontrados": defectos,
            },
            headers=auth_headers,
        )

    resp = client.get("/reportes/dashboard", headers=auth_headers)
    body = resp.json()
    assert body["calidad"]["total_inspecciones"] == 2
    assert body["calidad"]["tasa_aceptacion_pct"] == 50.0