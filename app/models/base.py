# -*- coding: utf-8 -*-
"""
TG Portal - Base Models & Mixins
"""

from datetime import datetime
from app import db


class TimestampMixin:
    """Oluşturma ve güncelleme zamanı için mixin"""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SoftDeleteMixin:
    """Soft delete için mixin"""
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def soft_delete(self, user_id=None):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user_id


class AuditMixin:
    """Audit trail için mixin"""
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


# Enum tanımlamaları
import enum

class TedarikciTipi(enum.Enum):
    SERVIS = 'servis'
    YAKIT = 'yakit'
    SIGORTA = 'sigorta'
    YEDEK_PARCA = 'yedek_parca'
    GENEL = 'genel'
    KIRA = 'kira'
    DIGER = 'diger'


class AracDurumu(enum.Enum):
    AKTIF = 'aktif'
    BAKIM = 'bakim'
    ARIZALI = 'arizali'
    SATILDI = 'satildi'
    HURDA = 'hurda'


class YakitTipi(enum.Enum):
    BENZIN = 'benzin'
    DIZEL = 'dizel'
    LPG = 'lpg'
    ELEKTRIK = 'elektrik'
    HIBRIT = 'hibrit'


class IslemTipi(enum.Enum):
    BAKIM = 'bakim'
    TAMIR = 'tamir'
    SIGORTA = 'sigorta'
    MUAYENE = 'muayene'
    KAZA = 'kaza'
    YAKIT = 'yakit'
    DIGER = 'diger'


class CalisanDurumu(enum.Enum):
    ADAY = 'aday'
    AKTIF = 'aktif'
    IZINLI = 'izinli'
    ASKIYA_ALINDI = 'askiya_alindi'
    AYRILDI = 'ayrildi'
