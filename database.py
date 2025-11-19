import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Veritabanı bağlantı URL'si
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://tgportal:tgportal123@localhost:5432/tgportal')

class PostgreSQLConnection:
    """SQLite benzeri interface sağlayan PostgreSQL wrapper"""
    
    def __init__(self, conn):
        self._conn = conn
        self._cursor = conn.cursor()
    
    def execute(self, query, params=None):
        """Execute wrapper - SQLite uyumlu interface"""
        if params:
            self._cursor.execute(query, params)
        else:
            self._cursor.execute(query)
        return self
    
    def fetchone(self):
        """Tek satır getir"""
        return self._cursor.fetchone()
    
    def fetchall(self):
        """Tüm satırları getir"""
        return self._cursor.fetchall()
    
    def commit(self):
        """Transaction commit"""
        self._conn.commit()
    
    def rollback(self):
        """Transaction rollback"""
        self._conn.rollback()
    
    def close(self):
        """Bağlantıyı kapat"""
        self._cursor.close()
        self._conn.close()
    
    def cursor(self):
        """Yeni cursor oluştur"""
        return self._conn.cursor()
    
    @property
    def lastrowid(self):
        """Son eklenen kaydın ID'si"""
        self._cursor.execute("SELECT lastval()")
        result = self._cursor.fetchone()
        return result['lastval'] if result else None

