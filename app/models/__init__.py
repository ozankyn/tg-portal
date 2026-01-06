# -*- coding: utf-8 -*-
"""
TG Portal - Models Package
Import order matters for SQLAlchemy relationships!
"""
# Base'i önce import et
from app.models.base import (
    TimestampMixin, 
    SoftDeleteMixin, 
    AuditMixin,
    CalisanDurumu,
    AracDurumu,
    YakitTipi,
    IslemTipi
)
# Core models
from app.models.core import User, Role, Permission, AuditLog
# İK models
from app.models.ik import (
    Departman,
    Pozisyon,
    Calisan,
    Aday,
    Izin
)
# Tedarikçi
from app.models.tedarikci import Tedarikci
# Proje models (Filo'dan önce import edilmeli!)
from app.models.proje import Musteri, Proje, HedefKadro
# Filo models (Proje'den sonra)
from app.models.filo import (
    Arac,
    FiloIslem,
    YakitKayit,
    Sigorta,
    Muayene,
    Kaza
)
# Egitim models
from app.models.egitim import (
    EgitimTipi,
    Egitim,
    EgitimKatilimci,
    EgitimMateryali,
    CalisanZorunluEgitim,
    PozisyonZorunluEgitim
)

# Quiz models
from app.models.quiz import (
    SoruKategorisi,
    Soru,
    SoruSecenegi,
    Test,
    TestSorusu,
    TestSonuc,
    TestCevap
)

# Onay models
from app.models.onay import (
    OnayTipi, OnayAkisi, OnayAdimi, 
    OnayTalebi, OnayKaydi, YetkiDevri,
    OnayServisi
)

from app.models.masraf import (
    MasrafKategorisi, Masraf, MasrafKalemi, MasrafAvans,
    get_calisan_masraf_ozeti
)

from app.models.sozlesme import (
    SozlesmeTipi, Sozlesme, SozlesmeEk,
    get_yaklasan_sozlesmeler, get_sona_eren_sozlesmeler
)

from app.models.satinalma import (
    SatinAlmaKategorisi, SatinAlmaTalebi, TalepKalemi,
    SatinAlmaTeklif, TeklifKalemi, SatinAlmaSiparisi, SiparisTeslimat
)

from app.models.talep import (
    TalepKategorisi, Talep, TalepYorum,
    get_acik_talepler, get_talep_istatistikleri
)

from app.models.ayarlar import (
    SistemAyar, AktiviteLog, varsayilan_ayarlari_yukle
)

from app.models.egitim import (
        EgitimTipi, Egitim, EgitimKatilimci, EgitimMateryali,
        CalisanZorunluEgitim, PozisyonZorunluEgitim
    )

__all__ = [
    # Base
    'TimestampMixin',
    'SoftDeleteMixin', 
    'AuditMixin',
    'CalisanDurumu',
    'AracDurumu',
    'YakitTipi',
    'IslemTipi',
    # Core
    'User',
    'Role',
    'Permission',
    'AuditLog',
    # İK
    'Departman',
    'Pozisyon',
    'Calisan',
    'Aday',
    'Izin',
    # Tedarikçi
    'Tedarikci',
    # Proje
    'Musteri',
    'Proje',
    'HedefKadro',
    # Filo
    'Arac',
    'FiloIslem',
    'YakitKayit',
    'Sigorta',
    'Muayene',
    'Kaza',
    # Egitim
    'EgitimTipi',
    'Egitim',
    'EgitimKatilimci',
    'EgitimMateryali',
    'CalisanZorunluEgitim',
    'PozisyonZorunluEgitim',
    # Quiz
    'SoruKategorisi',
    'Soru',
    'SoruSecenegi',
    'Test',
    'TestSorusu',
    'TestSonuc',
    'TestCevap',
]
