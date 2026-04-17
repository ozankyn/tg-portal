# TG Portal - Kullanım Kılavuzu

> **Team Guerilla ERP Sistemi**
> Son güncelleme: 17 Nisan 2026
> Hedef kitle: Ofis çalışanları (İK, Muhasebe, Koordinatörler, Yöneticiler)

---

## 1. Giriş ve Temel Bilgiler

### 1.1 Sisteme Giriş

1. Tarayıcınızda **portal.teamguerilla.com** adresine gidin
2. E-posta adresinizi ve şifrenizi girin
3. **Giriş Yap** butonuna tıklayın
4. Kontrol Paneli (Dashboard) açılacaktır

> **Not:** Şifrenizi unuttuysanız İK ekibinden sıfırlama talep edin.

### 1.2 Şifre Değiştirme

1. Sol menüden adınıza veya profil simgesine tıklayın
2. **Profil** sayfasında "Şifre Değiştir" bölümüne gidin
3. Mevcut şifrenizi, ardından yeni şifrenizi iki kez girin
4. **Kaydet** butonuna tıklayın

### 1.3 Çıkış Yapma

Sol menünün en altındaki kırmızı **Çıkış Yap** butonuna tıklayın.

---

## 2. Ana Sayfa ve Navigasyon

### 2.1 Kontrol Paneli (Dashboard)

Giriş yaptıktan sonra ilk karşınıza çıkan ekrandır. Özet bilgileri gösterir:

| Kart | Açıklama |
|------|----------|
| Toplam Çalışan | Aktif çalışan sayısı |
| Araç Sayısı | Filodaki aktif araç sayısı |
| Aktif Proje | Devam eden proje sayısı |
| Bekleyen Aday | İşe alım bekleyen aday sayısı |

Ayrıca:
- **Proje Doluluk Durumu** — Her projenin kadro/doluluk oranını gösterir
- **Acil Kadro İhtiyacı** — Öncelikli pozisyon açıklarını listeler
- **Son Eklenenler** — Yeni kayıt olan çalışanlar
- **Araç Durumu Özeti** — Aktif, bakımda, arızalı araç dağılımı

### 2.2 Sol Menü Yapısı

Sol menüde yetkinize göre farklı bölümler görürsünüz. Tüm menü öğeleri:

| Bölüm | Menü | Yetki |
|-------|------|-------|
| **Genel** | Kontrol Paneli, Onaylar, Görevlerim, Takvim, Mesajlar | Herkes |
| **Proje Yönetimi** | Projeler, Müşteriler | proje.view |
| **İnsan Kaynakları** | İK Dashboard, Organizasyon, Adaylar, Çalışanlar, Zimmet, Eğitim, İzin Talepleri | ik.view |
| **Masraf** | Masraflarım, Masraf Raporlarım | Herkes |
| **Sözleşmeler** | Sözleşmeler | sozlesme.view |
| **Satın Alma** | Satın Alma | satinalma.view |
| **Destek** | Talepler | Herkes |
| **Raporlar** | Raporlar, AI Asistan | rapor.view |
| **Filo Yönetimi** | Araçlar, İşlemler (Yakıt, Teslim/İade, Kazalar, Cezalar) | filo.view |
| **Tedarikçiler** | Tedarikçiler | tedarikci.view |
| **Yönetim** | Ayarlar | Sadece Admin |

### 2.3 Onay Bildirimleri

Sol menüdeki **Onaylar** sekmesinde turuncu bir sayı rozeti görüyorsanız, sizden onay bekleyen talepler vardır. Tıklayıp onay veya red işlemini yapabilirsiniz.

---

## 3. Rol Bazlı Erişim

Portal 15 farklı rol tanımına sahiptir. Her kullanıcıya bir veya birden fazla rol atanabilir.

### 3.1 Temel Roller

