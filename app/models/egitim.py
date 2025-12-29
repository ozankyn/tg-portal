# -*- coding: utf-8 -*-
"""
TG Portal - Eğitim Modelleri
Eğitim tanımları, katılımcılar ve takip
"""

from datetime import datetime, date
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class EgitimTipi(db.Model, TimestampMixin):
    """Eğitim tipleri - Oryantasyon, İSG, Ürün Eğitimi vb."""
    __tablename__ = 'egitim_tipleri'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    kod = db.Column(db.String(20), unique=True)  # ORYANTASYON, ISG, URUN
    kategori = db.Column(db.String(50))  # zorunlu, teknik, soft_skill, urun
    aciklama = db.Column(db.Text)
    
    # Ayarlar
    sure_saat = db.Column(db.Float)  # Standart süre (saat)
    gecerlilik_gun = db.Column(db.Integer)  # Sertifika geçerlilik süresi (gün), NULL = süresiz
    sertifika_gerekli = db.Column(db.Boolean, default=False)
    tekrar_periyot_gun = db.Column(db.Integer)  # Tekrar eğitim periyodu (gün)
    
    aktif = db.Column(db.Boolean, default=True)
    sira = db.Column(db.Integer, default=0)
    
    # İlişkiler
    egitimler = db.relationship('Egitim', backref='egitim_tipi', lazy='dynamic')
    
    def __repr__(self):
        return f'<EgitimTipi {self.ad}>'


