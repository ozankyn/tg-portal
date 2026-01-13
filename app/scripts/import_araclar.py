# -*- coding: utf-8 -*-
"""
Araç Excel Import Script
Kullanım: docker-compose exec web flask import-araclar /app/araclar.xlsx
"""

import click
import pandas as pd
from datetime import datetime
from flask.cli import with_appcontext
from app import db
from app.models.filo import Arac
from app.models.ik import Calisan
from app.models.proje import Proje
from app.models.tedarikci import Tedarikci
from app.models.base import AracDurumu, YakitTipi


def parse_yakit_tipi(yakit):
    """Yakıt tipi dönüştür"""
    if not yakit or pd.isna(yakit):
        return YakitTipi.DIZEL
    y = str(yakit).lower().strip()
    mapping = {
        'benzin': YakitTipi.BENZIN,
        'dizel': YakitTipi.DIZEL,
        'diesel': YakitTipi.DIZEL,
        'lpg': YakitTipi.LPG,
        'elektrik': YakitTipi.ELEKTRIK,
        'hibrit': YakitTipi.HIBRIT,
        'hybrid': YakitTipi.HIBRIT,
    }
    return mapping.get(y, YakitTipi.DIZEL)


def parse_sahiplik(sahiplik):
    """Sahiplik tipi dönüştür"""
    if not sahiplik or pd.isna(sahiplik):
        return 'sirket'
    s = str(sahiplik).lower().strip()
    if 'kira' in s:
        return 'kiralama'
    elif 'leasing' in s:
        return 'leasing'
    return 'sirket'


def clean_plaka(plaka):
    """Plaka temizle"""
    if not plaka or pd.isna(plaka):
        return None
    return str(plaka).strip().upper().replace(' ', '')


def find_calisan(ad_soyad):
    """Çalışan bul"""
    if not ad_soyad or pd.isna(ad_soyad):
        return None
    
    parts = str(ad_soyad).strip().split()
    if len(parts) < 2:
        return Calisan.query.filter(
            Calisan.ad.ilike(parts[0]),
            Calisan.is_deleted == False
        ).first()
    
    ad = ' '.join(parts[:-1])
    soyad = parts[-1]
    
    return Calisan.query.filter(
        Calisan.ad.ilike(ad),
        Calisan.soyad.ilike(soyad),
        Calisan.is_deleted == False
    ).first()


def find_proje(proje_adi):
    """Proje bul"""
    if not proje_adi or pd.isna(proje_adi):
        return None
    
    return Proje.query.filter(
        Proje.ad.ilike(str(proje_adi).strip()),
        Proje.is_deleted == False
    ).first()


def find_tedarikci(tedarikci_adi):
    """Tedarikçi bul"""
    if not tedarikci_adi or pd.isna(tedarikci_adi):
        return None
    
    return Tedarikci.query.filter(
        Tedarikci.ad.ilike(str(tedarikci_adi).strip()),
        Tedarikci.is_deleted == False
    ).first()


@click.command('import-araclar')
@click.argument('filepath')
@click.option('--dry-run', is_flag=True, help='Gerçek kayıt yapmadan test et')
@click.option('--skip-existing', is_flag=True, default=True, help='Plaka varsa atla')
@with_appcontext
def import_araclar(filepath, dry_run, skip_existing):
    """Excel'den araç import et"""
    
    click.echo(f"Dosya okunuyor: {filepath}")
    
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        click.echo(f"Hata: Dosya okunamadı - {e}", err=True)
        return
    
    click.echo(f"Toplam satır: {len(df)}")
    click.echo(f"Kolonlar: {', '.join(df.columns.tolist())}")
    
    if dry_run:
        click.echo("⚠️  DRY RUN - Kayıt yapılmayacak")
    
    created = 0
    skipped = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            plaka = clean_plaka(row.get('Plaka'))
            
            if not plaka:
                click.echo(f"  ❌ Hata (plaka yok): Satır {idx + 2}")
                errors += 1
                continue
            
            # Plaka kontrolü
            if skip_existing:
                existing = Arac.query.filter_by(plaka=plaka, is_deleted=False).first()
                if existing:
                    click.echo(f"  ⏭️  Atlandı (plaka mevcut): {plaka}")
                    skipped += 1
                    continue
            
            # İlişkili verileri bul
            calisan = find_calisan(row.get('Atanmış Personel') or row.get('Personel') or row.get('Atanan'))
            proje = find_proje(row.get('Proje'))
            tedarikci = find_tedarikci(row.get('Tedarikçi') or row.get('Kiralama Firması'))
            
            arac_data = {
                'plaka': plaka,
                'marka': str(row.get('Marka', '')).strip() if pd.notna(row.get('Marka')) else None,
                'model': str(row.get('Model', '')).strip() if pd.notna(row.get('Model')) else None,
                'model_yili': int(row.get('Model Yılı')) if pd.notna(row.get('Model Yılı')) else None,
                'renk': str(row.get('Renk', '')).strip() if pd.notna(row.get('Renk')) else None,
                'sasi_no': str(row.get('Şasi No', '')).strip() if pd.notna(row.get('Şasi No')) else None,
                'motor_no': str(row.get('Motor No', '')).strip() if pd.notna(row.get('Motor No')) else None,
                'yakit_tipi': parse_yakit_tipi(row.get('Yakıt Tipi') or row.get('Yakıt')),
                'km': int(row.get('KM', 0)) if pd.notna(row.get('KM')) else 0,
                'sahiplik_tipi': parse_sahiplik(row.get('Sahiplik') or row.get('Sahiplik Tipi')),
                'aylik_kira': float(row.get('Aylık Kira') or row.get('Kira Tutarı') or 0) if pd.notna(row.get('Aylık Kira') or row.get('Kira Tutarı')) else None,
                'durum': AracDurumu.AKTIF,
                'atanan_calisan_id': calisan.id if calisan else None,
                'proje_id': proje.id if proje else None,
            }
            
            if dry_run:
                click.echo(f"  ✅ {plaka} - {arac_data['marka']} {arac_data['model']} (DRY RUN)")
                if calisan:
                    click.echo(f"      → Personel: {calisan.full_name}")
                if proje:
                    click.echo(f"      → Proje: {proje.ad}")
            else:
                arac = Arac(**arac_data)
                db.session.add(arac)
                click.echo(f"  ✅ {plaka} - {arac_data['marka']} {arac_data['model']}")
            
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
    app.cli.add_command(import_araclar)
