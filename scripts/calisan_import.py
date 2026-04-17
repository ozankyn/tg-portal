"""
TG Portal - Calisan Import Script'i
=====================================
Excel verilerinden departman, pozisyon ve calisan kayitlari olusturur.
User hesaplariyla baglar.

KULLANIM:
  cd /app && PYTHONPATH=/app python3 scripts/calisan_import.py --dry-run
  cd /app && PYTHONPATH=/app python3 scripts/calisan_import.py --apply
"""
import sys
from datetime import datetime, date

# ============================================================
# DEPARTMANLAR
# ============================================================
DEPARTMANLAR = [
    # (ad, kod, ust_departman)
    ('Yönetim', 'YON', None),
    ('Retail', 'RET', None),
    ('Event', 'EVT', None),
    ('Muhasebe & Finans', 'MUH', None),
    ('İnsan Kaynakları', 'IK', None),
    ('Raporlama', 'RAP', None),
    ('Eğitim', 'EGT', None),
    ('Filo & Lojistik', 'FIL', None),
]

# ============================================================
# POZISYONLAR
# ============================================================
POZISYONLAR = [
    # (ad, kod, departman_adi, seviye)
    ('Ajans Başkanı', 'AB', 'Yönetim', 1),
    ('Direktör', 'DIR', 'Retail', 2),
    ('Genel Koordinatör', 'GK', 'Retail', 3),
    ('Event Müdürü', 'EM', 'Event', 3),
    ('Muhasebe Müdürü', 'MM', 'Muhasebe & Finans', 3),
    ('İK Takım Lideri', 'IKTL', 'İnsan Kaynakları', 3),
    ('Raporlama Takım Lideri', 'RTL', 'Raporlama', 4),
    ('Eğitim Takım Lideri', 'ETL', 'Eğitim', 4),
    ('Proje Koordinatörü', 'PK', 'Retail', 5),
    ('Saha Koordinatörü', 'SK', 'Retail', 5),
    ('Kıdemli Bütçe Uzmanı', 'KBU', 'Retail', 5),
    ('İK Uzmanı', 'IKU', 'İnsan Kaynakları', 5),
    ('Kıdemli Muhasebe Uzmanı', 'KMU', 'Muhasebe & Finans', 5),
    ('Muhasebe Uzman Yardımcısı', 'MUY', 'Muhasebe & Finans', 6),
    ('Ofis Sorumlusu', 'OFS', 'Muhasebe & Finans', 6),
    ('Raporlama Uzmanı', 'RU', 'Raporlama', 5),
    ('Eğitim Uzmanı', 'EU', 'Eğitim', 5),
    ('Filo Yöneticisi', 'FY', 'Filo & Lojistik', 4),
    ('Depo Sorumlusu', 'DS', 'Retail', 5),
    ('Lojistik ve Ulaştırma', 'LU', 'Event', 5),
    ('Sanat Yönetmeni', 'SY', 'Event', 5),
    ('Proje Asistanı', 'PA', 'Event', 6),
]

