# -*- coding: utf-8 -*-
"""
TG Portal - Bildirim Sablonlari Modeli
Tum otomatik mail bildirimlerini DB'den yonetilebilir yapar.
"""

from app import db
from app.models.base import TimestampMixin


# Her sablonda kullanilabilir degiskenler - admin UI'da yardim olarak gosterilir
AVAILABLE_VARIABLES = {
    'ISE_GIRIS': [
        'ad_soyad', 'tc_kimlik', 'ise_baslama', 'proje', 'pozisyon',
        'lokasyon', 'sgk_sube', 'sgk_no', 'yonetici', 'telefon', 'email',
    ],
    'ISTEN_CIKIS': [
        'ad_soyad', 'tc_kimlik', 'cikis_tarihi', 'bildirim_tarihi', 'cikis_nedeni',
        'proje', 'pozisyon', 'telefon', 'zimmet_durumu',
        'sgk_cikis_kodu', 'sgk_cikis_aciklama', 'liste_durumu',
    ],
    'ISTEN_CIKIS_BILDIRIMI': [
        'ad_soyad', 'tc_kimlik', 'proje', 'pozisyon', 'cikis_nedeni',
        'son_calisma_gunu', 'bildiren', 'aciklama', 'telefon', 'calisan_url',
    ],
    'SGK_CIKIS_YAPILDI': [
        'ad_soyad', 'tc_kimlik', 'sgk_cikis_tarihi', 'cikis_nedeni',
        'sgk_cikis_kodu', 'proje', 'pozisyon', 'telefon', 'yukleyen',
        'bildirim_tarihi', 'calisan_url',
    ],
    'YENI_BASVURU': [
        'ad_soyad', 'telefon', 'email', 'pozisyon', 'proje', 'lokasyon',
        'kaynak', 'tecrube_yil', 'son_is_yeri', 'son_pozisyon', 'basvuru_url',
    ],
    'SOZLESME_UYARI': [
        'toplam_sayi', 'liste_html',
    ],
    'SGK_GIRIS_TALEBI': [
        'ad_soyad', 'tc_kimlik', 'egitim_durumu', 'planlanan_baslangic', 'proje', 'pozisyon',
        'lokasyon', 'telefon', 'email', 'aday_url', 'aday_link',
    ],
    'SGK_GIRISI_YAPILDI': [
        'ad_soyad', 'tc_kimlik', 'egitim_durumu', 'proje', 'pozisyon', 'lokasyon',
        'sgk_giris_tarihi', 'aday_url', 'aday_link',
    ],
    'SIFRE_SIFIRLAMA': [
        'ad_soyad', 'reset_url', 'gecerlilik',
    ],
    # SMS sablonu - icerik_sablonu SMS metni olarak kullanilir (konu kullanilmaz)
    'ADAY_ONAY_SMS': [
        'ad_soyad', 'evrak_link', 'gun_sayisi',
    ],
    # SMS sablonu - yeni ise giris egitimi kayit daveti
    'EGITIM_DAVET_SMS': [
        'ad_soyad', 'egitim_link', 'egitim_adi',
    ],
    # SMS sablonu - arkadasini davet et (referans) public form daveti
    'REFERANS_DAVET_SMS': [
        'ad_soyad', 'referans_link', 'proje',
    ],
}


class BildirimSablonu(db.Model, TimestampMixin):
    """Otomatik mail bildirim sablonu"""
    __tablename__ = 'bildirim_sablonlari'

    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(50), unique=True, nullable=False, index=True)
    ad = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)

    konu_sablonu = db.Column(db.String(500), nullable=False)
    icerik_sablonu = db.Column(db.Text, nullable=False)

    # JSON array - sabit mail adresleri
    alicilar = db.Column(db.JSON, default=list)

    # Dinamik: bu yetkiye sahip tum aktif userlara da gider (opsiyonel)
    dinamik_alici_rolu = db.Column(db.String(50))

    # Proje koordinatorune de gonder (ileride Proje.koordinator_id eklenince aktif olur)
    proje_yoneticisine_gonder = db.Column(db.Boolean, default=False)

    aktif = db.Column(db.Boolean, default=True, nullable=False)

    @property
    def degiskenler(self):
        """Bu sablon kodu icin kullanilabilir degiskenler"""
        return AVAILABLE_VARIABLES.get(self.kod, [])

    def __repr__(self):
        return f'<BildirimSablonu {self.kod}>'
