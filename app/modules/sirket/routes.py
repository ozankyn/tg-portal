# -*- coding: utf-8 -*-
"""
Şirket / Tüzel Kişi Modülü Routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models.sirket import TuzelKisi, SgkDosya
from app.utils import permission_required

sirket_bp = Blueprint('sirket', __name__)


# ==================== TÜZEL KİŞİLER ====================

@sirket_bp.route('/')
@login_required
@permission_required('ayarlar.view')
def liste():
    """Tüzel kişi listesi"""
    tuzel_kisiler = TuzelKisi.query.filter_by(is_deleted=False).order_by(TuzelKisi.ad).all()
    return render_template('sirket/liste.html', tuzel_kisiler=tuzel_kisiler)


@sirket_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('ayarlar.edit')
def ekle():
    """Yeni tüzel kişi ekle"""
    if request.method == 'POST':
        tuzel_kisi = TuzelKisi(
            ad=request.form.get('ad', '').strip(),
            kisa_ad=request.form.get('kisa_ad', '').strip() or None,
            vergi_no=request.form.get('vergi_no', '').strip() or None,
            vergi_dairesi=request.form.get('vergi_dairesi', '').strip() or None,
            mersis_no=request.form.get('mersis_no', '').strip() or None,
            adres=request.form.get('adres', '').strip() or None,
            telefon=request.form.get('telefon', '').strip() or None,
            email=request.form.get('email', '').strip() or None,
            aktif=request.form.get('aktif') == 'on'
        )
        db.session.add(tuzel_kisi)
        db.session.commit()
        flash('Tüzel kişi eklendi.', 'success')
        return redirect(url_for('sirket.detay', id=tuzel_kisi.id))
    
    return render_template('sirket/form.html', tuzel_kisi=None)


@sirket_bp.route('/<int:id>')
@login_required
@permission_required('ayarlar.view')
def detay(id):
    """Tüzel kişi detayı"""
    tuzel_kisi = TuzelKisi.query.get_or_404(id)
    sgk_dosyalari = tuzel_kisi.sgk_dosyalari.filter_by(is_deleted=False).all()
    return render_template('sirket/detay.html', tuzel_kisi=tuzel_kisi, sgk_dosyalari=sgk_dosyalari)


@sirket_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('ayarlar.edit')
def duzenle(id):
    """Tüzel kişi düzenle"""
    tuzel_kisi = TuzelKisi.query.get_or_404(id)
    
    if request.method == 'POST':
        tuzel_kisi.ad = request.form.get('ad', '').strip()
        tuzel_kisi.kisa_ad = request.form.get('kisa_ad', '').strip() or None
        tuzel_kisi.vergi_no = request.form.get('vergi_no', '').strip() or None
        tuzel_kisi.vergi_dairesi = request.form.get('vergi_dairesi', '').strip() or None
        tuzel_kisi.mersis_no = request.form.get('mersis_no', '').strip() or None
        tuzel_kisi.adres = request.form.get('adres', '').strip() or None
        tuzel_kisi.telefon = request.form.get('telefon', '').strip() or None
        tuzel_kisi.email = request.form.get('email', '').strip() or None
        tuzel_kisi.aktif = request.form.get('aktif') == 'on'
        
        db.session.commit()
        flash('Tüzel kişi güncellendi.', 'success')
        return redirect(url_for('sirket.detay', id=id))
    
    return render_template('sirket/form.html', tuzel_kisi=tuzel_kisi)


# ==================== SGK DOSYALARI ====================

@sirket_bp.route('/<int:tuzel_kisi_id>/sgk/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('ayarlar.edit')
def sgk_ekle(tuzel_kisi_id):
    """SGK dosyası ekle"""
    tuzel_kisi = TuzelKisi.query.get_or_404(tuzel_kisi_id)
    
    if request.method == 'POST':
        sgk = SgkDosya(
            tuzel_kisi_id=tuzel_kisi_id,
            dosya_no=request.form.get('dosya_no', '').strip(),
            ad=request.form.get('ad', '').strip() or None,
            il=request.form.get('il', '').strip() or None,
            ilce=request.form.get('ilce', '').strip() or None,
            tehlike_sinifi=request.form.get('tehlike_sinifi', '').strip() or None,
            aktif=request.form.get('aktif') == 'on'
        )
        db.session.add(sgk)
        db.session.commit()
        flash('SGK dosyası eklendi.', 'success')
        return redirect(url_for('sirket.detay', id=tuzel_kisi_id))
    
    return render_template('sirket/sgk_form.html', tuzel_kisi=tuzel_kisi, sgk=None)


@sirket_bp.route('/sgk/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('ayarlar.edit')
def sgk_duzenle(id):
    """SGK dosyası düzenle"""
    sgk = SgkDosya.query.get_or_404(id)
    
    if request.method == 'POST':
        sgk.dosya_no = request.form.get('dosya_no', '').strip()
        sgk.ad = request.form.get('ad', '').strip() or None
        sgk.il = request.form.get('il', '').strip() or None
        sgk.ilce = request.form.get('ilce', '').strip() or None
        sgk.tehlike_sinifi = request.form.get('tehlike_sinifi', '').strip() or None
        sgk.aktif = request.form.get('aktif') == 'on'
        
        db.session.commit()
        flash('SGK dosyası güncellendi.', 'success')
        return redirect(url_for('sirket.detay', id=sgk.tuzel_kisi_id))
    
    return render_template('sirket/sgk_form.html', tuzel_kisi=sgk.tuzel_kisi, sgk=sgk)
