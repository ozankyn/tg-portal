# -*- coding: utf-8 -*-
"""
TG Portal - Onay Sistemi Routes
Bu dosyayı app/modules/onay/routes.py olarak kaydet
"""

from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.onay import (
    OnayTipi, OnayAkisi, OnayAdimi, OnayTalebi, OnayKaydi, 
    YetkiDevri, OnayServisi
)
from app.models.core import User
from app.utils import permission_required, paginate_query

onay_bp = Blueprint('onay', __name__)


# ============================================================
# BEKLEYEN ONAYLAR (Ana Sayfa)
# ============================================================

@onay_bp.route('/')
@login_required
def index():
    """Bekleyen onaylar dashboard"""
    bekleyenler = OnayServisi.bekleyen_onaylar(current_user.id)
    
    # Acil olanları ayır
    acil_onaylar = [k for k in bekleyenler if k.talep.acil]
    normal_onaylar = [k for k in bekleyenler if not k.talep.acil]
    
    # İstatistikler
    stats = {
        'bekleyen': len(bekleyenler),
        'acil': len(acil_onaylar),
        'bugun_onaylanan': OnayKaydi.query.filter(
            OnayKaydi.onaylayici_id == current_user.id,
            OnayKaydi.durum == 'onaylandi',
            db.func.date(OnayKaydi.islem_tarihi) == date.today()
        ).count()
    }
    
    return render_template('onay/index.html',
                          acil_onaylar=acil_onaylar,
                          normal_onaylar=normal_onaylar,
                          stats=stats)


# ============================================================
# ONAY DETAY & İŞLEM
# ============================================================

@onay_bp.route('/talep/<int:id>')
@login_required
def talep_detay(id):
    """Onay talebi detayı"""
    talep = OnayTalebi.query.get_or_404(id)
    
    # Yetki kontrolü - talep eden veya onaylayıcı mı?
    is_talep_eden = talep.talep_eden_id == current_user.id
    bekleyen_kayit = talep.kayitlar.filter_by(
        onaylayici_id=current_user.id, 
        durum='bekliyor'
    ).first()
    is_admin = current_user.has_permission('onay.admin')
    
    if not (is_talep_eden or bekleyen_kayit or is_admin):
        flash('Bu talebi görüntüleme yetkiniz yok.', 'danger')
        return redirect(url_for('onay.index'))
    
    # Referans kaydı getir
    referans = _get_referans_kayit(talep.referans_tablo, talep.referans_id)
    
    return render_template('onay/talep_detay.html',
                          talep=talep,
                          referans=referans,
                          bekleyen_kayit=bekleyen_kayit,
                          is_talep_eden=is_talep_eden)


@onay_bp.route('/kayit/<int:id>/onayla', methods=['POST'])
@login_required
def onayla(id):
    """Onay kaydını onayla"""
    not_ = request.form.get('not', '').strip()
    
    basarili, hata = OnayServisi.onayla(id, current_user.id, not_)
    
    if basarili:
        flash('Talep onaylandı.', 'success')
    else:
        flash(f'Hata: {hata}', 'danger')
    
    # Talep detayına dön
    kayit = OnayKaydi.query.get(id)
    if kayit:
        return redirect(url_for('onay.talep_detay', id=kayit.talep_id))
    return redirect(url_for('onay.index'))


@onay_bp.route('/kayit/<int:id>/reddet', methods=['POST'])
@login_required
def reddet(id):
    """Onay kaydını reddet"""
    not_ = request.form.get('not', '').strip()
    
    if not not_:
        flash('Red nedeni zorunludur.', 'warning')
        kayit = OnayKaydi.query.get(id)
        if kayit:
            return redirect(url_for('onay.talep_detay', id=kayit.talep_id))
        return redirect(url_for('onay.index'))
    
    basarili, hata = OnayServisi.reddet(id, current_user.id, not_)
    
    if basarili:
        flash('Talep reddedildi.', 'info')
    else:
        flash(f'Hata: {hata}', 'danger')
    
    kayit = OnayKaydi.query.get(id)
    if kayit:
        return redirect(url_for('onay.talep_detay', id=kayit.talep_id))
    return redirect(url_for('onay.index'))


# ============================================================
# TALEPLERİM (Kullanıcının kendi talepleri)
# ============================================================

@onay_bp.route('/taleplerim')
@login_required
def taleplerim():
    """Kullanıcının kendi talepleri"""
    durum = request.args.get('durum')
    talepler = OnayServisi.kullanici_talepleri(current_user.id, durum)
    
    return render_template('onay/taleplerim.html', talepler=talepler)


