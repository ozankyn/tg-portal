"""Eğitim davet SMS log tablosu (EgitimDavetSms)

Aday onaylandığında otomatik ve eğitim detayından manuel gönderilen
davet SMS'lerini loglar; mükerrer gönderimi engellemek için kullanılır.

Revision ID: a3f1c8e5d720
Revises: c8d2f6b3a914
Create Date: 2026-07-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a3f1c8e5d720'
down_revision = 'c8d2f6b3a914'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'egitim_davet_smsleri',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('egitim_id', sa.Integer(), nullable=False),
        sa.Column('aday_id', sa.Integer(), nullable=True),
        sa.Column('calisan_id', sa.Integer(), nullable=True),
        sa.Column('ad_soyad', sa.String(length=120), nullable=True),
        sa.Column('telefon', sa.String(length=20), nullable=True),
        sa.Column('basarili', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('hata', sa.String(length=255), nullable=True),
        sa.Column('kaynak', sa.String(length=20), nullable=False, server_default='manuel'),
        sa.Column('gonderen_id', sa.Integer(), nullable=True),
        sa.Column('gonderim_zamani', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['egitim_id'], ['egitimler.id']),
        sa.ForeignKeyConstraint(['aday_id'], ['adaylar.id']),
        sa.ForeignKeyConstraint(['calisan_id'], ['calisanlar.id']),
        sa.ForeignKeyConstraint(['gonderen_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_egitim_davet_smsleri_egitim_id',
                    'egitim_davet_smsleri', ['egitim_id'], unique=False)
    op.create_index('ix_egitim_davet_smsleri_aday_id',
                    'egitim_davet_smsleri', ['aday_id'], unique=False)
    op.create_index('ix_egitim_davet_smsleri_calisan_id',
                    'egitim_davet_smsleri', ['calisan_id'], unique=False)


def downgrade():
    op.drop_index('ix_egitim_davet_smsleri_calisan_id', table_name='egitim_davet_smsleri')
    op.drop_index('ix_egitim_davet_smsleri_aday_id', table_name='egitim_davet_smsleri')
    op.drop_index('ix_egitim_davet_smsleri_egitim_id', table_name='egitim_davet_smsleri')
    op.drop_table('egitim_davet_smsleri')
