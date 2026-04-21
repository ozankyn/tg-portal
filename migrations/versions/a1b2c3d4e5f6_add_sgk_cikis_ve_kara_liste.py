"""sgk_cikis_kodlari tablosu + calisan kara/gri liste alanları

Revision ID: a1b2c3d4e5f6
Revises: f4d92a6b1c37
Create Date: 2026-04-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'a1b2c3d4e5f6'
down_revision = 'f4d92a6b1c37'
branch_labels = None
depends_on = None


liste_durumu_enum = postgresql.ENUM(
    'TEMIZ', 'GRI_LISTE', 'KARA_LISTE',
    name='listedurumu',
    create_type=False,
)


ISTEN_CIKIS_ICERIK_V2 = """
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
            <tr><td style="padding: 10px 15px; color: #6b7280;">SGK Çıkış Kodu</td><td style="padding: 10px 15px;"><strong>{sgk_cikis_kodu}</strong> - {sgk_cikis_aciklama}</td></tr>
            <tr style="background: #f9fafb;"><td style="padding: 10px 15px; color: #6b7280;">Liste Durumu</td><td style="padding: 10px 15px;"><strong>{liste_durumu}</strong></td></tr>
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


def upgrade():
    # 1) Enum tipi
    postgresql.ENUM(
        'TEMIZ', 'GRI_LISTE', 'KARA_LISTE',
        name='listedurumu',
    ).create(op.get_bind(), checkfirst=True)

    # 2) sgk_cikis_kodlari tablosu
    op.create_table(
        'sgk_cikis_kodlari',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kod', sa.Integer(), nullable=False),
        sa.Column('aciklama', sa.String(length=300), nullable=False),
        sa.Column('aktif', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('kod'),
    )
    op.create_index('ix_sgk_cikis_kodlari_kod', 'sgk_cikis_kodlari', ['kod'])

    # 3) isten_cikislar.sgk_cikis_kodu_id
    op.add_column(
        'isten_cikislar',
        sa.Column('sgk_cikis_kodu_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_isten_cikislar_sgk_cikis_kodu_id',
        'isten_cikislar', 'sgk_cikis_kodlari',
        ['sgk_cikis_kodu_id'], ['id'],
    )

    # 4) calisanlar kara/gri liste alanları
    op.add_column(
        'calisanlar',
        sa.Column('liste_durumu', liste_durumu_enum,
                  nullable=False, server_default='TEMIZ'),
    )
    op.add_column('calisanlar', sa.Column('liste_nedeni', sa.Text(), nullable=True))
    op.add_column('calisanlar', sa.Column('liste_tarihi', sa.DateTime(), nullable=True))
    op.add_column('calisanlar', sa.Column('listeye_alan_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_calisanlar_listeye_alan_id',
        'calisanlar', 'users',
        ['listeye_alan_id'], ['id'],
    )

    # 5) ISTEN_CIKIS bildirim şablonunun içeriğini güncelle (SGK kodu + liste durumu)
    bildirim_table = sa.table(
        'bildirim_sablonlari',
        sa.column('kod', sa.String),
        sa.column('icerik_sablonu', sa.Text),
    )
    op.execute(
        bildirim_table.update()
        .where(bildirim_table.c.kod == 'ISTEN_CIKIS')
        .values(icerik_sablonu=ISTEN_CIKIS_ICERIK_V2)
    )


def downgrade():
    op.drop_constraint('fk_calisanlar_listeye_alan_id', 'calisanlar', type_='foreignkey')
    op.drop_column('calisanlar', 'listeye_alan_id')
    op.drop_column('calisanlar', 'liste_tarihi')
    op.drop_column('calisanlar', 'liste_nedeni')
    op.drop_column('calisanlar', 'liste_durumu')

    op.drop_constraint('fk_isten_cikislar_sgk_cikis_kodu_id', 'isten_cikislar', type_='foreignkey')
    op.drop_column('isten_cikislar', 'sgk_cikis_kodu_id')

    op.drop_index('ix_sgk_cikis_kodlari_kod', table_name='sgk_cikis_kodlari')
    op.drop_table('sgk_cikis_kodlari')

    postgresql.ENUM(name='listedurumu').drop(op.get_bind(), checkfirst=True)
