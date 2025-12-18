# -*- coding: utf-8 -*-
"""
TG Portal - Filo Routes
Araç yönetimi
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models.filo import Arac, FiloIslem, YakitKayit, Sigorta, Muayene
from app.models.base import AracDurumu, YakitTipi, IslemTipi
from app.models.ik import Calisan
from app.models.proje import Proje
from app.utils import permission_required

filo_bp = Blueprint('filo', __name__)


@filo_bp.route('/')
@login_required
@permission_required('filo.view')
def liste():
    """Araç listesi"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    durum = request.args.get('durum', '')
    proje_id = request.args.get('proje_id', type=int)
    
    query = Arac.query.filter_by(is_deleted=False)
    
    if search:
        query = query.filter(
            db.or_(
                Arac.plaka.ilike(f'%{search}%'),
                Arac.marka.ilike(f'%{search}%'),
                Arac.model.ilike(f'%{search}%')
            )
        )
    
    if durum:
        query = query.filter_by(durum=AracDurumu(durum))
    
    if proje_id:
        query = query.filter_by(proje_id=proje_id)
    
    query = query.order_by(Arac.plaka)
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    # Filtre için projeler
    projeler = Proje.query.filter_by(is_deleted=False, aktif=True).order_by(Proje.ad).all()
    
    return render_template('filo/liste.html',
                         araclar=pagination.items,
                         pagination=pagination,
                         projeler=projeler,
                         durumlar=AracDurumu)


