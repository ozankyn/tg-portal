"""Çalışana ehliyet sınıfı alanı

- calisanlar.ehliyet_sinifi (String(10)) — boş = ehliyet yok

Not: adaylar tablosunda ehliyet_var / ehliyet_sinifi / ehliyet_tarihi
zaten mevcut, eklenmiyor.

Revision ID: b1c4e7a9f250
Revises: a7f3c1d9e402
Create Date: 2026-07-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b1c4e7a9f250'
down_revision = 'a7f3c1d9e402'
branch_labels = None
depends_on = None


def _kolon_var(bind, tablo, kolon):
    return kolon in {c['name'] for c in sa.inspect(bind).get_columns(tablo)}


def upgrade():
    # Production'da kolon scripts/calisan_ehliyet_kolonu.sql ile eklenmiş
    # olabilir (migrations/ git'e girmiyor) — o durumda tekrar ekleme.
    bind = op.get_bind()
    if not _kolon_var(bind, 'calisanlar', 'ehliyet_sinifi'):
        op.add_column('calisanlar', sa.Column('ehliyet_sinifi', sa.String(length=10), nullable=True))


def downgrade():
    bind = op.get_bind()
    if _kolon_var(bind, 'calisanlar', 'ehliyet_sinifi'):
        op.drop_column('calisanlar', 'ehliyet_sinifi')
