# -*- coding: utf-8 -*-
"""
TG Portal - Takvim Routes
"""
from datetime import datetime, timedelta
from calendar import monthrange
import os
import msal
import requests as http_requests
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app import db, csrf
from app.models.takvim import Etkinlik, EtkinlikKatilimci, OutlookEntegrasyon
from app.models.core import User
from app.models.todo import Gorev
from app.models.egitim import Egitim

takvim_bp = Blueprint('takvim', __name__)

GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
SCOPES = ['https://graph.microsoft.com/Calendars.ReadWrite', 'https://graph.microsoft.com/User.Read']


def get_msal_app():
    return msal.ConfidentialClientApplication(
        os.environ.get('OUTLOOK_CLIENT_ID'),
        authority=f"https://login.microsoftonline.com/{os.environ.get('OUTLOOK_TENANT_ID', 'common')}",
        client_credential=os.environ.get('OUTLOOK_CLIENT_SECRET')
    )


def get_outlook_token(user_id):
    entegrasyon = OutlookEntegrasyon.query.filter_by(user_id=user_id).first()
    if not entegrasyon or not entegrasyon.refresh_token:
        return None
    if not entegrasyon.token_gecerli_mi:
        msal_app = get_msal_app()
        result = msal_app.acquire_token_by_refresh_token(entegrasyon.refresh_token, scopes=SCOPES)
        if 'access_token' in result:
            entegrasyon.access_token = result['access_token']
            entegrasyon.refresh_token = result.get('refresh_token', entegrasyon.refresh_token)
            entegrasyon.token_expires = datetime.now() + timedelta(seconds=result.get('expires_in', 3600))
            db.session.commit()
        else:
            return None
    return entegrasyon.access_token


@takvim_bp.route('/')
@login_required
def index():
    yil = request.args.get('yil', datetime.now().year, type=int)
    ay = request.args.get('ay', datetime.now().month, type=int)
    ay_basi = datetime(yil, ay, 1)
    _, son_gun = monthrange(yil, ay)
    ay_sonu = datetime(yil, ay, son_gun, 23, 59, 59)

    etkinlikler = Etkinlik.query.filter(
        Etkinlik.is_deleted == False,
        Etkinlik.olusturan_id == current_user.id,
        Etkinlik.baslangic <= ay_sonu,
        db.or_(Etkinlik.bitis >= ay_basi, Etkinlik.bitis == None)
    ).order_by(Etkinlik.baslangic).all()

    gorevler = Gorev.query.filter(
        Gorev.is_deleted == False,
        Gorev.bitis_tarihi != None,
        Gorev.bitis_tarihi >= ay_basi,
        Gorev.bitis_tarihi <= ay_sonu,
        db.or_(Gorev.olusturan_id == current_user.id, Gorev.atanan_id == current_user.id)
    ).all()

    egitimler = Egitim.query.filter(
        Egitim.is_deleted == False,
        Egitim.baslangic_tarihi >= ay_basi,
        Egitim.baslangic_tarihi <= ay_sonu
    ).all()

    onceki_yil, onceki_ay = (yil - 1, 12) if ay == 1 else (yil, ay - 1)
    sonraki_yil, sonraki_ay = (yil + 1, 1) if ay == 12 else (yil, ay + 1)

    return render_template('takvim/index.html',
                          etkinlikler=etkinlikler, gorevler=gorevler, egitimler=egitimler,
                          yil=yil, ay=ay, onceki_yil=onceki_yil, onceki_ay=onceki_ay,
                          sonraki_yil=sonraki_yil, sonraki_ay=sonraki_ay, bugun=datetime.now())


@takvim_bp.route('/etkinlik/ekle', methods=['GET', 'POST'])
@login_required
def etkinlik_ekle():
    if request.method == 'POST':
        baslangic_tarih = request.form.get('baslangic_tarih')
        baslangic_saat = request.form.get('baslangic_saat', '09:00')
        tum_gun = request.form.get('tum_gun') == 'on'

        if tum_gun:
            baslangic = datetime.strptime(baslangic_tarih, '%Y-%m-%d')
            bitis = baslangic + timedelta(hours=23, minutes=59)
        else:
            baslangic = datetime.strptime(f"{baslangic_tarih} {baslangic_saat}", '%Y-%m-%d %H:%M')
            bitis_tarih = request.form.get('bitis_tarih') or baslangic_tarih
            bitis_saat = request.form.get('bitis_saat', '10:00')
            bitis = datetime.strptime(f"{bitis_tarih} {bitis_saat}", '%Y-%m-%d %H:%M')

        etkinlik = Etkinlik(
            baslik=request.form.get('baslik'),
            aciklama=request.form.get('aciklama'),
            konum=request.form.get('konum'),
            baslangic=baslangic, bitis=bitis, tum_gun=tum_gun,
            etkinlik_tipi=request.form.get('etkinlik_tipi', 'genel'),
            renk=request.form.get('renk', '#6366f1'),
            hatirlatma=request.form.get('hatirlatma', 15, type=int),
            olusturan_id=current_user.id
        )
        db.session.add(etkinlik)
        db.session.commit()

        for user_id in request.form.getlist('katilimcilar'):
            db.session.add(EtkinlikKatilimci(etkinlik_id=etkinlik.id, user_id=int(user_id), durum='bekliyor'))
        db.session.commit()

        flash('Etkinlik olusturuldu.', 'success')
        return redirect(url_for('takvim.index'))

    tarih = request.args.get('tarih', datetime.now().strftime('%Y-%m-%d'))
    saat = request.args.get('saat', '09:00')
    kullanicilar = User.query.filter_by(is_deleted=False, is_active=True).order_by(User.ad).all()
    return render_template('takvim/etkinlik_form.html', etkinlik=None, tarih=tarih, saat=saat, kullanicilar=kullanicilar)


