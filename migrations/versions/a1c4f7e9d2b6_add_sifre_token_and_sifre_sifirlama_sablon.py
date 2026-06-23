"""users.sifre_token + sifre_token_expiry ve SIFRE_SIFIRLAMA bildirim sablonu

Revision ID: a1c4f7e9d2b6
Revises: c8e1f6a3b9d2
Create Date: 2026-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1c4f7e9d2b6'
down_revision = 'c8e1f6a3b9d2'
branch_labels = None
depends_on = None


SIFRE_SIFIRLAMA_ICERIK = """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #137fec, #0f67be); padding: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">Şifre Sıfırlama</h2>
    </div>
    <div style="padding: 25px; background: #f9fafb;">
        <p style="margin: 0 0 15px 0; color: #374151;">Sayın {ad_soyad},</p>
        <p style="margin: 0 0 15px 0; color: #374151;">TG Portal hesabınız için şifre sıfırlama talebinde bulundunuz. Şifrenizi sıfırlamak için aşağıdaki butona tıklayın:</p>
        <div style="text-align: center; margin: 25px 0;">
            <a href="{reset_url}" style="background: #137fec; color: white; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Şifremi Sıfırla</a>
        </div>
        <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 13px;">Bu bağlantı <strong>{gecerlilik}</strong> boyunca geçerlidir.</p>
        <p style="margin: 0; color: #6b7280; font-size: 13px;">Eğer buton çalışmazsa, aşağıdaki bağlantıyı tarayıcınıza kopyalayın:<br><span style="color: #137fec; word-break: break-all;">{reset_url}</span></p>
        <p style="margin: 20px 0 0 0; color: #9ca3af; font-size: 12px;">Bu talebi siz yapmadıysanız bu e-postayı yok sayabilirsiniz; şifreniz değişmeyecektir.</p>
    </div>
    <div style="padding: 15px; background: #e5e7eb; text-align: center;">
        <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi (Otomatik bildirim)</p>
    </div>
</div>
""".strip()


def upgrade():
    op.add_column('users', sa.Column('sifre_token', sa.String(length=128), nullable=True))
    op.add_column('users', sa.Column('sifre_token_expiry', sa.DateTime(), nullable=True))
    op.create_index('ix_users_sifre_token', 'users', ['sifre_token'])

    # SIFRE_SIFIRLAMA bildirim sablonu - yoksa ekle (idempotent)
    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT 1 FROM bildirim_sablonlari WHERE kod = 'SIFRE_SIFIRLAMA'")
    ).first()
    if not exists:
        conn.execute(
            sa.text("""
                INSERT INTO bildirim_sablonlari
                    (kod, ad, aciklama, konu_sablonu, icerik_sablonu, alicilar,
                     dinamik_alici_rolu, proje_yoneticisine_gonder, aktif, created_at, updated_at)
                VALUES
                    (:kod, :ad, :aciklama, :konu, :icerik, '[]'::json,
                     NULL, false, true, now(), now())
            """),
            {
                'kod': 'SIFRE_SIFIRLAMA',
                'ad': 'Şifre Sıfırlama',
                'aciklama': 'Kullanıcı "Şifremi Unuttum" ile sıfırlama talebinde bulunduğunda kendisine gönderilen mail. Alıcı dinamiktir (kullanıcının kendi e-postası).',
                'konu': 'Şifre Sıfırlama Talebi - TG Portal',
                'icerik': SIFRE_SIFIRLAMA_ICERIK,
            },
        )


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM bildirim_sablonlari WHERE kod = 'SIFRE_SIFIRLAMA'"))
    op.drop_index('ix_users_sifre_token', table_name='users')
    op.drop_column('users', 'sifre_token_expiry')
    op.drop_column('users', 'sifre_token')
