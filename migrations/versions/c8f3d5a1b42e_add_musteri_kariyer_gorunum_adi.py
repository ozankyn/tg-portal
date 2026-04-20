"""Musteri kariyer_gorunum_adi alani

Revision ID: c8f3d5a1b42e
Revises: dd7fab3c8ce6
Create Date: 2026-04-20 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c8f3d5a1b42e'
down_revision = 'dd7fab3c8ce6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('musteriler', sa.Column('kariyer_gorunum_adi', sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column('musteriler', 'kariyer_gorunum_adi')
