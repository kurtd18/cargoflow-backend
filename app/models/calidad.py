import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InspeccionAQL(Base):
    """Inspección de calidad por muestreo (ANSI/ASQ Z1.4), con checklist de
    7 aspectos y desglose de defectos por severidad (crítico/mayor/menor).
    Ver app/services/aql.py para el cálculo del plan de muestreo y las
    reglas de cambio de severidad."""

    __tablename__ = "inspecciones_aql"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    operacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operaciones.id"), nullable=True)
    proveedor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("proveedores.id"), nullable=False)

    tamano_lote: Mapped[int] = mapped_column(Integer, nullable=False)
    nivel_inspeccion_general: Mapped[str] = mapped_column(String, nullable=False, default="II")
    aql: Mapped[float] = mapped_column(Numeric, nullable=False)
    severidad: Mapped[str] = mapped_column(String, nullable=False, default="normal")

    codigo_letra: Mapped[str] = mapped_column(String, nullable=False)
    tamano_muestra: Mapped[int] = mapped_column(Integer, nullable=False)
    limite_aceptacion: Mapped[int] = mapped_column(Integer, nullable=False)
    limite_rechazo: Mapped[int] = mapped_column(Integer, nullable=False)

    defectos_criticos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    defectos_mayores: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    defectos_menores: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # checklist: lista de los 7 ítems evaluados (item, conforme, cantidad, severidad) -- para trazabilidad
    checklist: Mapped[list] = mapped_column(JSONB, nullable=True)

    resultado: Mapped[str] = mapped_column(String, nullable=False)

    creado_por: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))