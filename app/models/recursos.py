import uuid
from datetime import date

from sqlalchemy import String, Numeric, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TipoVehiculo(Base):
    __tablename__ = "tipos_vehiculo"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)  # camioneta | sencillo | turbo | tractomula
    tarifa_base: Mapped[float] = mapped_column(Numeric, nullable=False)


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    placa: Mapped[str] = mapped_column(String, nullable=False)
    tipo_vehiculo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tipos_vehiculo.id"))


class Cuadrilla(Base):
    __tablename__ = "cuadrillas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    # estado: disponible | asignada | en_trabajo | en_pausa
    estado: Mapped[str] = mapped_column(String, default="disponible")


class Servicio(Base):
    __tablename__ = "servicios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)  # cargue | descargue | picking | ...


class Tarifa(Base):
    __tablename__ = "tarifas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    servicio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("servicios.id"), nullable=False)
    # criterio: cajas | unidades | vehiculo
    criterio: Mapped[str] = mapped_column(String, nullable=False)
    valor: Mapped[float] = mapped_column(Numeric, nullable=False)
    tipo_vehiculo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tipos_vehiculo.id"), nullable=True)
    vigente_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigente_hasta: Mapped[date] = mapped_column(Date, nullable=True)  # NULL = vigente
