"""agregar desglose de defectos y checklist a inspecciones_aql

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-06
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE inspecciones_aql ADD COLUMN defectos_criticos INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE inspecciones_aql ADD COLUMN defectos_mayores INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE inspecciones_aql ADD COLUMN defectos_menores INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE inspecciones_aql ADD COLUMN checklist JSONB")


def downgrade():
    op.execute("ALTER TABLE inspecciones_aql DROP COLUMN IF EXISTS defectos_criticos")
    op.execute("ALTER TABLE inspecciones_aql DROP COLUMN IF EXISTS defectos_mayores")
    op.execute("ALTER TABLE inspecciones_aql DROP COLUMN IF EXISTS defectos_menores")
    op.execute("ALTER TABLE inspecciones_aql DROP COLUMN IF EXISTS checklist")