# -*- coding: utf-8 -*-
"""
TG Portal - Proje Routes
Müşteri, Proje, Hedef Kadro yönetimi
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models.proje import Musteri, Proje, HedefKadro
from app.models.ik import Aday, Calisan
from app.utils import permission_required

proje_bp = Blueprint('proje', __name__)


# ==================== MÜŞTERİ ====================

@proje_bp.route('/musteriler')
@login_required
@permission_required('proje.view')
def musteri_liste():
    """Müşteri listesi"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    aktif = request.args.get('aktif', '')
    
    query = Musteri.query.filter_by(is_deleted=False)
    
    if search:
        query = query.filter(
            db.or_(
                Musteri.ad.ilike(f'%{search}%'),
                Musteri.kisa_ad.ilike(f'%{search}%')
            )
        )
    
    if aktif:
        query = query.filter_by(aktif=(aktif == '1'))
    
    query = query.order_by(Musteri.ad)
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('proje/musteri_liste.html',
                         musteriler=pagination.items,
                         pagination=pagination)


@proje_bp.route('/musteri/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('proje.create')
def musteri_ekle():
    """Yeni müşteri ekle"""
    if request.method == 'POST':
        musteri = Musteri(
            ad=request.form.get('ad'),
            kisa_ad=request.form.get('kisa_ad'),
            vergi_no=request.form.get('vergi_no'),
            vergi_dairesi=request.form.get('vergi_dairesi'),
            adres=request.form.get('adres'),
            il=request.form.get('il'),
            ilce=request.form.get('ilce'),
            telefon=request.form.get('telefon'),
            email=request.form.get('email'),
            web=request.form.get('web'),
            yetkili_ad=request.form.get('yetkili_ad'),
            yetkili_telefon=request.form.get('yetkili_telefon'),
            yetkili_email=request.form.get('yetkili_email'),
            notlar=request.form.get('notlar'),
            aktif=request.form.get('aktif') == 'on'
        )
        db.session.add(musteri)
        db.session.commit()
        flash('Müşteri başarıyla eklendi.', 'success')
        return redirect(url_for('proje.musteri_liste'))
    
    return render_template('proje/musteri_form.html', musteri=None)


@proje_bp.route('/musteri/<int:id>')
@login_required
@permission_required('proje.view')
def musteri_detay(id):
    """Müşteri detayı"""
    musteri = Musteri.query.get_or_404(id)
    projeler = musteri.projeler.filter_by(is_deleted=False).order_by(Proje.created_at.desc()).all()
    
    return render_template('proje/musteri_detay.html',
                         musteri=musteri,
                         projeler=projeler)


@proje_bp.route('/musteri/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('proje.edit')
def musteri_duzenle(id):
    """Müşteri düzenle"""
    musteri = Musteri.query.get_or_404(id)
    
    if request.method == 'POST':
        musteri.ad = request.form.get('ad')
        musteri.kisa_ad = request.form.get('kisa_ad')
        musteri.vergi_no = request.form.get('vergi_no')
        musteri.vergi_dairesi = request.form.get('vergi_dairesi')
        musteri.adres = request.form.get('adres')
        musteri.il = request.form.get('il')
        musteri.ilce = request.form.get('ilce')
        musteri.telefon = request.form.get('telefon')
        musteri.email = request.form.get('email')
        musteri.web = request.form.get('web')
        musteri.yetkili_ad = request.form.get('yetkili_ad')
        musteri.yetkili_telefon = request.form.get('yetkili_telefon')
        musteri.yetkili_email = request.form.get('yetkili_email')
        musteri.notlar = request.form.get('notlar')
        musteri.aktif = request.form.get('aktif') == 'on'
        
        db.session.commit()
        flash('Müşteri başarıyla güncellendi.', 'success')
        return redirect(url_for('proje.musteri_detay', id=id))
    
    return render_template('proje/musteri_form.html', musteri=musteri)


# ==================== PROJE ====================

@proje_bp.route('/')
@proje_bp.route('/projeler')
@login_required
@permission_required('proje.view')
def proje_liste():
    """Proje listesi"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    musteri_id = request.args.get('musteri_id', type=int)
    aktif = request.args.get('aktif', '')
    
    query = Proje.query.filter_by(is_deleted=False)
    
    if search:
        query = query.filter(Proje.ad.ilike(f'%{search}%'))
    
    if musteri_id:
        query = query.filter_by(musteri_id=musteri_id)
    
    if aktif:
        query = query.filter_by(aktif=(aktif == '1'))
    
    query = query.order_by(Proje.created_at.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    musteriler = Musteri.query.filter_by(is_deleted=False, aktif=True).order_by(Musteri.ad).all()
    
    return render_template('proje/proje_liste.html',
                         projeler=pagination.items,
                         pagination=pagination,
                         musteriler=musteriler)


@proje_bp.route('/proje/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('proje.create')
def proje_ekle():
    """Yeni proje ekle"""
    if request.method == 'POST':
        proje = Proje(
            musteri_id=request.form.get('musteri_id', type=int),
            ad=request.form.get('ad'),
            kod=request.form.get('kod'),
            aciklama=request.form.get('aciklama'),
            baslangic_tarihi=request.form.get('baslangic_tarihi') or None,
            bitis_tarihi=request.form.get('bitis_tarihi') or None,
            butce=request.form.get('butce') or None,
            notlar=request.form.get('notlar'),
            aktif=request.form.get('aktif') == 'on'
        )
        db.session.add(proje)
        db.session.commit()
        flash('Proje başarıyla eklendi.', 'success')
        return redirect(url_for('proje.proje_detay', id=proje.id))
    
    musteriler = Musteri.query.filter_by(is_deleted=False, aktif=True).order_by(Musteri.ad).all()
    return render_template('proje/proje_form.html', proje=None, musteriler=musteriler)


@proje_bp.route('/proje/<int:id>')
@login_required
@permission_required('proje.view')
def proje_detay(id):
    """Proje detayı"""
    from app.models.filo import Arac
    
    proje = Proje.query.get_or_404(id)
    kadrolar = proje.kadrolar.filter_by(is_deleted=False).order_by(HedefKadro.oncelik, HedefKadro.pozisyon_adi).all()
    
    # Projeye atanmış araçlar
    araclar = Arac.query.filter_by(proje_id=id, is_deleted=False).order_by(Arac.plaka).all()
    
    # İstatistikler
    stats = {
        'toplam_kadro': proje.toplam_kadro,
        'mevcut_calisan': proje.mevcut_calisan,
        'eksik_kadro': proje.toplam_kadro - proje.mevcut_calisan,
        'doluluk_orani': proje.doluluk_orani,
        'bekleyen_aday': sum(k.bekleyen_aday_sayisi for k in kadrolar),
        'arac_sayisi': len(araclar)
    }
    
    return render_template('proje/proje_detay.html',
                         proje=proje,
                         kadrolar=kadrolar,
                         araclar=araclar,
                         stats=stats)


@proje_bp.route('/proje/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('proje.edit')
def proje_duzenle(id):
    """Proje düzenle"""
    proje = Proje.query.get_or_404(id)
    
    if request.method == 'POST':
        proje.musteri_id = request.form.get('musteri_id', type=int)
        proje.ad = request.form.get('ad')
        proje.kod = request.form.get('kod')
        proje.aciklama = request.form.get('aciklama')
        proje.baslangic_tarihi = request.form.get('baslangic_tarihi') or None
        proje.bitis_tarihi = request.form.get('bitis_tarihi') or None
        proje.butce = request.form.get('butce') or None
        proje.notlar = request.form.get('notlar')
        proje.aktif = request.form.get('aktif') == 'on'
        
        db.session.commit()
        flash('Proje başarıyla güncellendi.', 'success')
        return redirect(url_for('proje.proje_detay', id=id))
    
    musteriler = Musteri.query.filter_by(is_deleted=False, aktif=True).order_by(Musteri.ad).all()
    return render_template('proje/proje_form.html', proje=proje, musteriler=musteriler)

# ==================== KADRO LİSTESİ ====================
@proje_bp.route('/kadrolar')
@login_required
@permission_required('proje.view')
def kadro_liste():
    """Tüm kadroların listesi"""
    page = request.args.get('page', 1, type=int)
    proje_id = request.args.get('proje_id', type=int)
    q = request.args.get('q', '').strip()
    
    query = HedefKadro.query.filter_by(is_deleted=False)
    
    if proje_id:
        query = query.filter_by(proje_id=proje_id)
    
    if q:
        query = query.filter(HedefKadro.pozisyon_adi.ilike(f'%{q}%'))
    
    query = query.order_by(HedefKadro.oncelik, HedefKadro.pozisyon_adi)
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    projeler = Proje.query.filter_by(is_deleted=False, durum='aktif').order_by(Proje.ad).all()
    
    return render_template('proje/kadro_liste.html',
                          kadrolar=pagination.items,
                          pagination=pagination,
                          projeler=projeler)

# ==================== KADRO ====================

@proje_bp.route('/proje/<int:proje_id>/kadro/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('proje.edit')
def kadro_ekle(proje_id):
    """Projeye kadro ekle"""
    proje = Proje.query.get_or_404(proje_id)
    
    if request.method == 'POST':
        kadro = HedefKadro(
            proje_id=proje_id,
            pozisyon_adi=request.form.get('pozisyon_adi'),
            departman=request.form.get('departman'),
            il=request.form.get('il'),
            ilce=request.form.get('ilce'),
            bolge=request.form.get('bolge'),
            hedef_sayi=request.form.get('hedef_sayi', 1, type=int),
            oncelik=request.form.get('oncelik', 5, type=int),
            min_tecrube_yil=request.form.get('min_tecrube_yil', 0, type=int),
            egitim_seviyesi=request.form.get('egitim_seviyesi'),
            ehliyet_gerekli=request.form.get('ehliyet_gerekli') == 'on',
            ehliyet_sinifi=request.form.get('ehliyet_sinifi'),
            cinsiyet_tercihi=request.form.get('cinsiyet_tercihi'),
            yas_min=request.form.get('yas_min', type=int),
            yas_max=request.form.get('yas_max', type=int),
            maas_min=request.form.get('maas_min') or None,
            maas_max=request.form.get('maas_max') or None,
            notlar=request.form.get('notlar'),
            aktif=request.form.get('aktif') == 'on',
            sms_dogrulama_zorunlu=request.form.get('sms_dogrulama_zorunlu') == 'on'
        )
        db.session.add(kadro)
        db.session.commit()
        flash('Kadro başarıyla eklendi.', 'success')
        return redirect(url_for('proje.proje_detay', id=proje_id))
    
    return render_template('proje/kadro_form.html', proje=proje, kadro=None)


@proje_bp.route('/kadro/<int:id>')
@login_required
@permission_required('proje.view')
def kadro_detay(id):
    """Kadro detayı - adaylar ve çalışanlar"""
    kadro = HedefKadro.query.get_or_404(id)
    
    adaylar = kadro.adaylar.filter_by(is_deleted=False).order_by(Aday.created_at.desc()).all()
    calisanlar = kadro.calisanlar.filter_by(is_deleted=False).all()
    
    return render_template('proje/kadro_detay.html',
                         kadro=kadro,
                         adaylar=adaylar,
                         calisanlar=calisanlar)


@proje_bp.route('/kadro/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('proje.edit')
def kadro_duzenle(id):
    """Kadro düzenle"""
    kadro = HedefKadro.query.get_or_404(id)
    
    if request.method == 'POST':
        kadro.pozisyon_adi = request.form.get('pozisyon_adi')
        kadro.departman = request.form.get('departman')
        kadro.il = request.form.get('il')
        kadro.ilce = request.form.get('ilce')
        kadro.bolge = request.form.get('bolge')
        kadro.hedef_sayi = request.form.get('hedef_sayi', 1, type=int)
        kadro.oncelik = request.form.get('oncelik', 5, type=int)
        kadro.min_tecrube_yil = request.form.get('min_tecrube_yil', 0, type=int)
        kadro.egitim_seviyesi = request.form.get('egitim_seviyesi')
        kadro.ehliyet_gerekli = request.form.get('ehliyet_gerekli') == 'on'
        kadro.ehliyet_sinifi = request.form.get('ehliyet_sinifi')
        kadro.cinsiyet_tercihi = request.form.get('cinsiyet_tercihi')
        kadro.yas_min = request.form.get('yas_min', type=int)
        kadro.yas_max = request.form.get('yas_max', type=int)
        kadro.maas_min = request.form.get('maas_min') or None
        kadro.maas_max = request.form.get('maas_max') or None
        kadro.notlar = request.form.get('notlar')
        kadro.aktif = request.form.get('aktif') == 'on'
        kadro.sms_dogrulama_zorunlu = request.form.get('sms_dogrulama_zorunlu') == 'on'
        
        db.session.commit()
        flash('Kadro başarıyla güncellendi.', 'success')
        return redirect(url_for('proje.kadro_detay', id=id))
    
    return render_template('proje/kadro_form.html', proje=kadro.proje, kadro=kadro)


@proje_bp.route('/kadro/<int:id>/aday/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('ik.create')
def kadro_aday_ekle(id):
    """Kadroya aday ekle"""
    kadro = HedefKadro.query.get_or_404(id)
    
    if request.method == 'POST':
        aday = Aday(
            kadro_id=kadro.id,
            ad=request.form.get('ad'),
            soyad=request.form.get('soyad'),
            email=request.form.get('email'),
            telefon=request.form.get('telefon'),
            durum='basvurdu',
            kaynak=request.form.get('kaynak'),
            notlar=request.form.get('notlar')
        )
        db.session.add(aday)
        db.session.commit()
        flash('Aday başarıyla eklendi.', 'success')
        return redirect(url_for('proje.kadro_detay', id=id))
    
    return render_template('proje/aday_form.html', kadro=kadro, aday=None)


# ==================== API ====================

@proje_bp.route('/api/musteriler')
@login_required
def api_musteriler():
    """Select2 için müşteri arama"""
    q = request.args.get('q', '')
    query = Musteri.query.filter_by(is_deleted=False, aktif=True)
    
    if q:
        query = query.filter(
            db.or_(
                Musteri.ad.ilike(f'%{q}%'),
                Musteri.kisa_ad.ilike(f'%{q}%')
            )
        )
    
    musteriler = query.order_by(Musteri.ad).limit(20).all()
    return jsonify([{'id': m.id, 'text': m.display_name} for m in musteriler])


@proje_bp.route('/api/projeler')
@login_required
def api_projeler():
    """Select2 için proje arama"""
    q = request.args.get('q', '')
    musteri_id = request.args.get('musteri_id', type=int)
    
    query = Proje.query.filter_by(is_deleted=False, aktif=True)
    
    if musteri_id:
        query = query.filter_by(musteri_id=musteri_id)
    
    if q:
        query = query.filter(Proje.ad.ilike(f'%{q}%'))
    
    projeler = query.order_by(Proje.ad).limit(20).all()
    return jsonify([{'id': p.id, 'text': f'{p.ad} ({p.musteri.display_name})'} for p in projeler])


@proje_bp.route('/api/kadrolar')
@login_required
def api_kadrolar():
    """Select2 için kadro arama"""
    q = request.args.get('q', '')
    proje_id = request.args.get('proje_id', type=int)
    
    query = HedefKadro.query.filter_by(is_deleted=False, aktif=True)
    
    if proje_id:
        query = query.filter_by(proje_id=proje_id)
    
    if q:
        query = query.filter(HedefKadro.pozisyon_adi.ilike(f'%{q}%'))
    
    kadrolar = query.order_by(HedefKadro.pozisyon_adi).limit(20).all()
    return jsonify([{'id': k.id, 'text': k.full_title} for k in kadrolar])


# ==================== ARAÇ YÖNETİMİ ====================

@proje_bp.route('/proje/<int:proje_id>/arac/ata', methods=['GET', 'POST'])
@login_required
@permission_required('filo.edit')
def arac_ata(proje_id):
    """Projeye araç ata"""
    from app.models.filo import Arac
    
    proje = Proje.query.get_or_404(proje_id)
    
    if request.method == 'POST':
        arac_ids = request.form.getlist('arac_ids', type=int)
        
        if arac_ids:
            Arac.query.filter(Arac.id.in_(arac_ids)).update(
                {'proje_id': proje_id}, synchronize_session=False
            )
            db.session.commit()
            flash(f'{len(arac_ids)} araç projeye atandı.', 'success')
        
        return redirect(url_for('proje.proje_detay', id=proje_id))
    
    # Projeye atanmamış (proje_id == None) aktif araçlar
    musait_araclar = Arac.query.filter(
        Arac.is_deleted == False,
        Arac.proje_id == None
    ).order_by(Arac.plaka).all()
    
    return render_template('proje/arac_ata.html',
                         proje=proje,
                         musait_araclar=musait_araclar)


@proje_bp.route('/proje/<int:proje_id>/arac/<int:arac_id>/cikar')
@login_required
@permission_required('filo.edit')
def arac_cikar(proje_id, arac_id):
    """Araçı projeden çıkar"""
    from app.models.filo import Arac
    
    arac = Arac.query.get_or_404(arac_id)
    
    if arac.proje_id == proje_id:
        arac.proje_id = None
        db.session.commit()
        flash(f'{arac.plaka} projeden çıkarıldı.', 'success')
    
    return redirect(url_for('proje.proje_detay', id=proje_id))
# ============================================================
# routes.py'ye EKLENECEK ADAY → ÇALIŞAN DÖNÜŞÜMÜ
# Bu kodları app/modules/proje/routes.py dosyasına ekle
# ============================================================

@proje_bp.route('/aday/<int:id>/ise-al', methods=['GET', 'POST'])
@login_required
@permission_required('ik.create')
def aday_ise_al(id):
    """Adayı işe al - Çalışana dönüştür"""
    from app.models.ik import Aday, Calisan
    from app.models.base import CalisanDurumu
    from datetime import date
    
    aday = Aday.query.get_or_404(id)
    
    if request.method == 'POST':
        # Yeni çalışan oluştur
        calisan = Calisan(
            ad=aday.ad,
            soyad=aday.soyad,
            email=aday.email,
            telefon=aday.telefon,
            kadro_id=aday.kadro_id,
            pozisyon_id=aday.pozisyon_id,
            sicil_no=request.form.get('sicil_no'),
            tc_kimlik=request.form.get('tc_kimlik'),
            ise_baslama=datetime.strptime(request.form.get('ise_baslama'), '%Y-%m-%d').date() if request.form.get('ise_baslama') else date.today(),
            calisma_tipi=request.form.get('calisma_tipi', 'tam_zamanli'),
            durum=CalisanDurumu.AKTIF
        )
        
        # Adayı güncelle
        aday.durum = 'ise_alindi'
        
        db.session.add(calisan)
        db.session.commit()
        
        flash(f'{calisan.full_name} başarıyla işe alındı.', 'success')
        
        # Kadro detayına dön
        if aday.kadro_id:
            return redirect(url_for('proje.kadro_detay', id=aday.kadro_id))
        return redirect(url_for('ik.liste'))
    
    return render_template('proje/aday_ise_al.html', aday=aday)


@proje_bp.route('/aday/<int:id>/reddet')
@login_required
@permission_required('ik.edit')
def aday_reddet(id):
    """Adayı reddet"""
    from app.models.ik import Aday
    
    aday = Aday.query.get_or_404(id)
    aday.durum = 'red'
    db.session.commit()
    
    flash(f'{aday.full_name} reddedildi.', 'warning')
    
    if aday.kadro_id:
        return redirect(url_for('proje.kadro_detay', id=aday.kadro_id))
    return redirect(url_for('ik.aday_liste'))


@proje_bp.route('/aday/<int:id>/durum/<durum>')
@login_required
@permission_required('ik.edit')
def aday_durum_degistir(id, durum):
    """Aday durumunu değiştir"""
    from app.models.ik import Aday
    
    gecerli_durumlar = ['basvurdu', 'degerlendiriliyor', 'mulakat', 'teklif', 'ise_alindi', 'red']
    
    if durum not in gecerli_durumlar:
        flash('Geçersiz durum.', 'danger')
        return redirect(request.referrer or url_for('proje.proje_liste'))
    
    aday = Aday.query.get_or_404(id)
    aday.durum = durum
    db.session.commit()
    
    flash(f'{aday.full_name} durumu güncellendi: {durum}', 'success')
    
    if aday.kadro_id:
        return redirect(url_for('proje.kadro_detay', id=aday.kadro_id))
    return redirect(request.referrer or url_for('proje.proje_liste'))


