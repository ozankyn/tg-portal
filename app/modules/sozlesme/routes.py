# -*- coding: utf-8 -*-
"""
TG Portal - Sözleşme Modülü Routes
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models.sozlesme import (
    Sozlesme, SozlesmeTipi, SozlesmeEk,
    get_yaklasan_sozlesmeler, get_sona_eren_sozlesmeler
)
from app.models.proje import Musteri
from app.models.tedarikci import Tedarikci
from app.models.ik import Calisan
from app.models.base import CalisanDurumu
from app.utils import permission_required, paginate_query

sozlesme_bp = Blueprint('sozlesme', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# DASHBOARD
# ============================================================

@sozlesme_bp.route('/')
@login_required
@permission_required('sozlesme.view')
def dashboard():
    """Sözleşme dashboard"""
    from sqlalchemy import func
    
    # İstatistikler
    stats = {
        'toplam': Sozlesme.query.filter_by(is_deleted=False).count(),
        'aktif': Sozlesme.query.filter_by(is_deleted=False, durum='aktif').count(),
        'yaklasan_30': len(get_yaklasan_sozlesmeler(30)),
        'yaklasan_7': len(get_yaklasan_sozlesmeler(7)),
    }
    
    # Yaklaşan sözleşmeler
    yaklasan = get_yaklasan_sozlesmeler(30)
    
    # Tip bazlı dağılım
    tip_dagilim = db.session.query(
        SozlesmeTipi.ad,
        func.count(Sozlesme.id).label('adet')
    ).join(Sozlesme, Sozlesme.tip_id == SozlesmeTipi.id).filter(
        Sozlesme.is_deleted == False,
        Sozlesme.durum == 'aktif'
    ).group_by(SozlesmeTipi.ad).all()
    
    # Son eklenen sözleşmeler
    son_eklenen = Sozlesme.query.filter_by(is_deleted=False).order_by(
        Sozlesme.created_at.desc()
    ).limit(10).all()
    
    return render_template('sozlesme/dashboard.html',
                          stats=stats,
                          yaklasan=yaklasan,
                          tip_dagilim=tip_dagilim,
                          son_eklenen=son_eklenen)


# ============================================================
# LİSTE
# ============================================================

@sozlesme_bp.route('/liste')
@login_required
@permission_required('sozlesme.view')
def liste():
    """Sözleşme listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    tip_id = request.args.get('tip_id', type=int)
    taraf_tipi = request.args.get('taraf_tipi')
    arama = request.args.get('q', '').strip()
    
    query = Sozlesme.query.filter_by(is_deleted=False)
    
    # Filtreler
    if durum:
        query = query.filter(Sozlesme.durum == durum)
    if tip_id:
        query = query.filter(Sozlesme.tip_id == tip_id)
    if taraf_tipi == 'musteri':
        query = query.filter(Sozlesme.musteri_id.isnot(None))
    elif taraf_tipi == 'tedarikci':
        query = query.filter(Sozlesme.tedarikci_id.isnot(None))
    elif taraf_tipi == 'diger':
        query = query.filter(
            Sozlesme.musteri_id.is_(None),
            Sozlesme.tedarikci_id.is_(None)
        )
    
    if arama:
        query = query.filter(
            db.or_(
                Sozlesme.baslik.ilike(f'%{arama}%'),
                Sozlesme.sozlesme_no.ilike(f'%{arama}%')
            )
        )
    
    query = query.order_by(Sozlesme.bitis_tarihi.asc())
    pagination = paginate_query(query, page, 20)
    
    tipler = SozlesmeTipi.query.filter_by(aktif=True).order_by(SozlesmeTipi.sira).all()
    
    return render_template('sozlesme/liste.html',
                          sozlesmeler=pagination.items,
                          pagination=pagination,
                          tipler=tipler)


# ============================================================
# EKLE / DÜZENLE
# ============================================================

