-- İŞTEN ÇIKIŞ SİSTEMİ - DATABASE MIGRATION

-- 1. İşten Çıkış Kayıtları Tablosu
CREATE TABLE IF NOT EXISTS cikis_kayitlari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    calisan_id INTEGER NOT NULL,
    cikis_tarihi DATE NOT NULL,
    cikis_nedeni TEXT,
    liste_durumu TEXT DEFAULT 'Beyaz', -- Beyaz, Gri, Kara
    tekrar_ise_alinabilir INTEGER DEFAULT 1, -- 0: Hayır, 1: Evet
    
    -- Checklist
    zimmet_teslim INTEGER DEFAULT 0,
    kiyafet_teslim INTEGER DEFAULT 0,
    anahtar_teslim INTEGER DEFAULT 0,
    kimlik_teslim INTEGER DEFAULT 0,
    
    -- Tazminat Bilgileri
    ihbar_tazminat_durumu TEXT, -- Ödendi, Ödenmedi, Çalıştı
    kidem_tazminat_durumu TEXT, -- Ödendi, Ödenmedi, Hak Yok
    
    -- Notlar
    yonetici_notu TEXT,
    ik_notu TEXT,
    genel_degerlendirme TEXT,
    
    -- Metadata
    islem_yapan TEXT,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (calisan_id) REFERENCES calisanlar(id)
);

-- 2. Çıkış Nedenleri Tablosu
CREATE TABLE IF NOT EXISTS cikis_nedenleri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    neden TEXT NOT NULL UNIQUE,
    aciklama TEXT,
    aktif INTEGER DEFAULT 1,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Varsayılan Çıkış Nedenleri
INSERT INTO cikis_nedenleri (neden, aciklama) VALUES
    ('İstifa', 'Çalışanın kendi isteğiyle ayrılması'),
    ('İşten Çıkarma', 'İşveren tarafından sözleşmenin feshi'),
    ('Emeklilik', 'Emeklilik nedeniyle ayrılma'),
    ('Sözleşme Bitimi', 'Belirli süreli sözleşmenin sona ermesi'),
    ('Disiplin Cezası', 'Disiplin suçu nedeniyle işten çıkarma'),
    ('Performans', 'Düşük performans nedeniyle ayrılma'),
    ('Sağlık Sebepleri', 'Sağlık durumu nedeniyle ayrılma'),
    ('Askerlik', 'Askerlik görevi nedeniyle ayrılma'),
    ('Ölüm', 'Vefat nedeniyle ayrılma'),
    ('Diğer', 'Diğer sebepler');

-- 4. calisanlar tablosuna çıkış bilgisi sütunları ekle (eğer yoksa)
ALTER TABLE calisanlar ADD COLUMN cikis_tarihi DATE;
ALTER TABLE calisanlar ADD COLUMN cikis_nedeni TEXT;
ALTER TABLE calisanlar ADD COLUMN liste_durumu TEXT;

-- 5. Index'ler (Performans için)
CREATE INDEX IF NOT EXISTS idx_cikis_calisan ON cikis_kayitlari(calisan_id);
CREATE INDEX IF NOT EXISTS idx_cikis_tarihi ON cikis_kayitlari(cikis_tarihi);
CREATE INDEX IF NOT EXISTS idx_cikis_liste ON cikis_kayitlari(liste_durumu);
CREATE INDEX IF NOT EXISTS idx_calisan_aktif ON calisanlar(aktif);

-- Migration tamamlandı!