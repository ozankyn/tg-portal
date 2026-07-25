-- ============================================================
-- TG Portal - Haftalık Çalışma Beyanı tabloları
-- ============================================================
-- migrations/ dizini .gitignore'da olduğu için Alembic migration
-- dosyası production'a git ile taşınmaz. Bu script modellerden
-- (app/models/haftalik_beyan.py) birebir üretilmiştir ve
-- production'da elle çalıştırılabilir.
--
-- Kullanım (Hetzner):
--   docker compose -f docker-compose.prod.yml exec -T db \
--     psql -U tgportal -d tgportal < scripts/haftalik_beyan_tablolari.sql
--
-- Script idempotent'tir (IF NOT EXISTS), tekrar çalıştırmak güvenlidir.
-- ============================================================

BEGIN;

-- Haftalık beyan formu (proje + hafta sonu)
CREATE TABLE IF NOT EXISTS haftalik_beyanlar (
    id              SERIAL PRIMARY KEY,
    proje_id        INTEGER NOT NULL REFERENCES projeler (id),
    hafta_baslangic DATE NOT NULL,
    hafta_bitis     DATE NOT NULL,
    olusturan_id    INTEGER REFERENCES users (id),
    aktif           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_haftalik_beyanlar_proje_id
    ON haftalik_beyanlar (proje_id);

-- Çalışan bazlı gün seçimleri
CREATE TABLE IF NOT EXISTS beyan_kayitlari (
    id            SERIAL PRIMARY KEY,
    beyan_id      INTEGER NOT NULL REFERENCES haftalik_beyanlar (id),
    calisan_id    INTEGER REFERENCES calisanlar (id),
    telefon       VARCHAR(20),
    ad_soyad      VARCHAR(200),
    cuma          BOOLEAN NOT NULL DEFAULT FALSE,
    cumartesi     BOOLEAN NOT NULL DEFAULT FALSE,
    pazar         BOOLEAN NOT NULL DEFAULT FALSE,
    token         VARCHAR(64) UNIQUE,
    kayit_zamani  TIMESTAMP WITHOUT TIME ZONE,
    ip            VARCHAR(200),
    created_at    TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at    TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    CONSTRAINT uq_beyan_calisan UNIQUE (beyan_id, calisan_id)
);

CREATE INDEX IF NOT EXISTS ix_beyan_kayitlari_token
    ON beyan_kayitlari (token);

COMMIT;
