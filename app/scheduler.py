# -*- coding: utf-8 -*-
"""
TG Portal - Zamanlanmis Gorevler (Scheduler)
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import os

scheduler = BackgroundScheduler()


def outlook_otomatik_senkronizasyon(app):
    """Tum kullanicilarin Outlook takvimlerini senkronize et"""
    with app.app_context():
        from app import db
        from app.models.takvim import OutlookEntegrasyon, Etkinlik
        from app.modules.takvim.routes import get_outlook_token, GRAPH_API_ENDPOINT
        import requests as http_requests

        entegrasyonlar = OutlookEntegrasyon.query.filter(
            OutlookEntegrasyon.senkronizasyon_aktif == True,
            OutlookEntegrasyon.refresh_token != None
        ).all()

        print(f"[Scheduler] Outlook senkronizasyonu basliyor - {len(entegrasyonlar)} kullanici")

        for ent in entegrasyonlar:
            try:
                token = get_outlook_token(ent.user_id)
                if not token:
                    print(f"[Scheduler] Kullanici {ent.user_id} icin token alinamadi")
                    continue

                headers = {'Authorization': f'Bearer {token}'}
                start_date = datetime.now().isoformat() + 'Z'
                end_date = (datetime.now() + timedelta(days=30)).isoformat() + 'Z'

                url = f"{GRAPH_API_ENDPOINT}/me/calendarview?startDateTime={start_date}&endDateTime={end_date}"
                response = http_requests.get(url, headers=headers)

                if response.status_code != 200:
                    print(f"[Scheduler] Kullanici {ent.user_id} icin API hatasi: {response.status_code}")
                    continue

                outlook_events = response.json().get('value', [])
                imported_count = 0

                for event in outlook_events:
                    existing = Etkinlik.query.filter_by(
                        outlook_event_id=event['id'],
                        olusturan_id=ent.user_id
                    ).first()

                    if not existing:
                        start = event.get('start', {})
                        end = event.get('end', {})
                        baslangic = datetime.fromisoformat(start['dateTime'].replace('Z', '')) if start.get('dateTime') else datetime.now()
                        bitis = datetime.fromisoformat(end['dateTime'].replace('Z', '')) if end.get('dateTime') else baslangic + timedelta(hours=1)

                        etkinlik = Etkinlik(
                            baslik=event.get('subject', 'Outlook Etkinligi'),
                            aciklama=event.get('bodyPreview', ''),
                            konum=event.get('location', {}).get('displayName', ''),
                            baslangic=baslangic,
                            bitis=bitis,
                            tum_gun=event.get('isAllDay', False),
                            etkinlik_tipi='outlook',
                            renk='#0078d4',
                            olusturan_id=ent.user_id,
                            outlook_event_id=event['id']
                        )
                        db.session.add(etkinlik)
                        imported_count += 1

                ent.son_senkronizasyon = datetime.now()
                db.session.commit()

                if imported_count > 0:
                    print(f"[Scheduler] Kullanici {ent.user_id}: {imported_count} yeni etkinlik eklendi")

            except Exception as e:
                print(f"[Scheduler] Kullanici {ent.user_id} hatasi: {str(e)}")
                continue

        print(f"[Scheduler] Outlook senkronizasyonu tamamlandi")


def init_scheduler(app):
    """Scheduler i baslat"""
    if os.environ.get('FLASK_ENV') == 'production':
        # Her 15 dakikada bir calistir
        scheduler.add_job(
            func=lambda: outlook_otomatik_senkronizasyon(app),
            trigger=IntervalTrigger(minutes=15),
            id='outlook_sync',
            name='Outlook Otomatik Senkronizasyon',
            replace_existing=True
        )

        scheduler.start()
        print("[Scheduler] Outlook otomatik senkronizasyon aktif (her 15 dakika)")
