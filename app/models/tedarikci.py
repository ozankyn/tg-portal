# -*- coding: utf-8 -*-
"""
TG Portal - Tedarikçi (Supplier) Models
Generic modül - tüm diğer modüller tarafından kullanılabilir
"""

from datetime import datetime
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin, AuditMixin, TedarikciTipi


class Tedarikci(db.Model, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    Generic Tedarikçi Modeli
    
    Tüm modüller tarafından kullanılabilir:
    - Filo: Servis, yakıt istasyonu, sigorta şirketi
    - Masraf: Genel tedarikçiler
    - Envanter: Ekipman tedarikçileri
    """
    __tablename__ = 'tedarikciler'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Temel Bilgiler
    unvan = db.Column(db.String(200), nullable=False)  # Resmi Şirket Unvanı
    kisa_ad = db.Column(db.String(50))  # Kullanım/Kısa Adı
    
    # Vergi Bilgileri
    vergi_no = db.Column(db.String(11), unique=True)
    vergi_dairesi = db.Column(db.String(100))
    
    # Kategori
    tip = db.Column(db.Enum(TedarikciTipi), default=TedarikciTipi.GENEL)
    alt_kategori = db.Column(db.String(100))  # Daha detaylı kategori
    
    # İletişim Bilgileri
    adres = db.Column(db.Text)
    il = db.Column(db.String(50))
    ilce = db.Column(db.String(50))
    posta_kodu = db.Column(db.String(10))
    
    telefon = db.Column(db.String(20))
    telefon_2 = db.Column(db.String(20))
    fax = db.Column(db.String(20))
    email = db.Column(db.String(100))
    web = db.Column(db.String(200))
    
    # Yetkili Kişi
    yetkili_adi = db.Column(db.String(100))
    yetkili_unvan = db.Column(db.String(100))
    yetkili_telefon = db.Column(db.String(20))
    yetkili_email = db.Column(db.String(100))
    
    # Banka Bilgileri
    banka_adi = db.Column(db.String(100))
    sube = db.Column(db.String(100))
    iban = db.Column(db.String(34))
    hesap_no = db.Column(db.String(30))
    
    # Ödeme Koşulları
    odeme_vade = db.Column(db.Integer, default=30)  # Gün
    odeme_yontemi = db.Column(db.String(50))  # havale, cek, kredi_karti, nakit
    iskonto_orani = db.Column(db.Numeric(5, 2))  # % olarak
    
    # Değerlendirme
    puan = db.Column(db.Integer)  # 1-10 arası
    oncelik = db.Column(db.Integer, default=5)  # 1-10 arası
    
    # Durum
    aktif = db.Column(db.Boolean, default=True)
    notlar = db.Column(db.Text)
    
    # Sözleşme
    sozlesme_baslangic = db.Column(db.Date)
    sozlesme_bitis = db.Column(db.Date)
    sozlesme_dosya = db.Column(db.String(500))
    
    # İlişkiler - Diğer modüllerden referanslar
    filo_islemleri = db.relationship('FiloIslem', back_populates='tedarikci', lazy='dynamic')
    # masraflar = db.relationship('Masraf', back_populates='tedarikci', lazy='dynamic')  # Masraf modülü eklenince
    
    def __repr__(self):
        return f'<Tedarikci {self.kisa_ad or self.unvan}>'
    
    @property
    def display_name(self):
        return self.kisa_ad or self.unvan
    
    @property
    def tip_display(self):
        return self.tip.value.replace('_', ' ').title() if self.tip else '-'
    
    def to_dict(self):
        return {
            'id': self.id,
            'unvan': self.unvan,
            'kisa_ad': self.kisa_ad,
            'display_name': self.display_name,
            'vergi_no': self.vergi_no,
            'tip': self.tip.value if self.tip else None,
            'tip_display': self.tip_display,
            'il': self.il,
            'telefon': self.telefon,
            'email': self.email,
            'yetkili_adi': self.yetkili_adi,
            'aktif': self.aktif
        }
    
    def to_dict_full(self):
        """Tüm alanlarla birlikte"""
        data = self.to_dict()
        data.update({
            'vergi_dairesi': self.vergi_dairesi,
            'adres': self.adres,
            'ilce': self.ilce,
            'telefon_2': self.telefon_2,
            'fax': self.fax,
            'web': self.web,
            'yetkili_unvan': self.yetkili_unvan,
            'yetkili_telefon': self.yetkili_telefon,
            'yetkili_email': self.yetkili_email,
            'banka_adi': self.banka_adi,
            'iban': self.iban,
            'odeme_vade': self.odeme_vade,
            'odeme_yontemi': self.odeme_yontemi,
            'puan': self.puan,
            'notlar': self.notlar,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        })
        return data


class TedarikciIletisim(db.Model, TimestampMixin):
    """Tedarikçi ek iletişim kişileri"""
    __tablename__ = 'tedarikci_iletisimler'
    
    id = db.Column(db.Integer, primary_key=True)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'), nullable=False)
    
    ad_soyad = db.Column(db.String(100), nullable=False)
    unvan = db.Column(db.String(100))
    departman = db.Column(db.String(100))
    telefon = db.Column(db.String(20))
    dahili = db.Column(db.String(10))
    email = db.Column(db.String(100))
    birincil = db.Column(db.Boolean, default=False)
    notlar = db.Column(db.Text)
    
    tedarikci = db.relationship('Tedarikci', backref='iletisim_kisileri')
    
    def __repr__(self):
        return f'<TedarikciIletisim {self.ad_soyad}>'


class TedarikciDegerlendirme(db.Model, TimestampMixin):
    """Tedarikçi performans değerlendirmeleri"""
    __tablename__ = 'tedarikci_degerlendirmeler'
    
    id = db.Column(db.Integer, primary_key=True)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'), nullable=False)
    degerlendiren_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    tarih = db.Column(db.Date, nullable=False)
    donem = db.Column(db.String(20))  # 2024-Q1, 2024-01, vb.
    
    # Puanlama (1-10)
    kalite_puani = db.Column(db.Integer)
    teslimat_puani = db.Column(db.Integer)
    fiyat_puani = db.Column(db.Integer)
    iletisim_puani = db.Column(db.Integer)
    genel_puan = db.Column(db.Integer)
    
    guclu_yonler = db.Column(db.Text)
    gelistirme_alanlari = db.Column(db.Text)
    notlar = db.Column(db.Text)
    
    tedarikci = db.relationship('Tedarikci', backref='degerlendirmeler')
    degerlendiren = db.relationship('User', backref='tedarikci_degerlendirmeleri')
    
    def __repr__(self):
        return f'<TedarikciDegerlendirme {self.tedarikci_id} {self.donem}>'
