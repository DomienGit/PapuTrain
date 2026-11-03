"""Narzędzie ustawiające login i hasło jedynego użytkownika aplikacji.

Użycie:
    python -m app.create_user <login>

Hasło pytane dwukrotnie przez getpass — nie pojawia się w historii powłoki
ani na ekranie. Jeśli konto już istnieje, nadpisuje login i hasło
(przydatne do resetu hasła).
"""

import argparse
import getpass
import sys

from sqlmodel import Session, select

from app.auth import hash_password
from app.database import engine, init_db
from app.models import User


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ustaw login i hasło użytkownika PapuTrain"
    )
    parser.add_argument("username", help="login, np. dominik")
    args = parser.parse_args()

    password = getpass.getpass("Hasło (min. 8 znaków): ")
    repeat = getpass.getpass("Powtórz hasło: ")
    if password != repeat:
        print("Hasła nie są identyczne — nie zapisano niczego.", file=sys.stderr)
        return 1
    if len(password) < 8:
        print("Hasło musi mieć co najmniej 8 znaków.", file=sys.stderr)
        return 1

    init_db()
    with Session(engine) as session:
        user = session.exec(select(User)).first()
        if user is None:
            session.add(
                User(username=args.username, password_hash=hash_password(password))
            )
            print(f"Utworzono konto '{args.username}'.")
        else:
            user.username = args.username
            user.password_hash = hash_password(password)
            session.add(user)
            print(f"Zaktualizowano konto '{args.username}'.")
        session.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
