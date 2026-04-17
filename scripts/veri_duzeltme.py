"""
TG Portal - Veri Duzeltme Script'i
====================================
1. Departmani bos saha calisanlarina Retail departmanini ata
2. Kadro bilgisi olan calisanlarin pozisyon_id'sini kadrodaki pozisyon_adi'na gore esle
3. Proje isimlerini musteri bazli guncelle

KULLANIM:
  cd /app && PYTHONPATH=/app python3 scripts/veri_duzeltme.py --dry-run
  cd /app && PYTHONPATH=/app python3 scripts/veri_duzeltme.py --apply
  cd /app && PYTHONPATH=/app python3 scripts/veri_duzeltme.py --force-apply
"""
import sys
import re
from datetime import datetime

# ============================================================
# PROJE ISIM GUNCELLEMELERI
# ============================================================
# ============================================================
# KADRO POZISYON_ADI -> GENERIC POZISYON ESLESTIRME
# ============================================================
# Oncelik sirasi onemli: spesifik kurallar once, genel kurallar sonda
POZISYON_RULES = [
    # (pattern, generic_pozisyon_adi)
    (r'(?i)part\s*time\s*sse',          'Part Time SSE'),
    (r'(?i)sse\s*s[uü]perviz[oö]r',    'SSE Süpervizör'),
    (r'(?i)^sse\b',                     'SSE'),
    (r'(?i)part\s*time\s*sniper',       'Part Time Sniper'),
    (r'(?i)marka\s*el[cç]isi',         'Marka Elçisi'),
    (r'(?i)beylerbeyi',                 'Beylerbeyi Merchandiser'),
    (r'(?i)bf\b|brown\s*forman',        'BF Merchandiser'),
    (r'(?i)s[uü]perviz[oö]r',          'Süpervizör'),
    (r'(?i)yaya',                       'Yaya Merchandiser'),
    (r'(?i)merch|merchandiser',         'Merchandiser'),
]


def kadro_to_generic_pozisyon(pozisyon_adi):
    """HedefKadro.pozisyon_adi'ndan location bilgisini atarak generic pozisyon cikar.

    Ornekler:
      'SSE - İzmir'                -> 'SSE'
      'BF Araçlı Merch - Ankara'  -> 'BF Merchandiser'
      'SSE Süpervizör - İstanbul'  -> 'SSE Süpervizör'
      'Part Time SSE - Bursa'     -> 'Part Time SSE'
      'Beylerbeyi Araçlı - İzmir' -> 'Beylerbeyi Merchandiser'
      'Süpervizör - Antalya'      -> 'Süpervizör'
    """
    if not pozisyon_adi:
        return None
    for pattern, generic in POZISYON_RULES:
        if re.search(pattern, pozisyon_adi):
            return generic
    # Hicbir kurala uymadiysa - tire'den onceki kismi al
    base = pozisyon_adi.split(' - ')[0].strip()
    return base if base else pozisyon_adi


PROJE_RENAME = {
    1:  'Efes KK Merch',
    2:  'Efes Sniper',
    3:  'Efes Blues',
    6:  'PMI SSE',
    7:  'BF Merchandiser',
    9:  'Efes Marka Elçisi',
    10: 'Efes Modern Kanal',
}


