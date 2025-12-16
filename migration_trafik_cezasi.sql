-- Filo Yönetimi - Trafik Cezası Modülü
-- Tarih: 2025-12-16

-- Trafik Cezası Tablosu
CREATE TABLE IF NOT EXISTS arac_trafik_cezalari (
    id SERIAL PRIMARY KEY,
    arac_id INTEGER NOT NULL REFERENCES araclar(id) ON DELETE CASCADE,
    calisan_id INTEGER REFERENCES calisanlar(id) ON DELETE SET NULL,
    
    -- Ceza Bilgileri
    ceza_tarihi DATE NOT NULL,
    ceza_saati TIME,
    ceza_yeri TEXT,
    ceza_turu VARCHAR(100) NOT NULL, -- Hız, Park, Kırmızı Işık, Şerit, Emniyet Kemeri, vb.
    ceza_aciklama TEXT,
    
    -- Resmi Bilgiler
    ceza_no VARCHAR(100), -- Resmi ceza tutanak numarası
    teblig_tarihi DATE,
    
    -- Tutar Bilgileri
    ceza_tutari DECIMAL(10, 2) NOT NULL,
    indirimli_tutar DECIMAL(10, 2), -- Erken ödeme indirimi varsa
    para_birimi VARCHAR(10) DEFAULT 'TRY',
    
    -- Ödeme Bilgileri
    odeme_durumu VARCHAR(20) DEFAULT 'Ödenmedi', -- Ödenmedi, Ödendi, İtiraz Edildi
    odeme_tarihi DATE,
    odeme_sekli VARCHAR(50), -- Banka, Kredi Kartı, PTT, vb.
    
    -- Sorumluluk
    sorumlu VARCHAR(20) DEFAULT 'Çalışan', -- Çalışan, Şirket, Belirsiz
    calisan_odemesi_kesildi BOOLEAN DEFAULT FALSE,
    kesinti_tarihi DATE,
    kesinti_tutari DECIMAL(10, 2),
    
    -- İtiraz Bilgileri
    itiraz_var BOOLEAN DEFAULT FALSE,
    itiraz_tarihi DATE,
    itiraz_sonucu VARCHAR(50), -- Kabul, Red, Beklemede
    itiraz_aciklama TEXT,
    
    -- Belgeler
    ceza_belgesi_yolu TEXT, -- PDF/fotoğraf
    odeme_belgesi_yolu TEXT,
    
    -- Notlar
    notlar TEXT,
    
    -- Timestamps
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    olusturan_user_id INTEGER REFERENCES users(id),
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- İndeksler için kullanılacak
    CONSTRAINT chk_odeme_durumu CHECK (odeme_durumu IN ('Ödenmedi', 'Ödendi', 'İtiraz Edildi', 'İptal'))
);

-- Ceza Türleri Tanım Tablosu (Opsiyonel - standart ceza türleri için)
CREATE TABLE IF NOT EXISTS trafik_ceza_turleri (
    id SERIAL PRIMARY KEY,
    ceza_turu VARCHAR(100) UNIQUE NOT NULL,
    varsayilan_tutar DECIMAL(10, 2),
    aciklama TEXT,
    aktif BOOLEAN DEFAULT TRUE
);

-- Standart ceza türlerini ekle
INSERT INTO trafik_ceza_turleri (ceza_turu, varsayilan_tutar, aciklama) VALUES
('Hız Sınırı İhlali', 1000.00, 'Hız sınırını aşma'),
('Kırmızı Işık İhlali', 3000.00, 'Kırmızı ışıkta geçme'),
('Park İhlali', 500.00, 'Yasak yerde park etme'),
('Şerit İhlali', 800.00, 'Şerit değiştirme kurallarına uymama'),
('Emniyet Kemeri', 500.00, 'Emniyet kemeri takmama'),
('Cep Telefonu Kullanımı', 1000.00, 'Sürüş sırasında telefon kullanma'),
('Dönüş İhlali', 800.00, 'Yasak dönüş yapma'),
('Takip Mesafesi', 800.00, 'Güvenli takip mesafesini korumama'),
('Alkollü Araç Kullanma', 5000.00, 'Alkollü araç kullanma'),
('Ehliyetsiz Araç Kullanma', 10000.00, 'Ehliyetsiz veya geçersiz ehliyet ile araç kullanma'),
('Sigorta', 1500.00, 'Zorunlu trafik sigortası olmadan araç kullanma'),
('Muayene', 1000.00, 'Muayenesiz araç kullanma'),
('Diğer', 0.00, 'Diğer trafik cezaları')
ON CONFLICT (ceza_turu) DO NOTHING;

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_trafik_cezalari_arac ON arac_trafik_cezalari(arac_id);
CREATE INDEX IF NOT EXISTS idx_trafik_cezalari_calisan ON arac_trafik_cezalari(calisan_id);
CREATE INDEX IF NOT EXISTS idx_trafik_cezalari_tarih ON arac_trafik_cezalari(ceza_tarihi);
CREATE INDEX IF NOT EXISTS idx_trafik_cezalari_odeme ON arac_trafik_cezalari(odeme_durumu);
CREATE INDEX IF NOT EXISTS idx_trafik_cezalari_sorumlu ON arac_trafik_cezalari(sorumlu);
CREATE INDEX IF NOT EXISTS idx_trafik_cezalari_turu ON arac_trafik_cezalari(ceza_turu);

-- Yorumlar
COMMENT ON TABLE arac_trafik_cezalari IS 'Araç trafik cezaları ve ödeme takibi';
COMMENT ON TABLE trafik_ceza_turleri IS 'Standart trafik ceza türleri ve tutarları';
COMMENT ON COLUMN arac_trafik_cezalari.sorumlu IS 'Kim sorumlu: Çalışan, Şirket, Belirsiz';
COMMENT ON COLUMN arac_trafik_cezalari.calisan_odemesi_kesildi IS 'Ceza tutarı çalışandan kesildi mi?';

-- Trigger: Güncelleme tarihi otomatik güncelleme
CREATE OR REPLACE FUNCTION update_trafik_ceza_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.guncelleme_tarihi = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_trafik_ceza_timestamp
    BEFORE UPDATE ON arac_trafik_cezalari
    FOR EACH ROW
    EXECUTE FUNCTION update_trafik_ceza_timestamp();

SELECT 'Trafik Cezası modülü başarıyla oluşturuldu!' as sonuc;