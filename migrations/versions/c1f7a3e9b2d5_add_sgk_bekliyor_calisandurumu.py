"""CalisanDurumu enum'a SGK_BEKLIYOR degeri ekle (tekrar ise alim)

Revision ID: c1f7a3e9b2d5
Revises: b7e3c9f01a45
Create Date: 2026-07-01 09:00:00.000000

"""
from alembic import op


revision = 'c1f7a3e9b2d5'
down_revision = 'b7e3c9f01a45'
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL native enum tipine yeni deger ekle.
    # SQLAlchemy enum degerleri uye ADI ile (buyuk harf) saklanir: 'SGK_BEKLIYOR'.
    op.execute("ALTER TYPE calisandurumu ADD VALUE IF NOT EXISTS 'SGK_BEKLIYOR'")


def downgrade():
    # PostgreSQL enum'dan deger cikarmayi dogrudan desteklemez; downgrade no-op.
    pass