# ============================================================
# CALISANLAR (Excel'den)
# ============================================================
CALISANLAR = [
    # (email, ad, soyad, sicil_no, tc_kimlik, pozisyon, departman, yonetici_ad,
    #  sgk_sube, sgk_no, kidem_tarihi, giris_tarihi, telefon, dogum_tarihi,
    #  cinsiyet, egitim_durumu, yemek_karti, beden, kargo_subesi, adres)
    ('fatihkayan@teamguerilla.com', 'FATİH', 'KAYAN', '', '', 'Ajans Başkanı', 'Yönetim', None,
     '', '', None, None, '', None, 'Erkek', '', '', '', '', ''),
    ('ozanerenkayan@teamguerilla.com', 'OZAN EREN', 'KAYAN', 'T.34.0269', '44446981202', 'Direktör', 'Retail', 'Fatih Kayan',
     'MALTEPE TG', '27311080812330590343058000', '2015-11-13', '2024-09-23', '5497844529', '1988-11-13', 'Erkek', '', '6036819058223627', '', '', ''),
    ('hakanalpan@teamguerilla.com', 'HAKAN', 'ALPAN', 'T.34.3088', '19621477108', 'Genel Koordinatör', 'Retail', 'Ozan Eren Kayan',
     'MALTEPE TG', '27311080812330590343058000', '2007-11-22', '2026-02-04', '5546038386', '1981-03-04', 'Erkek', 'Lise', '6036819058223437', '', '', ''),
    ('ebrumeric@teamguerilla.com', 'EBRU', 'MERİÇ', 'E.34.0011', '23834180076', 'Event Müdürü', 'Event', 'Fatih Kayan',
     'MALTEPE EMİRA', '27311080812330600343075000', '2014-03-22', '2017-04-01', '5549941094', '1985-09-12', 'Kadın', '', '6036819058223643', '', '', ''),
    ('aysetilki@teamguerilla.com', 'AYŞE', 'TİLKİ', 'E.34.0053', '45583350036', 'Muhasebe Müdürü', 'Muhasebe & Finans', 'Fatih Kayan',
     'MALTEPE EMİRA', '27311080812330600343075000', None, '2023-04-24', '', '1971-02-25', 'Kadın', '', '6036819058223700', '', '', ''),
    ('serenkadiz@teamguerilla.com', 'SEREN', 'KADIZ', 'T.34.3016', '27091782714', 'İK Takım Lideri', 'İnsan Kaynakları', 'Fatih Kayan',
     'MALTEPE TG', '27311080812330590343058000', None, '2025-05-05', '5389878125', '1994-04-05', 'Kadın', 'Fakülte/Lisans', '6036819071095838', 'm', '', ''),
    ('abdurrahmangulec@teamguerilla.com', 'ABDURRAHMAN', 'GÜLEÇ', 'T.34.0262', '64615114200', 'Raporlama Takım Lideri', 'Raporlama', 'Ozan Eren Kayan',
     'MALTEPE TG', '27311080812330590343058000', '2022-01-27', '2024-09-23', '5498039712', '1991-08-22', 'Erkek', '', '6036819058223551', '', '', ''),
    ('oguzhangumus@teamguerilla.com', 'OĞUZHAN', 'GÜMÜŞ', 'T.34.0276', '43801220314', 'Eğitim Takım Lideri', 'Eğitim', 'Ozan Eren Kayan',
     'MALTEPE TG', '27311080812330590343058000', '2020-07-06', '2024-09-23', '5319124856', '1994-01-21', 'Erkek', '', '6036819058223569', '', '', ''),
    ('neziheozer@teamguerilla.com', 'NEZİHE', 'ÖZER', 'T.10.0156', '24395101746', 'İK Uzmanı', 'İnsan Kaynakları', 'Seren Kadız',
     'BALIKESİR TG', '27311010112035200100426000', None, '2024-03-28', '5346667098', '1998-10-27', 'Kadın', 'Fakülte/Lisans', '6036819061813448', 'XL', '', ''),
    ('oznurciftci@teamguerilla.com', 'ÖZNUR', 'ÇİFTÇİ', 'T.34.0271', '21182196336', 'İK Uzmanı', 'İnsan Kaynakları', 'Seren Kadız',
     'MALTEPE TG', '27311080812330590343058000', '2023-02-20', '2024-09-23', '5465016074', '1997-09-22', 'Kadın', '', '6036819058223494', '', '', ''),
    ('mervebaypayman@teamguerilla.com', 'MERVE', 'BAY PAYMAN', 'T.34.0282', '50449619356', 'Kıdemli Muhasebe Uzmanı', 'Muhasebe & Finans', 'Ayşe Tilki',
     'MALTEPE TG', '27311080812330590343058000', '2018-06-06', '2024-09-23', '5498039704', '1995-10-16', 'Kadın', '', '6036819058223668', '', '', ''),
    ('nurdanserav@teamguerilla.com', 'NURDAN ŞERAV', 'UÇAR', 'T.34.3040', '31681109010', 'Muhasebe Uzman Yardımcısı', 'Muhasebe & Finans', 'Ayşe Tilki',
     'MALTEPE TG', '27311080812330590343058000', None, '2025-10-16', '5536457002', '1991-01-25', 'Kadın', 'Fakülte/Lisans', '', '', '', ''),
    ('gizemgulpinar@teamguerilla.com', 'GİZEM GÜLPINAR', 'KAYA', 'T.34.3041', '14741423714', 'Muhasebe Uzman Yardımcısı', 'Muhasebe & Finans', 'Ayşe Tilki',
     'MALTEPE TG', '27311080812330590343058000', None, '2025-10-16', '5367662277', '1990-09-29', 'Kadın', 'Fakülte/Lisans', '', '', '', ''),
    ('fatiyildirim@teamguerilla.com', 'FATİ', 'YILDIRIM', 'E.35.0274', '24692154698', 'Ofis Sorumlusu', 'Muhasebe & Finans', 'Ayşe Tilki',
     'İZMİR EMİRA', '27311010115771190353045000', '2008-03-03', '2025-05-20', '5062899136', '1971-03-20', 'Kadın', '', '6036819058223726', '', '', ''),
    ('burakdurgun@teamguerilla.com', 'BURAK', 'DURGUN', 'T.35.0319', '55417462880', 'Filo Yöneticisi', 'Filo & Lojistik', 'Ozan Eren Kayan',
     'İZMİR TG', '27311010113830230353078000', None, '2025-09-15', '5542709484', '1994-06-17', 'Erkek', 'Fakülte/Lisans', '6036819074129832', '', '', ''),
    ('furkanbicakci@teamguerilla.com', 'FURKAN', 'BIÇAKÇI', 'T.34.1.001', '29389991280', 'Depo Sorumlusu', 'Retail', 'Hakan Alpan',
     'FERHATPAŞA TG', '27311070716498980344198000', None, '2025-03-21', '5307019836', '1997-03-28', 'Erkek', 'Lise', '6036819069925319', 'xl', '', ''),
    ('erdiaslantas@teamguerilla.com', 'ERDİ', 'ASLANTAŞ', 'T.34.0265', '43583023806', 'Proje Koordinatörü', 'Retail', 'Ozan Eren Kayan',
     'MALTEPE TG', '27311080812330590343058000', '2017-10-12', '2024-09-23', '5546038387', '1989-10-10', 'Erkek', '', '6036819058223445', '', '', ''),
    ('havvanurmahmutoglu@teamguerilla.com', 'HAVVANUR', 'MAHMUTOĞLU', 'T.34.3027', '40408950538', 'Proje Koordinatörü', 'Retail', 'Ozan Eren Kayan',
     'MALTEPE TG', '27311080812330590343058000', '2025-05-21', '2025-09-01', '5071885243', '1998-03-09', 'Kadın', 'Yüksek okul', '6036819071413908', 'S', '', ''),
    ('halilkaraoglan@teamguerilla.com', 'HALİL', 'KARAOĞLAN', 'T.34.3087', '10594356698', 'Proje Koordinatörü', 'Event', 'Ebru Meriç',
     'MALTEPE TG', '27311080812330590343058000', None, '2026-02-02', '5546038388', '1987-03-23', 'Erkek', 'Lise', '6036819058223593', 'L', '', ''),
    ('erdemmujdeci@teamguerilla.com', 'AHMET ERDEM', 'MÜJDECİ', 'T.34.3035', '30385889846', 'Proje Asistanı', 'Event', 'Ebru Meriç',
     'MALTEPE TG', '27311080812330590343058000', None, '2025-09-26', '5052522201', '2003-06-16', 'Erkek', 'Fakülte/Lisans', '6036819074333103', '', '', ''),
    ('yakupates@teamguerilla.com', 'YAKUP', 'ATEŞ', 'T.10.0029', '55957250176', 'Saha Koordinatörü', 'Retail', 'Hakan Alpan',
     'BALIKESİR TG', '27311010112035200100426000', '2017-01-03', '2022-03-01', '5446380383', '1987-06-20', 'Erkek', 'Fakülte/Lisans', '6036819058222397', 'L', '', ''),
    ('ufukdinc@teamguerilla.com', 'UFUK', 'DİNÇ', 'T.34.3086', '13138765802', 'Saha Koordinatörü', 'Retail', 'Hakan Alpan',
     'MALTEPE TG', '27311080812330590343058000', None, '2026-01-12', '5546038388', '1987-03-23', 'Erkek', 'Lise', '6036819058221415', 'L', '', ''),
    ('abidinkazimsifoglu@teamguerilla.com', 'ABİDİN KAZIM', 'SİFOĞLU', 'T.34.3019', '40705942786', 'Saha Koordinatörü', 'Retail', 'Hakan Alpan',
     'MALTEPE TG', '27311080812330590343058000', '2020-03-01', '2025-09-01', '5498039715', '1983-10-05', 'Erkek', 'Fakülte/Lisans', '6036819058222116', 'XXL', '', ''),
    ('muhammetaslan@teamguerilla.com', 'MUHAMMET', 'ASLAN', 'T.59.0199', '47044939224', 'Saha Koordinatörü', 'Retail', 'Ozan Eren Kayan',
     'TEKİRDAĞ TG', '27311010111354980590645000', None, '2025-11-10', '5375464228', '1991-05-07', 'Erkek', 'Fakülte/Lisans', '6036819075282457', '', '', ''),
    ('burcuhan@teamguerilla.com', 'BURCU', 'HAN', 'T.34.3028', '14999822734', 'Kıdemli Bütçe Uzmanı', 'Retail', 'Ozan Eren Kayan',
     'MALTEPE TG', '27311080812330590343058000', None, '2025-09-01', '5419263944', '1992-02-24', 'Kadın', 'Fakülte/Lisans', '6036819073931790', '', '', ''),
    ('mustafacangok@teamguerilla.com', 'MUSTAFA CAN', 'GÖK', 'T.34.3025', '22835217156', 'Raporlama Uzmanı', 'Raporlama', 'Abdurrahman Güleç',
     'MALTEPE TG', '27311080812330590343058000', '2024-12-30', '2025-09-01', '5516439261', '2001-08-13', 'Erkek', 'Fakülte/Lisans', '6036819067135890', 'm', '', ''),
    ('erkantoraman@teamguerilla.com', 'ERKAN', 'TORAMAN', 'T.34.3043', '54904354554', 'Raporlama Uzmanı', 'Raporlama', 'Abdurrahman Güleç',
     'MALTEPE TG', '27311080812330590343058000', None, '2025-10-20', '5467626367', '1988-08-12', 'Erkek', 'Fakülte/Lisans', '6036819074937317', '', '', ''),
    ('ozanmert@teamguerilla.com', 'OZAN', 'MERT', 'T.34.3023', '65914311796', 'Eğitim Uzmanı', 'Eğitim', 'Oğuzhan Gümüş',
     'MALTEPE TG', '27311080812330590343058000', '2024-10-22', '2025-09-01', '5447497534', '1997-06-27', 'Erkek', 'Fakülte/Lisans', '6036819065485946', 'XL', '', ''),
    ('metegencer@teamguerilla.com', 'METE', 'GENCER', 'E.59.0289', '11702660676', 'Lojistik ve Ulaştırma', 'Event', 'Ebru Meriç',
     'TEKİRDAĞ EMİRA', '27311010111354990590602000', '2013-04-03', '2025-02-19', '5423612280', '1965-09-16', 'Erkek', '', '6036819058223544', '', '', ''),
    ('boragelisken@teamguerilla.com', 'BORA', 'GELİŞKEN', 'T.34.0264', '23798651810', 'Sanat Yönetmeni', 'Event', 'Ebru Meriç',
     'MALTEPE TG', '27311080812330590343058000', '2012-07-12', '2024-09-23', '5536963043', '1985-07-02', 'Erkek', 'Yüksek okul', '6036819058223536', '', '', ''),
]

