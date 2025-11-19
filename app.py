from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from database import get_db, log_islem
from datetime import datetime, date
from werkzeug.utils import secure_filename
from email_service import yeni_ise_giris_bildirimi, isten_cikis_bildirimi
import os
import hashlib
import pandas as pd
import io
from functools import wraps
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'ozanerenkayan1988'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Dosya yükleme ayarları
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    """Dosya uzantısı kontrol"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(size_bytes):
    """Dosya boyutunu MB olarak döndür"""
    return round(size_bytes / (1024 * 1024), 2)

# Login gerekli decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin gerekli decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'warning')
            return redirect(url_for('login'))
        
        conn = get_db()
        user = conn.execute('SELECT role FROM users WHERE id = %s', (session['user_id'],)).fetchone()
        conn.close()
        
        if not user or user['role'] != 'admin':
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
    
# Manager veya Admin gerekli decorator
def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'warning')
            return redirect(url_for('login'))
        
        conn = get_db()
        user = conn.execute('SELECT role FROM users WHERE id = %s', (session['user_id'],)).fetchone()
        conn.close()
        
        if not user or user['role'] not in ['admin', 'manager']:
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Yetki kontrol fonksiyonu
def has_permission(action):
    """
    Kullanıcının belirli bir işlem için yetkisi var mı?
    action: 'view', 'add', 'edit', 'delete'
    """
    if 'user_id' not in session:
        return False
    
    role = session.get('role', 'user')
    
    permissions = {
        'admin': ['view', 'add', 'edit', 'delete', 'manage_users'],
        'manager': ['view', 'add', 'edit', 'delete'],
        'user': ['view', 'add']
    }
    
    return action in permissions.get(role, [])  

# Template'lerde kullanılacak fonksiyonlar
@app.context_processor
def utility_processor():
    """Template'lerde kullanılacak yardımcı fonksiyonlar"""
    def check_permission(action):
        return has_permission(action)
    return dict(has_permission=check_permission)    
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login sayfası"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db()
        user = conn.execute('''
            SELECT * FROM users 
            WHERE username = %s AND password_hash = %s AND aktif = TRUE
        ''', (username, password_hash)).fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            
            # Son giriş tarihini güncelle
            conn.execute('UPDATE users SET son_giris_tarihi = %s WHERE id = %s', 
                        (datetime.now(), user['id']))
            conn.commit()
            conn.close()
            
            log_islem('GİRİŞ', 'users', user['id'], f'{username} sisteme giriş yaptı')
            flash(f'Hoş geldiniz, {user["full_name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            conn.close()
            flash('Kullanıcı adı veya şifre hatalı!', 'danger')
    
    return render_template('login.html')
   


@app.route('/logout')
def logout():
    """Logout"""
    username = session.get('username', 'Bilinmeyen')
    user_id = session.get('user_id')
    
    if user_id:
        log_islem('ÇIKIŞ', 'users', user_id, f'{username} sistemden çıkış yaptı')
    
    session.clear()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('login'))    

# app.py içindeki index() fonksiyonunu bu kodla değiştir

@app.route('/')
@login_required
def index():
    """Ana sayfa - Dashboard"""
    conn = get_db()
    
    # Proje bazında özet
    projeler = conn.execute('''
        SELECT 
            p.id,
            p.proje_adi,
            COUNT(DISTINCT hk.id) as toplam_kadro,
            SUM(hk.hedef_kisi_sayisi) as toplam_hedef,
            SUM(hk.dolu_kisi_sayisi) as toplam_dolu,
            COUNT(DISTINCT a.id) as toplam_aday,
            COUNT(DISTINCT c.id) as toplam_calisan
        FROM projeler p
        LEFT JOIN hedef_kadrolar hk ON p.id = hk.proje_id
        LEFT JOIN adaylar a ON hk.id = a.kadro_id
        LEFT JOIN calisanlar c ON hk.id = c.kadro_id AND c.aktif = TRUE
        WHERE p.aktif = TRUE
        GROUP BY p.id, p.proje_adi
    ''').fetchall()
    
    # Kadro bazında detay
    kadrolar = conn.execute('''
        SELECT 
            hk.id,
            hk.proje_id,
            hk.pozisyon_adi,
            hk.calisma_sekli,
            hk.mudurluk_id,
            hk.direktorluk_id,
            hk.il_id,
            hk.ilce_id,
            hk.magaza_adi,
            hk.hedef_kisi_sayisi,
            hk.dolu_kisi_sayisi,
            hk.aracli_durum,
            hk.durum,
            hk.olusturma_tarihi,
            p.proje_adi,
            m.mudurluk_adi,
            d.direktorluk_adi,
            i.il_adi,
            ic.ilce_adi,
            COUNT(DISTINCT a.id) as aday_sayisi,
            COUNT(DISTINCT CASE WHEN c.aktif = TRUE THEN c.id END) as calisan_sayisi
        FROM hedef_kadrolar hk
        LEFT JOIN projeler p ON hk.proje_id = p.id
        LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
        LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
        LEFT JOIN iller i ON hk.il_id = i.id
        LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
        LEFT JOIN adaylar a ON hk.id = a.kadro_id
        LEFT JOIN calisanlar c ON hk.id = c.kadro_id
        GROUP BY hk.id, hk.proje_id, hk.pozisyon_adi, hk.calisma_sekli, hk.mudurluk_id, 
                 hk.direktorluk_id, hk.il_id, hk.ilce_id, hk.magaza_adi, hk.hedef_kisi_sayisi,
                 hk.dolu_kisi_sayisi, hk.aracli_durum, hk.durum, hk.olusturma_tarihi,
                 p.proje_adi, m.mudurluk_adi, d.direktorluk_adi, i.il_adi, ic.ilce_adi
        ORDER BY p.proje_adi, i.il_adi, ic.ilce_adi
    ''').fetchall()
    
    # Son işlemler
    son_islemler = conn.execute('''
        SELECT * FROM surec_loglari 
        ORDER BY islem_tarihi DESC 
        LIMIT 10
    ''').fetchall()
    
    # === GRAFİK VERİLERİ ===
    
    # 1. İl bazında çalışan dağılımı (Top 10)
    il_dagilim = conn.execute('''
        SELECT 
            i.il_adi,
            COUNT(DISTINCT c.id) as calisan_sayisi
        FROM calisanlar c
        LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
        LEFT JOIN iller i ON hk.il_id = i.id
        WHERE c.aktif = TRUE
        GROUP BY i.il_adi
        ORDER BY calisan_sayisi DESC
        LIMIT 10
    ''').fetchall()
    
    # 2. Aylık işe giriş trendi (Son 6 ay)
    aylik_giris = conn.execute('''
        SELECT 
            TO_CHAR(ise_baslama_tarihi, 'YYYY-MM') as ay,
            COUNT(*) as sayi
        FROM calisanlar
        WHERE ise_baslama_tarihi >= CURRENT_DATE - INTERVAL '6 months'
        AND aktif = TRUE
        GROUP BY ay
        ORDER BY ay
    ''').fetchall()
    
    # 3. Araçlı/Araçsız dağılım
    arac_dagilim = conn.execute('''
        SELECT 
            hk.aracli_durum,
            COUNT(DISTINCT c.id) as calisan_sayisi
        FROM calisanlar c
        LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
        WHERE c.aktif = TRUE
        GROUP BY hk.aracli_durum
    ''').fetchall()
    
    # 4. Müdürlük bazında dağılım (varsa)
    mudurluk_dagilim = conn.execute('''
        SELECT 
            COALESCE(m.mudurluk_adi, 'Tanımsız') as mudurluk,
            COUNT(DISTINCT c.id) as calisan_sayisi
        FROM calisanlar c
        LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
        LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
        WHERE c.aktif = TRUE
        GROUP BY mudurluk
        ORDER BY calisan_sayisi DESC
        LIMIT 8
    ''').fetchall()
    
    # 5. HARİTA İÇİN: TÜM İLLER VERİSİ - YENİ
    harita_verisi = conn.execute('''
        SELECT 
            i.il_adi,
            COUNT(DISTINCT hk.id) as kadro_sayisi,
            COUNT(DISTINCT c.id) as calisan_sayisi,
            COUNT(DISTINCT a.id) as aday_sayisi
        FROM iller i
        LEFT JOIN hedef_kadrolar hk ON i.id = hk.il_id
        LEFT JOIN calisanlar c ON hk.id = c.kadro_id AND c.aktif = TRUE
        LEFT JOIN adaylar a ON hk.id = a.kadro_id AND a.durum = 'Aday'
        GROUP BY i.id, i.il_adi
        ORDER BY i.il_adi
    ''').fetchall()
    
    # 6. Genel istatistikler
    stats = {
        'toplam_proje': conn.execute('SELECT COUNT(*) as cnt FROM projeler WHERE aktif = TRUE').fetchone()['cnt'],
        'toplam_kadro': conn.execute('SELECT COUNT(*) as cnt FROM hedef_kadrolar').fetchone()['cnt'],
        'toplam_aday': conn.execute('SELECT COUNT(*) as cnt FROM adaylar').fetchone()['cnt'],
        'toplam_calisan': conn.execute('SELECT COUNT(*) as cnt FROM calisanlar WHERE aktif = TRUE').fetchone()['cnt'],
        'hedef_toplam': conn.execute('SELECT SUM(hedef_kisi_sayisi) as total FROM hedef_kadrolar').fetchone()['total'] or 0,
        'dolu_toplam': conn.execute('SELECT SUM(dolu_kisi_sayisi) as total FROM hedef_kadrolar').fetchone()['total'] or 0,
        'acik_kadro': conn.execute("SELECT COUNT(*) as cnt FROM hedef_kadrolar WHERE durum = 'Açık'").fetchone()['cnt'],
        'dolu_kadro': conn.execute("SELECT COUNT(*) as cnt FROM hedef_kadrolar WHERE durum = 'Dolu'").fetchone()['cnt']
    }
    
    conn.close()
    
    return render_template('index.html', 
                         projeler=projeler, 
                         kadrolar=kadrolar,
                         son_islemler=son_islemler,
                         il_dagilim=il_dagilim,
                         aylik_giris=aylik_giris,
                         arac_dagilim=arac_dagilim,
                         mudurluk_dagilim=mudurluk_dagilim,
                         harita_verisi=harita_verisi,  # YENİ
                         stats=stats)

@app.route('/projeler')
@login_required
def projeler():
    """Proje listesi"""
    conn = get_db()
    projeler = conn.execute('''
        SELECT p.*, m.musteri_adi, m.logo_yolu
        FROM projeler p
        LEFT JOIN musteriler m ON p.musteri_id = m.id
        ORDER BY p.olusturma_tarihi DESC
    ''').fetchall()
    conn.close()
    return render_template('projeler.html', projeler=projeler)

@app.route('/proje/ekle', methods=['GET', 'POST'])
@manager_required
def proje_ekle():
    """Yeni proje ekle"""
    if request.method == 'POST':
        proje_adi = request.form['proje_adi']
        aciklama = request.form.get('aciklama', '')
        musteri_id = request.form.get('musteri_id') or None
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO projeler (proje_adi, aciklama, musteri_id) VALUES (%s, %s, %s)', 
                      (proje_adi, aciklama, musteri_id))
        proje_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        log_islem('EKLEME', 'projeler', proje_id, f'{proje_adi} projesi oluşturuldu')
        flash('Proje başarıyla eklendi!', 'success')
        return redirect(url_for('projeler'))
    
    # Müşteri listesi
    conn = get_db()
    musteriler = conn.execute('SELECT * FROM musteriler WHERE aktif = TRUE ORDER BY musteri_adi').fetchall()
    conn.close()
    
    return render_template('proje_form.html', musteriler=musteriler)

@app.route('/kadrolar')
@login_required
def kadrolar():
    """Kadro listesi"""
    conn = get_db()
    kadrolar = conn.execute('''
        SELECT hk.id,
               hk.proje_id,
               p.proje_adi,
               hk.pozisyon_adi,
               hk.calisma_sekli,
               m.mudurluk_adi,
               d.direktorluk_adi,
               i.il_adi,
               ic.ilce_adi,
               hk.magaza_adi,
               hk.aracli_durum,
               hk.hedef_kisi_sayisi,
               hk.dolu_kisi_sayisi,
               hk.durum,
               hk.olusturma_tarihi,
               COUNT(DISTINCT a.id) as aday_sayisi,
               COUNT(DISTINCT CASE WHEN c.aktif = TRUE THEN c.id END) as calisan_sayisi
        FROM hedef_kadrolar hk
        LEFT JOIN projeler p ON hk.proje_id = p.id
        LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
        LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
        LEFT JOIN iller i ON hk.il_id = i.id
        LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
        LEFT JOIN adaylar a ON hk.id = a.kadro_id
        LEFT JOIN calisanlar c ON hk.id = c.kadro_id
        GROUP BY hk.id, hk.proje_id, p.proje_adi, hk.pozisyon_adi, hk.calisma_sekli,
                 m.mudurluk_adi, d.direktorluk_adi, i.il_adi, ic.ilce_adi, hk.magaza_adi,
                 hk.aracli_durum, hk.hedef_kisi_sayisi, hk.dolu_kisi_sayisi, hk.durum,
                 hk.olusturma_tarihi
        ORDER BY p.proje_adi, hk.olusturma_tarihi DESC
    ''').fetchall()
    conn.close()
    return render_template('kadrolar.html', kadrolar=kadrolar)

@app.route('/kadro/ekle', methods=['GET', 'POST'])
@login_required
def kadro_ekle():
    """Yeni kadro ekle"""
    if request.method == 'POST':
        # Form verilerini al
        proje_id = request.form['proje_id']
        pozisyon_adi = request.form['pozisyon_adi']
        calisma_sekli = request.form['calisma_sekli']  # YENİ
        mudurluk_id = request.form.get('mudurluk_id') or None
        direktorluk_id = request.form.get('direktorluk_id') or None
        il_id = request.form['il_id']
        ilce_id = request.form.get('ilce_id') or None
        magaza_adi = request.form.get('magaza_adi', '')
        hedef_kisi_sayisi = request.form['hedef_kisi_sayisi']
        aracli_durum = request.form['aracli_durum']
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Kadro ekle
        cursor.execute('''
    INSERT INTO hedef_kadrolar 
    (proje_id, pozisyon_adi, mudurluk_id, direktorluk_id, il_id, ilce_id, 
     magaza_adi, hedef_kisi_sayisi, dolu_kisi_sayisi, aracli_durum, calisma_sekli)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
''', (proje_id, pozisyon_adi, mudurluk_id, direktorluk_id, il_id, ilce_id, 
      magaza_adi, hedef_kisi_sayisi, 0, aracli_durum, calisma_sekli))
        
        kadro_id = cursor.lastrowid
        
        # Durum güncelle (başlangıçta her zaman Açık)
        cursor.execute('UPDATE hedef_kadrolar SET durum = %s WHERE id = %s', ('Açık', kadro_id))
        
        conn.commit()
        conn.close()
        
        log_islem('EKLEME', 'hedef_kadrolar', kadro_id, f'{pozisyon_adi} kadrosu eklendi')
        flash('Kadro başarıyla eklendi!', 'success')
        return redirect(url_for('kadrolar'))
    
    # GET request - form için gerekli verileri çek
    conn = get_db()
    
    projeler = conn.execute('''
        SELECT * FROM projeler 
        WHERE aktif = TRUE 
        ORDER BY proje_adi
    ''').fetchall()
    
    mudurluker = conn.execute('''
        SELECT * FROM mudurluker 
        ORDER BY mudurluk_adi
    ''').fetchall()
    
    direktorlukler = conn.execute('''
        SELECT * FROM direktorlukler 
        ORDER BY direktorluk_adi
    ''').fetchall()
    
    iller = conn.execute('''
        SELECT * FROM iller 
        ORDER BY il_adi
    ''').fetchall()
    
    # Çalışma şekilleri - YENİ
    calisma_sekilleri = conn.execute('''
        SELECT calisma_sekli FROM calisma_sekilleri 
        WHERE aktif = TRUE 
        ORDER BY calisma_sekli
    ''').fetchall()
    
    conn.close()
    
    return render_template('kadro_form.html', 
                         projeler=projeler, 
                         mudurluker=mudurluker,
                         direktorlukler=direktorlukler,
                         iller=iller,
                         calisma_sekilleri=calisma_sekilleri)