@sozlesme_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('sozlesme.create')
def ekle():
    """Yeni sözleşme ekle"""
    if request.method == 'POST':
        sozlesme = Sozlesme(
            baslik=request.form.get('baslik', '').strip(),
            sozlesme_no=request.form.get('sozlesme_no', '').strip() or None,
            aciklama=request.form.get('aciklama', '').strip() or None,
            tip_id=int(request.form['tip_id']),
            baslangic_tarihi=datetime.strptime(request.form['baslangic_tarihi'], '%Y-%m-%d').date(),
            bitis_tarihi=datetime.strptime(request.form['bitis_tarihi'], '%Y-%m-%d').date(),
            otomatik_yenileme=request.form.get('otomatik_yenileme') == 'on',
            yenileme_suresi_ay=int(request.form.get('yenileme_suresi_ay', 12)),
            para_birimi=request.form.get('para_birimi', 'TRY'),
            kdv_dahil=request.form.get('kdv_dahil') == 'on',
            odeme_periyodu=request.form.get('odeme_periyodu') or None,
            ozel_sartlar=request.form.get('ozel_sartlar', '').strip() or None,
            notlar=request.form.get('notlar', '').strip() or None,
            durum=CalisanDurumu.AKTIF
        )
        
        # İmza tarihi
        if request.form.get('imza_tarihi'):
            sozlesme.imza_tarihi = datetime.strptime(request.form['imza_tarihi'], '%Y-%m-%d').date()
        
        # Tutar
        if request.form.get('tutar'):
            sozlesme.tutar = Decimal(request.form['tutar'].replace(',', '.'))
        
        # Taraf
        taraf_tipi = request.form.get('taraf_tipi')
        if taraf_tipi == 'musteri':
            sozlesme.musteri_id = int(request.form['musteri_id'])
        elif taraf_tipi == 'tedarikci':
            sozlesme.tedarikci_id = int(request.form['tedarikci_id'])
        else:
            sozlesme.diger_taraf = request.form.get('diger_taraf', '').strip()
        
        # Sorumlu
        if request.form.get('sorumlu_id'):
            sozlesme.sorumlu_id = int(request.form['sorumlu_id'])
        
        db.session.add(sozlesme)
        db.session.flush()
        
        # Dosya yükleme
        if 'dosya' in request.files:
            file = request.files['dosya']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                
                upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'sozlesme', str(sozlesme.id))
                os.makedirs(upload_folder, exist_ok=True)
                
                filepath = os.path.join(upload_folder, unique_name)
                file.save(filepath)
                
                sozlesme.dosya_adi = filename
                sozlesme.dosya_yolu = filepath
        
        db.session.commit()
        
        flash('Sözleşme eklendi.', 'success')
        return redirect(url_for('sozlesme.detay', id=sozlesme.id))
    
    tipler = SozlesmeTipi.query.filter_by(aktif=True).order_by(SozlesmeTipi.sira).all()
    musteriler = Musteri.query.filter_by(is_deleted=False).order_by(Musteri.ad).all()
    tedarikciler = Tedarikci.query.filter_by(is_deleted=False).order_by(Tedarikci.unvan).all()
    calisanlar = Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AKTIF).order_by(Calisan.ad).all()
    
    return render_template('sozlesme/form.html',
                          sozlesme=None,
                          tipler=tipler,
                          musteriler=musteriler,
                          tedarikciler=tedarikciler,
                          calisanlar=calisanlar)


@sozlesme_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('sozlesme.edit')
def duzenle(id):
    """Sözleşme düzenle"""
    sozlesme = Sozlesme.query.get_or_404(id)
    
    if request.method == 'POST':
        sozlesme.baslik = request.form.get('baslik', '').strip()
        sozlesme.sozlesme_no = request.form.get('sozlesme_no', '').strip() or None
        sozlesme.aciklama = request.form.get('aciklama', '').strip() or None
        sozlesme.tip_id = int(request.form['tip_id'])
        sozlesme.baslangic_tarihi = datetime.strptime(request.form['baslangic_tarihi'], '%Y-%m-%d').date()
        sozlesme.bitis_tarihi = datetime.strptime(request.form['bitis_tarihi'], '%Y-%m-%d').date()
        sozlesme.otomatik_yenileme = request.form.get('otomatik_yenileme') == 'on'
        sozlesme.yenileme_suresi_ay = int(request.form.get('yenileme_suresi_ay', 12))
        sozlesme.para_birimi = request.form.get('para_birimi', 'TRY')
        sozlesme.kdv_dahil = request.form.get('kdv_dahil') == 'on'
        sozlesme.odeme_periyodu = request.form.get('odeme_periyodu') or None
        sozlesme.ozel_sartlar = request.form.get('ozel_sartlar', '').strip() or None
        sozlesme.notlar = request.form.get('notlar', '').strip() or None
        
        # İmza tarihi
        if request.form.get('imza_tarihi'):
            sozlesme.imza_tarihi = datetime.strptime(request.form['imza_tarihi'], '%Y-%m-%d').date()
        else:
            sozlesme.imza_tarihi = None
        
        # Tutar
        if request.form.get('tutar'):
            sozlesme.tutar = Decimal(request.form['tutar'].replace(',', '.'))
        else:
            sozlesme.tutar = None
        
        # Taraf
        taraf_tipi = request.form.get('taraf_tipi')
        sozlesme.musteri_id = None
        sozlesme.tedarikci_id = None
        sozlesme.diger_taraf = None
        
        if taraf_tipi == 'musteri':
            sozlesme.musteri_id = int(request.form['musteri_id'])
        elif taraf_tipi == 'tedarikci':
            sozlesme.tedarikci_id = int(request.form['tedarikci_id'])
        else:
            sozlesme.diger_taraf = request.form.get('diger_taraf', '').strip()
        
        # Sorumlu
        if request.form.get('sorumlu_id'):
            sozlesme.sorumlu_id = int(request.form['sorumlu_id'])
        else:
            sozlesme.sorumlu_id = None
        
        # Yeni dosya
        if 'dosya' in request.files:
            file = request.files['dosya']
            if file and file.filename and allowed_file(file.filename):
                # Eski dosyayı sil
                if sozlesme.dosya_yolu and os.path.exists(sozlesme.dosya_yolu):
                    os.remove(sozlesme.dosya_yolu)
                
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                
                upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'sozlesme', str(sozlesme.id))
                os.makedirs(upload_folder, exist_ok=True)
                
                filepath = os.path.join(upload_folder, unique_name)
                file.save(filepath)
                
                sozlesme.dosya_adi = filename
                sozlesme.dosya_yolu = filepath
        
        db.session.commit()
        
        flash('Sözleşme güncellendi.', 'success')
        return redirect(url_for('sozlesme.detay', id=id))
    
    tipler = SozlesmeTipi.query.filter_by(aktif=True).order_by(SozlesmeTipi.sira).all()
    musteriler = Musteri.query.filter_by(is_deleted=False).order_by(Musteri.ad).all()
    tedarikciler = Tedarikci.query.filter_by(is_deleted=False).order_by(Tedarikci.unvan).all()
    calisanlar = Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AKTIF).order_by(Calisan.ad).all()
    
    return render_template('sozlesme/form.html',
                          sozlesme=sozlesme,
                          tipler=tipler,
                          musteriler=musteriler,
                          tedarikciler=tedarikciler,
                          calisanlar=calisanlar)


