import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.plataforma import Cliente
from app.schemas.clientes import ClienteCreate, ClienteOut

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