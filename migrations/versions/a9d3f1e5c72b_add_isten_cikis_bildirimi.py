"""İşten çıkış bildirimi tablosu + ISTEN_CIKIS_BILDIRIMI bildirim şablonu

SPV/Koordinatörün İK+Bordro ekibine gönderdiği işten çıkış ön bildirimi.

Revision ID: a9d3f1e5c72b
Revises: f6a2d9c1e803
Create Date: 2026-07-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'a9d3f1e5c72b'
down_revision = 'f6a2d9c1e803'
branch_labels = None
depends_on = None


ISTEN_CIKIS_BILDIRIMI_ICERIK = """
<div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #dc2626, #ef4444); padding: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">İşten Çıkış Bildirimi</h2>
    </div>
    <div style="padding: 25px; background: #f9fafb;">
        <p style="margin: 0 0 15px 0; color: #374151;"><strong>{bildiren}</strong> tarafından aşağıdaki personel için işten çıkış bildirimi iletilmiştir. Lütfen resmi çıkış sürecini başlatınız.</p>
        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
            <tr><td style="padding: 10px 15px; color: #6b7280; width: 200px;">Ad Soyad</td><td style="padding: 10px 15px;"><strong>{ad_soyad}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">TC Kimlik No</td><td style="padding: 10px 15px;"><strong>{tc_kimlik}</strong></td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Proje</td><td style="padding: 10px 15px;">{proje}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Pozisyon / Kadro</td><td style="padding: 10px 15px;">{pozisyon}</td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Çıkış Nedeni</td><td style="padding: 10px 15px;"><strong style="color: #dc2626;">{cikis_nedeni}</strong></td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Son Çalışma Günü</td><td style="padding: 10px 15px;"><strong>{son_calisma_gunu}</strong></td></tr>
            <tr><td style="padding: 10px 15px; color: #6b7280;">Bildiren (SPV)</td><td style="padding: 10px 15px;">{bildiren}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Not / Açıklama</td><td style="padding: 10px 15px;">{aciklama}</td></tr>
        </table>
        <div style="text-align: center; margin-top: 25px;">
            <a href="{calisan_url}" style="background: #dc2626; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold;">Çalışan Detayını Aç</a>
        </div>
    </div>
    <div style="padding: 15px; background: #e5e7eb; text-align: center;">
        <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi (Otomatik bildirim)</p>
    </div>
</div>
""".strip()


def upgrade():
    op.create_table(
        'isten_cikis_bildirimleri',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('calisan_id', sa.Integer(), nullable=False),
        sa.Column('bildiren_user_id', sa.Integer(), nullable=False),
        sa.Column('cikis_nedeni', sa.String(length=30), nullable=False),
        sa.Column('son_calisma_gunu', sa.Date(), nullable=False),
        sa.Column('aciklama', sa.Text(), nullable=True),
        sa.Column('durum', sa.String(length=20), nullable=False, server_default='beklemede'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['calisan_id'], ['calisanlar.id']),
        sa.ForeignKeyConstraint(['bildiren_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_isten_cikis_bildirimleri_calisan_id',
                    'isten_cikis_bildirimleri', ['calisan_id'], unique=False)

    # Bildirim şablonu seed
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
        sa.text("SELECT 1 FROM bildirim_sablonlari WHERE kod = 'ISTEN_CIKIS_BILDIRIMI'")
    ).first()
    if not mevcut:
        op.bulk_insert(bildirim_table, [{
            'kod': 'ISTEN_CIKIS_BILDIRIMI',
            'ad': 'İşten Çıkış Bildirimi (SPV)',
            'aciklama': 'SPV/Koordinatör çalışan detayından işten çıkış bildirimi gönderdiğinde İK ve Bordro ekibine iletilen bildirim.',
            'konu_sablonu': 'İşten Çıkış Bildirimi - {ad_soyad}',
            'icerik_sablonu': ISTEN_CIKIS_BILDIRIMI_ICERIK,
            'alicilar': ['ik@teamguerilla.com', 'bordro@teamguerilla.com',
                         'ozankayan@teamguerilla.com'],
            'dinamik_alici_rolu': None,
            'proje_yoneticisine_gonder': False,
            'aktif': True,
        }])


def downgrade():
    op.execute("DELETE FROM bildirim_sablonlari WHERE kod = 'ISTEN_CIKIS_BILDIRIMI'")
    op.drop_index('ix_isten_cikis_bildirimleri_calisan_id',
                  table_name='isten_cikis_bildirimleri')
    op.drop_table('isten_cikis_bildirimleri')
