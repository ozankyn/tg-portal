# -*- coding: utf-8 -*-
"""
TG Portal - İK (Human Resources) Models
Güncelleme: davet_eden_id ve kaynak zenginleştirmesi eklendi
"""

from datetime import datetime, date, timedelta
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin, AuditMixin, CalisanDurumu, ListeDurumu


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

    # Banka
    iban = db.Column(db.String(30))  # TR + 24 hane (otomatik okuma veya manuel)
    
    # Acil Durum
    acil_kisi_ad = db.Column(db.String(100))
    acil_kisi_telefon = db.Column(db.String(20))
    acil_kisi_yakinlik = db.Column(db.String(50))
    
    # İş Bilgileri
    departman_id = db.Column(db.Integer, db.ForeignKey('departmanlar.id'))
    pozisyon_id = db.Column(db.Integer, db.ForeignKey('pozisyonlar.id'))
    yonetici_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))
    kadro_id = db.Column(db.Integer, db.ForeignKey('hedef_kadrolar.id'))
    sgk_dosya_id = db.Column(db.Integer, db.ForeignKey('sgk_dosyalari.id'))
    
    # Ek Bilgiler
    kidem_tarihi = db.Column(db.Date)  # Kıdem başlangıç tarihi
    egitim_durumu = db.Column(db.String(50))  # ilkokul, ortaokul, lise, onlisans, lisans, yukseklisans, doktora
    is_grubu = db.Column(db.String(100))  # İş grup adı
    yemek_karti = db.Column(db.String(50))  # Yemek kartı numarası
    beden = db.Column(db.String(10))  # Kıyafet bedeni (S, M, L, XL, XXL)
    kargo_subesi = db.Column(db.String(500))  # Kargo şubesi
    ehliyet_sinifi = db.Column(db.String(10))  # B, A1, A2, C, D, E, BE, CE — boş = ehliyet yok

    ise_baslama = db.Column(db.Date)
    isten_ayrilma = db.Column(db.Date)
    ayrilma_nedeni = db.Column(db.Text)
    calisma_tipi = db.Column(db.String(20))  # tam_zamanli, yari_zamanli, stajyer, sozlesmeli
    
    # Durum
    durum = db.Column(db.Enum(CalisanDurumu), default=CalisanDurumu.AKTIF)
    notlar = db.Column(db.Text)

    # Kara/Gri Liste
    liste_durumu = db.Column(db.Enum(ListeDurumu), default=ListeDurumu.TEMIZ, nullable=False)
    liste_nedeni = db.Column(db.Text)
    liste_tarihi = db.Column(db.DateTime)
    listeye_alan_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Fotoğraf
    foto = db.Column(db.String(500))

    # Sözleşme Bilgileri
    sozlesme_sablon_id = db.Column(db.Integer, db.ForeignKey('sozlesme_sablonlari.id'))
    sozlesme_baslangic = db.Column(db.Date)
    sozlesme_bitis = db.Column(db.Date)
    sozlesme_pdf = db.Column(db.String(500))  # Sözleşme dosya yolu (oluşturulan .docx veya yüklenen imzalı PDF)

    # SGK Çıkış Bildirgesi (işten ayrılış sonrası bordronun yüklediği belge; UPLOAD_FOLDER'a göre relatif yol)
    sgk_cikis_bildirgesi = db.Column(db.String(500))

    # İlişkiler
    departman = db.relationship('Departman', foreign_keys=[departman_id], backref='calisanlar')
    pozisyon = db.relationship('Pozisyon', backref='calisanlar')
    yonetici = db.relationship('Calisan', remote_side=[id], backref='astlar')
    sozlesme_sablon = db.relationship('SozlesmeSablonu', backref=db.backref('calisanlar', lazy='dynamic'))
    izinler = db.relationship('Izin', backref='calisan', lazy='dynamic')
    listeye_alan = db.relationship('User', foreign_keys=[listeye_alan_id])

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

    @property
    def tekrar_ise_alinabilir(self):
        """Ayrılmış/askıya alınmış çalışan tekrar işe alınabilir."""
        return self.durum in (CalisanDurumu.AYRILDI, CalisanDurumu.ASKIYA_ALINDI)

    @property
    def sgk_giris_bekliyor(self):
        """Tekrar işe alım başlatıldı, SGK girişi bekleniyor (ara durum)."""
        return self.durum == CalisanDurumu.SGK_BEKLIYOR

    @property
    def sozlesme_kalan_gun(self):
        if not self.sozlesme_bitis:
            return None
        return (self.sozlesme_bitis - date.today()).days
    
    def to_dict(self):
        return {
            'id': self.id,
            'sicil_no': self.sicil_no,
            'ad': self.ad,
            'soyad': self.soyad,
            'full_name': self.full_name,
            'email': self.email,
            'telefon': self.telefon,
            'iban': self.iban,
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


# Aday işe alım süreci akışı (sıralı aşamalar). Reddedildi her aşamadan olabilir.
ADAY_DURUM_AKISI = [
    ('basvurdu', 'Başvurdu'),
    ('inceleniyor', 'İnceleniyor'),
    ('onaylandi', 'Onaylandı'),
    ('sgk_giris_talebi', 'SGK Giriş Talebi'),
    ('sgk_girisi_yapildi', 'SGK Girişi Yapıldı'),
    ('calisana_donusturuldu', 'Çalışana Dönüştürüldü'),
]


# Başvuru kaynağı - "Bize nereden ulaştınız?" (aday'ın kendisi seçer)
BASVURU_KAYNAK_TURLERI = [
    ('linkedin', 'LinkedIn'),
    ('instagram', 'Instagram'),
    ('kariyer_net', 'Kariyer.net'),
    ('referans', 'Referans'),
    ('is_ilani', 'İş İlanı'),
    ('arkadas_tavsiyesi', 'Arkadaş Tavsiyesi'),
    ('diger', 'Diğer'),
]

# Beden seçenekleri (üst/alt giyim)
BEDEN_SECENEKLERI = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL']

# Ehliyet sınıfları — boş değer "ehliyet yok" demektir
EHLIYET_SINIFLARI = ['A1', 'A2', 'A', 'B', 'BE', 'C', 'CE', 'D', 'E']


class Aday(db.Model, TimestampMixin, SoftDeleteMixin):
    """İş başvuru adayları - KVKK Uyumlu"""
    __tablename__ = 'adaylar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # ==================== Temel Bilgiler ====================
    ad = db.Column(db.String(50), nullable=False)
    soyad = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    telefon = db.Column(db.String(20), index=True)  # mükerrer başvuru taraması
    
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
    telefon_dogrulama_ip = db.Column(db.String(200))  # IPv6 + Cloudflare proxy zinciri için geniş tutuldu
    telefon_dogrulama_deneme = db.Column(db.Integer, default=0)
    
    # ==================== KVKK Onay ====================
    kvkk_onay = db.Column(db.Boolean, default=False)
    kvkk_onay_tarihi = db.Column(db.DateTime)
    kvkk_onay_ip = db.Column(db.String(200))  # IPv6 + Cloudflare proxy zinciri için geniş tutuldu
    aydinlatma_metni_versiyonu = db.Column(db.String(10), default='1.0')  # Hangi versiyon onaylandı

    # ==================== Telefon Doğrulama (OTP) ====================
    telefon_dogrulandi = db.Column(db.Boolean, default=False)
    telefon_dogrulama_kodu = db.Column(db.String(6))  # 6 haneli kod
    telefon_dogrulama_kodu_expires = db.Column(db.DateTime)  # Kod geçerlilik süresi (5 dk)
    telefon_dogrulama_tarihi = db.Column(db.DateTime)
    telefon_dogrulama_ip = db.Column(db.String(200))  # IPv6 + Cloudflare proxy zinciri için geniş tutuldu
    telefon_dogrulama_deneme = db.Column(db.Integer, default=0)  # Yanlış deneme sayısı (max 3)
    
    # ==================== Başvuru Durumu ====================
    basvuru_tamamlandi = db.Column(db.Boolean, default=False)
    basvuru_tarihi = db.Column(db.DateTime)  # Form gönderim tarihi
    durum = db.Column(db.String(30), default='davet_gonderildi')
    # davet_gonderildi, kvkk_bekleniyor, form_bekleniyor, basvurdu, 
    # degerlendiriliyor, mulakat, teklif, ise_alindi, red, iptal
    
    # ==================== Kişisel Bilgiler (Aday Doldurur) ====================
    tc_kimlik = db.Column(db.String(11), index=True)  # mükerrer başvuru taraması
    dogum_tarihi = db.Column(db.Date)
    dogum_yeri = db.Column(db.String(100))
    cinsiyet = db.Column(db.String(10))  # erkek, kadin
    medeni_durum = db.Column(db.String(20))  # bekar, evli, bosanmis
    adres = db.Column(db.Text)
    il = db.Column(db.String(50))
    ilce = db.Column(db.String(50))
    iban = db.Column(db.String(30))  # TR + 24 hane (evraktan otomatik okunur veya manuel)

    # ==================== Fiziksel Bilgiler ====================
    ust_beden = db.Column(db.String(10))    # XS, S, M, L, XL, XXL, 3XL
    alt_beden = db.Column(db.String(10))    # XS, S, M, L, XL, XXL, 3XL
    ayakkabi_no = db.Column(db.String(5))   # 36-47

    # ==================== Lojistik ====================
    kargo_subesi = db.Column(db.String(150))  # En yakın kargo şubesi
    kargo_barkod_foto = db.Column(db.String(255))  # Kargo gönderim barkodu fotoğrafı (dosya yolu)

    # ==================== Başvuru Kaynağı / Geçmiş ====================
    basvuru_kaynak = db.Column(db.String(50))   # BASVURU_KAYNAK_TURLERI'nden biri (nereden ulaştı)
    tg_calistimi = db.Column(db.Boolean, default=False)  # Daha önce Team Guerilla'da çalıştı mı?

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
    red_tarihi = db.Column(db.DateTime)

    # ==================== Havuz (Rezerve Aday) ====================
    havuz_notu = db.Column(db.Text)               # Hangi tür pozisyona uygun / neden havuza alındı
    havuza_alinma_tarihi = db.Column(db.DateTime)

    # ==================== Mükerrer Başvuru Uyarısı ====================
    # Aynı TC/telefon ile daha önce reddedilmiş ya da işten ayrılmış bir kayıt
    # varsa başvuru anında işaretlenir; İK onay/red kararını bilerek versin.
    mukerrer_uyari = db.Column(db.Boolean, default=False)
    mukerrer_uyari_notu = db.Column(db.Text)

    # ==================== İşe Alım Süreci (Faz 3) ====================
    planlanan_baslangic = db.Column(db.Date)          # Planlı işe başlangıç tarihi (onayda zorunlu)
    sgk_bildirgesi = db.Column(db.String(255))        # SGK giriş bildirgesi PDF dosya yolu
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))  # Dönüştürülen çalışan

    notlar = db.Column(db.Text)  # İK notları

    # ==================== İlişkiler ====================
    pozisyon = db.relationship('Pozisyon', backref='adaylar')
    donusen_calisan = db.relationship('Calisan', foreign_keys=[calisan_id])

    def __repr__(self):
        return f'<Aday {self.full_name}>'

    @property
    def full_name(self):
        return f'{self.ad} {self.soyad}'

    # Eğitim durumu kodu -> okunabilir etiket
    EGITIM_DURUMU_LABELS = {
        'ilkokul': 'İlkokul',
        'ortaokul': 'Ortaokul',
        'lise': 'Lise',
        'onlisans': 'Ön Lisans',
        'lisans': 'Lisans',
        'yukseklisans': 'Yüksek Lisans',
        'doktora': 'Doktora',
    }

    @property
    def egitim_durumu_label(self):
        """Eğitim durumu kodunu okunabilir etikete çevirir."""
        if not self.egitim_durumu:
            return ''
        return self.EGITIM_DURUMU_LABELS.get(self.egitim_durumu, self.egitim_durumu)

    @property
    def blacklist_calisan(self):
        """TC ile eski çalışan kaydını bulur — kara/gri liste kontrolü için.
        Returns Calisan or None.
        """
        if not self.tc_kimlik:
            return None
        return Calisan.query.filter(
            Calisan.tc_kimlik == self.tc_kimlik,
            Calisan.is_deleted == False,
            Calisan.liste_durumu != ListeDurumu.TEMIZ,
        ).first()

    @property
    def blacklist_durum(self):
        """Aday'ın eski kayıtlarından kara/gri liste durumu (None / ListeDurumu)"""
        c = self.blacklist_calisan
        return c.liste_durumu if c else None

    @property
    def is_kara_liste(self):
        return self.blacklist_durum == ListeDurumu.KARA_LISTE

    @property
    def is_gri_liste(self):
        return self.blacklist_durum == ListeDurumu.GRI_LISTE

    # ==================== Mükerrer Başvuru Tespiti ====================
    # Aynı kişi = aynı TC kimlik VEYA aynı cep telefonu. Telefon alanı eski
    # kayıtlarda normalize edilmemiş olabildiği için ham + normalize değerlerin
    # ikisiyle de eşleştirilir.

    RED_DURUMLARI = ('reddedildi', 'red')

    @staticmethod
    def telefon_varyantlari(telefon):
        """Telefon eşleştirmesinde kullanılacak değerler (ham + normalize)."""
        from app.utils import normalize_telefon
        return [t for t in {telefon, normalize_telefon(telefon)} if t]

    @classmethod
    def mukerrer_kosulu(cls, tc_kimlik=None, telefon=None):
        """Aynı kişiye ait kayıtları bulan SQLAlchemy koşulu.
        Eşleştirilecek hiçbir kimlik bilgisi yoksa None döner."""
        kosullar = []
        if tc_kimlik:
            kosullar.append(cls.tc_kimlik == tc_kimlik)
        varyantlar = cls.telefon_varyantlari(telefon)
        if varyantlar:
            kosullar.append(cls.telefon.in_(varyantlar))
        if not kosullar:
            return None
        return db.or_(*kosullar)

    @property
    def diger_basvurular(self):
        """Aynı TC veya telefonla yapılmış DİĞER başvurular (yeniden eskiye).
        Sonuç instance üzerinde cache'lenir (template birden çok kez okuyor)."""
        if not hasattr(self, '_diger_basvurular_cache'):
            kosul = Aday.mukerrer_kosulu(self.tc_kimlik, self.telefon)
            if kosul is None:
                self._diger_basvurular_cache = []
            else:
                self._diger_basvurular_cache = Aday.query.filter(
                    Aday.id != self.id,
                    Aday.is_deleted == False,
                    kosul,
                ).order_by(Aday.created_at.desc()).all()
        return self._diger_basvurular_cache

    @property
    def mukerrer_sayisi(self):
        """Bu kişiye ait toplam başvuru sayısı (kendisi dahil)."""
        return len(self.diger_basvurular) + 1

    @property
    def is_mukerrer(self):
        return len(self.diger_basvurular) > 0

    @property
    def onceki_redler(self):
        """Aynı kişinin daha önce reddedilmiş başvuruları."""
        return [a for a in self.diger_basvurular if a.durum in Aday.RED_DURUMLARI]

    @property
    def eski_calisan_kayitlari(self):
        """Aynı TC/telefonla işe alınmış ve AYRILMIŞ çalışan kayıtları.
        Bu adayın kendi dönüştüğü çalışan hariç tutulur."""
        if not hasattr(self, '_eski_calisan_cache'):
            kosullar = []
            if self.tc_kimlik:
                kosullar.append(Calisan.tc_kimlik == self.tc_kimlik)
            varyantlar = Aday.telefon_varyantlari(self.telefon)
            if varyantlar:
                kosullar.append(Calisan.telefon.in_(varyantlar))
            if not kosullar:
                self._eski_calisan_cache = []
            else:
                q = Calisan.query.filter(
                    Calisan.is_deleted == False,
                    Calisan.durum == CalisanDurumu.AYRILDI,
                    db.or_(*kosullar),
                )
                if self.calisan_id:
                    q = q.filter(Calisan.id != self.calisan_id)
                self._eski_calisan_cache = q.order_by(
                    Calisan.isten_ayrilma.desc().nulls_last()).all()
        return self._eski_calisan_cache

    @property
    def mukerrer_uyari_var(self):
        """İK'nın karar öncesi görmesi gereken bir geçmiş kayıt var mı?"""
        return bool(self.onceki_redler or self.eski_calisan_kayitlari)
    
    @property
    def is_token_valid(self):
        """Token hala geçerli mi?"""
        if not self.davet_token or not self.davet_token_expires:
            return False
        return datetime.now() < self.davet_token_expires
    
    @property
    def basvuru_durumu_text(self):
        """Başvuru durumunu okunabilir text olarak döndür"""
        durum_map = {
            'davet_gonderildi': 'Davet Gönderildi',
            'kvkk_bekleniyor': 'KVKK Onayı Bekleniyor',
            'form_bekleniyor': 'Form Bekleniyor',
            'basvurdu': 'Başvuru Yapıldı',
            'inceleniyor': 'İnceleniyor',
            'onaylandi': 'Onaylandı',
            'sgk_giris_talebi': 'SGK Giriş Talebi',
            'sgk_girisi_yapildi': 'SGK Girişi Yapıldı',
            'calisana_donusturuldu': 'Çalışana Dönüştürüldü',
            # Eski/legacy değerler
            'degerlendiriliyor': 'Değerlendiriliyor',
            'mulakat': 'Mülakat Aşamasında',
            'teklif': 'Teklif Yapıldı',
            'ise_alindi': 'İşe Alındı',
            'red': 'Reddedildi',
            'reddedildi': 'Reddedildi',
            'havuzda': 'Havuzda',
            'aday_reddetti': 'Aday Reddetti',
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
            'inceleniyor': 'info',
            'onaylandi': 'success',
            'sgk_giris_talebi': 'warning',
            'sgk_girisi_yapildi': 'info',
            'calisana_donusturuldu': 'success',
            'degerlendiriliyor': 'primary',
            'mulakat': 'info',
            'teklif': 'success',
            'ise_alindi': 'success',
            'red': 'danger',
            'reddedildi': 'danger',
            'havuzda': 'info',         # mavi
            'aday_reddetti': 'warning',  # turuncu
            'iptal': 'secondary'
        }
        return renk_map.get(self.durum, 'secondary')

    @property
    def is_reddedildi(self):
        return self.durum in ('red', 'reddedildi')

    @property
    def is_havuzda(self):
        return self.durum == 'havuzda'

    @property
    def donusum_kilitli(self):
        """Aday çalışana dönüştürülmüş VE bağlı çalışan hâlâ AKTIF/İZİNLİ ise
        durum değişiklikleri (reddet, havuza al, manuel durum vb.) kilitlidir.
        Çalışan AYRILDI/ASKIYA_ALINDI ise tekrar işe alım için kilit açılır."""
        if not self.calisan_id:
            return False
        c = self.donusen_calisan
        if not c:
            # Çalışan kaydı bulunamıyorsa (silinmiş) kilitleme
            return False
        return c.durum in (CalisanDurumu.AKTIF, CalisanDurumu.IZINLI)

    @property
    def tekrar_ise_alim_uygun(self):
        """calisan_id dolu ama bağlı çalışan AYRILDI/ASKIYA_ALINDI ise
        → tekrar işe alım süreci başlatılabilir."""
        if not self.calisan_id:
            return False
        c = self.donusen_calisan
        return bool(c) and c.durum in (CalisanDurumu.AYRILDI, CalisanDurumu.ASKIYA_ALINDI)

    @property
    def akis_adim_index(self):
        """ADAY_DURUM_AKISI içindeki sıra (0-bazlı); akışta değilse -1."""
        kodlar = [k for k, _ in ADAY_DURUM_AKISI]
        # Legacy durumları yeni akışa eşle
        esle = {'degerlendiriliyor': 'inceleniyor', 'mulakat': 'inceleniyor',
                'teklif': 'onaylandi', 'ise_alindi': 'calisana_donusturuldu'}
        d = esle.get(self.durum, self.durum)
        return kodlar.index(d) if d in kodlar else -1
    
    @property
    def kaynak_text(self):
        """Kaynak türünü okunabilir text olarak döndür"""
        kaynak_map = dict(KAYNAK_TURLERI)
        return kaynak_map.get(self.kaynak, self.kaynak or '-')

    @property
    def basvuru_kaynak_text(self):
        """'Bize nereden ulaştınız?' cevabını okunabilir text olarak döndür"""
        return dict(BASVURU_KAYNAK_TURLERI).get(self.basvuru_kaynak, self.basvuru_kaynak or '-')
    
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
        self.davet_token_expires = datetime.now() + timedelta(hours=72)
        return self.davet_token
    
    def generate_otp(self):
        '''6 haneli doğrulama kodu oluştur'''
        import random
        from datetime import datetime, timedelta
        
        self.telefon_dogrulama_kodu = str(random.randint(100000, 999999))
        self.telefon_dogrulama_kodu_expires = datetime.now() + timedelta(minutes=5)
        self.telefon_dogrulama_deneme = 0
        return self.telefon_dogrulama_kodu
    
    @property
    def is_otp_valid(self):
        '''OTP hala geçerli mi?'''
        if not self.telefon_dogrulama_kodu or not self.telefon_dogrulama_kodu_expires:
            return False
        return datetime.now() < self.telefon_dogrulama_kodu_expires
    
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
        self.telefon_dogrulama_tarihi = datetime.now()
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
            'iban': self.iban,
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
        self.telefon_dogrulama_kodu_expires = datetime.now() + timedelta(minutes=5)
        self.telefon_dogrulama_deneme = 0
        return self.telefon_dogrulama_kodu
    
    @property
    def is_otp_valid(self):
        """OTP hala geçerli mi?"""
        if not self.telefon_dogrulama_kodu or not self.telefon_dogrulama_kodu_expires:
            return False
        from datetime import datetime
        return datetime.now() < self.telefon_dogrulama_kodu_expires
    
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
        self.telefon_dogrulama_tarihi = datetime.now()
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


