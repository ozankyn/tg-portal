import os

# Twilio SMS Ayarları
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

UPLOAD_FOLDER = '/app/uploads'
# Şirket Ayarları
COMPANY_NAME = os.environ.get('COMPANY_NAME', 'TG PORTAL')
COMPANY_SUBTITLE = os.environ.get('COMPANY_SUBTITLE', 'ERP Sistemi')
COMPANY_LOGO = os.environ.get('COMPANY_LOGO', 'logo.png')  # örn: 'logo.png' - static/images/ klasöründe olmalı
