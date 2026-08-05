from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db_admin
from app.core.security import create_access_token, verify_password
from app.models.plataforma import Usuario
from app.schemas.operaciones import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _autenticar(email: str, password: str, db: Session) -> Usuario:
    usuario = db.scalar(select(Usuario).where(Usuario.email == email, Usuario.activo.is_(True)))
    if not usuario or not verify_password(password, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    return usuario


def _token_para(usuario: Usuario) -> TokenResponse:
    token = create_access_token(
        usuario_id=str(usuario.id),
        empresa_id=str(usuario.empresa_id),
        rol=usuario.rol,
        cliente_id=str(usuario.cliente_id) if usuario.cliente_id else None,
    )
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db_admin)):
    """Login en JSON — el que usa la app móvil/web real."""
    usuario = _autenticar(payload.email, payload.password, db)
    return _token_para(usuario)


@router.post("/token", response_model=TokenResponse)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db_admin)):
    """Login en formato formulario (username/password) — el que usa el botón
    'Authorize' de /docs. Es el mismo login que /auth/login, solo que en el
    formato que espera Swagger; internamente valida igual contra la tabla usuarios.
    """
    usuario = _autenticar(form_data.username, form_data.password, db)
    return _token_para(usuario)