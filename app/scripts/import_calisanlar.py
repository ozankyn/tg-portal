# -*- coding: utf-8 -*-
"""
Çalışan Excel Import Script
Kullanım: docker-compose exec web flask import-calisanlar /app/uploads/calisanlar.xlsx
"""

import click
import pandas as pd
from datetime import datetime
from flask import current_app
from flask.cli import with_appcontext
from app import db
from app.models.ik import Calisan, Departman
from app.models.sirket import TuzelKisi, SgkDosya
from app.models.base import CalisanDurumu


def parse_ad_soyad(ad_soyad):
    """Ad Soyad'ı ayır"""
    if not ad_soyad or pd.isna(ad_soyad):
        return None, None
    parts = str(ad_soyad).strip().split()
    if len(parts) == 1:
        return parts[0], ''
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        # Son kelime soyad, kalanı ad
        return ' '.join(parts[:-1]), parts[-1]


def parse_cinsiyet(cinsiyet):
    """Cinsiyet dönüştür"""
    if not cinsiyet or pd.isna(cinsiyet):
        return None
    c = str(cinsiyet).lower().strip()
    if c in ['erkek', 'e', 'male', 'm']:
        return 'erkek'
    elif c in ['kadın', 'kadin', 'k', 'female', 'f']:
        return 'kadin'
    return None


def parse_date(date_val):
    """Tarih parse et"""
    if pd.isna(date_val) or date_val is None:
        return None
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, str):
        for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']:
            try:
                return datetime.strptime(date_val, fmt).date()
            except:
                pass
    return None


def clean_phone(phone):
    """Telefon numarasını temizle"""
    if not phone or pd.isna(phone):
        return None
    digits = ''.join(filter(str.isdigit, str(phone)))
    if len(digits) == 10:
        return f"0{digits}"
    elif len(digits) == 11 and digits.startswith('0'):
        return digits
    return str(phone).strip() if phone else None


def find_sgk_dosya(firma_unvani):
    """Firma ünvanından SGK dosyası bul"""
    if not firma_unvani or pd.isna(firma_unvani):
        return None
    
    tuzel = TuzelKisi.query.filter(
        TuzelKisi.ad.ilike(firma_unvani),
        TuzelKisi.is_deleted == False
    ).first()
    
    if not tuzel:
        tuzel = TuzelKisi.query.filter(
            TuzelKisi.kisa_ad.ilike(firma_unvani),
            TuzelKisi.is_deleted == False
        ).first()
    
    if tuzel:
        sgk = SgkDosya.query.filter_by(
            tuzel_kisi_id=tuzel.id,
            is_deleted=False,
            aktif=True
        ).first()
        return sgk
    
    return None


def find_departman(dept_adi):
    """Departman adından departman bul"""
    if not dept_adi or pd.isna(dept_adi):
        return None
    
    dept = Departman.query.filter(
        Departman.ad.ilike(dept_adi.strip()),
        Departman.is_deleted == False
    ).first()
    
    return dept


def find_yonetici(yonetici_adi):
    """Yönetici adından çalışan bul"""
    if not yonetici_adi or pd.isna(yonetici_adi):
        return None
    
    ad, soyad = parse_ad_soyad(yonetici_adi)
    if not ad:
        return None
    
    query = Calisan.query.filter(Calisan.is_deleted == False)
    
    if soyad:
        yonetici = query.filter(
            Calisan.ad.ilike(ad),
            Calisan.soyad.ilike(soyad)
        ).first()
    else:
        yonetici = query.filter(Calisan.ad.ilike(ad)).first()
    
    return yonetici


