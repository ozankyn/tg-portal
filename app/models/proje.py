# -*- coding: utf-8 -*-
"""
TG Portal - Proje Modelleri
Müşteri, Proje, Hedef Kadro
"""

from datetime import datetime
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class Musteri(db.Model, TimestampMixin, SoftDeleteMixin):
    """Müşteri - Şirketin hizmet verdiği firmalar"""
    __tablename__ = 'musteriler'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(200), nullable=False)
    kisa_ad = db.Column(db.String(50))  # Migros, Efes vb.
    vergi_no = db.Column(db.String(11))
    vergi_dairesi = db.Column(db.String(100))
    
    # İletişim
    adres = db.Column(db.Text)
    il = db.Column(db.String(50))
    ilce = db.Column(db.String(50))
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(120))
    web = db.Column(db.String(200))
    
    # Yetkili
    yetkili_ad = db.Column(db.String(100))
    yetkili_telefon = db.Column(db.String(20))
    yetkili_email = db.Column(db.String(120))
    
    # Durum
    aktif = db.Column(db.Boolean, default=True)
    notlar = db.Column(db.Text)
    
    # İlişkiler
    projeler = db.relationship('Proje', back_populates='musteri', lazy='dynamic')
    
    @property
    def display_name(self):
        return self.kisa_ad or self.ad
    
    @property
    def aktif_proje_sayisi(self):
        return self.projeler.filter_by(is_deleted=False, aktif=True).count()
    
    def to_dict(self):
        return {
            'id': self.id,
            'ad': self.ad,
            'kisa_ad': self.kisa_ad,
            'il': self.il,
            'aktif': self.aktif
        }
    
    def __repr__(self):
        return f'<Musteri {self.display_name}>'


class Proje(db.Model, TimestampMixin, SoftDeleteMixin):
    """Proje - Müşteriye bağlı projeler"""
    __tablename__ = 'projeler'
    
    id = db.Column(db.Integer, primary_key=True)
    musteri_id = db.Column(db.Integer, db.ForeignKey('musteriler.id'), nullable=False)
    
    ad = db.Column(db.String(200), nullable=False)
    kod = db.Column(db.String(50))  # PRJ-001
    aciklama = db.Column(db.Text)
    
    # Tarihler
    baslangic_tarihi = db.Column(db.Date)
    bitis_tarihi = db.Column(db.Date)
    
    # Durum
    aktif = db.Column(db.Boolean, default=True)
    durum = db.Column(db.String(20), default='aktif')  # aktif, tamamlandi, askida, iptal
    
    # Bütçe
    butce = db.Column(db.Numeric(12, 2))
    para_birimi = db.Column(db.String(3), default='TRY')
    
    notlar = db.Column(db.Text)
    
    # İlişkiler
    musteri = db.relationship('Musteri', back_populates='projeler')
    kadrolar = db.relationship('HedefKadro', back_populates='proje', lazy='dynamic')
    araclar = db.relationship('Arac', backref='proje', lazy='dynamic')
    
    @property
    def toplam_kadro(self):
        """Toplam hedef kadro sayısı"""
        return db.session.query(db.func.sum(HedefKadro.hedef_sayi)).filter(
            HedefKadro.proje_id == self.id,
            HedefKadro.is_deleted == False
        ).scalar() or 0
    
    @property
    def mevcut_calisan(self):
        """Projede çalışan sayısı"""
        from app.models.ik import Calisan
        from app.models.base import CalisanDurumu
        return Calisan.query.join(HedefKadro).filter(
            HedefKadro.proje_id == self.id,
            Calisan.is_deleted == False,
            Calisan.durum.in_([CalisanDurumu.AKTIF, CalisanDurumu.IZINLI])
        ).count()
    
    @property
    def doluluk_orani(self):
        if self.toplam_kadro == 0:
            return 0
        return round((self.mevcut_calisan / self.toplam_kadro) * 100, 1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ad': self.ad,
            'kod': self.kod,
            'musteri': self.musteri.display_name if self.musteri else None,
            'aktif': self.aktif,
            'doluluk_orani': self.doluluk_orani
        }
    
    def __repr__(self):
        return f'<Proje {self.ad}>'


