import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.operaciones import Operacion, Pago
from app.models.plataforma import Cliente
from app.schemas.facturacion import PagoOut, ResumenClientePendiente, ResumenFacturacion

router = APIRouter(prefix="/facturacion", tags=["facturacion"])

ROLES_FACTURACION = ("supervisor", "gerente", "facturacion")


def _pago_a_out(pago: Pago, cliente_id: uuid.UUID, cliente_nombre: str) -> PagoOut:
    return PagoOut(
        id=pago.id,
        operacion_id=pago.operacion_id,
        cliente_id=cliente_id,
        cliente_nombre=cliente_nombre,
        forma_pago=pago.forma_pago,
        medio_pago=pago.medio_pago,
        monto=float(pago.monto),
        estado=pago.estado,
        creado_en=pago.creado_en,
    )


@router.get("/pendientes", response_model=list[PagoOut])
def listar_pendientes(
    cliente_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_FACTURACION)),
):
    """Pagos con estado pendiente_cobro (los que dejó /operaciones/{id}/cerrar
    con forma_pago='credito'), con el cliente ya resuelto para no obligar al
    consumidor de la API a hacer una consulta aparte."""
    query = (
        select(Pago, Operacion.cliente_id, Cliente.nombre)
        .join(Operacion, Pago.operacion_id == Operacion.id)
        .join(Cliente, Operacion.cliente_id == Cliente.id)
        .where(Pago.estado == "pendiente_cobro")
    )
    if cliente_id:
        query = query.where(Operacion.cliente_id == cliente_id)

    filas = db.execute(query.order_by(Pago.creado_en)).all()
    return [_pago_a_out(pago, cid, nombre) for pago, cid, nombre in filas]


@router.get("/resumen", response_model=ResumenFacturacion)
def resumen(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_FACTURACION)),
):
    """Total por cobrar, agrupado por cliente -- para un dashboard rápido
    de cartera pendiente."""
    filas = db.execute(
        select(Operacion.cliente_id, Cliente.nombre, func.count(Pago.id), func.sum(Pago.monto))
        .select_from(Pago)
        .join(Operacion, Pago.operacion_id == Operacion.id)
        .join(Cliente, Operacion.cliente_id == Cliente.id)
        .where(Pago.estado == "pendiente_cobro")
        .group_by(Operacion.cliente_id, Cliente.nombre)
    ).all()

    por_cliente = [
        ResumenClientePendiente(
            cliente_id=cid, cliente_nombre=nombre, cantidad_pagos=cantidad, total_pendiente=float(total or 0)
        )
        for cid, nombre, cantidad, total in filas
    ]

    return ResumenFacturacion(
        total_pendiente=sum(c.total_pendiente for c in por_cliente),
        cantidad_pagos_pendientes=sum(c.cantidad_pagos for c in por_cliente),
        por_cliente=por_cliente,
    )


@router.patch("/pagos/{pago_id}/marcar-pagado", response_model=PagoOut)
def marcar_pagado(
    pago_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_FACTURACION)),
):
    """Cierra el ciclo de un pago a crédito cuando el cliente efectivamente paga."""
    pago = db.get(Pago, pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    if pago.estado != "pendiente_cobro":
        raise HTTPException(status_code=400, detail=f"Este pago ya está en estado '{pago.estado}', no 'pendiente_cobro'")

    pago.estado = "pagado"
    db.commit()
    db.refresh(pago)

    operacion = db.get(Operacion, pago.operacion_id)
    cliente = db.get(Cliente, operacion.cliente_id)
    return _pago_a_out(pago, cliente.id, cliente.nombre)