# -*- coding: utf-8 -*-
"""
TG Portal - İK Models Eklentileri
Bu dosyayı mevcut app/models/ik.py dosyasının SONUNA ekleyin
"""

# ============================================================
# EVRAK YÖNETİMİ
# ============================================================

class EvrakTipi(db.Model, TimestampMixin):
    """Evrak tipi tanımları"""
    __tablename__ = 'evrak_tipleri'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)  # Nüfus Cüzdanı, Diploma, vb.
    kod = db.Column(db.String(20), unique=True)  # NUFUS, DIPLOMA, SGK, vb.
    aciklama = db.Column(db.Text)
    zorunlu = db.Column(db.Boolean, default=False)  # İşe alım için zorunlu mu?
    kategori = db.Column(db.String(50))  # kimlik, egitim, saglik, sozlesme, diger
    gecerlilik_suresi = db.Column(db.Integer)  # Gün cinsinden, null = süresiz
    sira = db.Column(db.Integer, default=0)  # Görüntüleme sırası
    aktif = db.Column(db.Boolean, default=True)
    
    evraklar = db.relationship('AdayEvrak', backref='evrak_tipi', lazy='dynamic')
    
    def __repr__(self):
        return f'<EvrakTipi {self.ad}>'


class AdayEvrak(db.Model, TimestampMixin):
    """Aday evrak yüklemeleri"""
    __tablename__ = 'aday_evraklar'
    
    id = db.Column(db.Integer, primary_key=True)
    aday_id = db.Column(db.Integer, db.ForeignKey('adaylar.id'), nullable=False)
    evrak_tipi_id = db.Column(db.Integer, db.ForeignKey('evrak_tipleri.id'), nullable=False)
    
    # Dosya bilgileri
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))
    dosya_boyut = db.Column(db.Integer)  # bytes
    mime_type = db.Column(db.String(100))
    
    # Onay durumu
    durum = db.Column(db.String(20), default='yuklendi')  # yuklendi, onaylandi, reddedildi
    red_sebebi = db.Column(db.Text)
    
    # İzleme
    yukleyen_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    onaylayan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    onay_tarihi = db.Column(db.DateTime)
    
    gecerlilik_bitis = db.Column(db.Date)  # Evrak geçerlilik bitiş tarihi
    
    # İlişkiler
    aday = db.relationship('Aday', backref=db.backref('evraklar', lazy='dynamic'))
    yukleyen = db.relationship('User', foreign_keys=[yukleyen_id], backref='yuklenen_evraklar')
    onaylayan = db.relationship('User', foreign_keys=[onaylayan_id], backref='onaylanan_evraklar')
    
    def __repr__(self):
        return f'<AdayEvrak {self.aday_id}-{self.evrak_tipi_id}>'
    
    @property
    def durum_renk(self):
        renk_map = {
            'yuklendi': 'warning',
            'onaylandi': 'success',
            'reddedildi': 'danger'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def durum_text(self):
        text_map = {
            'yuklendi': 'Onay Bekliyor',
            'onaylandi': 'Onaylandı',
            'reddedildi': 'Reddedildi'
        }
        return text_map.get(self.durum, self.durum)


class AdayMedya(db.Model, TimestampMixin):
    """Aday foto/video yüklemeleri"""
    __tablename__ = 'aday_medya'

    id = db.Column(db.Integer, primary_key=True)
    aday_id = db.Column(db.Integer, db.ForeignKey('adaylar.id'), nullable=False, index=True)
    tip = db.Column(db.String(10), nullable=False)  # 'foto' veya 'video'

    dosya_adi = db.Column(db.String(255))      # Orijinal isim
    dosya_yolu = db.Column(db.String(500))     # uploads klasörüne göre relatif yol (uploads/'a giren)
    dosya_boyut = db.Column(db.Integer)        # bytes
    mime_type = db.Column(db.String(100))

    yukleyen_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # İlişkiler
    aday = db.relationship('Aday', backref=db.backref('medyalar', lazy='dynamic', order_by='AdayMedya.created_at.desc()'))
    yukleyen = db.relationship('User')

    def __repr__(self):
        return f'<AdayMedya {self.aday_id}-{self.tip}-{self.id}>'


class AdayIslemGecmisi(db.Model, TimestampMixin):
    """Aday işe alım sürecindeki her aşama/işlem kaydı (audit timeline)."""
    __tablename__ = 'aday_islem_gecmisi'

    id = db.Column(db.Integer, primary_key=True)
    aday_id = db.Column(db.Integer, db.ForeignKey('adaylar.id'), nullable=False, index=True)

    islem = db.Column(db.String(50), nullable=False)  # incele, onayla, sgk_talep, sgk_giris, donustur, reddet, durum
    aciklama = db.Column(db.Text)
    onceki_durum = db.Column(db.String(30))
    yeni_durum = db.Column(db.String(30))

    # İletişim logları için: "geri_aranacak" işlemlerinde adayın ne zaman geri
    # aranacağı. Diğer işlemlerde NULL.
    hatirlatma_tarihi = db.Column(db.DateTime, nullable=True)

    kullanici_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # İlişkiler
    aday = db.relationship('Aday', backref=db.backref(
        'islem_gecmisi', lazy='dynamic', order_by='AdayIslemGecmisi.created_at.desc()'))
    kullanici = db.relationship('User')

    # İletişim (arama/not) işlem tipleri — süreç adımı değil, aday ile temas kaydı
    ILETISIM_ISLEMLER = {
        'arama_yapildi', 'ulasilamadi', 'sms_gonderildi',
        'whatsapp_yazildi', 'geri_aranacak',
    }

    ISLEM_ETIKET = {
        'incele': 'İncelemeye Alındı',
        'onayla': 'Onaylandı',
        'sgk_talep': 'SGK Giriş Talebi Oluşturuldu',
        'sgk_giris': 'SGK Girişi Yapıldı',
        'donustur': 'Çalışana Dönüştürüldü',
        'reddet': 'Reddedildi',
        'havuza_al': 'Havuza Alındı',
        'aday_reddetti': 'Aday İşi Reddetti',
        'havuzdan_ata': 'Havuzdan Kadroya Atandı',
        'mukerrer_basvuru': 'Mükerrer Başvuru Tespit Edildi',
        'durum': 'Durum Güncellendi',
        'planli_tarih': 'Planlı Başlangıç Tarihi Değiştirildi',
        # İletişim logları
        'arama_yapildi': 'Arama Yapıldı',
        'ulasilamadi': 'Ulaşılamadı',
        'sms_gonderildi': 'SMS Gönderildi',
        'whatsapp_yazildi': 'WhatsApp Yazıldı',
        'geri_aranacak': 'Geri Aranacak',
    }

    # İletişim işlemleri için Material Symbols ikon adı
    ILETISIM_IKON = {
        'arama_yapildi': 'call',
        'ulasilamadi': 'phone_missed',
        'sms_gonderildi': 'sms',
        'whatsapp_yazildi': 'chat',
        'geri_aranacak': 'schedule',
    }

    @property
    def islem_etiket(self):
        return self.ISLEM_ETIKET.get(self.islem, self.islem)

    @property
    def is_iletisim(self):
        return self.islem in self.ILETISIM_ISLEMLER

    @property
    def iletisim_ikon(self):
        return self.ILETISIM_IKON.get(self.islem, 'history')

    def __repr__(self):
        return f'<AdayIslemGecmisi {self.aday_id}-{self.islem}>'


class CalisanEvrak(db.Model, TimestampMixin):
    """Çalışan evrakları"""
    __tablename__ = 'calisan_evraklar'
    
    id = db.Column(db.Integer, primary_key=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    evrak_tipi_id = db.Column(db.Integer, db.ForeignKey('evrak_tipleri.id'), nullable=False)
    
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))
    dosya_boyut = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    
    gecerlilik_bitis = db.Column(db.Date)
    
    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('evraklar', lazy='dynamic'))
    evrak_tipi = db.relationship('EvrakTipi')
    
    def __repr__(self):
        return f'<CalisanEvrak {self.calisan_id}-{self.evrak_tipi_id}>'


