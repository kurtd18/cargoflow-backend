import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.api.routers.operaciones import TIPOS_EVIDENCIA_OBLIGATORIOS
from app.models.operaciones import Evidencia, Operacion
from app.schemas.operaciones import EvidenciaOut, EvidenciasEstado
from app.storage.evidencias import guardar_archivo_evidencia

router = APIRouter(prefix="/operaciones", tags=["evidencias"])

# Lista completa según el comentario de Evidencia.tipo en app/models/operaciones.py.
# Solo 'pedido' y 'factura' (TIPOS_EVIDENCIA_OBLIGATORIOS, importado de operaciones.py)
# bloquean hoy el botón de iniciar — los demás son evidencia informativa.
TIPOS_EVIDENCIA_VALIDOS = {
    "foto_llegada", "pedido", "factura", "foto_operacion", "firma_cliente",
    "soporte_pago", "foto_conductor", "foto_vehiculo", "evidencia_defecto_aql",
}


def _obtener_operacion(db: Session, operacion_id: uuid.UUID) -> Operacion:
    operacion = db.get(Operacion, operacion_id)
    if not operacion:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    return operacion


@router.post("/{operacion_id}/evidencias", response_model=EvidenciaOut, status_code=status.HTTP_201_CREATED)
async def subir_evidencia(
    operacion_id: uuid.UUID,
    tipo: str = Form(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor")),
):
    """Sube una evidencia (foto/documento) asociada a una operación."""
    _obtener_operacion(db, operacion_id)

    if tipo not in TIPOS_EVIDENCIA_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tipo de evidencia no reconocido: {tipo}",
        )

    try:
        ruta = await guardar_archivo_evidencia(archivo, operacion_id=operacion_id, tipo=tipo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e))

    evidencia = Evidencia(operacion_id=operacion_id, tipo=tipo, url_archivo=ruta)
    db.add(evidencia)
    db.commit()
    db.refresh(evidencia)
    return evidencia


@router.get("/{operacion_id}/evidencias", response_model=list[EvidenciaOut])
def listar_evidencias(
    operacion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    _obtener_operacion(db, operacion_id)
    return db.scalars(
        select(Evidencia).where(Evidencia.operacion_id == operacion_id).order_by(Evidencia.creado_en.desc())
    ).all()


@router.get("/{operacion_id}/evidencias/estado", response_model=EvidenciasEstado)
def estado_evidencias(
    operacion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    """Para que el frontend muestre qué falta antes de que el usuario
    choque con el 412 de /iniciar."""
    _obtener_operacion(db, operacion_id)
    presentes = {
        e.tipo for e in db.scalars(select(Evidencia).where(Evidencia.operacion_id == operacion_id))
    }
    faltantes = TIPOS_EVIDENCIA_OBLIGATORIOS - presentes
    return EvidenciasEstado(
        tipos_requeridos=sorted(TIPOS_EVIDENCIA_OBLIGATORIOS),
        tipos_presentes=sorted(presentes),
        tipos_faltantes=sorted(faltantes),
    )