import uuid

from pydantic import BaseModel, model_validator

# Roles internos de la empresa (staff de CargoFlow). 'cliente' NO está aquí
# a propósito -- esos logins se crean con POST /clientes/{id}/usuarios.
ROLES_INTERNOS_VALIDOS = {"gerente", "administrador", "supervisor", "operario", "auditor", "facturacion"}


class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    password: str
    rol: str

    @model_validator(mode="after")
    def _validar_rol(self):
        if self.rol not in ROLES_INTERNOS_VALIDOS:
            raise ValueError(f"rol debe ser uno de: {', '.join(sorted(ROLES_INTERNOS_VALIDOS))}")
        return self


class UsuarioOut(BaseModel):
    id: uuid.UUID
    nombre: str
    email: str
    rol: str
    activo: bool

    class Config:
        from_attributes = True