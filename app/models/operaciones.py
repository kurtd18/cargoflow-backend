import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Numeric, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Operacion(Base):
    __tablename__ = "operaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    proveedor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("proveedores.id"), nullable=True)
    servicio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("servicios.id"), nullable=False)
    vehiculo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehiculos.id"), nullable=True)
    muelle: Mapped[str] = mapped_column(String, nullable=True)
    categoria_mercancia: Mapped[str] = mapped_column(String, nullable=True)
    cuadrilla_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cuadrillas.id"), nullable=True)
    # tarifa_id/criterio_cobro/cantidad_estimada/cantidad_real: modo "clásico",
    # una sola tarifa por operación (ej. Víveres/Electro por tipo de vehículo).
    # Si la operación usa varias tarifas a la vez (ej. Fruver: descargue +
    # trasvaseo), estos quedan NULL y el detalle vive en LineaCobro.
    tarifa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tarifas.id"), nullable=True)
    criterio_cobro: Mapped[str] = mapped_column(String, nullable=True)
    cantidad_estimada: Mapped[float] = mapped_column(Numeric, nullable=True)
    cantidad_real: Mapped[float] = mapped_column(Numeric, nullable=True)
    estado: Mapped[str] = mapped_column(String, default="creada")
    hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    hora_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    tiempo_pausado_segundos: Mapped[int] = mapped_column(Integer, default=0)
    creado_por: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class LineaCobro(Base):
    """Un concepto de cobro dentro de una operación (tarifa + cantidad).
    Permite que UNA operación combine varios conceptos a la vez -- por
    ejemplo, en Fruver: descargue por tonelada Y trasvaseo por tonelada
    en la misma operación, cada uno con su propia tarifa y cantidad."""

    __tablename__ = "lineas_cobro"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    operacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operaciones.id"), nullable=False)
    tarifa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tarifas.id"), nullable=False)
    cantidad_estimada: Mapped[float] = mapped_column(Numeric, nullable=True)
    cantidad_real: Mapped[float] = mapped_column(Numeric, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Evidencia(Base):
    __tablename__ = "evidencias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operaciones.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    url_archivo: Mapped[str] = mapped_column(String, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Incidencia(Base):
    __tablename__ = "incidencias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operaciones.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str] = mapped_column(String, nullable=True)
    foto_url: Mapped[str] = mapped_column(String, nullable=True)
    creado_por: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operaciones.id"), nullable=False)
    forma_pago: Mapped[str] = mapped_column(String, nullable=False)
    medio_pago: Mapped[str] = mapped_column(String, nullable=True)
    monto: Mapped[float] = mapped_column(Numeric, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Liquidacion(Base):
    __tablename__ = "liquidaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operaciones.id"), nullable=False)
    tarifa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tarifas.id"), nullable=False)
    cantidad_real: Mapped[float] = mapped_column(Numeric, nullable=False)
    valor_calculado: Mapped[float] = mapped_column(Numeric, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))