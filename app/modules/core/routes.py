# -*- coding: utf-8 -*-
"""
TG Portal - Core Routes (Auth, Admin, Dashboard)
"""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.core import User, Role, Permission, AuditLog
from app.utils import admin_required

core_bp = Blueprint('core', __name__)


# ==================== AUTH ====================

@core_bp.route('/')
def index():
    """Ana sayfa - login'e veya dashboard'a yönlendir"""
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))
    return redirect(url_for('core.login'))


@core_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş sayfası"""
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email, is_deleted=False).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Hesabınız pasif durumda. Lütfen yönetici ile iletişime geçin.', 'warning')
                return render_template('core/login.html')
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Audit log
            log = AuditLog(
                user_id=user.id,
                action='login',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string[:255] if request.user_agent.string else None
            )
            db.session.add(log)
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('core.dashboard'))
        
        flash('Geçersiz email veya şifre.', 'danger')
    
    return render_template('core/login.html')


@core_bp.route('/logout')
@login_required
def logout():
    """Çıkış"""
    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        action='logout',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('core.login'))


# ==================== DASHBOARD ====================

@core_bp.route('/dashboard')
@login_required
def dashboard():
    """Ana dashboard"""
    from app.models.ik import Calisan, Aday
    from app.models.filo import Arac
    from app.models.proje import Proje, HedefKadro, Musteri
    from app.models.base import AracDurumu, CalisanDurumu
    
    # Ana istatistikler
    stats = {
        'calisan_sayisi': Calisan.query.filter_by(is_deleted=False).filter(
            Calisan.durum.in_([CalisanDurumu.AKTIF, CalisanDurumu.IZINLI])
        ).count(),
        'arac_sayisi': Arac.query.filter_by(is_deleted=False).count(),
        'aktif_proje': Proje.query.filter_by(is_deleted=False, aktif=True).count(),
        'bekleyen_aday': Aday.query.filter_by(is_deleted=False).filter(
            Aday.durum.in_(['basvurdu', 'degerlendiriliyor', 'mulakat', 'teklif'])
        ).count()
    }
    
    # Aktif projeler (doluluk için)
    projeler = Proje.query.filter_by(is_deleted=False, aktif=True).order_by(Proje.ad).limit(5).all()
    
    # Acil kadro ihtiyacı (eksik > 0 ve öncelik düşük)
    acil_kadrolar = HedefKadro.query.filter_by(is_deleted=False, aktif=True).filter(
        HedefKadro.oncelik <= 5
    ).order_by(HedefKadro.oncelik).limit(5).all()
    # Sadece eksik olanları filtrele
    acil_kadrolar = [k for k in acil_kadrolar if k.eksik_sayi > 0]
    
    # Son eklenen çalışanlar
    son_calisanlar = Calisan.query.filter_by(is_deleted=False).order_by(
        Calisan.created_at.desc()
    ).limit(5).all()
    
    # Araç durumu
    arac_durum = {
        'aktif': Arac.query.filter_by(is_deleted=False, durum=AracDurumu.AKTIF).count(),
        'bakimda': Arac.query.filter_by(is_deleted=False, durum=AracDurumu.BAKIM).count(),
        'arizali': Arac.query.filter_by(is_deleted=False, durum=AracDurumu.ARIZALI).count(),
        'projeli': Arac.query.filter(Arac.is_deleted==False, Arac.proje_id.isnot(None)).count(),
        'projesiz': Arac.query.filter(Arac.is_deleted==False, Arac.proje_id.is_(None)).count()
    }
    
    return render_template('core/dashboard.html',
                         stats=stats,
                         projeler=projeler,
                         acil_kadrolar=acil_kadrolar,
                         son_calisanlar=son_calisanlar,
                         arac_durum=arac_durum)


# ==================== PROFIL ====================

@core_bp.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    """Kullanıcı profil sayfası"""
    if request.method == 'POST':
        current_user.ad = request.form.get('ad', '').strip()
        current_user.soyad = request.form.get('soyad', '').strip()
        current_user.telefon = request.form.get('telefon', '').strip()
        
        # Şifre değişikliği
        new_password = request.form.get('new_password')
        if new_password:
            old_password = request.form.get('old_password')
            if not current_user.check_password(old_password):
                flash('Mevcut şifreniz hatalı.', 'danger')
                return render_template('core/profil.html')
            current_user.set_password(new_password)
            flash('Şifreniz güncellendi.', 'success')
        
        db.session.commit()
        flash('Profiliniz güncellendi.', 'success')
        return redirect(url_for('core.profil'))
    
    return render_template('core/profil.html')


# ==================== ADMIN ====================

@core_bp.route('/admin/kullanicilar')
@login_required
@admin_required
def admin_kullanicilar():
    """Kullanıcı yönetimi"""
    users = User.query.filter_by(is_deleted=False).order_by(User.ad).all()
    roles = Role.query.all()
    return render_template('core/admin_kullanicilar.html', users=users, roles=roles)


@core_bp.route('/admin/kullanici/ekle', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_kullanici_ekle():
    """Yeni kullanıcı ekle"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        # Email kontrolü
        if User.query.filter_by(email=email).first():
            flash('Bu email adresi zaten kullanılıyor.', 'danger')
            return redirect(url_for('core.admin_kullanici_ekle'))
        
        user = User(
            email=email,
            ad=request.form.get('ad', '').strip(),
            soyad=request.form.get('soyad', '').strip(),
            telefon=request.form.get('telefon', '').strip(),
            is_admin=request.form.get('is_admin') == 'on',
            is_active=True
        )
        user.set_password(request.form.get('password'))
        
        # Roller
        role_ids = request.form.getlist('roles')
        for role_id in role_ids:
            role = Role.query.get(role_id)
            if role:
                user.roles.append(role)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'{user.full_name} kullanıcısı oluşturuldu.', 'success')
        return redirect(url_for('core.admin_kullanicilar'))
    
    roles = Role.query.all()
    return render_template('core/admin_kullanici_form.html', user=None, roles=roles)


@core_bp.route('/admin/kullanici/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_kullanici_duzenle(id):
    """Kullanıcı düzenle"""
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        user.ad = request.form.get('ad', '').strip()
        user.soyad = request.form.get('soyad', '').strip()
        user.telefon = request.form.get('telefon', '').strip()
        user.is_admin = request.form.get('is_admin') == 'on'
        user.is_active = request.form.get('is_active') == 'on'
        
        # Şifre güncelleme (opsiyonel)
        new_password = request.form.get('password')
        if new_password:
            user.set_password(new_password)
        
        # Roller güncelle
        user.roles = []
        role_ids = request.form.getlist('roles')
        for role_id in role_ids:
            role = Role.query.get(role_id)
            if role:
                user.roles.append(role)
        
        db.session.commit()
        flash('Kullanıcı güncellendi.', 'success')
        return redirect(url_for('core.admin_kullanicilar'))
    
    roles = Role.query.all()
    return render_template('core/admin_kullanici_form.html', user=user, roles=roles)


@core_bp.route('/admin/roller')
@login_required
@admin_required
def admin_roller():
    """Rol yönetimi"""
    roles = Role.query.all()
    permissions = Permission.query.order_by(Permission.module, Permission.code).all()
    return render_template('core/admin_roller.html', roles=roles, permissions=permissions)


# ==================== ERROR HANDLERS ====================

@core_bp.app_errorhandler(403)
def forbidden(e):
    return render_template('core/403.html'), 403


@core_bp.app_errorhandler(404)
def not_found(e):
    return render_template('core/404.html'), 404


@core_bp.app_errorhandler(500)
def server_error(e):
    return render_template('core/500.html'), 500
