"""
Fixtures compartidas para las pruebas de CargoFlow.

Las pruebas corren contra una base de datos Postgres real y separada
(<nombre_de_tu_db>_test), no contra SQLite en memoria — los modelos usan
UUID nativo de Postgres y Row-Level Security (SET LOCAL app.current_tenant),
ninguno de los dos existe en SQLite.

IMPORTANTE: DATABASE_URL se sobreescribe a la base de test ANTES de
importar cualquier módulo de app/, porque app.core.config.settings y
app.core.database.engine son singletons que leen la URL una sola vez,
en el momento de importarse.
"""

import os
import sys
import uuid
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import dotenv_values  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

_env_file = dotenv_values(PROJECT_ROOT / ".env")
_base_url = os.environ.get("DATABASE_URL") or _env_file.get("DATABASE_URL")
if not _base_url:
    raise RuntimeError("No se encontró DATABASE_URL ni en el entorno ni en .env")

_base_url_obj = make_url(_base_url)
_test_url_obj = _base_url_obj.set(database=f"{_base_url_obj.database}_test")

os.environ["DATABASE_URL"] = _test_url_obj.render_as_string(hide_password=False)

import subprocess  # noqa: E402

import psycopg  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.plataforma import Cliente, Empresa, Proveedor, Usuario  # noqa: E402
from app.models.recursos import Cuadrilla, Servicio, Tarifa  # noqa: E402

PASSWORD_DEMO = "cargoflow123"

TABLAS_EN_ORDEN_DE_LIMPIEZA = (
    "lineas_cobro", "inspecciones_aql", "evidencias", "incidencias", "pagos", "liquidaciones", "operaciones",
    "tarifas", "servicios", "cuadrillas", "vehiculos", "tipos_vehiculo",
    "proveedores", "clientes", "usuarios", "empresas",
)


def _asegurar_base_de_datos_de_test():
    conn = psycopg.connect(
        host=_test_url_obj.host,
        port=_test_url_obj.port,
        user=_test_url_obj.username,
        password=_test_url_obj.password,
        dbname="postgres",
        autocommit=True,
    )
    try:
        existe = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (_test_url_obj.database,)
        ).fetchone()
        if not existe:
            conn.execute(f'CREATE DATABASE "{_test_url_obj.database}"')
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def _base_de_datos_de_test_lista():
    _asegurar_base_de_datos_de_test()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        check=True,
        env=os.environ.copy(),
    )


@pytest.fixture(autouse=True)
def _tablas_limpias(_base_de_datos_de_test_lista):
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {', '.join(TABLAS_EN_ORDEN_DE_LIMPIEZA)} RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
def _uploads_en_carpeta_temporal(tmp_path, monkeypatch):
    import app.storage.evidencias as storage_module
    monkeypatch.setattr(storage_module, "BASE_UPLOAD_DIR", tmp_path / "evidencias")


@pytest.fixture
def db_admin():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _fijar_tenant(db, empresa_id):
    db.execute(text("SELECT set_config('app.current_tenant', :tid, true)"), {"tid": str(empresa_id)})


@pytest.fixture
def empresa_demo(db_admin):
    db = db_admin

    empresa = Empresa(nombre="Empresa Test", plan="trial", estado="activa")
    db.add(empresa)
    db.commit()
    db.refresh(empresa)

    _fijar_tenant(db, empresa.id)

    usuario = Usuario(
        empresa_id=empresa.id,
        nombre="Supervisor Test",
        email="supervisor@test.demo",
        password_hash=hash_password(PASSWORD_DEMO),
        rol="supervisor",
        tipo_acceso="web",
        activo=True,
    )
    db.add(usuario)

    servicio = Servicio(empresa_id=empresa.id, nombre="Descargue")
    db.add(servicio)

    cliente = Cliente(
        empresa_id=empresa.id, nombre="Cliente Contado", nit="900000000-1",
        condicion_pago="contado", activo=True,
    )
    db.add(cliente)

    cliente_credito = Cliente(
        empresa_id=empresa.id, nombre="Cliente Credito", nit="900000001-2",
        condicion_pago="credito", activo=True,
    )
    db.add(cliente_credito)

    cuadrilla = Cuadrilla(empresa_id=empresa.id, nombre="Cuadrilla A", estado="disponible")
    db.add(cuadrilla)

    db.flush()

    tarifa = Tarifa(
        empresa_id=empresa.id, cliente_id=cliente.id, servicio_id=servicio.id,
        criterio="cajas", valor=1850, vigente_desde=date.today(),
    )
    db.add(tarifa)

    tarifa_credito = Tarifa(
        empresa_id=empresa.id, cliente_id=cliente_credito.id, servicio_id=servicio.id,
        criterio="cajas", valor=1850, vigente_desde=date.today(),
    )
    db.add(tarifa_credito)

    db.commit()

    return {
        "empresa_id": str(empresa.id),
        "email": usuario.email,
        "password": PASSWORD_DEMO,
        "cliente_id": str(cliente.id),
        "cliente_credito_id": str(cliente_credito.id),
        "servicio_id": str(servicio.id),
        "cuadrilla_id": str(cuadrilla.id),
        "tarifa_id": str(tarifa.id),
        "tarifa_credito_id": str(tarifa_credito.id),
    }


@pytest.fixture
def proveedor_demo(db_admin, empresa_demo):
    db = db_admin
    proveedor = Proveedor(
        empresa_id=uuid.UUID(empresa_demo["empresa_id"]),
        nombre="Proveedor Test",
        nit="900000002-3",
    )
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return str(proveedor.id)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client, empresa_demo):
    resp = client.post(
        "/auth/login",
        json={"email": empresa_demo["email"], "password": empresa_demo["password"]},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def gerente_headers(client, db_admin, empresa_demo):
    """Headers de un usuario con rol='gerente' en la misma empresa -- para
    endpoints que ya no permiten supervisor (ej. GET /reportes/dashboard)."""
    db = db_admin
    _fijar_tenant(db, uuid.UUID(empresa_demo["empresa_id"]))
    usuario = Usuario(
        empresa_id=uuid.UUID(empresa_demo["empresa_id"]),
        nombre="Gerente Test",
        email="gerente@test.demo",
        password_hash=hash_password(PASSWORD_DEMO),
        rol="gerente",
        tipo_acceso="web",
        activo=True,
    )
    db.add(usuario)
    db.commit()

    resp = client.post("/auth/login", json={"email": "gerente@test.demo", "password": PASSWORD_DEMO})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def portal_headers(client, auth_headers, empresa_demo):
    """Headers de un usuario del Portal de Cliente, ligado a cliente_id
    (el 'Cliente Contado' de empresa_demo)."""
    resp = client.post(
        f"/clientes/{empresa_demo['cliente_id']}/usuarios",
        json={"nombre": "Usuario Portal", "email": "portal@test.demo", "password": "portal123"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text

    resp = client.post("/auth/login", json={"email": "portal@test.demo", "password": "portal123"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}