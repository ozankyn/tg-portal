"""Aday IP alanlarını VARCHAR(45) -> VARCHAR(200) genişlet

telefon_dogrulama_ip ve kvkk_onay_ip: IPv6 + Cloudflare proxy zinciri
(X-Forwarded-For birden çok IP içerebilir) 45 karakteri aşabiliyor.

Revision ID: b7c4e21a9f56
Revises: e5a9c3b1f782
Create Date: 2026-07-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b7c4e21a9f56'
down_revision = 'e5a9c3b1f782'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('adaylar', 'telefon_dogrulama_ip',
                    existing_type=sa.String(length=45),
                    type_=sa.String(length=200),
                    existing_nullable=True)
    op.alter_column('adaylar', 'kvkk_onay_ip',
                    existing_type=sa.String(length=45),
                    type_=sa.String(length=200),
                    existing_nullable=True)


def downgrade():
    op.alter_column('adaylar', 'kvkk_onay_ip',
                    existing_type=sa.String(length=200),
                    type_=sa.String(length=45),
                    existing_nullable=True)
    op.alter_column('adaylar', 'telefon_dogrulama_ip',
                    existing_type=sa.String(length=200),
                    type_=sa.String(length=45),
                    existing_nullable=True)
