import uuid
from typing import Optional

from pydantic import BaseModel


class ProveedorCreate(BaseModel):
    nombre: str
    nit: Optional[str] = None


class ProveedorOut(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    nombre: str
    nit: Optional[str]
    nivel_riesgo: str
    nivel_inspeccion_actual: str

    class Config:
        from_attributes = True


class MuestraAQLOut(BaseModel):
    severidad_actual: str
    codigo_letra: str
    tamano_muestra: int
    limite_aceptacion: int
    limite_rechazo: int