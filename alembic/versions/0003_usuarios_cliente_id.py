"""agregar cliente_id a usuarios (portal de cliente)

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-05
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE usuarios ADD COLUMN cliente_id UUID REFERENCES clientes(id)")


def downgrade():
    op.execute("ALTER TABLE usuarios DROP COLUMN IF EXISTS cliente_id")