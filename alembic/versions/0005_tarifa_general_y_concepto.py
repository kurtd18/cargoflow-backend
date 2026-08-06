"""tarifas: cliente_id opcional (tarifa general), agregar concepto

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-06
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE tarifas ALTER COLUMN cliente_id DROP NOT NULL")
    op.execute("ALTER TABLE tarifas ADD COLUMN concepto TEXT")


def downgrade():
    op.execute("ALTER TABLE tarifas DROP COLUMN IF EXISTS concepto")
    op.execute("ALTER TABLE tarifas ALTER COLUMN cliente_id SET NOT NULL")