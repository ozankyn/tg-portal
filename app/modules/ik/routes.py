# -*- coding: utf-8 -*-
"""
TG Portal - İK (Human Resources) Routes
"""

from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.ik import Departman, Pozisyon, Calisan, Izin, Aday
from app.models.base import CalisanDurumu
from app.utils import permission_required, paginate_query

ik_bp = Blueprint('ik', __name__)


# ==================== ÇALIŞAN LİSTESİ ====================

@ik_bp.route('/')
@login_required
@permission_required('ik.view')
def liste():
    """Çalışan listesi"""
    page = request.args.get('page', 1, type=int)
    
    # Filtreler
    departman_id = request.args.get('departman_id', type=int)
    durum = request.args.get('durum')
    search = request.args.get('search', '').strip()
    
    query = Calisan.query.filter_by(is_deleted=False)
    
    if departman_id:
        query = query.filter(Calisan.departman_id == departman_id)
    if durum:
        query = query.filter(Calisan.durum == CalisanDurumu(durum))
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Calisan.ad.ilike(search_filter),
                Calisan.soyad.ilike(search_filter),
                Calisan.sicil_no.ilike(search_filter),
                Calisan.email.ilike(search_filter)
            )
        )
    
    query = query.order_by(Calisan.ad, Calisan.soyad)
    pagination = paginate_query(query, page, 20)
    
    departmanlar = Departman.query.filter_by(aktif=True).order_by(Departman.ad).all()
    
    return render_template('ik/liste.html',
                          calisanlar=pagination.items,
                          pagination=pagination,
                          departmanlar=departmanlar,
                          durumlar=CalisanDurumu)


# ==================== ÇALIŞAN DETAY ====================

@ik_bp.route('/<int:id>')
@login_required
@permission_required('ik.view')
def detay(id):
    """Çalışan detay sayfası"""
    calisan = Calisan.query.get_or_404(id)
    
    # İzin geçmişi
    izinler = calisan.izinler.order_by(Izin.baslangic.desc()).limit(10).all()
    
    return render_template('ik/detay.html',
                          calisan=calisan,
                          izinler=izinler)


# ==================== ÇALIŞAN EKLE ====================

@ik_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('ik.create')
def ekle():
    """Yeni çalışan ekle"""
    if request.method == 'POST':
        # TC Kimlik kontrolü
        tc = request.form.get('tc_kimlik', '').strip()
        if tc and Calisan.query.filter_by(tc_kimlik=tc, is_deleted=False).first():
            flash('Bu TC Kimlik numarası zaten kayıtlı.', 'danger')
            return redirect(url_for('ik.ekle'))
        
        calisan = Calisan(
            sicil_no=request.form.get('sicil_no', '').strip() or None,
            ad=request.form.get('ad', '').strip(),
            soyad=request.form.get('soyad', '').strip(),
            tc_kimlik=tc or None,
            dogum_tarihi=datetime.strptime(request.form.get('dogum_tarihi'), '%Y-%m-%d').date() if request.form.get('dogum_tarihi') else None,
            cinsiyet=request.form.get('cinsiyet') or None,
            email=request.form.get('email', '').strip() or None,
            telefon=request.form.get('telefon', '').strip() or None,
            adres=request.form.get('adres', '').strip() or None,
            il=request.form.get('il', '').strip() or None,
            ilce=request.form.get('ilce', '').strip() or None,
            departman_id=int(request.form.get('departman_id')) if request.form.get('departman_id') else None,
            pozisyon_id=int(request.form.get('pozisyon_id')) if request.form.get('pozisyon_id') else None,
            ise_baslama=datetime.strptime(request.form.get('ise_baslama'), '%Y-%m-%d').date() if request.form.get('ise_baslama') else None,
            calisma_tipi=request.form.get('calisma_tipi') or None,
            durum=CalisanDurumu(request.form.get('durum')) if request.form.get('durum') else CalisanDurumu.AKTIF,
            notlar=request.form.get('notlar', '').strip() or None,
            created_by=current_user.id
        )
        
        db.session.add(calisan)
        db.session.commit()
        
        flash(f'{calisan.full_name} çalışanı oluşturuldu.', 'success')
        return redirect(url_for('ik.detay', id=calisan.id))
    
    departmanlar = Departman.query.filter_by(aktif=True).order_by(Departman.ad).all()
    pozisyonlar = Pozisyon.query.filter_by(aktif=True).order_by(Pozisyon.ad).all()
    
    return render_template('ik/form.html',
                          calisan=None,
                          departmanlar=departmanlar,
                          pozisyonlar=pozisyonlar,
                          durumlar=CalisanDurumu)


# ==================== ÇALIŞAN DÜZENLE ====================

