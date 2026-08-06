import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_cliente
from app.models.operaciones import Evidencia, Operacion, Pago
from app.models.plataforma import Cliente
from app.schemas.facturacion import PagoOut
from app.schemas.operaciones import EvidenciaOut, OperacionOut

router = APIRouter(prefix="/portal", tags=["portal-cliente"])


def _mi_operacion_o_404(db: Session, operacion_id: uuid.UUID, current_user: CurrentUser) -> Operacion:
    operacion = db.get(Operacion, operacion_id)
    if not operacion or operacion.cliente_id != uuid.UUID(current_user.cliente_id):
        # 404, no 403: no confirmamos si la operación existe pero es de otro cliente
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    return operacion


@router.get("/mis-operaciones", response_model=list[OperacionOut])
def mis_operaciones(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_cliente),
):
    """Solo devuelve las operaciones del cliente_id ligado a este login --
    nunca las de otros clientes de la misma empresa, aunque compartan tenant."""
    return db.scalars(
        select(Operacion)
        .where(Operacion.cliente_id == uuid.UUID(current_user.cliente_id))
        .order_by(Operacion.creado_en.desc())
    ).all()


@router.get("/mis-operaciones/{operacion_id}", response_model=OperacionOut)
def mi_operacion(
    operacion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_cliente),
):
    return _mi_operacion_o_404(db, operacion_id, current_user)


@router.get("/mis-operaciones/{operacion_id}/evidencias", response_model=list[EvidenciaOut])
def mis_evidencias(
    operacion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_cliente),
):
    """PRD 5.11: el cliente consulta las evidencias de sus propias
    operaciones, sin depender de que el operador se las envíe manualmente."""
    _mi_operacion_o_404(db, operacion_id, current_user)
    return db.scalars(
        select(Evidencia).where(Evidencia.operacion_id == operacion_id).order_by(Evidencia.creado_en.desc())
    ).all()


@router.get("/mis-operaciones/{operacion_id}/evidencias/{evidencia_id}/archivo")
def descargar_mi_evidencia(
    operacion_id: uuid.UUID,
    evidencia_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_cliente),
):
    """El cliente descarga el archivo real de una de sus propias evidencias."""
    _mi_operacion_o_404(db, operacion_id, current_user)
    evidencia = db.get(Evidencia, evidencia_id)
    if not evidencia or evidencia.operacion_id != operacion_id:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    ruta = Path(evidencia.url_archivo)
    if not ruta.exists():
        raise HTTPException(status_code=404, detail="El archivo ya no está disponible en el servidor")
    return FileResponse(ruta, filename=ruta.name)


@router.get("/mis-pagos", response_model=list[PagoOut])
def mis_pagos(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_cliente),
):
    cliente_id = uuid.UUID(current_user.cliente_id)
    cliente = db.get(Cliente, cliente_id)

    pagos = db.scalars(
        select(Pago)
        .join(Operacion, Pago.operacion_id == Operacion.id)
        .where(Operacion.cliente_id == cliente_id)
        .order_by(Pago.creado_en.desc())
    ).all()

    return [
        PagoOut(
            id=pago.id, operacion_id=pago.operacion_id, cliente_id=cliente_id,
            cliente_nombre=cliente.nombre, forma_pago=pago.forma_pago,
            medio_pago=pago.medio_pago, monto=float(pago.monto),
            estado=pago.estado, creado_en=pago.creado_en,
        )
        for pago in pagos
    ]