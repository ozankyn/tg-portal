"""bildirim_sablonlari tablosu ve seed data

Revision ID: e3b8c7f9d241
Revises: a7b91e2d5c84
Create Date: 2026-04-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'e3b8c7f9d241'
down_revision = 'a7b91e2d5c84'
branch_labels = None
depends_on = None


# -------------------------------------------------------------------
# Seed HTML icerikleri - mevcut notify_* fonksiyonlarindan cevrildi
# -------------------------------------------------------------------

ISE_GIRIS_ICERIK = """
<div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #059669, #10b981); padding: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">İşe Giriş Bildirimi</h2>
    </div>
    <div style="padding: 25px; background: #f9fafb;">
        <p style="margin: 0 0 15px 0; color: #374151;">Aşağıdaki personelin işe giriş kaydı oluşturulmuştur:</p>
        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
            <tr><td style="padding: 10px 15px; color: #6b7280; width: 200px;">Ad Soyad</td><td style="padding: 10px 15px;"><strong>{ad_soyad}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">TC Kimlik No</td><td style="padding: 10px 15px;"><strong>{tc_kimlik}</strong></td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">İş Başı Tarihi</td><td style="padding: 10px 15px;"><strong style="color: #059669;">{ise_baslama}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Proje</td><td style="padding: 10px 15px;">{proje}</td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Pozisyon</td><td style="padding: 10px 15px;">{pozisyon}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Lokasyon</td><td style="padding: 10px 15px;">{lokasyon}</td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">SGK İşyeri Şubesi</td><td style="padding: 10px 15px;">{sgk_sube}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">SGK No</td><td style="padding: 10px 15px;">{sgk_no}</td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Yönetici</td><td style="padding: 10px 15px;">{yonetici}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Telefon</td><td style="padding: 10px 15px;">{telefon}</td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">E-posta</td><td style="padding: 10px 15px;">{email}</td></tr>
        </table>
    </div>
    <div style="padding: 15px; background: #e5e7eb; text-align: center;">
        <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi (Otomatik bildirim)</p>
    </div>
</div>
""".strip()

ISTEN_CIKIS_ICERIK = """
<div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #dc2626, #ef4444); padding: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">İşten Çıkış Bildirimi</h2>
    </div>
    <div style="padding: 25px; background: #f9fafb;">
        <p style="margin: 0 0 15px 0; color: #374151;">Aşağıdaki personelin işten çıkış kaydı tamamlanmıştır:</p>
        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
            <tr><td style="padding: 10px 15px; color: #6b7280; width: 200px;">Ad Soyad</td><td style="padding: 10px 15px;"><strong>{ad_soyad}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">TC Kimlik No</td><td style="padding: 10px 15px;"><strong>{tc_kimlik}</strong></td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Çıkış Tarihi</td><td style="padding: 10px 15px;"><strong style="color: #dc2626;">{cikis_tarihi}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Çıkış Nedeni</td><td style="padding: 10px 15px;">{cikis_nedeni}</td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Proje</td><td style="padding: 10px 15px;">{proje}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Pozisyon</td><td style="padding: 10px 15px;">{pozisyon}</td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Telefon</td><td style="padding: 10px 15px;">{telefon}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Zimmet Durumu</td><td style="padding: 10px 15px;">{zimmet_durumu}</td></tr>
        </table>
    </div>
    <div style="padding: 15px; background: #e5e7eb; text-align: center;">
        <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi (Otomatik bildirim)</p>
    </div>
</div>
""".strip()

YENI_BASVURU_ICERIK = """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #059669, #10b981); padding: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">Yeni Aday Başvurusu</h2>
    </div>
    <div style="padding: 25px; background: #f9fafb;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="padding: 8px 0; color: #6b7280;">Ad Soyad:</td><td style="padding: 8px 0;"><strong>{ad_soyad}</strong></td></tr>
            <tr><td style="padding: 8px 0; color: #6b7280;">Telefon:</td><td style="padding: 8px 0;">{telefon}</td></tr>
            <tr><td style="padding: 8px 0; color: #6b7280;">E-posta:</td><td style="padding: 8px 0;">{email}</td></tr>
            <tr><td style="padding: 8px 0; color: #6b7280;">Pozisyon:</td><td style="padding: 8px 0;">{pozisyon}</td></tr>
            <tr><td style="padding: 8px 0; color: #6b7280;">Proje:</td><td style="padding: 8px 0;">{proje}</td></tr>
            <tr><td style="padding: 8px 0; color: #6b7280;">Lokasyon:</td><td style="padding: 8px 0;">{lokasyon}</td></tr>
            <tr><td style="padding: 8px 0; color: #6b7280;">Kaynak:</td><td style="padding: 8px 0;">{kaynak}</td></tr>
            <tr><td style="padding: 8px 0; color: #6b7280;">Deneyim:</td><td style="padding: 8px 0;">{tecrube_yil} yıl</td></tr>
            <tr><td style="padding: 8px 0; color: #6b7280;">Son İş Yeri:</td><td style="padding: 8px 0;">{son_is_yeri}</td></tr>
            <tr><td style="padding: 8px 0; color: #6b7280;">Son Pozisyon:</td><td style="padding: 8px 0;">{son_pozisyon}</td></tr>
        </table>
        <div style="text-align: center; margin-top: 25px;">
            <a href="{basvuru_url}" style="background: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold;">Başvuruyu İncele</a>
        </div>
    </div>
    <div style="padding: 15px; background: #e5e7eb; text-align: center;">
        <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi</p>
    </div>
