#!/bin/bash
# Kiralama migration'ını uygula

cat << 'EOF' | docker exec -i tg-portal-db-1 psql -U tgportal -d tgportal

-- Filo Yönetimi - Kiralama Özellikleri Ekleme
-- Tarih: 2025-12-16

-- 1. Araçlar tablosuna mülkiyet tipi ekle
ALTER TABLE araclar ADD COLUMN IF NOT EXISTS mulkiyet_tipi VARCHAR(20) DEFAULT 'Özmal';
COMMENT ON COLUMN araclar.mulkiyet_tipi IS 'Araç mülkiyet durumu: Özmal veya Kiralık';

-- 2. Araç Kiralama Bilgileri Tablosu
CREATE TABLE IF NOT EXISTS arac_kira_bilgileri (
    id SERIAL PRIMARY KEY,
    arac_id INTEGER NOT NULL REFERENCES araclar(id) ON DELETE CASCADE,
    kiralama_sirket VARCHAR(200) NOT NULL,
    sirket_telefon VARCHAR(20),
    sirket_email VARCHAR(100),
    yetkili_kisi VARCHAR(100),
    sozlesme_no VARCHAR(100),
    sozlesme_baslangic DATE NOT NULL,
    sozlesme_bitis DATE NOT NULL,
    aylik_kira_bedeli DECIMAL(10, 2),
    para_birimi VARCHAR(10) DEFAULT 'TRY',
    odeme_donemi VARCHAR(50),
    odeme_gunu INTEGER,
    sozlesme_dosya_yolu TEXT,
    km_limiti INTEGER,
    km_asim_ucreti DECIMAL(6, 2),
    sigorta_dahil BOOLEAN DEFAULT FALSE,
    bakim_dahil BOOLEAN DEFAULT FALSE,
    notlar TEXT,
    aktif BOOLEAN DEFAULT TRUE,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_arac_kira_unique_aktif ON arac_kira_bilgileri(arac_id) WHERE aktif = TRUE;

-- 3. Kiralama Ödeme Takip Tablosu
CREATE TABLE IF NOT EXISTS arac_kira_odemeler (
    id SERIAL PRIMARY KEY,
    kira_bilgi_id INTEGER NOT NULL REFERENCES arac_kira_bilgileri(id) ON DELETE CASCADE,
    arac_id INTEGER NOT NULL REFERENCES araclar(id) ON DELETE CASCADE,
    odeme_donemi DATE NOT NULL,
    tutar DECIMAL(10, 2) NOT NULL,
    para_birimi VARCHAR(10) DEFAULT 'TRY',
    km_asim_tutari DECIMAL(10, 2) DEFAULT 0,
    toplam_tutar DECIMAL(10, 2),
    odeme_durumu VARCHAR(20) DEFAULT 'Bekliyor',
    planlanan_odeme_tarihi DATE,
    gerceklesen_odeme_tarihi DATE,
    fatura_no VARCHAR(100),
    odeme_belgesi_yolu TEXT,
    notlar TEXT,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_arac_kira_bilgileri_arac ON arac_kira_bilgileri(arac_id);
CREATE INDEX IF NOT EXISTS idx_arac_kira_bilgileri_aktif ON arac_kira_bilgileri(aktif);
CREATE INDEX IF NOT EXISTS idx_arac_kira_bilgileri_bitis ON arac_kira_bilgileri(sozlesme_bitis);
CREATE INDEX IF NOT EXISTS idx_arac_kira_odemeler_kira ON arac_kira_odemeler(kira_bilgi_id);
CREATE INDEX IF NOT EXISTS idx_arac_kira_odemeler_durum ON arac_kira_odemeler(odeme_durumu);
CREATE INDEX IF NOT EXISTS idx_arac_kira_odemeler_tarih ON arac_kira_odemeler(odeme_donemi);

-- Yorumlar
COMMENT ON TABLE arac_kira_bilgileri IS 'Kiralık araçların sözleşme ve maliyet bilgileri';
COMMENT ON TABLE arac_kira_odemeler IS 'Kiralık araçların ödeme takip kayıtları';
COMMENT ON COLUMN arac_kira_bilgileri.aylik_kira_bedeli IS 'Sadece admin ve finans rolü görebilir';

EOF

echo "Migration tamamlandı!"