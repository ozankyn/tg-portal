# -*- coding: utf-8 -*-
"""İşten Çıkış (ISTEN_CIKIS) mail şablonunun etiketlerini güncelle.

Neden: İşten çıkış mailinde:
  - "Çıkış Tarihi" etiketi aslında personelin SON İŞ GÜNÜ'nü (SGK çıkış tarihi)
    gösterir -> "SGK Çıkış Tarihi" olarak netleştirilir.
  - Mailin gönderildiği gün ayrı bir satır olarak eklenir ({bildirim_tarihi}).

Şablon gövdesi DB'de (BildirimSablonu.icerik_sablonu) tutulduğu ve admin
tarafından özelleştirilebildiği için bu betik:
  - {cikis_tarihi} placeholder'ını içeren satırı bulur,
  - o satırdaki "Çıkış Tarihi" etiketini "SGK Çıkış Tarihi" yapar,
  - hemen ardına aynı formatta bir "Bildirim Tarihi" satırı ekler.
İdempotenttir: {bildirim_tarihi} zaten varsa değişiklik yapmaz.

Çalıştırma (production):
  docker compose -f docker-compose.prod.yml exec web bash -c \
    "cd /app && PYTHONPATH=/app python3 scripts/isten_cikis_sablon_guncelle.py"

Ön izleme (yazmadan sadece göster):
  ... python3 scripts/isten_cikis_sablon_guncelle.py --dry-run
"""
import sys

from app import create_app, db
from app.models.bildirim import BildirimSablonu

DRY_RUN = '--dry-run' in sys.argv


def guncelle():
    sablon = BildirimSablonu.query.filter_by(kod='ISTEN_CIKIS').first()
    if not sablon:
        print('ISTEN_CIKIS şablonu bulunamadı. (Önce şablonlar oluşturulmalı.)')
        return

    icerik = sablon.icerik_sablonu or ''

    if '{cikis_tarihi}' not in icerik:
        print('UYARI: Şablonda {cikis_tarihi} placeholder’ı yok. '
              'Etiket düzeni beklenenden farklı; manuel düzenleme gerekli.')
        print('--- Mevcut gövde ---')
        print(icerik)
        return

    if '{bildirim_tarihi}' in icerik:
        print('Şablon zaten güncel ({bildirim_tarihi} mevcut). Değişiklik yapılmadı.')
        return

    lines = icerik.splitlines(keepends=True)
    yeni_lines = []
    eklendi = False
    for line in lines:
        if '{cikis_tarihi}' in line:
            # 1) Etiketi netleştir (çift uygulama olmasın diye kontrollü)
            if 'SGK Çıkış Tarihi' not in line:
                line = line.replace('Çıkış Tarihi', 'SGK Çıkış Tarihi')
            yeni_lines.append(line)
            # 2) Aynı formatta "Bildirim Tarihi" satırı ekle
            bildirim_line = line.replace('{cikis_tarihi}', '{bildirim_tarihi}')
            bildirim_line = bildirim_line.replace('SGK Çıkış Tarihi', 'Bildirim Tarihi')
            yeni_lines.append(bildirim_line)
            eklendi = True
        else:
            yeni_lines.append(line)

    yeni_icerik = ''.join(yeni_lines)

    print('--- ESKİ ---')
    print(icerik)
    print('\n--- YENİ ---')
    print(yeni_icerik)

    if not eklendi:
        print('\nSatır bulunamadı, değişiklik yapılmadı.')
        return

    if DRY_RUN:
        print('\n[dry-run] Yazılmadı.')
        return

    sablon.icerik_sablonu = yeni_icerik
    db.session.commit()
    print('\n✓ ISTEN_CIKIS şablonu güncellendi.')


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        guncelle()
