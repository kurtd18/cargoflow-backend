"""
Motor de base de datos y mecanismo de aislamiento multiempresa.

Patrón (ver Arquitectura Técnica, Sección 1):
- Toda tabla de negocio tiene una columna empresa_id.
- Cada tabla tiene una política Row-Level Security que exige
  empresa_id = current_setting('app.current_tenant').
- get_db_for_tenant() abre una sesión y ejecuta SET LOCAL app.current_tenant
  ANTES de cualquier consulta del request, dentro de la misma transacción.
  Esto hace que el aislamiento lo garantice Postgres, no el código de la app.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db_for_tenant(empresa_id: str):
    """Generador de sesión de base de datos acotada a una empresa (tenant).

    Uso típico dentro de una dependencia de FastAPI (ver app/api/deps.py),
    donde empresa_id proviene del JWT del usuario autenticado.
    """
    db = SessionLocal()
    try:
        # SET LOCAL no acepta parámetros bindeados (:tid); set_config() sí.
        # El tercer argumento (true) hace que el valor solo dure la transacción actual,
        # igual que SET LOCAL.
        db.execute(text("SELECT set_config('app.current_tenant', :tid, true)"), {"tid": empresa_id})
        yield db
    finally:
        db.close()


def get_db_admin():
    """Sesión sin restricción de tenant, solo para operaciones de plataforma
    (por ejemplo, crear una nueva empresa). Uso restringido al rol admin_plataforma.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
