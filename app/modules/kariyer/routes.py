# -*- coding: utf-8 -*-
"""
TG Portal - Public Kariyer Sayfası
Açık pozisyonları görüntüleme ve doğrudan başvuru - Login gerektirmez
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from datetime import datetime
from app import db
from app.models.ik import Aday, KAYNAK_TURLERI, EvrakTipi, AdayEvrak
from app.models.proje import HedefKadro, Proje, Musteri

kariyer_bp = Blueprint('kariyer', __name__)


@kariyer_bp.route('/')
def pozisyonlar():
    """Açık pozisyonları listele"""
    # Aktif projelerdeki eksik kadrolu pozisyonları getir
    kadrolar = HedefKadro.query.join(Proje).join(Musteri).filter(
        Proje.aktif == True,
        Musteri.aktif == True,
        HedefKadro.is_deleted == False
    ).all()
    
    # Sadece eksik kadrosu olanları filtrele
    acik_pozisyonlar = [k for k in kadrolar if k.eksik_sayi > 0]
    
    # İllere göre grupla
    iller = set()
    for k in acik_pozisyonlar:
        if k.il:
            iller.add(k.il)
    
    # Filtreler
    il_filtre = request.args.get('il')
    if il_filtre:
        acik_pozisyonlar = [k for k in acik_pozisyonlar if k.il == il_filtre]
    
    return render_template('kariyer/pozisyonlar.html', 
                         pozisyonlar=acik_pozisyonlar,
                         iller=sorted(iller),
                         il_filtre=il_filtre)


@kariyer_bp.route('/basvur/<int:kadro_id>')
def basvuru_kvkk(kadro_id):
    """Açık başvuru - KVKK aydınlatma metni"""
    kadro = HedefKadro.query.get_or_404(kadro_id)
    
    # Aktif proje kontrolü
    if not kadro.proje.aktif:
        flash('Bu pozisyon için başvuru alınmamaktadır.', 'warning')
        return redirect(url_for('kariyer.pozisyonlar'))
    
    return render_template('kariyer/kvkk_onay.html', kadro=kadro)


@kariyer_bp.route('/basvur/<int:kadro_id>/kvkk-onayla', methods=['POST'])
def kvkk_onayla(kadro_id):
    """Açık başvuru - KVKK onay işlemi"""
    kadro = HedefKadro.query.get_or_404(kadro_id)
    
    if not request.form.get('kvkk_onay'):
        flash('Devam etmek için aydınlatma metnini onaylamanız gerekmektedir.', 'warning')
        return redirect(url_for('kariyer.basvuru_kvkk', kadro_id=kadro_id))
    
    # Geçici aday oluştur (ad/soyad form'dan gelecek)
    aday = Aday(
        ad='',  # Form'dan doldurulacak
        soyad='',
        kadro_id=kadro_id,
        kaynak='acik_basvuru',
        durum='form_bekleniyor',
        kvkk_onay=True,
        kvkk_onay_tarihi=datetime.utcnow(),
        kvkk_onay_ip=request.headers.get('X-Forwarded-For', request.remote_addr),
        aydinlatma_metni_versiyonu='1.0'
    )
    
    # Token oluştur (form için)
    aday.generate_token()
    
    db.session.add(aday)
    db.session.commit()
    
    # SMS doğrulama gerekiyor mu?
    if kadro.sms_dogrulama_zorunlu:
        return redirect(url_for('basvuru.telefon_dogrula', token=aday.davet_token))
    
    return redirect(url_for('kariyer.basvuru_form', token=aday.davet_token))


@kariyer_bp.route('/basvur/form/<token>', methods=['GET', 'POST'])
def basvuru_form(token):
    """Açık başvuru formu"""
    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first_or_404()
    
    if not aday.is_token_valid:
        flash('Başvuru süreniz dolmuş. Lütfen tekrar başvurun.', 'danger')
        return redirect(url_for('kariyer.pozisyonlar'))
    
    if aday.basvuru_tamamlandi:
        return render_template('kariyer/zaten_tamamlandi.html', aday=aday)
    
    kadro = aday.kadro
    
    if request.method == 'POST':
        # Zorunlu alanlar
        aday.ad = request.form.get('ad')
        aday.soyad = request.form.get('soyad')
        
        if not aday.ad or not aday.soyad:
            flash('Ad ve soyad alanları zorunludur.', 'danger')
            return redirect(url_for('kariyer.basvuru_form', token=token))
        
        # Kişisel bilgiler
        aday.tc_kimlik = request.form.get('tc_kimlik')
        aday.dogum_tarihi = datetime.strptime(request.form.get('dogum_tarihi'), '%Y-%m-%d').date() if request.form.get('dogum_tarihi') else None
        aday.dogum_yeri = request.form.get('dogum_yeri')
        aday.cinsiyet = request.form.get('cinsiyet')
        aday.medeni_durum = request.form.get('medeni_durum')
        
        # İletişim
        aday.email = request.form.get('email')
        aday.telefon = request.form.get('telefon')
        aday.adres = request.form.get('adres')
        aday.il = request.form.get('il')
        aday.ilce = request.form.get('ilce')
        
        # Eğitim
        aday.egitim_durumu = request.form.get('egitim_durumu')
        aday.okul_adi = request.form.get('okul_adi')
        aday.bolum = request.form.get('bolum')
        aday.mezuniyet_yili = int(request.form.get('mezuniyet_yili')) if request.form.get('mezuniyet_yili') else None
        
        # Ehliyet
        aday.ehliyet_var = request.form.get('ehliyet_var') == 'on'
        aday.ehliyet_sinifi = request.form.get('ehliyet_sinifi')
        aday.ehliyet_tarihi = datetime.strptime(request.form.get('ehliyet_tarihi'), '%Y-%m-%d').date() if request.form.get('ehliyet_tarihi') else None
        aday.src_belgesi = request.form.get('src_belgesi') == 'on'
        aday.psikoteknik = request.form.get('psikoteknik') == 'on'
        
        # İş deneyimi
        aday.toplam_tecrube_yil = int(request.form.get('toplam_tecrube_yil') or 0)
        aday.son_is_yeri = request.form.get('son_is_yeri')
        aday.son_pozisyon = request.form.get('son_pozisyon')
        aday.son_is_baslangic = datetime.strptime(request.form.get('son_is_baslangic'), '%Y-%m-%d').date() if request.form.get('son_is_baslangic') else None
        aday.son_is_bitis = datetime.strptime(request.form.get('son_is_bitis'), '%Y-%m-%d').date() if request.form.get('son_is_bitis') else None
        aday.son_is_ayrilma_nedeni = request.form.get('son_is_ayrilma_nedeni')
        
        # Referans
        aday.referans_ad = request.form.get('referans_ad')
        aday.referans_telefon = request.form.get('referans_telefon')
        aday.referans_iliski = request.form.get('referans_iliski')
        
        # Ek bilgiler
        aday.saglik_sorunu = request.form.get('saglik_sorunu') == 'on'
        aday.saglik_sorunu_aciklama = request.form.get('saglik_sorunu_aciklama')
        aday.askerlik_durumu = request.form.get('askerlik_durumu')
        aday.askerlik_tecil_tarihi = datetime.strptime(request.form.get('askerlik_tecil_tarihi'), '%Y-%m-%d').date() if request.form.get('askerlik_tecil_tarihi') else None
        aday.sabika_kaydi = request.form.get('sabika_kaydi') == 'on'
        aday.sabika_aciklama = request.form.get('sabika_aciklama')
        
        # Tercihler
        aday.calisabilecegi_iller = request.form.get('calisabilecegi_iller')
        aday.beklenen_maas = request.form.get('beklenen_maas') or None
        aday.ne_zaman_baslayabilir = request.form.get('ne_zaman_baslayabilir')
        aday.vardiyali_calisabilir = request.form.get('vardiyali_calisabilir') == 'on'
        aday.seyahat_engeli = request.form.get('seyahat_engeli') == 'on'
        
        # Dosya yüklemeleri
        import os
        from werkzeug.utils import secure_filename
        
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'adaylar', str(aday.id))
        os.makedirs(upload_folder, exist_ok=True)
        
        file_fields = ['foto', 'cv_dosya', 'kimlik_on', 'kimlik_arka', 'ehliyet_foto', 
                      'diploma_foto', 'src_foto', 'ikametgah', 'adli_sicil']
        
        for field in file_fields:
            file = request.files.get(field)
            if file and file.filename:
                filename = secure_filename(f"{field}_{aday.id}_{file.filename}")
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                setattr(aday, field, f"uploads/adaylar/{aday.id}/{filename}")
        
        # Başvuruyu tamamla
        aday.basvuru_tamamlandi = True
        aday.basvuru_tarihi = datetime.utcnow()
        aday.durum = 'basvurdu'
        
        db.session.commit()

        # İK ekibine bildirim gönder
        from app.services.notification import notify_yeni_basvuru
        notify_yeni_basvuru(aday)
        
        return redirect(url_for('kariyer.basvuru_tamam', token=token))
    
    return render_template('kariyer/form.html', aday=aday, kadro=kadro)


@kariyer_bp.route('/basvur/tamam/<token>')
def basvuru_tamam(token):
    """Başvuru tamamlandı sayfası"""
    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first_or_404()
    return render_template('kariyer/tamam.html', aday=aday)


# ============================================================
# ADAY EVRAK YÜKLEME (PUBLIC - TOKEN İLE)
# ============================================================

@kariyer_bp.route('/evrak/<token>')
def evrak_yukle_sayfa(token):
    """Aday evrak yükleme sayfası (public)"""
    from datetime import datetime
    
    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first()
    
    if not aday:
        flash('Geçersiz veya süresi dolmuş link.', 'danger')
        return redirect(url_for('kariyer.basvuru'))
    
    # Token süresi kontrolü (opsiyonel - evrak için daha uzun süre verilebilir)
    # if aday.davet_token_expires and aday.davet_token_expires < datetime.utcnow():
    #     flash('Link süresi dolmuş.', 'danger')
    #     return redirect(url_for('kariyer.basvuru'))
    
    evrak_tipleri = EvrakTipi.query.filter_by(aktif=True).order_by(EvrakTipi.sira).all()
    evraklar = aday.evraklar.all()
    
    # Eksik evraklar
    yuklenen_tipler = [e.evrak_tipi_id for e in aday.evraklar.filter(
        AdayEvrak.durum.in_(['yuklendi', 'onaylandi'])
    ).all()]
    eksik_evraklar = [t for t in EvrakTipi.query.filter_by(zorunlu=True, aktif=True).all() if t.id not in yuklenen_tipler]
    
    # Tamamlanma oranı
    zorunlu_count = EvrakTipi.query.filter_by(zorunlu=True, aktif=True).count()
    if zorunlu_count == 0:
        evrak_tamamlanma = 100
    else:
        tamamlanan = len([t for t in EvrakTipi.query.filter_by(zorunlu=True, aktif=True).all() if t.id in yuklenen_tipler])
        evrak_tamamlanma = int((tamamlanan / zorunlu_count) * 100)
    
    return render_template('kariyer/evrak_yukle.html',
                          aday=aday,
                          token=token,
                          evraklar=evraklar,
                          evrak_tipleri=evrak_tipleri,
                          eksik_evraklar=eksik_evraklar,
                          evrak_tamamlanma=evrak_tamamlanma)


@kariyer_bp.route('/evrak/<token>/yukle', methods=['POST'])
def evrak_yukle_post(token):
    """Aday evrak yükleme işlemi (public)"""
    from datetime import datetime
    from werkzeug.utils import secure_filename
    import os
    
    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first()
    
    if not aday:
        flash('Geçersiz link.', 'danger')
        return redirect(url_for('kariyer.basvuru'))
    
    if 'dosya' not in request.files:
        flash('Dosya seçilmedi.', 'danger')
        return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))
    
    dosya = request.files['dosya']
    if dosya.filename == '':
        flash('Dosya seçilmedi.', 'danger')
        return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))
    
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    if dosya and allowed_file(dosya.filename):
        evrak_tipi_id = int(request.form['evrak_tipi_id'])
        
        # Dosya adı oluştur
        filename = secure_filename(dosya.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"aday_{aday.id}_{evrak_tipi_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        
        # Klasör oluştur
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'evraklar', 'adaylar', str(aday.id))
        os.makedirs(upload_folder, exist_ok=True)
        
        # Dosyayı kaydet
        filepath = os.path.join(upload_folder, new_filename)
        dosya.save(filepath)
        
        # Veritabanına ekle
        evrak = AdayEvrak(
            aday_id=aday.id,
            evrak_tipi_id=evrak_tipi_id,
            dosya_adi=filename,
            dosya_yolu=filepath,
            dosya_boyut=os.path.getsize(filepath),
            mime_type=dosya.content_type
        )
        db.session.add(evrak)
        db.session.commit()
        
        flash('Evrak başarıyla yüklendi.', 'success')
    else:
        flash('Geçersiz dosya formatı. (PDF, JPG, PNG, DOC, DOCX)', 'danger')
    
    return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))