| Rol | Erişim Kapsamı |
|-----|----------------|
| **Admin** | Tüm modüller, tüm yetkiler, kullanıcı ve rol yönetimi |
| **İK Yöneticisi** | İK modülü tam yetki (çalışan, aday, izin, evrak, eğitim) |
| **Proje Yöneticisi** | Proje, müşteri, kadro yönetimi |
| **Filo Yöneticisi** | Araç, yakıt, bakım, sigorta, kaza yönetimi |
| **Muhasebe** | Masraf, tedarikçi, sözleşme görüntüleme ve yönetim |
| **Saha Koordinatörü** | Kendi projesindeki personel ve masraflar |
| **Eğitim Yöneticisi** | Eğitim oluşturma, katılım takibi, zorunlu eğitim yönetimi |
| **Ofis Çalışanı** | Temel masraf girişi, görev ve takvim |
| **Saha Çalışanı** | Sadece kendi bilgileri, masraf girişi |
| **Viewer** | Sadece görüntüleme, değişiklik yapamaz |

### 3.2 Yetki Kontrolü

- Menüde göremediğiniz bir bölüm varsa o modüle yetkiniz yoktur
- Bir sayfaya erişmeye çalışıp "Yetkiniz yok" uyarısı alırsanız yöneticinize başvurun
- Yetki değişiklikleri admin tarafından **Ayarlar > Kullanıcı Yönetimi** üzerinden yapılır

---

## 4. Modül Kullanım Rehberi

---

### 4.1 İnsan Kaynakları (İK)

#### Çalışan Listesi Görüntüleme

1. Sol menüden **İnsan Kaynakları > Çalışanlar > Çalışan Listesi** seçin
2. Üst kısımdaki filtrelerle arayın:
   - **Arama kutusu**: Ad, soyad veya e-posta ile arama
   - **Departman**: Departmana göre filtreleme
   - **Durum**: Aktif, İzinli, Ayrıldı
3. Bir çalışanın adına tıklayarak detay sayfasına gidin

#### Yeni Çalışan Ekleme

1. **Çalışanlar > Yeni Çalışan** menüsüne tıklayın
2. Zorunlu alanları doldurun:
   - **Ad ve Soyad**
   - **TC Kimlik No** (11 haneli)
   - **Departman ve Pozisyon** seçin
   - **İşe Başlama Tarihi**
3. Ek bilgileri girin: telefon, e-posta, adres, eğitim durumu, beden, kargo şubesi
4. **Kaydet** butonuna tıklayın

#### Çalışan Bilgilerini Düzenleme

1. Çalışan listesinden ilgili kişiyi bulun
2. Detay sayfasında **Düzenle** butonuna tıklayın
3. Gerekli değişiklikleri yapın
4. **Kaydet** butonuna tıklayın

#### Evrak Yükleme

1. Çalışan detay sayfasında **Evraklar** sekmesine gidin
2. **Evrak Ekle** butonuna tıklayın
3. Evrak tipini seçin (Nüfus Cüzdanı, Diploma, SGK, Sağlık Raporu vb.)
4. Dosyayı seçin (PDF veya görsel)
5. Geçerlilik tarihi varsa girin
6. **Yükle** butonuna tıklayın

#### Zimmet Yönetimi

1. **İnsan Kaynakları > Zimmet > Zimmet Listesi** menüsüne gidin
2. **Yeni Zimmet** ile çalışana ekipman atayın:
   - Çalışan seçin
   - Zimmet tipi (Laptop, Telefon, Araç Anahtarı vb.)
   - Marka, model, seri numarası
   - Teslim tarihi
3. İşten ayrılma durumunda **İade Et** ile iade işlemini kaydedin

#### İzin Talepleri

1. **İnsan Kaynakları > İzin Talepleri** menüsüne gidin
2. **Yeni İzin Talebi** butonuna tıklayın
3. Bilgileri girin:
   - **İzin Tipi**: Yıllık, Mazeret, Hastalık, Ücretsiz, Doğum
   - **Başlangıç ve Bitiş Tarihi**
   - **Açıklama**
4. **Kaydet** veya **Onaya Gönder** butonuna tıklayın

**Yöneticiler için:** İzin taleplerini Onaylar sekmesinden onaylayabilir veya reddedebilirsiniz.

#### Aday Yönetimi ve İşe Alım

1. **İnsan Kaynakları > Adaylar > Aday Listesi** menüsüne gidin
2. **Yeni Aday Ekle** ile aday kaydı oluşturun
3. Adayın durumunu takip edin:
   - Başvurdu → Değerlendiriliyor → Mülakat → Teklif → İşe Alındı