@click.command('import-calisanlar')
@click.argument('filepath')
@click.option('--dry-run', is_flag=True, help='Gerçek kayıt yapmadan test et')
@click.option('--skip-existing', is_flag=True, default=True, help='TC kimlik varsa atla')
@with_appcontext
def import_calisanlar(filepath, dry_run, skip_existing):
    """Excel'den çalışan import et"""
    
    click.echo(f"Dosya okunuyor: {filepath}")
    
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        click.echo(f"Hata: Dosya okunamadı - {e}", err=True)
        return
    
    click.echo(f"Toplam satır: {len(df)}")
    
    if dry_run:
        click.echo("⚠️  DRY RUN - Kayıt yapılmayacak")
    
    created = 0
    skipped = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            tc_kimlik = str(int(row.get('TC.Kimlik no', 0))) if pd.notna(row.get('TC.Kimlik no')) else None
            
            if tc_kimlik and skip_existing:
                existing = Calisan.query.filter_by(tc_kimlik=tc_kimlik, is_deleted=False).first()
                if existing:
                    click.echo(f"  ⏭️  Atlandı (TC mevcut): {row.get('Adı Soyadı')}")
                    skipped += 1
                    continue
            
            ad, soyad = parse_ad_soyad(row.get('Adı Soyadı'))
            
            if not ad:
                click.echo(f"  ❌ Hata (ad yok): Satır {idx + 2}")
                errors += 1
                continue
            
            cikis_tarihi = parse_date(row.get('Çıkış Tarihi'))
            cikis_sebebi = row.get('Çıkış Sebebi')
            
            if cikis_tarihi or (pd.notna(cikis_sebebi) and cikis_sebebi != 0):
                durum = CalisanDurumu.AYRILDI
            else:
                durum = CalisanDurumu.AKTIF
            
            sgk_dosya = find_sgk_dosya(row.get('Firma Ünvanı'))
            departman = find_departman(row.get('Departman adı'))
            
            calisan_data = {
                'sicil_no': str(row.get('Personel Kodu', '')).strip() if pd.notna(row.get('Personel Kodu')) else None,
                'tc_kimlik': tc_kimlik,
                'ad': ad,
                'soyad': soyad or '',
                'telefon': clean_phone(row.get('Personel Mobil Telno')),
                'email': str(row.get('E-Posta Adresi', '')).strip() if pd.notna(row.get('E-Posta Adresi')) else None,
                'dogum_tarihi': parse_date(row.get('Doğum Tarihi')),
                'cinsiyet': parse_cinsiyet(row.get('Cinsiyeti')),
                'adres': str(row.get('Adres', '')).strip() if pd.notna(row.get('Adres')) else None,
                'ise_baslama': parse_date(row.get('Giriş Tarihi')),
                'isten_ayrilma': cikis_tarihi,
                'ayrilma_nedeni': str(row.get('Çıkış Nedeni', '')).strip() if pd.notna(row.get('Çıkış Nedeni')) else None,
                'kidem_tarihi': parse_date(row.get('Kıdem tarihi')),
                'egitim_durumu': str(row.get('Tahsili', '')).strip() if pd.notna(row.get('Tahsili')) else None,
                'is_grubu': str(row.get('İş Grup Adı', '')).strip() if pd.notna(row.get('İş Grup Adı')) else None,
                'yemek_karti': str(row.get('Yemek Kartı', '')).strip() if pd.notna(row.get('Yemek Kartı')) else None,
                'beden': str(row.get('Bedeni', '')).strip().upper() if pd.notna(row.get('Bedeni')) else None,
                'kargo_subesi': str(row.get('Kargo Şubesi', '')).strip() if pd.notna(row.get('Kargo Şubesi')) else None,
                'durum': durum,
                'sgk_dosya_id': sgk_dosya.id if sgk_dosya else None,
                'departman_id': departman.id if departman else None,
            }
            
            if dry_run:
                click.echo(f"  ✅ {ad} {soyad} - {tc_kimlik} (DRY RUN)")
            else:
                calisan = Calisan(**calisan_data)
                db.session.add(calisan)
                click.echo(f"  ✅ {ad} {soyad} - {tc_kimlik}")
            
            created += 1
            
        except Exception as e:
            click.echo(f"  ❌ Hata: Satır {idx + 2} - {e}", err=True)
            errors += 1
    
    if not dry_run:
        db.session.commit()
    
    click.echo("\n" + "=" * 50)
    click.echo(f"✅ Oluşturulan: {created}")
    click.echo(f"⏭️  Atlanan: {skipped}")
    click.echo(f"❌ Hata: {errors}")
    
    if dry_run:
        click.echo("\n⚠️  DRY RUN - Gerçek kayıt için --dry-run olmadan çalıştırın")


def init_app(app):
    """CLI command'ı uygulamaya ekle"""
    app.cli.add_command(import_calisanlar)