# ============================================================
# İŞTEN ÇIKIŞ YÖNETİMİ
# ============================================================

class SgkCikisKodu(db.Model, TimestampMixin):
    """Standart SGK işten çıkış kodları (referans tablo)"""
    __tablename__ = 'sgk_cikis_kodlari'

    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.Integer, unique=True, nullable=False, index=True)
    aciklama = db.Column(db.String(300), nullable=False)
    aktif = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f'<SgkCikisKodu {self.kod} - {self.aciklama}>'

    @property
    def onerilen_liste_durumu(self):
        """SGK koduna göre otomatik liste durumu önerisi"""
        # Kara liste: haklı fesih, disiplin
        if self.kod in (3, 26):
            return ListeDurumu.KARA_LISTE
        # Temiz: istifa, emeklilik, ölüm, askerlik, evlilik, sözleşme bitimi, mevsim
        if self.kod in (1, 2, 5, 8, 9, 10, 11, 12, 13, 14, 19, 20, 25, 34):
            return ListeDurumu.TEMIZ
        # Gri: diğer nedenler, 4, 15, 16, 17, 18, 22, 27, 29, 30, 31, 32, 33
        return ListeDurumu.GRI_LISTE


class IstenCikis(db.Model, TimestampMixin):
    """İşten çıkış süreç takibi"""
    __tablename__ = 'isten_cikislar'

    id = db.Column(db.Integer, primary_key=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)

    # Tarihler
    talep_tarihi = db.Column(db.Date, default=date.today)
    planlanan_cikis_tarihi = db.Column(db.Date, nullable=False)
    gerceklesen_cikis_tarihi = db.Column(db.Date)

    # Çıkış bilgileri
    cikis_tipi = db.Column(db.String(30))  # istifa, fesih, anlasmali, emeklilik, vefat, sozlesme_bitti
    cikis_sebebi = db.Column(db.String(100))
    detay_notu = db.Column(db.Text)

    # SGK Çıkış Kodu
    sgk_cikis_kodu_id = db.Column(db.Integer, db.ForeignKey('sgk_cikis_kodlari.id'))

    # Checklist
    zimmet_teslim = db.Column(db.Boolean, default=False)
    zimmet_notu = db.Column(db.Text)

    sgk_cikis_bildirimi = db.Column(db.Boolean, default=False)
    sgk_bildirim_tarihi = db.Column(db.Date)

    # Tazminatlar
    kidem_tazminati = db.Column(db.Numeric(12, 2))
    ihbar_tazminati = db.Column(db.Numeric(12, 2))

    # Çıkış mülakatı
    cikis_mulakati_yapildi = db.Column(db.Boolean, default=False)
    cikis_mulakat_notu = db.Column(db.Text)

    # Durum
    durum = db.Column(db.String(20), default='basladi')  # basladi, devam_ediyor, tamamlandi, iptal

    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('cikis_kayitlari', lazy='dynamic'))
    olusturan = db.relationship('User', backref='olusturulan_cikislar')
    sgk_cikis_kodu = db.relationship('SgkCikisKodu')
    
    def __repr__(self):
        return f'<IstenCikis {self.calisan_id}>'
    
    @property
    def durum_renk(self):
        renk_map = {
            'basladi': 'info',
            'devam_ediyor': 'warning',
            'tamamlandi': 'success',
            'iptal': 'secondary'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def tamamlanma_yuzdesi(self):
        """Checklist tamamlanma yüzdesi"""
        items = [self.zimmet_teslim, self.sgk_cikis_bildirimi, self.cikis_mulakati_yapildi]
        return int((sum(items) / len(items)) * 100)


class IstenCikisBildirimi(db.Model, TimestampMixin):
    """SPV / Koordinatör tarafından İK + Bordro ekibine gönderilen işten çıkış ön bildirimi.

    Resmi işten çıkış sürecinden (IstenCikis) önce; sahadaki yetkili çalışanın
    ayrılacak personeli İK'ya bildirmesini sağlar. İK bu bildirimi işleme alıp
    resmi çıkış sürecini başlatır.
    """
    __tablename__ = 'isten_cikis_bildirimleri'

    id = db.Column(db.Integer, primary_key=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False, index=True)
    bildiren_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    cikis_nedeni = db.Column(db.String(30), nullable=False)  # istifa, devamsizlik, performans, sozlesme_bitimi, diger
    son_calisma_gunu = db.Column(db.Date, nullable=False)
    aciklama = db.Column(db.Text)  # opsiyonel not/açıklama

    # beklemede -> isleme_alindi -> tamamlandi
    durum = db.Column(db.String(20), default='beklemede', nullable=False)

    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref(
        'cikis_bildirimleri', lazy='dynamic',
        order_by='IstenCikisBildirimi.created_at.desc()'))
    bildiren = db.relationship('User', backref='gonderdigi_cikis_bildirimleri')

    CIKIS_NEDENLERI = [
        ('istifa', 'İstifa'),
        ('devamsizlik', 'Devamsızlık'),
        ('performans', 'Performans'),
        ('sozlesme_bitimi', 'Sözleşme Bitimi'),
        ('diger', 'Diğer'),
    ]

    DURUMLAR = {
        'beklemede': 'Beklemede',
        'isleme_alindi': 'İşleme Alındı',
        'tamamlandi': 'Tamamlandı',
        # SGK çıkış akışı: resmi çıkış tamamlandıktan sonra bordronun SGK çıkışını
        # yapıp bildirgeyi yüklemesi beklenir.
        'sgk_cikis_bekleniyor': 'SGK Çıkışı Bekleniyor',
        'sgk_cikis_yapildi': 'SGK Çıkışı Yapıldı',
    }

    def __repr__(self):
        return f'<IstenCikisBildirimi {self.calisan_id}-{self.durum}>'

    @property
    def cikis_nedeni_text(self):
        return dict(self.CIKIS_NEDENLERI).get(self.cikis_nedeni, self.cikis_nedeni)

    @property
    def durum_text(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @property
    def durum_renk(self):
        return {
            'beklemede': 'warning',
            'isleme_alindi': 'info',
            'tamamlandi': 'success',
        }.get(self.durum, 'secondary')


# ============================================================
# ADAY MODELİNE EVRAK HELPER'LARI EKLENMELİ
# Mevcut Aday class'ına şu property'leri ekleyin:
# ============================================================

"""
# Aday class'ına eklenecek property'ler:

@property
def evrak_tamamlanma_orani(self):
    '''Zorunlu evrakların tamamlanma yüzdesi'''
    zorunlu_evraklar = EvrakTipi.query.filter_by(zorunlu=True, aktif=True).count()
    if zorunlu_evraklar == 0:
        return 100
    yuklenen = self.evraklar.join(EvrakTipi).filter(
        EvrakTipi.zorunlu == True,
        AdayEvrak.durum == 'onaylandi'
    ).count()
    return int((yuklenen / zorunlu_evraklar) * 100)

@property
def eksik_evraklar(self):
    '''Eksik zorunlu evrak listesi'''
    zorunlu_tipler = EvrakTipi.query.filter_by(zorunlu=True, aktif=True).all()
    yuklenen_tipler = [e.evrak_tipi_id for e in self.evraklar.filter(
        AdayEvrak.durum.in_(['yuklendi', 'onaylandi'])
    ).all()]
    return [t for t in zorunlu_tipler if t.id not in yuklenen_tipler]

@property
def ise_alim_hazir(self):
    '''Tüm zorunlu evraklar tamamlandı mı?'''
    return len(self.eksik_evraklar) == 0 and self.kvkk_onay
"""

# ============================================================
# ZİMMET / ENVANTER YÖNETİMİ
# ============================================================

class ZimmetTipi(db.Model, TimestampMixin):
    """Zimmet tipi tanımları"""
    __tablename__ = 'zimmet_tipleri'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)  # Laptop, Telefon, Araç Anahtarı
    kod = db.Column(db.String(20), unique=True)  # LAPTOP, TELEFON, ANAHTAR
    kategori = db.Column(db.String(50))  # elektronik, arac, ofis, diger
    aciklama = db.Column(db.Text)
    seri_no_zorunlu = db.Column(db.Boolean, default=False)  # Seri numarası zorunlu mu?
    iade_zorunlu = db.Column(db.Boolean, default=True)  # İşten çıkışta iade zorunlu mu?
    aktif = db.Column(db.Boolean, default=True)
    
    zimmetler = db.relationship('Zimmet', backref='zimmet_tipi', lazy='dynamic')
    
    def __repr__(self):
        return f'<ZimmetTipi {self.ad}>'


