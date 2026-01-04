# -*- coding: utf-8 -*-
"""
TG Portal - Raporlama Modülü
Tüm modüller için merkezi raporlama
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
import io

from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user
from sqlalchemy import func, extract

from app import db
from app.utils import permission_required

# Modelleri import et
from app.models.ik import Calisan, Departman
from app.models.masraf import Masraf, MasrafKategorisi
from app.models.sozlesme import Sozlesme, SozlesmeTipi
from app.models.satinalma import SatinAlmaTalebi, SatinAlmaSiparisi, SatinAlmaKategorisi
from app.models.talep import Talep, TalepKategorisi
from app.models.core import User

rapor_bp = Blueprint('rapor', __name__)


# ============================================================
# ANA DASHBOARD
# ============================================================

@rapor_bp.route('/')
@login_required
@permission_required('rapor.view')
def dashboard():
    """Raporlama ana sayfası"""
    return render_template('rapor/dashboard.html')


# ============================================================
# İK RAPORLARI
# ============================================================

@rapor_bp.route('/ik')
@login_required
@permission_required('rapor.view')
def ik_rapor():
    """İK raporları"""
    from app.models.base import CalisanDurumu
    
    # Genel istatistikler
    stats = {
        'toplam': Calisan.query.filter_by(is_deleted=False).count(),
        'aktif': Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AKTIF).count(),
        'izinli': Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.IZINLI).count(),
        'ayrildi': Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AYRILDI).count(),
    }
    
    # Departman dağılımı
    departman_dagilim = db.session.query(
        Departman.ad,
        func.count(Calisan.id).label('sayi')
    ).join(Calisan, Calisan.departman_id == Departman.id).filter(
        Calisan.is_deleted == False,
        Calisan.durum == CalisanDurumu.AKTIF
    ).group_by(Departman.ad).all()
    
    # Aylık işe alım (son 12 ay)
    aylik_ise_alim = db.session.query(
        extract('year', Calisan.ise_baslama).label('yil'),
        extract('month', Calisan.ise_baslama).label('ay'),
        func.count(Calisan.id).label('sayi')
    ).filter(
        Calisan.is_deleted == False,
        Calisan.ise_baslama >= date.today() - timedelta(days=365)
    ).group_by('yil', 'ay').order_by('yil', 'ay').all()
    
    return render_template('rapor/ik_rapor.html',
                          stats=stats,
                          departman_dagilim=departman_dagilim,
                          aylik_ise_alim=aylik_ise_alim)


# ============================================================
# MASRAF RAPORLARI
# ============================================================

@rapor_bp.route('/masraf')
@login_required
@permission_required('rapor.view')
def masraf_rapor():
    """Masraf raporları"""
    yil = request.args.get('yil', date.today().year, type=int)
    ay = request.args.get('ay', type=int)
    
    # Genel istatistikler
    query = Masraf.query.filter_by(is_deleted=False)
    if yil:
        query = query.filter(extract('year', Masraf.masraf_tarihi) == yil)
    if ay:
        query = query.filter(extract('month', Masraf.masraf_tarihi) == ay)
    
    stats = {
        'toplam_tutar': query.with_entities(func.sum(Masraf.tl_karsiligi)).scalar() or 0,
        'toplam_adet': query.count(),
        'onaylanan': query.filter(Masraf.durum == 'onaylandi').with_entities(func.sum(Masraf.tl_karsiligi)).scalar() or 0,
        'bekleyen': query.filter(Masraf.durum == 'onay_bekliyor').count(),
    }
    
    # Kategori dağılımı
    kategori_dagilim = db.session.query(
        MasrafKategorisi.ad,
        func.sum(Masraf.tl_karsiligi).label('toplam'),
        func.count(Masraf.id).label('adet')
    ).join(Masraf, Masraf.kategori_id == MasrafKategorisi.id).filter(
        Masraf.is_deleted == False,
        extract('year', Masraf.masraf_tarihi) == yil
    ).group_by(MasrafKategorisi.ad).all()
    
    # Aylık trend
    aylik_trend = db.session.query(
        extract('month', Masraf.masraf_tarihi).label('ay'),
        func.sum(Masraf.tl_karsiligi).label('toplam')
    ).filter(
        Masraf.is_deleted == False,
        extract('year', Masraf.masraf_tarihi) == yil
    ).group_by('ay').order_by('ay').all()
    
    return render_template('rapor/masraf_rapor.html',
                          stats=stats,
                          kategori_dagilim=kategori_dagilim,
                          aylik_trend=aylik_trend,
                          yil=yil,
                          ay=ay)


# ============================================================
# SÖZLEŞME RAPORLARI
# ============================================================

@rapor_bp.route('/sozlesme')
@login_required
@permission_required('rapor.view')
def sozlesme_rapor():
    """Sözleşme raporları"""
    # Genel istatistikler
    stats = {
        'toplam': Sozlesme.query.filter_by(is_deleted=False).count(),
        'aktif': Sozlesme.query.filter_by(is_deleted=False, durum='aktif').count(),
        'sona_eren': Sozlesme.query.filter_by(is_deleted=False, durum='sona_erdi').count(),
        'toplam_deger': Sozlesme.query.filter_by(is_deleted=False, durum='aktif').with_entities(
            func.sum(Sozlesme.tutar)
        ).scalar() or 0,
    }
    
    # Tip dağılımı
    tip_dagilim = db.session.query(
        SozlesmeTipi.ad,
        func.count(Sozlesme.id).label('adet'),
        func.sum(Sozlesme.tutar).label('toplam')
    ).join(Sozlesme, Sozlesme.tip_id == SozlesmeTipi.id).filter(
        Sozlesme.is_deleted == False,
        Sozlesme.durum == 'aktif'
    ).group_by(SozlesmeTipi.ad).all()
    
    # Yaklaşan bitiş (30 gün)
    yaklasan = Sozlesme.query.filter(
        Sozlesme.is_deleted == False,
        Sozlesme.durum == 'aktif',
        Sozlesme.bitis_tarihi <= date.today() + timedelta(days=30),
        Sozlesme.bitis_tarihi >= date.today()
    ).order_by(Sozlesme.bitis_tarihi).all()
    
    return render_template('rapor/sozlesme_rapor.html',
                          stats=stats,
                          tip_dagilim=tip_dagilim,
                          yaklasan=yaklasan)


# ============================================================
# SATIN ALMA RAPORLARI
# ============================================================

@rapor_bp.route('/satinalma')
@login_required
@permission_required('rapor.view')
def satinalma_rapor():
    """Satın alma raporları"""
    yil = request.args.get('yil', date.today().year, type=int)
    
    # Genel istatistikler
    stats = {
        'toplam_talep': SatinAlmaTalebi.query.filter_by(is_deleted=False).filter(
            extract('year', SatinAlmaTalebi.talep_tarihi) == yil
        ).count(),
        'toplam_siparis': SatinAlmaSiparisi.query.filter_by(is_deleted=False).filter(
            extract('year', SatinAlmaSiparisi.siparis_tarihi) == yil
        ).count(),
        'toplam_harcama': SatinAlmaSiparisi.query.filter_by(is_deleted=False).filter(
            extract('year', SatinAlmaSiparisi.siparis_tarihi) == yil
        ).with_entities(func.sum(SatinAlmaSiparisi.toplam_tutar)).scalar() or 0,
        'bekleyen': SatinAlmaTalebi.query.filter_by(is_deleted=False, durum='onay_bekliyor').count(),
    }
    
    # Kategori dağılımı
    kategori_dagilim = db.session.query(
        SatinAlmaKategorisi.ad,
        func.count(SatinAlmaTalebi.id).label('adet')
    ).join(SatinAlmaTalebi, SatinAlmaTalebi.kategori_id == SatinAlmaKategorisi.id).filter(
        SatinAlmaTalebi.is_deleted == False,
        extract('year', SatinAlmaTalebi.talep_tarihi) == yil
    ).group_by(SatinAlmaKategorisi.ad).all()
    
    # Aylık harcama
    aylik_harcama = db.session.query(
        extract('month', SatinAlmaSiparisi.siparis_tarihi).label('ay'),
        func.sum(SatinAlmaSiparisi.toplam_tutar).label('toplam')
    ).filter(
        SatinAlmaSiparisi.is_deleted == False,
        extract('year', SatinAlmaSiparisi.siparis_tarihi) == yil
    ).group_by('ay').order_by('ay').all()
    
    return render_template('rapor/satinalma_rapor.html',
                          stats=stats,
                          kategori_dagilim=kategori_dagilim,
                          aylik_harcama=aylik_harcama,
                          yil=yil)


# ============================================================
# TALEP RAPORLARI
# ============================================================

@rapor_bp.route('/talep')
@login_required
@permission_required('rapor.view')
def talep_rapor():
    """Talep raporları"""
    yil = request.args.get('yil', date.today().year, type=int)
    ay = request.args.get('ay', type=int)
    
    query = Talep.query.filter_by(is_deleted=False)
    if yil:
        query = query.filter(extract('year', Talep.created_at) == yil)
    if ay:
        query = query.filter(extract('month', Talep.created_at) == ay)
    
    # Genel istatistikler
    stats = {
        'toplam': query.count(),
        'acik': query.filter(Talep.durum.in_(['acik', 'atandi', 'devam_ediyor', 'beklemede'])).count(),
        'cozuldu': query.filter(Talep.durum == 'cozuldu').count(),
        'kapatildi': query.filter(Talep.durum == 'kapatildi').count(),
    }
    
    # Kategori dağılımı
    kategori_dagilim = db.session.query(
        TalepKategorisi.ad,
        func.count(Talep.id).label('adet')
    ).join(Talep, Talep.kategori_id == TalepKategorisi.id).filter(
        Talep.is_deleted == False,
        extract('year', Talep.created_at) == yil
    ).group_by(TalepKategorisi.ad).all()
    
    # Öncelik dağılımı
    oncelik_dagilim = db.session.query(
        Talep.oncelik,
        func.count(Talep.id).label('adet')
    ).filter(
        Talep.is_deleted == False,
        extract('year', Talep.created_at) == yil
    ).group_by(Talep.oncelik).all()
    
    # Aylık trend
    aylik_trend = db.session.query(
        extract('month', Talep.created_at).label('ay'),
        func.count(Talep.id).label('toplam')
    ).filter(
        Talep.is_deleted == False,
        extract('year', Talep.created_at) == yil
    ).group_by('ay').order_by('ay').all()
    
    return render_template('rapor/talep_rapor.html',
                          stats=stats,
                          kategori_dagilim=kategori_dagilim,
                          oncelik_dagilim=oncelik_dagilim,
                          aylik_trend=aylik_trend,
                          yil=yil,
                          ay=ay)


# ============================================================
# EXCEL EXPORT
# ============================================================

@rapor_bp.route('/export/<modul>')
@login_required
@permission_required('rapor.export')
def export_excel(modul):
    """Excel export"""
    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
    except ImportError:
        return "openpyxl yüklü değil", 500
    
    wb = openpyxl.Workbook()
    ws = wb.active
    
    if modul == 'masraf':
        ws.title = 'Masraflar'
        headers = ['Tarih', 'Başlık', 'Kategori', 'Tutar', 'Durum', 'Çalışan']
        ws.append(headers)
        
        masraflar = Masraf.query.filter_by(is_deleted=False).order_by(Masraf.masraf_tarihi.desc()).all()
        for m in masraflar:
            ws.append([
                m.masraf_tarihi.strftime('%d.%m.%Y') if m.masraf_tarihi else '',
                m.baslik,
                m.kategori.ad if m.kategori else '',
                float(m.tl_karsiligi or 0),
                m.durum_text,
                m.calisan.ad_soyad if m.calisan else ''
            ])
    
    elif modul == 'sozlesme':
        ws.title = 'Sözleşmeler'
        headers = ['No', 'Başlık', 'Tip', 'Taraf', 'Başlangıç', 'Bitiş', 'Tutar', 'Durum']
        ws.append(headers)
        
        sozlesmeler = Sozlesme.query.filter_by(is_deleted=False).order_by(Sozlesme.bitis_tarihi).all()
        for s in sozlesmeler:
            ws.append([
                s.sozlesme_no or str(s.id),
                s.baslik,
                s.tip.ad if s.tip else '',
                s.taraf_adi,
                s.baslangic_tarihi.strftime('%d.%m.%Y'),
                s.bitis_tarihi.strftime('%d.%m.%Y'),
                float(s.tutar or 0),
                s.durum_text
            ])
    
    elif modul == 'talep':
        ws.title = 'Talepler'
        headers = ['No', 'Konu', 'Kategori', 'Öncelik', 'Durum', 'Oluşturan', 'Tarih']
        ws.append(headers)
        
        talepler = Talep.query.filter_by(is_deleted=False).order_by(Talep.created_at.desc()).all()
        for t in talepler:
            ws.append([
                t.talep_no,
                t.konu,
                t.kategori.ad if t.kategori else '',
                t.oncelik_text,
                t.durum_text,
                t.olusturan.full_name if t.olusturan else '',
                t.created_at.strftime('%d.%m.%Y %H:%M')
            ])
    
    else:
        return "Geçersiz modül", 400
    
    # Sütun genişliklerini ayarla
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 15
    
    # Response
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={modul}_rapor.xlsx'}
    )


# ============================================================
# API - Grafik verileri
# ============================================================

@rapor_bp.route('/api/ozet')
@login_required
@permission_required('rapor.view')
def api_ozet():
    """Genel özet API"""
    from app.models.base import CalisanDurumu
    
    data = {
        'calisan': Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AKTIF).count(),
        'sozlesme': Sozlesme.query.filter_by(is_deleted=False, durum='aktif').count(),
        'acik_talep': Talep.query.filter(
            Talep.is_deleted == False,
            Talep.durum.in_(['acik', 'atandi', 'devam_ediyor', 'beklemede'])
        ).count(),
        'bu_ay_masraf': Masraf.query.filter(
            Masraf.is_deleted == False,
            extract('month', Masraf.masraf_tarihi) == date.today().month,
            extract('year', Masraf.masraf_tarihi) == date.today().year
        ).with_entities(func.sum(Masraf.tl_karsiligi)).scalar() or 0,
    }
    
    return jsonify(data)
