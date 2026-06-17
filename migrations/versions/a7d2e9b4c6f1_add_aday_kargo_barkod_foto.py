"""Aday'a kargo_barkod_foto alanı (kargo gönderim barkodu fotoğrafı)

Revision ID: a7d2e9b4c6f1
Revises: f3a9c1d4e2b8
Create Date: 2026-06-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a7d2e9b4c6f1'
down_revision = 'f3a9c1d4e2b8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('adaylar', sa.Column('kargo_barkod_foto', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('adaylar', 'kargo_barkod_foto')
