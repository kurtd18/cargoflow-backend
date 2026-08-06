import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, require_roles, CurrentUser
from app.models.operaciones import Operacion, Evidencia, Pago, Liquidacion, LineaCobro
from app.models.recursos import Tarifa
from app.models.plataforma import Cliente
from app.schemas.operaciones import (
    OperacionCreate, OperacionAsignar, OperacionActualizarCantidad, OperacionCerrar, OperacionOut,
    LineaCobroCreate, LineaCobroActualizarCantidad, LineaCobroOut,
)

router = APIRouter(prefix="/operaciones", tags=["operaciones"])

TIPOS_EVIDENCIA_OBLIGATORIOS = {"pedido", "factura"}
ROLES_OPERACION = ("supervisor", "operario")


def _obtener_operacion(db: Session, operacion_id: uuid.UUID) -> Operacion:
    operacion = db.get(Operacion, operacion_id)
    if not operacion:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    return operacion


def _calcular_valor(tarifa: Tarifa, cantidad_real: float) -> float:
    """criterio='vehiculo': tarifa plana por todo el vehículo, no se
    multiplica por la cantidad de cajas/unidades manejadas -- esa cantidad
    se sigue registrando (para AQL y productividad), simplemente no entra
    en el cálculo del cobro cuando el criterio es por vehículo."""
    if tarifa.criterio == "vehiculo":
        return float(tarifa.valor)
    return float(cantidad_real) * float(tarifa.valor)


@router.post("", response_model=OperacionOut, status_code=status.HTTP_201_CREATED)
def crear_operacion(
    payload: OperacionCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente", "operario")),
):
    """UX Spec 4.1.1 — Crear operación."""
    operacion = Operacion(
        empresa_id=current_user.empresa_id,
        cliente_id=payload.cliente_id,
        servicio_id=payload.servicio_id,
        vehiculo_id=payload.vehiculo_id,
        muelle=payload.muelle,
        categoria_mercancia=payload.categoria_mercancia,
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
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente", "operario")),
):
    return _obtener_operacion(db, operacion_id)


@router.patch("/{operacion_id}/asignar", response_model=OperacionOut)
def asignar_cuadrilla_y_tarifa(
    operacion_id: uuid.UUID,
    payload: OperacionAsignar,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_OPERACION)),
):
    operacion = _obtener_operacion(db, operacion_id)

    operacion.cuadrilla_id = payload.cuadrilla_id
    if payload.tarifa_id is not None:
        operacion.tarifa_id = payload.tarifa_id
        operacion.criterio_cobro = payload.criterio_cobro
        operacion.cantidad_estimada = payload.cantidad_estimada
    operacion.estado = "asignada"
    db.commit()
    db.refresh(operacion)
    return operacion


@router.post("/{operacion_id}/lineas", response_model=LineaCobroOut, status_code=status.HTTP_201_CREATED)
def agregar_linea_cobro(
    operacion_id: uuid.UUID,
    payload: LineaCobroCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_OPERACION)),
):
    operacion = _obtener_operacion(db, operacion_id)
    if operacion.estado not in ("asignada", "en_curso"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede agregar una línea de cobro en estado '{operacion.estado}'",
        )
    tarifa = db.get(Tarifa, payload.tarifa_id)
    if not tarifa:
        raise HTTPException(status_code=404, detail="Tarifa no encontrada")

    linea = LineaCobro(
        empresa_id=current_user.empresa_id,
        operacion_id=operacion_id,
        tarifa_id=payload.tarifa_id,
        cantidad_estimada=payload.cantidad_estimada,
    )
    db.add(linea)
    db.commit()
    db.refresh(linea)
    return linea


@router.get("/{operacion_id}/lineas", response_model=list[LineaCobroOut])
def listar_lineas_cobro(
    operacion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente", "operario")),
):
    _obtener_operacion(db, operacion_id)
    return db.scalars(
        select(LineaCobro).where(LineaCobro.operacion_id == operacion_id).order_by(LineaCobro.creado_en)
    ).all()


