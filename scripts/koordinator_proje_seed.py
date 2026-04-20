"""
TG Portal - Koordinator-Proje Atama Seed Script'i
==================================================
Koordinator calisanlarini, isim bazli olarak belirtilen projelere atar.
Var olan atamalari silmez, sadece eksik olanlari ekler.

KULLANIM:
  cd /app && PYTHONPATH=/app python3 scripts/koordinator_proje_seed.py             # dry-run
  cd /app && PYTHONPATH=/app python3 scripts/koordinator_proje_seed.py --apply
"""
import sys
import os


# (koordinator ad/soyad, [proje adlari])
ATAMALAR = [
    ('Ufuk', 'Dinc', ['Sniper', 'Adco Merchandiser', 'Modern Kanal Sniper', 'KK Merch']),
    ('Abidin Kazim', 'Sifoglu', ['KK Merch', 'Sniper']),
]


def main():
    apply = '--apply' in sys.argv
    mode = 'APPLY' if apply else 'DRY-RUN'
    print(f'=== Koordinator-Proje Seed ({mode}) ===\n')

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app import create_app, db
    from app.models.ik import Calisan
    from app.models.proje import Proje

    app = create_app()
    with app.app_context():
        eklenen = 0
        atlanan = 0

        for ad, soyad, proje_adlari in ATAMALAR:
            # Calisan'i bul - aksansiz karsilastirma icin unaccent olmadan direkt eslesme
            koordinator = Calisan.query.filter(
                db.func.lower(Calisan.ad) == ad.lower(),
                db.func.lower(Calisan.soyad) == soyad.lower(),
                Calisan.is_deleted == False,
            ).first()

            if not koordinator:
                print(f'[YOK] Koordinator bulunamadi: {ad} {soyad}')
                atlanan += 1
                continue

            print(f'\n[{koordinator.full_name}] (id={koordinator.id})')
            mevcut_proje_ids = {p.id for p in koordinator.koordinator_olarak_projeler}

            for pad in proje_adlari:
                proje = Proje.query.filter(
                    db.func.lower(Proje.ad) == pad.lower(),
                    Proje.is_deleted == False,
                ).first()

                if not proje:
                    print(f'  [YOK] Proje bulunamadi: {pad}')
                    atlanan += 1
                    continue

                if proje.id in mevcut_proje_ids:
                    print(f'  [OK] {pad} zaten atanmis (id={proje.id})')
                    continue

                print(f'  [EKLE] {pad} (id={proje.id})')
                if apply:
                    koordinator.koordinator_olarak_projeler.append(proje)
                eklenen += 1

        if apply:
            db.session.commit()
            print(f'\n>>> {eklenen} yeni atama kaydedildi.')
        else:
            print(f'\n>>> DRY-RUN: {eklenen} atama yapilacakti, {atlanan} atlandi.')


if __name__ == '__main__':
    main()
