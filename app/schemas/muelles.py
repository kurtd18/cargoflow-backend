import uuid
from typing import Optional

from pydantic import BaseModel


class MuelleEstado(BaseModel):
    muelle: str
    disponible: bool
    operacion_id: Optional[uuid.UUID] = None
    cliente_nombre: Optional[str] = None