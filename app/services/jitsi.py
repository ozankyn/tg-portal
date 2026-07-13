# -*- coding: utf-8 -*-
"""
TG Portal - Jitsi Meet Entegrasyonu
JWT token üretimi ve meeting yönetimi
"""

import jwt
import time
from flask import current_app


class JitsiService:
    """Jitsi Meet servisi"""

    # Ayarlar - config'den alınacak
    JITSI_DOMAIN = "meet.teamguerilla.com"
    APP_ID = "tgportal"
    APP_SECRET = "TgPortalJitsi2025!SecretKey"

    @classmethod
    def generate_token(cls, user, room_name, is_moderator=False, expires_in=3600):
        """
        Kullanıcı için JWT token üret

        Args:
            user: User veya Calisan objesi (name, email özellikleri olmalı)
            room_name: Oda adı (URL-safe olmalı)
            is_moderator: Moderatör yetkisi
            expires_in: Token geçerlilik süresi (saniye)

        Returns:
            str: JWT token
        """
        # Kullanıcı bilgilerini al
        if hasattr(user, 'full_name'):
            name = user.full_name
        elif hasattr(user, 'first_name'):
            name = f"{user.first_name} {user.last_name}".strip()
        else:
            name = str(user)

        email = getattr(user, 'email', '')
        avatar = getattr(user, 'avatar_url', '')

        payload = {
            "aud": "jitsi",
            "iss": cls.APP_ID,
            "sub": cls.JITSI_DOMAIN,
            "room": room_name,
            "exp": int(time.time()) + expires_in,
            "context": {
                "user": {
                    "name": name,
                    "email": email,
                    "moderator": is_moderator,
                    "affiliation": "owner" if is_moderator else "member"
                }
            }
        }

        if avatar:
            payload["context"]["user"]["avatar"] = avatar

        token = jwt.encode(payload, cls.APP_SECRET, algorithm="HS256")
        return token

    @classmethod
    def get_meeting_url(cls, room_name, user, is_moderator=False):
        """
        Kullanıcı için meeting URL'i oluştur

        Args:
            room_name: Oda adı
            user: Kullanıcı objesi
            is_moderator: Moderatör mü

        Returns:
            str: Tam meeting URL'i (JWT dahil)
        """
        token = cls.generate_token(user, room_name, is_moderator)
        meeting_url = f"https://{cls.JITSI_DOMAIN}/{room_name}?jwt={token}"

        # Moderatör olmayanlarda "End meeting" (toplantıyı sonlandır) butonu gizlensin.
        # Jitsi URL hash config override ile toolbar'dan 'end-meeting' çıkarılıyor;
        # 'hangup' (ayrıl) listede kalır, 'end-meeting' yer almaz.
        if not is_moderator:
            toolbar_buttons = (
                '["camera","chat","desktop","filmstrip","fullscreen","hangup",'
                '"microphone","participants-pane","profile","raisehand",'
                '"select-background","settings","tileview","toggle-camera","videoquality"]'
            )
            meeting_url += (
                f"#config.toolbarButtons={toolbar_buttons}"
                f"&interfaceConfig.TOOLBAR_BUTTONS={toolbar_buttons}"
                "&interfaceConfig.SHOW_PROMOTIONAL_CLOSE_PAGE=false"
            )

        return meeting_url

    @classmethod
    def create_room_name(cls, prefix, unique_id):
        """
        URL-safe oda adı oluştur

        Args:
            prefix: Ön ek (örn: "egitim", "toplanti")
            unique_id: Benzersiz ID

        Returns:
            str: URL-safe oda adı
        """
        import re
        # Türkçe karakterleri dönüştür
        tr_map = {
            'ç': 'c', 'Ç': 'C', 'ğ': 'g', 'Ğ': 'G',
            'ı': 'i', 'İ': 'I', 'ö': 'o', 'Ö': 'O',
            'ş': 's', 'Ş': 'S', 'ü': 'u', 'Ü': 'U'
        }

        room_name = f"{prefix}_{unique_id}"
        for tr_char, en_char in tr_map.items():
            room_name = room_name.replace(tr_char, en_char)

        # Sadece alfanumerik ve alt çizgi
        room_name = re.sub(r'[^a-zA-Z0-9_]', '', room_name)
        return room_name
