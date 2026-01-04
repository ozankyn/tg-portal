# -*- coding: utf-8 -*-
"""
TG Portal - Ayarlar Modülü Routes
Sistem konfigürasyonu, kullanıcı, rol ve yetki yönetimi
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from app import db
from app.models.ayarlar import SistemAyar, AktiviteLog, varsayilan_ayarlari_yukle
from app.models.core import User, Role, Permission
from app.utils import permission_required

ayarlar_bp = Blueprint('ayarlar', __name__)


# ============================================================
# ANA SAYFA
# ============================================================

@ayarlar_bp.route('/')
@login_required
def dashboard():
    """Ayarlar ana sayfası"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    stats = {
        'kullanici': User.query.filter_by(is_active=True).count(),
        'rol': Role.query.count(),
        'yetki': Permission.query.count(),
        'ayar': SistemAyar.query.count(),
    }
    return render_template('ayarlar/dashboard.html', stats=stats)


# ============================================================
# SİSTEM AYARLARI
# ============================================================

@ayarlar_bp.route('/sistem', methods=['GET', 'POST'])
@login_required
def sistem():
    """Sistem ayarları"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    if request.method == 'POST':
        for anahtar in request.form:
            if anahtar != 'csrf_token':
                deger = request.form.get(anahtar, '')
                ayar = SistemAyar.query.filter_by(anahtar=anahtar).first()
                if ayar:
                    ayar.deger = deger
        
        db.session.commit()
        flash('Ayarlar kaydedildi.', 'success')
        return redirect(url_for('ayarlar.sistem'))
    
    genel = SistemAyar.query.filter_by(kategori='genel').all()
    email = SistemAyar.query.filter_by(kategori='email').all()
    bildirim = SistemAyar.query.filter_by(kategori='bildirim').all()
    guvenlik = SistemAyar.query.filter_by(kategori='guvenlik').all()
    
    return render_template('ayarlar/sistem.html',
                          genel=genel,
                          email=email,
                          bildirim=bildirim,
                          guvenlik=guvenlik)


@ayarlar_bp.route('/sistem/yukle')
@login_required
def varsayilan_yukle():
    """Varsayılan ayarları yükle"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    varsayilan_ayarlari_yukle()
    flash('Varsayılan ayarlar yüklendi.', 'success')
    return redirect(url_for('ayarlar.sistem'))


# ============================================================
# KULLANICI YÖNETİMİ
# ============================================================

@ayarlar_bp.route('/kullanicilar')
@login_required
def kullanici_liste():
    """Kullanıcı listesi"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    arama = request.args.get('q', '').strip()
    
    query = User.query
    
    if durum == 'aktif':
        query = query.filter_by(is_active=True)
    elif durum == 'pasif':
        query = query.filter_by(is_active=False)
    
    if arama:
        query = query.filter(
            db.or_(
                User.email.ilike(f'%{arama}%'),
                User.ad.ilike(f'%{arama}%'),
                User.soyad.ilike(f'%{arama}%')
            )
        )
    
    query = query.order_by(User.ad)
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('ayarlar/kullanici_liste.html',
                          kullanicilar=pagination.items,
                          pagination=pagination)


@ayarlar_bp.route('/kullanici/ekle', methods=['GET', 'POST'])
@login_required
def kullanici_ekle():
    """Yeni kullanıcı ekle"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    if request.method == 'POST':
        # E-posta kontrolü
        if User.query.filter_by(email=request.form['email']).first():
            flash('Bu e-posta adresi zaten kullanılıyor.', 'danger')
            return redirect(url_for('ayarlar.kullanici_ekle'))
        
        user = User(
            email=request.form['email'].strip(),
            ad=request.form.get('ad', '').strip(),
            soyad=request.form.get('soyad', '').strip(),
            is_active=request.form.get('is_active') == 'on',
            is_admin=request.form.get('is_admin') == 'on'
        )
        
        # Şifre
        sifre = request.form.get('password', '').strip()
        if sifre:
            user.password_hash = generate_password_hash(sifre)
        else:
            flash('Şifre gerekli.', 'danger')
            return redirect(url_for('ayarlar.kullanici_ekle'))
        
        # Rol
        rol_id = request.form.get('role_id', type=int)
        if rol_id:
            rol = Role.query.get(rol_id)
            if rol:
                user.roles.append(rol)
        
        # Claims (bireysel yetkiler)
        claim_ids = request.form.getlist('claims[]')
        for claim_id in claim_ids:
            perm = Permission.query.get(int(claim_id))
            if perm:
                user.claims.append(perm)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Kullanıcı oluşturuldu.', 'success')
        return redirect(url_for('ayarlar.kullanici_liste'))
    
    roller = Role.query.order_by(Role.name).all()
    yetkiler = Permission.query.order_by(Permission.module, Permission.code).all()
    
    # Yetkileri modüllere göre grupla
    yetki_gruplari = {}
    for yetki in yetkiler:
        modul = yetki.module or 'diger'
        if modul not in yetki_gruplari:
            yetki_gruplari[modul] = []
        yetki_gruplari[modul].append(yetki)
    
    return render_template('ayarlar/kullanici_form.html', 
                          user=None, 
                          roller=roller, 
                          yetki_gruplari=yetki_gruplari)


