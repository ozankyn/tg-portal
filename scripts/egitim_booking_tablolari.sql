-- ============================================================
-- TG Portal - Eğitim Booking Sistemi tabloları
-- ============================================================
-- migrations/ dizini .gitignore'da olduğu için Alembic migration
-- dosyası production'a git ile taşınmaz. Bu script modellerden
-- birebir üretilmiştir ve production'da elle çalıştırılabilir.
--
-- Kullanım (Hetzner):
--   docker compose -f docker-compose.prod.yml exec -T db \
--     psql -U tgportal -d tgportal < scripts/egitim_booking_tablolari.sql
--
-- Script idempotent'tir (IF NOT EXISTS), tekrar çalıştırmak güvenlidir.
-- ============================================================

BEGIN;

-- Eğitim oturumları (tarih/saat bazlı, kontenjanlı)
CREATE TABLE IF NOT EXISTS egitim_oturumlari (
    id              SERIAL PRIMARY KEY,
    egitim_id       INTEGER NOT NULL REFERENCES egitimler (id),
    tarih           DATE NOT NULL,
    baslangic_saati TIME WITHOUT TIME ZONE NOT NULL,
    bitis_saati     TIME WITHOUT TIME ZONE,
    kontenjan       INTEGER NOT NULL DEFAULT 20,
    aciklama        VARCHAR(200),
    toplanti_linki  VARCHAR(500),
    aktif           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_egitim_oturumlari_egitim_id
    ON egitim_oturumlari (egitim_id);

-- Public booking kayıtları (telefon doğrulamalı)
CREATE TABLE IF NOT EXISTS egitim_kayitlari (
    id             SERIAL PRIMARY KEY,
    oturum_id      INTEGER NOT NULL REFERENCES egitim_oturumlari (id),
    egitim_id      INTEGER NOT NULL REFERENCES egitimler (id),
    ad_soyad       VARCHAR(120) NOT NULL,
    telefon        VARCHAR(20) NOT NULL,          -- normalize: son 10 hane
    email          VARCHAR(120),
    calisan_id     INTEGER REFERENCES calisanlar (id),
    aday_id        INTEGER REFERENCES adaylar (id),
    kayit_zamani   TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    durum          VARCHAR(20) NOT NULL DEFAULT 'onaylandi',  -- onaylandi | iptal
    iptal_zamani   TIMESTAMP WITHOUT TIME ZONE,
    iptal_eden     VARCHAR(20),                   -- katilimci | ik
    token          VARCHAR(64) NOT NULL,
    sms_gonderildi BOOLEAN DEFAULT FALSE,
    ip             VARCHAR(45),
    created_at     TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at     TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_egitim_kayitlari_egitim_id ON egitim_kayitlari (egitim_id);
CREATE INDEX IF NOT EXISTS ix_egitim_kayitlari_oturum_id ON egitim_kayitlari (oturum_id);
CREATE INDEX IF NOT EXISTS ix_egitim_kayitlari_telefon   ON egitim_kayitlari (telefon);
CREATE UNIQUE INDEX IF NOT EXISTS ix_egitim_kayitlari_token ON egitim_kayitlari (token);

-- Aynı eğitime aynı telefondan yalnızca BİR aktif kayıt.
-- Partial index: iptal edilmiş kayıtlar hariç tutulur ki kişi
-- iptal ettikten sonra yeniden kaydolabilsin.
CREATE UNIQUE INDEX IF NOT EXISTS uq_egitim_kayit_aktif
    ON egitim_kayitlari (egitim_id, telefon)
    WHERE durum = 'onaylandi';

-- Eğitim sonrası memnuniyet anketi (kayıt başına en fazla bir yanıt)
CREATE TABLE IF NOT EXISTS egitim_anketleri (
    id           SERIAL PRIMARY KEY,
    egitim_id    INTEGER NOT NULL REFERENCES egitimler (id),
    oturum_id    INTEGER REFERENCES egitim_oturumlari (id),
    kayit_id     INTEGER UNIQUE REFERENCES egitim_kayitlari (id),
    puan         INTEGER NOT NULL,   -- genel memnuniyet 1-5
    egitmen_puan INTEGER,            -- 1-5
    icerik_puan  INTEGER,            -- 1-5
    yorum        TEXT,
    ip           VARCHAR(45),
    created_at   TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at   TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_egitim_anketleri_egitim_id ON egitim_anketleri (egitim_id);

COMMIT;
