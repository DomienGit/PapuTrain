# PapuTrain

Webowa aplikacja treningowa na telefon (PWA) — AI generuje plan na tydzień na podstawie
profilu i sprzętu użytkownika, plan można modyfikować i zatwierdzać, treningi odhaczać
i oceniać. Jeden użytkownik: Dominik.

**Źródło prawdy dla funkcji i architektury: `PLAN.md`.** Zanim zaczniesz pracę nad funkcją,
przeczytaj odpowiednią sekcję PLAN.md. Gdy Dominik zmienia wymagania — najpierw zaktualizuj
PLAN.md, potem pisz kod.

## Tryb pracy

- **Dominik jest architektem** — podejmuje decyzje produktowe: co aplikacja robi, jak działa, jak wygląda.
- **Claude pisze kod** — tworzy aplikację i przy każdym większym kawałku KRÓTKO tłumaczy, co zrobił i dlaczego (Dominik uczy się Pythona i DevOps od zera).
- Decyzje implementacyjne w granicach PLAN.md podejmuj sam. Gdy pomysł wykracza poza PLAN.md albo zmienia ustaloną funkcję — zatrzymaj się i zapytaj.
- Nie zakładaj wiedzy Dominika — lepiej wyjaśnić, niż założyć.

## Komunikacja

- Po polsku. Cytaty z błędów/dokumentacji po angielsku zawsze objaśnij po polsku.
- Krótko i konkretnie, bez rozpisywania się bez potrzeby.
- Żargon (IaC, webhook, idempotentność...) wyjaśnij jednym zdaniem przy pierwszym użyciu.

## Proces

- Pracujemy etapami z sekcji "Etapy prac" w PLAN.md, po kolei. Etap kończy się kodem, który DZIAŁA (przetestowany uruchomieniem) + commitem.
- Nie zaczynaj kolejnego etapu bez zamknięcia poprzedniego.
- Push na GitHub tylko na wyraźną prośbę Dominika.
- Jeśli coś w PLAN.md okazuje się niepraktyczne w kodzie — zgłoś i zaproponuj zmianę planu, zanim ją zrobisz.

## Stack (szczegóły i uzasadnienia: PLAN.md)

- Backend: Python 3.12, FastAPI, SQLModel, SQLite (plik bazy w repożytorium serwera, nie w git), pydantic do walidacji.
- Frontend: React + Vite, JavaScript (bez TypeScript na start), Tailwind CSS, folder `frontend/`.
- AI: Google Gemini (model Flash), klucz API w `.env` — `.env` NIGDY nie trafia do repo (gitignore).
- Logowanie: JWT + bcrypt.
- Deploy docelowy: Docker + docker-compose + Nginx + certbot na VPS Dominika (Etap 10).

## Konwencje

- Teksty w UI aplikacji po polsku (aplikacja dla Dominika). Nazwy zmiennych, kod, komunikaty commitów po angielsku (standard branżowy, ważne dla portfolio).
- Commity: krótki, opisowy komunikat; jeden etap = jeden lub kilka sensownych commitów, nie jeden gigantyczny.
- Zależności backendu: `requirements.txt`. Zależności frontendu: `npm` (package-lock w repo).
- Środowisko Pythona: `venv` w katalogu `.venv` (gitignore).

## Stan projektu

- Repo na GitHub: `DomienGit/PapuTrain` (branch `main`), skonfigurowane remote.
- Zrobione: PLAN.md (pełna specyfikacja), CLAUDE.md. Kod: brak — start od Etapu 0.
- Otwarte pytanie z planu: domena na VPS (wpływa tylko na Etap 10).
