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


def admin_or_permission_required(permission):
    """
    Admin VEYA belirli bir yetkiye sahip kullanıcıların erişebildiği decorator

    is_admin=True olan herkes erişir VEYA verilen özel yetkisi (claim/rol) olan erişir.

    Kullanım:
        @admin_or_permission_required('admin.kullanici_yonetimi')
        def admin_kullanicilar():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bu işlem için giriş yapmalısınız.', 'warning')
                return redirect(url_for('core.login'))
            if not (current_user.is_admin or current_user.has_permission(permission)):
                flash('Bu işlem için yetkiniz bulunmamaktadır.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


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
    'Direktor Yardimcisi', 'Departman Muduru', 'IK Uzmani',
    'Muhasebe Uzmani',
}
_COORDINATOR_ROLES = {'Proje Koordinatoru', 'Saha Koordinatoru', 'supervizor'}
_TEAM_LEAD_ROLES = {'Takim Lideri'}


def _user_role_names(user):
    return {r.name for r in (user.roles or [])}


def apply_calisan_scope(query, user=None):
    """Calisan query'sine current user'in scope filtresini uygular.
    - Admin / Full-access roller: filtre yok (hepsini gorur)
    - Koordinator (Proje/Saha): yonetici_id == user.calisan_id + atanan proje kadrolari + kendisi
    - Takim Lideri: kendi departmanindaki calisanlar
    - Diger roller: sadece kendisi
    - Auth yok / calisan kaydi yok: bos liste
    """
    from app import db
    from app.models.ik import Calisan

    user = user or current_user
    if not user or not user.is_authenticated:
        print(f">>> SCOPE: auth yok, bos liste", flush=True)
        return query.filter(Calisan.id == -1)

    if user.is_admin:
        print(f">>> SCOPE: user={user.email} is_admin=True, filtre yok", flush=True)
        return query

    roles = _user_role_names(user)
    print(f">>> SCOPE: user={user.email}, calisan_id={user.calisan_id}, roles={roles}", flush=True)

    if roles & _FULL_ACCESS_ROLES:
        print(f">>> SCOPE: FULL_ACCESS branch, filtre yok", flush=True)
        return query

    calisan_id = user.calisan_id
    # Fallback: calisan_id bagli degilse user.email ile Calisan'i bul
    if not calisan_id and user.email:
        c = Calisan.query.filter_by(email=user.email, is_deleted=False).first()
        if c:
            calisan_id = c.id
            print(f">>> SCOPE: calisan_id fallback (email match) -> {calisan_id}", flush=True)
    if not calisan_id:
        print(f">>> SCOPE: calisan_id yok, bos liste", flush=True)
        return query.filter(Calisan.id == -1)

    if roles & _COORDINATOR_ROLES:
        from app.models.proje import HedefKadro, koordinator_projeler
        atanan_proje_ids = db.session.query(koordinator_projeler.c.proje_id).filter(
            koordinator_projeler.c.koordinator_calisan_id == calisan_id
        )
        atanan_kadro_ids = db.session.query(HedefKadro.id).filter(
            HedefKadro.proje_id.in_(atanan_proje_ids)
        )
        proje_ids_list = [r[0] for r in atanan_proje_ids.all()]
        print(f">>> SCOPE: COORDINATOR branch, calisan_id={calisan_id}, atanan_proje_ids={proje_ids_list}", flush=True)
        return query.filter(
            db.or_(
                Calisan.yonetici_id == calisan_id,
                Calisan.id == calisan_id,
                Calisan.kadro_id.in_(atanan_kadro_ids),
            )
        )

    if roles & _TEAM_LEAD_ROLES:
        print(f">>> SCOPE: TEAM_LEAD branch, calisan_id={calisan_id}", flush=True)
        me = Calisan.query.get(calisan_id)
        if not me or not me.departman_id:
            return query.filter(Calisan.id == calisan_id)
        return query.filter(Calisan.departman_id == me.departman_id)

    # Diger roller: sadece kendisi
    print(f">>> SCOPE: DIGER branch (sadece kendisi), calisan_id={calisan_id}", flush=True)
    return query.filter(Calisan.id == calisan_id)


def calisan_in_scope(calisan, user=None):
    """Detay erisim kontrolu - bool dondurur"""
    from app.models.ik import Calisan
    if calisan is None:
        return False
    q = apply_calisan_scope(Calisan.query.filter(Calisan.id == calisan.id), user)
    return q.first() is not None


# ============================================================
# ADAY SCOPE - Rol bazli aday listesi/detay erisim filtresi
# ============================================================

def apply_aday_scope(query, user=None):
    """Aday query'sine current user'in scope filtresini uygular.
    - Admin / Full-access roller: filtre yok (hepsini gorur)
    - Koordinator (Proje/Saha): atanan projelerin kadrolarina basvuran adaylar
    - Diger roller: bos liste
    """
    from app import db
    from app.models.ik import Aday, Calisan
    from app.models.proje import HedefKadro, koordinator_projeler

    user = user or current_user
    if not user or not user.is_authenticated:
        return query.filter(Aday.id == -1)

    if user.is_admin:
        return query

    roles = _user_role_names(user)

    if roles & _FULL_ACCESS_ROLES:
        return query

    calisan_id = user.calisan_id
    if not calisan_id and user.email:
        c = Calisan.query.filter_by(email=user.email, is_deleted=False).first()
        if c:
            calisan_id = c.id
    if not calisan_id:
        return query.filter(Aday.id == -1)

    if roles & _COORDINATOR_ROLES:
        atanan_proje_ids = db.session.query(koordinator_projeler.c.proje_id).filter(
            koordinator_projeler.c.koordinator_calisan_id == calisan_id
        )
        atanan_kadro_ids = db.session.query(HedefKadro.id).filter(
            HedefKadro.proje_id.in_(atanan_proje_ids)
        )
        return query.filter(Aday.kadro_id.in_(atanan_kadro_ids))

    return query.filter(Aday.id == -1)


def aday_in_scope(aday, user=None):
    """Aday detay erisim kontrolu - bool dondurur"""
    from app.models.ik import Aday
    if aday is None:
        return False
    q = apply_aday_scope(Aday.query.filter(Aday.id == aday.id), user)
    return q.first() is not None


def user_scoped_projeler(user=None):
    """Kullanicinin gorebildigi aktif proje listesini dondurur.
    - Admin / Full-access: tum aktif projeler
    - Koordinator: atanan projeler
    - Diger: bos liste
    """
    from app import db
    from app.models.ik import Calisan
    from app.models.proje import Proje, koordinator_projeler

    user = user or current_user
    if not user or not user.is_authenticated:
        return []

    base_q = Proje.query.filter_by(is_deleted=False, aktif=True).order_by(Proje.ad)

    if user.is_admin:
        return base_q.all()

    roles = _user_role_names(user)
    if roles & _FULL_ACCESS_ROLES:
        return base_q.all()

    calisan_id = user.calisan_id
    if not calisan_id and user.email:
        c = Calisan.query.filter_by(email=user.email, is_deleted=False).first()
        if c:
            calisan_id = c.id
    if not calisan_id:
        return []

    if roles & _COORDINATOR_ROLES:
        proje_ids = [r[0] for r in db.session.query(koordinator_projeler.c.proje_id).filter(
            koordinator_projeler.c.koordinator_calisan_id == calisan_id
        ).all()]
        if not proje_ids:
            return []
        return base_q.filter(Proje.id.in_(proje_ids)).all()

    return []
