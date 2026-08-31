"""Aday mükerrer başvuru uyarı kolonları

Aynı TC/telefon ile daha önce reddedilmiş ya da işten ayrılmış bir kayıt
varsa başvuru anında işaretlenir; İK onay/red kararını bilerek versin.

Revision ID: d5a3f2b81c47
Revises: c4e8b1a7d360
Create Date: 2026-08-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd5a3f2b81c47'
down_revision = 'c4e8b1a7d360'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('adaylar',
                  sa.Column('mukerrer_uyari', sa.Boolean(), nullable=False,
                            server_default=sa.text('false')))
    op.add_column('adaylar', sa.Column('mukerrer_uyari_notu', sa.Text(), nullable=True))
    # Mükerrer taramaları TC ve telefon üzerinden yapılıyor
    op.create_index('ix_adaylar_tc_kimlik', 'adaylar', ['tc_kimlik'])
    op.create_index('ix_adaylar_telefon', 'adaylar', ['telefon'])


def downgrade():
    op.drop_index('ix_adaylar_telefon', table_name='adaylar')
    op.drop_index('ix_adaylar_tc_kimlik', table_name='adaylar')
    op.drop_column('adaylar', 'mukerrer_uyari_notu')
    op.drop_column('adaylar', 'mukerrer_uyari')
