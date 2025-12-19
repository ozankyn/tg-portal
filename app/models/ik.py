# -*- coding: utf-8 -*-
"""
TG Portal - İK (Human Resources) Models
Güncelleme: davet_eden_id ve kaynak zenginleştirmesi eklendi
"""

from datetime import datetime, date, timedelta
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin, AuditMixin, CalisanDurumu


class Departman(db.Model, TimestampMixin, SoftDeleteMixin):
    """Departman modeli"""
    __tablename__ = 'departmanlar'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    kod = db.Column(db.String(20))
    aciklama = db.Column(db.Text)
    ust_departman_id = db.Column(db.Integer, db.ForeignKey('departmanlar.id'))
    yonetici_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))
    aktif = db.Column(db.Boolean, default=True)
    
    # İlişkiler
    alt_departmanlar = db.relationship('Departman', backref=db.backref('ust_departman', remote_side=[id]))
    pozisyonlar = db.relationship('Pozisyon', backref='departman', lazy='dynamic')
    
    def __repr__(self):
        return f'<Departman {self.ad}>'
    
    @property
    def calisan_sayisi(self):
        return Calisan.query.filter_by(departman_id=self.id, is_deleted=False).count()


class Pozisyon(db.Model, TimestampMixin, SoftDeleteMixin):
    """Pozisyon modeli"""
    __tablename__ = 'pozisyonlar'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    kod = db.Column(db.String(20))
    departman_id = db.Column(db.Integer, db.ForeignKey('departmanlar.id'))
    seviye = db.Column(db.Integer)  # Organizasyon seviyesi
    aciklama = db.Column(db.Text)
    aktif = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Pozisyon {self.ad}>'


