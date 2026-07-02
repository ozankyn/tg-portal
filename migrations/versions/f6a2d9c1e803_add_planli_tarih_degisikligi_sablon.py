"""PLANLI_TARIH_DEGISIKLIGI bildirim şablonu seed

Aday planlı başlangıç tarihi değiştirildiğinde bordro/muhasebe/İK ekibine
gönderilen bildirim şablonu (DB'den düzenlenebilir).

Revision ID: f6a2d9c1e803
Revises: c1f7a3e9b2d5
Create Date: 2026-07-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'f6a2d9c1e803'
down_revision = 'c1f7a3e9b2d5'
branch_labels = None
depends_on = None


PLANLI_TARIH_DEGISIKLIGI_ICERIK = """
<div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #2563eb, #3b82f6); padding: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">Planlı Başlangıç Tarihi Değişikliği</h2>
    </div>
    <div style="padding: 25px; background: #f9fafb;">
        <p style="margin: 0 0 15px 0; color: #374151;">Aşağıdaki aday için planlı başlangıç tarihi güncellenmiştir:</p>
        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
            <tr><td style="padding: 10px 15px; color: #6b7280; width: 200px;">Ad Soyad</td><td style="padding: 10px 15px;"><strong>{ad_soyad}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">TC Kimlik No</td><td style="padding: 10px 15px;"><strong>{tc_kimlik}</strong></td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Eski Planlı Başlangıç</td><td style="padding: 10px 15px;"><strong style="color: #dc2626; text-decoration: line-through;">{eski_tarih}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Yeni Planlı Başlangıç</td><td style="padding: 10px 15px;"><strong style="color: #16a34a;">{yeni_tarih}</strong></td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Değişiklik Nedeni</td><td style="padding: 10px 15px;">{degisiklik_nedeni}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Proje</td><td style="padding: 10px 15px;">{proje}</td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Pozisyon / Kadro</td><td style="padding: 10px 15px;">{pozisyon}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Lokasyon</td><td style="padding: 10px 15px;">{lokasyon}</td></tr>
        </table>
        <div style="text-align: center; margin-top: 25px;">
            <a href="{aday_url}" style="background: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold;">Aday Detayını Aç</a>
        </div>
        <p style="margin: 20px 0 0 0; color: #6b7280; font-size: 13px;">Lütfen SGK giriş planlamanızı yeni tarihe göre güncelleyiniz.</p>
    </div>
    <div style="padding: 15px; background: #e5e7eb; text-align: center;">
        <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi (Otomatik bildirim)</p>
    </div>
</div>
""".strip()


def upgrade():
    bildirim_table = sa.table(
        'bildirim_sablonlari',
        sa.column('kod', sa.String),
        sa.column('ad', sa.String),
        sa.column('aciklama', sa.Text),
        sa.column('konu_sablonu', sa.String),
        sa.column('icerik_sablonu', sa.Text),
        sa.column('alicilar', postgresql.JSON),
        sa.column('dinamik_alici_rolu', sa.String),
        sa.column('proje_yoneticisine_gonder', sa.Boolean),
        sa.column('aktif', sa.Boolean),
    )
    conn = op.get_bind()
    mevcut = conn.execute(
        sa.text("SELECT 1 FROM bildirim_sablonlari WHERE kod = 'PLANLI_TARIH_DEGISIKLIGI'")
    ).first()
    if not mevcut:
        op.bulk_insert(bildirim_table, [{
            'kod': 'PLANLI_TARIH_DEGISIKLIGI',
            'ad': 'Planlı Başlangıç Tarihi Değişikliği',
            'aciklama': 'Aday planlı başlangıç tarihi değiştirildiğinde bordro/muhasebe/İK ekibine gönderilen bildirim.',
            'konu_sablonu': 'Planlı Başlangıç Tarihi Değişikliği - {ad_soyad}',
            'icerik_sablonu': PLANLI_TARIH_DEGISIKLIGI_ICERIK,
            'alicilar': ['muhasebe@teamguerilla.com', 'bordro@teamguerilla.com',
                         'ik@teamguerilla.com', 'ozankayan@teamguerilla.com'],
            'dinamik_alici_rolu': None,
            'proje_yoneticisine_gonder': False,
            'aktif': True,
        }])


def downgrade():
    op.execute("DELETE FROM bildirim_sablonlari WHERE kod = 'PLANLI_TARIH_DEGISIKLIGI'")