4. **İşe Al** butonu ile adayı çalışan kaydına dönüştürün
5. İşe alım sırasında TC kimlik, işe başlama tarihi ve pozisyon bilgilerini doğrulayın

#### İşten Çıkış Süreci

1. **İnsan Kaynakları > Çalışanlar > İşten Çıkışlar** menüsüne gidin
2. **Yeni Çıkış Kaydı** oluşturun
3. Gerekli bilgileri doldurun:
   - Çalışan seçin
   - Çıkış tipi: İstifa, Fesih, Anlaşmalı, Emeklilik
   - Planlanan çıkış tarihi
   - Zimmet teslim kontrolü
   - SGK çıkış bildirimi
4. Süreç tamamlandığında çalışan durumu otomatik olarak **AYRILDI** olur

---

### 4.2 Filo Yönetimi

#### Araç Listesi

1. Sol menüden **Filo Yönetimi > Araçlar** seçin
2. Plaka, marka veya model ile arama yapın
3. Durum filtresi: Aktif, Bakımda, Arızalı, Satıldı
4. Araç plakasına tıklayarak detay sayfasını açın

#### Yeni Araç Ekleme

1. Araç listesinde **Yeni Araç** butonuna tıklayın
2. Bilgileri girin:
   - **Plaka** (zorunlu, benzersiz)
   - **Marka ve Model**
   - **Model Yılı, Renk, Yakıt Tipi**
   - **Şasi No, Motor No**
   - **Sahiplik**: Şirket, Kiralama veya Leasing
   - Kiralama ise: başlangıç/bitiş tarihi, aylık kira
   - **Atanan Çalışan** ve **Proje**
3. **Kaydet** butonuna tıklayın

#### Yakıt Kaydı Girişi

1. Araç detay sayfasında **Yakıt Ekle** butonuna tıklayın
   veya **Filo > İşlemler > Yakıt Kayıtları** menüsüne gidin
2. Bilgileri girin:
   - Tarih, güncel kilometre
   - Litre, birim fiyat (toplam otomatik hesaplanır)
   - İstasyon adı, full depo mu?
3. **Kaydet** — Araç kilometresi otomatik güncellenir

> **Toplu Yakıt İmport:** Yakıt kayıtları sayfasında **Excel İmport** butonu ile toplu yükleme yapabilirsiniz. Excel formatı: PLAKA, YAKIT TİPİ, İSTASYON, İŞLEM TARİHİ, MİKTAR, TUTAR

#### Bakım/Tamir Kaydı

1. Araç detay sayfasında **İşlem Ekle** butonuna tıklayın
2. İşlem tipini seçin: Bakım, Tamir, Sigorta, Muayene, Diğer
3. Tarih, kilometre, tutar ve açıklama girin
4. Fatura numarası ve tedarikçi seçin
5. Sonraki bakım tarihi/kilometresini girin (hatırlatma oluşturur)
6. **Kaydet** butonuna tıklayın

#### Araç Teslim ve İade

**Teslim (Çalışana araç verme):**
1. Araç detayında **Teslim Et** butonuna tıklayın
2. Kilometre okuyun ve girin
3. Yakıt seviyesini belirtin
4. Aksesuar kontrol listesini işaretleyin (stepne, yangın tüpü, çeki demiri vb.)
5. Hasar notu varsa yazın
6. Fotoğraf çekin ve yükleyin
7. **Teslim Et** butonuna tıklayın

**İade (Çalışandan araç alma):**
1. Araç detayında **İade Al** butonuna tıklayın
2. Aynı adımları takip edin
3. Teslim zamanındaki durumla karşılaştırın: eksik aksesuar, yeni hasar
4. **İade Al** butonuna tıklayın

#### Kaza Kaydı

1. **Filo > İşlemler > Kazalar** menüsüne gidin
2. **Kaza Bildir** butonuna tıklayın
3. Bilgileri girin:
   - Araç ve sürücü seçin
   - Tarih, saat, konum
   - Kusur oranı (%), hasar tutarı
   - Sigorta tarafından karşılanan tutar
   - Yaralanma var mı?
   - Tutanak no, açıklama