@onay_bp.route('/talep/<int:id>/iptal', methods=['POST'])
@login_required
def talep_iptal(id):
    """Talebi iptal et (sadece talep eden)"""
    talep = OnayTalebi.query.get_or_404(id)
    
    if talep.talep_eden_id != current_user.id:
        flash('Bu talebi iptal etme yetkiniz yok.', 'danger')
        return redirect(url_for('onay.taleplerim'))
    
    if talep.durum != 'bekliyor':
        flash('Sadece bekleyen talepler iptal edilebilir.', 'warning')
        return redirect(url_for('onay.talep_detay', id=id))
    
    talep.durum = 'iptal'
    talep.sonuc_tarihi = datetime.utcnow()
    talep.sonuc_notu = 'Talep eden tarafından iptal edildi.'
    
    # Bekleyen kayıtları da iptal et
    for kayit in talep.kayitlar.filter_by(durum='bekliyor').all():
        kayit.durum = 'atlandi'
        kayit.islem_tarihi = datetime.utcnow()
    
    db.session.commit()
    flash('Talep iptal edildi.', 'info')
    return redirect(url_for('onay.taleplerim'))


# ============================================================
# YETKİ DEVRİ
# ============================================================

@onay_bp.route('/yetki-devri')
@login_required
def yetki_devri_liste():
    """Yetki devri listesi"""
    verdiklerim = YetkiDevri.query.filter_by(devreden_id=current_user.id).order_by(YetkiDevri.baslangic_tarihi.desc()).all()
    aldıklarim = YetkiDevri.query.filter_by(devralan_id=current_user.id).order_by(YetkiDevri.baslangic_tarihi.desc()).all()
    
    return render_template('onay/yetki_devri_liste.html',
                          verdiklerim=verdiklerim,
                          aldiklarim=aldıklarim)


@onay_bp.route('/yetki-devri/ekle', methods=['GET', 'POST'])
@login_required
def yetki_devri_ekle():
    """Yetki devri oluştur"""
    if request.method == 'POST':
        devralan_id = request.form.get('devralan_id')
        baslangic = request.form.get('baslangic_tarihi')
        bitis = request.form.get('bitis_tarihi')
        neden = request.form.get('neden', '').strip()
        
        if not all([devralan_id, baslangic, bitis]):
            flash('Tüm alanları doldurun.', 'warning')
            return redirect(url_for('onay.yetki_devri_ekle'))
        
        # Kendine devredemez
        if int(devralan_id) == current_user.id:
            flash('Yetkiyi kendinize devredemezsiniz.', 'warning')
            return redirect(url_for('onay.yetki_devri_ekle'))
        
        devir = YetkiDevri(
            devreden_id=current_user.id,
            devralan_id=int(devralan_id),
            baslangic_tarihi=datetime.strptime(baslangic, '%Y-%m-%d').date(),
            bitis_tarihi=datetime.strptime(bitis, '%Y-%m-%d').date(),
            neden=neden or None
        )
        db.session.add(devir)
        db.session.commit()
        
        flash('Yetki devri oluşturuldu.', 'success')
        return redirect(url_for('onay.yetki_devri_liste'))
    
    # Devredilebilecek kullanıcılar
    kullanicilar = User.query.filter(
        User.id != current_user.id,
        User.aktif == True
    ).order_by(User.username).all()
    
    return render_template('onay/yetki_devri_form.html', kullanicilar=kullanicilar)


@onay_bp.route('/yetki-devri/<int:id>/iptal', methods=['POST'])
@login_required
def yetki_devri_iptal(id):
    """Yetki devrini iptal et"""
    devir = YetkiDevri.query.get_or_404(id)
    
    if devir.devreden_id != current_user.id:
        flash('Bu yetki devrini iptal etme yetkiniz yok.', 'danger')
        return redirect(url_for('onay.yetki_devri_liste'))
    
    devir.aktif = False
    db.session.commit()
    
    flash('Yetki devri iptal edildi.', 'info')
    return redirect(url_for('onay.yetki_devri_liste'))


# ============================================================
# ADMIN - ONAY AKIŞLARI YÖNETİMİ
# ============================================================

@onay_bp.route('/admin/tipler')
@login_required
@permission_required('onay.admin')
def admin_tipler():
    """Onay tipleri listesi"""
    tipler = OnayTipi.query.order_by(OnayTipi.sira, OnayTipi.ad).all()
    return render_template('onay/admin_tipler.html', tipler=tipler)


@onay_bp.route('/admin/tip/<int:id>/akislar')
@login_required
@permission_required('onay.admin')
def admin_akislar(id):
    """Onay tipi akışları"""
    tip = OnayTipi.query.get_or_404(id)
    akislar = tip.akislar.filter_by(is_deleted=False).all()
    
    return render_template('onay/admin_akislar.html', tip=tip, akislar=akislar)


