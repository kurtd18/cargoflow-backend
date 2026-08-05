import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.calidad import InspeccionAQL
from app.models.plataforma import Proveedor
from app.schemas.aql import InspeccionAQLCreate, InspeccionAQLOut, PlanMuestreoOut
from app.services.aql import AQLError, calcular_plan_muestreo, evaluar_resultado, recalcular_severidad

router = APIRouter(prefix="/aql", tags=["aql"])

ROLES_AQL = ("supervisor", "gerente", "auditor")


@router.get("/plan", response_model=PlanMuestreoOut)
def calcular_plan(
    tamano_lote: int = Query(..., ge=2),
    nivel_inspeccion_general: str = Query("II"),
    aql: float = Query(2.5),
    current_user: CurrentUser = Depends(require_roles(*ROLES_AQL)),
):
    """Calculadora del plan de muestreo, sin persistir nada -- para
    previsualizar cuantas unidades hay que inspeccionar antes de hacerlo."""
    try:
        plan = calcular_plan_muestreo(tamano_lote, nivel_inspeccion_general, aql)
    except AQLError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return PlanMuestreoOut(
        codigo_letra=plan.codigo_letra,
        tamano_muestra=plan.tamano_muestra,
        limite_aceptacion=plan.limite_aceptacion,
        limite_rechazo=plan.limite_rechazo,
    )


@router.post("/inspecciones", response_model=InspeccionAQLOut, status_code=status.HTTP_201_CREATED)
def crear_inspeccion(
    payload: InspeccionAQLCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_AQL)),
):
    """Registra una inspeccion AQL real y actualiza automaticamente la
    severidad (normal/reforzado/reducido) del proveedor segun las reglas
    de cambio de la norma (ver app.services.aql.recalcular_severidad)."""
    proveedor = db.get(Proveedor, payload.proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    try:
        plan = calcular_plan_muestreo(payload.tamano_lote, payload.nivel_inspeccion_general, payload.aql)
        resultado = evaluar_resultado(payload.defectos_encontrados, plan.limite_aceptacion, plan.limite_rechazo)
    except AQLError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    inspeccion = InspeccionAQL(
        empresa_id=current_user.empresa_id,
        operacion_id=payload.operacion_id,
        proveedor_id=payload.proveedor_id,
        tamano_lote=payload.tamano_lote,
        nivel_inspeccion_general=payload.nivel_inspeccion_general,
        aql=payload.aql,
        severidad=proveedor.nivel_inspeccion_actual,
        codigo_letra=plan.codigo_letra,
        tamano_muestra=plan.tamano_muestra,
        limite_aceptacion=plan.limite_aceptacion,
        limite_rechazo=plan.limite_rechazo,
        defectos_encontrados=payload.defectos_encontrados,
        resultado=resultado,
        creado_por=current_user.usuario_id,
    )
    db.add(inspeccion)
    db.flush()

    historial = db.scalars(
        select(InspeccionAQL.resultado)
        .where(InspeccionAQL.proveedor_id == payload.proveedor_id)
        .order_by(InspeccionAQL.creado_en.desc())
    ).all()
    nueva_severidad = recalcular_severidad(list(historial), proveedor.nivel_inspeccion_actual)
    proveedor.nivel_inspeccion_actual = nueva_severidad
    proveedor.nivel_riesgo = "riesgoso" if nueva_severidad == "reforzado" else "confiable"

    db.commit()
    db.refresh(inspeccion)
    return inspeccion


@router.get("/inspecciones", response_model=list[InspeccionAQLOut])
def listar_inspecciones(
    proveedor_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_AQL)),
):
    query = select(InspeccionAQL)
    if proveedor_id:
        query = query.where(InspeccionAQL.proveedor_id == proveedor_id)
    return db.scalars(query.order_by(InspeccionAQL.creado_en.desc())).all()


@router.get("/inspecciones/{inspeccion_id}", response_model=InspeccionAQLOut)
def consultar_inspeccion(
    inspeccion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(*ROLES_AQL)),
):
    inspeccion = db.get(InspeccionAQL, inspeccion_id)
    if not inspeccion:
        raise HTTPException(status_code=404, detail="Inspección no encontrada")
    return inspeccion