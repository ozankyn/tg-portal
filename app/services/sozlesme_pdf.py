# -*- coding: utf-8 -*-
"""
Sözleşme PDF Jeneratör
- Otomatik değişkenler: çalışan modelinden
- Manuel değişkenler: sözleşme oluşturma formundan
- HTML şablon → WeasyPrint → PDF
"""
import re
from datetime import date, datetime


# ============================================================
# DEĞİŞKEN KATALOĞU
# ============================================================

# Çalışan kaydından otomatik doldurulan değişkenler
OTOMATIK_DEGISKENLER = [
    {'kod': 'ad_soyad',          'aciklama': 'Çalışan ad soyad'},
    {'kod': 'tc_kimlik',         'aciklama': 'TC Kimlik No'},
    {'kod': 'ise_baslama',       'aciklama': 'İşe başlama tarihi (DD.MM.YYYY)'},
    {'kod': 'sozlesme_baslangic','aciklama': 'Sözleşme başlangıç tarihi'},
    {'kod': 'sozlesme_bitis',    'aciklama': 'Sözleşme bitiş tarihi'},
    {'kod': 'proje_adi',         'aciklama': 'Proje adı'},
    {'kod': 'pozisyon',          'aciklama': 'Pozisyon'},
    {'kod': 'departman',         'aciklama': 'Departman'},
    {'kod': 'adres',             'aciklama': 'Çalışan adresi'},
    {'kod': 'il',                'aciklama': 'İl'},
    {'kod': 'ilce',              'aciklama': 'İlçe'},
    {'kod': 'telefon',           'aciklama': 'Telefon'},
    {'kod': 'email',             'aciklama': 'E-posta'},
    {'kod': 'dogum_tarihi',      'aciklama': 'Doğum tarihi'},
    {'kod': 'dogum_yeri',        'aciklama': 'Doğum yeri'},
    {'kod': 'sicil_no',          'aciklama': 'Sicil numarası'},
    {'kod': 'bugunun_tarihi',    'aciklama': 'Bugünün (oluşturma) tarihi'},
]

# Manuel girilecek değişkenler
MANUEL_DEGISKENLER = [
    {'kod': 'brut_ucret',     'aciklama': 'Brüt ücret (₺)',           'tip': 'number',  'default': ''},
    {'kod': 'net_ucret',      'aciklama': 'Net ücret (₺)',            'tip': 'number',  'default': ''},
    {'kod': 'calisma_gunu',   'aciklama': 'Haftalık çalışma günü',    'tip': 'number',  'default': '5'},
    {'kod': 'calisma_saati',  'aciklama': 'Günlük çalışma saati',     'tip': 'number',  'default': '9'},
    {'kod': 'deneme_suresi',  'aciklama': 'Deneme süresi (gün)',      'tip': 'number',  'default': '60'},
    {'kod': 'yillik_izin',    'aciklama': 'Yıllık izin günü',         'tip': 'number',  'default': '14'},
]


def _format_date(d):
    if not d:
        return ''
    if isinstance(d, str):
        return d
    return d.strftime('%d.%m.%Y')


def calisan_degiskenleri(calisan):
    """Çalışan modelinden otomatik değişken sözlüğünü çıkarır."""
    proje_adi = ''
    if calisan.kadro and calisan.kadro.proje:
        proje_adi = calisan.kadro.proje.ad

    return {
        'ad_soyad':          calisan.full_name or '',
        'tc_kimlik':         calisan.tc_kimlik or '',
        'ise_baslama':       _format_date(calisan.ise_baslama),
        'sozlesme_baslangic':_format_date(calisan.sozlesme_baslangic),
        'sozlesme_bitis':    _format_date(calisan.sozlesme_bitis),
        'proje_adi':         proje_adi,
        'pozisyon':          (calisan.pozisyon.ad if calisan.pozisyon else '') or '',
        'departman':         (calisan.departman.ad if calisan.departman else '') or '',
        'adres':             calisan.adres or '',
        'il':                calisan.il or '',
        'ilce':              calisan.ilce or '',
        'telefon':           calisan.telefon or '',
        'email':             calisan.email or '',
        'dogum_tarihi':      _format_date(calisan.dogum_tarihi),
        'dogum_yeri':        calisan.dogum_yeri or '',
        'sicil_no':          calisan.sicil_no or '',
        'bugunun_tarihi':    _format_date(date.today()),
    }


