# -*- coding: utf-8 -*-
"""
TG Portal - Seed Data
Başlangıç verileri: roller, yetkiler, admin kullanıcı
"""

from app import db
from app.models.core import User, Role, Permission
from app.models.ik import Departman, Pozisyon
from app.models.tedarikci import Tedarikci
from app.models.base import TedarikciTipi


def seed_permissions():
    """Yetkileri oluştur"""
    permissions = [
        # İK Modülü
        ('ik.view', 'İK Görüntüleme', 'Çalışan ve aday bilgilerini görüntüleme', 'ik'),
        ('ik.create', 'İK Ekleme', 'Yeni çalışan ekleme', 'ik'),
        ('ik.edit', 'İK Düzenleme', 'Çalışan bilgilerini düzenleme', 'ik'),
        ('ik.delete', 'İK Silme', 'Çalışan kaydı silme', 'ik'),
        ('ik.ozluk', 'Özlük Bilgileri', 'Hassas özlük bilgilerine erişim', 'ik'),
        
        # Filo Modülü
        ('filo.view', 'Filo Görüntüleme', 'Araç bilgilerini görüntüleme', 'filo'),
        ('filo.create', 'Araç Ekleme', 'Yeni araç ekleme', 'filo'),
        ('filo.edit', 'Araç Düzenleme', 'Araç bilgilerini düzenleme', 'filo'),
        ('filo.delete', 'Araç Silme', 'Araç kaydı silme', 'filo'),
        ('filo.bakim', 'Bakım Kaydı', 'Bakım ve işlem kaydı ekleme', 'filo'),
        ('filo.yakit', 'Yakıt Kaydı', 'Yakıt kaydı ekleme', 'filo'),
        
        # Tedarikçi Modülü
        ('tedarikci.view', 'Tedarikçi Görüntüleme', 'Tedarikçi bilgilerini görüntüleme', 'tedarikci'),
        ('tedarikci.create', 'Tedarikçi Ekleme', 'Yeni tedarikçi ekleme', 'tedarikci'),
        ('tedarikci.edit', 'Tedarikçi Düzenleme', 'Tedarikçi bilgilerini düzenleme', 'tedarikci'),
        ('tedarikci.delete', 'Tedarikçi Silme', 'Tedarikçi kaydı silme', 'tedarikci'),
        
        # Admin
        ('admin.users', 'Kullanıcı Yönetimi', 'Kullanıcıları yönetme', 'admin'),
        ('admin.roles', 'Rol Yönetimi', 'Rolleri yönetme', 'admin'),
    ]
    
    for code, name, description, module in permissions:
        if not Permission.query.filter_by(code=code).first():
            perm = Permission(code=code, name=name, description=description, module=module)
            db.session.add(perm)
    
    db.session.commit()
    print(f"✓ {len(permissions)} yetki oluşturuldu")


def seed_roles():
    """Rolleri oluştur"""
    roles_data = [
        {
            'name': 'admin',
            'display_name': 'Sistem Yöneticisi',
            'description': 'Tüm yetkilere sahip',
            'is_system': True,
            'permissions': ['*']  # Tüm yetkiler
        },
        {
            'name': 'ik_yonetici',
            'display_name': 'İK Yöneticisi',
            'description': 'İK modülü tam yetki',
            'is_system': True,
            'permissions': ['ik.view', 'ik.create', 'ik.edit', 'ik.delete', 'ik.ozluk', 'tedarikci.view']
        },
        {
            'name': 'filo_yonetici',
            'display_name': 'Filo Yöneticisi',
            'description': 'Filo modülü tam yetki',
            'is_system': True,
            'permissions': ['filo.view', 'filo.create', 'filo.edit', 'filo.delete', 'filo.bakim', 'filo.yakit', 'tedarikci.view', 'tedarikci.create', 'tedarikci.edit']
        },
        {
            'name': 'muhasebe',
            'display_name': 'Muhasebe',
            'description': 'Görüntüleme ve tedarikçi yönetimi',
            'is_system': False,
            'permissions': ['ik.view', 'filo.view', 'tedarikci.view', 'tedarikci.create', 'tedarikci.edit']
        },
        {
            'name': 'viewer',
            'display_name': 'Görüntüleyici',
            'description': 'Sadece görüntüleme',
            'is_system': False,
            'permissions': ['ik.view', 'filo.view', 'tedarikci.view']
        }
    ]
    
    for role_data in roles_data:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(
                name=role_data['name'],
                display_name=role_data['display_name'],
                description=role_data['description'],
                is_system=role_data['is_system']
            )
            db.session.add(role)
            db.session.flush()
        
        # Yetkileri ekle
        for perm_code in role_data['permissions']:
            if perm_code == '*':
                continue  # Admin için özel işlem
            perm = Permission.query.filter_by(code=perm_code).first()
            if perm and perm not in role.permissions:
                role.permissions.append(perm)
    
    db.session.commit()
    print(f"✓ {len(roles_data)} rol oluşturuldu")


