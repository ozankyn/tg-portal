# -*- coding: utf-8 -*-
"""
TG Portal - To-Do Modeli
Görev yönetimi
"""
from datetime import datetime
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class GorevKategorisi(db.Model, TimestampMixin):
    """Görev kategorileri"""
    __tablename__ = 'gorev_kategorileri'

    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(50), nullable=False)
    renk = db.Column(db.String(20), default='#6366f1')  # Tailwind indigo
    ikon = db.Column(db.String(50), default='task')
    sira = db.Column(db.Integer, default=0)
    aktif = db.Column(db.Boolean, default=True)

    # İlişkiler
    gorevler = db.relationship('Gorev', backref='kategori', lazy='dynamic')

    def __repr__(self):
        return f'<GorevKategorisi {self.ad}>'


class Gorev(db.Model, TimestampMixin, SoftDeleteMixin):
    """Görev modeli"""
    __tablename__ = 'gorevler'

    id = db.Column(db.Integer, primary_key=True)

    # Temel bilgiler
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)

    # Durum ve öncelik
    durum = db.Column(db.String(20), default='bekliyor')  # bekliyor, devam_ediyor, tamamlandi, iptal
    oncelik = db.Column(db.String(20), default='orta')  # dusuk, orta, yuksek, acil

    # Tarihler
    baslangic_tarihi = db.Column(db.DateTime)
    bitis_tarihi = db.Column(db.DateTime)  # Deadline
    tamamlanma_tarihi = db.Column(db.DateTime)
    hatirlatma_tarihi = db.Column(db.DateTime)

    # İlerleme
    tamamlanma_yuzdesi = db.Column(db.Integer, default=0)  # 0-100

    # İlişkiler - Kişiler
    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    atanan_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Kime atandı

    # İlişkiler - Kategori
    kategori_id = db.Column(db.Integer, db.ForeignKey('gorev_kategorileri.id'))

    # İlişkiler - Diğer modüllerle bağlantı
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'))
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'))

    # Üst görev (alt görevler için)
    ust_gorev_id = db.Column(db.Integer, db.ForeignKey('gorevler.id'))

    # Etiketler (JSON array olarak)
    etiketler = db.Column(db.Text)  # JSON: ["etiket1", "etiket2"]

    # Relationships
    olusturan = db.relationship('User', foreign_keys=[olusturan_id], backref='olusturulan_gorevler')
    atanan = db.relationship('User', foreign_keys=[atanan_id], backref='atanan_gorevler')
    proje = db.relationship('Proje', backref='gorevler')
    egitim = db.relationship('Egitim', backref='gorevler')
    alt_gorevler = db.relationship('Gorev', backref=db.backref('ust_gorev', remote_side=[id]), lazy='dynamic')

    @property
    def gecikti_mi(self):
        """Görev gecikti mi?"""
        if self.durum == 'tamamlandi':
            return False
        if self.bitis_tarihi and datetime.now() > self.bitis_tarihi:
            return True
        return False

    @property
    def kalan_gun(self):
        """Deadline'a kalan gün"""
        if not self.bitis_tarihi:
            return None
        delta = self.bitis_tarihi - datetime.now()
        return delta.days

    @property
    def alt_gorev_sayisi(self):
        return self.alt_gorevler.count()

    @property
    def tamamlanan_alt_gorev_sayisi(self):
        return self.alt_gorevler.filter_by(durum='tamamlandi').count()

    def __repr__(self):
        return f'<Gorev {self.baslik}>'


class GorevYorum(db.Model, TimestampMixin):
    """Görev yorumları"""
    __tablename__ = 'gorev_yorumlari'

    id = db.Column(db.Integer, primary_key=True)
    gorev_id = db.Column(db.Integer, db.ForeignKey('gorevler.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    yorum = db.Column(db.Text, nullable=False)

    # İlişkiler
    gorev = db.relationship('Gorev', backref=db.backref('yorumlar', lazy='dynamic', order_by='GorevYorum.created_at.desc()'))
    user = db.relationship('User', backref='gorev_yorumlari')

    def __repr__(self):
        return f'<GorevYorum {self.id}>'


class GorevLog(db.Model, TimestampMixin):
    """Görev aktivite logu"""
    __tablename__ = 'gorev_loglari'

    id = db.Column(db.Integer, primary_key=True)
    gorev_id = db.Column(db.Integer, db.ForeignKey('gorevler.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    aksiyon = db.Column(db.String(50), nullable=False)  # olusturuldu, guncellendi, durum_degisti, atandi, yorum_eklendi
    detay = db.Column(db.Text)  # JSON: {"eski": "bekliyor", "yeni": "devam_ediyor"}

    # İlişkiler
    gorev = db.relationship('Gorev', backref=db.backref('loglar', lazy='dynamic', order_by='GorevLog.created_at.desc()'))
    user = db.relationship('User', backref='gorev_loglari')

    def __repr__(self):
        return f'<GorevLog {self.aksiyon}>'