@takvim_bp.route('/etkinlik/<int:id>')
@login_required
def etkinlik_detay(id):
    etkinlik = Etkinlik.query.get_or_404(id)
    return render_template('takvim/etkinlik_detay.html', etkinlik=etkinlik)


@takvim_bp.route('/etkinlik/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
def etkinlik_duzenle(id):
    etkinlik = Etkinlik.query.get_or_404(id)
    if etkinlik.olusturan_id != current_user.id:
        flash('Bu etkinligi duzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('takvim.index'))

    if request.method == 'POST':
        etkinlik.baslik = request.form.get('baslik')
        etkinlik.aciklama = request.form.get('aciklama')
        etkinlik.konum = request.form.get('konum')
        etkinlik.etkinlik_tipi = request.form.get('etkinlik_tipi', 'genel')
        etkinlik.renk = request.form.get('renk', '#6366f1')
        etkinlik.hatirlatma = request.form.get('hatirlatma', 15, type=int)

        baslangic_tarih = request.form.get('baslangic_tarih')
        baslangic_saat = request.form.get('baslangic_saat', '09:00')
        tum_gun = request.form.get('tum_gun') == 'on'
        etkinlik.tum_gun = tum_gun

        if tum_gun:
            etkinlik.baslangic = datetime.strptime(baslangic_tarih, '%Y-%m-%d')
            etkinlik.bitis = etkinlik.baslangic + timedelta(hours=23, minutes=59)
        else:
            etkinlik.baslangic = datetime.strptime(f"{baslangic_tarih} {baslangic_saat}", '%Y-%m-%d %H:%M')
            bitis_tarih = request.form.get('bitis_tarih') or baslangic_tarih
            bitis_saat = request.form.get('bitis_saat', '10:00')
            etkinlik.bitis = datetime.strptime(f"{bitis_tarih} {bitis_saat}", '%Y-%m-%d %H:%M')

        db.session.commit()
        flash('Etkinlik guncellendi.', 'success')
        return redirect(url_for('takvim.etkinlik_detay', id=id))

    kullanicilar = User.query.filter_by(is_deleted=False, is_active=True).order_by(User.ad).all()
    return render_template('takvim/etkinlik_form.html', etkinlik=etkinlik, kullanicilar=kullanicilar)


@takvim_bp.route('/etkinlik/<int:id>/sil', methods=['POST'])
@csrf.exempt
@login_required
def etkinlik_sil(id):
    etkinlik = Etkinlik.query.get_or_404(id)
    if etkinlik.olusturan_id != current_user.id:
        flash('Bu etkinligi silme yetkiniz yok.', 'danger')
        return redirect(url_for('takvim.index'))

    etkinlik.is_deleted = True
    etkinlik.deleted_at = datetime.now()
    etkinlik.deleted_by = current_user.id
    db.session.commit()
    flash('Etkinlik silindi.', 'success')
    return redirect(url_for('takvim.index'))


@takvim_bp.route('/api/etkinlikler')
@login_required
def api_etkinlikler():
    start = request.args.get('start')
    end = request.args.get('end')

    start_date = datetime.fromisoformat(start.replace('Z', '+00:00')).replace(tzinfo=None) if start else datetime.now() - timedelta(days=30)
    end_date = datetime.fromisoformat(end.replace('Z', '+00:00')).replace(tzinfo=None) if end else datetime.now() + timedelta(days=30)

    etkinlikler = Etkinlik.query.filter(
        Etkinlik.is_deleted == False, Etkinlik.olusturan_id == current_user.id,
        Etkinlik.baslangic <= end_date, db.or_(Etkinlik.bitis >= start_date, Etkinlik.bitis == None)
    ).all()

    events = []
    for e in etkinlikler:
        events.append({
            'id': f'etkinlik_{e.id}', 'title': e.baslik, 'start': e.baslangic.isoformat(),
            'end': e.bitis.isoformat() if e.bitis else None, 'allDay': e.tum_gun, 'color': e.renk,
            'url': url_for('takvim.etkinlik_detay', id=e.id),
            'extendedProps': {'type': 'etkinlik', 'tip': e.etkinlik_tipi, 'konum': e.konum}
        })

    gorevler = Gorev.query.filter(
        Gorev.is_deleted == False, Gorev.bitis_tarihi != None,
        Gorev.bitis_tarihi >= start_date, Gorev.bitis_tarihi <= end_date, Gorev.durum != 'tamamlandi',
        db.or_(Gorev.olusturan_id == current_user.id, Gorev.atanan_id == current_user.id)
    ).all()

    oncelik_renk = {'acil': '#ef4444', 'yuksek': '#f97316', 'orta': '#eab308', 'dusuk': '#22c55e'}
    for g in gorevler:
        events.append({
            'id': f'gorev_{g.id}', 'title': f'📋 {g.baslik}', 'start': g.bitis_tarihi.isoformat(),
            'allDay': True, 'color': oncelik_renk.get(g.oncelik, '#6366f1'),
            'url': url_for('todo.detay', id=g.id), 'extendedProps': {'type': 'gorev', 'oncelik': g.oncelik}
        })

    egitimler = Egitim.query.filter(
        Egitim.is_deleted == False, Egitim.baslangic_tarihi >= start_date, Egitim.baslangic_tarihi <= end_date
    ).all()

    for eg in egitimler:
        events.append({
            'id': f'egitim_{eg.id}', 'title': f'🎓 {eg.baslik}', 'start': eg.baslangic_tarihi.isoformat(),
            'end': eg.bitis_tarihi.isoformat() if eg.bitis_tarihi else None, 'color': '#06b6d4',
            'url': url_for('egitim.detay', id=eg.id), 'extendedProps': {'type': 'egitim'}
        })

    return jsonify(events)


# ==================== OUTLOOK ENTEGRASYONU ====================

@takvim_bp.route('/outlook/baglanti')
@login_required
def outlook_baglanti():
    entegrasyon = OutlookEntegrasyon.query.filter_by(user_id=current_user.id).first()
    return render_template('takvim/outlook_baglanti.html', entegrasyon=entegrasyon)


@takvim_bp.route('/outlook/baglan')
@login_required
def outlook_baglan():
    msal_app = get_msal_app()
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=os.environ.get('OUTLOOK_REDIRECT_URI'),
        state=str(current_user.id)
    )
    return redirect(auth_url)


@takvim_bp.route('/outlook/callback')
@login_required
def outlook_callback():
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        flash(f'Outlook baglanti hatasi: {error}', 'danger')
        return redirect(url_for('takvim.outlook_baglanti'))

    if not code:
        flash('Yetkilendirme kodu alinamadi.', 'danger')
        return redirect(url_for('takvim.outlook_baglanti'))

    msal_app = get_msal_app()
    result = msal_app.acquire_token_by_authorization_code(code, scopes=SCOPES, redirect_uri=os.environ.get('OUTLOOK_REDIRECT_URI'))

    if 'access_token' not in result:
        flash(f'Token alinamadi: {result.get("error_description", "Bilinmeyen hata")}', 'danger')
        return redirect(url_for('takvim.outlook_baglanti'))

    headers = {'Authorization': f'Bearer {result["access_token"]}'}
    user_info = http_requests.get(f'{GRAPH_API_ENDPOINT}/me', headers=headers).json()

    entegrasyon = OutlookEntegrasyon.query.filter_by(user_id=current_user.id).first()
    if not entegrasyon:
        entegrasyon = OutlookEntegrasyon(user_id=current_user.id)
        db.session.add(entegrasyon)

    entegrasyon.access_token = result['access_token']
    entegrasyon.refresh_token = result.get('refresh_token')
    entegrasyon.token_expires = datetime.now() + timedelta(seconds=result.get('expires_in', 3600))
    entegrasyon.outlook_email = user_info.get('mail') or user_info.get('userPrincipalName')
    entegrasyon.outlook_name = user_info.get('displayName')
    db.session.commit()

    flash(f'Outlook hesabi baglandi: {entegrasyon.outlook_email}', 'success')
    return redirect(url_for('takvim.outlook_baglanti'))


@takvim_bp.route('/outlook/kopar', methods=['POST'])
@csrf.exempt
@login_required
def outlook_kopar():
    entegrasyon = OutlookEntegrasyon.query.filter_by(user_id=current_user.id).first()
    if entegrasyon:
        db.session.delete(entegrasyon)
        db.session.commit()
        flash('Outlook baglantisi kaldirildi.', 'success')
    return redirect(url_for('takvim.outlook_baglanti'))


@takvim_bp.route('/outlook/senkronize', methods=['POST'])
@csrf.exempt
@login_required
def outlook_senkronize():
    token = get_outlook_token(current_user.id)
    if not token:
        flash('Outlook baglantisi gerekli.', 'warning')
        return redirect(url_for('takvim.outlook_baglanti'))

    headers = {'Authorization': f'Bearer {token}'}
    start_date = datetime.now().isoformat() + 'Z'
    end_date = (datetime.now() + timedelta(days=30)).isoformat() + 'Z'

    url = f"{GRAPH_API_ENDPOINT}/me/calendarview?startDateTime={start_date}&endDateTime={end_date}"
    response = http_requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Outlook API Hatasi: {response.status_code} - {response.text}")
        flash(f'Outlook etkinlikleri alinamadi: {response.status_code}', 'danger')
        return redirect(url_for('takvim.outlook_baglanti'))

    outlook_events = response.json().get('value', [])
    imported_count = 0

    for event in outlook_events:
        existing = Etkinlik.query.filter_by(outlook_event_id=event['id'], olusturan_id=current_user.id).first()
        if not existing:
            start = event.get('start', {})
            end = event.get('end', {})
            baslangic = datetime.fromisoformat(start['dateTime'].replace('Z', '')) if start.get('dateTime') else datetime.now()
            bitis = datetime.fromisoformat(end['dateTime'].replace('Z', '')) if end.get('dateTime') else baslangic + timedelta(hours=1)

            etkinlik = Etkinlik(
                baslik=event.get('subject', 'Outlook Etkinligi'),
                aciklama=event.get('bodyPreview', ''),
                konum=event.get('location', {}).get('displayName', ''),
                baslangic=baslangic, bitis=bitis,
                tum_gun=event.get('isAllDay', False),
                etkinlik_tipi='outlook', renk='#0078d4',
                olusturan_id=current_user.id,
                outlook_event_id=event['id']
            )
            db.session.add(etkinlik)
            imported_count += 1

    entegrasyon = OutlookEntegrasyon.query.filter_by(user_id=current_user.id).first()
    entegrasyon.son_senkronizasyon = datetime.now()
    db.session.commit()

    flash(f'{imported_count} yeni etkinlik Outlook tan aktarildi.', 'success')
    return redirect(url_for('takvim.outlook_baglanti'))


@takvim_bp.route('/etkinlik/<int:id>/outlook-gonder', methods=['POST'])
@csrf.exempt
@login_required
def etkinlik_outlook_gonder(id):
    etkinlik = Etkinlik.query.get_or_404(id)
    if etkinlik.olusturan_id != current_user.id:
        flash('Bu etkinligi gonderme yetkiniz yok.', 'danger')
        return redirect(url_for('takvim.etkinlik_detay', id=id))

    token = get_outlook_token(current_user.id)
    if not token:
        flash('Outlook baglantisi gerekli.', 'warning')
        return redirect(url_for('takvim.outlook_baglanti'))

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    event_data = {
        'subject': etkinlik.baslik,
        'body': {'contentType': 'HTML', 'content': etkinlik.aciklama or ''},
        'start': {'dateTime': etkinlik.baslangic.isoformat(), 'timeZone': 'Europe/Istanbul'},
        'end': {'dateTime': (etkinlik.bitis or etkinlik.baslangic + timedelta(hours=1)).isoformat(), 'timeZone': 'Europe/Istanbul'},
        'location': {'displayName': etkinlik.konum or ''},
        'isAllDay': etkinlik.tum_gun
    }

    katilimcilar = [{'emailAddress': {'address': k.user.email, 'name': k.user.ad_soyad}, 'type': 'required'}
                   for k in etkinlik.katilimcilar if k.user.email]
    if katilimcilar:
        event_data['attendees'] = katilimcilar

    if etkinlik.outlook_event_id:
        response = http_requests.patch(f"{GRAPH_API_ENDPOINT}/me/events/{etkinlik.outlook_event_id}", headers=headers, json=event_data)
    else:
        response = http_requests.post(f"{GRAPH_API_ENDPOINT}/me/events", headers=headers, json=event_data)

    if response.status_code in [200, 201]:
        etkinlik.outlook_event_id = response.json()['id']
        db.session.commit()
        flash('Etkinlik Outlook takvimine eklendi.', 'success')
    else:
        flash(f'Outlook hatasi: {response.text}', 'danger')

    return redirect(url_for('takvim.etkinlik_detay', id=id))
