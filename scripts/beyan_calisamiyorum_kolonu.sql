-- ============================================================
-- TG Portal - Beyan kaydı "çalışamıyorum" kolonu
-- ============================================================
-- migrations/ dizini .gitignore'da olduğu için Alembic migration
-- dosyası production'a git ile taşınmaz. Bu script
-- migrations/versions/c4e8b1a7d360_add_beyan_calisamiyorum.py
-- ile birebir aynı değişikliği uygular.
--
-- Kullanım (Hetzner):
--   docker compose -f docker-compose.prod.yml exec -T db \
--     psql -U tgportal -d tgportal < scripts/beyan_calisamiyorum_kolonu.sql
--
-- Script idempotent'tir (IF NOT EXISTS), tekrar çalıştırmak güvenlidir.
--
-- NOT: Mevcut kayıtlara dokunulmaz. Beyan #5'te 1 gün seçmiş olanlar
-- olduğu gibi kalır; minimum 2 gün kuralı yalnızca yeni gönderimlerde
-- (ve tekrar giren kişilerin güncellemelerinde) uygulanır.
-- ============================================================

BEGIN;

-- Bu hafta hiç çalışamayacağını beyan edenler
ALTER TABLE beyan_kayitlari
    ADD COLUMN IF NOT EXISTS calisamiyorum BOOLEAN NOT NULL DEFAULT FALSE;

-- Alembic sürüm tablosunu da ilerlet (migration ayrıca çalıştırılmayacaksa).
-- Zaten c4e8b1a7d360 ise ikinci çalıştırma bir şey değiştirmez.
UPDATE alembic_version
   SET version_num = 'c4e8b1a7d360'
 WHERE version_num = 'b7e4c2a90f15';

COMMIT;
