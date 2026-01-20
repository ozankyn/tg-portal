# -*- coding: utf-8 -*-
"""
TG Portal - To-Do Routes
Görev yönetimi
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
import json

from app import db
from app.models.todo import Gorev, GorevKategorisi, GorevYorum, GorevLog
from app.models.core import User
from app.models.proje import Proje
from app.utils import permission_required

todo_bp = Blueprint('todo', __name__)


def log_gorev(gorev, aksiyon, detay=None):
    """Görev aktivitesini logla"""
    log = GorevLog(
        gorev_id=gorev.id,
        user_id=current_user.id,
        aksiyon=aksiyon,
        detay=json.dumps(detay) if detay else None
    )
    db.session.add(log)


# ============================================================
# DASHBOARD & LİSTE
# ============================================================

@todo_bp.route('/')
@todo_bp.route('/liste')
@login_required
def liste():
    """Görev listesi - Kişisel ve atanan görevler"""
    durum = request.args.get('durum', '')
    oncelik = request.args.get('oncelik', '')
    kategori_id = request.args.get('kategori', type=int)
    gorunum = request.args.get('gorunum', 'liste')

    query = Gorev.query.filter(
        Gorev.is_deleted == False,
        Gorev.ust_gorev_id == None,
        db.or_(
            Gorev.olusturan_id == current_user.id,
            Gorev.atanan_id == current_user.id
        )
    )

    if durum:
        query = query.filter(Gorev.durum == durum)
    if oncelik:
        query = query.filter(Gorev.oncelik == oncelik)
    if kategori_id:
        query = query.filter(Gorev.kategori_id == kategori_id)

    query = query.order_by(
        db.case(
            (Gorev.oncelik == 'acil', 1),
            (Gorev.oncelik == 'yuksek', 2),
            (Gorev.oncelik == 'orta', 3),
            (Gorev.oncelik == 'dusuk', 4),
        ),
        Gorev.bitis_tarihi.asc().nullslast()
    )

    gorevler = query.all()
    kategoriler = GorevKategorisi.query.filter_by(aktif=True).order_by(GorevKategorisi.sira).all()

    toplam = len(gorevler)
    bekleyen = sum(1 for g in gorevler if g.durum == 'bekliyor')
    devam_eden = sum(1 for g in gorevler if g.durum == 'devam_ediyor')
    tamamlanan = sum(1 for g in gorevler if g.durum == 'tamamlandi')
    geciken = sum(1 for g in gorevler if g.gecikti_mi)

    return render_template('todo/liste.html',
                          gorevler=gorevler,
                          kategoriler=kategoriler,
                          gorunum=gorunum,
                          durum=durum,
                          oncelik=oncelik,
                          kategori_id=kategori_id,
                          toplam=toplam,
                          bekleyen=bekleyen,
                          devam_eden=devam_eden,
                          tamamlanan=tamamlanan,
                          geciken=geciken)


@todo_bp.route('/kanban')
@login_required
def kanban():
    """Kanban görünümü"""
    query = Gorev.query.filter(
        Gorev.is_deleted == False,
        Gorev.ust_gorev_id == None,
        db.or_(
            Gorev.olusturan_id == current_user.id,
            Gorev.atanan_id == current_user.id
        )
    )

    bekleyen = query.filter(Gorev.durum == 'bekliyor').order_by(Gorev.bitis_tarihi.asc().nullslast()).all()
    devam_eden = query.filter(Gorev.durum == 'devam_ediyor').order_by(Gorev.bitis_tarihi.asc().nullslast()).all()
    tamamlanan = query.filter(Gorev.durum == 'tamamlandi').order_by(Gorev.tamamlanma_tarihi.desc()).limit(20).all()

    return render_template('todo/kanban.html',
                          bekleyen=bekleyen,
                          devam_eden=devam_eden,
                          tamamlanan=tamamlanan)


# ============================================================
# GÖREV EKLEME / DÜZENLEME
# ============================================================

@todo_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
def ekle():
    """Yeni görev ekle"""
    if request.method == 'POST':
        gorev = Gorev(
            baslik=request.form.get('baslik'),
            aciklama=request.form.get('aciklama'),
            oncelik=request.form.get('oncelik', 'orta'),
            kategori_id=request.form.get('kategori_id') or None,
            atanan_id=request.form.get('atanan_id') or None,
            proje_id=request.form.get('proje_id') or None,
            olusturan_id=current_user.id,
            durum='bekliyor'
        )

        if request.form.get('bitis_tarihi'):
            gorev.bitis_tarihi = datetime.strptime(request.form.get('bitis_tarihi'), '%Y-%m-%dT%H:%M')

        if request.form.get('hatirlatma_tarihi'):
            gorev.hatirlatma_tarihi = datetime.strptime(request.form.get('hatirlatma_tarihi'), '%Y-%m-%dT%H:%M')

        etiketler = request.form.get('etiketler', '').strip()
        if etiketler:
            gorev.etiketler = json.dumps([e.strip() for e in etiketler.split(',') if e.strip()])

        db.session.add(gorev)
        db.session.commit()

        log_gorev(gorev, 'olusturuldu')
        db.session.commit()

        flash('Görev oluşturuldu.', 'success')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'id': gorev.id})

        return redirect(url_for('todo.liste'))

    kategoriler = GorevKategorisi.query.filter_by(aktif=True).order_by(GorevKategorisi.sira).all()
    kullanicilar = User.query.filter_by(is_deleted=False, is_active=True).order_by(User.ad).all()
    projeler = Proje.query.filter_by(is_deleted=False).order_by(Proje.ad).all()

    return render_template('todo/form.html',
                          gorev=None,
                          kategoriler=kategoriler,
                          kullanicilar=kullanicilar,
                          projeler=projeler)


@todo_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
def duzenle(id):
    """Görev düzenle"""
    gorev = Gorev.query.get_or_404(id)

    if gorev.olusturan_id != current_user.id and gorev.atanan_id != current_user.id:
        flash('Bu görevi düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('todo.liste'))

    if request.method == 'POST':
        gorev.baslik = request.form.get('baslik')
        gorev.aciklama = request.form.get('aciklama')
        gorev.oncelik = request.form.get('oncelik', 'orta')
        gorev.kategori_id = request.form.get('kategori_id') or None
        gorev.atanan_id = request.form.get('atanan_id') or None
        gorev.proje_id = request.form.get('proje_id') or None

        if request.form.get('bitis_tarihi'):
            gorev.bitis_tarihi = datetime.strptime(request.form.get('bitis_tarihi'), '%Y-%m-%dT%H:%M')
        else:
            gorev.bitis_tarihi = None

        if request.form.get('hatirlatma_tarihi'):
            gorev.hatirlatma_tarihi = datetime.strptime(request.form.get('hatirlatma_tarihi'), '%Y-%m-%dT%H:%M')
        else:
            gorev.hatirlatma_tarihi = None

        etiketler = request.form.get('etiketler', '').strip()
        if etiketler:
            gorev.etiketler = json.dumps([e.strip() for e in etiketler.split(',') if e.strip()])
        else:
            gorev.etiketler = None

        log_gorev(gorev, 'guncellendi')
        db.session.commit()

        flash('Görev güncellendi.', 'success')
        return redirect(url_for('todo.detay', id=gorev.id))

    kategoriler = GorevKategorisi.query.filter_by(aktif=True).order_by(GorevKategorisi.sira).all()
    kullanicilar = User.query.filter_by(is_deleted=False, is_active=True).order_by(User.ad).all()
    projeler = Proje.query.filter_by(is_deleted=False).order_by(Proje.ad).all()

    return render_template('todo/form.html',
                          gorev=gorev,
                          kategoriler=kategoriler,
                          kullanicilar=kullanicilar,
                          projeler=projeler)


@todo_bp.route('/<int:id>')
@login_required
def detay(id):
    """Görev detayı"""
    gorev = Gorev.query.get_or_404(id)
    alt_gorevler = gorev.alt_gorevler.filter_by(is_deleted=False).all()
    yorumlar = gorev.yorumlar.all()
    loglar = gorev.loglar.limit(20).all()

    return render_template('todo/detay.html',
                          gorev=gorev,
                          alt_gorevler=alt_gorevler,
                          yorumlar=yorumlar,
                          loglar=loglar)


# ============================================================
# DURUM DEĞİŞTİRME
# ============================================================

@todo_bp.route('/<int:id>/durum', methods=['POST'])
@login_required
def durum_degistir(id):
    """Görev durumunu değiştir"""
    gorev = Gorev.query.get_or_404(id)

    eski_durum = gorev.durum
    yeni_durum = request.form.get('durum')

    if yeni_durum in ['bekliyor', 'devam_ediyor', 'tamamlandi', 'iptal']:
        gorev.durum = yeni_durum

        if yeni_durum == 'tamamlandi':
            gorev.tamamlanma_tarihi = datetime.now()
            gorev.tamamlanma_yuzdesi = 100
        elif yeni_durum == 'devam_ediyor' and gorev.tamamlanma_yuzdesi == 0:
            gorev.tamamlanma_yuzdesi = 10

        log_gorev(gorev, 'durum_degisti', {'eski': eski_durum, 'yeni': yeni_durum})
        db.session.commit()

        flash('Görev durumu güncellendi.', 'success')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'durum': gorev.durum})

    return redirect(request.referrer or url_for('todo.liste'))


@todo_bp.route('/<int:id>/tamamla', methods=['POST'])
@login_required
def tamamla(id):
    """Görevi hızlıca tamamla"""
    gorev = Gorev.query.get_or_404(id)

    if gorev.durum != 'tamamlandi':
        gorev.durum = 'tamamlandi'
        gorev.tamamlanma_tarihi = datetime.now()
        gorev.tamamlanma_yuzdesi = 100
        log_gorev(gorev, 'tamamlandi')
        db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    return redirect(request.referrer or url_for('todo.liste'))


# ============================================================
# ALT GÖREVLER
# ============================================================

@todo_bp.route('/<int:id>/alt-gorev/ekle', methods=['POST'])
@login_required
def alt_gorev_ekle(id):
    """Alt görev ekle"""
    ust_gorev = Gorev.query.get_or_404(id)

    alt_gorev = Gorev(
        baslik=request.form.get('baslik'),
        ust_gorev_id=id,
        olusturan_id=current_user.id,
        atanan_id=ust_gorev.atanan_id,
        durum='bekliyor',
        oncelik=ust_gorev.oncelik
    )

    db.session.add(alt_gorev)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'id': alt_gorev.id, 'baslik': alt_gorev.baslik})

    flash('Alt görev eklendi.', 'success')
    return redirect(url_for('todo.detay', id=id))


# ============================================================
# YORUMLAR
# ============================================================

@todo_bp.route('/<int:id>/yorum/ekle', methods=['POST'])
@login_required
def yorum_ekle(id):
    """Göreve yorum ekle"""
    gorev = Gorev.query.get_or_404(id)

    yorum = GorevYorum(
        gorev_id=id,
        user_id=current_user.id,
        yorum=request.form.get('yorum')
    )

    db.session.add(yorum)
    log_gorev(gorev, 'yorum_eklendi')
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'yorum': {
                'id': yorum.id,
                'yorum': yorum.yorum,
                'user': current_user.full_name,
                'tarih': yorum.created_at.strftime('%d.%m.%Y %H:%M')
            }
        })

    flash('Yorum eklendi.', 'success')
    return redirect(url_for('todo.detay', id=id))


# ============================================================
# SİLME
# ============================================================

@todo_bp.route('/<int:id>/sil', methods=['POST'])
@login_required
def sil(id):
    """Görevi sil"""
    gorev = Gorev.query.get_or_404(id)

    if gorev.olusturan_id != current_user.id:
        flash('Bu görevi silme yetkiniz yok.', 'danger')
        return redirect(url_for('todo.liste'))

    gorev.is_deleted = True
    gorev.deleted_at = datetime.now()
    gorev.deleted_by = current_user.id
    db.session.commit()

    flash('Görev silindi.', 'success')
    return redirect(url_for('todo.liste'))


# ============================================================
# KATEGORİLER
# ============================================================

@todo_bp.route('/kategoriler')
@login_required
def kategoriler():
    """Kategori listesi"""
    kategoriler = GorevKategorisi.query.order_by(GorevKategorisi.sira).all()
    return render_template('todo/kategoriler.html', kategoriler=kategoriler)


@todo_bp.route('/kategori/ekle', methods=['POST'])
@login_required
def kategori_ekle():
    """Yeni kategori ekle"""
    kategori = GorevKategorisi(
        ad=request.form.get('ad'),
        renk=request.form.get('renk', '#6366f1'),
        ikon=request.form.get('ikon', 'task')
    )

    db.session.add(kategori)
    db.session.commit()

    flash('Kategori eklendi.', 'success')
    return redirect(url_for('todo.kategoriler'))


# ============================================================
# API ENDPOINTS
# ============================================================

@todo_bp.route('/api/gorevler')
@login_required
def api_gorevler():
    """Görevleri JSON olarak döndür"""
    gorevler = Gorev.query.filter(
        Gorev.is_deleted == False,
        db.or_(
            Gorev.olusturan_id == current_user.id,
            Gorev.atanan_id == current_user.id
        )
    ).all()

    return jsonify([{
        'id': g.id,
        'baslik': g.baslik,
        'durum': g.durum,
        'oncelik': g.oncelik,
        'bitis_tarihi': g.bitis_tarihi.isoformat() if g.bitis_tarihi else None,
        'gecikti': g.gecikti_mi
    } for g in gorevler])


@todo_bp.route('/api/hizli-ekle', methods=['POST'])
@login_required
def hizli_ekle():
    """Hızlı görev ekleme"""
    data = request.get_json()

    gorev = Gorev(
        baslik=data.get('baslik'),
        olusturan_id=current_user.id,
        durum='bekliyor',
        oncelik='orta'
    )

    db.session.add(gorev)
    db.session.commit()

    return jsonify({
        'success': True,
        'gorev': {
            'id': gorev.id,
            'baslik': gorev.baslik
        }
    })
