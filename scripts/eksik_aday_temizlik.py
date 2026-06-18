"""
TG Portal - Eksik Aday Temizlik Script'i
=========================================
Eski başvuru akışında, KVKK onayında boş ad/soyad ile oluşturulan ve form
hiçbir zaman tamamlanmamış "yarım" aday kayıtlarını temizler.

Yeni akışta aday kaydı yalnızca form gönderilince oluşur; bu script tek
seferlik geçiş temizliği içindir.

Adı veya soyadı boş/NULL olan aday kayıtlarını bulur ve soft-delete eder.

KULLANIM:
  cd /app && PYTHONPATH=/app python3 scripts/eksik_aday_temizlik.py --dry-run
  cd /app && PYTHONPATH=/app python3 scripts/eksik_aday_temizlik.py --apply

Production:
  docker compose -f docker-compose.prod.yml exec web bash -c \
    "cd /app && PYTHONPATH=/app python3 scripts/eksik_aday_temizlik.py --apply"
"""
import sys
from datetime import datetime
from sqlalchemy import or_


def run(mode='dry-run'):
    from app import create_app, db
    from app.models.ik import Aday

    app = create_app()
    with app.app_context():
        print("=" * 80)
        print(f"  EKSIK ADAY TEMIZLIK [{mode.upper()}]")
        print(f"  Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)

        # Adı veya soyadı boş/NULL olan, henüz silinmemiş adaylar
        eksikler = Aday.query.filter(
            Aday.is_deleted == False,
            or_(
                Aday.ad == None, Aday.ad == '',
                Aday.soyad == None, Aday.soyad == '',
            )
        ).all()

        print(f"\nBulunan eksik aday kaydı: {len(eksikler)}\n")

        if not eksikler:
            print("Temizlenecek kayıt yok. ✓")
            return

        for a in eksikler:
            print(f"  - id={a.id:<6} ad='{a.ad or ''}' soyad='{a.soyad or ''}' "
                  f"durum={a.durum} kadro_id={a.kadro_id} "
                  f"olusturma={a.created_at.strftime('%Y-%m-%d %H:%M') if a.created_at else '-'}")

        if mode != 'apply':
            print(f"\n[DRY-RUN] {len(eksikler)} kayıt silinecekti. "
                  f"Uygulamak için: --apply")
            return

        for a in eksikler:
            a.soft_delete()
        db.session.commit()
        print(f"\n[APPLY] {len(eksikler)} eksik aday kaydı soft-delete edildi. ✓")


if __name__ == '__main__':
    mode = 'apply' if '--apply' in sys.argv else 'dry-run'
    run(mode)
