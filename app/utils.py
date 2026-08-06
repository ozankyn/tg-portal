# -*- coding: utf-8 -*-
"""
TG Portal - Utility Functions & Decorators
"""

import re
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


def any_permission_required(*permissions):
    """
    Verilen yetkilerden EN AZ BİRİNE sahip kullanıcıların erişebildiği decorator

    Kullanım:
        @any_permission_required('ik.edit', 'egitim.edit')
        def davet_sms_liste(id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bu işlem için giriş yapmalısınız.', 'warning')
                return redirect(url_for('core.login'))
            if not any(current_user.has_permission(p) for p in permissions):
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
# TELEFON NORMALIZASYONU
# ============================================================

def normalize_telefon(telefon):
    """Türk cep telefonu numarasını 05XXXXXXXXX formatına çevirir.

    Rakam dışındaki TÜM karakterler baştan temizlenir: boşluk, tire, parantez,
    nokta, slash, artı, harfler ve Excel/kopyala-yapıştır ile gelen görünmez
    unicode kontrol karakterleri (\\u202a LRE, \\u202c PDF, \\u200e LRM, NBSP vb.).
    Ardından +90 / 90 / 0090 önekleri 0'a indirgenir; başında 0 olmayan 10 haneli
    5XX numaralara 0 eklenir.

    Geçerli bir cep numarası üretilemezse None döner (sabit hat, eksik hane,
    birden fazla numara içeren giriş vb.).

    >>> normalize_telefon('+90 (532) 123 45 67')
    '05321234567'
    >>> normalize_telefon('\\u202a+90 532 123 45 67\\u202c')
    '05321234567'
    >>> normalize_telefon('5321234567')
    '05321234567'
    >>> normalize_telefon('2123456789') is None   # sabit hat
    True
    """
    if telefon is None:
        return None

    # Rakam dışındaki her şeyi at. [^0-9] kullanılıyor ([^\d] değil): \d unicode
    # modda Arapça-Hint rakamlarını da eşleştirir ve numaraya sızmalarına izin verir.
    s = re.sub(r'[^0-9]', '', str(telefon))
    if not s:
        return None

    # Uluslararası önek: 0090XXXXXXXXXX -> 0XXXXXXXXXX
    # (+90 zaten rakam temizliğinde 90 önekine indi, aşağıda ele alınıyor)
    if s.startswith('0090'):
        s = '0' + s[4:]

    # 905XXXXXXXXX (12 hane) -> 05XXXXXXXXX
    if s.startswith('90') and len(s) == 12:
        s = '0' + s[2:]

    # 5XXXXXXXXX (10 hane) -> 05XXXXXXXXX
    if s.startswith('5') and len(s) == 10:
        s = '0' + s

    # Sonuç 05XXXXXXXXX (11 hane) değilse geçersiz
    if len(s) == 11 and s.startswith('05'):
        return s
    return None


# ============================================================
# SMS METİN YARDIMCILARI
# ============================================================

# Türkçe -> ASCII karakter eşlemesi (GSM-7 alfabesine sığması için)
_TR_ASCII = str.maketrans({
    'ç': 'c', 'Ç': 'C', 'ğ': 'g', 'Ğ': 'G', 'ı': 'i', 'İ': 'I',
    'ö': 'o', 'Ö': 'O', 'ş': 's', 'Ş': 'S', 'ü': 'u', 'Ü': 'U',
    'â': 'a', 'Â': 'A', 'î': 'i', 'Î': 'I', 'û': 'u', 'Û': 'U',
})


def sms_ascii(metin):
    """SMS metnindeki Türkçe karakterleri ASCII karşılıklarına çevirir.

    Türkçe karakter içeren SMS UCS-2 ile gönderilir ve segment başına
    70 karaktere düşer; saf ASCII metin GSM-7 ile 160 karakter/segment
    gider. Maliyeti yarıdan fazla düşürür.
    """
    if not metin:
        return metin
    donusen = str(metin).translate(_TR_ASCII)
    # Eşlemede olmayan diğer non-ASCII karakterleri de ayıkla
    return donusen.encode('ascii', 'ignore').decode('ascii')


def sms_turkce_mi(metin):
    """Metin GSM-7 dışı (Türkçe/unicode) karakter içeriyor mu?"""
    if not metin:
        return False
    try:
        str(metin).encode('ascii')
        return False
    except UnicodeEncodeError:
        return True


def sms_segment_sayisi(metin):
    """SMS'in kaç segment (kredi) tutacağını hesaplar.

    ASCII (GSM-7): 160 tek segment, çok parçalıda 153/segment
    Türkçe (UCS-2): 70 tek segment, çok parçalıda 67/segment
    """
    if not metin:
        return 0
    uzunluk = len(str(metin))
    if sms_turkce_mi(metin):
        tek, coklu = 70, 67
    else:
        tek, coklu = 160, 153
    if uzunluk <= tek:
        return 1
    return -(-uzunluk // coklu)  # ceil


# ============================================================
# CALISAN SCOPE - Rol bazli liste/detay erisim filtresi
# ============================================================

_FULL_ACCESS_ROLES = {
    'Sistem Yoneticisi', 'Ajans Baskani', 'Direktor',
    'Direktor Yardimcisi', 'Departman Muduru', 'IK Uzmani',
    'Muhasebe Uzmani', 'Butce Raporlama Uzmani',
}
_COORDINATOR_ROLES = {'Proje Koordinatoru', 'Saha Koordinatoru', 'supervizor'}
_TEAM_LEAD_ROLES = {'Takim Lideri'}


def _user_role_names(user):
    return {r.name for r in (user.roles or [])}


# ============================================================
# MALIYET GORUNURLUGU - Filo kiralama/yakit tutarlari
# ============================================================

# Arac maliyet bilgilerini (aylik kira, kira tarihleri, yakit/islem
# tutarlari) gorebilecek roller. Koordinator ve supervizorlar disarida.
MALIYET_GOREBILIR_ROLLER = {
    'Sistem Yoneticisi', 'Ajans Baskani', 'Direktor',
    'Filo Yoneticisi', 'Butce Raporlama Uzmani',
}


def maliyet_gorebilir(user=None):
    """Kullanici arac maliyet bilgilerini gorebilir mi? - bool dondurur"""
    user = user or current_user
    if not user or not user.is_authenticated:
        return False
    if user.is_admin:
        return True
    return bool(_user_role_names(user) & MALIYET_GOREBILIR_ROLLER)


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


# ============================================================
# IBAN EVRAK FORMAT KISITLAMASI
# ============================================================

# IBAN belgesi OCR ile okunduğu için sadece görsel/PDF kabul edilir.
# Word dosyaları (.doc/.docx) okunamadığı için kabul edilmez.
IBAN_EVRAK_UZANTILARI = {'jpg', 'jpeg', 'png', 'pdf'}

IBAN_FORMAT_HATASI = 'IBAN belgesi sadece JPEG, PNG veya PDF formatında yüklenebilir.'

IBAN_EVRAK_ACIKLAMA = (
    'IBAN belgenizi yükleyin. Kabul edilen formatlar: JPEG, PNG veya PDF. '
    'Online bankacılık hesap detaylarınızın ekran görüntüsünü veya '
    'hesap cüzdanınızın fotoğrafını yükleyebilirsiniz.'
)


def is_iban_evrak_tipi(evrak_tipi):
    """Evrak tipinin IBAN / hesap bilgisi belgesi olup olmadığını belirler.

    Kod 'IBAN' ise veya ad/kod içinde 'iban' geçiyorsa True.

    Args:
        evrak_tipi: EvrakTipi nesnesi (None olabilir).
    """
    if not evrak_tipi:
        return False
    if (evrak_tipi.kod or '').strip().upper() == 'IBAN':
        return True
    metin = f"{evrak_tipi.ad or ''} {evrak_tipi.kod or ''}".lower()
    return 'iban' in metin


def iban_evrak_uzanti_gecerli(filename):
    """IBAN evrağı için dosya uzantısının kabul edilip edilmediğini kontrol eder.

    Args:
        filename: Yüklenen dosyanın adı.

    Returns:
        True ise uzantı kabul edilir (jpg/jpeg/png/pdf), aksi halde False.
    """
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in IBAN_EVRAK_UZANTILARI


def iban_evrak_tipi_idleri(evrak_tipleri):
    """Verilen evrak tipi listesinden IBAN tipli olanların id'lerini döndürür.

    Template'te dosya seçicinin `accept` değerini dinamik ayarlamak için kullanılır.
    """
    return [t.id for t in (evrak_tipleri or []) if is_iban_evrak_tipi(t)]