def seed_admin_user():
    """Admin kullanıcı oluştur"""
    admin = User.query.filter_by(email='admin@teamguerilla.com').first()
    if not admin:
        admin = User(
            email='admin@teamguerilla.com',
            ad='Admin',
            soyad='User',
            is_admin=True,
            is_active=True
        )
        admin.set_password('admin123')
        
        # Admin rolü ekle
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            admin.roles.append(admin_role)
        
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin kullanıcı oluşturuldu: admin@teamguerilla.com / admin123")
    else:
        print("→ Admin kullanıcı zaten mevcut")


def seed_departmanlar():
    """Örnek departmanlar"""
    departmanlar = [
        ('Yönetim', 'YON'),
        ('İnsan Kaynakları', 'IK'),
        ('Satış', 'SAT'),
        ('Operasyon', 'OPR'),
        ('Muhasebe', 'MUH'),
        ('Bilgi Teknolojileri', 'BT'),
    ]
    
    for ad, kod in departmanlar:
        if not Departman.query.filter_by(kod=kod).first():
            dept = Departman(ad=ad, kod=kod, aktif=True)
            db.session.add(dept)
    
    db.session.commit()
    print(f"✓ {len(departmanlar)} departman oluşturuldu")


def seed_pozisyonlar():
    """Örnek pozisyonlar"""
    pozisyonlar = [
        'Genel Müdür',
        'Müdür',
        'Şef',
        'Uzman',
        'Asistan',
        'Stajyer',
        'Saha Personeli',
        'Şoför',
    ]
    
    for ad in pozisyonlar:
        if not Pozisyon.query.filter_by(ad=ad).first():
            poz = Pozisyon(ad=ad, aktif=True)
            db.session.add(poz)
    
    db.session.commit()
    print(f"✓ {len(pozisyonlar)} pozisyon oluşturuldu")


def seed_ornek_tedarikciler():
    """Örnek tedarikçiler"""
    tedarikciler = [
        {
            'unvan': 'Petrol Ofisi A.Ş.',
            'kisa_ad': 'PO',
            'tip': TedarikciTipi.YAKIT,
            'telefon': '444 7 888',
            'il': 'İstanbul',
            'aktif': True
        },
        {
            'unvan': 'Ford Yetkili Servisi',
            'kisa_ad': 'Ford Servis',
            'tip': TedarikciTipi.SERVIS,
            'telefon': '0212 555 1234',
            'il': 'İstanbul',
            'ilce': 'Maslak',
            'aktif': True
        },
        {
            'unvan': 'Axa Sigorta A.Ş.',
            'kisa_ad': 'Axa',
            'tip': TedarikciTipi.SIGORTA,
            'telefon': '444 0 292',
            'il': 'İstanbul',
            'aktif': True
        },
    ]
    
    for t_data in tedarikciler:
        if not Tedarikci.query.filter_by(unvan=t_data['unvan']).first():
            tedarikci = Tedarikci(**t_data)
            db.session.add(tedarikci)
    
    db.session.commit()
    print(f"✓ {len(tedarikciler)} örnek tedarikçi oluşturuldu")


def seed_all():
    """Tüm seed verilerini yükle"""
    print("\n🌱 Seed verileri yükleniyor...\n")
    
    seed_permissions()
    seed_roles()
    seed_admin_user()
    seed_departmanlar()
    seed_pozisyonlar()
    seed_ornek_tedarikciler()
    seed_projeler()
    seed_ornek_araclar()
    
    print("\n✅ Tüm seed verileri yüklendi!\n")


