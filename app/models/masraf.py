# -*- coding: utf-8 -*-
"""
TG Portal - Masraf Modülü Modelleri
Masraf girişi, kategori, fatura yükleme
"""

from datetime import datetime, date
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class MasrafKategorisi(db.Model, TimestampMixin):
    """Masraf kategorileri - Ulaşım, Yemek, Konaklama vb."""
    __tablename__ = 'masraf_kategorileri'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    kod = db.Column(db.String(20), unique=True)  # ULASIM, YEMEK, KONAKLAMA
    aciklama = db.Column(db.Text)
    ikon = db.Column(db.String(50), default='bi-receipt')  # Bootstrap icon
    renk = db.Column(db.String(20), default='secondary')  # Bootstrap renk
    
    # Limitler
    gunluk_limit = db.Column(db.Numeric(10, 2))  # Günlük max tutar
    aylik_limit = db.Column(db.Numeric(10, 2))   # Aylık max tutar
    fatura_zorunlu = db.Column(db.Boolean, default=True)
    
    # Muhasebe entegrasyonu
    muhasebe_kodu = db.Column(db.String(50))
    
    aktif = db.Column(db.Boolean, default=True)
    sira = db.Column(db.Integer, default=0)
    
    # İlişkiler
    masraflar = db.relationship('Masraf', backref='kategori', lazy='dynamic')
    
    def __repr__(self):
        return f'<MasrafKategorisi {self.ad}>'


