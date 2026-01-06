# -*- coding: utf-8 -*-
"""
TG Portal - Filo Routes
Araç yönetimi
"""
import os
import pandas as pd
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, make_response
from flask_login import login_required, current_user
from datetime import datetime, date
from werkzeug.utils import secure_filename
from app import db
from app.models.filo import Arac, FiloIslem, YakitKayit, Sigorta, Muayene, Kaza
from app.models.filo_update import AracTeslim, KazaFotograf, IkameArac, TrafikCezasi, VARSAYILAN_AKSESUARLAR
from app.models.base import AracDurumu, YakitTipi, IslemTipi, CalisanDurumu
from app.models.ik import Calisan
from app.models.proje import Proje
from app.models.tedarikci import Tedarikci
from app.utils import permission_required

filo_bp = Blueprint('filo', __name__)


@filo_bp.route('/')
@login_required
@permission_required('filo.view')
def liste():
    """Araç listesi"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    durum = request.args.get('durum', '')
    proje_id = request.args.get('proje_id', type=int)
    
    query = Arac.query.filter_by(is_deleted=False)
    
    if search:
        query = query.filter(
            db.or_(
                Arac.plaka.ilike(f'%{search}%'),
                Arac.marka.ilike(f'%{search}%'),
                Arac.model.ilike(f'%{search}%')
            )
        )
    
    if durum:
        query = query.filter_by(durum=AracDurumu(durum))
    
    if proje_id:
        query = query.filter_by(proje_id=proje_id)
    
    query = query.order_by(Arac.plaka)
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    # Filtre için projeler
    projeler = Proje.query.filter_by(is_deleted=False, aktif=True).order_by(Proje.ad).all()
    
    return render_template('filo/liste.html',
                         araclar=pagination.items,
                         pagination=pagination,
                         projeler=projeler,
                         durumlar=AracDurumu)


@filo_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('filo.create')
def ekle():
    """Yeni araç ekle"""
    if request.method == 'POST':
        arac = Arac(
            plaka=request.form.get('plaka', '').upper().replace(' ', ''),
            marka=request.form.get('marka'),
            model=request.form.get('model'),
            model_yili=request.form.get('model_yili') or None,
            renk=request.form.get('renk'),
            sasi_no=request.form.get('sasi_no'),
            motor_no=request.form.get('motor_no'),
            yakit_tipi=YakitTipi(request.form.get('yakit_tipi')) if request.form.get('yakit_tipi') else None,
            motor_hacmi=request.form.get('motor_hacmi') or None,
            vites_tipi=request.form.get('vites_tipi'),
            km=request.form.get('km') or 0,
            sahiplik_tipi=request.form.get('sahiplik_tipi'),
            kira_baslangic=request.form.get('kira_baslangic') or None,
            kira_bitis=request.form.get('kira_bitis') or None,
            aylik_kira=request.form.get('aylik_kira') or None,
            atanan_calisan_id=request.form.get('atanan_calisan_id') or None,
            proje_id=request.form.get('proje_id') or None,
            durum=AracDurumu(request.form.get('durum')) if request.form.get('durum') else AracDurumu.AKTIF,
            notlar=request.form.get('notlar')
        )
        
        try:
            db.session.add(arac)
            db.session.commit()
            flash('Araç başarıyla eklendi.', 'success')
            return redirect(url_for('filo.detay', id=arac.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'danger')
    
    calisanlar = Calisan.query.filter_by(is_deleted=False).order_by(Calisan.ad).all()
    projeler = Proje.query.filter_by(is_deleted=False, aktif=True).order_by(Proje.ad).all()
    
    return render_template('filo/form.html',
                         arac=None,
                         calisanlar=calisanlar,
                         projeler=projeler,
                         durumlar=AracDurumu,
                         yakit_tipleri=YakitTipi)


@filo_bp.route('/<int:id>')
@login_required
@permission_required('filo.view')
def detay(id):
    """Araç detayı"""
    arac = Arac.query.get_or_404(id)
    
    son_islemler = arac.islemler.order_by(FiloIslem.tarih.desc()).limit(5).all()
    son_yakit = arac.yakit_kayitlari.order_by(YakitKayit.tarih.desc()).limit(5).all()
    
    return render_template('filo/detay.html',
                         arac=arac,
                         son_islemler=son_islemler,
                         son_yakit=son_yakit)


@filo_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('filo.edit')
def duzenle(id):
    """Araç düzenle"""
    arac = Arac.query.get_or_404(id)
    
    if request.method == 'POST':
        arac.plaka = request.form.get('plaka', '').upper().replace(' ', '')
        arac.marka = request.form.get('marka')
        arac.model = request.form.get('model')
        arac.model_yili = request.form.get('model_yili') or None
        arac.renk = request.form.get('renk')
        arac.sasi_no = request.form.get('sasi_no')
        arac.motor_no = request.form.get('motor_no')
        arac.yakit_tipi = YakitTipi(request.form.get('yakit_tipi')) if request.form.get('yakit_tipi') else None
        arac.motor_hacmi = request.form.get('motor_hacmi') or None
        arac.vites_tipi = request.form.get('vites_tipi')
        arac.km = request.form.get('km') or 0
        arac.sahiplik_tipi = request.form.get('sahiplik_tipi')
        arac.kira_baslangic = request.form.get('kira_baslangic') or None
        arac.kira_bitis = request.form.get('kira_bitis') or None
        arac.aylik_kira = request.form.get('aylik_kira') or None
        arac.atanan_calisan_id = request.form.get('atanan_calisan_id') or None
        arac.proje_id = request.form.get('proje_id') or None
        arac.durum = AracDurumu(request.form.get('durum')) if request.form.get('durum') else AracDurumu.AKTIF
        arac.notlar = request.form.get('notlar')
        
        try:
            db.session.commit()
            flash('Araç başarıyla güncellendi.', 'success')
            return redirect(url_for('filo.detay', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'danger')
    
    calisanlar = Calisan.query.filter_by(is_deleted=False).order_by(Calisan.ad).all()
    projeler = Proje.query.filter_by(is_deleted=False, aktif=True).order_by(Proje.ad).all()
    
    return render_template('filo/form.html',
                         arac=arac,
                         calisanlar=calisanlar,
                         projeler=projeler,
                         durumlar=AracDurumu,
                         yakit_tipleri=YakitTipi)


@filo_bp.route('/<int:id>/sil')
@login_required
@permission_required('filo.delete')
def sil(id):
    """Araç sil (soft delete)"""
    arac = Arac.query.get_or_404(id)
    arac.is_deleted = True
    arac.deleted_at = datetime.utcnow()
    arac.deleted_by = current_user.id
    db.session.commit()
    flash('Araç silindi.', 'success')
    return redirect(url_for('filo.liste'))


# ==================== YAKIT ====================

@filo_bp.route('/<int:id>/yakit/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('filo.edit')
def yakit_ekle(id):
    """Yakıt kaydı ekle"""
    arac = Arac.query.get_or_404(id)
    
    if request.method == 'POST':
        kayit = YakitKayit(
            arac_id=id,
            tarih=datetime.strptime(request.form.get('tarih'), '%Y-%m-%dT%H:%M') if request.form.get('tarih') else datetime.now(),
            km=request.form.get('km'),
            yakit_tipi=arac.yakit_tipi,
            litre=request.form.get('litre'),
            birim_fiyat=request.form.get('birim_fiyat'),
            tutar=request.form.get('tutar'),
            istasyon_adi=request.form.get('istasyon_adi'),
            full_depo=request.form.get('full_depo') == 'on'
        )
        
        # Araç km güncelle
        if kayit.km and int(kayit.km) > (arac.km or 0):
            arac.km = kayit.km
            arac.son_km_guncelleme = datetime.utcnow()
        
        db.session.add(kayit)
        db.session.commit()
        flash('Yakıt kaydı eklendi.', 'success')
        return redirect(url_for('filo.detay', id=id))
    
    return render_template('filo/yakit_form.html', arac=arac)


# ==================== İŞLEM ====================

@filo_bp.route('/<int:id>/islem/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('filo.edit')
def islem_ekle(id):
    """İşlem kaydı ekle (bakım, tamir vb.)"""
    arac = Arac.query.get_or_404(id)
    
    if request.method == 'POST':
        islem = FiloIslem(
            arac_id=id,
            islem_tipi=IslemTipi(request.form.get('islem_tipi')),
            tarih=datetime.strptime(request.form.get('tarih'), '%Y-%m-%d').date() if request.form.get('tarih') else date.today(),
            km=request.form.get('km'),
            tutar=request.form.get('tutar'),
            kdv=request.form.get('kdv'),
            toplam=request.form.get('toplam'),
            aciklama=request.form.get('aciklama'),
            fatura_no=request.form.get('fatura_no'),
            sonraki_tarih=datetime.strptime(request.form.get('sonraki_tarih'), '%Y-%m-%d').date() if request.form.get('sonraki_tarih') else None,
            sonraki_km=request.form.get('sonraki_km')
        )
        
        # Araç km güncelle
        if islem.km and int(islem.km) > (arac.km or 0):
            arac.km = islem.km
            arac.son_km_guncelleme = datetime.utcnow()
        
        db.session.add(islem)
        db.session.commit()
        flash('İşlem kaydı eklendi.', 'success')
        return redirect(url_for('filo.detay', id=id))
    
    tedarikciler = Tedarikci.query.filter_by(is_deleted=False).order_by(Tedarikci.unvan).all()
    return render_template('filo/islem_form.html', arac=arac, islem_tipleri=IslemTipi, tedarikciler=tedarikciler)


# ==================== API ====================

@filo_bp.route('/api/araclar')
@login_required
def api_araclar():
    """Select2 için araç arama"""
    q = request.args.get('q', '')
    query = Arac.query.filter_by(is_deleted=False)
    
    if q:
        query = query.filter(
            db.or_(
                Arac.plaka.ilike(f'%{q}%'),
                Arac.marka.ilike(f'%{q}%')
            )
        )
    
    araclar = query.order_by(Arac.plaka).limit(20).all()
    return jsonify([{'id': a.id, 'text': a.display_name} for a in araclar])


# ==================== YAKIT EXCEL IMPORT ====================

@filo_bp.route('/yakit/import', methods=['GET', 'POST'])
@login_required
@permission_required('filo.create')
def yakit_import():
    """Yakıt verilerini Excel'den içe aktar"""
    if request.method == 'POST':
        if 'excel_file' not in request.files:
            flash('Dosya seçilmedi.', 'danger')
            return redirect(request.url)
        
        file = request.files['excel_file']
        if file.filename == '':
            flash('Dosya seçilmedi.', 'danger')
            return redirect(request.url)
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('Sadece Excel dosyaları (.xlsx, .xls) kabul edilir.', 'danger')
            return redirect(request.url)
        
        try:
            # Excel'i oku
            df = pd.read_excel(file)
            
            # Kolon mapping
            kolon_mapping = {
                'PLAKA': 'plaka',
                'YAKIT TİPİ': 'yakit_tipi',
                'İSTASYON': 'istasyon',
                'İŞLEM TARİHİ': 'tarih',
                'MİKTAR': 'miktar',
                'TUTAR': 'tutar'
            }
            
            # Gerekli kolonları kontrol et
            eksik_kolonlar = [k for k in ['PLAKA', 'İŞLEM TARİHİ', 'MİKTAR', 'TUTAR'] if k not in df.columns]
            if eksik_kolonlar:
                flash(f'Eksik kolonlar: {", ".join(eksik_kolonlar)}', 'danger')
                return redirect(request.url)
            
            eklenen = 0
            atlanan = 0
            hatalar = []
            
            for index, row in df.iterrows():
                try:
                    # Plakayı normalize et
                    plaka = str(row['PLAKA']).upper().replace(' ', '').strip()
                    
                    # Aracı bul
                    arac = Arac.query.filter_by(plaka=plaka, is_deleted=False).first()
                    if not arac:
                        hatalar.append(f"Satır {index+2}: {plaka} plakası sistemde bulunamadı")
                        atlanan += 1
                        continue
                    
                    # Tarihi parse et
                    tarih_str = str(row['İŞLEM TARİHİ'])
                    try:
                        # "31/12/2025 22:46" formatı
                        tarih = datetime.strptime(tarih_str, '%d/%m/%Y %H:%M')
                    except:
                        try:
                            # Alternatif formatlar
                            tarih = pd.to_datetime(row['İŞLEM TARİHİ'])
                        except:
                            hatalar.append(f"Satır {index+2}: Tarih formatı hatalı: {tarih_str}")
                            atlanan += 1
                            continue
                    
                    # Miktarı parse et (31,65 LT formatı)
                    miktar_str = str(row['MİKTAR']).replace(' LT', '').replace(',', '.').strip()
                    try:
                        litre = Decimal(miktar_str)
                    except:
                        hatalar.append(f"Satır {index+2}: Miktar formatı hatalı: {row['MİKTAR']}")
                        atlanan += 1
                        continue
                    
                    # Tutarı parse et (1695,17 TL formatı)
                    tutar_str = str(row['TUTAR']).replace(' TL', '').replace(',', '.').strip()
                    try:
                        tutar = Decimal(tutar_str)
                    except:
                        hatalar.append(f"Satır {index+2}: Tutar formatı hatalı: {row['TUTAR']}")
                        atlanan += 1
                        continue
                    
                    # Birim fiyat hesapla
                    birim_fiyat = tutar / litre if litre > 0 else Decimal('0')
                    
                    # Yakıt tipini belirle
                    yakit_tipi_str = str(row.get('YAKIT TİPİ', '')).upper().strip()
                    if 'MOTORİN' in yakit_tipi_str or 'DIZEL' in yakit_tipi_str:
                        yakit_tipi = YakitTipi.DIZEL
                    elif 'KURŞUNSUZ' in yakit_tipi_str or 'BENZİN' in yakit_tipi_str:
                        yakit_tipi = YakitTipi.BENZIN
                    elif 'LPG' in yakit_tipi_str:
                        yakit_tipi = YakitTipi.LPG
                    else:
                        yakit_tipi = arac.yakit_tipi or YakitTipi.DIZEL
                    
                    # İstasyon adı
                    istasyon = str(row.get('İSTASYON', '')).strip()[:100]
                    
                    # Duplicate kontrolü (aynı araç, aynı tarih, aynı miktar)
                    mevcut = YakitKayit.query.filter(
                        YakitKayit.arac_id == arac.id,
                        YakitKayit.tarih == tarih,
                        YakitKayit.litre == litre
                    ).first()
                    
                    if mevcut:
                        atlanan += 1
                        continue
                    
                    # Yakıt kaydı oluştur
                    yakit = YakitKayit(
                        arac_id=arac.id,
                        tarih=tarih,
                        km=arac.km or 0,  # Mevcut km (Excel'de yok)
                        yakit_tipi=yakit_tipi,
                        litre=litre,
                        birim_fiyat=birim_fiyat,
                        tutar=tutar,
                        istasyon_adi=istasyon,
                        full_depo=True
                    )
                    
                    db.session.add(yakit)
                    eklenen += 1
                    
                except Exception as e:
                    hatalar.append(f"Satır {index+2}: {str(e)}")
                    atlanan += 1
            
            db.session.commit()
            
            flash(f'{eklenen} yakıt kaydı eklendi, {atlanan} kayıt atlandı.', 'success')
            
            if hatalar[:10]:  # İlk 10 hatayı göster
                for hata in hatalar[:10]:
                    flash(hata, 'warning')
                if len(hatalar) > 10:
                    flash(f'... ve {len(hatalar) - 10} hata daha', 'warning')
            
            return redirect(url_for('filo.yakit_liste'))
            
        except Exception as e:
            flash(f'Excel okuma hatası: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('filo/yakit_import.html')


@filo_bp.route('/yakit')
@login_required
@permission_required('filo.view')
def yakit_liste():
    """Yakıt kayıtları listesi"""
    page = request.args.get('page', 1, type=int)
    arac_id = request.args.get('arac_id', type=int)
    baslangic = request.args.get('baslangic')
    bitis = request.args.get('bitis')
    
    query = YakitKayit.query.join(Arac).filter(Arac.is_deleted == False)
    
    if arac_id:
        query = query.filter(YakitKayit.arac_id == arac_id)
    
    if baslangic:
        query = query.filter(YakitKayit.tarih >= datetime.strptime(baslangic, '%Y-%m-%d'))
    
    if bitis:
        query = query.filter(YakitKayit.tarih <= datetime.strptime(bitis, '%Y-%m-%d'))
    
    query = query.order_by(YakitKayit.tarih.desc())
    pagination = query.paginate(page=page, per_page=50, error_out=False)
    
    # Özet istatistikler
    toplam_litre = db.session.query(db.func.sum(YakitKayit.litre)).scalar() or 0
    toplam_tutar = db.session.query(db.func.sum(YakitKayit.tutar)).scalar() or 0
    
    araclar = Arac.query.filter_by(is_deleted=False).order_by(Arac.plaka).all()
    
    return render_template('filo/yakit_liste.html',
                          kayitlar=pagination.items,
                          pagination=pagination,
                          araclar=araclar,
                          toplam_litre=toplam_litre,
                          toplam_tutar=toplam_tutar)


# ==================== ARAÇ TESLİM/İADE ====================

@filo_bp.route('/<int:id>/teslim', methods=['GET', 'POST'])
@login_required
@permission_required('filo.edit')
def arac_teslim(id):
    """Araç teslim formu"""
    arac = Arac.query.get_or_404(id)
    
    if request.method == 'POST':
        teslim = AracTeslim(
            arac_id=arac.id,
            islem_tipi='teslim',
            tarih=datetime.now(),
            km=int(request.form.get('km', 0)),
            yakit_durumu=request.form.get('yakit_durumu'),
            teslim_eden_id=current_user.id,
            teslim_alan_calisan_id=request.form.get('teslim_alan_calisan_id') or None,
            aksesuarlar=request.form.getlist('aksesuarlar'),
            mevcut_hasarlar=request.form.get('mevcut_hasarlar'),
            notlar=request.form.get('notlar'),
            imza_teslim_eden=request.form.get('imza_teslim_eden'),
            imza_teslim_alan=request.form.get('imza_teslim_alan')
        )
        
        # Fotoğrafları kaydet
        fotograflar = []
        if 'fotograflar' in request.files:
            for file in request.files.getlist('fotograflar'):
                if file and file.filename:
                    filename = secure_filename(f"{arac.plaka}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    upload_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'teslim')
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, filename))
                    fotograflar.append(f"teslim/{filename}")
        
        teslim.fotograflar = fotograflar
        
        # Aracı güncelle
        arac.km = teslim.km
        arac.son_km_guncelleme = datetime.now()
        arac.atanan_calisan_id = int(request.form.get('teslim_alan_calisan_id')) if request.form.get('teslim_alan_calisan_id') else None
        arac.atama_tarihi = datetime.now().date() if request.form.get('teslim_alan_calisan_id') else None
        
        db.session.add(teslim)
        db.session.commit()
        
        flash('Araç teslim kaydı oluşturuldu.', 'success')
        return redirect(url_for('filo.teslim_detay', id=teslim.id))
    
    calisanlar = Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AKTIF).order_by(Calisan.ad).all()
    
    return render_template('filo/teslim_form.html',
                          arac=arac,
                          islem_tipi='teslim',
                          calisanlar=calisanlar,
                          aksesuarlar=VARSAYILAN_AKSESUARLAR)


