# -*- coding: utf-8 -*-
"""
TG Portal - Eğitim Modelleri
Eğitim tanımları, katılımcılar ve takip
"""

import secrets
from datetime import datetime, date
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


def _kayit_token():
    """Public kayıt işlemleri (onay/iptal/anket) için tahmin edilemez token."""
    return secrets.token_urlsafe(24)


# Eğitim kategorileri — (kod, etiket) sırası form dropdown'ında da kullanılır.
# EgitimTipi.kategori'den farklıdır: o eğitimin konusunu (İSG, ürün vb.),
# bu ise eğitimin kime/neden verildiğini tanımlar.
EGITIM_KATEGORILERI = [
    ('yeni_giris', 'Yeni İşe Giriş Eğitimi'),
    ('tekrar', 'Tekrar Eğitimi'),
    ('genel', 'Genel Eğitim'),
]

EGITIM_KATEGORI_ETIKET = dict(EGITIM_KATEGORILERI)


class EgitimTipi(db.Model, TimestampMixin):
    """Eğitim tipleri - Oryantasyon, İSG, Ürün Eğitimi vb."""
    __tablename__ = 'egitim_tipleri'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    kod = db.Column(db.String(20), unique=True)  # ORYANTASYON, ISG, URUN
    kategori = db.Column(db.String(50))  # zorunlu, teknik, soft_skill, urun
    aciklama = db.Column(db.Text)
    
    # Ayarlar
    sure_saat = db.Column(db.Float)  # Standart süre (saat)
    gecerlilik_gun = db.Column(db.Integer)  # Sertifika geçerlilik süresi (gün), NULL = süresiz
    sertifika_gerekli = db.Column(db.Boolean, default=False)
    tekrar_periyot_gun = db.Column(db.Integer)  # Tekrar eğitim periyodu (gün)
    
    aktif = db.Column(db.Boolean, default=True)
    sira = db.Column(db.Integer, default=0)
    
    # İlişkiler
    egitimler = db.relationship('Egitim', backref='egitim_tipi', lazy='dynamic')
    
    def __repr__(self):
        return f'<EgitimTipi {self.ad}>'


