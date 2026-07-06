"""Eğitim dış katılım logu tablosu (EgitimKatilimLog)

Online eğitime /egitim/katil/<id> public linkinden giren kişileri loglar.

Revision ID: d4f7a2c9e611
Revises: c2e5f8a1b703
Create Date: 2026-07-06 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4f7a2c9e611'
down_revision = 'c2e5f8a1b703'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'egitim_katilim_loglari',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('egitim_id', sa.Integer(), nullable=False),
        sa.Column('ad_soyad', sa.String(length=120), nullable=False),
        sa.Column('telefon', sa.String(length=20), nullable=False),
        sa.Column('calisan_id', sa.Integer(), nullable=True),
        sa.Column('aday_id', sa.Integer(), nullable=True),
        sa.Column('giris_zamani', sa.DateTime(), nullable=False),
        sa.Column('ip', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['egitim_id'], ['egitimler.id']),
        sa.ForeignKeyConstraint(['calisan_id'], ['calisanlar.id']),
        sa.ForeignKeyConstraint(['aday_id'], ['adaylar.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_egitim_katilim_loglari_egitim_id',
                    'egitim_katilim_loglari', ['egitim_id'], unique=False)
    op.create_index('ix_egitim_katilim_loglari_telefon',
                    'egitim_katilim_loglari', ['telefon'], unique=False)


def downgrade():
    op.drop_index('ix_egitim_katilim_loglari_telefon', table_name='egitim_katilim_loglari')
    op.drop_index('ix_egitim_katilim_loglari_egitim_id', table_name='egitim_katilim_loglari')
    op.drop_table('egitim_katilim_loglari')
