import uuid
from typing import Optional

from pydantic import BaseModel, model_validator

CONDICIONES_PAGO_VALIDAS = {"contado", "credito"}


class ClienteCreate(BaseModel):
    nombre: str
    nit: Optional[str] = None
    condicion_pago: str = "contado"
    cupo_credito: Optional[float] = None

    @model_validator(mode="after")
    def _validar_condicion_pago(self):
        if self.condicion_pago not in CONDICIONES_PAGO_VALIDAS:
            raise ValueError(f"condicion_pago debe ser uno de: {', '.join(sorted(CONDICIONES_PAGO_VALIDAS))}")
        return self


class ClienteOut(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    nombre: str
    nit: Optional[str]
    condicion_pago: str
    cupo_credito: Optional[float]
    activo: bool

    class Config:
        from_attributes = True


class UsuarioClienteCreate(BaseModel):
    """Credencial de acceso al Portal del Cliente."""
    nombre: str
    email: str
    password: str


class UsuarioClienteOut(BaseModel):
    id: uuid.UUID
    nombre: str
    email: str
    cliente_id: uuid.UUID
    activo: bool

    class Config:
        from_attributes = True