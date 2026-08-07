from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.operaciones import Operacion
from app.models.plataforma import Cliente
from app.schemas.muelles import MuelleEstado

router = APIRouter(prefix="/muelles", tags=["muelles"])

TOTAL_MUELLES = 20
# Una operación "ocupa" físicamente el muelle mientras no haya cerrado.
ESTADOS_QUE_OCUPAN_MUELLE = {"creada", "asignada", "en_curso"}


@router.get("/disponibilidad", response_model=list[MuelleEstado])
def disponibilidad_muelles(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("supervisor", "gerente", "operario")),
):
    """Muelle 1 a Muelle 20, marcando cuáles están ocupados ahora mismo por
    una operación que todavía no cierra (para no asignar dos operaciones
    al mismo muelle físico al mismo tiempo)."""
    ocupados = db.execute(
        select(Operacion.muelle, Operacion.id, Cliente.nombre)
        .join(Cliente, Operacion.cliente_id == Cliente.id)
        .where(Operacion.estado.in_(ESTADOS_QUE_OCUPAN_MUELLE), Operacion.muelle.is_not(None))
    ).all()
    ocupados_map = {muelle: (op_id, cliente_nombre) for muelle, op_id, cliente_nombre in ocupados}

    resultado = []
    for i in range(1, TOTAL_MUELLES + 1):
        nombre = f"Muelle {i}"
        if nombre in ocupados_map:
            op_id, cliente_nombre = ocupados_map[nombre]
            resultado.append(MuelleEstado(muelle=nombre, disponible=False, operacion_id=op_id, cliente_nombre=cliente_nombre))
        else:
            resultado.append(MuelleEstado(muelle=nombre, disponible=True))
    return resultado