class HedefKadro(db.Model, TimestampMixin, SoftDeleteMixin):
    """Hedef Kadro - Proje içindeki pozisyon/kadro tanımları"""
    __tablename__ = 'hedef_kadrolar'
    
    id = db.Column(db.Integer, primary_key=True)
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'), nullable=False)
    
    # Kadro bilgileri
    pozisyon_adi = db.Column(db.String(100), nullable=False)  # Saha Satış Temsilcisi
    departman = db.Column(db.String(100))  # Satış, Operasyon
    
    # Lokasyon
    il = db.Column(db.String(50))
    ilce = db.Column(db.String(50))
    bolge = db.Column(db.String(100))  # Marmara, Ege vb.
    
    # Sayılar
    hedef_sayi = db.Column(db.Integer, default=1)  # Kaç kişi alınacak
    oncelik = db.Column(db.Integer, default=5)  # 1-10, 1 en acil
    
    # Gereksinimler
    min_tecrube_yil = db.Column(db.Integer, default=0)
    egitim_seviyesi = db.Column(db.String(50))  # lise, universite, yuksek_lisans
    ehliyet_gerekli = db.Column(db.Boolean, default=False)
    ehliyet_sinifi = db.Column(db.String(10))  # B, A2
    cinsiyet_tercihi = db.Column(db.String(20))  # erkek, kadin, farketmez
    yas_min = db.Column(db.Integer)
    yas_max = db.Column(db.Integer)
    
    # Maaş
    maas_min = db.Column(db.Numeric(10, 2))
    maas_max = db.Column(db.Numeric(10, 2))
    
    # Durum
    aktif = db.Column(db.Boolean, default=True)
    notlar = db.Column(db.Text)
    
    # İlişkiler
    proje = db.relationship('Proje', back_populates='kadrolar')
    adaylar = db.relationship('Aday', backref='kadro', lazy='dynamic')
    calisanlar = db.relationship('Calisan', backref='kadro', lazy='dynamic')
    
    @property
    def mevcut_sayi(self):
        """Kadroda çalışan sayısı"""
        from app.models.ik import Calisan
        from app.models.base import CalisanDurumu
        return self.calisanlar.filter(
            Calisan.is_deleted == False,
            Calisan.durum.in_([CalisanDurumu.AKTIF, CalisanDurumu.IZINLI])
        ).count()
    
    @property
    def eksik_sayi(self):
        return max(0, self.hedef_sayi - self.mevcut_sayi)
    
    @property
    def bekleyen_aday_sayisi(self):
        from app.models.ik import Aday
        return self.adaylar.filter(
            Aday.is_deleted == False,
            Aday.durum.in_(['basvurdu', 'degerlendiriliyor', 'mulakat'])
        ).count()
    
    @property
    def doluluk_orani(self):
        if self.hedef_sayi == 0:
            return 100
        return round((self.mevcut_sayi / self.hedef_sayi) * 100, 1)
    
    @property
    def full_title(self):
        """Pozisyon - İl şeklinde"""
        parts = [self.pozisyon_adi]
        if self.il:
            parts.append(self.il)
        return ' - '.join(parts)
    
    def to_dict(self):
        return {
            'id': self.id,
            'pozisyon_adi': self.pozisyon_adi,
            'il': self.il,
            'hedef_sayi': self.hedef_sayi,
            'mevcut_sayi': self.mevcut_sayi,
            'eksik_sayi': self.eksik_sayi,
            'doluluk_orani': self.doluluk_orani,
            'proje': self.proje.ad if self.proje else None
        }
    
    def __repr__(self):
        return f'<HedefKadro {self.pozisyon_adi} - {self.il}>'