from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.depo import Depo, UrunKategori, Urun, StokKarti, StokHareketi, StokHareketiKalem
from app.models.proje import Proje
from app.models.tedarikci import Tedarikci
from app.models.ik import Calisan
from app.utils import permission_required
from datetime import datetime, date
import uuid

depo_bp = Blueprint('depo', __name__, url_prefix='/depo')


# ============================================================
# DASHBOARD
# ============================================================

@depo_bp.route('/')
@login_required
@permission_required('depo.view')
def dashboard():
    """Depo dashboard"""
    depolar = Depo.query.filter_by(is_deleted=False, aktif=True).all()
    urunler = Urun.query.filter_by(is_deleted=False, aktif=True).all()
    
    # İstatistikler
    toplam_urun = len(urunler)
    toplam_depo = len(depolar)
    
    # Kritik stok (min_stok altında olan ürünler)
    kritik_stok = []
    for urun in urunler:
        if urun.min_stok and urun.toplam_stok < urun.min_stok:
            kritik_stok.append(urun)
    
    # Son hareketler
    son_hareketler = StokHareketi.query.filter_by(is_deleted=False)\
        .order_by(StokHareketi.tarih.desc()).limit(10).all()
    
    # Toplam stok değeri
    toplam_deger = 0
    for urun in urunler:
        if urun.alis_fiyati:
            toplam_deger += float(urun.toplam_stok) * float(urun.alis_fiyati)
    
    return render_template('depo/dashboard.html',
                          depolar=depolar,
                          toplam_urun=toplam_urun,
                          toplam_depo=toplam_depo,
                          kritik_stok=kritik_stok,
                          son_hareketler=son_hareketler,
                          toplam_deger=toplam_deger)


# ============================================================
# ÜRÜN YÖNETİMİ
# ============================================================

@depo_bp.route('/urunler')
@login_required
@permission_required('depo.view')
def urun_liste():
    """Ürün listesi"""
    urunler = Urun.query.filter_by(is_deleted=False).order_by(Urun.ad).all()
    kategoriler = UrunKategori.query.filter_by(is_deleted=False, aktif=True).all()
    return render_template('depo/urun_liste.html', urunler=urunler, kategoriler=kategoriler)


