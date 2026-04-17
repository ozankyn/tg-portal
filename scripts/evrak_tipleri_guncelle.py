"""
TG Portal - Evrak Tipleri Guncelleme Script'i
===============================================
Aday/Calisan evrak yükleme sayfalarındaki evrak tiplerini günceller.
Mevcut tipleri korur, eksikleri ekler, sırayı düzenler.

KULLANIM:
  cd /app && PYTHONPATH=/app python3 scripts/evrak_tipleri_guncelle.py --dry-run
  cd /app && PYTHONPATH=/app python3 scripts/evrak_tipleri_guncelle.py --apply
  cd /app && PYTHONPATH=/app python3 scripts/evrak_tipleri_guncelle.py --force-apply
"""
import sys
from datetime import datetime

# ============================================================
# HEDEF EVRAK TİPLERİ LİSTESİ
# ============================================================
# (ad, kod, kategori, zorunlu, sira)
EVRAK_TIPLERI = [
    ('Vesikalık Fotoğraf',                              'FOTO',        'kimlik',    True,  1),
    ('Sağlık Raporu',                                   'SAGLIK',      'saglik',    True,  2),
    ('Garanti Bankası IBAN',                             'IBAN',        'diger',     True,  3),
    ('Nüfus Cüzdanı',                                   'NUFUS',       'kimlik',    True,  4),
    ('Ehliyet (varsa)',                                  'EHLIYET',     'kimlik',    False, 5),
    ('Çalışma Belgesi',                                  'CALISMA',     'diger',     True,  6),
    ('Sabıka Kaydı',                                     'SABIKA',      'diger',     True,  7),
    ('İkametgah Belgesi',                                'IKAMETGAH',   'kimlik',    True,  8),
    ('Sürücü Belgesi Ceza Sorgulama',                    'SURUCU_CEZA', 'diger',     False, 9),
    ('SGK Hizmet Dökümü (4A)',                           'SGK_4A',      'diger',     True,  10),
    ('Diploma / Mezuniyet Belgesi',                      'DIPLOMA',     'egitim',    True,  11),
    ('Askerlik Durum Belgesi',                           'ASKERLIK',    'diger',     False, 12),
    ('Kişisel Verilerin Yurt Dışına Aktarımı Açık Rıza', 'KVKK_RIZA',   'sozlesme',  True,  13),
    ('Aylık Bordro Muvafakatnamesi',                     'BORDRO_MUV',  'sozlesme',  True,  14),
    ('KVKK Aydınlatma Metni',                            'KVKK_AYDIN',  'sozlesme',  True,  15),
    ('Gizlilik Taahhüdü',                                'GIZLILIK',    'sozlesme',  True,  16),
    ('KVKK Sözleşmesi',                                  'KVKK_SOZL',   'sozlesme',  True,  17),
]


def run(mode='dry-run'):
    from app import create_app, db
    from app.models.ik import EvrakTipi

    app = create_app()
    with app.app_context():
        print("=" * 80)
        print(f"  EVRAK TİPLERİ GÜNCELLEME [{mode.upper()}]")
        print(f"  Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)

        # Mevcut tipleri listele
        mevcut = EvrakTipi.query.order_by(EvrakTipi.sira).all()
        mevcut_kod = {t.kod: t for t in mevcut if t.kod}
        mevcut_ad = {t.ad: t for t in mevcut}

        print(f"\n[MEVCUT] {len(mevcut)} evrak tipi:")
        for t in mevcut:
            print(f"  id={t.id} kod={t.kod} sira={t.sira} zorunlu={t.zorunlu} aktif={t.aktif} -> '{t.ad}'")

        print(f"\n[HEDEF] {len(EVRAK_TIPLERI)} evrak tipi:")
        stats = {'yeni': 0, 'guncellenen': 0, 'deaktif': 0}

        for ad, kod, kategori, zorunlu, sira in EVRAK_TIPLERI:
            # Önce kod ile, sonra ad ile ara
            tip = mevcut_kod.get(kod) or mevcut_ad.get(ad)

            if tip:
                # Mevcut — güncelle
                changes = []
                if tip.kod != kod:
                    changes.append(f"kod: '{tip.kod}' -> '{kod}'")
                if tip.kategori != kategori:
                    changes.append(f"kategori: '{tip.kategori}' -> '{kategori}'")
                if tip.zorunlu != zorunlu:
                    changes.append(f"zorunlu: {tip.zorunlu} -> {zorunlu}")
                if tip.sira != sira:
                    changes.append(f"sira: {tip.sira} -> {sira}")
                if not tip.aktif:
                    changes.append("aktif: False -> True")

                if changes:
                    print(f"  [UPD] '{ad}' -> {', '.join(changes)}")
                    stats['guncellenen'] += 1
                    if mode == 'apply':
                        tip.ad = ad
                        tip.kod = kod
                        tip.kategori = kategori
                        tip.zorunlu = zorunlu
                        tip.sira = sira
                        tip.aktif = True
                        tip.updated_at = datetime.now()
                else:
                    print(f"  [OK]  '{ad}' (id={tip.id})")
            else:
                # Yeni
                print(f"  [YENI] '{ad}' (kod={kod}, kategori={kategori}, zorunlu={zorunlu}, sira={sira})")
                stats['yeni'] += 1
                if mode == 'apply':
                    tip = EvrakTipi(
                        ad=ad,
                        kod=kod,
                        kategori=kategori,
                        zorunlu=zorunlu,
                        sira=sira,
                        aktif=True,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    db.session.add(tip)

        # Hedefte olmayan mevcut tipleri deaktif et
        hedef_kodlar = {kod for _, kod, _, _, _ in EVRAK_TIPLERI}
        hedef_adlar = {ad for ad, _, _, _, _ in EVRAK_TIPLERI}
        print(f"\n[KONTROL] Hedefte olmayan mevcut tipler:")
        for t in mevcut:
            if t.kod not in hedef_kodlar and t.ad not in hedef_adlar:
                if t.aktif:
                    print(f"  [DEAKTIF] id={t.id} '{t.ad}' (kod={t.kod}) -> aktif=False")
                    stats['deaktif'] += 1
                    if mode == 'apply':
                        t.aktif = False
                        t.updated_at = datetime.now()
                else:
                    print(f"  [ZATEN DEAKTIF] id={t.id} '{t.ad}'")

        # COMMIT
        if mode == 'apply':
            db.session.commit()
            print(f"\n>>> TUM DEGISIKLIKLER KAYDEDILDI <<<")
        else:
            print(f"\n>>> DRY-RUN: Hicbir degisiklik yapilmadi <<<")

        # OZET
        print(f"\n{'=' * 80}")
        print(f"  OZET")
        print(f"  Yeni eklenen: {stats['yeni']}")
        print(f"  Güncellenen: {stats['guncellenen']}")
        print(f"  Deaktif edilen: {stats['deaktif']}")
        print(f"{'=' * 80}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Kullanim:")
        print("  python3 scripts/evrak_tipleri_guncelle.py --dry-run")
        print("  python3 scripts/evrak_tipleri_guncelle.py --apply")
        print("  python3 scripts/evrak_tipleri_guncelle.py --force-apply")
        sys.exit(1)

    arg = sys.argv[1]
    if arg == '--dry-run':
        run(mode='dry-run')
    elif arg == '--apply':
        print("DIKKAT: Evrak tipleri guncellenecek!")
        print("  - Yeni tipler eklenecek")
        print("  - Mevcut tipler guncellenecek")
        print("  - Hedefte olmayan tipler deaktif edilecek")
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
