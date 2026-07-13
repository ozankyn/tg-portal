"""AdayIslemGecmisi'ye hatirlatma_tarihi ekle (geri aranacak iletişim logu)

İletişim logu özelliği: aday kartından arama/not kaydı tutulur. "Geri Aranacak"
işlemlerinde adayın ne zaman geri aranacağı bu alanda saklanır.

Revision ID: c8b3f5d1a24e
Revises: b7c4e21a9f56
Create Date: 2026-07-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c8b3f5d1a24e'
down_revision = 'b7c4e21a9f56'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('aday_islem_gecmisi',
                  sa.Column('hatirlatma_tarihi', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('aday_islem_gecmisi', 'hatirlatma_tarihi')
