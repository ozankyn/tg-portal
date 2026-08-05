# -*- coding: utf-8 -*-
"""
TG Portal - Arkadaşını Davet Et (Referans) Modelleri

Saha çalışanları SMS ile gelen public linke girip telefonunu OTP ile
doğruladıktan sonra tanıdıklarını referans olarak bırakır. İK/koordinatör
bu referansları arayıp durumunu günceller.

Link proje bazlıdır (ReferansLink): projedeki her çalışan aynı linki kullanır,
kim olduğu telefon doğrulaması ile belirlenir. Böylece toplu SMS'te kişi başına
ayrı token üretmek gerekmez.
"""

import secrets
from datetime import datetime

from app import db
from app.models.base import TimestampMixin


# Referans durumları: kod -> (etiket, tailwind renk sınıfları)
REFERANS_DURUMLARI = {
    'yeni': ('Yeni', 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'),
    'arandi': ('Arandı', 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400'),
    'ulasilamadi': ('Ulaşılamadı', 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'),
    'basvurdu': ('Başvurdu', 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'),
    'reddedildi': ('Reddedildi', 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400'),
}


class ReferansLink(db.Model, TimestampMixin):
    """Bir projenin public referans linki (proje başına tek token)."""
    __tablename__ = 'referans_linkleri'

    id = db.Column(db.Integer, primary_key=True)
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'),
                         nullable=False, unique=True)
    token = db.Column(db.String(64), unique=True, index=True, nullable=False)

    aktif = db.Column(db.Boolean, default=True, nullable=False)  # False -> form kapalı
    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # İlişkiler
    proje = db.relationship('Proje')
    olusturan = db.relationship('User')

    def __repr__(self):
        return f'<ReferansLink proje={self.proje_id}>'

    @staticmethod
    def uret_token():
        return secrets.token_urlsafe(16)

    @classmethod
    def proje_icin(cls, proje_id, olusturan_id=None):
        """Projenin linkini döndürür; yoksa oluşturur (commit eder)."""
        link = cls.query.filter_by(proje_id=proje_id).first()
        if link:
            return link
        link = cls(proje_id=proje_id, token=cls.uret_token(),
                   olusturan_id=olusturan_id, aktif=True)
        db.session.add(link)
        db.session.commit()
        return link


class ReferansKayit(db.Model, TimestampMixin):
    """Bir çalışanın bıraktığı tek bir referans (davet edilen arkadaş)."""
    __tablename__ = 'referans_kayitlari'

    id = db.Column(db.Integer, primary_key=True)
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'),
                         nullable=False, index=True)

    # Davet eden çalışan - ad/telefon kayıt anındaki haliyle kopyalanır
    davet_eden_calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), index=True)
    davet_eden_ad_soyad = db.Column(db.String(200))
    davet_eden_telefon = db.Column(db.String(20))

    referans_ad_soyad = db.Column(db.String(200), nullable=False)
    referans_telefon = db.Column(db.String(20), nullable=False, index=True)
    referans_il = db.Column(db.String(100))
    referans_notu = db.Column(db.Text)

    durum = db.Column(db.String(20), default='yeni', nullable=False, index=True)

    # Arama takibi
    arayan_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    arama_notu = db.Column(db.Text)
    arama_tarihi = db.Column(db.DateTime)

    token = db.Column(db.String(64), unique=True, index=True)
    ip = db.Column(db.String(200))  # IPv6 + proxy zinciri için geniş

    # İlişkiler
    proje = db.relationship('Proje')
    davet_eden = db.relationship('Calisan')
    arayan = db.relationship('User')

    def __repr__(self):
        return f'<ReferansKayit {self.referans_ad_soyad} ({self.durum})>'

    def generate_token(self):
        self.token = secrets.token_urlsafe(32)
        return self.token

    @property
    def durum_etiket(self):
        return REFERANS_DURUMLARI.get(self.durum, (self.durum, ''))[0]

    @property
    def durum_renk(self):
        return REFERANS_DURUMLARI.get(self.durum, ('', 'bg-gray-100 text-gray-700'))[1]

    def durum_guncelle(self, durum, arama_notu=None, user_id=None):
        """Arama sonucunu işler; not verilmişse mevcut nota tarih damgalı ekler."""
        self.durum = durum
        self.arayan_user_id = user_id
        self.arama_tarihi = datetime.now()
        if arama_notu:
            damga = datetime.now().strftime('%d.%m.%Y %H:%M')
            satir = f'[{damga}] {arama_notu}'
            self.arama_notu = f'{self.arama_notu}\n{satir}' if self.arama_notu else satir
