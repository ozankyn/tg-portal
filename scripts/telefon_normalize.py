"""
TG Portal - Telefon Normalizasyon Script'i
==========================================
Mevcut DB'deki telefon numaralarını 05XXXXXXXXX formatına çevirir.

Boşluk/tire/parantez temizler, +90 ve 90 öneklerini 0'a indirger,
başında 0 olmayan 10 haneli numaralara 0 ekler.

Normalize edilemeyen (sabit hat, eksik hane, harf içeren) kayıtlar
DEĞİŞTİRİLMEZ; rapor sonunda ayrıca listelenir.

Tablolar: calisanlar, adaylar, users
  --tablo secenegi ile tek tablo da islenebilir.

KULLANIM:
  cd /app && PYTHONPATH=/app python3 scripts/telefon_normalize.py --dry-run
  cd /app && PYTHONPATH=/app python3 scripts/telefon_normalize.py --apply
  cd /app && PYTHONPATH=/app python3 scripts/telefon_normalize.py --apply --tablo calisanlar

Production:
  docker compose -f docker-compose.prod.yml exec web bash -c \
    "cd /app && PYTHONPATH=/app python3 scripts/telefon_normalize.py --dry-run"
"""
import sys
from datetime import datetime


def _kayitlari_isle(model, alan, etiket, mode):
    """Tek bir model/alan icin normalizasyon yapar, istatistik dondurur."""
    from app import db
    from app.utils import normalize_telefon

    sorgu = model.query.filter(getattr(model, alan).isnot(None))
    if hasattr(model, 'is_deleted'):
        sorgu = sorgu.filter(model.is_deleted == False)

    kayitlar = sorgu.all()
    duzeltilen, zaten_dogru, gecersiz = 0, 0, []
    numara_sahipleri = {}  # normalize sonrasi mukerrer tespiti icin

    for k in kayitlar:
        mevcut = (getattr(k, alan) or '').strip()
        if not mevcut:
            continue

        yeni = normalize_telefon(mevcut)
        if yeni is None:
            gecersiz.append((k.id, mevcut))
            continue

        ad = getattr(k, 'full_name', None) or f'ID {k.id}'
        numara_sahipleri.setdefault(yeni, []).append(f'{ad} (id={k.id})')

        if yeni == mevcut:
            zaten_dogru += 1
            continue

        print(f"  [{etiket}] {ad:<30} {mevcut!r:>20} -> {yeni}")
        duzeltilen += 1
        if mode == 'apply':
            setattr(k, alan, yeni)

    if mode == 'apply' and duzeltilen:
        db.session.commit()

    return {
        'toplam': len(kayitlar),
        'duzeltilen': duzeltilen,
        'zaten_dogru': zaten_dogru,
        'gecersiz': gecersiz,
        'mukerrer': {tel: sahipler for tel, sahipler in numara_sahipleri.items()
                     if len(sahipler) > 1},
    }


def run(mode='dry-run', tablo=None):
    from app import create_app
    from app.models.ik import Aday, Calisan
    from app.models.core import User

    hedefler = [
        ('calisanlar', Calisan, 'telefon', 'CALISAN'),
        ('adaylar', Aday, 'telefon', 'ADAY'),
        ('users', User, 'telefon', 'USER'),
    ]
    if tablo:
        hedefler = [h for h in hedefler if h[0] == tablo]
        if not hedefler:
            print(f"HATA: Bilinmeyen tablo '{tablo}'. "
                  f"Secenekler: calisanlar, adaylar, users")
            return 1

    app = create_app()
    with app.app_context():
        print("=" * 80)
        print(f"  TELEFON NORMALIZASYON [{mode.upper()}]")
        print(f"  Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)

        sonuclar = {}
        for tablo_ad, model, alan, etiket in hedefler:
            print(f"\n--- {tablo_ad} ---")
            sonuclar[tablo_ad] = _kayitlari_isle(model, alan, etiket, mode)

        print("\n" + "=" * 80)
        print("  OZET")
        print("=" * 80)
        toplam_duzeltilen = 0
        for tablo_ad, s in sonuclar.items():
            toplam_duzeltilen += s['duzeltilen']
            print(f"  {tablo_ad:<14} toplam={s['toplam']:<5} "
                  f"duzeltilen={s['duzeltilen']:<5} "
                  f"zaten_dogru={s['zaten_dogru']:<5} "
                  f"gecersiz={len(s['gecersiz']):<5} "
                  f"mukerrer={len(s['mukerrer'])}")

        # Normalize sonrasi ayni numaraya sahip kayitlar (elle incelenmeli)
        for tablo_ad, s in sonuclar.items():
            if not s['mukerrer']:
                continue
            print(f"\n  {tablo_ad} - AYNI NUMARAYI PAYLASAN KAYITLAR:")
            for tel, sahipler in s['mukerrer'].items():
                print(f"    {tel}: {', '.join(sahipler)}")

        # Normalize edilemeyenler - elle duzeltilmeli
        gecersizler = [(t, kid, tel) for t, s in sonuclar.items()
                       for kid, tel in s['gecersiz']]
        if gecersizler:
            print(f"\n  NORMALIZE EDILEMEYEN {len(gecersizler)} KAYIT "
                  f"(degistirilmedi, elle duzeltilmeli):")
            for tablo_ad, kid, tel in gecersizler:
                print(f"    {tablo_ad} id={kid}: {tel!r}")

        if mode == 'apply':
            print(f"\n  ✅ {toplam_duzeltilen} kayit guncellendi ve commit edildi.")
        else:
            print(f"\n  ℹ️  DRY-RUN: {toplam_duzeltilen} kayit duzeltilecek. "
                  f"Uygulamak icin --apply ile calistirin.")
        print("=" * 80)
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]

    if '--apply' in args:
        mode = 'apply'
    elif '--dry-run' in args:
        mode = 'dry-run'
    else:
        print(__doc__)
        sys.exit(1)

    tablo = None
    if '--tablo' in args:
        i = args.index('--tablo')
        if i + 1 >= len(args):
            print("HATA: --tablo icin deger verilmedi "
                  "(calisanlar | adaylar | users)")
            sys.exit(1)
        tablo = args[i + 1]

    sys.exit(run(mode, tablo))
