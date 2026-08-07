import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.plataforma import Proveedor
from app.schemas.proveedores import MuestraAQLOut, ProveedorCreate, ProveedorOut
from app.services.aql import AQLError, calcular_plan_muestreo

router = APIRouter(prefix="/proveedores", tags=["proveedores"])


@router.post("", response_model=ProveedorOut, status_code=status.HTTP_201_CREATED)
def crear_proveedor(
    payload: ProveedorCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    proveedor = Proveedor(empresa_id=current_user.empresa_id, nombre=payload.nombre, nit=payload.nit)
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


@router.get("", response_model=list[ProveedorOut])
def listar_proveedores(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente", "auditor", "operario")),
):
    return db.scalars(select(Proveedor).order_by(Proveedor.nombre)).all()


@router.get("/{proveedor_id}", response_model=ProveedorOut)
def consultar_proveedor(
    proveedor_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente", "auditor", "operario")),
):
    proveedor = db.get(Proveedor, proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor


@router.get("/{proveedor_id}/muestra-aql", response_model=MuestraAQLOut)
def calcular_muestra_aql(
    proveedor_id: uuid.UUID,
    tamano_lote: int = Query(..., ge=2),
    nivel_inspeccion_general: str = Query("II"),
    aql: float = Query(2.5),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente", "operario")),
):
    """Calcula cuántas cajas hay que revisar, a partir de la cantidad
    estimada del pedido y la severidad ACTUAL del proveedor (normal,
    reforzado o reducido) -- pensado para llamarse justo después de
    capturar la cantidad estimada al crear una operación."""
    proveedor = db.get(Proveedor, proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    try:
        plan = calcular_plan_muestreo(tamano_lote, nivel_inspeccion_general, aql)
    except AQLError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return MuestraAQLOut(
        severidad_actual=proveedor.nivel_inspeccion_actual,
        codigo_letra=plan.codigo_letra,
        tamano_muestra=plan.tamano_muestra,
        limite_aceptacion=plan.limite_aceptacion,
        limite_rechazo=plan.limite_rechazo,
    )