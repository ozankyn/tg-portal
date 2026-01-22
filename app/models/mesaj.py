# -*- coding: utf-8 -*-
"""
TG Portal - Mesajlasma Modeli
"""
from datetime import datetime
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class Mesaj(db.Model, TimestampMixin, SoftDeleteMixin):
    """Kullanicilar arasi mesaj"""
    __tablename__ = 'mesajlar'

    id = db.Column(db.Integer, primary_key=True)

    gonderen_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    alici_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    konu = db.Column(db.String(200))
    icerik = db.Column(db.Text, nullable=False)

    okundu = db.Column(db.Boolean, default=False)
    okunma_tarihi = db.Column(db.DateTime)

    # Yanit ise parent mesaj
    parent_id = db.Column(db.Integer, db.ForeignKey('mesajlar.id'))

    # Dosya eki
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))

    gonderen = db.relationship('User', foreign_keys=[gonderen_id], backref='gonderilen_mesajlar')
    alici = db.relationship('User', foreign_keys=[alici_id], backref='alinan_mesajlar')
    yanitlar = db.relationship('Mesaj', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def okundu_isaretle(self):
        if not self.okundu:
            self.okundu = True
            self.okunma_tarihi = datetime.now()

    @property
    def ozet(self):
        if len(self.icerik) > 100:
            return self.icerik[:100] + '...'
        return self.icerik

    def __repr__(self):
        return f'<Mesaj {self.id} - {self.gonderen_id} -> {self.alici_id}>'


class MesajBildirimi(db.Model, TimestampMixin):
    """Mesaj bildirimleri"""
    __tablename__ = 'mesaj_bildirimleri'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mesaj_id = db.Column(db.Integer, db.ForeignKey('mesajlar.id'), nullable=False)

    goruldu = db.Column(db.Boolean, default=False)
    gorulme_tarihi = db.Column(db.DateTime)

    user = db.relationship('User', backref='mesaj_bildirimleri')
    mesaj = db.relationship('Mesaj', backref='bildirimler')

    def __repr__(self):
        return f'<MesajBildirimi {self.user_id} - {self.mesaj_id}>'
