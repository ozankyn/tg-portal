"""
TG Portal - Rol & Kullanici Kurulum Script'i
==============================================
KULLANIM:
  python3 scripts/rol_kurulum.py --dry-run
  python3 scripts/rol_kurulum.py --apply
  python3 scripts/rol_kurulum.py --export-passwords
"""
import sys
import secrets
import string
from datetime import datetime
from werkzeug.security import generate_password_hash

ROL_PERMISSION_MATRIX = {
    'Sistem Yoneticisi': {
        'aciklama': 'Tum sistem yetkilerine sahip ust duzey yonetici',
        'permissions': '*',
    },
    'Ajans Baskani': {
        'aciklama': 'Tum modulleri goruntule, ust seviye onay yetkisi',
        'permissions': {
            'calisan': ['view'], 'egitim': ['view'], 'filo': ['view'], 'ik': ['view'],
            'masraf': ['view', 'onay'], 'onay': ['view', 'islem'], 'proje': ['view'],
            'rapor': ['view', 'export'], 'satinalma': ['view', 'onay'],
            'sozlesme': ['view', 'onay'], 'talep': ['view', 'onay'], 'tedarikci': ['view'],
        },
    },
    'Direktor': {
        'aciklama': 'Departman direktoru, genis operasyonel yetki',
        'permissions': {
            'calisan': ['view', 'create', 'edit'], 'egitim': ['view', 'create', 'edit'],
            'filo': ['view', 'create', 'edit', 'bakim', 'yakit'], 'ik': ['view'],
            'masraf': ['view', 'create', 'onay'], 'onay': ['view', 'islem'],
            'proje': ['view', 'create', 'edit', 'kadro'], 'rapor': ['view', 'export'],
            'satinalma': ['view', 'create', 'onay'], 'sozlesme': ['view', 'onay'],
            'talep': ['view', 'create', 'onay'], 'tedarikci': ['view', 'create', 'edit'],
        },
    },
    'Direktor Yardimcisi': {
        'aciklama': 'Direktor yardimcisi, Retail tam yetki, diger moduller onay dahil',
        'permissions': {
            'calisan': ['view', 'create', 'edit'], 'egitim': ['view'], 'filo': ['view'],
            'ik': ['view'], 'masraf': ['view', 'create', 'onay'], 'onay': ['view', 'islem'],
            'proje': ['view', 'create', 'edit', 'kadro'], 'rapor': ['view'],
            'satinalma': ['view', 'create', 'onay'], 'sozlesme': ['view', 'onay'],
            'talep': ['view', 'create', 'onay'], 'tedarikci': ['view'],
        },
    },
    'Departman Muduru': {
        'aciklama': 'Departman muduru, kendi alaninda tam yetki + onay',
        'permissions': {
            'calisan': ['view', 'edit'], 'egitim': ['view'], 'filo': ['view'], 'ik': ['view'],
            'masraf': ['view', 'create', 'onay'], 'onay': ['view', 'islem'],
            'proje': ['view', 'create', 'edit'], 'rapor': ['view', 'export'],
            'satinalma': ['view', 'create', 'onay'], 'sozlesme': ['view', 'onay'],
            'talep': ['view', 'create', 'onay'], 'tedarikci': ['view'],
        },
    },
    'Takim Lideri': {
        'aciklama': 'Takim lideri, kendi modulunde tam yetki',
        'permissions': {
            'calisan': ['view'], 'egitim': ['view', 'create', 'edit'],
            'masraf': ['view', 'create'], 'onay': ['view'], 'proje': ['view'],
            'rapor': ['view', 'export'], 'satinalma': ['view', 'create'],
            'talep': ['view', 'create'], 'tedarikci': ['view'],
        },
    },
    'IK Uzmani': {
        'aciklama': 'IK operasyonlari, calisan yonetimi, egitim katilim',
        'permissions': {
            'calisan': ['view', 'create', 'edit'], 'egitim': ['view', 'katilim'],
            'ik': ['view', 'create', 'edit', 'izin', 'sozlesme'],
            'masraf': ['view', 'create'], 'onay': ['view'], 'proje': ['view'],
            'rapor': ['view'], 'sozlesme': ['view', 'create'], 'talep': ['view', 'create'],
        },
    },
    'Muhasebe Uzmani': {
        'aciklama': 'Masraf, tedarikci, satinalma islemleri',
        'permissions': {
            'calisan': ['view'], 'filo': ['view'],
            'masraf': ['view', 'create', 'edit', 'onay'], 'onay': ['view'],
            'proje': ['view'], 'rapor': ['view', 'export'],
            'satinalma': ['view', 'create', 'onay'], 'sozlesme': ['view'],
            'talep': ['view', 'create'], 'tedarikci': ['view', 'create', 'edit'],
        },
    },
    'Filo Yoneticisi': {
        'aciklama': 'Filo modulu tam yetki, tedarikci yonetimi',
        'permissions': {
            'calisan': ['view'],
            'filo': ['view', 'create', 'edit', 'bakim', 'yakit', 'kaza', 'sigorta', 'teslim', 'ceza', 'admin'],
            'masraf': ['view', 'create'], 'onay': ['view'], 'proje': ['view'],
            'rapor': ['view'], 'satinalma': ['view', 'create'],
            'talep': ['view', 'create'], 'tedarikci': ['view', 'create', 'edit'],
        },
    },
    'Proje Koordinatoru': {
        'aciklama': 'Proje yonetimi, calisan atama, kadro planlama',
        'permissions': {
            'calisan': ['view', 'create', 'edit'], 'egitim': ['view'], 'filo': ['view'],
            'masraf': ['view', 'create'], 'onay': ['view'],
            'proje': ['view', 'create', 'edit', 'kadro'], 'rapor': ['view'],
            'satinalma': ['view', 'create'], 'talep': ['view', 'create'], 'tedarikci': ['view'],
        },
    },
    'Saha Koordinatoru': {
        'aciklama': 'Saha operasyonlari, kendi proje ekibi (Faz 2: scope filtreleme)',
        'permissions': {
            'calisan': ['view', 'edit'], 'egitim': ['view', 'katilim'], 'filo': ['view'],
            'masraf': ['view', 'create'], 'onay': ['view'], 'proje': ['view'],
            'talep': ['view', 'create'],
        },
    },
    'Butce Raporlama Uzmani': {
        'aciklama': 'Raporlama ve analiz, genis goruntuleme yetkisi',
        'permissions': {
            'calisan': ['view'], 'filo': ['view'], 'masraf': ['view'], 'proje': ['view'],
            'rapor': ['view', 'export', 'admin'], 'satinalma': ['view'],
            'talep': ['view'], 'tedarikci': ['view'],
        },
    },
    'Egitim Uzmani': {
        'aciklama': 'Egitim modulu tam yetki, calisan goruntuleme',
        'permissions': {
            'calisan': ['view'], 'egitim': ['view', 'create', 'edit', 'katilim'],
            'masraf': ['view', 'create'], 'proje': ['view'], 'rapor': ['view'],
            'satinalma': ['view', 'create'], 'talep': ['view', 'create'],
        },
    },
    'Lojistik Uzmani': {
        'aciklama': 'Lojistik operasyonlari, tedarikci ve filo goruntuleme',
        'permissions': {
            'filo': ['view'], 'masraf': ['view', 'create'], 'proje': ['view'],
            'satinalma': ['view', 'create'], 'talep': ['view', 'create'],
            'tedarikci': ['view', 'create', 'edit'],
        },
    },
    'Tasarimci Kreatif': {
        'aciklama': 'Tasarim ve kreatif isler (Faz 2: Event departman scope)',
        'permissions': {
            'calisan': ['view'], 'egitim': ['view', 'create', 'edit'], 'proje': ['view'],
            'masraf': ['view', 'create'], 'satinalma': ['view', 'create'],
            'talep': ['view', 'create'], 'tedarikci': ['view'],
        },
    },
}