@app.route('/adaylar')
@login_required
def adaylar():
    """Aday listesi"""
    conn = get_db()
    adaylar_raw = conn.execute('''
        SELECT a.*, 
               hk.pozisyon_adi, hk.magaza_adi, hk.aracli_durum,
               hk.calisma_sekli,
               m.mudurluk_adi,
               d.direktorluk_adi,
               i.il_adi,
               ic.ilce_adi,
               p.proje_adi,
               k.kaynak_adi
        FROM adaylar a
        LEFT JOIN hedef_kadrolar hk ON a.kadro_id = hk.id
        LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
        LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
        LEFT JOIN iller i ON hk.il_id = i.id
        LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
        LEFT JOIN projeler p ON hk.proje_id = p.id
        LEFT JOIN kaynaklar k ON a.kaynak_id = k.id
        ORDER BY a.basvuru_tarihi DESC
    ''').fetchall()
    
    # Yaş hesaplama
    adaylar = []
    for aday in adaylar_raw:
        aday_dict = dict(aday)
        
        # Yaş hesapla
        if aday_dict.get('dogum_tarihi'):
            try:
                dogum = datetime.strptime(aday_dict['dogum_tarihi'], '%Y-%m-%d')
                bugun = datetime.now()
                
                yil = bugun.year - dogum.year
                ay = bugun.month - dogum.month
                
                if ay < 0:
                    yil -= 1
                    ay += 12
                
                if bugun.day < dogum.day:
                    ay -= 1
                    if ay < 0:
                        yil -= 1
                        ay += 12
                
                aday_dict['yas'] = f"{yil}.{ay}"
                aday_dict['yas_yil'] = yil
            except:
                aday_dict['yas'] = None
                aday_dict['yas_yil'] = None
        else:
            aday_dict['yas'] = None
            aday_dict['yas_yil'] = None
        
        adaylar.append(aday_dict)
    
    conn.close()
    return render_template('adaylar.html', adaylar=adaylar)

@app.route('/aday/ekle', methods=['GET', 'POST'])
@login_required
def aday_ekle():
    """Yeni aday ekle"""
    if request.method == 'POST':
        # Form verilerini al
        kadro_id = request.form['kadro_id']
        ad_soyad = request.form['ad_soyad']
        telefon = request.form.get('telefon', '')
        email = request.form.get('email', '')
        tc_kimlik = request.form.get('tc_kimlik', '')
        dogum_tarihi = request.form.get('dogum_tarihi', None)  # â† BURASI VAR MI?
        notlar = request.form.get('notlar', '')
        
        # KAYNAK BİLGİSİ
        kaynak_id = request.form.get('kaynak_id') or None
        kaynak_diger = request.form.get('kaynak_diger', '').strip()
        
        # Eğer "Diğer" seçilmişse kaynak_id'yi NULL yap
        if kaynak_id and int(kaynak_id) == -1:
            kaynak_id = None
        
        # DEBUG: Form verilerini kontrol et
        print(f"DEBUG - Dogum Tarihi: [{dogum_tarihi}]")  # â† DEBUG EKLENDİ
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO adaylar (kadro_id, ad_soyad, telefon, email, tc_kimlik, dogum_tarihi, notlar, kaynak_id, kaynak_diger)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (kadro_id, ad_soyad, telefon or None, email or None, tc_kimlik or None, 
              dogum_tarihi or None, notlar or None, kaynak_id, kaynak_diger if kaynak_diger else None))
        
        aday_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        log_islem('EKLEME', 'adaylar', aday_id, f'{ad_soyad} adayı sisteme eklendi')
        flash('Aday başarıyla eklendi!', 'success')
        return redirect(url_for('adaylar'))
    
    # GET request için
    conn = get_db()
    kadrolar = conn.execute('''
        SELECT hk.*, 
               p.proje_adi,
               m.mudurluk_adi,
               d.direktorluk_adi,
               i.il_adi,
               ic.ilce_adi
        FROM hedef_kadrolar hk
        LEFT JOIN projeler p ON hk.proje_id = p.id
        LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
        LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
        LEFT JOIN iller i ON hk.il_id = i.id
        LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
        WHERE hk.durum = 'Açık'
        ORDER BY p.proje_adi, hk.pozisyon_adi
    ''').fetchall()
    
    # Kaynaklar listesi
    kaynaklar = conn.execute('''
        SELECT * FROM kaynaklar 
        WHERE aktif = TRUE 
        ORDER BY kaynak_adi
    ''').fetchall()
    
    conn.close()
    return render_template('aday_form.html', kadrolar=kadrolar, kaynaklar=kaynaklar)

