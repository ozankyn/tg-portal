-- ============================================================
-- TG Portal - Çalışan ehliyet sınıfı kolonu
-- ============================================================
-- migrations/ dizini .gitignore'da olduğu için Alembic migration
-- dosyası production'a git ile taşınmaz. Bu script
-- migrations/versions/b1c4e7a9f250_add_calisan_ehliyet_sinifi.py
-- ile birebir aynı değişikliği uygular.
--
-- Kullanım (Hetzner):
--   docker compose -f docker-compose.prod.yml exec -T db \
--     psql -U tgportal -d tgportal < scripts/calisan_ehliyet_kolonu.sql
--
-- Script idempotent'tir (IF NOT EXISTS), tekrar çalıştırmak güvenlidir.
--
-- NOT: adaylar tablosundaki ehliyet_var / ehliyet_sinifi / ehliyet_tarihi
-- kolonları zaten mevcuttur, bu script onlara dokunmaz.
-- ============================================================

BEGIN;

-- Ehliyet sınıfı (B, A1, A2, C, D, E, BE, CE ...) — NULL/boş = ehliyet yok
ALTER TABLE calisanlar ADD COLUMN IF NOT EXISTS ehliyet_sinifi VARCHAR(10);

-- Alembic sürüm tablosunu da ilerlet (migration ayrıca çalıştırılmayacaksa).
-- Zaten b1c4e7a9f250 ise ikinci çalıştırma bir şey değiştirmez.
UPDATE alembic_version
   SET version_num = 'b1c4e7a9f250'
 WHERE version_num = 'a7f3c1d9e402';

COMMIT;