# ============================================================
# DETAY
# ============================================================

@sozlesme_bp.route('/<int:id>')
@login_required
@permission_required('sozlesme.view')
def detay(id):
    """Sözleşme detayı"""
    sozlesme = Sozlesme.query.get_or_404(id)
    ekler = sozlesme.ekler.all()
    
    return render_template('sozlesme/detay.html',
                          sozlesme=sozlesme,
                          ekler=ekler)


# ============================================================
# YENİLE
# ============================================================

@sozlesme_bp.route('/<int:id>/yenile', methods=['POST'])
@login_required
@permission_required('sozlesme.edit')
def yenile(id):
    """Sözleşmeyi yenile"""
    sozlesme = Sozlesme.query.get_or_404(id)
    
    ay = request.form.get('ay', type=int) or sozlesme.yenileme_suresi_ay or 12
    sozlesme.yenile(ay)
    db.session.commit()
    
    flash(f'Sözleşme {ay} ay uzatıldı.', 'success')
    return redirect(url_for('sozlesme.detay', id=id))


# ============================================================
# DURUM DEĞİŞTİR
# ============================================================

@sozlesme_bp.route('/<int:id>/durum', methods=['POST'])
@login_required
@permission_required('sozlesme.edit')
def durum_degistir(id):
    """Sözleşme durumunu değiştir"""
    sozlesme = Sozlesme.query.get_or_404(id)
    
    yeni_durum = request.form.get('durum')
    if yeni_durum in ['aktif', 'sona_erdi', 'iptal', 'askida']:
        sozlesme.durum = yeni_durum
        db.session.commit()
        flash('Sözleşme durumu güncellendi.', 'success')
    
    return redirect(url_for('sozlesme.detay', id=id))


# ============================================================
# DOSYA İNDİR
# ============================================================

@sozlesme_bp.route('/<int:id>/dosya')
@login_required
@permission_required('sozlesme.view')
def dosya_indir(id):
    """Sözleşme dosyasını indir"""
    sozlesme = Sozlesme.query.get_or_404(id)
    
    if not sozlesme.dosya_yolu or not os.path.exists(sozlesme.dosya_yolu):
        flash('Dosya bulunamadı.', 'warning')
        return redirect(url_for('sozlesme.detay', id=id))
    
    return send_file(sozlesme.dosya_yolu,
                     download_name=sozlesme.dosya_adi,
                     as_attachment=True)


# ============================================================
# EK DOSYA İŞLEMLERİ
# ============================================================

