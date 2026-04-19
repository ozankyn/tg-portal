"""
TG Portal - Kadro Temizlik Script'i
====================================
Otomatik olusturulan generic HedefKadro kayitlarini soft-delete yapar.
Atanmis calisan varsa silmez, loglar.

KULLANIM:
  cd /app && PYTHONPATH=/app python3 scripts/kadro_temizlik.py --dry-run
  cd /app && PYTHONPATH=/app python3 scripts/kadro_temizlik.py --apply
  cd /app && PYTHONPATH=/app python3 scripts/kadro_temizlik.py --apply --force  (atanmis calisanlarin kadro_id'sini NULL yapar)
"""
import sys
import os

SILINECEK_IDS = [184, 185, 186, 187, 195, 192, 193]


def main():
    apply = '--apply' in sys.argv
    force = '--force' in sys.argv
    mode = 'APPLY' + (' + FORCE' if force else '') if apply else 'DRY-RUN' + (' + FORCE' if force else '')
    print(f'=== Kadro Temizlik ({mode}) ===\n')

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app import create_app, db
    from app.models.ik import Calisan
    from app.models.proje import HedefKadro

    app = create_app()

    with app.app_context():
        silinen = 0
        atlanan = 0

        for kadro_id in SILINECEK_IDS:
            kadro = HedefKadro.query.get(kadro_id)
            if not kadro:
                print(f'  [YOK] Kadro ID {kadro_id} bulunamadi')
                atlanan += 1
                continue

            if kadro.is_deleted:
                print(f'  [ZATEN] ID {kadro_id} ({kadro.pozisyon_adi}) - zaten silinmis')
                continue

            # Atanmis calisan kontrolu
            atananlar = Calisan.query.filter_by(kadro_id=kadro_id, is_deleted=False).all()
            if atananlar:
                isimler = ', '.join(f'{c.ad} {c.soyad}' for c in atananlar)
                if not force:
                    print(f'  [ATLI] ID {kadro_id} ({kadro.pozisyon_adi}) - {len(atananlar)} calisan atanmis: {isimler} - ATLANDI')
                    atlanan += 1
                    continue
                # Force: calisanlarin kadro_id'sini NULL yap
                print(f'  [FORCE] ID {kadro_id} ({kadro.pozisyon_adi}) - {len(atananlar)} calisanin kadro_id NULL yapiliyor: {isimler}')
                if apply:
                    for c in atananlar:
                        c.kadro_id = None

            proje_adi = kadro.proje.ad if kadro.proje else '?'
            print(f'  [SIL]  ID {kadro_id} - {proje_adi} / {kadro.pozisyon_adi}')

            if apply:
                kadro.is_deleted = True

            silinen += 1

        if apply:
            db.session.commit()
            print('\nDegisiklikler kaydedildi.')

        print(f'\n=== OZET ({mode}) ===')
        print(f'Silinecek:  {silinen}')
        print(f'Atlanan:    {atlanan}')

        if not apply and silinen > 0:
            print(f'\nUygulamak icin: python3 scripts/kadro_temizlik.py --apply')


if __name__ == '__main__':
    main()