@ik_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('ik.edit')
def duzenle(id):
    """Çalışan düzenle"""
    calisan = Calisan.query.get_or_404(id)
    
    if request.method == 'POST':
        tc = request.form.get('tc_kimlik', '').strip()
        if tc:
            existing = Calisan.query.filter(
                Calisan.tc_kimlik == tc,
                Calisan.id != id,
                Calisan.is_deleted == False
            ).first()
            if existing:
                flash('Bu TC Kimlik numarası başka bir çalışanda kayıtlı.', 'danger')
                return redirect(url_for('ik.duzenle', id=id))
        
        calisan.sicil_no = request.form.get('sicil_no', '').strip() or None
        calisan.ad = request.form.get('ad', '').strip()
        calisan.soyad = request.form.get('soyad', '').strip()
        calisan.tc_kimlik = tc or None
        calisan.dogum_tarihi = datetime.strptime(request.form.get('dogum_tarihi'), '%Y-%m-%d').date() if request.form.get('dogum_tarihi') else None
        calisan.cinsiyet = request.form.get('cinsiyet') or None
        calisan.email = request.form.get('email', '').strip() or None
        calisan.telefon = request.form.get('telefon', '').strip() or None
        calisan.adres = request.form.get('adres', '').strip() or None
        calisan.il = request.form.get('il', '').strip() or None
        calisan.ilce = request.form.get('ilce', '').strip() or None
        calisan.departman_id = int(request.form.get('departman_id')) if request.form.get('departman_id') else None
        calisan.pozisyon_id = int(request.form.get('pozisyon_id')) if request.form.get('pozisyon_id') else None
        calisan.ise_baslama = datetime.strptime(request.form.get('ise_baslama'), '%Y-%m-%d').date() if request.form.get('ise_baslama') else None
        calisan.calisma_tipi = request.form.get('calisma_tipi') or None
        calisan.durum = CalisanDurumu(request.form.get('durum')) if request.form.get('durum') else CalisanDurumu.AKTIF
        calisan.notlar = request.form.get('notlar', '').strip() or None
        calisan.updated_by = current_user.id
        
        db.session.commit()
        
        flash('Çalışan güncellendi.', 'success')
        return redirect(url_for('ik.detay', id=id))
    
    departmanlar = Departman.query.filter_by(aktif=True).order_by(Departman.ad).all()
    pozisyonlar = Pozisyon.query.filter_by(aktif=True).order_by(Pozisyon.ad).all()
    
    return render_template('ik/form.html',
                          calisan=calisan,
                          departmanlar=departmanlar,
                          pozisyonlar=pozisyonlar,
                          durumlar=CalisanDurumu)


# ==================== ADAY LİSTESİ ====================

@ik_bp.route('/adaylar')
@login_required
@permission_required('ik.view')
def aday_liste():
    """Aday listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    
    query = Aday.query.filter_by(is_deleted=False)
    
    if durum:
        query = query.filter(Aday.durum == durum)
    
    query = query.order_by(Aday.basvuru_tarihi.desc())
    pagination = paginate_query(query, page, 20)
    
    return render_template('ik/aday_liste.html',
                          adaylar=pagination.items,
                          pagination=pagination)


# ==================== İZİN TALEPLERİ ====================

@ik_bp.route('/izinler')
@login_required
@permission_required('ik.view')
def izin_liste():
    """İzin talepleri listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    
    query = Izin.query
    
    if durum:
        query = query.filter(Izin.durum == durum)
    
    query = query.order_by(Izin.created_at.desc())
    pagination = paginate_query(query, page, 20)
    
    return render_template('ik/izin_liste.html',
                          izinler=pagination.items,
                          pagination=pagination)


# ==================== DASHBOARD ====================

@ik_bp.route('/dashboard')
@login_required
@permission_required('ik.view')
def dashboard():
    """İK Dashboard"""
    # İstatistikler
    aktif_calisan = Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AKTIF).count()
    bekleyen_aday = Aday.query.filter_by(is_deleted=False).filter(
        Aday.durum.in_(['basvurdu', 'degerlendiriliyor', 'mulakat'])
    ).count()
    bekleyen_izin = Izin.query.filter_by(durum='beklemede').count()
    
    # Departman bazlı dağılım
    departman_stats = db.session.query(
        Departman.ad,
        db.func.count(Calisan.id)
    ).join(Calisan).filter(
        Calisan.is_deleted == False,
        Calisan.durum == CalisanDurumu.AKTIF
    ).group_by(Departman.ad).all()
    
    return render_template('ik/dashboard.html',
                          aktif_calisan=aktif_calisan,
                          bekleyen_aday=bekleyen_aday,
                          bekleyen_izin=bekleyen_izin,
                          departman_stats=departman_stats)
