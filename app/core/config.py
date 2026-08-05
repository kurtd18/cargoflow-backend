vfrom pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Ancla el archivo .env a la raíz del proyecto (donde está requirements.txt),
# sin importar desde qué carpeta se ejecute uvicorn o alembic.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

_SECRETOS_DE_EJEMPLO = {"", "change-this-in-production", "secret"}


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # development | production -- controla si se valida que JWT_SECRET ya
    # no sea el de ejemplo.
    environment: str = "development"

    # "*" en desarrollo. En producción, dominios reales separados por coma,
    # ej: "https://app.cargoflow.com,https://admin.cargoflow.com"
    allowed_origins: str = "*"

    # Independiente de environment a propósito: permite exponer /docs en un
    # despliegue de portafolio/demo sin necesidad de bajar la validación de
    # JWT_SECRET ni ninguna otra protección de producción.
    expose_docs: bool = False

    model_config = SettingsConfigDict(env_file=str(PROJECT_ROOT / ".env"), extra="ignore")

    @property
    def es_produccion(self) -> bool:
        return self.environment.strip().lower() == "production"

    @property
    def allowed_origins_list(self) -> list[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [origen.strip() for origen in self.allowed_origins.split(",") if origen.strip()]


settings = Settings()

if settings.es_produccion and settings.jwt_secret.strip() in _SECRETOS_DE_EJEMPLO:
    raise RuntimeError(
        "ENVIRONMENT=production pero JWT_SECRET sigue en su valor de ejemplo. "
        "Genera uno real antes de arrancar: "
        'python -c "import secrets; print(secrets.token_urlsafe(64))" '
        "y ponlo en el .env de producción."
    )