class Egitim(db.Model, TimestampMixin, SoftDeleteMixin):
    """Eğitim oturumu - Planlanan/gerçekleşen eğitimler"""
    __tablename__ = 'egitimler'
    
    id = db.Column(db.Integer, primary_key=True)
    egitim_tipi_id = db.Column(db.Integer, db.ForeignKey('egitim_tipleri.id'), nullable=False)
    
    # Temel bilgiler
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)

    # Kategori — yeni_giris, tekrar, genel (bkz. EGITIM_KATEGORILERI)
    egitim_kategorisi = db.Column(db.String(20), default='genel',
                                  nullable=False, server_default='genel')
    
    # Proje bağlantısı (opsiyonel - proje bazlı eğitimler için)
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'))
    
    # Tarih ve süre
    baslangic_tarihi = db.Column(db.DateTime, nullable=False)
    bitis_tarihi = db.Column(db.DateTime)
    sure_saat = db.Column(db.Float)  # Gerçekleşen süre
    
    # Lokasyon
    lokasyon_tipi = db.Column(db.String(20), default='yuz_yuze')  # yuz_yuze, online, hibrit
    lokasyon = db.Column(db.String(200))  # Adres veya online link
    
    # Eğitmen
    egitmen_tipi = db.Column(db.String(20))  # ic, dis
    egitmen_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))  # İç eğitmen
    dis_egitmen_ad = db.Column(db.String(100))  # Dış eğitmen adı
    dis_egitmen_kurum = db.Column(db.String(200))  # Eğitim firması
    
    # Kapasite
    kontenjan = db.Column(db.Integer)  # Max katılımcı
    min_katilimci = db.Column(db.Integer)  # Min katılımcı (açılma şartı)
    
    # Durum
    durum = db.Column(db.String(20), default='planli')  # planli, devam_ediyor, tamamlandi, iptal
    iptal_nedeni = db.Column(db.Text)
    
    # Maliyet
    maliyet = db.Column(db.Numeric(10, 2))
    para_birimi = db.Column(db.String(3), default='TRY')
    
    notlar = db.Column(db.Text)
    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
   
    # Jitsi Online Eğitim
    jitsi_room_name = db.Column(db.String(100))  # Oda adı
    jitsi_aktif = db.Column(db.Boolean, default=False)  # Canlı yayın aktif mi 
   
    # İlişkiler
    proje = db.relationship('Proje', backref=db.backref('egitimler', lazy='dynamic'))
    egitmen = db.relationship('Calisan', foreign_keys=[egitmen_id], backref='verdigi_egitimler')
    olusturan = db.relationship('User', foreign_keys=[olusturan_id])
    katilimcilar = db.relationship('EgitimKatilimci', backref='egitim', lazy='dynamic',
                                   cascade='all, delete-orphan')
    materyaller = db.relationship('EgitimMateryali', backref='egitim', lazy='dynamic',
                                  cascade='all, delete-orphan')
    
    @property
    def katilimci_sayisi(self):
        return self.katilimcilar.filter(
            EgitimKatilimci.durum.in_(['davetli', 'katildi', 'gecti'])
        ).count()
    
    @property
    def tamamlayan_sayisi(self):
        return self.katilimcilar.filter_by(durum='gecti').count()
    
    @property
    def doluluk_orani(self):
        if not self.kontenjan:
            return None
        return round((self.katilimci_sayisi / self.kontenjan) * 100, 1)
    
    @property
    def durum_renk(self):
        renk_map = {
            'planli': 'info',
            'devam_ediyor': 'warning',
            'tamamlandi': 'success',
            'iptal': 'danger'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def kategori_etiket(self):
        """Kategorinin okunabilir adı ('Genel Eğitim' vb.)"""
        return EGITIM_KATEGORI_ETIKET.get(self.egitim_kategorisi or 'genel', 'Genel Eğitim')

    @property
    def kategori_renk(self):
        """Kategori badge'i için Tailwind sınıfları (yeşil / mavi / gri)"""
        renk_map = {
            'yeni_giris': 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
            'tekrar': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
        }
        return renk_map.get(self.egitim_kategorisi,
                            'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300')

    @property
    def gecmis_mi(self):
        """Eğitim tarihi geçmiş mi?"""
        if self.bitis_tarihi:
            return datetime.now() > self.bitis_tarihi
        return datetime.now() > self.baslangic_tarihi
    
    def __repr__(self):
        return f'<Egitim {self.baslik}>'


class EgitimKatilimci(db.Model, TimestampMixin):
    """Eğitim katılımcıları - Çalışanların eğitime katılım durumu"""
    __tablename__ = 'egitim_katilimcilar'
    
    id = db.Column(db.Integer, primary_key=True)
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'), nullable=False)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    
    # Katılım durumu
    durum = db.Column(db.String(20), default='davetli')  # davetli, katildi, gecti, kaldi, iptal, mazeret
    
    # Davet
    davet_tarihi = db.Column(db.DateTime, default=datetime.now)
    davet_eden_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Katılım
    katilim_tarihi = db.Column(db.DateTime)
    katilim_notu = db.Column(db.Text)  # Katılımcı hakkında not
    
    # Değerlendirme
    puan = db.Column(db.Integer)  # 0-100 arası sınav puanı
    degerlendirme = db.Column(db.Text)  # Eğitmen değerlendirmesi
    
    # Sertifika
    sertifika_no = db.Column(db.String(50))
    sertifika_tarihi = db.Column(db.Date)
    sertifika_gecerlilik = db.Column(db.Date)  # Sertifika bitiş tarihi
    
    # Mazeret
    mazeret_nedeni = db.Column(db.Text)

    # Jitsi Online Katılım Takibi
    jitsi_katilim_baslangic = db.Column(db.DateTime)
    jitsi_katilim_bitis = db.Column(db.DateTime)
    jitsi_toplam_sure = db.Column(db.Integer, default=0)  # saniye cinsinden
    jitsi_katilim_sayisi = db.Column(db.Integer, default=0)  # kaç kez girdi

    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('egitim_kayitlari', lazy='dynamic'))
    davet_eden = db.relationship('User', foreign_keys=[davet_eden_id])
    
    # Unique constraint - aynı çalışan aynı eğitime bir kez katılabilir
    __table_args__ = (
        db.UniqueConstraint('egitim_id', 'calisan_id', name='unique_egitim_katilimci'),
    )
    
    @property
    def durum_text(self):
        durum_map = {
            'davetli': 'Davetli',
            'katildi': 'Katıldı',
            'gecti': 'Başarılı',
            'kaldi': 'Başarısız',
            'iptal': 'İptal',
            'mazeret': 'Mazeretli'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        renk_map = {
            'davetli': 'info',
            'katildi': 'primary',
            'gecti': 'success',
            'kaldi': 'danger',
            'iptal': 'secondary',
            'mazeret': 'warning'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def sertifika_gecerli_mi(self):
        """Sertifika hala geçerli mi?"""
        if not self.sertifika_gecerlilik:
            return True  # Süresiz
        return date.today() <= self.sertifika_gecerlilik
    
    def __repr__(self):
        return f'<EgitimKatilimci {self.calisan_id} - {self.egitim_id}>'


class EgitimMateryali(db.Model, TimestampMixin):
    """Eğitim materyalleri - Dökümanlar, sunumlar, videolar"""
    __tablename__ = 'egitim_materyalleri'
    
    id = db.Column(db.Integer, primary_key=True)
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'), nullable=False)
    
    ad = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    materyal_tipi = db.Column(db.String(20))  # dokuman, sunum, video, link
    
    # Dosya bilgileri
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))
    dosya_boyut = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    
    # Veya harici link
    harici_link = db.Column(db.String(500))
    
    sira = db.Column(db.Integer, default=0)
    yukleyen_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    yukleyen = db.relationship('User', foreign_keys=[yukleyen_id])
    
    def __repr__(self):
        return f'<EgitimMateryali {self.ad}>'


