import io
import uuid


def _crear_operacion(client, headers, empresa_demo):
    resp = client.post(
        "/operaciones",
        json={"cliente_id": empresa_demo["cliente_id"], "servicio_id": empresa_demo["servicio_id"]},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_reportar_incidencia_sin_foto_es_201(client, auth_headers, empresa_demo):
    """La foto es opcional: Incidencia.foto_url es nullable en el modelo."""
    operacion = _crear_operacion(client, auth_headers, empresa_demo)

    resp = client.post(
        f"/operaciones/{operacion['id']}/incidencias",
        data={"tipo": "retraso", "descripcion": "Cuadrilla llegó 40 minutos tarde"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["tipo"] == "retraso"
    assert body["descripcion"] == "Cuadrilla llegó 40 minutos tarde"
    assert body["foto_url"] is None


def test_reportar_incidencia_con_foto_es_201(client, auth_headers, empresa_demo):
    operacion = _crear_operacion(client, auth_headers, empresa_demo)

    archivo = ("dano.png", io.BytesIO(b"contenido-fake-de-prueba"), "image/png")
    resp = client.post(
        f"/operaciones/{operacion['id']}/incidencias",
        data={"tipo": "mercancia_danada", "descripcion": "Caja rota en la esquina"},
        files={"archivo": archivo},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["foto_url"] is not None


def test_reportar_incidencia_sin_descripcion_es_201(client, auth_headers, empresa_demo):
    """descripcion también es opcional -- solo tipo es obligatorio."""
    operacion = _crear_operacion(client, auth_headers, empresa_demo)

    resp = client.post(
        f"/operaciones/{operacion['id']}/incidencias",
        data={"tipo": "otro"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["descripcion"] is None


def test_listar_incidencias_devuelve_las_creadas(client, auth_headers, empresa_demo):
    operacion = _crear_operacion(client, auth_headers, empresa_demo)

    client.post(
        f"/operaciones/{operacion['id']}/incidencias",
        data={"tipo": "faltante", "descripcion": "Faltaron 3 cajas"},
        headers=auth_headers,
    )
    client.post(
        f"/operaciones/{operacion['id']}/incidencias",
        data={"tipo": "retraso"},
        headers=auth_headers,
    )

    resp = client.get(f"/operaciones/{operacion['id']}/incidencias", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    incidencias = resp.json()
    assert len(incidencias) == 2
    assert {i["tipo"] for i in incidencias} == {"faltante", "retraso"}


def test_reportar_incidencia_operacion_inexistente_da_404(client, auth_headers):
    resp = client.post(
        f"/operaciones/{uuid.uuid4()}/incidencias",
        data={"tipo": "retraso"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_listar_incidencias_operacion_inexistente_da_404(client, auth_headers):
    resp = client.get(f"/operaciones/{uuid.uuid4()}/incidencias", headers=auth_headers)
    assert resp.status_code == 404