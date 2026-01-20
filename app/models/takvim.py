# -*- coding: utf-8 -*-
"""
TG Portal - Takvim Modeli
"""
from datetime import datetime, timedelta
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class Etkinlik(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'etkinlikler'

    id = db.Column(db.Integer, primary_key=True)
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    konum = db.Column(db.String(200))
    baslangic = db.Column(db.DateTime, nullable=False)
    bitis = db.Column(db.DateTime)
    tum_gun = db.Column(db.Boolean, default=False)
    tekrar_tipi = db.Column(db.String(20))
    tekrar_bitis = db.Column(db.Date)
    hatirlatma = db.Column(db.Integer, default=15)
    hatirlatma_gonderildi = db.Column(db.Boolean, default=False)
    renk = db.Column(db.String(20), default='#6366f1')
    etkinlik_tipi = db.Column(db.String(30), default='genel')
    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    outlook_event_id = db.Column(db.String(200))
    google_event_id = db.Column(db.String(200))
    gorev_id = db.Column(db.Integer, db.ForeignKey('gorevler.id'))
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'))

    olusturan = db.relationship('User', foreign_keys=[olusturan_id], backref='etkinlikler')
    gorev = db.relationship('Gorev', backref='etkinlik')
    egitim = db.relationship('Egitim', backref='takvim_etkinligi')
    katilimcilar = db.relationship('EtkinlikKatilimci', backref='etkinlik', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def sure_dakika(self):
        if self.bitis and self.baslangic:
            return int((self.bitis - self.baslangic).total_seconds() / 60)
        return 0

    @property
    def gecti_mi(self):
        return datetime.now() > self.baslangic


class EtkinlikKatilimci(db.Model, TimestampMixin):
    __tablename__ = 'etkinlik_katilimcilari'

    id = db.Column(db.Integer, primary_key=True)
    etkinlik_id = db.Column(db.Integer, db.ForeignKey('etkinlikler.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    zorunlu = db.Column(db.Boolean, default=False)
    durum = db.Column(db.String(20), default='bekliyor')

    user = db.relationship('User', backref='etkinlik_katilimlari')

    __table_args__ = (
        db.UniqueConstraint('etkinlik_id', 'user_id', name='unique_etkinlik_katilimci'),
    )


class OutlookEntegrasyon(db.Model, TimestampMixin):
    __tablename__ = 'outlook_entegrasyonlari'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires = db.Column(db.DateTime)
    outlook_email = db.Column(db.String(200))
    outlook_name = db.Column(db.String(200))
    son_senkronizasyon = db.Column(db.DateTime)
    senkronizasyon_aktif = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref=db.backref('outlook_entegrasyon', uselist=False))

    @property
    def token_gecerli_mi(self):
        if not self.token_expires:
            return False
        return datetime.now() < self.token_expires
