from datetime import date, datetime, time, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.calidad import InspeccionAQL
from app.models.operaciones import Liquidacion, Operacion, Pago
from app.models.plataforma import Proveedor
from app.schemas.reportes import CalidadResumen, DashboardOut, FinancieroResumen, OperacionesResumen

router = APIRouter(prefix="/reportes", tags=["reportes"])

ROLES_REPORTES = ("gerente", "administrador")


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    desde: Optional[date] = Query(None, description="Por defecto, hoy"),
    hasta: Optional[date] = Query(None, description="Por defecto, hoy"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_REPORTES)),
):
    """Resumen del período [desde, hasta] -- si no se especifican fechas,
    muestra solo el día de hoy. Para un histórico completo, pasa un rango
    amplio (ej. desde=2020-01-01)."""
    hoy = datetime.now(timezone.utc).date()
    desde = desde or hoy
    hasta = hasta or hoy
    inicio = datetime.combine(desde, time.min, tzinfo=timezone.utc)
    fin = datetime.combine(hasta, time.max, tzinfo=timezone.utc)

    filtro_operacion = Operacion.creado_en.between(inicio, fin)
    filtro_aql = InspeccionAQL.creado_en.between(inicio, fin)
    filtro_liquidacion = Liquidacion.creado_en.between(inicio, fin)
    filtro_pago = Pago.creado_en.between(inicio, fin)

    filas_estado = db.execute(
        select(Operacion.estado, func.count(Operacion.id)).where(filtro_operacion).group_by(Operacion.estado)
    ).all()
    por_estado = {estado: cantidad for estado, cantidad in filas_estado}
    total_operaciones = sum(por_estado.values())

    duracion_ciclo_seg = db.execute(
        select(func.avg(func.extract("epoch", Operacion.hora_fin - Operacion.creado_en)))
        .where(filtro_operacion, Operacion.hora_fin.is_not(None))
    ).scalar()

    duracion_operativa_seg = db.execute(
        select(func.avg(func.extract("epoch", Operacion.hora_fin - Operacion.hora_inicio)))
        .where(filtro_operacion, Operacion.hora_fin.is_not(None), Operacion.hora_inicio.is_not(None))
    ).scalar()

    total_inspecciones = db.execute(select(func.count(InspeccionAQL.id)).where(filtro_aql)).scalar() or 0
    aceptadas = db.execute(
        select(func.count(InspeccionAQL.id)).where(filtro_aql, InspeccionAQL.resultado == "aceptado")
    ).scalar() or 0
    tasa_aceptacion = (aceptadas / total_inspecciones * 100) if total_inspecciones else None

    # proveedores_en_reforzado: estado ACTUAL (no tiene sentido filtrarlo por fecha)
    proveedores_reforzado = db.execute(
        select(func.count(Proveedor.id)).where(Proveedor.nivel_inspeccion_actual == "reforzado")
    ).scalar() or 0

    total_liquidado = db.execute(select(func.sum(Liquidacion.valor_calculado)).where(filtro_liquidacion)).scalar()
    total_pendiente = db.execute(
        select(func.sum(Pago.monto)).where(filtro_pago, Pago.estado == "pendiente_cobro")
    ).scalar()

    return DashboardOut(
        operaciones=OperacionesResumen(
            total=total_operaciones,
            por_estado=por_estado,
            tiempo_promedio_ciclo_minutos=round(duracion_ciclo_seg / 60, 1) if duracion_ciclo_seg is not None else None,
            tiempo_promedio_operativo_minutos=round(duracion_operativa_seg / 60, 1) if duracion_operativa_seg is not None else None,
        ),
        calidad=CalidadResumen(
            total_inspecciones=total_inspecciones,
            tasa_aceptacion_pct=round(tasa_aceptacion, 1) if tasa_aceptacion is not None else None,
            proveedores_en_reforzado=proveedores_reforzado,
        ),
        financiero=FinancieroResumen(
            total_liquidado_historico=float(total_liquidado or 0),
            total_pendiente_cobro=float(total_pendiente or 0),
        ),
    )