KULLANICILAR = [
    ('ozanerenkayan@gmail.com', 'Ozan Eren', 'Kayan', 'Sistem Yoneticisi'),
    ('ozankayan@teamguerilla.com', 'Ozan Eren', 'Kayan', 'Direktor'),
    ('fatihkayan@teamguerilla.com', 'Fatih', 'Kayan', 'Ajans Baskani'),
    ('hakanalpan@teamguerilla.com', 'Hakan', 'Alpan', 'Direktor Yardimcisi'),
    ('ebrumeric@teamguerilla.com', 'Ebru', 'Meric', 'Departman Muduru'),
    ('aysetilki@teamguerilla.com', 'Ayse', 'Tilki', 'Departman Muduru'),
    ('serenkadiz@teamguerilla.com', 'Seren', 'Kadiz', 'Departman Muduru'),
    ('abdurrahmangulec@teamguerilla.com', 'Abdurrahman', 'Gulec', 'Takim Lideri'),
    ('oguzhangumus@teamguerilla.com', 'Oguzhan', 'Gumus', 'Takim Lideri'),
    ('neziheozer@teamguerilla.com', 'Nezihe', 'Ozer', 'IK Uzmani'),
    ('oznurciftci@teamguerilla.com', 'Oznur', 'Ciftci', 'IK Uzmani'),
    ('mervebaypayman@teamguerilla.com', 'Merve', 'Bay Payman', 'Muhasebe Uzmani'),
    ('nurdanserav@teamguerilla.com', 'Nurdan Serav', 'Ucar', 'Muhasebe Uzmani'),
    ('gizemgulpinar@teamguerilla.com', 'Gizem', 'Gulpinar Kaya', 'Muhasebe Uzmani'),
    ('fatiyildirim@teamguerilla.com', 'Fati', 'Yildirim', 'Muhasebe Uzmani'),
    ('burakdurgun@teamguerilla.com', 'Burak', 'Durgun', 'Filo Yoneticisi'),
    ('furkanbicakci@teamguerilla.com', 'Furkan', 'Bicakci', 'Filo Yoneticisi'),
    ('erdiaslantas@teamguerilla.com', 'Erdi', 'Aslantas', 'Proje Koordinatoru'),
    ('havvanurmahmutoglu@teamguerilla.com', 'Havvanur', 'Mahmutoglu', 'Proje Koordinatoru'),
    ('halilkaraoglan@teamguerilla.com', 'Halil', 'Karaoglan', 'Proje Koordinatoru'),
    ('erdemmujdeci@teamguerilla.com', 'Ahmet Erdem', 'Mujdeci', 'Proje Koordinatoru'),
    ('yakupates@teamguerilla.com', 'Yakup', 'Ates', 'Saha Koordinatoru'),
    ('ufukdinc@teamguerilla.com', 'Ufuk', 'Dinc', 'Saha Koordinatoru'),
    ('abidinkazimsifoglu@teamguerilla.com', 'Abidin Kazim', 'Sifoglu', 'Saha Koordinatoru'),
    ('muhammetaslan@teamguerilla.com', 'Muhammet', 'Aslan', 'Saha Koordinatoru'),
    ('burcuhan@teamguerilla.com', 'Burcu', 'Han', 'Butce Raporlama Uzmani'),
    ('mustafacangok@teamguerilla.com', 'Mustafa Can', 'Gok', 'Butce Raporlama Uzmani'),
    ('erkantoraman@teamguerilla.com', 'Erkan', 'Toraman', 'Butce Raporlama Uzmani'),
    ('ozanmert@teamguerilla.com', 'Ozan', 'Mert', 'Egitim Uzmani'),
    ('metegencer@teamguerilla.com', 'Mete', 'Gencer', 'Lojistik Uzmani'),
    ('boragelisken@teamguerilla.com', 'Bora', 'Gelisken', 'Tasarimci Kreatif'),
]

