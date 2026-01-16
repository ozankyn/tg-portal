# -*- coding: utf-8 -*-
"""TG Portal - Demo Seed Data"""

import sys
sys.path.insert(0, '.')

from datetime import datetime, date
from decimal import Decimal
import random

from app import create_app, db
from app.models.core import User, Role
from app.models.ik import Calisan, ZimmetTipi, EvrakTipi, Departman, Pozisyon
from app.models.proje import Proje, Musteri
from app.models.filo import Arac
from app.models.tedarikci import Tedarikci
from app.models.egitim import EgitimTipi
from app.models.depo import Depo, UrunKategori, Urun, StokKarti

app = create_app()

def create_departments():
    print("🏛️  Departmanlar...")
    items = ['Yönetim', 'İnsan Kaynakları', 'Finans', 'Operasyon', 'Satış', 'Pazarlama', 'IT', 'Lojistik']
    created = []
    for d in items:
        obj = Departman.query.filter_by(ad=d).first()
        if not obj:
            obj = Departman(ad=d, aktif=True)
            db.session.add(obj)
        created.append(obj)
    db.session.commit()
    print(f"  ✅ {len(created)}")
    return created

def create_pozisyonlar():
    print("💼 Pozisyonlar...")
    items = ['Genel Müdür', 'Müdür', 'Şef', 'Uzman', 'Kıdemli Uzman', 'Asistan', 'Saha Personeli', 'Depo Sorumlusu']
    created = []
    for p in items:
        obj = Pozisyon.query.filter_by(ad=p).first()
        if not obj:
            obj = Pozisyon(ad=p, aktif=True)
            db.session.add(obj)
        created.append(obj)
    db.session.commit()
    print(f"  ✅ {len(created)}")
    return created

def create_users_and_calisanlar(departmanlar, pozisyonlar):
    print("👥 Kullanıcılar ve çalışanlar...")
    
    admin_role = Role.query.filter_by(name='Admin').first()
    user_role = Role.query.filter_by(name='User').first()
    
    data = [
        {'ad': 'Ahmet', 'soyad': 'Yılmaz', 'email': 'ahmet.yilmaz@teamguerilla.com', 'dept': 0, 'poz': 0, 'admin': True},
        {'ad': 'Ayşe', 'soyad': 'Demir', 'email': 'ayse.demir@teamguerilla.com', 'dept': 1, 'poz': 1},
        {'ad': 'Mehmet', 'soyad': 'Kaya', 'email': 'mehmet.kaya@teamguerilla.com', 'dept': 2, 'poz': 1},
        {'ad': 'Fatma', 'soyad': 'Çelik', 'email': 'fatma.celik@teamguerilla.com', 'dept': 3, 'poz': 1},
        {'ad': 'Ali', 'soyad': 'Şahin', 'email': 'ali.sahin@teamguerilla.com', 'dept': 4, 'poz': 1},
        {'ad': 'Zeynep', 'soyad': 'Arslan', 'email': 'zeynep.arslan@teamguerilla.com', 'dept': 5, 'poz': 3},
        {'ad': 'Mustafa', 'soyad': 'Erdoğan', 'email': 'mustafa.erdogan@teamguerilla.com', 'dept': 6, 'poz': 1},
        {'ad': 'Elif', 'soyad': 'Öztürk', 'email': 'elif.ozturk@teamguerilla.com', 'dept': 1, 'poz': 3},
    ]
    
    users = []
    calisanlar = []
    
    for i, c in enumerate(data):
        tc = f'1234567{i:04d}'
        calisan = Calisan.query.filter_by(tc_kimlik=tc).first()
        if not calisan:
            calisan = Calisan(
                ad=c['ad'],
                soyad=c['soyad'],
                tc_kimlik=tc,
                dogum_tarihi=date(1985 + (i % 15), (i % 12) + 1, (i % 28) + 1),
                cinsiyet='erkek' if i % 2 == 0 else 'kadin',
                telefon=f'0530555{i:04d}',
                email=c['email'],
                ise_baslama=date(2020 + (i % 5), (i % 12) + 1, 1),
                departman_id=departmanlar[c['dept']].id,
                pozisyon_id=pozisyonlar[c['poz']].id,
                durum='AKTIF'
            )
            db.session.add(calisan)
            db.session.flush()
        calisanlar.append(calisan)
        
        user = User.query.filter_by(email=c['email']).first()
        if not user:
            user = User(
                email=c['email'],
                ad=c['ad'],
                soyad=c['soyad'],
                is_active=True,
                is_admin=c.get('admin', False),
                calisan_id=calisan.id
            )
            user.set_password('demo123')
            if c.get('admin') and admin_role:
                user.roles.append(admin_role)
            elif user_role:
                user.roles.append(user_role)
            db.session.add(user)
        users.append(user)
    
    db.session.commit()
    print(f"  ✅ {len(users)} user, {len(calisanlar)} çalışan")
    return users, calisanlar

def create_musteriler():
    print("🏪 Müşteriler...")
    items = ['Migros', 'Efes Pilsen', 'Coca Cola', 'Unilever', 'P&G']
    created = []
    for ad in items:
        m = Musteri.query.filter_by(ad=ad).first()
        if not m:
            m = Musteri(ad=ad, kisa_ad=ad.split()[0])
            db.session.add(m)
        created.append(m)
    db.session.commit()
    print(f"  ✅ {len(created)}")
    return created

