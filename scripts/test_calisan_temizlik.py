"""
TG Portal - Test Calisan Temizlik Script'i
==========================================
Ad/soyadi icinde "deneme" veya "ozandenememail" gecen test calisanlarini
soft-delete yapar (is_deleted=True, durum=AYRILDI, kadro_id=NULL).

KULLANIM:
  cd /app && PYTHONPATH=/app python3 scripts/test_calisan_temizlik.py             # dry-run (default)
  cd /app && PYTHONPATH=/app python3 scripts/test_calisan_temizlik.py --apply
"""
import sys
import os
from datetime import datetime


PATTERNS = ['deneme', 'ozandenememail']


def main():
    apply = '--apply' in sys.argv
    mode = 'APPLY' if apply else 'DRY-RUN'
    print(f'=== Test Calisan Temizlik ({mode}) ===\n')

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app import create_app, db
    from app.models.ik import Calisan
    from app.models.base import CalisanDurumu

    app = create_app()

    with app.app_context():
        filters = []
        for p in PATTERNS:
            like = f'%{p}%'
            filters.append(Calisan.ad.ilike(like))
            filters.append(Calisan.soyad.ilike(like))

        calisanlar = Calisan.query.filter(
            Calisan.is_deleted == False,
            db.or_(*filters)
        ).order_by(Calisan.id).all()

        if not calisanlar:
            print('Eslesen kayit bulunamadi.')
            return

        print(f'{len(calisanlar)} test kaydi bulundu:\n')
        for c in calisanlar:
            kadro_info = f'kadro_id={c.kadro_id}' if c.kadro_id else 'kadro yok'
            durum_v = c.durum.value if c.durum else '-'
            print(f'  [id={c.id}] {c.ad} {c.soyad} | durum={durum_v} | {kadro_info} | email={c.email or "-"}')

        if not apply:
            print('\n--apply bayragi verilmedi. Degisiklik yapilmadi.')
            return

        print()
        silinen = 0
        for c in calisanlar:
            c.kadro_id = None
            c.durum = CalisanDurumu.AYRILDI
            c.is_deleted = True
            c.deleted_at = datetime.utcnow()
            silinen += 1
            print(f'  [SILINDI] id={c.id} {c.ad} {c.soyad}')

        db.session.commit()
        print(f'\nToplam {silinen} kayit soft-delete edildi.')


if __name__ == '__main__':
    main()
