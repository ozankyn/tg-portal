# -*- coding: utf-8 -*-
"""
TG Portal - Public Kariyer Sayfası
Açık pozisyonları görüntüleme ve doğrudan başvuru - Login gerektirmez
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session
from datetime import datetime, timedelta
from app import db
from app.models.ik import (
    Aday, KAYNAK_TURLERI, BASVURU_KAYNAK_TURLERI, BEDEN_SECENEKLERI,
    EvrakTipi, AdayEvrak, AdayMedya, SozlesmeSablonu,
)
from app.models.proje import HedefKadro, Proje, Musteri, Il, Ilce
from app.utils import (
    normalize_telefon,
    is_iban_evrak_tipi, iban_evrak_uzanti_gecerli, iban_evrak_tipi_idleri,
    IBAN_FORMAT_HATASI, IBAN_EVRAK_ACIKLAMA,
)

kariyer_bp = Blueprint('kariyer', __name__)


# ============================================================
# MEDYA (FOTO/VIDEO) KURALLARI
# Hem başvuru formu hem token'lı public yükleme aynı sınırları kullanır.
# ============================================================

_FOTO_EXTS = {'jpg', 'jpeg', 'png', 'webp'}
_VIDEO_EXTS = {'mp4', 'mov', 'webm'}
_FOTO_MAX = 10 * 1024 * 1024
_VIDEO_MAX = 100 * 1024 * 1024


def _kariyer_ext(fn):
    return fn.rsplit('.', 1)[1].lower() if '.' in fn else ''


def _dosya_boyut(f):
    """Yüklenen dosyanın boyutunu okur ve imleci başa alır."""
    import os
    f.seek(0, os.SEEK_END)
    boyut = f.tell()
    f.seek(0)
    return boyut


# ============================================================
# SESSION TABANLI BAŞVURU YARDIMCILARI
# Açık başvuruda aday kaydı YALNIZCA form gönderilince oluşur.
# KVKK onayı, telefon ve doğrulama bilgisi o ana kadar session'da tutulur.
# ============================================================

SESSION_KEY = 'kariyer_basvuru'


def _get_basvuru_session(kadro_id):
    """İlgili kadroya ait aktif başvuru session'ını döndür (yoksa None)."""
    s = session.get(SESSION_KEY)
    if not s or s.get('kadro_id') != kadro_id:
        return None
    return s


def _parse_dt(s):
    """ISO format string -> datetime (hatalıysa None)."""
    try:
        return datetime.fromisoformat(s) if s else None
    except (ValueError, TypeError):
        return None


def _parse_date(s):
    """'YYYY-MM-DD' string -> date (hatalıysa None). Form re-render için."""
    try:
        return datetime.strptime(s, '%Y-%m-%d').date() if s else None
    except (ValueError, TypeError):
        return None


def _otp_valid(bsv):
    """Session'daki OTP hâlâ geçerli mi?"""
    if not bsv.get('otp_kod') or not bsv.get('otp_expires'):
        return False
    exp = _parse_dt(bsv.get('otp_expires'))
    return bool(exp) and datetime.now() < exp


def _verify_session_otp(bsv, kod):
    """Session tabanlı OTP doğrulama. (basarili, mesaj) döner; bsv güncellenir."""
    if not _otp_valid(bsv):
        return False, 'Doğrulama kodunun süresi dolmuş. Lütfen yeni kod isteyin.'
    if bsv.get('otp_deneme', 0) >= 3:
        return False, 'Çok fazla yanlış deneme. Lütfen yeni kod isteyin.'
    if bsv.get('otp_kod') != kod:
        bsv['otp_deneme'] = bsv.get('otp_deneme', 0) + 1
        return False, f"Yanlış kod. {3 - bsv['otp_deneme']} deneme hakkınız kaldı."
    bsv['telefon_dogrulandi'] = True
    bsv['otp_kod'] = None
    return True, 'Telefon doğrulandı'


class _FormAday:
    """kariyer/form.html render'ı için geçici placeholder (DB'ye yazılmaz).
    GET'te boş form render edilir; POST doğrulama hatasında ise girilen
    değerlerle yeniden doldurulur (aday veri kaybı yaşamaz).
    Tanımsız alanlar None döner."""

    # Template'te .strftime() ile kullanılan tarih alanları → date/None dönmeli
    _TARIH_ALANLARI = {
        'dogum_tarihi', 'ehliyet_tarihi', 'son_is_baslangic',
        'son_is_bitis', 'askerlik_tecil_tarihi',
    }

    def __init__(self, form=None, telefon=None, telefon_dogrulandi=False):
        # __getattr__ ile çakışmamak için doğrudan __dict__'e yazıyoruz
        self.__dict__['_form'] = form or {}
        self.__dict__['telefon'] = telefon or (form.get('telefon') if form else None)
        self.__dict__['telefon_dogrulandi'] = telefon_dogrulandi
        # İlk GET (form yok) → makul varsayılanlar
        if not form:
            self.__dict__['vardiyali_calisabilir'] = True
            self.__dict__['toplam_tecrube_yil'] = 0

    def __getattr__(self, name):
        # Dunder/özel isimler için normal AttributeError davranışı korunur
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        form = self.__dict__.get('_form') or {}
        val = form.get(name)
        if name in _FormAday._TARIH_ALANLARI:
            return _parse_date(val)
        return val if val not in (None, '') else None


