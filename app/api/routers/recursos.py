from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.recursos import Cuadrilla, Servicio, TipoVehiculo
from app.schemas.recursos import (
    CuadrillaCreate, CuadrillaOut, ServicioCreate, ServicioOut, TipoVehiculoCreate, TipoVehiculoOut,
)

router = APIRouter(tags=["recursos"])


@router.post("/servicios", response_model=ServicioOut, status_code=status.HTTP_201_CREATED)
def crear_servicio(
    payload: ServicioCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    servicio = Servicio(empresa_id=current_user.empresa_id, nombre=payload.nombre)
    db.add(servicio)
    db.commit()
    db.refresh(servicio)
    return servicio


@router.get("/servicios", response_model=list[ServicioOut])
def listar_servicios(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    return db.scalars(select(Servicio).order_by(Servicio.nombre)).all()


@router.post("/cuadrillas", response_model=CuadrillaOut, status_code=status.HTTP_201_CREATED)
def crear_cuadrilla(
    payload: CuadrillaCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    cuadrilla = Cuadrilla(empresa_id=current_user.empresa_id, nombre=payload.nombre, estado="disponible")
    db.add(cuadrilla)
    db.commit()
    db.refresh(cuadrilla)
    return cuadrilla


@router.get("/cuadrillas", response_model=list[CuadrillaOut])
def listar_cuadrillas(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    query = select(Cuadrilla)
    if estado:
        query = query.where(Cuadrilla.estado == estado)
    return db.scalars(query.order_by(Cuadrilla.nombre)).all()


@router.post("/tipos-vehiculo", response_model=TipoVehiculoOut, status_code=status.HTTP_201_CREATED)
def crear_tipo_vehiculo(
    payload: TipoVehiculoCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    tipo = TipoVehiculo(empresa_id=current_user.empresa_id, nombre=payload.nombre, tarifa_base=payload.tarifa_base)
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return tipo


@router.get("/tipos-vehiculo", response_model=list[TipoVehiculoOut])
def listar_tipos_vehiculo(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    return db.scalars(select(TipoVehiculo).order_by(TipoVehiculo.nombre)).all()