class Masraf(db.Model, TimestampMixin, SoftDeleteMixin):
    """Ana masraf kaydı"""
    __tablename__ = 'masraflar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Masraf sahibi
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    
    # Temel bilgiler
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    
    # Tarih ve dönem
    masraf_tarihi = db.Column(db.Date, nullable=False)
    donem_ay = db.Column(db.Integer)  # 1-12
    donem_yil = db.Column(db.Integer)
    
    # Kategori
    kategori_id = db.Column(db.Integer, db.ForeignKey('masraf_kategorileri.id'))
    
    # Tutar bilgileri
    tutar = db.Column(db.Numeric(12, 2), nullable=False)
    kdv_orani = db.Column(db.Integer, default=20)  # %20, %10, %1, %0
    kdv_tutari = db.Column(db.Numeric(12, 2), default=0)
    toplam_tutar = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Para birimi
    para_birimi = db.Column(db.String(3), default='TRY')  # TRY, USD, EUR
    kur = db.Column(db.Numeric(10, 4), default=1)  # Döviz kuru
    tl_karsiligi = db.Column(db.Numeric(12, 2))  # TL karşılığı
    
    # Proje bağlantısı (opsiyonel)
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'))
    
    # Fatura/Fiş bilgileri
    fatura_no = db.Column(db.String(50))
    fatura_tarihi = db.Column(db.Date)
    firma_adi = db.Column(db.String(200))
    firma_vkn = db.Column(db.String(20))  # Vergi kimlik no
    
    # Dosya
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))
    dosya_tipi = db.Column(db.String(50))  # image/jpeg, application/pdf
    
    # OCR verileri (Faz 2 için)
    ocr_yapildi = db.Column(db.Boolean, default=False)
    ocr_ham_veri = db.Column(db.JSON)  # Claude'dan gelen raw JSON
    
    # Durum
    durum = db.Column(db.String(20), default='taslak')
    # taslak, onay_bekliyor, onaylandi, reddedildi, odendi
    
    # Ödeme bilgileri
    odeme_tarihi = db.Column(db.Date)
    odeme_referans = db.Column(db.String(100))
    
    # Onay referansı
    onay_talebi_id = db.Column(db.Integer, db.ForeignKey('onay_talepleri.id'))
    
    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('masraflar', lazy='dynamic'))
    proje = db.relationship('Proje', backref=db.backref('masraflar', lazy='dynamic'))
    onay_talebi = db.relationship('OnayTalebi')
    kalemler = db.relationship('MasrafKalemi', backref='masraf', lazy='dynamic',
                                cascade='all, delete-orphan')
    
    @property
    def durum_text(self):
        durum_map = {
            'taslak': 'Taslak',
            'onay_bekliyor': 'Onay Bekliyor',
            'onaylandi': 'Onaylandı',
            'reddedildi': 'Reddedildi',
            'odendi': 'Ödendi'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        renk_map = {
            'taslak': 'secondary',
            'onay_bekliyor': 'warning',
            'onaylandi': 'success',
            'reddedildi': 'danger',
            'odendi': 'info'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def duzenlenebilir(self):
        """Taslak veya reddedilmiş masraflar düzenlenebilir"""
        return self.durum in ['taslak', 'reddedildi']
    
    def hesapla_kdv(self):
        """KDV hesapla ve toplam tutarı güncelle"""
        if self.kdv_orani and self.tutar:
            self.kdv_tutari = self.tutar * self.kdv_orani / 100
            self.toplam_tutar = self.tutar + self.kdv_tutari
        else:
            self.kdv_tutari = 0
            self.toplam_tutar = self.tutar
        
        # TL karşılığı
        if self.para_birimi != 'TRY' and self.kur:
            self.tl_karsiligi = self.toplam_tutar * self.kur
        else:
            self.tl_karsiligi = self.toplam_tutar
    
    def __repr__(self):
        return f'<Masraf {self.id} - {self.baslik}>'


class MasrafKalemi(db.Model, TimestampMixin):
    """Masraf kalemleri - Tek fişte birden fazla kalem için"""
    __tablename__ = 'masraf_kalemleri'
    
    id = db.Column(db.Integer, primary_key=True)
    masraf_id = db.Column(db.Integer, db.ForeignKey('masraflar.id'), nullable=False)
    
    aciklama = db.Column(db.String(500), nullable=False)
    miktar = db.Column(db.Numeric(10, 2), default=1)
    birim_fiyat = db.Column(db.Numeric(12, 2), nullable=False)
    tutar = db.Column(db.Numeric(12, 2), nullable=False)
    
    kdv_orani = db.Column(db.Integer, default=20)
    kdv_tutari = db.Column(db.Numeric(12, 2), default=0)
    
    kategori_id = db.Column(db.Integer, db.ForeignKey('masraf_kategorileri.id'))
    
    # İlişki
    kategori = db.relationship('MasrafKategorisi')
    
    def hesapla(self):
        """Tutar ve KDV hesapla"""
        self.tutar = self.miktar * self.birim_fiyat
        self.kdv_tutari = self.tutar * self.kdv_orani / 100


class MasrafAvans(db.Model, TimestampMixin, SoftDeleteMixin):
    """Masraf avansları - Önceden alınan avanslar"""
    __tablename__ = 'masraf_avanslari'
    
    id = db.Column(db.Integer, primary_key=True)
    
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    
    tutar = db.Column(db.Numeric(12, 2), nullable=False)
    para_birimi = db.Column(db.String(3), default='TRY')
    
    tarih = db.Column(db.Date, nullable=False)
    aciklama = db.Column(db.Text)
    
    # Proje bazlı avans
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'))
    
    # Durum
    durum = db.Column(db.String(20), default='aktif')  # aktif, kapandi
    
    # Mahsup edilen tutar
    kullanilan_tutar = db.Column(db.Numeric(12, 2), default=0)
    
    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('avanslar', lazy='dynamic'))
    proje = db.relationship('Proje')
    
    @property
    def kalan_tutar(self):
        return self.tutar - (self.kullanilan_tutar or 0)
    
    def __repr__(self):
        return f'<MasrafAvans {self.id} - {self.tutar}>'


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def get_calisan_masraf_ozeti(calisan_id, yil=None, ay=None):
    """Çalışanın masraf özeti"""
    from sqlalchemy import func
    
    if not yil:
        yil = date.today().year
    if not ay:
        ay = date.today().month
    
    query = Masraf.query.filter(
        Masraf.calisan_id == calisan_id,
        Masraf.is_deleted == False,
        Masraf.donem_yil == yil,
        Masraf.donem_ay == ay
    )
    
    return {
        'toplam': query.with_entities(func.sum(Masraf.tl_karsiligi)).scalar() or 0,
        'onay_bekleyen': query.filter(Masraf.durum == 'onay_bekliyor').with_entities(func.sum(Masraf.tl_karsiligi)).scalar() or 0,
        'onaylanan': query.filter(Masraf.durum == 'onaylandi').with_entities(func.sum(Masraf.tl_karsiligi)).scalar() or 0,
        'odenen': query.filter(Masraf.durum == 'odendi').with_entities(func.sum(Masraf.tl_karsiligi)).scalar() or 0,
        'adet': query.count()
    }
