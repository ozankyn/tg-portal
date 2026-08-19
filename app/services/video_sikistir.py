# -*- coding: utf-8 -*-
"""
TG Portal - Aday Video Sıkıştırma

Yüklenen tanıtım videolarını ffmpeg ile otomatik sıkıştırır:
  - En fazla 720p (uzun kenar 1280, kısa kenar 720) çözünürlüğe indirir
  - ~10MB hedef boyutu aşmayacak bit hızıyla H.264/AAC MP4'e kodlar
  - İşlem başarılıysa orijinal dosyayı siler, AdayMedya kaydını günceller

Sıkıştırma arka plan thread'inde çalışır; yükleme isteği beklemez.
Hata durumunda (ffmpeg yok, bozuk dosya, timeout) orijinal dosya korunur.
"""

import json
import os
import subprocess
import threading

from flask import current_app

HEDEF_BOYUT = 10 * 1024 * 1024      # 10MB
MAX_GENISLIK = 1280
MAX_YUKSEKLIK = 720
SES_BITRATE_K = 96
MIN_VIDEO_BITRATE_K = 300
MAX_VIDEO_BITRATE_K = 2500
FFPROBE_TIMEOUT = 60
FFMPEG_TIMEOUT = 900                # 15 dk


def _video_bilgi(path):
    """ffprobe ile süre/çözünürlük/codec bilgisi döndürür (okunamazsa None)."""
    try:
        sonuc = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height,codec_name',
             '-show_entries', 'format=duration',
             '-of', 'json', path],
            capture_output=True, timeout=FFPROBE_TIMEOUT, check=True,
        )
        veri = json.loads(sonuc.stdout or b'{}')
        akis = (veri.get('streams') or [{}])[0]
        return {
            'sure': float(veri.get('format', {}).get('duration') or 0) or None,
            'genislik': akis.get('width'),
            'yukseklik': akis.get('height'),
            'codec': akis.get('codec_name'),
        }
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as e:
        current_app.logger.warning(f"Video bilgisi okunamadı ({path}): {e}")
        return None


def _sikistirma_gerekli(path, bilgi):
    """Zaten hedefe uygun (mp4/h264, <=720p, <=10MB) videoyu yeniden kodlama."""
    try:
        boyut = os.path.getsize(path)
    except OSError:
        return False

    if boyut > HEDEF_BOYUT:
        return True
    if not bilgi:
        return True
    if (bilgi.get('yukseklik') or 0) > MAX_YUKSEKLIK:
        return True
    if (bilgi.get('genislik') or 0) > MAX_GENISLIK:
        return True
    if bilgi.get('codec') != 'h264' or not path.lower().endswith('.mp4'):
        return True
    return False


def _video_bitrate_k(sure):
    """Hedef boyuta göre video bit hızını (kbps) hesaplar."""
    if not sure or sure <= 0:
        return MAX_VIDEO_BITRATE_K
    # %5 konteyner payı bırak, ses bit hızını düş
    toplam_k = (HEDEF_BOYUT * 8 * 0.95) / sure / 1000
    return int(max(MIN_VIDEO_BITRATE_K, min(MAX_VIDEO_BITRATE_K, toplam_k - SES_BITRATE_K)))


