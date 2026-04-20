"""users.sifre_degistirildi alani

Revision ID: a7b91e2d5c84
Revises: c8f3d5a1b42e
Create Date: 2026-04-20 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a7b91e2d5c84'
down_revision = 'c8f3d5a1b42e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('sifre_degistirildi', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )


def downgrade():
    op.drop_column('users', 'sifre_degistirildi')
