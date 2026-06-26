# -*- coding: utf-8 -*-
"""
TG Portal - Onay Sistemi Modelleri
Dinamik onay akışları, paralel onay, yetki devri
"""

from datetime import datetime, date
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin
# Referans tablo -> Model mapping (onay callback için)
REFERANS_MODEL_MAP = {
    'masraflar': {'module': 'app.models.masraf', 'model': 'Masraf', 'durum_field': 'durum', 'onaylandi': 'onaylandi', 'reddedildi': 'reddedildi'},
    'izinler': {'module': 'app.models.ik', 'model': 'Izin', 'durum_field': 'durum', 'onaylandi': 'onaylandi', 'reddedildi': 'reddedildi'},
    'arac_talepleri': {'module': 'app.models.filo', 'model': 'AracTalebi', 'durum_field': 'durum', 'onaylandi': 'onaylandi', 'reddedildi': 'reddedildi'},
    'evraklar': {'module': 'app.models.basvuru', 'model': 'Evrak', 'durum_field': 'durum', 'onaylandi': 'onaylandi', 'reddedildi': 'reddedildi'},
}




class OnayTipi(db.Model, TimestampMixin):
    """Onay tipleri - İzin, Masraf, Araç Talebi vb."""
    __tablename__ = 'onay_tipleri'
    
    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(50), unique=True, nullable=False)  # IZIN, MASRAF, ARAC_TALEBI
    ad = db.Column(db.String(100), nullable=False)
    aciklama = db.Column(db.Text)
    
    # İlgili modül
    modul = db.Column(db.String(50))  # ik, filo, finans
    
    # Varsayılan akış
    varsayilan_akis_id = db.Column(db.Integer, db.ForeignKey('onay_akislari.id'))
    
    aktif = db.Column(db.Boolean, default=True)
    sira = db.Column(db.Integer, default=0)
    
    # İlişkiler
    akislar = db.relationship('OnayAkisi', backref='onay_tipi', lazy='dynamic',
                               foreign_keys='OnayAkisi.onay_tipi_id')
    
    def __repr__(self):
        return f'<OnayTipi {self.kod}>'


class OnayAkisi(db.Model, TimestampMixin, SoftDeleteMixin):
    """Onay akışı tanımı - Hangi adımlardan geçecek"""
    __tablename__ = 'onay_akislari'
    
    id = db.Column(db.Integer, primary_key=True)
    onay_tipi_id = db.Column(db.Integer, db.ForeignKey('onay_tipleri.id'), nullable=False)
    
    ad = db.Column(db.String(100), nullable=False)
    aciklama = db.Column(db.Text)
    
    # Koşullar (JSON) - hangi durumlarda bu akış kullanılır
    # Örn: {"min_tutar": 1000, "departman_id": 5}
    kosullar = db.Column(db.JSON)
    
    # Öncelik - koşul eşleşmesinde hangisi seçilecek
    oncelik = db.Column(db.Integer, default=0)
    
    aktif = db.Column(db.Boolean, default=True)
    
    # İlişkiler
    adimlar = db.relationship('OnayAdimi', backref='akis', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='OnayAdimi.sira')
    
    @property
    def adim_sayisi(self):
        return self.adimlar.count()
    
    def __repr__(self):
        return f'<OnayAkisi {self.ad}>'


class OnayAdimi(db.Model, TimestampMixin):
    """Onay adımı - Akıştaki her bir onay noktası"""
    __tablename__ = 'onay_adimlari'
    
    id = db.Column(db.Integer, primary_key=True)
    akis_id = db.Column(db.Integer, db.ForeignKey('onay_akislari.id'), nullable=False)
    
    ad = db.Column(db.String(100), nullable=False)
    sira = db.Column(db.Integer, default=0)
    
    # Onaylayıcı tipi
    onaylayici_tipi = db.Column(db.String(20), nullable=False)
    # Değerler: 
    # - 'rol': Belirli bir rol (ör: yonetici, ik_muduru)
    # - 'kullanici': Belirli bir kullanıcı
    # - 'yonetici': Talep edenin yöneticisi
    # - 'departman_yoneticisi': Talep edenin departman yöneticisi
    # - 'proje_yoneticisi': Talep edenin proje yöneticisi
    
    # Onaylayıcı değeri (tipi'ne göre)
    onaylayici_rol = db.Column(db.String(50))  # rol adı
    onaylayici_kullanici_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Paralel onay - aynı sıradaki adımlar paralel mi?
    paralel = db.Column(db.Boolean, default=False)
    
    # Tümü mü yoksa biri mi onaylamalı (paralel için)
    tumu_onaymali = db.Column(db.Boolean, default=False)
    
    # Otomatik onay süresi (saat) - süre dolunca otomatik onayla
    otomatik_onay_sure = db.Column(db.Integer)
    
    # Atlanabilir mi?
    atlanabilir = db.Column(db.Boolean, default=False)
    
    # Koşullu adım (JSON) - bu adım ne zaman aktif
    kosul = db.Column(db.JSON)
    
    # İlişkiler
    onaylayici_kullanici = db.relationship('User', foreign_keys=[onaylayici_kullanici_id])
    
    def __repr__(self):
        return f'<OnayAdimi {self.ad} (Sıra:{self.sira})>'