class CalisanZorunluEgitim(db.Model, TimestampMixin):
    """Çalışanın zorunlu eğitim durumu - Pozisyon bazlı zorunlu eğitim takibi"""
    __tablename__ = 'calisan_zorunlu_egitimler'
    
    id = db.Column(db.Integer, primary_key=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    egitim_tipi_id = db.Column(db.Integer, db.ForeignKey('egitim_tipleri.id'), nullable=False)
    
    # Durum
    tamamlandi = db.Column(db.Boolean, default=False)
    tamamlanma_tarihi = db.Column(db.Date)
    son_gecerlilik = db.Column(db.Date)  # Ne zamana kadar geçerli
    
    # Hatırlatma
    hatirlatma_gonderildi = db.Column(db.Boolean, default=False)
    hatirlatma_tarihi = db.Column(db.DateTime)
    
    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('zorunlu_egitimler', lazy='dynamic'))
    egitim_tipi = db.relationship('EgitimTipi')
    
    __table_args__ = (
        db.UniqueConstraint('calisan_id', 'egitim_tipi_id', name='unique_calisan_zorunlu_egitim'),
    )
    
    @property
    def gecerli_mi(self):
        if not self.tamamlandi:
            return False
        if not self.son_gecerlilik:
            return True
        return date.today() <= self.son_gecerlilik
    
    @property
    def yenileme_gerekli_mi(self):
        """30 gün içinde yenileme gerekli mi?"""
        if not self.son_gecerlilik:
            return False
        from datetime import timedelta
        return date.today() + timedelta(days=30) >= self.son_gecerlilik
    
    def __repr__(self):
        return f'<CalisanZorunluEgitim {self.calisan_id} - {self.egitim_tipi_id}>'


# ============================================
# POZİSYON ZORUNLU EĞİTİM İLİŞKİSİ
# HedefKadro veya Pozisyon modeline eklenecek
# ============================================

