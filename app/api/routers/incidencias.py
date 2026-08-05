import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.operaciones import Incidencia, Operacion
from app.schemas.operaciones import IncidenciaOut
from app.storage.incidencias import guardar_foto_incidencia

router = APIRouter(prefix="/operaciones", tags=["incidencias"])

# tipo libre a propósito (como en evidencias): reportar una incidencia nueva
# no debería requerir una migración de esquema.
TIPOS_INCIDENCIA_SUGERIDOS = {
    "mercancia_danada", "faltante", "retraso", "accidente",
    "problema_vehiculo", "conflicto_personal", "otro",
}


def _obtener_operacion(db: Session, operacion_id: uuid.UUID) -> Operacion:
    operacion = db.get(Operacion, operacion_id)
    if not operacion:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    return operacion


@router.post("/{operacion_id}/incidencias", response_model=IncidenciaOut, status_code=status.HTTP_201_CREATED)
async def reportar_incidencia(
    operacion_id: uuid.UUID,
    tipo: str = Form(...),
    descripcion: Optional[str] = Form(None),
    archivo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    """Reporta una incidencia sobre una operación. La foto es opcional
    (Incidencia.foto_url es nullable en el modelo) — a diferencia de las
    evidencias, una incidencia se puede registrar solo con descripción.
    """
    _obtener_operacion(db, operacion_id)

    foto_url = None
    if archivo is not None:
        try:
            foto_url = await guardar_foto_incidencia(archivo, operacion_id=operacion_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e))

    incidencia = Incidencia(
        operacion_id=operacion_id,
        tipo=tipo,
        descripcion=descripcion,
        foto_url=foto_url,
        creado_por=current_user.usuario_id,
    )
    db.add(incidencia)
    db.commit()
    db.refresh(incidencia)
    return incidencia


@router.get("/{operacion_id}/incidencias", response_model=list[IncidenciaOut])
def listar_incidencias(
    operacion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    _obtener_operacion(db, operacion_id)
    return db.scalars(
        select(Incidencia).where(Incidencia.operacion_id == operacion_id).order_by(Incidencia.creado_en.desc())
    ).all()