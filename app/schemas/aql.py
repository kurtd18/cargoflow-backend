import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator

from app.services.aql import AQL_VALORES_VALIDOS, NIVELES_INSPECCION_GENERAL

ITEMS_CHECKLIST = ("estado_fisico", "cantidades", "fechas_vencimiento")
SEVERIDADES_DEFECTO = {"critico", "mayor", "menor"}


class ChecklistItemIn(BaseModel):
    item: str
    conforme: bool
    cantidad: int = 0
    severidad: Optional[str] = None  # obligatorio si conforme=False

    @model_validator(mode="after")
    def _validar(self):
        if self.item not in ITEMS_CHECKLIST:
            raise ValueError(f"item debe ser uno de: {', '.join(ITEMS_CHECKLIST)}")
        if not self.conforme:
            if self.severidad not in SEVERIDADES_DEFECTO:
                raise ValueError(f"severidad debe ser uno de: {', '.join(sorted(SEVERIDADES_DEFECTO))} cuando conforme=False")
            if self.cantidad < 1:
                raise ValueError("cantidad debe ser al menos 1 cuando conforme=False")
        return self


class InspeccionAQLCreate(BaseModel):
    operacion_id: Optional[uuid.UUID] = None
    proveedor_id: uuid.UUID
    tamano_lote: int
    nivel_inspeccion_general: str = "II"
    aql: float = 2.5
    checklist: list[ChecklistItemIn]

    @model_validator(mode="after")
    def _validar_rangos(self):
        if self.nivel_inspeccion_general not in NIVELES_INSPECCION_GENERAL:
            raise ValueError(f"nivel_inspeccion_general debe ser uno de: {', '.join(NIVELES_INSPECCION_GENERAL)}")
        if self.aql not in AQL_VALORES_VALIDOS:
            raise ValueError(f"aql debe ser uno de: {', '.join(str(v) for v in AQL_VALORES_VALIDOS)}")
        if self.tamano_lote < 2:
            raise ValueError("tamano_lote debe ser de al menos 2 unidades")
        if len(self.checklist) != len(ITEMS_CHECKLIST):
            raise ValueError(f"El checklist debe traer los {len(ITEMS_CHECKLIST)} ítems: {', '.join(ITEMS_CHECKLIST)}")
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
    defectos_criticos: int
    defectos_mayores: int
    defectos_menores: int
    resultado: str
    creado_por: uuid.UUID
    creado_en: datetime

    class Config:
        from_attributes = True


class PlanMuestreoOut(BaseModel):
    codigo_letra: str
    tamano_muestra: int
    limite_aceptacion: int
    limite_rechazo: int