@filo_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('filo.create')
def ekle():
    """Yeni araç ekle"""
    if request.method == 'POST':
        arac = Arac(
            plaka=request.form.get('plaka', '').upper().replace(' ', ''),
            marka=request.form.get('marka'),
            model=request.form.get('model'),
            model_yili=request.form.get('model_yili') or None,
            renk=request.form.get('renk'),
            sasi_no=request.form.get('sasi_no'),
            motor_no=request.form.get('motor_no'),
            yakit_tipi=YakitTipi(request.form.get('yakit_tipi')) if request.form.get('yakit_tipi') else None,
            motor_hacmi=request.form.get('motor_hacmi') or None,
            vites_tipi=request.form.get('vites_tipi'),
            km=request.form.get('km') or 0,
            sahiplik_tipi=request.form.get('sahiplik_tipi'),
            kira_baslangic=request.form.get('kira_baslangic') or None,
            kira_bitis=request.form.get('kira_bitis') or None,
            aylik_kira=request.form.get('aylik_kira') or None,
            atanan_calisan_id=request.form.get('atanan_calisan_id') or None,
            proje_id=request.form.get('proje_id') or None,
            durum=AracDurumu(request.form.get('durum')) if request.form.get('durum') else AracDurumu.AKTIF,
            notlar=request.form.get('notlar')
        )
        
        try:
            db.session.add(arac)
            db.session.commit()
            flash('Araç başarıyla eklendi.', 'success')
            return redirect(url_for('filo.detay', id=arac.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'danger')
    
    calisanlar = Calisan.query.filter_by(is_deleted=False).order_by(Calisan.ad).all()
    projeler = Proje.query.filter_by(is_deleted=False, aktif=True).order_by(Proje.ad).all()
    
    return render_template('filo/form.html',
                         arac=None,
                         calisanlar=calisanlar,
                         projeler=projeler,
                         durumlar=AracDurumu,
                         yakit_tipleri=YakitTipi)


@filo_bp.route('/<int:id>')
@login_required
@permission_required('filo.view')
def detay(id):
    """Araç detayı"""
    arac = Arac.query.get_or_404(id)
    
    son_islemler = arac.islemler.order_by(FiloIslem.tarih.desc()).limit(5).all()
    son_yakit = arac.yakit_kayitlari.order_by(YakitKayit.tarih.desc()).limit(5).all()
    
    return render_template('filo/detay.html',
                         arac=arac,
                         son_islemler=son_islemler,
                         son_yakit=son_yakit)


@filo_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('filo.edit')
def duzenle(id):
    """Araç düzenle"""
    arac = Arac.query.get_or_404(id)
    
    if request.method == 'POST':
        arac.plaka = request.form.get('plaka', '').upper().replace(' ', '')
        arac.marka = request.form.get('marka')
        arac.model = request.form.get('model')
        arac.model_yili = request.form.get('model_yili') or None
        arac.renk = request.form.get('renk')
        arac.sasi_no = request.form.get('sasi_no')
        arac.motor_no = request.form.get('motor_no')
        arac.yakit_tipi = YakitTipi(request.form.get('yakit_tipi')) if request.form.get('yakit_tipi') else None
        arac.motor_hacmi = request.form.get('motor_hacmi') or None
        arac.vites_tipi = request.form.get('vites_tipi')
        arac.km = request.form.get('km') or 0
        arac.sahiplik_tipi = request.form.get('sahiplik_tipi')
        arac.kira_baslangic = request.form.get('kira_baslangic') or None
        arac.kira_bitis = request.form.get('kira_bitis') or None
        arac.aylik_kira = request.form.get('aylik_kira') or None
        arac.atanan_calisan_id = request.form.get('atanan_calisan_id') or None
        arac.proje_id = request.form.get('proje_id') or None
        arac.durum = AracDurumu(request.form.get('durum')) if request.form.get('durum') else AracDurumu.AKTIF
        arac.notlar = request.form.get('notlar')
        
        try:
            db.session.commit()
            flash('Araç başarıyla güncellendi.', 'success')
            return redirect(url_for('filo.detay', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'danger')
    
    calisanlar = Calisan.query.filter_by(is_deleted=False).order_by(Calisan.ad).all()
    projeler = Proje.query.filter_by(is_deleted=False, aktif=True).order_by(Proje.ad).all()
    
    return render_template('filo/form.html',
                         arac=arac,
                         calisanlar=calisanlar,
                         projeler=projeler,
                         durumlar=AracDurumu,
                         yakit_tipleri=YakitTipi)


@filo_bp.route('/<int:id>/sil')
@login_required
@permission_required('filo.delete')
def sil(id):
    """Araç sil (soft delete)"""
    arac = Arac.query.get_or_404(id)
    arac.is_deleted = True
    arac.deleted_at = datetime.utcnow()
    arac.deleted_by = current_user.id
    db.session.commit()
    flash('Araç silindi.', 'success')
    return redirect(url_for('filo.liste'))


# ==================== YAKIT ====================

@filo_bp.route('/<int:id>/yakit/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('filo.edit')
def yakit_ekle(id):
    """Yakıt kaydı ekle"""
    arac = Arac.query.get_or_404(id)
    
    if request.method == 'POST':
        kayit = YakitKayit(
            arac_id=id,
            tarih=datetime.strptime(request.form.get('tarih'), '%Y-%m-%dT%H:%M') if request.form.get('tarih') else datetime.now(),
            km=request.form.get('km'),
            yakit_tipi=arac.yakit_tipi,
            litre=request.form.get('litre'),
            birim_fiyat=request.form.get('birim_fiyat'),
            tutar=request.form.get('tutar'),
            istasyon_adi=request.form.get('istasyon_adi'),
            full_depo=request.form.get('full_depo') == 'on'
        )
        
        # Araç km güncelle
        if kayit.km and int(kayit.km) > (arac.km or 0):
            arac.km = kayit.km
            arac.son_km_guncelleme = datetime.utcnow()
        
        db.session.add(kayit)
        db.session.commit()
        flash('Yakıt kaydı eklendi.', 'success')
        return redirect(url_for('filo.detay', id=id))
    
    return render_template('filo/yakit_form.html', arac=arac)


# ==================== İŞLEM ====================

@filo_bp.route('/<int:id>/islem/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('filo.edit')
def islem_ekle(id):
    """İşlem kaydı ekle (bakım, tamir vb.)"""
    arac = Arac.query.get_or_404(id)
    
    if request.method == 'POST':
        islem = FiloIslem(
            arac_id=id,
            islem_tipi=IslemTipi(request.form.get('islem_tipi')),
            tarih=datetime.strptime(request.form.get('tarih'), '%Y-%m-%d').date() if request.form.get('tarih') else date.today(),
            km=request.form.get('km'),
            tutar=request.form.get('tutar'),
            kdv=request.form.get('kdv'),
            toplam=request.form.get('toplam'),
            aciklama=request.form.get('aciklama'),
            fatura_no=request.form.get('fatura_no'),
            sonraki_tarih=datetime.strptime(request.form.get('sonraki_tarih'), '%Y-%m-%d').date() if request.form.get('sonraki_tarih') else None,
            sonraki_km=request.form.get('sonraki_km')
        )
        
        # Araç km güncelle
        if islem.km and int(islem.km) > (arac.km or 0):
            arac.km = islem.km
            arac.son_km_guncelleme = datetime.utcnow()
        
        db.session.add(islem)
        db.session.commit()
        flash('İşlem kaydı eklendi.', 'success')
        return redirect(url_for('filo.detay', id=id))
    
    return render_template('filo/islem_form.html', arac=arac, islem_tipleri=IslemTipi)


# ==================== API ====================

@filo_bp.route('/api/araclar')
@login_required
def api_araclar():
    """Select2 için araç arama"""
    q = request.args.get('q', '')
    query = Arac.query.filter_by(is_deleted=False)
    
    if q:
        query = query.filter(
            db.or_(
                Arac.plaka.ilike(f'%{q}%'),
                Arac.marka.ilike(f'%{q}%')
            )
        )
    
    araclar = query.order_by(Arac.plaka).limit(20).all()
    return jsonify([{'id': a.id, 'text': a.display_name} for a in araclar])
