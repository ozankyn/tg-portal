"""ADAY_ONAY_SMS bildirim sablonu seed (SMS)

Revision ID: d4f7a2c9e6b3
Revises: b2d5e8f1a3c7
Create Date: 2026-06-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4f7a2c9e6b3'
down_revision = 'b2d5e8f1a3c7'
branch_labels = None
depends_on = None


# SMS metni - icerik_sablonu olarak saklanir. {ad_soyad}, {evrak_link}, {gun_sayisi} degiskenleri.
ADAY_ONAY_SMS_ICERIK = (
    "Tebrikler! Team Guerilla basvurunuz onaylandi. "
    "Lutfen evraklarinizi {gun_sayisi} gun icinde yukleyiniz: {evrak_link}"
)


def upgrade():
    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT 1 FROM bildirim_sablonlari WHERE kod = 'ADAY_ONAY_SMS'")
    ).first()
    if not exists:
        conn.execute(
            sa.text("""
                INSERT INTO bildirim_sablonlari
                    (kod, ad, aciklama, konu_sablonu, icerik_sablonu, alicilar,
                     dinamik_alici_rolu, proje_yoneticisine_gonder, aktif, created_at, updated_at)
                VALUES
                    (:kod, :ad, :aciklama, :konu, :icerik,
                     '[]'::json, NULL, false, true, now(), now())
            """),
            {
                'kod': 'ADAY_ONAY_SMS',
                'ad': 'Aday Onay SMS',
                'aciklama': ('Aday onaylandiginda (durum: onaylandi) adayin telefonuna gonderilen, '
                             'evrak yukleme linkli SMS. Bu sablon SMS metnidir; konu alani kullanilmaz. '
                             'Degiskenler: {ad_soyad}, {evrak_link}, {gun_sayisi}'),
                'konu': 'Aday Onay SMS (konu kullanilmaz)',
                'icerik': ADAY_ONAY_SMS_ICERIK,
            },
        )


def downgrade():
    op.execute("DELETE FROM bildirim_sablonlari WHERE kod = 'ADAY_ONAY_SMS'")
