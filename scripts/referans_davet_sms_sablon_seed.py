# -*- coding: utf-8 -*-
"""REFERANS_DAVET_SMS bildirim şablonunu oluştur (idempotent).

"Arkadaşını Davet Et" kampanyasında projedeki aktif çalışanlara toplu
gönderilen referans formu daveti SMS'inin metni.

Şablon gövdesi DB'de (BildirimSablonu) tutulur; bu betik yoksa oluşturur, varsa
dokunmaz (admin özelleştirmelerini ezmemek için).

Kullanılabilir değişkenler: {ad_soyad}, {referans_link}, {proje}

SMS metni gönderim anında ASCII'ye çevrilir; yine de tek segmentte (160
karakter) kalması için metni kısa tutun — Türkçe karakter kullanmayın.

Çalıştırma (production):
  docker compose -f docker-compose.prod.yml exec web bash -c \
    "cd /app && PYTHONPATH=/app python3 scripts/referans_davet_sms_sablon_seed.py"
"""
from app import create_app, db
from app.models.bildirim import BildirimSablonu

KOD = 'REFERANS_DAVET_SMS'

# SMS şablonlarında konu kullanılmaz; kolon NOT NULL olduğu için doldurulur.
KONU = 'Referans Daveti SMS'

ICERIK = 'TG - Arkadasini davet et, birlikte calismaya baslayin: {referans_link}'


def seed():
    mevcut = BildirimSablonu.query.filter_by(kod=KOD).first()
    if mevcut:
        print(f'{KOD} şablonu zaten mevcut (id={mevcut.id}). Değişiklik yapılmadı.')
        return

    sablon = BildirimSablonu(
        kod=KOD,
        ad='Referans Daveti (SMS)',
        aciklama='Arkadaşını Davet Et kampanyasında projedeki aktif çalışanlara '
                 'gönderilen referans formu daveti SMS metni. '
                 'Değişkenler: {ad_soyad}, {referans_link}, {proje}',
        konu_sablonu=KONU,
        icerik_sablonu=ICERIK,
        alicilar=[],
        dinamik_alici_rolu=None,
        proje_yoneticisine_gonder=False,
        aktif=True,
    )
    db.session.add(sablon)
    db.session.commit()
    print(f'✓ {KOD} şablonu oluşturuldu (id={sablon.id}).')
    print(f'  Metin: {ICERIK}')
    print('  Not: Metni "Ayarlar → Bildirim Şablonları" üzerinden düzenleyebilirsiniz. '
          'SMS maliyeti için 160 ASCII karakteri aşmayın.')


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed()
