import uuid


def test_calculadora_plan_lote_conocido(client, auth_headers):
    """Caso verificado de la propia norma: lote de 4000, Nivel II, AQL 2.5
    -> código L, n=200, Ac=21, Re=22."""
    resp = client.get(
        "/aql/plan",
        params={"tamano_lote": 4000, "nivel_inspeccion_general": "II", "aql": 2.5},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["codigo_letra"] == "L"
    assert body["tamano_muestra"] == 200
    assert body["limite_aceptacion"] == 21
    assert body["limite_rechazo"] == 22


def test_calculadora_lote_muy_pequeno_da_422(client, auth_headers):
    resp = client.get("/aql/plan", params={"tamano_lote": 1}, headers=auth_headers)
    assert resp.status_code == 422


def test_crear_inspeccion_aceptada_es_201(client, auth_headers, proveedor_demo):
    resp = client.post(
        "/aql/inspecciones",
        json={
            "proveedor_id": proveedor_demo,
            "tamano_lote": 300,  # 281-500, Nivel II -> codigo H, n=50, Ac=7, Re=8
            "nivel_inspeccion_general": "II",
            "aql": 2.5,
            "defectos_encontrados": 0,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["resultado"] == "aceptado"
    assert body["codigo_letra"] == "H"
    assert body["tamano_muestra"] == 50


def test_crear_inspeccion_rechazada_es_201(client, auth_headers, proveedor_demo):
    resp = client.post(
        "/aql/inspecciones",
        json={
            "proveedor_id": proveedor_demo,
            "tamano_lote": 300,
            "nivel_inspeccion_general": "II",
            "aql": 2.5,
            "defectos_encontrados": 8,  # Re=8 para codigo H con AQL 2.5
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["resultado"] == "rechazado"


def test_dos_rechazos_en_cinco_activan_severidad_reforzada(client, auth_headers, proveedor_demo):
    for defectos in [8, 0, 0, 8, 0]:  # 2 rechazos entre las primeras 4 ya activan reforzado
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

    resp = client.post(
        "/aql/inspecciones",
        json={
            "proveedor_id": proveedor_demo,
            "tamano_lote": 300,
            "nivel_inspeccion_general": "II",
            "aql": 2.5,
            "defectos_encontrados": 0,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["severidad"] == "reforzado"


def test_diez_aceptados_activan_severidad_reducida(client, auth_headers, proveedor_demo):
    """Corregido: la norma exige 10 lotes consecutivos aceptados para pasar
    a reducido (verificado contra 7 CFR 42.108), no 5."""
    for _ in range(10):
        client.post(
            "/aql/inspecciones",
            json={
                "proveedor_id": proveedor_demo,
                "tamano_lote": 300,
                "nivel_inspeccion_general": "II",
                "aql": 2.5,
                "defectos_encontrados": 0,
            },
            headers=auth_headers,
        )

    resp = client.post(
        "/aql/inspecciones",
        json={
            "proveedor_id": proveedor_demo,
            "tamano_lote": 300,
            "nivel_inspeccion_general": "II",
            "aql": 2.5,
            "defectos_encontrados": 0,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["severidad"] == "reducido"


def test_crear_inspeccion_proveedor_inexistente_da_404(client, auth_headers):
    resp = client.post(
        "/aql/inspecciones",
        json={"proveedor_id": str(uuid.uuid4()), "tamano_lote": 300, "defectos_encontrados": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 404