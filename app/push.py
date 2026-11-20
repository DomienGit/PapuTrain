"""Wysyłka powiadomień Web Push (req 31).

Serwer szyfruje krótką wiadomość kluczami urządzenia i oddaje ją usłudze push
przeglądarki (Chrome na Androidzie = FCM Google), a ta dostarcza ją do telefonu —
także przy zamkniętej aplikacji. Na telefonie odbiera ją service worker (sw.js).

Zasada: powiadomienie to dodatek. Każdy błąd wysyłki tylko logujemy — nigdy nie
psuje głównej operacji (np. zapisu wygenerowanego planu).
"""

import json
import logging
from urllib.parse import urlparse

from pywebpush import WebPushException, webpush
from sqlmodel import Session, select

from app.config import settings
from app.models import PushSubscription

log = logging.getLogger(__name__)

# Serwer wysyła żądania pod adres podany przez przeglądarkę — dopuszczamy tylko
# znane usługi push, żeby nikt nie kazał serwerowi łączyć się z dowolnym adresem.
ALLOWED_PUSH_HOSTS = (
    "fcm.googleapis.com",  # Chrome / Android
    "updates.push.services.mozilla.com",  # Firefox
    "push.services.mozilla.com",
    "web.push.apple.com",  # Safari / iPhone
    "notify.windows.com",  # Edge na Windows
)


def is_allowed_endpoint(endpoint: str) -> bool:
    url = urlparse(endpoint)
    host = url.hostname or ""
    return url.scheme == "https" and any(
        host == allowed or host.endswith("." + allowed) for allowed in ALLOWED_PUSH_HOSTS
    )


def push_enabled() -> bool:
    return bool(settings.vapid_public_key and settings.vapid_private_key)


def notify_user(session: Session, user_id: int, title: str, body: str, url: str = "/") -> int:
    """Wysyła powiadomienie na wszystkie urządzenia użytkownika. Zwraca, ile doszło."""
    if not push_enabled():
        return 0
    subscriptions = session.exec(
        select(PushSubscription).where(PushSubscription.user_id == user_id)  # type: ignore[arg-type]
    ).all()
    payload = json.dumps({"title": title, "body": body, "url": url})
    sent = 0
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
                timeout=10,
                ttl=24 * 3600,  # telefon offline? usługa push trzyma wiadomość dobę
            )
            sent += 1
        except WebPushException as err:
            status = err.response.status_code if err.response is not None else None
            if status in (404, 410):
                # 404/410 = subskrypcja wygasła (np. odinstalowana aplikacja) — sprzątamy.
                log.info("Push: subskrypcja %s wygasła — usuwam", sub.id)
                session.delete(sub)
            else:
                log.warning("Push: błąd wysyłki do subskrypcji %s (HTTP %s)", sub.id, status)
        except Exception:  # noqa: BLE001 — powiadomienie nie może wywrócić żądania
            log.exception("Push: nieoczekiwany błąd wysyłki do subskrypcji %s", sub.id)
    session.commit()
    return sent
