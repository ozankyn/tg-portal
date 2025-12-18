# -*- coding: utf-8 -*-
"""
TG Portal - Tedarikçi Routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.tedarikci import Tedarikci, TedarikciIletisim, TedarikciDegerlendirme
from app.models.base import TedarikciTipi
from app.utils import permission_required, paginate_query

tedarikci_bp = Blueprint('tedarikci', __name__)


# ==================== LİSTE ====================

@tedarikci_bp.route('/')
@login_required
@permission_required('tedarikci.view')
def liste():
    """Tedarikçi listesi"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filtreler
    tip = request.args.get('tip')
    il = request.args.get('il')
    aktif = request.args.get('aktif')
    search = request.args.get('search', '').strip()
    
    query = Tedarikci.query.filter_by(is_deleted=False)
    
    if tip:
        query = query.filter(Tedarikci.tip == TedarikciTipi(tip))
    if il:
        query = query.filter(Tedarikci.il == il)
    if aktif is not None and aktif != '':
        query = query.filter(Tedarikci.aktif == (aktif == '1'))
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Tedarikci.unvan.ilike(search_filter),
                Tedarikci.kisa_ad.ilike(search_filter),
                Tedarikci.vergi_no.ilike(search_filter),
                Tedarikci.yetkili_adi.ilike(search_filter)
            )
        )
    
    query = query.order_by(Tedarikci.unvan)
    pagination = paginate_query(query, page, per_page)
    
    # Filtre seçenekleri
    iller = db.session.query(Tedarikci.il).filter(
        Tedarikci.il.isnot(None), Tedarikci.is_deleted == False
    ).distinct().order_by(Tedarikci.il).all()
    iller = [i[0] for i in iller if i[0]]
    
    return render_template('tedarikci/liste.html',
                          tedarikciler=pagination.items,
                          pagination=pagination,
                          tipler=TedarikciTipi,
                          iller=iller)


# ==================== DETAY ====================

@tedarikci_bp.route('/<int:id>')
@login_required
@permission_required('tedarikci.view')
def detay(id):
    """Tedarikçi detay sayfası"""
    tedarikci = Tedarikci.query.get_or_404(id)
    
    if tedarikci.is_deleted:
        flash('Bu tedarikçi silinmiş.', 'warning')
        return redirect(url_for('tedarikci.liste'))
    
    # İlişkili işlemler
    from app.models.filo import FiloIslem
    son_islemler = FiloIslem.query.filter_by(tedarikci_id=id).order_by(
        FiloIslem.tarih.desc()
    ).limit(10).all()
    
    return render_template('tedarikci/detay.html',
                          tedarikci=tedarikci,
                          son_islemler=son_islemler)


# ==================== EKLE ====================

@tedarikci_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('tedarikci.create')
def ekle():
    """Yeni tedarikçi ekle"""
    if request.method == 'POST':
        # Vergi no kontrolü
        vergi_no = request.form.get('vergi_no', '').strip()
        if vergi_no and Tedarikci.query.filter_by(vergi_no=vergi_no, is_deleted=False).first():
            flash('Bu vergi numarası zaten kayıtlı.', 'danger')
            return redirect(url_for('tedarikci.ekle'))
        
        tedarikci = Tedarikci(
            unvan=request.form.get('unvan', '').strip(),
            kisa_ad=request.form.get('kisa_ad', '').strip() or None,
            vergi_no=vergi_no or None,
            vergi_dairesi=request.form.get('vergi_dairesi', '').strip() or None,
            tip=TedarikciTipi(request.form.get('tip')) if request.form.get('tip') else TedarikciTipi.GENEL,
            alt_kategori=request.form.get('alt_kategori', '').strip() or None,
            adres=request.form.get('adres', '').strip() or None,
            il=request.form.get('il', '').strip() or None,
            ilce=request.form.get('ilce', '').strip() or None,
            telefon=request.form.get('telefon', '').strip() or None,
            telefon_2=request.form.get('telefon_2', '').strip() or None,
            email=request.form.get('email', '').strip() or None,
            web=request.form.get('web', '').strip() or None,
            yetkili_adi=request.form.get('yetkili_adi', '').strip() or None,
            yetkili_unvan=request.form.get('yetkili_unvan', '').strip() or None,
            yetkili_telefon=request.form.get('yetkili_telefon', '').strip() or None,
            yetkili_email=request.form.get('yetkili_email', '').strip() or None,
            banka_adi=request.form.get('banka_adi', '').strip() or None,
            iban=request.form.get('iban', '').strip() or None,
            odeme_vade=int(request.form.get('odeme_vade', 30)),
            odeme_yontemi=request.form.get('odeme_yontemi', '').strip() or None,
            notlar=request.form.get('notlar', '').strip() or None,
            aktif=request.form.get('aktif') == 'on',
            created_by=current_user.id
        )
        
        db.session.add(tedarikci)
        db.session.commit()
        
        flash(f'{tedarikci.display_name} tedarikçisi oluşturuldu.', 'success')
        return redirect(url_for('tedarikci.detay', id=tedarikci.id))
    
    return render_template('tedarikci/form.html', tedarikci=None, tipler=TedarikciTipi)


