import sys
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import get_db
from datetime import datetime

# Windows console encoding sorununu çöz
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_email_ayar(ayar_adi):
    """Email ayarını getir"""
    conn = get_db()
    ayar = conn.execute(
        'SELECT ayar_degeri FROM email_ayarlari WHERE ayar_adi = ? AND aktif = 1',
        (ayar_adi,)
    ).fetchone()
    conn.close()
    return ayar['ayar_degeri'] if ayar else None

def get_email_sablon(sablon_adi):
    """Email şablonunu getir"""
    conn = get_db()
    sablon = conn.execute(
        'SELECT * FROM email_sablonlari WHERE sablon_adi = ? AND aktif = 1',
        (sablon_adi,)
    ).fetchone()
    conn.close()
    return sablon

def email_gonder(alici_email, konu, icerik, sablon_adi=None, ilgili_tablo=None, ilgili_id=None):
    """
    Email gönder
    """
    try:
        # SMTP ayarları
        smtp_sunucu = get_email_ayar('smtp_sunucu')
        smtp_port = int(get_email_ayar('smtp_port') or 587)
        smtp_kullanici = get_email_ayar('smtp_kullanici')
        smtp_sifre = get_email_ayar('smtp_sifre')
        gonderici_adi = get_email_ayar('gonderici_adi')
        
        # DEBUG: Email değerlerini kontrol et
        print(f"DEBUG - smtp_kullanici: [{smtp_kullanici}] (len: {len(smtp_kullanici) if smtp_kullanici else 0})")
        print(f"DEBUG - smtp_kullanici repr: {repr(smtp_kullanici)}")
        print(f"DEBUG - gonderici_adi: [{gonderici_adi}]")
        
        if not all([smtp_sunucu, smtp_kullanici, smtp_sifre]):
            raise Exception("Email ayarları eksik!")
        
        # Email oluştur
        msg = MIMEMultipart('alternative')
        # RFC 5322 uyumlu From header (email adresini temizle ve tırnak içine al)
        smtp_kullanici_temiz = smtp_kullanici.strip().replace(' ', '')
        msg['From'] = f'"{gonderici_adi}" <{smtp_kullanici_temiz}>'
        # DEBUG: From header'ı kontrol et
        print(f"DEBUG - From header: {msg['From']}")
        print(f"DEBUG - From header repr: {repr(msg['From'])}")
        msg['To'] = alici_email
        msg['Subject'] = konu
        
        # HTML içerik
        html_part = MIMEText(icerik, 'html', 'utf-8')
        msg.attach(html_part)
        
        # SMTP ile gönder
        with smtplib.SMTP(smtp_sunucu, smtp_port) as server:
            server.starttls()
            server.login(smtp_kullanici, smtp_sifre)
            # DEBUG: Gönderilecek raw message
            raw_msg = msg.as_string()
            print(f"DEBUG - RAW MESSAGE PREVIEW (first 800 chars):")
            print(raw_msg[:800])
            print("=" * 50)
            server.send_message(msg)
        
        # Başarılı log
        log_email(alici_email, konu, 'gonderildi', None, sablon_adi, ilgili_tablo, ilgili_id)
        return True, "Email başarıyla gönderildi"
        
    except Exception as e:
        # Hata log
        log_email(alici_email, konu, 'hata', str(e), sablon_adi, ilgili_tablo, ilgili_id)
        return False, str(e)

