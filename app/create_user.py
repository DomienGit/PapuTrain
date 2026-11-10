"""Narzędzie admina do zarządzania kontami (req 27 — aplikacja jest wieloosobowa).

Użycie:
    python -m app.create_user <login>

Hasło pytane dwukrotnie przez getpass — nie pojawia się w historii powłoki
ani na ekranie. ENTER (puste hasło) tworzy konto bez hasła: użytkownik ustawi
je sam przy pierwszym logowaniu (ekran "ustaw hasło"). Nowe konto dostaje od
razu własny sprzęt predefiniowany i wbudowany katalog ćwiczeń (seed_user_data).
Jeśli konto o tym loginie już istnieje, nadpisane zostaje hasło (reset hasła
przez admina); dane konta zostają nietknięte.
"""

import argparse
import getpass
import sys

from sqlmodel import Session, select

from app.auth import hash_password
from app.database import engine, init_db, seed_user_data
from app.models import User


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Utwórz konto PapuTrain albo zresetuj jego hasło"
    )
    parser.add_argument("username", help="login, np. dominik")
    args = parser.parse_args()

    print("Hasło (min. 8 znaków). ENTER = puste — użytkownik ustawi")
    print("je sam przy pierwszym logowaniu.")
    password = getpass.getpass("Hasło: ")
    if password:
        repeat = getpass.getpass("Powtórz hasło: ")
        if password != repeat:
            print("Hasła nie są identyczne — nie zapisano niczego.", file=sys.stderr)
            return 1
        if len(password) < 8:
            print("Hasło musi mieć co najmniej 8 znaków.", file=sys.stderr)
            return 1

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
                print(f"Konto '{args.username}' będzie wymagać ustawienia hasła przy logowaniu.")
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
