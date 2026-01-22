# -*- coding: utf-8 -*-
"""
TG Portal - Mesajlasma Routes
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from app import db, csrf
from app.models.mesaj import Mesaj, MesajBildirimi
from app.models.core import User

mesaj_bp = Blueprint('mesaj', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@mesaj_bp.route('/')
@login_required
def index():
    """Gelen kutusu"""
    sayfa = request.args.get('sayfa', 1, type=int)

    mesajlar = Mesaj.query.filter(
        Mesaj.alici_id == current_user.id,
        Mesaj.is_deleted == False,
        Mesaj.parent_id == None
    ).order_by(Mesaj.created_at.desc()).paginate(page=sayfa, per_page=20)

    okunmamis_sayisi = Mesaj.query.filter(
        Mesaj.alici_id == current_user.id,
        Mesaj.is_deleted == False,
        Mesaj.okundu == False
    ).count()

    return render_template('mesaj/index.html',
                          mesajlar=mesajlar,
                          okunmamis_sayisi=okunmamis_sayisi,
                          aktif_sekme='gelen')


@mesaj_bp.route('/gonderilenler')
@login_required
def gonderilenler():
    """Gonderilen mesajlar"""
    sayfa = request.args.get('sayfa', 1, type=int)

    mesajlar = Mesaj.query.filter(
        Mesaj.gonderen_id == current_user.id,
        Mesaj.is_deleted == False,
        Mesaj.parent_id == None
    ).order_by(Mesaj.created_at.desc()).paginate(page=sayfa, per_page=20)

    return render_template('mesaj/index.html',
                          mesajlar=mesajlar,
                          aktif_sekme='gonderilen')


@mesaj_bp.route('/yeni', methods=['GET', 'POST'])
@login_required
def yeni():
    """Yeni mesaj olustur"""
    if request.method == 'POST':
        alici_id = request.form.get('alici_id', type=int)
        konu = request.form.get('konu', '').strip()
        icerik = request.form.get('icerik', '').strip()

        if not alici_id or not icerik:
            flash('Alici ve mesaj icerigi zorunludur.', 'danger')
            return redirect(url_for('mesaj.yeni'))

        mesaj = Mesaj(
            gonderen_id=current_user.id,
            alici_id=alici_id,
            konu=konu or '(Konusuz)',
            icerik=icerik
        )

        # Dosya eki
        if 'dosya' in request.files:
            dosya = request.files['dosya']
            if dosya and dosya.filename and allowed_file(dosya.filename):
                filename = secure_filename(dosya.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename

                upload_path = os.path.join('/app/uploads/mesajlar', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                dosya.save(upload_path)

                mesaj.dosya_adi = dosya.filename
                mesaj.dosya_yolu = f'mesajlar/{filename}'

        db.session.add(mesaj)

        # Bildirim olustur
        bildirim = MesajBildirimi(user_id=alici_id, mesaj=mesaj)
        db.session.add(bildirim)

        db.session.commit()

        flash('Mesaj gonderildi.', 'success')
        return redirect(url_for('mesaj.index'))

    alici_id = request.args.get('alici')
    kullanicilar = User.query.filter(
        User.is_deleted == False,
        User.is_active == True,
        User.id != current_user.id
    ).order_by(User.ad).all()

    return render_template('mesaj/yeni.html', kullanicilar=kullanicilar, secili_alici=alici_id)


@mesaj_bp.route('/<int:id>')
@login_required
def detay(id):
    """Mesaj detayi"""
    mesaj = Mesaj.query.get_or_404(id)

    # Yetki kontrolu
    if mesaj.gonderen_id != current_user.id and mesaj.alici_id != current_user.id:
        flash('Bu mesaji goruntuleme yetkiniz yok.', 'danger')
        return redirect(url_for('mesaj.index'))

    # Okundu isaretle
    if mesaj.alici_id == current_user.id and not mesaj.okundu:
        mesaj.okundu_isaretle()
        db.session.commit()

    # Yanitlari da okundu isaretle
    for yanit in mesaj.yanitlar:
        if yanit.alici_id == current_user.id and not yanit.okundu:
            yanit.okundu_isaretle()
    db.session.commit()

    return render_template('mesaj/detay.html', mesaj=mesaj)


@mesaj_bp.route('/<int:id>/yanitla', methods=['POST'])
@csrf.exempt
@login_required
def yanitla(id):
    """Mesaja yanit ver"""
    parent = Mesaj.query.get_or_404(id)

    # Yetki kontrolu
    if parent.gonderen_id != current_user.id and parent.alici_id != current_user.id:
        flash('Bu mesaja yanit verme yetkiniz yok.', 'danger')
        return redirect(url_for('mesaj.index'))

    icerik = request.form.get('icerik', '').strip()
    if not icerik:
        flash('Yanit icerigi bos olamaz.', 'danger')
        return redirect(url_for('mesaj.detay', id=id))

    # Alici: eger ben gonderdim karsi tarafa, karsi taraf gonderdiyse bana
    if parent.gonderen_id == current_user.id:
        alici_id = parent.alici_id
    else:
        alici_id = parent.gonderen_id

    yanit = Mesaj(
        gonderen_id=current_user.id,
        alici_id=alici_id,
        konu=f'Re: {parent.konu}',
        icerik=icerik,
        parent_id=parent.id
    )

    db.session.add(yanit)

    # Bildirim
    bildirim = MesajBildirimi(user_id=alici_id, mesaj=yanit)
    db.session.add(bildirim)

    db.session.commit()

    flash('Yanit gonderildi.', 'success')
    return redirect(url_for('mesaj.detay', id=id))


@mesaj_bp.route('/<int:id>/sil', methods=['POST'])
@csrf.exempt
@login_required
def sil(id):
    """Mesaji sil"""
    mesaj = Mesaj.query.get_or_404(id)

    if mesaj.gonderen_id != current_user.id and mesaj.alici_id != current_user.id:
        flash('Bu mesaji silme yetkiniz yok.', 'danger')
        return redirect(url_for('mesaj.index'))

    mesaj.is_deleted = True
    mesaj.deleted_at = datetime.now()
    mesaj.deleted_by = current_user.id
    db.session.commit()

    flash('Mesaj silindi.', 'success')
    return redirect(url_for('mesaj.index'))


@mesaj_bp.route('/api/okunmamis')
@login_required
def api_okunmamis():
    """Okunmamis mesaj sayisi (AJAX)"""
    sayi = Mesaj.query.filter(
        Mesaj.alici_id == current_user.id,
        Mesaj.is_deleted == False,
        Mesaj.okundu == False
    ).count()
    return jsonify({'sayi': sayi})


@mesaj_bp.route('/api/bildirimler')
@login_required
def api_bildirimler():
    """Son bildirimler (AJAX)"""
    bildirimler = MesajBildirimi.query.filter(
        MesajBildirimi.user_id == current_user.id,
        MesajBildirimi.goruldu == False
    ).order_by(MesajBildirimi.created_at.desc()).limit(5).all()

    sonuc = []
    for b in bildirimler:
        sonuc.append({
            'id': b.id,
            'mesaj_id': b.mesaj_id,
            'gonderen': b.mesaj.gonderen.ad_soyad,
            'konu': b.mesaj.konu,
            'ozet': b.mesaj.ozet,
            'tarih': b.created_at.strftime('%d.%m.%Y %H:%M')
        })

    return jsonify(sonuc)