class PozisyonZorunluEgitim(db.Model):
    """Pozisyon için zorunlu eğitimler"""
    __tablename__ = 'pozisyon_zorunlu_egitimler'
    
    id = db.Column(db.Integer, primary_key=True)
    pozisyon_id = db.Column(db.Integer, db.ForeignKey('pozisyonlar.id'))
    kadro_id = db.Column(db.Integer, db.ForeignKey('hedef_kadrolar.id'))  # Veya kadro bazlı
    egitim_tipi_id = db.Column(db.Integer, db.ForeignKey('egitim_tipleri.id'), nullable=False)
    
    zorunlu = db.Column(db.Boolean, default=True)
    oncelik = db.Column(db.Integer, default=1)  # İşe başlamadan önce (1) veya sonra (2)
    sure_gun = db.Column(db.Integer)  # İşe başladıktan kaç gün içinde tamamlanmalı

    egitim_tipi = db.relationship('EgitimTipi')


class EgitimKatilimLog(db.Model, TimestampMixin):
    """Online eğitime dış katılım logu (guest oturum yok - telefon eşleştirmeli).

    /egitim/katil/<id> public linkinden giren her kişi buraya loglanır.
    Telefon ile çalışan eşleşirse calisan_id, onaylı aday eşleşirse aday_id bağlanır.
    """
    __tablename__ = 'egitim_katilim_loglari'

    id = db.Column(db.Integer, primary_key=True)
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'), nullable=False, index=True)
    ad_soyad = db.Column(db.String(120), nullable=False)
    telefon = db.Column(db.String(20), nullable=False, index=True)  # normalize (son 10 hane)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))  # eşleşirse
    aday_id = db.Column(db.Integer, db.ForeignKey('adaylar.id'))        # onaylı aday eşleşirse
    giris_zamani = db.Column(db.DateTime, default=datetime.now, nullable=False)
    ayrilma_zamani = db.Column(db.DateTime)  # eğitim sonlandırılınca set edilir
    ip = db.Column(db.String(45))

    egitim = db.relationship('Egitim', backref=db.backref(
        'katilim_loglari', lazy='dynamic',
        order_by='EgitimKatilimLog.giris_zamani.desc()'))
    calisan = db.relationship('Calisan')
    aday = db.relationship('Aday')

    @property
    def kalma_suresi_dk(self):
        """Kalma süresi (dakika). Ayrılış yoksa None."""
        if not self.giris_zamani or not self.ayrilma_zamani:
            return None
        fark = (self.ayrilma_zamani - self.giris_zamani).total_seconds()
        if fark < 0:
            return 0
        return int(round(fark / 60))

    @property
    def eslesme_tipi(self):
        """Eşleşme tipi: 'Çalışan', 'Aday' veya 'Yok'."""
        if self.calisan_id:
            return 'Çalışan'
        if self.aday_id:
            return 'Aday'
        return 'Yok'

    def __repr__(self):
        return f'<EgitimKatilimLog {self.egitim_id}-{self.telefon}>'


# ============================================
# BOOKING (OTURUM / KAYIT / ANKET)
# ============================================

