# -*- coding: utf-8 -*-
"""
TG Portal - İK (Human Resources) Models
"""

from datetime import datetime, date
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


class Aday(db.Model, TimestampMixin, SoftDeleteMixin):
    """İş başvuru adayları"""
    __tablename__ = 'adaylar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Kişisel
    ad = db.Column(db.String(50), nullable=False)
    soyad = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    telefon = db.Column(db.String(20))
    
    # Başvuru
    pozisyon_id = db.Column(db.Integer, db.ForeignKey('pozisyonlar.id'))
    kadro_id = db.Column(db.Integer, db.ForeignKey('hedef_kadrolar.id'))
    basvuru_tarihi = db.Column(db.Date, default=date.today)
    kaynak = db.Column(db.String(50))  # kariyer_net, linkedin, referans, website
    
    # Durum
    durum = db.Column(db.String(30), default='basvurdu')  # basvurdu, degerlendiriliyor, mulakat, teklif, ise_alindi, red
    
    # CV ve Notlar
    cv_yolu = db.Column(db.String(500))
    notlar = db.Column(db.Text)
    
    # Değerlendirme
    degerlendirme_puani = db.Column(db.Integer)
    degerlendirme_notu = db.Column(db.Text)
    
    # İlişkiler
    pozisyon = db.relationship('Pozisyon', backref='adaylar')
    
    def __repr__(self):
        return f'<Aday {self.full_name}>'
    
    @property
    def full_name(self):
        return f'{self.ad} {self.soyad}'


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
