# -*- coding: utf-8 -*-
"""
TG Portal - İK (Human Resources) Routes
Güncellenmiş versiyon: Evrak yönetimi, İşten çıkış, Aday→Çalışan dönüşümü
"""

from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, jsonify
from flask_login import login_required, current_user
from app.models.ik import ZimmetTipi, Zimmet, ZimmetLog
from werkzeug.utils import secure_filename
import os

from app import db
from app.models.ik import (
    Departman, Pozisyon, Calisan, Izin, Aday,
    EvrakTipi, AdayEvrak, CalisanEvrak, IstenCikis
)
from app.models.base import CalisanDurumu
from app.utils import permission_required, paginate_query

ik_bp = Blueprint('ik', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# DASHBOARD
# ============================================================

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
    eksik_evrak_aday = 0
    
    # Eksik evraklı aday sayısı
    for aday in Aday.query.filter(Aday.is_deleted==False, Aday.durum.notin_(['red', 'iptal', 'ise_alindi'])).all():
        zorunlu = EvrakTipi.query.filter_by(zorunlu=True, aktif=True).count()
        yuklenen = aday.evraklar.join(EvrakTipi).filter(
            EvrakTipi.zorunlu == True,
            AdayEvrak.durum == 'onaylandi'
        ).count()
        if yuklenen < zorunlu:
            eksik_evrak_aday += 1
    
    # Departman bazlı dağılım
    departman_stats = db.session.query(
    Departman.ad,
    db.func.count(Calisan.id)
    ).join(Calisan, Calisan.departman_id == Departman.id).filter(
        Calisan.is_deleted == False,
        Calisan.durum == CalisanDurumu.AKTIF
    ).group_by(Departman.ad).all()
    
    # Son başvurular
    son_adaylar = Aday.query.filter_by(is_deleted=False)\
        .order_by(Aday.created_at.desc()).limit(5).all()
    
    # İşten çıkış bekleyenler
    cikis_bekleyen = IstenCikis.query.filter(
        IstenCikis.durum.in_(['basladi', 'devam_ediyor'])
    ).count()
    
    return render_template('ik/dashboard.html',
                          aktif_calisan=aktif_calisan,
                          bekleyen_aday=bekleyen_aday,
                          bekleyen_izin=bekleyen_izin,
                          eksik_evrak_aday=eksik_evrak_aday,
                          departman_stats=departman_stats,
                          son_adaylar=son_adaylar,
                          cikis_bekleyen=cikis_bekleyen)


# ============================================================
# ÇALIŞAN YÖNETİMİ
# ============================================================

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


@ik_bp.route('/<int:id>')
@login_required
@permission_required('ik.view')
def detay(id):
    """Çalışan detay sayfası"""
    calisan = Calisan.query.get_or_404(id)
    izinler = calisan.izinler.order_by(Izin.baslangic.desc()).limit(10).all()
    evraklar = calisan.evraklar.all() if hasattr(calisan, 'evraklar') else []
    
    return render_template('ik/detay.html',
                          calisan=calisan,
                          izinler=izinler,
                          evraklar=evraklar)


@ik_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('ik.create')
def ekle():
    """Yeni çalışan ekle"""
    if request.method == 'POST':
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


# ============================================================
# ADAY YÖNETİMİ
# ============================================================

@ik_bp.route('/adaylar')
@login_required
@permission_required('ik.view')
def aday_liste():
    """Aday listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    kaynak = request.args.get('kaynak')
    search = request.args.get('search', '').strip()
    
    query = Aday.query.filter_by(is_deleted=False)
    
    if durum:
        query = query.filter(Aday.durum == durum)
    if kaynak:
        query = query.filter(Aday.kaynak == kaynak)
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Aday.ad.ilike(search_filter),
                Aday.soyad.ilike(search_filter),
                Aday.telefon.ilike(search_filter),
                Aday.email.ilike(search_filter)
            )
        )
    
    query = query.order_by(Aday.created_at.desc())
    pagination = paginate_query(query, page, 20)
    
    # İstatistikler
    stats = {
        'toplam': Aday.query.filter_by(is_deleted=False).count(),
        'basvurdu': Aday.query.filter_by(is_deleted=False, durum='basvurdu').count(),
        'degerlendiriliyor': Aday.query.filter_by(is_deleted=False, durum='degerlendiriliyor').count(),
        'mulakat': Aday.query.filter_by(is_deleted=False, durum='mulakat').count(),
        'teklif': Aday.query.filter_by(is_deleted=False, durum='teklif').count(),
        'ise_alindi': Aday.query.filter_by(is_deleted=False, durum='ise_alindi').count(),
    }
    
    return render_template('ik/aday_liste.html',
                          adaylar=pagination.items,
                          pagination=pagination,
                          stats=stats)


@ik_bp.route('/aday/<int:id>')
@login_required
@permission_required('ik.view')
def aday_detay(id):
    """Aday detay sayfası"""
    aday = Aday.query.get_or_404(id)
    evrak_tipleri = EvrakTipi.query.filter_by(aktif=True).order_by(EvrakTipi.sira).all()
    
    # Evrak tamamlanma oranı hesapla
    zorunlu_evraklar = EvrakTipi.query.filter_by(zorunlu=True, aktif=True).count()
    if zorunlu_evraklar == 0:
        evrak_tamamlanma = 100
    else:
        yuklenen = aday.evraklar.join(EvrakTipi).filter(
            EvrakTipi.zorunlu == True,
            AdayEvrak.durum == 'onaylandi'
        ).count()
        evrak_tamamlanma = int((yuklenen / zorunlu_evraklar) * 100)
    
    # Eksik evraklar
    yuklenen_tipler = [e.evrak_tipi_id for e in aday.evraklar.filter(
        AdayEvrak.durum.in_(['yuklendi', 'onaylandi'])
    ).all()]
    eksik_evraklar = [t for t in EvrakTipi.query.filter_by(zorunlu=True, aktif=True).all() if t.id not in yuklenen_tipler]
    
    ise_alim_hazir = len(eksik_evraklar) == 0 and aday.kvkk_onay
    
    return render_template('ik/aday_detay.html',
                          aday=aday,
                          evrak_tipleri=evrak_tipleri,
                          evrak_tamamlanma=evrak_tamamlanma,
                          eksik_evraklar=eksik_evraklar,
                          ise_alim_hazir=ise_alim_hazir)


@ik_bp.route('/aday/<int:id>/durum', methods=['POST'])
@login_required
@permission_required('ik.edit')
def aday_durum_degistir(id):
    """Aday durumunu değiştir"""
    aday = Aday.query.get_or_404(id)
    aday.durum = request.form.get('durum')
    if request.form.get('degerlendirme_notu'):
        aday.degerlendirme_notu = request.form.get('degerlendirme_notu')
    db.session.commit()
    
    flash('Aday durumu güncellendi.', 'success')
    return redirect(url_for('ik.aday_detay', id=id))


@ik_bp.route('/aday/<int:id>/sil', methods=['POST'])
@login_required
@permission_required('ik.delete')
def aday_sil(id):
    """Aday sil (soft delete)"""
    aday = Aday.query.get_or_404(id)
    aday.soft_delete(current_user.id)
    db.session.commit()
    
    flash('Aday silindi.', 'success')
    return redirect(url_for('ik.aday_liste'))


# ============================================================
# EVRAK YÖNETİMİ
# ============================================================

@ik_bp.route('/aday/<int:id>/evrak', methods=['POST'])
@login_required
@permission_required('ik.edit')
def aday_evrak_yukle(id):
    """Aday evrak yükle"""
    aday = Aday.query.get_or_404(id)
    
    if 'dosya' not in request.files:
        flash('Dosya seçilmedi.', 'danger')
        return redirect(url_for('ik.aday_detay', id=id))
    
    dosya = request.files['dosya']
    if dosya.filename == '':
        flash('Dosya seçilmedi.', 'danger')
        return redirect(url_for('ik.aday_detay', id=id))
    
    if dosya and allowed_file(dosya.filename):
        evrak_tipi_id = int(request.form['evrak_tipi_id'])
        
        # Dosya adı oluştur
        filename = secure_filename(dosya.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"aday_{id}_{evrak_tipi_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        
        # Klasör oluştur
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'evraklar', 'adaylar', str(id))
        os.makedirs(upload_folder, exist_ok=True)
        
        # Dosyayı kaydet
        filepath = os.path.join(upload_folder, new_filename)
        dosya.save(filepath)
        
        # Veritabanına ekle
        evrak = AdayEvrak(
            aday_id=id,
            evrak_tipi_id=evrak_tipi_id,
            dosya_adi=filename,
            dosya_yolu=filepath,
            dosya_boyut=os.path.getsize(filepath),
            mime_type=dosya.content_type,
            yukleyen_id=current_user.id
        )
        db.session.add(evrak)
        db.session.commit()
        
        flash('Evrak başarıyla yüklendi.', 'success')
    else:
        flash('Geçersiz dosya formatı. (PDF, JPG, PNG, DOC, DOCX)', 'danger')
    
    return redirect(url_for('ik.aday_detay', id=id))


@ik_bp.route('/evrak/<int:id>/onayla', methods=['POST'])
@login_required
@permission_required('ik.edit')
def evrak_onayla(id):
    """Evrak onayla"""
    evrak = AdayEvrak.query.get_or_404(id)
    evrak.durum = 'onaylandi'
    evrak.onaylayan_id = current_user.id
    evrak.onay_tarihi = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Evrak onaylandı'})


@ik_bp.route('/evrak/<int:id>/reddet', methods=['POST'])
@login_required
@permission_required('ik.edit')
def evrak_reddet(id):
    """Evrak reddet"""
    evrak = AdayEvrak.query.get_or_404(id)
    data = request.get_json()
    evrak.durum = 'reddedildi'
    evrak.red_sebebi = data.get('sebep', '')
    evrak.onaylayan_id = current_user.id
    evrak.onay_tarihi = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Evrak reddedildi'})


@ik_bp.route('/evrak/<int:id>/indir')
@login_required
@permission_required('ik.view')
def evrak_indir(id):
    """Evrak indir"""
    evrak = AdayEvrak.query.get_or_404(id)
    return send_file(evrak.dosya_yolu, as_attachment=True, download_name=evrak.dosya_adi)


@ik_bp.route('/evrak-tipleri')
@login_required
@permission_required('ik.view')
def evrak_tipleri():
    """Evrak tipleri listesi"""
    tipleri = EvrakTipi.query.order_by(EvrakTipi.sira).all()
    return render_template('ik/evrak_tipleri.html', evrak_tipleri=tipleri)


@ik_bp.route('/evrak-tipi/ekle', methods=['POST'])
@login_required
@permission_required('ik.edit')
def evrak_tipi_ekle():
    """Yeni evrak tipi ekle"""
    evrak_tipi = EvrakTipi(
        ad=request.form.get('ad'),
        kod=request.form.get('kod'),
        kategori=request.form.get('kategori'),
        zorunlu=request.form.get('zorunlu') == 'on',
        aciklama=request.form.get('aciklama'),
        sira=int(request.form.get('sira', 0))
    )
    db.session.add(evrak_tipi)
    db.session.commit()
    
    flash('Evrak tipi eklendi.', 'success')
    return redirect(url_for('ik.evrak_tipleri'))


@ik_bp.route('/eksik-evraklar')
@login_required
@permission_required('ik.view')
def eksik_evraklar():
    """Eksik evrakları olan adaylar"""
    adaylar_data = []
    
    for aday in Aday.query.filter(Aday.is_deleted==False, Aday.durum.notin_(['red', 'iptal', 'ise_alindi'])).all():
        zorunlu_tipler = EvrakTipi.query.filter_by(zorunlu=True, aktif=True).all()
        yuklenen_tipler = [e.evrak_tipi_id for e in aday.evraklar.filter(
            AdayEvrak.durum.in_(['yuklendi', 'onaylandi'])
        ).all()]
        eksik = [t for t in zorunlu_tipler if t.id not in yuklenen_tipler]
        
        if eksik:
            zorunlu_count = len(zorunlu_tipler)
            yuklenen_count = zorunlu_count - len(eksik)
            oran = int((yuklenen_count / zorunlu_count) * 100) if zorunlu_count > 0 else 0
            
            adaylar_data.append({
                'aday': aday,
                'eksik': eksik,
                'oran': oran
            })
    
    return render_template('ik/eksik_evraklar.html', adaylar=adaylar_data)


# ============================================================
# ADAY → ÇALIŞAN DÖNÜŞÜMÜ
# ============================================================

@ik_bp.route('/aday/<int:id>/calisana-donustur', methods=['GET', 'POST'])
@login_required
@permission_required('ik.create')
def aday_calisana_donustur(id):
    """Adayı çalışana dönüştür"""
    aday = Aday.query.get_or_404(id)
    
    # Evrak kontrolü
    zorunlu_tipler = EvrakTipi.query.filter_by(zorunlu=True, aktif=True).all()
    yuklenen_tipler = [e.evrak_tipi_id for e in aday.evraklar.filter(
        AdayEvrak.durum == 'onaylandi'
    ).all()]
    eksik = [t for t in zorunlu_tipler if t.id not in yuklenen_tipler]
    
    if eksik:
        flash('Tüm zorunlu evraklar onaylanmadan işe alım yapılamaz.', 'danger')
        return redirect(url_for('ik.aday_detay', id=id))
    
    if not aday.kvkk_onay:
        flash('KVKK onayı alınmadan işe alım yapılamaz.', 'danger')
        return redirect(url_for('ik.aday_detay', id=id))
    
    if request.method == 'POST':
        # Yeni çalışan oluştur
        calisan = Calisan(
            ad=aday.ad,
            soyad=aday.soyad,
            tc_kimlik=aday.tc_kimlik,
            dogum_tarihi=aday.dogum_tarihi,
            cinsiyet=aday.cinsiyet,
            telefon=aday.telefon,
            email=aday.email,
            adres=aday.adres,
            il=aday.il,
            ilce=aday.ilce,
            pozisyon_id=aday.pozisyon_id,
            sicil_no=request.form.get('sicil_no'),
            ise_baslama=datetime.strptime(request.form['ise_baslama'], '%Y-%m-%d').date(),
            calisma_tipi=request.form.get('calisma_tipi', 'tam_zamanli'),
            durum=CalisanDurumu.AKTIF,
            created_by=current_user.id
        )
        db.session.add(calisan)
        db.session.flush()  # ID almak için
        
        # Aday durumunu güncelle
        aday.durum = 'ise_alindi'
        
        # Onaylı evrakları kopyala
        for aday_evrak in aday.evraklar.filter_by(durum='onaylandi').all():
            calisan_evrak = CalisanEvrak(
                calisan_id=calisan.id,
                evrak_tipi_id=aday_evrak.evrak_tipi_id,
                dosya_adi=aday_evrak.dosya_adi,
                dosya_yolu=aday_evrak.dosya_yolu,
                dosya_boyut=aday_evrak.dosya_boyut,
                mime_type=aday_evrak.mime_type,
                gecerlilik_bitis=aday_evrak.gecerlilik_bitis
            )
            db.session.add(calisan_evrak)
        
        db.session.commit()
        
        flash(f'{calisan.full_name} başarıyla çalışan olarak kaydedildi.', 'success')
        return redirect(url_for('ik.detay', id=calisan.id))
    
    departmanlar = Departman.query.filter_by(aktif=True).order_by(Departman.ad).all()
    pozisyonlar = Pozisyon.query.filter_by(aktif=True).order_by(Pozisyon.ad).all()
    
    return render_template('ik/aday_calisana_donustur.html',
                          aday=aday,
                          departmanlar=departmanlar,
                          pozisyonlar=pozisyonlar)


# ============================================================
# İŞTEN ÇIKIŞ YÖNETİMİ
# ============================================================

@ik_bp.route('/isten-cikislar')
@login_required
@permission_required('ik.view')
def isten_cikis_liste():
    """İşten çıkış listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    
    query = IstenCikis.query
    
    if durum:
        query = query.filter(IstenCikis.durum == durum)
    
    query = query.order_by(IstenCikis.created_at.desc())
    pagination = paginate_query(query, page, 20)
    
    return render_template('ik/isten_cikis_liste.html',
                          cikislar=pagination.items,
                          pagination=pagination)


@ik_bp.route('/calisan/<int:id>/cikis-baslat', methods=['GET', 'POST'])
@login_required
@permission_required('ik.edit')
def isten_cikis_baslat(id):
    """İşten çıkış süreci başlat"""
    calisan = Calisan.query.get_or_404(id)
    
    if request.method == 'POST':
        cikis = IstenCikis(
            calisan_id=id,
            planlanan_cikis_tarihi=datetime.strptime(request.form['planlanan_cikis_tarihi'], '%Y-%m-%d').date(),
            cikis_tipi=request.form.get('cikis_tipi'),
            cikis_sebebi=request.form.get('cikis_sebebi'),
            detay_notu=request.form.get('detay_notu'),
            olusturan_id=current_user.id
        )
        
        # Çalışan durumunu güncelle
        calisan.durum = CalisanDurumu.ASKIYA_ALINDI
        
        db.session.add(cikis)
        db.session.commit()
        
        flash('İşten çıkış süreci başlatıldı.', 'success')
        return redirect(url_for('ik.isten_cikis_detay', id=cikis.id))
    
    return render_template('ik/isten_cikis_baslat.html', calisan=calisan)


@ik_bp.route('/isten-cikis/<int:id>')
@login_required
@permission_required('ik.view')
def isten_cikis_detay(id):
    """İşten çıkış detay"""
    cikis = IstenCikis.query.get_or_404(id)
    return render_template('ik/isten_cikis_detay.html', cikis=cikis)


@ik_bp.route('/isten-cikis/<int:id>/guncelle', methods=['POST'])
@login_required
@permission_required('ik.edit')
def isten_cikis_guncelle(id):
    """İşten çıkış checklist güncelle"""
    cikis = IstenCikis.query.get_or_404(id)
    
    cikis.zimmet_teslim = request.form.get('zimmet_teslim') == 'on'
    cikis.zimmet_notu = request.form.get('zimmet_notu')
    cikis.sgk_cikis_bildirimi = request.form.get('sgk_cikis_bildirimi') == 'on'
    cikis.cikis_mulakati_yapildi = request.form.get('cikis_mulakati_yapildi') == 'on'
    cikis.cikis_mulakat_notu = request.form.get('cikis_mulakat_notu')
    
    if request.form.get('kidem_tazminati'):
        cikis.kidem_tazminati = Decimal(request.form.get('kidem_tazminati'))
    if request.form.get('ihbar_tazminati'):
        cikis.ihbar_tazminati = Decimal(request.form.get('ihbar_tazminati'))
    
    # Tüm adımlar tamamlandıysa
    if cikis.zimmet_teslim and cikis.sgk_cikis_bildirimi:
        cikis.durum = 'devam_ediyor'
    
    db.session.commit()
    
    flash('İşten çıkış bilgileri güncellendi.', 'success')
    return redirect(url_for('ik.isten_cikis_detay', id=id))


@ik_bp.route('/isten-cikis/<int:id>/tamamla', methods=['POST'])
@login_required
@permission_required('ik.edit')
def isten_cikis_tamamla(id):
    """İşten çıkışı tamamla"""
    cikis = IstenCikis.query.get_or_404(id)
    
    cikis.durum = 'tamamlandi'
    cikis.gerceklesen_cikis_tarihi = date.today()
    
    # Çalışan durumunu güncelle
    calisan = cikis.calisan
    calisan.durum = CalisanDurumu.AYRILDI
    calisan.isten_ayrilma = cikis.gerceklesen_cikis_tarihi
    calisan.ayrilma_nedeni = f"{cikis.cikis_tipi}: {cikis.cikis_sebebi}"
    
    db.session.commit()
    
    flash('İşten çıkış tamamlandı.', 'success')
    return redirect(url_for('ik.isten_cikis_detay', id=id))


# ============================================================
# İZİN YÖNETİMİ
# ============================================================

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
    
    # Bekleyen sayısı
    bekleyen_count = Izin.query.filter_by(durum='beklemede').count()
    
    return render_template('ik/izin_liste.html',
                          izinler=pagination.items,
                          pagination=pagination,
                          bekleyen_count=bekleyen_count)


@ik_bp.route('/izin/<int:id>/onayla', methods=['POST'])
@login_required
@permission_required('ik.edit')
def izin_onayla(id):
    """İzin talebi onayla"""
    izin = Izin.query.get_or_404(id)
    izin.durum = 'onaylandi'
    izin.onaylayan_id = current_user.id
    izin.onay_tarihi = datetime.utcnow()
    db.session.commit()
    
    flash('İzin talebi onaylandı.', 'success')
    return redirect(url_for('ik.izin_liste'))


@ik_bp.route('/izin/<int:id>/reddet', methods=['POST'])
@login_required
@permission_required('ik.edit')
def izin_reddet(id):
    """İzin talebi reddet"""
    izin = Izin.query.get_or_404(id)
    izin.durum = 'reddedildi'
    izin.red_nedeni = request.form.get('red_nedeni')
    izin.onaylayan_id = current_user.id
    izin.onay_tarihi = datetime.utcnow()
    db.session.commit()
    
    flash('İzin talebi reddedildi.', 'success')
    return redirect(url_for('ik.izin_liste'))

# ============================================================
# ZİMMET YÖNETİMİ
# ============================================================

# NOT: Önce import'lara şunları ekleyin:
# from app.models.ik import ZimmetTipi, Zimmet, ZimmetLog

@ik_bp.route('/zimmetler')
@login_required
@permission_required('ik.view')
def zimmet_liste():
    """Zimmet listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    tip_id = request.args.get('tip_id', type=int)
    search = request.args.get('search', '').strip()
    
    query = Zimmet.query.filter_by(is_deleted=False)
    
    if durum:
        query = query.filter(Zimmet.durum == durum)
    if tip_id:
        query = query.filter(Zimmet.zimmet_tipi_id == tip_id)
    if search:
        search_filter = f'%{search}%'
        query = query.join(Calisan).filter(
            db.or_(
                Zimmet.tanim.ilike(search_filter),
                Zimmet.seri_no.ilike(search_filter),
                Zimmet.demirbas_no.ilike(search_filter),
                Calisan.ad.ilike(search_filter),
                Calisan.soyad.ilike(search_filter)
            )
        )
    
    query = query.order_by(Zimmet.created_at.desc())
    pagination = paginate_query(query, page, 20)
    
    zimmet_tipleri = ZimmetTipi.query.filter_by(aktif=True).order_by(ZimmetTipi.ad).all()
    
    # İstatistikler
    stats = {
        'toplam': Zimmet.query.filter_by(is_deleted=False).count(),
        'teslim_edildi': Zimmet.query.filter_by(is_deleted=False, durum='teslim_edildi').count(),
        'iade_edildi': Zimmet.query.filter_by(is_deleted=False, durum='iade_edildi').count(),
        'kayip': Zimmet.query.filter_by(is_deleted=False, durum='kayip').count(),
    }
    
    return render_template('ik/zimmet_liste.html',
                          zimmetler=pagination.items,
                          pagination=pagination,
                          zimmet_tipleri=zimmet_tipleri,
                          stats=stats)


@ik_bp.route('/zimmet/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('ik.create')
def zimmet_ekle():
    """Yeni zimmet ekle"""
    if request.method == 'POST':
        zimmet = Zimmet(
            calisan_id=int(request.form['calisan_id']),
            zimmet_tipi_id=int(request.form['zimmet_tipi_id']),
            tanim=request.form.get('tanim', '').strip(),
            seri_no=request.form.get('seri_no', '').strip() or None,
            demirbas_no=request.form.get('demirbas_no', '').strip() or None,
            marka=request.form.get('marka', '').strip() or None,
            model=request.form.get('model', '').strip() or None,
            teslim_tarihi=datetime.strptime(request.form['teslim_tarihi'], '%Y-%m-%d').date(),
            teslim_eden_id=current_user.id,
            teslim_notu=request.form.get('teslim_notu', '').strip() or None,
            deger=Decimal(request.form['deger']) if request.form.get('deger') else None,
            durum='teslim_edildi'
        )
        db.session.add(zimmet)
        db.session.flush()
        
        # Log kaydı
        log = ZimmetLog(
            zimmet_id=zimmet.id,
            islem='teslim',
            aciklama=f'Zimmet {zimmet.calisan.full_name} adlı çalışana teslim edildi.',
            islem_yapan_id=current_user.id,
            yeni_calisan_id=zimmet.calisan_id
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Zimmet başarıyla eklendi.', 'success')
        return redirect(url_for('ik.zimmet_detay', id=zimmet.id))
    
    calisanlar = Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AKTIF).order_by(Calisan.ad).all()
    zimmet_tipleri = ZimmetTipi.query.filter_by(aktif=True).order_by(ZimmetTipi.ad).all()
    
    # URL'den gelen calisan_id varsa
    calisan_id = request.args.get('calisan_id', type=int)
    
    return render_template('ik/zimmet_form.html',
                          zimmet=None,
                          calisanlar=calisanlar,
                          zimmet_tipleri=zimmet_tipleri,
                          secili_calisan_id=calisan_id)


@ik_bp.route('/zimmet/<int:id>')
@login_required
@permission_required('ik.view')
def zimmet_detay(id):
    """Zimmet detay"""
    zimmet = Zimmet.query.get_or_404(id)
    loglar = zimmet.loglar.order_by(ZimmetLog.created_at.desc()).all()
    
    return render_template('ik/zimmet_detay.html',
                          zimmet=zimmet,
                          loglar=loglar)


@ik_bp.route('/zimmet/<int:id>/iade', methods=['GET', 'POST'])
@login_required
@permission_required('ik.edit')
def zimmet_iade(id):
    """Zimmet iade al"""
    zimmet = Zimmet.query.get_or_404(id)
    
    if zimmet.durum != 'teslim_edildi':
        flash('Bu zimmet zaten iade edilmiş veya durumu değiştirilmiş.', 'warning')
        return redirect(url_for('ik.zimmet_detay', id=id))
    
    if request.method == 'POST':
        zimmet.iade_tarihi = datetime.strptime(request.form['iade_tarihi'], '%Y-%m-%d').date()
        zimmet.iade_alan_id = current_user.id
        zimmet.iade_notu = request.form.get('iade_notu', '').strip() or None
        zimmet.iade_durumu = request.form.get('iade_durumu', 'saglam')
        zimmet.durum = 'iade_edildi'
        
        # Log kaydı
        log = ZimmetLog(
            zimmet_id=zimmet.id,
            islem='iade',
            aciklama=f'Zimmet {zimmet.calisan.full_name} tarafından iade edildi. Durum: {zimmet.iade_durumu}',
            islem_yapan_id=current_user.id,
            eski_calisan_id=zimmet.calisan_id
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Zimmet başarıyla iade alındı.', 'success')
        return redirect(url_for('ik.zimmet_detay', id=id))
    
    return render_template('ik/zimmet_iade.html', zimmet=zimmet)


@ik_bp.route('/zimmet/<int:id>/transfer', methods=['GET', 'POST'])
@login_required
@permission_required('ik.edit')
def zimmet_transfer(id):
    """Zimmet başka çalışana transfer et"""
    zimmet = Zimmet.query.get_or_404(id)
    
    if zimmet.durum != 'teslim_edildi':
        flash('Sadece teslim edilmiş zimmetler transfer edilebilir.', 'warning')
        return redirect(url_for('ik.zimmet_detay', id=id))
    
    if request.method == 'POST':
        eski_calisan_id = zimmet.calisan_id
        yeni_calisan_id = int(request.form['yeni_calisan_id'])
        
        if eski_calisan_id == yeni_calisan_id:
            flash('Zimmet zaten bu çalışanda.', 'warning')
            return redirect(url_for('ik.zimmet_transfer', id=id))
        
        zimmet.calisan_id = yeni_calisan_id
        zimmet.teslim_tarihi = datetime.strptime(request.form['transfer_tarihi'], '%Y-%m-%d').date()
        
        # Log kaydı
        eski_calisan = Calisan.query.get(eski_calisan_id)
        yeni_calisan = Calisan.query.get(yeni_calisan_id)
        
        log = ZimmetLog(
            zimmet_id=zimmet.id,
            islem='transfer',
            aciklama=f'Zimmet {eski_calisan.full_name} → {yeni_calisan.full_name} transfer edildi.',
            islem_yapan_id=current_user.id,
            eski_calisan_id=eski_calisan_id,
            yeni_calisan_id=yeni_calisan_id
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Zimmet {yeni_calisan.full_name} adlı çalışana transfer edildi.', 'success')
        return redirect(url_for('ik.zimmet_detay', id=id))
    
    calisanlar = Calisan.query.filter(
        Calisan.is_deleted == False,
        Calisan.durum == CalisanDurumu.AKTIF,
        Calisan.id != zimmet.calisan_id
    ).order_by(Calisan.ad).all()
    
    return render_template('ik/zimmet_transfer.html',
                          zimmet=zimmet,
                          calisanlar=calisanlar)


@ik_bp.route('/zimmet/<int:id>/kayip', methods=['POST'])
@login_required
@permission_required('ik.edit')
def zimmet_kayip_bildir(id):
    """Zimmet kayıp bildirimi"""
    zimmet = Zimmet.query.get_or_404(id)
    zimmet.durum = 'kayip'
    
    log = ZimmetLog(
        zimmet_id=zimmet.id,
        islem='kayip_bildirimi',
        aciklama=request.form.get('aciklama', 'Zimmet kayıp olarak bildirildi.'),
        islem_yapan_id=current_user.id
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Zimmet kayıp olarak işaretlendi.', 'warning')
    return redirect(url_for('ik.zimmet_detay', id=id))


# ============================================================
# ZİMMET TİPLERİ YÖNETİMİ
# ============================================================

@ik_bp.route('/zimmet-tipleri')
@login_required
@permission_required('ik.view')
def zimmet_tipleri():
    """Zimmet tipleri listesi"""
    tipler = ZimmetTipi.query.order_by(ZimmetTipi.ad).all()
    return render_template('ik/zimmet_tipleri.html', zimmet_tipleri=tipler)


@ik_bp.route('/zimmet-tipi/ekle', methods=['POST'])
@login_required
@permission_required('ik.edit')
def zimmet_tipi_ekle():
    """Yeni zimmet tipi ekle"""
    tip = ZimmetTipi(
        ad=request.form.get('ad'),
        kod=request.form.get('kod'),
        kategori=request.form.get('kategori'),
        aciklama=request.form.get('aciklama'),
        seri_no_zorunlu=request.form.get('seri_no_zorunlu') == 'on',
        iade_zorunlu=request.form.get('iade_zorunlu') == 'on'
    )
    db.session.add(tip)
    db.session.commit()
    
    flash('Zimmet tipi eklendi.', 'success')
    return redirect(url_for('ik.zimmet_tipleri'))


# ============================================================
# ÇALIŞAN ZİMMETLERİ
# ============================================================

@ik_bp.route('/calisan/<int:id>/zimmetler')
@login_required
@permission_required('ik.view')
def calisan_zimmetler(id):
    """Çalışanın zimmetleri"""
    calisan = Calisan.query.get_or_404(id)
    
    aktif_zimmetler = calisan.zimmetler.filter(
        Zimmet.durum == 'teslim_edildi',
        Zimmet.is_deleted == False
    ).all()
    
    gecmis_zimmetler = calisan.zimmetler.filter(
        Zimmet.durum != 'teslim_edildi',
        Zimmet.is_deleted == False
    ).order_by(Zimmet.iade_tarihi.desc()).all()
    
    return render_template('ik/calisan_zimmetler.html',
                          calisan=calisan,
                          aktif_zimmetler=aktif_zimmetler,
                          gecmis_zimmetler=gecmis_zimmetler)

