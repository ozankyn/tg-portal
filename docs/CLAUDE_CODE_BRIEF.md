# TG Portal - Claude Code Brief
# Bu dosyayı Claude Code'a yapıştır veya CLAUDE.md'ye ekle

## PROJE-KOORDİNATÖR EŞLEŞTİRMESİ

| Proje | Proje ID | Müşteri | Koordinatör | Excel Dept Adı |
|---|---|---|---|---|
| Blues | 3 | Efes | Yakup Ateş | Blues, Blues Spv |
| Sniper | 2 | Efes | Ufuk Dinç | (şu an aktif personel yok) |
| KK Merch | 1 | Efes | Kazım Sifoğlu | KK Merch |
| SSE | 6 | PMI | Erdi Aslantaş | Sse, Part Time Sse, Sse Spv |
| BF Merchandiser | 7 | Brown Forman (musteri_id=5) | Muhammet Aslan | Brown Forman |
| Beylerbeyi Merch | 4 | Beylerbeyi | Havvanur Mahmutoğlu | Beylerbeyi Merch, Beylerbeyi Merch Yaya |
| Adco Merchandiser | 5 | Kemer Gıda | Ufuk Dinç | Adco Merch |
| Marka Elçisi | YENİ | Efes | Halil Karaoğlan | Marka Elçisi |
| Modern Kanal Sniper | YENİ | Efes | Ufuk Dinç | Modern Kanal Part Time |
| Paylaşımlı Merch | YENİ | PMI + BF ortak pilot | Erdi Aslantaş | Paylaşımlı Merch (PMI-BF) |
| Efes Süpervizör | Sniper(2) | Efes | Hakan Alpan (direkt) | Efes Spv |

## ATLANACAK KAYITLAR
- Vena (4 kişi) → Kayıt oluşturma
- Triodor (4 kişi) → Kayıt oluşturma

## EXCEL KOLON EŞLEŞTİRME
Dosya: data/personel.xlsx (veya /mnt/user-data/uploads/PERSONEL_BI_LGI_LERI_.xlsx)

| Kolon | Excel Alanı | Calisan Alanı |
|---|---|---|
| B | Personel Kodu | sicil_no |
| C | TC Kimlik No | tc_kimlik |
| D | Adı Soyadı | ad + soyad (parse et) |
| E | Pozisyon | pozisyon_id (lookup/oluştur) |
| F | Departman | departman_id (lookup) |
| H | Bağlı olduğu yönetici | yonetici_id (koordinatör eşleştir) |
| I | Departman adı | → proje eşleştirme (yukarıdaki tablo) |
| J | İşyeri SGK Şubesi | (bilgi amaçlı) |
| K | İşyeri SGK No | (bilgi amaçlı) |
| L | Kıdem tarihi | kidem_tarihi |
| M | Giriş Tarihi | ise_baslama |
| N | Çıkış Tarihi | isten_ayrilma (varsa durum=AYRILDI) |
| P | Mobil Tel | telefon |
| Q | Doğum Tarihi | dogum_tarihi |
| R | Cinsiyet | cinsiyet |
| S | Tahsil | egitim_durumu |
| T | E-Posta | email (@teamguerilla.com normalize) |
| U | Yemek Kartı | yemek_karti |
| V | Beden | beden |
| W | Kargo Şubesi | kargo_subesi |
| X | Adres | adres |
| Y | Çıkış Sebebi | ayrilma_nedeni |

## ORGANİZASYON YAPISI

```
Fatih Kayan (Ajans Başkanı) [Yönetim dept]
├── Ozan Eren Kayan (Direktör) [Retail dept]
│   ├── Hakan Alpan (Genel Koordinatör) [Retail]
│   │   ├── Yakup Ateş (Saha Kor.) → Blues projesi
│   │   ├── Ufuk Dinç (Saha Kor.) → Sniper + Adco Merch + Modern Kanal
│   │   ├── Kazım Sifoğlu (Saha Kor.) → KK Merch
│   │   ├── Furkan Bıçakçı (Depo Sorumlusu) → Kiralık araçlar
│   │   └── Efes Spv ekibi (10 kişi) → direkt Hakan'a bağlı
│   ├── Erdi Aslantaş (Proje Kor.) → SSE + Paylaşımlı Merch
│   ├── Havvanur Mahmutoğlu (Proje Kor.) → Beylerbeyi
│   ├── Muhammet Aslan (Saha Kor.) → BF Merch
│   ├── Burcu Han (Bütçe Uzmanı)
│   ├── Burak Durgun (Filo Yöneticisi) [Filo dept]
│   ├── Abdurrahman Güleç (Raporlama TL) [Raporlama dept]
│   │   ├── Mustafa Can Gök
│   │   └── Erkan Toraman
│   └── Oğuzhan Gümüş (Eğitim TL) [Eğitim dept]
│       └── Ozan Mert
├── Ebru Meriç (Event Müdürü) [Event dept]
│   ├── Halil Karaoğlan (Proje Kor.) → Marka Elçisi
│   ├── Ahmet Erdem Müjdeci (Proje Asistanı)
│   ├── Mete Gencer (Lojistik)
│   └── Bora Gelişken (Sanat Yönetmeni)
├── Ayşe Tilki (Muhasebe Müdürü) [Muhasebe dept]
│   ├── Merve Bay Payman
│   ├── Nurdan Şerav Uçar
│   ├── Gizem Gülpınar Kaya
│   └── Fati Yıldırım
└── Seren Kadız (İK TL) [İK dept]
    ├── Nezihe Özer
    └── Öznur Çiftçi
```

## DB TEMİZLİK GÖREVLERİ
1. Brown Forman müşteri duplicate: musteri_id=6 sil (id=5 kalacak, projesi var)
2. Duplicate departmanlar: dept_id 1-8 ve 9-16 boş, 17-24 aktif → eski setleri sil
3. CalisanDurumu enum: DB'de büyük harf → ADAY, AKTIF, IZINLI, ASKIYA_ALINDI, AYRILDI

## MEVCUT SİSTEM BİLGİLERİ
- 276 mevcut çalışan kaydı (saha ekibi, önceden import edilmiş)
- 30 ofis çalışanı bugün oluşturuldu (id 278-306)
- 15 rol, 31 user oluşturuldu (scripts/rol_kurulum.py)
- HedefKadro.pozisyon_adi alanı kullanılıyor (ad değil!)
- Docker komutu: docker compose -f docker-compose.prod.yml exec web bash -c "cd /app && PYTHONPATH=/app python3 script.py"

## YAPILACAKLAR (ÖNCELİK SIRASI)
1. DB temizlik (duplicate dept, müşteri)
2. Yeni projeler oluştur (Marka Elçisi, Modern Kanal Sniper, Paylaşımlı Merch)
3. Excel'den tüm saha çalışanlarını güncelle (proje/kadro/koordinatör ata)
4. Çıkış yapanları AYRILDI durumuna çek
5. User ↔ Calisan bağlantılarını tamamla
6. İşe giriş/çıkış bildirim mail akışını kontrol et
7. Zorunlu evrak türlerini güncelle
8. Ofis kullanıcıları için rol bazlı eğitim içerikleri