@kariyer_bp.route('/')
def pozisyonlar():
    """Açık pozisyonları listele"""
    # Aktif projelerdeki eksik kadrolu pozisyonları getir
    kadrolar = HedefKadro.query.join(Proje).join(Musteri).filter(
        Proje.aktif == True,
        Musteri.aktif == True,
        HedefKadro.is_deleted == False
    ).all()
    
    # Sadece eksik kadrosu olanları filtrele
    acik_pozisyonlar = [k for k in kadrolar if k.eksik_sayi > 0]
    
    # İllere göre grupla
    iller = set()
    for k in acik_pozisyonlar:
        if k.il:
            iller.add(k.il)
    
    # Filtreler
    il_filtre = request.args.get('il')
    if il_filtre:
        acik_pozisyonlar = [k for k in acik_pozisyonlar if k.il == il_filtre]
    
    return render_template('kariyer/pozisyonlar.html', 
                         pozisyonlar=acik_pozisyonlar,
                         iller=sorted(iller),
                         il_filtre=il_filtre)


@kariyer_bp.route('/basvur/<int:kadro_id>')
def basvuru_kvkk(kadro_id):
    """Açık başvuru - KVKK aydınlatma metni"""
    kadro = HedefKadro.query.get_or_404(kadro_id)
    
    # Aktif proje kontrolü
    if not kadro.proje.aktif:
        flash('Bu pozisyon için başvuru alınmamaktadır.', 'warning')
        return redirect(url_for('kariyer.pozisyonlar'))
    
    return render_template('kariyer/kvkk_onay.html', kadro=kadro)


@kariyer_bp.route('/basvur/<int:kadro_id>/kvkk-onayla', methods=['POST'])
def kvkk_onayla(kadro_id):
    """Açık başvuru - KVKK onayı (session'a yazılır, DB'ye DEĞİL)"""
    kadro = HedefKadro.query.get_or_404(kadro_id)

    if not request.form.get('kvkk_onay'):
        flash('Devam etmek için aydınlatma metnini onaylamanız gerekmektedir.', 'warning')
        return redirect(url_for('kariyer.basvuru_kvkk', kadro_id=kadro_id))

    # Başvuru bilgilerini session'da başlat — DB kaydı form gönderilince oluşur
    session[SESSION_KEY] = {
        'kadro_id': kadro_id,
        'kvkk_onay': True,
        'kvkk_onay_tarihi': datetime.now().isoformat(),
        'kvkk_onay_ip': request.headers.get('X-Forwarded-For', request.remote_addr),
        'telefon': None,
        'telefon_dogrulandi': False,
        'otp_kod': None,
        'otp_expires': None,
        'otp_deneme': 0,
    }

    # SMS doğrulama gerekiyor mu?
    if kadro.sms_dogrulama_zorunlu:
        return redirect(url_for('kariyer.telefon_dogrula', kadro_id=kadro_id))

    return redirect(url_for('kariyer.basvuru_form', kadro_id=kadro_id))


@kariyer_bp.route('/basvur/<int:kadro_id>/telefon-dogrula', methods=['GET', 'POST'])
def telefon_dogrula(kadro_id):
    """Açık başvuru - telefon doğrulama (session tabanlı, DB kaydı yok)"""
    from app.modules.basvuru.routes import send_netgsm_sms
    import random

    kadro = HedefKadro.query.get_or_404(kadro_id)
    bsv = _get_basvuru_session(kadro_id)

    if not bsv or not bsv.get('kvkk_onay'):
        flash('Önce aydınlatma metnini onaylamanız gerekmektedir.', 'warning')
        return redirect(url_for('kariyer.basvuru_kvkk', kadro_id=kadro_id))

    if bsv.get('telefon_dogrulandi'):
        return redirect(url_for('kariyer.basvuru_form', kadro_id=kadro_id))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'send_code':
            telefon_ham = (request.form.get('telefon') or '').strip()
            if not telefon_ham:
                flash('Telefon numarası gereklidir.', 'danger')
                return redirect(url_for('kariyer.telefon_dogrula', kadro_id=kadro_id))

            telefon = normalize_telefon(telefon_ham)
            if not telefon:
                flash('Geçerli bir cep telefonu numarası girin. '
                      'Örnek: 05XX XXX XX XX', 'danger')
                return redirect(url_for('kariyer.telefon_dogrula', kadro_id=kadro_id))

            kod = str(random.randint(100000, 999999))
            bsv['telefon'] = telefon
            bsv['otp_kod'] = kod
            bsv['otp_expires'] = (datetime.now() + timedelta(minutes=5)).isoformat()
            bsv['otp_deneme'] = 0
            session[SESSION_KEY] = bsv

            mesaj = f"Team Guerilla is basvuru dogrulama kodunuz: {kod} - Bu kod 5 dakika gecerlidir."
            result = send_netgsm_sms(telefon, mesaj)
            if result['success']:
                flash('Doğrulama kodu telefonunuza gönderildi.', 'success')
            else:
                flash(f'SMS gönderilemedi: {result.get("error")}', 'danger')
            return redirect(url_for('kariyer.telefon_dogrula', kadro_id=kadro_id))

        elif action == 'verify_code':
            kod = (request.form.get('kod') or '').strip()
            if not kod:
                flash('Doğrulama kodunu giriniz.', 'warning')
                return redirect(url_for('kariyer.telefon_dogrula', kadro_id=kadro_id))

            ok, mesaj = _verify_session_otp(bsv, kod)
            session[SESSION_KEY] = bsv
            if ok:
                flash('Telefonunuz doğrulandı!', 'success')
                return redirect(url_for('kariyer.basvuru_form', kadro_id=kadro_id))
            flash(mesaj, 'danger')
            return redirect(url_for('kariyer.telefon_dogrula', kadro_id=kadro_id))

    kod_gonderildi = _otp_valid(bsv)
    return render_template('kariyer/telefon_dogrula.html',
                           kadro=kadro,
                           telefon=bsv.get('telefon'),
                           kod_gonderildi=kod_gonderildi,
                           deneme=bsv.get('otp_deneme', 0))


