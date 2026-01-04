# -*- coding: utf-8 -*-
"""
TG Portal - Sözleşme Modülü Modelleri
Sözleşme takibi, bitiş uyarıları
"""

from datetime import datetime, date, timedelta
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class SozlesmeTipi(db.Model, TimestampMixin):
    """Sözleşme tipleri - Müşteri, Tedarikçi, Kira, İş vb."""
    __tablename__ = 'sozlesme_tipleri'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    kod = db.Column(db.String(20), unique=True)  # MUSTERI, TEDARIKCI, KIRA, IS
    aciklama = db.Column(db.Text)
    
    # Varsayılan uyarı günleri
    uyari_gun_1 = db.Column(db.Integer, default=30)  # 30 gün önce
    uyari_gun_2 = db.Column(db.Integer, default=15)  # 15 gün önce
    uyari_gun_3 = db.Column(db.Integer, default=7)   # 7 gün önce
    
    aktif = db.Column(db.Boolean, default=True)
    sira = db.Column(db.Integer, default=0)
    
    # İlişkiler
    sozlesmeler = db.relationship('Sozlesme', backref='tip', lazy='dynamic')
    
    def __repr__(self):
        return f'<SozlesmeTipi {self.ad}>'


class Sozlesme(db.Model, TimestampMixin, SoftDeleteMixin):
    """Ana sözleşme kaydı"""
    __tablename__ = 'sozlesmeler'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Temel bilgiler
    baslik = db.Column(db.String(200), nullable=False)
    sozlesme_no = db.Column(db.String(50), unique=True)
    aciklama = db.Column(db.Text)
    
    # Tip
    tip_id = db.Column(db.Integer, db.ForeignKey('sozlesme_tipleri.id'), nullable=False)
    
    # Taraf bağlantıları (biri dolu olmalı)
    musteri_id = db.Column(db.Integer, db.ForeignKey('musteriler.id'))
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'))
    diger_taraf = db.Column(db.String(200))  # Müşteri/tedarikçi dışı taraflar için
    
    # Tarihler
    baslangic_tarihi = db.Column(db.Date, nullable=False)
    bitis_tarihi = db.Column(db.Date, nullable=False)
    imza_tarihi = db.Column(db.Date)
    
    # Otomatik yenileme
    otomatik_yenileme = db.Column(db.Boolean, default=False)
    yenileme_suresi_ay = db.Column(db.Integer, default=12)  # Kaç ay uzasın
    
    # Tutar bilgileri
    tutar = db.Column(db.Numeric(14, 2))
    para_birimi = db.Column(db.String(3), default='TRY')
    kdv_dahil = db.Column(db.Boolean, default=True)
    odeme_periyodu = db.Column(db.String(20))  # aylik, yillik, tek_seferlik
    
    # Durum
    durum = db.Column(db.String(20), default='aktif')
    # aktif, sona_erdi, iptal, askida, yenilendi
    
    # Sorumlu
    sorumlu_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))
    
    # Notlar ve şartlar
    ozel_sartlar = db.Column(db.Text)
    notlar = db.Column(db.Text)
    
    # Dosya
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))
    
    # Uyarı durumu
    son_uyari_tarihi = db.Column(db.Date)
    uyari_gonderildi_30 = db.Column(db.Boolean, default=False)
    uyari_gonderildi_15 = db.Column(db.Boolean, default=False)
    uyari_gonderildi_7 = db.Column(db.Boolean, default=False)
    
    # İlişkiler
    musteri = db.relationship('Musteri', backref=db.backref('sozlesmeler', lazy='dynamic'))
    tedarikci = db.relationship('Tedarikci', backref=db.backref('sozlesmeler', lazy='dynamic'))
    sorumlu = db.relationship('Calisan', backref=db.backref('sorumlu_sozlesmeler', lazy='dynamic'))
    ekler = db.relationship('SozlesmeEk', backref='sozlesme', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def taraf_adi(self):
        """Sözleşme tarafının adını döndür"""
        if self.musteri:
            return self.musteri.ad
        elif self.tedarikci:
            return self.tedarikci.ad
        return self.diger_taraf or '-'
    
    @property
    def taraf_tipi(self):
        """Taraf tipini döndür"""
        if self.musteri_id:
            return 'musteri'
        elif self.tedarikci_id:
            return 'tedarikci'
        return 'diger'
    
    @property
    def durum_text(self):
        durum_map = {
            'aktif': 'Aktif',
            'sona_erdi': 'Sona Erdi',
            'iptal': 'İptal Edildi',
            'askida': 'Askıda',
            'yenilendi': 'Yenilendi'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        renk_map = {
            'aktif': 'success',
            'sona_erdi': 'secondary',
            'iptal': 'danger',
            'askida': 'warning',
            'yenilendi': 'info'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def kalan_gun(self):
        """Bitiş tarihine kalan gün"""
        if not self.bitis_tarihi:
            return None
        delta = self.bitis_tarihi - date.today()
        return delta.days
    
    @property
    def kalan_gun_renk(self):
        """Kalan güne göre renk"""
        kalan = self.kalan_gun
        if kalan is None:
            return 'secondary'
        if kalan < 0:
            return 'dark'
        elif kalan <= 7:
            return 'danger'
        elif kalan <= 15:
            return 'warning'
        elif kalan <= 30:
            return 'info'
        return 'success'
    
    @property
    def sure_ay(self):
        """Sözleşme süresi (ay olarak)"""
        if not self.baslangic_tarihi or not self.bitis_tarihi:
            return None
        delta = self.bitis_tarihi - self.baslangic_tarihi
        return round(delta.days / 30)
    
    @property
    def gecerli_mi(self):
        """Sözleşme hala geçerli mi"""
        if self.durum != 'aktif':
            return False
        return self.bitis_tarihi >= date.today()
    
    def yenile(self, ay=None):
        """Sözleşmeyi yenile"""
        if ay is None:
            ay = self.yenileme_suresi_ay or 12
        
        self.baslangic_tarihi = self.bitis_tarihi + timedelta(days=1)
        self.bitis_tarihi = self.baslangic_tarihi + timedelta(days=ay*30)
        self.durum = 'aktif'
        
        # Uyarı flaglerini sıfırla
        self.uyari_gonderildi_30 = False
        self.uyari_gonderildi_15 = False
        self.uyari_gonderildi_7 = False
    
    def __repr__(self):
        return f'<Sozlesme {self.sozlesme_no or self.id}>'


class SozlesmeEk(db.Model, TimestampMixin):
    """Sözleşme ek dosyaları"""
    __tablename__ = 'sozlesme_ekleri'
    
    id = db.Column(db.Integer, primary_key=True)
    sozlesme_id = db.Column(db.Integer, db.ForeignKey('sozlesmeler.id'), nullable=False)
    
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))
    dosya_tipi = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<SozlesmeEk {self.baslik}>'


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def get_yaklasan_sozlesmeler(gun=30):
    """Bitiş tarihi yaklaşan sözleşmeleri getir"""
    bugun = date.today()
    bitis = bugun + timedelta(days=gun)
    
    return Sozlesme.query.filter(
        Sozlesme.is_deleted == False,
        Sozlesme.durum == 'aktif',
        Sozlesme.bitis_tarihi <= bitis,
        Sozlesme.bitis_tarihi >= bugun
    ).order_by(Sozlesme.bitis_tarihi).all()


def get_sona_eren_sozlesmeler():
    """Süresi dolmuş ama hala aktif olan sözleşmeler"""
    bugun = date.today()
    
    return Sozlesme.query.filter(
        Sozlesme.is_deleted == False,
        Sozlesme.durum == 'aktif',
        Sozlesme.bitis_tarihi < bugun
    ).all()


def guncelle_sozlesme_durumlari():
    """Süresi dolan sözleşmelerin durumunu güncelle"""
    sona_erenler = get_sona_eren_sozlesmeler()
    
    for sozlesme in sona_erenler:
        if sozlesme.otomatik_yenileme:
            sozlesme.yenile()
        else:
            sozlesme.durum = 'sona_erdi'
    
    if sona_erenler:
        db.session.commit()
    
    return len(sona_erenler)