class Zimmet(db.Model, TimestampMixin, SoftDeleteMixin):
    """Zimmet kayıtları"""
    __tablename__ = 'zimmetler'
    
    id = db.Column(db.Integer, primary_key=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    zimmet_tipi_id = db.Column(db.Integer, db.ForeignKey('zimmet_tipleri.id'), nullable=False)
    
    # Zimmet detayları
    tanim = db.Column(db.String(255))  # "MacBook Pro 14", "iPhone 13 Pro" vb.
    seri_no = db.Column(db.String(100))
    demirbas_no = db.Column(db.String(50))  # Şirket demirbaş numarası
    marka = db.Column(db.String(100))
    model = db.Column(db.String(100))
    
    # Teslim bilgileri
    teslim_tarihi = db.Column(db.Date, nullable=False)
    teslim_eden_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    teslim_notu = db.Column(db.Text)
    
    # İade bilgileri
    iade_tarihi = db.Column(db.Date)
    iade_alan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    iade_notu = db.Column(db.Text)
    iade_durumu = db.Column(db.String(50))  # saglam, hasarli, kayip
    
    # Durum
    durum = db.Column(db.String(20), default='teslim_edildi')  # teslim_edildi, iade_edildi, kayip, hasarli
    
    # Değer bilgisi (opsiyonel)
    deger = db.Column(db.Numeric(12, 2))  # TL cinsinden değer
    
    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('zimmetler', lazy='dynamic'))
    teslim_eden = db.relationship('User', foreign_keys=[teslim_eden_id], backref='teslim_edilen_zimmetler')
    iade_alan = db.relationship('User', foreign_keys=[iade_alan_id], backref='iade_alinan_zimmetler')
    
    def __repr__(self):
        return f'<Zimmet {self.id} - {self.tanim}>'
    
    @property
    def durum_text(self):
        durum_map = {
            'teslim_edildi': 'Teslim Edildi',
            'iade_edildi': 'İade Edildi',
            'kayip': 'Kayıp',
            'hasarli': 'Hasarlı'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        renk_map = {
            'teslim_edildi': 'primary',
            'iade_edildi': 'success',
            'kayip': 'danger',
            'hasarli': 'warning'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def aktif_mi(self):
        """Zimmet hala çalışanda mı?"""
        return self.durum == 'teslim_edildi' and self.iade_tarihi is None


class ZimmetLog(db.Model, TimestampMixin):
    """Zimmet hareket geçmişi"""
    __tablename__ = 'zimmet_loglar'
    
    id = db.Column(db.Integer, primary_key=True)
    zimmet_id = db.Column(db.Integer, db.ForeignKey('zimmetler.id'), nullable=False)
    islem = db.Column(db.String(50))  # teslim, iade, transfer, hasar_bildirimi, kayip_bildirimi
    aciklama = db.Column(db.Text)
    islem_yapan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Transfer için
    eski_calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))
    yeni_calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))
    
    # İlişkiler
    zimmet = db.relationship('Zimmet', backref=db.backref('loglar', lazy='dynamic', order_by='ZimmetLog.created_at.desc()'))
    islem_yapan = db.relationship('User', foreign_keys=[islem_yapan_id])
    eski_calisan = db.relationship('Calisan', foreign_keys=[eski_calisan_id])
    yeni_calisan = db.relationship('Calisan', foreign_keys=[yeni_calisan_id])