def _ffmpeg_calistir(kaynak, hedef, bitrate_k):
    """ffmpeg ile 720p + hedef bit hızında yeniden kodlar."""
    olcek = (
        f"scale='min({MAX_GENISLIK},iw)':'min({MAX_YUKSEKLIK},ih)'"
        ":force_original_aspect_ratio=decrease,"
        "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    )
    subprocess.run(
        ['ffmpeg', '-y', '-nostdin', '-i', kaynak,
         '-vf', olcek,
         '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '28',
         '-maxrate', f'{bitrate_k}k', '-bufsize', f'{bitrate_k * 2}k',
         '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', f'{SES_BITRATE_K}k', '-ac', '2',
         '-movflags', '+faststart',
         hedef],
        capture_output=True, timeout=FFMPEG_TIMEOUT, check=True,
    )


def _sikistir(medya_id):
    """Tek bir AdayMedya kaydının videosunu sıkıştırır (app context içinde)."""
    from app import db
    from app.models.ik import AdayMedya

    medya = AdayMedya.query.get(medya_id)
    if not medya or medya.tip != 'video' or not medya.dosya_yolu:
        return

    upload_folder = current_app.config['UPLOAD_FOLDER']
    kaynak = os.path.join(upload_folder, medya.dosya_yolu)
    if not os.path.exists(kaynak):
        return

    bilgi = _video_bilgi(kaynak)
    if not _sikistirma_gerekli(kaynak, bilgi):
        current_app.logger.info(f"Video zaten hedefe uygun, sıkıştırılmadı: {medya.dosya_yolu}")
        return

    # Çıktı her zaman .mp4; kaynak zaten .mp4 ise dosya yolu (ve URL) değişmez.
    kok, _ = os.path.splitext(kaynak)
    hedef = f"{kok}.mp4"
    gecici = f"{kok}.gecici.mp4"

    try:
        _ffmpeg_calistir(kaynak, gecici, _video_bitrate_k((bilgi or {}).get('sure')))
    except FileNotFoundError:
        current_app.logger.warning("ffmpeg bulunamadı, video sıkıştırma atlandı.")
        return
    except subprocess.TimeoutExpired:
        current_app.logger.warning(f"Video sıkıştırma zaman aşımına uğradı: {medya.dosya_yolu}")
        _temizle(gecici)
        return
    except subprocess.CalledProcessError as e:
        hata = (e.stderr or b'').decode('utf-8', 'replace')[-500:]
        current_app.logger.warning(f"Video sıkıştırılamadı ({medya.dosya_yolu}): {hata}")
        _temizle(gecici)
        return

    try:
        yeni_boyut = os.path.getsize(gecici)
        eski_boyut = os.path.getsize(kaynak)
    except OSError:
        _temizle(gecici)
        return

    if yeni_boyut <= 0 or yeni_boyut >= eski_boyut:
        # Sıkıştırma kazanç sağlamadıysa orijinali koru
        current_app.logger.info(f"Sıkıştırma kazanç sağlamadı, orijinal korundu: {medya.dosya_yolu}")
        _temizle(gecici)
        return

    # Sıkıştırılmışı yerine koy, orijinali sil
    try:
        os.replace(gecici, hedef)
    except OSError as e:
        current_app.logger.warning(f"Sıkıştırılmış video taşınamadı ({medya.dosya_yolu}): {e}")
        _temizle(gecici)
        return

    if os.path.abspath(kaynak) != os.path.abspath(hedef):
        _temizle(kaynak)

    yeni_rel = os.path.relpath(hedef, upload_folder).replace('\\', '/')
    medya.dosya_yolu = yeni_rel
    medya.dosya_boyut = yeni_boyut
    medya.mime_type = 'video/mp4'
    db.session.commit()

    current_app.logger.info(
        f"Video sıkıştırıldı: {yeni_rel} "
        f"({eski_boyut // 1024}KB -> {yeni_boyut // 1024}KB)"
    )


def _temizle(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError as e:
        current_app.logger.warning(f"Geçici video dosyası silinemedi ({path}): {e}")


def _thread_gorevi(app, medya_id):
    with app.app_context():
        from app import db
        try:
            _sikistir(medya_id)
        except Exception as e:  # thread içinde hiçbir hata sessizce kaybolmasın
            app.logger.error(f"Video sıkıştırma hatası (medya={medya_id}): {e}")
            db.session.rollback()
        finally:
            db.session.remove()


def sikistir_async(medya):
    """Videoyu arka planda sıkıştırmak üzere kuyruğa alır.

    `medya` DB'ye commit edilmiş bir AdayMedya kaydı olmalıdır; thread
    kaydı id ile yeniden okur.
    """
    if not medya or medya.tip != 'video':
        return
    app = current_app._get_current_object()
    threading.Thread(
        target=_thread_gorevi, args=(app, medya.id),
        daemon=True, name=f'video-sikistir-{medya.id}',
    ).start()
