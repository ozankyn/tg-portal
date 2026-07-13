# -*- coding: utf-8 -*-
"""SGK_CIKIS_YAPILDI bildirim şablonunu oluştur (idempotent).

İşten ayrılan personelin SGK çıkışı yapılıp çıkış bildirgesi yüklendiğinde
İK/Bordro ekibine gönderilen bilgilendirme mailinin şablonu.

Şablon gövdesi DB'de (BildirimSablonu) tutulur; bu betik yoksa oluşturur, varsa
dokunmaz (admin özelleştirmelerini ezmemek için).

Çalıştırma (production):
  docker compose -f docker-compose.prod.yml exec web bash -c \
    "cd /app && PYTHONPATH=/app python3 scripts/sgk_cikis_yapildi_sablon_seed.py"
"""
from app import create_app, db
from app.models.bildirim import BildirimSablonu

KOD = 'SGK_CIKIS_YAPILDI'

KONU = 'SGK Çıkışı Yapıldı - {ad_soyad}'

ICERIK = """<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #111418;">
  <h2 style="color: #dc2626;">SGK Çıkışı Yapıldı</h2>
  <p>Aşağıdaki personel için SGK çıkışı yapılmış ve çıkış bildirgesi sisteme yüklenmiştir.</p>
  <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
    <tr><td style="padding: 6px 0; color: #6b7280;">Ad Soyad</td><td style="padding: 6px 0; font-weight: bold;">{ad_soyad}</td></tr>
    <tr><td style="padding: 6px 0; color: #6b7280;">TC Kimlik</td><td style="padding: 6px 0;">{tc_kimlik}</td></tr>
    <tr><td style="padding: 6px 0; color: #6b7280;">Proje</td><td style="padding: 6px 0;">{proje}</td></tr>
    <tr><td style="padding: 6px 0; color: #6b7280;">Pozisyon</td><td style="padding: 6px 0;">{pozisyon}</td></tr>
    <tr><td style="padding: 6px 0; color: #6b7280;">SGK Çıkış Tarihi (son iş günü)</td><td style="padding: 6px 0; font-weight: bold;">{sgk_cikis_tarihi}</td></tr>
    <tr><td style="padding: 6px 0; color: #6b7280;">Çıkış Nedeni</td><td style="padding: 6px 0;">{cikis_nedeni}</td></tr>
    <tr><td style="padding: 6px 0; color: #6b7280;">SGK Çıkış Kodu</td><td style="padding: 6px 0;">{sgk_cikis_kodu}</td></tr>
    <tr><td style="padding: 6px 0; color: #6b7280;">Bildirge Yükleyen</td><td style="padding: 6px 0;">{yukleyen}</td></tr>
    <tr><td style="padding: 6px 0; color: #6b7280;">Bildirim Tarihi</td><td style="padding: 6px 0;">{bildirim_tarihi}</td></tr>
  </table>
  <p><a href="{calisan_url}" style="background: #137fec; color: white; padding: 10px 22px; text-decoration: none; border-radius: 6px; font-weight: bold;">Çalışan Kaydını Aç</a></p>
</div>"""


def seed():
    mevcut = BildirimSablonu.query.filter_by(kod=KOD).first()
    if mevcut:
        print(f'{KOD} şablonu zaten mevcut (id={mevcut.id}). Değişiklik yapılmadı.')
        return

    sablon = BildirimSablonu(
        kod=KOD,
        ad='SGK Çıkışı Yapıldı',
        aciklama='SGK çıkışı yapılıp çıkış bildirgesi yüklendiğinde İK/Bordro ekibine gönderilir.',
        konu_sablonu=KONU,
        icerik_sablonu=ICERIK,
        alicilar=[],
        dinamik_alici_rolu='ik.view',
        proje_yoneticisine_gonder=False,
        aktif=True,
    )
    db.session.add(sablon)
    db.session.commit()
    print(f'✓ {KOD} şablonu oluşturuldu (id={sablon.id}).')
    print('  Not: Alıcılar için "Ayarlar → Bildirim Şablonları" üzerinden sabit '
          'e-posta ekleyebilir veya dinamik alıcı rolünü düzenleyebilirsiniz.')


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed()