@sozlesme_bp.route('/<int:id>/ek/ekle', methods=['POST'])
@login_required
@permission_required('sozlesme.edit')
def ek_ekle(id):
    """Sözleşmeye ek dosya ekle"""
    sozlesme = Sozlesme.query.get_or_404(id)
    
    if 'dosya' not in request.files:
        flash('Dosya seçilmedi.', 'warning')
        return redirect(url_for('sozlesme.detay', id=id))
    
    file = request.files['dosya']
    if not file or not file.filename:
        flash('Dosya seçilmedi.', 'warning')
        return redirect(url_for('sozlesme.detay', id=id))
    
    if not allowed_file(file.filename):
        flash('Geçersiz dosya tipi.', 'danger')
        return redirect(url_for('sozlesme.detay', id=id))
    
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    
    upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'sozlesme', str(sozlesme.id), 'ekler')
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, unique_name)
    file.save(filepath)
    
    ek = SozlesmeEk(
        sozlesme_id=sozlesme.id,
        baslik=request.form.get('baslik', '').strip() or filename,
        aciklama=request.form.get('aciklama', '').strip() or None,
        dosya_adi=filename,
        dosya_yolu=filepath,
        dosya_tipi=file.content_type
    )
    
    db.session.add(ek)
    db.session.commit()
    
    flash('Ek dosya eklendi.', 'success')
    return redirect(url_for('sozlesme.detay', id=id))


@sozlesme_bp.route('/ek/<int:id>/indir')
@login_required
@permission_required('sozlesme.view')
def ek_indir(id):
    """Ek dosyayı indir"""
    ek = SozlesmeEk.query.get_or_404(id)
    
    if not ek.dosya_yolu or not os.path.exists(ek.dosya_yolu):
        flash('Dosya bulunamadı.', 'warning')
        return redirect(url_for('sozlesme.detay', id=ek.sozlesme_id))
    
    return send_file(ek.dosya_yolu,
                     download_name=ek.dosya_adi,
                     as_attachment=True)


@sozlesme_bp.route('/ek/<int:id>/sil', methods=['POST'])
@login_required
@permission_required('sozlesme.edit')
def ek_sil(id):
    """Ek dosyayı sil"""
    ek = SozlesmeEk.query.get_or_404(id)
    sozlesme_id = ek.sozlesme_id
    
    if ek.dosya_yolu and os.path.exists(ek.dosya_yolu):
        os.remove(ek.dosya_yolu)
    
    db.session.delete(ek)
    db.session.commit()
    
    flash('Ek dosya silindi.', 'success')
    return redirect(url_for('sozlesme.detay', id=sozlesme_id))


# ============================================================
# SİL
# ============================================================

@sozlesme_bp.route('/<int:id>/sil', methods=['POST'])
@login_required
@permission_required('sozlesme.delete')
def sil(id):
    """Sözleşmeyi sil (soft delete)"""
    sozlesme = Sozlesme.query.get_or_404(id)
    
    sozlesme.is_deleted = True
    sozlesme.deleted_at = datetime.utcnow()
    db.session.commit()
    
    flash('Sözleşme silindi.', 'success')
    return redirect(url_for('sozlesme.liste'))


# ============================================================
# TİP YÖNETİMİ
# ============================================================

@sozlesme_bp.route('/tipler')
@login_required
@permission_required('sozlesme.admin')
def tip_liste():
    """Sözleşme tipleri"""
    tipler = SozlesmeTipi.query.order_by(SozlesmeTipi.sira, SozlesmeTipi.ad).all()
    return render_template('sozlesme/tip_liste.html', tipler=tipler)


@sozlesme_bp.route('/tip/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('sozlesme.admin')
def tip_ekle():
    """Yeni sözleşme tipi ekle"""
    if request.method == 'POST':
        tip = SozlesmeTipi(
            ad=request.form.get('ad', '').strip(),
            kod=request.form.get('kod', '').strip().upper() or None,
            aciklama=request.form.get('aciklama', '').strip() or None,
            uyari_gun_1=int(request.form.get('uyari_gun_1', 30)),
            uyari_gun_2=int(request.form.get('uyari_gun_2', 15)),
            uyari_gun_3=int(request.form.get('uyari_gun_3', 7)),
            sira=int(request.form.get('sira', 0))
        )
        
        db.session.add(tip)
        db.session.commit()
        
        flash('Sözleşme tipi eklendi.', 'success')
        return redirect(url_for('sozlesme.tip_liste'))
    
    return render_template('sozlesme/tip_form.html', tip=None)


# ============================================================
# API
# ============================================================

@sozlesme_bp.route('/api/yaklasan')
@login_required
def api_yaklasan():
    """Yaklaşan sözleşmeler API"""
    gun = request.args.get('gun', 30, type=int)
    sozlesmeler = get_yaklasan_sozlesmeler(gun)
    
    return jsonify([{
        'id': s.id,
        'baslik': s.baslik,
        'taraf': s.taraf_adi,
        'bitis': s.bitis_tarihi.strftime('%d.%m.%Y'),
        'kalan_gun': s.kalan_gun
    } for s in sozlesmeler])