@filo_bp.route('/<int:id>/iade', methods=['GET', 'POST'])
@login_required
@permission_required('filo.edit')
def arac_iade(id):
    """Araç iade formu"""
    arac = Arac.query.get_or_404(id)
    
    # Son teslim kaydını bul
    son_teslim = AracTeslim.query.filter_by(
        arac_id=arac.id, 
        islem_tipi='teslim'
    ).order_by(AracTeslim.tarih.desc()).first()
    
    if request.method == 'POST':
        iade = AracTeslim(
            arac_id=arac.id,
            islem_tipi='iade',
            tarih=datetime.now(),
            km=int(request.form.get('km', 0)),
            yakit_durumu=request.form.get('yakit_durumu'),
            teslim_eden_calisan_id=arac.atanan_calisan_id,
            teslim_alan_id=current_user.id,
            aksesuarlar=request.form.getlist('aksesuarlar'),
            mevcut_hasarlar=request.form.get('mevcut_hasarlar'),
            yeni_hasar=request.form.get('yeni_hasar') == 'on',
            yeni_hasar_aciklama=request.form.get('yeni_hasar_aciklama'),
            notlar=request.form.get('notlar'),
            imza_teslim_eden=request.form.get('imza_teslim_eden'),
            imza_teslim_alan=request.form.get('imza_teslim_alan')
        )
        
        # Fotoğrafları kaydet
        fotograflar = []
        if 'fotograflar' in request.files:
            for file in request.files.getlist('fotograflar'):
                if file and file.filename:
                    filename = secure_filename(f"{arac.plaka}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    upload_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'teslim')
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, filename))
                    fotograflar.append(f"teslim/{filename}")
        
        iade.fotograflar = fotograflar
        
        # Aracı güncelle
        arac.km = iade.km
        arac.son_km_guncelleme = datetime.now()
        arac.atanan_calisan_id = None
        arac.atama_tarihi = None
        
        db.session.add(iade)
        db.session.commit()
        
        flash('Araç iade kaydı oluşturuldu.', 'success')
        return redirect(url_for('filo.teslim_detay', id=iade.id))
    
    return render_template('filo/teslim_form.html',
                          arac=arac,
                          islem_tipi='iade',
                          son_teslim=son_teslim,
                          aksesuarlar=VARSAYILAN_AKSESUARLAR)


