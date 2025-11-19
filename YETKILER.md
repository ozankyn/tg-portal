# Yetki Matrisi - İK Yönetim Sistemi

## Rol Tanımları

### 🔴 Admin (Sistem Yöneticisi)
- **Tüm yetkiler**
- Kullanıcı yönetimi (ekleme, düzenleme, silme)
- Tüm modüllere tam erişim

### 🟡 Manager (Yönetici)
- Proje ekleme/düzenleme
- Kadro ekleme/düzenleme
- Aday ekleme/düzenleme
- Çalışana dönüştürme
- Raporları görüntüleme
- **Kullanıcı yönetimi YOK**

### ⚫ User (Kullanıcı)
- Dashboard görüntüleme
- Proje/Kadro/Aday/Çalışan listelerini görüntüleme
- Aday ekleme (sadece)
- **Düzenleme/Silme YOK**

---

## Yetki Tablosu

| İşlem | Admin | Manager | User |
|-------|-------|---------|------|
| **Dashboard** |
| Dashboard Görüntüleme | ✅ | ✅ | ✅ |
| **Projeler** |
| Proje Listesi | ✅ | ✅ | ✅ |
| Proje Ekleme | ✅ | ✅ | ❌ |
| Proje Düzenleme | ✅ | ✅ | ❌ |
| Proje Silme | ✅ | ✅ | ❌ |
| **Kadrolar** |
| Kadro Listesi | ✅ | ✅ | ✅ |
| Kadro Ekleme | ✅ | ✅ | ❌ |
| Kadro Düzenleme | ✅ | ✅ | ❌ |
| Kadro Silme | ✅ | ✅ | ❌ |
| **Adaylar** |
| Aday Listesi | ✅ | ✅ | ✅ |
| Aday Ekleme | ✅ | ✅ | ✅ |
| Aday Düzenleme | ✅ | ✅ | ❌ |
| Çalışana Dönüştürme | ✅ | ✅ | ❌ |
| **Çalışanlar** |
| Çalışan Listesi | ✅ | ✅ | ✅ |
| **Kullanıcı Yönetimi** |
| Kullanıcı Listesi | ✅ | ❌ | ❌ |
| Kullanıcı Ekleme | ✅ | ❌ | ❌ |
| Kullanıcı Düzenleme | ✅ | ❌ | ❌ |
| Kullanıcı Silme | ✅ | ❌ | ❌ |
| **Loglar** |
| Log Görüntüleme | ✅ | ✅ | ✅ |
| **Profil** |
| Kendi Profilini Görme | ✅ | ✅ | ✅ |
| Şifre Değiştirme | ✅ | ✅ | ✅ |

---

## Kullanım Örnekleri

### Admin Kullanıcısı
```
Kullanıcı: admin
Şifre: admin123
Yetkiler: Tüm sistem
```

### Manager Kullanıcısı Oluşturma
1. Admin olarak giriş yap
2. Kullanıcılar menüsüne git
3. "Yeni Kullanıcı Ekle"
4. Rol: "Yönetici (Manager)" seç

### User Kullanıcısı Oluşturma
1. Admin olarak giriş yap
2. Kullanıcılar menüsüne git
3. "Yeni Kullanıcı Ekle"
4. Rol: "Kullanıcı (User)" seç