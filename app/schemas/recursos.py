import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, model_validator

CRITERIOS_VALIDOS = {"cajas", "unidades", "vehiculo", "toneladas"}
CATEGORIAS_MERCANCIA_VALIDAS = {"viveres", "electro", "fruver"}


class TarifaCreate(BaseModel):
    cliente_id: Optional[uuid.UUID] = None  # None = tarifa general de la empresa
    servicio_id: uuid.UUID
    criterio: str
    valor: float
    tipo_vehiculo_id: Optional[uuid.UUID] = None
    categoria_mercancia: Optional[str] = None
    concepto: Optional[str] = None
    vigente_desde: Optional[date] = None

    @model_validator(mode="after")
    def _validar_criterio_y_tipo_vehiculo(self):
        if self.criterio not in CRITERIOS_VALIDOS:
            raise ValueError(f"criterio debe ser uno de: {', '.join(sorted(CRITERIOS_VALIDOS))}")
        if self.criterio == "vehiculo" and self.tipo_vehiculo_id is None:
            raise ValueError("tipo_vehiculo_id es obligatorio cuando criterio es 'vehiculo'")
        if self.categoria_mercancia is not None and self.categoria_mercancia not in CATEGORIAS_MERCANCIA_VALIDAS:
            raise ValueError(f"categoria_mercancia debe ser uno de: {', '.join(sorted(CATEGORIAS_MERCANCIA_VALIDAS))}")
        return self


class TarifaVencer(BaseModel):
    vigente_hasta: Optional[date] = None


class TarifaOut(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    cliente_id: Optional[uuid.UUID]
    servicio_id: uuid.UUID
    criterio: str
    valor: float
    tipo_vehiculo_id: Optional[uuid.UUID]
    categoria_mercancia: Optional[str]
    concepto: Optional[str]
    vigente_desde: date
    vigente_hasta: Optional[date]

    class Config:
        from_attributes = True


class ServicioCreate(BaseModel):
    nombre: str


class ServicioOut(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    nombre: str

    class Config:
        from_attributes = True


class CuadrillaCreate(BaseModel):
    nombre: str


class CuadrillaOut(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    nombre: str
    estado: str

    class Config:
        from_attributes = True


class TipoVehiculoCreate(BaseModel):
    nombre: str
    tarifa_base: float


class TipoVehiculoOut(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    nombre: str
    tarifa_base: float

    class Config:
        from_attributes = True