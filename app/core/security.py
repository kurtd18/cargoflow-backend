from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(usuario_id: str, empresa_id: str, rol: str, cliente_id: Optional[str] = None) -> str:
    """Codifica empresa_id y rol dentro del JWT: son la base del aislamiento
    multiempresa (SET LOCAL app.current_tenant) y del control de acceso por rol.
    cliente_id solo se incluye para usuarios del portal de cliente (rol='cliente').
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": usuario_id, "empresa_id": empresa_id, "rol": rol, "exp": expire}
    if cliente_id:
        payload["cliente_id"] = cliente_id
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])