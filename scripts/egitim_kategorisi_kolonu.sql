-- ============================================================
-- TG Portal - Eğitim kategorisi kolonu
-- ============================================================
-- migrations/ dizini .gitignore'da olduğu için Alembic migration
-- dosyası production'a git ile taşınmaz. Bu script
-- migrations/versions/c8d2f6b3a914_add_egitim_kategorisi.py
-- ile birebir aynı değişikliği uygular.
--
-- Kullanım (Hetzner):
--   docker compose -f docker-compose.prod.yml exec -T db \
--     psql -U tgportal -d tgportal < scripts/egitim_kategorisi_kolonu.sql
--
-- Script idempotent'tir (IF NOT EXISTS), tekrar çalıştırmak güvenlidir.
-- ============================================================

BEGIN;

-- Eğitim kategorisi: yeni_giris | tekrar | genel
-- Mevcut kayıtlar DEFAULT ile 'genel' olur.
ALTER TABLE egitimler
    ADD COLUMN IF NOT EXISTS egitim_kategorisi VARCHAR(20) NOT NULL DEFAULT 'genel';

-- Alembic sürüm tablosunu ilerlet (migration ayrıca çalıştırılmayacaksa).
-- Önceki sürüm b1c4e7a9f250 (calisanlar.ehliyet_sinifi) değilse bir şey değişmez;
-- o durumda önce scripts/calisan_ehliyet_kolonu.sql çalıştırılmalıdır.
UPDATE alembic_version
   SET version_num = 'c8d2f6b3a914'
 WHERE version_num = 'b1c4e7a9f250';

COMMIT;