class Calisan(db.Model, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Çalışan modeli"""
    __tablename__ = 'calisanlar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Kişisel Bilgiler
    sicil_no = db.Column(db.String(20), unique=True)
    ad = db.Column(db.String(50), nullable=False)
    soyad = db.Column(db.String(50), nullable=False)
    tc_kimlik = db.Column(db.String(11), unique=True)
    dogum_tarihi = db.Column(db.Date)
    dogum_yeri = db.Column(db.String(50))
    cinsiyet = db.Column(db.String(10))  # erkek, kadin
    medeni_durum = db.Column(db.String(20))  # bekar, evli, bosanmis
    
    # İletişim
    email = db.Column(db.String(120))
    telefon = db.Column(db.String(20))
    adres = db.Column(db.Text)
    il = db.Column(db.String(50))
    ilce = db.Column(db.String(50))
    
    # Acil Durum
    acil_kisi_ad = db.Column(db.String(100))
    acil_kisi_telefon = db.Column(db.String(20))
    acil_kisi_yakinlik = db.Column(db.String(50))
    
    # İş Bilgileri
    departman_id = db.Column(db.Integer, db.ForeignKey('departmanlar.id'))
    pozisyon_id = db.Column(db.Integer, db.ForeignKey('pozisyonlar.id'))
    yonetici_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))
    kadro_id = db.Column(db.Integer, db.ForeignKey('hedef_kadrolar.id'))
    
    ise_baslama = db.Column(db.Date)
    isten_ayrilma = db.Column(db.Date)
    ayrilma_nedeni = db.Column(db.Text)
    calisma_tipi = db.Column(db.String(20))  # tam_zamanli, yari_zamanli, stajyer, sozlesmeli
    
    # Durum
    durum = db.Column(db.Enum(CalisanDurumu), default=CalisanDurumu.AKTIF)
    notlar = db.Column(db.Text)
    
    # Fotoğraf
    foto = db.Column(db.String(500))
    
    # İlişkiler
    departman = db.relationship('Departman', foreign_keys=[departman_id], backref='calisanlar')
    pozisyon = db.relationship('Pozisyon', backref='calisanlar')
    yonetici = db.relationship('Calisan', remote_side=[id], backref='astlar')
    izinler = db.relationship('Izin', backref='calisan', lazy='dynamic')
    
    def __repr__(self):
        return f'<Calisan {self.full_name}>'
    
    @property
    def full_name(self):
        return f'{self.ad} {self.soyad}'
    
    @property
    def kidem_yili(self):
        if not self.ise_baslama:
            return 0
        end_date = self.isten_ayrilma or date.today()
        return (end_date - self.ise_baslama).days // 365
    
    def to_dict(self):
        return {
            'id': self.id,
            'sicil_no': self.sicil_no,
            'ad': self.ad,
            'soyad': self.soyad,
            'full_name': self.full_name,
            'email': self.email,
            'telefon': self.telefon,
            'departman': self.departman.ad if self.departman else None,
            'pozisyon': self.pozisyon.ad if self.pozisyon else None,
            'durum': self.durum.value if self.durum else None
        }


# Kaynak türleri - zenginleştirilmiş
KAYNAK_TURLERI = [
    ('sms_davet', 'SMS ile Davet'),
    ('email_davet', 'E-posta ile Davet'),
    ('acik_basvuru', 'Açık Başvuru (Kariyer Sayfası)'),
    ('kariyer_net', 'Kariyer.net'),
    ('linkedin', 'LinkedIn'),
    ('indeed', 'Indeed'),
    ('referans', 'Çalışan Referansı'),
    ('is_kurumu', 'İŞKUR'),
    ('sosyal_medya', 'Sosyal Medya'),
    ('ilan', 'İlan (Gazete vb.)'),
    ('diger', 'Diğer'),
]


class Aday(db.Model, TimestampMixin, SoftDeleteMixin):
    """İş başvuru adayları - KVKK Uyumlu"""
    __tablename__ = 'adaylar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # ==================== Temel Bilgiler ====================
    ad = db.Column(db.String(50), nullable=False)
    soyad = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    telefon = db.Column(db.String(20))
    
    # ==================== Başvuru Bilgileri ====================
    pozisyon_id = db.Column(db.Integer, db.ForeignKey('pozisyonlar.id'))
    kadro_id = db.Column(db.Integer, db.ForeignKey('hedef_kadrolar.id'))
    kaynak = db.Column(db.String(50))  # KAYNAK_TURLERI'nden biri
    
    # ==================== Davet Eden Takibi (YENİ) ====================
    davet_eden_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Kim daveti gönderdi
    davet_eden = db.relationship('User', backref='davet_ettigi_adaylar', foreign_keys=[davet_eden_id])
    
    # ==================== Davet ve Doğrulama ====================
    davet_token = db.Column(db.String(64), unique=True, index=True)  # Benzersiz başvuru linki
    davet_token_expires = db.Column(db.DateTime)  # Token geçerlilik süresi (72 saat)
    davet_gonderim_tarihi = db.Column(db.DateTime)  # SMS/Email gönderim zamanı
    davet_tipi = db.Column(db.String(10))  # 'sms' veya 'email'

    # ==================== Telefon Doğrulama (OTP) ====================
    telefon_dogrulandi = db.Column(db.Boolean, default=False)
    telefon_dogrulama_kodu = db.Column(db.String(6))
    telefon_dogrulama_kodu_expires = db.Column(db.DateTime)
    telefon_dogrulama_tarihi = db.Column(db.DateTime)
    telefon_dogrulama_ip = db.Column(db.String(45))
    telefon_dogrulama_deneme = db.Column(db.Integer, default=0)
    
    # ==================== KVKK Onay ====================
    kvkk_onay = db.Column(db.Boolean, default=False)
    kvkk_onay_tarihi = db.Column(db.DateTime)
    kvkk_onay_ip = db.Column(db.String(45))  # IPv6 için 45 karakter
    aydinlatma_metni_versiyonu = db.Column(db.String(10), default='1.0')  # Hangi versiyon onaylandı

    # ==================== Telefon Doğrulama (OTP) ====================
    telefon_dogrulandi = db.Column(db.Boolean, default=False)
    telefon_dogrulama_kodu = db.Column(db.String(6))  # 6 haneli kod
    telefon_dogrulama_kodu_expires = db.Column(db.DateTime)  # Kod geçerlilik süresi (5 dk)
    telefon_dogrulama_tarihi = db.Column(db.DateTime)
    telefon_dogrulama_ip = db.Column(db.String(45))
    telefon_dogrulama_deneme = db.Column(db.Integer, default=0)  # Yanlış deneme sayısı (max 3)
    
    # ==================== Başvuru Durumu ====================
    basvuru_tamamlandi = db.Column(db.Boolean, default=False)
    basvuru_tarihi = db.Column(db.DateTime)  # Form gönderim tarihi
    durum = db.Column(db.String(30), default='davet_gonderildi')
    # davet_gonderildi, kvkk_bekleniyor, form_bekleniyor, basvurdu, 
    # degerlendiriliyor, mulakat, teklif, ise_alindi, red, iptal
    
    # ==================== Kişisel Bilgiler (Aday Doldurur) ====================
    tc_kimlik = db.Column(db.String(11))
    dogum_tarihi = db.Column(db.Date)
    dogum_yeri = db.Column(db.String(100))
    cinsiyet = db.Column(db.String(10))  # erkek, kadin
    medeni_durum = db.Column(db.String(20))  # bekar, evli, bosanmis
    adres = db.Column(db.Text)
    il = db.Column(db.String(50))
    ilce = db.Column(db.String(50))
    
    # ==================== Eğitim ====================
    egitim_durumu = db.Column(db.String(50))  # ilkokul, ortaokul, lise, onlisans, lisans, yukseklisans, doktora
    okul_adi = db.Column(db.String(200))
    bolum = db.Column(db.String(200))
    mezuniyet_yili = db.Column(db.Integer)
    
    # ==================== Ehliyet ====================
    ehliyet_var = db.Column(db.Boolean, default=False)
    ehliyet_sinifi = db.Column(db.String(10))  # A, A2, B, C, D, E
    ehliyet_tarihi = db.Column(db.Date)
    src_belgesi = db.Column(db.Boolean, default=False)
    psikoteknik = db.Column(db.Boolean, default=False)
    
    # ==================== İş Deneyimi ====================
    toplam_tecrube_yil = db.Column(db.Integer, default=0)
    son_is_yeri = db.Column(db.String(200))
    son_pozisyon = db.Column(db.String(100))
    son_is_baslangic = db.Column(db.Date)
    son_is_bitis = db.Column(db.Date)
    son_is_ayrilma_nedeni = db.Column(db.Text)
    
    # ==================== Referans ====================
    referans_ad = db.Column(db.String(100))
    referans_telefon = db.Column(db.String(20))
    referans_iliski = db.Column(db.String(50))  # eski_yonetici, is_arkadasi, aile, diger
    
    # ==================== Dosyalar ====================
    cv_dosya = db.Column(db.String(255))  # Dosya yolu
    foto = db.Column(db.String(255))
    kimlik_on = db.Column(db.String(255))
    kimlik_arka = db.Column(db.String(255))
    ehliyet_foto = db.Column(db.String(255))
    diploma_foto = db.Column(db.String(255))
    src_foto = db.Column(db.String(255))
    ikametgah = db.Column(db.String(255))
    adli_sicil = db.Column(db.String(255))
    
    # ==================== Ek Bilgiler ====================
    saglik_sorunu = db.Column(db.Boolean, default=False)
    saglik_sorunu_aciklama = db.Column(db.Text)
    askerlik_durumu = db.Column(db.String(50))  # yapti, muaf, tecilli, yapmiyor
    askerlik_tecil_tarihi = db.Column(db.Date)
    sabika_kaydi = db.Column(db.Boolean, default=False)
    sabika_aciklama = db.Column(db.Text)
    
    # ==================== Tercihler ====================
    calisabilecegi_iller = db.Column(db.String(500))  # Virgülle ayrılmış il listesi
    beklenen_maas = db.Column(db.Numeric(10, 2))
    ne_zaman_baslayabilir = db.Column(db.String(50))  # hemen, 1_hafta, 2_hafta, 1_ay
    vardiyali_calisabilir = db.Column(db.Boolean, default=True)
    seyahat_engeli = db.Column(db.Boolean, default=False)
    
    # ==================== Değerlendirme (İK Doldurur) ====================
    degerlendirme_puani = db.Column(db.Integer)  # 1-10
    degerlendirme_notu = db.Column(db.Text)
    mulakat_tarihi = db.Column(db.DateTime)
    mulakat_notu = db.Column(db.Text)
    teklif_maas = db.Column(db.Numeric(10, 2))
    red_nedeni = db.Column(db.Text)
    
    notlar = db.Column(db.Text)  # İK notları
    
    # ==================== İlişkiler ====================
    pozisyon = db.relationship('Pozisyon', backref='adaylar')
    
    def __repr__(self):
        return f'<Aday {self.full_name}>'
    
    @property
    def full_name(self):
        return f'{self.ad} {self.soyad}'
    
    @property
    def is_token_valid(self):
        """Token hala geçerli mi?"""
        if not self.davet_token or not self.davet_token_expires:
            return False
        return datetime.utcnow() < self.davet_token_expires
    
    @property
    def basvuru_durumu_text(self):
        """Başvuru durumunu okunabilir text olarak döndür"""
        durum_map = {
            'davet_gonderildi': 'Davet Gönderildi',
            'kvkk_bekleniyor': 'KVKK Onayı Bekleniyor',
            'form_bekleniyor': 'Form Bekleniyor',
            'basvurdu': 'Başvuru Yapıldı',
            'degerlendiriliyor': 'Değerlendiriliyor',
            'mulakat': 'Mülakat Aşamasında',
            'teklif': 'Teklif Yapıldı',
            'ise_alindi': 'İşe Alındı',
            'red': 'Reddedildi',
            'iptal': 'İptal Edildi'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        """Durum için badge rengi"""
        renk_map = {
            'davet_gonderildi': 'info',
            'kvkk_bekleniyor': 'warning',
            'form_bekleniyor': 'warning',
            'basvurdu': 'primary',
            'degerlendiriliyor': 'primary',
            'mulakat': 'info',
            'teklif': 'success',
            'ise_alindi': 'success',
            'red': 'danger',
            'iptal': 'secondary'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def kaynak_text(self):
        """Kaynak türünü okunabilir text olarak döndür"""
        kaynak_map = dict(KAYNAK_TURLERI)
        return kaynak_map.get(self.kaynak, self.kaynak or '-')
    
    @property
    def yas(self):
        """Yaş hesapla"""
        if not self.dogum_tarihi:
            return None
        today = date.today()
        return today.year - self.dogum_tarihi.year - ((today.month, today.day) < (self.dogum_tarihi.month, self.dogum_tarihi.day))
    
    def generate_token(self):
        """Benzersiz davet token'ı oluştur"""
        import secrets
        self.davet_token = secrets.token_urlsafe(32)
        self.davet_token_expires = datetime.utcnow() + timedelta(hours=72)
        return self.davet_token
    
    def generate_otp(self):
        '''6 haneli doğrulama kodu oluştur'''
        import random
        from datetime import datetime, timedelta
        
        self.telefon_dogrulama_kodu = str(random.randint(100000, 999999))
        self.telefon_dogrulama_kodu_expires = datetime.utcnow() + timedelta(minutes=5)
        self.telefon_dogrulama_deneme = 0
        return self.telefon_dogrulama_kodu
    
    @property
    def is_otp_valid(self):
        '''OTP hala geçerli mi?'''
        if not self.telefon_dogrulama_kodu or not self.telefon_dogrulama_kodu_expires:
            return False
        return datetime.utcnow() < self.telefon_dogrulama_kodu_expires
    
    def verify_otp(self, kod):
        '''OTP doğrula'''
        from datetime import datetime
        
        if not self.is_otp_valid:
            return False, 'Doğrulama kodunun süresi dolmuş'
        
        if self.telefon_dogrulama_deneme >= 3:
            return False, 'Çok fazla yanlış deneme. Lütfen yeni kod isteyin.'
        
        if self.telefon_dogrulama_kodu != kod:
            self.telefon_dogrulama_deneme += 1
            return False, f'Yanlış kod. {3 - self.telefon_dogrulama_deneme} deneme hakkınız kaldı.'
        
        # Başarılı
        self.telefon_dogrulandi = True
        self.telefon_dogrulama_tarihi = datetime.utcnow()
        self.telefon_dogrulama_kodu = None  # Kodu temizle
        return True, 'Telefon doğrulandı'
    
    def to_dict(self):
        """API için dict döndür"""
        return {
            'id': self.id,
            'ad': self.ad,
            'soyad': self.soyad,
            'full_name': self.full_name,
            'email': self.email,
            'telefon': self.telefon,
            'durum': self.durum,
            'durum_text': self.basvuru_durumu_text,
            'kaynak': self.kaynak,
            'kaynak_text': self.kaynak_text,
            'kvkk_onay': self.kvkk_onay,
            'basvuru_tamamlandi': self.basvuru_tamamlandi,
            'davet_eden': self.davet_eden.full_name if self.davet_eden else None
        }
    
    def generate_otp(self):
        """6 haneli doğrulama kodu oluştur"""
        import random
        from datetime import datetime, timedelta
        
        self.telefon_dogrulama_kodu = str(random.randint(100000, 999999))
        self.telefon_dogrulama_kodu_expires = datetime.utcnow() + timedelta(minutes=5)
        self.telefon_dogrulama_deneme = 0
        return self.telefon_dogrulama_kodu
    
    @property
    def is_otp_valid(self):
        """OTP hala geçerli mi?"""
        if not self.telefon_dogrulama_kodu or not self.telefon_dogrulama_kodu_expires:
            return False
        from datetime import datetime
        return datetime.utcnow() < self.telefon_dogrulama_kodu_expires
    
    def verify_otp(self, kod):
        """OTP doğrula"""
        from datetime import datetime
        
        if not self.is_otp_valid:
            return False, 'Doğrulama kodunun süresi dolmuş'
        
        if self.telefon_dogrulama_deneme >= 3:
            return False, 'Çok fazla yanlış deneme. Lütfen yeni kod isteyin.'
        
        if self.telefon_dogrulama_kodu != kod:
            self.telefon_dogrulama_deneme += 1
            return False, f'Yanlış kod. {3 - self.telefon_dogrulama_deneme} deneme hakkınız kaldı.'
        
        self.telefon_dogrulandi = True
        self.telefon_dogrulama_tarihi = datetime.utcnow()
        self.telefon_dogrulama_kodu = None
        return True, 'Telefon doğrulandı'


class Izin(db.Model, TimestampMixin):
    """İzin talepleri"""
    __tablename__ = 'izinler'
    
    id = db.Column(db.Integer, primary_key=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    
    izin_tipi = db.Column(db.String(30))  # yillik, mazeret, hastalik, ucretsiz, dogum
    baslangic = db.Column(db.Date, nullable=False)
    bitis = db.Column(db.Date, nullable=False)
    gun_sayisi = db.Column(db.Integer)
    
    aciklama = db.Column(db.Text)
    
    # Onay
    durum = db.Column(db.String(20), default='beklemede')  # beklemede, onaylandi, reddedildi
    onaylayan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    onay_tarihi = db.Column(db.DateTime)
    red_nedeni = db.Column(db.Text)
    
    onaylayan = db.relationship('User', backref='onaylanan_izinler')
    
    def __repr__(self):
        return f'<Izin {self.calisan_id} {self.izin_tipi}>'
