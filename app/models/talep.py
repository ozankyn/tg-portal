# -*- coding: utf-8 -*-
"""
TG Portal - Talep/Ticket Modülü Modelleri
Dahili destek talepleri - IT, İK, İdari İşler vb.
"""

from datetime import datetime, date
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class TalepKategorisi(db.Model, TimestampMixin):
    """Talep kategorileri - IT Destek, İK Talepleri, İdari İşler vb."""
    __tablename__ = 'talep_kategorileri'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    kod = db.Column(db.String(20), unique=True)
    aciklama = db.Column(db.Text)
    ikon = db.Column(db.String(50), default='bi-ticket')
    renk = db.Column(db.String(20), default='primary')
    
    # Varsayılan atanan departman/kişi
    varsayilan_atanan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # SLA (Service Level Agreement) - saat cinsinden
    sla_cevap = db.Column(db.Integer, default=4)  # İlk yanıt süresi
    sla_cozum = db.Column(db.Integer, default=24)  # Çözüm süresi
    
    aktif = db.Column(db.Boolean, default=True)
    sira = db.Column(db.Integer, default=0)
    
    # İlişkiler
    varsayilan_atanan = db.relationship('User', foreign_keys=[varsayilan_atanan_id])
    
    def __repr__(self):
        return f'<TalepKategorisi {self.ad}>'


class Talep(db.Model, TimestampMixin, SoftDeleteMixin):
    """Destek talebi"""
    __tablename__ = 'talepler'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Talep numarası
    talep_no = db.Column(db.String(20), unique=True)
    
    # Talep eden
    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Kategori
    kategori_id = db.Column(db.Integer, db.ForeignKey('talep_kategorileri.id'), nullable=False)
    
    # Temel bilgiler
    konu = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text, nullable=False)
    
    # Öncelik
    oncelik = db.Column(db.String(20), default='normal')
    # dusuk, normal, yuksek, kritik
    
    # Durum
    durum = db.Column(db.String(20), default='acik')
    # acik, atandi, devam_ediyor, beklemede, cozuldu, kapatildi
    
    # Atama
    atanan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    atanma_tarihi = db.Column(db.DateTime)
    
    # Tarihler
    ilk_yanit_tarihi = db.Column(db.DateTime)
    cozum_tarihi = db.Column(db.DateTime)
    kapatma_tarihi = db.Column(db.DateTime)
    
    # Çözüm
    cozum_notu = db.Column(db.Text)
    
    # Dosya
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))
    
    # İlişkiler
    olusturan = db.relationship('User', foreign_keys=[olusturan_id], backref=db.backref('olusturulan_talepler', lazy='dynamic'))
    atanan = db.relationship('User', foreign_keys=[atanan_id], backref=db.backref('atanan_talepler', lazy='dynamic'))
    kategori = db.relationship('TalepKategorisi', backref='talepler')
    yorumlar = db.relationship('TalepYorum', backref='talep', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def durum_text(self):
        durum_map = {
            'acik': 'Açık',
            'atandi': 'Atandı',
            'devam_ediyor': 'Devam Ediyor',
            'beklemede': 'Beklemede',
            'cozuldu': 'Çözüldü',
            'kapatildi': 'Kapatıldı'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        renk_map = {
            'acik': 'danger',
            'atandi': 'info',
            'devam_ediyor': 'primary',
            'beklemede': 'warning',
            'cozuldu': 'success',
            'kapatildi': 'secondary'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def oncelik_text(self):
        oncelik_map = {
            'dusuk': 'Düşük',
            'normal': 'Normal',
            'yuksek': 'Yüksek',
            'kritik': 'Kritik'
        }
        return oncelik_map.get(self.oncelik, self.oncelik)
    
    @property
    def oncelik_renk(self):
        renk_map = {
            'dusuk': 'secondary',
            'normal': 'info',
            'yuksek': 'warning',
            'kritik': 'danger'
        }
        return renk_map.get(self.oncelik, 'secondary')
    
    @property
    def acik_mi(self):
        return self.durum not in ['cozuldu', 'kapatildi']
    
    @property
    def sure_gecti(self):
        """Oluşturulma tarihinden bu yana geçen süre (saat)"""
        if not self.created_at:
            return 0
        delta = datetime.utcnow() - self.created_at
        return int(delta.total_seconds() / 3600)
    
    @property
    def sla_asim(self):
        """SLA aşıldı mı?"""
        if not self.acik_mi or not self.kategori:
            return False
        return self.sure_gecti > self.kategori.sla_cozum
    
    def talep_no_olustur(self):
        """Otomatik talep numarası"""
        yil = date.today().year
        son = Talep.query.filter(
            Talep.talep_no.like(f'TLP-{yil}-%')
        ).count()
        self.talep_no = f'TLP-{yil}-{son + 1:04d}'
    
    def __repr__(self):
        return f'<Talep {self.talep_no}>'


class TalepYorum(db.Model, TimestampMixin):
    """Talep yorumları/mesajları"""
    __tablename__ = 'talep_yorumlari'
    
    id = db.Column(db.Integer, primary_key=True)
    talep_id = db.Column(db.Integer, db.ForeignKey('talepler.id'), nullable=False)
    
    yazan_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    icerik = db.Column(db.Text, nullable=False)
    
    # Yorum tipi
    tip = db.Column(db.String(20), default='yorum')
    # yorum, cevap, not, durum_degisikligi
    
    # Dahili not mu? (sadece destek ekibi görür)
    dahili = db.Column(db.Boolean, default=False)
    
    # Dosya
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))
    
    # İlişki
    yazan = db.relationship('User', backref=db.backref('talep_yorumlari', lazy='dynamic'))
    
    def __repr__(self):
        return f'<TalepYorum {self.id}>'


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def get_acik_talepler(kullanici_id=None, atanan_id=None):
    """Açık talepleri getir"""
    query = Talep.query.filter(
        Talep.is_deleted == False,
        Talep.durum.in_(['acik', 'atandi', 'devam_ediyor', 'beklemede'])
    )
    
    if kullanici_id:
        query = query.filter(Talep.olusturan_id == kullanici_id)
    if atanan_id:
        query = query.filter(Talep.atanan_id == atanan_id)
    
    return query.order_by(Talep.created_at.desc()).all()


def get_talep_istatistikleri(atanan_id=None):
    """Talep istatistikleri"""
    from sqlalchemy import func
    
    base_query = Talep.query.filter(Talep.is_deleted == False)
    
    if atanan_id:
        base_query = base_query.filter(Talep.atanan_id == atanan_id)
    
    stats = {
        'toplam': base_query.count(),
        'acik': base_query.filter(Talep.durum.in_(['acik', 'atandi', 'devam_ediyor', 'beklemede'])).count(),
        'cozuldu': base_query.filter(Talep.durum == 'cozuldu').count(),
        'bugun': base_query.filter(func.date(Talep.created_at) == date.today()).count()
    }
    
    return stats
