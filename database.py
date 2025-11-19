import sqlite3
from datetime import datetime
import os

DB_PATH = 'hr_system.db'

def get_db():
    """Veritabanı bağlantısı oluştur"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Veritabanını başlat"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Projeler tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projeler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proje_adi TEXT NOT NULL UNIQUE,
            aciklama TEXT,
            aktif INTEGER DEFAULT 1,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Hedef Kadrolar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hedef_kadrolar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proje_id INTEGER NOT NULL,
            pozisyon_adi TEXT NOT NULL,
            il TEXT NOT NULL,
            ilce TEXT,
            magaza_adi TEXT,
            hedef_kisi_sayisi INTEGER DEFAULT 1,
            dolu_kisi_sayisi INTEGER DEFAULT 0,
            durum TEXT DEFAULT 'Açık',
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proje_id) REFERENCES projeler(id)
        )
    ''')
    
    # Adaylar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adaylar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kadro_id INTEGER NOT NULL,
            ad_soyad TEXT NOT NULL,
            telefon TEXT,
            email TEXT,
            tc_kimlik TEXT,
            durum TEXT DEFAULT 'Aday',
            basvuru_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ise_baslama_tarihi TIMESTAMP,
            notlar TEXT,
            FOREIGN KEY (kadro_id) REFERENCES hedef_kadrolar(id)
        )
    ''')
    
    # Çalışanlar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calisanlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aday_id INTEGER NOT NULL,
            kadro_id INTEGER NOT NULL,
            ad_soyad TEXT NOT NULL,
            telefon TEXT,
            email TEXT,
            tc_kimlik TEXT,
            ise_baslama_tarihi TIMESTAMP NOT NULL,
            aktif INTEGER DEFAULT 1,
            cikis_tarihi TIMESTAMP,
            FOREIGN KEY (aday_id) REFERENCES adaylar(id),
            FOREIGN KEY (kadro_id) REFERENCES hedef_kadrolar(id)
        )
    ''')
    
    # Süreç Logları tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS surec_loglari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            islem_tipi TEXT NOT NULL,
            tablo_adi TEXT NOT NULL,
            kayit_id INTEGER,
            aciklama TEXT NOT NULL,
            islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            kullanici TEXT DEFAULT 'Sistem'
        )
    ''')
    
    # Kullanıcılar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            email TEXT,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            aktif INTEGER DEFAULT 1,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            son_giris_tarihi TIMESTAMP
        )
    ''')
    
    # Dosyalar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dosyalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ilgili_tablo TEXT NOT NULL,
            ilgili_id INTEGER NOT NULL,
            dosya_tipi TEXT NOT NULL,
            dosya_adi TEXT NOT NULL,
            dosya_yolu TEXT NOT NULL,
            dosya_boyutu INTEGER,
            yukleyen_user_id INTEGER,
            yukleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            aciklama TEXT,
            FOREIGN KEY (yukleyen_user_id) REFERENCES users(id)
        )
    ''')
    
    # Email Ayarları tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_ayarlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ayar_adi TEXT NOT NULL UNIQUE,
            ayar_degeri TEXT,
            aciklama TEXT,
            aktif INTEGER DEFAULT 1,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Email Şablonları tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_sablonlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sablon_adi TEXT NOT NULL UNIQUE,
            sablon_konusu TEXT NOT NULL,
            sablon_icerik TEXT NOT NULL,
            aktif INTEGER DEFAULT 1,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Email Logları tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_loglari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alici_email TEXT NOT NULL,
            konu TEXT NOT NULL,
            sablon_adi TEXT,
            gonderim_durumu TEXT DEFAULT 'beklemede',
            hata_mesaji TEXT,
            ilgili_tablo TEXT,
            ilgili_id INTEGER,
            gonderim_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Veritabanı başarıyla oluşturuldu!")

def log_islem(islem_tipi, tablo_adi, kayit_id, aciklama, kullanici='Sistem'):
    """İşlem logu ekle"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO surec_loglari (islem_tipi, tablo_adi, kayit_id, aciklama, kullanici)
        VALUES (?, ?, ?, ?, ?)
    ''', (islem_tipi, tablo_adi, kayit_id, aciklama, kullanici))
    conn.commit()
    conn.close()

def seed_sample_data():
    """Örnek veri ekle"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Örnek projeler
    projeler = [
        ('Migros Mağaza Açılışı', 'Yeni mağaza açılışları için personel alımı'),
        ('ADCO Depo Genişletme', 'Depo operasyonları için eleman alımı')
    ]
    
    for proje in projeler:
        try:
            cursor.execute('INSERT INTO projeler (proje_adi, aciklama) VALUES (?, ?)', proje)
            log_islem('EKLEME', 'projeler', cursor.lastrowid, f'{proje[0]} projesi oluşturuldu')
        except:
            pass
    
    # Örnek hedef kadrolar
    kadrolar = [
        (1, 'Kasa Görevlisi', 'İstanbul', 'Gebze', 'Migros MMM', 3),
        (1, 'Reyon Görevlisi', 'İstanbul', 'Kartal', 'Migros 5M', 2),
        (2, 'Depo Operatörü', 'Kocaeli', 'Gebze', 'ADCO Merkez Depo', 5),
    ]
    
    for kadro in kadrolar:
        try:
            cursor.execute('''
                INSERT INTO hedef_kadrolar (proje_id, pozisyon_adi, il, ilce, magaza_adi, hedef_kisi_sayisi)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', kadro)
            log_islem('EKLEME', 'hedef_kadrolar', cursor.lastrowid, 
                     f'{kadro[1]} pozisyonu için {kadro[5]} kişilik kadro açıldı')
        except:
            pass
            
    # Admin kullanıcısı ekle (şifre: admin123)
    import hashlib
    
    admin_username = 'admin'
    admin_password = 'admin123'
    password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, full_name, role, aktif)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin_username, password_hash, 'admin@teamguerilla.com', 'Sistem Yöneticisi', 'admin', 1))
        log_islem('EKLEME', 'users', cursor.lastrowid, f'{admin_username} kullanıcısı oluşturuldu')
        print(f"✅ Admin kullanıcısı oluşturuldu: {admin_username} / {admin_password}")
    except:
        print("ℹ️ Admin kullanıcısı zaten mevcut")        
    
    conn.commit()
    conn.close()
    print("✅ Örnek veriler eklendi!")
    
    # Email SMTP Ayarları
    email_ayarlari = [
        ('smtp_sunucu', 'smtp.teamguerillamarketing.com', 'SMTP sunucu adresi'),
        ('smtp_port', '587', 'SMTP port numarası'),
        ('smtp_kullanici', 'ikportal@teamguerillamarketing.com', 'Gönderici email adresi'),
        ('smtp_sifre', '1q2w3e4R!!', 'Email şifresi veya app password'),
        ('gonderici_adi', 'İK Portal Sistemi', 'Gönderici adı'),
        ('egitim_email', 'oguzhangumus@teamguerilla.com', 'Eğitim departmanı email'),
        ('filo_email', 'burakdurgun@teamguerilla.com', 'Filo departmanı email'),
        ('ik_email', 'tgmik@teamguerilla.com', 'İK departmanı email'),
        ('yonetici_email', 'ozankayan@teamguerilla.com', 'Yönetici email'),
    ]
    
    for ayar in email_ayarlari:
        try:
            cursor.execute('''
                INSERT INTO email_ayarlari (ayar_adi, ayar_degeri, aciklama)
                VALUES (?, ?, ?)
            ''', ayar)
        except:
            pass
    
    # Email Şablonları
    email_sablonlari = [
        ('yeni_ise_giris', 
         'Yeni Personel İşe Giriş - {ad_soyad}',
         '''
         <h2>Yeni Personel İşe Giriş Bildirimi</h2>
         <p><strong>Sayın Yetkili,</strong></p>
         <p>Aşağıdaki personel işe başlamıştır. Gerekli işlemlerin yapılması rica olunur.</p>
         
         <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
             <tr style="background-color: #f8f9fa;">
                 <td style="padding: 10px; border: 1px solid #ddd;"><strong>Ad Soyad:</strong></td>
                 <td style="padding: 10px; border: 1px solid #ddd;">{ad_soyad}</td>
             </tr>
             <tr>
                 <td style="padding: 10px; border: 1px solid #ddd;"><strong>Proje:</strong></td>
                 <td style="padding: 10px; border: 1px solid #ddd;">{proje_adi}</td>
             </tr>
             <tr style="background-color: #f8f9fa;">
                 <td style="padding: 10px; border: 1px solid #ddd;"><strong>Pozisyon:</strong></td>
                 <td style="padding: 10px; border: 1px solid #ddd;">{pozisyon_adi}</td>
             </tr>
             <tr>
                 <td style="padding: 10px; border: 1px solid #ddd;"><strong>Lokasyon:</strong></td>
                 <td style="padding: 10px; border: 1px solid #ddd;">{il} / {ilce}</td>
             </tr>
             <tr style="background-color: #f8f9fa;">
                 <td style="padding: 10px; border: 1px solid #ddd;"><strong>Mağaza:</strong></td>
                 <td style="padding: 10px; border: 1px solid #ddd;">{magaza_adi}</td>
             </tr>
             <tr>
                 <td style="padding: 10px; border: 1px solid #ddd;"><strong>İşe Başlama Tarihi:</strong></td>
                 <td style="padding: 10px; border: 1px solid #ddd;">{ise_baslama_tarihi}</td>
             </tr>
             <tr style="background-color: #f8f9fa;">
                 <td style="padding: 10px; border: 1px solid #ddd;"><strong>Telefon:</strong></td>
                 <td style="padding: 10px; border: 1px solid #ddd;">{telefon}</td>
             </tr>
             <tr>
                 <td style="padding: 10px; border: 1px solid #ddd;"><strong>Email:</strong></td>
                 <td style="padding: 10px; border: 1px solid #ddd;">{email}</td>
             </tr>
         </table>
         
         <p>Bu mail İK Portal sistemi tarafından otomatik olarak gönderilmiştir.</p>
         <p>Detaylar için: <a href="{portal_url}">İK Portal</a></p>
         
         <hr style="margin: 20px 0;">
         <p style="color: #666; font-size: 12px;">
             <strong>Team Guerilla - İK Yönetim Sistemi</strong><br>
             Gönderilme Zamanı: {gonderim_zamani}
         </p>
         '''),
    ]
    
    for sablon in email_sablonlari:
        try:
            cursor.execute('''
                INSERT INTO email_sablonlari (sablon_adi, sablon_konusu, sablon_icerik)
                VALUES (?, ?, ?)
            ''', sablon)
        except:
            pass
    
    conn.commit()
    print("✅ Email ayarları ve şablonları eklendi!")

if __name__ == '__main__':
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    seed_sample_data()