4. **En az 1 fotoğraf** yüklemeniz zorunludur
5. **Kaydet** — Kaza onay sürecine girer
6. Yönetici onay veya red verir

#### Trafik Cezası Kaydı

1. **Filo > İşlemler > Trafik Cezaları** menüsüne gidin
2. **Ceza Ekle** butonuna tıklayın
3. Bilgileri girin: tarih, araç, sürücü, tutar, ihlal açıklaması
4. İndirimli tutar varsa girin
5. Ceza belgesi yükleyin
6. Ödeme yapıldığında **Ödendi** butonuna tıklayın
7. Sürücüye yansıtmak için **Yansıt** butonuna tıklayın

---

### 4.3 Masraf Yönetimi

#### Masraf Girişi

1. Sol menüden **Masraflarım** seçin
2. **Yeni Masraf** butonuna tıklayın
3. Bilgileri doldurun:
   - **Başlık**: Kısa açıklama (örn: "İstanbul-Ankara otobüs bileti")
   - **Tarih**: Masrafın yapıldığı tarih
   - **Kategori**: Ulaşım, Yemek, Konaklama, Ofis Malzemesi vb.
   - **Tutar**: KDV hariç tutar
   - **KDV Oranı**: %0, %1, %10 veya %20
   - **Proje**: Hangi projeye ait (opsiyonel)
   - **Firma Adı ve Fatura No**
4. **Fiş/Fatura yükleyin** (PDF veya görsel — zorunlu)
5. **Kaydet** butonuna tıklayın (taslak olarak kaydedilir)

#### AI ile Fiş Okuma

1. Masraf formunda **AI ile Formu Doldur** butonuna tıklayın
2. Fotoğrafını çektiğiniz fişi yükleyin
3. AI otomatik olarak şu bilgileri çıkaracaktır:
   - Firma adı
   - Tarih
   - Toplam tutar
   - Fatura numarası
   - Açıklama
4. Bilgileri kontrol edin ve gerekirse düzeltin
5. **Kaydet** ile masrafı tamamlayın

#### Masrafı Onaya Gönderme

1. Masraf listesinden taslak masrafı açın
2. **Onaya Gönder** butonuna tıklayın
3. Masraf durumu "Onay Bekliyor" olarak değişir
4. Yöneticiniz onay veya red verecektir
5. Reddedilirse düzeltip tekrar gönderebilirsiniz

#### Masraf Raporu Oluşturma

1. **Masraf Raporlarım** menüsüne gidin
2. **Yeni Rapor** butonuna tıklayın
3. Yıl ve ay seçin
4. Avans tutarı varsa girin
5. Sistem onaylanmış masrafları otomatik listeleyecektir
6. **Oluştur** butonuna tıklayın
7. Raporu **Onaya Gönder** ile yöneticiye iletin
8. Onaylandıktan sonra **Excel** butonu ile indirebilirsiniz

#### Onay Süreci (Yöneticiler İçin)

1. **Onaylar** menüsüne gidin
2. Bekleyen masraf onaylarını görüntüleyin
3. Masraf detayını inceleyin, fişi kontrol edin
4. **Onayla** veya **Reddet** (red nedeni zorunlu) butonuna tıklayın

---

### 4.4 Proje ve Müşteri Yönetimi

#### Müşteri Ekleme

1. **Proje Yönetimi > Müşteriler** menüsüne gidin
2. **Yeni Müşteri** butonuna tıklayın
3. Bilgileri girin: unvan, kısa ad, vergi no, adres, yetkili kişi bilgileri
4. **Kaydet** butonuna tıklayın

#### Proje Oluşturma

1. **Proje Yönetimi > Projeler** menüsüne gidin
2. **Yeni Proje** butonuna tıklayın
3. Bilgileri girin:
   - **Müşteri** seçin
   - **Proje Adı ve Kodu**
   - **Başlangıç/Bitiş Tarihi**
   - **Bütçe** (opsiyonel)
4. **Kaydet** butonuna tıklayın

#### Kadro (Hedef Pozisyon) Yönetimi

