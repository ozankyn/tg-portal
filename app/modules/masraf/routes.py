# -*- coding: utf-8 -*-
"""
TG Portal - Masraf Modülü Routes
"""

from datetime import datetime, date
from decimal import Decimal
import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models.masraf import Masraf, MasrafKategorisi, MasrafKalemi, MasrafAvans, get_calisan_masraf_ozeti
from app.models.ik import Calisan
from app.models.proje import Proje
from app.models.onay import OnayServisi
from app.utils import permission_required, paginate_query

masraf_bp = Blueprint('masraf', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# DASHBOARD
# ============================================================

@masraf_bp.route('/')
@login_required
def dashboard():
    """Masraf dashboard - özet ve son masraflar"""
    calisan = Calisan.query.filter_by(email=current_user.email, is_deleted=False).first()
    
    # Admin ise admin dashboard'a yönlendir
    if not calisan:
        if current_user.has_permission('masraf.admin'):
            return redirect(url_for('masraf.admin_dashboard'))
        flash('Çalışan kaydınız bulunamadı.', 'warning')
        return redirect(url_for('core.dashboard'))
    
    # Özet bilgiler
    bugun = date.today()
    ozet = get_calisan_masraf_ozeti(calisan.id, bugun.year, bugun.month)
    
    # Son masraflar
    son_masraflar = Masraf.query.filter_by(
        calisan_id=calisan.id,
        is_deleted=False
    ).order_by(Masraf.created_at.desc()).limit(10).all()
    
    # Kategoriler (hızlı ekleme için)
    kategoriler = MasrafKategorisi.query.filter_by(aktif=True).order_by(MasrafKategorisi.sira).all()
    
    return render_template('masraf/dashboard.html',
                          calisan=calisan,
                          ozet=ozet,
                          son_masraflar=son_masraflar,
                          kategoriler=kategoriler,
                          bugun=bugun)


# ============================================================
# MASRAF LİSTESİ
# ============================================================

@masraf_bp.route('/liste')
@login_required
def liste():
    """Masraf listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    kategori_id = request.args.get('kategori_id', type=int)
    ay = request.args.get('ay', type=int)
    yil = request.args.get('yil', type=int)
    
    # Kullanıcının çalışan kaydı
    calisan = Calisan.query.filter_by(email=current_user.email, is_deleted=False).first()
    
    # Admin tüm masrafları görebilir
    if current_user.has_permission('masraf.admin'):
        query = Masraf.query.filter_by(is_deleted=False)
    elif calisan:
        query = Masraf.query.filter_by(calisan_id=calisan.id, is_deleted=False)
    else:
        flash('Çalışan kaydınız bulunamadı.', 'warning')
        return redirect(url_for('core.dashboard'))
    
    # Filtreler
    if durum:
        query = query.filter(Masraf.durum == durum)
    if kategori_id:
        query = query.filter(Masraf.kategori_id == kategori_id)
    if ay and yil:
        query = query.filter(Masraf.donem_ay == ay, Masraf.donem_yil == yil)
    elif yil:
        query = query.filter(Masraf.donem_yil == yil)
    
    query = query.order_by(Masraf.masraf_tarihi.desc())
    pagination = paginate_query(query, page, 20)
    
    kategoriler = MasrafKategorisi.query.filter_by(aktif=True).order_by(MasrafKategorisi.ad).all()
    
    return render_template('masraf/liste.html',
                          masraflar=pagination.items,
                          pagination=pagination,
                          kategoriler=kategoriler)


# ============================================================
# MASRAF EKLE/DÜZENLE
# ============================================================

@masraf_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
def ekle():
    """Yeni masraf ekle"""
    calisan = Calisan.query.filter_by(email=current_user.email, is_deleted=False).first()
    
    if not calisan:
        flash('Çalışan kaydınız bulunamadı.', 'warning')
        return redirect(url_for('core.dashboard'))
    
    if request.method == 'POST':
        masraf = Masraf(
            calisan_id=calisan.id,
            baslik=request.form.get('baslik', '').strip(),
            aciklama=request.form.get('aciklama', '').strip() or None,
            masraf_tarihi=datetime.strptime(request.form['masraf_tarihi'], '%Y-%m-%d').date(),
            kategori_id=int(request.form['kategori_id']) if request.form.get('kategori_id') else None,
            tutar=Decimal(request.form.get('tutar', '0').replace(',', '.')),
            kdv_orani=int(request.form.get('kdv_orani', 20)),
            para_birimi=request.form.get('para_birimi', 'TRY'),
            proje_id=int(request.form['proje_id']) if request.form.get('proje_id') else None,
            firma_adi=request.form.get('firma_adi', '').strip() or None,
            fatura_no=request.form.get('fatura_no', '').strip() or None,
            durum='taslak'
        )
        
        # Dönem bilgisi
        masraf.donem_ay = masraf.masraf_tarihi.month
        masraf.donem_yil = masraf.masraf_tarihi.year
        
        # Döviz kuru
        if masraf.para_birimi != 'TRY' and request.form.get('kur'):
            masraf.kur = Decimal(request.form.get('kur', '1').replace(',', '.'))
        
        # KDV hesapla
        masraf.hesapla_kdv()
        
        db.session.add(masraf)
        db.session.flush()
        
        # Dosya yükleme
        if 'dosya' in request.files:
            file = request.files['dosya']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                
                upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'masraf', str(masraf.id))
                os.makedirs(upload_folder, exist_ok=True)
                
                filepath = os.path.join(upload_folder, unique_name)
                file.save(filepath)
                
                masraf.dosya_adi = filename
                masraf.dosya_yolu = filepath
                masraf.dosya_tipi = file.content_type
        
        db.session.commit()
        
        flash('Masraf kaydedildi.', 'success')
        return redirect(url_for('masraf.detay', id=masraf.id))
    
    kategoriler = MasrafKategorisi.query.filter_by(aktif=True).order_by(MasrafKategorisi.sira).all()
    projeler = Proje.query.filter_by(is_deleted=False, durum='aktif').order_by(Proje.ad).all()
    
    return render_template('masraf/form.html',
                          masraf=None,
                          kategoriler=kategoriler,
                          projeler=projeler)


@masraf_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
def duzenle(id):
    """Masraf düzenle"""
    masraf = Masraf.query.get_or_404(id)
    
    # Yetki kontrolü
    calisan = Calisan.query.filter_by(email=current_user.email, is_deleted=False).first()
    if not calisan or (masraf.calisan_id != calisan.id and not current_user.has_permission('masraf.admin')):
        flash('Bu masrafı düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('masraf.liste'))
    
    if not masraf.duzenlenebilir:
        flash('Bu masraf düzenlenemez.', 'warning')
        return redirect(url_for('masraf.detay', id=id))
    
    if request.method == 'POST':
        masraf.baslik = request.form.get('baslik', '').strip()
        masraf.aciklama = request.form.get('aciklama', '').strip() or None
        masraf.masraf_tarihi = datetime.strptime(request.form['masraf_tarihi'], '%Y-%m-%d').date()
        masraf.kategori_id = int(request.form['kategori_id']) if request.form.get('kategori_id') else None
        masraf.tutar = Decimal(request.form.get('tutar', '0').replace(',', '.'))
        masraf.kdv_orani = int(request.form.get('kdv_orani', 20))
        masraf.para_birimi = request.form.get('para_birimi', 'TRY')
        masraf.proje_id = int(request.form['proje_id']) if request.form.get('proje_id') else None
        masraf.firma_adi = request.form.get('firma_adi', '').strip() or None
        masraf.fatura_no = request.form.get('fatura_no', '').strip() or None
        
        # Dönem güncelle
        masraf.donem_ay = masraf.masraf_tarihi.month
        masraf.donem_yil = masraf.masraf_tarihi.year
        
        # Döviz kuru
        if masraf.para_birimi != 'TRY' and request.form.get('kur'):
            masraf.kur = Decimal(request.form.get('kur', '1').replace(',', '.'))
        
        # KDV hesapla
        masraf.hesapla_kdv()
        
        # Reddedilmişse taslağa çevir
        if masraf.durum == 'reddedildi':
            masraf.durum = 'taslak'
        
        # Yeni dosya yükleme
        if 'dosya' in request.files:
            file = request.files['dosya']
            if file and file.filename and allowed_file(file.filename):
                # Eski dosyayı sil
                if masraf.dosya_yolu and os.path.exists(masraf.dosya_yolu):
                    os.remove(masraf.dosya_yolu)
                
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                
                upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'masraf', str(masraf.id))
                os.makedirs(upload_folder, exist_ok=True)
                
                filepath = os.path.join(upload_folder, unique_name)
                file.save(filepath)
                
                masraf.dosya_adi = filename
                masraf.dosya_yolu = filepath
                masraf.dosya_tipi = file.content_type
        
        db.session.commit()
        
        flash('Masraf güncellendi.', 'success')
        return redirect(url_for('masraf.detay', id=id))
    
    kategoriler = MasrafKategorisi.query.filter_by(aktif=True).order_by(MasrafKategorisi.sira).all()
    projeler = Proje.query.filter_by(is_deleted=False, durum='aktif').order_by(Proje.ad).all()
    
    return render_template('masraf/form.html',
                          masraf=masraf,
                          kategoriler=kategoriler,
                          projeler=projeler)


# ============================================================
# MASRAF DETAY
# ============================================================

@masraf_bp.route('/<int:id>')
@login_required
def detay(id):
    """Masraf detayı"""
    masraf = Masraf.query.get_or_404(id)
    
    # Yetki kontrolü
    calisan = Calisan.query.filter_by(email=current_user.email, is_deleted=False).first()
    is_owner = calisan and masraf.calisan_id == calisan.id
    is_admin = current_user.has_permission('masraf.admin')
    
    if not is_owner and not is_admin:
        flash('Bu masrafı görüntüleme yetkiniz yok.', 'danger')
        return redirect(url_for('masraf.liste'))
    
    return render_template('masraf/detay.html',
                          masraf=masraf,
                          is_owner=is_owner)


# ============================================================
# ONAYA GÖNDER
# ============================================================

@masraf_bp.route('/<int:id>/onaya-gonder', methods=['POST'])
@login_required
def onaya_gonder(id):
    """Masrafı onaya gönder"""
    masraf = Masraf.query.get_or_404(id)
    
    # Yetki kontrolü
    calisan = Calisan.query.filter_by(email=current_user.email, is_deleted=False).first()
    if not calisan or masraf.calisan_id != calisan.id:
        flash('Bu masrafı onaya gönderme yetkiniz yok.', 'danger')
        return redirect(url_for('masraf.liste'))
    
    if masraf.durum not in ['taslak', 'reddedildi']:
        flash('Bu masraf onaya gönderilemez.', 'warning')
        return redirect(url_for('masraf.detay', id=id))
    
    # Fatura zorunlu mu kontrol
    if masraf.kategori and masraf.kategori.fatura_zorunlu and not masraf.dosya_yolu:
        flash('Bu kategori için fatura/fiş yüklemek zorunludur.', 'warning')
        return redirect(url_for('masraf.detay', id=id))
    
    # Onay talebi oluştur
    talep, hata = OnayServisi.talep_olustur(
        onay_tipi_kod='MASRAF',
        referans_tablo='masraflar',
        referans_id=masraf.id,
        talep_eden_id=current_user.id
    )
    
    if hata:
        flash(f'Onay talebi oluşturulamadı: {hata}', 'danger')
        return redirect(url_for('masraf.detay', id=id))
    
    masraf.durum = 'onay_bekliyor'
    masraf.onay_talebi_id = talep.id
    db.session.commit()
    
    flash('Masraf onaya gönderildi.', 'success')
    return redirect(url_for('masraf.detay', id=id))


# ============================================================
# DOSYA İNDİR
# ============================================================

@masraf_bp.route('/<int:id>/dosya')
@login_required
def dosya_indir(id):
    """Masraf faturası/fişini indir"""
    masraf = Masraf.query.get_or_404(id)
    
    # Yetki kontrolü
    calisan = Calisan.query.filter_by(email=current_user.email, is_deleted=False).first()
    is_owner = calisan and masraf.calisan_id == calisan.id
    is_admin = current_user.has_permission('masraf.admin')
    
    if not is_owner and not is_admin:
        flash('Bu dosyaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('masraf.liste'))
    
    if not masraf.dosya_yolu or not os.path.exists(masraf.dosya_yolu):
        flash('Dosya bulunamadı.', 'warning')
        return redirect(url_for('masraf.detay', id=id))
    
    return send_file(masraf.dosya_yolu, 
                     download_name=masraf.dosya_adi,
                     as_attachment=True)


# ============================================================
# SİL
# ============================================================

@masraf_bp.route('/<int:id>/sil', methods=['POST'])
@login_required
def sil(id):
    """Masrafı sil (soft delete)"""
    masraf = Masraf.query.get_or_404(id)
    
    # Yetki kontrolü
    calisan = Calisan.query.filter_by(email=current_user.email, is_deleted=False).first()
    if not calisan or masraf.calisan_id != calisan.id:
        flash('Bu masrafı silme yetkiniz yok.', 'danger')
        return redirect(url_for('masraf.liste'))
    
    if masraf.durum not in ['taslak', 'reddedildi']:
        flash('Sadece taslak veya reddedilmiş masraflar silinebilir.', 'warning')
        return redirect(url_for('masraf.detay', id=id))
    
    masraf.is_deleted = True
    masraf.deleted_at = datetime.utcnow()
    db.session.commit()
    
    flash('Masraf silindi.', 'success')
    return redirect(url_for('masraf.liste'))


# ============================================================
# KATEGORİ YÖNETİMİ (Admin)
# ============================================================

@masraf_bp.route('/kategoriler')
@login_required
@permission_required('masraf.admin')
def kategori_liste():
    """Masraf kategorileri"""
    kategoriler = MasrafKategorisi.query.order_by(MasrafKategorisi.sira, MasrafKategorisi.ad).all()
    return render_template('masraf/kategori_liste.html', kategoriler=kategoriler)


@masraf_bp.route('/kategori/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('masraf.admin')
def kategori_ekle():
    """Yeni kategori ekle"""
    if request.method == 'POST':
        kategori = MasrafKategorisi(
            ad=request.form.get('ad', '').strip(),
            kod=request.form.get('kod', '').strip().upper() or None,
            aciklama=request.form.get('aciklama', '').strip() or None,
            ikon=request.form.get('ikon', 'bi-receipt'),
            renk=request.form.get('renk', 'secondary'),
            fatura_zorunlu=request.form.get('fatura_zorunlu') == 'on',
            muhasebe_kodu=request.form.get('muhasebe_kodu', '').strip() or None
        )
        
        if request.form.get('gunluk_limit'):
            kategori.gunluk_limit = Decimal(request.form['gunluk_limit'].replace(',', '.'))
        if request.form.get('aylik_limit'):
            kategori.aylik_limit = Decimal(request.form['aylik_limit'].replace(',', '.'))
        
        db.session.add(kategori)
        db.session.commit()
        
        flash('Kategori eklendi.', 'success')
        return redirect(url_for('masraf.kategori_liste'))
    
    return render_template('masraf/kategori_form.html', kategori=None)


# ============================================================
# RAPORLAR
# ============================================================


@masraf_bp.route('/admin')
@login_required
@permission_required('masraf.admin')
def admin_dashboard():
    """Admin masraf dashboard"""
    from sqlalchemy import func
    from datetime import date
    
    bugun = date.today()
    
    # Genel istatistikler
    stats = {
        'bekleyen': Masraf.query.filter_by(durum='onay_bekliyor', is_deleted=False).count(),
        'bu_ay_toplam': db.session.query(func.sum(Masraf.tl_karsiligi)).filter(
            Masraf.is_deleted == False,
            Masraf.donem_ay == bugun.month,
            Masraf.donem_yil == bugun.year
        ).scalar() or 0,
        'onaylanan': Masraf.query.filter_by(durum='onaylandi', is_deleted=False).count(),
    }
    
    # Son masraflar (tümü)
    son_masraflar = Masraf.query.filter_by(is_deleted=False).order_by(Masraf.created_at.desc()).limit(20).all()
    
    # Kategoriler
    kategoriler = MasrafKategorisi.query.filter_by(aktif=True).order_by(MasrafKategorisi.sira).all()
    
    return render_template('masraf/admin_dashboard.html',
                          stats=stats,
                          son_masraflar=son_masraflar,
                          kategoriler=kategoriler,
                          bugun=bugun)


@masraf_bp.route('/rapor')
@login_required
@permission_required('masraf.admin')
def rapor():
    """Masraf raporları"""
    from sqlalchemy import func
    
    yil = request.args.get('yil', date.today().year, type=int)
    ay = request.args.get('ay', type=int)
    
    # Genel özet
    query = Masraf.query.filter(
        Masraf.is_deleted == False,
        Masraf.donem_yil == yil
    )
    
    if ay:
        query = query.filter(Masraf.donem_ay == ay)
    
    # Kategori bazlı
    kategori_ozet = db.session.query(
        MasrafKategorisi.ad,
        func.count(Masraf.id).label('adet'),
        func.sum(Masraf.tl_karsiligi).label('toplam')
    ).join(Masraf, Masraf.kategori_id == MasrafKategorisi.id).filter(
        Masraf.is_deleted == False,
        Masraf.donem_yil == yil
    )
    
    if ay:
        kategori_ozet = kategori_ozet.filter(Masraf.donem_ay == ay)
    
    kategori_ozet = kategori_ozet.group_by(MasrafKategorisi.ad).all()
    
    # Aylık trend
    aylik_trend = db.session.query(
        Masraf.donem_ay,
        func.sum(Masraf.tl_karsiligi).label('toplam')
    ).filter(
        Masraf.is_deleted == False,
        Masraf.donem_yil == yil
    ).group_by(Masraf.donem_ay).order_by(Masraf.donem_ay).all()
    
    return render_template('masraf/rapor.html',
                          yil=yil,
                          ay=ay,
                          kategori_ozet=kategori_ozet,
                          aylik_trend=aylik_trend)


# ============================================================
# API - AJAX için
# ============================================================

@masraf_bp.route('/api/kategori/<int:id>')
@login_required
def api_kategori_detay(id):
    """Kategori detayı (form için)"""
    kategori = MasrafKategorisi.query.get_or_404(id)
    return jsonify({
        'id': kategori.id,
        'ad': kategori.ad,
        'fatura_zorunlu': kategori.fatura_zorunlu,
        'gunluk_limit': float(kategori.gunluk_limit) if kategori.gunluk_limit else None,
        'aylik_limit': float(kategori.aylik_limit) if kategori.aylik_limit else None
    })
