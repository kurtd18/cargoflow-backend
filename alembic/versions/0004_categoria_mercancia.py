"""agregar categoria_mercancia a operaciones y tarifas

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-06
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE operaciones ADD COLUMN categoria_mercancia TEXT")
    op.execute("ALTER TABLE tarifas ADD COLUMN categoria_mercancia TEXT")


def downgrade():
    op.execute("ALTER TABLE operaciones DROP COLUMN IF EXISTS categoria_mercancia")
    op.execute("ALTER TABLE tarifas DROP COLUMN IF EXISTS categoria_mercancia")