Kadro, bir projede kaç kişi hangi pozisyonda çalışacağını tanımlar.

1. Proje detay sayfasında **Kadro Ekle** butonuna tıklayın
2. Bilgileri girin:
   - **Pozisyon Adı** (örn: "SSE - İzmir", "Merchandiser - Ankara")
   - **İl ve İlçe**
   - **Hedef Sayı** (kaç kişi gerekli)
   - **Öncelik** (1 = en acil, 10 = düşük)
   - Gereksinimler: deneyim, eğitim, ehliyet, yaş aralığı
3. **Kaydet** butonuna tıklayın

#### Personel Atama

1. Proje detay sayfasında kadro satırını tıklayın
2. **Aday Ekle** ile mevcut adaylardan seçin veya yeni aday oluşturun
3. Aday işe alındığında çalışan kaydı oluşturulur ve kadroya atanır

---

### 4.5 Eğitim Yönetimi

#### Eğitim Dashboard

**İnsan Kaynakları > Eğitim > Dashboard** menüsünden eğitim özetine ulaşın:
- Yaklaşan eğitimler (7 gün)
- Devam eden eğitimler
- Bu ay tamamlanan
- Eksik zorunlu eğitimler

#### Yeni Eğitim Oluşturma

1. **Eğitim > Yeni Eğitim** menüsüne gidin
2. Bilgileri girin:
   - **Eğitim Tipi** seçin (Oryantasyon, İSG, Ürün Eğitimi vb.)
   - **Başlık ve Açıklama**
   - **Proje** (opsiyonel — projeye özel eğitim)
   - **Tarih ve Süre** (saat)
   - **Konum Tipi**: Yüz Yüze, Online, Hibrit
   - Online ise **Jitsi bağlantısı** otomatik oluşturulur
   - **Eğitmen**: İç eğitmen seçin veya dış eğitmen bilgisi girin
   - **Kontenjan ve Minimum Katılımcı**
3. **Kaydet** butonuna tıklayın

#### Katılımcı Ekleme

1. Eğitim detay sayfasını açın
2. **Katılımcı Ekle** butonuna tıklayın
3. Üç yöntemle ekleyebilirsiniz:
   - **Tek tek**: Çalışan seçerek
   - **Projeye göre**: Tüm proje çalışanlarını ekle
   - **Pozisyona göre**: Belirli pozisyondakileri ekle
4. Katılımcılar "Davetli" olarak eklenir

#### Katılım Takibi

1. Eğitim detay sayfasında katılımcı listesini görüntüleyin
2. Her katılımcının durumunu güncelleyin:
   - **Katıldı**: Eğitime katıldı
   - **Geçti**: Sınavı geçti (puan girebilirsiniz)
   - **Kaldı**: Sınavda başarısız
   - **Mazeret**: Katılamadı (neden girin)
3. Online eğitimlerde Jitsi katılım süresi otomatik kaydedilir

#### Zorunlu Eğitim Takibi

1. **Eğitim > Zorunlu Takip** menüsüne gidin
2. Eksik zorunlu eğitimleri olan çalışanları görüntüleyin
3. Süresi dolmak üzere olan sertifikaları takip edin
4. Toplu eğitim planlaması yapın

#### Test ve Sınav

1. **Eğitim > Soru Bankası** ile sorular oluşturun (çoktan seçmeli, doğru/yanlış)
2. **Eğitim > Testler > Yeni Test** ile sınav oluşturun
3. Süre limiti, geçme notu, soru karıştırma seçeneklerini ayarlayın
4. Çalışanlar testi çözdükten sonra sonuçlar otomatik hesaplanır

---

### 4.6 Satın Alma

#### Satın Alma Talebi Oluşturma

1. Sol menüden **Satın Alma** seçin
2. **Yeni Talep** butonuna tıklayın
3. Bilgileri girin:
   - **Başlık ve Açıklama**
   - **Gerekçe** (neden gerekiyor?)
   - **Kategori, Öncelik, Talep Edilen Tarih**
   - **Tahmini Bütçe**
   - **Proje** (opsiyonel)
4. **Kalem Ekle** ile satın alınacak ürünleri listeleyin:
   - Ürün adı, miktar, birim, birim fiyat
