# -*- coding: utf-8 -*-
"""
TG Portal - Eğitim Routes
Eğitim yönetimi, katılımcı takibi
"""
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import random

from app import db
from app.models.egitim import (
    EgitimTipi, Egitim, EgitimKatilimci, EgitimMateryali,
    CalisanZorunluEgitim, PozisyonZorunluEgitim
)
from app.models.quiz import (
    SoruKategorisi, Soru, SoruSecenegi,
    Test, TestSorusu, TestSonuc, TestCevap
)
from app.models.ik import Calisan, Pozisyon
from app.models.proje import Proje, HedefKadro
from app.models.base import CalisanDurumu
from app.utils import permission_required, paginate_query

egitim_bp = Blueprint('egitim', __name__)

ALLOWED_EXTENSIONS = {
    'pdf': 'dokuman',
    'ppt': 'sunum',
    'pptx': 'sunum',
    'doc': 'dokuman',
    'docx': 'dokuman',
    'xls': 'dokuman',
    'xlsx': 'dokuman',
    'mp4': 'video',
    'webm': 'video',
    'jpg': 'gorsel',
    'jpeg': 'gorsel',
    'png': 'gorsel',
    'gif': 'gorsel'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_materyal_tipi(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    return ALLOWED_EXTENSIONS.get(ext, 'dokuman')



# ============================================================
# DASHBOARD
# ============================================================

@egitim_bp.route('/dashboard')
@login_required
@permission_required('egitim.view')
def dashboard():
    """Eğitim Dashboard"""
    # Yaklaşan eğitimler (7 gün içinde)
    from datetime import timedelta
    bugun = datetime.now()
    bir_hafta_sonra = bugun + timedelta(days=7)
    
    yaklasan_egitimler = Egitim.query.filter(
        Egitim.is_deleted == False,
        Egitim.durum == 'planli',
        Egitim.baslangic_tarihi >= bugun,
        Egitim.baslangic_tarihi <= bir_hafta_sonra
    ).order_by(Egitim.baslangic_tarihi).limit(5).all()
    
    # Devam eden eğitimler
    devam_eden = Egitim.query.filter(
        Egitim.is_deleted == False,
        Egitim.durum == 'devam_ediyor'
    ).count()
    
    # Bu ay tamamlanan
    ay_basi = bugun.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    tamamlanan_bu_ay = Egitim.query.filter(
        Egitim.is_deleted == False,
        Egitim.durum == 'tamamlandi',
        Egitim.bitis_tarihi >= ay_basi
    ).count()
    
    # Toplam eğitim alan çalışan (bu yıl)
    yil_basi = bugun.replace(month=1, day=1)
    egitim_alan_calisan = db.session.query(
        db.func.count(db.distinct(EgitimKatilimci.calisan_id))
    ).join(Egitim).filter(
        Egitim.baslangic_tarihi >= yil_basi,
        EgitimKatilimci.durum.in_(['katildi', 'gecti'])
    ).scalar() or 0
    
    # Zorunlu eğitimi eksik çalışanlar
    eksik_zorunlu = CalisanZorunluEgitim.query.filter(
        CalisanZorunluEgitim.tamamlandi == False
    ).count()
    
    # Eğitim tiplerine göre dağılım
    tip_dagilim = db.session.query(
        EgitimTipi.ad,
        db.func.count(Egitim.id)
    ).join(Egitim).filter(
        Egitim.is_deleted == False,
        Egitim.baslangic_tarihi >= yil_basi
    ).group_by(EgitimTipi.ad).all()
    
    return render_template('egitim/dashboard.html',
                          yaklasan_egitimler=yaklasan_egitimler,
                          devam_eden=devam_eden,
                          tamamlanan_bu_ay=tamamlanan_bu_ay,
                          egitim_alan_calisan=egitim_alan_calisan,
                          eksik_zorunlu=eksik_zorunlu,
                          tip_dagilim=tip_dagilim)


# ============================================================
# EĞİTİM LİSTESİ
# ============================================================

@egitim_bp.route('/')
@egitim_bp.route('/liste')
@login_required
@permission_required('egitim.view')
def liste():
    """Eğitim listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    tip_id = request.args.get('tip_id', type=int)
    proje_id = request.args.get('proje_id', type=int)
    tarih = request.args.get('tarih')  # gecmis, gelecek, bugun
    
    query = Egitim.query.filter_by(is_deleted=False)
    
    if durum:
        query = query.filter(Egitim.durum == durum)
    if tip_id:
        query = query.filter(Egitim.egitim_tipi_id == tip_id)
    if proje_id:
        query = query.filter(Egitim.proje_id == proje_id)
    
    if tarih == 'gecmis':
        query = query.filter(Egitim.baslangic_tarihi < datetime.now())
    elif tarih == 'gelecek':
        query = query.filter(Egitim.baslangic_tarihi >= datetime.now())
    elif tarih == 'bugun':
        bugun = date.today()
        query = query.filter(db.func.date(Egitim.baslangic_tarihi) == bugun)
    
    query = query.order_by(Egitim.baslangic_tarihi.desc())
    pagination = paginate_query(query, page, 20)
    
    egitim_tipleri = EgitimTipi.query.filter_by(aktif=True).order_by(EgitimTipi.ad).all()
    projeler = Proje.query.filter_by(is_deleted=False, aktif=True).order_by(Proje.ad).all()
    
    return render_template('egitim/liste.html',
                          egitimler=pagination.items,
                          pagination=pagination,
                          egitim_tipleri=egitim_tipleri,
                          projeler=projeler)


# ============================================================
# EĞİTİM EKLE / DÜZENLE
# ============================================================

@egitim_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('egitim.create')
def ekle():
    """Yeni eğitim ekle"""
    if request.method == 'POST':
        egitim = Egitim(
            egitim_tipi_id=int(request.form['egitim_tipi_id']),
            baslik=request.form.get('baslik', '').strip(),
            aciklama=request.form.get('aciklama', '').strip() or None,
            proje_id=int(request.form['proje_id']) if request.form.get('proje_id') else None,
            baslangic_tarihi=datetime.strptime(request.form['baslangic_tarihi'], '%Y-%m-%dT%H:%M'),
            bitis_tarihi=datetime.strptime(request.form['bitis_tarihi'], '%Y-%m-%dT%H:%M') if request.form.get('bitis_tarihi') else None,
            sure_saat=float(request.form['sure_saat']) if request.form.get('sure_saat') else None,
            lokasyon_tipi=request.form.get('lokasyon_tipi', 'yuz_yuze'),
            lokasyon=request.form.get('lokasyon', '').strip() or None,
            egitmen_tipi=request.form.get('egitmen_tipi'),
            egitmen_id=int(request.form['egitmen_id']) if request.form.get('egitmen_id') else None,
            dis_egitmen_ad=request.form.get('dis_egitmen_ad', '').strip() or None,
            dis_egitmen_kurum=request.form.get('dis_egitmen_kurum', '').strip() or None,
            kontenjan=int(request.form['kontenjan']) if request.form.get('kontenjan') else None,
            min_katilimci=int(request.form['min_katilimci']) if request.form.get('min_katilimci') else None,
            maliyet=float(request.form['maliyet']) if request.form.get('maliyet') else None,
            notlar=request.form.get('notlar', '').strip() or None,
            olusturan_id=current_user.id
        )
        
        db.session.add(egitim)
        db.session.commit()
        
        flash(f'"{egitim.baslik}" eğitimi oluşturuldu.', 'success')
        return redirect(url_for('egitim.detay', id=egitim.id))
    
    egitim_tipleri = EgitimTipi.query.filter_by(aktif=True).order_by(EgitimTipi.sira, EgitimTipi.ad).all()
    projeler = Proje.query.filter_by(is_deleted=False, aktif=True).order_by(Proje.ad).all()
    egitmenler = Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AKTIF).order_by(Calisan.ad).all()
    
    return render_template('egitim/form.html',
                          egitim=None,
                          egitim_tipleri=egitim_tipleri,
                          projeler=projeler,
                          egitmenler=egitmenler)


@egitim_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('egitim.edit')
def duzenle(id):
    """Eğitim düzenle"""
    egitim = Egitim.query.get_or_404(id)
    
    if request.method == 'POST':
        egitim.egitim_tipi_id = int(request.form['egitim_tipi_id'])
        egitim.baslik = request.form.get('baslik', '').strip()
        egitim.aciklama = request.form.get('aciklama', '').strip() or None
        egitim.proje_id = int(request.form['proje_id']) if request.form.get('proje_id') else None
        egitim.baslangic_tarihi = datetime.strptime(request.form['baslangic_tarihi'], '%Y-%m-%dT%H:%M')
        egitim.bitis_tarihi = datetime.strptime(request.form['bitis_tarihi'], '%Y-%m-%dT%H:%M') if request.form.get('bitis_tarihi') else None
        egitim.sure_saat = float(request.form['sure_saat']) if request.form.get('sure_saat') else None
        egitim.lokasyon_tipi = request.form.get('lokasyon_tipi', 'yuz_yuze')
        egitim.lokasyon = request.form.get('lokasyon', '').strip() or None
        egitim.egitmen_tipi = request.form.get('egitmen_tipi')
        egitim.egitmen_id = int(request.form['egitmen_id']) if request.form.get('egitmen_id') else None
        egitim.dis_egitmen_ad = request.form.get('dis_egitmen_ad', '').strip() or None
        egitim.dis_egitmen_kurum = request.form.get('dis_egitmen_kurum', '').strip() or None
        egitim.kontenjan = int(request.form['kontenjan']) if request.form.get('kontenjan') else None
        egitim.min_katilimci = int(request.form['min_katilimci']) if request.form.get('min_katilimci') else None
        egitim.maliyet = float(request.form['maliyet']) if request.form.get('maliyet') else None
        egitim.notlar = request.form.get('notlar', '').strip() or None
        
        db.session.commit()
        
        flash('Eğitim güncellendi.', 'success')
        return redirect(url_for('egitim.detay', id=id))
    
    egitim_tipleri = EgitimTipi.query.filter_by(aktif=True).order_by(EgitimTipi.sira, EgitimTipi.ad).all()
    projeler = Proje.query.filter_by(is_deleted=False, aktif=True).order_by(Proje.ad).all()
    egitmenler = Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AKTIF).order_by(Calisan.ad).all()
    
    return render_template('egitim/form.html',
                          egitim=egitim,
                          egitim_tipleri=egitim_tipleri,
                          projeler=projeler,
                          egitmenler=egitmenler)


# ============================================================
# EĞİTİM DETAY
# ============================================================

@egitim_bp.route('/<int:id>')
@login_required
@permission_required('egitim.view')
def detay(id):
    """Eğitim detay"""
    egitim = Egitim.query.get_or_404(id)
    
    katilimcilar = egitim.katilimcilar.join(Calisan).order_by(Calisan.ad).all()
    materyaller = egitim.materyaller.order_by(EgitimMateryali.sira).all()
    
    # Eklenebilecek çalışanlar (henüz eklenmemiş)
    mevcut_calisan_ids = [k.calisan_id for k in katilimcilar]
    eklenebilir_calisanlar = Calisan.query.filter(
        Calisan.is_deleted == False,
        Calisan.durum == CalisanDurumu.AKTIF,
        ~Calisan.id.in_(mevcut_calisan_ids) if mevcut_calisan_ids else True
    ).order_by(Calisan.ad).all()
    
    return render_template('egitim/detay.html',
                          egitim=egitim,
                          katilimcilar=katilimcilar,
                          materyaller=materyaller,
                          eklenebilir_calisanlar=eklenebilir_calisanlar)


# ============================================================
# EĞİTİM DURUM DEĞİŞTİR
# ============================================================

@egitim_bp.route('/<int:id>/durum/<durum>', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def durum_degistir(id, durum):
    """Eğitim durumunu değiştir"""
    egitim = Egitim.query.get_or_404(id)
    
    if durum not in ['planli', 'devam_ediyor', 'tamamlandi', 'iptal']:
        flash('Geçersiz durum.', 'danger')
        return redirect(url_for('egitim.detay', id=id))
    
    egitim.durum = durum
    
    if durum == 'tamamlandi' and not egitim.bitis_tarihi:
        egitim.bitis_tarihi = datetime.now()
    
    if durum == 'iptal':
        egitim.iptal_nedeni = request.form.get('iptal_nedeni')
    
    db.session.commit()
    
    flash(f'Eğitim durumu güncellendi: {durum}', 'success')
    return redirect(url_for('egitim.detay', id=id))


# ============================================================
# KATILIMCI YÖNETİMİ
# ============================================================

@egitim_bp.route('/<int:id>/katilimci/ekle', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def katilimci_ekle(id):
    """Eğitime katılımcı ekle"""
    egitim = Egitim.query.get_or_404(id)
    
    calisan_ids = request.form.getlist('calisan_ids')
    
    eklenen = 0
    for calisan_id in calisan_ids:
        # Zaten var mı kontrol
        mevcut = EgitimKatilimci.query.filter_by(
            egitim_id=id,
            calisan_id=int(calisan_id)
        ).first()
        
        if not mevcut:
            katilimci = EgitimKatilimci(
                egitim_id=id,
                calisan_id=int(calisan_id),
                davet_eden_id=current_user.id
            )
            db.session.add(katilimci)
            eklenen += 1
    
    db.session.commit()
    
    flash(f'{eklenen} katılımcı eklendi.', 'success')
    return redirect(url_for('egitim.detay', id=id))


@egitim_bp.route('/katilimci/<int:id>/durum', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def katilimci_durum(id):
    """Katılımcı durumunu güncelle"""
    katilimci = EgitimKatilimci.query.get_or_404(id)
    
    durum = request.form.get('durum')
    if durum:
        katilimci.durum = durum
        
        if durum in ['katildi', 'gecti']:
            katilimci.katilim_tarihi = datetime.now()
        
        if durum == 'gecti':
            # Sertifika bilgisi
            katilimci.sertifika_tarihi = date.today()
            if katilimci.egitim.egitim_tipi.gecerlilik_gun:
                from datetime import timedelta
                katilimci.sertifika_gecerlilik = date.today() + timedelta(days=katilimci.egitim.egitim_tipi.gecerlilik_gun)
    
    puan = request.form.get('puan')
    if puan:
        katilimci.puan = int(puan)
    
    katilimci.degerlendirme = request.form.get('degerlendirme')
    katilimci.katilim_notu = request.form.get('katilim_notu')
    
    if durum == 'mazeret':
        katilimci.mazeret_nedeni = request.form.get('mazeret_nedeni')
    
    db.session.commit()
    
    return jsonify({'success': True})


@egitim_bp.route('/katilimci/<int:id>/sil', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def katilimci_sil(id):
    """Katılımcıyı sil"""
    katilimci = EgitimKatilimci.query.get_or_404(id)
    egitim_id = katilimci.egitim_id
    
    db.session.delete(katilimci)
    db.session.commit()
    
    flash('Katılımcı silindi.', 'success')
    return redirect(url_for('egitim.detay', id=egitim_id))


# ============================================================
# TOPLU KATILIMCI EKLEME (Proje/Kadro bazlı)
# ============================================================

@egitim_bp.route('/<int:id>/toplu-katilimci', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def toplu_katilimci(id):
    """Proje veya kadrodan toplu katılımcı ekle"""
    egitim = Egitim.query.get_or_404(id)
    
    kaynak = request.form.get('kaynak')  # proje, kadro
    kaynak_id = request.form.get('kaynak_id', type=int)
    
    if kaynak == 'proje' and kaynak_id:
        # Projedeki tüm aktif çalışanları ekle
        calisanlar = Calisan.query.join(HedefKadro).filter(
            HedefKadro.proje_id == kaynak_id,
            Calisan.is_deleted == False,
            Calisan.durum == CalisanDurumu.AKTIF
        ).all()
    elif kaynak == 'kadro' and kaynak_id:
        # Kadrodaki tüm aktif çalışanları ekle
        calisanlar = Calisan.query.filter(
            Calisan.kadro_id == kaynak_id,
            Calisan.is_deleted == False,
            Calisan.durum == CalisanDurumu.AKTIF
        ).all()
    else:
        flash('Geçersiz kaynak.', 'danger')
        return redirect(url_for('egitim.detay', id=id))
    
    eklenen = 0
    for calisan in calisanlar:
        mevcut = EgitimKatilimci.query.filter_by(
            egitim_id=id,
            calisan_id=calisan.id
        ).first()
        
        if not mevcut:
            katilimci = EgitimKatilimci(
                egitim_id=id,
                calisan_id=calisan.id,
                davet_eden_id=current_user.id
            )
            db.session.add(katilimci)
            eklenen += 1
    
    db.session.commit()
    
    flash(f'{eklenen} katılımcı eklendi.', 'success')
    return redirect(url_for('egitim.detay', id=id))


# ============================================================
# EĞİTİM TİPLERİ YÖNETİMİ
# ============================================================

@egitim_bp.route('/tipler')
@login_required
@permission_required('egitim.view')
def tip_liste():
    """Eğitim tipleri listesi"""
    tipler = EgitimTipi.query.order_by(EgitimTipi.sira, EgitimTipi.ad).all()
    return render_template('egitim/tip_liste.html', egitim_tipleri=tipler)


@egitim_bp.route('/tip/ekle', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def tip_ekle():
    """Yeni eğitim tipi ekle"""
    tip = EgitimTipi(
        ad=request.form.get('ad'),
        kod=request.form.get('kod'),
        kategori=request.form.get('kategori'),
        aciklama=request.form.get('aciklama'),
        sure_saat=float(request.form['sure_saat']) if request.form.get('sure_saat') else None,
        gecerlilik_gun=int(request.form['gecerlilik_gun']) if request.form.get('gecerlilik_gun') else None,
        sertifika_gerekli=request.form.get('sertifika_gerekli') == 'on',
        tekrar_periyot_gun=int(request.form['tekrar_periyot_gun']) if request.form.get('tekrar_periyot_gun') else None
    )
    db.session.add(tip)
    db.session.commit()
    
    flash('Eğitim tipi eklendi.', 'success')
    return redirect(url_for('egitim.tip_liste'))


# ============================================================
# ÇALIŞAN EĞİTİM GEÇMİŞİ
# ============================================================

@egitim_bp.route('/calisan/<int:id>')
@login_required
@permission_required('egitim.view')
def calisan_egitimler(id):
    """Çalışanın eğitim geçmişi"""
    calisan = Calisan.query.get_or_404(id)
    
    egitim_kayitlari = calisan.egitim_kayitlari.join(Egitim).order_by(
        Egitim.baslangic_tarihi.desc()
    ).all()
    
    zorunlu_egitimler = calisan.zorunlu_egitimler.all()
    
    return render_template('egitim/calisan_egitimler.html',
                          calisan=calisan,
                          egitim_kayitlari=egitim_kayitlari,
                          zorunlu_egitimler=zorunlu_egitimler)


# ============================================================
# ZORUNLU EĞİTİM TAKİBİ
# ============================================================

@egitim_bp.route('/zorunlu-egitimler')
@login_required
@permission_required('egitim.view')
def zorunlu_egitim_takip():
    """Zorunlu eğitim durumu takibi"""
    # Eksik zorunlu eğitimleri olan çalışanlar
    eksik_egitimler = db.session.query(
        Calisan,
        CalisanZorunluEgitim
    ).join(CalisanZorunluEgitim).filter(
        Calisan.is_deleted == False,
        Calisan.durum == CalisanDurumu.AKTIF,
        CalisanZorunluEgitim.tamamlandi == False
    ).all()
    
    # Yenileme gereken eğitimler (30 gün içinde süresi dolacak)
    from datetime import timedelta
    otuz_gun_sonra = date.today() + timedelta(days=30)
    
    yenileme_gerekli = db.session.query(
        Calisan,
        CalisanZorunluEgitim
    ).join(CalisanZorunluEgitim).filter(
        Calisan.is_deleted == False,
        Calisan.durum == CalisanDurumu.AKTIF,
        CalisanZorunluEgitim.tamamlandi == True,
        CalisanZorunluEgitim.son_gecerlilik <= otuz_gun_sonra
    ).all()
    
    return render_template('egitim/zorunlu_takip.html',
                          eksik_egitimler=eksik_egitimler,
                          yenileme_gerekli=yenileme_gerekli)


# ============================================================
# RAPORLAR
# ============================================================

@egitim_bp.route('/rapor')
@login_required
@permission_required('egitim.view')
def rapor():
    """Eğitim raporları"""
    # Yıllık eğitim istatistikleri
    yil = request.args.get('yil', date.today().year, type=int)
    yil_basi = date(yil, 1, 1)
    yil_sonu = date(yil, 12, 31)
    
    # Aylık eğitim sayısı
    aylik_egitim = db.session.query(
        db.func.extract('month', Egitim.baslangic_tarihi).label('ay'),
        db.func.count(Egitim.id).label('sayi')
    ).filter(
        Egitim.is_deleted == False,
        Egitim.baslangic_tarihi >= yil_basi,
        Egitim.baslangic_tarihi <= yil_sonu
    ).group_by('ay').all()
    
    # Toplam eğitim saati
    toplam_saat = db.session.query(
        db.func.sum(Egitim.sure_saat)
    ).filter(
        Egitim.is_deleted == False,
        Egitim.durum == 'tamamlandi',
        Egitim.baslangic_tarihi >= yil_basi,
        Egitim.baslangic_tarihi <= yil_sonu
    ).scalar() or 0
    
    # Eğitim başarı oranı
    toplam_katilimci = EgitimKatilimci.query.join(Egitim).filter(
        Egitim.baslangic_tarihi >= yil_basi,
        Egitim.baslangic_tarihi <= yil_sonu
    ).count()
    
    basarili_katilimci = EgitimKatilimci.query.join(Egitim).filter(
        Egitim.baslangic_tarihi >= yil_basi,
        Egitim.baslangic_tarihi <= yil_sonu,
        EgitimKatilimci.durum == 'gecti'
    ).count()
    
    basari_orani = round((basarili_katilimci / toplam_katilimci * 100), 1) if toplam_katilimci > 0 else 0
    
    return render_template('egitim/rapor.html',
                          yil=yil,
                          aylik_egitim=aylik_egitim,
                          toplam_saat=toplam_saat,
                          toplam_katilimci=toplam_katilimci,
                          basarili_katilimci=basarili_katilimci,
                          basari_orani=basari_orani)

# ============================================================
# MATERYAL YÜKLEME
# ============================================================

@egitim_bp.route('/<int:id>/materyal/yukle', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def materyal_yukle(id):
    """Eğitime materyal yükle"""
    egitim = Egitim.query.get_or_404(id)
    
    # Harici link mi?
    if request.form.get('harici_link'):
        materyal = EgitimMateryali(
            egitim_id=id,
            ad=request.form.get('ad', 'Harici İçerik').strip(),
            aciklama=request.form.get('aciklama', '').strip() or None,
            materyal_tipi=request.form.get('materyal_tipi', 'link'),
            harici_link=request.form.get('harici_link').strip(),
            yukleyen_id=current_user.id
        )
        db.session.add(materyal)
        db.session.commit()
        flash('Harici link eklendi.', 'success')
        return redirect(url_for('egitim.detay', id=id))
    
    # Dosya yükleme
    if 'dosya' not in request.files:
        flash('Dosya seçilmedi.', 'danger')
        return redirect(url_for('egitim.detay', id=id))
    
    dosya = request.files['dosya']
    
    if dosya.filename == '':
        flash('Dosya seçilmedi.', 'danger')
        return redirect(url_for('egitim.detay', id=id))
    
    if dosya and allowed_file(dosya.filename):
        filename = secure_filename(dosya.filename)
        # Benzersiz isim oluştur
        import uuid
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Upload klasörü
        upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'egitim', str(id))
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, unique_filename)
        dosya.save(filepath)
        
        # Dosya boyutu
        file_size = os.path.getsize(filepath)
        
        materyal = EgitimMateryali(
            egitim_id=id,
            ad=request.form.get('ad', filename).strip(),
            aciklama=request.form.get('aciklama', '').strip() or None,
            materyal_tipi=get_materyal_tipi(filename),
            dosya_adi=filename,
            dosya_yolu=filepath,
            dosya_boyut=file_size,
            mime_type=dosya.content_type,
            yukleyen_id=current_user.id
        )
        db.session.add(materyal)
        db.session.commit()
        
        flash(f'"{filename}" yüklendi.', 'success')
    else:
        flash('Desteklenmeyen dosya formatı.', 'danger')
    
    return redirect(url_for('egitim.detay', id=id))


# ============================================================
# MATERYAL GÖRÜNTÜLEME
# ============================================================

@egitim_bp.route('/materyal/<int:id>/goruntule')
@login_required
@permission_required('egitim.view')
def materyal_goruntule(id):
    """Materyali görüntüle"""
    materyal = EgitimMateryali.query.get_or_404(id)
    
    return render_template('egitim/materyal_goruntule.html', materyal=materyal)


@egitim_bp.route('/materyal/<int:id>/indir')
@login_required
@permission_required('egitim.view')
def materyal_indir(id):
    """Materyali indir"""
    materyal = EgitimMateryali.query.get_or_404(id)
    
    if not materyal.dosya_yolu or not os.path.exists(materyal.dosya_yolu):
        flash('Dosya bulunamadı.', 'danger')
        return redirect(url_for('egitim.detay', id=materyal.egitim_id))
    
    return send_file(
        materyal.dosya_yolu,
        download_name=materyal.dosya_adi,
        as_attachment=True
    )


@egitim_bp.route('/materyal/<int:id>/embed')
@login_required
@permission_required('egitim.view')
def materyal_embed(id):
    """Materyal embed (iframe için)"""
    materyal = EgitimMateryali.query.get_or_404(id)
    
    if not materyal.dosya_yolu or not os.path.exists(materyal.dosya_yolu):
        return "Dosya bulunamadı", 404
    
    return send_file(
        materyal.dosya_yolu,
        mimetype=materyal.mime_type
    )


# ============================================================
# MATERYAL SİL
# ============================================================

@egitim_bp.route('/materyal/<int:id>/sil', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def materyal_sil(id):
    """Materyali sil"""
    materyal = EgitimMateryali.query.get_or_404(id)
    egitim_id = materyal.egitim_id
    
    # Dosyayı da sil
    if materyal.dosya_yolu and os.path.exists(materyal.dosya_yolu):
        os.remove(materyal.dosya_yolu)
    
    db.session.delete(materyal)
    db.session.commit()
    
    flash('Materyal silindi.', 'success')
    return redirect(url_for('egitim.detay', id=egitim_id))


# ============================================================
# MATERYAL SIRALAMA
# ============================================================

@egitim_bp.route('/<int:id>/materyal/sirala', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def materyal_sirala(id):
    """Materyal sırasını güncelle (AJAX)"""
    siralama = request.json.get('siralama', [])
    
    for index, materyal_id in enumerate(siralama):
        materyal = EgitimMateryali.query.get(materyal_id)
        if materyal and materyal.egitim_id == id:
            materyal.sira = index
    
    db.session.commit()
    return jsonify({'success': True})

# ============================================================
# SORU BANKASI YÖNETİMİ
# ============================================================

@egitim_bp.route('/sorular')
@login_required
@permission_required('egitim.view')
def soru_liste():
    """Soru bankası listesi"""
    page = request.args.get('page', 1, type=int)
    kategori_id = request.args.get('kategori_id', type=int)
    egitim_tipi_id = request.args.get('egitim_tipi_id', type=int)
    zorluk = request.args.get('zorluk', type=int)
    soru_tipi = request.args.get('soru_tipi')
    
    query = Soru.query.filter_by(is_deleted=False)
    
    if kategori_id:
        query = query.filter(Soru.kategori_id == kategori_id)
    if egitim_tipi_id:
        query = query.filter(Soru.egitim_tipi_id == egitim_tipi_id)
    if zorluk:
        query = query.filter(Soru.zorluk == zorluk)
    if soru_tipi:
        query = query.filter(Soru.soru_tipi == soru_tipi)
    
    query = query.order_by(Soru.created_at.desc())
    pagination = paginate_query(query, page, 20)
    
    kategoriler = SoruKategorisi.query.filter_by(aktif=True).order_by(SoruKategorisi.ad).all()
    egitim_tipleri = EgitimTipi.query.filter_by(aktif=True).order_by(EgitimTipi.ad).all()
    
    return render_template('egitim/soru_liste.html',
                          sorular=pagination.items,
                          pagination=pagination,
                          kategoriler=kategoriler,
                          egitim_tipleri=egitim_tipleri)


@egitim_bp.route('/soru/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('egitim.edit')
def soru_ekle():
    """Yeni soru ekle"""
    if request.method == 'POST':
        soru = Soru(
            soru_metni=request.form.get('soru_metni', '').strip(),
            soru_tipi=request.form.get('soru_tipi', 'coktan_secmeli'),
            kategori_id=int(request.form['kategori_id']) if request.form.get('kategori_id') else None,
            egitim_tipi_id=int(request.form['egitim_tipi_id']) if request.form.get('egitim_tipi_id') else None,
            zorluk=int(request.form.get('zorluk', 1)),
            puan=int(request.form.get('puan', 10)),
            aciklama=request.form.get('aciklama', '').strip() or None,
            olusturan_id=current_user.id
        )
        db.session.add(soru)
        db.session.flush()  # ID al
        
        # Seçenekleri ekle
        secenek_metinleri = request.form.getlist('secenek_metni')
        dogru_secenekler = request.form.getlist('dogru_secenek')
        
        for i, metin in enumerate(secenek_metinleri):
            if metin.strip():
                secenek = SoruSecenegi(
                    soru_id=soru.id,
                    secenek_metni=metin.strip(),
                    dogru=str(i) in dogru_secenekler,
                    sira=i
                )
                db.session.add(secenek)
        
        db.session.commit()
        flash('Soru eklendi.', 'success')
        return redirect(url_for('egitim.soru_liste'))
    
    kategoriler = SoruKategorisi.query.filter_by(aktif=True).order_by(SoruKategorisi.ad).all()
    egitim_tipleri = EgitimTipi.query.filter_by(aktif=True).order_by(EgitimTipi.ad).all()
    
    return render_template('egitim/soru_form.html',
                          soru=None,
                          kategoriler=kategoriler,
                          egitim_tipleri=egitim_tipleri)


@egitim_bp.route('/soru/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('egitim.edit')
def soru_duzenle(id):
    """Soru düzenle"""
    soru = Soru.query.get_or_404(id)
    
    if request.method == 'POST':
        soru.soru_metni = request.form.get('soru_metni', '').strip()
        soru.soru_tipi = request.form.get('soru_tipi', 'coktan_secmeli')
        soru.kategori_id = int(request.form['kategori_id']) if request.form.get('kategori_id') else None
        soru.egitim_tipi_id = int(request.form['egitim_tipi_id']) if request.form.get('egitim_tipi_id') else None
        soru.zorluk = int(request.form.get('zorluk', 1))
        soru.puan = int(request.form.get('puan', 10))
        soru.aciklama = request.form.get('aciklama', '').strip() or None
        
        # Mevcut seçenekleri sil
        SoruSecenegi.query.filter_by(soru_id=soru.id).delete()
        
        # Yeni seçenekleri ekle
        secenek_metinleri = request.form.getlist('secenek_metni')
        dogru_secenekler = request.form.getlist('dogru_secenek')
        
        for i, metin in enumerate(secenek_metinleri):
            if metin.strip():
                secenek = SoruSecenegi(
                    soru_id=soru.id,
                    secenek_metni=metin.strip(),
                    dogru=str(i) in dogru_secenekler,
                    sira=i
                )
                db.session.add(secenek)
        
        db.session.commit()
        flash('Soru güncellendi.', 'success')
        return redirect(url_for('egitim.soru_liste'))
    
    kategoriler = SoruKategorisi.query.filter_by(aktif=True).order_by(SoruKategorisi.ad).all()
    egitim_tipleri = EgitimTipi.query.filter_by(aktif=True).order_by(EgitimTipi.ad).all()
    
    return render_template('egitim/soru_form.html',
                          soru=soru,
                          kategoriler=kategoriler,
                          egitim_tipleri=egitim_tipleri)


@egitim_bp.route('/soru/<int:id>/sil', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def soru_sil(id):
    """Soru sil (soft delete)"""
    soru = Soru.query.get_or_404(id)
    soru.is_deleted = True
    soru.deleted_at = datetime.utcnow()
    db.session.commit()
    
    flash('Soru silindi.', 'success')
    return redirect(url_for('egitim.soru_liste'))


# ============================================================
# SORU KATEGORİLERİ
# ============================================================

@egitim_bp.route('/soru-kategorileri')
@login_required
@permission_required('egitim.view')
def soru_kategori_liste():
    """Soru kategorileri"""
    kategoriler = SoruKategorisi.query.order_by(SoruKategorisi.sira, SoruKategorisi.ad).all()
    return render_template('egitim/soru_kategori_liste.html', kategoriler=kategoriler)


@egitim_bp.route('/soru-kategori/ekle', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def soru_kategori_ekle():
    """Yeni kategori ekle"""
    kategori = SoruKategorisi(
        ad=request.form.get('ad'),
        aciklama=request.form.get('aciklama'),
        ust_kategori_id=int(request.form['ust_kategori_id']) if request.form.get('ust_kategori_id') else None
    )
    db.session.add(kategori)
    db.session.commit()
    
    flash('Kategori eklendi.', 'success')
    return redirect(url_for('egitim.soru_kategori_liste'))


# ============================================================
# TEST YÖNETİMİ
# ============================================================

@egitim_bp.route('/testler')
@login_required
@permission_required('egitim.view')
def test_liste():
    """Test listesi"""
    page = request.args.get('page', 1, type=int)
    egitim_id = request.args.get('egitim_id', type=int)
    aktif = request.args.get('aktif')
    
    query = Test.query.filter_by(is_deleted=False)
    
    if egitim_id:
        query = query.filter(Test.egitim_id == egitim_id)
    if aktif == '1':
        query = query.filter(Test.aktif == True)
    elif aktif == '0':
        query = query.filter(Test.aktif == False)
    
    query = query.order_by(Test.created_at.desc())
    pagination = paginate_query(query, page, 20)
    
    return render_template('egitim/test_liste.html',
                          testler=pagination.items,
                          pagination=pagination)


@egitim_bp.route('/test/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('egitim.edit')
def test_ekle():
    """Yeni test oluştur"""
    if request.method == 'POST':
        test = Test(
            baslik=request.form.get('baslik', '').strip(),
            aciklama=request.form.get('aciklama', '').strip() or None,
            egitim_id=int(request.form['egitim_id']) if request.form.get('egitim_id') else None,
            egitim_tipi_id=int(request.form['egitim_tipi_id']) if request.form.get('egitim_tipi_id') else None,
            sure_dakika=int(request.form['sure_dakika']) if request.form.get('sure_dakika') else None,
            gecme_puani=int(request.form.get('gecme_puani', 70)),
            soru_karistir=request.form.get('soru_karistir') == 'on',
            secenek_karistir=request.form.get('secenek_karistir') == 'on',
            sonucu_goster=request.form.get('sonucu_goster') == 'on',
            dogru_cevaplari_goster=request.form.get('dogru_cevaplari_goster') == 'on',
            tekrar_hak=int(request.form['tekrar_hak']) if request.form.get('tekrar_hak') else None,
            aktif=request.form.get('aktif') == 'on',
            olusturan_id=current_user.id
        )
        
        # Tarihler
        if request.form.get('baslangic_tarihi'):
            test.baslangic_tarihi = datetime.strptime(request.form['baslangic_tarihi'], '%Y-%m-%dT%H:%M')
        if request.form.get('bitis_tarihi'):
            test.bitis_tarihi = datetime.strptime(request.form['bitis_tarihi'], '%Y-%m-%dT%H:%M')
        
        db.session.add(test)
        db.session.commit()
        
        flash('Test oluşturuldu. Şimdi soru ekleyebilirsiniz.', 'success')
        return redirect(url_for('egitim.test_detay', id=test.id))
    
    egitimler = Egitim.query.filter_by(is_deleted=False).order_by(Egitim.baslangic_tarihi.desc()).all()
    egitim_tipleri = EgitimTipi.query.filter_by(aktif=True).order_by(EgitimTipi.ad).all()
    
    return render_template('egitim/test_form.html',
                          test=None,
                          egitimler=egitimler,
                          egitim_tipleri=egitim_tipleri)


@egitim_bp.route('/test/<int:id>')
@login_required
@permission_required('egitim.view')
def test_detay(id):
    """Test detay - sorular ve sonuçlar"""
    test = Test.query.get_or_404(id)
    
    # Test soruları
    test_sorulari = test.test_sorulari.order_by(TestSorusu.sira).all()
    
    # Eklenebilecek sorular
    mevcut_soru_ids = [ts.soru_id for ts in test_sorulari]
    eklenebilir_sorular = Soru.query.filter(
        Soru.is_deleted == False,
        Soru.aktif == True,
        ~Soru.id.in_(mevcut_soru_ids) if mevcut_soru_ids else True
    )
    
    # Eğitim tipi filtresi
    if test.egitim_tipi_id:
        eklenebilir_sorular = eklenebilir_sorular.filter(
            db.or_(Soru.egitim_tipi_id == test.egitim_tipi_id, Soru.egitim_tipi_id == None)
        )
    
    eklenebilir_sorular = eklenebilir_sorular.order_by(Soru.created_at.desc()).limit(100).all()
    
    # Son sonuçlar
    son_sonuclar = test.sonuclar.filter_by(tamamlandi=True).order_by(TestSonuc.bitis_zamani.desc()).limit(10).all()
    
    return render_template('egitim/test_detay.html',
                          test=test,
                          test_sorulari=test_sorulari,
                          eklenebilir_sorular=eklenebilir_sorular,
                          son_sonuclar=son_sonuclar)


@egitim_bp.route('/test/<int:id>/soru-ekle', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def test_soru_ekle(id):
    """Teste soru ekle"""
    test = Test.query.get_or_404(id)
    
    soru_ids = request.form.getlist('soru_ids')
    
    # Mevcut max sıra
    max_sira = db.session.query(db.func.max(TestSorusu.sira)).filter_by(test_id=id).scalar() or 0
    
    eklenen = 0
    for soru_id in soru_ids:
        # Zaten var mı?
        mevcut = TestSorusu.query.filter_by(test_id=id, soru_id=int(soru_id)).first()
        if not mevcut:
            max_sira += 1
            ts = TestSorusu(
                test_id=id,
                soru_id=int(soru_id),
                sira=max_sira
            )
            db.session.add(ts)
            eklenen += 1
    
    db.session.commit()
    flash(f'{eklenen} soru eklendi.', 'success')
    return redirect(url_for('egitim.test_detay', id=id))


@egitim_bp.route('/test/<int:id>/soru-cikar/<int:soru_id>', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def test_soru_cikar(id, soru_id):
    """Testten soru çıkar"""
    ts = TestSorusu.query.filter_by(test_id=id, soru_id=soru_id).first_or_404()
    db.session.delete(ts)
    db.session.commit()
    
    flash('Soru testten çıkarıldı.', 'success')
    return redirect(url_for('egitim.test_detay', id=id))


@egitim_bp.route('/test/<int:id>/soru-sirala', methods=['POST'])
@login_required
@permission_required('egitim.edit')
def test_soru_sirala(id):
    """Test sorularını sırala (AJAX)"""
    siralama = request.json.get('siralama', [])
    
    for index, ts_id in enumerate(siralama):
        ts = TestSorusu.query.get(ts_id)
        if ts and ts.test_id == id:
            ts.sira = index
    
    db.session.commit()
    return jsonify({'success': True})


# ============================================================
# TEST ÇÖZME
# ============================================================

@egitim_bp.route('/test/<int:id>/baslat', methods=['GET', 'POST'])
@login_required
def test_baslat(id):
    """Testi başlat"""
    test = Test.query.get_or_404(id)
    
    # Kullanıcının çalışan kaydını bul
    calisan = Calisan.query.filter_by(user_id=current_user.id, is_deleted=False).first()
    if not calisan:
        flash('Çalışan kaydınız bulunamadı.', 'danger')
        return redirect(url_for('egitim.test_liste'))
    
    # Çözebilir mi kontrol
    cozebilir, mesaj = test.kullanici_cozebilir_mi(calisan.id)
    if not cozebilir:
        flash(mesaj, 'warning')
        return redirect(url_for('egitim.test_liste'))
    
    # Devam eden sınav var mı?
    devam_eden = TestSonuc.query.filter_by(
        test_id=id,
        calisan_id=calisan.id,
        tamamlandi=False
    ).first()
    
    if devam_eden:
        # Süre kontrolü
        if test.sure_dakika:
            gecen_sure = (datetime.utcnow() - devam_eden.baslangic_zamani).total_seconds()
            if gecen_sure > test.sure_dakika * 60:
                # Süre dolmuş, otomatik bitir
                devam_eden.tamamlandi = True
                devam_eden.bitis_zamani = datetime.utcnow()
                devam_eden.gecen_sure_saniye = int(gecen_sure)
                _hesapla_sonuc(devam_eden)
                db.session.commit()
                flash('Önceki sınavınızın süresi dolmuştu, otomatik değerlendirildi.', 'info')
            else:
                # Devam et
                return redirect(url_for('egitim.test_coz', sonuc_id=devam_eden.id))
        else:
            return redirect(url_for('egitim.test_coz', sonuc_id=devam_eden.id))
    
    if request.method == 'POST':
        # Yeni sınav başlat
        sonuc = TestSonuc(
            test_id=id,
            calisan_id=calisan.id,
            toplam_puan=test.toplam_puan
        )
        db.session.add(sonuc)
        db.session.commit()
        
        return redirect(url_for('egitim.test_coz', sonuc_id=sonuc.id))
    
    return render_template('egitim/test_baslat.html', test=test)


@egitim_bp.route('/test/coz/<int:sonuc_id>', methods=['GET', 'POST'])
@login_required
def test_coz(sonuc_id):
    """Test çözme sayfası"""
    sonuc = TestSonuc.query.get_or_404(sonuc_id)
    test = sonuc.test
    
    # Yetki kontrolü
    calisan = Calisan.query.filter_by(user_id=current_user.id, is_deleted=False).first()
    if not calisan or sonuc.calisan_id != calisan.id:
        flash('Bu sınava erişim yetkiniz yok.', 'danger')
        return redirect(url_for('egitim.test_liste'))
    
    if sonuc.tamamlandi:
        return redirect(url_for('egitim.test_sonuc', sonuc_id=sonuc_id))
    
    # Süre kontrolü
    kalan_sure = None
    if test.sure_dakika:
        gecen_sure = (datetime.utcnow() - sonuc.baslangic_zamani).total_seconds()
        kalan_sure = max(0, test.sure_dakika * 60 - int(gecen_sure))
        
        if kalan_sure <= 0:
            # Süre doldu
            sonuc.tamamlandi = True
            sonuc.bitis_zamani = datetime.utcnow()
            sonuc.gecen_sure_saniye = test.sure_dakika * 60
            _hesapla_sonuc(sonuc)
            db.session.commit()
            flash('Süre doldu! Sınavınız otomatik değerlendirildi.', 'warning')
            return redirect(url_for('egitim.test_sonuc', sonuc_id=sonuc_id))
    
    # Soruları al
    test_sorulari = test.test_sorulari.order_by(TestSorusu.sira).all()
    
    if test.soru_karistir:
        random.shuffle(test_sorulari)
    
    # Mevcut cevapları al
    mevcut_cevaplar = {c.soru_id: c for c in sonuc.cevaplar.all()}
    
    if request.method == 'POST':
        # Cevapları kaydet
        for ts in test_sorulari:
            soru = ts.soru
            cevap_key = f'soru_{soru.id}'
            
            if soru.soru_tipi == 'coklu_secim':
                secilen = request.form.getlist(cevap_key)
                secilen_ids = [int(s) for s in secilen] if secilen else None
            else:
                secilen = request.form.get(cevap_key)
                secilen_ids = int(secilen) if secilen else None
            
            # Mevcut cevabı güncelle veya yeni oluştur
            cevap = mevcut_cevaplar.get(soru.id)
            if not cevap:
                cevap = TestCevap(sonuc_id=sonuc_id, soru_id=soru.id)
                db.session.add(cevap)
            
            if soru.soru_tipi == 'coklu_secim':
                cevap.secilen_secenekler = secilen_ids
            else:
                cevap.secilen_secenek_id = secilen_ids
        
        db.session.commit()
        
        # Bitir mi?
        if request.form.get('bitir'):
            sonuc.tamamlandi = True
            sonuc.bitis_zamani = datetime.utcnow()
            sonuc.gecen_sure_saniye = int((sonuc.bitis_zamani - sonuc.baslangic_zamani).total_seconds())
            _hesapla_sonuc(sonuc)
            db.session.commit()
            
            flash('Sınavınız tamamlandı!', 'success')
            return redirect(url_for('egitim.test_sonuc', sonuc_id=sonuc_id))
        
        flash('Cevaplarınız kaydedildi.', 'info')
    
    return render_template('egitim/test_coz.html',
                          test=test,
                          sonuc=sonuc,
                          test_sorulari=test_sorulari,
                          mevcut_cevaplar=mevcut_cevaplar,
                          kalan_sure=kalan_sure)


def _hesapla_sonuc(sonuc):
    """Test sonucunu hesapla"""
    test = sonuc.test
    
    dogru = 0
    yanlis = 0
    bos = 0
    alinan_puan = 0
    
    for ts in test.test_sorulari.all():
        soru = ts.soru
        cevap = sonuc.cevaplar.filter_by(soru_id=soru.id).first()
        
        if not cevap or (not cevap.secilen_secenek_id and not cevap.secilen_secenekler):
            bos += 1
            if cevap:
                cevap.dogru = False
                cevap.alinan_puan = 0
            continue
        
        # Doğru mu kontrol et
        if soru.soru_tipi == 'coklu_secim':
            # Çoklu seçim
            dogru_ids = set(s.id for s in soru.dogru_secenekler)
            secilen_ids = set(cevap.secilen_secenekler or [])
            dogru_mu = dogru_ids == secilen_ids
        else:
            # Tekli seçim
            dogru_secenek = soru.dogru_secenek
            dogru_mu = dogru_secenek and cevap.secilen_secenek_id == dogru_secenek.id
        
        cevap.dogru = dogru_mu
        
        if dogru_mu:
            dogru += 1
            cevap.alinan_puan = ts.puan
            alinan_puan += ts.puan
        else:
            yanlis += 1
            cevap.alinan_puan = 0
    
    sonuc.dogru_sayisi = dogru
    sonuc.yanlis_sayisi = yanlis
    sonuc.bos_sayisi = bos
    sonuc.alinan_puan = alinan_puan
    sonuc.yuzde = round((alinan_puan / sonuc.toplam_puan * 100), 1) if sonuc.toplam_puan > 0 else 0
    sonuc.gecti = sonuc.yuzde >= test.gecme_puani


@egitim_bp.route('/test/sonuc/<int:sonuc_id>')
@login_required
def test_sonuc(sonuc_id):
    """Test sonuç sayfası"""
    sonuc = TestSonuc.query.get_or_404(sonuc_id)
    test = sonuc.test
    
    # Yetki kontrolü
    calisan = Calisan.query.filter_by(user_id=current_user.id, is_deleted=False).first()
    is_owner = calisan and sonuc.calisan_id == calisan.id
    is_admin = current_user.has_permission('egitim.edit')
    
    if not is_owner and not is_admin:
        flash('Bu sonuca erişim yetkiniz yok.', 'danger')
        return redirect(url_for('egitim.test_liste'))
    
    # Cevapları al
    cevaplar = []
    for ts in test.test_sorulari.order_by(TestSorusu.sira).all():
        cevap = sonuc.cevaplar.filter_by(soru_id=ts.soru_id).first()
        cevaplar.append({
            'soru': ts.soru,
            'cevap': cevap
        })
    
    return render_template('egitim/test_sonuc.html',
                          test=test,
                          sonuc=sonuc,
                          cevaplar=cevaplar)


# ============================================================
# EĞİTİME BAĞLI TESTLERİ GÖR
# ============================================================

@egitim_bp.route('/<int:id>/testler')
@login_required
@permission_required('egitim.view')
def egitim_testleri(id):
    """Eğitime bağlı testler"""
    egitim = Egitim.query.get_or_404(id)
    testler = egitim.testler.filter_by(is_deleted=False).all()
    
    return render_template('egitim/egitim_testleri.html',
                          egitim=egitim,
                          testler=testler)