"""EgitimKatilimLog'a ayrilma_zamani kolonu

Kalma süresi hesabı (ayrilma - giris) için. Eğitim sonlandırıldığında set edilir.

Revision ID: e5a9c3b1f782
Revises: d4f7a2c9e611
Create Date: 2026-07-06 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e5a9c3b1f782'
down_revision = 'd4f7a2c9e611'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('egitim_katilim_loglari',
                  sa.Column('ayrilma_zamani', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('egitim_katilim_loglari', 'ayrilma_zamani')
