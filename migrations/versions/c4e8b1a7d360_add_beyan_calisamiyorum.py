"""Beyan kaydına calisamiyorum kolonu

Haftalık beyanda minimum 2 gün seçimi zorunlu hale geldi. Hiç
çalışamayacak olanlar gün seçmek yerine "Bu hafta çalışamıyorum"
seçeneğini işaretler.

Revision ID: c4e8b1a7d360
Revises: b7e4c2a90f15
Create Date: 2026-08-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c4e8b1a7d360'
down_revision = 'b7e4c2a90f15'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('beyan_kayitlari',
                  sa.Column('calisamiyorum', sa.Boolean(), nullable=False,
                            server_default=sa.text('false')))


def downgrade():
    op.drop_column('beyan_kayitlari', 'calisamiyorum')