class Egitim(db.Model, TimestampMixin, SoftDeleteMixin):
    """Eğitim oturumu - Planlanan/gerçekleşen eğitimler"""
    __tablename__ = 'egitimler'
    
    id = db.Column(db.Integer, primary_key=True)
    egitim_tipi_id = db.Column(db.Integer, db.ForeignKey('egitim_tipleri.id'), nullable=False)
    
    # Temel bilgiler
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    
    # Proje bağlantısı (opsiyonel - proje bazlı eğitimler için)
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'))
    
    # Tarih ve süre
    baslangic_tarihi = db.Column(db.DateTime, nullable=False)
    bitis_tarihi = db.Column(db.DateTime)
    sure_saat = db.Column(db.Float)  # Gerçekleşen süre
    
    # Lokasyon
    lokasyon_tipi = db.Column(db.String(20), default='yuz_yuze')  # yuz_yuze, online, hibrit
    lokasyon = db.Column(db.String(200))  # Adres veya online link
    
    # Eğitmen
    egitmen_tipi = db.Column(db.String(20))  # ic, dis
    egitmen_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))  # İç eğitmen
    dis_egitmen_ad = db.Column(db.String(100))  # Dış eğitmen adı
    dis_egitmen_kurum = db.Column(db.String(200))  # Eğitim firması
    
    # Kapasite
    kontenjan = db.Column(db.Integer)  # Max katılımcı
    min_katilimci = db.Column(db.Integer)  # Min katılımcı (açılma şartı)
    
    # Durum
    durum = db.Column(db.String(20), default='planli')  # planli, devam_ediyor, tamamlandi, iptal
    iptal_nedeni = db.Column(db.Text)
    
    # Maliyet
    maliyet = db.Column(db.Numeric(10, 2))
    para_birimi = db.Column(db.String(3), default='TRY')
    
    notlar = db.Column(db.Text)
    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # İlişkiler
    proje = db.relationship('Proje', backref=db.backref('egitimler', lazy='dynamic'))
    egitmen = db.relationship('Calisan', foreign_keys=[egitmen_id], backref='verdigi_egitimler')
    olusturan = db.relationship('User', foreign_keys=[olusturan_id])
    katilimcilar = db.relationship('EgitimKatilimci', backref='egitim', lazy='dynamic',
                                   cascade='all, delete-orphan')
    materyaller = db.relationship('EgitimMateryali', backref='egitim', lazy='dynamic',
                                  cascade='all, delete-orphan')
    
    @property
    def katilimci_sayisi(self):
        return self.katilimcilar.filter(
            EgitimKatilimci.durum.in_(['davetli', 'katildi', 'gecti'])
        ).count()
    
    @property
    def tamamlayan_sayisi(self):
        return self.katilimcilar.filter_by(durum='gecti').count()
    
    @property
    def doluluk_orani(self):
        if not self.kontenjan:
            return None
        return round((self.katilimci_sayisi / self.kontenjan) * 100, 1)
    
    @property
    def durum_renk(self):
        renk_map = {
            'planli': 'info',
            'devam_ediyor': 'warning',
            'tamamlandi': 'success',
            'iptal': 'danger'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def gecmis_mi(self):
        """Eğitim tarihi geçmiş mi?"""
        if self.bitis_tarihi:
            return datetime.now() > self.bitis_tarihi
        return datetime.now() > self.baslangic_tarihi
    
    def __repr__(self):
        return f'<Egitim {self.baslik}>'


class EgitimKatilimci(db.Model, TimestampMixin):
    """Eğitim katılımcıları - Çalışanların eğitime katılım durumu"""
    __tablename__ = 'egitim_katilimcilar'
    
    id = db.Column(db.Integer, primary_key=True)
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'), nullable=False)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    
    # Katılım durumu
    durum = db.Column(db.String(20), default='davetli')  # davetli, katildi, gecti, kaldi, iptal, mazeret
    
    # Davet
    davet_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    davet_eden_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Katılım
    katilim_tarihi = db.Column(db.DateTime)
    katilim_notu = db.Column(db.Text)  # Katılımcı hakkında not
    
    # Değerlendirme
    puan = db.Column(db.Integer)  # 0-100 arası sınav puanı
    degerlendirme = db.Column(db.Text)  # Eğitmen değerlendirmesi
    
    # Sertifika
    sertifika_no = db.Column(db.String(50))
    sertifika_tarihi = db.Column(db.Date)
    sertifika_gecerlilik = db.Column(db.Date)  # Sertifika bitiş tarihi
    
    # Mazeret
    mazeret_nedeni = db.Column(db.Text)
    
    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('egitim_kayitlari', lazy='dynamic'))
    davet_eden = db.relationship('User', foreign_keys=[davet_eden_id])
    
    # Unique constraint - aynı çalışan aynı eğitime bir kez katılabilir
    __table_args__ = (
        db.UniqueConstraint('egitim_id', 'calisan_id', name='unique_egitim_katilimci'),
    )
    
    @property
    def durum_text(self):
        durum_map = {
            'davetli': 'Davetli',
            'katildi': 'Katıldı',
            'gecti': 'Başarılı',
            'kaldi': 'Başarısız',
            'iptal': 'İptal',
            'mazeret': 'Mazeretli'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        renk_map = {
            'davetli': 'info',
            'katildi': 'primary',
            'gecti': 'success',
            'kaldi': 'danger',
            'iptal': 'secondary',
            'mazeret': 'warning'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def sertifika_gecerli_mi(self):
        """Sertifika hala geçerli mi?"""
        if not self.sertifika_gecerlilik:
            return True  # Süresiz
        return date.today() <= self.sertifika_gecerlilik
    
    def __repr__(self):
        return f'<EgitimKatilimci {self.calisan_id} - {self.egitim_id}>'


class EgitimMateryali(db.Model, TimestampMixin):
    """Eğitim materyalleri - Dökümanlar, sunumlar, videolar"""
    __tablename__ = 'egitim_materyalleri'
    
    id = db.Column(db.Integer, primary_key=True)
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'), nullable=False)
    
    ad = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    materyal_tipi = db.Column(db.String(20))  # dokuman, sunum, video, link
    
    # Dosya bilgileri
    dosya_adi = db.Column(db.String(255))
    dosya_yolu = db.Column(db.String(500))
    dosya_boyut = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    
    # Veya harici link
    harici_link = db.Column(db.String(500))
    
    sira = db.Column(db.Integer, default=0)
    yukleyen_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    yukleyen = db.relationship('User', foreign_keys=[yukleyen_id])
    
    def __repr__(self):
        return f'<EgitimMateryali {self.ad}>'


class CalisanZorunluEgitim(db.Model, TimestampMixin):
    """Çalışanın zorunlu eğitim durumu - Pozisyon bazlı zorunlu eğitim takibi"""
    __tablename__ = 'calisan_zorunlu_egitimler'
    
    id = db.Column(db.Integer, primary_key=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    egitim_tipi_id = db.Column(db.Integer, db.ForeignKey('egitim_tipleri.id'), nullable=False)
    
    # Durum
    tamamlandi = db.Column(db.Boolean, default=False)
    tamamlanma_tarihi = db.Column(db.Date)
    son_gecerlilik = db.Column(db.Date)  # Ne zamana kadar geçerli
    
    # Hatırlatma
    hatirlatma_gonderildi = db.Column(db.Boolean, default=False)
    hatirlatma_tarihi = db.Column(db.DateTime)
    
    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('zorunlu_egitimler', lazy='dynamic'))
    egitim_tipi = db.relationship('EgitimTipi')
    
    __table_args__ = (
        db.UniqueConstraint('calisan_id', 'egitim_tipi_id', name='unique_calisan_zorunlu_egitim'),
    )
    
    @property
    def gecerli_mi(self):
        if not self.tamamlandi:
            return False
        if not self.son_gecerlilik:
            return True
        return date.today() <= self.son_gecerlilik
    
    @property
    def yenileme_gerekli_mi(self):
        """30 gün içinde yenileme gerekli mi?"""
        if not self.son_gecerlilik:
            return False
        from datetime import timedelta
        return date.today() + timedelta(days=30) >= self.son_gecerlilik
    
    def __repr__(self):
        return f'<CalisanZorunluEgitim {self.calisan_id} - {self.egitim_tipi_id}>'


# ============================================
# POZİSYON ZORUNLU EĞİTİM İLİŞKİSİ
# HedefKadro veya Pozisyon modeline eklenecek
# ============================================

class PozisyonZorunluEgitim(db.Model):
    """Pozisyon için zorunlu eğitimler"""
    __tablename__ = 'pozisyon_zorunlu_egitimler'
    
    id = db.Column(db.Integer, primary_key=True)
    pozisyon_id = db.Column(db.Integer, db.ForeignKey('pozisyonlar.id'))
    kadro_id = db.Column(db.Integer, db.ForeignKey('hedef_kadrolar.id'))  # Veya kadro bazlı
    egitim_tipi_id = db.Column(db.Integer, db.ForeignKey('egitim_tipleri.id'), nullable=False)
    
    zorunlu = db.Column(db.Boolean, default=True)
    oncelik = db.Column(db.Integer, default=1)  # İşe başlamadan önce (1) veya sonra (2)
    sure_gun = db.Column(db.Integer)  # İşe başladıktan kaç gün içinde tamamlanmalı
    
    egitim_tipi = db.relationship('EgitimTipi')
