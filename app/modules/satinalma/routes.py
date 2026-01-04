# -*- coding: utf-8 -*-
"""
TG Portal - Satın Alma Modülü Routes
Talep → Teklif → Sipariş → Teslimat akışı
"""

from datetime import datetime, date
from decimal import Decimal
import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models.satinalma import (
    SatinAlmaKategorisi, SatinAlmaTalebi, TalepKalemi,
    SatinAlmaTeklif, TeklifKalemi, SatinAlmaSiparisi, SiparisTeslimat
)
from app.models.tedarikci import Tedarikci
from app.models.proje import Proje
from app.models.onay import OnayServisi
from app.utils import permission_required, paginate_query

satinalma_bp = Blueprint('satinalma', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# DASHBOARD
# ============================================================

@satinalma_bp.route('/')
@login_required
@permission_required('satinalma.view')
def dashboard():
    """Satın alma dashboard"""
    # İstatistikler
    stats = {
        'bekleyen_talepler': SatinAlmaTalebi.query.filter_by(is_deleted=False, durum='onay_bekliyor').count(),
        'acik_talepler': SatinAlmaTalebi.query.filter(
            SatinAlmaTalebi.is_deleted == False,
            SatinAlmaTalebi.durum.in_(['onaylandi', 'teklif_asamasinda'])
        ).count(),
        'bekleyen_siparisler': SatinAlmaSiparisi.query.filter_by(is_deleted=False, durum='siparis_verildi').count(),
        'bu_ay_toplam': db.session.query(db.func.sum(SatinAlmaSiparisi.toplam_tutar)).filter(
            SatinAlmaSiparisi.is_deleted == False,
            db.extract('month', SatinAlmaSiparisi.siparis_tarihi) == date.today().month,
            db.extract('year', SatinAlmaSiparisi.siparis_tarihi) == date.today().year
        ).scalar() or 0
    }
    
    # Son talepler
    son_talepler = SatinAlmaTalebi.query.filter_by(is_deleted=False).order_by(
        SatinAlmaTalebi.created_at.desc()
    ).limit(10).all()
    
    # Bekleyen siparişler
    bekleyen_siparisler = SatinAlmaSiparisi.query.filter_by(
        is_deleted=False, durum='siparis_verildi'
    ).order_by(SatinAlmaSiparisi.beklenen_teslimat).limit(5).all()
    
    return render_template('satinalma/dashboard.html',
                          stats=stats,
                          son_talepler=son_talepler,
                          bekleyen_siparisler=bekleyen_siparisler)


# ============================================================
# TALEP YÖNETİMİ
# ============================================================

@satinalma_bp.route('/talepler')
@login_required
@permission_required('satinalma.view')
def talep_liste():
    """Talep listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    kategori_id = request.args.get('kategori_id', type=int)
    
    query = SatinAlmaTalebi.query.filter_by(is_deleted=False)
    
    # Sadece kendi taleplerini görsün (admin hariç)
    if not current_user.has_permission('satinalma.admin'):
        query = query.filter(SatinAlmaTalebi.talep_eden_id == current_user.id)
    
    if durum:
        query = query.filter(SatinAlmaTalebi.durum == durum)
    if kategori_id:
        query = query.filter(SatinAlmaTalebi.kategori_id == kategori_id)
    
    query = query.order_by(SatinAlmaTalebi.created_at.desc())
    pagination = paginate_query(query, page, 20)
    
    kategoriler = SatinAlmaKategorisi.query.filter_by(aktif=True).order_by(SatinAlmaKategorisi.sira).all()
    
    return render_template('satinalma/talep_liste.html',
                          talepler=pagination.items,
                          pagination=pagination,
                          kategoriler=kategoriler)


@satinalma_bp.route('/talep/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('satinalma.create')
def talep_ekle():
    """Yeni talep oluştur"""
    if request.method == 'POST':
        talep = SatinAlmaTalebi(
            talep_eden_id=current_user.id,
            baslik=request.form.get('baslik', '').strip(),
            aciklama=request.form.get('aciklama', '').strip() or None,
            gerekce=request.form.get('gerekce', '').strip() or None,
            kategori_id=int(request.form['kategori_id']) if request.form.get('kategori_id') else None,
            oncelik=request.form.get('oncelik', 'normal'),
            departman=request.form.get('departman', '').strip() or None,
            para_birimi=request.form.get('para_birimi', 'TRY'),
            durum='taslak'
        )
        
        if request.form.get('istenen_tarih'):
            talep.istenen_tarih = datetime.strptime(request.form['istenen_tarih'], '%Y-%m-%d').date()
        
        if request.form.get('tahmini_tutar'):
            talep.tahmini_tutar = Decimal(request.form['tahmini_tutar'].replace(',', '.'))
        
        if request.form.get('proje_id'):
            talep.proje_id = int(request.form['proje_id'])
        
        talep.talep_no_olustur()
        
        db.session.add(talep)
        db.session.flush()
        
        # Kalemleri ekle
        urun_adlari = request.form.getlist('urun_adi[]')
        miktarlar = request.form.getlist('miktar[]')
        birimler = request.form.getlist('birim[]')
        birim_fiyatlar = request.form.getlist('birim_fiyat[]')
        
        for i, urun_adi in enumerate(urun_adlari):
            if urun_adi.strip():
                kalem = TalepKalemi(
                    talep_id=talep.id,
                    urun_adi=urun_adi.strip(),
                    miktar=Decimal(miktarlar[i].replace(',', '.')) if miktarlar[i] else 1,
                    birim=birimler[i] if i < len(birimler) else 'Adet'
                )
                if i < len(birim_fiyatlar) and birim_fiyatlar[i]:
                    kalem.birim_fiyat = Decimal(birim_fiyatlar[i].replace(',', '.'))
                    kalem.tutar = kalem.miktar * kalem.birim_fiyat
                db.session.add(kalem)
        
        db.session.commit()
        
        flash('Talep oluşturuldu.', 'success')
        return redirect(url_for('satinalma.talep_detay', id=talep.id))
    
    kategoriler = SatinAlmaKategorisi.query.filter_by(aktif=True).order_by(SatinAlmaKategorisi.sira).all()
    projeler = Proje.query.filter_by(is_deleted=False, durum='aktif').order_by(Proje.ad).all()
    
    return render_template('satinalma/talep_form.html',
                          talep=None,
                          kategoriler=kategoriler,
                          projeler=projeler)


@satinalma_bp.route('/talep/<int:id>')
@login_required
@permission_required('satinalma.view')
def talep_detay(id):
    """Talep detayı"""
    talep = SatinAlmaTalebi.query.get_or_404(id)
    
    # Yetki kontrolü
    if not current_user.has_permission('satinalma.admin') and talep.talep_eden_id != current_user.id:
        flash('Bu talebi görüntüleme yetkiniz yok.', 'danger')
        return redirect(url_for('satinalma.talep_liste'))
    
    kalemler = talep.kalemler.all()
    teklifler = talep.teklifler.filter_by(is_deleted=False).all()
    
    return render_template('satinalma/talep_detay.html',
                          talep=talep,
                          kalemler=kalemler,
                          teklifler=teklifler)


@satinalma_bp.route('/talep/<int:id>/onaya-gonder', methods=['POST'])
@login_required
def talep_onaya_gonder(id):
    """Talebi onaya gönder"""
    talep = SatinAlmaTalebi.query.get_or_404(id)
    
    if talep.talep_eden_id != current_user.id:
        flash('Bu talebi onaya gönderme yetkiniz yok.', 'danger')
        return redirect(url_for('satinalma.talep_liste'))
    
    if talep.durum not in ['taslak', 'reddedildi']:
        flash('Bu talep onaya gönderilemez.', 'warning')
        return redirect(url_for('satinalma.talep_detay', id=id))
    
    # Kalem kontrolü
    if talep.kalemler.count() == 0:
        flash('En az bir kalem eklemelisiniz.', 'warning')
        return redirect(url_for('satinalma.talep_detay', id=id))
    
    # Onay talebi oluştur
    onay_talep, hata = OnayServisi.talep_olustur(
        onay_tipi_kod='SATIN_ALMA',
        referans_tablo='satinalma_talepleri',
        referans_id=talep.id,
        talep_eden_id=current_user.id
    )
    
    if hata:
        flash(f'Onay talebi oluşturulamadı: {hata}', 'danger')
        return redirect(url_for('satinalma.talep_detay', id=id))
    
    talep.durum = 'onay_bekliyor'
    talep.onay_talebi_id = onay_talep.id
    db.session.commit()
    
    flash('Talep onaya gönderildi.', 'success')
    return redirect(url_for('satinalma.talep_detay', id=id))


@satinalma_bp.route('/talep/<int:id>/iptal', methods=['POST'])
@login_required
def talep_iptal(id):
    """Talebi iptal et"""
    talep = SatinAlmaTalebi.query.get_or_404(id)
    
    if talep.talep_eden_id != current_user.id and not current_user.has_permission('satinalma.admin'):
        flash('Bu talebi iptal etme yetkiniz yok.', 'danger')
        return redirect(url_for('satinalma.talep_liste'))
    
    if talep.durum in ['siparis_verildi', 'tamamlandi']:
        flash('Sipariş verilmiş talepler iptal edilemez.', 'warning')
        return redirect(url_for('satinalma.talep_detay', id=id))
    
    talep.durum = 'iptal'
    db.session.commit()
    
    flash('Talep iptal edildi.', 'success')
    return redirect(url_for('satinalma.talep_liste'))


# ============================================================
# TEKLİF YÖNETİMİ
# ============================================================

@satinalma_bp.route('/talep/<int:talep_id>/teklif/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('satinalma.admin')
def teklif_ekle(talep_id):
    """Talebe teklif ekle"""
    talep = SatinAlmaTalebi.query.get_or_404(talep_id)
    
    if talep.durum not in ['onaylandi', 'teklif_asamasinda']:
        flash('Bu talebe teklif eklenemez.', 'warning')
        return redirect(url_for('satinalma.talep_detay', id=talep_id))
    
    if request.method == 'POST':
        teklif = SatinAlmaTeklif(
            talep_id=talep.id,
            tedarikci_id=int(request.form['tedarikci_id']),
            teklif_no=request.form.get('teklif_no', '').strip() or None,
            toplam_tutar=Decimal(request.form['toplam_tutar'].replace(',', '.')),
            para_birimi=request.form.get('para_birimi', 'TRY'),
            kdv_dahil=request.form.get('kdv_dahil') == 'on',
            teslimat_suresi=request.form.get('teslimat_suresi', '').strip() or None,
            odeme_kosulu=request.form.get('odeme_kosulu', '').strip() or None,
            notlar=request.form.get('notlar', '').strip() or None,
            durum='beklemede'
        )
        
        if request.form.get('teklif_tarihi'):
            teklif.teklif_tarihi = datetime.strptime(request.form['teklif_tarihi'], '%Y-%m-%d').date()
        if request.form.get('gecerlilik_tarihi'):
            teklif.gecerlilik_tarihi = datetime.strptime(request.form['gecerlilik_tarihi'], '%Y-%m-%d').date()
        
        db.session.add(teklif)
        
        # Talep durumunu güncelle
        if talep.durum == 'onaylandi':
            talep.durum = 'teklif_asamasinda'
        
        db.session.commit()
        
        flash('Teklif eklendi.', 'success')
        return redirect(url_for('satinalma.talep_detay', id=talep_id))
    
    tedarikciler = Tedarikci.query.filter_by(is_deleted=False).order_by(Tedarikci.unvan).all()
    
    return render_template('satinalma/teklif_form.html',
                          talep=talep,
                          teklif=None,
                          tedarikciler=tedarikciler)


@satinalma_bp.route('/teklif/<int:id>/sec', methods=['POST'])
@login_required
@permission_required('satinalma.admin')
def teklif_sec(id):
    """Teklifi seç ve siparişe dönüştür"""
    teklif = SatinAlmaTeklif.query.get_or_404(id)
    talep = teklif.talep
    
    # Diğer teklifleri reddet
    for t in talep.teklifler:
        if t.id != teklif.id:
            t.durum = 'reddedildi'
    
    teklif.durum = 'secildi'
    
    # Sipariş oluştur
    siparis = SatinAlmaSiparisi(
        talep_id=talep.id,
        teklif_id=teklif.id,
        tedarikci_id=teklif.tedarikci_id,
        toplam_tutar=teklif.toplam_tutar,
        para_birimi=teklif.para_birimi,
        durum='siparis_verildi'
    )
    siparis.siparis_no_olustur()
    
    if teklif.teslimat_suresi:
        # Basit bir hesaplama - örn: "5 iş günü" -> 7 gün sonra
        siparis.beklenen_teslimat = date.today()
    
    db.session.add(siparis)
    
    # Talep durumunu güncelle
    talep.durum = 'siparis_verildi'
    
    db.session.commit()
    
    flash(f'Sipariş oluşturuldu: {siparis.siparis_no}', 'success')
    return redirect(url_for('satinalma.siparis_detay', id=siparis.id))


# ============================================================
# SİPARİŞ YÖNETİMİ
# ============================================================

@satinalma_bp.route('/siparisler')
@login_required
@permission_required('satinalma.view')
def siparis_liste():
    """Sipariş listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    
    query = SatinAlmaSiparisi.query.filter_by(is_deleted=False)
    
    if durum:
        query = query.filter(SatinAlmaSiparisi.durum == durum)
    
    query = query.order_by(SatinAlmaSiparisi.created_at.desc())
    pagination = paginate_query(query, page, 20)
    
    return render_template('satinalma/siparis_liste.html',
                          siparisler=pagination.items,
                          pagination=pagination)


@satinalma_bp.route('/siparis/<int:id>')
@login_required
@permission_required('satinalma.view')
def siparis_detay(id):
    """Sipariş detayı"""
    siparis = SatinAlmaSiparisi.query.get_or_404(id)
    teslimatlar = siparis.teslimatlar.order_by(SiparisTeslimat.teslimat_tarihi.desc()).all()
    
    return render_template('satinalma/siparis_detay.html',
                          siparis=siparis,
                          teslimatlar=teslimatlar)


@satinalma_bp.route('/siparis/<int:id>/teslimat', methods=['POST'])
@login_required
@permission_required('satinalma.admin')
def teslimat_kaydet(id):
    """Teslimat kaydı ekle"""
    siparis = SatinAlmaSiparisi.query.get_or_404(id)
    
    teslimat = SiparisTeslimat(
        siparis_id=siparis.id,
        teslimat_tarihi=datetime.strptime(request.form['teslimat_tarihi'], '%Y-%m-%d').date(),
        teslim_alan_id=current_user.id,
        irsaliye_no=request.form.get('irsaliye_no', '').strip() or None,
        notlar=request.form.get('notlar', '').strip() or None
    )
    
    db.session.add(teslimat)
    
    # Durum güncelle
    tam_teslimat = request.form.get('tam_teslimat') == 'on'
    if tam_teslimat:
        siparis.durum = 'teslim_alindi'
        siparis.talep.durum = 'tamamlandi'
    else:
        siparis.durum = 'kismen_teslim'
    
    db.session.commit()
    
    flash('Teslimat kaydedildi.', 'success')
    return redirect(url_for('satinalma.siparis_detay', id=id))


# ============================================================
# KATEGORİ YÖNETİMİ
# ============================================================

@satinalma_bp.route('/kategoriler')
@login_required
@permission_required('satinalma.admin')
def kategori_liste():
    """Kategori listesi"""
    kategoriler = SatinAlmaKategorisi.query.order_by(SatinAlmaKategorisi.sira, SatinAlmaKategorisi.ad).all()
    return render_template('satinalma/kategori_liste.html', kategoriler=kategoriler)


@satinalma_bp.route('/kategori/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('satinalma.admin')
def kategori_ekle():
    """Yeni kategori ekle"""
    if request.method == 'POST':
        kategori = SatinAlmaKategorisi(
            ad=request.form.get('ad', '').strip(),
            kod=request.form.get('kod', '').strip().upper() or None,
            aciklama=request.form.get('aciklama', '').strip() or None,
            ikon=request.form.get('ikon', 'bi-box'),
            sira=int(request.form.get('sira', 0))
        )
        
        if request.form.get('onay_limiti'):
            kategori.onay_limiti = Decimal(request.form['onay_limiti'].replace(',', '.'))
        
        db.session.add(kategori)
        db.session.commit()
        
        flash('Kategori eklendi.', 'success')
        return redirect(url_for('satinalma.kategori_liste'))
    
    return render_template('satinalma/kategori_form.html', kategori=None)


# ============================================================
# API
# ============================================================

@satinalma_bp.route('/api/talep/<int:id>/kalemler')
@login_required
def api_talep_kalemler(id):
    """Talep kalemleri (teklif formu için)"""
    talep = SatinAlmaTalebi.query.get_or_404(id)
    kalemler = [{
        'id': k.id,
        'urun_adi': k.urun_adi,
        'miktar': float(k.miktar),
        'birim': k.birim
    } for k in talep.kalemler]
    return jsonify(kalemler)
