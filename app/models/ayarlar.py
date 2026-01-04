# -*- coding: utf-8 -*-
"""
TG Portal - Ayarlar Modülü Modelleri
Sistem konfigürasyonu ve genel ayarlar
"""

from datetime import datetime
from app import db
from app.models.base import TimestampMixin


class SistemAyar(db.Model, TimestampMixin):
    """Anahtar-değer bazlı sistem ayarları"""
    __tablename__ = 'sistem_ayarlari'
    
    id = db.Column(db.Integer, primary_key=True)
    
    kategori = db.Column(db.String(50), nullable=False, default='genel')
    # genel, email, bildirim, guvenlik, entegrasyon
    
    anahtar = db.Column(db.String(100), nullable=False, unique=True)
    deger = db.Column(db.Text)
    
    tip = db.Column(db.String(20), default='text')
    # text, number, boolean, json, password
    
    aciklama = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<SistemAyar {self.anahtar}>'
    
    @staticmethod
    def get(anahtar, varsayilan=None):
        """Ayar değerini getir"""
        ayar = SistemAyar.query.filter_by(anahtar=anahtar).first()
        if ayar:
            if ayar.tip == 'boolean':
                return ayar.deger.lower() in ('true', '1', 'evet', 'yes')
            elif ayar.tip == 'number':
                try:
                    return int(ayar.deger) if '.' not in ayar.deger else float(ayar.deger)
                except:
                    return varsayilan
            return ayar.deger
        return varsayilan
    
    @staticmethod
    def set(anahtar, deger, kategori='genel', tip='text', aciklama=None):
        """Ayar değerini kaydet"""
        ayar = SistemAyar.query.filter_by(anahtar=anahtar).first()
        if ayar:
            ayar.deger = str(deger)
            if tip:
                ayar.tip = tip
            if aciklama:
                ayar.aciklama = aciklama
        else:
            ayar = SistemAyar(
                anahtar=anahtar,
                deger=str(deger),
                kategori=kategori,
                tip=tip,
                aciklama=aciklama
            )
            db.session.add(ayar)
        db.session.commit()
        return ayar


class AktiviteLog(db.Model):
    """Kullanıcı aktivite logları"""
    __tablename__ = 'aktivite_loglari'
    
    id = db.Column(db.Integer, primary_key=True)
    
    kullanici_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    eylem = db.Column(db.String(50), nullable=False)
    # login, logout, create, update, delete, view, export
    
    modul = db.Column(db.String(50))
    # ik, masraf, sozlesme, talep, satinalma vb.
    
    aciklama = db.Column(db.String(255))
    
    # Detay (JSON olarak)
    detay = db.Column(db.Text)
    
    ip_adresi = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    
    tarih = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişki
    kullanici = db.relationship('User', backref=db.backref('aktiviteler', lazy='dynamic'))
    
    def __repr__(self):
        return f'<AktiviteLog {self.eylem}>'
    
    @staticmethod
    def kaydet(kullanici_id, eylem, modul=None, aciklama=None, detay=None, request=None):
        """Aktivite kaydı oluştur"""
        log = AktiviteLog(
            kullanici_id=kullanici_id,
            eylem=eylem,
            modul=modul,
            aciklama=aciklama,
            detay=detay
        )
        
        if request:
            log.ip_adresi = request.remote_addr
            log.user_agent = request.user_agent.string[:255] if request.user_agent else None
        
        db.session.add(log)
        db.session.commit()
        return log


# ============================================================
# VARSAYILAN AYARLAR
# ============================================================

VARSAYILAN_AYARLAR = [
    # Genel
    ('sirket_adi', 'Team Guerilla', 'genel', 'text', 'Şirket adı'),
    ('sirket_logo', '', 'genel', 'text', 'Logo dosya yolu'),
    ('sayfa_basina_kayit', '20', 'genel', 'number', 'Listelerde sayfa başına kayıt'),
    
    # E-posta
    ('email_aktif', 'false', 'email', 'boolean', 'E-posta bildirimleri aktif'),
    ('smtp_host', '', 'email', 'text', 'SMTP sunucu'),
    ('smtp_port', '587', 'email', 'number', 'SMTP port'),
    ('smtp_user', '', 'email', 'text', 'SMTP kullanıcı'),
    ('smtp_password', '', 'email', 'password', 'SMTP şifre'),
    ('email_gonderen', '', 'email', 'text', 'Gönderen e-posta'),
    
    # Bildirim
    ('bildirim_masraf_onay', 'true', 'bildirim', 'boolean', 'Masraf onay bildirimi'),
    ('bildirim_talep_yeni', 'true', 'bildirim', 'boolean', 'Yeni talep bildirimi'),
    ('bildirim_sozlesme_bitis', 'true', 'bildirim', 'boolean', 'Sözleşme bitiş uyarısı'),
    
    # Güvenlik
    ('oturum_suresi', '480', 'guvenlik', 'number', 'Oturum süresi (dakika)'),
    ('sifre_min_uzunluk', '8', 'guvenlik', 'number', 'Minimum şifre uzunluğu'),
    ('giris_deneme_limiti', '5', 'guvenlik', 'number', 'Başarısız giriş limiti'),
]


def varsayilan_ayarlari_yukle():
    """Varsayılan ayarları yükle"""
    for anahtar, deger, kategori, tip, aciklama in VARSAYILAN_AYARLAR:
        mevcut = SistemAyar.query.filter_by(anahtar=anahtar).first()
        if not mevcut:
            ayar = SistemAyar(
                anahtar=anahtar,
                deger=deger,
                kategori=kategori,
                tip=tip,
                aciklama=aciklama
            )
            db.session.add(ayar)
    db.session.commit()
