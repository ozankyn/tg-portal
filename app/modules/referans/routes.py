# -*- coding: utf-8 -*-
"""
TG Portal - Arkadaşını Davet Et / Referans (Public)

Login gerektirmez. Çalışan SMS ile gönderilen proje linkine tıklar,
telefonunu girer, OTP ile doğrular ve tanıdıklarının ad/telefon
bilgilerini bırakır. Aynı çalışan istediği kadar kez giriş yapabilir.

OTP altyapısı ve doğrulama akışı haftalık beyan modülü (app/modules/beyan)
ile aynıdır; doğrulama state'i Flask session'da tutulur.
"""

import random
import re
from datetime import datetime, timedelta

from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, session)

from app import db
from app.models.base import CalisanDurumu
from app.models.ik import Calisan
from app.models.proje import HedefKadro, Il
from app.models.referans import ReferansLink, ReferansKayit
from app.modules.basvuru.routes import send_netgsm_sms
from app.utils import normalize_telefon

referans_bp = Blueprint('referans', __name__)

OTP_GECERLILIK_DK = 5
OTP_MAX_DENEME = 5

# Tek gönderimde alınacak en fazla referans satırı (form kötüye kullanımına karşı)
MAX_REFERANS_SATIR = 20


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
    """Girilen telefona göre projedeki aktif çalışanı bulur (son 10 hane)."""
    hedef = _normalize_tel(telefon)
    if not hedef:
        return None
    for c in _proje_aktif_calisanlar(proje_id):
        if _normalize_tel(c.telefon) == hedef:
            return c
    return None


def _client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)


def _il_listesi():
    """Form datalist'i için il adları; il tablosu boşsa boş liste döner."""
    try:
        return [i.ad for i in Il.query.order_by(Il.ad).all()]
    except Exception:
        db.session.rollback()
        return []


@referans_bp.route('/<token>', methods=['GET', 'POST'])
def referans_sayfa(token):
    """Public referans sayfası: telefon → OTP → arkadaş bilgileri."""
    link = ReferansLink.query.filter_by(token=token).first_or_404()

    if not link.aktif:
        return render_template('referans/kapali.html', link=link)

    otp_key = f'referans_otp_{link.id}'
    calisan_key = f'referans_calisan_{link.id}'
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
                return redirect(url_for('referans.referans_sayfa', token=token))

            calisan = _calisan_bul(link.proje_id, telefon)
            if not calisan:
                flash('Bu telefon numarası bu projedeki aktif çalışanlar '
                      'arasında bulunamadı. Lütfen İK ile iletişime geçin.', 'danger')
                return redirect(url_for('referans.referans_sayfa', token=token))

            kod = str(random.randint(100000, 999999))
            session[otp_key] = {
                'telefon': telefon,
                'calisan_id': calisan.id,
                'kod': kod,
                'expires': (datetime.now() + timedelta(minutes=OTP_GECERLILIK_DK)).isoformat(),
                'deneme': 0,
            }
            session.modified = True

            mesaj = (f'Team Guerilla referans formu dogrulama kodunuz: {kod} '
                     f'- Bu kod {OTP_GECERLILIK_DK} dakika gecerlidir.')
            result = send_netgsm_sms(calisan.telefon, mesaj)
            if result.get('success'):
                flash('Doğrulama kodu telefonunuza gönderildi.', 'success')
            else:
                flash(f'SMS gönderilemedi: {result.get("error")}', 'danger')
            return redirect(url_for('referans.referans_sayfa', token=token))

        # 2) Doğrulama kodunu kontrol et
        if action == 'verify_code':
            kod = (request.form.get('kod') or '').strip()
            otp = session.get(otp_key)
            if not otp:
                flash('Önce telefonunuza doğrulama kodu gönderin.', 'warning')
                return redirect(url_for('referans.referans_sayfa', token=token))

            if datetime.now() > datetime.fromisoformat(otp['expires']):
                session.pop(otp_key, None)
                flash('Doğrulama kodunun süresi doldu. Lütfen tekrar kod isteyin.', 'warning')
                return redirect(url_for('referans.referans_sayfa', token=token))

            if otp.get('deneme', 0) >= OTP_MAX_DENEME:
                session.pop(otp_key, None)
                flash('Çok fazla hatalı deneme. Lütfen tekrar kod isteyin.', 'danger')
                return redirect(url_for('referans.referans_sayfa', token=token))

            if kod != otp['kod']:
                otp['deneme'] = otp.get('deneme', 0) + 1
                session[otp_key] = otp
                session.modified = True
                kalan = OTP_MAX_DENEME - otp['deneme']
                flash(f'Doğrulama kodu hatalı. Kalan deneme: {kalan}', 'danger')
                return redirect(url_for('referans.referans_sayfa', token=token))

            # Başarılı
            session[calisan_key] = otp['calisan_id']
            session.pop(otp_key, None)
            session.modified = True
            return redirect(url_for('referans.referans_sayfa', token=token))

    # GET
    if verified_calisan_id:
        calisan = Calisan.query.get(verified_calisan_id)
        if not calisan:
            session.pop(calisan_key, None)
            return redirect(url_for('referans.referans_sayfa', token=token))
        onceki = ReferansKayit.query.filter_by(
            proje_id=link.proje_id, davet_eden_calisan_id=calisan.id
        ).order_by(ReferansKayit.created_at.desc()).all()
        return render_template('referans/referans_form.html', link=link, asama='form',
                               calisan=calisan, onceki=onceki, iller=_il_listesi())

    # Doğrulama aşaması: OTP gönderildiyse kod ekranı, değilse telefon ekranı
    asama = 'kod' if session.get(otp_key) else 'telefon'
    return render_template('referans/referans_form.html', link=link, asama=asama)


