# Changelog

Tüm önemli değişiklikler bu dosyada belgelenir.

Format [Keep a Changelog](https://keepachangelog.com/tr/1.0.0/) standardına uygundur.

## [1.0.0] - 2026-01-12

### Eklendi
- **İK Modülü**: Çalışan yönetimi, zimmet takibi, izin yönetimi, işten çıkış süreci
- **Proje Modülü**: Müşteri, proje ve kadro yönetimi
- **Başvuru Modülü**: Aday davet sistemi, kariyer portalı, SMS doğrulama
- **Filo Modülü**: Araç takibi, yakıt yönetimi, kaza/ceza kayıtları, teslim tutanakları
- **Eğitim Modülü**: Eğitim tanımlama, test sistemi, zorunlu eğitim takibi
- **Masraf Modülü**: Masraf girişi, kategori yönetimi, onay sistemi
- **Satınalma Modülü**: Talep, teklif, sipariş yönetimi
- **Sözleşme Modülü**: Sözleşme takibi, tip yönetimi
- **Talep Modülü**: Genel talep sistemi
- **Onay Modülü**: Çok aşamalı onay akışları, yetki devri
- **Rapor Modülü**: İK, masraf, satınalma raporları
- **Ayarlar Modülü**: Sistem yapılandırması

### Teknik
- Flask 3.0 + SQLAlchemy 2.0
- PostgreSQL 15 veritabanı
- Docker containerization
- Tailwind CSS + Material Symbols tasarım
- NetGSM SMS entegrasyonu
- Flask-Mail email sistemi
- Alpine.js interaktif bileşenler

---

## [Unreleased]

### Planlanıyor
- Bildirim sistemi genişletmesi (izin, masraf, sözleşme hatırlatmaları)
- Dashboard widget'ları
- Mobil uyumluluk iyileştirmeleri