@kariyer_bp.route('/basvur/<int:kadro_id>/kod-tekrar')
def kod_tekrar_gonder(kadro_id):
    """Açık başvuru - doğrulama kodunu tekrar gönder (session tabanlı)"""
    from app.modules.basvuru.routes import send_netgsm_sms
    import random

    bsv = _get_basvuru_session(kadro_id)
    if not bsv or not bsv.get('telefon'):
        flash('Önce telefon numaranızı girin.', 'warning')
        return redirect(url_for('kariyer.telefon_dogrula', kadro_id=kadro_id))

    kod = str(random.randint(100000, 999999))
    bsv['otp_kod'] = kod
    bsv['otp_expires'] = (datetime.now() + timedelta(minutes=5)).isoformat()
    bsv['otp_deneme'] = 0
    session[SESSION_KEY] = bsv

    mesaj = f"Team Guerilla is basvuru dogrulama kodunuz: {kod} - Bu kod 5 dakika gecerlidir."
    result = send_netgsm_sms(bsv['telefon'], mesaj)
    if result['success']:
        flash('Yeni doğrulama kodu gönderildi.', 'success')
    else:
        flash(f'SMS gönderilemedi: {result.get("error")}', 'danger')

    return redirect(url_for('kariyer.telefon_dogrula', kadro_id=kadro_id))


