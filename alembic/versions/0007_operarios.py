"""tabla operarios (personal: nombre, cedula, tipo de sangre)

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-06
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE operarios (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            empresa_id UUID NOT NULL REFERENCES empresas(id),
            nombre TEXT NOT NULL,
            cedula TEXT NOT NULL,
            tipo_sangre TEXT,
            cuadrilla_id UUID REFERENCES cuadrillas(id),
            activo BOOLEAN DEFAULT true,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("ALTER TABLE operarios ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON operarios
        USING (empresa_id = current_setting('app.current_tenant', true)::uuid)
        WITH CHECK (empresa_id = current_setting('app.current_tenant', true)::uuid)
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS operarios CASCADE")