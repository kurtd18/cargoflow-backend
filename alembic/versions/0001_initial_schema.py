"""esquema inicial + row-level security multiempresa

Revision ID: 0001
Revises:
Create Date: 2026-08-04
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Tablas de negocio que deben quedar aisladas por empresa_id (ver Arquitectura Técnica, Sección 1.2)
TABLAS_CON_TENANT = [
    "usuarios", "clientes", "proveedores", "tipos_vehiculo", "vehiculos",
    "cuadrillas", "servicios", "tarifas", "operaciones",
]


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    op.execute("""
        CREATE TABLE empresas (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            nombre TEXT NOT NULL,
            nit TEXT,
            plan TEXT DEFAULT 'basico',
            estado TEXT DEFAULT 'activa',
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE usuarios (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL,
            tipo_acceso TEXT DEFAULT 'web',
            activo BOOLEAN DEFAULT true,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE clientes (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            nombre TEXT NOT NULL,
            nit TEXT,
            condicion_pago TEXT DEFAULT 'contado',
            cupo_credito NUMERIC,
            activo BOOLEAN DEFAULT true
        )
    """)

    op.execute("""
        CREATE TABLE proveedores (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            nombre TEXT NOT NULL,
            nit TEXT,
            nivel_riesgo TEXT DEFAULT 'confiable',
            nivel_inspeccion_actual TEXT DEFAULT 'normal',
            actualizado_en TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE tipos_vehiculo (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            nombre TEXT NOT NULL,
            tarifa_base NUMERIC NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE vehiculos (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            placa TEXT NOT NULL,
            tipo_vehiculo_id UUID REFERENCES tipos_vehiculo(id)
        )
    """)

    op.execute("""
        CREATE TABLE cuadrillas (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            nombre TEXT NOT NULL,
            estado TEXT DEFAULT 'disponible'
        )
    """)

    op.execute("""
        CREATE TABLE servicios (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            nombre TEXT NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE tarifas (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            cliente_id UUID NOT NULL REFERENCES clientes(id),
            servicio_id UUID NOT NULL REFERENCES servicios(id),
            criterio TEXT NOT NULL,
            valor NUMERIC NOT NULL,
            tipo_vehiculo_id UUID REFERENCES tipos_vehiculo(id),
            vigente_desde DATE NOT NULL,
            vigente_hasta DATE
        )
    """)

    op.execute("""
        CREATE TABLE operaciones (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            cliente_id UUID NOT NULL REFERENCES clientes(id),
            proveedor_id UUID REFERENCES proveedores(id),
            servicio_id UUID NOT NULL REFERENCES servicios(id),
            vehiculo_id UUID REFERENCES vehiculos(id),
            muelle TEXT,
            cuadrilla_id UUID REFERENCES cuadrillas(id),
            tarifa_id UUID REFERENCES tarifas(id),
            criterio_cobro TEXT,
            cantidad_estimada NUMERIC,
            cantidad_real NUMERIC,
            estado TEXT DEFAULT 'creada',
            hora_inicio TIMESTAMPTZ,
            hora_fin TIMESTAMPTZ,
            tiempo_pausado_segundos INT DEFAULT 0,
            creado_por UUID NOT NULL REFERENCES usuarios(id),
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE evidencias (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            operacion_id UUID NOT NULL REFERENCES operaciones(id),
            tipo TEXT NOT NULL,
            url_archivo TEXT NOT NULL,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE incidencias (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            operacion_id UUID NOT NULL REFERENCES operaciones(id),
            tipo TEXT NOT NULL,
            descripcion TEXT,
            foto_url TEXT,
            creado_por UUID NOT NULL REFERENCES usuarios(id),
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE pagos (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            operacion_id UUID NOT NULL REFERENCES operaciones(id),
            forma_pago TEXT NOT NULL,
            medio_pago TEXT,
            monto NUMERIC NOT NULL,
            estado TEXT NOT NULL,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE liquidaciones (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            operacion_id UUID NOT NULL REFERENCES operaciones(id),
            tarifa_id UUID NOT NULL REFERENCES tarifas(id),
            cantidad_real NUMERIC NOT NULL,
            valor_calculado NUMERIC NOT NULL,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)

    # Row-Level Security: aislamiento multiempresa a nivel de motor de base de datos.
    # Ver Arquitectura Técnica, Sección 1.2. Esto se activa desde la primera migración,
    # no se agrega después.
    for tabla in TABLAS_CON_TENANT:
        op.execute(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {tabla}
            USING (empresa_id = current_setting('app.current_tenant', true)::uuid)
            WITH CHECK (empresa_id = current_setting('app.current_tenant', true)::uuid)
        """)


def downgrade():
    tablas = [
        "liquidaciones", "pagos", "incidencias", "evidencias", "operaciones",
        "tarifas", "servicios", "cuadrillas", "vehiculos", "tipos_vehiculo",
        "proveedores", "clientes", "usuarios", "empresas",
    ]
    for tabla in tablas:
        op.execute(f"DROP TABLE IF EXISTS {tabla} CASCADE")