def log_email(alici_email, konu, durum, hata_mesaji, sablon_adi=None, ilgili_tablo=None, ilgili_id=None):
    """Email gönderim logunu kaydet"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO email_loglari 
        (alici_email, konu, sablon_adi, gonderim_durumu, hata_mesaji, ilgili_tablo, ilgili_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (alici_email, konu, sablon_adi, durum, hata_mesaji, ilgili_tablo, ilgili_id))
    conn.commit()
    conn.close()

def yeni_ise_giris_bildirimi(aday_bilgileri):
    """
    Yeni işe giriş bildirimi gönder
    aday_bilgileri: dict - Aday ve pozisyon bilgileri
    """
    # Şablonu getir
    sablon = get_email_sablon('yeni_ise_giris')
    if not sablon:
        return False, "Email şablonu bulunamadı"
    
    # Şablon değişkenlerini doldur
    portal_url = "https://ikportal.teamguerilla.com"
    gonderim_zamani = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    # DOĞUM TARİHİ VE YAŞ HESAPLA
    dogum_tarihi_str = '-'
    yas_str = '-'
    
    if aday_bilgileri.get('dogum_tarihi'):
        try:
            dogum_tarihi_obj = datetime.strptime(aday_bilgileri['dogum_tarihi'], '%Y-%m-%d')
            bugun = datetime.now()
            
            # Yaş hesapla
            yil = bugun.year - dogum_tarihi_obj.year
            ay = bugun.month - dogum_tarihi_obj.month
            
            if ay < 0:
                yil -= 1
                ay += 12
            
            if bugun.day < dogum_tarihi_obj.day:
                ay -= 1
                if ay < 0:
                    yil -= 1
                    ay += 12
            
            dogum_tarihi_str = dogum_tarihi_obj.strftime('%d.%m.%Y')
            yas_str = f"{yil}.{ay} yaş"
        except Exception as e:
            print(f"Doğum tarihi parse hatası: {e}")
    
    icerik = sablon['sablon_icerik'].format(
        ad_soyad=aday_bilgileri.get('ad_soyad', '-'),
        tc_kimlik=aday_bilgileri.get('tc_kimlik', '-'),
        dogum_tarihi=dogum_tarihi_str,  # ← YENİ
        yas=yas_str,  # ← YENİ
        telefon=aday_bilgileri.get('telefon', '-'),
        email=aday_bilgileri.get('email', '-'),
        proje_adi=aday_bilgileri.get('proje_adi', '-'),
        pozisyon_adi=aday_bilgileri.get('pozisyon_adi', '-'),
        mudurluk_adi=aday_bilgileri.get('mudurluk_adi', '-'),  # ← YENİ
        direktorluk_adi=aday_bilgileri.get('direktorluk_adi', '-'),  # ← YENİ
        il=aday_bilgileri.get('il', '-'),
        ilce=aday_bilgileri.get('ilce', '-'),
        magaza_adi=aday_bilgileri.get('magaza_adi', '-'),
        aracli_durum=aday_bilgileri.get('aracli_durum', 'Araçsız'),
        calisma_sekli=aday_bilgileri.get('calisma_sekli', '-'),
        ise_baslama_tarihi=aday_bilgileri.get('ise_baslama_tarihi', '-'),
        portal_url=portal_url,
        gonderim_zamani=gonderim_zamani
    )
    
    konu = sablon['sablon_konusu'].format(
        ad_soyad=aday_bilgileri.get('ad_soyad', '-')
    )
    
    # Alıcı listesi
    alicilar = [
        ('egitim_email', 'Eğitim Departmanı'),
        ('filo_email', 'Filo Departmanı'),
        ('ik_email', 'İK Departmanı'),
        ('raporlama_email', 'Raporlama Departmanı'),
        ('yonetici_email', 'Yönetici')
    ]
    
    basarili_sayisi = 0
    hatalar = []
    
    for ayar_adi, departman_adi in alicilar:
        email_ayari = get_email_ayar(ayar_adi)
        if email_ayari:
            # Virgülle ayrılmış birden fazla email olabilir
            email_listesi = [e.strip() for e in email_ayari.split(',') if e.strip()]
            
            for email in email_listesi:
                basarili, mesaj = email_gonder(
                    email, 
                    konu, 
                    icerik, 
                    'yeni_ise_giris',
                    'calisanlar',
                    aday_bilgileri.get('id')
                )
                if basarili:
                    basarili_sayisi += 1
                    print(f"[OK] {departman_adi} email gonderildi: {email}")
                else:
                    hatalar.append(f"{departman_adi} ({email}): {mesaj}")
                    print(f"[HATA] {departman_adi} email gonderilemedi ({email}): {mesaj}")
    
    if basarili_sayisi > 0:
        return True, f"{basarili_sayisi} departmana bildirim gonderildi"
    else:
        return False, "Hicbir departmana email gonderilemedi: " + ", ".join(hatalar)


def isten_cikis_bildirimi(cikis_bilgileri):
    """
    İşten çıkış bildirimi gönder
    cikis_bilgileri: dict - Çalışan ve çıkış bilgileri
    """
    # Şablonu getir
    sablon = get_email_sablon('isten_cikis')
    if not sablon:
        return False, "Email şablonu bulunamadı"
    
    # Şablon değişkenlerini doldur
    portal_url = "https://ikportal.teamguerilla.com"
    gonderim_zamani = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    # Checklist sembolleri
    zimmet_sembol = '✓' if cikis_bilgileri.get('zimmet_teslim') else '✗'
    kiyafet_sembol = '✓' if cikis_bilgileri.get('kiyafet_teslim') else '✗'
    anahtar_sembol = '✓' if cikis_bilgileri.get('anahtar_teslim') else '✗'
    kimlik_sembol = '✓' if cikis_bilgileri.get('kimlik_teslim') else '✗'
    
    icerik = sablon['sablon_icerik'].format(
        ad_soyad=cikis_bilgileri.get('ad_soyad', '-'),
        telefon=cikis_bilgileri.get('telefon', '-'),
        email=cikis_bilgileri.get('email', '-'),
        tc_kimlik=cikis_bilgileri.get('tc_kimlik', '-'),
        proje_adi=cikis_bilgileri.get('proje_adi', '-'),
        pozisyon_adi=cikis_bilgileri.get('pozisyon_adi', '-'),
        mudurluk_adi=cikis_bilgileri.get('mudurluk_adi', '-'),  # ← YENİ
        direktorluk_adi=cikis_bilgileri.get('direktorluk_adi', '-'),  # ← YENİ
        il=cikis_bilgileri.get('il', '-'),
        ilce=cikis_bilgileri.get('ilce', '-'),
        magaza_adi=cikis_bilgileri.get('magaza_adi', '-'),
        aracli_durum=cikis_bilgileri.get('aracli_durum', 'Araçsız'),
        ise_baslama_tarihi=cikis_bilgileri.get('ise_baslama_tarihi', '-'),
        cikis_tarihi=cikis_bilgileri.get('cikis_tarihi', '-'),
        cikis_nedeni=cikis_bilgileri.get('cikis_nedeni', '-'),
        liste_durumu=cikis_bilgileri.get('liste_durumu', '-'),
        tekrar_ise_alinabilir='Evet' if cikis_bilgileri.get('tekrar_ise_alinabilir') else 'Hayır',
        zimmet_teslim=zimmet_sembol,
        kiyafet_teslim=kiyafet_sembol,
        anahtar_teslim=anahtar_sembol,
        kimlik_teslim=kimlik_sembol,
        ihbar_tazminat=cikis_bilgileri.get('ihbar_tazminat_durumu', '-'),
        kidem_tazminat=cikis_bilgileri.get('kidem_tazminat_durumu', '-'),
        yonetici_notu=cikis_bilgileri.get('yonetici_notu', '-'),
        ik_notu=cikis_bilgileri.get('ik_notu', '-'),
        genel_degerlendirme=cikis_bilgileri.get('genel_degerlendirme', '-'),
        islem_yapan=cikis_bilgileri.get('islem_yapan', '-'),
        portal_url=portal_url,
        gonderim_zamani=gonderim_zamani
    )
    
    konu = sablon['sablon_konusu'].format(
        ad_soyad=cikis_bilgileri.get('ad_soyad', '-')
    )
    
    # Alıcı listesi (aynı departmanlar)
    alicilar = [
        ('egitim_email', 'Eğitim Departmanı'),
        ('filo_email', 'Filo Departmanı'),
        ('ik_email', 'İK Departmanı'),
        ('raporlama_email', 'Raporlama Departmanı'),
        ('yonetici_email', 'Yönetici')
    ]
    
    basarili_sayisi = 0
    hatalar = []
    
    for ayar_adi, departman_adi in alicilar:
        email_ayari = get_email_ayar(ayar_adi)
        if email_ayari:
            # Virgülle ayrılmış birden fazla email olabilir
            email_listesi = [e.strip() for e in email_ayari.split(',') if e.strip()]
            
            for email in email_listesi:
                basarili, mesaj = email_gonder(
                    email, 
                    konu, 
                    icerik, 
                    'isten_cikis',
                    'cikis_kayitlari',
                    cikis_bilgileri.get('id')
                )
                if basarili:
                    basarili_sayisi += 1
                    print(f"[OK] {departman_adi} email gönderildi: {email}")
                else:
                    hatalar.append(f"{departman_adi} ({email}): {mesaj}")
                    print(f"[HATA] {departman_adi} email gönderilemedi ({email}): {mesaj}")
    
    if basarili_sayisi > 0:
        return True, f"{basarili_sayisi} departmana bildirim gönderildi"
    else:
        return False, "Hiçbir departmana email gönderilemedi: " + ", ".join(hatalar)