@referans_bp.route('/<token>/kaydet', methods=['POST'])
def referans_kaydet(token):
    """Doğrulanmış çalışanın girdiği referansları kaydeder."""
    link = ReferansLink.query.filter_by(token=token).first_or_404()
    if not link.aktif:
        return render_template('referans/kapali.html', link=link)

    calisan_id = session.get(f'referans_calisan_{link.id}')
    if not calisan_id:
        flash('Oturum doğrulaması bulunamadı. Lütfen telefonunuzu tekrar doğrulayın.', 'warning')
        return redirect(url_for('referans.referans_sayfa', token=token))

    calisan = Calisan.query.get_or_404(calisan_id)

    adlar = request.form.getlist('ad_soyad')[:MAX_REFERANS_SATIR]
    telefonlar = request.form.getlist('telefon')[:MAX_REFERANS_SATIR]
    iller = request.form.getlist('il')[:MAX_REFERANS_SATIR]
    notlar = request.form.getlist('not')[:MAX_REFERANS_SATIR]

    davet_eden_tel = normalize_telefon(calisan.telefon) or calisan.telefon
    kendi_tel = _normalize_tel(calisan.telefon)

    # Aynı projede daha önce kayıtlı numaralar - mükerrer referans sayılmasın
    mevcut_tel = {
        _normalize_tel(r.referans_telefon)
        for r in ReferansKayit.query.filter_by(proje_id=link.proje_id).all()
    }

    eklenen, atlanan, hatali = [], [], 0
    for i, ad in enumerate(adlar):
        ad = (ad or '').strip()
        ham_tel = (telefonlar[i] if i < len(telefonlar) else '') or ''
        ham_tel = ham_tel.strip()

        if not ad and not ham_tel:
            continue  # boş satır

        telefon = normalize_telefon(ham_tel)
        if not ad or not telefon:
            hatali += 1
            continue

        norm = _normalize_tel(telefon)
        if norm == kendi_tel:
            atlanan.append((ad, 'Kendi numaranızı referans olarak ekleyemezsiniz'))
            continue
        if norm in mevcut_tel:
            atlanan.append((ad, 'Bu numara daha önce referans olarak kaydedilmiş'))
            continue

        kayit = ReferansKayit(
            proje_id=link.proje_id,
            davet_eden_calisan_id=calisan.id,
            davet_eden_ad_soyad=calisan.full_name,
            davet_eden_telefon=davet_eden_tel,
            referans_ad_soyad=ad,
            referans_telefon=telefon,
            referans_il=((iller[i] if i < len(iller) else '') or '').strip() or None,
            referans_notu=((notlar[i] if i < len(notlar) else '') or '').strip() or None,
            durum='yeni',
            ip=_client_ip(),
        )
        kayit.generate_token()
        db.session.add(kayit)
        mevcut_tel.add(norm)
        eklenen.append(kayit)

    if not eklenen and not atlanan:
        flash('Kaydedilecek referans bulunamadı. Ad soyad ve telefon alanlarını doldurun.',
              'warning')
        return redirect(url_for('referans.referans_sayfa', token=token))

    db.session.commit()

    return render_template('referans/tesekkur.html', link=link, calisan=calisan,
                           eklenen=eklenen, atlanan=atlanan, hatali=hatali)
