"""Calisan'a sgk_cikis_bildirgesi ekle (SGK çıkış bildirgesi dosya yolu)

İşten ayrılan personel için bordronun SGK çıkışını yaptıktan sonra yüklediği
SGK çıkış bildirgesinin (PDF/JPG/PNG) UPLOAD_FOLDER'a göre relatif yolu.

Revision ID: d1e6f9a3b52c
Revises: c8b3f5d1a24e
Create Date: 2026-07-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd1e6f9a3b52c'
down_revision = 'c8b3f5d1a24e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('calisanlar',
                  sa.Column('sgk_cikis_bildirgesi', sa.String(length=500), nullable=True))


def downgrade():
    op.drop_column('calisanlar', 'sgk_cikis_bildirgesi')
