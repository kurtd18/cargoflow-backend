import uuid
from datetime import date

from sqlalchemy import String, Numeric, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TipoVehiculo(Base):
    __tablename__ = "tipos_vehiculo"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
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
    estado: Mapped[str] = mapped_column(String, default="disponible")


class Operario(Base):
    """Personal de campo, dado de alta en un módulo aparte del flujo de
    operaciones (el supervisor lo llena antes, no durante la creación de
    una operación). cuadrilla_id es opcional -- un operario sin cuadrilla
    asignada todavía existe en el sistema, solo no está en ningún equipo."""

    __tablename__ = "operarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    cedula: Mapped[str] = mapped_column(String, nullable=False)
    # tipo_sangre: O+ | O- | A+ | A- | B+ | B- | AB+ | AB-
    tipo_sangre: Mapped[str] = mapped_column(String, nullable=True)
    cuadrilla_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cuadrillas.id"), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Servicio(Base):
    __tablename__ = "servicios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)


class Tarifa(Base):
    __tablename__ = "tarifas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=True)
    servicio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("servicios.id"), nullable=False)
    criterio: Mapped[str] = mapped_column(String, nullable=False)
    valor: Mapped[float] = mapped_column(Numeric, nullable=False)
    tipo_vehiculo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tipos_vehiculo.id"), nullable=True)
    categoria_mercancia: Mapped[str] = mapped_column(String, nullable=True)
    concepto: Mapped[str] = mapped_column(String, nullable=True)
    vigente_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigente_hasta: Mapped[date] = mapped_column(Date, nullable=True)