@kariyer_bp.route('/basvur/<int:kadro_id>/form', methods=['GET', 'POST'])
def basvuru_form(kadro_id):
    """Açık başvuru formu — Aday kaydı YALNIZCA form gönderilince oluşur"""
    kadro = HedefKadro.query.get_or_404(kadro_id)
    bsv = _get_basvuru_session(kadro_id)

    # KVKK onayı session'da yoksa baştan başlat
    if not bsv or not bsv.get('kvkk_onay'):
        flash('Önce aydınlatma metnini onaylamanız gerekmektedir.', 'warning')
        return redirect(url_for('kariyer.basvuru_kvkk', kadro_id=kadro_id))

    # SMS doğrulama zorunluysa telefon doğrulanmış olmalı
    if kadro.sms_dogrulama_zorunlu and not bsv.get('telefon_dogrulandi'):
        flash('Devam etmek için telefon numaranızı doğrulamanız gerekmektedir.', 'warning')
        return redirect(url_for('kariyer.telefon_dogrula', kadro_id=kadro_id))

    if request.method == 'POST':
        # Doğrulama hatalarını topla — redirect yerine formu girilen verilerle
        # yeniden gösteriyoruz (aday veri kaybı yaşamaz).
        hatalar = []

        # Zorunlu alan kontrolü — tüm bilgiler tek seferde alınır
        ad = (request.form.get('ad') or '').strip()
        soyad = (request.form.get('soyad') or '').strip()
        zorunlu_alanlar = {
            'Ad': ad,
            'Soyad': soyad,
            'TC Kimlik No': request.form.get('tc_kimlik'),
            'Doğum tarihi': request.form.get('dogum_tarihi'),
            'Cinsiyet': request.form.get('cinsiyet'),
            'E-posta': request.form.get('email'),
            'Telefon': request.form.get('telefon'),
            'İl': request.form.get('il'),
        }
        # İlçe zorunlu — ancak yalnızca seçilen ilin DB'de ilçesi varsa
        # (ilçe verisi eksik iller için başvuruyu bloklamamak adına)
        secili_il = (request.form.get('il') or '').strip()
        if secili_il:
            il_obj = Il.query.filter_by(ad=secili_il).first()
            if il_obj and il_obj.ilceler.count() > 0:
                zorunlu_alanlar['İlçe'] = request.form.get('ilce')
        eksikler = [etiket for etiket, deger in zorunlu_alanlar.items() if not deger]
        if eksikler:
            hatalar.append('Lütfen şu zorunlu alanları doldurun: ' + ', '.join(eksikler))

        if request.form.get('cinsiyet') == 'erkek' and not request.form.get('askerlik_durumu'):
            hatalar.append('Askerlik durumu erkek adaylar için zorunludur.')

        # Kadro flag'lerine göre foto/video zorunlu kontrolü (aday oluşturmadan önce).
        # Format/boyut da burada doğrulanır: aksi halde geçersiz dosya sessizce
        # atlanır ve "zorunlu" alan boş kalmış bir başvuru kaydedilirdi.
        fotos, video_file = [], None

        if kadro.foto_gerekli:
            fotos = [f for f in request.files.getlist('medya_fotos') if f and f.filename]
            if not fotos:
                hatalar.append('Bu pozisyon için en az bir fotoğraf yüklemeniz zorunludur.')
            for f in fotos:
                if _kariyer_ext(f.filename) not in _FOTO_EXTS:
                    hatalar.append(f'{f.filename}: fotoğraf yalnızca JPG, PNG veya WEBP olabilir.')
                elif _dosya_boyut(f) > _FOTO_MAX:
                    hatalar.append(f'{f.filename}: fotoğraf boyutu 10 MB sınırını aşıyor.')

        if kadro.video_gerekli:
            video_file = request.files.get('medya_video')
            if not video_file or not video_file.filename:
                video_file = None
                hatalar.append('Bu pozisyon için video yüklemeniz zorunludur.')
            elif _kariyer_ext(video_file.filename) not in _VIDEO_EXTS:
                hatalar.append(f'{video_file.filename}: video yalnızca MP4, MOV veya WEBM olabilir.')
            elif _dosya_boyut(video_file) > _VIDEO_MAX:
                hatalar.append(f'{video_file.filename}: video boyutu 100 MB sınırını aşıyor.')

        # Mükerrer başvuru kontrolü — aynı kadroya aynı TC veya telefon ile
        # daha önce başvuru yapılmış mı? (silinmiş kayıtlar sayılmaz)
        tc_kimlik = request.form.get('tc_kimlik')
        telefon = (bsv.get('telefon') if bsv.get('telefon_dogrulandi')
                   else normalize_telefon(request.form.get('telefon')))
        if not telefon:
            hatalar.append('Geçerli bir cep telefonu numarası girin. Örnek: 05XX XXX XX XX')
        if not hatalar:
            mukerrer = Aday.query.filter(
                Aday.kadro_id == kadro_id,
                Aday.is_deleted == False,
                db.or_(
                    db.and_(tc_kimlik != None, Aday.tc_kimlik == tc_kimlik),
                    db.and_(telefon != None, Aday.telefon == telefon),
                ),
            ).first()
            if mukerrer:
                hatalar.append('Bu pozisyona daha önce başvuru yapmışsınız.')

        # Hata varsa: girilen verileri koruyarak formu yeniden göster (redirect YOK)
        if hatalar:
            form_aday = _FormAday(
                form=request.form,
                telefon=bsv.get('telefon'),
                telefon_dogrulandi=bool(bsv.get('telefon_dogrulandi')),
            )
            iller = Il.query.order_by(Il.ad).all()
            return render_template('kariyer/form.html', aday=form_aday, kadro=kadro,
                                   basvuru_kaynak_turleri=BASVURU_KAYNAK_TURLERI,
                                   beden_secenekleri=BEDEN_SECENEKLERI,
                                   iller=iller, form_hatalari=hatalar), 400

        # ---- Aday kaydını oluştur (tüm bilgiler tek INSERT) ----
        aday = Aday(
            ad=ad,
            soyad=soyad,
            kadro_id=kadro_id,
            kaynak='acik_basvuru',
            durum='basvurdu',
            kvkk_onay=True,
            kvkk_onay_tarihi=_parse_dt(bsv.get('kvkk_onay_tarihi')) or datetime.now(),
            kvkk_onay_ip=bsv.get('kvkk_onay_ip'),
            aydinlatma_metni_versiyonu='1.0',
            telefon_dogrulandi=bool(bsv.get('telefon_dogrulandi')),
            basvuru_tamamlandi=True,
            basvuru_tarihi=datetime.now(),
        )
        aday.generate_token()
        if bsv.get('telefon_dogrulandi'):
            aday.telefon_dogrulama_tarihi = datetime.now()
            aday.telefon_dogrulama_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        # Kişisel bilgiler
        aday.tc_kimlik = request.form.get('tc_kimlik')
        aday.dogum_tarihi = datetime.strptime(request.form.get('dogum_tarihi'), '%Y-%m-%d').date() if request.form.get('dogum_tarihi') else None
        aday.dogum_yeri = request.form.get('dogum_yeri')
        aday.cinsiyet = request.form.get('cinsiyet')
        aday.medeni_durum = request.form.get('medeni_durum')
        
        # İletişim — doğrulanmış telefon session'dan alınır
        aday.email = request.form.get('email')
        aday.telefon = telefon  # yukarıda normalize edildi (05XXXXXXXXX)
        aday.adres = request.form.get('adres')
        aday.il = request.form.get('il')
        aday.ilce = request.form.get('ilce')

        # Fiziksel bilgiler
        aday.ust_beden = request.form.get('ust_beden') or None
        aday.alt_beden = request.form.get('alt_beden') or None
        aday.ayakkabi_no = request.form.get('ayakkabi_no') or None

        # Lojistik
        aday.kargo_subesi = request.form.get('kargo_subesi') or None

        # Başvuru kaynağı / geçmiş
        aday.basvuru_kaynak = request.form.get('basvuru_kaynak') or None
        aday.tg_calistimi = request.form.get('tg_calistimi') == 'on'

        # Eğitim
        aday.egitim_durumu = request.form.get('egitim_durumu')
        aday.okul_adi = request.form.get('okul_adi')
        aday.bolum = request.form.get('bolum')
        aday.mezuniyet_yili = int(request.form.get('mezuniyet_yili')) if request.form.get('mezuniyet_yili') else None
        
        # Ehliyet
        aday.ehliyet_var = request.form.get('ehliyet_var') == 'on'
        aday.ehliyet_sinifi = request.form.get('ehliyet_sinifi')
        aday.ehliyet_tarihi = datetime.strptime(request.form.get('ehliyet_tarihi'), '%Y-%m-%d').date() if request.form.get('ehliyet_tarihi') else None
        aday.src_belgesi = request.form.get('src_belgesi') == 'on'
        aday.psikoteknik = request.form.get('psikoteknik') == 'on'
        
        # İş deneyimi
        aday.toplam_tecrube_yil = int(request.form.get('toplam_tecrube_yil') or 0)
        aday.son_is_yeri = request.form.get('son_is_yeri')
        aday.son_pozisyon = request.form.get('son_pozisyon')
        aday.son_is_baslangic = datetime.strptime(request.form.get('son_is_baslangic'), '%Y-%m-%d').date() if request.form.get('son_is_baslangic') else None
        aday.son_is_bitis = datetime.strptime(request.form.get('son_is_bitis'), '%Y-%m-%d').date() if request.form.get('son_is_bitis') else None
        aday.son_is_ayrilma_nedeni = request.form.get('son_is_ayrilma_nedeni')
        
        # Referans
        aday.referans_ad = request.form.get('referans_ad')
        aday.referans_telefon = request.form.get('referans_telefon')
        aday.referans_iliski = request.form.get('referans_iliski')
        
        # Ek bilgiler
        aday.saglik_sorunu = request.form.get('saglik_sorunu') == 'on'
        aday.saglik_sorunu_aciklama = request.form.get('saglik_sorunu_aciklama')
        aday.askerlik_durumu = request.form.get('askerlik_durumu')
        aday.askerlik_tecil_tarihi = datetime.strptime(request.form.get('askerlik_tecil_tarihi'), '%Y-%m-%d').date() if request.form.get('askerlik_tecil_tarihi') else None
        aday.sabika_kaydi = request.form.get('sabika_kaydi') == 'on'
        aday.sabika_aciklama = request.form.get('sabika_aciklama')
        
        # Tercihler
        aday.calisabilecegi_iller = request.form.get('calisabilecegi_iller')
        aday.beklenen_maas = request.form.get('beklenen_maas') or None
        aday.ne_zaman_baslayabilir = request.form.get('ne_zaman_baslayabilir')
        aday.vardiyali_calisabilir = request.form.get('vardiyali_calisabilir') == 'on'
        aday.seyahat_engeli = request.form.get('seyahat_engeli') == 'on'
        
        # Aday'ı kaydet ve ID al (dosya yolları aday.id'ye göre oluşturulur)
        db.session.add(aday)
        db.session.flush()

        # Dosya yüklemeleri
        import os
        from werkzeug.utils import secure_filename

        # CV opsiyonel; foto/video zorunluluğu yukarıda kontrol edildi.
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'adaylar', str(aday.id))
        os.makedirs(upload_folder, exist_ok=True)

        # Başvuru formunda artık yalnızca CV (opsiyonel) + kadro bazlı foto/video alınıyor.
        # Diğer belgeler (kimlik, ehliyet, diploma, adli sicil vb.) işe alım sürecinde
        # /kariyer/evrak akışından toplanıyor.
        file_fields = ['cv_dosya']

        for field in file_fields:
            file = request.files.get(field)
            if file and file.filename:
                filename = secure_filename(f"{field}_{aday.id}_{file.filename}")
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                setattr(aday, field, f"uploads/adaylar/{aday.id}/{filename}")

        # Tanıtım foto/video → AdayMedya
        # Dosyalar yukarıda (aday oluşturulmadan önce) format/boyut açısından
        # doğrulandı; burada yalnızca kaydediliyor.
        if fotos:
            fotos_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'adaylar', str(aday.id), 'fotos')
            os.makedirs(fotos_dir, exist_ok=True)
            for f in fotos:
                ext = _kariyer_ext(f.filename)
                boyut = _dosya_boyut(f)
                fname = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{ext}"
                fpath = os.path.join(fotos_dir, fname)
                f.save(fpath)
                rel = f"adaylar/{aday.id}/fotos/{fname}"
                db.session.add(AdayMedya(
                    aday_id=aday.id, tip='foto',
                    dosya_adi=secure_filename(f.filename),
                    dosya_yolu=rel, dosya_boyut=boyut,
                    mime_type=f.mimetype or f'image/{ext}',
                ))

        if video_file:
            ext = _kariyer_ext(video_file.filename)
            boyut = _dosya_boyut(video_file)
            videos_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'adaylar', str(aday.id), 'videos')
            os.makedirs(videos_dir, exist_ok=True)
            fname = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{ext}"
            fpath = os.path.join(videos_dir, fname)
            video_file.save(fpath)
            rel = f"adaylar/{aday.id}/videos/{fname}"
            db.session.add(AdayMedya(
                aday_id=aday.id, tip='video',
                dosya_adi=secure_filename(video_file.filename),
                dosya_yolu=rel, dosya_boyut=boyut,
                mime_type=video_file.mimetype or f'video/{ext}',
            ))

        # Başvuru tamamlandı (durum/flag'ler aday oluşturulurken set edildi)
        db.session.commit()

        # Session temizle
        session.pop(SESSION_KEY, None)

        # İK ekibine bildirim gönder
        from app.services.notification import notify_yeni_basvuru
        notify_yeni_basvuru(aday)

        # "Başvurunuz alındı" sayfasına yönlendir.
        # Evrak yükleme linki İK tarafından aday kaydından manuel paylaşılır.
        return redirect(url_for('kariyer.basvuru_tamam', token=aday.davet_token))

    # GET — boş formu placeholder ile render et (henüz DB kaydı yok)
    form_aday = _FormAday(
        telefon=bsv.get('telefon'),
        telefon_dogrulandi=bool(bsv.get('telefon_dogrulandi')),
    )
    iller = Il.query.order_by(Il.ad).all()
    return render_template('kariyer/form.html', aday=form_aday, kadro=kadro,
                           basvuru_kaynak_turleri=BASVURU_KAYNAK_TURLERI,
                           beden_secenekleri=BEDEN_SECENEKLERI,
                           iller=iller)