def get_db():
    """PostgreSQL veritabanı bağlantısı oluştur"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    conn.set_client_encoding('UTF8')
    return PostgreSQLConnection(conn)

def init_db():
    """Veritabanını başlat - tüm tabloları oluştur"""
    conn = get_db()
    cursor = conn.cursor()
    
    # ===== KULLANICI YÖNETİMİ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            email VARCHAR(120),
            full_name VARCHAR(100),
            role VARCHAR(20) DEFAULT 'user',
            aktif BOOLEAN DEFAULT TRUE,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            son_giris_tarihi TIMESTAMP
        )
    ''')
    
    # ===== MÜŞTERİ VE PROJE YÖNETİMİ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS musteriler (
            id SERIAL PRIMARY KEY,
            musteri_adi VARCHAR(100) UNIQUE NOT NULL,
            sektor VARCHAR(100),
            yetkili_kisi VARCHAR(100),
            telefon VARCHAR(20),
            email VARCHAR(120),
            adres TEXT,
            logo_yolu VARCHAR(255),
            aktif BOOLEAN DEFAULT TRUE,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projeler (
            id SERIAL PRIMARY KEY,
            proje_adi VARCHAR(100) NOT NULL,
            aciklama TEXT,
            musteri_id INTEGER REFERENCES musteriler(id),
            aktif BOOLEAN DEFAULT TRUE,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ===== ORGANİZASYON YAPISI =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mudurluker (
            id SERIAL PRIMARY KEY,
            mudurluk_adi VARCHAR(100) UNIQUE NOT NULL,
            aktif BOOLEAN DEFAULT TRUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS direktorlukler (
            id SERIAL PRIMARY KEY,
            direktorluk_adi VARCHAR(100) UNIQUE NOT NULL,
            aktif BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # ===== ÇALIŞMA ŞEKİLLERİ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calisma_sekilleri (
            id SERIAL PRIMARY KEY,
            calisma_sekli VARCHAR(100) UNIQUE NOT NULL,
            aktif BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # ===== LOKASYON =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS iller (
            id SERIAL PRIMARY KEY,
            il_adi VARCHAR(50) UNIQUE NOT NULL,
            aktif BOOLEAN DEFAULT TRUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ilceler (
            id SERIAL PRIMARY KEY,
            il_id INTEGER REFERENCES iller(id) NOT NULL,
            ilce_adi VARCHAR(50) NOT NULL,
            aktif BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # ===== KAYNAK YÖNETİMİ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kaynaklar (
            id SERIAL PRIMARY KEY,
            kaynak_adi VARCHAR(100) UNIQUE NOT NULL,
            aciklama TEXT,
            aktif BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # ===== KADRO YÖNETİMİ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hedef_kadrolar (
            id SERIAL PRIMARY KEY,
            proje_id INTEGER REFERENCES projeler(id) NOT NULL,
            pozisyon_adi VARCHAR(100) NOT NULL,
            calisma_sekli VARCHAR(50),
            mudurluk_id INTEGER REFERENCES mudurluker(id),
            direktorluk_id INTEGER REFERENCES direktorlukler(id),
            il_id INTEGER REFERENCES iller(id),
            ilce_id INTEGER REFERENCES ilceler(id),
            magaza_adi VARCHAR(100),
            hedef_kisi_sayisi INTEGER DEFAULT 1,
            dolu_kisi_sayisi INTEGER DEFAULT 0,
            aracli_durum VARCHAR(20),
            durum VARCHAR(20) DEFAULT 'Açık',
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ===== ADAY TAKİBİ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adaylar (
            id SERIAL PRIMARY KEY,
            kadro_id INTEGER REFERENCES hedef_kadrolar(id) NOT NULL,
            ad_soyad VARCHAR(100) NOT NULL,
            telefon VARCHAR(20),
            email VARCHAR(120),
            tc_kimlik VARCHAR(11),
            dogum_tarihi DATE,
            notlar TEXT,
            kaynak_id INTEGER REFERENCES kaynaklar(id),
            kaynak_diger VARCHAR(100),
            durum VARCHAR(20) DEFAULT 'Aday',
            basvuru_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ise_baslama_tarihi DATE
        )
    ''')
    
    # ===== ÇALIŞAN YÖNETİMİ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calisanlar (
            id SERIAL PRIMARY KEY,
            aday_id INTEGER REFERENCES adaylar(id),
            kadro_id INTEGER REFERENCES hedef_kadrolar(id) NOT NULL,
            ad_soyad VARCHAR(100) NOT NULL,
            telefon VARCHAR(20),
            email VARCHAR(120),
            tc_kimlik VARCHAR(11),
            dogum_tarihi DATE,
            adres TEXT,
            ise_baslama_tarihi DATE NOT NULL,
            cikis_tarihi DATE,
            cikis_nedeni VARCHAR(100),
            liste_durumu VARCHAR(20),
            aracli_durum VARCHAR(20),
            aktif BOOLEAN DEFAULT TRUE,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ===== ÇIKIŞ İŞLEMLERİ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cikis_nedenleri (
            id SERIAL PRIMARY KEY,
            neden VARCHAR(100) UNIQUE NOT NULL,
            aktif BOOLEAN DEFAULT TRUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cikis_kayitlari (
            id SERIAL PRIMARY KEY,
            calisan_id INTEGER REFERENCES calisanlar(id) NOT NULL,
            cikis_tarihi DATE NOT NULL,
            cikis_nedeni VARCHAR(100),
            liste_durumu VARCHAR(20),
            tekrar_ise_alinabilir BOOLEAN DEFAULT TRUE,
            zimmet_teslim BOOLEAN DEFAULT FALSE,
            kiyafet_teslim BOOLEAN DEFAULT FALSE,
            anahtar_teslim BOOLEAN DEFAULT FALSE,
            kimlik_teslim BOOLEAN DEFAULT FALSE,
            ihbar_tazminat_durumu VARCHAR(100),
            kidem_tazminat_durumu VARCHAR(100),
            yonetici_notu TEXT,
            ik_notu TEXT,
            genel_degerlendirme TEXT,
            islem_yapan VARCHAR(100),
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ===== DOSYA YÖNETİMİ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dosyalar (
            id SERIAL PRIMARY KEY,
            ilgili_tablo VARCHAR(50) NOT NULL,
            ilgili_id INTEGER NOT NULL,
            dosya_tipi VARCHAR(50) NOT NULL,
            dosya_adi VARCHAR(255) NOT NULL,
            dosya_yolu VARCHAR(500) NOT NULL,
            dosya_boyutu INTEGER,
            yukleyen_user_id INTEGER REFERENCES users(id),
            yukleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            aciklama TEXT
        )
    ''')
    
    # ===== EMAIL SİSTEMİ =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_ayarlari (
            id SERIAL PRIMARY KEY,
            ayar_adi VARCHAR(100) UNIQUE NOT NULL,
            ayar_degeri TEXT,
            aciklama TEXT,
            aktif BOOLEAN DEFAULT TRUE,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_sablonlari (
            id SERIAL PRIMARY KEY,
            sablon_adi VARCHAR(100) UNIQUE NOT NULL,
            sablon_konusu VARCHAR(255) NOT NULL,
            sablon_icerik TEXT NOT NULL,
            aktif BOOLEAN DEFAULT TRUE,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_loglari (
            id SERIAL PRIMARY KEY,
            alici_email VARCHAR(120) NOT NULL,
            konu VARCHAR(255) NOT NULL,
            sablon_adi VARCHAR(100),
            gonderim_durumu VARCHAR(20) DEFAULT 'beklemede',
            hata_mesaji TEXT,
            ilgili_tablo VARCHAR(50),
            ilgili_id INTEGER,
            gonderim_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ===== SÜREÇ LOGLARI =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS surec_loglari (
            id SERIAL PRIMARY KEY,
            islem_tipi VARCHAR(50),
            tablo_adi VARCHAR(50),
            kayit_id INTEGER,
            aciklama TEXT,
            kullanici VARCHAR(100),
            islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ PostgreSQL veritabanı tabloları başarıyla oluşturuldu!")

def log_islem(islem_tipi, tablo_adi, kayit_id, aciklama, kullanici='Sistem'):
    """İşlem logu ekle"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO surec_loglari (islem_tipi, tablo_adi, kayit_id, aciklama, kullanici)
        VALUES (%s, %s, %s, %s, %s)
    ''', (islem_tipi, tablo_adi, kayit_id, aciklama, kullanici))
    conn.commit()
    conn.close()

def seed_sample_data():
    """SQLite'dan aktarılan gerçek verileri yükle"""
    conn = get_db()
    cursor = conn.cursor()
    
    # seed_data.py modülünden veri aktarım fonksiyonunu çağır
    try:
        from seed_data import seed_from_sqlite_data
        seed_from_sqlite_data(conn._conn, cursor)
    except ImportError:
        print("⚠️ seed_data.py bulunamadı, varsayılan veriler yükleniyor...")
        # Fallback: Basit admin kullanıcısı
        import hashlib
        admin_password = 'admin123'
        password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, full_name, role, aktif)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            ''', ('admin', password_hash, 'admin@teamguerilla.com', 'Sistem Yöneticisi', 'admin', True))
            print(f"✅ Admin kullanıcısı oluşturuldu: admin / admin123")
        except Exception as e:
            print(f"ℹ️ Admin kullanıcısı: {e}")
        
        conn._conn.commit()
    
    conn.close()
    print("✅ Veri yükleme tamamlandı!")

if __name__ == '__main__':
    init_db()
    seed_sample_data()