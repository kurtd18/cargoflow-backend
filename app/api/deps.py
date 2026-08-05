from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db_for_tenant
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class CurrentUser:
    def __init__(self, usuario_id: str, empresa_id: str, rol: str, cliente_id: str | None = None):
        self.usuario_id = usuario_id
        self.empresa_id = empresa_id
        self.rol = rol
        self.cliente_id = cliente_id


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    return CurrentUser(
        usuario_id=payload["sub"],
        empresa_id=payload["empresa_id"],
        rol=payload["rol"],
        cliente_id=payload.get("cliente_id"),
    )


def get_db(current_user: CurrentUser = Depends(get_current_user)) -> Session:
    """Sesión de base de datos ya acotada a la empresa del usuario autenticado.
    Ver app/core/database.py — este es el punto donde se activa el aislamiento RLS.
    """
    yield from get_db_for_tenant(current_user.empresa_id)


def require_roles(*roles_permitidos: str):
    """Dependencia factory para restringir un endpoint a ciertos roles.
    Uso: current_user: CurrentUser = Depends(require_roles("supervisor", "gerente"))
    """

    def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.rol not in roles_permitidos:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para esta acción")
        return current_user

    return checker


def require_cliente(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Restringe un endpoint a usuarios del Portal de Cliente (rol='cliente'
    con cliente_id asignado). Los endpoints de staff (require_roles) ya
    rechazan 'cliente' automáticamente porque nunca aparece en su lista de
    roles permitidos -- esta dependencia es el equivalente inverso.
    """
    if current_user.rol != "cliente" or not current_user.cliente_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este endpoint es solo para usuarios del portal de cliente",
        )
    return current_user