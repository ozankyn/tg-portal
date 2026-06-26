"""Aday havuz alanlari: havuz_notu, havuza_alinma_tarihi

Revision ID: e3a8b1c4d9f2
Revises: d4f7a2c9e6b3
Create Date: 2026-06-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e3a8b1c4d9f2'
down_revision = 'd4f7a2c9e6b3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('adaylar', schema=None) as batch_op:
        batch_op.add_column(sa.Column('havuz_notu', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('havuza_alinma_tarihi', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('adaylar', schema=None) as batch_op:
        batch_op.drop_column('havuza_alinma_tarihi')
        batch_op.drop_column('havuz_notu')