class OnayTalebi(db.Model, TimestampMixin, SoftDeleteMixin):
    """Onay talebi - Oluşturulan her talep"""
    __tablename__ = 'onay_talepleri'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Talep bilgileri
    onay_tipi_id = db.Column(db.Integer, db.ForeignKey('onay_tipleri.id'), nullable=False)
    akis_id = db.Column(db.Integer, db.ForeignKey('onay_akislari.id'), nullable=False)
    
    # Referans (hangi kayıt için talep)
    referans_tablo = db.Column(db.String(50), nullable=False)  # izinler, masraflar, arac_talepleri
    referans_id = db.Column(db.Integer, nullable=False)
    
    # Talep eden
    talep_eden_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    talep_tarihi = db.Column(db.DateTime, default=datetime.now)
    
    # Durum
    durum = db.Column(db.String(20), default='bekliyor')
    # Değerler: bekliyor, onaylandi, reddedildi, iptal
    
    # Mevcut adım
    mevcut_adim = db.Column(db.Integer, default=1)
    
    # Sonuç
    sonuc_tarihi = db.Column(db.DateTime)
    sonuc_notu = db.Column(db.Text)
    
    # Aciliyet
    acil = db.Column(db.Boolean, default=False)
    
    # İlişkiler
    onay_tipi = db.relationship('OnayTipi')
    akis = db.relationship('OnayAkisi')
    talep_eden = db.relationship('User', foreign_keys=[talep_eden_id])
    kayitlar = db.relationship('OnayKaydi', backref='talep', lazy='dynamic',
                                cascade='all, delete-orphan', order_by='OnayKaydi.created_at')
    
    @property
    def durum_text(self):
        durum_map = {
            'bekliyor': 'Onay Bekliyor',
            'onaylandi': 'Onaylandı',
            'reddedildi': 'Reddedildi',
            'iptal': 'İptal Edildi'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        renk_map = {
            'bekliyor': 'warning',
            'onaylandi': 'success',
            'reddedildi': 'danger',
            'iptal': 'secondary'
        }
        return renk_map.get(self.durum, 'secondary')
    
    @property
    def bekleyen_onaycilar(self):
        """Şu an bekleyen onayıcıları döndür"""
        return self.kayitlar.filter_by(durum='bekliyor').all()
    
    @property
    def timeline(self):
        """Onay geçmişi timeline"""
        return self.kayitlar.order_by(OnayKaydi.created_at).all()
    
    def __repr__(self):
        return f'<OnayTalebi {self.id} - {self.onay_tipi.kod if self.onay_tipi else "?"}>'


class OnayKaydi(db.Model, TimestampMixin):
    """Onay kaydı - Her adım için onay/red kaydı"""
    __tablename__ = 'onay_kayitlari'
    
    id = db.Column(db.Integer, primary_key=True)
    talep_id = db.Column(db.Integer, db.ForeignKey('onay_talepleri.id'), nullable=False)
    adim_id = db.Column(db.Integer, db.ForeignKey('onay_adimlari.id'), nullable=False)
    
    # Onaylayıcı
    onaylayici_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Vekil onay
    vekil_mi = db.Column(db.Boolean, default=False)
    asil_onaylayici_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Durum
    durum = db.Column(db.String(20), default='bekliyor')
    # Değerler: bekliyor, onaylandi, reddedildi, atlandi
    
    # Tarihler
    islem_tarihi = db.Column(db.DateTime)
    
    # Not
    not_ = db.Column(db.Text)
    
    # İlişkiler
    adim = db.relationship('OnayAdimi')
    onaylayici = db.relationship('User', foreign_keys=[onaylayici_id])
    asil_onaylayici = db.relationship('User', foreign_keys=[asil_onaylayici_id])
    
    @property
    def durum_text(self):
        durum_map = {
            'bekliyor': 'Bekliyor',
            'onaylandi': 'Onayladı',
            'reddedildi': 'Reddetti',
            'atlandi': 'Atlandı'
        }
        return durum_map.get(self.durum, self.durum)
    
    @property
    def durum_renk(self):
        renk_map = {
            'bekliyor': 'warning',
            'onaylandi': 'success',
            'reddedildi': 'danger',
            'atlandi': 'secondary'
        }
        return renk_map.get(self.durum, 'secondary')
    
    def __repr__(self):
        return f'<OnayKaydi Talep:{self.talep_id} Adim:{self.adim_id}>'


class YetkiDevri(db.Model, TimestampMixin):
    """Yetki devri - Tatil, izin vb. durumlarda onay yetkisi devri"""
    __tablename__ = 'yetki_devirleri'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Devreden
    devreden_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Devralan
    devralan_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Süre
    baslangic_tarihi = db.Column(db.Date, nullable=False)
    bitis_tarihi = db.Column(db.Date, nullable=False)
    
    # Kapsam (hangi onay tipleri için)
    tum_tipler = db.Column(db.Boolean, default=True)
    onay_tipi_ids = db.Column(db.JSON)  # [1, 2, 3] - belirli tipler için
    
    # Durum
    aktif = db.Column(db.Boolean, default=True)
    neden = db.Column(db.Text)  # Yıllık izin, seyahat vb.
    
    # İlişkiler
    devreden = db.relationship('User', foreign_keys=[devreden_id], backref='verdigi_yetkiler')
    devralan = db.relationship('User', foreign_keys=[devralan_id], backref='aldigi_yetkiler')
    
    @property
    def gecerli_mi(self):
        """Yetki devri şu an geçerli mi?"""
        if not self.aktif:
            return False
        bugun = date.today()
        return self.baslangic_tarihi <= bugun <= self.bitis_tarihi
    
    def __repr__(self):
        return f'<YetkiDevri {self.devreden_id} -> {self.devralan_id}>'


# ============================================================
# ONAY SERVİS FONKSİYONLARI
# ============================================================

class OnayServisi:
    """Onay işlemlerini yöneten servis sınıfı"""
    
    @staticmethod
    def talep_olustur(onay_tipi_kod, referans_tablo, referans_id, talep_eden_id, acil=False):
        """
        Yeni onay talebi oluştur
        Returns: OnayTalebi veya None (hata durumunda)
        """
        # Onay tipini bul
        onay_tipi = OnayTipi.query.filter_by(kod=onay_tipi_kod, aktif=True).first()
        if not onay_tipi:
            return None, "Onay tipi bulunamadı"
        
        # Uygun akışı bul (şimdilik varsayılan)
        akis = OnayAkisi.query.filter_by(
            onay_tipi_id=onay_tipi.id, 
            aktif=True, 
            is_deleted=False
        ).order_by(OnayAkisi.oncelik.desc()).first()
        
        if not akis:
            return None, "Onay akışı bulunamadı"
        
        # Talep oluştur
        talep = OnayTalebi(
            onay_tipi_id=onay_tipi.id,
            akis_id=akis.id,
            referans_tablo=referans_tablo,
            referans_id=referans_id,
            talep_eden_id=talep_eden_id,
            acil=acil
        )
        db.session.add(talep)
        db.session.flush()
        
        # İlk adım için onay kayıtları oluştur
        OnayServisi._adim_kayitlari_olustur(talep, 1)
        
        db.session.commit()
        return talep, None
    
    @staticmethod
    def _adim_kayitlari_olustur(talep, adim_sira):
        """Belirli adım için onay kayıtlarını oluştur"""
        from app.models.core import User
        
        adimlar = talep.akis.adimlar.filter_by(sira=adim_sira).all()
        
        for adim in adimlar:
            # Onaylayıcıyı belirle
            onaylayici_id = OnayServisi._onaylayici_bul(adim, talep.talep_eden_id)
            
            if onaylayici_id:
                # Yetki devri kontrolü
                vekil_id = OnayServisi._vekil_kontrol(onaylayici_id, talep.onay_tipi_id)
                
                kayit = OnayKaydi(
                    talep_id=talep.id,
                    adim_id=adim.id,
                    onaylayici_id=vekil_id or onaylayici_id,
                    vekil_mi=vekil_id is not None,
                    asil_onaylayici_id=onaylayici_id if vekil_id else None
                )
                db.session.add(kayit)
    
    @staticmethod
    def _onaylayici_bul(adim, talep_eden_id):
        """Adım için onaylayıcıyı bul - Fallback mekanizması ile"""
        from app.models.core import User
        from app.models.ik import Calisan
        
        onaylayici_id = None
        
        if adim.onaylayici_tipi == 'kullanici':
            # Sabit kullanıcı
            onaylayici_id = adim.onaylayici_kullanici_id
        
        elif adim.onaylayici_tipi == 'yonetici':
            # Talep edenin direkt yöneticisi
            user = User.query.get(talep_eden_id)
            calisan = user.calisan if user else None
            if calisan and calisan.yonetici_id:
                yonetici = Calisan.query.get(calisan.yonetici_id)
                if yonetici and yonetici.user_account:
                    onaylayici_id = yonetici.user_account.id
        
        elif adim.onaylayici_tipi == 'departman_yoneticisi':
            # Departman yöneticisi
            user = User.query.get(talep_eden_id)
            calisan = user.calisan if user else None
            if calisan and calisan.departman and calisan.departman.yonetici_id:
                yonetici = Calisan.query.get(calisan.departman.yonetici_id)
                if yonetici and yonetici.user_account:
                    onaylayici_id = yonetici.user_account.id
        
        elif adim.onaylayici_tipi == 'rol':
            # Belirli roldeki kullanıcı
            user = User.query.join(User.roles).filter_by(name=adim.onaylayici_rol).first()
            if user:
                onaylayici_id = user.id
        
        # ============================================================
        # FALLBACK MEKANİZMASI
        # Yönetici bulunamazsa, sırasıyla şunları dene:
        # 1. onay_yetkilisi rolü
        # 2. ik_yonetici rolü  
        # 3. Admin kullanıcı
        # ============================================================
        if onaylayici_id is None and adim.onaylayici_tipi in ['yonetici', 'departman_yoneticisi']:
            # Log için (opsiyonel)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Onaylayıcı bulunamadı (tip: {adim.onaylayici_tipi}, talep_eden: {talep_eden_id}). Fallback deneniyor...")
            
            # Fallback 1: onay_yetkilisi rolü
            fallback_user = User.query.join(User.roles).filter_by(name='onay_yetkilisi').filter(User.is_active == True).first()
            
            # Fallback 2: ik_yonetici rolü
            if not fallback_user:
                fallback_user = User.query.join(User.roles).filter_by(name='ik_yonetici').filter(User.is_active == True).first()
            
            # Fallback 3: Herhangi bir admin
            if not fallback_user:
                fallback_user = User.query.filter_by(is_admin=True, is_active=True).first()
            
            if fallback_user:
                onaylayici_id = fallback_user.id
                logger.info(f"Fallback onaylayıcı atandı: {fallback_user.email}")
        
        return onaylayici_id
    
    @staticmethod
    def _vekil_kontrol(onaylayici_id, onay_tipi_id):
        """Yetki devri var mı kontrol et"""
        bugun = date.today()
        
        devir = YetkiDevri.query.filter(
            YetkiDevri.devreden_id == onaylayici_id,
            YetkiDevri.aktif == True,
            YetkiDevri.baslangic_tarihi <= bugun,
            YetkiDevri.bitis_tarihi >= bugun
        ).first()
        
        if devir:
            # Tip kontrolü
            if devir.tum_tipler:
                return devir.devralan_id
            elif devir.onay_tipi_ids and onay_tipi_id in devir.onay_tipi_ids:
                return devir.devralan_id
        
        return None
    
    @staticmethod
    def onayla(kayit_id, onaylayici_id, not_=None):
        """Onay kaydını onayla"""
        kayit = OnayKaydi.query.get(kayit_id)
        if not kayit:
            return False, "Kayıt bulunamadı"
        
        if kayit.onaylayici_id != onaylayici_id:
            return False, "Bu kaydı onaylama yetkiniz yok"
        
        if kayit.durum != 'bekliyor':
            return False, "Bu kayıt zaten işlem görmüş"
        
        # Onayla
        kayit.durum = 'onaylandi'
        kayit.islem_tarihi = datetime.now()
        kayit.not_ = not_
        
        # Sonraki adıma geç
        talep = kayit.talep
        OnayServisi._sonraki_adim_kontrol(talep)
        
        # Talep tamamlandıysa referans kaydı güncelle
        if talep.durum == 'onaylandi':
            OnayServisi._referans_guncelle(talep, 'onaylandi')
        
        db.session.commit()
        return True, None
    
    @staticmethod
    def reddet(kayit_id, onaylayici_id, not_=None):
        """Onay kaydını reddet"""
        kayit = OnayKaydi.query.get(kayit_id)
        if not kayit:
            return False, "Kayıt bulunamadı"
        
        if kayit.onaylayici_id != onaylayici_id:
            return False, "Bu kaydı reddetme yetkiniz yok"
        
        if kayit.durum != 'bekliyor':
            return False, "Bu kayıt zaten işlem görmüş"
        
        # Reddet
        kayit.durum = 'reddedildi'
        kayit.islem_tarihi = datetime.now()
        kayit.not_ = not_
        
        # Talebi reddet
        talep = kayit.talep
        talep.durum = 'reddedildi'
        talep.sonuc_tarihi = datetime.now()
        talep.sonuc_notu = not_
        
        # Referans kaydı güncelle
        OnayServisi._referans_guncelle(talep, 'reddedildi')
        
        db.session.commit()
        return True, None
    
    @staticmethod
    def _sonraki_adim_kontrol(talep):
        """Mevcut adım tamamlandı mı, sonraki adıma geçilmeli mi kontrol et"""
        mevcut_adim = talep.mevcut_adim
        
        # Mevcut adımdaki tüm kayıtlar
        mevcut_kayitlar = talep.kayitlar.join(OnayAdimi).filter(OnayAdimi.sira == mevcut_adim).all()
        
        if not mevcut_kayitlar:
            # Adım yok, talebi onayla
            talep.durum = 'onaylandi'
            talep.sonuc_tarihi = datetime.now()
            return
        
        # Bekleyen var mı?
        bekleyenler = [k for k in mevcut_kayitlar if k.durum == 'bekliyor']
        onaylananlar = [k for k in mevcut_kayitlar if k.durum == 'onaylandi']
        
        # Paralel onay kontrolü
        adim = mevcut_kayitlar[0].adim
        
        if adim.tumu_onaymali:
            # Tümü onaylamalı
            if len(bekleyenler) == 0 and len(onaylananlar) == len(mevcut_kayitlar):
                # Sonraki adıma geç
                OnayServisi._sonraki_adima_gec(talep)
        else:
            # Biri onaylamalı yeterli
            if len(onaylananlar) > 0:
                # Diğer bekleyenleri atla
                for k in bekleyenler:
                    k.durum = 'atlandi'
                    k.islem_tarihi = datetime.now()
                # Sonraki adıma geç
                OnayServisi._sonraki_adima_gec(talep)
    
    @staticmethod
    def _sonraki_adima_gec(talep):
        """Sonraki adıma geç"""
        mevcut_adim = talep.mevcut_adim
        
        # Sonraki adım var mı?
        sonraki_adim = talep.akis.adimlar.filter(OnayAdimi.sira > mevcut_adim).order_by(OnayAdimi.sira).first()
        
        if sonraki_adim:
            talep.mevcut_adim = sonraki_adim.sira
            OnayServisi._adim_kayitlari_olustur(talep, sonraki_adim.sira)
        else:
            # Son adımdı, talebi onayla
            talep.durum = 'onaylandi'
            talep.sonuc_tarihi = datetime.now()
    

    @staticmethod
    def _referans_guncelle(talep, yeni_durum):
        """Onay talebiyle ilişkili referans kaydın durumunu güncelle."""
        referans_tablo = talep.referans_tablo
        referans_id = talep.referans_id
        
        if referans_tablo not in REFERANS_MODEL_MAP:
            import logging
            logging.getLogger(__name__).warning(f"Bilinmeyen referans tablo: {referans_tablo}")
            return
        
        config = REFERANS_MODEL_MAP[referans_tablo]
        
        try:
            import importlib
            module = importlib.import_module(config['module'])
            Model = getattr(module, config['model'])
            
            kayit = Model.query.get(referans_id)
            if kayit:
                durum_field = config['durum_field']
                yeni_deger = config.get(yeni_durum, yeni_durum)
                setattr(kayit, durum_field, yeni_deger)
                
                import logging
                logging.getLogger(__name__).info(f"Referans güncellendi: {referans_tablo}#{referans_id} -> {yeni_deger}")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Referans güncelleme hatası: {e}")

    @staticmethod
    def bekleyen_onaylar(kullanici_id):
        """Kullanıcının bekleyen onaylarını getir"""
        return OnayKaydi.query.filter_by(
            onaylayici_id=kullanici_id,
            durum='bekliyor'
        ).join(OnayTalebi).filter(
            OnayTalebi.durum == 'bekliyor'
        ).order_by(OnayTalebi.acil.desc(), OnayTalebi.talep_tarihi).all()
    
    @staticmethod
    def kullanici_talepleri(kullanici_id, durum=None):
        """Kullanıcının kendi taleplerini getir"""
        query = OnayTalebi.query.filter_by(talep_eden_id=kullanici_id, is_deleted=False)
        if durum:
            query = query.filter_by(durum=durum)
        return query.order_by(OnayTalebi.talep_tarihi.desc()).all()
