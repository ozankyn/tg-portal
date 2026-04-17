# TG Portal - CLAUDE.md

> Bu dosya Claude Code'un her oturumda otomatik okuduğu proje bağlam dosyasıdır.
> Proje kökünde tutulmalıdır.

---

## 🏢 Proje Bilgileri

- **Proje:** TG Portal - Team Guerilla ERP Sistemi
- **Şirket:** Team Guerilla (Türk pazarlama ve merchandising şirketi)
- **Geliştirici:** Ozan Eren Kayan (@ozankyn)
- **Dil:** Türkçe (UI, değişken isimleri, yorumlar)
- **Kullanıcı sayısı:** ~400-500

---

## 🛠️ Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| **Backend** | Python 3.11+ / Flask |
| **ORM** | SQLAlchemy + Flask-Migrate (Alembic) |
| **Database** | PostgreSQL 15 (Docker) |
| **Cache** | Redis 7 (Docker) |
| **Frontend** | Jinja2 templates + Tailwind CSS (migration tamamlandı ✅) |
| **Auth** | Flask-Login + Role-Permission sistemi |
| **Deploy** | Docker Compose + Gunicorn + Nginx |
| **VCS** | Git → GitHub (github.com/ozankyn/tg-portal) |
| **SMS** | NetGSM API |
| **CSRF** | Flask-WTF CSRFProtect |

---

## 📁 Proje Yapısı

```
tg-portal/
├── app/
│   ├── __init__.py              # Flask factory (create_app)
│   ├── utils.py                 # Decorators, helpers
│   ├── models/
│   │   ├── __init__.py          # Tüm model import'ları (sıralama önemli!)
│   │   ├── base.py              # TimestampMixin, SoftDeleteMixin, AuditMixin, Enum'lar
│   │   ├── core.py              # User, Role, Permission, AuditLog
│   │   ├── ik.py                # Departman, Pozisyon, Calisan, Aday, Izin
│   │   ├── filo.py              # Arac, FiloIslem, YakitKayit, Sigorta, Muayene, Kaza
│   │   ├── tedarikci.py         # Tedarikci
│   │   ├── proje.py             # Musteri, Proje, HedefKadro
│   │   ├── egitim.py            # EgitimTipi, Egitim, EgitimKatilimci, Quiz modeli
│   │   ├── sirket.py            # TuzelKisi, SgkDosya
│   │   ├── masraf.py            # Masraf modeli
│   │   └── onay.py              # Onay workflow modeli
│   │
│   ├── modules/                 # Flask Blueprints
│   │   ├── core/                # Auth, Admin, Dashboard (prefix: /)
│   │   ├── ik/                  # İnsan Kaynakları (prefix: /ik)
│   │   ├── filo/                # Filo Yönetimi (prefix: /filo)
│   │   ├── tedarikci/           # Tedarikçi Yönetimi (prefix: /tedarikci)
│   │   ├── proje/               # Proje & Müşteri (prefix: /proje)
│   │   ├── masraf/              # Masraf Yönetimi (prefix: /masraf)
│   │   ├── egitim/              # Eğitim & Quiz (prefix: /egitim)
│   │   ├── satinalma/           # Satın Alma (prefix: /satinalma)
│   │   ├── basvuru/             # Aday Başvuru - dış erişim (prefix: /basvuru)
│   │   ├── kariyer/             # Kariyer Sayfası - dış erişim (prefix: /kariyer)
│   │   ├── onay/                # Onay Workflow (prefix: /onay)
│   │   ├── ayarlar/             # Sistem Ayarları (prefix: /ayarlar)
│   │   ├── takvim/              # Takvim & Outlook (prefix: /takvim)
│   │   ├── mesaj/               # Mesajlaşma (prefix: /mesaj)
│   │   └── api/                 # REST API v1 (prefix: /api/v1)
│   │
│   └── templates/               # Jinja2 templates (Tailwind CSS)
│       ├── base.html            # Master layout
│       └── [modül_adı]/         # Her modülün kendi template klasörü
│
├── migrations/                  # Alembic migration dosyaları
├── uploads/                     # Kullanıcı dosyaları (Docker volume)
├── static/                      # CSS, JS, images
├── app.py                       # Entry point
├── database.py                  # PostgreSQL connection helper (raw SQL)
├── seed_data.py                 # Seed data scripts
├── docker-compose.yml           # Development
├── docker-compose.prod.yml      # Production
├── Dockerfile
├── nginx.conf                   # Production Nginx config
├── requirements.txt
├── .env                         # Environment variables (git'te YOK)
├── .env.example
├── CHANGELOG.md
└── README.md
```

---

## 🔐 Yetki Sistemi

### Roller
- `Admin` - Tüm yetkiler
- `ik_yonetici` - İK modülü tam yetki
- `filo_yonetici` - Filo + Tedarikçi tam yetki
- `muhasebe` - Görüntüleme + Masraf/Tedarikçi
- `viewer` - Sadece görüntüleme

### Permission Format: `modul.aksiyon`
```
ik.view, ik.create, ik.edit, ik.delete
filo.view, filo.create, filo.edit, filo.bakim, filo.yakit
proje.view, proje.create, proje.edit, proje.delete
masraf.view, masraf.create, masraf.edit
depo.view, depo.edit, depo.delete, depo.admin
egitim.view, egitim.create, egitim.edit
```

### Template'lerde: `{% if has_permission('modul.view') %}`

---

## 🗄️ Veritabanı

- **ORM + Raw SQL karma kullanılıyor** - mevcut dosyanın stiline uy
- **Migration:** `flask db migrate -m "mesaj"` → `flask db upgrade`
- **Model import sırası önemli!** `app/models/__init__.py`'de: base → core → ik → tedarikci → proje → filo → egitim (foreign key bağımlılıkları)
- **RealDictCursor:** `database.py` üzerinden raw SQL sorgular dict döner

---

## 🐳 Docker

### Development (Local - Mac Mini M4 Pro)
```bash
docker-compose up -d
docker-compose exec web bash
docker-compose logs -f web
```

### Production (Hetzner - Linux)
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Container'lar
| Container | Image | Port |
|-----------|-------|------|
| web | Flask + Gunicorn | 5000 (internal) |
| db | postgres:15-alpine | 5432 |
| redis | redis:7-alpine | 6379 |
| nginx | nginx:alpine | 80, 443 (prod only) |

### Volumes (git pull etkilemez!)
- `postgres_data` → Veritabanı
- `redis_data` → Cache
- `uploads_data` → Kullanıcı dosyaları

---

## 🌍 Ortamlar

| Ortam | Sunucu | URL |
|-------|--------|-----|
| Local | Mac Mini M4 Pro | http://localhost:5001 |
| Production | Hetzner 91.99.149.161 | portal.teamguerilla.com |
| Jitsi | Hetzner 49.12.11.155 | meet.teamguerilla.com |

### Deploy: `git push` → sunucuda `git pull` → `docker-compose restart web`
### Migration varsa: `docker-compose exec web flask db upgrade` → `restart web`

---

## ⚙️ Environment Variables (.env)

```bash
SECRET_KEY=xxx
DATABASE_URL=postgresql://tgportal:xxx@db:5432/tgportal
REDIS_URL=redis://redis:6379/0
FLASK_ENV=development|production
NETGSM_USERCODE=5336000570
NETGSM_PASSWORD=xxx
NETGSM_HEADER=TGREKLAMLTD
MAIL_SERVER=mail.teamguerilla.com
MAIL_PORT=587
MAIL_USERNAME=portal@teamguerilla.com
MAIL_PASSWORD=xxx
```

---

## 📐 Kodlama Kuralları

### Genel
- **Türkçe** değişken/fonksiyon isimleri (calisan, arac, tedarikci)
- **Tailwind CSS** kullan (Bootstrap DEĞİL - migration tamamlandı)
- **UTF-8** encoding
- Raw SQL ve ORM karışık - **mevcut dosyanın stiline uy**

### Yeni Blueprint Ekleme
```python
# 1. Model:     app/models/yeni_modul.py
# 2. Routes:    app/modules/yeni_modul/routes.py  
# 3. Templates: app/templates/yeni_modul/*.html
# 4. Register:  app/__init__.py →
from app.modules.yeni_modul.routes import yeni_modul_bp
app.register_blueprint(yeni_modul_bp, url_prefix='/yeni-modul')
csrf.exempt(yeni_modul_bp)  # Gerekiyorsa
```

### Route Pattern
```python
@bp.route('/liste')
@login_required
@permission_required('modul.view')
def liste():
    return render_template('modul/liste.html', active='modul-liste')
```

### Template Pattern
```jinja2
{% extends "base.html" %}
{% block title %}Sayfa Başlığı{% endblock %}
{% block content %}
  <!-- Tailwind CSS class'ları kullan -->
{% endblock %}
```

---

## 📋 Modül Özeti (100+ template)

| Modül | Template | Açıklama |
|-------|----------|----------|
| core | 3 | Auth, Dashboard, Admin |
| ik | 21 | Çalışan, Aday, İzin, Departman, Pozisyon |
| filo | 19 | Araç, Teslim/İade, Yakıt, Sigorta, Muayene, Kaza |
| proje | 12 | Proje, Müşteri, Hedef Kadro |
| egitim | 16 | Eğitim, Quiz, Katılım, Jitsi entegrasyon |
| satinalma | 9 | Satın alma talepleri |
| basvuru | 8 | Dış başvuru formu, SMS doğrulama |
| ayarlar | 8 | Sistem, Kullanıcı, Rol yönetimi |
| masraf | 6 | Masraf girişi, AI fiş okuma, Onay |
| tedarikci | 3 | Tedarikçi CRUD |
| kariyer | 4 | Kariyer sayfası |
| onay | 6 | Generic onay workflow |

---

## 🚨 Dikkat Noktaları

1. **Model import sırası:** `app/models/__init__.py`'de FK bağımlılıklarına dikkat
2. **Docker TTY:** `docker exec container python3 -c "..."` kullan (`-it` flag'i script'lerde hata verir)
3. **Git auth:** GitHub PAT token gerekli
4. **CSRF:** Dış erişimli blueprint'ler ve API için `csrf.exempt()` gerekli
5. **Tailwind:** Tüm 100 template migrate edildi, yeni template'ler de Tailwind kullanmalı

---

## 🗺️ Yol Haritası

- [ ] YOLO bazlı raf tanıma (shelf recognition) entegrasyonu
- [ ] Fotoğraf doğrulama sistemi ticarileştirme
- [ ] Mobile app (API: /api/v1/)
- [ ] Raporlama modülü geliştirme
- [ ] Depo/stok yönetimi modülü genişletme
