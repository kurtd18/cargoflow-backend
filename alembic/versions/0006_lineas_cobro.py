"""tabla lineas_cobro -- para operaciones con varios conceptos a la vez

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-06
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE lineas_cobro (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            operacion_id UUID NOT NULL REFERENCES operaciones(id) ON DELETE CASCADE,
            tarifa_id UUID NOT NULL REFERENCES tarifas(id),
            cantidad_estimada NUMERIC,
            cantidad_real NUMERIC,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("ALTER TABLE lineas_cobro ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON lineas_cobro
        USING (empresa_id = current_setting('app.current_tenant', true)::uuid)
        WITH CHECK (empresa_id = current_setting('app.current_tenant', true)::uuid)
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS lineas_cobro CASCADE")