class EgitimOturumu(db.Model, TimestampMixin):
    """Bir eğitimin tarih/saat bazlı oturumu.

    Bir eğitimin birden fazla oturumu olabilir (farklı günler/saatler).
    Public booking sayfasında aday/çalışan bu oturumlardan birini seçip kaydolur.
    """
    __tablename__ = 'egitim_oturumlari'

    id = db.Column(db.Integer, primary_key=True)
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'), nullable=False, index=True)

    tarih = db.Column(db.Date, nullable=False)
    baslangic_saati = db.Column(db.Time, nullable=False)
    bitis_saati = db.Column(db.Time)

    kontenjan = db.Column(db.Integer, nullable=False, default=20)
    aciklama = db.Column(db.String(200))  # "Grup A", "Sabah oturumu" vb.

    # Online katılım linki (Teams / Zoom / Meet / Jitsi)
    toplanti_linki = db.Column(db.String(500))

    aktif = db.Column(db.Boolean, default=True, nullable=False)

    egitim = db.relationship('Egitim', backref=db.backref(
        'oturumlar', lazy='dynamic', cascade='all, delete-orphan',
        order_by='EgitimOturumu.tarih, EgitimOturumu.baslangic_saati'))

    @property
    def baslangic_dt(self):
        """Tarih + başlangıç saati birleşimi."""
        return datetime.combine(self.tarih, self.baslangic_saati)

    @property
    def kayit_sayisi(self):
        """Onaylı (iptal edilmemiş) kayıt sayısı."""
        return self.kayitlar.filter_by(durum='onaylandi').count()

    @property
    def kalan_kontenjan(self):
        return max(0, (self.kontenjan or 0) - self.kayit_sayisi)

    @property
    def dolu_mu(self):
        return self.kalan_kontenjan <= 0

    @property
    def gecmis_mi(self):
        return datetime.now() > self.baslangic_dt

    @property
    def kayit_alinabilir_mi(self):
        """Public booking sayfasında bu oturuma kaydolunabilir mi?"""
        return bool(self.aktif) and not self.dolu_mu and not self.gecmis_mi

    @property
    def zaman_text(self):
        s = f"{self.tarih.strftime('%d.%m.%Y')} {self.baslangic_saati.strftime('%H:%M')}"
        if self.bitis_saati:
            s += f" - {self.bitis_saati.strftime('%H:%M')}"
        return s

    def __repr__(self):
        return f'<EgitimOturumu {self.egitim_id} {self.zaman_text}>'


class EgitimKayit(db.Model, TimestampMixin):
    """Public booking kaydı - bir kişinin bir oturuma kaydı.

    Aynı kişi (telefon) aynı eğitime yalnızca bir aktif kayıt yaptırabilir;
    bu kural DB'de partial unique index ile de garanti altına alınmıştır.
    """
    __tablename__ = 'egitim_kayitlari'

    id = db.Column(db.Integer, primary_key=True)
    oturum_id = db.Column(db.Integer, db.ForeignKey('egitim_oturumlari.id'), nullable=False, index=True)
    # Mükerrer kontrolü eğitim bazında yapıldığı için denormalize tutuluyor
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'), nullable=False, index=True)

    ad_soyad = db.Column(db.String(120), nullable=False)
    telefon = db.Column(db.String(20), nullable=False, index=True)  # normalize (son 10 hane)
    email = db.Column(db.String(120))

    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))  # telefon eşleşirse
    aday_id = db.Column(db.Integer, db.ForeignKey('adaylar.id'))        # onaylı aday eşleşirse

    kayit_zamani = db.Column(db.DateTime, default=datetime.now, nullable=False)
    durum = db.Column(db.String(20), default='onaylandi', nullable=False)  # onaylandi, iptal
    iptal_zamani = db.Column(db.DateTime)
    iptal_eden = db.Column(db.String(20))  # katilimci, ik

    # Public onay/iptal/anket linkleri için
    token = db.Column(db.String(64), unique=True, nullable=False, index=True, default=_kayit_token)

    sms_gonderildi = db.Column(db.Boolean, default=False)
    ip = db.Column(db.String(45))

    oturum = db.relationship('EgitimOturumu', backref=db.backref(
        'kayitlar', lazy='dynamic', cascade='all, delete-orphan'))
    egitim = db.relationship('Egitim', backref=db.backref('kayitlar', lazy='dynamic'))
    calisan = db.relationship('Calisan')
    aday = db.relationship('Aday')

    __table_args__ = (
        # Aynı eğitime aynı telefondan yalnızca bir AKTİF kayıt (iptal edilenler hariç)
        db.Index('uq_egitim_kayit_aktif', 'egitim_id', 'telefon',
                 unique=True, postgresql_where=db.text("durum = 'onaylandi'")),
    )

    @property
    def eslesme_tipi(self):
        if self.calisan_id:
            return 'Çalışan'
        if self.aday_id:
            return 'Aday'
        return 'Yok'

    @property
    def iptal_edilebilir_mi(self):
        """Oturum başlamadan önce katılımcı kendi kaydını iptal edebilir."""
        return self.durum == 'onaylandi' and self.oturum is not None and not self.oturum.gecmis_mi

    def __repr__(self):
        return f'<EgitimKayit {self.egitim_id}-{self.telefon} {self.durum}>'


