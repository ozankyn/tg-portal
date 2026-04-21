# -*- coding: utf-8 -*-
"""
TG Portal - SGK İşten Çıkış Kodları Seed
Standart SGK çıkış kodlarını sgk_cikis_kodlari tablosuna ekler.

Kullanım (Docker):
    docker compose exec web bash -c "cd /app && PYTHONPATH=/app python3 scripts/sgk_cikis_kodlari_seed.py"
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.ik import SgkCikisKodu


KODLAR = [
    (1, 'Deneme süresi içinde işveren feshi'),
    (2, 'Deneme süresi içinde işçi feshi'),
    (3, 'Belirsiz süreli iş sözleşmesinin işveren tarafından haklı nedenle feshi'),
    (4, 'Belirsiz süreli iş sözleşmesinin işçi tarafından haklı nedenle feshi'),
    (5, 'Belirli süreli iş sözleşmesinin sona ermesi'),
    (8, 'Emeklilik (yaşlılık)'),
    (9, 'Malulen emeklilik'),
    (10, 'Ölüm'),
    (11, 'İş kazası sonucu ölüm'),
    (12, 'Askerlik'),
    (13, 'Kadının evlenmesi'),
    (14, 'Emeklilik (yaş dışı)'),
    (15, 'Toplu işçi çıkarma'),
    (16, 'Diğer nedenler'),
    (17, 'İşyerinin kapanması'),
    (18, 'İşin sona ermesi'),
    (19, 'Mevsim bitimi'),
    (20, 'Kampanya bitimi'),
    (22, 'Diğer nedenler (4857 sk)'),
    (25, 'İşçi istifası (4857/17)'),
    (26, 'Disiplin kurulu kararıyla fesih'),
    (27, 'İşveren tarafından zorunlu nedenle fesih'),
    (29, 'İşçi tarafından zorunlu nedenle fesih'),
    (30, 'Vize süresinin bitimi (yabancı)'),
    (31, 'Borçlar kanunu fesih'),
    (32, '4046 sayılı kanun (özelleştirme)'),
    (33, 'OHAL kapsamında fesih'),
    (34, 'Doğum sonrası kadın işçi feshi'),
]


def seed_sgk_cikis_kodlari():
    eklenen = 0
    guncellenen = 0
    for kod, aciklama in KODLAR:
        existing = SgkCikisKodu.query.filter_by(kod=kod).first()
        if existing:
            if existing.aciklama != aciklama:
                existing.aciklama = aciklama
                guncellenen += 1
            continue
        db.session.add(SgkCikisKodu(kod=kod, aciklama=aciklama, aktif=True))
        eklenen += 1
    db.session.commit()
    print(f'✓ SGK çıkış kodları: {eklenen} yeni, {guncellenen} güncellendi, {len(KODLAR)} toplam.')


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_sgk_cikis_kodlari()