def seed_projeler():
    """Örnek müşteri, proje ve kadro verileri"""
    from app.models.proje import Musteri, Proje, HedefKadro
    from datetime import date, timedelta
    
    print("  Projeler seed ediliyor...")
    
    # Müşteriler
    musteriler = [
        {
            'ad': 'Migros Ticaret A.Ş.',
            'kisa_ad': 'Migros',
            'vergi_no': '1234567890',
            'il': 'İstanbul',
            'telefon': '0212 555 1234',
            'yetkili_ad': 'Ahmet Yılmaz',
            'yetkili_telefon': '0532 555 1234',
            'yetkili_email': 'ahmet.yilmaz@migros.com.tr'
        },
        {
            'ad': 'Anadolu Efes Biracılık ve Malt Sanayi A.Ş.',
            'kisa_ad': 'Efes',
            'vergi_no': '2345678901',
            'il': 'İstanbul',
            'telefon': '0216 555 5678',
            'yetkili_ad': 'Mehmet Demir',
            'yetkili_telefon': '0533 555 5678',
            'yetkili_email': 'mehmet.demir@efes.com.tr'
        },
        {
            'ad': 'Coca-Cola İçecek A.Ş.',
            'kisa_ad': 'CCI',
            'vergi_no': '3456789012',
            'il': 'İstanbul',
            'telefon': '0212 555 9012',
            'yetkili_ad': 'Ayşe Kaya',
            'yetkili_telefon': '0534 555 9012',
            'yetkili_email': 'ayse.kaya@cci.com.tr'
        }
    ]
    
    musteri_objs = []
    for m in musteriler:
        if not Musteri.query.filter_by(kisa_ad=m['kisa_ad']).first():
            musteri = Musteri(**m, aktif=True)
            db.session.add(musteri)
            musteri_objs.append(musteri)
    
    db.session.flush()
    
    # Projeler
    if musteri_objs:
        projeler = [
            {
                'musteri': 'Migros',
                'ad': 'Migros Saha Satış Ekibi 2024',
                'kod': 'MIG-2024-01',
                'baslangic_tarihi': date.today() - timedelta(days=60),
                'bitis_tarihi': date.today() + timedelta(days=300),
                'butce': 2500000
            },
            {
                'musteri': 'Efes',
                'ad': 'Efes Merchandising Projesi',
                'kod': 'EFS-2024-01',
                'baslangic_tarihi': date.today() - timedelta(days=30),
                'bitis_tarihi': date.today() + timedelta(days=335),
                'butce': 1800000
            },
            {
                'musteri': 'CCI',
                'ad': 'CCI Market Aktivasyon',
                'kod': 'CCI-2024-01',
                'baslangic_tarihi': date.today(),
                'bitis_tarihi': date.today() + timedelta(days=180),
                'butce': 1200000
            }
        ]
        
        proje_objs = []
        for p in projeler:
            musteri = Musteri.query.filter_by(kisa_ad=p['musteri']).first()
            if musteri and not Proje.query.filter_by(kod=p['kod']).first():
                proje = Proje(
                    musteri_id=musteri.id,
                    ad=p['ad'],
                    kod=p['kod'],
                    baslangic_tarihi=p['baslangic_tarihi'],
                    bitis_tarihi=p['bitis_tarihi'],
                    butce=p['butce'],
                    aktif=True
                )
                db.session.add(proje)
                proje_objs.append(proje)
        
        db.session.flush()
        
        # Kadrolar
        kadrolar = [
            # Migros
            {'proje': 'MIG-2024-01', 'pozisyon': 'Saha Satış Temsilcisi', 'il': 'İstanbul', 'hedef': 15, 'oncelik': 2, 'maas_min': 25000, 'maas_max': 35000},
            {'proje': 'MIG-2024-01', 'pozisyon': 'Saha Satış Temsilcisi', 'il': 'Ankara', 'hedef': 8, 'oncelik': 3, 'maas_min': 22000, 'maas_max': 30000},
            {'proje': 'MIG-2024-01', 'pozisyon': 'Saha Satış Temsilcisi', 'il': 'İzmir', 'hedef': 6, 'oncelik': 4, 'maas_min': 22000, 'maas_max': 30000},
            {'proje': 'MIG-2024-01', 'pozisyon': 'Bölge Yöneticisi', 'il': 'İstanbul', 'hedef': 2, 'oncelik': 1, 'maas_min': 45000, 'maas_max': 60000},
            
            # Efes
            {'proje': 'EFS-2024-01', 'pozisyon': 'Merchandiser', 'il': 'İstanbul', 'hedef': 20, 'oncelik': 2, 'maas_min': 20000, 'maas_max': 28000},
            {'proje': 'EFS-2024-01', 'pozisyon': 'Merchandiser', 'il': 'Antalya', 'hedef': 10, 'oncelik': 3, 'maas_min': 18000, 'maas_max': 25000},
            {'proje': 'EFS-2024-01', 'pozisyon': 'Takım Lideri', 'il': 'İstanbul', 'hedef': 3, 'oncelik': 2, 'maas_min': 35000, 'maas_max': 45000},
            
            # CCI
            {'proje': 'CCI-2024-01', 'pozisyon': 'Aktivasyon Uzmanı', 'il': 'İstanbul', 'hedef': 12, 'oncelik': 3, 'maas_min': 23000, 'maas_max': 32000},
            {'proje': 'CCI-2024-01', 'pozisyon': 'Aktivasyon Uzmanı', 'il': 'Bursa', 'hedef': 5, 'oncelik': 5, 'maas_min': 20000, 'maas_max': 28000},
        ]
        
        for k in kadrolar:
            proje = Proje.query.filter_by(kod=k['proje']).first()
            if proje:
                existing = HedefKadro.query.filter_by(
                    proje_id=proje.id,
                    pozisyon_adi=k['pozisyon'],
                    il=k['il']
                ).first()
                if not existing:
                    kadro = HedefKadro(
                        proje_id=proje.id,
                        pozisyon_adi=k['pozisyon'],
                        il=k['il'],
                        hedef_sayi=k['hedef'],
                        oncelik=k['oncelik'],
                        maas_min=k['maas_min'],
                        maas_max=k['maas_max'],
                        ehliyet_gerekli=True,
                        ehliyet_sinifi='B',
                        aktif=True
                    )
                    db.session.add(kadro)
    
    db.session.commit()
    print("  ✓ Projeler seed edildi")