# ============================================================
# CALISAN MODELİNE EKLENECEK PROPERTY'LER
# Mevcut Calisan class'ına şu property'leri ekleyin:
# ============================================================

"""
# Calisan class'ına eklenecek property'ler:

@property
def aktif_zimmetler(self):
    '''Çalışanda bulunan aktif zimmetler'''
    return self.zimmetler.filter(
        Zimmet.durum == 'teslim_edildi',
        Zimmet.iade_tarihi == None,
        Zimmet.is_deleted == False
    ).all()

@property
def aktif_zimmet_sayisi(self):
    '''Aktif zimmet sayısı'''
    return len(self.aktif_zimmetler)

@property
def zimmet_iade_bekliyor(self):
    '''İade bekleyen zimmet var mı?'''
    return self.aktif_zimmet_sayisi > 0
"""

# ============================================================
# DİSİPLİN YÖNETİMİ
# ============================================================

class DisiplinKaydi(db.Model, TimestampMixin, SoftDeleteMixin):
    """Çalışan disiplin kayıtları"""
    __tablename__ = 'disiplin_kayitlari'
    
    id = db.Column(db.Integer, primary_key=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    
    # Disiplin bilgileri
    tarih = db.Column(db.Date, nullable=False)
    tur = db.Column(db.String(50), nullable=False)  # uyari, ihtar, fesih_uyarisi, is_akdi_feshi
    seviye = db.Column(db.Integer, default=1)  # 1: Hafif, 2: Orta, 3: Ağır
    konu = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    
    # Belge
    belge_path = db.Column(db.String(500))
    
    # Onay bilgileri
    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    onaylayan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    onay_tarihi = db.Column(db.DateTime)
    durum = db.Column(db.String(30), default='taslak')  # taslak, onaylandi, iptal
    
    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('disiplin_kayitlari', lazy='dynamic'))
    olusturan = db.relationship('User', foreign_keys=[olusturan_id])
    onaylayan = db.relationship('User', foreign_keys=[onaylayan_id])
    
    @property
    def tur_text(self):
        turler = {
            'uyari': 'Sözlü Uyarı',
            'ihtar': 'Yazılı İhtar',
            'fesih_uyarisi': 'Fesih Uyarısı',
            'is_akdi_feshi': 'İş Akdi Feshi'
        }
        return turler.get(self.tur, self.tur)
    
    @property
    def seviye_text(self):
        seviyeler = {1: 'Hafif', 2: 'Orta', 3: 'Ağır'}
        return seviyeler.get(self.seviye, '-')


