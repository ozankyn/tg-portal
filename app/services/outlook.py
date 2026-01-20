# -*- coding: utf-8 -*-
"""
TG Portal - Microsoft Outlook Entegrasyonu
Microsoft Graph API ile takvim senkronizasyonu
"""
import os
import requests
from datetime import datetime, timedelta
from flask import url_for, current_app


class OutlookService:
    """Microsoft Graph API servisi"""

    AUTHORITY = "https://login.microsoftonline.com"
    GRAPH_URL = "https://graph.microsoft.com/v1.0"
    SCOPES = ["Calendars.ReadWrite", "User.Read", "offline_access"]

    @classmethod
    def get_client_id(cls):
        return os.environ.get('MICROSOFT_CLIENT_ID')

    @classmethod
    def get_client_secret(cls):
        return os.environ.get('MICROSOFT_CLIENT_SECRET')

    @classmethod
    def get_tenant_id(cls):
        return os.environ.get('MICROSOFT_TENANT_ID', 'common')

    @classmethod
    def get_auth_url(cls, redirect_uri, state=None):
        """OAuth yetkilendirme URL'si oluştur"""
        params = {
            'client_id': cls.get_client_id(),
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'response_mode': 'query',
            'scope': ' '.join(cls.SCOPES),
            'state': state or 'tgportal'
        }

        query = '&'.join(f"{k}={v}" for k, v in params.items())
        return f"{cls.AUTHORITY}/{cls.get_tenant_id()}/oauth2/v2.0/authorize?{query}"

    @classmethod
    def get_token_from_code(cls, code, redirect_uri):
        """Authorization code ile token al"""
        token_url = f"{cls.AUTHORITY}/{cls.get_tenant_id()}/oauth2/v2.0/token"

        data = {
            'client_id': cls.get_client_id(),
            'client_secret': cls.get_client_secret(),
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
            'scope': ' '.join(cls.SCOPES)
        }

        response = requests.post(token_url, data=data)

        if response.status_code == 200:
            token_data = response.json()
            return {
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in', 3600)
            }
        else:
            return None

    @classmethod
    def refresh_token(cls, refresh_token):
        """Refresh token ile yeni access token al"""
        token_url = f"{cls.AUTHORITY}/{cls.get_tenant_id()}/oauth2/v2.0/token"

        data = {
            'client_id': cls.get_client_id(),
            'client_secret': cls.get_client_secret(),
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
            'scope': ' '.join(cls.SCOPES)
        }

        response = requests.post(token_url, data=data)

        if response.status_code == 200:
            token_data = response.json()
            return {
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in', 3600)
            }
        else:
            return None

    @classmethod
    def get_user_info(cls, access_token):
        """Kullanıcı bilgilerini al"""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f"{cls.GRAPH_URL}/me", headers=headers)

        if response.status_code == 200:
            return response.json()
        return None

    @classmethod
    def get_calendar_events(cls, access_token, start_date=None, end_date=None):
        """Takvim etkinliklerini al"""
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Prefer': 'outlook.timezone="Europe/Istanbul"'
        }

        params = {
            'startDateTime': start_date.isoformat(),
            'endDateTime': end_date.isoformat(),
            '$orderby': 'start/dateTime',
            '$top': 100
        }

        response = requests.get(
            f"{cls.GRAPH_URL}/me/calendarView",
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            return response.json().get('value', [])
        return []

    @classmethod
    def create_event(cls, access_token, event_data):
        """Outlook'ta etkinlik oluştur"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        outlook_event = {
            'subject': event_data.get('baslik'),
            'body': {
                'contentType': 'text',
                'content': event_data.get('aciklama', '')
            },
            'start': {
                'dateTime': event_data.get('baslangic').isoformat(),
                'timeZone': 'Europe/Istanbul'
            },
            'end': {
                'dateTime': event_data.get('bitis').isoformat() if event_data.get('bitis') else (event_data.get('baslangic') + timedelta(hours=1)).isoformat(),
                'timeZone': 'Europe/Istanbul'
            },
            'isAllDay': event_data.get('tum_gun', False)
        }

        if event_data.get('konum'):
            outlook_event['location'] = {'displayName': event_data.get('konum')}

        if event_data.get('hatirlatma'):
            outlook_event['reminderMinutesBeforeStart'] = event_data.get('hatirlatma')

        response = requests.post(
            f"{cls.GRAPH_URL}/me/events",
            headers=headers,
            json=outlook_event
        )

        if response.status_code == 201:
            return response.json()
        return None

    @classmethod
    def update_event(cls, access_token, event_id, event_data):
        """Outlook'taki etkinliği güncelle"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        outlook_event = {
            'subject': event_data.get('baslik'),
            'body': {
                'contentType': 'text',
                'content': event_data.get('aciklama', '')
            },
            'start': {
                'dateTime': event_data.get('baslangic').isoformat(),
                'timeZone': 'Europe/Istanbul'
            },
            'end': {
                'dateTime': event_data.get('bitis').isoformat() if event_data.get('bitis') else (event_data.get('baslangic') + timedelta(hours=1)).isoformat(),
                'timeZone': 'Europe/Istanbul'
            },
            'isAllDay': event_data.get('tum_gun', False)
        }

        if event_data.get('konum'):
            outlook_event['location'] = {'displayName': event_data.get('konum')}

        response = requests.patch(
            f"{cls.GRAPH_URL}/me/events/{event_id}",
            headers=headers,
            json=outlook_event
        )

        if response.status_code == 200:
            return response.json()
        return None

    @classmethod
    def delete_event(cls, access_token, event_id):
        """Outlook'taki etkinliği sil"""
        headers = {'Authorization': f'Bearer {access_token}'}

        response = requests.delete(
            f"{cls.GRAPH_URL}/me/events/{event_id}",
            headers=headers
        )

        return response.status_code == 204
