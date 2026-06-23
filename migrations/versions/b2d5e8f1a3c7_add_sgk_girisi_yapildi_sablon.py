"""SGK_GIRISI_YAPILDI bildirim sablonu seed

Revision ID: b2d5e8f1a3c7
Revises: a1c4f7e9d2b6
Create Date: 2026-06-23 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2d5e8f1a3c7'
down_revision = 'a1c4f7e9d2b6'
branch_labels = None
depends_on = None


SGK_GIRISI_YAPILDI_ICERIK = """
<div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #059669, #10b981); padding: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">SGK Girişi Yapıldı</h2>
    </div>
    <div style="padding: 25px; background: #f9fafb;">
        <p style="margin: 0 0 15px 0; color: #374151;">Aşağıdaki adayın SGK girişi yapılmış ve giriş bildirgesi sisteme yüklenmiştir:</p>
        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
            <tr><td style="padding: 10px 15px; color: #6b7280; width: 200px;">Ad Soyad</td><td style="padding: 10px 15px;"><strong>{ad_soyad}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">TC Kimlik No</td><td style="padding: 10px 15px;"><strong>{tc_kimlik}</strong></td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">SGK Giriş Tarihi</td><td style="padding: 10px 15px;"><strong style="color: #059669;">{sgk_giris_tarihi}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Proje</td><td style="padding: 10px 15px;">{proje}</td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Kadro / Pozisyon</td><td style="padding: 10px 15px;">{pozisyon}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Lokasyon</td><td style="padding: 10px 15px;">{lokasyon}</td></tr>
        </table>
        <div style="text-align: center; margin-top: 25px;">
            <a href="{aday_link}" style="background: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold;">Aday Detayını Aç</a>
        </div>
        <p style="margin: 20px 0 0 0; color: #6b7280; font-size: 13px;">Aday artık çalışana dönüştürülmeye hazırdır.</p>
    </div>
    <div style="padding: 15px; background: #e5e7eb; text-align: center;">
        <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi (Otomatik bildirim)</p>
    </div>
</div>
""".strip()


def upgrade():
    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT 1 FROM bildirim_sablonlari WHERE kod = 'SGK_GIRISI_YAPILDI'")
    ).first()
    if not exists:
        conn.execute(
            sa.text("""
                INSERT INTO bildirim_sablonlari
                    (kod, ad, aciklama, konu_sablonu, icerik_sablonu, alicilar,
                     dinamik_alici_rolu, proje_yoneticisine_gonder, aktif, created_at, updated_at)
                VALUES
                    (:kod, :ad, :aciklama, :konu, :icerik,
                     '["ik@teamguerilla.com", "ozankayan@teamguerilla.com"]'::json,
                     NULL, false, true, now(), now())
            """),
            {
                'kod': 'SGK_GIRISI_YAPILDI',
                'ad': 'SGK Girişi Yapıldı',
                'aciklama': 'Bir adayın SGK girişi yapıldığında (giriş bildirgesi yüklendiğinde) İK ekibine gönderilen bilgilendirme.',
                'konu': 'SGK Girişi Yapıldı - {ad_soyad} - {sgk_giris_tarihi}',
                'icerik': SGK_GIRISI_YAPILDI_ICERIK,
            },
        )


def downgrade():
    op.execute("DELETE FROM bildirim_sablonlari WHERE kod = 'SGK_GIRISI_YAPILDI'")
