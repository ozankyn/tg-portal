# -*- coding: utf-8 -*-
"""
TG Portal - Haftalık Çalışma Beyanı Modelleri

Çalışanların hafta sonu (Cuma-Cumartesi-Pazar) çalışma günlerini
public link + SMS OTP doğrulaması ile beyan etmesini sağlar.

İlk kullanım: Proje 12. Model proje bağımsızdır, sonradan genelleştirilebilir.
"""

import secrets
from datetime import datetime

from app import db
from app.models.base import TimestampMixin


class HaftalikBeyan(db.Model, TimestampMixin):
    """Bir proje için belirli bir hafta sonuna (Cuma-Pazar) açılan beyan formu."""
    __tablename__ = 'haftalik_beyanlar'

    id = db.Column(db.Integer, primary_key=True)
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'), nullable=False)

    hafta_baslangic = db.Column(db.Date, nullable=False)  # Cuma
    hafta_bitis = db.Column(db.Date, nullable=False)       # Pazar

    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    aktif = db.Column(db.Boolean, default=True)  # False -> form kapalı, beyan alınmaz

    # İlişkiler
    proje = db.relationship('Proje')
    olusturan = db.relationship('User')
    kayitlar = db.relationship('BeyanKayit', backref='beyan', lazy='dynamic',
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<HaftalikBeyan proje={self.proje_id} {self.hafta_baslangic}>'

    @property
    def baslik(self):
        b = self.hafta_baslangic.strftime('%d.%m.%Y') if self.hafta_baslangic else '-'
        s = self.hafta_bitis.strftime('%d.%m.%Y') if self.hafta_bitis else '-'
        return f'{b} - {s}'

    @property
    def gun_sayaclari(self):
        """Gün bazında kaç kişinin çalışacağını döndürür."""
        from sqlalchemy import func
        row = db.session.query(
            func.count(BeyanKayit.id).label('toplam'),
            func.sum(db.cast(BeyanKayit.cuma, db.Integer)).label('cuma'),
            func.sum(db.cast(BeyanKayit.cumartesi, db.Integer)).label('cumartesi'),
            func.sum(db.cast(BeyanKayit.pazar, db.Integer)).label('pazar'),
        ).filter(BeyanKayit.beyan_id == self.id).one()
        return {
            'toplam': row.toplam or 0,
            'cuma': int(row.cuma or 0),
            'cumartesi': int(row.cumartesi or 0),
            'pazar': int(row.pazar or 0),
        }


class BeyanKayit(db.Model, TimestampMixin):
    """Bir çalışanın belirli bir haftalık beyan için verdiği çalışma günü seçimi."""
    __tablename__ = 'beyan_kayitlari'

    id = db.Column(db.Integer, primary_key=True)
    beyan_id = db.Column(db.Integer, db.ForeignKey('haftalik_beyanlar.id'), nullable=False)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))

    telefon = db.Column(db.String(20))
    ad_soyad = db.Column(db.String(200))

    cuma = db.Column(db.Boolean, default=False)
    cumartesi = db.Column(db.Boolean, default=False)
    pazar = db.Column(db.Boolean, default=False)

    token = db.Column(db.String(64), unique=True, index=True)
    kayit_zamani = db.Column(db.DateTime)
    ip = db.Column(db.String(200))  # IPv6 + proxy zinciri için geniş

    # İlişkiler
    calisan = db.relationship('Calisan')

    # Aynı çalışan aynı beyanda tek kayıt (tekrar girişte güncellenir)
    __table_args__ = (
        db.UniqueConstraint('beyan_id', 'calisan_id', name='uq_beyan_calisan'),
    )

    def __repr__(self):
        return f'<BeyanKayit beyan={self.beyan_id} {self.ad_soyad}>'

    def generate_token(self):
        self.token = secrets.token_urlsafe(32)
        return self.token

    @property
    def gun_sayisi(self):
        return sum([bool(self.cuma), bool(self.cumartesi), bool(self.pazar)])

    @property
    def secilen_gunler(self):
        gunler = []
        if self.cuma:
            gunler.append('Cuma')
        if self.cumartesi:
            gunler.append('Cumartesi')
        if self.pazar:
            gunler.append('Pazar')
        return gunler