class EgitimDavetSms(db.Model, TimestampMixin):
    """Eğitim davet SMS gönderim logu.

    Hem otomatik (aday onaylandığında) hem manuel (toplu davet ekranı)
    gönderimler buraya yazılır. Aynı kişiye tekrar SMS gönderilmesini
    engellemek/uyarmak ve "davet edilenler" listesini üretmek için kullanılır.
    """
    __tablename__ = 'egitim_davet_smsleri'

    id = db.Column(db.Integer, primary_key=True)
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'), nullable=False, index=True)

    aday_id = db.Column(db.Integer, db.ForeignKey('adaylar.id'), index=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), index=True)

    ad_soyad = db.Column(db.String(120))
    telefon = db.Column(db.String(20))  # normalize edilmiş (05XXXXXXXXX)

    basarili = db.Column(db.Boolean, default=False, nullable=False)
    hata = db.Column(db.String(255))

    kaynak = db.Column(db.String(20), default='manuel', nullable=False)  # otomatik, manuel
    gonderen_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # manuel gönderimde kullanıcı
    gonderim_zamani = db.Column(db.DateTime, default=datetime.now, nullable=False)

    egitim = db.relationship('Egitim', backref=db.backref(
        'davet_smsleri', lazy='dynamic',
        order_by='EgitimDavetSms.gonderim_zamani.desc()'))
    aday = db.relationship('Aday')
    calisan = db.relationship('Calisan')
    gonderen = db.relationship('User', foreign_keys=[gonderen_id])

    @property
    def kaynak_text(self):
        return 'Otomatik' if self.kaynak == 'otomatik' else 'Manuel'

    def __repr__(self):
        return f'<EgitimDavetSms {self.egitim_id}-{self.telefon} {"OK" if self.basarili else "HATA"}>'


def davet_sms_gonderildi_mi(egitim_id, aday_id=None, calisan_id=None, telefon=None):
    """Bu eğitim için kişiye daha önce BAŞARILI davet SMS'i gitmiş mi?

    aday_id / calisan_id / telefon'dan verilenlerin herhangi biri eşleşirse
    True döner (aday çalışana dönüştüğünde de mükerrer gönderim olmasın diye).
    """
    kosullar = []
    if aday_id:
        kosullar.append(EgitimDavetSms.aday_id == aday_id)
    if calisan_id:
        kosullar.append(EgitimDavetSms.calisan_id == calisan_id)
    if telefon:
        kosullar.append(EgitimDavetSms.telefon == telefon)
    if not kosullar:
        return False
    return db.session.query(
        EgitimDavetSms.query.filter(
            EgitimDavetSms.egitim_id == egitim_id,
            EgitimDavetSms.basarili == True,  # noqa: E712
            db.or_(*kosullar),
        ).exists()
    ).scalar()


class EgitimAnket(db.Model, TimestampMixin):
    """Eğitim sonrası memnuniyet anketi (kayıt başına en fazla bir yanıt)."""
    __tablename__ = 'egitim_anketleri'

    id = db.Column(db.Integer, primary_key=True)
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'), nullable=False, index=True)
    oturum_id = db.Column(db.Integer, db.ForeignKey('egitim_oturumlari.id'))
    kayit_id = db.Column(db.Integer, db.ForeignKey('egitim_kayitlari.id'), unique=True)

    puan = db.Column(db.Integer, nullable=False)   # Genel memnuniyet 1-5
    egitmen_puan = db.Column(db.Integer)           # Eğitmen 1-5
    icerik_puan = db.Column(db.Integer)            # İçerik 1-5
    yorum = db.Column(db.Text)
    ip = db.Column(db.String(45))

    egitim = db.relationship('Egitim', backref=db.backref('anketler', lazy='dynamic'))
    oturum = db.relationship('EgitimOturumu')
    kayit = db.relationship('EgitimKayit', backref=db.backref('anket', uselist=False))

    def __repr__(self):
        return f'<EgitimAnket {self.egitim_id} puan={self.puan}>'
