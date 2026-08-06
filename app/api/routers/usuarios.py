from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.core.security import hash_password
from app.models.plataforma import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioOut

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("gerente")),
):
    """Crea un usuario interno de la empresa (staff de CargoFlow). Solo un
    gerente puede dar de alta usuarios nuevos -- distinto de
    POST /clientes/{id}/usuarios, que crea logins del portal de cliente."""
    existente = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")

    usuario = Usuario(
        empresa_id=current_user.empresa_id,
        nombre=payload.nombre,
        email=payload.email,
        password_hash=hash_password(payload.password),
        rol=payload.rol,
        tipo_acceso="movil",
        activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("gerente", "administrador")),
):
    return db.scalars(
        select(Usuario).where(Usuario.cliente_id.is_(None)).order_by(Usuario.nombre)
    ).all()