"""Aday işe alım süreci: yeni alanlar + aday_islem_gecmisi + SGK_GIRIS_TALEBI bildirim

- adaylar: planlanan_baslangic, sgk_bildirgesi, calisan_id, red_tarihi
- aday_islem_gecmisi tablosu (süreç timeline / audit)
- BildirimSablonu seed: SGK_GIRIS_TALEBI

Revision ID: c8e1f6a3b9d2
Revises: a7d2e9b4c6f1
Create Date: 2026-06-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'c8e1f6a3b9d2'
down_revision = 'a7d2e9b4c6f1'
branch_labels = None
depends_on = None


SGK_GIRIS_TALEBI_ICERIK = """
<div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #d97706, #f59e0b); padding: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">SGK Giriş Talebi</h2>
    </div>
    <div style="padding: 25px; background: #f9fafb;">
        <p style="margin: 0 0 15px 0; color: #374151;">Aşağıdaki aday için SGK girişi yapılması talep edilmektedir:</p>
        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
            <tr><td style="padding: 10px 15px; color: #6b7280; width: 200px;">Ad Soyad</td><td style="padding: 10px 15px;"><strong>{ad_soyad}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">TC Kimlik No</td><td style="padding: 10px 15px;"><strong>{tc_kimlik}</strong></td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Planlı Başlangıç</td><td style="padding: 10px 15px;"><strong style="color: #d97706;">{planlanan_baslangic}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Proje</td><td style="padding: 10px 15px;">{proje}</td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Pozisyon</td><td style="padding: 10px 15px;">{pozisyon}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Lokasyon</td><td style="padding: 10px 15px;">{lokasyon}</td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Telefon</td><td style="padding: 10px 15px;">{telefon}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">E-posta</td><td style="padding: 10px 15px;">{email}</td></tr>
        </table>
        <div style="text-align: center; margin-top: 25px;">
            <a href="{aday_url}" style="background: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold;">Aday Detayını Aç</a>
        </div>
        <p style="margin: 20px 0 0 0; color: #6b7280; font-size: 13px;">SGK girişi tamamlandıktan sonra portal üzerinden "SGK Girişi Yaptım" adımı ile giriş bildirgesini yükleyiniz.</p>
    </div>
    <div style="padding: 15px; background: #e5e7eb; text-align: center;">
        <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi (Otomatik bildirim)</p>
    </div>
</div>
""".strip()


def upgrade():
    # 1) adaylar yeni alanlar
    op.add_column('adaylar', sa.Column('red_tarihi', sa.DateTime(), nullable=True))
    op.add_column('adaylar', sa.Column('planlanan_baslangic', sa.Date(), nullable=True))
    op.add_column('adaylar', sa.Column('sgk_bildirgesi', sa.String(length=255), nullable=True))
    op.add_column('adaylar', sa.Column('calisan_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_adaylar_calisan_id', 'adaylar', 'calisanlar', ['calisan_id'], ['id'])

    # 2) aday_islem_gecmisi tablosu
    op.create_table(
        'aday_islem_gecmisi',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aday_id', sa.Integer(), nullable=False),
        sa.Column('islem', sa.String(length=50), nullable=False),
        sa.Column('aciklama', sa.Text(), nullable=True),
        sa.Column('onceki_durum', sa.String(length=30), nullable=True),
        sa.Column('yeni_durum', sa.String(length=30), nullable=True),
        sa.Column('kullanici_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['aday_id'], ['adaylar.id']),
        sa.ForeignKeyConstraint(['kullanici_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_aday_islem_gecmisi_aday_id', 'aday_islem_gecmisi', ['aday_id'])

    # 3) SGK_GIRIS_TALEBI bildirim şablonu seed (varsa atla)
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
        sa.text("SELECT 1 FROM bildirim_sablonlari WHERE kod = 'SGK_GIRIS_TALEBI'")
    ).first()
    if not mevcut:
        op.bulk_insert(bildirim_table, [{
            'kod': 'SGK_GIRIS_TALEBI',
            'ad': 'SGK Giriş Talebi',
            'aciklama': 'Aday onaylanıp SGK giriş talebi oluşturulduğunda bordro/muhasebe ekibine gönderilen bildirim.',
            'konu_sablonu': 'SGK Giriş Talebi - {ad_soyad} - {planlanan_baslangic}',
            'icerik_sablonu': SGK_GIRIS_TALEBI_ICERIK,
            'alicilar': ['muhasebe@teamguerilla.com', 'bordro@teamguerilla.com',
                         'ik@teamguerilla.com', 'ozankayan@teamguerilla.com'],
            'dinamik_alici_rolu': None,
            'proje_yoneticisine_gonder': False,
            'aktif': True,
        }])


def downgrade():
    op.execute("DELETE FROM bildirim_sablonlari WHERE kod = 'SGK_GIRIS_TALEBI'")
    op.drop_index('ix_aday_islem_gecmisi_aday_id', table_name='aday_islem_gecmisi')
    op.drop_table('aday_islem_gecmisi')
    op.drop_constraint('fk_adaylar_calisan_id', 'adaylar', type_='foreignkey')
    op.drop_column('adaylar', 'calisan_id')
    op.drop_column('adaylar', 'sgk_bildirgesi')
    op.drop_column('adaylar', 'planlanan_baslangic')
    op.drop_column('adaylar', 'red_tarihi')
