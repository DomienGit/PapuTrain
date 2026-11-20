"""Powiadomienia push (req 31): klucz publiczny, zapis/usunięcie subskrypcji, test.

Frontend pobiera klucz publiczny VAPID, prosi telefon o zgodę i subskrypcję,
a wynik (endpoint + klucze) zapisuje tutaj. Wysyłka: app/push.py.
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.auth import CurrentUserObj
from app.config import settings
from app.database import SessionDep
from app.models import PushSubscription
from app.push import is_allowed_endpoint, notify_user, push_enabled
from app.schemas import PushSubscriptionIn, PushUnsubscribeIn

router = APIRouter(prefix="/api/push", tags=["push"])


@router.get("/public-key")
def public_key() -> dict:
    """Klucz publiczny VAPID; null = push wyłączony na serwerze (brak kluczy w .env)."""
    return {"public_key": settings.vapid_public_key if push_enabled() else None}


@router.post("/subscriptions")
def subscribe(data: PushSubscriptionIn, user: CurrentUserObj, session: SessionDep) -> dict:
    if not push_enabled():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Powiadomienia są wyłączone na serwerze")
    if not is_allowed_endpoint(data.endpoint):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Nieznana usługa powiadomień")
    # Upsert po endpoincie: to samo urządzenie zapisane ponownie (albo po
    # przelogowaniu na inne konto) nadpisuje stary wpis zamiast tworzyć duplikat.
    sub = session.exec(
        select(PushSubscription).where(PushSubscription.endpoint == data.endpoint)  # type: ignore[arg-type]
    ).first()
    if sub is None:
        sub = PushSubscription(user_id=user.id, endpoint=data.endpoint, p256dh="", auth="")
    sub.user_id = user.id
    sub.p256dh = data.keys.p256dh
    sub.auth = data.keys.auth
    session.add(sub)
    session.commit()
    return {"subscribed": True}


@router.delete("/subscriptions")
def unsubscribe(data: PushUnsubscribeIn, user: CurrentUserObj, session: SessionDep) -> dict:
    sub = session.exec(
        select(PushSubscription).where(
            PushSubscription.endpoint == data.endpoint,  # type: ignore[arg-type]
            PushSubscription.user_id == user.id,  # type: ignore[arg-type]
        )
    ).first()
    if sub is not None:
        session.delete(sub)
        session.commit()
    return {"subscribed": False}


@router.post("/test")
def send_test(user: CurrentUserObj, session: SessionDep) -> dict:
    """Testowe powiadomienie na wszystkie urządzenia konta — do sprawdzenia, czy działa."""
    sent = notify_user(session, user.id, "PapuTrain", "Powiadomienia działają 💪")
    if sent == 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Brak aktywnych urządzeń z powiadomieniami")
    return {"sent": sent}
