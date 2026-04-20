"""koordinator_projeler many-to-many tablosu

Revision ID: f4d92a6b1c37
Revises: e3b8c7f9d241
Create Date: 2026-04-20 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f4d92a6b1c37'
down_revision = 'e3b8c7f9d241'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'koordinator_projeler',
        sa.Column('koordinator_calisan_id', sa.Integer(), nullable=False),
        sa.Column('proje_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['koordinator_calisan_id'], ['calisanlar.id']),
        sa.ForeignKeyConstraint(['proje_id'], ['projeler.id']),
        sa.PrimaryKeyConstraint('koordinator_calisan_id', 'proje_id'),
    )


def downgrade():
    op.drop_table('koordinator_projeler')