@filo_bp.route('/teslim/<int:id>')
@login_required
@permission_required('filo.view')
def teslim_detay(id):
    """Teslim/iade detayı"""
    teslim = AracTeslim.query.get_or_404(id)
    return render_template('filo/teslim_detay.html', 
                          teslim=teslim,
                          aksesuarlar=VARSAYILAN_AKSESUARLAR)


@filo_bp.route('/teslim/<int:id>/pdf')
@login_required
@permission_required('filo.view')
def teslim_pdf(id):
    """Teslim/iade PDF oluştur"""
    teslim = AracTeslim.query.get_or_404(id)
    
    # HTML şablonunu render et ve PDF'e çevir
    html = render_template('filo/teslim_pdf.html', 
                          teslim=teslim,
                          aksesuarlar=VARSAYILAN_AKSESUARLAR)
    
    # WeasyPrint veya başka bir PDF kütüphanesi ile PDF oluştur
    # Şimdilik HTML olarak döndür
    from flask import make_response
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    # response.headers['Content-Disposition'] = f'attachment; filename=teslim_{teslim.id}.pdf'
    return response


@filo_bp.route('/teslimler')
@login_required
@permission_required('filo.view')
def teslim_liste():
    """Teslim/iade kayıtları listesi"""
    page = request.args.get('page', 1, type=int)
    arac_id = request.args.get('arac_id', type=int)
    islem_tipi = request.args.get('islem_tipi')
    
    query = AracTeslim.query.join(Arac).filter(Arac.is_deleted == False)
    
    if arac_id:
        query = query.filter(AracTeslim.arac_id == arac_id)
    
    if islem_tipi:
        query = query.filter(AracTeslim.islem_tipi == islem_tipi)
    
    query = query.order_by(AracTeslim.tarih.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    araclar = Arac.query.filter_by(is_deleted=False).order_by(Arac.plaka).all()
    
    return render_template('filo/teslim_liste.html',
                          teslimler=pagination.items,
                          pagination=pagination,
                          araclar=araclar)


# ==================== KAZA YÖNETİMİ ====================

@filo_bp.route('/<int:id>/kaza/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('filo.create')
def kaza_ekle(id):
    """Kaza kaydı ekle"""
    arac = Arac.query.get_or_404(id)
    
    if request.method == 'POST':
        # En az 1 fotoğraf zorunlu
        if 'fotograflar' not in request.files or not request.files.getlist('fotograflar')[0].filename:
            flash('En az 1 fotoğraf yüklemeniz zorunludur.', 'danger')
            return redirect(request.url)
        
        kaza = Kaza(
            arac_id=arac.id,
            surucu_id=request.form.get('surucu_id') or arac.atanan_calisan_id,
            tarih=datetime.strptime(request.form['tarih'], '%Y-%m-%dT%H:%M'),
            konum=request.form.get('konum'),
            kusur_orani=request.form.get('kusur_orani') or None,
            hasar_tutari=request.form.get('hasar_tutari') or None,
            sigorta_karsiladi=request.form.get('sigorta_karsiladi') or None,
            yaralanma=request.form.get('yaralanma') == 'on',
            aciklama=request.form.get('aciklama'),
            tutanak_no=request.form.get('tutanak_no'),
            durum='acik',
            onay_durumu='bekliyor'
        )
        
        db.session.add(kaza)
        db.session.flush()  # ID almak için
        
        # Fotoğrafları kaydet
        for file in request.files.getlist('fotograflar'):
            if file and file.filename:
                filename = secure_filename(f"kaza_{kaza.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                upload_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'kaza')
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                
                foto = KazaFotograf(
                    kaza_id=kaza.id,
                    dosya_adi=file.filename,
                    dosya_yolu=f"kaza/{filename}",
                    dosya_boyut=file.content_length,
                    mime_type=file.content_type,
                    yukleyen_id=current_user.id
                )
                db.session.add(foto)
        
        db.session.commit()
        
        flash('Kaza kaydı oluşturuldu. Filo yöneticisi onayı bekleniyor.', 'success')
        return redirect(url_for('filo.kaza_detay', id=kaza.id))
    
    calisanlar = Calisan.query.filter_by(is_deleted=False).order_by(Calisan.ad).all()
    
    return render_template('filo/kaza_form.html',
                          arac=arac,
                          calisanlar=calisanlar)


@filo_bp.route('/kaza/<int:id>')
@login_required
@permission_required('filo.view')
def kaza_detay(id):
    """Kaza detayı"""
    kaza = Kaza.query.get_or_404(id)
    return render_template('filo/kaza_detay.html', kaza=kaza)


@filo_bp.route('/kaza/<int:id>/onayla', methods=['POST'])
@login_required
@permission_required('filo.admin')
def kaza_onayla(id):
    """Kaza kaydını onayla"""
    kaza = Kaza.query.get_or_404(id)
    
    kaza.onay_durumu = 'onaylandi'
    kaza.onaylayan_id = current_user.id
    kaza.onay_tarihi = datetime.now()
    
    db.session.commit()
    
    flash('Kaza kaydı onaylandı.', 'success')
    return redirect(url_for('filo.kaza_detay', id=kaza.id))


@filo_bp.route('/kaza/<int:id>/reddet', methods=['POST'])
@login_required
@permission_required('filo.admin')
def kaza_reddet(id):
    """Kaza kaydını reddet"""
    kaza = Kaza.query.get_or_404(id)
    
    kaza.onay_durumu = 'reddedildi'
    kaza.onaylayan_id = current_user.id
    kaza.onay_tarihi = datetime.now()
    kaza.red_nedeni = request.form.get('red_nedeni')
    
    db.session.commit()
    
    flash('Kaza kaydı reddedildi.', 'warning')
    return redirect(url_for('filo.kaza_detay', id=kaza.id))


@filo_bp.route('/kazalar')
@login_required
@permission_required('filo.view')
def kaza_liste():
    """Kaza kayıtları listesi"""
    page = request.args.get('page', 1, type=int)
    arac_id = request.args.get('arac_id', type=int)
    durum = request.args.get('durum')
    onay_durumu = request.args.get('onay_durumu')
    
    query = Kaza.query.join(Arac).filter(Arac.is_deleted == False)
    
    if arac_id:
        query = query.filter(Kaza.arac_id == arac_id)
    
    if durum:
        query = query.filter(Kaza.durum == durum)
    
    if onay_durumu:
        query = query.filter(Kaza.onay_durumu == onay_durumu)
    
    query = query.order_by(Kaza.tarih.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    # Onay bekleyen sayısı
    bekleyen_sayisi = Kaza.query.filter_by(onay_durumu='bekliyor').count()
    
    araclar = Arac.query.filter_by(is_deleted=False).order_by(Arac.plaka).all()
    
    return render_template('filo/kaza_liste.html',
                          kazalar=pagination.items,
                          pagination=pagination,
                          araclar=araclar,
                          bekleyen_sayisi=bekleyen_sayisi)


# ==================== İKAME ARAÇ ====================

@filo_bp.route('/<int:id>/ikame/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('filo.create')
def ikame_ekle(id):
    """İkame araç ekle"""
    arac = Arac.query.get_or_404(id)
    
    if request.method == 'POST':
        ikame = IkameArac(
            asil_arac_id=arac.id,
            plaka=request.form.get('plaka', '').upper().replace(' ', ''),
            marka=request.form.get('marka'),
            model=request.form.get('model'),
            baslangic_tarihi=datetime.strptime(request.form['baslangic_tarihi'], '%Y-%m-%d').date(),
            baslangic_km=request.form.get('baslangic_km') or None,
            tedarikci_id=request.form.get('tedarikci_id') or None,
            gunluk_ucret=request.form.get('gunluk_ucret') or None,
            neden=request.form.get('neden'),
            ilgili_kaza_id=request.form.get('ilgili_kaza_id') or None,
            notlar=request.form.get('notlar'),
            durum='aktif'
        )
        
        db.session.add(ikame)
        db.session.commit()
        
        flash('İkame araç kaydı oluşturuldu.', 'success')
        return redirect(url_for('filo.ikame_detay', id=ikame.id))
    
    tedarikciler = Tedarikci.query.filter_by(is_deleted=False).order_by(Tedarikci.unvan).all()
    kazalar = Kaza.query.filter_by(arac_id=arac.id).order_by(Kaza.tarih.desc()).all()
    
    return render_template('filo/ikame_form.html',
                          arac=arac,
                          tedarikciler=tedarikciler,
                          kazalar=kazalar)


@filo_bp.route('/ikame/<int:id>')
@login_required
@permission_required('filo.view')
def ikame_detay(id):
    """İkame araç detayı"""
    ikame = IkameArac.query.get_or_404(id)
    return render_template('filo/ikame_detay.html', ikame=ikame)


@filo_bp.route('/ikame/<int:id>/iade', methods=['POST'])
@login_required
@permission_required('filo.edit')
def ikame_iade(id):
    """İkame aracı iade et"""
    ikame = IkameArac.query.get_or_404(id)
    
    ikame.bitis_tarihi = datetime.strptime(request.form['bitis_tarihi'], '%Y-%m-%d').date()
    ikame.bitis_km = request.form.get('bitis_km') or None
    ikame.durum = 'iade_edildi'
    
    db.session.commit()
    
    flash('İkame araç iade edildi.', 'success')
    return redirect(url_for('filo.ikame_detay', id=ikame.id))


@filo_bp.route('/ikameler')
@login_required
@permission_required('filo.view')
def ikame_liste():
    """İkame araç listesi"""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum')
    
    query = IkameArac.query.join(Arac, IkameArac.asil_arac_id == Arac.id).filter(Arac.is_deleted == False)
    
    if durum:
        query = query.filter(IkameArac.durum == durum)
    
    query = query.order_by(IkameArac.baslangic_tarihi.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    # Aktif ikame sayısı
    aktif_sayisi = IkameArac.query.filter_by(durum='aktif').count()
    
    return render_template('filo/ikame_liste.html',
                          ikameler=pagination.items,
                          pagination=pagination,
                          aktif_sayisi=aktif_sayisi)


# ==================== TRAFİK CEZASI ====================

@filo_bp.route('/cezalar')
@login_required
@permission_required('filo.view')
def ceza_liste():
    """Trafik cezaları listesi"""
    page = request.args.get('page', 1, type=int)
    arac_id = request.args.get('arac_id', type=int)
    durum = request.args.get('durum')
    
    query = TrafikCezasi.query.join(Arac).filter(Arac.is_deleted == False)
    
    if arac_id:
        query = query.filter(TrafikCezasi.arac_id == arac_id)
    
    if durum:
        query = query.filter(TrafikCezasi.durum == durum)
    
    query = query.order_by(TrafikCezasi.ceza_tarihi.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    # Özet
    bekleyen = TrafikCezasi.query.filter_by(durum='bekliyor').count()
    toplam_borc = db.session.query(db.func.sum(TrafikCezasi.ceza_tutari)).filter(TrafikCezasi.durum == 'bekliyor').scalar() or 0
    
    araclar = Arac.query.filter_by(is_deleted=False).order_by(Arac.plaka).all()
    
    return render_template('filo/ceza_liste.html',
                          cezalar=pagination.items,
                          pagination=pagination,
                          araclar=araclar,
                          bekleyen=bekleyen,
                          toplam_borc=toplam_borc)


@filo_bp.route('/<int:id>/ceza/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('filo.create')
def ceza_ekle(id):
    """Trafik cezası ekle"""
    arac = Arac.query.get_or_404(id)
    
    if request.method == 'POST':
        ceza = TrafikCezasi(
            arac_id=arac.id,
            surucu_id=request.form.get('surucu_id') or arac.atanan_calisan_id,
            ceza_tarihi=datetime.strptime(request.form['ceza_tarihi'], '%Y-%m-%dT%H:%M'),
            teblig_tarihi=datetime.strptime(request.form['teblig_tarihi'], '%Y-%m-%d').date() if request.form.get('teblig_tarihi') else None,
            son_odeme_tarihi=datetime.strptime(request.form['son_odeme_tarihi'], '%Y-%m-%d').date() if request.form.get('son_odeme_tarihi') else None,
            ceza_tutari=request.form.get('ceza_tutari'),
            indirimli_tutar=request.form.get('indirimli_tutar') or None,
            ceza_turu=request.form.get('ceza_turu'),
            ceza_puani=request.form.get('ceza_puani') or 0,
            konum=request.form.get('konum'),
            tutanak_no=request.form.get('tutanak_no'),
            aciklama=request.form.get('aciklama'),
            durum='bekliyor'
        )
        
        db.session.add(ceza)
        db.session.commit()
        
        flash('Trafik cezası kaydedildi.', 'success')
        return redirect(url_for('filo.ceza_detay', id=ceza.id))
    
    calisanlar = Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AKTIF).order_by(Calisan.ad).all()
    
    return render_template('filo/ceza_form.html',
                          arac=arac,
                          calisanlar=calisanlar)


@filo_bp.route('/ceza/<int:id>')
@login_required
@permission_required('filo.view')
def ceza_detay(id):
    """Trafik cezası detayı"""
    ceza = TrafikCezasi.query.get_or_404(id)
    return render_template('filo/ceza_detay.html', ceza=ceza)


@filo_bp.route('/ceza/<int:id>/ode', methods=['POST'])
@login_required
@permission_required('filo.edit')
def ceza_ode(id):
    """Trafik cezası öde"""
    ceza = TrafikCezasi.query.get_or_404(id)
    
    ceza.durum = 'odendi'
    ceza.odeme_tarihi = datetime.strptime(request.form['odeme_tarihi'], '%Y-%m-%d').date()
    ceza.odenen_tutar = request.form.get('odenen_tutar') or ceza.ceza_tutari
    
    db.session.commit()
    
    flash('Ceza ödendi olarak işaretlendi.', 'success')
    return redirect(url_for('filo.ceza_detay', id=ceza.id))


@filo_bp.route('/ceza/<int:id>/yansit', methods=['POST'])
@login_required
@permission_required('filo.edit')
def ceza_yansit(id):
    """Cezayı sürücüye yansıt"""
    ceza = TrafikCezasi.query.get_or_404(id)
    
    ceza.surucuye_yansitildi = True
    ceza.yansitma_tarihi = date.today()
    
    db.session.commit()
    
    flash('Ceza sürücüye yansıtıldı.', 'success')
    return redirect(url_for('filo.ceza_detay', id=ceza.id))
