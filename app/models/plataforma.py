import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    nit: Mapped[str] = mapped_column(String, nullable=True)
    plan: Mapped[str] = mapped_column(String, default="basico")
    estado: Mapped[str] = mapped_column(String, default="activa")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    # cliente_id: solo se usa cuando rol='cliente' (portal de cliente) -- liga
    # este login a UN cliente específico de la empresa, para que solo vea sus
    # propias operaciones/pagos. NULL para usuarios internos de la empresa.
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    # rol: admin_plataforma | gerente | supervisor | auxiliar | auditor | facturacion | cliente
    rol: Mapped[str] = mapped_column(String, nullable=False)
    tipo_acceso: Mapped[str] = mapped_column(String, default="web")  # web | movil
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    nit: Mapped[str] = mapped_column(String, nullable=True)
    # condicion_pago: contado | credito -- ver PRD Sección 4.4
    condicion_pago: Mapped[str] = mapped_column(String, default="contado")
    cupo_credito: Mapped[float] = mapped_column(Numeric, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    nit: Mapped[str] = mapped_column(String, nullable=True)
    nivel_riesgo: Mapped[str] = mapped_column(String, default="confiable")
    nivel_inspeccion_actual: Mapped[str] = mapped_column(String, default="normal")
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))