@kariyer_bp.route('/api/ilceler')
def api_ilceler():
    """İl ID'sine göre ilçeleri getir (public - başvuru formu AJAX için)"""
    il_id = request.args.get('il_id', type=int)
    if not il_id:
        return jsonify([])

    ilceler = Ilce.query.filter_by(il_id=il_id).order_by(Ilce.ad).all()
    return jsonify([{'id': i.id, 'ad': i.ad} for i in ilceler])


@kariyer_bp.route('/basvur/tamam/<token>')
def basvuru_tamam(token):
    """Başvuru tamamlandı sayfası"""
    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first_or_404()
    return render_template('kariyer/tamam.html', aday=aday)


# ============================================================
# ADAY EVRAK YÜKLEME (PUBLIC - TOKEN İLE)
# ============================================================

@kariyer_bp.route('/evrak/<token>')
def evrak_yukle_sayfa(token):
    """Aday evrak yükleme sayfası (public)"""
    from datetime import datetime
    
    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first()
    
    if not aday:
        flash('Geçersiz veya süresi dolmuş link.', 'danger')
        return redirect(url_for('kariyer.pozisyonlar'))
    
    # Token süresi kontrolü (opsiyonel - evrak için daha uzun süre verilebilir)
    # if aday.davet_token_expires and aday.davet_token_expires < datetime.now():
    #     flash('Link süresi dolmuş.', 'danger')
    #     return redirect(url_for('kariyer.pozisyonlar'))
    
    evrak_tipleri = EvrakTipi.query.filter_by(aktif=True).order_by(EvrakTipi.sira).all()
    evraklar = aday.evraklar.all()
    
    # Eksik evraklar
    yuklenen_tipler = [e.evrak_tipi_id for e in aday.evraklar.filter(
        AdayEvrak.durum.in_(['yuklendi', 'onaylandi'])
    ).all()]
    eksik_evraklar = [t for t in EvrakTipi.query.filter_by(zorunlu=True, aktif=True).all() if t.id not in yuklenen_tipler]
    
    # Tamamlanma oranı
    zorunlu_count = EvrakTipi.query.filter_by(zorunlu=True, aktif=True).count()
    if zorunlu_count == 0:
        evrak_tamamlanma = 100
    else:
        tamamlanan = len([t for t in EvrakTipi.query.filter_by(zorunlu=True, aktif=True).all() if t.id in yuklenen_tipler])
        evrak_tamamlanma = int((tamamlanan / zorunlu_count) * 100)
    
    fotos = aday.medyalar.filter_by(tip='foto').all()
    videos = aday.medyalar.filter_by(tip='video').all()
    kadro = aday.kadro

    # Şirket evrakları: adayın kadrosunun proje/müşterisine tanımlı sözleşme şablonları
    sirket_sablonlari = []
    if kadro and kadro.proje:
        musteri_id = kadro.proje.musteri_id
        sablonlar = SozlesmeSablonu.sablonlari_filtrele(
            musteri_id=musteri_id, proje_id=kadro.proje_id
        )
        # Sadece indirilebilir dosyası olanları göster
        sirket_sablonlari = [s for s in sablonlar if s.sablon_dosya]

    return render_template('kariyer/evrak_yukle.html',
                          aday=aday,
                          token=token,
                          evraklar=evraklar,
                          evrak_tipleri=evrak_tipleri,
                          eksik_evraklar=eksik_evraklar,
                          evrak_tamamlanma=evrak_tamamlanma,
                          kadro=kadro,
                          fotos=fotos,
                          videos=videos,
                          sirket_sablonlari=sirket_sablonlari,
                          iban_tipi_idleri=iban_evrak_tipi_idleri(evrak_tipleri),
                          iban_evrak_aciklama=IBAN_EVRAK_ACIKLAMA)


