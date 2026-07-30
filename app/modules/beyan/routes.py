# -*- coding: utf-8 -*-
"""
TG Portal - Haftalık Çalışma Beyanı (Public)

Login gerektirmez. Çalışan SMS ile gönderilen linke tıklar, telefonunu
girer, OTP ile doğrular ve haftanın çalışma günlerini (Cuma/Cmt/Pazar)
işaretler. Aynı kişi tekrar girerse mevcut seçimi güncellenir.

OTP altyapısı basvuru modülündeki send_netgsm_sms fonksiyonunu kullanır.
Doğrulama state'i Flask session'da tutulur (kayıt öncesi çalışan bulunmadığı
için OTP bir DB kaydına bağlanamaz).
"""

import random
import re
from datetime import datetime, timedelta

from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, session, current_app)

from app import db
from app.models.base import CalisanDurumu
from app.models.ik import Calisan
from app.models.proje import HedefKadro
from app.models.haftalik_beyan import HaftalikBeyan, BeyanKayit
from app.modules.basvuru.routes import send_netgsm_sms
from app.utils import normalize_telefon

beyan_bp = Blueprint('beyan', __name__)

OTP_GECERLILIK_DK = 5
OTP_MAX_DENEME = 5


def _normalize_tel(tel):
    """Telefonu sadece rakamlara indirger ve son 10 haneyi döndürür."""
    if not tel:
        return ''
    rakam = re.sub(r'\D', '', tel)
    if rakam.startswith('90') and len(rakam) > 10:
        rakam = rakam[2:]
    return rakam[-10:]


def _proje_aktif_calisanlar(proje_id):
    """Projede kadrosu olan aktif çalışanlar."""
    return Calisan.query.join(HedefKadro, Calisan.kadro_id == HedefKadro.id).filter(
        HedefKadro.proje_id == proje_id,
        Calisan.is_deleted == False,
        Calisan.durum == CalisanDurumu.AKTIF
    ).all()


def _calisan_bul(proje_id, telefon):
    """Girilen telefona göre projedeki aktif çalışanı bulur.

    Eşleştirme son 10 hane üzerinden yapılır; DB'de henüz normalize
    edilmemiş kayıtlar da bulunabilsin diye format bağımsızdır.
    """
    hedef = _normalize_tel(telefon)
    if not hedef:
        return None
    for c in _proje_aktif_calisanlar(proje_id):
        if _normalize_tel(c.telefon) == hedef:
            return c
    return None


def _client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)


