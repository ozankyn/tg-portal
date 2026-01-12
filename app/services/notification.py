# -*- coding: utf-8 -*-
"""
Bildirim Servisi - Email bildirimleri
"""

from flask import current_app, url_for
from flask_mail import Message
from app import mail, db


def send_notification(to, subject, html_body, text_body=None):
    """Genel bildirim gönderme fonksiyonu"""
    try:
        if not current_app.config.get('MAIL_SERVER'):
            current_app.logger.warning("Mail sunucusu yapılandırılmamış")
            return False
        
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            html=html_body,
            body=text_body
        )
        mail.send(msg)
        current_app.logger.info(f"Bildirim gönderildi: {to} - {subject}")
        return True
    except Exception as e:
        current_app.logger.error(f"Bildirim hatası: {str(e)}")
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