@kariyer_bp.route('/evrak/<token>/yukle', methods=['POST'])
def evrak_yukle_post(token):
    """Aday evrak yükleme işlemi (public)"""
    from datetime import datetime
    from werkzeug.utils import secure_filename
    import os
    
    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first()
    
    if not aday:
        flash('Geçersiz link.', 'danger')
        return redirect(url_for('kariyer.pozisyonlar'))
    
    if 'dosya' not in request.files:
        flash('Dosya seçilmedi.', 'danger')
        return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))
    
    dosya = request.files['dosya']
    if dosya.filename == '':
        flash('Dosya seçilmedi.', 'danger')
        return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))
    
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    if dosya and allowed_file(dosya.filename):
        evrak_tipi_id = int(request.form['evrak_tipi_id'])
        evrak_tipi = EvrakTipi.query.get(evrak_tipi_id)

        # IBAN evrağı OCR ile okunduğu için sadece JPEG/PNG/PDF kabul edilir
        if is_iban_evrak_tipi(evrak_tipi) and not iban_evrak_uzanti_gecerli(dosya.filename):
            flash(IBAN_FORMAT_HATASI, 'danger')
            return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))

        # Dosya adı oluştur
        filename = secure_filename(dosya.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"aday_{aday.id}_{evrak_tipi_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"

        # Klasör oluştur
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'evraklar', 'adaylar', str(aday.id))
        os.makedirs(upload_folder, exist_ok=True)

        # Dosyayı kaydet
        filepath = os.path.join(upload_folder, new_filename)
        dosya.save(filepath)

        # dosya_yolu UPLOAD_FOLDER'a göre RELATİF saklanır (uploaded_file / send_file ile uyumlu)
        rel_path = f"evraklar/adaylar/{aday.id}/{new_filename}"

        # Veritabanına ekle
        evrak = AdayEvrak(
            aday_id=aday.id,
            evrak_tipi_id=evrak_tipi_id,
            dosya_adi=filename,
            dosya_yolu=rel_path,
            dosya_boyut=os.path.getsize(filepath),
            mime_type=dosya.content_type
        )
        db.session.add(evrak)
        db.session.commit()

        flash('Evrak başarıyla yüklendi.', 'success')
    else:
        flash('Geçersiz dosya formatı. (PDF, JPG, PNG, DOC, DOCX)', 'danger')

    return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))