@ayarlar_bp.route('/kullanici/<int:id>', methods=['GET', 'POST'])
@login_required
def kullanici_duzenle(id):
    """Kullanıcı düzenle"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        # E-posta kontrolü (kendi dışında)
        mevcut = User.query.filter(User.email == request.form['email'], User.id != id).first()
        if mevcut:
            flash('Bu e-posta adresi zaten kullanılıyor.', 'danger')
            return redirect(url_for('ayarlar.kullanici_duzenle', id=id))
        
        user.email = request.form['email'].strip()
        user.ad = request.form.get('ad', '').strip()
        user.soyad = request.form.get('soyad', '').strip()
        user.is_active = request.form.get('is_active') == 'on'
        user.is_admin = request.form.get('is_admin') == 'on'
        
        # Şifre değişikliği
        yeni_sifre = request.form.get('password', '').strip()
        if yeni_sifre:
            user.password_hash = generate_password_hash(yeni_sifre)
        
        # Rol güncelle
        user.roles.clear()
        rol_id = request.form.get('role_id', type=int)
        if rol_id:
            rol = Role.query.get(rol_id)
            if rol:
                user.roles.append(rol)
        
        # Claims güncelle
        user.claims.clear()
        claim_ids = request.form.getlist('claims[]')
        for claim_id in claim_ids:
            perm = Permission.query.get(int(claim_id))
            if perm:
                user.claims.append(perm)
        
        db.session.commit()
        
        flash('Kullanıcı güncellendi.', 'success')
        return redirect(url_for('ayarlar.kullanici_liste'))
    
    roller = Role.query.order_by(Role.name).all()
    yetkiler = Permission.query.order_by(Permission.module, Permission.code).all()
    
    # Yetkileri modüllere göre grupla
    yetki_gruplari = {}
    for yetki in yetkiler:
        modul = yetki.module or 'diger'
        if modul not in yetki_gruplari:
            yetki_gruplari[modul] = []
        yetki_gruplari[modul].append(yetki)
    
    return render_template('ayarlar/kullanici_form.html', 
                          user=user, 
                          roller=roller, 
                          yetki_gruplari=yetki_gruplari)


@ayarlar_bp.route('/kullanici/<int:id>/durum', methods=['POST'])
@login_required
def kullanici_durum(id):
    """Kullanıcı aktif/pasif yap"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('Kendi hesabınızı devre dışı bırakamazsınız.', 'danger')
        return redirect(url_for('ayarlar.kullanici_liste'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    flash(f'Kullanıcı {"aktif" if user.is_active else "pasif"} yapıldı.', 'success')
    return redirect(url_for('ayarlar.kullanici_liste'))


# ============================================================
# ROL YÖNETİMİ
# ============================================================

@ayarlar_bp.route('/roller')
@login_required
def rol_liste():
    """Rol listesi"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    roller = Role.query.order_by(Role.name).all()
    return render_template('ayarlar/rol_liste.html', roller=roller)


@ayarlar_bp.route('/rol/ekle', methods=['GET', 'POST'])
@login_required
def rol_ekle():
    """Yeni rol ekle"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    if request.method == 'POST':
        rol = Role(
            name=request.form['name'].strip(),
            display_name=request.form.get('display_name', '').strip() or None,
            description=request.form.get('description', '').strip() or None
        )
        
        # Yetkileri ekle
        yetki_ids = request.form.getlist('permissions[]')
        for yetki_id in yetki_ids:
            yetki = Permission.query.get(int(yetki_id))
            if yetki:
                rol.permissions.append(yetki)
        
        db.session.add(rol)
        db.session.commit()
        
        flash('Rol oluşturuldu.', 'success')
        return redirect(url_for('ayarlar.rol_liste'))
    
    yetkiler = Permission.query.order_by(Permission.module, Permission.code).all()
    
    # Yetkileri modüllere göre grupla
    yetki_gruplari = {}
    for yetki in yetkiler:
        modul = yetki.module or 'diger'
        if modul not in yetki_gruplari:
            yetki_gruplari[modul] = []
        yetki_gruplari[modul].append(yetki)
    
    return render_template('ayarlar/rol_form.html', rol=None, yetki_gruplari=yetki_gruplari)


@ayarlar_bp.route('/rol/<int:id>', methods=['GET', 'POST'])
@login_required
def rol_duzenle(id):
    """Rol düzenle"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    rol = Role.query.get_or_404(id)
    
    if request.method == 'POST':
        rol.name = request.form['name'].strip()
        rol.display_name = request.form.get('display_name', '').strip() or None
        rol.description = request.form.get('description', '').strip() or None
        
        # Yetkileri güncelle
        rol.permissions.clear()
        yetki_ids = request.form.getlist('permissions[]')
        for yetki_id in yetki_ids:
            yetki = Permission.query.get(int(yetki_id))
            if yetki:
                rol.permissions.append(yetki)
        
        db.session.commit()
        
        flash('Rol güncellendi.', 'success')
        return redirect(url_for('ayarlar.rol_liste'))
    
    yetkiler = Permission.query.order_by(Permission.module, Permission.code).all()
    
    # Yetkileri modüllere göre grupla
    yetki_gruplari = {}
    for yetki in yetkiler:
        modul = yetki.module or 'diger'
        if modul not in yetki_gruplari:
            yetki_gruplari[modul] = []
        yetki_gruplari[modul].append(yetki)
    
    return render_template('ayarlar/rol_form.html', rol=rol, yetki_gruplari=yetki_gruplari)


# ============================================================
# AKTİVİTE LOGLARI
# ============================================================

@ayarlar_bp.route('/loglar')
@login_required
def log_liste():
    """Aktivite logları"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    eylem = request.args.get('eylem')
    modul = request.args.get('modul')
    kullanici_id = request.args.get('kullanici_id', type=int)
    
    query = AktiviteLog.query
    
    if eylem:
        query = query.filter(AktiviteLog.eylem == eylem)
    if modul:
        query = query.filter(AktiviteLog.modul == modul)
    if kullanici_id:
        query = query.filter(AktiviteLog.kullanici_id == kullanici_id)
    
    query = query.order_by(AktiviteLog.tarih.desc())
    pagination = query.paginate(page=page, per_page=50, error_out=False)
    
    kullanicilar = User.query.filter_by(is_active=True).order_by(User.ad).all()
    
    return render_template('ayarlar/log_liste.html',
                          loglar=pagination.items,
                          pagination=pagination,
                          kullanicilar=kullanicilar)


# ============================================================
# YETKİ YÖNETİMİ
# ============================================================

@ayarlar_bp.route('/yetkiler')
@login_required
def yetki_liste():
    """Yetki listesi"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    yetkiler = Permission.query.order_by(Permission.module, Permission.code).all()
    
    # Modüllere göre grupla
    yetki_gruplari = {}
    for yetki in yetkiler:
        modul = yetki.module or 'diger'
        if modul not in yetki_gruplari:
            yetki_gruplari[modul] = []
        yetki_gruplari[modul].append(yetki)
    
    return render_template('ayarlar/yetki_liste.html', yetki_gruplari=yetki_gruplari)


@ayarlar_bp.route('/yetki/ekle', methods=['POST'])
@login_required
def yetki_ekle():
    """Yeni yetki ekle"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    code = request.form.get('code', '').strip()
    name = request.form.get('name', '').strip()
    module = request.form.get('module', '').strip()
    
    if code:
        mevcut = Permission.query.filter_by(code=code).first()
        if mevcut:
            flash('Bu yetki kodu zaten mevcut.', 'warning')
        else:
            yetki = Permission(
                code=code, 
                name=name or code,
                module=module or code.split('.')[0] if '.' in code else None
            )
            db.session.add(yetki)
            db.session.commit()
            flash('Yetki eklendi.', 'success')
    
    return redirect(url_for('ayarlar.yetki_liste'))


@ayarlar_bp.route('/yetkiler/varsayilan')
@login_required
def varsayilan_yetkiler():
    """Varsayılan yetkileri oluştur"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    yetkiler = [
        # İK
        ('ik.view', 'İK Görüntüleme', 'ik'),
        ('ik.create', 'İK Kayıt Oluşturma', 'ik'),
        ('ik.edit', 'İK Kayıt Düzenleme', 'ik'),
        ('ik.delete', 'İK Kayıt Silme', 'ik'),
        ('ik.admin', 'İK Yönetici', 'ik'),
        
        # Proje
        ('proje.view', 'Proje Görüntüleme', 'proje'),
        ('proje.create', 'Proje Oluşturma', 'proje'),
        ('proje.edit', 'Proje Düzenleme', 'proje'),
        ('proje.admin', 'Proje Yönetici', 'proje'),
        
        # Eğitim
        ('egitim.view', 'Eğitim Görüntüleme', 'egitim'),
        ('egitim.create', 'Eğitim Oluşturma', 'egitim'),
        ('egitim.test', 'Test Yapabilme', 'egitim'),
        ('egitim.admin', 'Eğitim Yönetici', 'egitim'),
        
        # Filo
        ('filo.view', 'Filo Görüntüleme', 'filo'),
        ('filo.create', 'Araç Ekleme', 'filo'),
        ('filo.admin', 'Filo Yönetici', 'filo'),
        
        # Masraf
        ('masraf.view', 'Masraf Görüntüleme', 'masraf'),
        ('masraf.create', 'Masraf Oluşturma', 'masraf'),
        ('masraf.approve', 'Masraf Onaylama', 'masraf'),
        ('masraf.admin', 'Masraf Yönetici', 'masraf'),
        
        # Talep
        ('talep.view', 'Talep Görüntüleme', 'talep'),
        ('talep.create', 'Talep Oluşturma', 'talep'),
        ('talep.admin', 'Talep Yönetici', 'talep'),
        
        # Satın Alma
        ('satinalma.view', 'Satın Alma Görüntüleme', 'satinalma'),
        ('satinalma.create', 'Satın Alma Talebi Oluşturma', 'satinalma'),
        ('satinalma.admin', 'Satın Alma Yönetici', 'satinalma'),
        
        # Sözleşme
        ('sozlesme.view', 'Sözleşme Görüntüleme', 'sozlesme'),
        ('sozlesme.create', 'Sözleşme Oluşturma', 'sozlesme'),
        ('sozlesme.admin', 'Sözleşme Yönetici', 'sozlesme'),
        
        # Tedarikçi
        ('tedarikci.view', 'Tedarikçi Görüntüleme', 'tedarikci'),
        ('tedarikci.create', 'Tedarikçi Ekleme', 'tedarikci'),
        ('tedarikci.admin', 'Tedarikçi Yönetici', 'tedarikci'),
        
        # Rapor
        ('rapor.view', 'Rapor Görüntüleme', 'rapor'),
        ('rapor.export', 'Rapor Dışa Aktarma', 'rapor'),
        ('rapor.admin', 'Rapor Yönetici', 'rapor'),
        
        # Onay
        ('onay.view', 'Onay Görüntüleme', 'onay'),
        ('onay.approve', 'Onay Verme', 'onay'),
        ('onay.admin', 'Onay Yönetici', 'onay'),
        
        # Ayarlar
        ('ayarlar.view', 'Ayarlar Görüntüleme', 'ayarlar'),
        ('ayarlar.admin', 'Ayarlar Yönetici', 'ayarlar'),
    ]
    
    eklenen = 0
    for code, name, module in yetkiler:
        mevcut = Permission.query.filter_by(code=code).first()
        if not mevcut:
            yetki = Permission(code=code, name=name, module=module)
            db.session.add(yetki)
            eklenen += 1
    
    db.session.commit()
    flash(f'{eklenen} yetki eklendi.', 'success')
    return redirect(url_for('ayarlar.yetki_liste'))


# ============================================================
# VARSAYILAN ROLLER
# ============================================================

@ayarlar_bp.route('/roller/varsayilan')
@login_required
def varsayilan_roller():
    """Varsayılan rolleri oluştur"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('core.dashboard'))
    
    roller = [
        {
            'name': 'saha_calisan',
            'display_name': 'Saha Çalışanı',
            'description': 'Temel saha personeli',
            'permissions': ['talep.view', 'talep.create', 'masraf.create', 'egitim.view', 'egitim.test']
        },
        {
            'name': 'supervizor',
            'display_name': 'Süpervizör',
            'description': 'Saha süpervizörü - ekip yönetimi',
            'permissions': ['talep.view', 'talep.create', 'masraf.create', 'masraf.view', 
                          'proje.view', 'egitim.view', 'egitim.test', 'rapor.view']
        },
        {
            'name': 'ofis_calisan',
            'display_name': 'Ofis Çalışanı',
            'description': 'Ofis personeli',
            'permissions': ['talep.view', 'talep.create', 'masraf.create', 'masraf.view',
                          'sozlesme.view', 'egitim.view', 'egitim.test']
        },
        {
            'name': 'ik_yonetici',
            'display_name': 'İK Yöneticisi',
            'description': 'İnsan kaynakları yöneticisi',
            'permissions': ['ik.view', 'ik.create', 'ik.edit', 'ik.admin',
                          'egitim.view', 'egitim.create', 'egitim.admin',
                          'rapor.view', 'onay.view']
        },
        {
            'name': 'proje_yonetici',
            'display_name': 'Proje Yöneticisi',
            'description': 'Proje/Kısım lideri',
            'permissions': ['proje.view', 'proje.create', 'proje.edit', 'proje.admin',
                          'talep.view', 'talep.admin', 'masraf.view', 'masraf.approve',
                          'rapor.view', 'onay.approve']
        },
        {
            'name': 'filo_yonetici',
            'display_name': 'Filo Yöneticisi',
            'description': 'Araç filosu yöneticisi',
            'permissions': ['filo.view', 'filo.create', 'filo.admin', 'rapor.view']
        },
        {
            'name': 'egitim_yonetici',
            'display_name': 'Eğitim Yöneticisi',
            'description': 'Eğitim sorumlusu',
            'permissions': ['egitim.view', 'egitim.create', 'egitim.admin', 'rapor.view']
        },
    ]
    
    eklenen = 0
    for rol_data in roller:
        mevcut = Role.query.filter_by(name=rol_data['name']).first()
        if not mevcut:
            rol = Role(
                name=rol_data['name'],
                display_name=rol_data['display_name'],
                description=rol_data['description'],
                is_system=True
            )
            
            # Yetkileri ekle
            for perm_code in rol_data['permissions']:
                perm = Permission.query.filter_by(code=perm_code).first()
                if perm:
                    rol.permissions.append(perm)
            
            db.session.add(rol)
            eklenen += 1
    
    db.session.commit()
    flash(f'{eklenen} rol eklendi.', 'success')
    return redirect(url_for('ayarlar.rol_liste'))