@app.route('/aday/<int:aday_id>/calisana-donustur', methods=['POST'])
@manager_required
def aday_calisana_donustur(aday_id):
    """Adayı çalışana dönüştür"""
    ise_baslama_tarihi = request.form.get('ise_baslama_tarihi', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Aday ve kadro bilgilerini tek sorguda al
    aday_detay_raw = conn.execute('''
    SELECT a.*, 
           hk.pozisyon_adi, 
           hk.magaza_adi, 
           hk.proje_id,
           hk.aracli_durum,
           hk.calisma_sekli,
           m.mudurluk_adi,
           d.direktorluk_adi,
           i.il_adi,
           ic.ilce_adi,
           p.proje_adi
    FROM adaylar a
    LEFT JOIN hedef_kadrolar hk ON a.kadro_id = hk.id
    LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
    LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
    LEFT JOIN iller i ON hk.il_id = i.id
    LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
    LEFT JOIN projeler p ON hk.proje_id = p.id
    WHERE a.id = %s
    ''', (aday_id,)).fetchone()
    
    if not aday_detay_raw:
        conn.close()
        flash('Aday bulunamadı!', 'danger')
        return redirect(url_for('adaylar'))
    
    # Dict'e çevir
    aday_detay = dict(aday_detay_raw)
    
    # Çalışan olarak ekle
    cursor.execute('''
        INSERT INTO calisanlar (aday_id, kadro_id, ad_soyad, telefon, email, tc_kimlik, 
                               dogum_tarihi, ise_baslama_tarihi, aracli_durum)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (aday_id, aday_detay['kadro_id'], aday_detay['ad_soyad'], aday_detay['telefon'], 
          aday_detay['email'], aday_detay['tc_kimlik'], aday_detay.get('dogum_tarihi'),
          ise_baslama_tarihi, aday_detay['aracli_durum']))
    
    # Aday durumunu güncelle
    cursor.execute('UPDATE adaylar SET durum = %s, ise_baslama_tarihi = %s WHERE id = %s',
                   ('Çalışan', ise_baslama_tarihi, aday_id))
    
    # Kadro dolu sayısını artır
    cursor.execute('''
        UPDATE hedef_kadrolar 
        SET dolu_kisi_sayisi = dolu_kisi_sayisi + 1
        WHERE id = %s
    ''', (aday_detay['kadro_id'],))
    
    # Kadro durumunu kontrol et ve güncelle
    cursor.execute('''
        UPDATE hedef_kadrolar 
        SET durum = CASE 
            WHEN dolu_kisi_sayisi >= hedef_kisi_sayisi THEN 'Dolu'
            ELSE 'Açık'
        END
        WHERE id = %s
    ''', (aday_detay['kadro_id'],))
    
    conn.commit()
    
    # Email bildirimi gönder
    print("ðŸ”¥ðŸ”¥ðŸ”¥ EMAIL KODU ÇALIŞTI! ðŸ”¥ðŸ”¥ðŸ”¥")
    try:
        aday_bilgileri = {
            'id': aday_id,
            'ad_soyad': aday_detay['ad_soyad'],
            'tc_kimlik': aday_detay['tc_kimlik'],
            'dogum_tarihi': aday_detay.get('dogum_tarihi'),
            'telefon': aday_detay['telefon'] or '-',
            'email': aday_detay['email'] or '-',
            'ise_baslama_tarihi': ise_baslama_tarihi,
            'proje_adi': aday_detay['proje_adi'],
            'pozisyon_adi': aday_detay['pozisyon_adi'],
            'mudurluk_adi': aday_detay['mudurluk_adi'] or '-',  # â† YENİ
            'direktorluk_adi': aday_detay['direktorluk_adi'] or '-',  # â† YENİ
            'il': aday_detay['il_adi'],
            'ilce': aday_detay['ilce_adi'] or '-',
            'magaza_adi': aday_detay['magaza_adi'] or '-',
            'aracli_durum': aday_detay['aracli_durum'],
            'calisma_sekli': aday_detay['calisma_sekli'],
        }  
        
        print(f"Aday bilgileri: {aday_bilgileri}")
        
        email_basarili, email_mesaj = yeni_ise_giris_bildirimi(aday_bilgileri)
        
        print(f"Email sonucu: {email_basarili}, {email_mesaj}")
        
        if email_basarili:
            flash(email_mesaj, 'info')
    except Exception as e:
        print(f"âŒ Email gönderimi hatası: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Uyarı: Email bildirimi gönderilemedi', 'warning')
    
    conn.close()
    
    log_islem('DÖNÜŞÜM', 'calisanlar', aday_id, 
             f'{aday_detay["ad_soyad"]} adaydan çalışana dönüştürüldü', 
             session.get('username'))
    flash('Aday başarıyla çalışana dönüştürüldü!', 'success')
    return redirect(url_for('calisanlar'))

@app.route('/calisanlar')
@login_required
def calisanlar():
    """Çalışan listesi"""
    conn = get_db()
    calisanlar_raw = conn.execute('''
        SELECT c.*, 
               hk.pozisyon_adi, hk.magaza_adi, hk.aracli_durum,
               hk.calisma_sekli,
               m.mudurluk_adi,
               d.direktorluk_adi,
               i.il_adi,
               ic.ilce_adi,
               p.proje_adi
        FROM calisanlar c
        LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
        LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
        LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
        LEFT JOIN iller i ON hk.il_id = i.id
        LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
        LEFT JOIN projeler p ON hk.proje_id = p.id
        WHERE c.aktif = TRUE
        ORDER BY c.ise_baslama_tarihi DESC
    ''').fetchall()
    
    # Yaş hesaplama
    calisanlar = []
    for calisan in calisanlar_raw:
        calisan_dict = dict(calisan)
        
        # Yaş hesapla
        if calisan_dict.get('dogum_tarihi'):
            try:
                dogum = datetime.strptime(calisan_dict['dogum_tarihi'], '%Y-%m-%d')
                bugun = datetime.now()
                
                yil = bugun.year - dogum.year
                ay = bugun.month - dogum.month
                
                if ay < 0:
                    yil -= 1
                    ay += 12
                
                if bugun.day < dogum.day:
                    ay -= 1
                    if ay < 0:
                        yil -= 1
                        ay += 12
                
                calisan_dict['yas'] = f"{yil}.{ay}"
                calisan_dict['yas_yil'] = yil
            except:
                calisan_dict['yas'] = None
                calisan_dict['yas_yil'] = None
        else:
            calisan_dict['yas'] = None
            calisan_dict['yas_yil'] = None
        
        calisanlar.append(calisan_dict)
    
    conn.close()
    return render_template('calisanlar.html', calisanlar=calisanlar)
    
@app.route('/calisanlar/excel-export')
@login_required
def calisanlar_excel_export():
    """Çalışanları Excel'e aktar"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from io import BytesIO
    
    conn = get_db()
    calisanlar = conn.execute('''
        SELECT c.*, 
               hk.pozisyon_adi, hk.magaza_adi, hk.aracli_durum, hk.calisma_sekli,
               m.mudurluk_adi,
               d.direktorluk_adi,
               i.il_adi,
               ic.ilce_adi,
               p.proje_adi
        FROM calisanlar c
        LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
        LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
        LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
        LEFT JOIN iller i ON hk.il_id = i.id
        LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
        LEFT JOIN projeler p ON hk.proje_id = p.id
        WHERE c.aktif = TRUE
        ORDER BY c.ise_baslama_tarihi DESC
    ''').fetchall()
    conn.close()
    
    # Excel oluştur
    wb = Workbook()
    ws = wb.active
    ws.title = "Çalışanlar"
    
    # Başlık satırı
    headers = ['ID', 'Ad Soyad', 'Telefon', 'Email', 'TC Kimlik', 
               'Doğum Tarihi', 'Yaş',
               'Proje', 'Pozisyon', 'Müdürlük', 'Direktörlük',
               'İl', 'İlçe', 'Mağaza', 'Araç Durumu', 'Çalışma Şekli',
               'İşe Başlama', 'Durum']
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Veri satırları
    for row_idx, calisan in enumerate(calisanlar, 2):
        # Yaş hesapla
        yas_str = '-'
        if calisan['dogum_tarihi']:
            try:
                dogum = datetime.strptime(calisan['dogum_tarihi'], '%Y-%m-%d')
                bugun = datetime.now()
                yil = bugun.year - dogum.year
                ay = bugun.month - dogum.month
                if ay < 0:
                    yil -= 1
                    ay += 12
                if bugun.day < dogum.day:
                    ay -= 1
                    if ay < 0:
                        yil -= 1
                        ay += 12
                yas_str = f"{yil}.{ay}"
            except:
                pass
        
        ws.cell(row=row_idx, column=1, value=calisan['id'])
        ws.cell(row=row_idx, column=2, value=calisan['ad_soyad'])
        ws.cell(row=row_idx, column=3, value=calisan['telefon'] or '')
        ws.cell(row=row_idx, column=4, value=calisan['email'] or '')
        ws.cell(row=row_idx, column=5, value=calisan['tc_kimlik'] or '')
        ws.cell(row=row_idx, column=6, value=calisan['dogum_tarihi'] or '')
        ws.cell(row=row_idx, column=7, value=yas_str)
        ws.cell(row=row_idx, column=8, value=calisan['proje_adi'] or '')
        ws.cell(row=row_idx, column=9, value=calisan['pozisyon_adi'] or '')
        ws.cell(row=row_idx, column=10, value=calisan['mudurluk_adi'] or '')
        ws.cell(row=row_idx, column=11, value=calisan['direktorluk_adi'] or '')
        ws.cell(row=row_idx, column=12, value=calisan['il_adi'] or '')
        ws.cell(row=row_idx, column=13, value=calisan['ilce_adi'] or '')
        ws.cell(row=row_idx, column=14, value=calisan['magaza_adi'] or '')
        ws.cell(row=row_idx, column=15, value=calisan['aracli_durum'] or '')
        ws.cell(row=row_idx, column=16, value=calisan['calisma_sekli'] or '')
        ws.cell(row=row_idx, column=17, value=calisan['ise_baslama_tarihi'])
        ws.cell(row=row_idx, column=18, value='Aktif' if calisan['aktif'] else 'Pasif')
    
    # Sütun genişliklerini ayarla
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[column].width = min(max_length + 2, 50)
    
    # Dosyayı belleğe kaydet
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'calisanlar_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )    
    
@app.route('/calisan/<int:calisan_id>/cikis', methods=['GET'])
@login_required
def calisan_cikis(calisan_id):
    """İşten çıkış formu"""
    conn = get_db()
    
    # Çalışan bilgilerini getir
    calisan = conn.execute('''
        SELECT c.*, 
               hk.pozisyon_adi,
               p.proje_adi
        FROM calisanlar c
        LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
        LEFT JOIN projeler p ON hk.proje_id = p.id
        WHERE c.id = %s AND c.aktif = TRUE
    ''', (calisan_id,)).fetchone()
    
    if not calisan:
        flash('Çalışan bulunamadı veya zaten pasif durumda!', 'error')
        return redirect(url_for('calisanlar'))
    
    # Çıkış nedenleri
    cikis_nedenleri = conn.execute('''
        SELECT * FROM cikis_nedenleri 
        WHERE aktif = TRUE 
        ORDER BY neden
    ''').fetchall()
    
    conn.close()
    
    # Bugünün tarihi
    today = date.today().isoformat()
    now = datetime.now()
    
    return render_template('calisan_cikis.html', 
                         calisan=calisan,
                         cikis_nedenleri=cikis_nedenleri,
                         today=today,
                         now=now)


@app.route('/calisan/<int:calisan_id>/cikis/kaydet', methods=['POST'])
@login_required
def calisan_cikis_kaydet(calisan_id):
    """İşten çıkışı kaydet"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Çalışan kontrolü
    calisan = conn.execute('SELECT * FROM calisanlar WHERE id = %s AND aktif = TRUE', 
                          (calisan_id,)).fetchone()
    
    if not calisan:
        flash('Çalışan bulunamadı!', 'error')
        return redirect(url_for('calisanlar'))
    
    # Form verilerini al
    cikis_tarihi = request.form['cikis_tarihi']
    cikis_nedeni = request.form['cikis_nedeni']
    liste_durumu = request.form['liste_durumu']
    tekrar_ise_alinabilir = 1 if request.form.get('tekrar_ise_alinabilir') else 0
    
    # Checklist
    zimmet_teslim = 1 if request.form.get('zimmet_teslim') else 0
    kiyafet_teslim = 1 if request.form.get('kiyafet_teslim') else 0
    anahtar_teslim = 1 if request.form.get('anahtar_teslim') else 0
    kimlik_teslim = 1 if request.form.get('kimlik_teslim') else 0
    
    # Tazminat
    ihbar_tazminat_durumu = request.form.get('ihbar_tazminat_durumu', '')
    kidem_tazminat_durumu = request.form.get('kidem_tazminat_durumu', '')
    
    # Notlar
    yonetici_notu = request.form.get('yonetici_notu', '')
    ik_notu = request.form.get('ik_notu', '')
    genel_degerlendirme = request.form.get('genel_degerlendirme', '')
    
    try:
        # 1. Çıkış kaydı oluştur
        cursor.execute('''
            INSERT INTO cikis_kayitlari 
            (calisan_id, cikis_tarihi, cikis_nedeni, liste_durumu, tekrar_ise_alinabilir,
             zimmet_teslim, kiyafet_teslim, anahtar_teslim, kimlik_teslim,
             ihbar_tazminat_durumu, kidem_tazminat_durumu,
             yonetici_notu, ik_notu, genel_degerlendirme, islem_yapan)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (calisan_id, cikis_tarihi, cikis_nedeni, liste_durumu, tekrar_ise_alinabilir,
              zimmet_teslim, kiyafet_teslim, anahtar_teslim, kimlik_teslim,
              ihbar_tazminat_durumu, kidem_tazminat_durumu,
              yonetici_notu, ik_notu, genel_degerlendirme,
              session.get('username')))
        
        cikis_kayit_id = cursor.lastrowid
        
        # 2. Çalışanı pasif yap ve çıkış bilgilerini güncelle
        cursor.execute('''
            UPDATE calisanlar 
            SET aktif = FALSE,
                cikis_tarihi = %s,
                cikis_nedeni = %s,
                liste_durumu = %s
            WHERE id = %s
        ''', (cikis_tarihi, cikis_nedeni, liste_durumu, calisan_id))
        
        # 3. YENI: Aday durumunu güncelle
        aday_id = calisan['aday_id']
        if aday_id:
            cursor.execute('''
            UPDATE adaylar 
            SET durum = 'Pasif'
               WHERE id = %s
    ''', (aday_id,))
        
        # 4. Kadro doluluk sayısını güncelle
        kadro_id = calisan['kadro_id']
        cursor.execute('''
            UPDATE hedef_kadrolar 
            SET dolu_kisi_sayisi = dolu_kisi_sayisi - 1
            WHERE id = %s
        ''', (kadro_id,))
        
        # 5. Kadro durumunu güncelle (Dolu â†’ Açık)
        cursor.execute('''
            UPDATE hedef_kadrolar 
            SET durum = CASE 
                WHEN dolu_kisi_sayisi < hedef_kisi_sayisi THEN 'Açık'
                ELSE 'Dolu'
            END
            WHERE id = %s
        ''', (kadro_id,))
        
        conn.commit()
        
        # Log kaydet
        log_islem('ÇIKIŞ', 'calisanlar', calisan_id, 
                 f'{calisan["ad_soyad"]} - {cikis_nedeni} nedeniyle işten çıkış')
        # ============================================
        # YENİ: E-POSTA BİLDİRİMİ
        # ============================================
        try:
            # Çalışan detay bilgilerini getir
            calisan_detay = conn.execute('''
    SELECT c.*,
           hk.pozisyon_adi,
           hk.magaza_adi,
           hk.aracli_durum,
           m.mudurluk_adi,
           d.direktorluk_adi,
           p.proje_adi,
           i.il_adi,
           ic.ilce_adi
    FROM calisanlar c
    LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
    LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
    LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
    LEFT JOIN projeler p ON hk.proje_id = p.id
    LEFT JOIN iller i ON hk.il_id = i.id
    LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
    WHERE c.id = %s
''', (calisan_id,)).fetchone()
            
            cikis_bilgileri = {
                'id': cikis_kayit_id,
                'ad_soyad': calisan_detay['ad_soyad'],
                'telefon': calisan_detay['telefon'] or '-',
                'email': calisan_detay['email'] or '-',
                'tc_kimlik': calisan_detay['tc_kimlik'] or '-',
                'proje_adi': calisan_detay['proje_adi'],
                'pozisyon_adi': calisan_detay['pozisyon_adi'],
                'mudurluk_adi': calisan_detay['mudurluk_adi'] or '-',  # â† YENİ
                'direktorluk_adi': calisan_detay['direktorluk_adi'] or '-',  # â† YENİ
                'il': calisan_detay['il_adi'],
                'ilce': calisan_detay['ilce_adi'] or '-',
                'magaza_adi': calisan_detay['magaza_adi'] or '-',
                'aracli_durum': calisan_detay['aracli_durum'] or 'Araçsız',
                'ise_baslama_tarihi': calisan_detay['ise_baslama_tarihi'],
                'cikis_tarihi': cikis_tarihi,
                'cikis_nedeni': cikis_nedeni,
                'liste_durumu': liste_durumu,
                'tekrar_ise_alinabilir': tekrar_ise_alinabilir,
                'zimmet_teslim': zimmet_teslim,
                'kiyafet_teslim': kiyafet_teslim,
                'anahtar_teslim': anahtar_teslim,
                'kimlik_teslim': kimlik_teslim,
                'ihbar_tazminat_durumu': ihbar_tazminat_durumu,
                'kidem_tazminat_durumu': kidem_tazminat_durumu,
                'yonetici_notu': yonetici_notu,
                'ik_notu': ik_notu,
                'genel_degerlendirme': genel_degerlendirme,
                'islem_yapan': session.get('username')
            }
            
            email_basarili, email_mesaj = isten_cikis_bildirimi(cikis_bilgileri)
            if email_basarili:
                flash(email_mesaj, 'info')
        except Exception as e:
            print(f"Email gönderimi hatası: {e}")
            flash(f'Uyarı: Email bildirimi gönderilemedi', 'warning')
        
        return redirect(url_for('cikis_kayitlari'))
        
    except Exception as e:
        conn.rollback()
        flash(f'Hata oluştu: {str(e)}', 'error')
        return redirect(url_for('calisan_cikis', calisan_id=calisan_id))
    finally:
        conn.close()


@app.route('/cikis-kayitlari')
@login_required
def cikis_kayitlari():
    """Çıkış kayıtları listesi"""
    conn = get_db()
    
    kayitlar = conn.execute('''
        SELECT ck.*,
               c.ad_soyad,
               c.telefon,
               hk.pozisyon_adi,
               p.proje_adi,
               i.il_adi
        FROM cikis_kayitlari ck
        LEFT JOIN calisanlar c ON ck.calisan_id = c.id
        LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
        LEFT JOIN projeler p ON hk.proje_id = p.id
        LEFT JOIN iller i ON hk.il_id = i.id
        ORDER BY ck.cikis_tarihi DESC, ck.olusturma_tarihi DESC
    ''').fetchall()
    
    # İstatistikler
    stats = {
        'toplam_cikis': len(kayitlar),
        'beyaz_liste': len([k for k in kayitlar if k['liste_durumu'] == 'Beyaz']),
        'gri_liste': len([k for k in kayitlar if k['liste_durumu'] == 'Gri']),
        'kara_liste': len([k for k in kayitlar if k['liste_durumu'] == 'Kara'])
    }
    
    conn.close()
    
    return render_template('cikis_kayitlari.html', kayitlar=kayitlar, stats=stats)


@app.route('/cikis-kaydi/<int:kayit_id>')
@login_required
def cikis_detay(kayit_id):
    conn = get_db()
    
    kayit = conn.execute('''
        SELECT ck.*,
               c.ad_soyad,
               c.telefon,
               c.email,
               c.ise_baslama_tarihi,
               hk.pozisyon_adi,
               hk.magaza_adi,
               p.proje_adi,
               m.mudurluk_adi,
               d.direktorluk_adi,
               i.il_adi,
               ic.ilce_adi
        FROM cikis_kayitlari ck
        LEFT JOIN calisanlar c ON ck.calisan_id = c.id
        LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
        LEFT JOIN projeler p ON hk.proje_id = p.id
        LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
        LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
        LEFT JOIN iller i ON hk.il_id = i.id
        LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
        WHERE ck.id = %s
    ''', (kayit_id,)).fetchone()
    
    if not kayit:
        flash('Kayıt bulunamadı!', 'error')
        return redirect(url_for('cikis_kayitlari'))
    
    conn.close()
    
    # YENİ: Return ekle!
    return render_template('cikis_detay.html', kayit=kayit)    
    
@app.route('/adaylar/excel-export')
@login_required
def adaylar_excel_export():
    """Adayları Excel'e aktar"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from io import BytesIO
    
    conn = get_db()
    adaylar = conn.execute('''
        SELECT a.*, 
               hk.pozisyon_adi, hk.magaza_adi, hk.aracli_durum, hk.calisma_sekli,
               m.mudurluk_adi,
               d.direktorluk_adi,
               i.il_adi,
               ic.ilce_adi,
               p.proje_adi,
               k.kaynak_adi
        FROM adaylar a
        LEFT JOIN hedef_kadrolar hk ON a.kadro_id = hk.id
        LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
        LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
        LEFT JOIN iller i ON hk.il_id = i.id
        LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
        LEFT JOIN projeler p ON hk.proje_id = p.id
        LEFT JOIN kaynaklar k ON a.kaynak_id = k.id
        ORDER BY a.basvuru_tarihi DESC
    ''').fetchall()
    conn.close()
    
    # Excel oluştur
    wb = Workbook()
    ws = wb.active
    ws.title = "Adaylar"
    
    # Başlık satırı
    headers = ['ID', 'Ad Soyad', 'Telefon', 'Email', 'TC Kimlik', 
               'Doğum Tarihi', 'Yaş', 
               'Proje', 'Pozisyon', 'Müdürlük', 'Direktörlük', 
               'İl', 'İlçe', 'Mağaza', 'Araç Durumu', 'Çalışma Şekli',
               'Kaynak', 'Başvuru Tarihi', 'Durum']
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Veri satırları
    for row_idx, aday in enumerate(adaylar, 2):
        # Yaş hesapla
        yas_str = '-'
        if aday['dogum_tarihi']:
            try:
                dogum = datetime.strptime(aday['dogum_tarihi'], '%Y-%m-%d')
                bugun = datetime.now()
                yil = bugun.year - dogum.year
                ay = bugun.month - dogum.month
                if ay < 0:
                    yil -= 1
                    ay += 12
                if bugun.day < dogum.day:
                    ay -= 1
                    if ay < 0:
                        yil -= 1
                        ay += 12
                yas_str = f"{yil}.{ay}"
            except:
                pass
        
        ws.cell(row=row_idx, column=1, value=aday['id'])
        ws.cell(row=row_idx, column=2, value=aday['ad_soyad'])
        ws.cell(row=row_idx, column=3, value=aday['telefon'] or '')
        ws.cell(row=row_idx, column=4, value=aday['email'] or '')
        ws.cell(row=row_idx, column=5, value=aday['tc_kimlik'] or '')
        ws.cell(row=row_idx, column=6, value=aday['dogum_tarihi'] or '')
        ws.cell(row=row_idx, column=7, value=yas_str)
        ws.cell(row=row_idx, column=8, value=aday['proje_adi'] or '')
        ws.cell(row=row_idx, column=9, value=aday['pozisyon_adi'] or '')
        ws.cell(row=row_idx, column=10, value=aday['mudurluk_adi'] or '')
        ws.cell(row=row_idx, column=11, value=aday['direktorluk_adi'] or '')
        ws.cell(row=row_idx, column=12, value=aday['il_adi'] or '')
        ws.cell(row=row_idx, column=13, value=aday['ilce_adi'] or '')
        ws.cell(row=row_idx, column=14, value=aday['magaza_adi'] or '')
        ws.cell(row=row_idx, column=15, value=aday['aracli_durum'] or '')
        ws.cell(row=row_idx, column=16, value=aday['calisma_sekli'] or '')
        ws.cell(row=row_idx, column=17, value=aday['kaynak_adi'] or aday['kaynak_diger'] or '')
        ws.cell(row=row_idx, column=18, value=aday['basvuru_tarihi'])
        ws.cell(row=row_idx, column=19, value=aday['durum'])
    
    # Sütun genişliklerini ayarla
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[column].width = min(max_length + 2, 50)
    
    # Dosyayı belleğe kaydet
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'adaylar_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )
    
# ÇALIŞAN DÜZENLE ROUTE'U
# app.py'ye eklenecek (İşten çıkış route'larından sonra)

@app.route('/calisan/<int:calisan_id>/duzenle', methods=['GET', 'POST'])
@login_required
def calisanlar_duzenle(calisan_id):
    """Çalışan düzenle"""
    conn = get_db()
    
    if request.method == 'GET':
        # Çalışan bilgilerini getir
        calisan = conn.execute('''
            SELECT c.*, hk.proje_id
            FROM calisanlar c
            LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
            WHERE c.id = %s
        ''', (calisan_id,)).fetchone()
        
        if not calisan:
            flash('Çalışan bulunamadı!', 'error')
            return redirect(url_for('calisanlar'))
        
        # Dropdown'lar için veriler
        projeler = conn.execute('SELECT * FROM projeler ORDER BY proje_adi').fetchall()
        kadrolar = conn.execute('''
            SELECT hk.*, p.proje_adi, i.il_adi, ic.ilce_adi
            FROM hedef_kadrolar hk
            LEFT JOIN projeler p ON hk.proje_id = p.id
            LEFT JOIN iller i ON hk.il_id = i.id
            LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
            ORDER BY p.proje_adi, hk.pozisyon_adi
        ''').fetchall()
        calisma_sekilleri = conn.execute('SELECT * FROM calisma_sekilleri WHERE aktif = TRUE ORDER BY calisma_sekli').fetchall()
        
        conn.close()
        
        return render_template('calisan_duzenle.html', 
                             calisan=calisan,
                             projeler=projeler,
                             kadrolar=kadrolar,
                             calisma_sekilleri=calisma_sekilleri)
    
    else:  # POST
        # Form verilerini al
        ad_soyad = request.form['ad_soyad']
        telefon = request.form.get('telefon', '')
        email = request.form.get('email', '')
        tc_kimlik = request.form.get('tc_kimlik', '')
        dogum_tarihi = request.form.get('dogum_tarihi', None)
        adres = request.form.get('adres', '')
        ise_baslama_tarihi = request.form['ise_baslama_tarihi']
        kadro_id = request.form['kadro_id']
        aracli_durum = request.form.get('aracli_durum', 'Araçsız')
        calisma_sekli_id = request.form.get('calisma_sekli_id', None)
        aktif = TRUE if request.form.get('aktif') else 0
        
        try:
            cursor = conn.cursor()
            
            # Eski kadro bilgisi
            eski_calisan = conn.execute('SELECT kadro_id FROM calisanlar WHERE id = %s', 
                                       (calisan_id,)).fetchone()
            eski_kadro_id = eski_calisan['kadro_id']
            
            # Çalışanı güncelle
            cursor.execute('''
                UPDATE calisanlar 
                SET ad_soyad = %s,
                    telefon = %s,
                    email = %s,
                    tc_kimlik = %s,
                    dogum_tarihi = %s,
                    adres = %s,
                    ise_baslama_tarihi = %s,
                    kadro_id = %s,
                    aracli_durum = %s,
                    calisma_sekli_id = %s,
                    aktif = %s
                WHERE id = %s
            ''', (ad_soyad, telefon, email, tc_kimlik, dogum_tarihi, adres,
                  ise_baslama_tarihi, kadro_id, aracli_durum, calisma_sekli_id,
                  aktif, calisan_id))
            
            # Kadro değiştiyse doluluk sayılarını güncelle
            if eski_kadro_id != int(kadro_id):
                # Eski kadrodan çıkar
                cursor.execute('''
                    UPDATE hedef_kadrolar 
                    SET dolu_kisi_sayisi = dolu_kisi_sayisi - 1
                    WHERE id = %s
                ''', (eski_kadro_id,))
                
                # Yeni kadroya ekle
                cursor.execute('''
                    UPDATE hedef_kadrolar 
                    SET dolu_kisi_sayisi = dolu_kisi_sayisi + 1
                    WHERE id = %s
                ''', (kadro_id,))
                
                # Her iki kadronun durumunu güncelle
                cursor.execute('''
                    UPDATE hedef_kadrolar 
                    SET durum = CASE 
                        WHEN dolu_kisi_sayisi >= hedef_kisi_sayisi THEN 'Dolu'
                        ELSE 'Açık'
                    END
                    WHERE id IN (%s, %s)
                ''', (eski_kadro_id, kadro_id))
            
            conn.commit()
            
            # Log kaydet
            log_islem('GÜNCELLEME', 'calisanlar', calisan_id, 
                     f'{ad_soyad} bilgileri güncellendi')
            
            flash('Çalışan başarıyla güncellendi!', 'success')
            return redirect(url_for('calisan_detay', calisan_id=calisan_id))
            
        except Exception as e:
            conn.rollback()
            flash(f'Hata oluştu: {str(e)}', 'error')
            return redirect(url_for('calisanlar_duzenle', calisan_id=calisan_id))
        finally:
            conn.close()    
    
@app.route('/calisan/<int:calisan_id>/detay')
@login_required
def calisan_detay(calisan_id):
    """Çalışan detay sayfası"""
    conn = get_db()
    
    # Çalışan bilgileri
    calisan_raw = conn.execute('''
        SELECT c.*, 
               hk.pozisyon_adi, hk.magaza_adi, hk.aracli_durum, hk.calisma_sekli,
               m.mudurluk_adi,
               d.direktorluk_adi,
               i.il_adi,
               ic.ilce_adi,
               p.proje_adi
        FROM calisanlar c
        LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
        LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
        LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
        LEFT JOIN iller i ON hk.il_id = i.id
        LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
        LEFT JOIN projeler p ON hk.proje_id = p.id
        WHERE c.id = %s
    ''', (calisan_id,)).fetchone()
    
    if not calisan_raw:
        conn.close()
        flash('Çalışan bulunamadı!', 'danger')
        return redirect(url_for('calisanlar'))
    
    # Dict'e çevir
    calisan = dict(calisan_raw)
    
    # YAŞ HESAPLA
    if calisan.get('dogum_tarihi'):
        try:
            dogum = datetime.strptime(calisan['dogum_tarihi'], '%Y-%m-%d')
            bugun = datetime.now()
            
            yil = bugun.year - dogum.year
            ay = bugun.month - dogum.month
            
            if ay < 0:
                yil -= 1
                ay += 12
            
            if bugun.day < dogum.day:
                ay -= 1
                if ay < 0:
                    yil -= 1
                    ay += 12
            
            calisan['yas'] = f"{yil}.{ay}"
            calisan['yas_yil'] = yil
        except Exception as e:
            print(f"Yaş hesaplama hatası: {e}")
            calisan['yas'] = None
            calisan['yas_yil'] = None
    else:
        calisan['yas'] = None
        calisan['yas_yil'] = None
    
    # Dosyalar (aday_id üzerinden de ara - aday döneminden kalan dosyalar için)
    dosyalar = conn.execute('''
        SELECT d.*, u.username as yukleyen
        FROM dosyalar d
        LEFT JOIN users u ON d.yukleyen_user_id = u.id
        WHERE (d.ilgili_tablo = 'calisanlar' AND d.ilgili_id = %s)
           OR (d.ilgili_tablo = 'adaylar' AND d.ilgili_id = %s)
        ORDER BY d.yukleme_tarihi DESC
    ''', (calisan_id, calisan['aday_id'])).fetchall()
    
    conn.close()
    
    return render_template('calisan_detay.html', calisan=calisan, dosyalar=dosyalar)
    
@app.route('/calisan/<int:calisan_id>/dosya-yukle', methods=['POST'])
@login_required
def calisan_dosya_yukle(calisan_id):
    """Çalışana dosya yükle"""
    if 'dosya' not in request.files:
        flash('Dosya seçilmedi!', 'danger')
        return redirect(url_for('calisan_detay', calisan_id=calisan_id))
    
    file = request.files['dosya']
    dosya_tipi = request.form.get('dosya_tipi', 'diger')
    aciklama = request.form.get('aciklama', '')
    
    if file.filename == '':
        flash('Dosya seçilmedi!', 'danger')
        return redirect(url_for('calisan_detay', calisan_id=calisan_id))
    
    if not allowed_file(file.filename):
        flash('Geçersiz dosya formatı! İzin verilen: PDF, DOC, DOCX, JPG, PNG', 'danger')
        return redirect(url_for('calisan_detay', calisan_id=calisan_id))
    
    # Güvenli dosya adı oluştur
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    yeni_dosya_adi = f"{calisan_id}_{dosya_tipi}_{timestamp}_{filename}"
    
    # Klasör yolu
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'calisanlar')
    os.makedirs(upload_path, exist_ok=True)
    
    # Dosyayı kaydet
    dosya_yolu = os.path.join(upload_path, yeni_dosya_adi)
    file.save(dosya_yolu)
    
    # Dosya boyutu
    dosya_boyutu = os.path.getsize(dosya_yolu)
    
    # Veritabanına kaydet
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO dosyalar 
        (ilgili_tablo, ilgili_id, dosya_tipi, dosya_adi, dosya_yolu, dosya_boyutu, yukleyen_user_id, aciklama)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', ('calisanlar', calisan_id, dosya_tipi, filename, dosya_yolu, dosya_boyutu, session['user_id'], aciklama))
    conn.commit()
    conn.close()
    
    log_islem('DOSYA_YUKLEME', 'dosyalar', calisan_id, 
             f'{dosya_tipi} dosyası yüklendi: {filename}', session.get('username'))
    
    flash(f'Dosya başarıyla yüklendi! ({get_file_size_mb(dosya_boyutu)} MB)', 'success')
    return redirect(url_for('calisan_detay', calisan_id=calisan_id))    

@app.route('/loglar')
@login_required
def loglar():
    """Süreç logları"""
    conn = get_db()
    loglar = conn.execute('''
        SELECT * FROM surec_loglari 
        ORDER BY islem_tarihi DESC 
        LIMIT 100
    ''').fetchall()
    conn.close()
    return render_template('loglar.html', loglar=loglar)

@app.route('/api/stats')
@login_required
def api_stats():
    """Dashboard için istatistikler"""
    conn = get_db()
    
    stats = {
        'toplam_proje': conn.execute('SELECT COUNT(*) as cnt FROM projeler WHERE aktif = TRUE').fetchone()['cnt'],
        'toplam_kadro': conn.execute('SELECT COUNT(*) as cnt FROM hedef_kadrolar').fetchone()['cnt'],
        'toplam_aday': conn.execute('SELECT COUNT(*) as cnt FROM adaylar').fetchone()['cnt'],
        'toplam_calisan': conn.execute('SELECT COUNT(*) as cnt FROM calisanlar WHERE aktif = TRUE').fetchone()['cnt'],
        'hedef_toplam': conn.execute('SELECT SUM(hedef_kisi_sayisi) as total FROM hedef_kadrolar').fetchone()['total'] or 0,
        'dolu_toplam': conn.execute('SELECT SUM(dolu_kisi_sayisi) as total FROM hedef_kadrolar').fetchone()['total'] or 0
    }
    
    conn.close()
    return jsonify(stats)
@app.route('/users')
@admin_required
def users():
    """Kullanıcı listesi (Sadece Admin)"""
    conn = get_db()
    users = conn.execute('''
        SELECT id, username, email, full_name, role, aktif, 
               olusturma_tarihi, son_giris_tarihi
        FROM users 
        ORDER BY olusturma_tarihi DESC
    ''').fetchall()
    conn.close()
    return render_template('users.html', users=users)

@app.route('/user/ekle', methods=['GET', 'POST'])
@admin_required
def user_ekle():
    """Yeni kullanıcı ekle (Sadece Admin)"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        full_name = request.form['full_name']
        role = request.form['role']
        
        # Şifreyi hashle
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
            ''', (username, password_hash, email, full_name, role))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            log_islem('EKLEME', 'users', user_id, 
                     f'{username} kullanıcısı oluşturuldu (Rol: {role})', 
                     session.get('username', 'Sistem'))
            flash(f'Kullanıcı "{username}" başarıyla eklendi!', 'success')
            return redirect(url_for('users'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Bu kullanıcı adı zaten kullanılıyor!', 'danger')
    
    return render_template('user_form.html')

@app.route('/user/<int:user_id>/duzenle', methods=['GET', 'POST'])
@admin_required
def user_duzenle(user_id):
    """Kullanıcı düzenle (Sadece Admin)"""
    conn = get_db()
    
    if request.method == 'POST':
        email = request.form.get('email', '')
        full_name = request.form['full_name']
        role = request.form['role']
        aktif = TRUE if request.form.get('aktif') == 'on' else 0
        
        # Şifre değiştirilmek isteniyorsa
        new_password = request.form.get('new_password', '')
        if new_password:
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            conn.execute('''
                UPDATE users 
                SET email = %s, full_name = %s, role = %s, aktif = %s, password_hash = %s
                WHERE id = %s
            ''', (email, full_name, role, aktif, password_hash, user_id))
        else:
            conn.execute('''
                UPDATE users 
                SET email = %s, full_name = %s, role = %s, aktif = %s
                WHERE id = %s
            ''', (email, full_name, role, aktif, user_id))
        
        conn.commit()
        conn.close()
        
        log_islem('GÜNCELLEME', 'users', user_id, 
                 f'Kullanıcı bilgileri güncellendi', 
                 session.get('username', 'Sistem'))
        flash('Kullanıcı başarıyla güncellendi!', 'success')
        return redirect(url_for('users'))
    
    user = conn.execute('SELECT * FROM users WHERE id = %s', (user_id,)).fetchone()
    conn.close()
    
    if not user:
        flash('Kullanıcı bulunamadı!', 'danger')
        return redirect(url_for('users'))
    
    return render_template('user_edit.html', user=user)

@app.route('/user/<int:user_id>/sil', methods=['POST'])
@admin_required
def user_sil(user_id):
    """Kullanıcı sil (Sadece Admin)"""
    # Kendi hesabını silemez
    if user_id == session.get('user_id'):
        flash('Kendi hesabınızı silemezsiniz!', 'danger')
        return redirect(url_for('users'))
    
    conn = get_db()
    user = conn.execute('SELECT username FROM users WHERE id = %s', (user_id,)).fetchone()
    
    if user:
        conn.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        log_islem('SİLME', 'users', user_id, 
                 f'{user["username"]} kullanıcısı silindi', 
                 session.get('username', 'Sistem'))
        flash(f'Kullanıcı "{user["username"]}" başarıyla silindi!', 'success')
    else:
        flash('Kullanıcı bulunamadı!', 'danger')
    
    conn.close()
    return redirect(url_for('users'))

@app.route('/profil')
@login_required
def profil():
    """Kullanıcı profili"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('profil.html', user=user)

@app.route('/profil/sifre-degistir', methods=['POST'])
@login_required
def sifre_degistir():
    """Şifre değiştir"""
    eski_sifre = request.form['eski_sifre']
    yeni_sifre = request.form['yeni_sifre']
    yeni_sifre_tekrar = request.form['yeni_sifre_tekrar']
    
    if yeni_sifre != yeni_sifre_tekrar:
        flash('Yeni şifreler eşleşmiyor!', 'danger')
        return redirect(url_for('profil'))
    
    # Eski şifre kontrolü
    eski_sifre_hash = hashlib.sha256(eski_sifre.encode()).hexdigest()
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = %s AND password_hash = %s', 
                       (session['user_id'], eski_sifre_hash)).fetchone()
    
    if not user:
        conn.close()
        flash('Eski şifre hatalı!', 'danger')
        return redirect(url_for('profil'))
    
    # Yeni şifreyi kaydet
    yeni_sifre_hash = hashlib.sha256(yeni_sifre.encode()).hexdigest()
    conn.execute('UPDATE users SET password_hash = %s WHERE id = %s', 
                (yeni_sifre_hash, session['user_id']))
    conn.commit()
    conn.close()
    
    log_islem('GÜNCELLEME', 'users', session['user_id'], 
             'Şifre değiştirildi', session.get('username', 'Sistem'))
    flash('Şifreniz başarıyla değiştirildi!', 'success')
    return redirect(url_for('profil')) 

@app.route('/yetkisiz')
@login_required
def yetkisiz():
    """Yetki yok sayfası"""
    return render_template('yetkisiz.html')
    
@app.route('/aday/<int:aday_id>/dosya-yukle', methods=['POST'])
@login_required
def aday_dosya_yukle(aday_id):
    """Adaya dosya yükle"""
    if 'dosya' not in request.files:
        flash('Dosya seçilmedi!', 'danger')
        return redirect(url_for('aday_detay', aday_id=aday_id))
    
    file = request.files['dosya']
    dosya_tipi = request.form.get('dosya_tipi', 'diger')
    aciklama = request.form.get('aciklama', '')
    
    if file.filename == '':
        flash('Dosya seçilmedi!', 'danger')
        return redirect(url_for('aday_detay', aday_id=aday_id))
    
    if not allowed_file(file.filename):
        flash('Geçersiz dosya formatı! İzin verilen: PDF, DOC, DOCX, JPG, PNG', 'danger')
        return redirect(url_for('aday_detay', aday_id=aday_id))
    
    # Güvenli dosya adı oluştur
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    yeni_dosya_adi = f"{aday_id}_{dosya_tipi}_{timestamp}_{filename}"
    
    # Klasör yolu
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'adaylar')
    os.makedirs(upload_path, exist_ok=True)
    
    # Dosyayı kaydet
    dosya_yolu = os.path.join(upload_path, yeni_dosya_adi)
    file.save(dosya_yolu)
    
    # Dosya boyutu
    dosya_boyutu = os.path.getsize(dosya_yolu)
    
    # Veritabanına kaydet
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO dosyalar 
        (ilgili_tablo, ilgili_id, dosya_tipi, dosya_adi, dosya_yolu, dosya_boyutu, yukleyen_user_id, aciklama)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', ('adaylar', aday_id, dosya_tipi, filename, dosya_yolu, dosya_boyutu, session['user_id'], aciklama))
    conn.commit()
    conn.close()
    
    log_islem('DOSYA_YUKLEME', 'dosyalar', aday_id, 
             f'{dosya_tipi} dosyası yüklendi: {filename}', session.get('username'))
    
    flash(f'Dosya başarıyla yüklendi! ({get_file_size_mb(dosya_boyutu)} MB)', 'success')
    return redirect(url_for('aday_detay', aday_id=aday_id))

@app.route('/dosya/<int:dosya_id>/indir')
@login_required
def dosya_indir(dosya_id):
    """Dosya indir"""
    conn = get_db()
    dosya = conn.execute('SELECT * FROM dosyalar WHERE id = %s', (dosya_id,)).fetchone()
    conn.close()
    
    if not dosya:
        flash('Dosya bulunamadı!', 'danger')
        return redirect(url_for('index'))
    
    try:
        from flask import send_file
        return send_file(dosya['dosya_yolu'], 
                        as_attachment=True, 
                        download_name=dosya['dosya_adi'])
    except Exception as e:
        flash(f'Dosya indirilemedi: {str(e)}', 'danger')
        return redirect(request.referrer or url_for('index'))

@app.route('/dosya/<int:dosya_id>/sil', methods=['POST'])
@login_required
def dosya_sil(dosya_id):
    """Dosya sil"""
    conn = get_db()
    dosya = conn.execute('SELECT * FROM dosyalar WHERE id = %s', (dosya_id,)).fetchone()
    
    if not dosya:
        conn.close()
        flash('Dosya bulunamadı!', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # Yetki kontrolü (sadece admin veya yükleyen silebilir)
    if session.get('role') != 'admin' and dosya['yukleyen_user_id'] != session['user_id']:
        conn.close()
        flash('Bu dosyayı silme yetkiniz yok!', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # Fiziksel dosyayı sil
    try:
        if os.path.exists(dosya['dosya_yolu']):
            os.remove(dosya['dosya_yolu'])
    except Exception as e:
        print(f"Dosya silinemedi: {e}")
    
    # Veritabanından sil
    conn.execute('DELETE FROM dosyalar WHERE id = %s', (dosya_id,))
    conn.commit()
    conn.close()
    
    log_islem('DOSYA_SILME', 'dosyalar', dosya_id, 
             f'Dosya silindi: {dosya["dosya_adi"]}', session.get('username'))
    
    flash('Dosya başarıyla silindi!', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/aday/<int:aday_id>/detay')
@login_required
def aday_detay(aday_id):
    """Aday detay sayfası"""
    conn = get_db()
    
    # Aday bilgileri
    aday = conn.execute('''
        SELECT a.*, 
               hk.pozisyon_adi, hk.magaza_adi,
               i.il_adi,
               ic.ilce_adi,
               p.proje_adi
        FROM adaylar a
        LEFT JOIN hedef_kadrolar hk ON a.kadro_id = hk.id
        LEFT JOIN iller i ON hk.il_id = i.id
        LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
        LEFT JOIN projeler p ON hk.proje_id = p.id
        WHERE a.id = %s
    ''', (aday_id,)).fetchone()
    
    if not aday:
        conn.close()
        flash('Aday bulunamadı!', 'danger')
        return redirect(url_for('adaylar'))
    
    # Dosyalar
    dosyalar = conn.execute('''
        SELECT d.*, u.username as yukleyen
        FROM dosyalar d
        LEFT JOIN users u ON d.yukleyen_user_id = u.id
        WHERE d.ilgili_tablo = 'adaylar' AND d.ilgili_id = %s
        ORDER BY d.yukleme_tarihi DESC
    ''', (aday_id,)).fetchall()
    
    conn.close()
    
    return render_template('aday_detay.html', aday=aday, dosyalar=dosyalar)


@app.route('/email-ayarlari')
@admin_required
def email_ayarlari():
    """Email ayarları sayfası (Sadece Admin)"""
    conn = get_db()
    
    # Email ayarları
    ayarlar = conn.execute('''
        SELECT * FROM email_ayarlari 
        ORDER BY 
            CASE ayar_adi
                WHEN 'smtp_sunucu' THEN 1
                WHEN 'smtp_port' THEN 2
                WHEN 'smtp_kullanici' THEN 3
                WHEN 'smtp_sifre' THEN 4
                WHEN 'gonderici_adi' THEN 5
                ELSE 6
            END
    ''').fetchall()
    
    # Email şablonları
    sablonlar = conn.execute('''
        SELECT * FROM email_sablonlari 
        ORDER BY olusturma_tarihi DESC
    ''').fetchall()
    
    # Email logları (son 50)
    loglar = conn.execute('''
        SELECT * FROM email_loglari 
        ORDER BY gonderim_tarihi DESC 
        LIMIT 50
    ''').fetchall()
    
    # İstatistikler
    stats = {
        'toplam_gonderim': conn.execute('SELECT COUNT(*) as cnt FROM email_loglari').fetchone()['cnt'],
        'basarili': conn.execute("SELECT COUNT(*) as cnt FROM email_loglari WHERE gonderim_durumu = 'gonderildi'").fetchone()['cnt'],
        'basarisiz': conn.execute("SELECT COUNT(*) as cnt FROM email_loglari WHERE gonderim_durumu = 'hata'").fetchone()['cnt'],
    }
    
    conn.close()
    
    return render_template('email_ayarlari.html', 
                         ayarlar=ayarlar, 
                         sablonlar=sablonlar, 
                         loglar=loglar,
                         stats=stats)

@app.route('/email-ayarlari/guncelle', methods=['POST'])
@admin_required
def email_ayarlari_guncelle():
    """Email ayarlarını güncelle"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Form'dan gelen tüm ayarları güncelle
    for key, value in request.form.items():
        if key.startswith('ayar_'):
            ayar_adi = key.replace('ayar_', '')
            cursor.execute('''
                UPDATE email_ayarlari 
                SET ayar_degeri = %s 
                WHERE ayar_adi = %s
            ''', (value, ayar_adi))
    
    conn.commit()
    conn.close()
    
    log_islem('GÜNCELLEME', 'email_ayarlari', 0, 
             'Email ayarları güncellendi', session.get('username'))
    
    flash('Email ayarları başarıyla güncellendi!', 'success')
    return redirect(url_for('email_ayarlari'))

@app.route('/email-sablonu/<int:sablon_id>/duzenle', methods=['GET', 'POST'])
@admin_required
def email_sablon_duzenle(sablon_id):
    """Email şablonunu düzenle"""
    conn = get_db()
    
    if request.method == 'POST':
        sablon_konusu = request.form['sablon_konusu']
        sablon_icerik = request.form['sablon_icerik']
        aktif = TRUE if request.form.get('aktif') == 'on' else 0
        
        conn.execute('''
            UPDATE email_sablonlari 
            SET sablon_konusu = %s, sablon_icerik = %s, aktif = %s
            WHERE id = %s
        ''', (sablon_konusu, sablon_icerik, aktif, sablon_id))
        conn.commit()
        conn.close()
        
        log_islem('GÜNCELLEME', 'email_sablonlari', sablon_id, 
                 'Email şablonu güncellendi', session.get('username'))
        
        flash('Email şablonu başarıyla güncellendi!', 'success')
        return redirect(url_for('email_ayarlari'))
    
    sablon = conn.execute('SELECT * FROM email_sablonlari WHERE id = %s', (sablon_id,)).fetchone()
    conn.close()
    
    if not sablon:
        flash('Şablon bulunamadı!', 'danger')
        return redirect(url_for('email_ayarlari'))
    
    return render_template('email_sablon_duzenle.html', sablon=sablon)

@app.route('/email-test-gonder', methods=['POST'])
@admin_required
def email_test_gonder():
    """Test email gönder"""
    test_email = request.form.get('test_email')
    
    if not test_email:
        flash('Test email adresi girilmedi!', 'danger')
        return redirect(url_for('email_ayarlari'))
    
    try:
        from email_service import email_gonder
        
        test_icerik = """
        <h2>Test Email</h2>
        <p>Bu bir test emailidir. Email ayarlarınız doğru çalışıyor!</p>
        <p><strong>Gönderim Zamanı:</strong> {}</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            Team Guerilla - İK Yönetim Sistemi<br>
            Test Email
        </p>
        """.format(datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
        
        basarili, mesaj = email_gonder(
            test_email,
            'Test Email - İK Portal',
            test_icerik,
            'test_email'
        )
        
        if basarili:
            flash(f'Test email başarıyla gönderildi: {test_email}', 'success')
        else:
            flash(f'Test email gönderilemedi: {mesaj}', 'danger')
            
    except Exception as e:
        flash(f'Hata: {str(e)}', 'danger')
    
    return redirect(url_for('email_ayarlari'))

@app.route('/email-loglari/temizle', methods=['POST'])
@admin_required
def email_loglari_temizle():
    """Email loglarını temizle"""
    conn = get_db()
    
    # 30 günden eski logları sil
    conn.execute("""
        DELETE FROM email_loglari 
        WHERE gonderim_tarihi < datetime('now', '-30 days')
    """)
    
    silinen = conn.total_changes
    conn.commit()
    conn.close()
    
    log_islem('SİLME', 'email_loglari', 0, 
             f'{silinen} eski email logu temizlendi', session.get('username'))
    
    flash(f'{silinen} eski email logu temizlendi!', 'success')
    return redirect(url_for('email_ayarlari'))    
    
# ============================================
# TANIMLAR YÖNETİMİ (Müdürlük, Direktörlük)
# ============================================

# tanimlar() route'unu app.py'de güncelle:

@app.route('/tanimlar')
@admin_required
def tanimlar():
    """Sistem tanımları - Müdürlük, Direktörlük, Çalışma Şekilleri, Kaynaklar"""
    conn = get_db()
    
    # İstatistikler
    stats = {
        'mudurluk_sayisi': conn.execute('SELECT COUNT(*) as cnt FROM mudurluker WHERE aktif = TRUE').fetchone()['cnt'],
        'direktorluk_sayisi': conn.execute('SELECT COUNT(*) as cnt FROM direktorlukler WHERE aktif = TRUE').fetchone()['cnt'],
        'calisma_sekli_sayisi': conn.execute('SELECT COUNT(*) as cnt FROM calisma_sekilleri WHERE aktif = TRUE').fetchone()['cnt'],
        'kaynak_sayisi': conn.execute('SELECT COUNT(*) as cnt FROM kaynaklar WHERE aktif = TRUE').fetchone()['cnt']
    }
    
    # Müdürlükler
    mudurluker = conn.execute('''
        SELECT * FROM mudurluker 
        ORDER BY mudurluk_adi
    ''').fetchall()
    
    # Direktörlükler
    direktorlukler = conn.execute('''
        SELECT * FROM direktorlukler 
        ORDER BY direktorluk_adi
    ''').fetchall()
    
    # Çalışma Şekilleri - YENİ
    calisma_sekilleri = conn.execute('''
        SELECT cs.id,
               cs.calisma_sekli,
               cs.aktif,
               COUNT(hk.id) as kadro_sayisi
        FROM calisma_sekilleri cs
        LEFT JOIN hedef_kadrolar hk ON cs.calisma_sekli = hk.calisma_sekli
        GROUP BY cs.id, cs.calisma_sekli, cs.aktif
        ORDER BY cs.calisma_sekli
    ''').fetchall()
    
    # Kaynaklar - YENİ
    kaynaklar = conn.execute('''
        SELECT k.id,
               k.kaynak_adi,
               k.aciklama,
               k.aktif,
               COUNT(a.id) as aday_sayisi
        FROM kaynaklar k
        LEFT JOIN adaylar a ON k.id = a.kaynak_id
        GROUP BY k.id, k.kaynak_adi, k.aciklama, k.aktif
        ORDER BY k.kaynak_adi
    ''').fetchall()
    
    conn.close()
    
    return render_template('tanimlar.html', 
                         stats=stats,
                         mudurluker=mudurluker, 
                         direktorlukler=direktorlukler,
                         calisma_sekilleri=calisma_sekilleri,
                         kaynaklar=kaynaklar)

@app.route('/mudurluk/ekle', methods=['POST'])
@admin_required
def mudurluk_ekle():
    """Yeni müdürlük ekle"""
    mudurluk_adi = request.form['mudurluk_adi']
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO mudurluker (mudurluk_adi) VALUES (%s)', (mudurluk_adi,))
        mudurluk_id = cursor.lastrowid
        conn.commit()
        log_islem('EKLEME', 'mudurluker', mudurluk_id, f'{mudurluk_adi} müdürlüğü eklendi')
        flash(f'Müdürlük "{mudurluk_adi}" başarıyla eklendi!', 'success')
    except sqlite3.IntegrityError:
        flash('Bu müdürlük zaten mevcut!', 'danger')
    
    conn.close()
    return redirect(url_for('tanimlar'))

@app.route('/direktorluk/ekle', methods=['POST'])
@admin_required
def direktorluk_ekle():
    """Yeni direktörlük ekle"""
    direktorluk_adi = request.form['direktorluk_adi']
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO direktorlukler (direktorluk_adi) VALUES (%s)', (direktorluk_adi,))
        direktorluk_id = cursor.lastrowid
        conn.commit()
        log_islem('EKLEME', 'direktorlukler', direktorluk_id, f'{direktorluk_adi} direktörlüğü eklendi')
        flash(f'Direktörlük "{direktorluk_adi}" başarıyla eklendi!', 'success')
    except sqlite3.IntegrityError:
        flash('Bu direktörlük zaten mevcut!', 'danger')
    
    conn.close()
    return redirect(url_for('tanimlar'))

@app.route('/mudurluk/<int:mudurluk_id>/sil', methods=['POST'])
@admin_required
def mudurluk_sil(mudurluk_id):
    """Müdürlük sil"""
    conn = get_db()
    mudurluk = conn.execute('SELECT mudurluk_adi FROM mudurluker WHERE id = %s', (mudurluk_id,)).fetchone()
    
    if mudurluk:
        conn.execute('DELETE FROM mudurluker WHERE id = %s', (mudurluk_id,))
        conn.commit()
        log_islem('SİLME', 'mudurluker', mudurluk_id, f'{mudurluk["mudurluk_adi"]} müdürlüğü silindi')
        flash('Müdürlük başarıyla silindi!', 'success')
    
    conn.close()
    return redirect(url_for('tanimlar'))

@app.route('/direktorluk/<int:direktorluk_id>/sil', methods=['POST'])
@admin_required
def direktorluk_sil(direktorluk_id):
    """Direktörlük sil"""
    conn = get_db()
    direktorluk = conn.execute('SELECT direktorluk_adi FROM direktorlukler WHERE id = %s', (direktorluk_id,)).fetchone()
    
    if direktorluk:
        conn.execute('DELETE FROM direktorlukler WHERE id = %s', (direktorluk_id,))
        conn.commit()
        log_islem('SİLME', 'direktorlukler', direktorluk_id, f'{direktorluk["direktorluk_adi"]} direktörlüğü silindi')
        flash('Direktörlük başarıyla silindi!', 'success')
    
    conn.close()
    return redirect(url_for('tanimlar'))

@app.route('/api/ilceler/<int:il_id>')
@login_required
def api_ilceler(il_id):
    """İle göre ilçeleri getir (AJAX için)"""
    conn = get_db()
    ilceler = conn.execute('''
        SELECT id, ilce_adi 
        FROM ilceler 
        WHERE il_id = %s AND aktif = TRUE 
        ORDER BY ilce_adi
    ''', (il_id,)).fetchall()
    conn.close()
    
    return jsonify([{'id': ilce['id'], 'ilce_adi': ilce['ilce_adi']} for ilce in ilceler]) 

# ============================================
# MÜŞTERİ YÖNETİMİ
# ============================================

@app.route('/musteriler')
@admin_required
def musteriler():
    """Müşteri listesi (Sadece Admin)"""
    conn = get_db()
    
    stats = {
        'toplam_musteri': conn.execute('SELECT COUNT(*) as cnt FROM musteriler WHERE aktif = TRUE').fetchone()['cnt'],
        'toplam_proje': conn.execute('SELECT COUNT(*) as cnt FROM projeler WHERE musteri_id IS NOT NULL').fetchone()['cnt']
    }
    
    musteriler = conn.execute('''
        SELECT m.id,
               m.musteri_adi,
               m.sektor,
               m.yetkili_kisi,
               m.telefon,
               m.email,
               m.adres,
               m.logo_yolu,
               m.aktif,
               m.olusturma_tarihi,
               COUNT(DISTINCT p.id) as proje_sayisi
        FROM musteriler m
        LEFT JOIN projeler p ON m.id = p.musteri_id
        GROUP BY m.id, m.musteri_adi, m.sektor, m.yetkili_kisi, m.telefon, 
                 m.email, m.adres, m.logo_yolu, m.aktif, m.olusturma_tarihi
        ORDER BY m.musteri_adi
    ''').fetchall()
    
    conn.close()
    return render_template('musteriler.html', musteriler=musteriler, stats=stats)

@app.route('/musteri/ekle', methods=['GET', 'POST'])
@admin_required
def musteri_ekle():
    """Yeni müşteri ekle"""
    if request.method == 'POST':
        musteri_adi = request.form['musteri_adi']
        sektor = request.form.get('sektor', '')
        yetkili_kisi = request.form.get('yetkili_kisi', '')
        telefon = request.form.get('telefon', '')
        email = request.form.get('email', '')
        adres = request.form.get('adres', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO musteriler (musteri_adi, sektor, yetkili_kisi, telefon, email, adres)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (musteri_adi, sektor, yetkili_kisi, telefon, email, adres))
            musteri_id = cursor.lastrowid
            
            # Logo yükleme
            if 'logo' in request.files:
                file = request.files['logo']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    yeni_dosya_adi = f"musteri_{musteri_id}_{timestamp}_{filename}"
                    
                    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'musteriler')
                    os.makedirs(upload_path, exist_ok=True)
                    
                    logo_yolu = os.path.join(upload_path, yeni_dosya_adi)
                    file.save(logo_yolu)
                    
                    cursor.execute('UPDATE musteriler SET logo_yolu = %s WHERE id = %s', 
                                 (logo_yolu, musteri_id))
            
            conn.commit()
            log_islem('EKLEME', 'musteriler', musteri_id, f'{musteri_adi} müşterisi eklendi')
            flash(f'Müşteri "{musteri_adi}" başarıyla eklendi!', 'success')
            conn.close()
            return redirect(url_for('musteriler'))
            
        except sqlite3.IntegrityError:
            conn.close()
            flash('Bu müşteri adı zaten kullanılıyor!', 'danger')
    
    return render_template('musteri_form.html')

@app.route('/musteri/<int:musteri_id>/duzenle', methods=['GET', 'POST'])
@admin_required
def musteri_duzenle(musteri_id):
    """Müşteri düzenle"""
    conn = get_db()
    
    if request.method == 'POST':
        musteri_adi = request.form['musteri_adi']
        sektor = request.form.get('sektor', '')
        yetkili_kisi = request.form.get('yetkili_kisi', '')
        telefon = request.form.get('telefon', '')
        email = request.form.get('email', '')
        adres = request.form.get('adres', '')
        aktif = TRUE if request.form.get('aktif') == 'on' else 0
        
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE musteriler 
            SET musteri_adi = %s, sektor = %s, yetkili_kisi = %s, 
                telefon = %s, email = %s, adres = %s, aktif = %s
            WHERE id = %s
        ''', (musteri_adi, sektor, yetkili_kisi, telefon, email, adres, aktif, musteri_id))
        
        # Logo güncelleme
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                yeni_dosya_adi = f"musteri_{musteri_id}_{timestamp}_{filename}"
                
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'musteriler')
                os.makedirs(upload_path, exist_ok=True)
                
                logo_yolu = os.path.join(upload_path, yeni_dosya_adi)
                file.save(logo_yolu)
                
                cursor.execute('UPDATE musteriler SET logo_yolu = %s WHERE id = %s', 
                             (logo_yolu, musteri_id))
        
        conn.commit()
        log_islem('GÜNCELLEME', 'musteriler', musteri_id, f'{musteri_adi} müşterisi güncellendi')
        flash('Müşteri başarıyla güncellendi!', 'success')
        conn.close()
        return redirect(url_for('musteriler'))
    
    musteri = conn.execute('SELECT * FROM musteriler WHERE id = %s', (musteri_id,)).fetchone()
    conn.close()
    
    if not musteri:
        flash('Müşteri bulunamadı!', 'danger')
        return redirect(url_for('musteriler'))
    
    return render_template('musteri_edit.html', musteri=musteri)

