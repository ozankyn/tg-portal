"""Aday'a fiziksel/lojistik/kaynak alanları

- ust_beden, alt_beden, ayakkabi_no (fiziksel)
- kargo_subesi (lojistik)
- basvuru_kaynak, tg_calistimi (kaynak / geçmiş)

Not: seyahat_engeli zaten mevcut, eklenmiyor.

Revision ID: f3a9c1d4e2b8
Revises: e5f1a8c20b73
Create Date: 2026-06-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f3a9c1d4e2b8'
down_revision = 'e5f1a8c20b73'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('adaylar', sa.Column('ust_beden', sa.String(length=10), nullable=True))
    op.add_column('adaylar', sa.Column('alt_beden', sa.String(length=10), nullable=True))
    op.add_column('adaylar', sa.Column('ayakkabi_no', sa.String(length=5), nullable=True))
    op.add_column('adaylar', sa.Column('kargo_subesi', sa.String(length=150), nullable=True))
    op.add_column('adaylar', sa.Column('basvuru_kaynak', sa.String(length=50), nullable=True))
    op.add_column('adaylar', sa.Column('tg_calistimi', sa.Boolean(), nullable=True, server_default=sa.false()))


def downgrade():
    op.drop_column('adaylar', 'tg_calistimi')
    op.drop_column('adaylar', 'basvuru_kaynak')
    op.drop_column('adaylar', 'kargo_subesi')
    op.drop_column('adaylar', 'ayakkabi_no')
    op.drop_column('adaylar', 'alt_beden')
    op.drop_column('adaylar', 'ust_beden')
