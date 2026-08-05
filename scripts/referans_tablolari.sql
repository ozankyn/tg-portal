-- ============================================================
-- TG Portal - Arkadaşını Davet Et (Referans) tabloları
-- ============================================================
-- migrations/ dizini .gitignore'da olduğu için Alembic migration
-- dosyası production'a git ile taşınmaz. Bu script modellerden
-- (app/models/referans.py) birebir üretilmiştir ve production'da
-- elle çalıştırılabilir.
--
-- Kullanım (Hetzner):
--   docker compose -f docker-compose.prod.yml exec -T db \
--     psql -U tgportal -d tgportal < scripts/referans_tablolari.sql
--
-- Ardından SMS şablonunu oluşturun:
--   docker compose -f docker-compose.prod.yml exec web bash -c \
--     "cd /app && PYTHONPATH=/app python3 scripts/referans_davet_sms_sablon_seed.py"
--
-- Script idempotent'tir (IF NOT EXISTS), tekrar çalıştırmak güvenlidir.
-- ============================================================

BEGIN;

-- Proje bazlı public referans linki (proje başına tek token)
CREATE TABLE IF NOT EXISTS referans_linkleri (
    id           SERIAL PRIMARY KEY,
    proje_id     INTEGER NOT NULL UNIQUE REFERENCES projeler (id),
    token        VARCHAR(64) NOT NULL UNIQUE,
    aktif        BOOLEAN NOT NULL DEFAULT TRUE,
    olusturan_id INTEGER REFERENCES users (id),
    created_at   TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at   TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_referans_linkleri_token
    ON referans_linkleri (token);

-- Çalışanların bıraktığı referanslar (davet edilen arkadaşlar)
CREATE TABLE IF NOT EXISTS referans_kayitlari (
    id                    SERIAL PRIMARY KEY,
    proje_id              INTEGER NOT NULL REFERENCES projeler (id),
    davet_eden_calisan_id INTEGER REFERENCES calisanlar (id),
    davet_eden_ad_soyad   VARCHAR(200),
    davet_eden_telefon    VARCHAR(20),
    referans_ad_soyad     VARCHAR(200) NOT NULL,
    referans_telefon      VARCHAR(20) NOT NULL,
    referans_il           VARCHAR(100),
    referans_notu         TEXT,
    durum                 VARCHAR(20) NOT NULL DEFAULT 'yeni',
    arayan_user_id        INTEGER REFERENCES users (id),
    arama_notu            TEXT,
    arama_tarihi          TIMESTAMP WITHOUT TIME ZONE,
    token                 VARCHAR(64) UNIQUE,
    ip                    VARCHAR(200),
    created_at            TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at            TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_referans_kayitlari_proje_id
    ON referans_kayitlari (proje_id);
CREATE INDEX IF NOT EXISTS ix_referans_kayitlari_davet_eden_calisan_id
    ON referans_kayitlari (davet_eden_calisan_id);
CREATE INDEX IF NOT EXISTS ix_referans_kayitlari_referans_telefon
    ON referans_kayitlari (referans_telefon);
CREATE INDEX IF NOT EXISTS ix_referans_kayitlari_durum
    ON referans_kayitlari (durum);
CREATE INDEX IF NOT EXISTS ix_referans_kayitlari_token
    ON referans_kayitlari (token);

COMMIT;
