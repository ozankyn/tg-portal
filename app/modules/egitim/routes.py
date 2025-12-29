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

from app import db
from app.models.egitim import (
    EgitimTipi, Egitim, EgitimKatilimci, EgitimMateryali,
    CalisanZorunluEgitim, PozisyonZorunluEgitim
)
from app.models.ik import Calisan, Pozisyon
from app.models.proje import Proje, HedefKadro
from app.models.base import CalisanDurumu
from app.utils import permission_required, paginate_query

egitim_bp = Blueprint('egitim', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx', 'doc', 'docx', 'xls', 'xlsx', 'mp4', 'jpg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
