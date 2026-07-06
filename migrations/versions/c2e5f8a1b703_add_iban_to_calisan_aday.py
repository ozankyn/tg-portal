"""Çalışan ve Aday'a IBAN alanı ekle

IBAN otomatik okuma özelliği için calisanlar ve adaylar tablolarına iban kolonu.
Ayrıca aday evrak yüklemede otomatik IBAN okuması için 'IBAN' evrak tipini seed eder.

Revision ID: c2e5f8a1b703
Revises: b1c4e2f7a908
Create Date: 2026-07-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c2e5f8a1b703'
down_revision = 'b1c4e2f7a908'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('calisanlar', sa.Column('iban', sa.String(length=30), nullable=True))
    op.add_column('adaylar', sa.Column('iban', sa.String(length=30), nullable=True))

    # IBAN evrak tipi seed (varsa dokunma)
    evrak_table = sa.table(
        'evrak_tipleri',
        sa.column('ad', sa.String),
        sa.column('kod', sa.String),
        sa.column('aciklama', sa.Text),
        sa.column('zorunlu', sa.Boolean),
        sa.column('kategori', sa.String),
        sa.column('sira', sa.Integer),
        sa.column('aktif', sa.Boolean),
    )
    conn = op.get_bind()
    mevcut = conn.execute(
        sa.text("SELECT 1 FROM evrak_tipleri WHERE kod = 'IBAN'")
    ).first()
    if not mevcut:
        op.bulk_insert(evrak_table, [{
            'ad': 'IBAN / Hesap Bilgisi',
            'kod': 'IBAN',
            'aciklama': 'Banka IBAN / hesap bilgisi belgesi. Yüklendiğinde IBAN otomatik okunur.',
            'zorunlu': False,
            'kategori': 'diger',
            'sira': 50,
            'aktif': True,
        }])


def downgrade():
    op.execute("DELETE FROM evrak_tipleri WHERE kod = 'IBAN'")
    op.drop_column('adaylar', 'iban')
    op.drop_column('calisanlar', 'iban')
