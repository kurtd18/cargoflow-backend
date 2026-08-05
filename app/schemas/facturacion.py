import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PagoOut(BaseModel):
    id: uuid.UUID
    operacion_id: uuid.UUID
    cliente_id: uuid.UUID
    cliente_nombre: str
    forma_pago: str
    medio_pago: Optional[str]
    monto: float
    estado: str
    creado_en: datetime


class ResumenClientePendiente(BaseModel):
    cliente_id: uuid.UUID
    cliente_nombre: str
    cantidad_pagos: int
    total_pendiente: float


class ResumenFacturacion(BaseModel):
    total_pendiente: float
    cantidad_pagos_pendientes: int
    por_cliente: list[ResumenClientePendiente]