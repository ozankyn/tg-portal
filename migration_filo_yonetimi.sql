-- Filo Yönetimi Modülü - PostgreSQL Migration
-- Oluşturma Tarihi: 2025-12-16

-- 1. ARAÇLAR TABLOSU
CREATE TABLE IF NOT EXISTS araclar (
    id SERIAL PRIMARY KEY,
    plaka VARCHAR(20) NOT NULL UNIQUE,
    marka VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    yil INTEGER,
    renk VARCHAR(50),
    
    -- Teknik Bilgiler
    sasi_no VARCHAR(100),
    motor_no VARCHAR(100),
    yakit_tipi VARCHAR(50), -- Benzin, Dizel, LPG, Elektrik, Hybrid
    
    -- Sigorta Bilgileri
    sigorta_sirket VARCHAR(100),
    sigorta_police_no VARCHAR(100),
    sigorta_bitis_tarihi DATE,
    
    -- Muayene
    muayene_tarihi DATE,
    sonraki_muayene_tarihi DATE,
    
    -- Kilometre
    baslangic_km INTEGER DEFAULT 0,
    guncel_km INTEGER DEFAULT 0,
    
    -- Durum
    durum VARCHAR(20) DEFAULT 'Aktif', -- Aktif, Bakımda, Hasarlı, Pasif
    aktif BOOLEAN DEFAULT TRUE,
    
    -- Notlar
    notlar TEXT,
    
    -- Timestamps
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. ARAÇ TESLİM/İADE TABLOSU
CREATE TABLE IF NOT EXISTS arac_teslim_iade (
    id SERIAL PRIMARY KEY,
    arac_id INTEGER NOT NULL REFERENCES araclar(id) ON DELETE CASCADE,
    calisan_id INTEGER NOT NULL REFERENCES calisanlar(id) ON DELETE CASCADE,
    
    -- Teslim mi İade mi?
    islem_tipi VARCHAR(20) NOT NULL, -- Teslim, İade
    
    -- Tarih ve Saat
    islem_tarihi TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Araç Durumu
    kilometre INTEGER NOT NULL,
    yakit_durumu VARCHAR(20), -- Boş, 1/4, 1/2, 3/4, Dolu
    
    -- Hasar Kontrolü
    hasar_var BOOLEAN DEFAULT FALSE,
    hasar_aciklama TEXT,
    
    -- Genel Durum
    temizlik_durumu VARCHAR(20), -- Temiz, Orta, Kirli
    ic_durum_aciklama TEXT,
    dis_durum_aciklama TEXT,
    
    -- Eksikler/Sorunlar
    eksikler TEXT,
    
    -- Fotoğraflar
    fotograf_yolu TEXT, -- JSON array olarak saklanacak: ["foto1.jpg", "foto2.jpg"]
    
    -- Teslim/İade Eden Kişi
    teslim_eden_user_id INTEGER REFERENCES users(id),
    
    -- Notlar
    notlar TEXT,
    
    -- Timestamps
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. ARAÇ ZİMMET TABLOSU (Mevcut Zimmet Durumu)
CREATE TABLE IF NOT EXISTS arac_zimmet (
    id SERIAL PRIMARY KEY,
    arac_id INTEGER NOT NULL REFERENCES araclar(id) ON DELETE CASCADE,
    calisan_id INTEGER NOT NULL REFERENCES calisanlar(id) ON DELETE CASCADE,
    
    -- Teslim Bilgileri
    teslim_tarihi DATE NOT NULL,
    teslim_km INTEGER NOT NULL,
    teslim_kayit_id INTEGER REFERENCES arac_teslim_iade(id),
    
    -- İade Bilgileri (NULL = Hala Zimmetli)
    iade_tarihi DATE,
    iade_km INTEGER,
    iade_kayit_id INTEGER REFERENCES arac_teslim_iade(id),
    
    -- Durum
    aktif BOOLEAN DEFAULT TRUE, -- TRUE = Hala zimmetli, FALSE = İade edildi
    
    -- Timestamps
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Constraint: Bir araç aynı anda sadece bir kişide olabilir
CREATE UNIQUE INDEX idx_arac_zimmet_unique_aktif ON arac_zimmet(arac_id) WHERE aktif = TRUE;

-- 4. ARAÇ BAKIM/TAMİR KAYITLARI
CREATE TABLE IF NOT EXISTS arac_bakim (
    id SERIAL PRIMARY KEY,
    arac_id INTEGER NOT NULL REFERENCES araclar(id) ON DELETE CASCADE,
    
    -- Bakım Türü
    bakim_tipi VARCHAR(50) NOT NULL, -- Periyodik Bakım, Tamir, Lastik, Akü, vb.
    
    -- Tarih ve Kilometre
    bakim_tarihi DATE NOT NULL,
    bakim_km INTEGER,
    
    -- Detaylar
    aciklama TEXT NOT NULL,
    yapilan_islemler TEXT,
    
    -- Maliyet
    tutar DECIMAL(10, 2),
    
    -- Servis
    servis_adi VARCHAR(200),
    servis_telefon VARCHAR(20),
    
    -- Sonraki Bakım
    sonraki_bakim_km INTEGER,
    sonraki_bakim_tarihi DATE,
    
    -- Fatura/Belge
    belge_yolu TEXT,
    
    -- Timestamps
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. ARAÇ YAKIT KAYITLARI
CREATE TABLE IF NOT EXISTS arac_yakit (
    id SERIAL PRIMARY KEY,
    arac_id INTEGER NOT NULL REFERENCES araclar(id) ON DELETE CASCADE,
    calisan_id INTEGER REFERENCES calisanlar(id) ON DELETE SET NULL,
    
    -- Yakıt Bilgileri
    yakit_tarihi DATE NOT NULL,
    kilometre INTEGER NOT NULL,
    litre DECIMAL(6, 2) NOT NULL,
    birim_fiyat DECIMAL(6, 2),
    toplam_tutar DECIMAL(10, 2),
    
    -- Yakıt Türü
    yakit_tipi VARCHAR(50), -- Benzin, Dizel, LPG
    
    -- Fatura
    fatura_no VARCHAR(100),
    istasyon VARCHAR(200),
    
    -- Notlar
    notlar TEXT,
    
    -- Timestamps
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. ARAÇ SİGORTA/KAZA KAYITLARI
CREATE TABLE IF NOT EXISTS arac_sigorta_kaza (
    id SERIAL PRIMARY KEY,
    arac_id INTEGER NOT NULL REFERENCES araclar(id) ON DELETE CASCADE,
    
    -- Kayıt Türü
    kayit_tipi VARCHAR(20) NOT NULL, -- Sigorta Yenileme, Kaza, Hasar
    
    -- Tarih
    kayit_tarihi DATE NOT NULL,
    
    -- Kaza ise
    kaza_aciklama TEXT,
    kusur_durumu VARCHAR(50), -- Bizde, Karşı Tarafta, Karşılıklı
    hasar_tutari DECIMAL(10, 2),
    
    -- Sigorta ise
    sigorta_sirket VARCHAR(100),
    police_no VARCHAR(100),
    baslangic_tarihi DATE,
    bitis_tarihi DATE,
    prim_tutari DECIMAL(10, 2),
    
    -- Belgeler
    belge_yolu TEXT,
    
    -- Notlar
    notlar TEXT,
    
    -- Timestamps
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İNDEXLER
CREATE INDEX idx_araclar_plaka ON araclar(plaka);
CREATE INDEX idx_araclar_durum ON araclar(durum, aktif);
CREATE INDEX idx_arac_teslim_arac ON arac_teslim_iade(arac_id);
CREATE INDEX idx_arac_teslim_calisan ON arac_teslim_iade(calisan_id);
CREATE INDEX idx_arac_zimmet_arac ON arac_zimmet(arac_id);
CREATE INDEX idx_arac_zimmet_calisan ON arac_zimmet(calisan_id);
CREATE INDEX idx_arac_zimmet_aktif ON arac_zimmet(aktif);
CREATE INDEX idx_arac_bakim_arac ON arac_bakim(arac_id);
CREATE INDEX idx_arac_yakit_arac ON arac_yakit(arac_id);

-- NOTLAR
COMMENT ON TABLE araclar IS 'Filo yönetimi - Araç bilgileri';
COMMENT ON TABLE arac_teslim_iade IS 'Araç teslim ve iade işlemleri';
COMMENT ON TABLE arac_zimmet IS 'Mevcut araç zimmet durumu';
COMMENT ON TABLE arac_bakim IS 'Araç bakım ve tamir kayıtları';
COMMENT ON TABLE arac_yakit IS 'Araç yakıt alım kayıtları';
COMMENT ON TABLE arac_sigorta_kaza IS 'Araç sigorta ve kaza kayıtları';