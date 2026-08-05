import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OperacionCreate(BaseModel):
    cliente_id: uuid.UUID
    servicio_id: uuid.UUID
    vehiculo_id: Optional[uuid.UUID] = None
    muelle: Optional[str] = None


class OperacionAsignar(BaseModel):
    cuadrilla_id: uuid.UUID
    tarifa_id: uuid.UUID
    criterio_cobro: str  # cajas | unidades | vehiculo
    cantidad_estimada: Optional[float] = None


class OperacionCerrar(BaseModel):
    cantidad_real: float
    forma_pago: str  # contado | credito
    medio_pago: Optional[str] = None


class OperacionOut(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    cliente_id: uuid.UUID
    estado: str
    criterio_cobro: Optional[str]
    cantidad_estimada: Optional[float]
    cantidad_real: Optional[float]
    hora_inicio: Optional[datetime]
    hora_fin: Optional[datetime]

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