# ============================================================
# ADAY MEDYA (Foto/Video) - PUBLIC TOKEN İLE
# Format/boyut sabitleri dosyanın başında tanımlıdır.
# ============================================================

def _kariyer_medya_dict(m):
    return {
        'id': m.id,
        'tip': m.tip,
        'dosya_adi': m.dosya_adi,
        'url': url_for('uploaded_file', filename=m.dosya_yolu),
        'boyut': m.dosya_boyut,
        'mime_type': m.mime_type,
    }


@kariyer_bp.route('/evrak/<token>/medya/foto', methods=['POST'])
def medya_foto_yukle(token):
    """Public foto yükleme (token ile)."""
    import os
    from werkzeug.utils import secure_filename

    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first()
    if not aday:
        return jsonify({'success': False, 'message': 'Geçersiz link.'}), 403

    files = request.files.getlist('fotos')
    if not files:
        return jsonify({'success': False, 'message': 'Dosya seçilmedi.'}), 400

    fotos_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'adaylar', str(aday.id), 'fotos')
    os.makedirs(fotos_dir, exist_ok=True)

    eklenen, hatalar = [], []
    for f in files:
        if not f or not f.filename:
            continue
        ext = _kariyer_ext(f.filename)
        if ext not in _FOTO_EXTS:
            hatalar.append(f"{f.filename}: geçersiz format")
            continue
        f.seek(0, os.SEEK_END); boyut = f.tell(); f.seek(0)
        if boyut > _FOTO_MAX:
            hatalar.append(f"{f.filename}: 10MB'dan büyük")
            continue
        fname = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{ext}"
        fpath = os.path.join(fotos_dir, fname)
        f.save(fpath)
        rel = f"adaylar/{aday.id}/fotos/{fname}"
        m = AdayMedya(
            aday_id=aday.id, tip='foto',
            dosya_adi=secure_filename(f.filename),
            dosya_yolu=rel, dosya_boyut=boyut,
            mime_type=f.mimetype or f'image/{ext}',
        )
        db.session.add(m)
        db.session.flush()
        eklenen.append(_kariyer_medya_dict(m))

    db.session.commit()
    return jsonify({'success': True, 'eklenen': eklenen, 'hatalar': hatalar})


@kariyer_bp.route('/evrak/<token>/medya/video', methods=['POST'])
def medya_video_yukle(token):
    """Public video yükleme (token ile)."""
    import os
    from werkzeug.utils import secure_filename

    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first()
    if not aday:
        return jsonify({'success': False, 'message': 'Geçersiz link.'}), 403

    v = request.files.get('video')
    if not v or not v.filename:
        return jsonify({'success': False, 'message': 'Dosya seçilmedi.'}), 400

    ext = _kariyer_ext(v.filename)
    if ext not in _VIDEO_EXTS:
        return jsonify({'success': False, 'message': 'Geçersiz video formatı (mp4, mov, webm).'}), 400

    v.seek(0, os.SEEK_END); boyut = v.tell(); v.seek(0)
    if boyut > _VIDEO_MAX:
        return jsonify({'success': False, 'message': 'Video 100MB\'dan büyük olamaz.'}), 400

    videos_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'adaylar', str(aday.id), 'videos')
    os.makedirs(videos_dir, exist_ok=True)
    fname = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{ext}"
    fpath = os.path.join(videos_dir, fname)
    v.save(fpath)
    rel = f"adaylar/{aday.id}/videos/{fname}"
    m = AdayMedya(
        aday_id=aday.id, tip='video',
        dosya_adi=secure_filename(v.filename),
        dosya_yolu=rel, dosya_boyut=boyut,
        mime_type=v.mimetype or f'video/{ext}',
    )
    db.session.add(m)
    db.session.commit()
    return jsonify({'success': True, 'eklenen': _kariyer_medya_dict(m)})