@depo_bp.route('/urun/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('depo.edit')
def urun_ekle():
    """Yeni ürün ekle"""
    if request.method == 'POST':
        # Kod kontrolü
        kod = request.form.get('kod', '').strip()
        if Urun.query.filter_by(kod=kod, is_deleted=False).first():
            flash('Bu ürün kodu zaten kullanılıyor.', 'danger')
            return redirect(url_for('depo.urun_ekle'))
        
        urun = Urun(
            kod=kod,
            barkod=request.form.get('barkod', '').strip() or None,
            ad=request.form.get('ad', '').strip(),
            aciklama=request.form.get('aciklama', '').strip() or None,
            kategori_id=int(request.form.get('kategori_id')) if request.form.get('kategori_id') else None,
            birim=request.form.get('birim', 'Adet'),
            alis_fiyati=float(request.form.get('alis_fiyati')) if request.form.get('alis_fiyati') else None,
            satis_fiyati=float(request.form.get('satis_fiyati')) if request.form.get('satis_fiyati') else None,
            min_stok=int(request.form.get('min_stok')) if request.form.get('min_stok') else 0,
            max_stok=int(request.form.get('max_stok')) if request.form.get('max_stok') else None,
            aktif=True
        )
        
        db.session.add(urun)
        db.session.commit()
        
        flash('Ürün oluşturuldu.', 'success')
        return redirect(url_for('depo.urun_liste'))
    
    kategoriler = UrunKategori.query.filter_by(is_deleted=False, aktif=True).all()
    return render_template('depo/urun_form.html', urun=None, kategoriler=kategoriler)


@depo_bp.route('/urun/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@permission_required('depo.edit')
def urun_duzenle(id):
    """Ürün düzenle"""
    urun = Urun.query.get_or_404(id)
    
    if request.method == 'POST':
        kod = request.form.get('kod', '').strip()
        existing = Urun.query.filter(Urun.kod == kod, Urun.id != id, Urun.is_deleted == False).first()
        if existing:
            flash('Bu ürün kodu zaten kullanılıyor.', 'danger')
            return redirect(url_for('depo.urun_duzenle', id=id))
        
        urun.kod = kod
        urun.barkod = request.form.get('barkod', '').strip() or None
        urun.ad = request.form.get('ad', '').strip()
        urun.aciklama = request.form.get('aciklama', '').strip() or None
        urun.kategori_id = int(request.form.get('kategori_id')) if request.form.get('kategori_id') else None
        urun.birim = request.form.get('birim', 'Adet')
        urun.alis_fiyati = float(request.form.get('alis_fiyati')) if request.form.get('alis_fiyati') else None
        urun.satis_fiyati = float(request.form.get('satis_fiyati')) if request.form.get('satis_fiyati') else None
        urun.min_stok = int(request.form.get('min_stok')) if request.form.get('min_stok') else 0
        urun.max_stok = int(request.form.get('max_stok')) if request.form.get('max_stok') else None
        urun.aktif = request.form.get('aktif') == 'on'
        
        db.session.commit()
        flash('Ürün güncellendi.', 'success')
        return redirect(url_for('depo.urun_liste'))
    
    kategoriler = UrunKategori.query.filter_by(is_deleted=False, aktif=True).all()
    return render_template('depo/urun_form.html', urun=urun, kategoriler=kategoriler)


# ============================================================
# DEPO YÖNETİMİ
# ============================================================

@depo_bp.route('/depolar')
@login_required
@permission_required('depo.view')
def depo_liste():
    """Depo listesi"""
    depolar = Depo.query.filter_by(is_deleted=False).order_by(Depo.ad).all()
    return render_template('depo/depo_liste.html', depolar=depolar)


@depo_bp.route('/depo/ekle', methods=['GET', 'POST'])
@login_required
@permission_required('depo.edit')
def depo_ekle():
    """Yeni depo ekle"""
    if request.method == 'POST':
        kod = request.form.get('kod', '').strip()
        if Depo.query.filter_by(kod=kod, is_deleted=False).first():
            flash('Bu depo kodu zaten kullanılıyor.', 'danger')
            return redirect(url_for('depo.depo_ekle'))
        
        depo = Depo(
            kod=kod,
            ad=request.form.get('ad', '').strip(),
            adres=request.form.get('adres', '').strip() or None,
            sorumlu_id=int(request.form.get('sorumlu_id')) if request.form.get('sorumlu_id') else None,
            notlar=request.form.get('notlar', '').strip() or None,
            aktif=True
        )
        
        db.session.add(depo)
        db.session.commit()
        
        flash('Depo oluşturuldu.', 'success')
        return redirect(url_for('depo.depo_liste'))
    
    from app.models.core import User
    kullanicilar = User.query.filter_by(is_active=True).all()
    return render_template('depo/depo_form.html', depo=None, kullanicilar=kullanicilar)


@depo_bp.route('/depo/<int:id>/stok')
@login_required
@permission_required('depo.view')
def depo_stok(id):
    """Depo stok durumu"""
    depo = Depo.query.get_or_404(id)
    stok_kartlari = StokKarti.query.filter_by(depo_id=id, is_deleted=False).all()
    return render_template('depo/depo_stok.html', depo=depo, stok_kartlari=stok_kartlari)


# ============================================================
# STOK HAREKETLERİ
# ============================================================

@depo_bp.route('/hareketler')
@login_required
@permission_required('depo.view')
def hareket_liste():
    """Stok hareketleri listesi"""
    hareketler = StokHareketi.query.filter_by(is_deleted=False)\
        .order_by(StokHareketi.tarih.desc()).all()
    return render_template('depo/hareket_liste.html', hareketler=hareketler)


@depo_bp.route('/hareket/giris', methods=['GET', 'POST'])
@login_required
@permission_required('depo.edit')
def hareket_giris():
    """Mal girişi"""
    if request.method == 'POST':
        hareket_no = f"GRS-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        hareket = StokHareketi(
            hareket_no=hareket_no,
            tarih=datetime.strptime(request.form.get('tarih'), '%Y-%m-%dT%H:%M') if request.form.get('tarih') else datetime.now(),
            tip='giris',
            depo_id=int(request.form.get('depo_id')),
            taraf_tipi=request.form.get('taraf_tipi'),
            tedarikci_id=int(request.form.get('tedarikci_id')) if request.form.get('tedarikci_id') else None,
            sirket_adi=request.form.get('sirket_adi') if request.form.get('taraf_tipi') == 'diger' else None,
            proje_id=int(request.form.get('proje_id')) if request.form.get('proje_id') else None,
            belge_no=request.form.get('belge_no'),
            belge_tarihi=datetime.strptime(request.form.get('belge_tarihi'), '%Y-%m-%d').date() if request.form.get('belge_tarihi') else None,
            aciklama=request.form.get('aciklama'),
            durum='taslak',
            olusturan_id=current_user.id
        )
        
        db.session.add(hareket)
        db.session.commit()
        
        flash('Mal girişi oluşturuldu. Ürünleri ekleyebilirsiniz.', 'success')
        return redirect(url_for('depo.hareket_detay', id=hareket.id))
    
    depolar = Depo.query.filter_by(is_deleted=False, aktif=True).all()
    tedarikciler = Tedarikci.query.filter_by(is_deleted=False, aktif=True).all()
    projeler = Proje.query.filter_by(is_deleted=False).all()
    
    return render_template('depo/hareket_giris_form.html',
                          depolar=depolar,
                          tedarikciler=tedarikciler,
                          projeler=projeler)


@depo_bp.route('/hareket/cikis', methods=['GET', 'POST'])
@login_required
@permission_required('depo.edit')
def hareket_cikis():
    """Mal çıkışı"""
    if request.method == 'POST':
        tip = request.form.get('tip', 'cikis')
        prefix = 'ZMT' if tip == 'zimmet' else 'CKS'
        hareket_no = f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        hareket = StokHareketi(
            hareket_no=hareket_no,
            tarih=datetime.strptime(request.form.get('tarih'), '%Y-%m-%dT%H:%M') if request.form.get('tarih') else datetime.now(),
            tip=tip,
            depo_id=int(request.form.get('depo_id')),
            taraf_tipi=request.form.get('taraf_tipi'),
            calisan_id=int(request.form.get('calisan_id')) if request.form.get('calisan_id') else None,
            sirket_adi=request.form.get('sirket_adi') if request.form.get('taraf_tipi') == 'sirket' else None,
            proje_id=int(request.form.get('proje_id')) if request.form.get('proje_id') else None,
            belge_no=request.form.get('belge_no'),
            aciklama=request.form.get('aciklama'),
            durum='taslak',
            olusturan_id=current_user.id
        )
        
        db.session.add(hareket)
        db.session.commit()
        
        flash('Mal çıkışı oluşturuldu. Ürünleri ekleyebilirsiniz.', 'success')
        return redirect(url_for('depo.hareket_detay', id=hareket.id))
    
    depolar = Depo.query.filter_by(is_deleted=False, aktif=True).all()
    calisanlar = Calisan.query.filter_by(is_deleted=False).all()
    projeler = Proje.query.filter_by(is_deleted=False).all()
    
    return render_template('depo/hareket_cikis_form.html',
                          depolar=depolar,
                          calisanlar=calisanlar,
                          projeler=projeler)


@depo_bp.route('/hareket/<int:id>')
@login_required
@permission_required('depo.view')
def hareket_detay(id):
    """Hareket detay"""
    hareket = StokHareketi.query.get_or_404(id)
    kalemler = hareket.kalemler.filter_by(is_deleted=False).all()
    urunler = Urun.query.filter_by(is_deleted=False, aktif=True).order_by(Urun.ad).all()
    
    return render_template('depo/hareket_detay.html',
                          hareket=hareket,
                          kalemler=kalemler,
                          urunler=urunler)


@depo_bp.route('/hareket/<int:id>/kalem-ekle', methods=['POST'])
@login_required
@permission_required('depo.edit')
def hareket_kalem_ekle(id):
    """Harekete kalem ekle"""
    hareket = StokHareketi.query.get_or_404(id)
    
    if hareket.durum != 'taslak':
        flash('Onaylanmış hareketlere kalem eklenemez.', 'danger')
        return redirect(url_for('depo.hareket_detay', id=id))
    
    kalem = StokHareketiKalem(
        hareket_id=id,
        urun_id=int(request.form.get('urun_id')),
        miktar=float(request.form.get('miktar')),
        birim_fiyat=float(request.form.get('birim_fiyat')) if request.form.get('birim_fiyat') else None,
        seri_no=request.form.get('seri_no') or None,
        lot_no=request.form.get('lot_no') or None,
        aciklama=request.form.get('aciklama') or None
    )
    
    db.session.add(kalem)
    db.session.commit()
    
    flash('Kalem eklendi.', 'success')
    return redirect(url_for('depo.hareket_detay', id=id))


@depo_bp.route('/hareket/<int:id>/onayla', methods=['POST'])
@login_required
@permission_required('depo.edit')
def hareket_onayla(id):
    """Hareketi onayla ve stok güncelle"""
    hareket = StokHareketi.query.get_or_404(id)
    
    if hareket.durum != 'taslak':
        flash('Bu hareket zaten onaylanmış.', 'warning')
        return redirect(url_for('depo.hareket_detay', id=id))
    
    kalemler = hareket.kalemler.filter_by(is_deleted=False).all()
    if not kalemler:
        flash('Hareket onaylamak için en az bir kalem eklemelisiniz.', 'danger')
        return redirect(url_for('depo.hareket_detay', id=id))
    
    # Stok güncelle
    for kalem in kalemler:
        # Stok kartı bul veya oluştur
        stok_karti = StokKarti.query.filter_by(
            depo_id=hareket.depo_id,
            urun_id=kalem.urun_id,
            proje_id=hareket.proje_id,
            is_deleted=False
        ).first()
        
        if not stok_karti:
            stok_karti = StokKarti(
                depo_id=hareket.depo_id,
                urun_id=kalem.urun_id,
                proje_id=hareket.proje_id,
                miktar=0
            )
            db.session.add(stok_karti)
        
        # Giriş/Çıkış'a göre stok güncelle
        if hareket.tip in ['giris', 'sayim']:
            stok_karti.miktar = float(stok_karti.miktar or 0) + float(kalem.miktar)
        elif hareket.tip in ['cikis', 'zimmet']:
            stok_karti.miktar = float(stok_karti.miktar or 0) - float(kalem.miktar)
            if stok_karti.miktar < 0:
                flash(f'{kalem.urun.ad} için yeterli stok yok!', 'danger')
                return redirect(url_for('depo.hareket_detay', id=id))
    
    hareket.durum = 'onaylandi'
    hareket.onaylayan_id = current_user.id
    hareket.onay_tarihi = datetime.now()
    
    db.session.commit()
    flash('Hareket onaylandı ve stok güncellendi.', 'success')
    return redirect(url_for('depo.hareket_detay', id=id))


@depo_bp.route('/hareket/<int:id>/imzala', methods=['POST'])
@login_required
@permission_required('depo.edit')
def hareket_imzala(id):
    """Hareketi imzala"""
    hareket = StokHareketi.query.get_or_404(id)
    
    hareket.imza_data = request.form.get('imza_data')
    hareket.imzalayan_ad = request.form.get('imzalayan_ad')
    hareket.imza_tarihi = datetime.now()
    
    db.session.commit()
    flash('İmza kaydedildi.', 'success')
    return redirect(url_for('depo.hareket_detay', id=id))


@depo_bp.route('/hareket/<int:id>/yazdir')
@login_required
@permission_required('depo.view')
def hareket_yazdir(id):
    """Hareket formu yazdır"""
    hareket = StokHareketi.query.get_or_404(id)
    kalemler = hareket.kalemler.filter_by(is_deleted=False).all()
    
    return render_template('depo/hareket_yazdir.html',
                          hareket=hareket,
                          kalemler=kalemler)


# ============================================================
# KATEGORİ YÖNETİMİ
# ============================================================

@depo_bp.route('/kategoriler')
@login_required
@permission_required('depo.view')
def kategori_liste():
    """Kategori listesi"""
    kategoriler = UrunKategori.query.filter_by(is_deleted=False).order_by(UrunKategori.ad).all()
    return render_template('depo/kategori_liste.html', kategoriler=kategoriler)


@depo_bp.route('/kategori/ekle', methods=['POST'])
@login_required
@permission_required('depo.edit')
def kategori_ekle():
    """Kategori ekle"""
    kategori = UrunKategori(
        ad=request.form.get('ad'),
        ust_kategori_id=int(request.form.get('ust_kategori_id')) if request.form.get('ust_kategori_id') else None,
        aktif=True
    )
    db.session.add(kategori)
    db.session.commit()
    flash('Kategori eklendi.', 'success')
    return redirect(url_for('depo.kategori_liste'))


# ============================================================
# API ENDPOINTS
# ============================================================

@depo_bp.route('/api/urun/<int:id>/stok')
@login_required
def api_urun_stok(id):
    """Ürün stok bilgisi API"""
    urun = Urun.query.get_or_404(id)
    stok_kartlari = StokKarti.query.filter_by(urun_id=id, is_deleted=False).all()
    
    data = {
        'toplam': urun.toplam_stok,
        'depolar': [{
            'depo_id': sk.depo_id,
            'depo_ad': sk.depo.ad,
            'miktar': float(sk.miktar),
            'kullanilabilir': sk.kullanilabilir_miktar
        } for sk in stok_kartlari]
    }
    return jsonify(data)
