"""Add kiralama_firmasi_id to Arac

Revision ID: 8f7b73d6cf9a
Revises: d2f481a7c3b9
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa


revision = '8f7b73d6cf9a'
down_revision = 'd2f481a7c3b9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('araclar') as batch_op:
        batch_op.add_column(sa.Column('kiralama_firmasi_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_araclar_kiralama_firmasi_id_tedarikciler',
            'tedarikciler',
            ['kiralama_firmasi_id'], ['id'],
        )


def downgrade():
    with op.batch_alter_table('araclar') as batch_op:
        batch_op.drop_constraint('fk_araclar_kiralama_firmasi_id_tedarikciler', type_='foreignkey')
        batch_op.drop_column('kiralama_firmasi_id')
