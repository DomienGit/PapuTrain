"""Narzędzie admina do zarządzania kontami (req 27 — aplikacja jest wieloosobowa).

Użycie:
    python -m app.create_user <login>            # konto bez hasła
    python -m app.create_user <login> --set-password  # ustaw/zresetuj hasło

Domyślnie tworzy konto BEZ hasła — użytkownik ustawi je sam przy pierwszym
logowaniu (ekran "ustaw hasło"). Konto dostaje od razu własny sprzęt
predefiniowany i wbudowany katalog ćwiczeń (seed_user_data).

Jeśli konto o tym loginie już istnieje:
    - bez flagi: hasło zostaje WYCZYSZCZONE (użytkownik przy następnym
      logowaniu ustawi nowe — taki jest "reset hasła" przez admina),
    - z flagą --set-password: admin wpisuje nowe hasło (min. 8 znaków,
      getpass — nie widać go na ekranie i nie ląduje w historii powłoki).
Dane konta (profil, plany itd.) zostają zawsze nietknięte.
"""

import argparse
import getpass
import sys

from sqlmodel import Session, select

from app.auth import hash_password
from app.database import engine, init_db, seed_user_data
from app.models import User


def ask_password() -> str:
    """Hasło od admina, dwukrotnie (kontrola literówki), min. 8 znaków."""
    password = getpass.getpass("Hasło (min. 8 znaków): ")
    repeat = getpass.getpass("Powtórz hasło: ")
    if password != repeat:
        print("Hasła nie są identyczne — nie zapisano niczego.", file=sys.stderr)
        raise SystemExit(1)
    if len(password) < 8:
        print("Hasło musi mieć co najmniej 8 znaków.", file=sys.stderr)
        raise SystemExit(1)
    return password


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Utwórz konto PapuTrain albo zresetuj jego hasło"
    )
    parser.add_argument("username", help="login, np. kasia")
    parser.add_argument(
        "--set-password",
        action="store_true",
        help="ustaw hasło teraz (domyślnie: konto bez hasła — użytkownik "
        "ustawi je przy pierwszym logowaniu)",
    )
    args = parser.parse_args()

    password = ask_password() if args.set_password else ""

    init_db()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == args.username)).first()
        if user is not None:
            user.password_hash = hash_password(password) if password else ""
            session.add(user)
            session.commit()
            if password:
                print(f"Zresetowano hasło konta '{args.username}'.")
            else:
                print(
                    f"Wyczyszczono hasło konta '{args.username}' — użytkownik ustawi "
                    f"nowe przy następnym logowaniu."
                )
            return 0

        user = User(
            username=args.username,
            password_hash=hash_password(password) if password else "",
        )
        session.add(user)
        session.flush()  # potrzebne, by mieć user.id przed seedowaniem
        seed_user_data(session, user.id)
        if password:
            print(f"Utworzono konto '{args.username}' z hasłem.")
        else:
            print(
                f"Utworzono konto '{args.username}' bez hasła — użytkownik ustawi je "
                f"przy pierwszym logowaniu."
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