@app.route('/musteri/<int:musteri_id>/sil', methods=['POST'])
@admin_required
def musteri_sil(musteri_id):
    """Müşteri sil"""
    conn = get_db()
    musteri = conn.execute('SELECT musteri_adi FROM musteriler WHERE id = %s', (musteri_id,)).fetchone()
    
    if musteri:
        conn.execute('DELETE FROM musteriler WHERE id = %s', (musteri_id,))
        conn.commit()
        log_islem('SİLME', 'musteriler', musteri_id, f'{musteri["musteri_adi"]} müşterisi silindi')
        flash('Müşteri başarıyla silindi!', 'success')
    
    conn.close()
    return redirect(url_for('musteriler'))

@app.route('/musteri/logo/<int:musteri_id>')
def musteri_logo(musteri_id):
    """Müşteri logosunu göster"""
    conn = get_db()
    musteri = conn.execute('SELECT logo_yolu FROM musteriler WHERE id = %s', (musteri_id,)).fetchone()
    conn.close()
    
    if musteri and musteri['logo_yolu'] and os.path.exists(musteri['logo_yolu']):
        from flask import send_file
        return send_file(musteri['logo_yolu'])
    else:
        # Varsayılan logo
        from flask import send_file
        default_logo_path = os.path.join('static', 'images', 'default-company.png')
        if os.path.exists(default_logo_path):
            return send_file(default_logo_path)
        else:
            return '', 404    
            