def seed_ornek_araclar():
    """Örnek araç verileri"""
    from app.models.filo import Arac
    from app.models.proje import Proje
    from app.models.base import AracDurumu, YakitTipi
    
    print("  Araçlar seed ediliyor...")
    
    # Projeleri al
    migros_proje = Proje.query.filter_by(kod='MIG-2024-01').first()
    efes_proje = Proje.query.filter_by(kod='EFS-2024-01').first()
    
    araclar = [
        {'plaka': '34TG001', 'marka': 'Ford', 'model': 'Transit Courier', 'yil': 2023, 'km': 15000, 'proje': migros_proje},
        {'plaka': '34TG002', 'marka': 'Ford', 'model': 'Transit Courier', 'yil': 2023, 'km': 18500, 'proje': migros_proje},
        {'plaka': '34TG003', 'marka': 'Fiat', 'model': 'Doblo', 'yil': 2022, 'km': 32000, 'proje': migros_proje},
        {'plaka': '34TG004', 'marka': 'Renault', 'model': 'Kangoo', 'yil': 2022, 'km': 28000, 'proje': efes_proje},
        {'plaka': '34TG005', 'marka': 'Renault', 'model': 'Kangoo', 'yil': 2022, 'km': 31000, 'proje': efes_proje},
        {'plaka': '34TG006', 'marka': 'Volkswagen', 'model': 'Caddy', 'yil': 2023, 'km': 12000, 'proje': None},
        {'plaka': '34TG007', 'marka': 'Volkswagen', 'model': 'Caddy', 'yil': 2023, 'km': 8500, 'proje': None},
        {'plaka': '06TG001', 'marka': 'Ford', 'model': 'Transit Courier', 'yil': 2022, 'km': 45000, 'proje': migros_proje},
        {'plaka': '35TG001', 'marka': 'Fiat', 'model': 'Doblo', 'yil': 2021, 'km': 62000, 'proje': None},
    ]
    
    for a in araclar:
        if not Arac.query.filter_by(plaka=a['plaka']).first():
            arac = Arac(
                plaka=a['plaka'],
                marka=a['marka'],
                model=a['model'],
                model_yili=a['yil'],
                km=a['km'],
                yakit_tipi=YakitTipi.DIZEL,
                durum=AracDurumu.AKTIF,
                sahiplik_tipi='sirket',
                proje_id=a['proje'].id if a['proje'] else None
            )
            db.session.add(arac)
    
    db.session.commit()
    print("  ✓ Araçlar seed edildi")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_all()


