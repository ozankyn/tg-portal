# -*- coding: utf-8 -*-
"""
Şirket / Tüzel Kişi ve SGK Dosya Modelleri
"""

from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class TuzelKisi(db.Model, TimestampMixin, SoftDeleteMixin):
    """Tüzel Kişi / Şirket"""
    __tablename__ = 'tuzel_kisiler'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(200), nullable=False)  # Şirket unvanı
    kisa_ad = db.Column(db.String(50))  # Kısa ad
    vergi_no = db.Column(db.String(11))
    vergi_dairesi = db.Column(db.String(100))
    mersis_no = db.Column(db.String(20))
    adres = db.Column(db.Text)
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(120))
    aktif = db.Column(db.Boolean, default=True)
    
    # İlişkiler
    sgk_dosyalari = db.relationship('SgkDosya', backref='tuzel_kisi', lazy='dynamic')
    
    def __repr__(self):
        return f'<TuzelKisi {self.kisa_ad or self.ad}>'
    
    @property
    def display_name(self):
        return self.kisa_ad or self.ad


class SgkDosya(db.Model, TimestampMixin, SoftDeleteMixin):
    """SGK Dosyası"""
    __tablename__ = 'sgk_dosyalari'
    
    id = db.Column(db.Integer, primary_key=True)
    tuzel_kisi_id = db.Column(db.Integer, db.ForeignKey('tuzel_kisiler.id'), nullable=False)
    dosya_no = db.Column(db.String(30), nullable=False)  # SGK işyeri sicil no
    ad = db.Column(db.String(200))  # Dosya adı/açıklaması
    il = db.Column(db.String(50))
    ilce = db.Column(db.String(50))
    tehlike_sinifi = db.Column(db.String(20))  # Az tehlikeli, tehlikeli, çok tehlikeli
    aktif = db.Column(db.Boolean, default=True)
    
    # İlişkiler
    calisanlar = db.relationship('Calisan', backref='sgk_dosya', lazy='dynamic')
    
    def __repr__(self):
        return f'<SgkDosya {self.dosya_no}>'
    
    @property
    def display_name(self):
        return f"{self.dosya_no} - {self.ad}" if self.ad else self.dosya_no