@onay_bp.route('/admin/akis/<int:id>')
@login_required
@permission_required('onay.admin')
def admin_akis_detay(id):
    """Akış detayı ve adımları"""
    akis = OnayAkisi.query.get_or_404(id)
    adimlar = akis.adimlar.order_by(OnayAdimi.sira).all()
    
    return render_template('onay/admin_akis_detay.html', akis=akis, adimlar=adimlar)


@onay_bp.route('/admin/akis/ekle/<int:tip_id>', methods=['GET', 'POST'])
@login_required
@permission_required('onay.admin')
def admin_akis_ekle(tip_id):
    """Yeni akış ekle"""
    tip = OnayTipi.query.get_or_404(tip_id)
    
    if request.method == 'POST':
        akis = OnayAkisi(
            onay_tipi_id=tip_id,
            ad=request.form.get('ad', '').strip(),
            aciklama=request.form.get('aciklama', '').strip() or None,
            oncelik=int(request.form.get('oncelik', 0))
        )
        db.session.add(akis)
        db.session.commit()
        
        flash('Akış oluşturuldu. Şimdi adımları ekleyebilirsiniz.', 'success')
        return redirect(url_for('onay.admin_akis_detay', id=akis.id))
    
    return render_template('onay/admin_akis_form.html', tip=tip, akis=None)


@onay_bp.route('/admin/akis/<int:id>/adim-ekle', methods=['POST'])
@login_required
@permission_required('onay.admin')
def admin_adim_ekle(id):
    """Akışa adım ekle"""
    akis = OnayAkisi.query.get_or_404(id)
    
    # Mevcut max sıra
    max_sira = db.session.query(db.func.max(OnayAdimi.sira)).filter_by(akis_id=id).scalar() or 0
    
    adim = OnayAdimi(
        akis_id=id,
        ad=request.form.get('ad', '').strip(),
        sira=max_sira + 1,
        onaylayici_tipi=request.form.get('onaylayici_tipi', 'yonetici'),
        onaylayici_rol=request.form.get('onaylayici_rol') or None,
        onaylayici_kullanici_id=int(request.form['onaylayici_kullanici_id']) if request.form.get('onaylayici_kullanici_id') else None,
        paralel=request.form.get('paralel') == 'on',
        tumu_onaymali=request.form.get('tumu_onaymali') == 'on'
    )
    db.session.add(adim)
    db.session.commit()
    
    flash('Adım eklendi.', 'success')
    return redirect(url_for('onay.admin_akis_detay', id=id))


@onay_bp.route('/admin/adim/<int:id>/sil', methods=['POST'])
@login_required
@permission_required('onay.admin')
def admin_adim_sil(id):
    """Adım sil"""
    adim = OnayAdimi.query.get_or_404(id)
    akis_id = adim.akis_id
    
    db.session.delete(adim)
    db.session.commit()
    
    flash('Adım silindi.', 'success')
    return redirect(url_for('onay.admin_akis_detay', id=akis_id))


# ============================================================
# TÜM TALEPLER (Admin)
# ============================================================

@onay_bp.route('/admin/talepler')
@login_required
@permission_required('onay.admin')
def admin_talepler():
    """Tüm talepler listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    tip_id = request.args.get('tip_id', type=int)
    
    query = OnayTalebi.query.filter_by(is_deleted=False)
    
    if durum:
        query = query.filter(OnayTalebi.durum == durum)
    if tip_id:
        query = query.filter(OnayTalebi.onay_tipi_id == tip_id)
    
    query = query.order_by(OnayTalebi.talep_tarihi.desc())
    pagination = paginate_query(query, page, 20)
    
    tipler = OnayTipi.query.filter_by(aktif=True).all()
    
    return render_template('onay/admin_talepler.html',
                          talepler=pagination.items,
                          pagination=pagination,
                          tipler=tipler)


# ============================================================
# HELPER FONKSİYONLAR
# ============================================================

def _get_referans_kayit(tablo, id):
    """Referans tablosundan kaydı getir"""
    # Dinamik olarak ilgili modeli bul
    model_map = {
        'izinler': 'Izin',
        'masraflar': 'Masraf',
        'arac_talepleri': 'AracTalebi',
        # Diğer tablolar eklenecek
    }
    
    # Şimdilik basit bir dict döndür
    return {'tablo': tablo, 'id': id}


# ============================================================
# API ENDPOINTS (AJAX için)
# ============================================================

@onay_bp.route('/api/bekleyen-sayi')
@login_required
def api_bekleyen_sayi():
    """Bekleyen onay sayısı (header badge için)"""
    sayi = len(OnayServisi.bekleyen_onaylar(current_user.id))
    return jsonify({'sayi': sayi})
