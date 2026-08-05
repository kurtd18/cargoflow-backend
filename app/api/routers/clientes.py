import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.core.security import hash_password
from app.models.plataforma import Cliente, Usuario
from app.schemas.clientes import ClienteCreate, ClienteOut, UsuarioClienteCreate, UsuarioClienteOut

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def crear_cliente(
    payload: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    cliente = Cliente(
        empresa_id=current_user.empresa_id,
        nombre=payload.nombre,
        nit=payload.nit,
        condicion_pago=payload.condicion_pago,
        cupo_credito=payload.cupo_credito,
        activo=True,
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.get("", response_model=list[ClienteOut])
def listar_clientes(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente", "facturacion")),
):
    return db.scalars(select(Cliente).order_by(Cliente.nombre)).all()


@router.get("/{cliente_id}", response_model=ClienteOut)
def consultar_cliente(
    cliente_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente", "facturacion")),
):
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.post("/{cliente_id}/usuarios", response_model=UsuarioClienteOut, status_code=status.HTTP_201_CREATED)
def crear_usuario_portal(
    cliente_id: uuid.UUID,
    payload: UsuarioClienteCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    """Crea una credencial de acceso al Portal del Cliente. El login queda
    ligado a este cliente_id (rol='cliente') y solo puede ver sus propias
    operaciones y pagos -- ver app/api/routers/portal_cliente.py."""
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    usuario = Usuario(
        empresa_id=current_user.empresa_id,
        cliente_id=cliente_id,
        nombre=payload.nombre,
        email=payload.email,
        password_hash=hash_password(payload.password),
        rol="cliente",
        tipo_acceso="web",
        activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario