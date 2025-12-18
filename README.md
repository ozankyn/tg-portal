# TG Portal - Team Guerilla ERP Sistemi

Modüler ERP sistemi. İK, Filo Yönetimi ve Tedarikçi Yönetimi modüllerini içerir.

## 🚀 Hızlı Başlangıç

### Docker ile (Önerilen)

```bash
# Repo'yu klonla
git clone https://github.com/ozankyn/tg-portal.git
cd tg-portal

# Docker'ı başlat
docker-compose up -d

# Veritabanını oluştur ve seed data yükle
docker-compose exec web flask init-db
docker-compose exec web flask seed

# Tarayıcıda aç
# http://localhost:5000
# Giriş: admin@teamguerilla.com / admin123
```

### Manuel Kurulum

```bash
# Virtual environment oluştur
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# .env dosyasını düzenle

# Veritabanını oluştur
flask init-db
flask seed

# Çalıştır
python app.py
```

## 📁 Proje Yapısı

```
tg-portal/
├── app/
│   ├── __init__.py        # Flask factory
│   ├── utils.py           # Decorators & helpers
│   ├── models/            # SQLAlchemy models
│   │   ├── base.py        # Mixins & Enums
│   │   ├── core.py        # User, Role, Permission
│   │   ├── ik.py          # HR models
│   │   ├── filo.py        # Fleet models
│   │   └── tedarikci.py   # Supplier models
│   ├── modules/           # Blueprint routes
│   │   ├── core/          # Auth, Admin, Dashboard
│   │   ├── ik/            # HR routes
│   │   ├── filo/          # Fleet routes
│   │   ├── tedarikci/     # Supplier routes
│   │   └── api/           # REST API
│   └── templates/         # Jinja2 templates
├── migrations/            # Alembic migrations
├── uploads/               # User uploads
├── app.py                 # Entry point
├── seed_data.py           # Initial data
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 🔐 Yetki Sistemi

### Roller
- **admin**: Tüm yetkiler
- **ik_yonetici**: İK modülü tam yetki
- **filo_yonetici**: Filo + Tedarikçi tam yetki
- **muhasebe**: Görüntüleme + Tedarikçi yönetimi
- **viewer**: Sadece görüntüleme

### Yetki Kodları
- `ik.view`, `ik.create`, `ik.edit`, `ik.delete`
- `filo.view`, `filo.create`, `filo.edit`, `filo.bakim`, `filo.yakit`
- `tedarikci.view`, `tedarikci.create`, `tedarikci.edit`, `tedarikci.delete`

## 🔧 CLI Komutları

```bash
flask init-db    # Tabloları oluştur
flask seed       # Örnek verileri yükle
flask shell      # Interactive shell
```

## 📡 API Endpoints

```
GET  /api/v1/health          # Health check
GET  /api/v1/me              # Current user
GET  /api/v1/calisanlar      # Çalışan listesi
GET  /api/v1/araclar         # Araç listesi
GET  /api/v1/tedarikciler    # Tedarikçi listesi
GET  /api/v1/stats           # İstatistikler
```

## 🛠️ Teknolojiler

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: Bootstrap 5, Jinja2
- **Auth**: Flask-Login, Role+Permission system
- **Deploy**: Docker, Gunicorn

## 📝 Geliştirme

```bash
# Test çalıştır
pytest

# Migration oluştur
flask db migrate -m "Description"
flask db upgrade
```

## 📄 Lisans

© 2024 Team Guerilla - Tüm hakları saklıdır.
