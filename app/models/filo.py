# -*- coding: utf-8 -*-
"""
TG Portal - Filo (Fleet Management) Models
"""

from datetime import datetime, date
from app import db
from app.models.base import (TimestampMixin, SoftDeleteMixin, AuditMixin, 
                              AracDurumu, YakitTipi, IslemTipi)


class Arac(db.Model, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Araç modeli"""
    __tablename__ = 'araclar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Temel Bilgiler
    plaka = db.Column(db.String(20), unique=True, nullable=False)
    marka = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50))
    model_yili = db.Column(db.Integer)
    renk = db.Column(db.String(30))
    
    # Teknik Bilgiler
    sasi_no = db.Column(db.String(50), unique=True)
    motor_no = db.Column(db.String(50))
    yakit_tipi = db.Column(db.Enum(YakitTipi), default=YakitTipi.DIZEL)
    motor_hacmi = db.Column(db.Integer)  # cc
    vites_tipi = db.Column(db.String(20))  # manuel, otomatik
    
    # Kilometre
    km = db.Column(db.Integer, default=0)
    son_km_guncelleme = db.Column(db.DateTime)
    
    # Sahiplik
    sahiplik_tipi = db.Column(db.String(20))  # sirket, kiralama, leasing
    kira_baslangic = db.Column(db.Date)
    kira_bitis = db.Column(db.Date)
    aylik_kira = db.Column(db.Numeric(12, 2))
    
    # Atama
    atanan_calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))
    atama_tarihi = db.Column(db.Date)
    
    # Durum
    durum = db.Column(db.Enum(AracDurumu), default=AracDurumu.AKTIF)
    konum = db.Column(db.String(200))  # Son bilinen konum
    notlar = db.Column(db.Text)
    
    # İlişkiler
    atanan_calisan = db.relationship('Calisan', backref='araclar')
    islemler = db.relationship('FiloIslem', backref='arac', lazy='dynamic')
    yakit_kayitlari = db.relationship('YakitKayit', backref='arac', lazy='dynamic')
    sigortalar = db.relationship('Sigorta', backref='arac', lazy='dynamic')
    muayeneler = db.relationship('Muayene', backref='arac', lazy='dynamic')
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'))

    
    def __repr__(self):
        return f'<Arac {self.plaka}>'
    
    @property
    def display_name(self):
        return f'{self.plaka} - {self.marka} {self.model}'
    
    @property
    def aktif_sigorta(self):
        """Geçerli sigortayı döndürür"""
        today = date.today()
        return self.sigortalar.filter(
            Sigorta.bitis >= today,
            Sigorta.iptal == False
        ).first()
    
    @property
    def muayene_gecerli(self):
        """Muayene geçerli mi kontrol eder"""
        today = date.today()
        son_muayene = self.muayeneler.order_by(Muayene.tarih.desc()).first()
        if son_muayene and son_muayene.sonraki_muayene:
            return son_muayene.sonraki_muayene >= today
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'plaka': self.plaka,
            'marka': self.marka,
            'model': self.model,
            'model_yili': self.model_yili,
            'km': self.km,
            'durum': self.durum.value if self.durum else None,
            'atanan': self.atanan_calisan.full_name if self.atanan_calisan else None
        }


class FiloIslem(db.Model, TimestampMixin, AuditMixin):
    """Araç işlemleri (bakım, tamir, vb.)"""
    __tablename__ = 'filo_islemler'
    
    id = db.Column(db.Integer, primary_key=True)
    arac_id = db.Column(db.Integer, db.ForeignKey('araclar.id'), nullable=False)
    
    # İşlem Bilgileri
    islem_tipi = db.Column(db.Enum(IslemTipi), nullable=False)
    tarih = db.Column(db.Date, nullable=False)
    km = db.Column(db.Integer)
    
    # Tedarikçi
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'))
    
    # Maliyet
    tutar = db.Column(db.Numeric(12, 2))
    kdv = db.Column(db.Numeric(12, 2))
    toplam = db.Column(db.Numeric(12, 2))
    
    # Detaylar
    aciklama = db.Column(db.Text)
    fatura_no = db.Column(db.String(50))
    belge_yolu = db.Column(db.String(500))
    
    # Hatırlatma
    sonraki_tarih = db.Column(db.Date)
    sonraki_km = db.Column(db.Integer)
    
    # İlişkiler
    tedarikci = db.relationship('Tedarikci', back_populates='filo_islemleri')
    
    
    def __repr__(self):
        return f'<FiloIslem {self.islem_tipi} {self.arac_id}>'


class YakitKayit(db.Model, TimestampMixin):
    """Yakıt alım kayıtları"""
    __tablename__ = 'yakit_kayitlari'
    
    id = db.Column(db.Integer, primary_key=True)
    arac_id = db.Column(db.Integer, db.ForeignKey('araclar.id'), nullable=False)
    
    tarih = db.Column(db.DateTime, nullable=False)
    km = db.Column(db.Integer, nullable=False)
    
    # Yakıt Detayları
    yakit_tipi = db.Column(db.Enum(YakitTipi))
    litre = db.Column(db.Numeric(8, 2))
    birim_fiyat = db.Column(db.Numeric(8, 2))
    tutar = db.Column(db.Numeric(12, 2))
    
    # İstasyon
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'))
    istasyon_adi = db.Column(db.String(100))
    
    # Full depo mu?
    full_depo = db.Column(db.Boolean, default=True)
    
    # Hesaplama
    onceki_km = db.Column(db.Integer)
    tuketim = db.Column(db.Numeric(5, 2))  # lt/100km
    
    tedarikci = db.relationship('Tedarikci', backref='yakit_kayitlari')
    
    def __repr__(self):
        return f'<YakitKayit {self.arac_id} {self.tarih}>'


class Sigorta(db.Model, TimestampMixin):
    """Araç sigortaları"""
    __tablename__ = 'sigortalar'
    
    id = db.Column(db.Integer, primary_key=True)
    arac_id = db.Column(db.Integer, db.ForeignKey('araclar.id'), nullable=False)
    
    sigorta_tipi = db.Column(db.String(50))  # kasko, trafik, ihtiyari
    sirket = db.Column(db.String(100))
    police_no = db.Column(db.String(50))
    
    baslangic = db.Column(db.Date, nullable=False)
    bitis = db.Column(db.Date, nullable=False)
    
    prim = db.Column(db.Numeric(12, 2))
    taksit_sayisi = db.Column(db.Integer, default=1)
    
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'))
    iptal = db.Column(db.Boolean, default=False)
    notlar = db.Column(db.Text)
    
    tedarikci = db.relationship('Tedarikci', backref='sigortalar')
    
    def __repr__(self):
        return f'<Sigorta {self.sigorta_tipi} {self.arac_id}>'
    
    @property
    def gecerli_mi(self):
        return not self.iptal and self.bitis >= date.today()


class Muayene(db.Model, TimestampMixin):
    """Araç muayene kayıtları"""
    __tablename__ = 'muayeneler'
    
    id = db.Column(db.Integer, primary_key=True)
    arac_id = db.Column(db.Integer, db.ForeignKey('araclar.id'), nullable=False)
    
    tarih = db.Column(db.Date, nullable=False)
    km = db.Column(db.Integer)
    
    sonuc = db.Column(db.String(20))  # gecti, kaldi, sartli_gecti
    sonraki_muayene = db.Column(db.Date)
    
    istasyon = db.Column(db.String(100))
    tutar = db.Column(db.Numeric(12, 2))
    notlar = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Muayene {self.arac_id} {self.tarih}>'


class Kaza(db.Model, TimestampMixin, AuditMixin):
    """Kaza kayıtları"""
    __tablename__ = 'kazalar'
    
    id = db.Column(db.Integer, primary_key=True)
    arac_id = db.Column(db.Integer, db.ForeignKey('araclar.id'), nullable=False)
    surucu_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))
    
    tarih = db.Column(db.DateTime, nullable=False)
    konum = db.Column(db.String(200))
    
    # Detaylar
    kusur_orani = db.Column(db.Integer)  # % olarak
    hasar_tutari = db.Column(db.Numeric(12, 2))
    sigorta_karsiladi = db.Column(db.Numeric(12, 2))
    
    yaralanma = db.Column(db.Boolean, default=False)
    aciklama = db.Column(db.Text)
    
    # Belgeler
    tutanak_no = db.Column(db.String(50))
    belge_yolu = db.Column(db.String(500))
    
    # Durum
    durum = db.Column(db.String(50), default='acik')  # acik, kapandi, dava
    
    # Onay sistemi
    onay_durumu = db.Column(db.String(20), default='bekliyor')  # bekliyor, onaylandi, reddedildi
    onaylayan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    onay_tarihi = db.Column(db.DateTime)
    red_nedeni = db.Column(db.Text)
    
    # İlişkiler
    arac = db.relationship('Arac', backref='kazalar')
    surucu = db.relationship('Calisan', backref='kazalar')
    onaylayan = db.relationship('User', foreign_keys=[onaylayan_id], backref='onayladigi_kazalar')
    fotograflar = db.relationship('KazaFotograf', backref='kaza', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Kaza {self.arac_id} {self.tarih}>'
