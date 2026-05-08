"""Aday foto/video için aday_medya tablosu

Revision ID: c4e7a91d3f02
Revises: 8f7b73d6cf9a
Create Date: 2026-05-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c4e7a91d3f02'
down_revision = '8f7b73d6cf9a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'aday_medya',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('aday_id', sa.Integer(), sa.ForeignKey('adaylar.id'), nullable=False),
        sa.Column('tip', sa.String(length=10), nullable=False),
        sa.Column('dosya_adi', sa.String(length=255)),
        sa.Column('dosya_yolu', sa.String(length=500)),
        sa.Column('dosya_boyut', sa.Integer()),
        sa.Column('mime_type', sa.String(length=100)),
        sa.Column('yukleyen_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_aday_medya_aday_id', 'aday_medya', ['aday_id'])


def downgrade():
    op.drop_index('ix_aday_medya_aday_id', table_name='aday_medya')
    op.drop_table('aday_medya')
