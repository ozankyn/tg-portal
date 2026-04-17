# -*- coding: utf-8 -*-
"""
Bildirim Servisi - Email bildirimleri
"""

from flask import current_app, url_for
from flask_mail import Message
from app import mail, db


def send_notification(to, subject, html_body, text_body=None):
    """Genel bildirim gönderme fonksiyonu"""
    recipients = [to] if isinstance(to, str) else to
    print(f"[Mail] Gönderim başlıyor: to={recipients}, subject={subject}")
    try:
        mail_server = current_app.config.get('MAIL_SERVER')
        if not mail_server:
            print(f"[Mail] MAIL_SERVER yapılandırılmamış, gönderim iptal")
            return False

        print(f"[Mail] SMTP: {mail_server}:{current_app.config.get('MAIL_PORT')}, user={current_app.config.get('MAIL_USERNAME')}")
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            body=text_body
        )
        mail.send(msg)
        print(f"[Mail] Başarıyla gönderildi: {recipients}")
        return True
    except Exception as e:
        print(f"[Mail] HATA: {e}")
        import traceback
        traceback.print_exc()
        return False


def notify_yeni_basvuru(aday):
    """Yeni aday başvurusu - İK'ya bildirim"""
    from app.models.core import User
    
    # İK yetkisi olan kullanıcıları bul
    ik_users = User.query.filter(
        User.is_active == True,
        User.email.isnot(None)
    ).all()
    
    ik_emails = [u.email for u in ik_users if u.has_permission('ik.view')]
    
    if not ik_emails:
        current_app.logger.warning("İK yetkili kullanıcı bulunamadı")
        return False
    
    kadro_bilgi = ""
    if aday.kadro:
        musteri = aday.kadro.proje.musteri.kisa_ad or aday.kadro.proje.musteri.ad
        kadro_bilgi = f"{musteri} - {aday.kadro.pozisyon_adi}"
    
    subject = f"Yeni Başvuru: {aday.full_name}"
    if kadro_bilgi:
        subject += f" ({kadro_bilgi})"
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #059669, #10b981); padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Yeni Aday Başvurusu</h2>
        </div>
        <div style="padding: 25px; background: #f9fafb;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Ad Soyad:</td>
                    <td style="padding: 8px 0;"><strong>{aday.full_name}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Telefon:</td>
                    <td style="padding: 8px 0;">{aday.telefon or '-'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">E-posta:</td>
                    <td style="padding: 8px 0;">{aday.email or '-'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Pozisyon:</td>
                    <td style="padding: 8px 0;">{kadro_bilgi or '-'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Kaynak:</td>
                    <td style="padding: 8px 0;">{aday.kaynak or 'Belirtilmemiş'}</td>
                </tr>
            </table>
            <div style="text-align: center; margin-top: 25px;">
                <a href="{url_for('proje.kadro_detay', id=aday.kadro_id, _external=True) if aday.kadro_id else '#'}" 
                   style="background: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Başvuruyu İncele
                </a>
            </div>
        </div>
        <div style="padding: 15px; background: #e5e7eb; text-align: center;">
            <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi</p>
        </div>
    </div>
    """
    
    return send_notification(ik_emails, subject, html_body)


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
# İŞE GİRİŞ / ÇIKIŞ BİLDİRİMLERİ
# ============================================================

# Departman bildirim adresleri
BILDIRIM_ALICILARI = [
    'muhasebe@teamguerilla.com',
    'filo@teamguerilla.com',
    'egitim@teamguerilla.com',
    'ik@teamguerilla.com',
]


def notify_ise_giris(calisan):
    """İşe giriş bildirimi — Muhasebe, Filo, Eğitim, İK departmanlarına"""

    # Proje bilgisi (kadro üzerinden)
    proje_adi = '-'
    pozisyon_adi = '-'
    lokasyon = '-'
    if calisan.kadro_id:
        from app.models.proje import HedefKadro
        kadro = HedefKadro.query.get(calisan.kadro_id)
        if kadro:
            pozisyon_adi = kadro.pozisyon_adi or '-'
            if kadro.proje:
                proje_adi = kadro.proje.ad
            if kadro.il:
                lokasyon = kadro.il
            elif hasattr(kadro, 'il_obj') and kadro.il_obj:
                lokasyon = kadro.il_obj.ad

    if calisan.pozisyon and pozisyon_adi == '-':
        pozisyon_adi = calisan.pozisyon.ad

    if calisan.il and lokasyon == '-':
        lokasyon = calisan.il

    # SGK bilgisi
    sgk_sube = '-'
    sgk_no = '-'
    if calisan.sgk_dosya_id:
        from app.models.sirket import SgkDosya
        sgk = SgkDosya.query.get(calisan.sgk_dosya_id)
        if sgk:
            sgk_sube = sgk.ad or sgk.dosya_no
            sgk_no = sgk.dosya_no

    # Yönetici
    yonetici_adi = '-'
    if calisan.yonetici_id:
        from app.models.ik import Calisan as CalisanModel
        yon = CalisanModel.query.get(calisan.yonetici_id)
        if yon:
            yonetici_adi = f"{yon.ad} {yon.soyad}"

    ise_baslama = calisan.ise_baslama.strftime('%d.%m.%Y') if calisan.ise_baslama else '-'

    subject = f"İşe Giriş Bildirimi - {calisan.ad} {calisan.soyad} - {ise_baslama}"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #059669, #10b981); padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">İşe Giriş Bildirimi</h2>
        </div>
        <div style="padding: 25px; background: #f9fafb;">
            <p style="margin: 0 0 15px 0; color: #374151;">Aşağıdaki personelin işe giriş kaydı oluşturulmuştur:</p>
            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px 15px; color: #6b7280; width: 200px;">Ad Soyad</td>
                    <td style="padding: 10px 15px;"><strong>{calisan.ad} {calisan.soyad}</strong></td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb; background: #f9fafb;">
                    <td style="padding: 10px 15px; color: #6b7280;">TC Kimlik No</td>
                    <td style="padding: 10px 15px;"><strong>{calisan.tc_kimlik or '-'}</strong></td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px 15px; color: #6b7280;">İş Başı Tarihi</td>
                    <td style="padding: 10px 15px;"><strong style="color: #059669;">{ise_baslama}</strong></td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb; background: #f9fafb;">
                    <td style="padding: 10px 15px; color: #6b7280;">Proje</td>
                    <td style="padding: 10px 15px;">{proje_adi}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px 15px; color: #6b7280;">Pozisyon</td>
                    <td style="padding: 10px 15px;">{pozisyon_adi}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb; background: #f9fafb;">
                    <td style="padding: 10px 15px; color: #6b7280;">Lokasyon</td>
                    <td style="padding: 10px 15px;">{lokasyon}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px 15px; color: #6b7280;">SGK İşyeri Şubesi</td>
                    <td style="padding: 10px 15px;">{sgk_sube}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb; background: #f9fafb;">
                    <td style="padding: 10px 15px; color: #6b7280;">SGK No</td>
                    <td style="padding: 10px 15px;">{sgk_no}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px 15px; color: #6b7280;">Yönetici</td>
                    <td style="padding: 10px 15px;">{yonetici_adi}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb; background: #f9fafb;">
                    <td style="padding: 10px 15px; color: #6b7280;">Telefon</td>
                    <td style="padding: 10px 15px;">{calisan.telefon or '-'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 15px; color: #6b7280;">E-posta</td>
                    <td style="padding: 10px 15px;">{calisan.email or '-'}</td>
                </tr>
            </table>
        </div>
        <div style="padding: 15px; background: #e5e7eb; text-align: center;">
            <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi (Otomatik bildirim)</p>
        </div>
    </div>
    """

    return send_notification(BILDIRIM_ALICILARI, subject, html_body)


def notify_isten_cikis(calisan, cikis_tarihi, cikis_nedeni, zimmet_teslim=None):
    """İşten çıkış bildirimi — Muhasebe, Filo, Eğitim, İK departmanlarına"""

    # Proje bilgisi
    proje_adi = '-'
    pozisyon_adi = '-'
    if calisan.kadro_id:
        from app.models.proje import HedefKadro
        kadro = HedefKadro.query.get(calisan.kadro_id)
        if kadro:
            pozisyon_adi = kadro.pozisyon_adi or '-'
            if kadro.proje:
                proje_adi = kadro.proje.ad

    if calisan.pozisyon and pozisyon_adi == '-':
        pozisyon_adi = calisan.pozisyon.ad

    cikis_str = cikis_tarihi.strftime('%d.%m.%Y') if cikis_tarihi else '-'

    # Zimmet durumu
    zimmet_html = '-'
    if zimmet_teslim is not None:
        zimmet_html = '<span style="color: #059669;">Teslim edildi</span>' if zimmet_teslim else '<span style="color: #dc2626;">Teslim edilmedi</span>'

    subject = f"İşten Çıkış Bildirimi - {calisan.ad} {calisan.soyad} - {cikis_str}"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #dc2626, #ef4444); padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">İşten Çıkış Bildirimi</h2>
        </div>
        <div style="padding: 25px; background: #f9fafb;">
            <p style="margin: 0 0 15px 0; color: #374151;">Aşağıdaki personelin işten çıkış kaydı tamamlanmıştır:</p>
            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px 15px; color: #6b7280; width: 200px;">Ad Soyad</td>
                    <td style="padding: 10px 15px;"><strong>{calisan.ad} {calisan.soyad}</strong></td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb; background: #f9fafb;">
                    <td style="padding: 10px 15px; color: #6b7280;">TC Kimlik No</td>
                    <td style="padding: 10px 15px;"><strong>{calisan.tc_kimlik or '-'}</strong></td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px 15px; color: #6b7280;">Çıkış Tarihi</td>
                    <td style="padding: 10px 15px;"><strong style="color: #dc2626;">{cikis_str}</strong></td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb; background: #f9fafb;">
                    <td style="padding: 10px 15px; color: #6b7280;">Çıkış Nedeni</td>
                    <td style="padding: 10px 15px;">{cikis_nedeni or '-'}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px 15px; color: #6b7280;">Proje</td>
                    <td style="padding: 10px 15px;">{proje_adi}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb; background: #f9fafb;">
                    <td style="padding: 10px 15px; color: #6b7280;">Pozisyon</td>
                    <td style="padding: 10px 15px;">{pozisyon_adi}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px 15px; color: #6b7280;">Telefon</td>
                    <td style="padding: 10px 15px;">{calisan.telefon or '-'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 15px; color: #6b7280;">Zimmet Durumu</td>
                    <td style="padding: 10px 15px;">{zimmet_html}</td>
                </tr>
            </table>
        </div>
        <div style="padding: 15px; background: #e5e7eb; text-align: center;">
            <p style="margin: 0; color: #6b7280; font-size: 12px;">TG Portal - Team Guerilla ERP Sistemi (Otomatik bildirim)</p>
        </div>
    </div>
    """

    return send_notification(BILDIRIM_ALICILARI, subject, html_body)
