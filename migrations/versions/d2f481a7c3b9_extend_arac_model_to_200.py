"""araclar.model alanını VARCHAR(200) yap

Revision ID: d2f481a7c3b9
Revises: a1b2c3d4e5f6
Create Date: 2026-04-24 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd2f481a7c3b9'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'araclar', 'model',
        existing_type=sa.String(length=50),
        type_=sa.String(length=200),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        'araclar', 'model',
        existing_type=sa.String(length=200),
        type_=sa.String(length=50),
        existing_nullable=True,
    )
