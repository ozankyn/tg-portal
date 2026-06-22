"""
TG Portal - Kullanıcı Yönetimi Özel Yetki Script'i
===================================================
1. 'admin.kullanici_yonetimi' permission'ını oluşturur (yoksa).
2. Bu yetkiyi bireysel claim olarak 'abdurrahmangulec' kullanıcısına atar.

Bu yetkisi olan kullanıcı, is_admin olmasa bile kullanıcı yönetimi
ekranlarına (core.admin_kullanicilar / ekle / duzenle) erişebilir.

KULLANIM (production'da):
  docker compose -f docker-compose.prod.yml exec web bash -c \
    "cd /app && PYTHONPATH=/app python3 scripts/kullanici_yonetimi_yetki.py"

KULLANIM (local):
  docker-compose exec web bash -c \
    "cd /app && PYTHONPATH=/app python3 scripts/kullanici_yonetimi_yetki.py"
"""

PERM_CODE = 'admin.kullanici_yonetimi'
PERM_NAME = 'Kullanıcı Yönetimi'
PERM_DESC = 'Admin olmadan kullanıcı ekleme/düzenleme/listeleme erişimi'
PERM_MODULE = 'admin'

HEDEF_KULLANICI = 'abdurrahmangulec'  # email'in @ öncesi kısmı


def run():
    from app import create_app, db
    from app.models.core import User, Permission

    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("  KULLANICI YÖNETİMİ ÖZEL YETKİ KURULUMU")
        print("=" * 70)

        # 1) Permission oluştur / bul
        perm = Permission.query.filter_by(code=PERM_CODE).first()
        if perm:
            print(f"[OK]   Permission zaten var: {PERM_CODE} (id={perm.id})")
        else:
            perm = Permission(
                code=PERM_CODE,
                name=PERM_NAME,
                description=PERM_DESC,
                module=PERM_MODULE,
            )
            db.session.add(perm)
            db.session.flush()
            print(f"[YENI] Permission oluşturuldu: {PERM_CODE} (id={perm.id})")

        # 2) Kullanıcıyı bul (email @ öncesi ile)
        user = User.query.filter(
            User.email.ilike(f'{HEDEF_KULLANICI}@%'),
            User.is_deleted == False,
        ).first()

        if not user:
            print(f"[HATA] Kullanıcı bulunamadı: '{HEDEF_KULLANICI}@...'")
            print("       Mevcut benzer kullanıcılar:")
            for u in User.query.filter(User.email.ilike(f'%{HEDEF_KULLANICI}%')).all():
                print(f"         - {u.email}")
            db.session.rollback()
            return

        print(f"[OK]   Kullanıcı: {user.full_name} <{user.email}> (id={user.id}, admin={user.is_admin})")

        # 3) Claim ata
        if perm in user.claims:
            print(f"[OK]   Yetki zaten atanmış: {PERM_CODE}")
        else:
            user.claims.append(perm)
            print(f"[YENI] Yetki atandı: {PERM_CODE} -> {user.email}")

        db.session.commit()
        print("\n[TAMAM] Değişiklikler kaydedildi.")
        print(f"        {user.email} artık kullanıcı yönetimine erişebilir.")


if __name__ == '__main__':
    run()
