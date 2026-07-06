# -*- coding: utf-8 -*-
"""
TG Portal - OCR Servisi (Anthropic Claude)

Görsel/PDF belgelerden IBAN numarası okuma.
API anahtarı .env'den ANTHROPIC_API_KEY olarak alınır (app.config üzerinden).
"""

import os
import re
import base64
import logging

from flask import current_app

logger = logging.getLogger(__name__)

# Ucuz ve hızlı model - değiştirmek için tek yer.
IBAN_OCR_MODEL = "claude-sonnet-4-6"

# TR IBAN: TR + 24 rakam = toplam 26 karakter
IBAN_PROMPT = (
    "Bu görseldeki IBAN numarasını bul ve sadece IBAN'ı döndür. "
    "Format: TRXX XXXX XXXX XXXX XXXX XXXX XX. "
    "IBAN bulunamadıysa 'YOK' döndür."
)

# Desteklenen görsel uzantı -> media_type
_IMAGE_MIME = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'webp': 'image/webp',
}


def normalize_iban(text):
    """AI yanıtından TR IBAN'ı ayıklar ve doğrular.

    - Boşlukları temizler, büyük harfe çevirir.
    - TR ile başlayıp toplam 26 karakter (TR + 24 rakam) kontrolü yapar.

    Returns: 'TR' + 24 hane string, veya bulunamazsa None.
    """
    if not text:
        return None

    # Tüm boşluk/newline temizle, büyük harf
    temiz = re.sub(r'\s+', '', text).upper()

    if temiz == 'YOK' or not temiz:
        return None

    # Metin içinde TR + 24 rakam kalıbını ara
    m = re.search(r'TR\d{24}', temiz)
    if not m:
        return None

    iban = m.group(0)
    # TR + 24 rakam = 26 karakter kontrolü
    if len(iban) != 26 or not iban.startswith('TR'):
        return None

    return iban


def _dosya_bloklari(image_path):
    """Dosya yolundan Anthropic content bloğu (image veya document) üretir."""
    ext = image_path.rsplit('.', 1)[1].lower() if '.' in image_path else ''

    with open(image_path, 'rb') as f:
        data = base64.standard_b64encode(f.read()).decode('utf-8')

    if ext == 'pdf':
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": data,
            },
        }

    media_type = _IMAGE_MIME.get(ext)
    if not media_type:
        raise ValueError(f"Desteklenmeyen dosya tipi: .{ext}")

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": data,
        },
    }


def extract_iban_from_image(image_path):
    """Görsel/PDF dosyasından IBAN numarasını okur.

    Args:
        image_path: Okunacak dosyanın tam yolu (jpg/png/gif/webp/pdf).

    Returns:
        'TR' + 24 hane IBAN string, veya bulunamazsa/hata olursa None.
    """
    import anthropic

    api_key = current_app.config.get('ANTHROPIC_API_KEY')
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY tanımlı değil - IBAN okuma atlandı.")
        return None

    if not image_path or not os.path.exists(image_path):
        logger.warning("IBAN okuma: dosya bulunamadı: %s", image_path)
        return None

    try:
        icerik_blok = _dosya_bloklari(image_path)
    except ValueError as e:
        logger.info("IBAN okuma: %s", e)
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=IBAN_OCR_MODEL,
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": [
                    icerik_blok,
                    {"type": "text", "text": IBAN_PROMPT},
                ],
            }],
        )
        yanit = (message.content[0].text or '').strip()
        return normalize_iban(yanit)
    except Exception as e:
        logger.error("IBAN okuma hatası (%s): %s", image_path, e)
        return None