@app.route('/adaylar/import')
@manager_required
def adaylar_import():
    """Adaylar toplu yükleme sayfası"""
    return render_template('adaylar_import.html')

@app.route('/adaylar/import/sablon-indir')
@manager_required
def adaylar_import_sablon():
    """Adaylar import şablonu indir"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Adaylar"
    
    # Başlık satırı
    headers = [
        'Ad Soyad*', 'Telefon', 'Email', 'TC Kimlik', 
        'Proje Adı*', 'Pozisyon Adı*', 'Müdürlük', 'Direktörlük',
        'İl*', 'İlçe', 'Mağaza Adı', 'Araç Durumu*', 
        'Başvuru Tarihi', 'Notlar'
    ]
    
    # Stil tanımlamaları
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Başlıkları ekle
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border
    
    # Açıklama satırı (2. satır)
    aciklamalar = [
        'Zorunlu', 'Opsiyonel', 'Opsiyonel', 'Opsiyonel',
        'Sistemde kayıtlı proje adı', 'Kadro pozisyon adı', 'Opsiyonel', 'Opsiyonel',
        'Sistemde kayıtlı il adı', 'Opsiyonel', 'Opsiyonel', 'Araçlı veya Araçsız',
        'YYYY-MM-DD formatında', 'Opsiyonel notlar'
    ]
    
    for col, aciklama in enumerate(aciklamalar, 1):
        cell = ws.cell(row=2, column=col, value=aciklama)
        cell.font = Font(italic=True, size=9, color="666666")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    # Örnek veri satırları (3-5. satırlar)
    ornekler = [
        ['Ahmet Yılmaz', '05551234567', 'ahmet@example.com', '12345678901', 
         'Migros Projesi', 'Satış Danışmanı', 'Perakende Müdürlüğü', 'İstanbul Direktörlüğü',
         'İstanbul', 'Kadıköy', 'Migros Acıbadem', 'Araçsız', 
         '2025-01-15', 'İyi bir aday'],
        ['Ayşe Demir', '05559876543', 'ayse@example.com', '98765432109',
         'Migros Projesi', 'Reyon Görevlisi', '', '',
         'Ankara', 'Çankaya', '', 'Araçlı',
         '2025-01-16', ''],
        ['Mehmet Kaya', '', '', '',
         'CarrefourSA', 'Kasa Görevlisi', '', '',
         'İzmir', 'Konak', 'CarrefourSA Alsancak', 'Araçsız',
         '', 'Acil değerlendirilmeli']
    ]
    
    for row_idx, ornek in enumerate(ornekler, 3):
        for col_idx, deger in enumerate(ornek, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=deger)
            cell.alignment = Alignment(vertical="center")
            cell.border = border
    
    # Sütun genişliklerini ayarla
    column_widths = [20, 15, 25, 15, 20, 20, 20, 25, 15, 15, 20, 15, 15, 30]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = width
    
    # Satır yüksekliklerini ayarla
    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 25
    
    # Dosyayı belleğe kaydet
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'adaylar_import_sablonu_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@app.route('/adaylar/import/yukle', methods=['POST'])
@manager_required
def adaylar_import_yukle():
    """Adaylar Excel dosyasını yükle ve işle"""
    if 'excel_file' not in request.files:
        return jsonify({'success': False, 'message': 'Dosya seçilmedi!'}), 400
    
    file = request.files['excel_file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Dosya seçilmedi!'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'success': False, 'message': 'Geçersiz dosya formatı! Sadece Excel dosyaları (.xlsx, .xls) kabul edilir.'}), 400
    
    try:
        # Excel dosyasını oku
        df = pd.read_excel(file, sheet_name=0)
        
        # Başlık satırından sonraki açıklama satırını atla (eğer varsa)
        if len(df) > 0 and 'Zorunlu' in str(df.iloc[0].values):
            df = df.iloc[1:].reset_index(drop=True)
        
        # Boş satırları temizle
        df = df.dropna(how='all')
        
        conn = get_db()
        cursor = conn.cursor()
        
        basarili_sayisi = 0
        hatalar = []
        
        for index, row in df.iterrows():
            satir_no = index + 3  # Excel'de başlık + açıklama + 1-indexed
            
            try:
                # Zorunlu alanları kontrol et
                ad_soyad = str(row.get('Ad Soyad*', '')).strip()
                proje_adi = str(row.get('Proje Adı*', '')).strip()
                pozisyon_adi = str(row.get('Pozisyon Adı*', '')).strip()
                il_adi = str(row.get('İl*', '')).strip()
                aracli_durum = str(row.get('Araç Durumu*', '')).strip()
                
                if not ad_soyad or ad_soyad == 'nan':
                    hatalar.append(f"Satır {satir_no}: Ad Soyad zorunludur")
                    continue
                
                if not proje_adi or proje_adi == 'nan':
                    hatalar.append(f"Satır {satir_no}: Proje Adı zorunludur")
                    continue
                
                if not pozisyon_adi or pozisyon_adi == 'nan':
                    hatalar.append(f"Satır {satir_no}: Pozisyon Adı zorunludur")
                    continue
                
                if not il_adi or il_adi == 'nan':
                    hatalar.append(f"Satır {satir_no}: İl zorunludur")
                    continue
                
                if not aracli_durum or aracli_durum == 'nan':
                    hatalar.append(f"Satır {satir_no}: Araç Durumu zorunludur")
                    continue
                
                # Araç durumu kontrolü
                if aracli_durum not in ['Araçlı', 'Araçsız']:
                    hatalar.append(f"Satır {satir_no}: Araç Durumu 'Araçlı' veya 'Araçsız' olmalıdır")
                    continue
                
                # Proje kontrolü
                proje = cursor.execute('SELECT id FROM projeler WHERE proje_adi = %s AND aktif = TRUE', 
                                      (proje_adi,)).fetchone()
                if not proje:
                    hatalar.append(f"Satır {satir_no}: '{proje_adi}' projesi bulunamadı")
                    continue
                proje_id = proje['id']
                
                # İl kontrolü
                il = cursor.execute('SELECT id FROM iller WHERE il_adi = %s AND aktif = TRUE', 
                                   (il_adi,)).fetchone()
                if not il:
                    hatalar.append(f"Satır {satir_no}: '{il_adi}' ili bulunamadı")
                    continue
                il_id = il['id']
                
                # İlçe kontrolü (opsiyonel)
                ilce_adi = str(row.get('İlçe', '')).strip()
                ilce_id = None
                if ilce_adi and ilce_adi != 'nan':
                    ilce = cursor.execute('SELECT id FROM ilceler WHERE ilce_adi = %s AND il_id = %s AND aktif = TRUE',
                                        (ilce_adi, il_id)).fetchone()
                    if ilce:
                        ilce_id = ilce['id']
                
                # Müdürlük kontrolü (opsiyonel)
                mudurluk_adi = str(row.get('Müdürlük', '')).strip()
                mudurluk_id = None
                if mudurluk_adi and mudurluk_adi != 'nan':
                    mudurluk = cursor.execute('SELECT id FROM mudurluker WHERE mudurluk_adi = %s AND aktif = TRUE',
                                             (mudurluk_adi,)).fetchone()
                    if mudurluk:
                        mudurluk_id = mudurluk['id']
                
                # Direktörlük kontrolü (opsiyonel)
                direktorluk_adi = str(row.get('Direktörlük', '')).strip()
                direktorluk_id = None
                if direktorluk_adi and direktorluk_adi != 'nan':
                    direktorluk = cursor.execute('SELECT id FROM direktorlukler WHERE direktorluk_adi = %s AND aktif = TRUE',
                                                (direktorluk_adi,)).fetchone()
                    if direktorluk:
                        direktorluk_id = direktorluk['id']
                
                # Kadro ara veya oluştur
                magaza_adi = str(row.get('Mağaza Adı', '')).strip()
                if magaza_adi == 'nan':
                    magaza_adi = ''
                
                kadro = cursor.execute('''
                    SELECT id FROM hedef_kadrolar 
                    WHERE proje_id = %s AND pozisyon_adi = %s 
                    AND il_id = %s AND COALESCE(ilce_id, 0) = COALESCE(%s, 0)
                    AND COALESCE(magaza_adi, '') = %s
                    AND aracli_durum = %s
                ''', (proje_id, pozisyon_adi, il_id, ilce_id, magaza_adi, aracli_durum)).fetchone()
                
                if not kadro:
                    # Kadro yoksa oluştur
                    cursor.execute('''
                        INSERT INTO hedef_kadrolar 
                        (proje_id, pozisyon_adi, mudurluk_id, direktorluk_id, il_id, ilce_id, 
                         magaza_adi, aracli_durum, hedef_kisi_sayisi)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
                    ''', (proje_id, pozisyon_adi, mudurluk_id, direktorluk_id, il_id, ilce_id, 
                          magaza_adi, aracli_durum))
                    kadro_id = cursor.lastrowid
                else:
                    kadro_id = kadro['id']
                
                # Opsiyonel alanlar
                telefon = str(row.get('Telefon', '')).strip()
                if telefon == 'nan':
                    telefon = ''
                
                email = str(row.get('Email', '')).strip()
                if email == 'nan':
                    email = ''
                
                tc_kimlik = str(row.get('TC Kimlik', '')).strip()
                if tc_kimlik == 'nan':
                    tc_kimlik = ''
                
                notlar = str(row.get('Notlar', '')).strip()
                if notlar == 'nan':
                    notlar = ''
                
                # Başvuru tarihi
                basvuru_tarihi = None
                basvuru_tarihi_raw = row.get('Başvuru Tarihi', '')
                if pd.notna(basvuru_tarihi_raw):
                    try:
                        if isinstance(basvuru_tarihi_raw, str):
                            basvuru_tarihi = datetime.strptime(basvuru_tarihi_raw, '%Y-%m-%d').strftime('%Y-%m-%d')
                        else:
                            basvuru_tarihi = basvuru_tarihi_raw.strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Adayı ekle
                cursor.execute('''
                    INSERT INTO adaylar (kadro_id, ad_soyad, telefon, email, tc_kimlik, basvuru_tarihi, notlar)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (kadro_id, ad_soyad, telefon or None, email or None, tc_kimlik or None, 
                      basvuru_tarihi, notlar or None))
                
                basarili_sayisi += 1
                
            except Exception as e:
                hatalar.append(f"Satır {satir_no}: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        # Log kaydı
        log_islem('TOPLU_EKLEME', 'adaylar', 0, 
                 f'{basarili_sayisi} aday Excel ile yüklendi', 
                 session.get('username'))
        
        # Sonuç mesajı
        if basarili_sayisi > 0 and len(hatalar) == 0:
            return jsonify({
                'success': True,
                'message': f'âœ… {basarili_sayisi} aday başarıyla eklendi!',
                'basarili_sayisi': basarili_sayisi,
                'hata_sayisi': 0
            })
        elif basarili_sayisi > 0 and len(hatalar) > 0:
            return jsonify({
                'success': True,
                'message': f'âš ï¸ {basarili_sayisi} aday eklendi, {len(hatalar)} satırda hata oluştu',
                'basarili_sayisi': basarili_sayisi,
                'hata_sayisi': len(hatalar),
                'hatalar': hatalar[:10]  # İlk 10 hatayı göster
            })
        else:
            return jsonify({
                'success': False,
                'message': f'âŒ Hiçbir aday eklenemedi. {len(hatalar)} hata bulundu.',
                'basarili_sayisi': 0,
                'hata_sayisi': len(hatalar),
                'hatalar': hatalar[:10]
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Dosya işlenirken hata oluştu: {str(e)}'
        }), 500

# ============================================
# ÇALIŞANLAR IMPORT
# ============================================

@app.route('/calisanlar/import')
@manager_required
def calisanlar_import():
    """Çalışanlar toplu yükleme sayfası"""
    return render_template('calisanlar_import.html')

@app.route('/calisanlar/import/sablon-indir')
@manager_required
def calisanlar_import_sablon():
    """Çalışanlar import şablonu indir"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Çalışanlar"
    
    # Başlık satırı
    headers = [
        'Ad Soyad*', 'Telefon', 'Email', 'TC Kimlik*', 
        'Proje Adı*', 'Pozisyon Adı*', 'Müdürlük', 'Direktörlük',
        'İl*', 'İlçe', 'Mağaza Adı', 'Araç Durumu*', 
        'İşe Başlama Tarihi*'
    ]
    
    # Stil tanımlamaları
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="28a745", end_color="28a745", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Başlıkları ekle
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border
    
    # Açıklama satırı
    aciklamalar = [
        'Zorunlu', 'Opsiyonel', 'Opsiyonel', 'Zorunlu (11 haneli)',
        'Sistemde kayıtlı proje adı', 'Kadro pozisyon adı', 'Opsiyonel', 'Opsiyonel',
        'Sistemde kayıtlı il adı', 'Opsiyonel', 'Opsiyonel', 'Araçlı veya Araçsız',
        'YYYY-MM-DD formatında zorunlu'
    ]
    
    for col, aciklama in enumerate(aciklamalar, 1):
        cell = ws.cell(row=2, column=col, value=aciklama)
        cell.font = Font(italic=True, size=9, color="666666")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    # Örnek veri satırları
    ornekler = [
        ['Fatma Şahin', '05551112233', 'fatma@example.com', '11122233344',
         'Migros Projesi', 'Satış Danışmanı', 'Perakende Müdürlüğü', 'İstanbul Direktörlüğü',
         'İstanbul', 'Kadıköy', 'Migros Acıbadem', 'Araçsız',
         '2025-01-10'],
        ['Ali Yılmaz', '05559998877', 'ali@example.com', '55566677788',
         'CarrefourSA', 'Reyon Görevlisi', '', '',
         'Ankara', '', 'CarrefourSA Kızılay', 'Araçlı',
         '2025-01-05']
    ]
    
    for row_idx, ornek in enumerate(ornekler, 3):
        for col_idx, deger in enumerate(ornek, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=deger)
            cell.alignment = Alignment(vertical="center")
            cell.border = border
    
    # Sütun genişliklerini ayarla
    column_widths = [20, 15, 25, 15, 20, 20, 20, 25, 15, 15, 20, 15, 20]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = width
    
    # Satır yüksekliklerini ayarla
    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 25
    
    # Dosyayı belleğe kaydet
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'calisanlar_import_sablonu_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@app.route('/calisanlar/import/yukle', methods=['POST'])
@manager_required
def calisanlar_import_yukle():
    """Çalışanlar Excel dosyasını yükle ve işle"""
    if 'excel_file' not in request.files:
        return jsonify({'success': False, 'message': 'Dosya seçilmedi!'}), 400
    
    file = request.files['excel_file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Dosya seçilmedi!'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'success': False, 'message': 'Geçersiz dosya formatı! Sadece Excel dosyaları (.xlsx, .xls) kabul edilir.'}), 400
    
    try:
        # Excel dosyasını oku
        df = pd.read_excel(file, sheet_name=0)
        
        # Başlık satırından sonraki açıklama satırını atla
        if len(df) > 0 and 'Zorunlu' in str(df.iloc[0].values):
            df = df.iloc[1:].reset_index(drop=True)
        
        # Boş satırları temizle
        df = df.dropna(how='all')
        
        conn = get_db()
        cursor = conn.cursor()
        
        basarili_sayisi = 0
        hatalar = []
        
        for index, row in df.iterrows():
            satir_no = index + 3
            
            try:
                # Zorunlu alanları kontrol et
                ad_soyad = str(row.get('Ad Soyad*', '')).strip()
                tc_kimlik = str(row.get('TC Kimlik*', '')).strip()
                proje_adi = str(row.get('Proje Adı*', '')).strip()
                pozisyon_adi = str(row.get('Pozisyon Adı*', '')).strip()
                il_adi = str(row.get('İl*', '')).strip()
                aracli_durum = str(row.get('Araç Durumu*', '')).strip()
                
                if not ad_soyad or ad_soyad == 'nan':
                    hatalar.append(f"Satır {satir_no}: Ad Soyad zorunludur")
                    continue
                
                if not tc_kimlik or tc_kimlik == 'nan' or len(tc_kimlik) != 11:
                    hatalar.append(f"Satır {satir_no}: TC Kimlik zorunludur ve 11 haneli olmalıdır")
                    continue
                
                if not proje_adi or proje_adi == 'nan':
                    hatalar.append(f"Satır {satir_no}: Proje Adı zorunludur")
                    continue
                
                if not pozisyon_adi or pozisyon_adi == 'nan':
                    hatalar.append(f"Satır {satir_no}: Pozisyon Adı zorunludur")
                    continue
                
                if not il_adi or il_adi == 'nan':
                    hatalar.append(f"Satır {satir_no}: İl zorunludur")
                    continue
                
                if not aracli_durum or aracli_durum == 'nan':
                    hatalar.append(f"Satır {satir_no}: Araç Durumu zorunludur")
                    continue
                
                if aracli_durum not in ['Araçlı', 'Araçsız']:
                    hatalar.append(f"Satır {satir_no}: Araç Durumu 'Araçlı' veya 'Araçsız' olmalıdır")
                    continue
                
                # İşe başlama tarihi kontrolü
                ise_baslama_tarihi = None
                ise_baslama_tarihi_raw = row.get('İşe Başlama Tarihi*', '')
                if pd.isna(ise_baslama_tarihi_raw):
                    hatalar.append(f"Satır {satir_no}: İşe Başlama Tarihi zorunludur")
                    continue
                
                try:
                    if isinstance(ise_baslama_tarihi_raw, str):
                        ise_baslama_tarihi = datetime.strptime(ise_baslama_tarihi_raw, '%Y-%m-%d').strftime('%Y-%m-%d')
                    else:
                        ise_baslama_tarihi = ise_baslama_tarihi_raw.strftime('%Y-%m-%d')
                except:
                    hatalar.append(f"Satır {satir_no}: İşe Başlama Tarihi formatı hatalı (YYYY-MM-DD olmalı)")
                    continue
                
                # Proje kontrolü
                proje = cursor.execute('SELECT id FROM projeler WHERE proje_adi = %s AND aktif = TRUE',
                                      (proje_adi,)).fetchone()
                if not proje:
                    hatalar.append(f"Satır {satir_no}: '{proje_adi}' projesi bulunamadı")
                    continue
                proje_id = proje['id']
                
                # İl kontrolü
                il = cursor.execute('SELECT id FROM iller WHERE il_adi = %s AND aktif = TRUE',
                                   (il_adi,)).fetchone()
                if not il:
                    hatalar.append(f"Satır {satir_no}: '{il_adi}' ili bulunamadı")
                    continue
                il_id = il['id']
                
                # İlçe, Müdürlük, Direktörlük kontrolü (opsiyonel)
                ilce_adi = str(row.get('İlçe', '')).strip()
                ilce_id = None
                if ilce_adi and ilce_adi != 'nan':
                    ilce = cursor.execute('SELECT id FROM ilceler WHERE ilce_adi = %s AND il_id = %s AND aktif = TRUE',
                                        (ilce_adi, il_id)).fetchone()
                    if ilce:
                        ilce_id = ilce['id']
                
                mudurluk_adi = str(row.get('Müdürlük', '')).strip()
                mudurluk_id = None
                if mudurluk_adi and mudurluk_adi != 'nan':
                    mudurluk = cursor.execute('SELECT id FROM mudurluker WHERE mudurluk_adi = %s AND aktif = TRUE',
                                             (mudurluk_adi,)).fetchone()
                    if mudurluk:
                        mudurluk_id = mudurluk['id']
                
                direktorluk_adi = str(row.get('Direktörlük', '')).strip()
                direktorluk_id = None
                if direktorluk_adi and direktorluk_adi != 'nan':
                    direktorluk = cursor.execute('SELECT id FROM direktorlukler WHERE direktorluk_adi = %s AND aktif = TRUE',
                                                (direktorluk_adi,)).fetchone()
                    if direktorluk:
                        direktorluk_id = direktorluk['id']
                
                # Kadro ara veya oluştur
                magaza_adi = str(row.get('Mağaza Adı', '')).strip()
                if magaza_adi == 'nan':
                    magaza_adi = ''
                
                kadro = cursor.execute('''
                    SELECT id FROM hedef_kadrolar
                    WHERE proje_id = %s AND pozisyon_adi = %s
                    AND il_id = %s AND COALESCE(ilce_id, 0) = COALESCE(%s, 0)
                    AND COALESCE(magaza_adi, '') = %s
                    AND aracli_durum = %s
                ''', (proje_id, pozisyon_adi, il_id, ilce_id, magaza_adi, aracli_durum)).fetchone()
                
                if not kadro:
                    # Kadro yoksa oluştur
                    cursor.execute('''
                        INSERT INTO hedef_kadrolar
                        (proje_id, pozisyon_adi, mudurluk_id, direktorluk_id, il_id, ilce_id,
                         magaza_adi, aracli_durum, hedef_kisi_sayisi, dolu_kisi_sayisi)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 1)
                    ''', (proje_id, pozisyon_adi, mudurluk_id, direktorluk_id, il_id, ilce_id,
                          magaza_adi, aracli_durum))
                    kadro_id = cursor.lastrowid
                else:
                    kadro_id = kadro['id']
                    # Dolu sayısını artır
                    cursor.execute('''
                        UPDATE hedef_kadrolar
                        SET dolu_kisi_sayisi = dolu_kisi_sayisi + 1
                        WHERE id = %s
                    ''', (kadro_id,))
                
                # Opsiyonel alanlar
                telefon = str(row.get('Telefon', '')).strip()
                if telefon == 'nan':
                    telefon = ''
                
                email = str(row.get('Email', '')).strip()
                if email == 'nan':
                    email = ''
                
                # Çalışanı ekle (aday_id olmadan direkt ekleme)
                cursor.execute('''
                    INSERT INTO calisanlar 
                    (aday_id, kadro_id, ad_soyad, telefon, email, tc_kimlik, ise_baslama_tarihi)
                    VALUES (0, %s, %s, %s, %s, %s, %s)
                ''', (kadro_id, ad_soyad, telefon or None, email or None, tc_kimlik, ise_baslama_tarihi))
                
                basarili_sayisi += 1
                
            except Exception as e:
                hatalar.append(f"Satır {satir_no}: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        # Log kaydı
        log_islem('TOPLU_EKLEME', 'calisanlar', 0,
                 f'{basarili_sayisi} çalışan Excel ile yüklendi',
                 session.get('username'))
        
        # Sonuç mesajı
        if basarili_sayisi > 0 and len(hatalar) == 0:
            return jsonify({
                'success': True,
                'message': f'âœ… {basarili_sayisi} çalışan başarıyla eklendi!',
                'basarili_sayisi': basarili_sayisi,
                'hata_sayisi': 0
            })
        elif basarili_sayisi > 0 and len(hatalar) > 0:
            return jsonify({
                'success': True,
                'message': f'âš ï¸ {basarili_sayisi} çalışan eklendi, {len(hatalar)} satırda hata oluştu',
                'basarili_sayisi': basarili_sayisi,
                'hata_sayisi': len(hatalar),
                'hatalar': hatalar[:10]
            })
        else:
            return jsonify({
                'success': False,
                'message': f'âŒ Hiçbir çalışan eklenemedi. {len(hatalar)} hata bulundu.',
                'basarili_sayisi': 0,
                'hata_sayisi': len(hatalar),
                'hatalar': hatalar[:10]
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Dosya işlenirken hata oluştu: {str(e)}'
        }), 500            

@app.route('/kaynaklar')
@admin_required
def kaynaklar():
    """Kaynak listesi (Sadece Admin)"""
    conn = get_db()
    
    stats = {
        'toplam_kaynak': conn.execute('SELECT COUNT(*) as cnt FROM kaynaklar WHERE aktif = TRUE').fetchone()['cnt'],
        'kaynak_kullanan_aday': conn.execute('SELECT COUNT(DISTINCT kaynak_id) as cnt FROM adaylar WHERE kaynak_id IS NOT NULL').fetchone()['cnt']
    }
    
    kaynaklar = conn.execute('''
        SELECT k.id,
               k.kaynak_adi,
               k.aciklama,
               k.aktif,
               COUNT(a.id) as aday_sayisi
        FROM kaynaklar k
        LEFT JOIN adaylar a ON k.id = a.kaynak_id
        GROUP BY k.id, k.kaynak_adi, k.aciklama, k.aktif
        ORDER BY k.kaynak_adi
    ''').fetchall()
    
    # Manuel girilen diğer kaynaklar
    diger_kaynaklar = conn.execute('''
        SELECT kaynak_diger, COUNT(*) as sayi
        FROM adaylar
        WHERE kaynak_diger IS NOT NULL AND kaynak_diger != ''
        GROUP BY kaynak_diger
        ORDER BY sayi DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('kaynaklar.html', 
                         kaynaklar=kaynaklar,
                         diger_kaynaklar=diger_kaynaklar,
                         stats=stats)

@app.route('/kaynak/ekle', methods=['POST'])
@admin_required
def kaynak_ekle():
    """Yeni kaynak ekle"""
    kaynak_adi = request.form['kaynak_adi']
    aciklama = request.form.get('aciklama', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO kaynaklar (kaynak_adi, aciklama) VALUES (%s, %s)', 
                      (kaynak_adi, aciklama))
        kaynak_id = cursor.lastrowid
        conn.commit()
        log_islem('EKLEME', 'kaynaklar', kaynak_id, f'{kaynak_adi} kaynağı eklendi')
        flash(f'Kaynak "{kaynak_adi}" başarıyla eklendi!', 'success')
    except sqlite3.IntegrityError:
        flash('Bu kaynak zaten mevcut!', 'danger')
    
    conn.close()
    return redirect(url_for('kaynaklar'))

@app.route('/kaynak/<int:kaynak_id>/sil', methods=['POST'])
@admin_required
def kaynak_sil(kaynak_id):
    """Kaynak sil"""
    conn = get_db()
    
    # Önce bu kaynağı kullanan aday var mı kontrol et
    aday_sayisi = conn.execute('SELECT COUNT(*) as cnt FROM adaylar WHERE kaynak_id = %s', 
                               (kaynak_id,)).fetchone()['cnt']
    
    if aday_sayisi > 0:
        flash(f'Bu kaynak {aday_sayisi} aday tarafından kullanılıyor, silinemez!', 'danger')
    else:
        kaynak = conn.execute('SELECT kaynak_adi FROM kaynaklar WHERE id = %s', (kaynak_id,)).fetchone()
        if kaynak:
            conn.execute('DELETE FROM kaynaklar WHERE id = %s', (kaynak_id,))
            conn.commit()
            log_islem('SİLME', 'kaynaklar', kaynak_id, f'{kaynak["kaynak_adi"]} kaynağı silindi')
            flash('Kaynak başarıyla silindi!', 'success')
    
    conn.close()
    return redirect(url_for('kaynaklar'))

@app.route('/kaynak/<int:kaynak_id>/toggle', methods=['POST'])
@admin_required
def kaynak_toggle(kaynak_id):
    """Kaynak aktif/pasif durumu değiştir"""
    conn = get_db()
    
    kaynak = conn.execute('SELECT * FROM kaynaklar WHERE id = %s', (kaynak_id,)).fetchone()
    if kaynak:
        yeni_durum = 0 if kaynak['aktif'] else 1
        conn.execute('UPDATE kaynaklar SET aktif = %s WHERE id = %s', (yeni_durum, kaynak_id))
        conn.commit()
        
        durum_text = 'aktif' if yeni_durum else 'pasif'
        log_islem('GÜNCELLEME', 'kaynaklar', kaynak_id, 
                 f'{kaynak["kaynak_adi"]} kaynağı {durum_text} yapıldı')
        flash(f'Kaynak {durum_text} yapıldı!', 'success')
    
    conn.close()
    return redirect(url_for('kaynaklar'))   

@app.route('/calisma-sekilleri')
@admin_required
def calisma_sekilleri():
    """Çalışma şekilleri listesi (Sadece Admin)"""
    conn = get_db()
    
    stats = {
        'toplam_sekil': conn.execute('SELECT COUNT(*) as cnt FROM calisma_sekilleri WHERE aktif = TRUE').fetchone()['cnt'],
        'kullanan_kadro': conn.execute('SELECT COUNT(DISTINCT calisma_sekli) as cnt FROM hedef_kadrolar WHERE calisma_sekli IS NOT NULL').fetchone()['cnt']
    }
    
    calisma_sekilleri = conn.execute('''
        SELECT cs.id,
               cs.calisma_sekli,
               cs.aktif,
               COUNT(hk.id) as kadro_sayisi
        FROM calisma_sekilleri cs
        LEFT JOIN hedef_kadrolar hk ON cs.calisma_sekli = hk.calisma_sekli
        GROUP BY cs.id, cs.calisma_sekli, cs.aktif
        ORDER BY cs.calisma_sekli
    ''').fetchall()
    
    conn.close()
    
    return render_template('calisma_sekilleri.html', 
                         calisma_sekilleri=calisma_sekilleri,
                         stats=stats)

@app.route('/calisma-sekli/ekle', methods=['POST'])
@admin_required
def calisma_sekli_ekle():
    """Yeni çalışma şekli ekle"""
    calisma_sekli = request.form['calisma_sekli']
    aciklama = request.form.get('aciklama', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO calisma_sekilleri (calisma_sekli, aciklama) VALUES (%s, %s)', 
                      (calisma_sekli, aciklama))
        sekil_id = cursor.lastrowid
        conn.commit()
        log_islem('EKLEME', 'calisma_sekilleri', sekil_id, f'{calisma_sekli} çalışma şekli eklendi')
        flash(f'Çalışma şekli "{calisma_sekli}" başarıyla eklendi!', 'success')
    except sqlite3.IntegrityError:
        flash('Bu çalışma şekli zaten mevcut!', 'danger')
    
    conn.close()
    return redirect(url_for('calisma_sekilleri'))

@app.route('/calisma-sekli/<int:sekil_id>/sil', methods=['POST'])
@admin_required
def calisma_sekli_sil(sekil_id):
    """Çalışma şekli sil"""
    conn = get_db()
    
    # Önce bu çalışma şeklini kullanan kadro var mı kontrol et
    kadro_sayisi = conn.execute('SELECT COUNT(*) as cnt FROM hedef_kadrolar WHERE calisma_sekli = (SELECT calisma_sekli FROM calisma_sekilleri WHERE id = %s)', 
                                (sekil_id,)).fetchone()['cnt']
    
    if kadro_sayisi > 0:
        flash(f'Bu çalışma şekli {kadro_sayisi} kadro tarafından kullanılıyor, silinemez!', 'danger')
    else:
        sekil = conn.execute('SELECT calisma_sekli FROM calisma_sekilleri WHERE id = %s', (sekil_id,)).fetchone()
        if sekil:
            conn.execute('DELETE FROM calisma_sekilleri WHERE id = %s', (sekil_id,))
            conn.commit()
            log_islem('SİLME', 'calisma_sekilleri', sekil_id, f'{sekil["calisma_sekli"]} çalışma şekli silindi')
            flash('Çalışma şekli başarıyla silindi!', 'success')
    
    conn.close()
    return redirect(url_for('calisma_sekilleri'))

@app.route('/calisma-sekli/<int:sekil_id>/toggle', methods=['POST'])
@admin_required
def calisma_sekli_toggle(sekil_id):
    """Çalışma şekli aktif/pasif durumu değiştir"""
    conn = get_db()
    
    sekil = conn.execute('SELECT * FROM calisma_sekilleri WHERE id = %s', (sekil_id,)).fetchone()
    if sekil:
        yeni_durum = 0 if sekil['aktif'] else 1
        conn.execute('UPDATE calisma_sekilleri SET aktif = %s WHERE id = %s', (yeni_durum, sekil_id))
        conn.commit()
        
        durum_text = 'aktif' if yeni_durum else 'pasif'
        log_islem('GÜNCELLEME', 'calisma_sekilleri', sekil_id, 
                 f'{sekil["calisma_sekli"]} çalışma şekli {durum_text} yapıldı')
        flash(f'Çalışma şekli {durum_text} yapıldı!', 'success')
    
    conn.close()
    return redirect(url_for('calisma_sekilleri'))    
    
@app.route('/cikis-kayitlari/excel-export')
@login_required
def cikis_kayitlari_excel_export():
    """Çıkış kayıtlarını Excel'e aktar"""
    conn = get_db()
    
    # Çıkış kayıtlarını getir
    kayitlar = conn.execute('''
        SELECT ck.*,
               c.ad_soyad,
               c.telefon,
               c.email,
               c.tc_kimlik,
               c.ise_baslama_tarihi,
               hk.pozisyon_adi,
               hk.magaza_adi,
               p.proje_adi,
               m.mudurluk_adi,
               d.direktorluk_adi,
               i.il_adi,
               ic.ilce_adi
        FROM cikis_kayitlari ck
        LEFT JOIN calisanlar c ON ck.calisan_id = c.id
        LEFT JOIN hedef_kadrolar hk ON c.kadro_id = hk.id
        LEFT JOIN projeler p ON hk.proje_id = p.id
        LEFT JOIN mudurluker m ON hk.mudurluk_id = m.id
        LEFT JOIN direktorlukler d ON hk.direktorluk_id = d.id
        LEFT JOIN iller i ON hk.il_id = i.id
        LEFT JOIN ilceler ic ON hk.ilce_id = ic.id
        ORDER BY ck.cikis_tarihi DESC, ck.olusturma_tarihi DESC
    ''').fetchall()
    
    conn.close()
    
    # Excel workbook oluştur
    wb = Workbook()
    ws = wb.active
    ws.title = "Çıkış Kayıtları"
    
    # Stil tanımlamaları
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    cell_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    center_alignment = Alignment(horizontal="center", vertical="center")
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Başlıklar
    headers = [
        'Kayıt ID', 'Ad Soyad', 'TC Kimlik', 'Telefon', 'Email',
        'Proje', 'Pozisyon', 'Müdürlük', 'Direktörlük',
        'İl', 'İlçe', 'Mağaza',
        'İşe Başlama', 'Çıkış Tarihi', 'Çıkış Nedeni',
        'Liste Durumu', 'Tekrar İşe Alınabilir',
        'Zimmet Teslim', 'Kıyafet Teslim', 'Anahtar Teslim', 'Kimlik Teslim',
        'İhbar Tazminat', 'Kıdem Tazminat',
        'Yönetici Notu', 'İK Notu', 'Genel Değerlendirme',
        'İşlem Yapan', 'Kayıt Tarihi'
    ]
    
    # Başlık satırını yaz
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border
    
    # Veri satırlarını yaz
    for row_num, kayit in enumerate(kayitlar, 2):
        # Temel bilgiler
        ws.cell(row=row_num, column=1, value=kayit['id']).alignment = center_alignment
        ws.cell(row=row_num, column=2, value=kayit['ad_soyad']).alignment = cell_alignment
        ws.cell(row=row_num, column=3, value=kayit['tc_kimlik'] or '-').alignment = center_alignment
        ws.cell(row=row_num, column=4, value=kayit['telefon'] or '-').alignment = center_alignment
        ws.cell(row=row_num, column=5, value=kayit['email'] or '-').alignment = cell_alignment
        
        # İş bilgileri
        ws.cell(row=row_num, column=6, value=kayit['proje_adi'] or '-').alignment = cell_alignment
        ws.cell(row=row_num, column=7, value=kayit['pozisyon_adi'] or '-').alignment = cell_alignment
        ws.cell(row=row_num, column=8, value=kayit['mudurluk_adi'] or '-').alignment = cell_alignment
        ws.cell(row=row_num, column=9, value=kayit['direktorluk_adi'] or '-').alignment = cell_alignment
        
        # Lokasyon
        ws.cell(row=row_num, column=10, value=kayit['il_adi'] or '-').alignment = cell_alignment
        ws.cell(row=row_num, column=11, value=kayit['ilce_adi'] or '-').alignment = cell_alignment
        ws.cell(row=row_num, column=12, value=kayit['magaza_adi'] or '-').alignment = cell_alignment
        
        # Tarihler
        ws.cell(row=row_num, column=13, value=kayit['ise_baslama_tarihi'] or '-').alignment = center_alignment
        ws.cell(row=row_num, column=14, value=kayit['cikis_tarihi']).alignment = center_alignment
        
        # Çıkış bilgileri
        ws.cell(row=row_num, column=15, value=kayit['cikis_nedeni']).alignment = cell_alignment
        ws.cell(row=row_num, column=16, value=kayit['liste_durumu']).alignment = center_alignment
        ws.cell(row=row_num, column=17, value='Evet' if kayit['tekrar_ise_alinabilir'] else 'Hayır').alignment = center_alignment
        
        # Checklist
        ws.cell(row=row_num, column=18, value='âœ“' if kayit['zimmet_teslim'] else 'âœ—').alignment = center_alignment
        ws.cell(row=row_num, column=19, value='âœ“' if kayit['kiyafet_teslim'] else 'âœ—').alignment = center_alignment
        ws.cell(row=row_num, column=20, value='âœ“' if kayit['anahtar_teslim'] else 'âœ—').alignment = center_alignment
        ws.cell(row=row_num, column=21, value='âœ“' if kayit['kimlik_teslim'] else 'âœ—').alignment = center_alignment
        
        # Tazminatlar
        ws.cell(row=row_num, column=22, value=kayit['ihbar_tazminat_durumu'] or '-').alignment = cell_alignment
        ws.cell(row=row_num, column=23, value=kayit['kidem_tazminat_durumu'] or '-').alignment = cell_alignment
        
        # Notlar
        ws.cell(row=row_num, column=24, value=kayit['yonetici_notu'] or '-').alignment = cell_alignment
        ws.cell(row=row_num, column=25, value=kayit['ik_notu'] or '-').alignment = cell_alignment
        ws.cell(row=row_num, column=26, value=kayit['genel_degerlendirme'] or '-').alignment = cell_alignment
        
        # Meta
        ws.cell(row=row_num, column=27, value=kayit['islem_yapan'] or '-').alignment = cell_alignment
        ws.cell(row=row_num, column=28, value=str(kayit['olusturma_tarihi']) if kayit['olusturma_tarihi'] else '-').alignment = center_alignment
        
        # Border ekle
        for col in range(1, 29):
            ws.cell(row=row_num, column=col).border = border
    
    # Sütun genişliklerini ayarla
    column_widths = {
        'A': 10, 'B': 25, 'C': 15, 'D': 15, 'E': 30,
        'F': 20, 'G': 20, 'H': 20, 'I': 20,
        'J': 15, 'K': 15, 'L': 25,
        'M': 15, 'N': 15, 'O': 20,
        'P': 15, 'Q': 20,
        'R': 12, 'S': 12, 'T': 12, 'U': 12,
        'V': 20, 'W': 20,
        'X': 40, 'Y': 40, 'Z': 40,
        'AA': 20, 'AB': 20
    }
    
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width
    
    # Satır yüksekliğini ayarla
    ws.row_dimensions[1].height = 40  # Başlık
    for row in range(2, len(kayitlar) + 2):
        ws.row_dimensions[row].height = 30
    
    # Excel dosyasını memory'ye kaydet
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Dosya adı
    from datetime import datetime
    filename = f"Cikis_Kayitlari_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )    

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001)