# -*- coding: utf-8 -*-
"""
TG Portal - Public Başvuru Routes
Aday başvuru sistemi - Login gerektirmez
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from datetime import datetime
from app import db
from app.models.ik import Aday

basvuru_bp = Blueprint('basvuru', __name__)


@basvuru_bp.route('/<token>')
def basvuru_giris(token):
    """Başvuru giriş sayfası - KVKK aydınlatma metni"""
    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first_or_404()
    
    # Token geçerlilik kontrolü
    if not aday.is_token_valid:
        return render_template('basvuru/token_expired.html', aday=aday)
    
    # Zaten tamamlandı mı?
    if aday.basvuru_tamamlandi:
        return render_template('basvuru/zaten_tamamlandi.html', aday=aday)
    
    # KVKK onaylandı mı?
    if aday.kvkk_onay:
        return redirect(url_for('basvuru.basvuru_form', token=token))
    
    return render_template('basvuru/kvkk_onay.html', aday=aday)


@basvuru_bp.route('/<token>/kvkk-onayla', methods=['POST'])
def kvkk_onayla(token):
    """KVKK onay işlemi"""
    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first_or_404()
    
    if not aday.is_token_valid:
        flash('Başvuru linkinizin süresi dolmuş.', 'danger')
        return redirect(url_for('basvuru.basvuru_giris', token=token))
    
    # Onay checkbox kontrolü
    if not request.form.get('kvkk_onay'):
        flash('Devam etmek için aydınlatma metnini onaylamanız gerekmektedir.', 'warning')
        return redirect(url_for('basvuru.basvuru_giris', token=token))
    
    # KVKK onayını kaydet
    aday.kvkk_onay = True
    aday.kvkk_onay_tarihi = datetime.utcnow()
    aday.kvkk_onay_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    aday.aydinlatma_metni_versiyonu = '1.0'
    aday.durum = 'form_bekleniyor'
    
    db.session.commit()
    
    flash('KVKK onayınız kaydedildi. Lütfen başvuru formunu doldurun.', 'success')
    return redirect(url_for('basvuru.basvuru_form', token=token))


@basvuru_bp.route('/<token>/form', methods=['GET', 'POST'])
def basvuru_form(token):
    """Başvuru formu"""
    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first_or_404()
    
    if not aday.is_token_valid:
        return render_template('basvuru/token_expired.html', aday=aday)
    
    if not aday.kvkk_onay:
        flash('Devam etmek için önce aydınlatma metnini onaylamanız gerekmektedir.', 'warning')
        return redirect(url_for('basvuru.basvuru_giris', token=token))
    
    if aday.basvuru_tamamlandi:
        return render_template('basvuru/zaten_tamamlandi.html', aday=aday)
    
    if request.method == 'POST':
        # Kişisel bilgiler
        aday.ad = request.form.get('ad', aday.ad)
        aday.soyad = request.form.get('soyad', aday.soyad)
        aday.tc_kimlik = request.form.get('tc_kimlik')
        aday.dogum_tarihi = datetime.strptime(request.form.get('dogum_tarihi'), '%Y-%m-%d').date() if request.form.get('dogum_tarihi') else None
        aday.dogum_yeri = request.form.get('dogum_yeri')
        aday.cinsiyet = request.form.get('cinsiyet')
        aday.medeni_durum = request.form.get('medeni_durum')
        
        # İletişim
        aday.email = request.form.get('email', aday.email)
        aday.telefon = request.form.get('telefon', aday.telefon)
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
        
        return redirect(url_for('basvuru.basvuru_tamam', token=token))
    
    # Kadro bilgilerini al
    kadro = aday.kadro if hasattr(aday, 'kadro') and aday.kadro else None
    
    return render_template('basvuru/form.html', aday=aday, kadro=kadro)


@basvuru_bp.route('/<token>/tamam')
def basvuru_tamam(token):
    """Başvuru tamamlandı sayfası"""
    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first_or_404()
    return render_template('basvuru/tamam.html', aday=aday)


# ==================== İK Tarafı Route'ları ====================

from flask_login import login_required, current_user
from app.utils import permission_required


def send_sms_davet(aday, basvuru_link):
    """SMS ile davet gönder (Twilio)"""
    try:
        from twilio.rest import Client
        
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        from_number = current_app.config.get('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, from_number]):
            current_app.logger.error("Twilio yapılandırması eksik")
            return {'success': False, 'error': 'SMS servisi yapılandırılmamış'}
        
        client = Client(account_sid, auth_token)
        
        # Telefon numarasını formatla
        telefon = aday.telefon.replace(' ', '').replace('-', '')
        if telefon.startswith('0'):
            telefon = '+90' + telefon[1:]
        elif not telefon.startswith('+'):
            telefon = '+90' + telefon
        
        # Kadro bilgisi
        kadro_bilgi = ""
        if aday.kadro:
            musteri_ad = aday.kadro.proje.musteri.kisa_ad or aday.kadro.proje.musteri.ad
            kadro_bilgi = f"{musteri_ad} - {aday.kadro.pozisyon_adi} "
        
        mesaj = (
            f"Sayin {aday.ad} {aday.soyad}, "
            f"{kadro_bilgi}pozisyonu icin is basvuru davetiniz: {basvuru_link} "
            f"Link 72 saat gecerlidir. - Team Guerilla IK"
        )
        
        message = client.messages.create(
            body=mesaj,
            from_=from_number,
            to=telefon
        )
        
        current_app.logger.info(f"SMS gönderildi: {telefon} - SID: {message.sid}")
        return {'success': True, 'message_sid': message.sid}
        
    except Exception as e:
        current_app.logger.error(f"SMS gönderim hatası: {str(e)}")
        return {'success': False, 'error': str(e)}


def send_email_davet(aday, basvuru_link):
    """Email ile davet gönder"""
    # TODO: Flask-Mail entegrasyonu
    current_app.logger.info(f"Email gönderilecek: {aday.email} - Link: {basvuru_link}")
    return {'success': True, 'info': 'Email simüle edildi'}


@basvuru_bp.route('/davet/<int:kadro_id>', methods=['GET', 'POST'])
@login_required
@permission_required('ik.create')
def aday_davet(kadro_id):
    """Kadroya aday davet et"""
    from app.models.proje import HedefKadro
    
    kadro = HedefKadro.query.get_or_404(kadro_id)
    
    if request.method == 'POST':
        ad = request.form.get('ad')
        soyad = request.form.get('soyad')
        iletisim = request.form.get('iletisim')  # telefon veya email
        davet_tipi = request.form.get('davet_tipi', 'sms')  # sms veya email
        
        if not ad or not soyad or not iletisim:
            flash('Ad, soyad ve iletişim bilgisi zorunludur.', 'danger')
            return redirect(url_for('basvuru.aday_davet', kadro_id=kadro_id))
        
        # Aday oluştur
        aday = Aday(
            ad=ad,
            soyad=soyad,
            kadro_id=kadro_id,
            pozisyon_id=kadro.pozisyon_id if hasattr(kadro, 'pozisyon_id') else None,
            davet_tipi=davet_tipi,
            kaynak=f'{davet_tipi}_davet',
            durum='davet_gonderildi'
        )
        
        if davet_tipi == 'email':
            aday.email = iletisim
        else:
            aday.telefon = iletisim
        
        # Token oluştur
        aday.generate_token()
        aday.davet_gonderim_tarihi = datetime.utcnow()
        
        db.session.add(aday)
        db.session.commit()
        
        # Başvuru linki oluştur
        basvuru_link = url_for('basvuru.basvuru_giris', token=aday.davet_token, _external=True)
        
        # SMS veya Email gönder
        if davet_tipi == 'sms':
            result = send_sms_davet(aday, basvuru_link)
            if result['success']:
                flash(f'SMS daveti gönderildi: {iletisim}', 'success')
            else:
                flash(f'SMS gönderilemedi: {result.get("error", "Bilinmeyen hata")}. Link: {basvuru_link}', 'warning')
        else:
            result = send_email_davet(aday, basvuru_link)
            if result['success']:
                flash(f'Email daveti gönderildi: {iletisim}', 'success')
            else:
                flash(f'Email gönderilemedi. Link: {basvuru_link}', 'warning')
        
        return redirect(url_for('proje.kadro_detay', id=kadro_id))
    
    return render_template('basvuru/davet_form.html', kadro=kadro)


@basvuru_bp.route('/toplu-davet/<int:kadro_id>', methods=['POST'])
@login_required
@permission_required('ik.create')
def toplu_davet(kadro_id):
    """Toplu aday davet - CSV/Excel'den veya manuel liste"""
    from app.models.proje import HedefKadro
    
    kadro = HedefKadro.query.get_or_404(kadro_id)
    
    # Metin alanından çoklu kişi al (her satır: ad, soyad, telefon/email)
    kisi_listesi = request.form.get('kisi_listesi', '')
    davet_tipi = request.form.get('davet_tipi', 'sms')
    
    basarili = 0
    hatali = 0
    
    for satir in kisi_listesi.strip().split('\n'):
        parcalar = [p.strip() for p in satir.split(',')]
        if len(parcalar) >= 3:
            ad, soyad, iletisim = parcalar[0], parcalar[1], parcalar[2]
            
            try:
                aday = Aday(
                    ad=ad,
                    soyad=soyad,
                    kadro_id=kadro_id,
                    davet_tipi=davet_tipi,
                    kaynak=f'{davet_tipi}_davet',
                    durum='davet_gonderildi'
                )
                
                if davet_tipi == 'email':
                    aday.email = iletisim
                else:
                    aday.telefon = iletisim
                
                aday.generate_token()
                aday.davet_gonderim_tarihi = datetime.utcnow()
                
                db.session.add(aday)
                db.session.flush()  # ID al
                
                # Başvuru linki oluştur ve SMS gönder
                basvuru_link = url_for('basvuru.basvuru_giris', token=aday.davet_token, _external=True)
                
                if davet_tipi == 'sms':
                    send_sms_davet(aday, basvuru_link)
                else:
                    send_email_davet(aday, basvuru_link)
                
                basarili += 1
            except Exception as e:
                current_app.logger.error(f"Toplu davet hatası: {str(e)}")
                hatali += 1
        else:
            hatali += 1
    
    db.session.commit()
    
    flash(f'{basarili} aday davet edildi, {hatali} hata oluştu.', 'success' if basarili > 0 else 'warning')
    return redirect(url_for('proje.kadro_detay', id=kadro_id))


