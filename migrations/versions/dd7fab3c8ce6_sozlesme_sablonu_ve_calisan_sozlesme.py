"""SozlesmeSablonu ve Calisan sozlesme alanlari

Revision ID: dd7fab3c8ce6
Revises: e9086209810d
Create Date: 2026-04-19 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dd7fab3c8ce6'
down_revision = 'e9086209810d'
branch_labels = None
depends_on = None


def upgrade():
    # sozlesme_sablonlari tablosu
    op.create_table('sozlesme_sablonlari',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ad', sa.String(length=200), nullable=False),
        sa.Column('tip', sa.String(length=50), nullable=False),
        sa.Column('musteri_id', sa.Integer(), nullable=True),
        sa.Column('proje_id', sa.Integer(), nullable=True),
        sa.Column('pozisyon_id', sa.Integer(), nullable=True),
        sa.Column('departman_id', sa.Integer(), nullable=True),
        sa.Column('sablon_dosya', sa.String(length=500), nullable=True),
        sa.Column('aciklama', sa.Text(), nullable=True),
        sa.Column('aktif', sa.Boolean(), nullable=True),
        sa.Column('sira', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['musteri_id'], ['musteriler.id'], ),
        sa.ForeignKeyConstraint(['proje_id'], ['projeler.id'], ),
        sa.ForeignKeyConstraint(['pozisyon_id'], ['pozisyonlar.id'], ),
        sa.ForeignKeyConstraint(['departman_id'], ['departmanlar.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # calisanlar tablosuna sozlesme alanlari
    op.add_column('calisanlar', sa.Column('sozlesme_sablon_id', sa.Integer(), nullable=True))
    op.add_column('calisanlar', sa.Column('sozlesme_baslangic', sa.Date(), nullable=True))
    op.add_column('calisanlar', sa.Column('sozlesme_bitis', sa.Date(), nullable=True))
    op.add_column('calisanlar', sa.Column('sozlesme_pdf', sa.String(length=500), nullable=True))
    op.create_foreign_key('fk_calisanlar_sozlesme_sablon', 'calisanlar', 'sozlesme_sablonlari', ['sozlesme_sablon_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_calisanlar_sozlesme_sablon', 'calisanlar', type_='foreignkey')
    op.drop_column('calisanlar', 'sozlesme_pdf')
    op.drop_column('calisanlar', 'sozlesme_bitis')
    op.drop_column('calisanlar', 'sozlesme_baslangic')
    op.drop_column('calisanlar', 'sozlesme_sablon_id')
    op.drop_table('sozlesme_sablonlari')