@kariyer_bp.route('/evrak/<token>/medya/<int:medya_id>/sil', methods=['POST'])
def medya_sil(token, medya_id):
    """Public medya silme (token + sahiplik kontrolü)."""
    import os

    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first()
    if not aday:
        return jsonify({'success': False, 'message': 'Geçersiz link.'}), 403

    m = AdayMedya.query.filter_by(id=medya_id, aday_id=aday.id).first()
    if not m:
        return jsonify({'success': False, 'message': 'Medya bulunamadı.'}), 404

    try:
        full = os.path.join(current_app.config['UPLOAD_FOLDER'], m.dosya_yolu)
        if os.path.exists(full):
            os.remove(full)
    except Exception as e:
        current_app.logger.warning(f"Medya silinemedi: {e}")

    db.session.delete(m)
    db.session.commit()
    return jsonify({'success': True})


# ============================================================
# KARGO GÖNDERİM BARKODU (PUBLIC - TOKEN İLE)
# ============================================================

_BARKOD_EXTS = {'jpg', 'jpeg', 'png', 'webp'}
_BARKOD_MAX = 10 * 1024 * 1024


@kariyer_bp.route('/evrak/<token>/kargo-barkod', methods=['POST'])
def kargo_barkod_yukle(token):
    """Kargo gönderim barkodu fotoğrafı yükleme (public, token ile)."""
    import os
    from werkzeug.utils import secure_filename

    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first()
    if not aday:
        flash('Geçersiz veya süresi dolmuş link.', 'danger')
        return redirect(url_for('kariyer.pozisyonlar'))

    foto = request.files.get('kargo_barkod')
    if not foto or not foto.filename:
        # Kargo barkodu opsiyonel - dosya seçilmeden gönderilirse sessizce geri dön
        return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))

    ext = foto.filename.rsplit('.', 1)[1].lower() if '.' in foto.filename else ''
    if ext not in _BARKOD_EXTS:
        flash('Geçersiz format. Sadece JPG, PNG veya WEBP yükleyebilirsiniz.', 'danger')
        return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))

    foto.seek(0, os.SEEK_END)
    boyut = foto.tell()
    foto.seek(0)
    if boyut > _BARKOD_MAX:
        flash('Dosya 10MB\'dan büyük olamaz.', 'danger')
        return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))

    barkod_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'adaylar', str(aday.id), 'kargo_barkod')
    os.makedirs(barkod_dir, exist_ok=True)

    # Eski barkod fotoğrafını temizle (tek dosya tutulur)
    if aday.kargo_barkod_foto:
        try:
            eski = os.path.join(current_app.config['UPLOAD_FOLDER'], aday.kargo_barkod_foto)
            if os.path.exists(eski):
                os.remove(eski)
        except Exception as e:
            current_app.logger.warning(f"Eski kargo barkodu silinemedi: {e}")

    fname = f"barkod_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{ext}"
    foto.save(os.path.join(barkod_dir, fname))
    aday.kargo_barkod_foto = f"adaylar/{aday.id}/kargo_barkod/{fname}"
    db.session.commit()

    flash('Kargo gönderim barkodu başarıyla yüklendi.', 'success')
    return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))


# ============================================================
# ŞİRKET EVRAKLARI İNDİRME (PUBLIC - TOKEN İLE)
# ============================================================

@kariyer_bp.route('/evrak/<token>/sirket-evrak/<int:sablon_id>')
def sirket_evrak_indir(token, sablon_id):
    """Adayın kadrosuna tanımlı sözleşme şablonunu indir (public, token ile)."""
    import os
    from flask import send_file

    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first()
    if not aday:
        flash('Geçersiz veya süresi dolmuş link.', 'danger')
        return redirect(url_for('kariyer.pozisyonlar'))

    sablon = SozlesmeSablonu.query.filter_by(id=sablon_id, is_deleted=False, aktif=True).first()
    if not sablon or not sablon.sablon_dosya:
        flash('Evrak bulunamadı.', 'danger')
        return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))

    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], sablon.sablon_dosya)
    if not os.path.exists(full_path):
        flash('Evrak dosyası bulunamadı.', 'danger')
        return redirect(url_for('kariyer.evrak_yukle_sayfa', token=token))

    ext = sablon.sablon_dosya.rsplit('.', 1)[1].lower() if '.' in sablon.sablon_dosya else 'docx'
    indirme_adi = f"{sablon.ad}.{ext}"
    return send_file(full_path, as_attachment=True, download_name=indirme_adi)


@kariyer_bp.route('/evrak/<token>/kvkk-metni')
def kvkk_indir(token):
    """KVKK aydınlatma metnini indirilebilir HTML olarak ver (public, token ile)."""
    from flask import Response

    aday = Aday.query.filter_by(davet_token=token, is_deleted=False).first()
    if not aday:
        flash('Geçersiz veya süresi dolmuş link.', 'danger')
        return redirect(url_for('kariyer.pozisyonlar'))

    html = render_template('kariyer/kvkk_indir.html', aday=aday)
    return Response(
        html,
        mimetype='text/html',
        headers={'Content-Disposition': 'attachment; filename=kvkk-aydinlatma-metni.html'},
    )