5. **Kaydet** ve **Onaya Gönder**

#### Satın Alma Süreci

```
Talep Oluştur → Onaya Gönder → Yönetici Onayı → Teklif Al → Teklif Seç → Sipariş → Teslimat
```

1. **Teklif Ekleme** (admin): Talep detayında tedarikçilerden gelen teklifleri girin
2. **Teklif Seçme**: En uygun teklifi seçin — otomatik olarak sipariş oluşur
3. **Teslimat Kaydı**: Ürünler geldiğinde teslimat bilgilerini girin
4. Sipariş durumu otomatik güncellenir

---

### 4.7 Raporlar ve AI Asistan

#### Rapor Dashboard

Sol menüden **Raporlar** seçerek tüm rapor kategorilerine ulaşın:

| Rapor | İçerik |
|-------|--------|
| **İK Raporları** | Çalışan dağılımı, işe alım trendi, departman analizi |
| **Masraf Raporları** | Kategori dağılımı, aylık trend, harcama analizi |
| **Sözleşme Raporları** | Aktif sözleşmeler, bitiş takibi, tip dağılımı |
| **Satın Alma Raporları** | Harcama trendi, kategori analizi |
| **Talep Raporları** | SLA analizi, kategori ve öncelik dağılımı |

Her rapor sayfasında **Excel'e Aktar** seçeneği mevcuttur.

#### AI Raporlama Asistanı

Sol menüden **AI Asistan** seçin veya Raporlar dashboard'undaki AI kartına tıklayın.

**Kullanımı:**
1. Soru kutusuna doğal Türkçe ile sorunuzu yazın
2. **Sor** butonuna tıklayın
3. AI sorunuzu analiz eder, uygun SQL sorgusunu oluşturur ve çalıştırır
4. Sonuçlar tablo formatında gösterilir
5. Tablonun sağ üstündeki **Excel** butonu ile sonuçları indirebilirsiniz

**Örnek sorular:**
- "Kaç aktif çalışan var?"
- "Proje bazlı personel dağılımı göster"
- "Bu ay ayrılanlar kimler?"
- "Departman bazlı personel sayıları"
- "Araç filosu durumu nedir?"
- "Son 3 ayda işe giren çalışanlar"
- "Hangi projede kadro açığı var?"
- "Bu yılki masraf toplamı ne kadar?"

> **Not:** AI Asistan sadece veri sorgulama yapar, hiçbir kayıt değiştirmez. Verileriniz güvende.

---

### 4.8 Onay Yönetimi

#### Bekleyen Onayları Görüntüleme

1. Sol menüden **Onaylar** seçin (turuncu rozet bekleyen sayısını gösterir)
2. Bekleyen onayları listede görüntüleyin
3. Acil olanlar kırmızı etiketle işaretlenir

#### Onay Verme / Reddetme

1. Onay detay sayfasını açın
2. İlgili belgeyi inceleyin (masraf fişi, izin talebi, satın alma vb.)
3. **Onayla** (opsiyonel not ekleyebilirsiniz) veya **Reddet** (red nedeni zorunlu)
4. Çok aşamalı onaylarda sonraki onaylayıcıya otomatik iletilir

#### Yetki Devri

Tatil veya izin dönemlerinde onay yetkinizi başka birine devredebilirsiniz:

1. **Onaylar > Yetki Devri** menüsüne gidin
2. **Yeni Devir** butonuna tıklayın
3. Devralan kişiyi, başlangıç/bitiş tarihlerini ve nedenini girin
4. **Kaydet** — Belirlenen tarihler arasında o kişi sizin adınıza onay verebilir

---

### 4.9 Diğer Modüller

#### Takvim

- Sol menüden **Takvim** ile etkinlikleri görüntüleyin
- Outlook ile otomatik senkronizasyon desteklenir (15 dakika aralıkla)

#### Mesajlar

- Sol menüden **Mesajlar** ile portal içi mesajlaşma yapın
- Özel mesaj gönderin, dosya ekleyin
- Okunmamış mesajlar kırmızı rozet ile gösterilir

#### Talepler (Destek)

