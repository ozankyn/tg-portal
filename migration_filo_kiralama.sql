-- Filo Yönetimi - Kiralama Özellikleri Ekleme
-- Tarih: 2025-12-16

-- 1. Araçlar tablosuna mülkiyet tipi ekle
ALTER TABLE araclar ADD COLUMN IF NOT EXISTS mulkiyet_tipi VARCHAR(20) DEFAULT 'Özmal';
-- Değerler: 'Özmal' veya 'Kiralık'

COMMENT ON COLUMN araclar.mulkiyet_tipi IS 'Araç mülkiyet durumu: Özmal veya Kiralık';

-- 2. Araç Kiralama Bilgileri Tablosu
CREATE TABLE IF NOT EXISTS arac_kira_bilgileri (
    id SERIAL PRIMARY KEY,
    arac_id INTEGER NOT NULL REFERENCES araclar(id) ON DELETE CASCADE,
    
    -- Kiralama Şirketi
    kiralama_sirket VARCHAR(200) NOT NULL,
    sirket_telefon VARCHAR(20),
    sirket_email VARCHAR(100),
    yetkili_kisi VARCHAR(100),
    
    -- Sözleşme Bilgileri
    sozlesme_no VARCHAR(100),
    sozlesme_baslangic DATE NOT NULL,
    sozlesme_bitis DATE NOT NULL,
    
    -- Maliyet Bilgileri (Sadece admin ve finans rolü görebilir)
    aylik_kira_bedeli DECIMAL(10, 2),
    para_birimi VARCHAR(10) DEFAULT 'TRY',
    
    -- Ödeme Koşulları
    odeme_donemi VARCHAR(50), -- Aylık, Üç Aylık, vb.
    odeme_gunu INTEGER, -- Ayın kaçıncı günü ödeme yapılacak
    
    -- Sözleşme Dosyası
    sozlesme_dosya_yolu TEXT,
    
    -- Ek Koşullar
    km_limiti INTEGER, -- Aylık/yıllık km limiti varsa
    km_asim_ucreti DECIMAL(6, 2), -- KM aşımında km başına ücret
    
    -- Sigorta
    sigorta_dahil BOOLEAN DEFAULT FALSE,
    bakim_dahil BOOLEAN DEFAULT FALSE,
    
    -- Notlar
    notlar TEXT,
    
    -- Durum
    aktif BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Constraint: Bir araç için aynı anda sadece bir aktif kira kaydı
CREATE UNIQUE INDEX idx_arac_kira_unique_aktif ON arac_kira_bilgileri(arac_id) WHERE aktif = TRUE;

-- 3. Kiralama Ödeme Takip Tablosu
CREATE TABLE IF NOT EXISTS arac_kira_odemeler (
    id SERIAL PRIMARY KEY,
    kira_bilgi_id INTEGER NOT NULL REFERENCES arac_kira_bilgileri(id) ON DELETE CASCADE,
    arac_id INTEGER NOT NULL REFERENCES araclar(id) ON DELETE CASCADE,
    
    -- Ödeme Dönemi
    odeme_donemi DATE NOT NULL, -- Hangi ay/dönem için ödeme
    
    -- Tutar
    tutar DECIMAL(10, 2) NOT NULL,
    para_birimi VARCHAR(10) DEFAULT 'TRY',
    
    -- KM Aşım Bedeli (varsa)
    km_asim_tutari DECIMAL(10, 2) DEFAULT 0,
    
    -- Toplam
    toplam_tutar DECIMAL(10, 2),
    
    -- Ödeme Durumu
    odeme_durumu VARCHAR(20) DEFAULT 'Bekliyor', -- Bekliyor, Ödendi, Gecikti
    planlanan_odeme_tarihi DATE,
    gerceklesen_odeme_tarihi DATE,
    
    -- Fatura/Dekont
    fatura_no VARCHAR(100),
    odeme_belgesi_yolu TEXT,
    
    -- Notlar
    notlar TEXT,
    
    -- Timestamps
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İndeksler
CREATE INDEX idx_arac_kira_bilgileri_arac ON arac_kira_bilgileri(arac_id);
CREATE INDEX idx_arac_kira_bilgileri_aktif ON arac_kira_bilgileri(aktif);
CREATE INDEX idx_arac_kira_bilgileri_bitis ON arac_kira_bilgileri(sozlesme_bitis);
CREATE INDEX idx_arac_kira_odemeler_kira ON arac_kira_odemeler(kira_bilgi_id);
CREATE INDEX idx_arac_kira_odemeler_durum ON arac_kira_odemeler(odeme_durumu);
CREATE INDEX idx_arac_kira_odemeler_tarih ON arac_kira_odemeler(odeme_donemi);

-- Yorumlar
COMMENT ON TABLE arac_kira_bilgileri IS 'Kiralık araçların sözleşme ve maliyet bilgileri';
COMMENT ON TABLE arac_kira_odemeler IS 'Kiralık araçların ödeme takip kayıtları';
COMMENT ON COLUMN arac_kira_bilgileri.aylik_kira_bedeli IS 'Sadece admin ve finans rolü görebilir';