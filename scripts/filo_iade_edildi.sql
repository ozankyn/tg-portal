-- ============================================================
-- TG Portal - Filo: "İade Edildi" araç durumu + iade tarihi
-- ============================================================
-- migrations/ dizini .gitignore'da olduğu için Alembic migration
-- dosyası production'a git ile taşınmaz. Bu script modellerden
-- birebir üretilmiştir ve production'da elle çalıştırılabilir.
--
-- Kullanım (Hetzner):
--   docker compose -f docker-compose.prod.yml exec -T db \
--     psql -U tgportal -d tgportal < scripts/filo_iade_edildi.sql
--
-- Script idempotent'tir (IF NOT EXISTS), tekrar çalıştırmak güvenlidir.
--
-- NOT: "ALTER TYPE ... ADD VALUE" transaction bloğu (BEGIN/COMMIT)
-- içinde çalışmaz; bu yüzden aşağıdaki komutlar transaction'sız,
-- her biri kendi başına autocommit ile çalışır.
-- ============================================================

-- 1) aracdurumu enum'una yeni değeri ekle.
--    SQLAlchemy enum'u üye ADLARINI (büyük harf) saklar: AKTIF, BAKIM, ...
--    Bu yüzden eklenen değer de 'IADE_EDILDI' olmalıdır.
--    Sıralama için ARIZALI'dan sonra, SATILDI'dan önce eklenir.
ALTER TYPE aracdurumu ADD VALUE IF NOT EXISTS 'IADE_EDILDI' BEFORE 'SATILDI';

-- 2) Araç iade tarihi kolonu.
ALTER TABLE araclar ADD COLUMN IF NOT EXISTS iade_tarihi DATE;