@basvuru_bp.route('/davet-tekrar/<int:aday_id>')
@login_required
@permission_required('ik.edit')
def davet_tekrar(aday_id):
    """Davet linkini yeniden gönder"""
    aday = Aday.query.get_or_404(aday_id)
    
    # Yeni token oluştur
    aday.generate_token()
    aday.davet_gonderim_tarihi = datetime.utcnow()
    aday.durum = 'davet_gonderildi'
    
    db.session.commit()
    
    basvuru_link = url_for('basvuru.basvuru_giris', token=aday.davet_token, _external=True)
    
    # Gönderim
    if aday.davet_tipi == 'sms' and aday.telefon:
        result = send_sms_davet(aday, basvuru_link)
        if result['success']:
            flash(f'SMS tekrar gönderildi: {aday.telefon}', 'success')
        else:
            flash(f'SMS gönderilemedi: {result.get("error")}. Link: {basvuru_link}', 'warning')
    elif aday.email:
        result = send_email_davet(aday, basvuru_link)
        flash(f'Email tekrar gönderildi: {aday.email}', 'success')
    else:
        flash(f'İletişim bilgisi bulunamadı. Link: {basvuru_link}', 'warning')
    
    if aday.kadro_id:
        return redirect(url_for('proje.kadro_detay', id=aday.kadro_id))
    return redirect(url_for('ik.aday_liste'))