# ==================== DÜZENLE ====================

@tedarikci_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('tedarikci.edit')
def duzenle(id):
    """Tedarikçi düzenle"""
    tedarikci = Tedarikci.query.get_or_404(id)
    
    if request.method == 'POST':
        # Vergi no kontrolü (kendisi hariç)
        vergi_no = request.form.get('vergi_no', '').strip()
        if vergi_no:
            existing = Tedarikci.query.filter(
                Tedarikci.vergi_no == vergi_no,
                Tedarikci.id != id,
                Tedarikci.is_deleted == False
            ).first()
            if existing:
                flash('Bu vergi numarası başka bir tedarikçide kayıtlı.', 'danger')
                return redirect(url_for('tedarikci.duzenle', id=id))
        
        tedarikci.unvan = request.form.get('unvan', '').strip()
        tedarikci.kisa_ad = request.form.get('kisa_ad', '').strip() or None
        tedarikci.vergi_no = vergi_no or None
        tedarikci.vergi_dairesi = request.form.get('vergi_dairesi', '').strip() or None
        tedarikci.tip = TedarikciTipi(request.form.get('tip')) if request.form.get('tip') else TedarikciTipi.GENEL
        tedarikci.alt_kategori = request.form.get('alt_kategori', '').strip() or None
        tedarikci.adres = request.form.get('adres', '').strip() or None
        tedarikci.il = request.form.get('il', '').strip() or None
        tedarikci.ilce = request.form.get('ilce', '').strip() or None
        tedarikci.telefon = request.form.get('telefon', '').strip() or None
        tedarikci.telefon_2 = request.form.get('telefon_2', '').strip() or None
        tedarikci.email = request.form.get('email', '').strip() or None
        tedarikci.web = request.form.get('web', '').strip() or None
        tedarikci.yetkili_adi = request.form.get('yetkili_adi', '').strip() or None
        tedarikci.yetkili_unvan = request.form.get('yetkili_unvan', '').strip() or None
        tedarikci.yetkili_telefon = request.form.get('yetkili_telefon', '').strip() or None
        tedarikci.yetkili_email = request.form.get('yetkili_email', '').strip() or None
        tedarikci.banka_adi = request.form.get('banka_adi', '').strip() or None
        tedarikci.iban = request.form.get('iban', '').strip() or None
        tedarikci.odeme_vade = int(request.form.get('odeme_vade', 30))
        tedarikci.odeme_yontemi = request.form.get('odeme_yontemi', '').strip() or None
        tedarikci.notlar = request.form.get('notlar', '').strip() or None
        tedarikci.aktif = request.form.get('aktif') == 'on'
        tedarikci.updated_by = current_user.id
        
        db.session.commit()
        
        flash('Tedarikçi güncellendi.', 'success')
        return redirect(url_for('tedarikci.detay', id=id))
    
    return render_template('tedarikci/form.html', tedarikci=tedarikci, tipler=TedarikciTipi)


# ==================== SİL ====================

@tedarikci_bp.route('/<int:id>/sil', methods=['POST'])
@login_required
@permission_required('tedarikci.delete')
def sil(id):
    """Tedarikçi sil (soft delete)"""
    tedarikci = Tedarikci.query.get_or_404(id)
    
    tedarikci.soft_delete(current_user.id)
    db.session.commit()
    
    flash(f'{tedarikci.display_name} tedarikçisi silindi.', 'success')
    return redirect(url_for('tedarikci.liste'))


# ==================== API ====================

@tedarikci_bp.route('/api/search')
@login_required
def api_search():
    """Tedarikçi arama API (select2, autocomplete için)"""
    q = request.args.get('q', '').strip()
    tip = request.args.get('tip')
    limit = request.args.get('limit', 20, type=int)
    
    query = Tedarikci.query.filter_by(is_deleted=False, aktif=True)
    
    if q:
        search_filter = f'%{q}%'
        query = query.filter(
            db.or_(
                Tedarikci.unvan.ilike(search_filter),
                Tedarikci.kisa_ad.ilike(search_filter)
            )
        )
    
    if tip:
        query = query.filter(Tedarikci.tip == TedarikciTipi(tip))
    
    tedarikciler = query.order_by(Tedarikci.unvan).limit(limit).all()
    
    return jsonify({
        'results': [
            {
                'id': t.id,
                'text': t.display_name,
                'tip': t.tip_display
            } for t in tedarikciler
        ]
    })