# -*- coding: utf-8 -*-
"""
TG Portal - Seed Data Eklemeleri
Bu fonksiyonu mevcut seed_data.py dosyasına ekleyin
"""

def seed_evrak_tipleri():
    """Standart evrak tiplerini ekle"""
    from app import db
    from app.models.ik import EvrakTipi
    
    evraklar = [
        {'kod': 'NUFUS', 'ad': 'Nüfus Cüzdanı Fotokopisi', 'kategori': 'kimlik', 'zorunlu': True, 'sira': 1},
        {'kod': 'VESIKALIK', 'ad': 'Vesikalık Fotoğraf (2 adet)', 'kategori': 'kimlik', 'zorunlu': True, 'sira': 2},
        {'kod': 'IKAMETGAH', 'ad': 'İkametgah Belgesi', 'kategori': 'kimlik', 'zorunlu': True, 'sira': 3},
        {'kod': 'ADLISICIL', 'ad': 'Adli Sicil Kaydı', 'kategori': 'kimlik', 'zorunlu': True, 'sira': 4},
        {'kod': 'DIPLOMA', 'ad': 'Diploma / Mezuniyet Belgesi', 'kategori': 'egitim', 'zorunlu': True, 'sira': 5},
        {'kod': 'TRANSKRIPT', 'ad': 'Transkript', 'kategori': 'egitim', 'zorunlu': False, 'sira': 6},
        {'kod': 'SGK_ISEYERI', 'ad': 'SGK İşe Giriş Bildirgesi', 'kategori': 'sgk', 'zorunlu': True, 'sira': 7},
        {'kod': 'SAGLIK', 'ad': 'Sağlık Raporu', 'kategori': 'saglik', 'zorunlu': True, 'sira': 8},
        {'kod': 'ASKERLIK', 'ad': 'Askerlik Durum Belgesi', 'kategori': 'diger', 'zorunlu': False, 'sira': 9, 'aciklama': 'Erkek adaylar için'},
        {'kod': 'EHLIYET', 'ad': 'Ehliyet Fotokopisi', 'kategori': 'diger', 'zorunlu': False, 'sira': 10},
        {'kod': 'BANKA', 'ad': 'Banka Hesap Bilgileri / IBAN', 'kategori': 'diger', 'zorunlu': True, 'sira': 11},
        {'kod': 'CV', 'ad': 'Özgeçmiş (CV)', 'kategori': 'diger', 'zorunlu': False, 'sira': 12},
        {'kod': 'REFERANS', 'ad': 'Referans Mektubu', 'kategori': 'diger', 'zorunlu': False, 'sira': 13},
        {'kod': 'ISSOZLESMESI', 'ad': 'İmzalı İş Sözleşmesi', 'kategori': 'sozlesme', 'zorunlu': True, 'sira': 14},
        {'kod': 'KVKK', 'ad': 'KVKK Aydınlatma Metni (İmzalı)', 'kategori': 'sozlesme', 'zorunlu': True, 'sira': 15},
    ]
    
    for e in evraklar:
        if not EvrakTipi.query.filter_by(kod=e['kod']).first():
            evrak = EvrakTipi(**e)
            db.session.add(evrak)
    
    db.session.commit()
    print(f'✓ {len(evraklar)} evrak tipi eklendi/kontrol edildi')


# Mevcut seed_all() fonksiyonuna ekle:
# seed_evrak_tipleri()
