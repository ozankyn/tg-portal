# ============================================================
# app/models/ik.py içindeki Aday modeline EKLENECEK ALANLAR
# ============================================================

# Mevcut alanlara ek olarak şunları ekle:

    # Davet ve Doğrulama
    davet_token = db.Column(db.String(64), unique=True, index=True)  # Benzersiz başvuru linki
    davet_token_expires = db.Column(db.DateTime)  # Token geçerlilik süresi
    davet_gonderim_tarihi = db.Column(db.DateTime)  # SMS/Email gönderim zamanı
    davet_tipi = db.Column(db.String(10))  # 'sms' veya 'email'
    
    # KVKK Onay
    kvkk_onay = db.Column(db.Boolean, default=False)
    kvkk_onay_tarihi = db.Column(db.DateTime)
    kvkk_onay_ip = db.Column(db.String(45))  # IPv6 için 45 karakter
    aydinlatma_metni_versiyonu = db.Column(db.String(10))  # Hangi versiyon onaylandı
    
    # Başvuru Durumu
    basvuru_tamamlandi = db.Column(db.Boolean, default=False)
    basvuru_tarihi = db.Column(db.DateTime)  # Form gönderim tarihi
    
    # Ek Bilgiler (aday tarafından doldurulacak)
    tc_kimlik = db.Column(db.String(11))
    dogum_tarihi = db.Column(db.Date)
    dogum_yeri = db.Column(db.String(100))
    cinsiyet = db.Column(db.String(10))  # erkek, kadin
    adres = db.Column(db.Text)
    il = db.Column(db.String(50))
    ilce = db.Column(db.String(50))
    
    # Eğitim
    egitim_durumu = db.Column(db.String(50))  # ilkokul, ortaokul, lise, onlisans, lisans, yukseklisans, doktora
    okul_adi = db.Column(db.String(200))
    bolum = db.Column(db.String(200))
    mezuniyet_yili = db.Column(db.Integer)
    
    # Ehliyet
    ehliyet_var = db.Column(db.Boolean, default=False)
    ehliyet_sinifi = db.Column(db.String(10))  # A, A2, B, C, D, E
    ehliyet_tarihi = db.Column(db.Date)
    src_belgesi = db.Column(db.Boolean, default=False)
    psikoteknik = db.Column(db.Boolean, default=False)
    
    # İş Deneyimi
    toplam_tecrube_yil = db.Column(db.Integer, default=0)
    son_is_yeri = db.Column(db.String(200))
    son_pozisyon = db.Column(db.String(100))
    son_is_baslangic = db.Column(db.Date)
    son_is_bitis = db.Column(db.Date)
    son_is_ayrilma_nedeni = db.Column(db.Text)
    
    # Referans
    referans_ad = db.Column(db.String(100))
    referans_telefon = db.Column(db.String(20))
    referans_iliski = db.Column(db.String(50))  # eski yönetici, iş arkadaşı, vb.
    
    # Dosyalar
    cv_dosya = db.Column(db.String(255))  # Dosya yolu
    kimlik_foto = db.Column(db.String(255))
    ehliyet_foto = db.Column(db.String(255))
    diploma_foto = db.Column(db.String(255))
    
    # Ek Notlar
    saglik_durumu = db.Column(db.Text)
    askerlik_durumu = db.Column(db.String(50))  # yapti, muaf, tecilli
    calisabilecegi_il = db.Column(db.String(100))
    beklenen_maas = db.Column(db.Numeric(10, 2))
    ne_zaman_baslayabilir = db.Column(db.String(50))


# ============================================================
# Yeni property'ler
# ============================================================

    @property
    def is_token_valid(self):
        """Token hala geçerli mi?"""
        if not self.davet_token or not self.davet_token_expires:
            return False
        return datetime.utcnow() < self.davet_token_expires
    
    @property
    def basvuru_durumu_text(self):
        """Başvuru durumunu text olarak döndür"""
        if not self.davet_token:
            return "Manuel Eklendi"
        if not self.kvkk_onay:
            return "KVKK Bekliyor"
        if not self.basvuru_tamamlandi:
            return "Form Bekliyor"
        return "Tamamlandı"
