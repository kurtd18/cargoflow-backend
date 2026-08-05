"""tabla inspecciones_aql + row-level security

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-05
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE inspecciones_aql (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            operacion_id UUID REFERENCES operaciones(id),
            proveedor_id UUID NOT NULL REFERENCES proveedores(id),
            tamano_lote INTEGER NOT NULL,
            nivel_inspeccion_general TEXT NOT NULL DEFAULT 'II',
            aql NUMERIC NOT NULL,
            severidad TEXT NOT NULL DEFAULT 'normal',
            codigo_letra TEXT NOT NULL,
            tamano_muestra INTEGER NOT NULL,
            limite_aceptacion INTEGER NOT NULL,
            limite_rechazo INTEGER NOT NULL,
            defectos_encontrados INTEGER NOT NULL,
            resultado TEXT NOT NULL,
            creado_por UUID NOT NULL REFERENCES usuarios(id),
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)

    # Row-Level Security: mismo patrón que 0001_initial_schema.py -- esta tabla
    # tiene empresa_id, así que queda aislada por tenant desde su creación.
    op.execute("ALTER TABLE inspecciones_aql ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON inspecciones_aql
        USING (empresa_id = current_setting('app.current_tenant', true)::uuid)
        WITH CHECK (empresa_id = current_setting('app.current_tenant', true)::uuid)
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS inspecciones_aql CASCADE")