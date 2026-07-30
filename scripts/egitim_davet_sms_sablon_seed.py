# -*- coding: utf-8 -*-
"""EGITIM_DAVET_SMS bildirim şablonunu oluştur (idempotent).

Aday onaylandığında (ve eğitim detayından manuel toplu gönderimde),
projesinde uygun bir "yeni işe giriş" eğitimi varsa gönderilen kayıt
daveti SMS'inin metni.

Şablon gövdesi DB'de (BildirimSablonu) tutulur; bu betik yoksa oluşturur, varsa
dokunmaz (admin özelleştirmelerini ezmemek için).

Kullanılabilir değişkenler: {ad_soyad}, {egitim_link}, {egitim_adi}

SMS metni gönderim anında ASCII'ye çevrilir; yine de tek segmentte (160
karakter) kalması için metni kısa tutun — Türkçe karakter kullanmayın.

Çalıştırma (production):
  docker compose -f docker-compose.prod.yml exec web bash -c \
    "cd /app && PYTHONPATH=/app python3 scripts/egitim_davet_sms_sablon_seed.py"
"""
from app import create_app, db
from app.models.bildirim import BildirimSablonu

KOD = 'EGITIM_DAVET_SMS'

# SMS şablonlarında konu kullanılmaz; kolon NOT NULL olduğu için doldurulur.
KONU = 'Eğitim Daveti SMS'

ICERIK = 'TG - Ise giris egitiminize kayit olun: {egitim_link}'


def seed():
    mevcut = BildirimSablonu.query.filter_by(kod=KOD).first()
    if mevcut:
        print(f'{KOD} şablonu zaten mevcut (id={mevcut.id}). Değişiklik yapılmadı.')
        return

    sablon = BildirimSablonu(
        kod=KOD,
        ad='Eğitim Daveti (SMS)',
        aciklama='Aday onaylandığında (ve eğitim detayından manuel toplu gönderimde), '
                 'projesinde uygun bir yeni işe giriş eğitimi varsa gönderilen kayıt '
                 'daveti SMS metni. Değişkenler: {ad_soyad}, {egitim_link}, {egitim_adi}',
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
