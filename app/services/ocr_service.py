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

# Dosya imzası (magic bytes) -> media_type
# Uzantıya güvenilmez; gerçek format dosya içeriğinden tespit edilir.
# Anthropic API'nin desteklediği tipler: jpeg, png, gif, webp, pdf.
def tespit_media_type(data):
    """Dosya içeriğinden gerçek MIME tipini bulur.

    Args:
        data: Dosyanın ham byte içeriği (bytes).

    Returns:
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf' veya tanınmazsa None.
    """
    if not data or len(data) < 12:
        return None

    # JPEG: FF D8 FF
    if data[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'

    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'

    # GIF: "GIF87a" veya "GIF89a"
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return 'image/gif'

    # WEBP: "RIFF" + 4 byte boyut + "WEBP"
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'

    # PDF: "%PDF"
    if data[:4] == b'%PDF':
        return 'application/pdf'

    return None


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
    """Dosya yolundan Anthropic content bloğu (image veya document) üretir.

    Dosya tipi uzantıdan değil, içerikten (magic bytes) tespit edilir.
    """
    with open(image_path, 'rb') as f:
        ham = f.read()

    media_type = tespit_media_type(ham)
    if not media_type:
        raise ValueError(f"Desteklenmeyen veya tanınmayan dosya tipi: {image_path}")

    data = base64.standard_b64encode(ham).decode('utf-8')

    if media_type == 'application/pdf':
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": data,
            },
        }

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
        image_path: Okunacak dosyanın tam yolu. Format dosya içeriğinden
            tespit edilir (jpeg/png/gif/webp/pdf); uzantı dikkate alınmaz.

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
