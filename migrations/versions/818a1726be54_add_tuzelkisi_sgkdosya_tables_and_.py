"""Add TuzelKisi, SgkDosya tables and Calisan new fields
Revision ID: 818a1726be54
Revises: 06867c698478
Create Date: 2026-01-13 10:05:10.569188
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '818a1726be54'
down_revision = '06867c698478'
branch_labels = None
depends_on = None


def upgrade():
    # Önce tuzel_kisiler tablosu oluşturulmalı
    op.create_table('tuzel_kisiler',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ad', sa.String(length=200), nullable=False),
    sa.Column('kisa_ad', sa.String(length=50), nullable=True),
    sa.Column('vergi_no', sa.String(length=11), nullable=True),
    sa.Column('vergi_dairesi', sa.String(length=100), nullable=True),
    sa.Column('mersis_no', sa.String(length=20), nullable=True),
    sa.Column('adres', sa.Text(), nullable=True),
    sa.Column('telefon', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('aktif', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Sonra sgk_dosyalari (tuzel_kisiler'e bağımlı)
    op.create_table('sgk_dosyalari',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tuzel_kisi_id', sa.Integer(), nullable=False),
    sa.Column('dosya_no', sa.String(length=30), nullable=False),
    sa.Column('ad', sa.String(length=200), nullable=True),
    sa.Column('il', sa.String(length=50), nullable=True),
    sa.Column('ilce', sa.String(length=50), nullable=True),
    sa.Column('tehlike_sinifi', sa.String(length=20), nullable=True),
    sa.Column('aktif', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tuzel_kisi_id'], ['tuzel_kisiler.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Calisan tablosuna yeni kolonlar
    with op.batch_alter_table('calisanlar', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sgk_dosya_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('kidem_tarihi', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('egitim_durumu', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('is_grubu', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('yemek_karti', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('beden', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('kargo_subesi', sa.String(length=100), nullable=True))
        batch_op.create_foreign_key('fk_calisan_sgk_dosya', 'sgk_dosyalari', ['sgk_dosya_id'], ['id'])


def downgrade():
    with op.batch_alter_table('calisanlar', schema=None) as batch_op:
        batch_op.drop_constraint('fk_calisan_sgk_dosya', type_='foreignkey')
        batch_op.drop_column('kargo_subesi')
        batch_op.drop_column('beden')
        batch_op.drop_column('yemek_karti')
        batch_op.drop_column('is_grubu')
        batch_op.drop_column('egitim_durumu')
        batch_op.drop_column('kidem_tarihi')
        batch_op.drop_column('sgk_dosya_id')
    
    op.drop_table('sgk_dosyalari')
    op.drop_table('tuzel_kisiler')