def create_projeler(musteriler):
    print("📁 Projeler...")
    items = [
        ('Migros Merchandising', 'MIG-2024', 0),
        ('Efes Promosyon', 'EFS-2024', 1),
        ('Coca Cola Aktivasyon', 'CCL-2024', 2),
        ('Unilever Saha', 'UNI-2024', 3),
    ]
    created = []
    for ad, kod, mi in items:
        p = Proje.query.filter_by(kod=kod).first()
        if not p:
            p = Proje(
                ad=ad, kod=kod,
                musteri_id=musteriler[mi].id,
                baslangic_tarihi=date(2024, 1, 1),
                bitis_tarihi=date(2024, 12, 31),
                aktif=True,
                butce=Decimal(random.randint(300000, 800000))
            )
            db.session.add(p)
        created.append(p)
    db.session.commit()
    print(f"  ✅ {len(created)}")
    return created

def create_tedarikciler():
    print("🏭 Tedarikçiler...")
    items = ['ABC Bilişim', 'XYZ Ofis', 'Mega Akaryakıt', 'Prime Araç Kiralama']
    created = []
    for ad in items:
        t = Tedarikci.query.filter_by(unvan=ad).first()
        if not t:
            t = Tedarikci(unvan=ad, kisa_ad=ad.split()[0])
            db.session.add(t)
        created.append(t)
    db.session.commit()
    print(f"  ✅ {len(created)}")
    return created

def create_araclar():
    print("🚗 Araçlar...")
    items = [
        ('34 TG 001', 'Volkswagen', 'Passat', 2023),
        ('34 TG 002', 'Renault', 'Megane', 2022),
        ('34 TG 003', 'Ford', 'Focus', 2023),
        ('34 TG 004', 'Fiat', 'Egea', 2022),
        ('34 TG 005', 'Toyota', 'Corolla', 2023),
    ]
    created = []
    for plaka, marka, model, yil in items:
        a = Arac.query.filter_by(plaka=plaka).first()
        if not a:
            a = Arac(
                plaka=plaka, marka=marka, model=model, model_yili=yil,
                renk='Beyaz', vites_tipi='otomatik',
                km=random.randint(10000, 60000)
            )
            db.session.add(a)
        created.append(a)
    db.session.commit()
    print(f"  ✅ {len(created)}")
    return created

def create_zimmet_tipleri():
    print("📦 Zimmet tipleri...")
    items = ['Laptop', 'Telefon', 'Tablet', 'Monitör', 'Araç Anahtarı', 'Yaka Kartı']
    created = []
    for t in items:
        tip = ZimmetTipi.query.filter_by(ad=t).first()
        if not tip:
            tip = ZimmetTipi(ad=t, aktif=True)
            db.session.add(tip)
        created.append(tip)
    db.session.commit()
    print(f"  ✅ {len(created)}")
    return created

def create_evrak_tipleri():
    print("📄 Evrak tipleri...")
    items = ['Kimlik Fotokopisi', 'İkametgah', 'Adli Sicil', 'Diploma', 'SGK İşe Giriş', 'Sağlık Raporu']
    created = []
    for ad in items:
        tip = EvrakTipi.query.filter_by(ad=ad).first()
        if not tip:
            tip = EvrakTipi(ad=ad, zorunlu=True, aktif=True)
            db.session.add(tip)
        created.append(tip)
    db.session.commit()
    print(f"  ✅ {len(created)}")
    return created

def create_egitim_tipleri():
    print("📚 Eğitim tipleri...")
    items = [
        ('İSG Eğitimi', True, 365),
        ('Hijyen Eğitimi', True, 365),
        ('İlk Yardım', True, 730),
        ('Ürün Bilgisi', False, None),
    ]
    created = []
    for ad, zorunlu, gecerlilik in items:
        tip = EgitimTipi.query.filter_by(ad=ad).first()
        if not tip:
            tip = EgitimTipi(ad=ad, kategori='zorunlu' if zorunlu else 'teknik', gecerlilik_gun=gecerlilik, aktif=True)
            db.session.add(tip)
        created.append(tip)
    db.session.commit()
    print(f"  ✅ {len(created)}")
    return created

def main():
    print("=" * 50)
    print("🚀 TG Portal Demo Seed")
    print("=" * 50)
    
    with app.app_context():
        departmanlar = create_departments()
        pozisyonlar = create_pozisyonlar()
        users, calisanlar = create_users_and_calisanlar(departmanlar, pozisyonlar)
        musteriler = create_musteriler()
        projeler = create_projeler(musteriler)
        tedarikciler = create_tedarikciler()
        araclar = create_araclar()
        zimmet_tipleri = create_zimmet_tipleri()
        evrak_tipleri = create_evrak_tipleri()
        egitim_tipleri = create_egitim_tipleri()
        
        print("=" * 50)
        print("✅ Demo veriler oluşturuldu!")
        print("📌 Giriş: ahmet.yilmaz@teamguerilla.com / demo123")
        print("=" * 50)

if __name__ == '__main__':
    main()
