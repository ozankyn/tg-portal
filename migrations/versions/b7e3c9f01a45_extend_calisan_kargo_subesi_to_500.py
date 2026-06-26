"""calisanlar.kargo_subesi alanını VARCHAR(500) yap

Revision ID: b7e3c9f01a45
Revises: e3a8b1c4d9f2
Create Date: 2026-06-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b7e3c9f01a45'
down_revision = 'e3a8b1c4d9f2'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'calisanlar', 'kargo_subesi',
        existing_type=sa.String(length=100),
        type_=sa.String(length=500),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        'calisanlar', 'kargo_subesi',
        existing_type=sa.String(length=500),
        type_=sa.String(length=100),
        existing_nullable=True,
    )
