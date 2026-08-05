import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InspeccionAQL(Base):
    """Inspección de calidad por muestreo (ANSI/ASQ Z1.4). Ver app/services/aql.py
    para el cálculo del plan de muestreo (código de letra, Ac/Re) y las
    reglas de cambio de severidad que actualizan Proveedor.nivel_inspeccion_actual.
    """

    __tablename__ = "inspecciones_aql"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    operacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operaciones.id"), nullable=True)
    proveedor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("proveedores.id"), nullable=False)

    tamano_lote: Mapped[int] = mapped_column(Integer, nullable=False)
    # nivel_inspeccion_general: I | II | III (ver app.services.aql.NIVELES_INSPECCION_GENERAL)
    nivel_inspeccion_general: Mapped[str] = mapped_column(String, nullable=False, default="II")
    aql: Mapped[float] = mapped_column(Numeric, nullable=False)
    # severidad aplicada en esta inspección: normal | reforzado | reducido
    severidad: Mapped[str] = mapped_column(String, nullable=False, default="normal")

    codigo_letra: Mapped[str] = mapped_column(String, nullable=False)
    tamano_muestra: Mapped[int] = mapped_column(Integer, nullable=False)
    limite_aceptacion: Mapped[int] = mapped_column(Integer, nullable=False)
    limite_rechazo: Mapped[int] = mapped_column(Integer, nullable=False)

    defectos_encontrados: Mapped[int] = mapped_column(Integer, nullable=False)
    # resultado: aceptado | rechazado (calculado a partir de defectos_encontrados vs Ac/Re)
    resultado: Mapped[str] = mapped_column(String, nullable=False)

    creado_por: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))