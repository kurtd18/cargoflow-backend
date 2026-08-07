import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator

CATEGORIAS_MERCANCIA_VALIDAS = {"viveres", "electro", "fruver"}


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OperacionCreate(BaseModel):
    cliente_id: uuid.UUID
    servicio_id: uuid.UUID
    proveedor_id: Optional[uuid.UUID] = None
    vehiculo_id: Optional[uuid.UUID] = None
    muelle: Optional[str] = None
    categoria_mercancia: Optional[str] = None

    @model_validator(mode="after")
    def _validar_categoria(self):
        if self.categoria_mercancia is not None and self.categoria_mercancia not in CATEGORIAS_MERCANCIA_VALIDAS:
            raise ValueError(f"categoria_mercancia debe ser uno de: {', '.join(sorted(CATEGORIAS_MERCANCIA_VALIDAS))}")
        return self


class OperacionAsignar(BaseModel):
    cuadrilla_id: uuid.UUID
    tarifa_id: Optional[uuid.UUID] = None
    criterio_cobro: Optional[str] = None
    cantidad_estimada: Optional[float] = None


class OperacionActualizarCantidad(BaseModel):
    cantidad_real: float


class OperacionCerrar(BaseModel):
    cantidad_real: Optional[float] = None
    forma_pago: str
    medio_pago: Optional[str] = None


class OperacionOut(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    cliente_id: uuid.UUID
    proveedor_id: Optional[uuid.UUID] = None
    estado: str
    criterio_cobro: Optional[str]
    cantidad_estimada: Optional[float]
    cantidad_real: Optional[float]
    categoria_mercancia: Optional[str]
    hora_inicio: Optional[datetime]
    hora_fin: Optional[datetime]

    class Config:
        from_attributes = True


class LineaCobroCreate(BaseModel):
    tarifa_id: uuid.UUID
    cantidad_estimada: Optional[float] = None


class LineaCobroActualizarCantidad(BaseModel):
    cantidad_real: float


class LineaCobroOut(BaseModel):
    id: uuid.UUID
    operacion_id: uuid.UUID
    tarifa_id: uuid.UUID
    cantidad_estimada: Optional[float]
    cantidad_real: Optional[float]
    creado_en: datetime

    class Config:
        from_attributes = True


class EvidenciaOut(BaseModel):
    id: uuid.UUID
    operacion_id: uuid.UUID
    tipo: str
    url_archivo: str
    creado_en: datetime

    class Config:
        from_attributes = True


class EvidenciasEstado(BaseModel):
    tipos_requeridos: list[str]
    tipos_presentes: list[str]
    tipos_faltantes: list[str]


class IncidenciaCreate(BaseModel):
    tipo: str
    descripcion: Optional[str] = None


class IncidenciaOut(BaseModel):
    id: uuid.UUID
    operacion_id: uuid.UUID
    tipo: str
    descripcion: Optional[str]
    foto_url: Optional[str]
    creado_por: uuid.UUID
    creado_en: datetime

    class Config:
        from_attributes = True