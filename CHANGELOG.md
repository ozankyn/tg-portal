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

### Eklendi
- **Eğitim kategorisi**: `egitimler.egitim_kategorisi` (String(20), varsayılan `genel`)
  — Yeni İşe Giriş / Tekrar / Genel. Eğitim ekle-düzenle formunda dropdown,
  listede renkli badge (yeşil/mavi/gri) + kategori filtresi, detayda gösterim
  (migration: `c8d2f6b3a914`, production SQL: `scripts/egitim_kategorisi_kolonu.sql`)
- **Çalışan ehliyet bilgisi**: `calisanlar.ehliyet_sinifi` (String(10), boş = ehliyet yok).
  Çalışan ekle/düzenle formunda dropdown, çalışan detayında gösterim, aday →
  çalışan dönüşümünde otomatik aktarım
  (migration: `b1c4e7a9f250`, production SQL: `scripts/calisan_ehliyet_kolonu.sql`)
- **Ehliyet filtresi**: aday ve çalışan listelerinde Var/Yok/Tümü filtresi
- **Excel export kolonları**: çalışan export'una `TC Kimlik` + `Ehliyet`,
  aday export'una `Ehliyet`
- İK aday ekle/düzenle formuna ehliyet sınıfı alanı ("Var (sınıf belirtilmemiş)"
  seçeneği, sınıfsız işaretlenmiş eski kayıtları korur)

- **Telefon normalizasyonu**: `app/utils.py` içinde `normalize_telefon()` — tüm cep
  numaraları `05XXXXXXXXX` formatına indirgenir (İK çalışan/aday, kariyer başvuru,
  başvuru daveti, beyan doğrulama, kullanıcı formları)
- `scripts/telefon_normalize.py` — mevcut DB kayıtları için toplu düzeltme
  (`--dry-run` / `--apply`, mükerrer ve normalize edilemeyen kayıt raporu)

### Düzeltildi
- Eğitim listesinde 2. sayfadan sonra sayfalama bağlantıları 500 veriyordu
  (`url_for(..., page=p, **request.args)` — `page` iki kez geçiyordu)
- Aday detay sayfasında sürücü belgesi bloğu var olmayan `aday.ehliyet` alanına
  baktığı için hiçbir zaman görünmüyordu; `ehliyet_sinifi` / `ehliyet_var` /
  `ehliyet_tarihi` alanlarına bağlandı
- Açık başvuru formunda zorunlu foto/video, geçersiz format veya boyut aşımında
  sessizce atlanıyor ve başvuru medyasız tamamlanıyordu; format/boyut kontrolü
  aday kaydı oluşturulmadan önceye alındı

### Değiştirildi
- **SMS maliyet optimizasyonu**: NetGSM gönderiminde ASCII metinler `dil=EN` ile
  GSM-7 (160 karakter/segment) olarak gider; Türkçe karakterli metinler `dil=TR`
  ile gönderilmeye devam eder
- Haftalık beyan davet/hatırlatma SMS'i ASCII'ye çevrilip tek segmente (160
  karakter) sığdırılıyor — uzun proje/hafta adlarında metin kademeli kısaltılır
- `send_netgsm_sms()` gönderim öncesi numarayı normalize eder; geçersiz numaralar
  gönderilmez, log'a uyarı yazılır

### Planlanıyor
- Bildirim sistemi genişletmesi (izin, masraf, sözleşme hatırlatmaları)
- Dashboard widget'ları
- Mobil uyumluluk iyileştirmeleri
