import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator

from app.services.aql import AQL_VALORES_VALIDOS, NIVELES_INSPECCION_GENERAL


class InspeccionAQLCreate(BaseModel):
    operacion_id: Optional[uuid.UUID] = None
    proveedor_id: uuid.UUID
    tamano_lote: int
    nivel_inspeccion_general: str = "II"
    aql: float = 2.5
    defectos_encontrados: int

    @model_validator(mode="after")
    def _validar_rangos(self):
        if self.nivel_inspeccion_general not in NIVELES_INSPECCION_GENERAL:
            raise ValueError(f"nivel_inspeccion_general debe ser uno de: {', '.join(NIVELES_INSPECCION_GENERAL)}")
        if self.aql not in AQL_VALORES_VALIDOS:
            raise ValueError(f"aql debe ser uno de: {', '.join(str(v) for v in AQL_VALORES_VALIDOS)}")
        if self.tamano_lote < 2:
            raise ValueError("tamano_lote debe ser de al menos 2 unidades")
        if self.defectos_encontrados < 0:
            raise ValueError("defectos_encontrados no puede ser negativo")
        return self


class InspeccionAQLOut(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    operacion_id: Optional[uuid.UUID]
    proveedor_id: uuid.UUID
    tamano_lote: int
    nivel_inspeccion_general: str
    aql: float
    severidad: str
    codigo_letra: str
    tamano_muestra: int
    limite_aceptacion: int
    limite_rechazo: int
    defectos_encontrados: int
    resultado: str
    creado_por: uuid.UUID
    creado_en: datetime

    class Config:
        from_attributes = True


class PlanMuestreoOut(BaseModel):
    """Respuesta de la calculadora (GET /aql/plan) -- para previsualizar el
    plan de muestreo antes de registrar una inspección real."""

    codigo_letra: str
    tamano_muestra: int
    limite_aceptacion: int
    limite_rechazo: int