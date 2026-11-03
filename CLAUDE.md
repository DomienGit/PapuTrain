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
- Zrobione: PLAN.md (pełna specyfikacja), Etap 0 (szkielet FastAPI), Etap 1 (baza SQLModel, 6 tabel, katalog ćwiczeń JSON, CRUD: profil/sprzęt/katalog), Etap 2 (logowanie JWT + bcrypt, ochrona /api, skrypt `python -m app.create_user`), Etap 3 (frontend: React+Vite+Tailwind w `frontend/`, ekran logowania, token w localStorage, proxy `/api` w vite.config.js), Etap 4 (onboarding 3 kroki, zakładka "Sprzęt i ćwiczenia", panel "Obciążenie" z krążkami, flaga "Siłownia"; przetestowane na poziomie API i builda — kliki Dominika do potwierdzenia), Etap 5 (Gemini generuje draft planu: prompt z profilu/sprzętu/katalogu, walidacja JSON, zapis do bazy, endpointy generate/draft/active; fallback modeli z .env GEMINI_MODELS przy wyczerpaniu darmowego limitu + do 3 ponowień tego samego modelu przy przeciążeniu; klucz w .env; przetestowane NA ŻYWO — plan wygenerowany w ~3,5 s), Etap 6 (panel szkicu: zatwierdzenie draft→active ze zarchiwizowaniem starego, odrzucenie, ręczna edycja treningu/ćwiczeń (PATCH/DELETE), "poproś AI o zmianę" per trening na żywo; frontend DraftPanel.jsx; edycja tylko w statusie draft), Etap 7 (trening na żywo: odhaczanie treningów z datą wykonania, oceny wykonania 1-5 i uwagi do ćwiczeń w aktywnym planie, blokada "Generuj następny tydzień" do odhaczenia wszystkich, generowanie z HISTORIĄ poprzedniego planu w promptcie (wykonania, oceny, uwagi, daty + zasada progresji), zakładka Stoper (start/stop/reset, stan w App.jsx) + pływający pasek na każdej zakładce, gwiazdki preferencji 1-5 w katalogu; wspólne gwiazdki: components/Stars.jsx).
- Następny: Etap 8 (historia: lista archiwalnych planów + widok szczegółów).
- Uwaga środowiskowa: `.venv` budować na Pythonie 3.12 (na 3.14 sqlmodel 0.0.24 się wysypuje; lokalnie używamy `uv venv --python 3.12`).
- Otwarte pytanie z planu: domena na VPS (wpływa tylko na Etap 10).
