"""
TG Portal - Blues Pozisyon Guncelleme
=====================================
Efes Blues projesindeki "Merchandiser" pozisyonlu calisanlari
"Blues" pozisyonuna cevirir. Blues pozisyonu yoksa olusturur.

KULLANIM:
  cd /app && PYTHONPATH=/app python3 scripts/blues_pozisyon.py --dry-run
  cd /app && PYTHONPATH=/app python3 scripts/blues_pozisyon.py --apply
"""
import sys
import os

PROJE_ADI = 'Efes Blues'
ESKI_POZISYON = 'Merchandiser'
YENI_POZISYON = 'Blues'
DEPARTMAN_ADI = 'Retail'


def main():
    apply = '--apply' in sys.argv
    mode = 'APPLY' if apply else 'DRY-RUN'
    print(f'=== Blues Pozisyon Guncelleme ({mode}) ===\n')

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app import create_app, db
    from app.models.ik import Calisan, Pozisyon, Departman
    from app.models.proje import Proje, HedefKadro

    app = create_app()

    with app.app_context():
        # 1. Efes Blues projesini bul
        proje = Proje.query.filter_by(ad=PROJE_ADI, is_deleted=False).first()
        if not proje:
            print(f'HATA: Proje bulunamadi: {PROJE_ADI}')
            return
        print(f'Proje: {proje.ad} (id={proje.id})')

        # 2. Merchandiser pozisyonunu bul
        eski_poz = Pozisyon.query.filter_by(ad=ESKI_POZISYON, is_deleted=False).first()
        if not eski_poz:
            print(f'HATA: Pozisyon bulunamadi: {ESKI_POZISYON}')
            return
        print(f'Eski pozisyon: {eski_poz.ad} (id={eski_poz.id})')

        # 3. Blues pozisyonunu bul veya olustur
        yeni_poz = Pozisyon.query.filter_by(ad=YENI_POZISYON, is_deleted=False).first()
        if yeni_poz:
            print(f'Blues pozisyonu mevcut: id={yeni_poz.id}')
        else:
            dept = Departman.query.filter_by(ad=DEPARTMAN_ADI, is_deleted=False).first()
            if not dept:
                print(f'HATA: Departman bulunamadi: {DEPARTMAN_ADI}')
                return
            print(f'Blues pozisyonu olusturulacak (departman: {dept.ad}, id={dept.id})')
            if apply:
                yeni_poz = Pozisyon(ad=YENI_POZISYON, departman_id=dept.id, aktif=True)
                db.session.add(yeni_poz)
                db.session.flush()
                print(f'  Blues pozisyonu olusturuldu: id={yeni_poz.id}')

        # 4. Efes Blues kadrolarina atanmis calisanlari bul
        blues_kadro_ids = [
            k.id for k in HedefKadro.query.filter_by(proje_id=proje.id, is_deleted=False).all()
        ]
        print(f'Blues kadro ID\'leri: {blues_kadro_ids}')

        calisanlar = Calisan.query.filter(
            Calisan.kadro_id.in_(blues_kadro_ids),
            Calisan.pozisyon_id == eski_poz.id,
            Calisan.is_deleted == False
        ).all()

        print(f'\nGuncellenecek calisan sayisi: {len(calisanlar)}\n')

        for c in calisanlar:
            print(f'  {c.sicil_no or "?"} - {c.ad} {c.soyad}: pozisyon {ESKI_POZISYON} -> {YENI_POZISYON}')
            if apply and yeni_poz:
                c.pozisyon_id = yeni_poz.id

        if apply:
            db.session.commit()
            print('\nDegisiklikler kaydedildi.')
        elif calisanlar:
            print(f'\nUygulamak icin: python3 scripts/blues_pozisyon.py --apply')


if __name__ == '__main__':
    main()
