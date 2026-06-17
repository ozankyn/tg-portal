# -*- coding: utf-8 -*-
"""
Bildirim Servisi - Email bildirimleri
"""

import re
from collections import defaultdict
from flask import current_app, url_for
from flask_mail import Message
from app import mail, db


# -------------------------------------------------------------------
# Sablon render + sablon bazli bildirim gonderimi
# -------------------------------------------------------------------

_VAR_RE = re.compile(r'\{(\w+)\}')


class _DefaultDict(dict):
    """Eksik anahtarlari '-' olarak dondurur"""
    def __missing__(self, key):
        return '-'


def render_sablon(tpl, degiskenler):
    """Sablondaki {anahtar} placeholder'larini doldurur.
    CSS/HTML'deki { } karakterlerine dokunmaz - sadece {kelime} pattern'ini yakalar.
    Bilinmeyen anahtarlar '-' olur.
    """
    if not tpl:
        return ''
    vars_dict = _DefaultDict(degiskenler or {})
    return _VAR_RE.sub(lambda m: str(vars_dict[m.group(1)]), tpl)


def send_bildirim(kod, degiskenler=None, proje_id=None):
    """DB'deki bildirim sablonunu render edip mail gonderir.

    kod: BildirimSablonu.kod (ISE_GIRIS, ISTEN_CIKIS, YENI_BASVURU, SOZLESME_UYARI)
    degiskenler: dict - sablondaki {anahtar}'lari doldurmak icin
    proje_id: opsiyonel - proje_yoneticisine_gonder=True ise ilgili koordinatore de gonderir
    """
    from app.models.bildirim import BildirimSablonu
    from app.models.core import User

    degiskenler = degiskenler or {}
    sablon = BildirimSablonu.query.filter_by(kod=kod, aktif=True).first()
    if not sablon:
        print(f">>> BILDIRIM: sablon bulunamadi veya pasif: {kod}", flush=True)
        return False

    konu = render_sablon(sablon.konu_sablonu, degiskenler)
    icerik = render_sablon(sablon.icerik_sablonu, degiskenler)

    alicilar = set(sablon.alicilar or [])

    if sablon.dinamik_alici_rolu:
        rol = sablon.dinamik_alici_rolu
        users = User.query.filter(User.is_active == True, User.email.isnot(None)).all()
        for u in users:
            if u.has_permission(rol):
                alicilar.add(u.email)

    if sablon.proje_yoneticisine_gonder and proje_id:
        # Proje'de koordinator_id alani yok - ileride eklenince aktif olur
        from app.models.proje import Proje
        proje = Proje.query.get(proje_id)
        if proje and hasattr(proje, 'koordinator') and proje.koordinator and proje.koordinator.email:
            alicilar.add(proje.koordinator.email)
        elif proje:
            current_app.logger.info(f"[{kod}] proje_yoneticisine_gonder=True ama Proje.koordinator yok (proje_id={proje_id})")

    if not alicilar:
        print(f">>> BILDIRIM: alici bulunamadi: {kod}", flush=True)
        return False

    return send_notification(sorted(alicilar), konu, icerik)


