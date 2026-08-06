def test_listar_servicios(client, auth_headers, empresa_demo):
    resp = client.get("/servicios", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    nombres = [s["nombre"] for s in resp.json()]
    assert "Descargue" in nombres


def test_listar_cuadrillas(client, auth_headers, empresa_demo):
    resp = client.get("/cuadrillas", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    nombres = [c["nombre"] for c in resp.json()]
    assert "Cuadrilla A" in nombres