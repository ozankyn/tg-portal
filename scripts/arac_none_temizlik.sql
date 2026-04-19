-- String 'None' degerlerini NULL'a cevir
-- KULLANIM: docker compose exec db psql -U tgportal -d tgportal -f /app/scripts/arac_none_temizlik.sql

UPDATE araclar SET sasi_no = NULL WHERE sasi_no = 'None';
UPDATE araclar SET motor_no = NULL WHERE motor_no = 'None';
UPDATE calisanlar SET sicil_no = NULL WHERE sicil_no IN ('None', 'none', '');