def send_notification(to, subject, html_body, text_body=None):
    """Genel bildirim gönderme fonksiyonu"""
    import sys
    recipients = [to] if isinstance(to, str) else to
    print(f">>> MAIL GONDERILIYOR: to={recipients}, subject={subject}", flush=True)
    try:
        mail_server = current_app.config.get('MAIL_SERVER')
        if not mail_server:
            print(f">>> MAIL_SERVER BOŞ — gönderim iptal", flush=True)
            return False

        print(f">>> SMTP: {mail_server}:{current_app.config.get('MAIL_PORT')}, user={current_app.config.get('MAIL_USERNAME')}", flush=True)
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            body=text_body
        )
        mail.send(msg)
        print(f">>> MAIL BASARIYLA GONDERILDI: {recipients}", flush=True)
        return True
    except Exception as e:
        print(f">>> MAIL HATA: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        return False


def notify_yeni_basvuru(aday):
    """Yeni aday basvurusu - sablonu YENI_BASVURU"""
    proje_adi = '-'
    pozisyon_adi = '-'
    lokasyon = '-'
    proje_id = None
    if aday.kadro:
        pozisyon_adi = aday.kadro.pozisyon_adi or '-'
        if aday.kadro.proje:
            proje_adi = aday.kadro.proje.ad
            proje_id = aday.kadro.proje.id
        if aday.kadro.il:
            lokasyon = aday.kadro.il

    try:
        basvuru_url = url_for('proje.kadro_detay', id=aday.kadro_id, _external=True) if aday.kadro_id else '#'
    except Exception:
        basvuru_url = '#'

    degiskenler = {
        'ad_soyad': aday.full_name,
        'telefon': aday.telefon or '-',
        'email': aday.email or '-',
        'pozisyon': pozisyon_adi,
        'proje': proje_adi,
        'lokasyon': lokasyon,
        'kaynak': aday.kaynak or 'Belirtilmemiş',
        'tecrube_yil': getattr(aday, 'toplam_tecrube_yil', 0) or 0,
        'son_is_yeri': getattr(aday, 'son_is_yeri', None) or '-',
        'son_pozisyon': getattr(aday, 'son_pozisyon', None) or '-',
        'basvuru_url': basvuru_url,
    }
    return send_bildirim('YENI_BASVURU', degiskenler, proje_id=proje_id)


def notify_onay_bekliyor(talep, onaylayan):
    """Onay bekleyen talep - Onaylayana bildirim"""
    
    if not onaylayan.email:
        return False
    
    talep_turu = getattr(talep, 'talep_turu', type(talep).__name__)
    talep_sahibi = talep.calisan.full_name if hasattr(talep, 'calisan') else 'Bilinmiyor'
    
    subject = f"Onay Bekliyor: {talep_turu}"
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #d97706, #f59e0b); padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Onayınız Bekleniyor</h2>
        </div>
        <div style="padding: 25px; background: #f9fafb;">
            <p>Sayın <strong>{onaylayan.full_name}</strong>,</p>
            <p>Aşağıdaki talep onayınızı beklemektedir:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Talep Türü:</td>
                    <td style="padding: 8px 0;"><strong>{talep_turu}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Talep Sahibi:</td>
                    <td style="padding: 8px 0;">{talep_sahibi}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Tarih:</td>
                    <td style="padding: 8px 0;">{talep.created_at.strftime('%d.%m.%Y %H:%M') if talep.created_at else '-'}</td>
                </tr>
            </table>
            <div style="text-align: center; margin-top: 25px;">
                <a href="{url_for('onay.index', _external=True)}" 
                   style="background: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Onay Paneline Git
                </a>
            </div>
        </div>
        <div style="padding: 15px; background: #e5e7eb; text-align: center;">
            <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi</p>
        </div>
    </div>
    """
    
    return send_notification(onaylayan.email, subject, html_body)


def notify_onay_sonucu(talep, onaylandi=True, aciklama=None):
    """Onay/Red sonucu - Talep sahibine bildirim"""
    
    calisan = talep.calisan if hasattr(talep, 'calisan') else None
    if not calisan or not calisan.email:
        return False
    
    talep_turu = getattr(talep, 'talep_turu', type(talep).__name__)
    durum = "Onaylandı" if onaylandi else "Reddedildi"
    renk = "#059669" if onaylandi else "#dc2626"
    
    subject = f"Talebiniz {durum}: {talep_turu}"
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, {renk}, {renk}dd); padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Talep {durum}</h2>
        </div>
        <div style="padding: 25px; background: #f9fafb;">
            <p>Sayın <strong>{calisan.full_name}</strong>,</p>
            <p><strong>{talep_turu}</strong> talebiniz <strong style="color: {renk};">{durum.lower()}</strong>.</p>
            {f'<div style="background: #fef3c7; border: 1px solid #f59e0b; padding: 15px; border-radius: 8px; margin: 20px 0;"><strong>Açıklama:</strong> {aciklama}</div>' if aciklama else ''}
            <div style="text-align: center; margin-top: 25px;">
                <a href="{url_for('onay.taleplerim', _external=True)}" 
                   style="background: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Taleplerime Git
                </a>
            </div>
        </div>
        <div style="padding: 15px; background: #e5e7eb; text-align: center;">
            <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi</p>
        </div>
    </div>
    """
    
    return send_notification(calisan.email, subject, html_body)


def notify_masraf_raporu_onay(rapor):
    """Masraf raporu onay bekliyor - Yöneticiye bildirim"""
    from app.models.ik import Calisan
    
    calisan = rapor.calisan
    
    # Yöneticiyi bul, yoksa admin'e fallback
    yonetici = None
    alici_email = None
    alici_ad = "Yetkili"
    
    if calisan.yonetici_id:
        yonetici = Calisan.query.get(calisan.yonetici_id)
        if yonetici and yonetici.email:
            alici_email = yonetici.email
            alici_ad = yonetici.full_name
    
    # Fallback: masraf.admin yetkisi olan kullanıcılar
    if not alici_email:
        from app.models.core import User
        admin_users = User.query.filter(User.is_active == True, User.email.isnot(None)).all()
        admin_emails = [u.email for u in admin_users if u.has_permission('masraf.admin')]
        if admin_emails:
            alici_email = admin_emails
            alici_ad = "Muhasebe/Admin"
            current_app.logger.info(f"Yönetici bulunamadı, admin'e gönderiliyor: {admin_emails}")
        else:
            current_app.logger.warning(f"Çalışan {calisan.id} için yönetici ve admin bulunamadı")
            return False
    
    subject = f"Masraf Raporu Onayı - {calisan.full_name} ({rapor.donem_text})"
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #d97706, #f59e0b); padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Masraf Raporu Onayı Bekliyor</h2>
        </div>
        <div style="padding: 25px; background: #f9fafb;">
            <p>Sayın <strong>{alici_ad}</strong>,</p>
            <p><strong>{calisan.full_name}</strong> tarafından oluşturulan masraf raporu onayınızı beklemektedir.</p>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr><td style="padding: 8px; color: #6b7280;">Dönem:</td><td style="padding: 8px;"><strong>{rapor.donem_text}</strong></td></tr>
                <tr><td style="padding: 8px; color: #6b7280;">Masraf Sayısı:</td><td style="padding: 8px;"><strong>{len(rapor.masraflar)} adet</strong></td></tr>
                <tr><td style="padding: 8px; color: #6b7280;">Toplam:</td><td style="padding: 8px;"><strong>₺{rapor.toplam_masraf:,.2f}</strong></td></tr>
                <tr><td style="padding: 8px; color: #6b7280;">Net Ödeme:</td><td style="padding: 8px;"><strong style="color: #059669;">₺{rapor.net_odeme:,.2f}</strong></td></tr>
            </table>
            <div style="text-align: center; margin-top: 25px;">
                <a href="{url_for('masraf.rapor_detay', id=rapor.id, _external=True)}" 
                   style="background: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px;">Raporu İncele</a>
            </div>
        </div>
    </div>
    """
    
    return send_notification(alici_email, subject, html_body)


def notify_masraf_raporu_muhasebe(rapor):
    """Onaylanan masraf raporu - Muhasebeye bildirim"""
    from app.models.core import User
    
    calisan = rapor.calisan
    
    muhasebe_emails = []
    users = User.query.filter(User.is_active == True, User.email.isnot(None)).all()
    for u in users:
        if u.has_permission('masraf.admin'):
            muhasebe_emails.append(u.email)
    
    if not muhasebe_emails:
        current_app.logger.warning("Muhasebe yetkili kullanıcı bulunamadı")
        return False
    
    subject = f"Masraf Raporu Onaylandı - {calisan.full_name} ({rapor.donem_text})"
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #059669, #10b981); padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Masraf Raporu Onaylandı</h2>
        </div>
        <div style="padding: 25px; background: #f9fafb;">
            <p>Aşağıdaki masraf raporu onaylanmıştır:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr><td style="padding: 8px; color: #6b7280;">Çalışan:</td><td style="padding: 8px;"><strong>{calisan.full_name}</strong></td></tr>
                <tr><td style="padding: 8px; color: #6b7280;">Departman:</td><td style="padding: 8px;">{calisan.departman.ad if calisan.departman else '-'}</td></tr>
                <tr><td style="padding: 8px; color: #6b7280;">Dönem:</td><td style="padding: 8px;"><strong>{rapor.donem_text}</strong></td></tr>
                <tr><td style="padding: 8px; color: #6b7280;">Net Ödeme:</td><td style="padding: 8px;"><strong style="color: #059669; font-size: 18px;">₺{rapor.net_odeme:,.2f}</strong></td></tr>
            </table>
            <div style="text-align: center; margin-top: 25px;">
                <a href="{url_for('masraf.rapor_detay', id=rapor.id, _external=True)}" 
                   style="background: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px;">Raporu Görüntüle</a>
            </div>
        </div>
    </div>
    """
    
    return send_notification(muhasebe_emails, subject, html_body)


def notify_masraf_raporu_sonuc(rapor, onaylandi=True, aciklama=None):
    """Masraf raporu sonucu - Çalışana bildirim"""
    
    calisan = rapor.calisan
    if not calisan.email:
        return False
    
    durum = "Onaylandı" if onaylandi else "Reddedildi"
    renk = "#059669" if onaylandi else "#dc2626"
    
    subject = f"Masraf Raporunuz {durum} - {rapor.donem_text}"
    
    aciklama_html = f'<div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;"><strong>Not:</strong> {aciklama}</div>' if aciklama else ''
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: {renk}; padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Masraf Raporu {durum}</h2>
        </div>
        <div style="padding: 25px; background: #f9fafb;">
            <p>Sayın <strong>{calisan.full_name}</strong>,</p>
            <p><strong>{rapor.donem_text}</strong> dönemi masraf raporunuz <strong style="color: {renk};">{durum.lower()}</strong>.</p>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr><td style="padding: 8px; color: #6b7280;">Toplam Masraf:</td><td style="padding: 8px;"><strong>₺{rapor.toplam_masraf:,.2f}</strong></td></tr>
                <tr><td style="padding: 8px; color: #6b7280;">Net Ödeme:</td><td style="padding: 8px;"><strong style="color: #059669;">₺{rapor.net_odeme:,.2f}</strong></td></tr>
            </table>
            {aciklama_html}
        </div>
    </div>
    """

    return send_notification(calisan.email, subject, html_body)


# ============================================================
# İŞE GİRİŞ / ÇIKIŞ / BAŞVURU / SÖZLEŞME - BildirimSablonu tabanli
# Alici listeleri ve icerikler artik DB'de (bildirim_sablonlari) tutulur.
# Yonetim: /ayarlar/bildirim-sablonlari
# ============================================================


def notify_sgk_giris_talebi(aday):
    """SGK giriş talebi - bordro/muhasebe ekibine bildirim (sablon: SGK_GIRIS_TALEBI)"""
    proje_adi = '-'
    pozisyon_adi = '-'
    lokasyon = '-'
    proje_id = None
    if aday.kadro:
        pozisyon_adi = aday.kadro.pozisyon_adi or '-'
        if aday.kadro.proje:
            proje_adi = aday.kadro.proje.ad
            proje_id = aday.kadro.proje.id
        if aday.kadro.il:
            lokasyon = aday.kadro.il

    try:
        aday_url = url_for('ik.aday_detay', id=aday.id, _external=True)
    except Exception:
        aday_url = '#'

    degiskenler = {
        'ad_soyad': aday.full_name,
        'tc_kimlik': aday.tc_kimlik or '-',
        'planlanan_baslangic': aday.planlanan_baslangic.strftime('%d.%m.%Y') if aday.planlanan_baslangic else '-',
        'proje': proje_adi,
        'pozisyon': pozisyon_adi,
        'lokasyon': lokasyon,
        'telefon': aday.telefon or '-',
        'email': aday.email or '-',
        'aday_url': aday_url,
    }
    return send_bildirim('SGK_GIRIS_TALEBI', degiskenler, proje_id=proje_id)


def notify_ise_giris(calisan):
    """Ise giris bildirimi - sablonu ISE_GIRIS"""
    print(f">>> NOTIFY_ISE_GIRIS TETIKLENDI: {calisan.ad} {calisan.soyad} (id={calisan.id})", flush=True)

    proje_adi = '-'
    pozisyon_adi = '-'
    lokasyon = '-'
    proje_id = None
    if calisan.kadro_id:
        from app.models.proje import HedefKadro
        kadro = HedefKadro.query.get(calisan.kadro_id)
        if kadro:
            pozisyon_adi = kadro.pozisyon_adi or '-'
            if kadro.proje:
                proje_adi = kadro.proje.ad
                proje_id = kadro.proje.id
            if kadro.il:
                lokasyon = kadro.il
            elif hasattr(kadro, 'il_obj') and kadro.il_obj:
                lokasyon = kadro.il_obj.ad

    if calisan.pozisyon and pozisyon_adi == '-':
        pozisyon_adi = calisan.pozisyon.ad
    if calisan.il and lokasyon == '-':
        lokasyon = calisan.il

    sgk_sube = '-'
    sgk_no = '-'
    if calisan.sgk_dosya_id:
        from app.models.sirket import SgkDosya
        sgk = SgkDosya.query.get(calisan.sgk_dosya_id)
        if sgk:
            sgk_sube = sgk.ad or sgk.dosya_no
            sgk_no = sgk.dosya_no

    yonetici_adi = '-'
    if calisan.yonetici_id:
        from app.models.ik import Calisan as CalisanModel
        yon = CalisanModel.query.get(calisan.yonetici_id)
        if yon:
            yonetici_adi = f"{yon.ad} {yon.soyad}"

    degiskenler = {
        'ad_soyad': f"{calisan.ad} {calisan.soyad}",
        'tc_kimlik': calisan.tc_kimlik or '-',
        'ise_baslama': calisan.ise_baslama.strftime('%d.%m.%Y') if calisan.ise_baslama else '-',
        'proje': proje_adi,
        'pozisyon': pozisyon_adi,
        'lokasyon': lokasyon,
        'sgk_sube': sgk_sube,
        'sgk_no': sgk_no,
        'yonetici': yonetici_adi,
        'telefon': calisan.telefon or '-',
        'email': calisan.email or '-',
    }
    return send_bildirim('ISE_GIRIS', degiskenler, proje_id=proje_id)


def notify_isten_cikis(calisan, cikis_tarihi, cikis_nedeni, zimmet_teslim=None,
                       sgk_cikis_kodu=None, liste_durumu=None):
    """Isten cikis bildirimi - sablonu ISTEN_CIKIS

    Args:
        sgk_cikis_kodu: SgkCikisKodu instance veya None
        liste_durumu: ListeDurumu enum veya string veya None
    """
    proje_adi = '-'
    pozisyon_adi = '-'
    proje_id = None
    if calisan.kadro_id:
        from app.models.proje import HedefKadro
        kadro = HedefKadro.query.get(calisan.kadro_id)
        if kadro:
            pozisyon_adi = kadro.pozisyon_adi or '-'
            if kadro.proje:
                proje_adi = kadro.proje.ad
                proje_id = kadro.proje.id

    if calisan.pozisyon and pozisyon_adi == '-':
        pozisyon_adi = calisan.pozisyon.ad

    zimmet_durumu = '-'
    if zimmet_teslim is True:
        zimmet_durumu = 'Teslim edildi'
    elif zimmet_teslim is False:
        zimmet_durumu = 'Teslim edilmedi'

    sgk_kod_str = '-'
    sgk_aciklama_str = '-'
    if sgk_cikis_kodu is not None:
        sgk_kod_str = str(sgk_cikis_kodu.kod)
        sgk_aciklama_str = sgk_cikis_kodu.aciklama or '-'

    liste_etiket = {
        'temiz': 'Temiz',
        'gri_liste': 'Gri Liste',
        'kara_liste': 'Kara Liste',
    }
    liste_durumu_str = '-'
    if liste_durumu is not None:
        val = liste_durumu.value if hasattr(liste_durumu, 'value') else str(liste_durumu)
        liste_durumu_str = liste_etiket.get(val, val)

    degiskenler = {
        'ad_soyad': f"{calisan.ad} {calisan.soyad}",
        'tc_kimlik': calisan.tc_kimlik or '-',
        'cikis_tarihi': cikis_tarihi.strftime('%d.%m.%Y') if cikis_tarihi else '-',
        'cikis_nedeni': cikis_nedeni or '-',
        'proje': proje_adi,
        'pozisyon': pozisyon_adi,
        'telefon': calisan.telefon or '-',
        'zimmet_durumu': zimmet_durumu,
        'sgk_cikis_kodu': sgk_kod_str,
        'sgk_cikis_aciklama': sgk_aciklama_str,
        'liste_durumu': liste_durumu_str,
    }
    return send_bildirim('ISTEN_CIKIS', degiskenler, proje_id=proje_id)


# ============================================================
# SÖZLEŞME BİTİŞ UYARISI
# ============================================================

def notify_sozlesme_dolacak():
    """30 gun icinde sozlesmesi dolacak personeli IK'ya bildir - sablonu SOZLESME_UYARI"""
    from app.models.ik import Calisan
    from app.models.base import CalisanDurumu
    from datetime import date, timedelta

    bugun = date.today()
    otuz_gun = bugun + timedelta(days=30)

    dolacaklar = Calisan.query.filter(
        Calisan.is_deleted == False,
        Calisan.durum == CalisanDurumu.AKTIF,
        Calisan.sozlesme_bitis.isnot(None),
        Calisan.sozlesme_bitis <= otuz_gun,
        Calisan.sozlesme_bitis >= bugun
    ).order_by(Calisan.sozlesme_bitis).all()

    if not dolacaklar:
        return 0

    rows = []
    for c in dolacaklar:
        kalan = (c.sozlesme_bitis - bugun).days
        renk = '#dc2626' if kalan <= 7 else '#d97706' if kalan <= 15 else '#2563eb'
        sablon_adi = c.sozlesme_sablon.ad if c.sozlesme_sablon else '-'
        tip = c.sozlesme_sablon.tip_text if c.sozlesme_sablon else '-'
        rows.append(
            f'<tr>'
            f'<td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{c.full_name}</td>'
            f'<td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{sablon_adi}</td>'
            f'<td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{tip}</td>'
            f'<td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{c.sozlesme_bitis.strftime("%d.%m.%Y")}</td>'
            f'<td style="padding: 10px; border-bottom: 1px solid #e5e7eb; color: {renk}; font-weight: bold;">{kalan} gün</td>'
            f'</tr>'
        )

    degiskenler = {
        'toplam_sayi': len(dolacaklar),
        'liste_html': ''.join(rows),
    }
    send_bildirim('SOZLESME_UYARI', degiskenler)
    return len(dolacaklar)