- Sol menüden **Talepler** ile IT veya operasyonel destek talebi oluşturun
- Öncelik, kategori belirleyin
- Durumu takip edin: Açık → Atandı → Devam Ediyor → Çözüldü

#### Tedarikçiler

- **Tedarikçiler** menüsünden firma bilgilerini yönetin
- Tedarikçi tipleri: Servis, Yakıt, Sigorta, Yedek Parça, Kiralama, Genel
- İletişim kişileri, sözleşme bilgileri, performans değerlendirmesi ekleyin

---

## 5. Sıkça Sorulan Sorular (SSS)

### Genel

**S: Şifremi unuttum, ne yapmalıyım?**
C: İK ekibine veya sistem yöneticisine başvurun. Admin panelinden şifreniz sıfırlanacaktır.

**S: Menüde bazı bölümler görünmüyor, neden?**
C: Rolünüze atanmış yetkiler hangi menüleri görebileceğinizi belirler. Ek yetki gerekiyorsa yöneticinize başvurun.

**S: Bir sayfada "Yetkiniz yok" hatası alıyorum.**
C: O sayfaya erişim yetkiniz yoktur. Yöneticiniz veya admin size gerekli rolü atayabilir.

### Masraf

**S: Masraf girişinde fiş yüklemek zorunlu mu?**
C: Evet, "fatura zorunlu" olarak işaretlenmiş kategorilerde (Yemek, Ulaşım vb.) fiş veya fatura yüklemeden onaya gönderemezsiniz.

**S: Reddedilen masrafı tekrar göndermek mümkün mü?**
C: Evet. Reddedilen masraf otomatik olarak taslak durumuna döner. Düzeltip tekrar onaya gönderebilirsiniz.

**S: AI fiş okuma yanlış bilgi çıkardı, ne yapmalıyım?**
C: AI'ın çıkardığı bilgiler formu otomatik doldurur ancak kesin doğruluğu garanti etmez. Bilgileri kontrol edip gerekirse manuel düzeltin.

### Filo

**S: Araç teslimlerde fotoğraf yüklemek zorunlu mu?**
C: Teslim formunda fotoğraf yüklenmesi şiddetle tavsiye edilir. Kaza kayıtlarında en az 1 fotoğraf zorunludur.

**S: Yakıt kaydı girdiğimde kilometre neden otomatik değişiyor?**
C: Sistem, yakıt kaydındaki kilometreyi aracın güncel kilometresi olarak günceller. Doğru km girdiğinizden emin olun.

### İK

**S: Bir çalışanı silmek mümkün mü?**
C: Hayır. Çalışan kayıtları silinmez, durum "AYRILDI" olarak güncellenir. Bu yasal kayıt tutma zorunluluğu gereğidir.

**S: İşten çıkış sürecinde zimmetlerin iadesi nasıl takip edilir?**
C: İşten çıkış formunda "Zimmet Teslim" kontrol kutusu vardır. Tüm zimmetler iade edilmeden süreç tamamlanmaz.

### Proje

**S: Kadro doluluk oranı nasıl hesaplanıyor?**
C: Hedef sayıya karşı o kadroya atanmış aktif çalışan sayısı oranıdır. Örneğin: 5 hedef, 3 atanmış = %60 doluluk.

### AI Asistan

**S: AI Asistan veritabanında değişiklik yapabilir mi?**
C: Hayır. AI Asistan sadece SELECT (okuma) sorguları çalıştırır. Hiçbir veri ekleme, silme veya değiştirme işlemi yapamaz.

**S: AI Asistan yanlış sonuç verdi, ne yapmalıyım?**
C: Sorunuzu daha spesifik hale getirip tekrar sorun. Örneğin "çalışan sayısı" yerine "aktif çalışan sayısı" yazın. Sorun devam ederse IT ekibine bildirin.

---

## 6. İletişim ve Destek

| Konu | İletişim |
|------|----------|
| Şifre sıfırlama, yetki talebi | İK Ekibi |
| Teknik sorun, sistem hatası | IT / Sistem Yöneticisi |
| Modül kullanım soruları | Departman yöneticiniz |
| Portal içi destek talebi | Sol menü > Talepler > Yeni Talep |