# ============================================================
# DAVA YÖNETİMİ
# ============================================================

class Dava(db.Model, TimestampMixin, SoftDeleteMixin):
    """Hukuki dava kayıtları"""
    __tablename__ = 'davalar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dava bilgileri
    dosya_no = db.Column(db.String(50), unique=True)
    esas_no = db.Column(db.String(50))
    mahkeme = db.Column(db.String(200), nullable=False)
    dava_turu = db.Column(db.String(100), nullable=False)  # ise_iade, alacak, tespit, tazminat, ceza
    
    # Taraflar
    davaci = db.Column(db.String(200), nullable=False)
    davali = db.Column(db.String(200), nullable=False)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))  # İlişkili çalışan varsa
    
    # Tarihler
    acilis_tarihi = db.Column(db.Date, nullable=False)
    son_durusma = db.Column(db.Date)
    sonraki_durusma = db.Column(db.Date)
    karar_tarihi = db.Column(db.Date)
    
    # Tutarlar
    talep_tutari = db.Column(db.Numeric(12, 2))
    karar_tutari = db.Column(db.Numeric(12, 2))
    
    # Durum
    durum = db.Column(db.String(30), default='devam_ediyor')  # devam_ediyor, karara_baglandi, temyiz, kapandi
    sonuc = db.Column(db.String(50))  # kabul, ret, kismi_kabul, sulh, feragat
    
    # Açıklamalar
    konu_ozeti = db.Column(db.Text)
    notlar = db.Column(db.Text)
    
    # Avukat bilgileri
    avukat = db.Column(db.String(200))
    avukat_telefon = db.Column(db.String(20))
    
    # Sorumlu
    sorumlu_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('davalar', lazy='dynamic'))
    sorumlu = db.relationship('User', foreign_keys=[sorumlu_id])
    
    @property
    def durum_text(self):
        durumlar = {
            'devam_ediyor': 'Devam Ediyor',
            'karara_baglandi': 'Karara Bağlandı',
            'temyiz': 'Temyizde',
            'kapandi': 'Kapandı'
        }
        return durumlar.get(self.durum, self.durum)
    
    @property
    def dava_turu_text(self):
        turler = {
            'ise_iade': 'İşe İade',
            'alacak': 'İşçi Alacağı',
            'tespit': 'Tespit Davası',
            'tazminat': 'Tazminat',
            'ceza': 'Ceza Davası',
            'diger': 'Diğer'
        }
        return turler.get(self.dava_turu, self.dava_turu)



