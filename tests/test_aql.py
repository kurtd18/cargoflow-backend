import uuid


def _checklist_todo_conforme():
    items = ["estado_fisico", "cantidades", "empaque", "etiquetado", "fechas_vencimiento", "condiciones_temperatura", "lote_trazabilidad"]
    return [{"item": i, "conforme": True} for i in items]


def test_calculadora_plan_lote_conocido(client, auth_headers):
    resp = client.get("/aql/plan", params={"tamano_lote": 4000, "nivel_inspeccion_general": "II", "aql": 2.5}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["codigo_letra"] == "L"
    assert body["tamano_muestra"] == 200
    assert body["limite_aceptacion"] == 21
    assert body["limite_rechazo"] == 22


def test_crear_inspeccion_todo_conforme_es_aceptado(client, auth_headers, proveedor_demo):
    resp = client.post(
        "/aql/inspecciones",
        json={"proveedor_id": proveedor_demo, "tamano_lote": 300, "nivel_inspeccion_general": "II", "aql": 2.5, "checklist": _checklist_todo_conforme()},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["resultado"] == "aceptado"
    assert body["defectos_criticos"] == 0


def test_defecto_critico_rechaza_sin_importar_ac_re(client, auth_headers, proveedor_demo):
    checklist = _checklist_todo_conforme()
    checklist[0] = {"item": "estado_fisico", "conforme": False, "cantidad": 1, "severidad": "critico"}
    resp = client.post(
        "/aql/inspecciones",
        json={"proveedor_id": proveedor_demo, "tamano_lote": 300, "nivel_inspeccion_general": "II", "aql": 2.5, "checklist": checklist},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["resultado"] == "rechazado"
    assert body["defectos_criticos"] == 1


def test_mayores_y_menores_se_suman_para_la_decision(client, auth_headers, proveedor_demo):
    # codigo H (lote 300, Nivel II) con AQL 2.5 -> Ac=7, Re=8
    checklist = _checklist_todo_conforme()
    checklist[0] = {"item": "estado_fisico", "conforme": False, "cantidad": 5, "severidad": "mayor"}
    checklist[1] = {"item": "cantidades", "conforme": False, "cantidad": 2, "severidad": "menor"}
    resp = client.post(
        "/aql/inspecciones",
        json={"proveedor_id": proveedor_demo, "tamano_lote": 300, "nivel_inspeccion_general": "II", "aql": 2.5, "checklist": checklist},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["defectos_mayores"] == 5
    assert body["defectos_menores"] == 2
    assert body["resultado"] == "aceptado"  # 5+2=7, Ac=7 -> aceptado


def test_checklist_incompleto_da_422(client, auth_headers, proveedor_demo):
    resp = client.post(
        "/aql/inspecciones",
        json={"proveedor_id": proveedor_demo, "tamano_lote": 300, "checklist": _checklist_todo_conforme()[:3]},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_diez_aceptados_activan_severidad_reducida(client, auth_headers, proveedor_demo):
    for _ in range(10):
        client.post(
            "/aql/inspecciones",
            json={"proveedor_id": proveedor_demo, "tamano_lote": 300, "nivel_inspeccion_general": "II", "aql": 2.5, "checklist": _checklist_todo_conforme()},
            headers=auth_headers,
        )
    resp = client.post(
        "/aql/inspecciones",
        json={"proveedor_id": proveedor_demo, "tamano_lote": 300, "nivel_inspeccion_general": "II", "aql": 2.5, "checklist": _checklist_todo_conforme()},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["severidad"] == "reducido"


def test_crear_inspeccion_proveedor_inexistente_da_404(client, auth_headers):
    resp = client.post(
        "/aql/inspecciones",
        json={"proveedor_id": str(uuid.uuid4()), "tamano_lote": 300, "checklist": _checklist_todo_conforme()},
        headers=auth_headers,
    )
    assert resp.status_code == 404