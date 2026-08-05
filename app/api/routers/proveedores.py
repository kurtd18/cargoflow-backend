import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.plataforma import Proveedor
from app.schemas.proveedores import ProveedorCreate, ProveedorOut

router = APIRouter(prefix="/proveedores", tags=["proveedores"])


@router.post("", response_model=ProveedorOut, status_code=status.HTTP_201_CREATED)
def crear_proveedor(
    payload: ProveedorCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    """nivel_riesgo y nivel_inspeccion_actual nacen en sus valores por defecto
    (confiable / normal) -- los actualiza automáticamente el módulo AQL a
    partir de los resultados de inspección, nunca se fijan a mano aquí."""
    proveedor = Proveedor(empresa_id=current_user.empresa_id, nombre=payload.nombre, nit=payload.nit)
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


@router.get("", response_model=list[ProveedorOut])
def listar_proveedores(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente", "auditor")),
):
    return db.scalars(select(Proveedor).order_by(Proveedor.nombre)).all()


@router.get("/{proveedor_id}", response_model=ProveedorOut)
def consultar_proveedor(
    proveedor_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente", "auditor")),
):
    proveedor = db.get(Proveedor, proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor