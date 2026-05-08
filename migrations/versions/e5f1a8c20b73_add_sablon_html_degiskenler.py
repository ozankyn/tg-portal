"""SozlesmeSablonu'na html_sablon ve degiskenler alanları

Revision ID: e5f1a8c20b73
Revises: d83b2e9a6f15
Create Date: 2026-05-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'e5f1a8c20b73'
down_revision = 'd83b2e9a6f15'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'sozlesme_sablonlari',
        sa.Column('html_sablon', sa.Text(), nullable=True),
    )
    op.add_column(
        'sozlesme_sablonlari',
        sa.Column('degiskenler', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )


def downgrade():
    op.drop_column('sozlesme_sablonlari', 'degiskenler')
    op.drop_column('sozlesme_sablonlari', 'html_sablon')