@router.patch("/{operacion_id}/lineas/{linea_id}/cantidad", response_model=LineaCobroOut)
def actualizar_cantidad_linea(
    operacion_id: uuid.UUID,
    linea_id: uuid.UUID,
    payload: LineaCobroActualizarCantidad,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_OPERACION)),
):
    linea = db.get(LineaCobro, linea_id)
    if not linea or linea.operacion_id != operacion_id:
        raise HTTPException(status_code=404, detail="Línea de cobro no encontrada")
    linea.cantidad_real = payload.cantidad_real
    db.commit()
    db.refresh(linea)
    return linea


@router.post("/{operacion_id}/iniciar", response_model=OperacionOut)
def iniciar_operacion(
    operacion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_OPERACION)),
):
    operacion = _obtener_operacion(db, operacion_id)

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


@router.patch("/{operacion_id}/cantidad", response_model=OperacionOut)
def actualizar_cantidad(
    operacion_id: uuid.UUID,
    payload: OperacionActualizarCantidad,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_OPERACION)),
):
    operacion = _obtener_operacion(db, operacion_id)
    if operacion.estado != "en_curso":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede actualizar la cantidad en estado '{operacion.estado}'; debe estar en_curso",
        )
    operacion.cantidad_real = payload.cantidad_real
    db.commit()
    db.refresh(operacion)
    return operacion


@router.post("/{operacion_id}/cerrar", response_model=OperacionOut)
def cerrar_operacion(
    operacion_id: uuid.UUID,
    payload: OperacionCerrar,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente")),
):
    """Cerrar implica confirmar forma de pago -- se deja restringido a
    supervisor/gerente, no a operario."""
    operacion = _obtener_operacion(db, operacion_id)
    if operacion.estado != "en_curso":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede cerrar una operación en estado '{operacion.estado}'; debe estar en_curso",
        )

    if payload.forma_pago == "credito":
        cliente = db.get(Cliente, operacion.cliente_id)
        if not cliente or cliente.condicion_pago != "credito":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este cliente no está registrado con condición de crédito",
            )

    lineas = db.scalars(select(LineaCobro).where(LineaCobro.operacion_id == operacion_id)).all()

    if lineas:
        valor_total = 0.0
        for linea in lineas:
            if linea.cantidad_real is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Falta registrar cantidad_real en la línea {linea.id} antes de cerrar",
                )
            tarifa = db.get(Tarifa, linea.tarifa_id)
            valor_calculado = _calcular_valor(tarifa, linea.cantidad_real)
            valor_total += valor_calculado
            db.add(Liquidacion(
                operacion_id=operacion.id,
                tarifa_id=tarifa.id,
                cantidad_real=linea.cantidad_real,
                valor_calculado=valor_calculado,
            ))
    else:
        if not operacion.tarifa_id:
            raise HTTPException(status_code=400, detail="La operación no tiene tarifa asignada")
        if payload.cantidad_real is None:
            raise HTTPException(
                status_code=400,
                detail="cantidad_real es obligatoria para cerrar una operación sin líneas de cobro",
            )
        tarifa = db.get(Tarifa, operacion.tarifa_id)
        valor_total = _calcular_valor(tarifa, payload.cantidad_real)
        operacion.cantidad_real = payload.cantidad_real
        db.add(Liquidacion(
            operacion_id=operacion.id,
            tarifa_id=tarifa.id,
            cantidad_real=payload.cantidad_real,
            valor_calculado=valor_total,
        ))

    operacion.estado = "finalizada"
    operacion.hora_fin = datetime.now(timezone.utc)

    db.add(Pago(
        operacion_id=operacion.id,
        forma_pago=payload.forma_pago,
        medio_pago=payload.medio_pago,
        monto=valor_total,
        estado="pendiente_cobro" if payload.forma_pago == "credito" else "pagado",
    ))
    db.commit()
    db.refresh(operacion)
    return operacion