def run(mode='dry-run'):
    from app import create_app, db
    from app.models.ik import Calisan, Departman, Pozisyon
    from app.models.proje import Proje, HedefKadro

    app = create_app()
    with app.app_context():
        print("=" * 80)
        print(f"  VERI DUZELTME [{mode.upper()}]")
        print(f"  Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)

        # ============================================================
        # ADIM 1: DEPARTMANI BOS CALISANLARA RETAIL ATA
        # ============================================================
        print("\n[1] DEPARTMAN ATAMASI (Retail)")
        print("-" * 40)

        retail = Departman.query.filter_by(ad='Retail', is_deleted=False).first()
        if not retail:
            print("  [!!!] Retail departmani bulunamadi!")
            return
        print(f"  Retail departman: id={retail.id}")

        # Departmani NULL olan ve ofis olmayan (kadro_id olan = saha) calisanlar
        bos_dept = Calisan.query.filter(
            Calisan.departman_id.is_(None),
            Calisan.is_deleted == False
        ).all()

        dept_count = 0
        for c in bos_dept:
            print(f"  [ATA] id={c.id} {c.ad} {c.soyad} (sicil={c.sicil_no}) -> departman_id={retail.id}")
            dept_count += 1
            if mode == 'apply':
                c.departman_id = retail.id
                c.updated_at = datetime.now()

        print(f"  Toplam: {dept_count} calisan")

        # ============================================================
        # ADIM 2: KADRO -> POZISYON ESLESTIRME
        # ============================================================
        print(f"\n[2] KADRO -> POZISYON ESLESTIRME")
        print("-" * 40)

        # Kadrosu olan calisanlari bul
        kadrolu = Calisan.query.filter(
            Calisan.kadro_id.isnot(None),
            Calisan.is_deleted == False
        ).all()
        print(f"  Kadrolu calisan: {len(kadrolu)}")

        # Kadro pozisyon_adi -> generic pozisyon mapping'i goster
        kadro_poz_ornek = {}
        for c in kadrolu:
            kadro = HedefKadro.query.get(c.kadro_id)
            if kadro and kadro.pozisyon_adi:
                generic = kadro_to_generic_pozisyon(kadro.pozisyon_adi)
                if kadro.pozisyon_adi not in kadro_poz_ornek:
                    kadro_poz_ornek[kadro.pozisyon_adi] = generic
        # Unique generic pozisyonlari listele
        unique_generics = sorted(set(kadro_poz_ornek.values()))
        print(f"  {len(kadro_poz_ornek)} farkli kadro pozisyon_adi -> {len(unique_generics)} generic pozisyon:")
        for g in unique_generics:
            ornekler = [k for k, v in kadro_poz_ornek.items() if v == g][:3]
            print(f"    '{g}' <- {ornekler}")

        # Mevcut pozisyonlari yukle
        poz_map = {}  # pozisyon_adi -> Pozisyon
        for p in Pozisyon.query.filter_by(is_deleted=False).all():
            poz_map[p.ad] = p

        poz_count = 0
        poz_created = 0
        for c in kadrolu:
            kadro = HedefKadro.query.get(c.kadro_id)
            if not kadro or not kadro.pozisyon_adi:
                continue

            poz_adi = kadro_to_generic_pozisyon(kadro.pozisyon_adi)
            if not poz_adi:
                continue

            # Pozisyon var mi?
            poz = poz_map.get(poz_adi)
            if not poz:
                print(f"  [YENI POZ] '{poz_adi}'")
                poz_created += 1
                if mode == 'apply':
                    poz = Pozisyon(
                        ad=poz_adi,
                        kod=poz_adi[:3].upper(),
                        departman_id=retail.id,
                        aktif=True,
                        is_deleted=False,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    db.session.add(poz)
                    db.session.flush()
                    poz_map[poz_adi] = poz

            # Pozisyon degisecek mi?
            poz_id = poz.id if poz else None
            if poz_id and c.pozisyon_id != poz_id:
                eski_poz = Pozisyon.query.get(c.pozisyon_id) if c.pozisyon_id else None
                eski_ad = eski_poz.ad if eski_poz else 'YOK'
                print(f"  [UPD] id={c.id} {c.ad} {c.soyad} | '{eski_ad}' -> '{poz_adi}'")
                poz_count += 1
                if mode == 'apply':
                    c.pozisyon_id = poz_id
                    c.updated_at = datetime.now()

        print(f"  Yeni pozisyon: {poz_created}")
        print(f"  Pozisyon guncellenen: {poz_count}")

        # ============================================================
        # ADIM 3: PROJE ISIM GUNCELLEMESI
        # ============================================================
        print(f"\n[3] PROJE ISIM GUNCELLEMESI")
        print("-" * 40)

        proje_count = 0
        for proje_id, yeni_ad in PROJE_RENAME.items():
            proje = Proje.query.get(proje_id)
            if not proje:
                print(f"  [!!!] Proje id={proje_id} bulunamadi")
                continue

            if proje.ad == yeni_ad:
                print(f"  [OK] id={proje_id} '{proje.ad}' zaten dogru")
                continue

            print(f"  [UPD] id={proje_id} '{proje.ad}' -> '{yeni_ad}'")
            proje_count += 1
            if mode == 'apply':
                proje.ad = yeni_ad
                proje.updated_at = datetime.now()

        print(f"  Guncellenen: {proje_count}")

        # ============================================================
        # COMMIT
        # ============================================================
        if mode == 'apply':
            db.session.commit()
            print(f"\n>>> TUM DEGISIKLIKLER KAYDEDILDI <<<")
        else:
            print(f"\n>>> DRY-RUN: Hicbir degisiklik yapilmadi <<<")

        # ============================================================
        # OZET
        # ============================================================
        print(f"\n{'=' * 80}")
        print(f"  OZET")
        print(f"  [1] Departman atanan: {dept_count}")
        print(f"  [2] Yeni pozisyon: {poz_created}, Pozisyon guncellenen: {poz_count}")
        print(f"  [3] Proje rename: {proje_count}")
        print(f"{'=' * 80}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Kullanim:")
        print("  python3 scripts/veri_duzeltme.py --dry-run")
        print("  python3 scripts/veri_duzeltme.py --apply")
        print("  python3 scripts/veri_duzeltme.py --force-apply")
        sys.exit(1)

    arg = sys.argv[1]
    if arg == '--dry-run':
        run(mode='dry-run')
    elif arg == '--apply':
        print("DIKKAT: Asagidaki islemler yapilacak:")
        print("  - Departmani bos calisanlara Retail atanacak")
        print("  - Kadro bazli pozisyon eslestirmesi yapilacak")
        print("  - 7 proje yeniden adlandirilacak")
        print()
        print("Devam etmek icin 'EVET' yazin: ", end='')
        onay = input().strip()
        if onay == 'EVET':
            run(mode='apply')
        else:
            print("Iptal edildi.")
    elif arg == '--force-apply':
        run(mode='apply')
    else:
        print(f"Bilinmeyen arguman: {arg}")
        sys.exit(1)