@beyan_bp.route('/<int:id>', methods=['GET', 'POST'])
def beyan_sayfa(id):
    """Public beyan sayfası: telefon → OTP → gün seçimi."""
    beyan = HaftalikBeyan.query.get_or_404(id)

    if not beyan.aktif:
        return render_template('beyan/kapali.html', beyan=beyan)

    otp_key = f'beyan_otp_{id}'
    calisan_key = f'beyan_calisan_{id}'
    verified_calisan_id = session.get(calisan_key)

    if request.method == 'POST':
        action = request.form.get('action')

        # 1) Doğrulama kodu gönder
        if action == 'send_code':
            telefon_ham = (request.form.get('telefon') or '').strip()
            # "Kodu tekrar gönder" telefon alanı olmadan gelir -> session'daki numarayı kullan
            if not telefon_ham and session.get(otp_key):
                telefon_ham = session[otp_key].get('telefon', '')

            telefon = normalize_telefon(telefon_ham)
            if not telefon:
                flash('Geçerli bir cep telefonu numarası girin. '
                      'Örnek: 05XX XXX XX XX', 'danger')
                return redirect(url_for('beyan.beyan_sayfa', id=id))

            calisan = _calisan_bul(beyan.proje_id, telefon)
            if not calisan:
                flash('Bu telefon numarası bu projedeki aktif çalışanlar '
                      'arasında bulunamadı. Lütfen İK ile iletişime geçin.', 'danger')
                return redirect(url_for('beyan.beyan_sayfa', id=id))

            kod = str(random.randint(100000, 999999))
            session[otp_key] = {
                'telefon': telefon,
                'calisan_id': calisan.id,
                'kod': kod,
                'expires': (datetime.now() + timedelta(minutes=OTP_GECERLILIK_DK)).isoformat(),
                'deneme': 0,
            }
            session.modified = True

            mesaj = (f'Team Guerilla haftalik calisma beyani dogrulama kodunuz: {kod} '
                     f'- Bu kod {OTP_GECERLILIK_DK} dakika gecerlidir.')
            result = send_netgsm_sms(calisan.telefon, mesaj)
            if result.get('success'):
                flash('Doğrulama kodu telefonunuza gönderildi.', 'success')
            else:
                flash(f'SMS gönderilemedi: {result.get("error")}', 'danger')
            return redirect(url_for('beyan.beyan_sayfa', id=id))

        # 2) Doğrulama kodunu kontrol et
        if action == 'verify_code':
            kod = (request.form.get('kod') or '').strip()
            otp = session.get(otp_key)
            if not otp:
                flash('Önce telefonunuza doğrulama kodu gönderin.', 'warning')
                return redirect(url_for('beyan.beyan_sayfa', id=id))

            if datetime.now() > datetime.fromisoformat(otp['expires']):
                session.pop(otp_key, None)
                flash('Doğrulama kodunun süresi doldu. Lütfen tekrar kod isteyin.', 'warning')
                return redirect(url_for('beyan.beyan_sayfa', id=id))

            if otp.get('deneme', 0) >= OTP_MAX_DENEME:
                session.pop(otp_key, None)
                flash('Çok fazla hatalı deneme. Lütfen tekrar kod isteyin.', 'danger')
                return redirect(url_for('beyan.beyan_sayfa', id=id))

            if kod != otp['kod']:
                otp['deneme'] = otp.get('deneme', 0) + 1
                session[otp_key] = otp
                session.modified = True
                kalan = OTP_MAX_DENEME - otp['deneme']
                flash(f'Doğrulama kodu hatalı. Kalan deneme: {kalan}', 'danger')
                return redirect(url_for('beyan.beyan_sayfa', id=id))

            # Başarılı
            session[calisan_key] = otp['calisan_id']
            session.pop(otp_key, None)
            session.modified = True
            flash('Telefonunuz doğrulandı. Lütfen çalışma günlerinizi seçin.', 'success')
            return redirect(url_for('beyan.beyan_sayfa', id=id))

    # GET
    if verified_calisan_id:
        calisan = Calisan.query.get(verified_calisan_id)
        if not calisan:
            session.pop(calisan_key, None)
            return redirect(url_for('beyan.beyan_sayfa', id=id))
        kayit = BeyanKayit.query.filter_by(beyan_id=id, calisan_id=calisan.id).first()
        return render_template('beyan/beyan_form.html', beyan=beyan, asama='gun',
                               calisan=calisan, kayit=kayit)

    # Doğrulama aşaması: OTP gönderildiyse kod ekranı, değilse telefon ekranı
    asama = 'kod' if session.get(otp_key) else 'telefon'
    return render_template('beyan/beyan_form.html', beyan=beyan, asama=asama)


@beyan_bp.route('/<int:id>/kaydet', methods=['POST'])
def beyan_kaydet(id):
    """Doğrulanmış çalışanın gün seçimini kaydeder/günceller."""
    beyan = HaftalikBeyan.query.get_or_404(id)
    if not beyan.aktif:
        return render_template('beyan/kapali.html', beyan=beyan)

    calisan_id = session.get(f'beyan_calisan_{id}')
    if not calisan_id:
        flash('Oturum doğrulaması bulunamadı. Lütfen telefonunuzu tekrar doğrulayın.', 'warning')
        return redirect(url_for('beyan.beyan_sayfa', id=id))

    calisan = Calisan.query.get_or_404(calisan_id)

    cuma = request.form.get('cuma') == 'on'
    cumartesi = request.form.get('cumartesi') == 'on'
    pazar = request.form.get('pazar') == 'on'

    kayit = BeyanKayit.query.filter_by(beyan_id=id, calisan_id=calisan.id).first()
    if not kayit:
        kayit = BeyanKayit(beyan_id=id, calisan_id=calisan.id)
        kayit.generate_token()
        db.session.add(kayit)

    kayit.telefon = normalize_telefon(calisan.telefon) or calisan.telefon
    kayit.ad_soyad = calisan.full_name
    kayit.kadro_adi = calisan.kadro.pozisyon_adi if calisan.kadro else None
    kayit.cuma = cuma
    kayit.cumartesi = cumartesi
    kayit.pazar = pazar
    kayit.kayit_zamani = datetime.now()
    kayit.ip = _client_ip()

    db.session.commit()

    return render_template('beyan/tesekkur.html', beyan=beyan, calisan=calisan, kayit=kayit)