</div>
""".strip()

SOZLESME_UYARI_ICERIK = """
<div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
    <div style="background: #d97706; color: white; padding: 20px; text-align: center;">
        <h2 style="margin: 0;">Sözleşme Bitiş Uyarısı</h2>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">30 gün içinde sözleşmesi dolacak {toplam_sayi} personel</p>
    </div>
    <div style="padding: 20px; background: white;">
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <thead>
                <tr style="background: #f3f4f6;">
                    <th style="padding: 10px; text-align: left;">Ad Soyad</th>
                    <th style="padding: 10px; text-align: left;">Şablon</th>
                    <th style="padding: 10px; text-align: left;">Tip</th>
                    <th style="padding: 10px; text-align: left;">Bitiş Tarihi</th>
                    <th style="padding: 10px; text-align: left;">Kalan</th>
                </tr>
            </thead>
            <tbody>{liste_html}</tbody>
        </table>
    </div>
    <div style="padding: 15px; background: #e5e7eb; text-align: center;">
        <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi</p>
    </div>
</div>
""".strip()


SEED_DATA = [
    {
        'kod': 'ISE_GIRIS',
        'ad': 'İşe Giriş Bildirimi',
        'aciklama': 'Bir çalışan işe alındığında Muhasebe, Filo, Eğitim ve İK departmanlarına gönderilen bildirim.',
        'konu_sablonu': 'İşe Giriş Bildirimi - {ad_soyad} - {ise_baslama}',
        'icerik_sablonu': ISE_GIRIS_ICERIK,
        'alicilar': ['muhasebe@teamguerilla.com', 'filo@teamguerilla.com', 'egitim@teamguerilla.com',
                     'ik@teamguerilla.com', 'ozankayan@teamguerilla.com', 'ozanerenkayan@gmail.com'],
        'dinamik_alici_rolu': None,
        'proje_yoneticisine_gonder': False,
    },
    {
        'kod': 'ISTEN_CIKIS',
        'ad': 'İşten Çıkış Bildirimi',
        'aciklama': 'Bir çalışanın işten çıkış kaydı tamamlandığında ilgili departmanlara gönderilen bildirim.',
        'konu_sablonu': 'İşten Çıkış Bildirimi - {ad_soyad} - {cikis_tarihi}',
        'icerik_sablonu': ISTEN_CIKIS_ICERIK,
        'alicilar': ['muhasebe@teamguerilla.com', 'filo@teamguerilla.com', 'egitim@teamguerilla.com',
                     'ik@teamguerilla.com', 'ozankayan@teamguerilla.com', 'ozanerenkayan@gmail.com'],
        'dinamik_alici_rolu': None,
        'proje_yoneticisine_gonder': False,
    },
    {
        'kod': 'YENI_BASVURU',
        'ad': 'Yeni Başvuru Bildirimi',
        'aciklama': 'Kariyer sayfasından yeni başvuru geldiğinde İK ve ilgili proje koordinatörüne gönderilen bildirim.',
        'konu_sablonu': 'Yeni Başvuru - {pozisyon} - {ad_soyad}',
        'icerik_sablonu': YENI_BASVURU_ICERIK,
        'alicilar': ['ik@teamguerilla.com', 'ozankayan@teamguerilla.com'],
        'dinamik_alici_rolu': 'ik.view',
        'proje_yoneticisine_gonder': True,
    },
    {
        'kod': 'SOZLESME_UYARI',
        'ad': 'Sözleşme Bitiş Uyarısı',
        'aciklama': '30 gün içinde sözleşmesi dolacak personelleri İK\'ya bildirir.',
        'konu_sablonu': '[TG Portal] {toplam_sayi} Personelin Sözleşmesi Dolmak Üzere',
        'icerik_sablonu': SOZLESME_UYARI_ICERIK,
        'alicilar': ['ik@teamguerilla.com', 'ozankayan@teamguerilla.com'],
        'dinamik_alici_rolu': 'ik.view',
        'proje_yoneticisine_gonder': False,
    },
]


def upgrade():
    op.create_table(
        'bildirim_sablonlari',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kod', sa.String(length=50), nullable=False),
        sa.Column('ad', sa.String(length=200), nullable=False),
        sa.Column('aciklama', sa.Text(), nullable=True),
        sa.Column('konu_sablonu', sa.String(length=500), nullable=False),
        sa.Column('icerik_sablonu', sa.Text(), nullable=False),
        sa.Column('alicilar', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('dinamik_alici_rolu', sa.String(length=50), nullable=True),
        sa.Column('proje_yoneticisine_gonder', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('aktif', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('kod'),
    )
    op.create_index('ix_bildirim_sablonlari_kod', 'bildirim_sablonlari', ['kod'])

    # Seed data
    import json
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
    rows = []
    for s in SEED_DATA:
        rows.append({**s, 'aktif': True})
    op.bulk_insert(bildirim_table, rows)


def downgrade():
    op.drop_index('ix_bildirim_sablonlari_kod', table_name='bildirim_sablonlari')
    op.drop_table('bildirim_sablonlari')