ESKI_ROLLER = ['admin', 'User']


def generate_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def run(mode='dry-run'):
    from app import create_app, db
    from app.models.core import User, Role, Permission

    app = create_app()
    with app.app_context():
        sifre_listesi = []

        print("=" * 80)
        print(f"  TG PORTAL - ROL & KULLANICI KURULUMU [{mode.upper()}]")
        print(f"  Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)

        # ADIM 1: MEVCUT DURUM
        print("\n[1] MEVCUT DURUM")
        print("-" * 40)
        mevcut_roller = Role.query.all()
        print(f"  Rol sayisi: {len(mevcut_roller)}")
        for r in mevcut_roller:
            pc = len(r.permissions) if r.permissions else 0
            print(f"    {r.name} ({r.display_name or '-'}) -> {pc} perm")

        mevcut_users = User.query.filter_by(is_deleted=False).all()
        print(f"  Aktif kullanici: {len(mevcut_users)}")
        for u in mevcut_users:
            roller = [r.name for r in u.roles] if u.roles else []
            print(f"    {u.email}: {roller}")

        # ADIM 2: ESKI ROLLERI TEMIZLE
        print(f"\n[2] ESKI ROLLERI TEMIZLE")
        print("-" * 40)
        for eski in ESKI_ROLLER:
            rol = Role.query.filter_by(name=eski).first()
            if rol:
                users_in = User.query.filter(User.roles.any(Role.name == eski)).all()
                print(f"  '{eski}': {len(users_in)} kullanici -> silinecek")
                if mode == 'apply':
                    for u in users_in:
                        u.roles.remove(rol)
                    rol.permissions = []
                    db.session.delete(rol)
            else:
                print(f"  '{eski}': bulunamadi")

        # ADIM 3: ROLLERI OLUSTUR
        print(f"\n[3] ROLLERI OLUSTUR/GUNCELLE")
        print("-" * 40)
        tum_permler = {p.code: p for p in Permission.query.all()}
        print(f"  Sistemde {len(tum_permler)} permission var")

        rol_objeleri = {}
        for rol_name, rol_config in ROL_PERMISSION_MATRIX.items():
            aciklama = rol_config.get('aciklama', '')
            perms_config = rol_config.get('permissions', {})

            rol = Role.query.filter_by(name=rol_name).first()
            if rol:
                print(f"  [VAR] {rol_name} (id={rol.id})")
            else:
                print(f"  [YENI] {rol_name}")
                if mode == 'apply':
                    rol = Role(
                        name=rol_name,
                        display_name=rol_name,
                        description=aciklama,
                        is_system=(rol_name == 'Sistem Yoneticisi'),
                    )
                    db.session.add(rol)
                    db.session.flush()

            # Permission atama
            if perms_config == '*':
                target_perms = list(tum_permler.values())
                print(f"         -> TUM ({len(target_perms)} perm)")
            else:
                target_perm_codes = []
                for modul, actions in perms_config.items():
                    for action in actions:
                        target_perm_codes.append(f"{modul}.{action}")

                target_perms = []
                eksik = []
                for code in target_perm_codes:
                    if code in tum_permler:
                        target_perms.append(tum_permler[code])
                    else:
                        eksik.append(code)

                if eksik:
                    print(f"         EKSIK PERM (olusturulacak): {eksik}")
                    if mode == 'apply':
                        for code in eksik:
                            parts = code.split('.')
                            yp = Permission(
                                code=code,
                                name=code.replace('.', ' ').title(),
                                module=parts[0],
                            )
                            db.session.add(yp)
                            db.session.flush()
                            tum_permler[code] = yp
                            target_perms.append(yp)

                print(f"         -> {len(target_perms)} perm")

            if mode == 'apply' and rol:
                rol.permissions = target_perms
                rol.display_name = rol_name
                rol.description = aciklama

            rol_objeleri[rol_name] = rol

        # ADIM 4: KULLANICILARI OLUSTUR/GUNCELLE
        print(f"\n[4] KULLANICILARI OLUSTUR/GUNCELLE")
        print("-" * 40)

        for email, ad, soyad, rol_name in KULLANICILAR:
            user = User.query.filter_by(email=email).first()

            if user:
                eski_roller = [r.name for r in user.roles]
                print(f"  [VAR] {email}: {eski_roller} -> {rol_name}")
                if mode == 'apply':
                    user.ad = ad
                    user.soyad = soyad
                    user.is_active = True
                    user.is_deleted = False
                    user.is_admin = (rol_name == 'Sistem Yoneticisi')
                    user.roles = [rol_objeleri[rol_name]] if rol_objeleri.get(rol_name) else []
            else:
                sifre = generate_password()
                print(f"  [YENI] {email} ({ad} {soyad}) -> {rol_name} | sifre: {sifre}")
                sifre_listesi.append({
                    'email': email, 'ad': f"{ad} {soyad}",
                    'rol': rol_name, 'sifre': sifre,
                })
                if mode == 'apply':
                    user = User(
                        email=email,
                        password_hash=generate_password_hash(sifre),
                        ad=ad, soyad=soyad,
                        is_active=True,
                        is_admin=(rol_name == 'Sistem Yoneticisi'),
                        is_deleted=False,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    db.session.add(user)
                    db.session.flush()
                    user.roles = [rol_objeleri[rol_name]] if rol_objeleri.get(rol_name) else []

        # ADIM 5: KULLANILMAYAN ROLLERI TEMIZLE
        print(f"\n[5] KULLANILMAYAN ESKI ROLLERI TEMIZLE")
        print("-" * 40)
        yeni_isimler = set(ROL_PERMISSION_MATRIX.keys())
        for mr in Role.query.all():
            if mr.name not in yeni_isimler and mr.name not in ESKI_ROLLER:
                uc = User.query.filter(User.roles.any(Role.id == mr.id)).count()
                if uc == 0:
                    print(f"  [SIL] {mr.name} (0 kullanici)")
                    if mode == 'apply':
                        mr.permissions = []
                        db.session.delete(mr)
                else:
                    print(f"  [KORU] {mr.name} ({uc} kullanici)")

        # COMMIT
        if mode == 'apply':
            db.session.commit()
            print(f"\n>>> TUM DEGISIKLIKLER KAYDEDILDI <<<")
        else:
            print(f"\n>>> DRY-RUN: Hicbir degisiklik yapilmadi <<<")
            print(f"    Uygulamak icin: python3 scripts/rol_kurulum.py --apply")

        # OZET
        print(f"\n{'=' * 80}")
        print(f"  OZET: {len(ROL_PERMISSION_MATRIX)} rol, {len(KULLANICILAR)} kullanici")
        print(f"  Yeni olusturulacak: {len(sifre_listesi)}")
        print(f"  Mevcut guncellenecek: {len(KULLANICILAR) - len(sifre_listesi)}")

        if sifre_listesi:
            print(f"\n  YENI KULLANICI SIFRELERI:")
            print(f"  {'Email':<45} {'Ad':<25} {'Rol':<25} Sifre")
            print(f"  {'-'*120}")
            for s in sifre_listesi:
                print(f"  {s['email']:<45} {s['ad']:<25} {s['rol']:<25} {s['sifre']}")

        return sifre_listesi


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Kullanim:")
        print("  python3 scripts/rol_kurulum.py --dry-run")
        print("  python3 scripts/rol_kurulum.py --apply")
        print("  python3 scripts/rol_kurulum.py --export-passwords")
        sys.exit(1)

    arg = sys.argv[1]
    if arg == '--dry-run':
        run(mode='dry-run')
    elif arg == '--apply':
        print("DIKKAT: Bu islem veritabanini degistirecek!")
        print("Devam etmek icin 'EVET' yazin: ", end='')
        onay = input().strip()
        if onay == 'EVET':
            run(mode='apply')
        else:
            print("Iptal edildi.")
    elif arg == '--force-apply':
        run(mode='apply')
    elif arg == '--export-passwords':
        run(mode='dry-run')
    else:
        print(f"Bilinmeyen parametre: {arg}")
        sys.exit(1)
