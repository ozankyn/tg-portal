"""
TG Portal - Sözleşme Tipi Seed
================================
Varsayilan sozlesme tiplerini olusturur.

KULLANIM:
  cd /app && PYTHONPATH=/app python3 scripts/sozlesme_tipi_seed.py
"""
import sys
import os

TIPLER = [
    {'ad': 'Müşteri Sözleşmesi', 'kod': 'MUSTERI', 'aciklama': 'Müşteri ile yapılan hizmet sözleşmesi', 'uyari_gun_1': 60, 'uyari_gun_2': 30, 'uyari_gun_3': 7, 'sira': 1},
    {'ad': 'Tedarikçi Sözleşmesi', 'kod': 'TEDARIKCI', 'aciklama': 'Tedarikçi ile yapılan temin sözleşmesi', 'uyari_gun_1': 60, 'uyari_gun_2': 30, 'uyari_gun_3': 7, 'sira': 2},
    {'ad': 'Kiralama Sözleşmesi', 'kod': 'KIRALAMA', 'aciklama': 'Araç, ofis vb. kiralama sözleşmesi', 'uyari_gun_1': 60, 'uyari_gun_2': 30, 'uyari_gun_3': 7, 'sira': 3},
    {'ad': 'Hizmet Sözleşmesi', 'kod': 'HIZMET', 'aciklama': 'Danışmanlık, IT vb. hizmet sözleşmesi', 'uyari_gun_1': 30, 'uyari_gun_2': 15, 'uyari_gun_3': 7, 'sira': 4},
    {'ad': 'Gizlilik Sözleşmesi (NDA)', 'kod': 'NDA', 'aciklama': 'Karşılıklı gizlilik sözleşmesi', 'uyari_gun_1': 30, 'uyari_gun_2': 15, 'uyari_gun_3': 7, 'sira': 5},
]


def main():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app import create_app, db
    from app.models.sozlesme import SozlesmeTipi

    app = create_app()

    with app.app_context():
        for t in TIPLER:
            mevcut = SozlesmeTipi.query.filter_by(kod=t['kod']).first()
            if mevcut:
                print(f'  [MEVCUT] {t["kod"]} - {t["ad"]}')
                continue

            tip = SozlesmeTipi(
                ad=t['ad'],
                kod=t['kod'],
                aciklama=t['aciklama'],
                uyari_gun_1=t['uyari_gun_1'],
                uyari_gun_2=t['uyari_gun_2'],
                uyari_gun_3=t['uyari_gun_3'],
                sira=t['sira'],
                aktif=True
            )
            db.session.add(tip)
            print(f'  [EKLENDI] {t["kod"]} - {t["ad"]}')

        db.session.commit()
        print(f'\nToplam {SozlesmeTipi.query.count()} sozlesme tipi mevcut.')


if __name__ == '__main__':
    main()
