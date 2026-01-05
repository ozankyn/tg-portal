# -*- coding: utf-8 -*-
"""
TG Portal - Filo Models Güncellemesi
Yeni modeller: AracTeslim, KazaFotograf, IkameArac
Kaza modeli güncelleme: onay sistemi
"""

from datetime import datetime, date
from app import db
from app.models.base import TimestampMixin, AuditMixin


# ==================== ARAÇ TESLİM/İADE ====================
class AracTeslim(db.Model, TimestampMixin, AuditMixin):
    """Araç teslim/iade kayıtları"""
    __tablename__ = 'arac_teslimler'
    
    id = db.Column(db.Integer, primary_key=True)
    arac_id = db.Column(db.Integer, db.ForeignKey('araclar.id'), nullable=False)
    
    # Teslim Tipi
    islem_tipi = db.Column(db.String(20), nullable=False)  # teslim, iade
    tarih = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Kilometre ve Yakıt
    km = db.Column(db.Integer, nullable=False)
    yakit_durumu = db.Column(db.String(20))  # dolu, uc_ceyrek, yarim, ceyrek, bos
    
    # Kişiler
    teslim_eden_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    teslim_alan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    teslim_eden_calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))
    teslim_alan_calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))
    
    # Aksesuarlar (JSON)
    aksesuarlar = db.Column(db.JSON, default=dict)
    # Örnek: {"stepne": true, "kriko": true, "yangin_sondurucusu": false, "ilk_yardim": true}
    
    # Hasar Durumu
    mevcut_hasarlar = db.Column(db.Text)
    yeni_hasar = db.Column(db.Boolean, default=False)
    yeni_hasar_aciklama = db.Column(db.Text)
    
    # Fotoğraflar (JSON - dosya yolları)
    fotograflar = db.Column(db.JSON, default=list)
    
    # İmzalar (base64 veya dosya yolu)
    imza_teslim_eden = db.Column(db.Text)
    imza_teslim_alan = db.Column(db.Text)
    
    # Notlar
    notlar = db.Column(db.Text)
    
    # İlişkiler
    arac = db.relationship('Arac', backref=db.backref('teslimler', lazy='dynamic'))
    teslim_eden = db.relationship('User', foreign_keys=[teslim_eden_id], backref='teslim_ettigi_araclar')
    teslim_alan = db.relationship('User', foreign_keys=[teslim_alan_id], backref='teslim_aldigi_araclar')
    teslim_eden_calisan = db.relationship('Calisan', foreign_keys=[teslim_eden_calisan_id])
    teslim_alan_calisan = db.relationship('Calisan', foreign_keys=[teslim_alan_calisan_id])
    
    def __repr__(self):
        return f'<AracTeslim {self.islem_tipi} {self.arac_id}>'
    
    @property
    def yakit_durumu_display(self):
        yakit_map = {
            'dolu': 'Dolu',
            'uc_ceyrek': '3/4',
            'yarim': '1/2',
            'ceyrek': '1/4',
            'bos': 'Boş'
        }
        return yakit_map.get(self.yakit_durumu, self.yakit_durumu)


# ==================== KAZA FOTOĞRAF ====================
class KazaFotograf(db.Model, TimestampMixin):
    """Kaza fotoğrafları"""
    __tablename__ = 'kaza_fotograflar'
    
    id = db.Column(db.Integer, primary_key=True)
    kaza_id = db.Column(db.Integer, db.ForeignKey('kazalar.id'), nullable=False)
    
    dosya_adi = db.Column(db.String(255), nullable=False)
    dosya_yolu = db.Column(db.String(500), nullable=False)
    dosya_boyut = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    
    aciklama = db.Column(db.String(255))
    yukleyen_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    yukleyen = db.relationship('User', backref='yuklenen_kaza_fotograflari')
    
    def __repr__(self):
        return f'<KazaFotograf {self.kaza_id} {self.dosya_adi}>'


# ==================== İKAME ARAÇ ====================
class IkameArac(db.Model, TimestampMixin, AuditMixin):
    """İkame araç kayıtları"""
    __tablename__ = 'ikame_araclar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Asıl araç (bizim aracımız)
    asil_arac_id = db.Column(db.Integer, db.ForeignKey('araclar.id'), nullable=False)
    
    # İkame araç bilgileri
    plaka = db.Column(db.String(20), nullable=False)
    marka = db.Column(db.String(50))
    model = db.Column(db.String(50))
    
    # Süre
    baslangic_tarihi = db.Column(db.Date, nullable=False)
    bitis_tarihi = db.Column(db.Date)
    
    # Kilometre
    baslangic_km = db.Column(db.Integer)
    bitis_km = db.Column(db.Integer)
    
    # Tedarikçi
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'))
    gunluk_ucret = db.Column(db.Numeric(10, 2))
    
    # Neden
    neden = db.Column(db.String(50))  # kaza, bakim, ariza, diger
    ilgili_kaza_id = db.Column(db.Integer, db.ForeignKey('kazalar.id'))
    
    # Durum
    durum = db.Column(db.String(20), default='aktif')  # aktif, iade_edildi
    
    # Notlar
    notlar = db.Column(db.Text)
    
    # İlişkiler
    asil_arac = db.relationship('Arac', backref=db.backref('ikame_araclar', lazy='dynamic'))
    tedarikci = db.relationship('Tedarikci', backref='ikame_araclar')
    ilgili_kaza = db.relationship('Kaza', backref='ikame_araclar')
    
    def __repr__(self):
        return f'<IkameArac {self.plaka}>'
    
    @property
    def aktif_gun_sayisi(self):
        """Aktif gün sayısını hesapla"""
        bitis = self.bitis_tarihi or date.today()
        return (bitis - self.baslangic_tarihi).days + 1
    
    @property
    def toplam_maliyet(self):
        """Toplam maliyeti hesapla"""
        if self.gunluk_ucret:
            return self.aktif_gun_sayisi * float(self.gunluk_ucret)
        return 0


# ==================== KAZA MODELİ GÜNCELLEMESİ ====================
# Bu alanları mevcut Kaza modeline eklemen gerekiyor:
"""
Kaza modeline eklenecek alanlar:

# Fotoğraflar ilişkisi
fotograflar = db.relationship('KazaFotograf', backref='kaza', lazy='dynamic', cascade='all, delete-orphan')

# Onay sistemi
onay_durumu = db.Column(db.String(20), default='bekliyor')  # bekliyor, onaylandi, reddedildi
onaylayan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
onay_tarihi = db.Column(db.DateTime)
red_nedeni = db.Column(db.Text)

onaylayan = db.relationship('User', foreign_keys=[onaylayan_id], backref='onayladigi_kazalar')
"""


# ==================== VARSAYILAN AKSESUARLAR ====================
VARSAYILAN_AKSESUARLAR = {
    'stepne': 'Stepne',
    'kriko': 'Kriko',
    'bijon_anahtari': 'Bijon Anahtarı',
    'yangin_sondurucu': 'Yangın Söndürücü',
    'ilk_yardim_cantasi': 'İlk Yardım Çantası',
    'reflekto': 'Reflektör',
    'tasit_belgesi': 'Araç Ruhsatı',
    'sigorta_policesi': 'Sigorta Poliçesi',
    'yedek_anahtar': 'Yedek Anahtar',
    'kullanim_kilavuzu': 'Kullanım Kılavuzu',
}