# User email -> Calisan email eslestirme (farkli email kullananlar)
USER_CALISAN_MAP = {
    'ozanerenkayan@gmail.com': 'ozanerenkayan@teamguerilla.com',
    'ozankayan@teamguerilla.com': 'ozanerenkayan@teamguerilla.com',
}

def parse_date(val):
    if not val:
        return None
    if isinstance(val, (date, datetime)):
        return val
    try:
        return datetime.strptime(val, '%Y-%m-%d').date()
    except:
        return None

def run(mode='dry-run'):
    from app import create_app, db
    from app.models.core import User
    from app.models.ik import Calisan, Departman, Pozisyon

    app = create_app()
    with app.app_context():
        print("=" * 80)
        print(f"  CALISAN IMPORT [{mode.upper()}]")
        print(f"  Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)

        # ADIM 1: DEPARTMANLAR
        print("\n[1] DEPARTMANLAR")
        print("-" * 40)
        dept_map = {}
        for ad, kod, ust in DEPARTMANLAR:
            d = Departman.query.filter_by(ad=ad).first()
            if d:
                print(f"  [VAR] {ad} (id={d.id})")
                dept_map[ad] = d
            else:
                print(f"  [YENI] {ad} ({kod})")
                if mode == 'apply':
                    d = Departman(ad=ad, kod=kod, aktif=True,
                                 created_at=datetime.now(), updated_at=datetime.now(),
                                 is_deleted=False)
                    db.session.add(d)
                    db.session.flush()
                dept_map[ad] = d

        # ADIM 2: POZISYONLAR
        print(f"\n[2] POZISYONLAR")
        print("-" * 40)
        poz_map = {}
        for ad, kod, dept_ad, seviye in POZISYONLAR:
            p = Pozisyon.query.filter_by(ad=ad).first()
            if p:
                print(f"  [VAR] {ad} (id={p.id})")
                poz_map[ad] = p
            else:
                dept = dept_map.get(dept_ad)
                dept_id = dept.id if dept else None
                print(f"  [YENI] {ad} -> {dept_ad} (dept_id={dept_id})")
                if mode == 'apply':
                    p = Pozisyon(ad=ad, kod=kod, departman_id=dept_id, seviye=seviye,
                                aktif=True, created_at=datetime.now(), updated_at=datetime.now(),
                                is_deleted=False)
                    db.session.add(p)
                    db.session.flush()
                poz_map[ad] = p

        # ADIM 3: CALISANLAR
        print(f"\n[3] CALISANLAR")
        print("-" * 40)
        calisan_map = {}  # email -> calisan

        for row in CALISANLAR:
            (email, ad, soyad, sicil, tc, poz_ad, dept_ad, yon_ad,
             sgk_sube, sgk_no, kidem, giris, telefon, dogum,
             cinsiyet, egitim, yemek, beden, kargo, adres) = row

            # Mevcut calisan kontrolu (email ile)
            c = Calisan.query.filter_by(email=email).first()
            if c:
                print(f"  [VAR] {ad} {soyad} (id={c.id}, email={email})")
                calisan_map[email] = c
                if mode == 'apply':
                    # Departman ve pozisyon guncelle
                    dept = dept_map.get(dept_ad)
                    poz = poz_map.get(poz_ad)
                    if dept:
                        c.departman_id = dept.id
                    if poz:
                        c.pozisyon_id = poz.id
                    c.updated_at = datetime.now()
                continue

            dept = dept_map.get(dept_ad)
            poz = poz_map.get(poz_ad)
            dept_id = dept.id if dept else None
            poz_id = poz.id if poz else None

            print(f"  [YENI] {ad} {soyad} | {poz_ad} | {dept_ad}")
            print(f"         sicil={sicil} tc={tc} tel={telefon} dogum={dogum}")

            if mode == 'apply':
                c = Calisan(
                    sicil_no=sicil or None,
                    ad=ad,
                    soyad=soyad,
                    tc_kimlik=tc or None,
                    dogum_tarihi=parse_date(dogum),
                    cinsiyet=cinsiyet or None,
                    email=email,
                    telefon=telefon or None,
                    adres=adres.strip() if adres else None,
                    departman_id=dept_id,
                    pozisyon_id=poz_id,
                    kidem_tarihi=parse_date(kidem),
                    egitim_durumu=egitim or None,
                    yemek_karti=yemek or None,
                    beden=beden or None,
                    kargo_subesi=kargo or None,
                    ise_baslama=parse_date(giris),
                    durum='CalisanDurumu.AKTIF',
                    is_deleted=False,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.session.add(c)
                db.session.flush()
                calisan_map[email] = c

        # ADIM 4: YONETICI BAGLANTILARI
        print(f"\n[4] YONETICI BAGLANTILARI")
        print("-" * 40)
        if mode == 'apply':
            for row in CALISANLAR:
                email, ad, soyad = row[0], row[1], row[2]
                yon_ad = row[7]
                if not yon_ad:
                    continue
                calisan = calisan_map.get(email)
                if not calisan:
                    continue
                # Yoneticiyi bul
                yon_parts = yon_ad.split()
                if len(yon_parts) >= 2:
                    yonetici = None
                    for e, c in calisan_map.items():
                        if c and c.ad and c.soyad:
                            full = f"{c.ad} {c.soyad}".upper()
                            if yon_parts[0].upper() in full and yon_parts[-1].upper() in full:
                                yonetici = c
                                break
                    if yonetici:
                        calisan.yonetici_id = yonetici.id
                        print(f"  {ad} {soyad} -> {yonetici.ad} {yonetici.soyad} (id={yonetici.id})")
                    else:
                        print(f"  {ad} {soyad} -> '{yon_ad}' BULUNAMADI")
        else:
            for row in CALISANLAR:
                if row[7]:
                    print(f"  {row[1]} {row[2]} -> {row[7]}")

        # ADIM 5: USER <-> CALISAN BAGLANTISI
        print(f"\n[5] USER <-> CALISAN BAGLANTISI")
        print("-" * 40)
        users = User.query.filter_by(is_deleted=False).all()
        for u in users:
            # Hangi calisan email'ine eslenecek?
            calisan_email = USER_CALISAN_MAP.get(u.email, u.email)
            calisan = calisan_map.get(calisan_email)
            if not calisan:
                # DB'den ara
                calisan = Calisan.query.filter_by(email=calisan_email).first()

            if calisan:
                c_id = calisan.id if hasattr(calisan, 'id') and calisan.id else '?'
                if u.calisan_id != (calisan.id if calisan else None):
                    print(f"  [BAGLA] {u.email} -> calisan_id={c_id} ({calisan.ad} {calisan.soyad})")
                    if mode == 'apply':
                        u.calisan_id = calisan.id
                else:
                    print(f"  [OK] {u.email} -> calisan_id={c_id}")
            else:
                print(f"  [ATLA] {u.email} -> calisan kaydi yok")

        # COMMIT
        if mode == 'apply':
            db.session.commit()
            print(f"\n>>> TUM DEGISIKLIKLER KAYDEDILDI <<<")
        else:
            print(f"\n>>> DRY-RUN: Hicbir degisiklik yapilmadi <<<")

        # OZET
        print(f"\n{'=' * 80}")
        print(f"  OZET")
        print(f"  Departman: {len(DEPARTMANLAR)}")
        print(f"  Pozisyon: {len(POZISYONLAR)}")
        print(f"  Calisan: {len(CALISANLAR)}")
        print(f"{'=' * 80}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Kullanim:")
        print("  python3 scripts/calisan_import.py --dry-run")
        print("  python3 scripts/calisan_import.py --apply")
        sys.exit(1)

    arg = sys.argv[1]
    if arg == '--dry-run':
        run(mode='dry-run')
    elif arg == '--apply':
        print("DIKKAT: Calisan kayitlari olusturulacak!")
        print("Devam etmek icin 'EVET' yazin: ", end='')
        onay = input().strip()
        if onay == 'EVET':
            run(mode='apply')
        else:
            print("Iptal edildi.")
    elif arg == '--force-apply':
        run(mode='apply')
    else:
        print(f"Bilinmeyen: {arg}")
        sys.exit(1)
