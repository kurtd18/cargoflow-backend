"""eliminar columna vieja defectos_encontrados (reemplazada por el desglose critico/mayor/menor)

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-06
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE inspecciones_aql DROP COLUMN IF EXISTS defectos_encontrados")


def downgrade():
    op.execute("ALTER TABLE inspecciones_aql ADD COLUMN defectos_encontrados INTEGER NOT NULL DEFAULT 0")