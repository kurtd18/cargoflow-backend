import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, model_validator

CRITERIOS_VALIDOS = {"cajas", "unidades", "vehiculo"}


class TarifaCreate(BaseModel):
    cliente_id: uuid.UUID
    servicio_id: uuid.UUID
    criterio: str  # cajas | unidades | vehiculo
    valor: float
    tipo_vehiculo_id: Optional[uuid.UUID] = None
    vigente_desde: Optional[date] = None  # si no se envía, se usa hoy

    @model_validator(mode="after")
    def _validar_criterio_y_tipo_vehiculo(self):
        if self.criterio not in CRITERIOS_VALIDOS:
            raise ValueError(f"criterio debe ser uno de: {', '.join(sorted(CRITERIOS_VALIDOS))}")
        if self.criterio == "vehiculo" and self.tipo_vehiculo_id is None:
            raise ValueError("tipo_vehiculo_id es obligatorio cuando criterio es 'vehiculo'")
        return self


class TarifaVencer(BaseModel):
    vigente_hasta: Optional[date] = None  # si no se envía, se usa hoy


class TarifaOut(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    cliente_id: uuid.UUID
    servicio_id: uuid.UUID
    criterio: str
    valor: float
    tipo_vehiculo_id: Optional[uuid.UUID]
    vigente_desde: date
    vigente_hasta: Optional[date]

    class Config:
        from_attributes = True