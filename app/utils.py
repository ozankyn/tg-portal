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
