# -*- coding: utf-8 -*-
"""
TG Portal - Utility Functions & Decorators
"""

from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def permission_required(permission):
    """
    Belirli bir yetkiyi kontrol eden decorator
    
    Kullanım:
        @permission_required('tedarikci.create')
        def tedarikci_ekle():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bu işlem için giriş yapmalısınız.', 'warning')
                return redirect(url_for('core.login'))
            if not current_user.has_permission(permission):
                flash('Bu işlem için yetkiniz bulunmamaktadır.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Admin yetkisi gerektiren decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bu işlem için giriş yapmalısınız.', 'warning')
            return redirect(url_for('core.login'))
        if not current_user.is_admin:
            flash('Bu işlem için admin yetkisi gereklidir.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def module_access_required(module):
    """
    Modül erişim yetkisi kontrolü
    
    Kullanım:
        @module_access_required('filo')
        def filo_listesi():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bu işlem için giriş yapmalısınız.', 'warning')
                return redirect(url_for('core.login'))
            if not current_user.has_module_access(module):
                flash(f'{module.upper()} modülüne erişim yetkiniz bulunmamaktadır.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Pagination helper
def paginate_query(query, page, per_page=20):
    """SQLAlchemy query'sini paginate eder"""
    return query.paginate(page=page, per_page=per_page, error_out=False)


# Türkçe tarih formatı
def format_date_tr(date):
    """Tarihi Türkçe formatında döndürür"""
    if date is None:
        return '-'
    months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
              'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    return f"{date.day} {months[date.month-1]} {date.year}"


# Para formatı
def format_currency(amount, currency='TRY'):
    """Para miktarını formatlar"""
    if amount is None:
        return '-'
    symbols = {'TRY': '₺', 'USD': '$', 'EUR': '€'}
    symbol = symbols.get(currency, currency)
    return f"{amount:,.2f} {symbol}"


# Enum helper
def enum_choices(enum_class):
    """Enum sınıfını form choices listesine çevirir"""
    return [(e.value, e.name.replace('_', ' ').title()) for e in enum_class]


# ============================================================
# CALISAN SCOPE - Rol bazli liste/detay erisim filtresi
# ============================================================

_FULL_ACCESS_ROLES = {
    'Sistem Yoneticisi', 'Ajans Baskani', 'Direktor',
    'Direktor Yardimcisi', 'Departman Muduru',
}
_COORDINATOR_ROLES = {'Proje Koordinatoru', 'Saha Koordinatoru'}
_TEAM_LEAD_ROLES = {'Takim Lideri'}


def _user_role_names(user):
    return {r.name for r in (user.roles or [])}


def apply_calisan_scope(query, user=None):
    """Calisan query'sine current user'in scope filtresini uygular.
    - Admin / Full-access roller: filtre yok (hepsini gorur)
    - Koordinator (Proje/Saha): yonetici_id == user.calisan_id olanlar + kendisi
    - Takim Lideri: kendi departmanindaki calisanlar
    - Diger roller: sadece kendisi
    - Auth yok / calisan kaydi yok: bos liste
    """
    from app import db
    from app.models.ik import Calisan

    user = user or current_user
    if not user or not user.is_authenticated:
        return query.filter(Calisan.id == -1)

    if user.is_admin:
        return query

    roles = _user_role_names(user)
    if roles & _FULL_ACCESS_ROLES:
        return query

    calisan_id = user.calisan_id
    # Fallback: calisan_id bagli degilse user.email ile Calisan'i bul
    if not calisan_id and user.email:
        c = Calisan.query.filter_by(email=user.email, is_deleted=False).first()
        if c:
            calisan_id = c.id
    if not calisan_id:
        return query.filter(Calisan.id == -1)

    if roles & _COORDINATOR_ROLES:
        return query.filter(
            db.or_(
                Calisan.yonetici_id == calisan_id,
                Calisan.id == calisan_id,
            )
        )

    if roles & _TEAM_LEAD_ROLES:
        me = Calisan.query.get(calisan_id)
        if not me or not me.departman_id:
            return query.filter(Calisan.id == calisan_id)
        return query.filter(Calisan.departman_id == me.departman_id)

    # Diger roller: sadece kendisi
    return query.filter(Calisan.id == calisan_id)


def calisan_in_scope(calisan, user=None):
    """Detay erisim kontrolu - bool dondurur"""
    from app.models.ik import Calisan
    if calisan is None:
        return False
    q = apply_calisan_scope(Calisan.query.filter(Calisan.id == calisan.id), user)
    return q.first() is not None
