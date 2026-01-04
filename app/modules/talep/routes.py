# -*- coding: utf-8 -*-
"""
TG Portal - Talep/Ticket Modülü Routes
"""

from datetime import datetime, date
import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models.talep import (
    TalepKategorisi, Talep, TalepYorum,
    get_acik_talepler, get_talep_istatistikleri
)
from app.models.core import User
from app.utils import permission_required, paginate_query

talep_bp = Blueprint('talep', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'txt'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# DASHBOARD
# ============================================================

@talep_bp.route('/')
@login_required
def dashboard():
    """Talep dashboard"""
    # Admin veya destek ekibi mi?
    is_destek = current_user.has_permission('talep.admin')
    
    if is_destek:
        # Tüm istatistikler
        stats = get_talep_istatistikleri()
        # Bana atanan açık talepler
        bana_atanan = get_acik_talepler(atanan_id=current_user.id)
        # Atanmamış talepler
        atanmamis = Talep.query.filter_by(is_deleted=False, durum='acik', atanan_id=None).order_by(Talep.created_at).all()
    else:
        # Sadece kendi talepleri
        stats = get_talep_istatistikleri()
        stats['benim'] = Talep.query.filter_by(is_deleted=False, olusturan_id=current_user.id).filter(
            Talep.durum.in_(['acik', 'atandi', 'devam_ediyor', 'beklemede'])
        ).count()
        bana_atanan = []
        atanmamis = []
    
    # Son talepler
    if is_destek:
        son_talepler = Talep.query.filter_by(is_deleted=False).order_by(Talep.created_at.desc()).limit(10).all()
    else:
        son_talepler = Talep.query.filter_by(is_deleted=False, olusturan_id=current_user.id).order_by(Talep.created_at.desc()).limit(10).all()
    
    kategoriler = TalepKategorisi.query.filter_by(aktif=True).order_by(TalepKategorisi.sira).all()
    
    return render_template('talep/dashboard.html',
                          stats=stats,
                          bana_atanan=bana_atanan,
                          atanmamis=atanmamis,
                          son_talepler=son_talepler,
                          kategoriler=kategoriler,
                          is_destek=is_destek)


# ============================================================
# LİSTE
# ============================================================

@talep_bp.route('/liste')
@login_required
def liste():
    """Talep listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    kategori_id = request.args.get('kategori_id', type=int)
    oncelik = request.args.get('oncelik')
    sadece_benim = request.args.get('benim') == '1'
    
    is_destek = current_user.has_permission('talep.admin')
    
    query = Talep.query.filter_by(is_deleted=False)
    
    # Normal kullanıcılar sadece kendi taleplerini görsün
    if not is_destek or sadece_benim:
        query = query.filter(Talep.olusturan_id == current_user.id)
    
    if durum:
        query = query.filter(Talep.durum == durum)
    if kategori_id:
        query = query.filter(Talep.kategori_id == kategori_id)
    if oncelik:
        query = query.filter(Talep.oncelik == oncelik)
    
    query = query.order_by(Talep.created_at.desc())
    pagination = paginate_query(query, page, 20)
    
    kategoriler = TalepKategorisi.query.filter_by(aktif=True).order_by(TalepKategorisi.sira).all()
    
    return render_template('talep/liste.html',
                          talepler=pagination.items,
                          pagination=pagination,
                          kategoriler=kategoriler,
                          is_destek=is_destek)


# ============================================================
# YENİ TALEP
# ============================================================

@talep_bp.route('/yeni', methods=['GET', 'POST'])
@login_required
def yeni():
    """Yeni talep oluştur"""
    if request.method == 'POST':
        talep = Talep(
            olusturan_id=current_user.id,
            kategori_id=int(request.form['kategori_id']),
            konu=request.form.get('konu', '').strip(),
            aciklama=request.form.get('aciklama', '').strip(),
            oncelik=request.form.get('oncelik', 'normal'),
            durum='acik'
        )
        
        talep.talep_no_olustur()
        
        # Kategorinin varsayılan atananı varsa ata
        kategori = TalepKategorisi.query.get(talep.kategori_id)
        if kategori and kategori.varsayilan_atanan_id:
            talep.atanan_id = kategori.varsayilan_atanan_id
            talep.atanma_tarihi = datetime.utcnow()
            talep.durum = 'atandi'
        
        db.session.add(talep)
        db.session.flush()
        
        # Dosya yükleme
        if 'dosya' in request.files:
            file = request.files['dosya']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                
                upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'talep', str(talep.id))
                os.makedirs(upload_folder, exist_ok=True)
                
                filepath = os.path.join(upload_folder, unique_name)
                file.save(filepath)
                
                talep.dosya_adi = filename
                talep.dosya_yolu = filepath
        
        db.session.commit()
        
        flash(f'Talep oluşturuldu: {talep.talep_no}', 'success')
        return redirect(url_for('talep.detay', id=talep.id))
    
    kategoriler = TalepKategorisi.query.filter_by(aktif=True).order_by(TalepKategorisi.sira).all()
    
    return render_template('talep/form.html',
                          talep=None,
                          kategoriler=kategoriler)


# ============================================================
# DETAY
# ============================================================

@talep_bp.route('/<int:id>')
@login_required
def detay(id):
    """Talep detayı"""
    talep = Talep.query.get_or_404(id)
    is_destek = current_user.has_permission('talep.admin')
    
    # Yetki kontrolü
    if not is_destek and talep.olusturan_id != current_user.id:
        flash('Bu talebi görüntüleme yetkiniz yok.', 'danger')
        return redirect(url_for('talep.liste'))
    
    # Yorumları getir (dahili notlar sadece destek ekibine)
    if is_destek:
        yorumlar = talep.yorumlar.order_by(TalepYorum.created_at).all()
    else:
        yorumlar = talep.yorumlar.filter_by(dahili=False).order_by(TalepYorum.created_at).all()
    
    # Destek ekibi listesi (atama için)
    destek_ekibi = []
    if is_destek:
        destek_ekibi = User.query.filter_by(is_active=True).order_by(User.first_name).all()
    
    return render_template('talep/detay.html',
                          talep=talep,
                          yorumlar=yorumlar,
                          destek_ekibi=destek_ekibi,
                          is_destek=is_destek)


# ============================================================
# YORUM EKLE
# ============================================================

@talep_bp.route('/<int:id>/yorum', methods=['POST'])
@login_required
def yorum_ekle(id):
    """Talebe yorum ekle"""
    talep = Talep.query.get_or_404(id)
    is_destek = current_user.has_permission('talep.admin')
    
    # Yetki kontrolü
    if not is_destek and talep.olusturan_id != current_user.id:
        flash('Bu talebe yorum ekleme yetkiniz yok.', 'danger')
        return redirect(url_for('talep.liste'))
    
    icerik = request.form.get('icerik', '').strip()
    if not icerik:
        flash('Yorum boş olamaz.', 'warning')
        return redirect(url_for('talep.detay', id=id))
    
    yorum = TalepYorum(
        talep_id=talep.id,
        yazan_id=current_user.id,
        icerik=icerik,
        tip='cevap' if is_destek else 'yorum',
        dahili=request.form.get('dahili') == 'on' and is_destek
    )
    
    # Dosya
    if 'dosya' in request.files:
        file = request.files['dosya']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4().hex}_{filename}"
            
            upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'talep', str(talep.id), 'yorumlar')
            os.makedirs(upload_folder, exist_ok=True)
            
            filepath = os.path.join(upload_folder, unique_name)
            file.save(filepath)
            
            yorum.dosya_adi = filename
            yorum.dosya_yolu = filepath
    
    db.session.add(yorum)
    
    # İlk yanıt tarihini güncelle
    if is_destek and not talep.ilk_yanit_tarihi:
        talep.ilk_yanit_tarihi = datetime.utcnow()
    
    db.session.commit()
    
    flash('Yorum eklendi.', 'success')
    return redirect(url_for('talep.detay', id=id))


# ============================================================
# DURUM DEĞİŞTİR
# ============================================================

@talep_bp.route('/<int:id>/durum', methods=['POST'])
@login_required
@permission_required('talep.admin')
def durum_degistir(id):
    """Talep durumunu değiştir"""
    talep = Talep.query.get_or_404(id)
    
    yeni_durum = request.form.get('durum')
    if yeni_durum in ['acik', 'atandi', 'devam_ediyor', 'beklemede', 'cozuldu', 'kapatildi']:
        eski_durum = talep.durum
        talep.durum = yeni_durum
        
        # Özel durumlar
        if yeni_durum == 'cozuldu':
            talep.cozum_tarihi = datetime.utcnow()
            talep.cozum_notu = request.form.get('cozum_notu', '').strip() or None
        elif yeni_durum == 'kapatildi':
            talep.kapatma_tarihi = datetime.utcnow()
        
        # Durum değişikliği notu
        if eski_durum != yeni_durum:
            yorum = TalepYorum(
                talep_id=talep.id,
                yazan_id=current_user.id,
                icerik=f"Durum değiştirildi: {talep.durum_text}",
                tip='durum_degisikligi',
                dahili=True
            )
            db.session.add(yorum)
        
        db.session.commit()
        flash('Durum güncellendi.', 'success')
    
    return redirect(url_for('talep.detay', id=id))


# ============================================================
# ATAMA
# ============================================================

@talep_bp.route('/<int:id>/ata', methods=['POST'])
@login_required
@permission_required('talep.admin')
def ata(id):
    """Talebi birine ata"""
    talep = Talep.query.get_or_404(id)
    
    atanan_id = request.form.get('atanan_id', type=int)
    
    if atanan_id:
        talep.atanan_id = atanan_id
        talep.atanma_tarihi = datetime.utcnow()
        if talep.durum == 'acik':
            talep.durum = 'atandi'
        
        atanan = User.query.get(atanan_id)
        yorum = TalepYorum(
            talep_id=talep.id,
            yazan_id=current_user.id,
            icerik=f"Talep {atanan.full_name} kişisine atandı.",
            tip='durum_degisikligi',
            dahili=True
        )
        db.session.add(yorum)
    else:
        talep.atanan_id = None
        talep.atanma_tarihi = None
        talep.durum = 'acik'
    
    db.session.commit()
    flash('Atama güncellendi.', 'success')
    return redirect(url_for('talep.detay', id=id))


# ============================================================
# ÖNCELİK DEĞİŞTİR
# ============================================================

@talep_bp.route('/<int:id>/oncelik', methods=['POST'])
@login_required
@permission_required('talep.admin')
def oncelik_degistir(id):
    """Öncelik değiştir"""
    talep = Talep.query.get_or_404(id)
    
    yeni_oncelik = request.form.get('oncelik')
    if yeni_oncelik in ['dusuk', 'normal', 'yuksek', 'kritik']:
        talep.oncelik = yeni_oncelik
        db.session.commit()
        flash('Öncelik güncellendi.', 'success')
    
    return redirect(url_for('talep.detay', id=id))


# ============================================================
# DOSYA İNDİR
# ============================================================

@talep_bp.route('/<int:id>/dosya')
@login_required
def dosya_indir(id):
    """Talep dosyasını indir"""
    talep = Talep.query.get_or_404(id)
    is_destek = current_user.has_permission('talep.admin')
    
    if not is_destek and talep.olusturan_id != current_user.id:
        flash('Yetkiniz yok.', 'danger')
        return redirect(url_for('talep.liste'))
    
    if not talep.dosya_yolu or not os.path.exists(talep.dosya_yolu):
        flash('Dosya bulunamadı.', 'warning')
        return redirect(url_for('talep.detay', id=id))
    
    return send_file(talep.dosya_yolu, download_name=talep.dosya_adi, as_attachment=True)


@talep_bp.route('/yorum/<int:id>/dosya')
@login_required
def yorum_dosya_indir(id):
    """Yorum dosyasını indir"""
    yorum = TalepYorum.query.get_or_404(id)
    talep = yorum.talep
    is_destek = current_user.has_permission('talep.admin')
    
    if not is_destek and talep.olusturan_id != current_user.id:
        flash('Yetkiniz yok.', 'danger')
        return redirect(url_for('talep.liste'))
    
    if not yorum.dosya_yolu or not os.path.exists(yorum.dosya_yolu):
        flash('Dosya bulunamadı.', 'warning')
        return redirect(url_for('talep.detay', id=talep.id))
    
    return send_file(yorum.dosya_yolu, download_name=yorum.dosya_adi, as_attachment=True)


# ============================================================
# KATEGORİ YÖNETİMİ
# ============================================================

@talep_bp.route('/kategoriler')
@login_required
@permission_required('talep.admin')
def kategori_liste():
    """Kategori listesi"""
    kategoriler = TalepKategorisi.query.order_by(TalepKategorisi.sira, TalepKategorisi.ad).all()
    return render_template('talep/kategori_liste.html', kategoriler=kategoriler)


@talep_bp.route('/kategori/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('talep.admin')
def kategori_ekle():
    """Yeni kategori ekle"""
    if request.method == 'POST':
        kategori = TalepKategorisi(
            ad=request.form.get('ad', '').strip(),
            kod=request.form.get('kod', '').strip().upper() or None,
            aciklama=request.form.get('aciklama', '').strip() or None,
            ikon=request.form.get('ikon', 'bi-ticket'),
            renk=request.form.get('renk', 'primary'),
            sla_cevap=int(request.form.get('sla_cevap', 4)),
            sla_cozum=int(request.form.get('sla_cozum', 24)),
            sira=int(request.form.get('sira', 0))
        )
        
        if request.form.get('varsayilan_atanan_id'):
            kategori.varsayilan_atanan_id = int(request.form['varsayilan_atanan_id'])
        
        db.session.add(kategori)
        db.session.commit()
        
        flash('Kategori eklendi.', 'success')
        return redirect(url_for('talep.kategori_liste'))
    
    kullanicilar = User.query.filter_by(is_active=True).order_by(User.first_name).all()
    return render_template('talep/kategori_form.html', kategori=None, kullanicilar=kullanicilar)


# ============================================================
# API
# ============================================================

@talep_bp.route('/api/istatistikler')
@login_required
@permission_required('talep.admin')
def api_istatistikler():
    """Dashboard için istatistikler"""
    stats = get_talep_istatistikleri()
    return jsonify(stats)
