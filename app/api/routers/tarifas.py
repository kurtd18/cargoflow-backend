import uuid
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.recursos import Tarifa
from app.schemas.recursos import TarifaCreate, TarifaOut, TarifaVencer

router = APIRouter(prefix="/tarifas", tags=["tarifas"])


def _condicion_null_segura(columna, valor):
    """Compara NULL-seguro: si valor es None, exige que la columna sea NULL;
    si no, exige igualdad exacta. Necesario porque cliente_id, categoria_mercancia
    y concepto son todos opcionales y '= NULL' en SQL nunca es verdadero."""
    return columna.is_(None) if valor is None else columna == valor


def _obtener_tarifa(db: Session, tarifa_id: uuid.UUID) -> Tarifa:
    tarifa = db.get(Tarifa, tarifa_id)
    if not tarifa:
        raise HTTPException(status_code=404, detail="Tarifa no encontrada")
    return tarifa


@router.post("", response_model=TarifaOut, status_code=status.HTTP_201_CREATED)
def crear_tarifa(
    payload: TarifaCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    """Crea una nueva tarifa vigente. Se cierra automáticamente la anterior
    SOLO si coincide exactamente en cliente_id (o ambas son generales),
    servicio, criterio, categoria_mercancia y concepto -- así una tarifa
    general y una especial para un cliente puntual, o una tarifa de
    'viveres' y otra de 'fruver', nunca se pisan entre sí."""
    vigente_desde = payload.vigente_desde or date.today()

    filtros = [
        Tarifa.servicio_id == payload.servicio_id,
        Tarifa.criterio == payload.criterio,
        Tarifa.vigente_hasta.is_(None),
        _condicion_null_segura(Tarifa.cliente_id, payload.cliente_id),
        _condicion_null_segura(Tarifa.categoria_mercancia, payload.categoria_mercancia),
        _condicion_null_segura(Tarifa.concepto, payload.concepto),
    ]
    if payload.criterio == "vehiculo":
        filtros.append(_condicion_null_segura(Tarifa.tipo_vehiculo_id, payload.tipo_vehiculo_id))

    tarifa_anterior = db.scalars(select(Tarifa).where(*filtros)).first()
    if tarifa_anterior:
        tarifa_anterior.vigente_hasta = vigente_desde - timedelta(days=1)

    nueva = Tarifa(
        empresa_id=current_user.empresa_id,
        cliente_id=payload.cliente_id,
        servicio_id=payload.servicio_id,
        criterio=payload.criterio,
        valor=payload.valor,
        tipo_vehiculo_id=payload.tipo_vehiculo_id,
        categoria_mercancia=payload.categoria_mercancia,
        concepto=payload.concepto,
        vigente_desde=vigente_desde,
        vigente_hasta=None,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("", response_model=list[TarifaOut])
def listar_tarifas(
    cliente_id: Optional[uuid.UUID] = None,
    servicio_id: Optional[uuid.UUID] = None,
    categoria_mercancia: Optional[str] = None,
    solo_vigentes: bool = True,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    """Si se pasa cliente_id, devuelve tanto las tarifas específicas de ESE
    cliente como las tarifas generales (cliente_id NULL) -- el consumidor
    (la app) debe preferir la específica si hay ambas para la misma
    combinación de servicio/criterio/categoría."""
    query = select(Tarifa)
    if cliente_id:
        query = query.where(or_(Tarifa.cliente_id == cliente_id, Tarifa.cliente_id.is_(None)))
    if servicio_id:
        query = query.where(Tarifa.servicio_id == servicio_id)
    if categoria_mercancia:
        query = query.where(Tarifa.categoria_mercancia == categoria_mercancia)
    if solo_vigentes:
        query = query.where(Tarifa.vigente_hasta.is_(None))
    return db.scalars(query.order_by(Tarifa.vigente_desde.desc())).all()


@router.get("/{tarifa_id}", response_model=TarifaOut)
def consultar_tarifa(
    tarifa_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    return _obtener_tarifa(db, tarifa_id)


@router.patch("/{tarifa_id}/vencer", response_model=TarifaOut)
def vencer_tarifa(
    tarifa_id: uuid.UUID,
    payload: TarifaVencer,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    tarifa = _obtener_tarifa(db, tarifa_id)
    if tarifa.vigente_hasta is not None:
        raise HTTPException(status_code=400, detail="Esta tarifa ya tiene fecha de vencimiento")
    tarifa.vigente_hasta = payload.vigente_hasta or date.today()
    db.commit()
    db.refresh(tarifa)
    return tarifa