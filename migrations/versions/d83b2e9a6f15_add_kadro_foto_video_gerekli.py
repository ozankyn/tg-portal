"""HedefKadro'ya foto_gerekli + video_gerekli alanları

Revision ID: d83b2e9a6f15
Revises: c4e7a91d3f02
Create Date: 2026-05-08 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd83b2e9a6f15'
down_revision = 'c4e7a91d3f02'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'hedef_kadrolar',
        sa.Column('foto_gerekli', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'hedef_kadrolar',
        sa.Column('video_gerekli', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column('hedef_kadrolar', 'video_gerekli')
    op.drop_column('hedef_kadrolar', 'foto_gerekli')