# ============================================================
# İCRA DOSYASI YÖNETİMİ
# ============================================================

class IcraDosyasi(db.Model, TimestampMixin, SoftDeleteMixin):
    """Çalışan icra dosyaları ve kesinti takibi"""
    __tablename__ = 'icra_dosyalari'
    
    id = db.Column(db.Integer, primary_key=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    
    # Dosya bilgileri
    dosya_no = db.Column(db.String(100), nullable=False)
    icra_dairesi = db.Column(db.String(200), nullable=False)
    alacakli = db.Column(db.String(200))  # Alacaklı kişi/kurum
    
    # Tutar bilgileri
    toplam_borc = db.Column(db.Numeric(12, 2), nullable=False)
    kalan_borc = db.Column(db.Numeric(12, 2))
    
    # Taksit bilgileri
    taksit_sayisi = db.Column(db.Integer)
    taksit_tutari = db.Column(db.Numeric(12, 2))
    baslangic_tarihi = db.Column(db.Date)
    bitis_tarihi = db.Column(db.Date)
    
    # Kesinti oranı (maaşın yüzdesi olarak)
    kesinti_orani = db.Column(db.Numeric(5, 2))  # Örn: 25.00 = %25
    
    # Durum
    durum = db.Column(db.String(30), default='aktif')  # aktif, tamamlandi, iptal, beklemede
    notlar = db.Column(db.Text)
    
    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('icra_dosyalari', lazy='dynamic'))
    kesintiler = db.relationship('IcraKesinti', backref='icra_dosyasi', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def durum_text(self):
        durumlar = {
            'aktif': 'Aktif',
            'tamamlandi': 'Tamamlandı',
            'iptal': 'İptal',
            'beklemede': 'Beklemede'
        }
        return durumlar.get(self.durum, self.durum)
    
    @property
    def toplam_kesilen(self):
        return sum(k.tutar for k in self.kesintiler.filter_by(is_deleted=False).all()) or 0
    
    @property
    def ilerleme_yuzdesi(self):
        if not self.toplam_borc or self.toplam_borc == 0:
            return 0
        return min(100, int((self.toplam_kesilen / float(self.toplam_borc)) * 100))


# ============================================================
# SÖZLEŞME ŞABLONLARI
# ============================================================

class SozlesmeSablonu(db.Model, TimestampMixin, SoftDeleteMixin):
    """Personel sözleşme şablonları"""
    __tablename__ = 'sozlesme_sablonlari'

    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(200), nullable=False)
    tip = db.Column(db.String(50), nullable=False)  # belirsiz_sureli, belirli_sureli, part_time

    # Filtreleme kriterleri (hepsi nullable - genel sablon icin hepsi bos)
    musteri_id = db.Column(db.Integer, db.ForeignKey('musteriler.id'))
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'))
    pozisyon_id = db.Column(db.Integer, db.ForeignKey('pozisyonlar.id'))
    departman_id = db.Column(db.Integer, db.ForeignKey('departmanlar.id'))

    sablon_dosya = db.Column(db.String(500))  # .docx şablon yolu (placeholder'lı Word dosyası)
    html_sablon = db.Column(db.Text)          # (deprecated - eski HTML şablonları için saklanıyor)
    degiskenler = db.Column(db.JSON)          # Şablonda kullanılan değişken listesi (opsiyonel meta)
    aciklama = db.Column(db.Text)
    aktif = db.Column(db.Boolean, default=True)
    sira = db.Column(db.Integer, default=0)

    # İlişkiler
    musteri = db.relationship('Musteri', backref=db.backref('sozlesme_sablonlari', lazy='dynamic'))
    proje = db.relationship('Proje', backref=db.backref('sozlesme_sablonlari', lazy='dynamic'))
    pozisyon = db.relationship('Pozisyon', backref=db.backref('sozlesme_sablonlari', lazy='dynamic'))
    departman_rel = db.relationship('Departman', backref=db.backref('sozlesme_sablonlari', lazy='dynamic'))

    TIPLER = [
        ('belirsiz_sureli', 'Belirsiz Süreli'),
        ('belirli_sureli', 'Belirli Süreli'),
        ('part_time', 'Part Time'),
    ]

    @property
    def tip_text(self):
        return dict(self.TIPLER).get(self.tip, self.tip)

    @property
    def kapsam_text(self):
        parts = []
        if self.musteri:
            parts.append(self.musteri.display_name)
        if self.proje:
            parts.append(self.proje.ad)
        if self.pozisyon:
            parts.append(self.pozisyon.ad)
        if self.departman_rel:
            parts.append(self.departman_rel.ad)
        return ' / '.join(parts) if parts else 'Genel'

    @classmethod
    def sablonlari_filtrele(cls, musteri_id=None, proje_id=None, pozisyon_id=None, departman_id=None):
        """Spesifikten genele dogru sablon ara"""
        base = cls.query.filter_by(aktif=True, is_deleted=False)

        # 1. musteri + proje + pozisyon
        if musteri_id and proje_id and pozisyon_id:
            sonuc = base.filter_by(musteri_id=musteri_id, proje_id=proje_id, pozisyon_id=pozisyon_id).all()
            if sonuc:
                return sonuc

        # 2. musteri + proje
        if musteri_id and proje_id:
            sonuc = base.filter_by(musteri_id=musteri_id, proje_id=proje_id, pozisyon_id=None).all()
            if sonuc:
                return sonuc

        # 3. musteri + pozisyon
        if musteri_id and pozisyon_id:
            sonuc = base.filter_by(musteri_id=musteri_id, pozisyon_id=pozisyon_id, proje_id=None).all()
            if sonuc:
                return sonuc

        # 4. departman + pozisyon
        if departman_id and pozisyon_id:
            sonuc = base.filter_by(departman_id=departman_id, pozisyon_id=pozisyon_id).all()
            if sonuc:
                return sonuc

        # 5. sadece departman
        if departman_id:
            sonuc = base.filter_by(departman_id=departman_id, pozisyon_id=None, musteri_id=None).all()
            if sonuc:
                return sonuc

        # 6. Fallback: genel sablonlar
        return base.filter_by(musteri_id=None, proje_id=None, pozisyon_id=None, departman_id=None).all()

    def __repr__(self):
        return f'<SozlesmeSablonu {self.ad}>'


class IcraKesinti(db.Model, TimestampMixin, SoftDeleteMixin):
    """Aylık icra kesintileri"""
    __tablename__ = 'icra_kesintileri'
    
    id = db.Column(db.Integer, primary_key=True)
    icra_dosyasi_id = db.Column(db.Integer, db.ForeignKey('icra_dosyalari.id'), nullable=False)
    
    # Kesinti bilgileri
    donem = db.Column(db.String(7), nullable=False)  # YYYY-MM formatında
    tutar = db.Column(db.Numeric(12, 2), nullable=False)
    kesinti_tarihi = db.Column(db.Date)
    
    # Durum
    durum = db.Column(db.String(30), default='bekliyor')  # bekliyor, kesildi, iptal
    notlar = db.Column(db.Text)
    
    @property
    def durum_text(self):
        durumlar = {
            'bekliyor': 'Bekliyor',
            'kesildi': 'Kesildi',
            'iptal': 'İptal'
        }
        return durumlar.get(self.durum, self.durum)
