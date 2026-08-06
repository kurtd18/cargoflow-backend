from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.recursos import Cuadrilla, Servicio
from app.schemas.recursos import CuadrillaOut, ServicioOut

router = APIRouter(tags=["recursos"])


@router.get("/servicios", response_model=list[ServicioOut])
def listar_servicios(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    return db.scalars(select(Servicio).order_by(Servicio.nombre)).all()


@router.get("/cuadrillas", response_model=list[CuadrillaOut])
def listar_cuadrillas(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    return db.scalars(select(Cuadrilla).order_by(Cuadrilla.nombre)).all()