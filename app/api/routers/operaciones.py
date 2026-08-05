import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, require_roles, CurrentUser
from app.models.operaciones import Operacion, Evidencia, Pago, Liquidacion
from app.models.recursos import Tarifa
from app.models.plataforma import Cliente
from app.schemas.operaciones import OperacionCreate, OperacionAsignar, OperacionCerrar, OperacionOut

router = APIRouter(prefix="/operaciones", tags=["operaciones"])

TIPOS_EVIDENCIA_OBLIGATORIOS = {"pedido", "factura"}


@router.post("", response_model=OperacionOut, status_code=status.HTTP_201_CREATED)
def crear_operacion(
    payload: OperacionCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    """UX Spec 4.1.1 — Crear operación."""
    operacion = Operacion(
        empresa_id=current_user.empresa_id,
        cliente_id=payload.cliente_id,
        servicio_id=payload.servicio_id,
        vehiculo_id=payload.vehiculo_id,
        muelle=payload.muelle,
        estado="creada",
        creado_por=current_user.usuario_id,
    )
    db.add(operacion)
    db.commit()
    db.refresh(operacion)
    return operacion


@router.get("/{operacion_id}", response_model=OperacionOut)
def consultar_operacion(
    operacion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    """Consulta el estado actual de una operación."""
    operacion = db.get(Operacion, operacion_id)
    if not operacion:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    return operacion


@router.patch("/{operacion_id}/asignar", response_model=OperacionOut)
def asignar_cuadrilla_y_tarifa(
    operacion_id: uuid.UUID,
    payload: OperacionAsignar,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor")),
):
    """UX Spec 4.1.2 — Asignar cuadrilla y tarifa.

    Regla de negocio: cantidad_estimada es solo referencial (PRD Sección 4.1);
    nunca se usa para liquidar. Se guarda únicamente para mostrarla como
    proyección en la pantalla "Operación en curso".
    """
    operacion = db.get(Operacion, operacion_id)
    if not operacion:
        raise HTTPException(status_code=404, detail="Operación no encontrada")

    operacion.cuadrilla_id = payload.cuadrilla_id
    operacion.tarifa_id = payload.tarifa_id
    operacion.criterio_cobro = payload.criterio_cobro
    operacion.cantidad_estimada = payload.cantidad_estimada
    operacion.estado = "asignada"
    db.commit()
    db.refresh(operacion)
    return operacion


@router.post("/{operacion_id}/iniciar", response_model=OperacionOut)
def iniciar_operacion(
    operacion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor")),
):
    """UX Spec 4.1.2 — el botón "Iniciar operación" exige que ya existan
    las evidencias obligatorias de pedido y factura (regla transversal, UX Spec Sección 5).
    """
    operacion = db.get(Operacion, operacion_id)
    if not operacion:
        raise HTTPException(status_code=404, detail="Operación no encontrada")

    tipos_cargados = {
        e.tipo for e in db.scalars(select(Evidencia).where(Evidencia.operacion_id == operacion_id))
    }
    faltantes = TIPOS_EVIDENCIA_OBLIGATORIOS - tipos_cargados
    if faltantes:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f"Faltan evidencias obligatorias antes de iniciar: {', '.join(sorted(faltantes))}",
        )

    operacion.estado = "en_curso"
    operacion.hora_inicio = datetime.now(timezone.utc)
    db.commit()
    db.refresh(operacion)
    return operacion


@router.post("/{operacion_id}/cerrar", response_model=OperacionOut)
def cerrar_operacion(
    operacion_id: uuid.UUID,
    payload: OperacionCerrar,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor")),
):
    """UX Spec 4.1.5 — Cerrar operación.

    Regla de negocio central (PRD Sección 4.1 y 4.4, confirmada en el chat de diseño):
    la liquidación SIEMPRE se calcula con cantidad_real, nunca con cantidad_estimada.
    La forma de pago a crédito solo es válida si el cliente está registrado como tal.

    Solo se puede cerrar una operación que ya está en_curso (fue iniciada) —
    no se puede cerrar una operación creada/asignada que nunca arrancó.
    """
    operacion = db.get(Operacion, operacion_id)
    if not operacion:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    if operacion.estado != "en_curso":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede cerrar una operación en estado '{operacion.estado}'; debe estar en_curso",
        )
    if not operacion.tarifa_id:
        raise HTTPException(status_code=400, detail="La operación no tiene tarifa asignada")

    if payload.forma_pago == "credito":
        cliente = db.get(Cliente, operacion.cliente_id)
        if not cliente or cliente.condicion_pago != "credito":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este cliente no está registrado con condición de crédito",
            )

    operacion.cantidad_real = payload.cantidad_real
    operacion.estado = "finalizada"
    operacion.hora_fin = datetime.now(timezone.utc)

    tarifa = db.get(Tarifa, operacion.tarifa_id)
    valor_calculado = float(payload.cantidad_real) * float(tarifa.valor)

    liquidacion = Liquidacion(
        operacion_id=operacion.id,
        tarifa_id=tarifa.id,
        cantidad_real=payload.cantidad_real,
        valor_calculado=valor_calculado,
    )
    pago = Pago(
        operacion_id=operacion.id,
        forma_pago=payload.forma_pago,
        medio_pago=payload.medio_pago,
        monto=valor_calculado,
        estado="pendiente_cobro" if payload.forma_pago == "credito" else "pagado",
    )
    db.add_all([liquidacion, pago])
    db.commit()
    db.refresh(operacion)
    return operacion