def ornek_degerler():
    """Önizleme için örnek verilerle doldurulmuş sözlük."""
    return {
        'ad_soyad':          'Ahmet Yılmaz',
        'tc_kimlik':         '12345678901',
        'ise_baslama':       '01.06.2026',
        'sozlesme_baslangic':'01.06.2026',
        'sozlesme_bitis':    '31.12.2026',
        'proje_adi':         'Örnek Proje',
        'pozisyon':          'Saha Satış Temsilcisi',
        'departman':         'Saha',
        'adres':             'Örnek Mah. Atatürk Cad. No:1',
        'il':                'İstanbul',
        'ilce':              'Kadıköy',
        'telefon':           '0532 000 00 00',
        'email':             'ornek@example.com',
        'dogum_tarihi':      '15.05.1995',
        'dogum_yeri':        'İstanbul',
        'sicil_no':          'TG-0001',
        'bugunun_tarihi':    _format_date(date.today()),
        # Manuel
        'brut_ucret':        '30.000',
        'net_ucret':         '23.500',
        'calisma_gunu':      '5',
        'calisma_saati':     '9',
        'deneme_suresi':     '60',
        'yillik_izin':       '14',
    }


# {ad_soyad} stilini bulur (boşluk yok varsayıyoruz)
_PLACEHOLDER_RE = re.compile(r'\{([a-zA-Z0-9_]+)\}')


def degiskenleri_doldur(html, degerler):
    """HTML içindeki {key} placeholder'larını degerler sözlüğüyle değiştirir.

    Tanımsız değişken kaldıysa boş string'e dönüştürülür (sözleşme bozulmasın).
    """
    if not html:
        return ''

    def _repl(m):
        key = m.group(1)
        return str(degerler.get(key, ''))

    return _PLACEHOLDER_RE.sub(_repl, html)


def kullanilan_degiskenler(html):
    """Şablonda kullanılan placeholder'ların unique listesini döner."""
    if not html:
        return []
    return sorted(set(_PLACEHOLDER_RE.findall(html)))


# ============================================================
# PDF RENDER
# ============================================================

# A4 + temiz tipografi için varsayılan CSS
_DEFAULT_CSS = """
@page {
    size: A4;
    margin: 2.5cm 2cm;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #666;
    }
}
body {
    font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
}
h1, h2, h3, h4 { font-weight: 700; margin-top: 1.2em; margin-bottom: 0.5em; }
h1 { font-size: 18pt; text-align: center; }
h2 { font-size: 14pt; }
h3 { font-size: 12pt; }
p  { margin: 0.5em 0; text-align: justify; }
table { width: 100%; border-collapse: collapse; margin: 0.8em 0; }
th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; vertical-align: top; }
th { background: #f4f4f4; font-weight: 700; }
ul, ol { margin: 0.5em 0; padding-left: 1.6em; }
li { margin: 0.2em 0; }
.imza-tablo { margin-top: 3em; }
.imza-tablo td { border: none; padding-top: 1.5em; width: 50%; }
"""


def html_to_pdf_bytes(html, css_extra=None):
    """HTML → PDF bytes (WeasyPrint)."""
    from weasyprint import HTML, CSS

    full_html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="utf-8">
    <title>Sözleşme</title>
</head>
<body>
{html}
</body>
</html>"""

    stylesheets = [CSS(string=_DEFAULT_CSS)]
    if css_extra:
        stylesheets.append(CSS(string=css_extra))

    return HTML(string=full_html).write_pdf(stylesheets=stylesheets)


def render_sozlesme_pdf(html_sablon, degerler):
    """Şablonu doldur + PDF bytes döner."""
    doldurulmus = degiskenleri_doldur(html_sablon, degerler)
    return html_to_pdf_bytes(doldurulmus)
