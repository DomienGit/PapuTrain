"""Powiadomienia push (req 31): klucz publiczny, zapis/usunięcie subskrypcji, test.

Frontend pobiera klucz publiczny VAPID, prosi telefon o zgodę i subskrypcję,
a wynik (endpoint + klucze) zapisuje tutaj. Wysyłka: app/push.py.
"""

import time

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlmodel import Session, select

from app.auth import CurrentUserObj
from app.config import settings
from app.database import SessionDep, engine
from app.models import PushSubscription
from app.push import is_allowed_endpoint, notify_user, push_enabled
from app.schemas import PushSubscriptionIn, PushUnsubscribeIn

router = APIRouter(prefix="/api/push", tags=["push"])

# Opóźnienie powiadomienia testowego: czas na zamknięcie aplikacji — przy
# otwartej aplikacji sw.js celowo nie pokazuje powiadomienia.
TEST_DELAY_S = 10


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
def send_test(
    background: BackgroundTasks, user: CurrentUserObj, session: SessionDep
) -> dict:
    """Testowe powiadomienie na wszystkie urządzenia konta, wysyłane po TEST_DELAY_S
    sekundach. Odpowiedź wraca od razu; wysyłka idzie w tle (BackgroundTasks =
    zadanie, które FastAPI uruchamia po wysłaniu odpowiedzi)."""
    has_device = session.exec(
        select(PushSubscription).where(PushSubscription.user_id == user.id)  # type: ignore[arg-type]
    ).first()
    if has_device is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Brak aktywnych urządzeń z powiadomieniami")
    background.add_task(_send_test_later, user.id)
    return {"delay_s": TEST_DELAY_S}


def _send_test_later(user_id: int) -> None:
    time.sleep(TEST_DELAY_S)
    # Sesja z żądania jest już zamknięta — zadanie w tle otwiera własną.
    with Session(engine) as session:
        notify_user(session, user_id, "PapuTrain", "Powiadomienia działają 💪")
