# -*- coding: utf-8 -*-
"""
TG Portal - Satın Alma Modülü Modelleri
Talep → Teklif → Sipariş → Teslimat akışı
"""

from datetime import datetime, date
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class SatinAlmaKategorisi(db.Model, TimestampMixin):
    """Satın alma kategorileri - IT Ekipman, Ofis Malzemesi vb."""
    __tablename__ = 'satinalma_kategorileri'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    kod = db.Column(db.String(20), unique=True)
    aciklama = db.Column(db.Text)
    ikon = db.Column(db.String(50), default='bi-box')
    
    # Onay limiti (bu tutarın üstü onay gerektirir)
    onay_limiti = db.Column(db.Numeric(12, 2), default=0)
    
    aktif = db.Column(db.Boolean, default=True)
    sira = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<SatinAlmaKategorisi {self.ad}>'


class SatinAlmaTalebi(db.Model, TimestampMixin, SoftDeleteMixin):
    """Satın alma talep kaydı"""
    __tablename__ = 'satinalma_talepleri'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Talep numarası (otomatik)
    talep_no = db.Column(db.String(20), unique=True)
    
    # Talep eden
    talep_eden_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    departman = db.Column(db.String(100))
    
    # Kategori
    kategori_id = db.Column(db.Integer, db.ForeignKey('satinalma_kategorileri.id'))
    
    # Temel bilgiler
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    gerekce = db.Column(db.Text)  # Neden gerekli?
    
    # Öncelik ve tarih
    oncelik = db.Column(db.String(20), default='normal')  # dusuk, normal, yuksek, acil
    talep_tarihi = db.Column(db.Date, default=date.today)
    istenen_tarih = db.Column(db.Date)  # Ne zamana kadar isteniyor
    
    # Tahmini bütçe
    tahmini_tutar = db.Column(db.Numeric(12, 2))
    para_birimi = db.Column(db.String(3), default='TRY')
    
    # Proje bağlantısı
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'))
    
    # Durum
    durum = db.Column(db.String(20), default='taslak')
    # taslak, onay_bekliyor, onaylandi, reddedildi, teklif_asamasinda, siparis_verildi, tamamlandi, iptal
    
    # Onay referansı
    onay_talebi_id = db.Column(db.Integer, db.ForeignKey('onay_talepleri.id'))
    
    # İlişkiler
    talep_eden = db.relationship('User', foreign_keys=[talep_eden_id], backref=db.backref('satinalma_talepleri', lazy='dynamic'))
    kategori = db.relationship('SatinAlmaKategorisi', backref='talepler')
    proje = db.relationship('Proje', backref=db.backref('satinalma_talepleri', lazy='dynamic'))
    onay_talebi = db.relationship('OnayTalebi')
    kalemler = db.relationship('TalepKalemi', backref='talep', lazy='dynamic', cascade='all, delete-orphan')
    teklifler = db.relationship('SatinAlmaTeklif', backref='talep', lazy='dynamic')
    
    @property
    def durum_text(self):
        durum_map = {
            'taslak': 'Taslak',
            'onay_bekliyor': 'Onay Bekliyor',
            'onaylandi': 'Onaylandı',
            'reddedildi': 'Reddedildi',
            'teklif_asamasinda': 'Teklif Aşamasında',
            'siparis_verildi': 'Sipariş Verildi',
            'tamamlandi': 'Tamamlandı',
            'iptal': 'İptal'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        renk_map = {
            'taslak': 'secondary',
            'onay_bekliyor': 'warning',
            'onaylandi': 'success',
            'reddedildi': 'danger',
            'teklif_asamasinda': 'info',
            'siparis_verildi': 'primary',
            'tamamlandi': 'success',
            'iptal': 'dark'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def oncelik_text(self):
        oncelik_map = {
            'dusuk': 'Düşük',
            'normal': 'Normal',
            'yuksek': 'Yüksek',
            'acil': 'Acil'
        }
        return oncelik_map.get(self.oncelik, self.oncelik)
    
    @property
    def oncelik_renk(self):
        renk_map = {
            'dusuk': 'secondary',
            'normal': 'info',
            'yuksek': 'warning',
            'acil': 'danger'
        }
        return renk_map.get(self.oncelik, 'secondary')
    
    @property
    def toplam_tutar(self):
        """Kalemlerin toplam tutarı"""
        return sum(k.tutar or 0 for k in self.kalemler)
    
    def talep_no_olustur(self):
        """Otomatik talep numarası oluştur"""
        yil = date.today().year
        son = SatinAlmaTalebi.query.filter(
            SatinAlmaTalebi.talep_no.like(f'SAT-{yil}-%')
        ).count()
        self.talep_no = f'SAT-{yil}-{son + 1:04d}'
    
    def __repr__(self):
        return f'<SatinAlmaTalebi {self.talep_no}>'


class TalepKalemi(db.Model, TimestampMixin):
    """Talep kalemleri"""
    __tablename__ = 'talep_kalemleri'
    
    id = db.Column(db.Integer, primary_key=True)
    talep_id = db.Column(db.Integer, db.ForeignKey('satinalma_talepleri.id'), nullable=False)
    
    urun_adi = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    miktar = db.Column(db.Numeric(10, 2), default=1)
    birim = db.Column(db.String(20), default='Adet')
    
    # Tahmini fiyat
    birim_fiyat = db.Column(db.Numeric(12, 2))
    tutar = db.Column(db.Numeric(12, 2))
    
    def __repr__(self):
        return f'<TalepKalemi {self.urun_adi}>'


class SatinAlmaTeklif(db.Model, TimestampMixin, SoftDeleteMixin):
    """Tedarikçi teklifleri"""
    __tablename__ = 'satinalma_teklifleri'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Bağlantılar
    talep_id = db.Column(db.Integer, db.ForeignKey('satinalma_talepleri.id'), nullable=False)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'), nullable=False)
    
    # Teklif bilgileri
    teklif_no = db.Column(db.String(50))
    teklif_tarihi = db.Column(db.Date, default=date.today)
    gecerlilik_tarihi = db.Column(db.Date)
    
    # Tutar
    toplam_tutar = db.Column(db.Numeric(12, 2), nullable=False)
    para_birimi = db.Column(db.String(3), default='TRY')
    kdv_dahil = db.Column(db.Boolean, default=True)
    
    # Teslimat
    teslimat_suresi = db.Column(db.String(50))  # Örn: "3-5 iş günü"
    teslimat_notu = db.Column(db.Text)
    
    # Ödeme koşulları
    odeme_kosulu = db.Column(db.String(100))  # Örn: "30 gün vadeli"
    
    # Durum
    durum = db.Column(db.String(20), default='beklemede')
    # beklemede, degerlendiriliyor, secildi, reddedildi
    
    # Notlar
    notlar = db.Column(db.Text)
    
    # Dosya
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))
    
    # İlişkiler
    tedarikci = db.relationship('Tedarikci', backref=db.backref('teklifler', lazy='dynamic'))
    kalemler = db.relationship('TeklifKalemi', backref='teklif', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def durum_text(self):
        durum_map = {
            'beklemede': 'Beklemede',
            'degerlendiriliyor': 'Değerlendiriliyor',
            'secildi': 'Seçildi',
            'reddedildi': 'Reddedildi'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        renk_map = {
            'beklemede': 'secondary',
            'degerlendiriliyor': 'info',
            'secildi': 'success',
            'reddedildi': 'danger'
        }
        return renk_map.get(self.durum, 'secondary')
    
    def __repr__(self):
        return f'<SatinAlmaTeklif {self.id}>'


class TeklifKalemi(db.Model, TimestampMixin):
    """Teklif kalemleri"""
    __tablename__ = 'teklif_kalemleri'
    
    id = db.Column(db.Integer, primary_key=True)
    teklif_id = db.Column(db.Integer, db.ForeignKey('satinalma_teklifleri.id'), nullable=False)
    
    # Talep kalemini referans (opsiyonel)
    talep_kalemi_id = db.Column(db.Integer, db.ForeignKey('talep_kalemleri.id'))
    
    urun_adi = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    miktar = db.Column(db.Numeric(10, 2), default=1)
    birim = db.Column(db.String(20), default='Adet')
    
    birim_fiyat = db.Column(db.Numeric(12, 2), nullable=False)
    tutar = db.Column(db.Numeric(12, 2), nullable=False)
    
    # İlişki
    talep_kalemi = db.relationship('TalepKalemi')
    
    def __repr__(self):
        return f'<TeklifKalemi {self.urun_adi}>'


class SatinAlmaSiparisi(db.Model, TimestampMixin, SoftDeleteMixin):
    """Satın alma siparişi"""
    __tablename__ = 'satinalma_siparisleri'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Sipariş numarası
    siparis_no = db.Column(db.String(20), unique=True)
    
    # Bağlantılar
    talep_id = db.Column(db.Integer, db.ForeignKey('satinalma_talepleri.id'), nullable=False)
    teklif_id = db.Column(db.Integer, db.ForeignKey('satinalma_teklifleri.id'))
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'), nullable=False)
    
    # Sipariş bilgileri
    siparis_tarihi = db.Column(db.Date, default=date.today)
    beklenen_teslimat = db.Column(db.Date)
    
    # Tutar
    toplam_tutar = db.Column(db.Numeric(12, 2), nullable=False)
    para_birimi = db.Column(db.String(3), default='TRY')
    
    # Durum
    durum = db.Column(db.String(20), default='siparis_verildi')
    # siparis_verildi, kismen_teslim, teslim_alindi, iptal
    
    # Notlar
    notlar = db.Column(db.Text)
    
    # İlişkiler
    talep = db.relationship('SatinAlmaTalebi', backref=db.backref('siparisler', lazy='dynamic'))
    teklif = db.relationship('SatinAlmaTeklif', backref=db.backref('siparis', uselist=False))
    tedarikci = db.relationship('Tedarikci', backref=db.backref('siparisler', lazy='dynamic'))
    teslimatlar = db.relationship('SiparisTeslimat', backref='siparis', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def durum_text(self):
        durum_map = {
            'siparis_verildi': 'Sipariş Verildi',
            'kismen_teslim': 'Kısmen Teslim',
            'teslim_alindi': 'Teslim Alındı',
            'iptal': 'İptal'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        renk_map = {
            'siparis_verildi': 'info',
            'kismen_teslim': 'warning',
            'teslim_alindi': 'success',
            'iptal': 'danger'
        }
        return renk_map.get(self.durum, 'secondary')
    
    def siparis_no_olustur(self):
        """Otomatik sipariş numarası"""
        yil = date.today().year
        son = SatinAlmaSiparisi.query.filter(
            SatinAlmaSiparisi.siparis_no.like(f'SIP-{yil}-%')
        ).count()
        self.siparis_no = f'SIP-{yil}-{son + 1:04d}'
    
    def __repr__(self):
        return f'<SatinAlmaSiparisi {self.siparis_no}>'


class SiparisTeslimat(db.Model, TimestampMixin):
    """Sipariş teslimat kaydı"""
    __tablename__ = 'siparis_teslimatlari'
    
    id = db.Column(db.Integer, primary_key=True)
    siparis_id = db.Column(db.Integer, db.ForeignKey('satinalma_siparisleri.id'), nullable=False)
    
    teslimat_tarihi = db.Column(db.Date, nullable=False)
    teslim_alan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # İrsaliye
    irsaliye_no = db.Column(db.String(50))
    
    # Teslimat notu
    notlar = db.Column(db.Text)
    
    # Dosya (irsaliye fotoğrafı vb.)
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))
    
    # İlişki
    teslim_alan = db.relationship('User', foreign_keys=[teslim_alan_id])
    
    def __repr__(self):
        return f'<SiparisTeslimat {self.id}>'
